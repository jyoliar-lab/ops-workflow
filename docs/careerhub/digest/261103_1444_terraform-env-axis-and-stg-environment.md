---
type: digest
goal: careerhub-env-separation
topic: careerhub
subjects: [jyoliar-platform-terraform, terraform-cloud, tfe-provider, variable-set, aws-tags, careerhub-stg, careerhub-prod, jyoliar-k8s, argocd, zitadel, mongodb, cloudnativepg, external-secrets]
status: current
ref-adrs: [ADR-0034]
sources:
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
  - docs/careerhub/discussion/261102_1903_stg-env-external-dependencies-survey.md
  - docs/homelab/discussion/261102_2007_terraform-env-vs-shared-resource-separation-survey.md
  - docs/homelab/discussion/261103_1429_terraform-restructure-migration-plan.md
  - docs/homelab/discussion/261103_1809_tfe-project-variable-set-provider-survey.md
  - docs/homelab/discussion/261103_1809_tfc-project-and-variable-set-redesign.md
superseded_by:
---

# careerhub 환경 분리 — terraform 환경 축 · 프로젝트와 stg 환경 (2026-11-03 시점)

## 개요

careerhub는 지금 `careerhub-prod` 하나로 공개 서비스를 하고 있고, 그 옆에 상시 pre-prod 환경 `stg`를 세운다.
stg는 prod와 같은 토폴로지로 서서 리뉴얼 스택(careerhub-web·Zitadel·신 세대 composer와 auth-service)이 prod에 가기 전에 먼저 서는 자리이자, DB·오퍼레이터 업그레이드와 이미지 태그 인상을 prod보다 먼저 보는 자리다.
환경이 둘이 되면 환경마다 따로 서는 자격증명(Zitadel masterkey·Google OAuth 클라이언트)이 필요하고, 그것을 만드는 terraform 저장소(`jyoliar-platform-terraform`)가 환경 축을 갖도록 먼저 재구성한다.
HCP Terraform 쪽에서는 프로젝트가 그 축을 받는다 — 디렉터리 묶음 하나가 프로젝트 하나이고, 프로젝트가 자기 워크스페이스 전부에 `env`를 준다.
이 문서는 그 둘 — terraform 저장소의 새 구조와 이행 순서, 그리고 그 위에 서는 stg 환경 — 이 한 덩어리로 어떻게 돌아가는지를 서술한다.
관통하는 사례는 **stg Zitadel의 masterkey 한 개**다 — 그것이 어디서 선언되고, 어떤 워크스페이스가 만들고, 어떻게 클러스터에 닿고, 그 전에 prod의 masterkey가 어떻게 새 자리로 옮겨 가는가.

## 어휘

- **공유 루트** — 모든 환경이 함께 쓰는 리소스를 가진 terraform 루트. 환경 축이 없다. `shared/` 아래.
- **환경 루트** — 한 환경의 리소스만 가진 얇은 루트. 모듈을 부른다. `envs/<env>/` 아래.
- **메타 워크스페이스** — 다른 워크스페이스들의 이름·경로·연결·프로젝트·variable set을 선언하는 루트. 최상위 `tfc/`. 공유 인프라와 같은 층이 아니다.
- **프로젝트** — HCP Terraform에서 워크스페이스를 묶는 폴더. 디렉터리 묶음 하나(`shared/`·`lab/`·`envs/prod/`·`envs/stg/`)가 프로젝트 하나다. 프로젝트는 variable set 하나를 소유하고, 그 set이 프로젝트의 모든 워크스페이스에 `env`·`region`을 준다 — 프로젝트 하나 = `env` 값 하나.
- **env** — 워크스페이스가 프로젝트에서 받는 변수이자 모든 AWS 리소스의 태그. 환경 프로젝트에서는 환경 이름(`prod`·`stg`)이고, 공유·실험 프로젝트에서는 디렉터리 이름(`shared`·`lab`)이다. 환경 이름은 네임스페이스(`careerhub-<env>`)·SSM 경로(`/jyo-liar/k8s/baremetal/careerhub/<env>/…`)·DNS(`<env>-careerhub.jyo-liar.com`)에 같은 글자로 들어간다.
- **태그** — AWS provider의 `default_tags`가 모든 리소스에 `env`와 `managed_by = terraform`을 붙인다. terraform 없이 AWS 콘솔만 봐도 어느 프로젝트의 것이고 코드가 만든 것인지 읽힌다.

