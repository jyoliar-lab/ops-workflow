---
type: discussion
kind: deliberation
goal: platform-terraform-restructure
topic: homelab
subjects: [jyoliar-platform-terraform, terraform-cloud, zitadel, external-secrets, jyoliar-k8s]
status: done
ref-adrs: [ADR-0034]
related:
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
  - docs/homelab/discussion/261102_2007_terraform-env-vs-shared-resource-separation-survey.md
---

# terraform 구조 개선 이행 — 이동만으로 되는 워크스페이스와 state 이동이 따르는 워크스페이스

## 1. 문제

stg 환경 논의(`careerhub/261102_1903`)의 4-4가 E로 판정됐다 — 공유 루트는 환경 축 없이 `shared/`에, 환경별 리소스는 `envs/<env>/`의 얇은 루트가 모듈을 불러 세우고, stateful(백업 버킷)은 변동성으로 한 번 더 가른다.
사람은 stg 환경 구축을 이 구조 개선 뒤로 놓았다 — stg가 쓸 SSM 파라미터가 새 구조에서 나와야 하기 때문이다.
이 논의는 그 이행을 계획한다.

워크스페이스 9개는 두 부류로 갈린다.
디렉터리를 옮기고 TFC 워크스페이스의 working directory만 바꾸면 되는 것 — state를 건드리지 않고 plan이 "No changes"여야 한다.
리소스가 다른 워크스페이스로 옮겨 가야 하는 것 — `terraform state mv`나 재생성이 따르고, 그중 Zitadel masterkey는 값이 바뀌면 Zitadel이 기동 불능이라 실수의 대가가 가장 크다.

끝났을 때 손에 있어야 하는 것은 다음이다.
저장소 트리가 E의 모양이다.
워크스페이스 전부가 VCS 연동이고, 이름·working directory·연결이 tfe provider로 선언돼 있다.
기존 리소스는 하나도 재생성되지 않았다 — 각 워크스페이스의 plan이 "No changes"(공유 루트는 태그 제거만)다.
`admin` Google 클라이언트 파라미터는 새 경로에 있고 jyoliar-k8s의 ExternalSecret 둘이 그것을 읽는다.
옛 `zitadel`·`oauth` 워크스페이스는 비워져 삭제됐다.

이번에 다루지 않는 것 — stg 워크스페이스(`careerhub-secrets-stg`) 생성, Stacks 전환, 모듈 버저닝, `vpc`·`vpn` 내용 변경, 공유 루트의 provider 버전 정렬(aws 5.81 · 6.27 혼재).

## 2. 실측

**워크스페이스 9개 — 분류.** 리소스 수는 `grep '^resource'`. 현재 워크스페이스 이름은 코드가 참조하는 셋(`onpremise-iam`·`onpremise-vpc`·`onpremise-backup`)만 확실하고 나머지는 TFC가 답한다.

| 디렉터리 | 리소스 | 새 자리 | 새 워크스페이스 | 부류 | 함께 바뀌는 것 |
|---|---|---|---|---|---|
| `iam` | 11 | `shared/iam` | `shared-iam` | **이동** | `env` 변수·`default_tags` 제거 → AWS 리소스 전부 태그 in-place 변경. `backup`이 remote state로 읽는 쪽 |
| `ci` | 12 | `shared/ci` | `shared-ci` | **이동** | `env`·`default_tags` 제거 |
| `cloudflare` | 14 | `shared/cloudflare` | `shared-cloudflare` | **이동** | 없음 — `env` 변수도 `default_tags`도 원래 없다 |
| `alert` | 14 | `shared/alert` | `shared-alert` | **이동** | `env`·`default_tags` 제거 |
| `backup` | 9 | `envs/prod/backup` | `careerhub-backup-prod` | **이동** | `data.tf`의 `workspaces = ["onpremise-iam"]` → `"shared-iam"`. `env=prod`는 이름 재료라 유지 |
| `vpc` | 모듈 2 | `lab/vpc` | `lab-vpc` | **이동** | `env=onpremise` 유지. `vpn`이 remote state로 읽는 쪽 |
| `vpn` | 7 + 모듈 2 | `lab/vpn` | `lab-vpn` | **이동** | `data.tf`의 `"onpremise-vpc"` → `"lab-vpc"` |
| `zitadel` | 2 | `envs/prod/careerhub`(모듈 경유) | `careerhub-secrets-prod` | **state 이동** | `random_password.zitadel_masterkey` · `aws_ssm_parameter.zitadel_masterkey` 둘. 경로 문자열은 그대로(`…/careerhub/prod/…`) |
| `oauth` | 2 | 둘로 갈린다 | — | **state 이동 + 재생성** | `google_client` → `envs/prod/careerhub`(state 이동, 경로 그대로) · `admin_google_client` → `shared/admin-oauth`(새 경로라 재생성) |

