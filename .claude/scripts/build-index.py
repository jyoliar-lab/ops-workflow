#!/usr/bin/env python3
"""docs/ frontmatter 스캔 → docs/_index/ 생성 (CLAUDE.md §7).

이 스크립트는 **검증하지 않는다** — 이상한 것은 경고로 뱉고 인덱스는 만든다.
게이트는 린터의 몫이다. 인덱스가 커밋을 막으면 dogfood 가 막힌다.
"""
import os
import re
import shutil
import sys

# _lib 는 스킬들의 공유 라이브러리다 — 이 스크립트는 .claude/scripts/ 로 나왔지만 같은 것을 쓴다
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "_lib"))
from opsdoc import TYPES, as_list, filename_problem, read_frontmatter, repo_root  # noqa: E402

HEADER = "<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->\n"

root = repo_root()
docs = os.path.join(root, "docs")
if not os.path.isdir(docs):
    # 콜드스타트. exit 1 은 "거부"를 뜻하므로 여기서 쓰지 않는다 — 인덱스할 것이 없을 뿐이다.
    print("docs/ 가 없다 — 인덱스할 문서가 없다. (콜드스타트: 에러가 아니다)")
    sys.exit(0)


def title_of(path, fallback):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return fallback


# ── 수집 ──────────────────────────────────────────────────────────────────
entries, warnings = [], []
for dirpath, dirnames, filenames in os.walk(docs):
    parts = os.path.relpath(dirpath, docs).split(os.sep)
    if parts[0] == "_index":
        dirnames[:] = []
        continue
    for name in sorted(filenames):
        if not name.endswith(".md"):
            continue
        path = os.path.join(dirpath, name)
        fm = read_frontmatter(path)
        rel = os.path.relpath(path, root)

        doc_type = fm.get("type")
        if doc_type not in TYPES:
            warnings.append("type 이 없거나 알 수 없다 (%r) — 건너뛴다: %s" % (doc_type, rel))
            continue

        folder_topic = parts[0] if parts[0] != "." else None
        topic = fm.get("topic")
        if topic and folder_topic and topic != folder_topic:
            warnings.append("topic(%s) ≠ 폴더(%s): %s" % (topic, folder_topic, rel))
        topic = topic or folder_topic or "(없음)"

        subjects = as_list(fm.get("subjects"))
        if not subjects:
            warnings.append("subjects 가 비었다 — 정밀 검색에서 사라진다: %s" % rel)

        # ref-adrs 는 discussion(ADR-0022)·digest(ADR-0035) 의 것이다 — 다루거나 낳은 ADR 의 id 목록.
        # ADR 은 자족성 때문에 이쪽을 가리키지 않으므로, 이 관계는 여기서만 나온다.
        ref_adrs = as_list(fm.get("ref-adrs")) if doc_type in ("discussion", "digest") else []
        for rid in ref_adrs:
            if not re.fullmatch(r"ADR-\d{4}", str(rid)):
                warnings.append("ref-adrs 값이 ADR id 꼴이 아니다 (%r): %s" % (rid, rel))

        problem = filename_problem(path, fm)
        if problem:
            warnings.append(problem.replace("\n", " ") + " — " + rel)

        # id 는 ADR 에만 있다(§7 — 전역 순차). discussion·postmortem 에는 원래 없으므로
        # "비었음"만으로는 이상을 알 수 없다 — **type 을 함께 봐야** 보인다.
        # 실제로 놓쳤다: 포매터가 `id: ADR-0015` 를 `## id:` 헤딩으로 바꾸자 나머지 필드는
        # 다 살아남고 id 만 사라져, ADR 이 id 칸 `—` 로 조용히 등재됐다.
        if doc_type == "adr" and not fm.get("id"):
            warnings.append("adr 인데 id 가 없다 — frontmatter 가 깨졌을 수 있다: %s" % rel)

        status = fm.get("status", "(없음)")
        accepted_at = fm.get("accepted_at", "")

        # accepted_at 은 **권위 있는 필드**다 (§7 · ADR-0004) — *"검토가 언제 끝났는가"* 에
        # 문서가 스스로 답한다. git 과 대조하지 않는다: accept 한 날과 커밋한 날이 어긋나는 것은
        # **정상**이다(다른 사실이다). 여기서 볼 수 있는 것은 **짝이 맞는가** 뿐이다.
        if status == "accepted" and not accepted_at:
            warnings.append("accepted 인데 accepted_at 이 없다 (accept.py 를 거치지 않았다): %s" % rel)
        if status == "superseded" and not fm.get("superseded_by"):
            warnings.append("superseded 인데 superseded_by 가 비었다 — 무엇이 대체했는지 알 수 없다: %s" % rel)

        entries.append({
            "path": path, "rel": rel,
            "id": fm.get("id", ""),
            "type": doc_type,
            "topic": topic,
            "subjects": subjects,
            "status": status,
            "parent": fm.get("parent", ""),
            "accepted_at": accepted_at,
            "ref-adrs": ref_adrs,
            "goal": fm.get("goal", ""),          # 같은 목표의 discussion·digest 를 묶는 자유 필드
            "title": title_of(path, name),
        })

# ref-adrs 해석 검사 — 가리킨 ADR 이 코퍼스에 실제로 있는가 (경고만 — 게이트는 린터의 몫)
known_adr_ids = {e["id"] for e in entries if e["type"] == "adr" and e["id"]}
for e in entries:
    for rid in e["ref-adrs"]:
        if re.fullmatch(r"ADR-\d{4}", str(rid)) and rid not in known_adr_ids:
            warnings.append("ref-adrs 가 가리키는 ADR 이 코퍼스에 없다 (%s): %s" % (rid, e["rel"]))

