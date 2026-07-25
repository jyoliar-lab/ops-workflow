#!/bin/sh
# SessionStart — 스킬 scripts/ 디렉터리들을 PATH에 올려 bare-name 실행을 가능하게 한다
# (예: `accept.py ADR-0001`). hook 프로세스 안의 export는 세션에 전파되지 않는다 —
# CLAUDE_ENV_FILE에 쓴 export만 이후 모든 Bash 호출 전에 source된다.
[ -n "$CLAUDE_ENV_FILE" ] || exit 0
dirs=$(find "$CLAUDE_PROJECT_DIR/.claude/skills" -type d -name scripts 2>/dev/null | paste -sd: -)
[ -d "$CLAUDE_PROJECT_DIR/.claude/scripts" ] && dirs="${dirs:+$dirs:}$CLAUDE_PROJECT_DIR/.claude/scripts"
[ -n "$dirs" ] || exit 0
printf 'export PATH="%s:$PATH"\n' "$dirs" >> "$CLAUDE_ENV_FILE"
