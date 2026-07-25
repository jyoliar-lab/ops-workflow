#!/usr/bin/env python3
"""PostToolUse — docs/** 를 고쳤으면 _index/ 를 자동 재생성한다.

"문서를 바꾼 뒤 반드시 `_index/`를 재생성한다"(CLAUDE.md §7)를 기억(산문)이 아니라
구조(hook)로 강제한다 — §8. 잊는 것이 불가능해진다.

- docs/** 안의 Write/Edit/MultiEdit           → 재생성
- Bash 로 accept/unaccept/supersede.py 실행   → 재생성 (frontmatter 를 바꾸는 스크립트들)
- docs/** 밖 · docs/_index/** (생성물 자신)   → 무시
- build-index.py 실패                         → 세션을 막지 않는다(비차단). stderr 한 줄만
                                                남긴다. 수동 재생성은 사람의 /docs-index 커맨드.

★ build-index.py 의 repo_root() 는 cwd 에서 .git 을 찾는다 — 반드시
  cwd=$CLAUDE_PROJECT_DIR 로 실행한다.
"""
import json
import os
import re
import subprocess
import sys


def norm(p):
    return os.path.realpath(os.path.abspath(p))


def under(path, root):
    root = norm(root)
    path = norm(path)
    return path == root or path.startswith(root + os.sep)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if not proj:
        sys.exit(0)

    if tool == "Bash":
        # frontmatter 를 바꾸는 스킬 스크립트가 돌았으면 인덱스도 낡았다
        cmd = tool_input.get("command", "") or ""
        if not re.search(r"\b(accept|unaccept|supersede)\.py\b", cmd):
            sys.exit(0)
    elif tool in ("Write", "Edit", "MultiEdit"):
        fp = tool_input.get("file_path")
        if not fp:
            sys.exit(0)
        docs = os.path.join(proj, "docs")
        if not under(fp, docs) or under(fp, os.path.join(docs, "_index")):
            sys.exit(0)
    else:
        sys.exit(0)

    script = os.path.join(proj, ".claude", "scripts", "build-index.py")
    try:
        r = subprocess.run([sys.executable, script], cwd=proj,
                           capture_output=True, text=True, timeout=60)
        ok, detail = r.returncode == 0, (r.stderr or r.stdout or "")
    except Exception as e:
        ok, detail = False, str(e)

    if not ok:
        sys.stderr.write("reindex-docs: build-index.py 실패(비차단) — "
                         "사람에게 알려 /docs-index 로 재생성하게 하라.\n")
        sys.stderr.write(detail.strip()[-500:] + "\n")
        sys.exit(1)  # 비차단 알림 — 세션은 계속된다
    sys.exit(0)


if __name__ == "__main__":
    main()
