#!/usr/bin/env python3
"""동결 사전 검사 (CLAUDE.md §3 불변 경계).

본문을 고치기 전에 돌린다.
  exit 0 = 본문 수정 가능
  exit 1 = 동결 — 수정 불가

동결 상태: adr = accepted | superseded · postmortem = frozen
accept 이후 허용되는 편집은 status · superseded_by 두 필드뿐이고, 그 둘은 supersede.py 가 한다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import FROZEN, die, read_frontmatter  # noqa: E402

if len(sys.argv) != 2:
    print("usage: freeze-check.py <path-to-doc>", file=sys.stderr)
    sys.exit(2)
path = sys.argv[1]

if not os.path.isfile(path):
    print("신규 파일 — 동결 아님")          # 콜드스타트. 에러가 아니다.
    sys.exit(0)

status = read_frontmatter(path).get("status", "")

if status in FROZEN:
    die("거부: 동결된 문서다 (status: %s)" % status,
        "  " + path,
        "",
        "본문 수정 불가. 허용되는 편집은 status · superseded_by 두 필드뿐이다.",
        "",
        "결정을 바꾸려면 → 새 ADR을 쓰고 supersede 한다:",
        "  1. .claude/skills/adr/scripts/next-id.py",
        "  2. 새 ADR 저작 — 여전히 유효한 부분은 **재진술**한다 (부분 supersede 없음)",
        "  3. .claude/skills/adr/scripts/supersede.py --old <옛 id> --by <새 id>")

if not status:
    print("경고: status 필드를 찾지 못했다 — %s" % path, file=sys.stderr)
    sys.exit(0)

print("수정 가능 (status: %s)" % status)