## 1. terraform 저장소의 모양

```
tfc/                         # 메타 워크스페이스 — 아래 모든 프로젝트 · variable set · 워크스페이스를 선언한다
_modules/
  tfc_remote_state/          # 다른 워크스페이스의 출력을 읽는다
  nat/
  careerhub-env/             # 환경 하나의 careerhub 재료 — masterkey · google-client
shared/                      # 프로젝트 shared — env = shared
  iam/                       # OIDC Provider · IRSA Role(external-secrets · ecr-image-puller)
  ci/                        # ECR · CodeBuild
  cloudflare/                # zone · 터널 · 엣지 · external-dns 토큰
  alert/                     # Discord 채널 · webhook
  admin-oauth/               # argocd·grafana 로그인용 Google 클라이언트
envs/
  prod/                      # 프로젝트 prod-careerhub — env = prod
    careerhub/               # module "careerhub" { env = var.env }
    careerhub-backup/        # CNPG 백업 S3 버킷 · IRSA Role
  stg/                       # 프로젝트 stg-careerhub — env = stg
    careerhub/               # module "careerhub" { env = var.env }
lab/                         # 프로젝트 lab — env = lab
  vpc/  vpn/                 # AWS 모의 환경
```

`_modules/careerhub-env`가 환경 하나의 careerhub 재료를 정의한다.
`random_password`로 32자 masterkey를 만들어 `/jyo-liar/k8s/baremetal/careerhub/${var.env}/zitadel/masterkey`에 SecureString으로 심고, 변수로 받은 Google 클라이언트 ID·secret을 `/jyo-liar/k8s/baremetal/careerhub/${var.env}/oauth/google-client`에 심는다.
두 파라미터 모두 `prevent_destroy`다.
출력은 파라미터의 경로이고, 값은 내보내지 않는다.

`envs/stg/careerhub/main.tf`는 이 모듈을 부르는 블록 하나다.
`env`는 리터럴이 아니라 변수다 — 값 `stg`는 프로젝트 `stg-careerhub`의 variable set이 준다.

```hcl
module "careerhub" {
  source               = "../../../_modules/careerhub-env"
  env                  = var.env
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
}
```

모든 AWS 루트의 `providers.tf`는 같은 `default_tags`를 갖는다.

```hcl
provider "aws" {
  region = var.region
  default_tags {
    tags = {
      env        = var.env
      managed_by = "terraform"
    }
  }
}
```

공유 루트도 `variable "env"`를 받지만 리소스 이름에는 쓰지 않고 태그에만 쓴다 — 값은 `shared`다.
`shared/iam`의 IRSA Role은 `system:serviceaccount:*:ecr-image-puller`처럼 네임스페이스를 와일드카드로 신뢰하고, `shared/ci`의 ECR 저장소는 환경과 무관하게 하나다.
`shared/admin-oauth`의 파라미터 경로는 `/jyo-liar/k8s/baremetal/admin/oauth/google-client`다.

의존은 공유 → 환경 한 방향이다.
`envs/prod/careerhub-backup`이 `shared-iam`의 OIDC Provider ARN을 `tfc_remote_state`로 읽는다.
공유 루트가 환경 루트를 읽는 일은 없다.

## 2. 워크스페이스와 구동

디렉터리 하나가 HCP Terraform 워크스페이스 하나이고, 디렉터리 묶음 하나가 프로젝트 하나다.
프로젝트마다 자기가 소유한 variable set 하나가 붙어 `env`·`region`을 준다.

