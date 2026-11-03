---
type: discussion
kind: deliberation
goal: careerhub-env-separation
topic: homelab
subjects: [terraform-cloud, tfe-provider, variable-set, jyoliar-platform-terraform, aws-tags]
status: done
ref-adrs: []
related:
  - docs/homelab/discussion/261103_1809_tfe-project-variable-set-provider-survey.md
  - docs/homelab/discussion/261103_1429_terraform-restructure-migration-plan.md
---

# Terraform Cloud 프로젝트 · variable set 재설계 — env는 프로젝트가 주고, 태그는 남긴다

## 1. 문제

jyoliar-platform-terraform의 모든 AWS 루트는 `provider "aws" { default_tags { tags = { env = var.env } } }`로 리소스마다 `env` 태그를 붙인다.
`env`·`region` 값은 워크스페이스 변수가 아니라 프로젝트에 걸린 variable set이 주입한다.
그런데 프로젝트가 `onpremise`(공유 4 · 실험 2 · careerhub-oauth)와 `prod-careerhub`(backup · zitadel) 둘이라, 공유·실험 리소스가 전부 `env = onpremise`를 받는다.
AWS 콘솔에서 태그만 보면 IAM Role과 VPC가 같은 소속으로 읽히고, 어느 디렉터리의 코드가 만들었는지 알 수 없다.

