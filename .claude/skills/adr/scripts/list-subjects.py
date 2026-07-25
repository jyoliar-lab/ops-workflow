#!/usr/bin/env python3
"""이미 쓰인 subjects 어휘를 보여준다 (CLAUDE.md §7 — 태그 부패 방지).

이 스크립트는 값을 **고르지 않는다. 보여주고 사람이 고르게 한다.**
자동 추론(본문 키워드 추출 등)을 하면 어휘는 반드시 범용어로 흐른다(`architecture`·`performance`).
이건 관측 장비가 아니라 영구 규율이므로, 확정 skill 에서도 계속 묻는다.

원본은 문서의 frontmatter 다. `docs/_index/by-subject/` 는 그 파생물이며 인덱스 skill 을
돌려야 갱신되므로 **낡을 수 있다** → 둘이 어긋나면 감추지 않고 경고한다.

문서 0건 → 빈 목록. 에러가 아니라 정상 경로다(콜드스타트).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import as_list, iter_docs, repo_root  # noqa: E402

root = repo_root()
live = {s for _, fm in iter_docs(root) for s in as_list(fm.get("subjects"))}

if not live:
    print("기존 subject 없음 — 이 문서가 어휘의 씨앗이 된다.")
    print('판별 기준: "이것이 시스템에 실제로 존재하는가?"  (범주는 subject 가 아니다)')
    sys.exit(0)

print("이미 쓰인 subjects (%d):" % len(live))
for s in sorted(live):
    print("  - " + s)
print()
print('이 중에서 고른다. 새 값을 만들려면 먼저 답한다: "이것이 시스템에 실제로 존재하는가?"')

# 인덱스 드리프트 — 파생물이 원본과 다르면 알린다.
by_subject = os.path.join(root, "docs", "_index", "by-subject")
if os.path.isdir(by_subject):
    indexed = {f[:-3] for f in os.listdir(by_subject) if f.endswith(".md")}
    if indexed != live:
        print(file=sys.stderr)
        print("경고: _index/by-subject/ 가 문서와 어긋난다 — 인덱스가 낡았다.", file=sys.stderr)
        if live - indexed:
            print("  인덱스에 없음: " + ", ".join(sorted(live - indexed)), file=sys.stderr)
        if indexed - live:
            print("  문서에 없음:   " + ", ".join(sorted(indexed - live)), file=sys.stderr)
        print("  → 인덱스가 낡았다. 보통은 hook 이 자동 재생성한다 — 계속 어긋나면"
              " 사람에게 /docs-index 재생성을 요청한다.", file=sys.stderr)
