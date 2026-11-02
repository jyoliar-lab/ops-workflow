---
type: discussion
kind: survey
goal: careerhub-env-separation
topic: homelab
subjects: [jyoliar-platform-terraform, terraform-cloud]
status: active
related:
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
---

# terraform에서 환경별 리소스와 공유 리소스를 가르는 모범사례 — 조사 (2026-11-02)

## 질문

careerhub stg 환경 논의의 4-4(terraform 환경 축 구조)가 물었다.
환경마다 따로 서는 리소스(Zitadel masterkey·Google 클라이언트 파라미터·백업 버킷)와 모든 환경이 공유하는 리소스(IAM OIDC Provider·IRSA Role·ECR·Cloudflare zone·알림 채널)를 terraform에서 어떻게 분리하는 것이 권고되는가.
HashiCorp(HCP Terraform 워크스페이스·CLI 워크스페이스·Stacks)·Google Cloud·Gruntwork의 공개 문서를 읽었다.
조사일은 전부 2026-11-02다.

## 조사

### 1. HashiCorp — 워크스페이스는 "컴포넌트 × 환경" 격자이고, 공유는 remote state로

HCP Terraform의 워크스페이스 모범사례는 블라스트 반경을 작게 두는 것에서 시작한다.
> "manage resources in separate workspaces when possible, grouping together only necessary and logically-related resources."

가르는 기준은 변동성이고, 상태를 가진 것과 없는 것을 떼라고 한다.
> "When planning your workspace organization, group resources by volatility."
> "Your compute resources are stateless and should still have a separate workspace."

이름 규약이 분리의 두 축을 그대로 드러낸다 — 컴포넌트(layer)와 환경(env)이 워크스페이스 이름의 좌표다.
> "`<business-unit>-<app-name>-<layer>-<env>`" — "The environment that the workspace manages (for example, prod, staging, QA, prod)."

워크스페이스 사이의 공유는 출력 공유로 한다.
> "To share outputs from a workspace, you must explicitly enable remote state sharing in the workspace settings."
> "you can share the outputs using the tfe_outputs data source."

문서에 "환경당 하나냐 컴포넌트당 하나냐"의 규칙은 없다. 예시 그림이 같은 컴포넌트 분할을 환경마다 반복한다 — "One approach is to create four different workspaces, two for the developer environment and two for production."
— https://developer.hashicorp.com/terraform/cloud-docs/workspaces/best-practices

HashiCorp 엔지니어링 블로그는 그것을 한 줄로 쓴다.
> "One workspace per environment per terraform configuration."
— https://medium.com/hashicorp-engineering/automating-multi-environment-deployments-with-terraform-cloud-workspaces-6d9c7dcd2321

### 2. HashiCorp — CLI 워크스페이스는 환경 분리 도구가 아니다

`terraform workspace`(CLI 워크스페이스)는 같은 백엔드·같은 자격증명 안의 임시 사본을 위한 것이다.
> "Non-default workspaces are often related to feature branches in version control."
> "Workspaces alone are not a suitable tool for system decomposition"
> "the backend for each deployment often has different credentials and access controls … they are not a suitable isolation mechanism for this scenario."

대안은 모듈 + 인스턴스별 구성 + remote state다.
> "you can use one or more re-usable modules to represent the common elements"
> "represent each instance as a separate configuration that instantiates those common elements"
> `terraform_remote_state` 로 "directly consume its root module outputs."
— https://developer.hashicorp.com/terraform/cli/workspaces
— https://developer.hashicorp.com/terraform/language/state/workspaces ("Workspaces are not appropriate for system decomposition or deployments requiring separate credentials and access controls.")

**HCP Terraform 워크스페이스는 CLI 워크스페이스와 다른 것이다.** HCP 워크스페이스는 state·변수·자격증명·실행 설정을 각자 가지므로, 위 "인스턴스별 구성"의 구현체다. 같은 working directory를 보는 HCP 워크스페이스 둘은 CLI 워크스페이스 둘이 아니라 별도 구성 둘이다.

튜토리얼은 디렉터리 분리와 워크스페이스 분리의 비용을 대칭으로 적는다.
> 디렉터리 — "Directory-separated environments rely on duplicate Terraform code." / "the directory structure runs the risk of creating drift between the environments over time." / "To separate environments with potential configuration differences, use a directory structure."
> 워크스페이스 — "Workspace-separated environments use the same Terraform code but have different state files" / "Use workspaces for environments that do not greatly deviate from one another" / "you must … be aware of the workspace you are working in"
— https://developer.hashicorp.com/terraform/tutorials/modules/organize-configuration

### 3. Google Cloud — `modules/` + `environments/<env>/` 루트, 공유는 출력만

```
SERVICE-DIRECTORY/
   -- modules/
      -- <service-name>/   (main.tf · variables.tf · outputs.tf · provider.tf)
   -- environments/
      -- dev/   (backend.tf · main.tf)
      -- qa/    (backend.tf · main.tf)
      -- prod/  (backend.tf · main.tf)
```

> "Each environment directory (`dev`, `qa`, `prod`) corresponds to a default Terraform workspace" "and deploys a version of the service to that environment."

환경 디렉터리는 얇은 루트이고 내용은 모듈에 있다.
다른 구성이 읽을 수 있는 것은 루트의 출력만이다.
> "Other Terraform environments and applications can reference root module-level outputs only."
> "By using remote state, you can reference root module outputs."

state 크기에 상한을 권고한다.
> "Don't include more than 100 resources (and ideally only a few dozen) in a single state."
— https://docs.cloud.google.com/docs/terraform/best-practices/root-modules

