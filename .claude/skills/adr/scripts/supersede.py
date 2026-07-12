#!/usr/bin/env python3
"""옛 ADR을 supersede 한다 (CLAUDE.md §3).

  supersede.py --old ADR-0001 --by ADR-0007

동결된 문서에 허용되는 편집은 **status · superseded_by 두 필드뿐**이다.
그 둘을 사람 손이 아니라 이 스크립트가 한다 — **본문에 손댈 방법이 없는 것**이
동결을 규율이 아니라 구조로 만든다. (freeze-check.py 는 본문 수정을 거부하고,
이 스크립트는 frontmatter 두 줄 말고는 아무것도 건드리지 않는다.)

부분 supersede 는 없다 — 옛 ADR **전체**가 superseded 가 된다.
여전히 유효한 부분은 새 ADR에 **재진술**한다. 재진술 여부는 이 스크립트가 검사할 수 없다(사람 판단).
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import die, find_adr, read_frontmatter, repo_root  # noqa: E402

args = sys.argv[1:]
if len(args) != 4 or args[0] != "--old" or args[2] != "--by":
    print("usage: supersede.py --old ADR-NNNN --by ADR-NNNN", file=sys.stderr)
    sys.exit(2)
old_id, new_id = args[1], args[3]
if old_id == new_id:
    die("거부: 자기 자신을 supersede 할 수 없다.")

root = repo_root()
old_path = find_adr(root, old_id)
new_path = find_adr(root, new_id)
old_fm = read_frontmatter(old_path)
new_fm = read_frontmatter(new_path)

# 옛 ADR — 뒤집을 것이 있으려면 accepted 여야 한다.
old_status = old_fm.get("status", "")
if old_status == "superseded":
    die("거부: %s 는 이미 superseded 다 (superseded_by: %s)"
        % (old_id, old_fm.get("superseded_by") or "?"))
if old_status != "accepted":
    die("거부: %s 의 status 가 '%s' 다. accepted 인 결정만 supersede 한다." % (old_id, old_status or "없음"),
        "  (proposed 라면 그냥 고치거나 rejected 로 닫는다 — 동결선을 넘지 않았다.)")

# 새 ADR — 굳지 않은 결정으로 옛 결정을 무효화하지 않는다.
new_status = new_fm.get("status", "")
if new_status != "accepted":
    die("거부: %s 의 status 가 '%s' 다. accepted 인 새 ADR만 옛 ADR을 대체한다."
        % (new_id, new_status or "없음"),
        "  먼저 새 ADR을 accept 한다.")

# ── frontmatter 두 필드만 수정. 본문은 읽지도 쓰지도 않는다. ──────────────
with open(old_path, encoding="utf-8") as f:
    lines = f.read().splitlines(keepends=True)

end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
if end is None:
    die("거부: frontmatter 가 닫히지 않았다 — %s" % old_path)

head, body = lines[1:end], lines[end:]
out, saw_superseded_by = [], False
for line in head:
    if re.match(r"^status\s*:", line):
        out.append("status: superseded\n")
    elif re.match(r"^superseded_by\s*:", line):
        out.append("superseded_by: %s\n" % new_id)
        saw_superseded_by = True
    else:
        out.append(line)
if not saw_superseded_by:
    out.append("superseded_by: %s\n" % new_id)

with open(old_path, "w", encoding="utf-8") as f:
    f.write(lines[0])
    f.writelines(out)
    f.writelines(body)

print("%s → superseded (by %s)" % (old_id, new_id))
print("  " + os.path.relpath(old_path, root))
print()
print("본문은 건드리지 않았다. 옛 ADR에서 여전히 유효한 부분이 있다면 %s 안에 **재진술**돼 있어야 한다"
      " — 부분 supersede 는 없다." % new_id)
print("인덱스를 다시 만든다 → docs-index skill (decisions-log 가 바뀐다).")
