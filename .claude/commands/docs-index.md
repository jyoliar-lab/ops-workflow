---
description: docs/ frontmatter 스캔 → docs/_index/ 재생성. 사람 전용 — 보통은 PostToolUse hook이 자동으로 돌리므로, 이 커맨드는 hook 사각지대(에디터 직접 편집·git 병합·mv·hook 실패) 이후에 쓴다.
disable-model-invocation: true
allowed-tools: Bash(build-index.py:*), Bash(python3 .claude/scripts/build-index.py:*)
---

인덱스 재생성 결과:

!`python3 "$CLAUDE_PROJECT_DIR/.claude/scripts/build-index.py"`

위 출력에 경고가 있으면 요약해 보여준다. 경고가 없으면 "재생성 완료"만 짧게 알린다.
`docs/_index/`는 생성물이다 — 결과가 이상해도 인덱스 파일을 직접 고치지 않는다(원본 문서의 frontmatter 또는 스크립트를 고친다).