신설되는 루트는 넷 — `_modules/careerhub-env`(masterkey·google-client 정의), `envs/prod/careerhub`, `shared/admin-oauth`, `tfc`(워크스페이스를 선언하는 최상위 메타 루트).

**TFC의 현재 상태(사람, 2026-11-03).** 거의 전부 로컬 CLI 구동이다. 코드에 `cloud`·`backend` 블록이 없고, 연결은 gitignore된 로컬 파일의 `cloud` 블록이 담당한다. 그래서 디렉터리를 옮기면 그 로컬 파일도 사람이 따라 옮겨야 하고, VCS 연동으로 바꾸면 그 파일은 state 조작 때만 쓰는 임시 도구가 된다.

**교차 참조 — 이름 문자열.** `_modules/tfc_remote_state`는 `tfe_outputs`를 워크스페이스 **이름**으로 읽는다. 개명은 소비자(`backup/data.tf`·`vpn/data.tf`)의 문자열 변경과 같은 커밋이어야 한다. 소비자 쪽에서 remote state 읽기가 허용돼야 한다 — `tfe_workspace_settings`의 `global_remote_state` 또는 `remote_state_consumer_ids`.

**SSM 경로의 소비자(jyoliar-k8s).** 이번에 경로가 바뀌는 파라미터는 `admin` 하나다. 소비자는 `gitops/overlays/baremetal/bootstrap/argocd/argocd-oidc-google-externalsecret.yaml`과 `gitops/overlays/baremetal/system/prometheus-config/grafana-oauth-externalsecret.yaml`, refresh 1h. 파라미터가 사라져도 이미 만들어진 k8s Secret은 남는다 — 로그인은 끊기지 않고 ExternalSecret이 오류 상태가 된다. careerhub·zitadel·discord·external-dns 경로는 바뀌지 않는다.

**공유 루트의 `env`.** `iam`·`ci`·`alert`는 `variable "env"`를 받아 provider `default_tags`에만 쓴다 — 리소스 이름에는 쓰지 않는다. 제거하면 plan은 AWS 리소스마다 태그 한 쌍 제거(in-place)다. `cloudflare`는 둘 다 없다.

**tfe provider — 선언 가능한 것(조사일 2026-11-02).**
- `tfe_workspace` — `name`·`working_directory`("A relative path that Terraform will execute within")·`project_id`·`vcs_repo { identifier · branch · github_app_installation_id | oauth_token_id }`. import는 `terraform import tfe_workspace.x <org>/<name>` 또는 `ws-…` ID. 기존 워크스페이스 9개를 전부 import할 수 있다.
  — https://registry.terraform.io/providers/hashicorp/tfe/latest/docs/resources/workspace
- 파일 트리거 — `file_triggers_enabled`(기본 true: "the working directory and trigger prefixes describe a set of paths")·`trigger_prefixes`("List of repository-root-relative paths which describe all locations to be tracked for changes"). **모듈을 쓰는 루트는 모듈 경로를 `trigger_prefixes`에 넣어야 모듈 변경이 run을 만든다** — `envs/*/careerhub` ← `_modules/careerhub-env`, `backup`·`vpn` ← `_modules/tfc_remote_state`, `vpn` ← `_modules/nat`.
- `tfe_workspace_settings` — `execution_mode`(remote·local·agent)·`global_remote_state`·`remote_state_consumer_ids`. `tfe_workspace`의 같은 인자는 deprecated다.
  — https://registry.terraform.io/providers/hashicorp/tfe/latest/docs/resources/workspace_settings
