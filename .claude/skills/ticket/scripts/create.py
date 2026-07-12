#!/usr/bin/env python3
"""Issue 발행 + Issue Type 지정 (CLAUDE.md §5).

  create.py --type epic|feature|task|bug --title "..." --body-file <path> [--adr ADR-NNNN] [--repo owner/name]

`gh issue create` 에는 --type 플래그가 없다 → Issue Type 은 GraphQL 로만 지정된다.

★ close 하는 스크립트가 이 skill 에 없다 (§5) — PR 머지 ≠ 티켓 종료. close 는 사람이 한다.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
import gh  # noqa: E402
from opsdoc import die  # noqa: E402

# Issue Types 4종 (§5). story·spike 는 없다 — argparse 가 그 값을 받지 않는다.
TYPE_NAMES = {"epic": "Epic", "feature": "Feature", "task": "Task", "bug": "Bug"}
CONTAINERS = ("epic", "feature")

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--type", required=True, choices=sorted(TYPE_NAMES))
parser.add_argument("--title", required=True)
parser.add_argument("--body-file", required=True)
parser.add_argument("--adr", help="컨테이너 티켓(epic·feature)의 근거 ADR. 필수")
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
args = parser.parse_args()

if not os.path.isfile(args.body_file):
    die("거부: 본문 파일이 없다 — %s" % args.body_file)

# ★ 게이트 — 컨테이너 티켓은 accepted ADR을 전제한다.
if args.type in CONTAINERS:
    if not args.adr:
        die("거부: --adr 없이 %s 을 만들 수 없다." % TYPE_NAMES[args.type],
            "  컨테이너 티켓은 accepted ADR을 전제한다 (CLAUDE.md §5). 결정을 먼저 굳힌다.",
            "  결정이 아직 없다면 → 리프 티켓(task·bug)이거나, discussion 문서에서 시작한다.")
    gate = subprocess.run([sys.executable, os.path.join(HERE, "adr-gate.py"),
                           "--adr", args.adr, "--type", args.type])
    if gate.returncode != 0:
        sys.exit(gate.returncode)          # 게이트의 거부를 그대로 물려준다. 우회하지 않는다.

number, url = gh.create_issue(args.repo, args.title, args.body_file)
print("생성: #%d — %s" % (number, url))

issue_id, _ = gh.issue_node(args.repo, number)
type_id = gh.issue_type_id(args.repo, TYPE_NAMES[args.type])
issue = gh.set_issue_type(issue_id, type_id)
print("타입 지정: #%s → %s" % (issue["number"], issue["issueType"]["name"]))

if args.adr:
    print("근거 ADR: %s — 문서의 frontmatter ticket: 에 %s#%d 를 되쓴다 (다리는 양쪽에서 놓는다)."
          % (args.adr, args.repo, number))
print(url)