| 디렉터리 | 프로젝트 | variable set | 워크스페이스 |
|---|---|---|---|
| `tfc` | `Default Project` | 없음 | `tfc` |
| `shared/iam` · `shared/ci` · `shared/cloudflare` · `shared/alert` · `shared/admin-oauth` | `shared` | `shared` — `env = shared` | `shared-iam` · `shared-ci` · `shared-cloudflare` · `shared-alert` · `shared-admin-oauth` |
| `envs/prod/careerhub` · `envs/prod/careerhub-backup` | `prod-careerhub` | `prod` — `env = prod` | `careerhub-secrets-prod` · `prod-careerhub-backup` |
| `envs/stg/careerhub` | `stg-careerhub` | `stg` — `env = stg` | `careerhub-secrets-stg` |
| `lab/vpc` · `lab/vpn` | `lab` | `lab` — `env = lab` | `lab-vpc` · `lab-vpn` |

variable set은 프로젝트 소유다 — 그 프로젝트 안에만 붙고 다른 프로젝트에는 붙일 수 없다.
`priority`가 켜져 있어 워크스페이스에 같은 이름의 변수가 있어도 set의 값이 이긴다.
`region`은 모든 set에 같은 값(`ap-northeast-2`)으로 들어 있다.
워크스페이스에는 `env`·`region` 변수가 없다 — 프로젝트에서 받는다.

`tfc`를 뺀 전부가 VCS 연동이다.
`main`에 머지되면 그 워크스페이스가 plan을 만들고, 사람이 콘솔에서 apply를 승인한다.
VCS 루트의 코드에 `cloud`·`backend` 블록은 없다.
`tfc`만 로컬 CLI다 — `tfc/`에 커밋된 `cloud` 블록으로 운영자 머신에서 plan·apply하고, state만 HCP에 둔다.
워크스페이스는 자기 working directory와 `trigger_prefixes` 아래 파일이 바뀔 때만 run을 만든다 — `careerhub-secrets-*`는 `_modules/careerhub-env`를, `prod-careerhub-backup`·`lab-vpn`은 `_modules/tfc_remote_state`(와 `_modules/nat`)를 trigger prefix로 가진다.

`tfc/`가 이 표 전체를 선언한다 — 프로젝트는 `tfe_project`, variable set은 `tfe_variable_set`(`parent_project_id`로 소유 프로젝트를 가리킨다)과 `tfe_project_variable_set`(프로젝트에 붙인다), set의 변수 `env`·`region`은 `tfe_variable`(`variable_set_id`), 워크스페이스는 `tfe_workspace`·`tfe_workspace_settings` — 이름, working directory, 프로젝트, GitHub App 연결, 브랜치, trigger prefix, 실행 모드, remote state 소비자(`shared-iam` → `prod-careerhub-backup`, `lab-vpc` → `lab-vpn`).
워크스페이스 고유의 비밀 아닌 변수(`cnpg_app_name`·`discord_server_id` 같은 것)도 `tfe_variable`로 선언한다.
비밀(Google 클라이언트 ID·secret, Discord 토큰, Cloudflare 자격증명)은 콘솔에서 sensitive 변수로 넣는다 — sensitive면 콘솔, 아니면 코드.
워크스페이스를 하나 더 만드는 것, 개명하는 것, 경로를 옮기는 것, 환경 하나를 더하는 것(프로젝트 + variable set + 워크스페이스)은 전부 `tfc/`의 PR이다.
`tfc` 자신은 운영자의 `terraform login` 자격증명으로 돌고, 그 토큰이 tfe provider의 토큰이다 — 워크스페이스 변수에 토큰이 없다.

## 3. 사례 — stg masterkey 한 개의 여정

사람이 Google 콘솔에서 stg용 OAuth 클라이언트를 만든다.
redirect URI는 `https://id.stg-careerhub.jyo-liar.com/…`이다.
그 ID와 secret을 `careerhub-secrets-stg` 워크스페이스의 sensitive 변수로 넣는다.
`env = stg`와 `region`은 넣지 않는다 — 워크스페이스가 속한 프로젝트 `stg-careerhub`의 variable set이 이미 준다.

