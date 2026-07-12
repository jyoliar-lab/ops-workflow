"""docs/ 문서를 읽는 공용 모듈. 표준 라이브러리만 쓴다.

frontmatter 파서는 **여기 한 벌만** 있다. 스크립트마다 awk·grep으로 다시 짜면
같은 문서를 스크립트마다 다르게 읽게 되고, 동결 검사와 게이트가 서로 다른 status를 볼 수 있다.

외부 의존(PyYAML 등)을 들이는 것은 그 자체로 결정이므로, 필요해지면 마찰 로그에 적고 판단한다.
"""
import os
import re
import sys

# 동결 상태 (CLAUDE.md §3): adr = accepted|superseded · postmortem = frozen
FROZEN = {"accepted", "superseded", "frozen"}
TYPES = ["adr", "discussion", "postmortem"]

# 파일명 규약 (CLAUDE.md §7): adr-0012-<slug>.md
#   id 가 파일명 **선두**에 온다 — 인용키로 바로 찾기 위해서다.
#   날짜 prefix 를 쓰지 않는다 — id 가 생성순과 단조 일치하므로 날짜는 중복이다.
ADR_FILENAME = re.compile(r"^adr-(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_WORDS = (3, 6)


def die(*lines):
    """거부한다. exit 1 = 거부 (부록 D). agent는 이것을 우회하지 않는다."""
    for line in lines:
        print(line, file=sys.stderr)
    sys.exit(1)


def repo_root():
    d = os.path.abspath(os.curdir)
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    die("거부: git 저장소 안에서 실행한다.")


def read_frontmatter(path):
    """--- 로 감싼 머리말을 dict 로 읽는다.

    지원: 스칼라(`k: v`) · 인라인 리스트(`k: [a, b]`) · 블록 리스트(`k:` 다음 줄 `- a`).
    값이 비면 빈 문자열/빈 리스트다 — 키가 없는 것과 구분한다.
    """
    fields, key = {}, None
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return fields
    if not lines or lines[0].strip() != "---":
        return fields

    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.lstrip().startswith("#") or not line.strip():
            continue
        if line.startswith((" ", "\t", "-")) and key:              # 블록 리스트 항목
            item = line.strip().lstrip("-").strip().strip("\"'")
            if item:
                if not isinstance(fields.get(key), list):
                    fields[key] = []
                fields[key].append(item)
            continue
        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key, raw = key.strip(), raw.strip()
        if raw.startswith("[") and raw.endswith("]"):              # 인라인 리스트
            fields[key] = [v.strip().strip("\"'") for v in raw[1:-1].split(",") if v.strip()]
        elif raw:
            fields[key] = raw.strip("\"'")
        else:
            fields[key] = ""
    return fields


def as_list(value):
    if isinstance(value, list):
        return [v for v in value if v]
    return [value] if value else []


def iter_docs(root):
    """docs/ 의 모든 문서를 (경로, frontmatter) 로 훑는다. _index/ 는 생성물이라 제외한다."""
    docs = os.path.join(root, "docs")
    for dirpath, dirnames, filenames in os.walk(docs):
        rel = os.path.relpath(dirpath, docs)
        if rel.split(os.sep)[0] == "_index":
            dirnames[:] = []
            continue
        for name in sorted(filenames):
            if name.endswith(".md"):
                path = os.path.join(dirpath, name)
                yield path, read_frontmatter(path)


def slug_problem(slug):
    """슬러그가 규약(§7)을 어기면 그 이유를, 멀쩡하면 None 을 준다."""
    if not SLUG.match(slug):
        return ("소문자 kebab-case 만 쓴다 (한글·대문자·밑줄·공백 금지) — 받은 값: %r" % slug)
    words = slug.split("-")
    lo, hi = SLUG_WORDS
    if not (lo <= len(words) <= hi):
        return ("슬러그는 %d~%d 단어다 (받은 값: %d단어 — %s)" % (lo, hi, len(words), slug))
    return None


def adr_filename(adr_id, slug):
    """ADR-0012 + slug → adr-0012-slug.md (파일명은 소문자, frontmatter 의 id 는 대문자)."""
    return "%s-%s.md" % (adr_id.lower(), slug)


def filename_problem(path, fm):
    """파일명이 규약(§7)을 어기면 그 이유를 준다. ADR 만 검사한다 —
    discussion·postmortem 의 파일명(YYMMDD_HHmm_<slug>.md)은 아직 어떤 skill 도 만들지 않으므로
    기계가 강제할 지점이 없다. 린터가 생기면 거기서 잡는다."""
    if fm.get("type") != "adr":
        return None
    name = os.path.basename(path)
    m = ADR_FILENAME.match(name)
    if not m:
        return ("파일명이 규약을 어긴다: %s\n  규약(§7): adr-0012-<slug>.md — 소문자, id 가 선두" % name)
    adr_id = fm.get("id", "")
    if adr_id and adr_id.lower() != "adr-" + m.group(1):
        return ("파일명(%s)과 frontmatter id(%s)가 어긋난다 — 인용키가 갈라진다." % (name, adr_id))
    return slug_problem(m.group(2))


def find_adr(root, adr_id, missing_hint=()):
    """ADR id → 파일 경로. 없거나 둘 이상이면 거부한다 (전역 유일성, §7)."""
    hits = [p for p, fm in iter_docs(root)
            if fm.get("type") == "adr" and fm.get("id") == adr_id]
    if not hits:
        die("거부: %s 을 docs/ 에서 찾지 못했다." % adr_id, *missing_hint)
    if len(hits) > 1:
        die("거부: %s 이 %d곳에 있다 — 전역 유일성이 깨졌다." % (adr_id, len(hits)),
            *["  " + os.path.relpath(p, root) for p in hits])
    return hits[0]
