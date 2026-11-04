---
type: digest
goal: platform-terraform-restructure
topic: homelab
subjects: [jyoliar-platform-terraform, terraform-cloud, tfe-provider, variable-set, aws-tags, zitadel, external-secrets, cloudnativepg, barman-cloud-plugin, aws-s3, aws-iam]
status: current
ref-adrs: [ADR-0034]
sources:
  - docs/homelab/discussion/261102_2007_terraform-env-vs-shared-resource-separation-survey.md
  - docs/homelab/discussion/261103_1429_terraform-restructure-migration-plan.md
  - docs/homelab/discussion/261103_1809_tfe-project-variable-set-provider-survey.md
  - docs/homelab/discussion/261103_1809_tfc-project-and-variable-set-redesign.md
  - docs/homelab/discussion/261104_1636_cnpg-backup-module-and-workspace-merge.md
superseded_by:
---

# jyoliar-platform-terraform 구조 개선 — 환경 축 · 프로젝트 · 이행 (2026-11-04 시점)

## 개요

`jyoliar-platform-terraform`은 홈랩 Kubernetes가 AWS·Cloudflare·HCP Terraform에 두는 것들을 선언하는 저장소다.
지금은 최상위 디렉터리 하나가 워크스페이스 하나이고, 환경(`prod`)과 환경 무관(공유)의 구분이 디렉터리에도 프로젝트에도 없다.
이 설계는 저장소에 환경 축을 넣는다 — 공유 리소스와 환경별 리소스를 디렉터리로 가르고, 환경별 리소스는 모듈 둘(인증 재료 · CNPG 백업)을 환경 루트 하나가 부르는 모양으로 바꾼다.
HCP Terraform 쪽에서는 프로젝트가 그 축을 받는다 — 디렉터리 묶음 하나가 프로젝트 하나이고, 프로젝트가 소유한 variable set이 자기 워크스페이스 전부에 `env`·`region`을 준다.
모든 AWS 리소스는 `env`와 `managed_by` 태그를 달아, terraform 없이 AWS 콘솔만 봐도 어느 프로젝트의 것이고 코드가 만든 것인지 읽힌다.
이 문서는 새 구조가 어떻게 돌아가고, 지금 있는 리소스가 어떤 순서로 그 자리에 가는지를 서술한다.
관통하는 사례는 **prod Zitadel의 masterkey 한 개**다 — 그것이 어디서 선언되고, 어떤 프로젝트가 `env`를 주고, 지금 자리에서 새 자리로 어떻게 옮겨 가는가.

## 어휘

- **공유 루트** — 모든 환경이 함께 쓰는 리소스를 가진 terraform 루트. 환경 축이 없다. `shared/` 아래.
- **환경 루트** — 한 환경의 리소스만 가진 얇은 루트. 모듈을 부른다. `envs/<env>/careerhub` 하나가 환경 하나이고 워크스페이스 하나다.
- **메타 워크스페이스** — 다른 워크스페이스들의 이름·경로·연결·프로젝트·variable set을 선언하는 루트. 최상위 `tfc/`. 공유 인프라와 같은 층이 아니다.
- **프로젝트** — HCP Terraform에서 워크스페이스를 묶는 폴더. 디렉터리 묶음 하나(`shared/`·`lab/`·`envs/prod/`)가 프로젝트 하나다. 프로젝트는 variable set 하나를 소유하고, 그 set이 프로젝트의 모든 워크스페이스에 `env`·`region`을 준다 — 프로젝트 하나 = `env` 값 하나.
- **env** — 워크스페이스가 프로젝트에서 받는 변수이자 모든 AWS 리소스의 태그. 환경 프로젝트에서는 환경 이름(`prod`)이고, 공유·실험 프로젝트에서는 디렉터리 이름(`shared`·`lab`)이다. 환경 루트에서는 SSM 경로(`/jyo-liar/k8s/baremetal/careerhub/<env>/…`)와 네임스페이스(`careerhub-<env>`)의 재료다.
- **태그** — AWS provider의 `default_tags`가 모든 리소스에 `env`와 `managed_by = terraform`을 붙인다.

## 1. 저장소의 모양

