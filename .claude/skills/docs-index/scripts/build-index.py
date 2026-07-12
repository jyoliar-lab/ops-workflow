#!/usr/bin/env python3
"""docs/ frontmatter 스캔 → docs/_index/ 생성 (CLAUDE.md §7).

이 스크립트는 **검증하지 않는다** — 이상한 것은 경고로 뱉고 인덱스는 만든다.
게이트는 린터의 몫이다. 인덱스가 커밋을 막으면 dogfood 가 막힌다.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import TYPES, as_list, read_frontmatter, repo_root  # noqa: E402

HEADER = "<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — docs-index skill 이 만든다. -->\n"

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

        entries.append({
            "path": path, "rel": rel,
            "id": fm.get("id", ""),
            "type": doc_type,
            "topic": topic,
            "subjects": subjects,
            "status": fm.get("status", "(없음)"),
            "parent": fm.get("parent", ""),
            "title": title_of(path, name),
        })

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
    d = os.path.join(index_dir, "by-type")
    write(os.path.join(d, t + ".md"),
          ["# by-type / %s (%d)" % (t, len(rows)), ""]
          + table(rows, d, ("id", "status", "topic", "subjects")))

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
                  key=sort_key)
lines = ["# decisions-log — accepted ADR", "",
         "*ADR id 순. frontmatter 에 날짜 필드가 없어 시각순이 아니다 (§7) — 초판의 한계.*", ""]
lines += table(accepted, index_dir, ("id", "topic", "subjects", "parent")) if accepted else ["*(없음)*"]
write(os.path.join(index_dir, "decisions-log.md"), lines)

# ── 보고 ──────────────────────────────────────────────────────────────────
print("문서 %d건 → docs/_index/" % len(entries))
print("  by-type: %d · by-topic: %d · by-subject: %d · accepted ADR: %d"
      % (len({e["type"] for e in entries}),
         len({e["topic"] for e in entries}),
         len({s for e in entries for s in e["subjects"]}),
         len(accepted)))
if warnings:
    print("\n경고 %d건 (인덱스는 만들었다 — 검증은 린터의 몫):" % len(warnings), file=sys.stderr)
    for w in warnings:
        print("  - " + w, file=sys.stderr)
