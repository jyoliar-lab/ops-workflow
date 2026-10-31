---
type: discussion
kind: deliberation
goal: public-face
topic: ops-workflow
subjects: [github-org-profile, discussion, digest, adr, github-issues, github-projects, ticket-engineer, tdd, jyoliar-k8s, jyoliar-platform-terraform, onpremise-k8s]
status: done
ref-adrs: []
related: [261031_1601_public-face-overview-and-readmes.md]
---

# 조직 Overview — 하네스가 아니라 일의 흐름을 적는다

## 1. 문제

`261031_1601` 의 분담표대로 쓴 Overview 초안은 읽기 어려웠다.
용어가 정의 없이 나왔고, 그림은 두 화면이었고, 표는 빽빽했고, 문체는 내부용이었다.
한 화면으로 줄이고 상세를 별도 파일로 내리는 두 번째 초안도 같은 뼈대 — 역할 넷과 저장소 셋의 연결 — 위에 있었다.
독자가 알고 싶은 것은 agent 가 몇 개이고 어떻게 연결됐는가가 아니라, 이 조직이 **문제를 어떻게 정의하고 · 계획하고 · 기록하고 · 일하는가**다.
그래서 뼈대를 바꾼다 — 하네스 구조가 아니라 일의 흐름을 축으로, 문서 규칙 · 생명주기 · 티켓 관리 · 상태를 그 흐름 안에 둔다.
앞선 논의 `261031_1653`(첫 화면과 그림)은 이 전환으로 전제가 사라져 제거했다.

## 2. 실측

**문서 4종과 상태값(CLAUDE.md §3).** discussion `active → done · rejected`, digest `current → superseded`(ADR-0035), ADR `proposed → accepted · rejected · superseded`(본문 동결은 공표 시점 — ADR-0006), postmortem `draft → frozen`.
정책 ADR 은 심사를 통과해도 `proposed` 로 남는다(ADR-0032).
digest 는 규범이 아니고 읽기 순서는 ADR → 티켓 → digest 다.

**티켓(CLAUDE.md §5 · ADR-0033).** Issue Types 넷 — Epic · Feature(컨테이너) · Task · Bug(리프). 3층 권장.
Status 여섯 — Draft · Todo · In Progress · In Review · Done · Cancelled.
`Ops Workflow` 프로젝트의 Status 필드 옵션이 이 여섯과 일치한다(2026-10-31 조회).
리프는 저장소(target · ref)와 선행 의존을 명시하고, 근거 ADR 은 Epic 에 필수 · Feature 와 리프에 선택이다.
Status 전이와 close 는 사람이 한다.
조사에는 티켓이 없다.

**집행(ticket-engineer).** 착수는 `ticket-start` — 티켓 · 근거 읽기 → AC · Requirements 추출 → `ticket-run.py` 가 게이트(계층 전체의 근거 ADR accepted · Status 비Draft · 저장소 절 존재)를 판정하고 티켓별 worktree 를 만든다.
그 뒤 TDD 판정 한 줄(대상 / 비대상) — 기준은 "변경 전에 · 저장소 안에서 · 이번 변경의 약속을 · 실패하는 테스트로 쓸 수 있는가" 이고, Terraform · Ansible · k8s manifest 는 비대상이다.
대상이면 `tdd-loop` — 시나리오 표(사람 승인) → red → red 검토(subagent) → green · refactor(subagent) → verify(subagent, 사람이 다음 지시).
비대상이면 바로 작업 → PR(`ticket-pr.py`) → `ticket-report`(preflight → AC 항목별 대조표 코멘트).
AC 그룹은 여섯(동작 · 검사 · 선언 · 수렴 · 지속 · 판독)이고, 인프라의 근거는 수렴(배포 뒤 명령 한 번 + 출력)과 지속(창 끝 재확인)이다.
agent 의 kubectl 은 전용 ServiceAccount 로 클러스터 전역 읽기 전용(Secret 제외)이고, 규약은 "클러스터를 고치는 길은 GitOps 저장소의 PR" 이다.
Ansible(onpremise-k8s) · Terraform 의 반영 방식은 하네스 규약에 적혀 있지 않다 — 사람의 답으로 닫는다(3-9).