```
tfc/                         # 메타 워크스페이스 — 아래 모든 프로젝트 · variable set · 워크스페이스를 선언한다
_modules/
  tfc_remote_state/          # 다른 워크스페이스의 출력을 읽는다
  nat/
  cnpg-backup/               # CNPG 클러스터 하나의 백업 재료 — S3 버킷 · IRSA Role
  careerhub/
    auth/                    # 환경 하나의 careerhub 인증 재료 — masterkey · google-client
shared/                      # 프로젝트 shared — env = shared
  iam/                       # OIDC Provider · IRSA Role(external-secrets · ecr-image-puller)
  ci/                        # ECR · CodeBuild
  cloudflare/                # zone · 터널 · 엣지 · external-dns 토큰
  alert/                     # Discord 채널 · webhook
  admin-oauth/               # argocd·grafana 로그인용 Google 클라이언트
envs/
  prod/                      # 프로젝트 prod-careerhub — env = prod
    careerhub/               # module "auth" · module "cnpg_backup"
lab/                         # 프로젝트 lab — env = lab
  vpc/  vpn/                 # AWS 모의 환경
```

`_modules/careerhub/auth`가 환경 하나의 careerhub 인증 재료를 정의한다.
`_modules/careerhub/`는 디렉터리일 뿐이고, 모듈은 그 아래 `auth/`다.
`random_password`로 32자 masterkey를 만들어 `/jyo-liar/k8s/baremetal/careerhub/${var.env}/zitadel/masterkey`에 SecureString으로 심고, 변수로 받은 Google 클라이언트 ID·secret을 `/jyo-liar/k8s/baremetal/careerhub/${var.env}/oauth/google-client`에 심는다.
두 파라미터 모두 `prevent_destroy`다.
출력은 파라미터의 경로이고, 값은 내보내지 않는다.

`_modules/cnpg-backup`이 CNPG 클러스터 하나의 백업 재료를 정의한다.
네임스페이스와 Cluster 이름, OIDC Provider ARN과 issuer URL을 받아 S3 버킷 `cnpg-backup-<namespace>-<cluster>-<계정>`과 IRSA Role `cnpg-backup-<namespace>-<cluster>`를 만든다 — `careerhub`라는 글자는 모듈에 없고 호출자가 넘긴다.
버킷에는 SSE-S3·공개 차단·라이프사이클(미완 멀티파트 7d)이 붙고 `prevent_destroy`다 — 버저닝은 없다.
Role은 그 네임스페이스의 ServiceAccount `<cluster>`와 `<cluster>-restore` 둘만 신뢰하고, Policy는 barman-cloud가 그 버킷에 필요한 S3 액션만 허용한다.
출력은 버킷 이름과 Role ARN이다.

`envs/prod/careerhub/main.tf`는 두 모듈을 부르는 블록 둘이다.
`env`는 리터럴이 아니라 변수다 — 값 `prod`는 프로젝트 `prod-careerhub`의 variable set이 준다.
백업 모듈에 넘기는 OIDC Provider ARN은 루트가 `tfc_remote_state`로 `shared-iam`에서 읽는다 — 모듈은 `tfe` provider를 모른다.

