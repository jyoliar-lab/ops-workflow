#!/usr/bin/env python3
"""ADR 파일 경로를 도출한다 (CLAUDE.md §7).

  doc-path.py --topic ops-workflow --id ADR-0001 --slug two-plane-split
  → docs/ops-workflow/adr/adr-0001-two-plane-split.md

파일명은 `adr-0012-<slug>.md` — **소문자**, id 가 **선두**(인용키로 바로 찾기 위해).
날짜 prefix 를 쓰지 않는다 — id 가 생성순과 단조 일치하므로 날짜는 중복이다.

슬러그를 여기서 검증한다. **accept 후에는 rename 이 금지되므로**, 이름이 잘못된 채
얼어붙으면 되돌릴 방법이 없다(새 ADR 로 supersede 하는 수밖에). 앞에서 막는 게 싸다.

타입 폴더(`adr/`)는 lazy 다 — 이 경로에 첫 문서를 쓸 때 폴더가 생긴다.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib"))
from opsdoc import adr_filename, die, repo_root, slug_problem  # noqa: E402

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--topic", required=True, help="폴더가 된다 (거친 1축, 단일 값)")
parser.add_argument("--id", required=True, help="next-id.py 가 발급한 값")
parser.add_argument("--slug", required=True, help="소문자 kebab-case, 3~6 단어")
args = parser.parse_args()

if not args.id.startswith("ADR-") or not args.id[4:].isdigit():
    die("거부: id 는 ADR-NNNN 꼴이다 (받은 값: %s)" % args.id)

if args.topic != args.topic.lower() or not args.topic.replace("-", "").isalnum():
    die("거부: topic 은 소문자 kebab-case 다 (받은 값: %s)" % args.topic)

problem = slug_problem(args.slug)
if problem:
    die("거부: " + problem,
        "  파일명은 accept 시 얼어붙는다 — 지금 바로잡는다.",
        "  예: two-plane-split · loki-object-storage · issue-type-hierarchy")

root = repo_root()
rel = os.path.join("docs", args.topic, "adr", adr_filename(args.id, args.slug))

if os.path.exists(os.path.join(root, rel)):
    die("거부: 이미 있는 파일이다 — %s" % rel)

print(rel)
