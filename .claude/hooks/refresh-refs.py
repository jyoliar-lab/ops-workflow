#!/usr/bin/env python3
"""SessionStart hook — 참조 저장소(workspace/ref)를 목록대로 최신화한다.

ticket-engineer 의 refresh-refs 와 같은 패턴이되, 방향이 다르다 — 저쪽은
티켓이 저장소를 지목하고 hook 는 있는 것만 최신화하지만, 여기는 **목록이
먼저다**: 필요한 참조 저장소를 `.claude/ref-repos.txt` 가 미리 정의한다.
  - 목록의 저장소가 없으면 clone 한다.
  - 있으면 ff-only pull 로 최신화한다.
  - ref 에 있는데 목록에 없는 디렉터리는 경고만 한다(지우지 않는다 — 사람 몫).
ref 는 읽기 전용 참조다(CLAUDE.md §6) — 쓰기는 guard-write hook 가 거부한다.
실패는 경고만 한다 — 세션을 막지 않는다(fail-open).
"""
import os
import subprocess
import sys

LIST_REL = os.path.join(".claude", "ref-repos.txt")


def warn(msg):
    print(msg, file=sys.stderr)


def load_urls(path):
    urls = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    except OSError as e:
        warn("경고: 참조 목록(%s)을 읽지 못했다 — %s" % (LIST_REL, e))
    return urls


def repo_name(url):
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name[:-4] if name.endswith(".git") else name


def project_root():
    """hook 컨텍스트에서는 CLAUDE_PROJECT_DIR, 수동 실행에서는 스크립트 위치로 역산.

    이 스크립트는 <프로젝트>/.claude/hooks/ 에 산다 — cwd 와 무관하게 루트를 찾는다.
    둘 다 실패하면 무음 no-op 이 아니라 경고를 낸다(수동 실행의 무음 실패 방지).
    """
    base = os.environ.get("CLAUDE_PROJECT_DIR")
    if base:
        # CLAUDE_PROJECT_DIR 은 세션을 연 디렉터리(harness/<역할>/)라 루트가 아닐 수 있다 — git 으로 역산
        r = subprocess.run(["git", "-C", base, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    guess = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.isfile(os.path.join(guess, LIST_REL)):
        return guess
    warn("경고: CLAUDE_PROJECT_DIR 없음, 스크립트 위치(%s)에서도 %s 를 찾지 못했다 "
         "— 아무것도 하지 않는다." % (guess, LIST_REL))
    return None


def main():
    proj = project_root()
    if not proj:
        return
    ref = os.path.join(proj, "workspace", "ref")
    os.makedirs(ref, exist_ok=True)

    listed = set()
    for url in load_urls(os.path.join(proj, LIST_REL)):
        name = repo_name(url)
        listed.add(name)
        dest = os.path.join(ref, name)
        if not os.path.isdir(os.path.join(dest, ".git")):
            r = subprocess.run(["git", "clone", url, dest],
                               capture_output=True, text=True)
            if r.returncode != 0:
                warn("경고: ref/%s clone 실패 — %s" % (name, r.stderr.strip()))
            continue
        subprocess.run(["git", "-C", dest, "fetch", "--prune"],
                       capture_output=True, text=True)
        r = subprocess.run(["git", "-C", dest, "pull", "--ff-only"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            warn("경고: ref/%s ff-pull 실패 — 로컬 변경/분기가 있다"
                 "(읽기 전용이어야 할 클론이다). 사람에게 알려라." % name)

    for name in sorted(os.listdir(ref)):
        if name not in listed and os.path.isdir(os.path.join(ref, name, ".git")):
            warn("경고: ref/%s 는 목록(%s)에 없다 — 필요하면 목록에 올리고, "
                 "아니면 지운다(사람 몫)." % (name, LIST_REL))


if __name__ == "__main__":
    main()
    sys.exit(0)   # 어떤 경우에도 세션을 막지 않는다
