#!/usr/bin/env python3
"""PreToolUse guard — 쓰기 경계와 사람의 자리(close·커밋 승인)를 구조로 강제한다.

CLAUDE.md 의 산문 규칙 중 구조로 옮길 수 있는 것을 여기서 강제한다 —
§8("규율이 아니라 구조")대로.

Write/Edit/MultiEdit:
  허용 — $CLAUDE_PROJECT_DIR/**       (이 저장소: docs/ · .claude/ · CLAUDE.md
                                       · staging/ — 하네스 마찰 로그 인박스. §6)
  거부 — docs/_index/**               (생성물 — 도구만 쓴다. §7. 재생성은 hook 자동)
  거부 — workspace/**                 (참조 저장소 로컬 클론 — agent 는 **읽고
         인용할 뿐** 고치지 않는다(§6). 코드 변경은 그 저장소의 PR 로, 사람이 한다)
  거부 — 그 외 전부(이 저장소 밖). OS 임시 디렉터리도 밖이다 — 티켓 본문 등
         일회용 초안은 temp-tickets/ (gitignored)에 쓴다.

Bash:
  거부 — `gh issue close`             (close 는 언제나 사람 — §5)
  확인 — `git commit` · `git push`    (무인 write 금지 — §6. 사람 승인을 묻는다)

경계는 $CLAUDE_PROJECT_DIR 로 동적이다(하드코딩 없음) — Claude Code 권한 패턴이
env 확장을 못 하므로 이 hook 가 대신 강제한다.
"""
import os
import re
import sys
import json
import tempfile


def out_decision(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


def out_deny(reason):
    out_decision("deny", reason)


def out_ask(reason):
    out_decision("ask", reason)


def allow():
    sys.exit(0)


def norm(p):
    return os.path.realpath(os.path.abspath(p))


def under(path, root):
    if not root:
        return False
    root = norm(root)
    path = norm(path)
    return path == root or path.startswith(root + os.sep)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        allow()  # 입력 파싱 불가 → 가드 불가. 세션을 브릭하지 않는다(fail-open).

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}

    if tool == "Bash":
        cmd = tool_input.get("command", "") or ""
        if re.search(r"\bgh\s+issue\s+close\b", cmd) or (
            re.search(r"\bgh\s+api\b", cmd)
            and re.search(r"(?:-[fF]|--field|--raw-field)[ =]+['\"]?state=closed", cmd)
        ):
            out_deny("close 는 언제나 사람이 한다(CLAUDE.md §5) — PR 머지 ≠ 티켓 종료, "
                     "그 사이에 사람의 검수가 산다. agent 는 코멘트까지만 남긴다.")
        if re.search(r"\bgit\s+(commit|push)\b", cmd):
            out_ask("무인 write 금지(CLAUDE.md §6) — 지식 플레인의 최종 저자는 사람이다. "
                    "커밋·push 는 사람이 이 프롬프트로 승인할 때만 실행된다.")
        allow()

    if tool not in ("Write", "Edit", "MultiEdit"):
        allow()

    fp = tool_input.get("file_path")
    if not fp:
        allow()

    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if not proj:
        allow()  # 경계를 모르면 가드 불가. hook 부재와 같은 상태로 둔다.

    if under(fp, os.path.join(proj, "docs", "_index")):
        out_deny("docs/_index/ 는 생성물이다(CLAUDE.md §7) — 손으로 고치지 않는다. "
                 "고칠 곳은 원본 문서의 frontmatter 이고, 재생성은 도구가 한다(hook 자동).")

    if under(fp, os.path.join(proj, "workspace")):
        out_deny(
            "참조 저장소는 read only 다(CLAUDE.md §6): %s — workspace/ref 는 코드를 "
            "읽고 인용하기 위한 로컬 클론이다(이 저장소에 코드는 없다 — §1). "
            "코드를 읽고 결정의 '왜'를 여기 문서로 남기되, 코드 자체는 고치지 않는다. "
            "변경이 필요하면 티켓으로 남기고, 그 저장소의 PR 로 사람이 한다." % fp
        )

    if under(fp, proj):
        allow()

    tmp_roots = {tempfile.gettempdir(), "/tmp", "/private/tmp", "/var/folders"}
    if any(under(fp, t) for t in tmp_roots):
        out_deny(
            "OS 임시 디렉터리에 쓰지 않는다: %s — 티켓 본문 등 일회용 초안은 저장소의 "
            "temp-tickets/ 에 쓴다(gitignored). 사람이 초안을 볼 수 있는 자리다." % fp
        )

    out_deny(
        "쓰기 경계 위반: %s — 이 하네스는 $CLAUDE_PROJECT_DIR(%s) 안에만 쓴다. "
        "바깥 저장소는 읽기 전용이다." % (fp, proj)
    )


if __name__ == "__main__":
    main()