- `tfe_github_app_installation` 데이터 소스 — `installation_id` 또는 `name`(GitHub 조직명)으로 찾는다. VCS 연결은 GitHub App 설치가 먼저다(TFC 콘솔에서 1회).
- `tfe_variable` — `key`·`value`·`category`(terraform·env)·`sensitive`("written once and not visible thereafter"). sensitive 변수는 콘솔에서 바꾸면 드리프트를 못 본다. `value_wo`(write-only)는 state에 남지 않는다.
  — https://registry.terraform.io/providers/hashicorp/tfe/latest/docs/resources/variable

**state 이동의 도구(조사일 2026-11-02).**
- `terraform state push`는 lineage가 다르면 거부하고("Terraform will not allow you to push the state"), 원격 serial이 더 높으면 거부한다. `-force`는 "not recommended". 한 번도 state가 없던 새 워크스페이스에는 lineage 검사가 걸리지 않는다.
  — https://developer.hashicorp.com/terraform/cli/commands/state/push
- `moved` 블록은 같은 구성 안에서만 동작한다 — 워크스페이스 사이 이동에는 쓸 수 없다.
- `random_password`는 import를 지원한다(값을 ID로). masterkey 복구의 최후 수단이지, 계획의 경로가 아니다.
  — https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password
- VCS 연동 워크플로우에서는 `cloud` 블록이 필요 없다 — HashiCorp 튜토리얼이 전환 직전에 블록을 지운다. 필요한 것은 CLI 구동일 때다.
  — https://developer.hashicorp.com/terraform/tutorials/cloud-get-started/cloud-vcs-change

**ADR-0034(proposed).** terraform은 클러스터 안을 모른다. 이 이행은 SSM 접점의 경로 하나(`admin`)를 바꾸는 것 외에 접점을 늘리지 않는다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 목표 트리

**선택: stg 논의 4-4 E의 트리에 메타 루트 `tfc/`를 최상위로 더한 평면 트리.** `tfc/` · `_modules/careerhub-env` · `shared/{iam,ci,cloudflare,alert,admin-oauth}` · `envs/prod/{careerhub,backup}` · `lab/{vpc,vpn}`. `tfc`는 다른 워크스페이스들을 선언하는 층이라 그것들과 나란히 두지 않는다. (판정 승계 + 인터뷰, 2026-11-03. 처음 `tfc`였다가 최상위로 올렸다.)

<details><summary>버린 안</summary>

- `shared/tfc` — 메타 루트가 공유 인프라 루트와 같은 층에 보인다
- `tfc/` + `infra/{_modules,shared,envs,lab}` — 최상위가 제어/인프라 둘로 읽히지만, 형제 하나를 위해 working directory 11개에 토막이 붙는다. 제어 루트가 더 생기면 그때 `git mv` 한 번

</details>

### 3-2. 워크스페이스 이름

**선택: 전부 새 규약으로 바꾼다** — `shared-<name>` · `careerhub-<layer>-<env>` · `lab-<name>`. 개명은 `tfe_workspace.name` 변경이고, remote state 소비자의 문자열 변경과 같은 커밋이다. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- 디렉터리만 옮기고 이름은 둔다 — 이름과 경로가 어긋난 채 남고, `onpremise-iam`이 공유 루트의 이름으로 남는다
- 새로 만드는 것만 새 규약 — 두 규약이 공존한다

</details>

### 3-3. 구동 방식

**선택: `tfc`를 뺀 전부를 VCS 연동으로 전환한다. `tfc`만 로컬 CLI·local 실행이고, 그 루트에만 `cloud` 블록을 커밋한다.** VCS 루트는 머지가 plan·apply를 만들고 코드에 `cloud` 블록이 없다. `tfc`는 운영자의 `terraform login` 자격증명으로 운영자 머신에서 실행하고 state만 HCP에 둔다 — 조직 수준 tfe 토큰을 어느 워크스페이스에도 저장하지 않고, 자기 연결을 자기가 끊는 고리가 없다. 로컬 `cloud` 블록 파일은 state 조작(pull·mv·push·rm)에만 쓰는 임시 도구가 된다. README의 "코드에 백엔드 블록은 없다"는 "`tfc/` 하나만 예외"로 고쳐 쓴다. (인터뷰, 2026-11-03. 처음 전부 VCS였다가 `tfc`를 예외로 뺐다.)

<details><summary>버린 안</summary>

