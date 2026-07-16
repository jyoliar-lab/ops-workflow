#!/usr/bin/env python3
"""PreToolUse guard — 이 저장소 밖의 Write/Edit/MultiEdit 를 거부한다.

CLAUDE.md §6 은 agent 의 코드 저장소 권한을 **read only** 로 규정한다. 그러나 산문은
강제하지 않는다 — §8("규율이 아니라 구조")대로 여기서 구조가 거부한다.

허용:
  - $CLAUDE_PROJECT_DIR/**   (이 저장소: docs/ · .claude/ · CLAUDE.md)

거부:
  - 그 외 전부. 특히 $CODE_ROOT 이하의 코드 저장소 — agent 는 **읽고 인용할 뿐**
    고치지 않는다. 코드 변경은 그 저장소의 PR 로, 사람이 한다.

경계는 $CLAUDE_PROJECT_DIR 로 동적이다(하드코딩 없음) — Claude Code 권한 패턴이
env 확장을 못 하므로 이 hook 가 대신 강제한다.
"""
import os
import sys
import json


def out_deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


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

    if data.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        allow()

    fp = (data.get("tool_input") or {}).get("file_path")
    if not fp:
        allow()

    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if not proj:
        allow()  # 경계를 모르면 가드 불가. hook 부재와 같은 상태로 둔다.

    if under(fp, proj):
        allow()

    code_root = os.environ.get("CODE_ROOT")
    if under(fp, code_root):
        out_deny(
            "코드 저장소는 read only 다(CLAUDE.md §6): %s — 이 저장소에 코드는 없다(§1). "
            "코드를 읽고 결정의 '왜'를 여기 문서로 남기되, 코드 자체는 고치지 않는다. "
            "변경이 필요하면 티켓으로 남기고, 그 저장소의 PR 로 사람이 한다." % fp
        )

    out_deny(
        "쓰기 경계 위반: %s — 이 하네스는 $CLAUDE_PROJECT_DIR(%s) 안에만 쓴다. "
        "바깥 저장소는 읽기 전용이다." % (fp, proj)
    )


if __name__ == "__main__":
    main()