`envs/stg/careerhub/main.tf`를 담은 PR이 `main`에 머지된다.
`careerhub-secrets-stg`가 plan을 만든다 — `random_password` 하나, SSM 파라미터 둘.
사람이 apply를 승인하면 `/jyo-liar/k8s/baremetal/careerhub/stg/zitadel/masterkey`와 `/jyo-liar/k8s/baremetal/careerhub/stg/oauth/google-client`가 생긴다.
두 파라미터에는 `env = stg`·`managed_by = terraform` 태그가 붙어 있다 — AWS 콘솔에서 파라미터만 봐도 stg의 것이고 terraform이 만든 것임이 읽힌다.
terraform의 일은 여기서 끝난다 — 클러스터 안에서 그 값이 어떻게 쓰이는지 terraform은 모른다.

클러스터에서는 `careerhub-stg` 네임스페이스의 ExternalSecret이 `ClusterSecretStore/aws-parameter-store`를 통해 그 경로를 읽는다.
읽기 권한은 `shared-iam`의 external-secrets Role이 `/jyo-liar/k8s/*` 전체에 주고 있어 환경이 늘어도 바뀌지 않는다.
Secret `zitadel-masterkey`가 만들어지고, stg Zitadel pod가 그것으로 자기 DB를 암호화한다.
같은 네임스페이스의 Secret `google-oauth`는 Zitadel 구성 Job이 읽어 Google IdP를 등록한다.
prod의 masterkey는 `/…/careerhub/prod/…`에, stg의 것은 `/…/careerhub/stg/…`에 있고, 두 Zitadel은 서로의 값을 모른다.

## 4. 이행 — prod의 masterkey가 새 자리로 가는 순서

지금 prod의 masterkey는 `zitadel/` 디렉터리의 `prod-careerhub-zitadel` 워크스페이스 state에, Google 클라이언트 파라미터는 `oauth/` 디렉터리의 `careerhub-oauth` 워크스페이스 state에 있다.
둘을 `careerhub-secrets-prod`로 옮기고 나머지 디렉터리를 새 자리로 보내는 순서는 다음이다.
단계마다 합격선이 있고, 넘지 못하면 다음 단계로 가지 않는다.

**0. 메타 워크스페이스.**
`tfc/` 루트를 쓴다 — `cloud { workspaces { name = "tfc" } }` 블록을 포함한다.
`terraform login` 뒤 `terraform init`을 치면 HCP에 `tfc` 워크스페이스가 생긴다. 실행 모드를 local로 두고 GitHub App 설치를 확인한다.
기존 워크스페이스 9개와 `tfc` 자신, 프로젝트 3개(`Default Project`·`onpremise`·`prod-careerhub`)를 지금 이름·지금 경로 그대로 선언하고 import한다.
합격선: `tfc`의 plan이 "No changes" — 선언이 TFC의 현재와 일치한다.

**1. 이동 7개.**
한 PR에서 `git mv`로 `iam`·`ci`·`cloudflare`·`alert`를 `shared/`로, `backup`을 `envs/prod/careerhub-backup`으로, `vpc`·`vpn`을 `lab/`으로 옮긴다.
같은 PR에서 `backup/data.tf`의 `"onpremise-iam"`을 `"shared-iam"`으로, `vpn/data.tf`의 `"onpremise-vpc"`를 `"lab-vpc"`로 바꾸고, `tfc/`에서 7개의 `name`·`working_directory`·`vcs_repo`·`trigger_prefixes`·remote state 소비자를 새 값으로 바꾼다.
머지되면 `tfc`가 개명과 경로 변경을 apply하고, 7개 워크스페이스가 VCS 연동으로 각자 plan을 만든다.
합격선: 7개 전부 "No changes".