- CLI 유지 + `cloud` 블록을 코드에 — 조직명이 코드에 들어가고, VCS 전환을 또 한 번 미룬다
- CLI 유지 + 로컬 파일 유지 — 옮긴 디렉터리마다 사람이 로컬 파일을 다시 만든다
- `tfc`까지 VCS — tfe 토큰이 `tfc` 워크스페이스의 sensitive 변수로 상주하고, 콘솔에서 1회 생성해야 하며, 자기 `vcs_repo`를 잘못 바꾸면 콘솔로 복구한다
- 인프라 루트까지 섞는다 — 두 구동 방식이 공존해 "이 워크스페이스는 어떻게 반영하나"를 매번 물어야 한다. 예외는 성질이 다른 `tfc` 하나로 끝낸다

</details>

### 3-4. TFC 설정의 소유

**선택: tfe provider로 코드화한다** — `tfc` 루트(워크스페이스 `tfc`)가 워크스페이스·settings·VCS 연결을 선언한다. 개명·working directory 변경·VCS 연결이 전부 PR이 된다. 어디까지 코드화하나는 4-1. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- 콘솔 수동 — 10개면 안팎이라 가능하지만, 이름·경로의 짝이 코드에 남지 않고 다음 환경 때 같은 손작업이다

</details>

### 3-5. 함께 하는 것

**선택: 셋을 함께 한다.** 공유 루트(`iam`·`ci`·`alert`)의 `env` 변수·`default_tags` 제거. `admin` 파라미터 경로를 `/jyo-liar/k8s/baremetal/admin/oauth/google-client`로 — **한 번에**(terraform 재생성 + jyoliar-k8s 패치를 같은 날, ExternalSecret의 짧은 오류 창 수용). `vpc`·`vpn`을 `lab/`으로. (인터뷰, 2026-11-03)

<details><summary>버린 안</summary>

- admin 경로 expand/contract — 오류 창 0이지만 PR 셋. 로그인이 끊기지 않으므로 한 번에 가는 비용이 더 싸다
- stg 워크스페이스 생성까지 — stg 환경 구축의 첫 조각이라 그쪽 티켓의 것이다

</details>

### 3-6. state 이동의 수행자

**선택: 사람이 CLI로. 티켓이 순서와 합격선을 적는다.** 이행 스크립트를 저장소에 두지 않는다 — 1회용 코드가 남는다. (인터뷰, 2026-11-03)

## 4. 열린 축 — 논의

### 4-1. 메타 워크스페이스(`tfc`)의 범위

실측: `tfe_workspace`·`tfe_workspace_settings`·`tfe_variable` 셋이 각각 모양·실행·변수를 선언한다. sensitive 변수는 "written once", 콘솔 변경을 드리프트로 못 본다. `value_wo`는 state에 남지 않는다.
메타 워크스페이스 자체는 닭과 알이다 — 자기를 선언하려면 먼저 존재해야 한다. 로컬 CLI(3-3)에서는 `terraform init`이 그것을 만들고, tfe provider의 토큰은 운영자의 `terraform login` 자격증명이다.

- **A. 모양만** — `tfe_workspace`(이름·working_directory·vcs_repo·trigger_prefixes) + `tfe_workspace_settings`(execution_mode·remote state 소비자). 변수는 전부 콘솔. 이기는 조건: 변수가 적고(region·env·몇 개의 시크릿) 바뀌지 않을 때. 지는 조건: `env=prod`·`region` 같은 비밀 아닌 변수도 코드 밖에 산다 — "stg 워크스페이스가 받는 변수"가 코드에 없다.
- **B. 모양 + 비밀 아닌 변수** — A에 `tfe_variable`로 `env`·`region`·`cnpg_app_name` 같은 평문 변수를 더한다. 시크릿(Google 클라이언트·Discord 토큰·Cloudflare)은 콘솔. 이기는 조건: 환경별 루트의 "받는 변수"가 코드에 보이면서 비밀은 state에 들어가지 않는다 — 지금 저장소에 맞는 선. 지는 조건: 변수의 소유가 둘로 갈려(코드·콘솔) 어느 쪽인지 규칙이 필요하다 — "sensitive면 콘솔"이 규칙이다.
- **C. 시크릿까지** — `value_wo`로 시크릿도 선언한다. 값은 메타 워크스페이스의 변수(sensitive)에서 온다. 이기는 조건: 변수 하나도 콘솔에 남기지 않겠다는 요구. 지는 조건: 시크릿이 결국 메타 워크스페이스의 콘솔 변수로 한 겹 밀린 것뿐이고, 회전 때 두 곳을 만진다.
- D. 안 한다 — 3-4에서 버렸다. 현상 유지의 비용은 이름·경로의 짝이 어디에도 기록되지 않는 것이다.

