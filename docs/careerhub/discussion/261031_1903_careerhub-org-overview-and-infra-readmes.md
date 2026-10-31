---
type: discussion
kind: deliberation
goal: public-face
topic: careerhub
subjects: [github-org-profile, readme, onpremise-k8s, jyoliar-k8s, jyoliar-platform-terraform, careerhub-front, auth-service, zitadel, careerhub-web, careerhub-incident-agent]
status: done
ref-adrs: [ADR-0028, ADR-0030]
related: [../../ops-workflow/discussion/261031_1601_public-face-overview-and-readmes.md, ../../ops-workflow/discussion/261031_1733_overview-workflow-narrative.md, 260717_1853_revenue-model-and-viability.md]
---

# 커리어허브 조직 Overview — 시작의 동기, 서비스·인프라 구조, 인프라 README 셋

## 1. 문제

이력서가 조직 둘을 가리키게 된다.
`jyoliar-lab` 의 Overview 는 일하는 방식을 적고(`261031_1733`), `jyoliar-careerhub` 의 Overview 는 시스템을 적는다 — 무엇을 왜 만들었고 어떻게 생겼나.
지금 `jyoliar-careerhub` 에는 Overview 가 없다.
공개할 인프라 저장소 셋의 README 는 외부 원본 그대로(onpremise-k8s) · 없음(jyoliar-k8s) · 제목뿐(jyoliar-platform-terraform)이다.
그리고 AWS 시대의 저장소 넷이 이미 public 이라 Overview 옆에 그대로 보인다.
정할 것은 넷이다 — Overview 의 절과 깊이, 이미 있는 서비스 흐름도의 취급, 세 README 의 성격, 옛 public 저장소의 처분.
시작의 동기와 홈랩 이전의 동기는 코퍼스 어디에도 없어 인터뷰로 받았다.

## 2. 실측

**GitHub 사양.** 조직 Overview 는 public 저장소 `.github` 의 `profile/README.md` 다.
`jyoliar-careerhub/.github` 는 이미 public 이고 내용은 `.github/workflows/build-and-push-ecr.yaml` 하나다 — `profile/` 이 없다.
조직 description 은 "해당 조직은 Jyo Liar가 Careerhub 프로젝트의 코드 및 저장소들을 별도로 관리하기 위하여 만들어졌습니다" 이고 Overview 위에 먼저 보인다.

**저장소 상태(2026-10-31).** 조직 저장소 22개 중 public 5 — `.github` · common-infra · careerhub-infra · k8s-config · goutils(fork).
넷은 AWS 시대의 것이고 archive 되지 않았다 — 마지막 push 는 careerhub-infra 2025-11-16.
docs · Issues 에 이 넷을 가리키는 링크는 0건이고, fork · star · watcher 도 0이다.
goutils fork 는 쓰이지 않는다 — 서비스 `go.mod` 일곱이 전부 `jae2274/goutils` 를 가리킨다.
jyoliar-k8s 는 `jyoliar-careerhub/jyoliar-k8s` 로 이관됐다(`.claude/ref-repos.txt` 의 `jae2274` URL 은 리다이렉트).

**README 상태.**

| 저장소 | README |
|---|---|
| onpremise-k8s | IBM `ansible-kubernetes-ha-cluster` 의 원본 README 그대로 — haproxy · keepalived · IBM clone URL. 현재 코드(kube-vip · 라즈베리파이 · Tailscale 워크스페이스)와 어긋난다 |
| jyoliar-k8s | 없음 |
| jyoliar-platform-terraform | 제목 한 줄 |
| careerhub-api-composer · careerhub-web | 계약 규약을 담은 본문 있음 |
| 나머지 서비스 아홉 | 없음 또는 제목 한 줄 |

**시작 시점(첫 커밋).** careerhub-front 2023-07 → posting-provider · posting-service 2023-12 → skillscanner 2024-02 → auth-service · api-composer · userinfo 2024-03 → review-service · review-crawler 2024-05.
인프라는 AWS 시대(common-infra 2025-02 · careerhub-infra · k8s-config 2025-04) → onpremise-k8s 2025-12 · jyoliar-k8s 2026-01 · jyoliar-platform-terraform 2026-02 순이다.
careerhub-web 은 2026-07 시작이고 배포되지 않았다.
careerhub-incident-agent 는 2026-05 의 PoC 커밋 넷이다.

