#!/usr/bin/env python3
"""Issue 발행 + Issue Type 지정 + Project 등록 (CLAUDE.md §5).

  create.py --type epic|feature|task|bug --title "..." --body-file <path>
            [--adr ADR-NNNN]... [--repo owner/name]
            [--target-repo owner/name]... | --no-target-repo   [--ref-repo owner/name]...

★ 리프(task·bug)는 저장소 맥락에 답해야 발행된다 (ADR-0016 파일럿):
  - 수정 대상(target) — 집행자가 고쳐도 되는 저장소의 전부(다수 가능). 지정하거나
    --no-target-repo 로 부재(신규 저장소 생성 등)를 명시적으로 선언한다.
    침묵은 거부다 — 빈 자리는 누락인지 부재인지 말하지 못한다.
  - 참조(ref) — 구조 파악의 출발점. 비완전 목록(나열 밖 참조 허용)이라 선택 입력.
  두 곳에 박는다: 이슈 본문 '저장소' 절(YAML 블록 — 사람·집행 도구 공용 표기) + Project 'Target Repos' 필드(보드 질의).
  컨테이너(epic·feature)는 담지 않는다 — 집행 맥락은 수행 단위(리프)의 것이다.
  게이트·렌더링은 repo_context.py 에 산다 — 사후 기입·갱신(set-repos.py)과 같은 코드다.

★ 근거 ADR 은 목록이다(--adr 반복 가능) — 게이트는 명시된 전부에 걸린다.
  컨테이너: 필수(전제). 리프: 선택 — **직접 이행하는** 결정이 있을 때만 명시하고,
  부모 컨테이너의 근거를 되풀이하지 않는다. 이행할 일이 낱개 하나면 리프로 충분하다.
  (컨테이너의 근거 = 존재의 전제 · 리프의 근거 = 이행 추적. 리프 목록은 비완전한 힌트다.)

★ 본문은 templates/ 의 타입별 템플릿에서 시작한다 (epic.md — Feature 도 이것 · task.md · bug.md).
  공통 절(Context·Goal·Acceptance Criteria·References)은 이름까지 한 벌이다.
  ADR 링크·'저장소' 절은 템플릿에 없다 — 이 스크립트가 박는다.

`gh issue create` 에는 --type 플래그가 없다 → Issue Type 은 GraphQL 로만 지정된다.

브리지는 **이슈가 문서를 가리키는** 방향으로만 놓인다 (§1) — 동결 문서는 살아 있는 필드를 담지 못하므로.
그래서 이 스크립트가 두 곳에 근거 ADR 을 박는다. 사람이 잊을 수 없고 agent 가 빠뜨릴 수 없다:
  1. **이슈 본문 '근거 ADR' 절** — YAML 블록(기계) + 링크(사람이 건너간다). 표기는 adr_context.py
  2. **Project 의 ADR 필드** — 기계가 정확히 필터한다 (라벨은 다중·평면이라 단일 값 속성에 안 맞는다)

★ close 하는 스크립트는 이 skill 에 없다 (§5) — PR 머지 ≠ 티켓 종료. close 는 사람이 한다.
"""
import argparse
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
import gh  # noqa: E402
import repo_context  # noqa: E402  (같은 디렉터리 — ADR-0016 저장소 맥락 공용 로직)
import adr_context  # noqa: E402  (같은 디렉터리 — '근거 ADR' 절 공용 로직)
from opsdoc import die  # noqa: E402

# Issue Types 4종 (§5). story·spike 는 없다 — argparse 가 그 값을 받지 않는다.
TYPE_NAMES = {"epic": "Epic", "feature": "Feature", "task": "Task", "bug": "Bug"}
CONTAINERS = ("epic", "feature")

PROJECT_NUMBER = int(os.environ.get("OPS_PROJECT", "1"))
INITIAL_STATUS = "Backlog"     # 도구는 초기값만 넣는다. 이후 전이는 사람의 것이다 (§5)

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--type", required=True, choices=sorted(TYPE_NAMES))
parser.add_argument("--title", required=True)
parser.add_argument("--body-file", required=True)
parser.add_argument("--adr", action="append",
                    help="근거 ADR. 반복 가능. 컨테이너는 필수 · 리프는 선택(직접 이행하는 결정만)")
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
repo_context.add_args(parser)   # --target-repo / --no-target-repo / --ref-repo
args = parser.parse_args()

if not os.path.isfile(args.body_file):
    die("거부: 본문 파일이 없다 — %s" % args.body_file)

# ★ 저장소 맥락 게이트 — 리프는 "어디를 고치는가"에 답해야 발행된다 (ADR-0016 파일럿).
if args.type in CONTAINERS:
    if args.target_repo or args.no_target_repo or args.ref_repo:
        die("거부: 컨테이너(%s)는 저장소 맥락을 담지 않는다." % TYPE_NAMES[args.type],
            "  묶음은 여러 저장소에 걸칠 수 있다 — 집행 맥락은 수행 단위(리프)의 것이다 (ADR-0016).")
