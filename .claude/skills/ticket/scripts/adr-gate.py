#!/usr/bin/env python3
"""티켓의 ADR 게이트 (CLAUDE.md §5).

  adr-gate.py --adr ADR-0001 --type epic|feature|task|bug

Epic 티켓은 **accepted ADR을 전제한다.** 굳지 않은 결정으로 일하지 않는다.
Feature·리프(task·bug)는 근거를 전제하지 않는다 — 그러나 **명시했다면 같은 검사를 지난다**:
답하지 않아도 되지만, 답하면 참이어야 한다(accepted·공표).
  exit 0 = 통과 · exit 1 = 거부

★ **워킹 트리가 아니라 공표된 사본(origin/main)을 읽는다.**
내 디스크에만 있는 결정은 아무도 볼 수 없다 — 그것을 근거로 티켓을 만들면 티켓의 문서 링크가
**죽은 링크**로 태어난다. "굳었다"는 것은 accept 했다는 뜻만이 아니라 **공표됐다**는 뜻이다.

커밋·푸시는 사람의 행위다(§6). 이 스크립트는 사람에게 커밋을 시키지 않는다 —
**공표되기 전에는 그 결정으로 일을 시작하지 않을 뿐이다.**

출력(통과 시, stdout):
  path=<공표된 사본의 경로>
  sha=<그 시점 origin/main 커밋>
  title=<공표된 사본 H1 의 제목 문장 (id 접두어 제외 · 없으면 빈 값)>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
import vcs  # noqa: E402
from opsdoc import die, iter_docs, parse_frontmatter, repo_root  # noqa: E402

args = sys.argv[1:]
if len(args) != 4 or args[0] != "--adr" or args[2] != "--type":
    print("usage: adr-gate.py --adr ADR-NNNN --type epic|feature|task|bug", file=sys.stderr)
    sys.exit(2)
adr_id, ticket_type = args[1], args[3]

if ticket_type not in ("epic", "feature", "task", "bug"):
    print("거부: 모르는 티켓 타입이다 — %s" % ticket_type, file=sys.stderr)
    sys.exit(2)

adr_required = ticket_type == "epic"
# 검사 내용은 같다 — 다른 것은 전제의 강도다:
#   Epic: 근거가 필수다(전제).  Feature·리프: 선택이지만, 답했으면 참이어야 한다.
premise = "Epic 티켓은 accepted ADR을 전제한다" if adr_required \
    else ("%s 의 근거는 선택이지만, 명시한 근거는 accepted·공표여야 한다" % ticket_type)

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
        "  %s — 결정을 먼저 굳힌다." % premise)

published = vcs.read_at(root, path)
fm = parse_frontmatter(published)
status = fm.get("status", "")

# 제목 — H1("# ADR-NNNN — <제목 문장>")에서 뽑는다. id 는 따로 다니므로 접두어는 벗긴다.
title = ""
for line in published.splitlines():
    if line.startswith("# "):
        title = line[2:].strip()
        prefix = "%s —" % adr_id
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
        break

if status != "accepted":
    die("거부: %s 의 status 가 '%s' 다 — accepted 가 아니다." % (adr_id, status or "없음"),
        "  %s:%s" % (vcs.PUBLISHED, path),
        "",
        "  %s (CLAUDE.md §5). 굳지 않은 결정으로 일하지 않는다." % premise,
        "  ADR을 먼저 accept 하거나, " + ("--adr 없이 Feature/리프로 발행한다."
                                    if adr_required else "--adr 없이 발행한다."))

# 워킹 트리가 공표된 사본보다 앞서 있으면 알린다 — 티켓은 **공표된 것**을 근거로 삼는다.
local_path = os.path.join(root, path)
if os.path.isfile(local_path):
    from opsdoc import read_frontmatter  # noqa: E402
    if read_frontmatter(local_path).get("status") != status:
        print("경고: 워킹 트리의 status 가 공표된 것과 다르다 — 티켓은 공표된 사본(%s)을 근거로 삼는다."
              % status, file=sys.stderr)

# "founding / sub" 는 **절대적 구분이 아니다** — parent 에 깊이 제한이 없으므로(§4③),
# 어떤 ADR 이든 다른 ADR 의 하위 축일 수 있다. 그래서 근거 ADR 이 parent 를
# 갖는 것도 안 갖는 것도 **정상**이다. 그것을 이상하다고 경고하지 않는다.
# (Feature 의 "하위 축 ADR" 경고는 제거됐다 — Feature 는 근거 없이도 리프를 묶는
#  그룹화 컨테이너가 되면서, "하위 축의 결정을 전제한다"는 독트린 자체가 내려갔다.)

sha = vcs.ref_sha(root)
print("통과: %s accepted — 공표됨 (%s:%s)" % (adr_id, vcs.PUBLISHED, path), file=sys.stderr)
print("path=%s" % path)
print("sha=%s" % sha)
print("title=%s" % title)
