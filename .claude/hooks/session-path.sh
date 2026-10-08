#!/bin/sh
# SessionStart — 스킬 scripts/ 디렉터리들을 PATH에 올려 bare-name 실행을 가능하게 한다
# (예: `accept.py ADR-0001`). hook 프로세스 안의 export는 세션에 전파되지 않는다 —
# CLAUDE_ENV_FILE에 쓴 export만 이후 모든 Bash 호출 전에 source된다.
#
# 세션은 저장소 루트에서 열리고 역할은 `claude --add-dir harness/<역할>` 로 덧붙는다(README).
# hook 은 어느 역할이 덧붙었는지 모르므로 루트 + 모든 하네스의 scripts 를 올린다 —
# PATH 는 경계가 아니다. 경계는 역할 프롬프트와 권한이다.
[ -n "$CLAUDE_ENV_FILE" ] || exit 0
root=$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --show-toplevel 2>/dev/null) || root="$CLAUDE_PROJECT_DIR"
[ -n "$root" ] || exit 0
dirs=$(find "$root/.claude/skills" "$root"/harness/*/.claude/skills -type d -name scripts 2>/dev/null | paste -sd: -)
[ -d "$root/.claude/scripts" ] && dirs="${dirs:+$dirs:}$root/.claude/scripts"
[ -d "$root/.claude/hooks" ] && dirs="${dirs:+$dirs:}$root/.claude/hooks"
[ -n "$dirs" ] || exit 0
printf 'export PATH="%s:$PATH"\n' "$dirs" >> "$CLAUDE_ENV_FILE"
