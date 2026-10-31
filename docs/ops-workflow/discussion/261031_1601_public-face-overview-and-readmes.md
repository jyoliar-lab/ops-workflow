---
type: discussion
kind: deliberation
goal: public-face
topic: ops-workflow
subjects: [github-org-profile, readme, ops-workflow, ticket-engineer, ops-workflow-steward, obs-toolkit, github-issues]
status: done
ref-adrs: []
related: [../../homelab/discussion/261029_1413_pre-exposure-patch-priority-and-difficulty.md, ../../careerhub/discussion/261026_1610_legacy-public-exposure-auth-disposition.md]
---

# 공개 얼굴 — 조직 Overview와 하네스 README의 분담, 공개 전환 점검

## 1. 문제

이력서가 `jyoliar-lab` 조직을 가리키게 된다.
독자는 이력서 → 조직 Overview → 저장소 순서로 들어오고, 채용 담당자와 엔지니어가 섞여 있다.
지금 조직의 저장소 다섯은 전부 private 이고, 하네스 세 저장소의 README 는 운영자를 위한 구조 안내라 "왜" 가 없다.
그래서 정할 것은 셋이다 — Overview 가 담을 것과 README 가 담을 것의 경계, 저장소를 public 으로 돌릴 때 점검할 것, 티켓·docs 가 가리키는 참조 저장소를 어디까지 함께 공개하는가.
AI 기반 업무 프로세스를 이력서의 주요 역량으로 적는 작업(AX 여섯 요소)과 같은 목표에서 나왔지만, 이 문서는 공개 페이지와 공개 전환만 다룬다.

## 2. 실측

**GitHub 사양.** 조직 Overview 는 public 저장소 `.github` 의 `profile/README.md` 가 렌더링된다 — 루트 `README.md` 가 아니다.
저장소가 public 이 되면 Issues 와 코멘트도 전부 공개된다.
Projects 는 별개다 — `Ops Workflow` 프로젝트는 지금 `public: false` 이고 저장소 공개와 무관하게 따로 켠다.

**저장소 상태(2026-10-31).** jyoliar-lab 의 ops-workflow · ticket-engineer · ops-workflow-steward · obs-toolkit · obs-bench 전부 private.
참조 저장소(`.claude/ref-repos.txt`) 열여덟도 전부 private — jyoliar-careerhub 열셋(서비스 11 · onpremise-k8s · jyoliar-platform-terraform), jae2274 둘(goutils · jyoliar-k8s), jyoliar-lab 셋.
Issues 137건, 코멘트 193건.

**기존 README 의 성격.** 세 저장소 모두 첫 줄이 "사람을 위한 하네스 구조 안내이고 agent 는 읽지 않는다" 류이고, 본문은 세션 여는 명령 · 디렉터리 트리 · 역할 표 · "구조로 강제하는 것" 표 · 로컬 설정이다.
동기 · 문제 · 흐름은 없다.
README 나 공개에 관한 기존 ADR · discussion 은 없다.

**시크릿 스캔.** 하네스 세 저장소의 추적 파일 · git 이력 전체 · Issues 본문 · 코멘트에서 실제 토큰 · 키 · 개인키는 없다.
있는 것은 자리표시자(`TOKEN=…` · `test-token-not-real`)와 사설 주소다 — 노드 대역 `10.18.1.x` · 서비스 대역 `10.18.100.x` · pod 대역 `10.244.x` · `*.svc.cluster.local` · 네임스페이스 이름(careerhub-prod · oidc-provider).
사설 주소는 인터넷에서 라우팅되지 않는다 — 드러나는 것은 주소가 아니라 내부 구성의 지도다.
obs-toolkit fixture 는 실제 prod 로그 · 트레이스를 담지만 이메일 · 외부 클라이언트 IP 는 없다.
`jyo-liar.com` 도메인과 `id.careerhub.jyo-liar.com` 이 docs · fixture 에 나온다 — 이미 공개 노출된 주소다.