**흐름도와 현재(careerhub-prod).** 흐름도의 서비스는 전부 지금도 돈다 — Deployment api-composer · auth-service · frontend(careerhub-front) · posting · review · userinfo, CronJob posting-provider-jumpit · posting-provider-wanted · posting-skillscanner · review-crawler.
posting · review · userinfo 는 MongoDB 를, auth-service 와 zitadel 은 PostgreSQL(CNPG pooler)을 쓴다.
흐름도에 없는 것은 zitadel · zitadel-login(2026-08-11 배포) · 공개 Gateway · 데이터 저장소다.
인증은 ADR-0028 · ADR-0030 으로 Zitadel 에 위임됐고, `261026_1610` 의 `/auth` 룰 제거(#138 · jyoliar-k8s#54)로 auth-service 는 인터넷에서 닿지 않는다.
따라서 흐름도의 "로그인을 통한 accessToken 발급" 화살표만 현재와 다르다.

**이미지 경로.** 태그 push → 조직 재사용 워크플로 → CodeBuild ARM 러너 → ECR 까지가 CI 이고, GitOps overlay 의 이미지 태그는 PR 로 올린다(jyoliar-k8s#55 · #56).

**인프라 서술의 재료.** 세 저장소가 각각 무엇을 선언하고 서로 무엇을 읽는가는 `tmp/resume-devops.md` 2-보 에 코드 경로와 함께 정리돼 있다.
`tmp/` 는 지식 플레인 밖이므로 초안을 쓸 때 코드로 다시 확인한다.

**onpremise-k8s 의 평문 키.** `kubernetes/inventory/baremetal:152` 에 apiserver Secret 암호화 키(`encoded_secret`)가 평문으로 있고, 2026-03-01 이후 한 값으로 git 이력과 `archive/aws-ec2` 태그에도 남아 있다.
`261031_1601` 의 시크릿 스캔은 개인키 · AWS 키 · GitHub 토큰 패턴만 봐서 이 base64 키를 잡지 못했다.
티켓 #73(Vault 분리 · 키 로테이션, Draft)이 이것을 다루고 2026-10-31 본문을 현행 규약으로 고쳤다.
로테이션이 끝나기 전에는 공개할 수 없다 — 이력의 구 키가 지금 etcd 를 여는 키다.

**이어받는 결정(`261031_1601`).** 한국어만(3-4) · Overview 에 운영 수치 없음(3-5) · 저장소 먼저 공개하고 Overview 마지막(4-2) · careerhub 서비스는 비공개 · 요청 시 열람(4-1 A).
lab Overview 의 코드 저장소 행은 조직이 아니라 인프라 저장소 셋을 직접 링크한다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 입구

**선택: 이력서가 `jyoliar-careerhub` 조직을 직접 링크한다.** Overview 가 첫 페이지다. lab Overview 는 고치지 않는다 — 거기서는 저장소 셋을 직접 링크한 채로 둔다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- lab Overview 의 코드 저장소 행이 조직을 가리키게 바꾼다 — lab 을 먼저 읽는 독자만 전제하게 된다
- 둘 다 — 분담이 흐려진다

</details>

### 3-2. 시작의 동기

**선택: 둘이다 — 내가 쓰려고(Wanted · JumpIt 공고를 한 자리에서 보고 TeamBlind 리뷰를 옆에 붙인다), 그리고 기술 학습(gRPC · MSA · 배치 · k8s 를 직접 겪는다).** 코퍼스에 없던 사실이라 인터뷰로 받았다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 취업 포트폴리오 — 출발점이 아니었다
- 수익화 — `260717_1853` 이 그 전제를 무너뜨렸고 출발점도 아니었다

</details>

### 3-3. 홈랩 이전의 동기

**선택: 비용.** AWS 월 비용이 사이드 프로젝트로 감당하기 어려웠다. Overview 에는 AWS 시대를 이 한 줄로만 말한다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 베어메탈 운영 학습 — 결과이지 동기가 아니다
- 클라우드 종속 없는 구조 실험 — 같다
- AWS 시대를 언급하지 않는다 — 옛 public 저장소의 전사가 없으면 이전이 설명되지 않는다

</details>

### 3-4. 절 순서

**선택: 동기 → 서비스 구조 → 인프라 구조 → 저장소 안내.** 무엇을 만들었나 다음에 어디에 올렸나이고, 저장소 표는 마지막이다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 저장소 안내를 앞에 — lab 방식이지만 여기서는 시스템 설명이 먼저다
- 인프라를 먼저 — 공개 저장소가 인프라 셋이라는 이유였으나 독자가 알고 싶은 것은 서비스가 먼저다

</details>

### 3-5. 서비스 절과 흐름도

**선택: 흐름도는 그대로 넣는다. 본문이 "현재 공개된 레거시 careerhub 중심의 흐름이고, 보안 강화를 위해 인증은 막았으며 Zitadel 로 인증을 위임하는 리뉴얼이 진행 중" 이라고 말한다.** 흐름도의 범례(데이터 통합 API · gRPC/REST · 배치 · 외부 수집 사이트)가 서비스 절의 분류다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 캡션 한 줄만 — 리뉴얼이 진행 중이라는 사실은 본문의 것이다
- 사람이 그림을 갱신 — 레거시 흐름이 지금 공개된 것이고 리뉴얼은 끝나지 않았다
- 캡션 없이 — auth 화살표가 현재와 다르다는 것을 독자가 알 길이 없다

</details>

### 3-6. 인프라 절의 구성

**선택: 소절 둘 — ① 현재 홈랩 내부 인프라 구성, ② AWS · Cloudflare · GitHub Actions · 홈랩 인프라 간 상관관계.** 세 저장소의 역할과 의존 방향은 ②에 녹인다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 저장소 셋의 역할과 의존 방향만 — 관점이 저장소 하나뿐이다
- 설계 결정 서너 개와 이유 — 어필이지 설명이 아니다
- 하드웨어 구성 — 3-8 에서 대수를 뺐다

</details>

### 3-7. 그림

**선택: 인프라 절에는 그림이 없다.** 그림은 서비스 흐름도 하나뿐이다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 둘 다 사람이 그린다 — 유지할 그림이 셋이 된다
- Mermaid — 흐름도 이미지와 스타일이 다르다
- 상관관계 절만 그림 — 글로 충분하다

</details>

### 3-8. 구체성

**선택: 컴포넌트 이름만 적는다. 대수 · 버전은 뺀다.** "라즈베리파이 여러 대의 HA 클러스터" 수준이고, 대수는 인벤토리가 · 버전은 코드가 말한다. lab 의 3-5 와 같은 이유다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 대수와 컴포넌트 이름까지 — 노드를 더하면 낡는다
- 대수 · 컴포넌트 · 버전 전부와 기준일 — 갱신 책임이 생긴다

</details>

### 3-9. 범위 밖

**선택: careerhub-incident-agent · jyoliar-lab 링크는 넣지 않는다. careerhub-web 은 서비스 구조 절에는 넣지 않되 저장소 표에는 공개 저장소로 넣는다. 관측 스택(Prometheus · Loki · Tempo · Alloy)은 홈랩 내부 구성에 넣는다.** PoC 는 "준비 중" 이 되고, 일하는 방식은 이 Overview 의 주제가 아니다.
미배포 리뉴얼 프런트는 흐름도에 없으니 서비스 절에서는 빼되, 공개 저장소인데 표에서 빠지면 조직의 저장소 목록과 표가 어긋나 보인다. (인터뷰, 2026-10-31. 처음에는 careerhub-web 도 전부 뺐으나 서비스 저장소를 공개로 돌리면서 저장소 표에만 넣었다)

### 3-10. 세 README

**선택: onpremise-k8s · jyoliar-k8s · jyoliar-platform-terraform 셋 다 새로 쓴다. 성격은 운영자용 구조 안내 — 디렉터리 · 환경(Ansible 워크스페이스 · 인벤토리 · overlay · Terraform 워크스페이스) · 반영 방법 · 다른 두 저장소에서 받는 것. Overview 링크는 두지 않는다.** onpremise-k8s 는 IBM 원본을 전면 교체한다. 서비스 저장소 README 는 비공개이므로 건드리지 않는다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- 외부인 소개 한 단락 + 운영자용 — Overview 와 겹친다
- 외부인용 중심 — 입구가 Overview 라 필요가 없다
- 공개 셋 + 서비스 11개 — 비공개 저장소의 README 는 지금 독자가 없다

</details>

### 3-11. 옛 public 저장소 넷

**선택: common-infra · careerhub-infra · k8s-config · goutils(fork)를 private 으로 돌린다.** 실측(§2)에서 가리키는 링크 · fork · star 가 0 이라 죽는 것이 없다. (인터뷰, 2026-10-31)

<details><summary>버린 안</summary>

- archive — "옛 것" 표시가 붙어도 조직 페이지에 남아 공개 셋과 섞인다
- 그대로 — Overview 가 설명하지 않는 저장소가 넷 보인다

</details>

### 3-12. 저장소 안내의 비공개 표기

**선택: 저장소 절을 인프라 저장소 · 애플리케이션 저장소 두 표로 나눈다. 애플리케이션 표는 저장소 · 그림에서 · 역할 세 열로 흐름도의 이름과 저장소를 1:1 로 잇고, 공개 여덟은 링크, 수집 배치 둘(careerhub-posting-provider · careerhub-review-crawler)은 이름만 링크 없이 두고 "비공개" 와 이유 한 문장을 적는다.** 이유는 수집 대상 사이트(Wanted · JumpIt · TeamBlind)의 부하다 — 수집 코드가 퍼지면 그 사이트들에 뜻하지 않은 부하를 줄 수 있다. (인터뷰, 2026-10-31. 처음에는 서비스 11개를 전부 "비공개 · 요청 시 열람" 으로 두었으나, 공개 전 시크릿 스캔(전 이력 · 실값 0건)을 거쳐 서비스 저장소도 공개로 돌리기로 하면서 수집 배치 둘만 비공개로 남겼다)

<details><summary>버린 안</summary>

- 공개 셋만 표에 — 서비스와 저장소의 대응이 안 보인다
- 서비스 11개 전부 비공개 · 요청 시 열람 — 공개할 수 없는 이유가 없었다. 스캔으로 확인했다
- 수집 배치 둘도 공개 — 코드 자체보다 코드가 퍼진 뒤 수집 대상 사이트가 받는 부하가 문제다. 비공개 이유는 숨길 것이 아니라 Overview 에 적는다

</details>

### 3-13. 조직 description

**선택: Overview 첫 문장과 맞춘 한 줄로 바꾼다.** 문구는 초안에서 정한다. (인터뷰, 2026-10-31)

### 3-14. 이어받는 것

**선택: 한국어만 · 운영 수치 없음 · 저장소 먼저 공개하고 Overview 는 마지막. 단 onpremise-k8s 는 #73 이 close 된 뒤에 공개하고, 그 전의 Overview 는 저장소 표에 "공개 예정" 과 #73 링크로 적는다.** `261031_1601` 의 3-4 · 3-5 · 4-2 를 그대로 쓴다. 같은 문서의 4-1 A(careerhub 서비스 비공개)는 이어받지 않고 3-12 로 대체한다. 공개 순서에 3-11 의 private 전환이 앞에 붙는다. (인터뷰, 2026-10-31. 처음에는 인프라 셋을 함께 공개하려 했으나 평문 키(§2)가 드러나 onpremise-k8s 를 뒤로 뺐다)

## 4. 열린 축 — 논의

없음.
축이 전부 의도 · 범위 · 취향에서 닫혔고, 사실이 필요했던 둘(옛 public 넷의 죽은 링크, 흐름도와 현재의 차이)은 실측이 전제를 확인만 했다.

## 5. 반대편 — 이 설계가 틀리는 조건

- Overview 는 생존형 문서다. "리뉴얼 진행 중" 문장과 흐름도의 auth 화살표는 Zitadel 전환이 끝나거나 careerhub-web 이 배포되면 낡는다. 그때 고칠 사람이 없다는 것이 틀리는 조건이다 — lab §5 와 같다.
- 컴포넌트 이름(3-8)도 낡는다. Longhorn 이 Rook-Ceph 를 대체했듯 이름은 바뀐다 — 대수보다 느릴 뿐이다.
- "비용" 한 단어(3-3)는 설계 동기를 말하지 않는다. 독자가 "클라우드를 못 쓰는 사람" 으로 읽으면 베어메탈 IRSA · 무포트 공개 같은 설계가 궁여지책으로 보인다.
- careerhub-web 을 빼면(3-9) 리뉴얼이 인증뿐인 것으로 읽힌다. 계약 우선(ADR-0018 ~ 0021)과 새 프런트가 리뉴얼의 절반이다.
- jyoliar-lab 링크가 없으면(3-9) 일하는 방식에 관심 있는 독자는 이력서로 돌아가야 한다.
- 입구가 이력서 하나(3-1)라 lab Overview 에서 저장소 셋으로 바로 내려간 독자는 이 Overview 를 지나친다.
- 세 README 에 Overview 링크가 없으면(3-10) 검색으로 저장소에 직접 들어온 독자는 "왜" 를 찾지 못한다.

## 6. 버린 것

- lab Overview 에 careerhub 절을 더하는 길 — 조직이 둘이고 주제가 다르다(일하는 방식 / 시스템).
- 세 README 를 외부인용으로 — 입구가 Overview 로 정해지면서 필요가 사라졌다.
- 서비스 저장소 README 정비 — 공개로 돌리지만 이 논의의 범위는 인프라 셋이다. 필요하면 별도 논의.
- 흐름도 갱신 — 레거시 흐름이 공개된 현재이고 리뉴얼은 진행 중이다.
- 인프라 그림 — 글과 표로 충분하다.
- 설계 결정을 "왜" 와 함께 — 이력서의 어필이지 Overview 의 설명이 아니다(`tmp/resume-devops.md` 는 그쪽에 쓴다).

## 7. 임계선 — ADR 감인가

ADR 감이 아니다.
public → private 전환은 되돌릴 수 있는 방향이고(반대 방향이 one-way door 다), Overview · README · description 은 전부 한 시간 안에 고쳐진다.
`261031_1601` §7 과 같다.

## 8. 다음

- Overview 초안 `profile/README.md` — 3-4 의 순서로, `jyoliar-careerhub/.github` 의 로컬 클론에 쓴다(lab 과 같은 방식). 흐름도 이미지는 `profile/` 아래 파일로 사람이 올린다. 커밋은 사람 승인 뒤.
- 조직 description 한 줄 — 초안의 첫 문장이 정해지면 사람이 GitHub 설정에서 바꾼다.
- 옛 public 넷 private 전환 → jyoliar-k8s · jyoliar-platform-terraform public 전환 → Overview 게시 — 전부 사람. 순서는 3-14.
- 서비스 저장소 여덟(careerhub-front · careerhub-web · careerhub-api-composer · careerhub-posting-service · careerhub-review-service · careerhub-userinfo-service · auth-service · careerhub-posting-skillscanner)의 public 전환 — 사람. 수집 배치 둘은 private 로 둔다(3-12). 공개 전 스캔은 2026-10-31 에 전 이력 대상으로 마쳤고 실값은 없었다.
- onpremise-k8s 공개는 #73(Vault 분리 · 키 로테이션) close 뒤다. 공개 시점에 Overview 저장소 표의 "공개 예정" 을 링크로 바꾼다. #73 의 집행 순서는 그 티켓의 작업 가이드 코멘트에 있다.
- README 셋 — 코드 저장소 쓰기이므로 티켓이다. 한 Task 에 target 셋이거나 저장소별 Task 셋 — 검수 단위가 저장소마다 다르면 셋이다. onpremise-k8s 는 IBM 원본 교체.
- lab Overview 는 바꾸지 않는다(3-1).
