#!/usr/bin/env python3
"""동결 사전 검사 (CLAUDE.md §3 불변 경계).

  freeze-check.py <path>    본문을 고치기 전에 돌린다
  freeze-check.py           동결 문서 전량의 **경로 변경**을 훑는다

  exit 0 = 통과 · exit 1 = 거부

**동결은 본문만이 아니라 경로에도 걸린다.** 본문을 얼려 놓고 파일을 옮기면
그 ADR 을 가리키던 인용이 전부 깨진다 — 얼린 의미가 없다.
그래서 accept 이후의 rename 은 금지이고, 여기서 검출한다(기준: HEAD 의 경로).

동결 상태: adr = accepted | superseded · postmortem = frozen
accept 이후 허용되는 편집은 status · superseded_by 두 필드뿐이고, 그 둘은 accept.py · supersede.py 가 한다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import FROZEN, iter_docs, read_frontmatter, repo_root  # noqa: E402
from vcs import head_path_of_id  # noqa: E402

root = repo_root()


def moved(path, fm):
    """동결 문서가 HEAD 와 다른 경로에 있으면 (옛 경로, 새 경로)."""
    doc_id = fm.get("id")
    if not doc_id:
        return None                       # id 없는 문서(discussion·postmortem)는 인용키가 없다
    was = head_path_of_id(root, doc_id)
    now = os.path.relpath(path, root)
    return (was, now) if was and was != now else None


# ── 인자 없음: 동결 문서 전량의 경로 변경을 훑는다 ────────────────────────
if len(sys.argv) == 1:
    moves = []
    for path, fm in iter_docs(root):
        if fm.get("status") in FROZEN:
            m = moved(path, fm)
            if m:
                moves.append((fm.get("id"), m[0], m[1]))
    if moves:
        print("거부: 동결된 문서의 경로가 바뀌었다 — 이 id 를 가리키던 인용이 전부 깨진다.",
              file=sys.stderr)
        for doc_id, was, now in moves:
            print("  %s: %s → %s" % (doc_id, was, now), file=sys.stderr)
        print("", file=sys.stderr)
        print("  accept 후 rename 은 금지다 (§3). 옛 경로로 되돌린다.", file=sys.stderr)
        print("  이름이 정말 잘못됐다면 → 새 ADR 로 supersede 한다. 얼린 문서는 그대로 둔다.",
              file=sys.stderr)
        sys.exit(1)
    print("동결 문서의 경로 변경 없음")
    sys.exit(0)

if len(sys.argv) != 2:
    print("usage: freeze-check.py [<path-to-doc>]", file=sys.stderr)
    sys.exit(2)
path = sys.argv[1]

# ── 경로 하나: 본문 수정 가능한가 ─────────────────────────────────────────
if not os.path.isfile(path):
    print("신규 파일 — 동결 아님")            # 콜드스타트. 에러가 아니다.
    sys.exit(0)

fm = read_frontmatter(path)
status = fm.get("status", "")

if status in FROZEN:
    m = moved(os.path.abspath(path), fm)
    print("거부: 동결된 문서다 (status: %s)" % status, file=sys.stderr)
    print("  " + path, file=sys.stderr)
    if m:
        print("  ⚠ 게다가 경로가 HEAD 와 다르다: %s → %s" % m, file=sys.stderr)
        print("    accept 후 rename 은 금지다 — 인용이 깨진다. 옛 경로로 되돌린다.", file=sys.stderr)
    print("", file=sys.stderr)
    print("본문 수정 불가. 허용되는 편집은 status · superseded_by 두 필드뿐이다.", file=sys.stderr)
    print("", file=sys.stderr)
    print("결정을 바꾸려면 → 새 ADR 을 쓰고 supersede 한다:", file=sys.stderr)
    print("  1. .claude/skills/adr/scripts/next-id.py", file=sys.stderr)
    print("  2. 새 ADR 저작 — 여전히 유효한 부분은 **재진술**한다 (부분 supersede 없음)", file=sys.stderr)
    print("  3. .claude/skills/adr/scripts/supersede.py --old <옛 id> --by <새 id>", file=sys.stderr)
    sys.exit(1)

if not status:
    print("경고: status 필드를 찾지 못했다 — %s" % path, file=sys.stderr)
    sys.exit(0)

print("수정 가능 (status: %s)" % status)