**2. 프로젝트 재설계.**
지금은 프로젝트가 `onpremise`(공유 4 · 실험 2 · `careerhub-oauth`)와 `prod-careerhub`(backup · zitadel) 둘이고, 콘솔에서 만든 조직 소유 variable set `common_vars`(`env = onpremise`)와 `prod`(`env = prod`)가 각각에 붙어 있다.
`tfc/`의 PR 하나에서 프로젝트 `shared`·`lab`과 각자가 소유한 variable set `shared`(`env = shared`)·`lab`(`env = lab`)을 새로 선언하고, `prod-careerhub`가 소유한 variable set `prod`를 새로 선언한다 — 콘솔의 `prod`는 import하지 않고 새 것으로 바꾼다.
같은 PR에서 공유 워크스페이스 4개를 `shared`로, `lab-*` 둘을 `lab`으로, `careerhub-oauth`를 `prod-careerhub`로 옮긴다 — 워크스페이스의 프로젝트 이동은 in-place다.
`onpremise`는 `removed` 블록으로 관리에서 떼어 코드에서 없앤다 — destroy하지 않고, 콘솔에는 남는다.
같은 PR에서 AWS 루트 8개의 `default_tags`에 `managed_by = "terraform"`을 더한다.
`tfc` apply 뒤 8개 워크스페이스가 각자 plan을 만든다.
합격선: `tfc`의 plan에 워크스페이스 destroy·create가 0이고, 8개 워크스페이스의 plan이 태그 update in-place(공유·실험은 `env` 값 변경 + `managed_by` 추가, prod는 `managed_by` 추가)만이며 destroy·create가 0이다.

**3. `careerhub-secrets-prod`와 state 이동.**
`_modules/careerhub-env`와 `envs/prod/careerhub`를 쓰고, `tfc/`에 `careerhub-secrets-prod`를 프로젝트 `prod-careerhub`에 선언한다(trigger prefix에 모듈 경로).
머지 뒤 새 워크스페이스는 비어 있다 — 아직 run을 만들지 않는다.
사람이 CLI로 한 세션에 셋을 옮긴다.
`prod-careerhub-zitadel`·`careerhub-oauth` 워크스페이스에서 `terraform state pull`로 받은 원본을 그대로 보관한다.
로컬에서 `state mv -state=<원본> -state-out=<새 state>`로 `random_password.zitadel_masterkey`·`aws_ssm_parameter.zitadel_masterkey`·`aws_ssm_parameter.google_client`를 `module.careerhub.<type>.<name>` 주소로 옮긴다.
새 state를 `careerhub-secrets-prod`에 `state push`하고, 옛 두 워크스페이스에서 `state rm`으로 셋을 뗀다.
합격선: `careerhub-secrets-prod`의 plan이 "No changes", `prod-careerhub-zitadel` 워크스페이스의 state가 비어 있음, SSM의 masterkey 값이 그대로여서 ExternalSecret 재동기화 뒤 prod Zitadel pod가 정상.
`prod-careerhub-zitadel` 워크스페이스를 `tfc/`에서 제거해 삭제한다.
되돌리기는 보관한 원본 state를 옛 워크스페이스에 다시 push하는 것이다.

**4. admin 파라미터 재생성.**
`shared/admin-oauth`를 쓰고 `shared-admin-oauth`를 프로젝트 `shared`에 선언·apply한다 — 새 경로 `/jyo-liar/k8s/baremetal/admin/oauth/google-client`에 같은 값이 `env = shared` 태그로 생긴다.
같은 날 jyoliar-k8s에서 argocd·grafana의 ExternalSecret 둘이 새 경로를 읽도록 패치한다.
`careerhub-oauth` 워크스페이스에서 옛 파라미터를 destroy하고 워크스페이스를 삭제한다.
그 사이 ExternalSecret은 이미 만든 Secret을 유지하므로 로그인은 이어진다.
합격선: 두 ExternalSecret이 `SecretSynced`, 옛 경로의 파라미터 없음.

**5. 저장소 안내.**
terraform 저장소의 README·CLAUDE.md를 새 트리, 프로젝트 = `env` 값의 단위, "sensitive면 콘솔" 규칙, "`tfc/`만 CLI" 예외로 고친다.

여기까지가 terraform 구조 개선이다.
그 뒤 `envs/stg/careerhub`를 쓰고, `tfc/`에 프로젝트 `stg-careerhub`·variable set `stg`·워크스페이스 `careerhub-secrets-stg`를 선언하는 것이 stg 환경 구축의 첫 조각이다 — 3절의 여정이 그때 일어난다.

## 5. stg 환경