```hcl
module "auth" {
  source               = "../../../_modules/careerhub/auth"
  env                  = var.env
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
}

module "cnpg_backup" {
  source                = "../../../_modules/cnpg-backup"
  namespace             = "careerhub-${var.env}"
  cluster_name          = "careerhub-postgresql"
  k8s_oidc_provider_arn = local.iam_outputs["k8s_oidc_provider_arn"]
  k8s_oidc_issuer_url   = var.k8s_oidc_issuer_url
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
`shared/admin-oauth`의 파라미터 경로는 `/jyo-liar/k8s/baremetal/admin/oauth/google-client`다 — 환경 이름이 없다.

의존은 공유 → 환경 한 방향이다.
`envs/prod/careerhub`가 `shared-iam`의 OIDC Provider ARN을 `tfc_remote_state`로 읽는다.
공유 루트가 환경 루트를 읽는 일은 없다.

## 2. 워크스페이스와 구동

디렉터리 하나가 HCP Terraform 워크스페이스 하나이고, 디렉터리 묶음 하나가 프로젝트 하나다.
워크스페이스 이름은 디렉터리 좌표를 따른다 — `<env>-<루트>`.
프로젝트마다 자기가 소유한 variable set 하나가 붙어 `env`·`region`을 준다.

| 디렉터리 | 프로젝트 | variable set | 워크스페이스 |
|---|---|---|---|
| `tfc` | `Default Project` | 없음 | `tfc` |
| `shared/iam` · `shared/ci` · `shared/cloudflare` · `shared/alert` · `shared/admin-oauth` | `shared` | `shared` — `env = shared` | `shared-iam` · `shared-ci` · `shared-cloudflare` · `shared-alert` · `shared-admin-oauth` |
| `envs/prod/careerhub` | `prod-careerhub` | `prod` — `env = prod` | `prod-careerhub` |
| `lab/vpc` · `lab/vpn` | `lab` | `lab` — `env = lab` | `lab-vpc` · `lab-vpn` |

variable set은 프로젝트 소유다 — 그 프로젝트 안에만 붙고 다른 프로젝트에는 붙일 수 없다.
`priority`가 켜져 있어 워크스페이스에 같은 이름의 변수가 있어도 set의 값이 이긴다.
`region`은 모든 set에 같은 값(`ap-northeast-2`)으로 들어 있다.
워크스페이스에는 `env`·`region` 변수가 없다 — 프로젝트에서 받는다.

`tfc`를 뺀 전부가 VCS 연동이다.
`main`에 머지되면 그 워크스페이스가 plan을 만들고, 사람이 콘솔에서 apply를 승인한다.
VCS 루트의 코드에 `cloud`·`backend` 블록은 없다.
`tfc`만 로컬 CLI다 — `tfc/`에 커밋된 `cloud` 블록으로 운영자 머신에서 plan·apply하고, state만 HCP에 둔다.
워크스페이스는 자기 working directory와 `trigger_prefixes` 아래 파일이 바뀔 때만 run을 만든다 — `prod-careerhub`는 `_modules/careerhub/auth`·`_modules/cnpg-backup`·`_modules/tfc_remote_state`를, `lab-vpn`은 `_modules/tfc_remote_state`와 `_modules/nat`를 trigger prefix로 가진다.

`tfc/`가 이 표 전체를 선언한다 — 프로젝트는 `tfe_project`, variable set은 `tfe_variable_set`(`parent_project_id`로 소유 프로젝트를 가리킨다)과 `tfe_project_variable_set`(프로젝트에 붙인다), set의 변수 `env`·`region`은 `tfe_variable`(`variable_set_id`), 워크스페이스는 `tfe_workspace`·`tfe_workspace_settings` — 이름, working directory, 프로젝트, GitHub App 연결, 브랜치, trigger prefix, 실행 모드, remote state 소비자(`shared-iam` → `prod-careerhub`, `lab-vpc` → `lab-vpn`).
워크스페이스 고유의 비밀 아닌 변수(`cnpg_app_name`·`discord_server_id` 같은 것)도 `tfe_variable`로 선언한다.
비밀(Google 클라이언트 ID·secret, Discord 토큰, Cloudflare 자격증명)은 콘솔에서 sensitive 변수로 넣는다 — sensitive면 콘솔, 아니면 코드.
워크스페이스를 하나 더 만드는 것, 개명하는 것, 경로를 옮기는 것은 전부 `tfc/`의 PR이다.
`tfc` 자신은 운영자의 `terraform login` 자격증명으로 돌고, 그 토큰이 tfe provider의 토큰이다 — 워크스페이스 변수에 토큰이 없다.

**환경 하나를 더하는 것**도 같은 모양이다.
`envs/<env>/careerhub` 디렉터리 하나와, `tfc/`에 프로젝트 `<env>-careerhub`·그것이 소유한 variable set(`env = <env>`·`region`)·워크스페이스 `<env>-careerhub` 선언, `shared-iam`의 remote state 소비자에 그 워크스페이스 추가, 콘솔에 그 환경의 Google 클라이언트 sensitive 변수.
모듈 둘은 그대로이고, `env` 값만 프로젝트에서 달리 들어온다.
masterkey와 Google 클라이언트 파라미터는 `/…/careerhub/<env>/…` 경로에 `env = <env>` 태그로, 백업 버킷과 Role은 `cnpg-backup-careerhub-<env>-careerhub-postgresql` 이름으로 선다.

## 3. 사례 — prod masterkey 한 개

prod Zitadel의 masterkey는 `aws_ssm_parameter.zitadel_masterkey`와 그 값을 만든 `random_password.zitadel_masterkey`다.
새 구조에서 둘은 `_modules/careerhub/auth`에 정의되고, `envs/prod/careerhub`가 `module "auth"`로 부른다.
state 주소는 `module.auth.random_password.zitadel_masterkey`·`module.auth.aws_ssm_parameter.zitadel_masterkey`다.
`env = prod`는 `envs/prod/careerhub`가 속한 프로젝트 `prod-careerhub`의 variable set `prod`가 준다 — 루트는 `variable "env"`를 선언만 한다.
파라미터 경로는 지금과 같은 `/jyo-liar/k8s/baremetal/careerhub/prod/zitadel/masterkey`이고, 태그 `env = prod`·`managed_by = terraform`이 붙는다.
값은 바뀌지 않는다 — 값이 바뀌면 prod Zitadel이 자기 DB를 열지 못한다.
그래서 이행은 재생성이 아니라 state 이동이다.

## 4. 이행 — masterkey가 새 자리로 가는 순서

지금 prod의 masterkey는 `zitadel/` 디렉터리의 `prod-careerhub-zitadel` 워크스페이스 state에, Google 클라이언트 파라미터는 `oauth/` 디렉터리의 `careerhub-oauth` 워크스페이스 state에 있다.
둘을 `prod-careerhub`로 옮기고 나머지 디렉터리를 새 자리로 보내는 순서는 다음이다.
단계마다 합격선이 있고, 넘지 못하면 다음 단계로 가지 않는다.

**0. 메타 워크스페이스.**
`tfc/` 루트를 쓴다 — `cloud { workspaces { name = "tfc" } }` 블록을 포함한다.
`terraform login` 뒤 `terraform init`을 치면 HCP에 `tfc` 워크스페이스가 생긴다. 실행 모드를 local로 두고 GitHub App 설치를 확인한다.
기존 워크스페이스 9개와 `tfc` 자신, 프로젝트 3개(`Default Project`·`onpremise`·`prod-careerhub`)를 지금 이름·지금 경로 그대로 선언하고 import한다.
합격선: `tfc`의 plan이 "No changes" — 선언이 HCP의 현재와 일치한다.

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

**3. `prod-careerhub`와 state 이동.**
`_modules/careerhub/auth`와 `envs/prod/careerhub`를 쓰고, `tfc/`에 `prod-careerhub`를 프로젝트 `prod-careerhub`에 선언한다(trigger prefix에 모듈 경로).
머지 뒤 새 워크스페이스는 비어 있다 — 아직 run을 만들지 않는다.
사람이 CLI로 한 세션에 셋을 옮긴다.
`prod-careerhub-zitadel`·`careerhub-oauth` 워크스페이스에서 `terraform state pull`로 받은 원본을 그대로 보관한다.
로컬에서 `state mv -state=<원본> -state-out=<새 state>`로 `random_password.zitadel_masterkey`·`aws_ssm_parameter.zitadel_masterkey`·`aws_ssm_parameter.google_client`를 `module.auth.<type>.<name>` 주소로 옮긴다.
새 state를 `prod-careerhub`에 `state push`하고, 옛 두 워크스페이스에서 `state rm`으로 셋을 뗀다.
합격선: `prod-careerhub`의 plan이 "No changes", `prod-careerhub-zitadel` 워크스페이스의 state가 비어 있음, SSM의 masterkey 값이 그대로여서 ExternalSecret 재동기화 뒤 prod Zitadel pod가 정상.
`prod-careerhub-zitadel` 워크스페이스를 `tfc/`에서 제거해 삭제하고, `zitadel/` 디렉터리를 지운다.
되돌리기는 보관한 원본 state를 옛 워크스페이스에 다시 push하는 것이다.

**4. admin 파라미터 재생성.**
`shared/admin-oauth`를 쓰고 `shared-admin-oauth`를 프로젝트 `shared`에 선언·apply한다 — 새 경로 `/jyo-liar/k8s/baremetal/admin/oauth/google-client`에 같은 값이 `env = shared` 태그로 생긴다.
같은 날 jyoliar-k8s에서 argocd·grafana의 ExternalSecret 둘이 새 경로를 읽도록 패치한다.
`careerhub-oauth` 워크스페이스에서 옛 파라미터를 destroy하고 워크스페이스를 삭제하고, `oauth/` 디렉터리를 지운다.
그 사이 ExternalSecret은 이미 만든 Secret을 유지하므로 로그인은 이어진다.
합격선: 두 ExternalSecret이 `SecretSynced`, 옛 경로의 파라미터 없음.

**5. 저장소 안내.**
terraform 저장소의 README·CLAUDE.md를 새 트리, 프로젝트 = `env` 값의 단위, "sensitive면 콘솔" 규칙, "`tfc/`만 CLI" 예외로 고친다.

**6. 백업을 모듈로 — 신규 생성, 옛 것 destroy.**
state 이동은 없다 — 이름이 바뀌므로 모듈이 만드는 것은 전부 새 리소스이고, 옛 버킷의 백업(보존 3d)은 보존하지 않는다.
첫 PR은 terraform이다.
`_modules/cnpg-backup`을 쓰고 `envs/prod/careerhub`에 `tfe` provider·`tfc_remote_state`·`module "cnpg_backup"`을 더한다.
`tfc/`에서 `shared-iam`의 remote state 소비자에 `prod-careerhub`를 더하고 `prod-careerhub`의 trigger prefix에 두 모듈 경로를 더한다 — 옛 루트와 `prod-careerhub-backup`은 아직 그대로다.
`tfc` apply가 먼저다 — 소비자가 바뀌어야 `prod-careerhub`가 `shared-iam`을 읽는다.
머지 뒤 `prod-careerhub`의 plan은 새 버킷·Role·Policy 생성만이다 — `auth`의 파라미터는 건드리지 않는다.
합격선: `cnpg-backup-careerhub-prod-careerhub-postgresql-<계정>` 버킷과 같은 이름의 Role이 있고 옛 것도 그대로다.
둘째 PR은 jyoliar-k8s다.
prod overlay의 `destinationPath`와 `AWS_ROLE_ARN`을 새 버킷·Role로 바꾸고, on-demand `Backup` 하나를 만든다.
합격선: 새 버킷에 base backup과 WAL이 쌓인다.
그 다음은 콘솔 둘이다.
사람이 S3 콘솔에서 옛 버킷을 비운다 — 버저닝 버킷이라 모든 버전과 delete marker까지 지우는 "비우기"다.
`prod-careerhub-backup`에 destroy run을 걸어 옛 여덟을 지운다 — 비어 있지 않은 버킷은 거부된다.
셋째 PR은 terraform이다.
`tfc/`에서 `prod-careerhub-backup` 선언을 제거하고 `envs/prod/careerhub-backup` 디렉터리를 지운다 — state가 빈 뒤라 워크스페이스 삭제가 통과한다.
합격선: `prod-careerhub`의 plan이 "No changes", `prod-careerhub-backup` 워크스페이스 없음, 옛 버킷·Role 없음.
README·CLAUDE.md는 각 PR이 현 상태로 고친다.
전환 시점 이전으로의 PITR은 옛 버킷과 함께 사라진다 — 리뉴얼 컷오버의 롤백 창과 겹치지 않는 때에 한다.

여기까지가 이 설계의 범위다.
그 위에 환경을 더하는 것(2절의 "환경 하나를 더하는 것")은 그 환경의 설계가 정한다.

## 이 설계가 하지 않는 것

- Terraform Stacks를 쓰지 않는다.
- 모듈을 버저닝하지 않는다 — 저장소 안 상대 경로다.
- `vpc`·`vpn`의 내용과 공유 루트의 provider 버전(aws 5.81 · 6.27 혼재)은 건드리지 않는다.
- `region`을 프로젝트들이 공유하는 하나의 set으로 모으지 않는다 — 프로젝트마다 같은 값을 둔다.
- 이 저장소 밖에서 `onpremise` 프로젝트나 `common_vars`를 쓰는 워크스페이스가 있어도 건드리지 않는다.
- 프로젝트 수준 설정(알림·팀 권한)과 기존 워크스페이스 이름은 바꾸지 않는다.
