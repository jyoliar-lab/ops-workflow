#!/usr/bin/env python3
"""컨테이너 티켓의 ADR 게이트 (CLAUDE.md §5).

  adr-gate.py --adr ADR-0001 --type epic|feature

컨테이너 티켓(epic·feature)은 **accepted ADR을 전제한다.** 굳지 않은 결정으로 일하지 않는다.
  exit 0 = 통과 · exit 1 = 거부

create.py 가 epic·feature 를 만들기 전에 이것을 먼저 돌린다. 거부는 우회하지 않는다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import die, find_adr, read_frontmatter, repo_root  # noqa: E402

args = sys.argv[1:]
if len(args) != 4 or args[0] != "--adr" or args[2] != "--type":
    print("usage: adr-gate.py --adr ADR-NNNN --type epic|feature", file=sys.stderr)
    sys.exit(2)
adr_id, ticket_type = args[1], args[3]

if ticket_type not in ("epic", "feature"):
    print("거부: 게이트는 컨테이너 티켓(epic·feature)에만 건다. 리프(task·bug)는 ADR을 전제하지 않는다.",
          file=sys.stderr)
    sys.exit(2)

root = repo_root()
path = find_adr(root, adr_id, missing_hint=(
    "  컨테이너 티켓(%s)은 accepted ADR을 전제한다 — 결정을 먼저 굳힌다." % ticket_type,))
fm = read_frontmatter(path)
rel = os.path.relpath(path, root)

status = fm.get("status", "")
if status != "accepted":
    die("거부: %s 의 status 가 '%s' 다 — accepted 가 아니다." % (adr_id, status or "없음"),
        "  " + rel,
        "",
        "  컨테이너 티켓(%s)은 accepted ADR을 전제한다 (CLAUDE.md §5)." % ticket_type,
        "  굳지 않은 결정으로 일하지 않는다. ADR을 먼저 accept 하거나, 리프 티켓(task·bug)으로 발행한다.")

# founding / sub 는 경고까지만 한다.
# 판정 근거가 parent 필드 하나뿐이라 거부로 올리기엔 이르다 — 실측 후 판단한다(마찰 로그).
parent = fm.get("parent", "")
if ticket_type == "epic" and parent:
    print("경고: Epic 의 근거 ADR인데 parent(%s)가 있다 — sub-ADR 로 보인다. founding ADR 이 맞나?"
          % parent, file=sys.stderr)
if ticket_type == "feature" and not parent:
    print("경고: Feature 의 근거 ADR인데 parent 가 없다 — founding ADR 로 보인다.", file=sys.stderr)
    print("      Feature 는 sub-ADR 을 전제한다. 정말 Feature 인가, Task 면 충분한가?", file=sys.stderr)

print("통과: %s accepted (%s)" % (adr_id, rel))
