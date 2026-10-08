#!/usr/bin/env python3
"""sub-issue 연결 (CLAUDE.md §5). GraphQL addSubIssue — gh CLI 미지원.

  link-sub.py --parent <N> --child <M> [--repo owner/name]

거부하는 것은 둘뿐이다 (ADR-0010 — 컨테이너/리프 이분):
  리프(Task·Bug)는 부모가 될 수 없다 · Epic 은 하위가 될 수 없다(최상위 컨테이너).
깊이 상한은 두지 않는다 — Feature 밑에 Feature 도 온다(GitHub 자체 상한 8단).
  **3층(Epic → Feature → 리프)을 권장한다** — 얕음은 규칙이 아니라 결과다.
  ADR 계층도 깊이 제한이 없다 — 그것을 티켓에 그대로 옮기려 들지 않는다.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import _bootstrap  # noqa: F401 — git 루트의 .claude/skills/_lib 를 sys.path 에 올린다
import gh  # noqa: E402
from opsdoc import die  # noqa: E402

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--parent", required=True, type=int)
parser.add_argument("--child", required=True, type=int)
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
args = parser.parse_args()

if args.parent == args.child:
    die("거부: 자기 자신에게 붙일 수 없다.")

parent_id, parent_type = gh.issue_node(args.repo, args.parent)
child_id, child_type = gh.issue_node(args.repo, args.child)

if parent_type in ("Task", "Bug"):
    die("거부: #%d 은 %s — 리프다. 컨테이너가 아니므로 하위 이슈를 담을 수 없다 (§5)."
        % (args.parent, parent_type))
if parent_type is None:
    die("거부: #%d 에 Issue Type 이 없다. 타입 없는 이슈를 컨테이너로 쓰지 않는다." % args.parent)
if child_type == "Epic":
    die("거부: Epic 은 하위 이슈가 될 수 없다 — 최상위 컨테이너다 (§5).")

linked = gh.add_sub_issue(parent_id, child_id)
print("연결: #%s ← #%s" % (linked["issue"]["number"], linked["subIssue"]["number"]))
print("  %s #%d  ←  %s #%d" % (parent_type, args.parent, child_type or "(타입 없음)", args.child))