메타 워크스페이스 자체의 부트스트랩은 어느 안에서도 같다 — `tfc/`의 `cloud { workspaces { name = "tfc" } }` 블록으로 `terraform login` 뒤 `terraform init`을 치면 HCP가 워크스페이스를 만들고, 첫 apply에서 기존 9개와 자기 자신을 import한다. 토큰은 운영자의 로그인 자격증명이고 워크스페이스 변수가 아니다.

**판정(사람, 2026-11-03): B — 모양 + 비밀 아닌 변수. 규칙은 "sensitive면 콘솔".**

### 4-2. `careerhub-secrets-prod`로의 리소스 이전 — 셋의 방법

실측: 옮길 리소스는 셋 — `zitadel` 워크스페이스의 `random_password.zitadel_masterkey`·`aws_ssm_parameter.zitadel_masterkey`, `oauth` 워크스페이스의 `aws_ssm_parameter.google_client`. 새 주소는 `module.careerhub.<type>.<name>`. masterkey는 `prevent_destroy`이고 값이 바뀌면 Zitadel이 기동 불능이다(`zitadel/masterkey.tf` 주석·ADR-0030). `google_client`의 값은 변수에서 오므로 재생성이 가능하다. 새 워크스페이스는 state가 없어 push에 lineage 검사가 걸리지 않는다.

- **A. 셋 다 state 이동, 한 세션에** — 옛 두 워크스페이스에서 `state pull` → 로컬에서 `state mv -state=<old> -state-out=<new>`로 셋을 새 주소로 → 새 워크스페이스에 `state push` → 옛 워크스페이스에서 `state rm` 셋 → 새 워크스페이스 plan "No changes". 이기는 조건: 파라미터 공백 0, 값 불변이 state로 보증된다. 지는 조건: 사람이 임시 `cloud` 바인딩을 세 번 바꿔 가며 CLI를 친다 — 실수 지점이 많다. 그래서 **pull 받은 원본 state 파일을 그대로 보관**하는 것이 되돌리기다.
- B. masterkey만 이동, `google_client`는 재생성 — `oauth`에서 destroy, 새 워크스페이스에서 create. 이기는 조건: state 조작을 한 워크스페이스로 줄이고 싶을 때. 지는 조건: 같은 이름의 SSM 파라미터라 destroy가 먼저여야 하고 그 사이 공백이 생긴다 — ExternalSecret은 Secret을 유지하므로 로그인은 끊기지 않지만, 공백 창이 있다는 점에서 A보다 나쁘고 state 조작은 어차피 한다.
- **C. 전부 재생성 — masterkey를 새로 만들고 Zitadel을 처음부터 다시 세운다.** 사람의 전제(2026-11-03): Zitadel 가입자는 운영자 본인 하나라 원장을 버려도 된다. 그러면 state 조작이 0이 된다 — `zitadel`·`oauth`를 destroy하고 `careerhub-secrets-prod`를 apply하면 새 masterkey와 같은 값의 google-client 파라미터가 생긴다. 대가는 terraform 밖에 있다. 새 masterkey로는 기존 Zitadel DB를 복호화할 수 없으므로 **Zitadel DB를 비우고 init·setup을 다시 돌려야 한다** — `Database/careerhub-zitadel-db`는 `databaseReclaimPolicy: retain`이라 CR 삭제로는 비워지지 않고, `DROP DATABASE` 또는 reclaim 변경 뒤 재생성이 사람의 손작업이다. 구성 Job이 IdP·project·careerhub-web 앱을 다시 수렴시키지만 **careerhub-web의 client_id·secret이 바뀌고**(소비자 미배포라 영향 없음) **운영자 계정의 Zitadel `sub`가 바뀐다** — #60이 이미 userinfo에 백필한 식별자(scrapJob 12건)와 auth DB의 `zitadel_sub`가 고아가 되어 재백필하거나 버린다. SSM 파라미터 이름이 같아 destroy가 apply보다 먼저여야 하고, 그 사이 ExternalSecret은 옛 Secret을 유지한다. 이기는 조건: state 조작을 한 줄도 하고 싶지 않고, Zitadel 원장·백필 결과를 버려도 되는 지금. 지는 조건: 작업량으로는 A가 적다 — A는 CLI 열 줄이고 클러스터를 건드리지 않는데, C는 DB 리셋·구성 Job 재수렴·재백필(또는 폐기 결정)이 따른다. "덜 무섭다"와 "덜 일한다"가 갈리는 안이다. 가입자가 생기는 순간 C는 닫힌다.
- D. 안 한다 — `zitadel`·`oauth`를 그대로 두고 stg만 새 구조로. 이기는 조건: 없다 — prod가 옛 구조에 남아 환경 둘이 다른 모양이 되고, E의 목적이 무너진다.

