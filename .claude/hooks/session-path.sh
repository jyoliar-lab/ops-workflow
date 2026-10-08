#!/bin/sh
# SessionStart — 스킬 scripts/ 디렉터리들을 PATH에 올려 bare-name 실행을 가능하게 한다
# (예: `accept.py ADR-0001`). hook 프로세스 안의 export는 세션에 전파되지 않는다 —
# CLAUDE_ENV_FILE에 쓴 export만 이후 모든 Bash 호출 전에 source된다.
#
# 세션은 harness/<역할>/ 에서 열린다. 그래서 둘을 합친다:
#   - git 루트의 .claude/skills/**/scripts  (공통 스킬)  + .claude/scripts + .claude/hooks
#   - cwd($CLAUDE_PROJECT_DIR)의 .claude/skills/**/scripts  (하네스 전용 스킬)
[ -n "$CLAUDE_ENV_FILE" ] || exit 0
root=$(git -C "${CLAUDE_PROJECT_DIR:-.}" rev-parse --show-toplevel 2>/dev/null) || root="$CLAUDE_PROJECT_DIR"
[ -n "$root" ] || exit 0
dirs=$(find "$root/.claude/skills" -type d -name scripts 2>/dev/null | paste -sd: -)
if [ -n "$CLAUDE_PROJECT_DIR" ] && [ "$CLAUDE_PROJECT_DIR" != "$root" ] && [ -d "$CLAUDE_PROJECT_DIR/.claude/skills" ]; then
  local_dirs=$(find "$CLAUDE_PROJECT_DIR/.claude/skills" -type d -name scripts 2>/dev/null | paste -sd: -)
  [ -n "$local_dirs" ] && dirs="${dirs:+$dirs:}$local_dirs"
fi
[ -d "$root/.claude/scripts" ] && dirs="${dirs:+$dirs:}$root/.claude/scripts"
[ -d "$root/.claude/hooks" ] && dirs="${dirs:+$dirs:}$root/.claude/hooks"
[ -n "$dirs" ] || exit 0
printf 'export PATH="%s:$PATH"\n' "$dirs" >> "$CLAUDE_ENV_FILE"
