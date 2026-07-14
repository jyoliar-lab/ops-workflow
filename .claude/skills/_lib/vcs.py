"""git 조회 공용 모듈. 표준 라이브러리(subprocess)만 쓴다.

**git 에 묻는 것은 딱 하나다 — "이것이 공표됐는가".** (CLAUDE.md §3)

동결은 **시각이 아니라 상태**이고, 그 상태는 `origin/main` 에 있느냐로만 판정된다.
문서 밖의 사실이므로 필드로 두지 않는다 — 그래서 여기서 파생한다.

**`accepted_at` 은 git 에 묻지 않는다.** 그것은 *"검토가 언제 끝났는가"* 이고
**문서 자신의 사실**이며 **권위 있다**(§7 · ADR-0004). accept 한 날과 커밋한 날이
어긋나는 것은 **정상**이다 — 둘은 다른 사실이다.

여기 있는 함수는 전부 **읽기**다. git 을 근거로 문서를 고치지 않는다.
"""
import subprocess

# 공표된 사본이 사는 곳. **워킹 트리는 공표가 아니다** — 내 디스크에만 있는 결정은
# 아무도 볼 수 없고, 그것을 근거로 만든 티켓의 링크는 죽은 링크다.
PUBLISHED = "origin/main"


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


def is_tracked(root, rel_path):
    return bool(_git(root, "ls-files", "--", rel_path).strip())


# ── 공표된 사본 읽기 ──────────────────────────────────────────────────────

def fetch_published(root, ref=PUBLISHED):
    """origin/main 을 최신으로 당긴다. 실패해도 죽지 않는다 — 오프라인이면 로컬 ref 로 판단하고 알린다."""
    remote, _, branch = ref.partition("/")
    p = subprocess.run(["git", "-C", root, "fetch", "--quiet", remote, branch],
                       capture_output=True, text=True)
    return p.returncode == 0


def ref_sha(root, ref=PUBLISHED):
    return _git(root, "rev-parse", ref).strip() or None


def path_of_id(root, doc_id, ref=PUBLISHED):
    """공표된 사본에서 이 id 를 가진 문서의 경로. 없으면 None."""
    out = _git(root, "grep", "-l", "-E", "^id:[[:space:]]*%s[[:space:]]*$" % doc_id,
               ref, "--", "docs")
    paths = [line.split(":", 1)[1] for line in out.splitlines() if ":" in line]
    return paths[0] if len(paths) == 1 else None


def read_at(root, rel_path, ref=PUBLISHED):
    """공표된 사본의 내용. 없으면 빈 문자열."""
    return _git(root, "show", "%s:%s" % (ref, rel_path))