**사이클 모음의 재료 — 실제 체인.** 여섯 단계를 한 번에 다 지난 체인은 없다.

| 체인 | 1 논의 | 2 digest | 3 ADR | 4 티켓 | 6-1 TDD | 6-2 인프라 | PR |
|---|---|---|---|---|---|---|---|
| Zitadel 위임 | `260807_0158` 외 여덟 | — | ADR-0030 accepted | Epic #43 → Feature #44 → Task #50 · #53 | — | terraform · jyoliar-k8s | terraform#2 · jyoliar-k8s#20 · #23~#26 |
| 레거시 공개 | `261026_1610` | `261026_1715` | ADR-0034 proposed | Feature #133 → Task #135 | — | terraform | terraform#5 |
| obs-toolkit red | `260917_1726` · `260917_1742` | — | — | Feature #92 → Task #102 | 시나리오 · 검수 · ready 코멘트 | — | obs-toolkit#17 |

Zitadel 체인의 티켓은 ADR-0030 을 본문 산문에서 인용하고 `### 근거 ADR` 절은 없다.
`### 근거 ADR` 절을 갖춘 티켓은 careerhub 서비스 대상(#47~#71)뿐이라 PR 이 비공개다.
digest 를 지난 체인은 레거시 공개 하나다 — digest 는 2026-10 에 생겼다(ADR-0035).
jyoliar-k8s 는 `jyoliar-careerhub/jyoliar-k8s` 로 이관됐고 `jae2274/jyoliar-k8s` 는 리다이렉트다 — 티켓 target 의 옛 이름은 살아 있지만 Overview 링크는 현재 owner 로 적는다.

**이어받는 것.** `261031_1601` 의 닫힌 축 — 입구는 Overview(3-1) · README 그대로(3-2) · 한국어(3-4) · 수치 없음(3-5) · 공개 순서는 저장소 먼저(4-2).
독자는 Claude Code 를 써 본 엔지니어다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 뼈대 — 일의 흐름 순서

**선택: 논의 → digest → ADR → 티켓 → 착수 → 작업의 순서로 절을 세우고, 문서 규칙 · 생명주기 · 상태는 그 단계 안에 적는다.** 저장소별 배열과 "어떻게 정의하나 / 계획하나 / 기록하나 / 일하나" 네 절은 버렸다. (인터뷰, 2026-10-31)

### 3-2. 분량 — Overview 하나

**선택: 별도 상세 파일 없이 Overview 하나에 끝까지 담는다. 길어져도 된다.** `.github/docs/design.md` 는 지운다. (인터뷰, 2026-10-31)

### 3-3. 역할 이름

**선택: design-partner · adr-judge · ticket-engineer · steward 를 그대로 쓰고 첫 등장에 한 줄 정의를 단다.** 하네스 중심을 피하는 것은 뼈대(3-1)로 하고 이름은 숨기지 않는다. (인터뷰, 2026-10-31)

### 3-4. 구체성 — 값까지

**선택: 문서 4종의 status 값, Issue Types 넷, Status 여섯, 동결 시점을 실제 값으로 적는다.** 원칙만 적고 값은 링크로 넘기는 안은 버렸다. (인터뷰, 2026-10-31)

### 3-5. 예시의 자리

**선택: 본문에는 예시 링크를 두지 않고, 마지막 절에 실제 체인의 링크 사슬을 모은다.** 어느 체인인가는 4-1. (인터뷰, 2026-10-31)

### 3-6. 그림

**선택: 그림 없음.** 순서는 절 번호가 말한다. (인터뷰, 2026-10-31)

### 3-7. 동기

**선택: 첫 절에 다섯 문장 안으로, 중립 서술로 적는다.** 출발점이 된 고통은 셋 — 코드에 "왜" 가 없어 같은 논의를 반복한 것, 사람이 agent 의 산출물을 전부 읽어야 하는 병목, 계획 · 집행 · 규칙 정비가 한 세션에 섞여 맥락이 오염된 것. "추정이 사실이 된다" 는 실제 출발점이 아니라 뺀다. 단계마다 "왜" 를 다는 안과 경험담 시점은 버렸다. (인터뷰, 2026-10-31)

### 3-8. 가지 — 본줄기만

**선택: 장애 대응(postmortem) · 정책 변경(steward 루프) · 관측(obs-toolkit)은 흐름에 넣지 않는다.** steward 와 obs-toolkit 은 저장소 표(3-10)에서만 한 줄로 말한다. (인터뷰, 2026-10-31)

### 3-9. 단계 — 여섯, 저장소 제목 아래

**선택: 여섯 단계를 두 저장소 제목으로 묶는다.** (인터뷰, 2026-10-31)

- **ops-workflow** — 1 논의(discussion) · 2 digest · 3 ADR 과 심사 · 4 티켓
- **ticket-engineer** — 5 착수 · 6 작업, 서브단계 넷
  - 6-1 애플리케이션 — "tdd-loop 를 트리거하는 AC 가 존재할 때" 로만 분기를 적는다. 판정 기준 문장과 저장소 종류는 적지 않는다
  - 6-2 인프라 — ArgoCD GitOps 저장소(jyoliar-k8s)와 Terraform(jyoliar-platform-terraform)은 PR 로 반영, Ansible(onpremise-k8s)은 로컬에서 반영한 뒤 PR 을 만든다. 검증은 배포 뒤 실측이고, 머지 후 확인까지 티켓이 열려 있다. agent 의 kubectl 은 읽기 전용이다. **Terraform 은 지금 로컬 apply 이지만 원격 저장소 변경으로만 반영되도록 바꿀 예정이므로 예정 기준으로 적는다** — 그 전환이 끝나기 전에 Overview 가 공개되면 한 줄이 앞선다
  - 6-3 PR 과 완료 보고 — 관문 스크립트로 PR, preflight, AC 항목별 대조표 코멘트. AC 그룹 여섯과 근거 표는 싣지 않는다
  - 6-4 검수와 close — 사람의 것. PR 머지 ≠ 티켓 종료

### 3-10. 저장소 표 — 흐름 앞에

**선택: 동기 절 다음, 흐름 전에 저장소별 역할 표 하나.** 행은 ops-workflow · ticket-engineer · ops-workflow-steward · obs-toolkit · 코드 저장소(인프라 셋 공개 · 서비스 비공개)다. (인터뷰, 2026-10-31)

### 3-11. 사람의 승인 지점

**선택: 단계마다 고정 위치에 같은 표식으로 한 줄.** 훑어 읽으면 승인 지점만 모아 읽힌다. 표식의 모양은 초안에서 정한다 — 후보는 각 절 끝의 `**사람:** …` 한 줄. (인터뷰, 2026-10-31)

## 4. 열린 축 — 논의

### 4-1. 사이클 모음 — 어느 실제 체인으로

실측(§2): 여섯 단계를 다 지난 체인은 없다.
Zitadel 체인은 accepted ADR 과 Epic → Feature → Task 삼층, 인프라 PR 을 갖췄고, obs-toolkit 체인은 TDD 코멘트와 PR 을 갖췄고, 레거시 공개 체인만 digest 를 지났다.
공개 저장소만 링크한다는 전제(`261031_1601` 4-1)에서 careerhub 서비스 PR 은 쓸 수 없다.

- **A. 가지별 체인 둘 + digest 한 줄** — 인프라는 Zitadel(논의 `260807_0158` → ADR-0030 → #43 → #44 → #50 → terraform#2 · jyoliar-k8s#20), 애플리케이션은 obs-toolkit(논의 `260917_1726` → #92 → #102 → 시나리오 · 검수 코멘트 → obs-toolkit#17). digest 행만 레거시 공개의 `261026_1715` 를 빌려 적는다 / 6-1 · 6-2 양쪽에 실물이 있고 accepted 게이트를 실제로 지난 체인이 있다 / 체인이 둘이라 "한 사이클" 이 아니고 digest 는 빌린 것이다
- B. 레거시 공개 체인 하나 — `261026_1610` → `261026_1715` → ADR-0034 → #133 → #135 → terraform#5 / 1~4 와 6-2 를 한 사이클로 지난다 / ADR 이 proposed 이고 티켓이 ADR 을 인용하지 않아 "accepted 게이트" 가 실물로 보이지 않으며 TDD 가 없다
- C. 단계마다 가장 맞는 예를 모은다 — 1 · 2 는 레거시 공개, 3 · 4 · 6-2 는 Zitadel, 6-1 은 obs-toolkit / 각 단계의 가장 좋은 실물 / 사슬이 아니라 목록이라 "한 작업이 이 순서를 지났다" 는 메시지가 약하다
- D. 안 한다 — 저장소 링크로 끝낸다 / 가장 짧다 / 규칙만 있고 실물이 없어 설득력이 준다

**판정(사람, 2026-10-31): A. 가지별 체인 둘 + digest 한 줄.**

## 5. 반대편 — 이 설계가 틀리는 조건

- 값까지 적는다(3-4)는 Overview 가 ADR-0033 · 0035 · 0006 의 값을 복제한다는 뜻이다. 그 ADR 이 supersede 되면 Overview 가 낡는다 — 생존형 문서를 두지 않는 코퍼스에서 Overview 는 예외이고, 고칠 사람이 없다는 것이 틀리는 조건이다.
- 본줄기만(3-8) 적으면 "규칙은 누가 어떻게 바꾸나" 가 Overview 에 없다. steward 저장소가 공개되는데 그 역할이 표 한 줄뿐이면 독자가 그 저장소의 존재 이유를 Overview 에서 읽지 못한다.
- 6-2 의 Terraform 한 줄은 예정 기준이다 — 전환 전에 독자가 저장소를 열면 로컬 apply 흔적과 어긋난다.
- 분량 제약을 풀었다(3-2) — 첫 초안이 읽기 어려웠던 원인 중 하나가 분량이었다면 같은 문제가 돌아온다. 뼈대가 바뀌어 읽히는가는 초안을 봐야 안다.
- 4-1 에서 A 를 고르면 체인 둘의 티켓이 전부 ADR 을 `### 근거 ADR` 절로 인용하지 않는다 — "티켓은 근거 ADR 을 적는다" 는 규칙의 실물이 공개 범위 안에 없다.

## 6. 버린 것

- 역할 넷 · 저장소 셋의 연결을 뼈대로 — 두 초안이 그 위에 있었고 읽히지 않았다.
- 한 화면 + 별도 상세 파일 — 흐름을 끊지 않고 끝까지 읽게 하는 쪽을 택했다.
- Mermaid 흐름도 · 상태 전이도 — 절 번호와 값 나열로 대신한다.
- 문제 → 응답 여섯 쌍 · 경구 — 동기는 다섯 문장이면 된다.
- 장애 · 정책 변경 · 관측 가지 — 본줄기를 흐린다.
- AC 그룹 여섯의 근거 표 · TDD 판정 기준 문장 — 하네스 내부의 정밀도이고 독자에게는 "AC 가 있으면 TDD" 로 충분하다.

## 7. 임계선 — ADR 감인가

ADR 감이 아니다.
Overview 의 내용은 정책을 서술할 뿐 하네스를 구속하지 않고, 고쳐 쓰는 데 한 시간이면 된다.
`261031_1601` §7 과 같다.

## 8. 다음

- `$ORG_PROFILE_ROOT/profile/README.md` 를 3-1 ~ 3-11 · 4-1 대로 다시 썼고 `docs/design.md` 를 지웠다. 커밋은 사람 승인 뒤.
- jyoliar-k8s 링크는 `jyoliar-careerhub/jyoliar-k8s` 로 적는다(옛 owner 는 리다이렉트).
- Terraform 원격 반영 전환은 이 논의 밖의 작업이다 — 끝나기 전에 Overview 가 공개되면 6-2 한 줄이 앞선다는 것만 적어 둔다(§5).
