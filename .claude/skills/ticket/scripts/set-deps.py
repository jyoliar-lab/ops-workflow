#!/usr/bin/env python3
"""리프 티켓의 선행 의존을 사후 기입·갱신한다 (ADR-0017 파일럿).

  set-deps.py --issue <N> --blocked-by <M>... | --no-deps

발행(create.py)과 같은 게이트(dep_context.py)로 GitHub 네이티브 의존 관계를 다시 쓴다.

★ 통째 교체 — --blocked-by 나열이 선행의 전부가 된다(나열 밖 기존 관계는 제거).
  --no-deps 는 전부 제거(무의존). 사이드바 손편집 금지 — 갱신은 언제나 이 스크립트다.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_lib"))
import gh  # noqa: E402
import dep_context  # noqa: E402
from opsdoc import die  # noqa: E402

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--issue", required=True, type=int)
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
dep_context.add_args(parser)    # --blocked-by / --no-deps
args = parser.parse_args()

dep_context.validate_answer(args.blocked_by, args.no_deps, "선행 의존 갱신")

brief = gh.issue_brief(args.repo, args.issue)
if brief["type"] not in dep_context.LEAF_TYPES:
    die("거부: #%d 는 %s(컨테이너)다 — 선행 의존은 리프(Task·Bug)의 것이다 (ADR-0017)."
        % (args.issue, brief["type"] or "타입 없음"))
if brief["state"] != "OPEN":
    die("거부: #%d 는 닫혀 있다(%s) — 닫힌 티켓의 의존은 갱신하지 않는다." % (args.issue, brief["state"]))

entries = dep_context.gate(args.repo, args.blocked_by, self_number=args.issue)
added, removed = dep_context.replace(args.repo, args.issue, brief["id"], entries)

print("#%d 선행 의존 (blocked by): %s" % (args.issue, dep_context.describe(entries)))
if added:
    print("  + 추가: %s" % ", ".join("#%d" % e["number"] for e in added))
if removed:
    print("  - 제거: %s" % ", ".join("#%d" % c["number"] for c in removed))
if not added and not removed:
    print("  (변경 없음 — 이미 그 답이다)")