**자리.** 같은 클러스터의 네임스페이스 `careerhub-stg`.
Argo CD의 services 층에 `careerhub-stg` AppProject·ApplicationSet이 있고, prod와 같은 세 묶음(mongodb·postgresql·apps)을 `gitops/overlays/baremetal/services/careerhub/stg/`에서 동기화한다.
지금 있는 `careerhub-dev` 네임스페이스와 그 안의 MongoDB 1멤버는 지우고, 그 ApplicationSet·AppProject 뼈대는 stg로 이름을 바꿔 쓴다.

**DB.** PG 2인스턴스 + pooler 1, Mongo 2멤버 + arbiter 1 — prod와 같은 토폴로지다.
선언 스토리지만 작다(Mongo 10Gi·PG 5Gi 수준, 실 데이터는 5Gi 안).
PriorityClass는 `database-prod`보다 낮다.
PG 백업은 없다 — stg overlay가 ObjectStore·ScheduledBackup을 지우고 Cluster의 barman plugin·projected token 선언을 비운다.

**앱.** 리뉴얼 스택만 — careerhub-web·Zitadel·api-composer·auth-service(신 세대)·posting·review·userinfo gRPC·수집 jobs.
레거시 front와 Google OAuth 직접 처리 세대의 auth-service는 없다.
careerhub-web의 매니페스트는 base + overlay 모양으로 들어와 stg overlay가 소비한다.

**데이터.** posting·review DB는 prod에서 한 번 복사한다 — `careerhub-stg`의 Job이 prod의 `mongodb-readonly`로 `mongodump`하고 stg의 admin으로 `mongorestore`한다.
Job은 다시 돌릴 수 있어, stg가 깨지면 같은 Job으로 다시 채운다.
userinfo·auth DB·Zitadel 원장은 비어서 시작한다.

**수집.** CronJob 4개(posting-provider wanted·jumpit, skillscanner, review-crawler)는 stg overlay에서 `suspend: true`다.
돌릴 때는 `kubectl create job --from=cronjob/<name>`이다.

**Zitadel.** stg 전용 인스턴스.
`ExternalDomain`은 `id.stg-careerhub.jyo-liar.com`, masterkey와 Google IdP 클라이언트는 3절의 두 파라미터다.
구성 Job이 stg용 선언(IdP·project·careerhub-web 앱·redirect URI `https://stg-careerhub.jyo-liar.com/…`)을 빈 인스턴스에 수렴시킨다.

**접근.** 공개 노출은 없다.
`careerhub-stg`에 kube-vip LoadBalancer Gateway가 서고, 인증서는 `stg-careerhub.jyo-liar.com`과 `*.stg-careerhub.jyo-liar.com` 두 SAN이다.
external-dns가 HTTPRoute에서 레코드를 만들어 공개 DNS에 사설 IP를 싣고, 사람은 Tailscale VPN으로 들어간다.
cloudflared 터널 ingress는 바뀌지 않는다.

## 6. 그 뒤

terraform 구조 개선 → stg 환경 구축의 순서로 티켓이 나간다.
stg가 서면 리뉴얼의 검증 자리가 stg가 되고, prod 컷오버의 그림은 그 전제로 다시 그린다.
필요할 때 띄우고 끝나면 지우는 임시 환경은 이 설계에 없다.

## 이 설계가 하지 않는 것

- CI가 stg에 자동 배포하지 않는다 — 태그 인상은 사람의 PR이다.
- 관측·알림은 환경별로 갈라지지 않는다.
- NetworkPolicy가 없다 — stg pod는 prod DB에 네트워크로 닿는다.
- stg DB 백업이 없다.
- Terraform Stacks를 쓰지 않는다.
- `region`을 프로젝트들이 공유하는 하나의 set으로 모으지 않는다 — 프로젝트마다 같은 값을 둔다.
- 이 저장소 밖에서 `onpremise` 프로젝트나 `common_vars`를 쓰는 워크스페이스가 있어도 건드리지 않는다.
- 프로젝트 수준 설정(알림·팀 권한)과 기존 워크스페이스 이름은 바꾸지 않는다.