else:
    repo_context.validate_answer(args.target_repo, args.no_target_repo, args.ref_repo,
                                 TYPE_NAMES[args.type])

# ★ 게이트 — 근거 ADR 은 **목록**이다(1개 이상). 티켓 하나가 여러 결정에서 비롯될 수 있다.
#   컨테이너: 근거 필수(전제 — CLAUDE.md §5). 침묵은 거부다.
#   리프: 근거 선택 — 리프가 **직접 이행하는** 결정이 있을 때만 명시한다.
#         부모 컨테이너의 근거를 되풀이하지 않는다(사본은 낡는다).
#   명시된 근거는 타입 불문 전부 게이트를 지난다: 하나라도 미accept·미공표면 발행 거부.
#   — 답하지 않아도 되(리프)지만, 답하면 참이어야 한다.
adr_entries = []                    # [(id, title, path, sha)] — 게이트를 통과한 사본들
if args.type in CONTAINERS and not args.adr:
    die("거부: --adr 없이 %s 을 만들 수 없다." % TYPE_NAMES[args.type],
        "  컨테이너 티켓은 accepted ADR을 전제한다 (CLAUDE.md §5). 결정을 먼저 굳힌다.",
        "  결정이 아직 없다면 → 리프 티켓(task·bug)이거나, discussion 문서에서 시작한다.")
for adr_id in dict.fromkeys(args.adr or []):    # 중복 제거 · 순서 보존
    gate = subprocess.run([sys.executable, os.path.join(HERE, "adr-gate.py"),
                           "--adr", adr_id, "--type", args.type],
                          capture_output=True, text=True)
    sys.stderr.write(gate.stderr)
    if gate.returncode != 0:
        sys.exit(gate.returncode)          # 게이트의 거부를 그대로 물려준다. 우회하지 않는다.
    adr_path, adr_sha, adr_title = None, None, ""
    for line in gate.stdout.splitlines():   # 게이트가 통과시킨 바로 그 사본을 링크한다
        if line.startswith("path="):
            adr_path = line[5:].strip()
        elif line.startswith("sha="):
            adr_sha = line[4:].strip()
        elif line.startswith("title="):
            adr_title = line[6:].strip()
    if not adr_path or not adr_sha:
        die("거부: 게이트가 공표된 사본의 경로·커밋을 주지 않았다 — %s" % adr_id)
    adr_entries.append((adr_id, adr_title, adr_path, adr_sha))

# ── 본문에 '근거 ADR' 절을 박는다 — 구조화 표기('저장소' 절과 같은 패턴).
#    YAML 블록(기계) + HEAD·permalink 링크(사람). 왜 그 모양인지는 adr_context.py.
extra = []
if adr_entries:
    extra.append(adr_context.render_section(adr_entries, args.repo))

# ── 리프의 '저장소' 절 (ADR-0016 파일럿) — 집행자가 읽는 자리 ────────────────
# target 은 살아 있는 사실이다: 작업 중 수정 대상이 늘면 이 절과 Project 필드를
# **먼저 갱신**한다(필수 — set-repos.py). ref 는 비완전 힌트 — 갱신은 권장.
if args.type not in CONTAINERS:
    extra.append(repo_context.render_section(args.target_repo, args.ref_repo))

body_file = args.body_file
if extra:
    with open(args.body_file, encoding="utf-8") as f:
        body = f.read().rstrip()
    body += "\n\n---\n\n" + "\n".join(extra)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(body)
    tmp.close()
    body_file = tmp.name

number, url = gh.create_issue(args.repo, args.title, body_file)
print("생성: #%d — %s" % (number, url))

issue_id, _ = gh.issue_node(args.repo, number)
type_id = gh.issue_type_id(args.repo, TYPE_NAMES[args.type])
issue = gh.set_issue_type(issue_id, type_id)
print("타입 지정: #%s → %s" % (issue["number"], issue["issueType"]["name"]))

# ── Project 등록 — 근거 ADR 이 사는 곳 ────────────────────────────────────
org = args.repo.split("/")[0]
proj = gh.project(org, PROJECT_NUMBER)
item_id = gh.add_to_project(proj["id"], issue_id)

status = proj["fields"].get("Status")
if status:
    gh.set_select_field(proj["id"], item_id, status["id"], gh.option_id(status, INITIAL_STATUS))
    print("Project #%d 등록 · Status: %s" % (PROJECT_NUMBER, INITIAL_STATUS))

if adr_entries:   # 텍스트 필드 — 필터는 부분 일치라 다수여도 걸린다
    adr_value = adr_context.set_field(proj, item_id, [e[0] for e in adr_entries], PROJECT_NUMBER)
    print("ADR 필드: %s  (조회: Project 보드에서 ADR 부분 일치로 필터)" % adr_value)

# ── Target Repos 필드 — 기계가 "이 저장소를 고치는 열린 리프"를 질의하는 자리 (ADR-0016) ──
if args.type not in CONTAINERS:
    trepo_value = repo_context.set_field(proj, item_id, args.target_repo, PROJECT_NUMBER)
    print("Target Repos 필드: %s" % trepo_value)

print(url)
