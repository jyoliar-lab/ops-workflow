#!/usr/bin/env python3
"""ADR 전역 순차번호 발급 (CLAUDE.md §7).

docs/ 전량 스캔 → max+1. 같은 id 가 두 번 나오면 **거부한다** —
전역 유일성이 깨진 채로 번호를 더 발급하지 않는다.

문서 0건 → ADR-0001. 콜드스타트는 에러가 아니다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import die, iter_docs, repo_root  # noqa: E402

root = repo_root()

seen = {}
for path, fm in iter_docs(root):
    if fm.get("type") != "adr":
        continue
    adr_id = fm.get("id")
    if adr_id:
        seen.setdefault(adr_id, []).append(os.path.relpath(path, root))

dupes = {k: v for k, v in seen.items() if len(v) > 1}
if dupes:
    lines = []
    for adr_id, paths in sorted(dupes.items()):
        lines.append("  %s:" % adr_id)
        lines += ["    " + p for p in paths]
    die("거부: ADR id 가 중복됐다 — 전역 순차가 깨졌다.", *lines,
        "중복을 먼저 해소한다. 번호를 더 발급하지 않는다.")

numbers = [int(k.split("-")[1]) for k in seen if k.startswith("ADR-") and k.split("-")[1].isdigit()]
print("ADR-%04d" % (max(numbers) + 1 if numbers else 1))