**참조 저장소 넷의 스캔.** jyoliar-k8s(301 파일 · 216 커밋) · onpremise-k8s(123 · 53) · jyoliar-platform-terraform(73 · 27) · goutils(55 · 76).
secret 이름의 매니페스트는 전부 ExternalSecret · ECRAuthorizationToken 선언이고 값이 없다.
terraform 의 secret 은 변수 참조다.
git 이력에 개인키 · AWS 키 · GitHub 토큰 패턴 0건.
onpremise-k8s 문서에 Tailscale `100.x` 주소가 있다 — tailnet 밖에서 닿지 않는다.
jyoliar-k8s 매니페스트 세 곳에 이메일 주소(Argo CD RBAC · cert-manager issuer · prometheus-operator patch).

**결함을 적은 문서.** 알려진 결함 목록은 사설 주소보다 직접적인 단서라 따로 봤다.
homelab `261029_1359`(done) · `261029_1413`(active) — 공개 전 패치 범위는 4-2 판정으로 oidc nginx · cloudflared · NGF 까지이고, 셋은 패치 완료다(사람 확인, 2026-10-31). 4-3 · 4-4(데이터 계층 · EOL 라인)는 공개 뒤로 판정됐다.
careerhub `260804_1735` · `260805_1323`(auth-service 결함 · ASVS 격차, active) — `261026_1610` 이 `/auth` 룰 제거로 auth-service 를 인터넷에서 닿지 않게 했고(#138, closed), ADR-0028 이 인증을 외부 IdP 로 위임했다.
결함 문서 넷 중 공개 전에 남는 패치는 없다.

**살아 있는 링크의 후보.** 공개 노출 Feature #133 과 리프 #135 ~ #141 은 전부 closed 이고 대상이 jyoliar-platform-terraform · jyoliar-k8s · careerhub 서비스다.
obs-toolkit 의 tdd-loop 티켓(#94 · #102 · #109 · #111 · #119 · #120)은 대상이 jyoliar-lab 안에 있다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 입구

**선택: 이력서는 조직 링크 하나만 두고, 독자는 Overview 에서 저장소로 내려간다.** Overview 가 첫 페이지이고 저장소 README 는 두 번째 페이지다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 이력서가 저장소를 직접 링크 — 저장소 README 가 입구가 되어 세 README 모두 외부인용 서두가 필요해진다
- 둘 다 — 두 페이지 모두 첫 페이지일 수 있어 분담이 흐려진다

</details>

### 3-2. 기존 README

**선택: 세 저장소의 README 는 그대로 둔다.** 운영자용 구조 안내로 남기고 외부인용 설명은 Overview 가 전부 맡는다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- README 를 외부인용으로 다시 쓰고 운영 안내는 별도 파일로 — 운영 안내가 밀려나고 두 저장소를 고쳐야 한다
- README 상단에 외부인용 절을 더한다 — 같은 내용이 Overview 와 README 두 곳에 생겨 한쪽만 고쳐진다

</details>

### 3-3. Overview 와 README 의 분담

**선택: Overview 는 "왜 · 전체 구조 · 한 사이클 · 강제의 원칙 · 정책 변경의 길" 을, README 는 "그 저장소 안의 구조 · 여는 법 · 강제의 구현 위치" 를 맡는다.** 독자가 README 를 열 때는 Overview 에서 그 저장소가 무엇이고 왜 있는지를 이미 읽은 뒤라는 전제다. (인터뷰, 2026-10-31)

| 내용 | Overview (`.github/profile/README.md`) | 저장소 README (현재 그대로) |
|---|---|---|
| 조직이 무엇인지 · 운영 기간 | 한 문단 | — |
| 겪은 문제 여섯 → 설계 응답 | 각 두 줄 | — |
| 세 층 그림 — steward / ops-workflow(두 플레인 · design-partner · adr-judge) / ticket-engineer | 그림 하나 + 역할 표(역할 · 저장소 · 세션 단위 · 모델 · 쓸 수 있는 곳) | 자기 저장소의 디렉터리 트리 · 역할 표 |
| 한 사이클 — 논의 → ADR → 티켓 → 착수 게이트 → TDD → PR → 보고 → 다이제스트, 사람 승인 지점 | 단계마다 실제 ADR · 티켓 · PR 링크 하나 | — |
| 구조로 강제한다는 원칙 | 원칙과 대표 예 셋(hook 거부 · exit 코드 게이트 · 읽기 전용 RBAC), 거부 메시지 인용 하나 | "구조로 강제하는 것" 표 — 무엇을 어느 파일이 막나 |
| 정책은 어떻게 바뀌나 — 정책 ADR 이 proposed 로 남는 이유 · 롤백 원장 | 한 절 | steward README 의 "ADR 의 흐름에서 steward 가 서는 자리" |
| 세션 여는 명령 · `--add-dir` · 로컬 설정 · PATH | — | 본문 |
| 저장소 안내 넷(ops-workflow · ticket-engineer · ops-workflow-steward · obs-toolkit) | 한 줄씩 + 링크 | — |
| 한계와 배운 것 | 두세 줄 | — |

Overview 가 가리키는 링크의 대상은 ADR · 티켓 · PR · hook 파일의 특정 줄이고, README 는 링크 대상이 아니라 저장소 첫 화면으로만 만난다.

### 3-4. 언어

**선택: 한국어만.** 이력서가 국내 구직용이고 ADR · discussion 전부가 한국어다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 한국어 + 영어 요약 한 단락 — 요약만 영어면 그 뒤를 못 읽는 독자에게 반쪽이다
- 둘 다 전문 — 유지 비용이 두 배다

</details>

### 3-5. 수치

**선택: Overview 에 운영 수치(ADR 수 · 티켓 수 · PR 수 · 기간)를 넣지 않는다.** 상시 갱신 없이는 낡고, 이 코퍼스는 생존형 문서를 두지 않는다(CLAUDE.md §3). 수치는 이력서에만 있고 Overview 는 Issues · docs 링크로 대신한다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 기준일과 함께 넣는다 — 이력서를 고칠 때마다 두 곳을 고친다
- 기간만 — 시작 월은 조직 저장소의 첫 커밋이 이미 말한다

</details>

### 3-6. steward 의 자리

**선택: 그림에 넣되 사이클 위의 층으로 그린다.** steward 도 public 이 되므로 빼면 "정책은 누가 바꾸나" 가 빈다. design-partner · adr-judge · ticket-engineer 는 정책에 매이는 쪽이고 steward 는 밖에서 고치는 쪽이라는 지위 차이가 그림에서 읽혀야 한다 — 네 역할을 같은 높이에 두면 그 차이가 사라진다. 층 사이 화살표는 둘뿐이다 — steward → 두 하네스로 "정책 전파", ticket-engineer → ops-workflow 로 "보고 · 마찰 로그". (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- steward 를 그림에서 빼고 "프로세스 자기진화" 한 문단으로만 — steward 저장소가 공개되는데 그림에 없으면 어색하다

</details>

### 3-7. Issues 공개

**선택: 사설 주소 · 클러스터 내부 주소는 그대로 두고, 결함 문서가 말하는 패치 상태만 사람이 확인한 뒤 공개한다.** 사설 주소는 밖에서 닿지 않고, 드러나는 지도는 공개 입구가 뚫린 뒤에야 쓸모가 있다 — 개인 홈랩 기준으로 감수한다. 확인은 §2 에서 끝났다 — 공개 전 패치 셋 완료. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 결함 문서가 가리키는 패치를 전부 끝내고 공개 — 4-3 · 4-4 는 공개 뒤로 이미 판정됐고, 공개 전환이 데이터 계층 이전에 묶인다
- 전수 검토 후 공개 — 이슈 137건 · 코멘트 193건을 사람이 훑는 비용에 비해 스캔이 이미 실제 시크릿 0건을 보였다
- 점검 없이 공개 — 결함 문서의 패치 상태는 확인할 가치가 있었다

</details>

### 3-8. 범위

**선택: 공개 전환 점검을 이 논의에 넣는다. obs-toolkit README · 이력서의 링크 문구 · obs-bench 는 뺀다.** obs-bench 는 시작 전이라 private 로 남고 Overview 에도 적지 않는다 — 비어 있는 private 저장소를 "준비 중" 으로 적으면 궁금증만 남긴다. (인터뷰, 2026-10-31)

## 4. 열린 축 — 논의

### 4-1. 참조 저장소의 공개 범위

실측: 인프라 셋과 goutils 는 스캔이 깨끗하다(§2).
careerhub 서비스 11개는 스캔하지 않았다 — 공개 여부가 먼저다.
티켓 137건 중 다수가 careerhub 서비스를 대상으로 하므로, careerhub 가 private 이면 그 티켓의 PR 링크는 외부인에게 죽은 링크다.
세 역량 중 AX 의 증거는 하네스 셋 · 티켓 · obs-toolkit 이고, DevOps 의 증거는 인프라 셋이며, 백엔드만 careerhub 코드에 걸린다.
저장소 공개는 one-way door 다 — private → public 은 언제든 가능하지만, public → private 은 fork · 캐시 · 클론을 되돌리지 못한다.

- **A. 인프라 셋(jyoliar-k8s · onpremise-k8s · jyoliar-platform-terraform) + goutils, careerhub 는 "비공개 · 요청 시 열람"** — 유사 서비스 걱정이 남아 있는 한 이긴다 / 면접에서 백엔드 코드를 요구하는 신호가 반복되면 진다 — 그때 B 로 넓히면 된다
- B. A + 비핵심 careerhub(계약 · 스펙만 담은 posting-provider, 프런트 careerhub-web · careerhub-front, 레거시 auth-service) — 백엔드 코드를 일부 보이면서 데이터 수집 · 가공(crawler · skillscanner · review-service)은 닫는다 / 어느 것이 "비핵심" 인지 저장소마다 사람이 가려야 한다
- C. 전부 공개 — 설득력은 가장 크다 / 유사 서비스 걱정이 현실이 되면 되돌릴 수 없다. 걱정 때문에 열지 않은 손해는 없고, 설득력 때문에 열었다가 생기는 손해는 있다
- D. 안 한다 — 하네스 셋 + obs-toolkit 만 — DevOps 역량의 코드 증거가 없고, 공개 노출 Feature #133 트리의 PR 링크가 전부 죽는다

**판정(사람, 2026-10-31): A. careerhub 는 비공개 · 요청 시 열람. 면접에서 코드 요구가 반복되면 B 로 넓힌다.**

### 4-2. 공개의 순서

실측: Overview 의 링크는 public 저장소를 전제한다.
`.github` 저장소는 아직 없다.

- **A. 저장소를 먼저 public 으로 돌리고 Overview 를 마지막에 게시한다** — Overview 가 뜨는 순간 링크가 전부 살아 있다 / 저장소가 먼저 열려 있는 기간에 Overview 없이 README 만 보인다 — 짧게 끝내면 무방하다
- B. `.github` 를 먼저 만들고 저장소 공개와 같은 날 게시 — 사람이 한 자리에서 끝낸다 / 순서를 어기면 죽은 링크가 잠시 보인다
- C. Overview 를 먼저 게시 — 링크가 죽은 채 보인다. 이길 조건이 없다

**판정(사람, 2026-10-31): A. 저장소 먼저, Overview 마지막.**

### 4-3. Projects 공개

실측: `Ops Workflow` 프로젝트는 private 이고, 저장소 공개로 열리지 않는다.
Overview 의 "한 사이클" 절이 Status(Todo · In Progress …)를 말하려면 보드가 보이는 편이 낫다.

- **A. 공개로 바꾼다** — 사이클 설명과 Status 어휘(ADR-0033)의 실물이 보인다 / 보드의 커스텀 필드 값까지 드러나지만 이슈가 이미 공개이므로 새 정보는 없다
- B. 비공개로 둔다 — Overview 는 Issues 목록으로만 링크한다 / Status 는 글로만 설명한다

**판정(사람, 2026-10-31): A. 공개로 바꾼다.**

## 5. 반대편 — 이 설계가 틀리는 조건

- Overview 는 이 코퍼스에 없던 생존형 문서다 — 수치를 뺐어도 구조 설명은 하네스가 바뀌면 낡는다. 역할 · 층 · 사이클이 바뀌는 ADR 이 나오면 Overview 를 고칠 사람이 없다는 것이 틀리는 조건이다.
- 3-2 · 3-3 은 "독자가 README 를 열 때 Overview 를 읽은 뒤" 를 전제한다 — 검색이나 공유로 저장소에 직접 들어온 독자는 "agent 는 읽지 않는다" 와 세션 여는 명령으로 시작하는 README 를 만난다. 그런 유입이 많으면 README 상단 한 단락(버린 안)이 되살아난다.
- 4-1 에서 A 를 고르면 티켓 다수의 PR 링크가 죽는다 — 독자가 티켓을 열어 보다 "증거가 없다" 고 느끼는 조건이다. Overview 의 예시 링크를 살아 있는 쪽(§2 마지막)에서 고르는 것이 완화책이고, 그래도 티켓 목록 전체는 그렇지 않다.
- 결함 문서는 패치됐어도 구조와 과거의 약점을 말한다 — 공개 노출 서비스의 설계 결함을 읽고 다음 약점을 추정하는 독자가 있다면 3-7 이 틀린다.
- 3-5 는 "수치는 이력서에" 를 전제한다 — 이력서 없이 Overview 만 보는 독자(검색 유입)에게는 규모가 보이지 않는다.

## 6. 버린 것

- README 를 외부인용 문서로 재편하는 길 — 입구가 Overview 로 정해지면서 필요가 사라졌다.
- 영어 병기 — 독자 · 코퍼스 언어와 어긋난다.
- 수치를 스크립트로 생성해 넣는 길 — 생성물을 Overview 에 심으면 갱신 책임이 다시 생긴다.
- Overview 에 규약(CLAUDE.md) 전문이나 도구 이름 나열 — 설명이 아니라 복제이고 낡는다.
- 이력서 문구를 Overview 에 그대로 옮기는 길 — 어필과 설명은 톤이 다르다.

## 7. 임계선 — ADR 감인가

ADR 감이 아니다.
저장소 공개는 one-way door 이지만 프로세스(정책)의 결정이 아니라 운영 결정이고, 분담표는 하네스를 구속하지 않는다.
공개 저장소를 전제로 docs · 티켓에 적어도 되는 것(사설 주소 허용 · 시크릿 금지 · 결함 문서의 취급)을 규칙으로 세울 필요가 생기면 그때 정책 ADR 이다 — 지금은 3-7 의 한 번의 판단이다.

## 8. 다음

- `.github` 저장소 생성과 `profile/README.md` 초안 — 3-3 의 왼쪽 열이 목차다. steward 의 쓰기 경계 밖이므로 사람이 열거나 일반 세션이 쓴다. 초안은 steward `staging/` 에 먼저 둔다.
- 공개 전환 Task 하나 — 항목은 §2 가 말한다: 공개 전 패치 셋 완료 확인(끝남) · jyoliar-k8s 의 이메일 세 곳 처리 여부 · 각 저장소의 `.claude/settings.local.json` 이 gitignored 인지 재확인 · Projects 공개(4-3) · 저장소 공개 순서(4-2).
- 참조 저장소 공개 — jyoliar-k8s · onpremise-k8s · jyoliar-platform-terraform · goutils(4-1 A).
- 세 README 는 바꾸지 않는다(3-2).
