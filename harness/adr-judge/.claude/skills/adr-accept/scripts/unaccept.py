#!/usr/bin/env python3
"""공표 **전**의 accept 를 되돌린다 (CLAUDE.md §3).

  unaccept.py ADR-0001

동결은 **공표(push) 시점에 발효한다.** 아직 push 되지 않은 accept 는 아무도 보지 못한 결정이므로
되돌릴 수 있다 — 아무도 못 본 문서를 무를 수 없다고 우기는 것은 규율이 아니라 형식이다.

**공표된 순간 이 스크립트는 거부한다.** 그 뒤로는 supersede 만이 결정을 바꾸는 길이다.

accept.py · supersede.py 와 같은 형태다 — **본문에 손댈 능력이 없는 스크립트.**
status 와 accepted_at 두 필드만 되돌린다.
"""
import os
import re
import sys

import _bootstrap  # noqa: F401 — git 루트의 .claude/skills/_lib 를 sys.path 에 올린다
import vcs  # noqa: E402
from opsdoc import FROZEN, die, find_adr, parse_frontmatter, read_frontmatter, repo_root  # noqa: E402

if len(sys.argv) != 2:
    print("usage: unaccept.py <ADR-NNNN | path>", file=sys.stderr)
    sys.exit(2)
target = sys.argv[1]

root = repo_root()
path = find_adr(root, target) if re.match(r"^ADR-\d{4}$", target) else os.path.abspath(target)
if not os.path.isfile(path):
    die("거부: 파일이 없다 — %s" % target)

rel = os.path.relpath(path, root).replace(os.sep, "/")
fm = read_frontmatter(path)

if fm.get("status") != "accepted":
    die("거부: status 가 '%s' 다. accepted 인 것만 되돌린다." % (fm.get("status") or "없음"))

# ★ 공표됐는가 — 여기가 유일한 관문이다.
vcs.fetch_published(root)
pub = parse_frontmatter(vcs.read_at(root, rel))
if pub and pub.get("status") in FROZEN:
    die("거부: %s 는 이미 **공표됐다** (%s 의 status: %s)" % (target, vcs.PUBLISHED, pub["status"]),
        "  " + rel,
        "",
        "  공표된 결정은 되돌리지 않는다 — 이미 남들이 그것을 근거로 일하고 있을 수 있다.",
        "  바꾸려면 → 새 ADR 을 쓰고 supersede 한다.")

# ── status · accepted_at 만 되돌린다. 본문은 읽지도 쓰지도 않는다. ────────
with open(path, encoding="utf-8") as f:
    lines = f.read().splitlines(keepends=True)

end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
if end is None:
    die("거부: frontmatter 가 닫히지 않았다 — %s" % rel)

head, body = lines[1:end], lines[end:]
out = []
for line in head:
    if re.match(r"^status\s*:", line):
        out.append("status: proposed\n")
    elif re.match(r"^accepted_at\s*:", line):
        out.append("accepted_at:\n")           # accept.py 가 다시 채운다. 손으로 적지 않는다
    else:
        out.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.write(lines[0])
    f.writelines(out)
    f.writelines(body)

print("%s → proposed (공표 전이므로 되돌렸다)" % fm.get("id", rel))
print("  " + rel)
print()
print("본문은 건드리지 않았다. 이제 고칠 수 있다 — 고친 뒤 accept.py 로 다시 얼린다.")
