#!/usr/bin/env python3
"""ADR 을 accept 한다 — 동결선을 넘는 문 (CLAUDE.md §3).

  accept.py ADR-0001

`proposed` → `accepted` 전이는 (공표된 뒤에는) **되돌릴 수 없는 경계**다. 넘고 나면
본문(결정의 의미)이 얼어붙어, 그것을 고쳐 결정을 바꾸려면 새 ADR 로 supersede 한다(ADR-0006).
*경로·포맷은 얼지 않고, 분류(topic·subjects)·생명주기 필드도 얼음 밖이다(ADR-0004).*

그래서 이 전이도 사람 손이 아니라 기계가 한다. supersede.py 와 같은 형태다 —
**본문에 손댈 능력이 없는 스크립트.** 동결 게이트를 넘는 문이 전부 기계라야,
동결이 규율이 아니라 구조가 된다.

넘기 전에 두 가지를 강제한다:
  1. 파일명이 규약(소문자 kebab·3~6단어)에 맞는가 — accept 는 좋은 이름을 확인하는 관문이다
  2. status 가 정말 proposed 인가

`accepted_at` 은 여기서 채운다 — *"검토가 언제 끝났는가"*. **권위 있는 필드**이므로
**사람이 손으로 적지 않는다**: 틀리면 문서가 거짓말을 하고, 대조할 바깥이 없다.
**동결 시각이 아니다** — 동결은 공표(push) 시점에 발효하며, 그것은 저장소의 사실이다.
"""
import datetime
import os
import re
import sys

import _bootstrap  # noqa: F401 — git 루트의 .claude/skills/_lib 를 sys.path 에 올린다
from opsdoc import die, filename_problem, find_adr, read_frontmatter, repo_root  # noqa: E402

if len(sys.argv) != 2:
    print("usage: accept.py <ADR-NNNN | path>", file=sys.stderr)
    sys.exit(2)
target = sys.argv[1]

root = repo_root()
path = find_adr(root, target) if re.match(r"^ADR-\d{4}$", target) else os.path.abspath(target)
if not os.path.isfile(path):
    die("거부: 파일이 없다 — %s" % target)

fm = read_frontmatter(path)
rel = os.path.relpath(path, root)

if fm.get("type") != "adr":
    die("거부: adr 문서가 아니다 (type: %s)" % (fm.get("type") or "없음"),
        "  postmortem 을 frozen 으로 바꾸는 스크립트는 아직 없다 — 미결이다(마찰 로그).")

status = fm.get("status", "")
if status == "accepted":
    die("거부: %s 는 이미 accepted 다 — 이미 동결선을 넘었다." % rel)
if status in ("superseded", "rejected"):
    die("거부: status 가 '%s' 다. 죽은 결정을 되살리지 않는다 — 새 ADR 을 쓴다." % status)
if status != "proposed":
    die("거부: status 가 '%s' 다. accept 는 proposed 에서만 넘어간다." % (status or "없음"))

# 파일명 규약을 accept 관문에서 확인한다. 경로는 얼지 않아 나중에 rename 도 되지만(ADR-0006),
# 확정 시점에 규약을 맞춰 두는 편이 낫다.
problem = filename_problem(path, fm)
if problem:
    die("거부: " + problem,
        "  " + rel,
        "",
        "  파일명 규약(소문자 kebab·3~6단어)에 맞춘 뒤 다시 accept 한다.")

# 초 단위 + 오프셋. 날짜만 쓰면 **같은 날 여러 건을 accept할 때 순서가 사라지고**,
# decisions-log 는 id 순(= 저작 순)으로 되돌아간다 — 이 필드를 둔 이유가 없어진다.
accepted_at = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

# ── frontmatter 두 필드만 수정. 본문은 읽지도 쓰지도 않는다. ──────────────
with open(path, encoding="utf-8") as f:
    lines = f.read().splitlines(keepends=True)

end = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
if end is None:
    die("거부: frontmatter 가 닫히지 않았다 — %s" % rel)

head, body = lines[1:end], lines[end:]
out, saw_accepted_at = [], False
for line in head:
    if re.match(r"^status\s*:", line):
        out.append("status: accepted\n")
    elif re.match(r"^accepted_at\s*:", line):
        out.append("accepted_at: %s\n" % accepted_at)
        saw_accepted_at = True
    else:
        out.append(line)
if not saw_accepted_at:
    # status 바로 뒤에 놓는다 — 둘은 함께 움직이는 필드다.
    at = next((i for i, line in enumerate(out) if line.startswith("status:")), len(out) - 1)
    out.insert(at + 1, "accepted_at: %s\n" % accepted_at)

with open(path, "w", encoding="utf-8") as f:
    f.write(lines[0])
    f.writelines(out)
    f.writelines(body)

print("%s → accepted (accepted_at: %s)" % (fm.get("id", rel), accepted_at))
print("  " + rel)
print()
print("★ 여기서부터 본문(결정의 의미)이 얼어붙는다. 바꾸려면 새 ADR 로 supersede.py.")
print("  경로·포맷·분류(topic·subjects)는 얼음 밖 — 문서 관리는 계속 개선할 수 있다.")
print()
print("다음: 이 변경을 커밋하고 push 한다 — **동결은 공표 시점에 발효한다.**")
print("      (인덱스는 hook 이 자동 재생성한다 — decisions-log 가 바뀐다.)")
