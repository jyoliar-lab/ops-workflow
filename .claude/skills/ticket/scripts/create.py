#!/usr/bin/env python3
"""Issue 발행 + Issue Type 지정 + Project 등록 (CLAUDE.md §5).

  create.py --type epic|feature|task|bug --title "..." --body-file <path> [--adr ADR-NNNN] [--repo owner/name]

`gh issue create` 에는 --type 플래그가 없다 → Issue Type 은 GraphQL 로만 지정된다.

브리지는 **이슈가 문서를 가리키는** 방향으로만 놓인다 (§1) — 동결 문서는 살아 있는 필드를 담지 못하므로.
그래서 이 스크립트가 두 곳에 근거 ADR 을 박는다. 사람이 잊을 수 없고 agent 가 빠뜨릴 수 없다:
  1. **이슈 본문** — 사람이 읽고 문서로 건너간다
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
parser.add_argument("--adr", help="컨테이너 티켓(epic·feature)의 근거 ADR. 필수")
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
args = parser.parse_args()

if not os.path.isfile(args.body_file):
    die("거부: 본문 파일이 없다 — %s" % args.body_file)

# ★ 게이트 — 컨테이너 티켓은 accepted ADR을 전제한다. (공표된 사본을 읽는다)
adr_path, adr_sha = None, None
if args.type in CONTAINERS:
    if not args.adr:
        die("거부: --adr 없이 %s 을 만들 수 없다." % TYPE_NAMES[args.type],
            "  컨테이너 티켓은 accepted ADR을 전제한다 (CLAUDE.md §5). 결정을 먼저 굳힌다.",
            "  결정이 아직 없다면 → 리프 티켓(task·bug)이거나, discussion 문서에서 시작한다.")
    gate = subprocess.run([sys.executable, os.path.join(HERE, "adr-gate.py"),
                           "--adr", args.adr, "--type", args.type],
                          capture_output=True, text=True)
    sys.stderr.write(gate.stderr)
    if gate.returncode != 0:
        sys.exit(gate.returncode)          # 게이트의 거부를 그대로 물려준다. 우회하지 않는다.
    for line in gate.stdout.splitlines():   # 게이트가 통과시킨 바로 그 사본을 링크한다
        if line.startswith("path="):
            adr_path = line[5:].strip()
        elif line.startswith("sha="):
            adr_sha = line[4:].strip()
    if not adr_path or not adr_sha:
        die("거부: 게이트가 공표된 사본의 경로·커밋을 주지 않았다.")

# ── 본문에 근거 ADR 을 박는다 (사람이 읽고 건너가는 통로) ──────────────────
# 링크는 **절대 URL**이라야 한다. 이슈 본문의 상대 경로는 저장소 루트가 아니라
# 이슈 URL 기준으로 풀린다 (…/issues/docs/… → 404). README 와 다르다.
# 브리지가 클릭되지 않으면 그것은 놓인 브리지가 아니다.
#
# 링크를 **둘** 넣는다 — 서로 다른 질문에 답한다:
#   HEAD      → "이 결정이 지금도 유효한가" (supersede 되면 그 자리에서 드러난다)
#   permalink → "이 티켓은 어느 시점의 문서를 근거로 발행됐나" (불변)
# 주 링크는 HEAD 다. SHA 만 걸면 supersede 된 결정이 accepted 인 채로 영원히 보인다.
body_file = args.body_file
if adr_path:
    with open(args.body_file, encoding="utf-8") as f:
        body = f.read().rstrip()
    body += "\n\n---\n\n근거: **%s** — [`%s`](https://github.com/%s/blob/HEAD/%s)\n" % (
        args.adr, adr_path, args.repo, adr_path)
    body += "\n<sub>발행 시점 스냅샷: [`%s`](https://github.com/%s/blob/%s/%s)</sub>\n" % (
        adr_sha[:7], args.repo, adr_sha, adr_path)
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

if args.adr:
    adr_field = proj["fields"].get("ADR")
    if not adr_field:
        die("거부: Project #%d 에 'ADR' 필드가 없다 — 근거를 담을 자리가 없다." % PROJECT_NUMBER)
    gh.set_text_field(proj["id"], item_id, adr_field["id"], args.adr)
    print("ADR 필드: %s  (조회: Project 보드에서 ADR = %s 로 필터)" % (args.adr, args.adr))

print(url)