`admin_google_client`는 이 축 밖이다 — 경로가 바뀌므로 재생성이고(3-5), `shared/admin-oauth`에서 create하고 `oauth`를 destroy하면 끝이다.

**판정(사람, 2026-11-03): A — 셋 다 state 이동, 한 세션에. 사람이 직접 수행하고, 명령 순서·보관할 원본·합격선은 그 Task 본문이 가이드로 적는다.**

## 5. 반대편 — 이 계획이 틀리는 조건

- VCS 연동 전환이 state 조작을 어렵게 한다 — VCS 워크스페이스에서 CLI `apply`는 막히지만 `state` 명령은 열려 있다(HCP 문서는 "manual state manipulation … requires the use of Terraform CLI"). 그래도 **임시 바인딩을 만드는 로컬 파일은 끝까지 필요하다** — "로컬 파일을 없앤다"는 평소 경로에 한한다.
- `trigger_prefixes`를 빼먹으면 모듈 변경이 run을 만들지 않는다 — `_modules/careerhub-env`를 고쳐도 `careerhub-secrets-prod`가 가만히 있다. 메타 루트가 선언하므로 한 곳에서 보이지만, 처음 선언할 때 빠지면 아무도 모른다.
- 공유 루트의 태그 제거가 "No changes"가 아니라 리소스 N건의 in-place 변경이라, 이동이 맞는지(재생성 없음)를 태그 변경 속에서 읽어야 한다 — 이동과 태그 제거를 **다른 PR**로 나누면 이동의 plan이 "No changes"로 깨끗해진다. 비용은 PR 수.
- 개명과 remote state 문자열 변경이 다른 커밋이면 `backup`·`vpn`의 plan이 깨진다. 같은 PR이어야 한다.
- 메타 워크스페이스가 로컬 CLI라 plan이 PR에 보이지 않는다 — 운영자 한 명이 머신에서 plan을 읽고 apply한다. 사람이 둘 이상이 되면 이 예외를 다시 본다.
- `oauth` 워크스페이스는 리소스 둘이 각각 다른 곳으로 가므로 두 PR(4-2 이동 · admin 재생성)이 끝나야 비워진다 — 그 사이 `oauth`의 VCS run이 "삭제 plan"을 보일 수 있다. 전환 중에는 `oauth`를 VCS에 붙이지 않고 CLI 상태로 두는 것이 안전하다.

## 6. 버린 것

- **Stacks로 간다** — 같은 격자의 세 번째 표현이지만 state 마이그레이션이 따르는 별도 워크플로우다(조사 문서 §5). 리소스 둘을 위해 들일 것이 아니다.
- **`moved` 블록으로 이전** — 워크스페이스 사이에서는 동작하지 않는다.
- **stg와 동시에** — stg 파라미터를 옛 구조로 먼저 만들면 두 번 옮긴다. 사람이 순서를 정했다.
- **이름을 두고 디렉터리만** — 3-2.
- **이행 스크립트를 저장소에** — 3-6.

## 7. 임계선 — ADR감인가

ADR이 아니다 — 전부 되돌릴 수 있고(디렉터리 복원·working directory 복원·state 원본 push), 데이터는 바뀌지 않는다.
E 자체가 결정이고 그 결정은 stg 논의 §7의 ADR 후보("환경은 네임스페이스·데이터 플레인·자격증명 경로가 함께 갈리는 단위다")에 얹힌다 — 이 문서는 그 결정의 이행이다.
masterkey 이동은 one-way door가 아니라 **실수가 one-way인 작업**이다 — 그래서 되돌리기(원본 state 보관)가 절차에 들어간다.