# ── 방출 ──────────────────────────────────────────────────────────────────
index_dir = os.path.join(docs, "_index")
for sub in ("by-type", "by-topic", "by-subject"):
    shutil.rmtree(os.path.join(index_dir, sub), ignore_errors=True)   # 사라진 값의 잔재를 남기지 않는다
    os.makedirs(os.path.join(index_dir, sub), exist_ok=True)


def table(rows, from_dir, cols):
    out = ["| " + " | ".join(list(cols) + ["문서"]) + " |",
           "|" + "---|" * (len(cols) + 1)]
    for e in rows:
        cells = []
        for c in cols:
            v = e[c]
            v = ", ".join(v) if isinstance(v, list) else v
            cells.append(v or "—")
        cells.append("[%s](%s)" % (e["title"], os.path.relpath(e["path"], from_dir)))
        out.append("| " + " | ".join(cells) + " |")
    return out


def write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(HEADER + "\n" + "\n".join(lines) + "\n")


def sort_key(e):
    return (e["id"] or "~", e["rel"])       # id 없는 문서(discussion·postmortem)는 뒤로


for t in TYPES:
    rows = sorted([e for e in entries if e["type"] == t], key=sort_key)
    if not rows:
        continue                            # 없는 타입의 빈 인덱스는 만들지 않는다 (lazy, §7)
    # discussion·digest 는 id 가 없고 goal·ref-adrs 를 가진다 (ADR-0022 · ADR-0035) — 열을 타입에 맞춘다
    cols = (("status", "goal", "topic", "subjects", "ref-adrs") if t in ("discussion", "digest")
            else ("id", "status", "topic", "subjects"))
    d = os.path.join(index_dir, "by-type")
    write(os.path.join(d, t + ".md"),
          ["# by-type / %s (%d)" % (t, len(rows)), ""]
          + table(rows, d, cols))

for topic in sorted({e["topic"] for e in entries}):
    rows = sorted([e for e in entries if e["topic"] == topic], key=sort_key)
    d = os.path.join(index_dir, "by-topic")
    write(os.path.join(d, topic + ".md"),
          ["# by-topic / %s (%d)" % (topic, len(rows)), ""]
          + table(rows, d, ("id", "type", "status", "subjects")))

for subject in sorted({s for e in entries for s in e["subjects"]}):
    rows = sorted([e for e in entries if subject in e["subjects"]], key=sort_key)
    d = os.path.join(index_dir, "by-subject")
    write(os.path.join(d, subject + ".md"),
          ["# by-subject / %s (%d)" % (subject, len(rows)), "",
           "topic·type 을 가로지른다 — 세부 주제 검색의 유일한 수단이다.", ""]
          + table(rows, d, ("id", "type", "topic", "status")))

accepted = sorted([e for e in entries if e["type"] == "adr" and e["status"] == "accepted"],
                  key=lambda e: (e["accepted_at"] or "9999-99-99", e["id"]))   # 시간순 (§7)
lines = ["# decisions-log — accepted ADR", "",
         "*accept 순 — 검토가 끝난 시각(`accepted_at`) 기준. **동결(공표) 순서와는 다를 수 있다.***", ""]
lines += (table(accepted, index_dir, ("id", "accepted_at", "topic", "subjects", "parent"))
          if accepted else ["*(없음)*"])
write(os.path.join(index_dir, "decisions-log.md"), lines)

# ── by-ref-adr — 결정과 얽힌 논의 (ADR-0022) ──────────────────────────────
# ADR 은 discussion 을 가리키지 않는다(자족성) — "이 결정과 얽힌 논의"는 여기서 파생한다.
adr_by_id = {e["id"]: e for e in entries if e["type"] == "adr" and e["id"]}
refmap = {}
for e in entries:
    for rid in e["ref-adrs"]:
        refmap.setdefault(rid, []).append(e)
lines = ["# by-ref-adr — 결정과 얽힌 논의·digest (`ref-adrs` 에서 파생)", "",
         "*ADR 은 discussion·digest 를 가리키지 않는다(자족성) — 역방향 조회는 이 뷰가 답한다. "
         "둘 다 보관을 약속하지 않으므로 이 목록은 편의이지 근거가 아니다.*", ""]
if refmap:
    for rid in sorted(refmap):
        t = adr_by_id.get(rid)
        lines.append("## " + (t["title"] if t else rid + " *(코퍼스에 없음)*"))
        lines.append("")
        for e in sorted(refmap[rid], key=lambda x: x["rel"]):
            lines.append("- [%s](%s) — `%s` · `%s`" % (e["title"], os.path.relpath(e["path"], index_dir), e["type"], e["status"]))
        lines.append("")
else:
    lines.append("*(없음)*")
write(os.path.join(index_dir, "by-ref-adr.md"), lines)

# ── 보고 ──────────────────────────────────────────────────────────────────
print("문서 %d건 → docs/_index/" % len(entries))
print("  by-type: %d · by-topic: %d · by-subject: %d · accepted ADR: %d · ref-adrs 링크: %d"
      % (len({e["type"] for e in entries}),
         len({e["topic"] for e in entries}),
         len({s for e in entries for s in e["subjects"]}),
         len(accepted),
         sum(len(e["ref-adrs"]) for e in entries)))
if warnings:
    print("\n경고 %d건 (인덱스는 만들었다 — 검증은 린터의 몫):" % len(warnings), file=sys.stderr)
    for w in warnings:
        print("  - " + w, file=sys.stderr)
