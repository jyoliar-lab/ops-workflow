#!/usr/bin/env python3
"""동결 사전 검사 (ADR-0006).

  freeze-check.py <path>    본문을 고치기 전에 돌린다 — exit 0 = 통과 · exit 1 = 거부

★ **판정 기준은 공표된 사본(origin/main)이다. 워킹 트리가 아니다.**
동결은 **공표 시점에 발효한다** — 아직 push 되지 않은 상태 변화는 아무도 보지 못한 것이므로
되돌릴 수 있다. **동결은 시각이 아니라 상태이고, 그 상태는 "공표됐는가" 하나로 판정된다.**

**얼어붙는 것은 본문 — 결정의 의미다.** 경로도 포맷도 얼지 않는다(그릇은 결정이 아니다) —
파일을 옮기거나 이름을 바꾸는 것은 이 검사의 관심사가 아니다. 참조는 경로가 아니라 id 로 걸린다.
그리고 **분류 메타데이터(topic·subjects)와 생명주기 필드도 얼음 밖이다**(ADR-0004). 이 검사가
막는 것은 오직 **얼어붙은 본문(과 id·type·parent·references)을 고쳐 결정을 바꾸는 것**이다.

동결 상태(본문이 언 상태): adr = accepted|rejected|superseded · postmortem = frozen
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
import vcs  # noqa: E402
from opsdoc import FROZEN, parse_frontmatter, read_frontmatter, repo_root  # noqa: E402

root = repo_root()


def published(path):
    """공표된 사본의 frontmatter. 아직 공표되지 않았으면 None."""
    rel = os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/")
    text = vcs.read_at(root, rel)
    return parse_frontmatter(text) if text else None


if len(sys.argv) != 2:
    print("usage: freeze-check.py <path-to-doc>", file=sys.stderr)
    sys.exit(2)
path = sys.argv[1]

vcs.fetch_published(root)     # 실패해도 죽지 않는다 — 로컬의 마지막 사본으로 판단한다

if not os.path.isfile(path):
    print("신규 파일 — 동결 아님")            # 콜드스타트. 에러가 아니다.
    sys.exit(0)

pub = published(path)
local_status = read_frontmatter(path).get("status", "")

if pub is None:
    # 아직 공표되지 않았다 → 얼지 않았다. 로컬에서 확정했더라도 되돌릴 수 있다.
    if local_status in FROZEN:
        print("수정 가능 — 아직 공표되지 않았다 (로컬 status: %s)" % local_status)
        print("  push 하는 순간 본문이 얼어붙는다. 고칠 것이 있으면 지금이다.")
    else:
        print("수정 가능 (status: %s)" % (local_status or "없음"))
    sys.exit(0)

pub_status = pub.get("status", "")

if pub_status in FROZEN:
    print("거부: 공표된 동결 문서다 (status: %s)" % pub_status, file=sys.stderr)
    print("  " + path, file=sys.stderr)
    print("", file=sys.stderr)
    print("얼어붙은 것은 **본문(결정의 의미)** 과 id·type·parent·references 다 — 이를 고쳐 결정을 바꿀 수 없다.",
          file=sys.stderr)
    print("얼음 밖(고쳐도 된다): topic·subjects(분류) · status·superseded_by(생명주기) · 파일 경로·포맷.",
          file=sys.stderr)
    print("", file=sys.stderr)
    print("결정을 바꾸려면 → 새 ADR 을 쓰고 supersede 한다:", file=sys.stderr)
    print("  1. .claude/skills/adr/scripts/next-id.py", file=sys.stderr)
    print("  2. 새 ADR 저작 — 여전히 유효한 부분은 **재진술**한다 (부분 supersede 없음)", file=sys.stderr)
    print("  3. .claude/skills/adr/scripts/supersede.py --old <옛 id> --by <새 id>", file=sys.stderr)
    sys.exit(1)

print("수정 가능 (공표된 status: %s)" % (pub_status or "없음"))