앞선 이행 계획은 공유 루트의 `env` 변수와 `default_tags`를 지우는 것으로 이 거짓 분류를 풀려 했다(#155).
이번에 사람이 그 길을 접었다 — terraform 없이 AWS 리소스만 봐도 소속을 읽을 수 있어야 하므로 태그는 남겨야 한다.
그러면서 워크스페이스마다 `env` 변수를 하나씩 두는 것도 피하려 한다.
남는 길은 **프로젝트를 다시 그려 프로젝트 = `env` 값의 단위로 만들고, variable set을 `tfc/`가 선언하는 것**이다.

열려 있던 것은 프로젝트를 가르는 축, 공유·실험 리소스의 `env` 값, 더 붙일 태그, variable set의 거처, 그리고 기존 프로젝트·variable set을 새 모양으로 옮기는 방법이었다.
앞의 넷은 인터뷰에서 닫혔고 마지막 하나가 열린 축이다.

## 2. 실측

읽은 저장소: `workspace/ref/jyoliar-platform-terraform` (PR #10 머지 시점, 2026-11-03).

- 프로젝트 셋이 `tfc/projects.tf`에 선언돼 있다 — `Default Project`(tfc 자신), `onpremise`, `prod-careerhub`.
- 워크스페이스 소속 — `onpremise`: `shared-alert`·`shared-ci`·`shared-cloudflare`·`shared-iam`·`lab-vpc`·`lab-vpn`·`careerhub-oauth`. `prod-careerhub`: `prod-careerhub-backup`·`prod-careerhub-zitadel`. `Default Project`: `tfc`. (`tfc/ws-shared.tf`·`ws-lab.tf`·`ws-envs.tf`·`ws-tfc.tf`)
- variable set은 코드에 없다. `tfc/ws-shared.tf` 주석 — "env · region 은 워크스페이스 변수가 아니라 variable set(onpremise 프로젝트 `common_vars`)으로 주입된다 — variable set 은 이 저장소 밖 워크스페이스와 공유되는 조직 수준 객체라 여기서 선언하지 않는다."
- 콘솔의 값(사람, 2026-11-03) — `common_vars`: `env = onpremise`, `region = ap-northeast-2`. `prod`: `env = prod`, `region = ap-northeast-2`.
- 저장소 밖에서 두 프로젝트·variable set을 쓰는 워크스페이스가 있는지는 콘솔을 봐야 안다 — 미확인.
- AWS provider를 쓰는 8개 루트의 `default_tags`는 전부 `env = var.env` 한 줄이다. `shared/cloudflare`에는 `default_tags`가 없다. 리소스 쪽 태그는 `Name`만 더 있다.
- `var.env`의 태그 밖 사용 — `shared/*`: 없음. `lab/vpc/main.tf`: `"${var.env}-common-vpc"`·`"${var.env}-core"`가 모듈 `name`으로 들어가 **Name 태그**에만 쓰인다. `lab/vpn/main.tf`: 리소스가 전부 주석이다. `envs/prod/careerhub-backup/data.tf`: 버킷·네임스페이스 이름이 `var.env`에서 파생된다(prod는 값이 바뀌지 않는다).
  → 공유·실험 루트의 `env` 값을 바꾸면 plan은 태그 update in-place뿐이다.
- `oauth/`의 두 SSM 파라미터 경로는 `.../careerhub/prod/...`·`.../admin/prod/...`인데 워크스페이스는 `onpremise` 프로젝트라 `env = onpremise` 태그를 달고 있다.
- `tfc/_modules/workspace`의 `tfe_variable`은 워크스페이스 변수만 만든다 — variable set 변수는 아직 선언할 자리가 없다.
- provider 사실(조사 문서) — 프로젝트 개명·워크스페이스의 프로젝트 이동은 in-place, variable set·변수·프로젝트 연결은 import 가능, 조직 소유 set을 프로젝트 소유로 바꾸는 것만 재생성, 워크스페이스 변수가 set 값을 덮고 `priority = true`가 그것을 막는다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 프로젝트를 가르는 축

**선택: 디렉터리 트리 그대로 — `shared` · `lab` · `prod-careerhub` · (뒤에) `stg-careerhub`, `tfc`는 `Default Project`.** 프로젝트 이름이 트리의 좌표와 같아 variable set 하나 = 디렉터리 묶음 하나 = `env` 값 하나가 된다. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- 환경만으로(`shared`·`lab`·`prod`·`stg`) — 프로젝트 수는 적지만 다른 앱이 생기면 같은 `prod`에 섞이고, `envs/<env>/<app>` 트리와 어긋난다
- 공유·실험을 한 프로젝트로 — `env` 태그가 둘에 같은 값이 되어 shared와 lab이 구별되지 않는다

</details>

### 3-2. 공유·실험 리소스의 `env` 태그 값

**선택: `shared` · `lab`.** 디렉터리 이름 그대로라 태그만 보고 코드의 어디인지 찾을 수 있다. 변경은 태그 in-place update다(§2). (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- `onpremise` 유지 — 바꿀 것은 없지만 shared와 lab이 구별되지 않고 디렉터리 이름과 어긋난다
- shared만 바꾸고 lab은 `onpremise` — "AWS 모의 온프레미스"라는 뜻은 살지만 이름 체계가 둘이 된다

</details>

### 3-3. `env` 외의 공통 태그

**선택: `env` + `managed_by = terraform`.** 콘솔에서 손으로 만든 리소스와 갈린다. `managed_by`는 상수라 variable set이 아니라 각 루트 `default_tags`의 리터럴로 적는다 — 변수로 받으면 8개 루트에 `variable "managed_by"`를 더하는 일만 늘고 값은 같다. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- `env`만 — 루트 코드를 안 건드리지만 손으로 만든 리소스와 구별되지 않는다
- `env` + `workspace` — 어느 루트가 만들었는지까지 보이지만 루트별 리터럴(또는 `TFC_WORKSPACE_NAME` 읽기)이 필요해 8개 루트를 더 깊이 건든다

</details>

### 3-4. variable set의 거처

**선택: `tfc/`가 선언한다 — 객체·프로젝트 연결·값(`env`·`region`)까지.** 전부 비밀이 아닌 값이다. stg 환경 추가가 프로젝트 하나 + variable set 하나 + 워크스페이스 선언의 PR 하나가 된다. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- 객체·연결만 코드, 값은 콘솔 — `env` 값이 코드에 없어 "이 프로젝트가 무슨 env인가"를 콘솔이 답한다
- 전부 콘솔 — 지금과 같다. 프로젝트만 다시 그리고 variable set은 손으로 맞춘다

</details>

### 3-5. 이번에 다루지 않는 것

**선택: 저장소 밖 워크스페이스의 처리 · `region` 같은 바뀌지 않는 변수의 통합 · 워크스페이스 이름 재정리 · 프로젝트 수준 설정(알림·팀 권한).** 밖 워크스페이스는 콘솔 확인 뒤 있으면 별도의 일이고, 여기서는 variable set을 코드로 가져올 수 있는지만 받는다. (인터뷰, 2026-11-03)

## 4. 열린 축 — 논의

### 4-1. 기존 프로젝트 · variable set을 새 모양으로 옮기는 길

실측: 프로젝트 개명과 워크스페이스의 프로젝트 이동은 in-place다. variable set·변수·프로젝트 연결은 import된다. `common_vars`·`prod`를 저장소 밖 워크스페이스가 쓰는지는 미확인이다.

- **A. `onpremise`를 `shared`로 개명하고 `common_vars`를 import해 `env`를 `shared`로 바꾼다. `lab` 프로젝트·variable set은 신설하고 `lab-*` 둘을 옮긴다.** — 객체 수가 가장 적고 삭제가 없다 / 밖 워크스페이스가 `common_vars`에 붙어 있으면 그 쪽 `env`가 `onpremise`에서 `shared`로 바뀐다. 콘솔 확인이 선행이다.
- **B. `shared`·`lab` 프로젝트와 variable set을 신설하고 이 저장소의 워크스페이스를 옮긴다. `onpremise`·`common_vars`는 비면 삭제하고, 밖 워크스페이스가 남아 있으면 그대로 둔다.** — 기존 객체를 건드리지 않아 밖 워크스페이스와 무관하게 진행된다 / 객체가 둘 더 생기고 `onpremise`가 빈 껍데기로 남을 수 있다. `prod`는 어느 안이든 import다.
- C. 안 한다 — 프로젝트는 그대로 두고 `managed_by`만 더한다. 공유·실험 리소스가 계속 `env = onpremise`를 달고, stg 추가 때 프로젝트·variable set을 콘솔에서 손으로 만든다.

두 안 모두 `careerhub-oauth`는 `prod-careerhub`로 옮긴다 — 파라미터 경로가 `prod`이고, 그래야 `onpremise`가 빌 수 있다(4-2).
두 안 모두 `env`·`region` set에 `priority = true`를 둔다 — 워크스페이스에 남은 같은 키의 변수가 조용히 이기는 것을 막는다.
set의 소유는 4-3이 정한다 — 4-1의 두 안은 소유와 무관하게 성립한다.

**판정(사람, 2026-11-03): B. 불필요해진 `onpremise` 프로젝트는 destroy가 아니라 `removed` 블록으로 관리에서 제외해 코드에서 없앤다 — 객체는 콘솔에 남는다.**

### 4-2. `careerhub-oauth` 워크스페이스의 소속 — 해체되기 전까지

실측: `oauth/`는 Feature #152의 뒤 Task(#157·#158)에서 비워지고 삭제된다. 그때까지 어느 프로젝트에 두는가가 `onpremise` 삭제 시점을 정한다.

- **A. 이번에 `prod-careerhub`로 옮긴다** — 두 파라미터가 `env = prod` 태그를 받아 경로와 맞고, `onpremise`를 바로 비울 수 있다 / plan에 태그 update 두 건이 더 보인다
- B. `onpremise`에 남겨 두고 해체 뒤 프로젝트를 지운다 — 이번 작업이 작아진다 / `onpremise`·`common_vars`가 #158까지 살아 있어야 하고, 그 사이 트리와 프로젝트가 어긋난 상태가 지속된다
- C. `shared`로 옮긴다 — 프로젝트 하나를 덜 쓴다 / careerhub prod의 파라미터에 `env = shared`가 붙어 분류가 또 거짓이 된다

**판정(사람, 2026-11-03): A.**

### 4-3. variable set의 소유 — 조직인가 프로젝트인가

실측: 적용(어느 프로젝트가 받나)과 소유(누가 관리하나)는 다른 축이다.
어느 소유든 set은 `tfe_project_variable_set`으로 프로젝트에 붙고 그 프로젝트의 모든 워크스페이스가 `env`·`region`을 받는다.
프로젝트 소유 set은 그 프로젝트 밖에 붙일 수 없다. 조직 소유 set은 어느 프로젝트에든 붙는다.
`parent_project_id`는 `ForceNew`라 콘솔에서 조직 소유로 만든 기존 `prod`를 import한 뒤 프로젝트 소유로 바꾸면 재생성이다.
variable set은 state도 비밀도 없는 값 두세 개짜리 객체라 재생성 비용은 `tfc` apply 한 번이고, 그 사이 run이 돌지 않으면 영향이 없다.

- **A. 프로젝트 소유** — 새 set 전부 `parent_project_id`를 둔다. `prod`는 import하지 않고 재생성한다. "프로젝트 = `env` 값의 단위"가 객체 소속으로 드러나고, 다른 프로젝트에 잘못 붙이는 일이 구조적으로 막힌다 / `region`처럼 전 프로젝트가 같은 값은 프로젝트마다 복제된다. `prod` 재생성 동안 `prod-careerhub`에 `env`가 비는 창이 잠깐 생긴다
- B. 조직 소유 — 기존 `prod`를 import하고 새 것도 조직 소유로 만든다. 재생성이 없다 / 어느 프로젝트에든 붙일 수 있어 경계가 코드 규율에만 기댄다
- C. 섞는다 — `env`는 프로젝트 소유, `region`은 조직 소유 전역(`global`) 하나 — 복제가 없다 / 3-5가 범위 밖으로 뺀 `region` 통합을 다시 열어야 하고 소유 모양이 둘이 된다

**판정(사람, 2026-11-03): A.**

## 5. 반대편 — 이 설계가 틀리는 조건

- 저장소 밖 워크스페이스가 `common_vars`의 `env = onpremise`에 기대어 리소스 이름을 만들고 있으면 4-1 A는 그 쪽을 재생성시킨다. B는 안전하다.
- `env` 태그가 환경이 아닌 값(`shared`·`lab`)을 갖는 것은 키 이름과 뜻이 어긋나는 것이다. 태그 키를 `scope`나 `tier`로 바꾸는 것이 더 정직하지만, 모든 루트와 기존 태그를 고치는 일이 되어 이번에는 `env`를 유지한다. 뒤에 환경 수가 늘어 `env`를 환경에만 쓰고 싶어지면 그때 다시 본다.
- variable set의 변수가 코드에 있으면 콘솔에서 값을 고친 것은 다음 `tfc` apply가 되돌린다 — 콘솔 수정이 습관이면 충돌한다. 그것이 바로 3-4가 원한 바다.
- 프로젝트가 `env` 값의 단위이므로 한 환경 안에서 다른 `env` 값을 쓰는 워크스페이스는 둘 수 없다. 지금 그런 요구는 없다.

## 6. 버린 것

- **공유 루트의 `default_tags`를 지운다(#155의 원안)** — 거짓 분류는 없어지지만 AWS 콘솔에서 소속을 읽을 길도 없어진다. 사람이 접었다.
- **워크스페이스마다 `env` 변수** — 프로젝트 없이도 되지만 워크스페이스 수만큼 반복이고, 이 논의가 피하려는 바로 그것이다.
- **`region`을 전역(`global`) set 하나로** — 값이 전부 같아 가능하지만 3-5에서 범위 밖으로 뺐다.
- **`tfc`를 위한 별도 프로젝트** — `Default Project`는 조직이 만들어 둔 것이고 `tfc` 하나만 산다. 새 프로젝트를 만들 이유가 없다.

## 7. 임계선 — ADR감인가

ADR이 아니다.
프로젝트 개명·이동·variable set 값 변경은 전부 in-place이고 되돌리는 데 한 시간이 들지 않는다.
영향 범위는 이 저장소의 워크스페이스 10개와 그 태그다.
결정은 티켓과 코드로 간다.

## 8. 다음

- **#155를 다시 쓴다** — 제목·본문을 "공유 루트의 env 제거"에서 "프로젝트 재설계 · variable set 선언 · env 값 shared/lab · managed_by 태그"로 바꾼다. 번호·선행(#154)·상위(#152)는 그대로다. 4-1·4-2·4-3의 판정이 본문의 절차를 정한다.
- **#152의 범위 문장**에서 "공유 루트의 `env`·`default_tags` 제거"를 "프로젝트·variable set 재설계"로 고친다.
- **digest 수정** — `261103_1444_terraform-env-axis-and-stg-environment.md`의 "공유 루트에는 env가 없다"는 서술이 바뀐다. 사람이 지시하면 고쳐 쓴다.
- stg 환경 Feature(미발행)의 terraform 리프에 "`stg-careerhub` 프로젝트 + variable set `stg`(env=stg) 선언"이 들어간다.