## 8. 다음 — 단계와 합격선

이 순서가 계획이다. 단계마다 합격선이 있고, 합격선을 넘지 못하면 다음으로 가지 않는다. 티켓은 단계 하나가 Task 하나다 — 트리는 GitHub에 산다.

**0. 메타 워크스페이스 부트스트랩.** `tfc` 루트 작성(4-1의 범위대로, `cloud` 블록 포함). `terraform login` → `terraform init`이 `tfc` 워크스페이스를 만든다(local 실행 모드로 설정). GitHub App 설치 확인. 기존 9개 + 자기 자신 import. 합격선: `tfc` plan이 "No changes" — 선언이 현재 TFC와 일치한다는 뜻이다.

**1. 이동 7개 — 디렉터리·개명·VCS 연결.** `git mv`로 `shared/{iam,ci,cloudflare,alert}`·`envs/prod/backup`·`lab/{vpc,vpn}`. 같은 PR에서 `backup/data.tf`·`vpn/data.tf`의 이름 문자열 변경, 메타 루트에서 `name`·`working_directory`·`vcs_repo`·`trigger_prefixes`·remote state 소비자 선언. 합격선: 7개 워크스페이스 전부 plan "No changes". 태그 제거는 여기서 하지 않는다(§5).

**2. 공유 루트의 `env` 제거.** `iam`·`ci`·`alert`에서 변수·`default_tags`·TFC 변수 삭제. 합격선: plan이 태그 제거(in-place)만이고 destroy·create가 0.

**3. `careerhub-secrets-prod` 신설과 state 이동(4-2).** `_modules/careerhub-env`·`envs/prod/careerhub` 작성, 메타 루트에 워크스페이스 선언(`trigger_prefixes`에 모듈 경로). 사람이 CLI로 셋을 옮긴다 — pull 원본 보관 → mv → push → 옛 쪽 rm. 합격선: 새 워크스페이스 plan "No changes", `zitadel` 워크스페이스 state 비어 있음, SSM의 masterkey 값 불변(ExternalSecret 재동기화 뒤 Zitadel pod 정상). `zitadel` 워크스페이스 삭제(메타 루트에서 제거).

**4. `admin` 재생성 — 한 번에(3-5).** `shared/admin-oauth` 작성·apply(새 경로), 같은 날 jyoliar-k8s PR(ExternalSecret 둘의 `key`), `oauth`의 `admin_google_client` destroy, `oauth` 워크스페이스 삭제. 합격선: argocd·grafana ExternalSecret `SecretSynced`, 옛 경로 파라미터 없음.

**5. 문서.** terraform 저장소 README·CLAUDE.md의 디렉터리 구조·환경·반영 방법 절을 새 트리와 "`tfc/`만 CLI"로 — 저장소 안의 운영자 안내라 그 저장소 PR이다(이 지식 플레인의 문서가 아니다).

이 뒤에 stg 환경 구축이 온다 — `envs/stg/careerhub`와 `careerhub-secrets-stg`가 그 첫 조각이고, 그것은 stg 논의의 티켓이다.
티켓의 저장소는 `jyoliar-careerhub/jyoliar-platform-terraform`이고, 4단계만 `jae2274/jyoliar-k8s`가 더해진다.

**쪼갬(사람, 2026-11-03).** 이 이행은 Feature 하나(근거 ADR 없음, 부모 없음)이고 리프는 일곱이다.
단계 하나가 Task 하나이되, 3단계는 둘로 가른다 — 루트·모듈 작성과 `tfc` 선언(PR)과 **사람이 수행하는 state 이동**(가이드가 본문)은 수행자와 합격선이 다르다.
4단계는 target 저장소 둘(terraform·jyoliar-k8s)을 가진 Task 하나다 — "한 번에"가 요구라서다.
선행은 0→1→{2, 3}→4→5→6이고 2와 3은 병행한다.
Task 단위의 기준: PR 하나 크기, 합격선이 그 Task 안에서 혼자 판정된다, 사람만 할 수 있는 작업은 코드 PR과 다른 Task다.
버린 쪼갬 — 3단계를 한 Task로(PR과 콘솔 세션이 한 합격선을 나눠 쓴다) · 전체를 Task 하나로(합격선 여섯이 한 티켓에 쌓인다).
