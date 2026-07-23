"""ADR-0016 파일럿 — 리프 티켓의 저장소 맥락(target/ref) 공용 로직. 라이브러리다 — 직접 실행하지 않는다.

발행(create.py)과 사후 기입·갱신(set-repos.py)이 **같은 게이트·같은 표기**를 지나도록 여기 묶는다.

본문 '### 저장소' 절은 **YAML 펜스 블록**이다 — 사람과 기계가 **같은 표기 하나**를 읽는다.
사람용 산문과 기계용 숨은 데이터로 두 벌을 두면 반드시 어긋난다(같은 사실의 두 표기 — ADR-0016).

블록은 **도구만 쓴다**: 이 모듈이 emit 하고, 이 모듈과 ticket-engineer 의 쌍둥이 파서가 읽는다.
그래서 파서는 엄격하다 — PyYAML 없이, 우리가 emit 하는 부분집합만 받고 이탈은 거부한다.
관대한 파서는 손편집을 조용히 받아들여 본문과 보드 필드를 가른다. **손으로 고치지 않는다 —
갱신은 set-repos.py 로.**

  - target — 권위 있는 사실. 목록 XOR 명시적 부재(`null`). 침묵은 거부.
  - ref    — 비완전한 힌트. 선택 입력(`[]` 허용).

담는 자리는 둘이다: 이슈 본문 '### 저장소' 절(사람·집행 도구) + Project 'Target Repos' 필드(보드 질의).

★ 쌍둥이 파서: ticket-engineer `.claude/skills/_lib/repos.py` — 표기를 바꾸면 **함께** 바꾼다.
  그 정합은 steward 의 conformance 감사 대상이다 (파일럿 원장: steward pilots.md).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
import gh  # noqa: E402
from opsdoc import die  # noqa: E402

SECTION_HEADER = "### 저장소"
FIELD_NAME = "Target Repos"
ABSENT = "(없음)"          # Project 필드의 부재 표기 — 본문 블록에서는 null 이다

_KEYS = ("target-repos", "ref-repos")

# YAML 펜스 블록 절: 헤더 → (빈 줄) → ```yaml … ```
_SEC_YAML_RE = re.compile(
    r"^### 저장소[ \t]*\n(?:[ \t]*\n)*```yaml\n(.*?)\n```[ \t]*\n?", re.M | re.S)
# 구식 산문 절(YAML 블록 도입 전): 헤더 → 다음 헤딩 직전 또는 본문 끝까지
_SEC_PROSE_RE = re.compile(
    r"^### 저장소[ \t]*\n.*?(?=^#{1,3} |\Z)", re.M | re.S)


def add_args(parser):
    """발행·사후 갱신 공통의 저장소 맥락 인자. 두 스크립트의 플래그가 같아야 규약이 하나로 읽힌다."""
    parser.add_argument("--target-repo", action="append", default=[], metavar="owner/name",
                        help="수정 대상 저장소(반복 가능). 리프는 이것 또는 --no-target-repo 가 필수")
    parser.add_argument("--no-target-repo", action="store_true",
                        help="수정 대상이 아직 존재하지 않음을 명시적으로 선언(신규 저장소 생성 등)")
    parser.add_argument("--ref-repo", action="append", default=[], metavar="owner/name",
                        help="구조 파악에 필요한 참조 저장소(반복 가능·비완전 목록)")


def validate_answer(target_repos, no_target, ref_repos, type_label):
    """리프의 저장소 맥락 게이트 — "어디를 고치는가"에 답해야 통과한다 (ADR-0016)."""
    if target_repos and no_target:
        die("거부: --target-repo 와 --no-target-repo 는 함께 못 쓴다 — 지정과 부재 선언은 배타다.")
    if not target_repos and not no_target:
        die("거부: 리프(%s)는 수정 대상 저장소에 답해야 한다 (ADR-0016)." % type_label,
            "  고칠 저장소가 있다      → --target-repo owner/name (반복 가능)",
            "  대상이 아직 없다        → --no-target-repo (신규 저장소 생성 등 — 명시적 부재 선언)",
            "  선택 입력이 아니다 — 빈 자리는 누락인지 부재인지 말하지 못하고,",
            "  집행자가 그 자리에서 다시 추론하게 된다.")
    for r in target_repos + ref_repos:
        if "/" not in r:
            die("거부: 저장소는 owner/name 꼴이다 (받은 값: %s)" % r)


def render_section(target_repos, ref_repos):
    """'### 저장소' 절(YAML 블록) — emit 직후 자기 파서로 왕복 검증한다(표기 계약의 자가 감시)."""
    lines = [SECTION_HEADER, "", "```yaml",
             "# target: 고쳐도 되는 저장소의 전부 — 작업 중 늘면 먼저 갱신한다(필수 · set-repos.py)"]
    if target_repos:
        lines.append("target-repos:")
        lines += ["  - %s" % r for r in target_repos]
    else:
        lines.append("target-repos: null  # 아직 존재하지 않는다(신규 저장소 생성 등)")
    lines.append("# ref: 구조 파악의 출발점 — 비완전(나열 밖 참조 허용) · 갱신은 권장")
    if ref_repos:
        lines.append("ref-repos:")
        lines += ["  - %s" % r for r in ref_repos]
    else:
        lines.append("ref-repos: []")
    lines.append("```")
    section = "\n".join(lines) + "\n"

    try:
        parsed = parse_section(section)
    except ValueError as e:
        die("버그: emit 한 절을 자기 파서가 거부했다 — repo_context.py 왕복 불일치.", "  %s" % e)
    if parsed != (list(target_repos), not target_repos, list(ref_repos)):
        die("버그: 저장소 절 emitter/parser 왕복 불일치 — repo_context.py 를 의심하라.")
    return section


def parse_section(body):
    """본문 → (target 목록, 부재 선언 여부, ref 목록). 절이 없으면 None. 형식 이탈은 ValueError.

    ★ ticket-engineer `.claude/skills/_lib/repos.py` 의 parse_section 과 쌍둥이 — 함께 바꾼다.
    """
    if SECTION_HEADER not in body:
        return None
    m = _SEC_YAML_RE.search(body)
    if m is None:
        raise ValueError("'저장소' 절은 있는데 YAML 블록이 아니다 — 구식(산문) 또는 손상된 표기. "
                         "set-repos.py 로 다시 기입한다.")
    found, key = {}, None
    for raw in m.group(1).splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("  - "):
            if key is None:
                raise ValueError("목록 항목이 키 밖에 있다: %r" % line)
            found[key].append(line[4:].split("#", 1)[0].strip())
            continue
        head, sep, rest = line.partition(":")
        if not sep or head not in _KEYS or head in found:
            raise ValueError("모르는·중복된 줄: %r" % line)
        val = rest.split("#", 1)[0].strip()
        if val == "":                                   # 블록 목록이 이어진다
            found[head], key = [], head
        elif val == "[]":
            found[head], key = [], None
        elif val == "null" and head == "target-repos":  # 명시적 부재 선언
            found[head], key = None, None
        else:
            raise ValueError("받을 수 없는 값: %r" % line)
    if set(found) != set(_KEYS):
        raise ValueError("target-repos·ref-repos 두 키가 다 있어야 한다 (있는 키: %s)" % sorted(found))
    targets = found["target-repos"]
    if targets == []:
        raise ValueError("target-repos 가 비었다 — 목록이거나 null(명시적 부재)이어야 한다. 침묵은 없다.")
    for r in (targets or []) + found["ref-repos"]:
        if "/" not in r:
            raise ValueError("저장소는 owner/name 꼴이다 (받은 값: %r)" % r)
    return (targets or [], targets is None, found["ref-repos"])


def upsert_section(body, section):
    """본문의 '### 저장소' 절을 통째로 교체하고, 없으면 끝에 붙인다.

    구식 산문 절도 여기서 교체된다 — set-repos.py 한 번이 곧 YAML 블록으로의 마이그레이션이다.
    소급 기입(절이 없다)과 갱신(절이 있다)이 같은 코드를 지난다 — 절은 언제나 하나다.
    """
    for pat in (_SEC_YAML_RE, _SEC_PROSE_RE):
        if pat.search(body):
            return pat.sub(lambda _m: section, body, count=1)
    return body.rstrip() + "\n\n---\n\n" + section


def field_value(target_repos):
    return ", ".join(target_repos) if target_repos else ABSENT


def set_field(proj, item_id, target_repos, project_number):
    """Project 'Target Repos' 필드 — 보드가 "이 저장소를 고치는 열린 리프"를 질의하는 자리."""
    field = proj["fields"].get(FIELD_NAME)
    if not field:
        die("거부: Project #%d 에 '%s' 필드가 없다 — 수정 대상을 질의할 자리가 없다."
            % (project_number, FIELD_NAME))
    value = field_value(target_repos)
    gh.set_text_field(proj["id"], item_id, field["id"], value)
    return value
