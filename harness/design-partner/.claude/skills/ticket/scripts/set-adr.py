#!/usr/bin/env python3
"""티켓의 근거 ADR 을 **사후에** 기입·갱신·철회한다.

  set-adr.py --issue N [--repo owner/name]
             --adr ADR-NNNN... | --clear

세 용도 — 발행(create.py)과 같은 게이트, 같은 표기(adr_context.py)로:
  1. **소급 기입** — '근거 ADR' 절 없이 발행된 티켓에 절·필드를 단다.
  2. **갱신** — 근거 목록이 달라졌을 때(supersede 반영, 이행 결정 추가 등).
     부분 수정이 아니라 **전체 답을 다시 낸다** — 절은 통째로 교체된다. 절은 언제나 하나다.
  3. **철회**(--clear · Epic 외 전용) — 잘못 단 명시를 거둔다. 절 제거 + 필드 비움.

게이트는 발행과 같다:
  - 명시된 ADR 은 전부 공표·비superseded·비rejected 여야 한다 (adr-gate.py — 답하면
    참이어야 한다. accepted 요구는 착수의 문 — 집행 도구의 착수 게이트가 검사한다).
  - **Epic 은 --clear 가 거부된다** — Epic 의 근거는 존재의 전제다. 없앨 수 있는 문은 없다.
  - --adr 과 --clear 는 XOR — 침묵도, 양다리도 답이 아니다.
  - **Project 미등록 이슈 거부** — 등록은 발행(create.py)의 일이다. 여기서 슬쩍 등록하지 않는다.

블록을 손으로 고치지 않는다 — 갱신은 언제나 이 스크립트다 (set-repos.py 와 같은 규약).
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import _bootstrap  # noqa: F401 — git 루트의 .claude/skills/_lib 를 sys.path 에 올린다
import gh  # noqa: E402
import adr_context  # noqa: E402  (같은 디렉터리 — '근거 ADR' 절 공용 로직)
from opsdoc import die  # noqa: E402

ADR_REQUIRED_TYPES = ("Epic",)   # 근거가 존재의 전제인 타입 — --clear 불가 (CLAUDE.md §5)
PROJECT_NUMBER = int(os.environ.get("OPS_PROJECT", "1"))

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--issue", required=True, type=int, metavar="N", help="대상 이슈 번호")
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
parser.add_argument("--adr", action="append", default=[], metavar="ADR-NNNN",
                    help="근거 ADR(반복 가능). 절·필드가 이 목록으로 통째 교체된다")
parser.add_argument("--clear", action="store_true",
                    help="근거 명시를 철회한다(Epic 외 전용) — 절 제거 + 필드 비움")
args = parser.parse_args()

if bool(args.adr) == args.clear:
    die("거부: --adr 목록 XOR --clear — 둘 중 하나로 답한다.",
        "  갱신이면 새 전체 목록을 --adr 로, 철회(리프)면 --clear 로.")

issue_id, type_name, body = gh.issue_view(args.repo, args.issue)

if not type_name:
    die("거부: #%d 에 Issue Type 이 없다 — 컨테이너/리프를 판정할 수 없다." % args.issue,
        "  먼저 타입을 지정한다.")
if args.clear and type_name in ADR_REQUIRED_TYPES:
    die("거부: #%d 는 %s 다 — 근거는 존재의 전제라 철회할 수 없다." % (args.issue, type_name),
        "  근거가 틀렸다면 --adr 로 올바른 전체 목록을 다시 낸다.")

# ── 게이트 — 발행과 같은 문. 명시된 근거는 전부 공표·비superseded·비rejected 여야 한다 ──
adr_entries = []                            # [(id, title, path, sha)]
for adr_id in dict.fromkeys(args.adr):      # 중복 제거 · 순서 보존
    gate = subprocess.run([sys.executable, os.path.join(HERE, "adr-gate.py"),
                           "--adr", adr_id, "--type", type_name.lower()],
                          capture_output=True, text=True)
    sys.stderr.write(gate.stderr)
    if gate.returncode != 0:
        sys.exit(gate.returncode)          # 게이트의 거부를 그대로 물려준다. 우회하지 않는다.
    adr_path, adr_sha, adr_title = None, None, ""
    for line in gate.stdout.splitlines():
        if line.startswith("path="):
            adr_path = line[5:].strip()
        elif line.startswith("sha="):
            adr_sha = line[4:].strip()
        elif line.startswith("title="):
            adr_title = line[6:].strip()
    if not adr_path or not adr_sha:
        die("거부: 게이트가 공표된 사본의 경로·커밋을 주지 않았다 — %s" % adr_id)
    adr_entries.append((adr_id, adr_title, adr_path, adr_sha))

# ── ① 본문 '### 근거 ADR' 절 — 교체·추가·제거 ──────────────────────────────
had_section = adr_context.SECTION_HEADER in body
if args.clear:
    if not had_section:
        print("본문: #%d 에 '근거 ADR' 절이 원래 없다 — 본문은 그대로." % args.issue)
    else:
        gh.update_issue_body(issue_id, adr_context.remove_section(body))
        print("본문 '근거 ADR' 절 제거: #%d" % args.issue)
else:
    new_body = adr_context.upsert_section(
        body, adr_context.render_section(adr_entries, args.repo))
    gh.update_issue_body(issue_id, new_body)
    print("본문 '근거 ADR' 절 %s: #%d" % ("갱신" if had_section else "소급 기입", args.issue))

# ── ② Project 'ADR' 필드 — 기계 질의의 자리 ────────────────────────────────
org = args.repo.split("/")[0]
proj = gh.project(org, PROJECT_NUMBER)
item_id = gh.project_item(issue_id, proj["id"])
if not item_id:
    die("거부: #%d 는 Project #%d 에 등록돼 있지 않다." % (args.issue, PROJECT_NUMBER),
        "  등록(+초기 Status)은 발행 스크립트(create.py)의 일이다 — 여기서 슬쩍 등록하지 않는다.")
value = adr_context.set_field(proj, item_id, [e[0] for e in adr_entries], PROJECT_NUMBER)
print("ADR 필드: %s" % (value or "(비움)"))
