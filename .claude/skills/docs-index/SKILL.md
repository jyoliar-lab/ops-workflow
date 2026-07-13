---
name: docs-index
description: docs/ 의 frontmatter를 스캔해 docs/_index/ 를 생성한다 (by-type · by-topic · by-subject · decisions-log). 문서를 추가·변경·accept·supersede 한 뒤에 돌린다. 규약은 CLAUDE.md §7.
---

# 인덱스 생성

> **잠정판(관측 장비).** 고쳤다면 고친 이유를 마찰 로그에 남긴다.

```bash
.claude/skills/docs-index/scripts/build-index.py
```

`docs/_index/` 를 **통째로 다시 만든다.** 판단이 없다 — 순수 기계다.

```
docs/_index/
├── by-type/{adr,discussion,postmortem}.md
├── by-topic/{topic}.md
├── by-subject/{subject}.md    ← topic·type을 가로지르는 정밀 검색의 유일한 수단
└── decisions-log.md           ← accepted ADR만
```

## 언제 돌리나

문서를 **추가·변경**했을 때. 특히 **accept·supersede 직후** — `decisions-log.md`가 바뀐다.

인덱스는 **파생물**이다. 원본은 문서의 frontmatter다. 돌리지 않으면 낡는다(`adr` skill의 `list-subjects.py`가 그 드리프트를 경고한다).

## 손으로 고치지 않는다

`_index/`는 **생성물**이다(§7). 수동 MOC를 만들지 않는다 — drift를 구조적으로 제거하기 위해서다.
인덱스가 틀렸다면 고칠 곳은 인덱스가 아니라 **문서의 frontmatter** 또는 **이 스크립트**다.

## 부산물 — 어휘 목록

`by-subject/`의 파일 목록이 곧 **"지금까지 쓰인 subject 전량"**이다. `adr` skill이 이것을 읽어 사용자에게 제시한다 → **태그 부패 방지 루프가 닫힌다.** 어휘 드리프트가 파일 목록으로 **눈에 보인다.**

## 알려진 한계 (초판)

- **`decisions-log.md`는 `accepted_at` 순으로 정렬한다** (동률·누락 시 id 순). `accepted_at`은 **비권위적 편의 필드**이고 진실 원본은 **git(accept 커밋)**이다(§7) — 그래서 스크립트는 둘이 어긋나면 **경고만** 하고 실패시키지 않는다. 권위 없는 필드를 도구가 강제하면 그건 권위를 준 것이다.
- 스크립트는 **경고만** 하고 실패하지 않는다(필수 필드 누락, `topic` ≠ 폴더명 등). **검증은 린터의 몫**이며 린터는 아직 없다. 인덱스가 게이트 노릇을 하면 dogfood를 막는다.
