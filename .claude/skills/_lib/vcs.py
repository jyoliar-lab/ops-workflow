"""git 조회 공용 모듈. 표준 라이브러리(subprocess)만 쓴다.

**`accepted_at` 의 진실 원본은 git 이다** (CLAUDE.md §7). frontmatter 의 `accepted_at` 은
읽기 편하라고 둔 **비권위적 편의 필드**이며, git 과 어긋나면 **git 이 이긴다.**

그래서 여기 있는 함수는 전부 **읽기**다. git 을 근거로 문서를 고치지 않는다 —
어긋남은 경고로 드러내고, 판단은 사람이 한다. 권위 없는 필드를 도구가 강제하면 그건 권위를 준 것이다.
"""
import subprocess


def _git(root, *args):
    p = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True)
    if p.returncode != 0:
        return ""                       # 매치 없음·이력 없음 — 에러가 아니다
    return p.stdout


def head_path_of_id(root, doc_id):
    """HEAD 에서 이 id 를 가진 문서의 경로. 없으면 None (아직 커밋되지 않은 신규 문서)."""
    out = _git(root, "grep", "-l", "-E", "^id:[[:space:]]*%s[[:space:]]*$" % doc_id,
               "HEAD", "--", "docs")
    paths = [line.split(":", 1)[1] for line in out.splitlines() if ":" in line]
    return paths[0] if len(paths) == 1 else None


def accept_commit_date(root, rel_path):
    """이 문서를 accepted 로 바꾼 **가장 이른** 커밋의 날짜(YYYY-MM-DD). 없으면 None.

    아직 커밋 전이면 None 이다 — 그것도 정상이다(작업 트리에서 방금 accept 한 상태).
    """
    out = _git(root, "log", "--reverse", "--format=%ad", "--date=short",
               "-S", "status: accepted", "--", rel_path)
    lines = out.splitlines()
    return lines[0].strip() if lines else None


def is_tracked(root, rel_path):
    return bool(_git(root, "ls-files", "--", rel_path).strip())
