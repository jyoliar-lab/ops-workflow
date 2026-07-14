#!/usr/bin/env python3
"""동결 사전 검사 (CLAUDE.md §3 불변 경계).

  freeze-check.py <path>    본문을 고치기 전에 돌린다
  freeze-check.py           동결 문서 전량의 **경로 변경**을 훑는다

  exit 0 = 통과 · exit 1 = 거부

★ **판정 기준은 공표된 사본(origin/main)이다. 워킹 트리가 아니다.**
동결은 **공표 시점에 발효한다** — 아직 push 되지 않은 accept 는 아무도 보지 못한 결정이므로
되돌릴 수 있다(§3). **동결은 시각이 아니라 상태이고, 그 상태는 "공표됐는가" 하나로 판정된다.**
워킹 트리의 status 로 판정하면, 아무도 못 본 문서를 무를 수 없다고 우기게 된다.
그건 규율이 아니라 형식이다.

**동결은 경로에도 걸린다.** 본문을 얼려 놓고 파일을 옮기면 그 문서를 가리키던 인용이 깨진다.

동결 상태: adr = accepted | superseded · postmortem = frozen
공표 이후 허용되는 편집은 status · superseded_by 두 필드뿐이고, 그 둘은 accept.py · supersede.py 가 한다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
import vcs  # noqa: E402
from opsdoc import FROZEN, iter_docs, parse_frontmatter, read_frontmatter, repo_root  # noqa: E402

root = repo_root()


def published(path):
    """공표된 사본의 frontmatter. 아직 공표되지 않았으면 None."""
    rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")
    text = vcs.read_at(root, rel)
    return parse_frontmatter(text) if text else None


def moved(path, fm):
    """동결 문서가 공표된 사본과 다른 경로에 있으면 (옛 경로, 새 경로)."""
    doc_id = fm.get("id")
    if not doc_id:
        return None                       # id 없는 문서(discussion·postmortem)는 인용키가 없다
    was = vcs.path_of_id(root, doc_id)
    now = os.path.relpath(path, root).replace(os.sep, "/")
    return (was, now) if was and was != now else None


vcs.fetch_published(root)     # 실패해도 죽지 않는다 — 로컬의 마지막 사본으로 판단한다

# ── 인자 없음: 동결 문서 전량의 경로 변경을 훑는다 ────────────────────────
if len(sys.argv) == 1:
    moves = []
    for path, fm in iter_docs(root):
        pub = published(path)
        if pub and pub.get("status") in FROZEN:
            m = moved(path, pub)
            if m:
                moves.append((pub.get("id"), m[0], m[1]))
    if moves:
        print("거부: 공표된 동결 문서의 경로가 바뀌었다 — 이 id 를 가리키던 인용이 전부 깨진다.",
              file=sys.stderr)
        for doc_id, was, now in moves:
            print("  %s: %s → %s" % (doc_id, was, now), file=sys.stderr)
        print("", file=sys.stderr)
        print("  accept·공표 후 rename 은 금지다 (§3). 옛 경로로 되돌린다.", file=sys.stderr)
        print("  이름이 정말 잘못됐다면 → 새 ADR 로 supersede 한다. 얼린 문서는 그대로 둔다.",
              file=sys.stderr)
        sys.exit(1)
    print("공표된 동결 문서의 경로 변경 없음")
    sys.exit(0)

if len(sys.argv) != 2:
    print("usage: freeze-check.py [<path-to-doc>]", file=sys.stderr)
    sys.exit(2)
path = sys.argv[1]

# ── 경로 하나: 본문 수정 가능한가 ─────────────────────────────────────────
if not os.path.isfile(path):
    print("신규 파일 — 동결 아님")            # 콜드스타트. 에러가 아니다.
    sys.exit(0)

pub = published(path)
local_status = read_frontmatter(path).get("status", "")

if pub is None:
    # 아직 공표되지 않았다 → 얼지 않았다. 로컬에서 accept 했더라도 되돌릴 수 있다.
    if local_status in FROZEN:
        print("수정 가능 — 아직 공표되지 않았다 (로컬 status: %s)" % local_status)
        print("  push 하는 순간 얼어붙는다. 고칠 것이 있으면 지금이다.")
    else:
        print("수정 가능 (status: %s)" % (local_status or "없음"))
    sys.exit(0)

pub_status = pub.get("status", "")

if pub_status in FROZEN:
    m = moved(os.path.abspath(path), pub)
    print("거부: 공표된 동결 문서다 (status: %s)" % pub_status, file=sys.stderr)
    print("  " + path, file=sys.stderr)
    if m:
        print("  ⚠ 게다가 경로가 공표된 것과 다르다: %s → %s" % m, file=sys.stderr)
        print("    공표 후 rename 은 금지다 — 인용이 깨진다. 옛 경로로 되돌린다.", file=sys.stderr)
    print("", file=sys.stderr)
    print("본문 수정 불가. 허용되는 편집은 status · superseded_by 두 필드뿐이다.", file=sys.stderr)
    print("", file=sys.stderr)
    print("결정을 바꾸려면 → 새 ADR 을 쓰고 supersede 한다:", file=sys.stderr)
    print("  1. .claude/skills/adr/scripts/next-id.py", file=sys.stderr)
    print("  2. 새 ADR 저작 — 여전히 유효한 부분은 **재진술**한다 (부분 supersede 없음)", file=sys.stderr)
    print("  3. .claude/skills/adr/scripts/supersede.py --old <옛 id> --by <새 id>", file=sys.stderr)
    sys.exit(1)

print("수정 가능 (공표된 status: %s)" % (pub_status or "없음"))
