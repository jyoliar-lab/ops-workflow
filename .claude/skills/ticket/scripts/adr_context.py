"""컨테이너 티켓의 '근거 ADR' 절 — 구조화 표기의 공용 로직 (repo_context.py 와 같은 패턴).

라이브러리다 — 직접 실행하지 않는다. create.py 가 발행 시 박고, 소급 기입도 이 렌더러를 쓴다.

'### 근거 ADR' 절 = YAML 블록(기계가 읽는 자리) + ADR별 링크(사람이 건너가는 자리).
근거는 **목록**이다(1개 이상) — 티켓 하나가 여러 결정에서 비롯될 수 있다.
단일이어도 목록 표기(`adrs:`)로 쓴다 — 미래의 파서가 두 형을 갖지 않게.

링크는 **절대 URL** 이라야 한다 — 이슈 본문의 상대 경로는 저장소 루트가 아니라
이슈 URL 기준으로 풀린다 (…/issues/docs/… → 404).

ADR마다 링크가 둘인 이유 — 서로 다른 질문에 답한다:
  HEAD      → "이 결정이 지금도 유효한가" (supersede 되면 그 자리에서 드러난다)
  permalink → "이 티켓은 어느 시점의 문서를 근거로 발행됐나" (불변)
주 링크는 HEAD 다. SHA 만 걸면 supersede 된 결정이 accepted 인 채로 영원히 보인다.

★ 집행·감사 도구가 이 절을 기계로 읽게 되면 repo_context 처럼 쌍둥이 파서를 두고 함께 바꾼다.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
import gh  # noqa: E402
from opsdoc import die  # noqa: E402

SECTION_HEADER = "### 근거 ADR"
FIELD_NAME = "ADR"

# 절 전체: 헤더 → (빈 줄) → ```yaml … ``` → (빈 줄) → ADR별 링크 불릿들
_SEC_RE = re.compile(
    r"^### 근거 ADR[ \t]*\n(?:[ \t]*\n)*```yaml\n.*?\n```[ \t]*\n"
    r"(?:[ \t]*\n)*(?:- \*\*ADR-\d{4}.*(?:\n|\Z))*",
    re.M | re.S)


def render_section(entries, repo):
    """entries: [(adr_id, title, path, sha), ...] — 1개 이상. title 은 빈 값일 수 있다."""
    lines = [SECTION_HEADER, "", "```yaml", "adrs:"]
    for adr_id, _title, path, sha in entries:
        lines += ["  - id: %s" % adr_id,
                  "    path: %s" % path,
                  "    sha: %s" % sha]
    lines += ["```", ""]
    for adr_id, title, path, sha in entries:
        head = "https://github.com/%s/blob/HEAD/%s" % (repo, path)
        pin = "https://github.com/%s/blob/%s/%s" % (repo, sha, path)
        label = "%s — %s" % (adr_id, title) if title else adr_id
        lines.append("- **%s** · [`HEAD`](%s) 지금도 유효한가 · [`%s`](%s) 발행 시점 스냅샷"
                     % (label, head, sha[:7], pin))
    return "\n".join(lines) + "\n"


def upsert_section(body, section):
    """본문의 '### 근거 ADR' 절을 통째로 교체하고, 없으면 끝에 붙인다.

    소급 기입(절이 없다)과 갱신(절이 있다)이 같은 코드를 지난다 — 절은 언제나 하나다.
    부분 수정이 아니라 전체 답을 다시 낸다 (set-repos.py 와 같은 규약).
    """
    if _SEC_RE.search(body):
        return _SEC_RE.sub(lambda _m: section, body, count=1)
    return body.rstrip() + "\n\n---\n\n" + section


def remove_section(body):
    """'### 근거 ADR' 절을 제거한다 (리프의 명시 철회). 절이 없으면 그대로 돌려준다."""
    if not _SEC_RE.search(body):
        return body
    out = _SEC_RE.sub("", body, count=1)
    # 절이 트레일러 끝이었다면 매달린 구분선을 정리한다
    stripped = out.rstrip()
    if stripped.endswith("---"):
        stripped = stripped[:-3].rstrip()
    return stripped + "\n"


def field_value(adr_ids):
    return ", ".join(adr_ids)          # 빈 목록 → "" (필드 비움)


def set_field(proj, item_id, adr_ids, project_number):
    """Project 'ADR' 필드 — 컨테이너의 값은 존재 근거(권위), 리프의 값은 이행 추적(비완전)."""
    field = proj["fields"].get(FIELD_NAME)
    if not field:
        die("거부: Project #%d 에 '%s' 필드가 없다 — 근거를 담을 자리가 없다."
            % (project_number, FIELD_NAME))
    value = field_value(adr_ids)
    gh.set_text_field(proj["id"], item_id, field["id"], value)
    return value
