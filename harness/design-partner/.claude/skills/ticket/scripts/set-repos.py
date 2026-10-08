#!/usr/bin/env python3
"""리프 티켓의 저장소 맥락(target/ref)을 **사후에** 기입·갱신한다 (ADR-0016 파일럿).

  set-repos.py --issue N [--repo owner/name]
               --target-repo owner/name... | --no-target-repo   [--ref-repo owner/name]...

두 용도 — 같은 게이트, 같은 표기(repo_context.py)로:
  1. **소급 기입** — ADR-0016 이전에 발행돼 '저장소' 절이 없는 리프. 집행자가 산문에서
     저장소를 추론해야 하는 상태를 소급해서 없앤다.
  2. **갱신** — 작업 중 수정 대상이 늘었을 때. target 은 살아 있는 사실이다 — 목록이
     실제 수정 범위와 어긋난 채 남으면 화석이고, 저장소 질의가 거짓말을 한다.

발행(create.py)과 같은 게이트를 지난다: 침묵은 거부 — 지정(--target-repo) XOR 부재 선언(--no-target-repo).
같은 두 자리에 쓴다: 이슈 본문 '### 저장소' 절(YAML 블록 — 있으면 통째 교체·없으면 추가)
+ Project 'Target Repos' 필드. 구식 산문 절도 YAML 블록으로 교체된다 — 실행 한 번이 곧 마이그레이션이다.

거부 둘:
  - **컨테이너**(Epic·Feature) — 저장소 맥락을 담지 않는다. 집행 맥락은 수행 단위(리프)의 것이다.
  - **Project 미등록 이슈** — 등록(+초기 Status)은 발행(create.py)의 일이다. 여기서 슬쩍
    등록하면 Status 없는 유령 항목이 생긴다.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import _bootstrap  # noqa: F401 — git 루트의 .claude/skills/_lib 를 sys.path 에 올린다
import gh  # noqa: E402
import repo_context  # noqa: E402  (같은 디렉터리 — ADR-0016 저장소 맥락 공용 로직)
from opsdoc import die  # noqa: E402

CONTAINER_TYPES = ("Epic", "Feature")
PROJECT_NUMBER = int(os.environ.get("OPS_PROJECT", "1"))

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("--issue", required=True, type=int, metavar="N", help="대상 이슈 번호")
parser.add_argument("--repo", default=os.environ.get("OPS_REPO", "jyoliar-lab/ops-workflow"))
repo_context.add_args(parser)   # --target-repo / --no-target-repo / --ref-repo
args = parser.parse_args()

issue_id, type_name, body = gh.issue_view(args.repo, args.issue)

# ── 대상 게이트 — 리프만 받는다 ─────────────────────────────────────────────
if type_name in CONTAINER_TYPES:
    die("거부: #%d 는 컨테이너(%s)다 — 저장소 맥락을 담지 않는다." % (args.issue, type_name),
        "  묶음은 여러 저장소에 걸칠 수 있다 — 집행 맥락은 수행 단위(리프)의 것이다 (ADR-0016).")
if not type_name:
    die("거부: #%d 에 Issue Type 이 없다 — 리프인지 판정할 수 없다." % args.issue,
        "  먼저 타입(Task·Bug)을 지정한다.")

# ── 저장소 맥락 게이트 — 발행과 같은 문이다. 침묵은 거부 (ADR-0016) ──────────
repo_context.validate_answer(args.target_repo, args.no_target_repo, args.ref_repo, type_name)

# ── ① 본문 '### 저장소' 절 — 있으면 교체, 없으면(사전-0016 티켓) 추가 ────────
had_section = repo_context.SECTION_HEADER in body
new_body = repo_context.upsert_section(
    body, repo_context.render_section(args.target_repo, args.ref_repo))
gh.update_issue_body(issue_id, new_body)
print("본문 '저장소' 절 %s: #%d" % ("갱신" if had_section else "소급 기입", args.issue))

# ── ② Project 'Target Repos' 필드 — 기계 질의의 자리 ────────────────────────
org = args.repo.split("/")[0]
proj = gh.project(org, PROJECT_NUMBER)
item_id = gh.project_item(issue_id, proj["id"])
if not item_id:
    die("거부: #%d 는 Project #%d 에 등록돼 있지 않다." % (args.issue, PROJECT_NUMBER),
        "  등록(+초기 Status)은 발행 스크립트(create.py)의 일이다 — 여기서 슬쩍 등록하지 않는다.")
value = repo_context.set_field(proj, item_id, args.target_repo, PROJECT_NUMBER)
print("Target Repos 필드: %s" % value)
