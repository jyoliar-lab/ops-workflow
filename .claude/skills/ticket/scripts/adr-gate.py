#!/usr/bin/env python3
"""컨테이너 티켓의 ADR 게이트 (CLAUDE.md §5).

  adr-gate.py --adr ADR-0001 --type epic|feature

컨테이너 티켓(epic·feature)은 **accepted ADR을 전제한다.** 굳지 않은 결정으로 일하지 않는다.
  exit 0 = 통과 · exit 1 = 거부

★ **워킹 트리가 아니라 공표된 사본(origin/main)을 읽는다.**
내 디스크에만 있는 결정은 아무도 볼 수 없다 — 그것을 근거로 티켓을 만들면 티켓의 문서 링크가
**죽은 링크**로 태어난다. "굳었다"는 것은 accept 했다는 뜻만이 아니라 **공표됐다**는 뜻이다.

커밋·푸시는 사람의 행위다(§6). 이 스크립트는 사람에게 커밋을 시키지 않는다 —
**공표되기 전에는 그 결정으로 일을 시작하지 않을 뿐이다.**

출력(통과 시, stdout):
  path=<공표된 사본의 경로>
  sha=<그 시점 origin/main 커밋>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
import vcs  # noqa: E402
from opsdoc import die, iter_docs, parse_frontmatter, repo_root  # noqa: E402

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

if not vcs.fetch_published(root):
    print("경고: %s 를 당기지 못했다 — 로컬에 있는 마지막 사본으로 판단한다." % vcs.PUBLISHED,
          file=sys.stderr)

path = vcs.path_of_id(root, adr_id)

if not path:
    # 워킹 트리에는 있는데 공표되지 않았는가? — 가장 흔한 실패다. 정확히 짚어준다.
    local = [p for p, fm in iter_docs(root)
             if fm.get("type") == "adr" and fm.get("id") == adr_id]
    if local:
        die("거부: %s 이 아직 **공표되지 않았다** — %s 에 없다." % (adr_id, vcs.PUBLISHED),
            "  워킹 트리에는 있다: " + os.path.relpath(local[0], root),
            "",
            "  이 상태로 티켓을 만들면 티켓의 문서 링크가 죽은 링크가 된다.",
            "  결정을 먼저 **커밋·푸시**한다. 공표되지 않은 결정으로 일하지 않는다.")
    die("거부: %s 을 찾지 못했다 (%s · 워킹 트리 양쪽 모두)." % (adr_id, vcs.PUBLISHED),
        "  컨테이너 티켓(%s)은 accepted ADR을 전제한다 — 결정을 먼저 굳힌다." % ticket_type)

fm = parse_frontmatter(vcs.read_at(root, path))
status = fm.get("status", "")

if status != "accepted":
    die("거부: %s 의 status 가 '%s' 다 — accepted 가 아니다." % (adr_id, status or "없음"),
        "  %s:%s" % (vcs.PUBLISHED, path),
        "",
        "  컨테이너 티켓(%s)은 accepted ADR을 전제한다 (CLAUDE.md §5)." % ticket_type,
        "  굳지 않은 결정으로 일하지 않는다. ADR을 먼저 accept 하거나, 리프 티켓(task·bug)으로 발행한다.")

# 워킹 트리가 공표된 사본보다 앞서 있으면 알린다 — 티켓은 **공표된 것**을 근거로 삼는다.
local_path = os.path.join(root, path)
if os.path.isfile(local_path):
    from opsdoc import read_frontmatter  # noqa: E402
    if read_frontmatter(local_path).get("status") != status:
        print("경고: 워킹 트리의 status 가 공표된 것과 다르다 — 티켓은 공표된 사본(%s)을 근거로 삼는다."
              % status, file=sys.stderr)

# "founding / sub" 는 **절대적 구분이 아니다** — parent 에 깊이 제한이 없으므로(§4③),
# 어떤 ADR 이든 다른 ADR 의 하위 축일 수 있다. 그래서 Epic 의 근거 ADR 이 parent 를
# 갖는 것은 **정상**이다. 그것을 이상하다고 경고하지 않는다.
#
# 남는 검사는 하나다: Feature 는 **하위 축의 결정**을 전제하므로 parent 가 있어야 한다.
# 경고까지만 한다 — Feature 의 근거 ADR 이 *그 Epic 의 근거 ADR* 의 하위 축인지까지는
# 아직 확인하지 않는다(티켓 ADR 에서 정한다).
parent = fm.get("parent", "")
if ticket_type == "feature" and not parent:
    print("경고: Feature 의 근거 ADR 에 parent 가 없다 — 하위 축이 아니다.", file=sys.stderr)
    print("      Feature 는 독립 하위 축의 결정을 전제한다. 정말 Feature 인가, Task 면 충분한가?",
          file=sys.stderr)

sha = vcs.ref_sha(root)
print("통과: %s accepted — 공표됨 (%s:%s)" % (adr_id, vcs.PUBLISHED, path), file=sys.stderr)
print("path=%s" % path)
print("sha=%s" % sha)
