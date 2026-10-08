"""리프 티켓의 선행 의존 — 발행 게이트 + 기입의 공용 로직 (ADR-0017 파일럿).

GitHub 네이티브 의존 관계(blocked by)에 건다 — 본문 절·Project 필드 없음.
발행(create.py)과 사후 갱신(set-deps.py)이 같은 게이트·같은 기입을 지난다.

게이트: 선행은 **존재하는 열린 리프(Task·Bug)** 만 — 닫힌 이슈·컨테이너·자기 자신은 거부.
(순환은 GitHub이 거부한다 — 그 오류를 그대로 전파.)
"""
from opsdoc import die

import gh

LEAF_TYPES = ("Task", "Bug")


def add_args(parser):
    parser.add_argument("--blocked-by", action="append", type=int, metavar="N",
                        help="선행 티켓 번호. 반복 가능 — 이 티켓은 나열된 전부가 close된 뒤에야 착수된다")
    parser.add_argument("--no-deps", action="store_true",
                        help="선행 없음의 명시적 선언 (침묵과 구분된다 — ADR-0017)")


def validate_answer(blocked_by, no_deps, type_label):
    """리프는 선행 의존에 답해야 발행된다 — 나열 XOR 무의존 선언. 침묵은 거부다."""
    if blocked_by and no_deps:
        die("거부: --blocked-by 와 --no-deps 는 함께 못 쓴다 — 선행이 있는가 없는가, 답은 하나다.")
    if not blocked_by and not no_deps:
        die("거부: %s 는 선행 의존에 답해야 발행된다 (ADR-0017)." % type_label,
            "  선행 티켓이 있으면 --blocked-by <N> (반복 가능),",
            "  없으면 --no-deps 로 무의존을 명시적으로 선언한다.",
            "  침묵은 거부다 — 빈 자리는 누락인지 무의존인지 말하지 못한다.")


def gate(repo, numbers, self_number=None):
    """명시된 선행 전부를 검증한다 → [{id, number, title}]. 하나라도 어긋나면 거부."""
    entries = []
    for n in dict.fromkeys(numbers or []):     # 중복 제거 · 순서 보존
        if self_number is not None and n == self_number:
            die("거부: #%d 는 자기 자신을 선행으로 걸 수 없다." % n)
        brief = gh.issue_brief(repo, n)
        if brief["type"] not in LEAF_TYPES:
            die("거부: #%d 는 %s(컨테이너)다 — 선행 의존은 리프(Task·Bug) 간 순서다 (ADR-0017)."
                % (n, brief["type"] or "타입 없음"),
                "  묶음 사이의 순서는 로드맵의 의미다 — 여기 담지 않는다.")
        if brief["state"] != "OPEN":
            die("거부: #%d 는 닫혀 있다(%s) — 닫힌 이슈는 선행이 아니라 이미 끝난 일이다."
                % (n, brief["state"]),
                "  이미 충족된 전제는 걸지 않는다 — 남은 선행만 나열한다.")
        entries.append({"id": brief["id"], "number": n, "title": brief["title"]})
    return entries


def apply(issue_id, entries):
    """검증된 선행들을 네이티브 관계로 건다."""
    for e in entries:
        gh.add_blocked_by(issue_id, e["id"])


def replace(repo, number, issue_id, entries):
    """현재 blocked-by 를 entries 로 **통째로 교체**한다 — 부분 수정이 아니라 전체 답을 다시 낸다.
    (set-repos.py 의 절 교체와 같은 규칙 — 절은 언제나 하나, 여기서는 관계 집합이 하나.)"""
    current = gh.issue_blocked_by(repo, number)
    want = {e["id"] for e in entries}
    removed = [c for c in current if c["id"] not in want]
    have = {c["id"] for c in current}
    added = [e for e in entries if e["id"] not in have]
    for c in removed:
        gh.remove_blocked_by(issue_id, c["id"])
    for e in added:
        gh.add_blocked_by(issue_id, e["id"])
    return added, removed


def describe(entries):
    return ", ".join("#%d" % e["number"] for e in entries) if entries else "없음(선언)"
