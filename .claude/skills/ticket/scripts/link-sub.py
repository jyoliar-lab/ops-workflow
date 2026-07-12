#!/usr/bin/env python3
"""sub-issue 연결 (CLAUDE.md §5). GraphQL addSubIssue — gh CLI 미지원.

  link-sub.py --parent <N> --child <M> [--repo owner/name]

계층은 **3층에서 멈춘다**: Epic → (Feature) → Task·Bug
  리프(Task·Bug)는 부모가 될 수 없고, Feature 밑에 Feature 는 오지 않는다 → 거부한다.
  (ADR 계층이 2단이므로 티켓 계층도 3층에서 멈춘다.)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
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
if parent_type == "Feature" and child_type in ("Feature", "Epic"):
    die("거부: Feature 밑에 %s 은 오지 않는다 — 계층은 3층에서 멈춘다 (§5)." % child_type)
if child_type == "Epic":
    die("거부: Epic 은 하위 이슈가 될 수 없다 — 최상위 컨테이너다 (§5).")

linked = gh.add_sub_issue(parent_id, child_id)
print("연결: #%s ← #%s" % (linked["issue"]["number"], linked["subIssue"]["number"]))
print("  %s #%d  ←  %s #%d" % (parent_type, args.parent, child_type or "(타입 없음)", args.child))