이 문서에 "모든 환경이 공유하는 리소스" 전용 자리는 없다 — 서비스 단위 레이아웃이라, 공유 리소스는 다른 서비스 디렉터리(다른 루트)이고 출력으로 소비된다.

### 4. Gruntwork — 공유 리소스의 자리를 `_global`로 명시한다

```
account
└ _global
└ region
   └ _global
   └ environment
      └ category
         └ resource
```

> account 수준 `_global` — "a `_global` folder may exist to define resources applicable across all AWS regions in the account" "such as IAM users, Route 53 hosted zones, or CloudTrail configurations."
> region 수준 `_global` — "A `_global` folder may also be included here to define resources shared across environments in the region" "such as Route 53 A records, SNS topics, or ECR repositories."
> 환경 — "you might organize units within regions into environments like `qa`, `stage`, or `prod`." "many organizations chose to isolate different environments by AWS account".
— https://docs.gruntwork.io/2.0/docs/overview/concepts/infrastructure-live
— https://docs.gruntwork.io/foundations/iac-foundations/folder-structure

여기서 공유 리소스의 예시가 이 저장소의 것과 겹친다 — IAM(IRSA Role·OIDC Provider), DNS zone(Cloudflare zone), ECR이 전부 `_global`이고, 환경 폴더에는 그 환경의 것만 있다.
`_global` 폴더에는 환경 축이 없다 — 공유 리소스는 `env` 변수를 받지 않는다.

### 5. HashiCorp Stacks — 한 구성 안의 "컴포넌트 × deployment"

Stacks는 같은 격자를 워크스페이스 여럿이 아니라 구성 하나로 표현한다.
> "Stacks let you define deployments for each environment within a single configuration"
> 환경 추가 = `deployment` 블록 추가 — "By default, HCP Terraform notices that you changed your configuration and will create a new plan for your new deployment."
> "Stacks let you define and deploy shared infrastructure components across different accounts"
— https://developer.hashicorp.com/terraform/language/stacks/use-cases

Stacks는 HCP Terraform 전용 워크플로우이고, 기존 워크스페이스의 state를 그대로 쓰지 않는다(마이그레이션이 따른다).
개요 문서의 한도(컴포넌트 100·리소스 1만·deployment group당 deployment 1)는 바뀔 수 있다.
— https://docs.hashicorp.com/terraform/cloud-docs/stacks

### 6. 비교 — 세 출처가 같은 뼈대를 말한다

| | HashiCorp(HCP 워크스페이스) | Google Cloud | Gruntwork |
|---|---|---|---|
| 환경별 리소스의 루트 | 워크스페이스 `<app>-<layer>-<env>` 하나씩 | `environments/<env>/` 디렉터리 하나씩 | `<account>/<region>/<env>/<category>/` |
| 공유 리소스의 루트 | 별도 워크스페이스(변동성·소유로 가름) | 별도 서비스 디렉터리 | `_global/`(account·region 수준) — 환경 축 없음 |
| 공유 → 환경 전달 | remote state sharing · `tfe_outputs` | 루트 출력 + remote state | Terragrunt `dependency`(remote state) |
| 코드 중복 처리 | 같은 디렉터리를 여러 워크스페이스가 봄 | 모듈 + 얇은 루트 | 모듈 + 얇은 `terragrunt.hcl` |
| 환경 차이가 클 때 | 디렉터리로 가라(튜토리얼) | 디렉터리가 기본 | 디렉터리가 기본 |

공통 뼈대는 셋이다.
환경별 리소스와 공유 리소스는 **state(루트)가 다르다.**
공유 루트는 하나이고 환경 축이 없으며, 환경별 루트는 환경마다 하나다.
의존은 **공유 → 환경 단방향**이고 출력(remote state)으로만 건넌다.

## 논의 문서로 가져가는 것

- 모범사례는 "환경별 루트를 디렉터리로 두느냐 같은 디렉터리의 HCP 워크스페이스로 두느냐"를 가르지 않는다. 둘 다 안에 있다. 가르는 기준은 환경 사이의 차이 크기다 — 차이가 작으면 워크스페이스, 크면 디렉터리.
- 셋이 일치하는 것은 공유 리소스의 처리다 — 별도 루트, 환경 축 없음, 출력으로만 전달, 단방향. **4-4의 A·B 어느 쪽을 고르든 이 부분은 같아야 한다.**
- 현재 저장소에 대면 공유 루트는 `iam`·`ci`·`cloudflare`·`alert`이고 환경별 루트는 `zitadel`·`oauth/google.tf`·`backup`이다. `oauth/admin.tf`는 공유 리소스가 환경별 디렉터리에 들어가 있는 오분류다 — 어느 안에서도 공유 루트로 옮긴다.
- 공유 → 환경 단방향 패턴은 이미 있다 — `backup/data.tf`가 `_modules/tfc_remote_state`로 `onpremise-iam`의 OIDC Provider ARN을 읽는다. 새 구조는 이것을 규칙으로 승격하는 일이다.
- 공유 루트(`iam`·`ci`·`cloudflare`·`alert`)가 지금 `env` 변수를 받아 provider `default_tags`에 넣는다(`*/providers.tf`). Gruntwork `_global`에는 환경 축이 없다 — 공유 루트에서 `env`를 걷어내는 것이 분류를 코드로 드러낸다.
- 4-4 A는 HashiCorp의 `<app>-<layer>-<env>` 워크스페이스 격자에, B는 Google의 `environments/<env>/` 디렉터리에 대응한다. 전환 조건(튜토리얼): 환경 사이에 "configuration differences"가 생기면 디렉터리로.
- Stacks는 같은 격자의 세 번째 표현이지만 state 마이그레이션이 따르는 별도 워크플로우다 — 지금 저장소 규모에서 선택지로 올리지 않는다.
