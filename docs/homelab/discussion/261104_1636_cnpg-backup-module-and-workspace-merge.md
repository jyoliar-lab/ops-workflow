---
type: discussion
kind: deliberation
goal: platform-terraform-restructure
topic: homelab
subjects: [jyoliar-platform-terraform, cloudnativepg, barman-cloud-plugin, terraform-cloud, aws-s3, aws-iam, careerhub-prod, careerhub-stg, jyoliar-k8s]
status: done
ref-adrs: [ADR-0034]
related:
  - docs/homelab/discussion/261103_1429_terraform-restructure-migration-plan.md
  - docs/homelab/discussion/261103_1809_tfc-project-and-variable-set-redesign.md
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
---

# CNPG 백업 루트를 모듈로 — `_modules/cnpg-backup` 과 `prod-careerhub` 로의 합병

## 1. 문제

`envs/prod/careerhub-backup`은 CNPG(PostgreSQL) 클러스터 하나의 백업 재료다 — S3 버킷 하나와 그 부속 설정 넷, 버킷에 쓰는 IRSA Role·Policy·Attachment 셋.
환경이 늘면 이 여덟이 환경마다 한 벌씩 반복된다.
지금은 루트 하나에 리소스가 직접 서 있어, 환경을 더하려면 디렉터리를 복사하고 워크스페이스를 하나 더 선언해야 한다.
`careerhub/auth`가 모듈 호출 하나로 환경 하나를 세우는 모양과 다르다.

이 논의는 그 여덟을 모듈로 떼고, 모듈의 범위·입력·보호, 그리고 모듈이 서는 자리를 정한다.
두 번째 호출자는 stg다 — careerhub stg 논의(4-1)가 "stg 백업 없음"으로 닫았던 것을 사람이 이 논의에서 되돌렸다.
stg도 prod와 같은 토폴로지·같은 보존(3d · 03:00 KST)으로 백업을 갖는다.

열려 있던 것은 둘이다.
모듈이 만드는 버킷·Role의 이름 규칙 — 지금 이름을 유지할지, 클러스터 좌표로 새로 지을지.
그리고 여덟 리소스를 state 이동으로 옮길지, 새 워크스페이스에서 새로 만들고 옛 것을 지울지 — 기존 백업을 보존하는가가 가른다.

## 2. 실측

코드 — `workspace/ref/jyoliar-platform-terraform` (2026-11-04, `2ce5bf7`).

- `envs/prod/careerhub-backup`의 리소스는 여덟이다 — `aws_s3_bucket.cnpg`, `aws_s3_bucket_versioning.cnpg`, `aws_s3_bucket_server_side_encryption_configuration.cnpg`(SSE-S3 · `blocked_encryption_types = ["SSE-C"]`), `aws_s3_bucket_public_access_block.cnpg`, `aws_s3_bucket_lifecycle_configuration.cnpg`(미완 멀티파트 7d · 비현행 버전 30d), `aws_iam_role.cnpg_backup`, `aws_iam_policy.cnpg_backup`, `aws_iam_role_policy_attachment.cnpg_backup`.
  그 외는 `data.aws_caller_identity`와 `module.tfc_remote_state`(data `tfe_outputs`)다 — state 에 남는 실체가 없다.
- 이름은 전부 `local.name_prefix = "homelab-cnpg-backup-${var.env}"`에서 파생된다 — 버킷 `homelab-cnpg-backup-prod-986069063944`, Role `homelab-cnpg-backup-prod`, Policy `homelab-cnpg-backup-prod-policy`.
  이름에 클러스터가 없다 — 같은 환경에 CNPG 클러스터가 둘이면 이 규칙으로는 두 번 부를 수 없다.
- 신뢰 정책의 `sub`는 둘을 열거한다 — `system:serviceaccount:careerhub-${var.env}:careerhub-postgresql`과 같은 네임스페이스의 `careerhub-postgresql-restore`.
  `cnpg_app_name = "careerhub"` · `cnpg_sa_name = "careerhub-postgresql"`이 변수 default 로 박혀 있다.
- OIDC Provider ARN 은 `shared-iam`의 출력을 `_modules/tfc_remote_state`로 읽는다(`data.tf`).
  `tfc/ws-shared.tf`의 `shared-iam`은 `remote_state_consumer_ids = [module.backup.id]` — 소비자가 `prod-careerhub-backup` 하나다.
- `envs/prod/careerhub`는 `module "auth"` 하나를 부르는 얇은 루트다.
  provider 는 `aws`·`random`만 있다 — `tfe` provider 와 `tfc_remote_state` 호출이 없다.
  `tfc/ws-envs.tf`의 `prod-careerhub`는 `another_trigger_patterns = ["_modules/careerhub/auth/**/*"]`다.
- 버킷에 `prevent_destroy`가 없다.
  `tfc/_modules/workspace`의 `tfe_workspace`에는 `prevent_destroy = true` · `force_delete = false`가 있다 — 워크스페이스를 지우려면 선언을 코드에서 제거해야 하고, state 가 비어 있어야 한다.
- 소비자 — `jyoliar-k8s/gitops/overlays/baremetal/services/careerhub/prod/postgresql/objectstore-patch.yaml`에 `destinationPath: s3://homelab-cnpg-backup-prod-986069063944`와 `AWS_ROLE_ARN: arn:aws:iam::986069063944:role/homelab-cnpg-backup-prod`가 리터럴로 있다.
  base 의 `ScheduledBackup`은 `immediate: true`다 — 생성 시점에 한 번 즉시 백업한다.
  `retentionPolicy: 3d`.

Terraform 문서 (2026-11-04).

- `lifecycle` 인자는 리터럴만 받는다 — "only literal values can be used because the processing happens too early for arbitrary expression evaluation" ([lifecycle meta-argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)).
  `prevent_destroy`를 변수로 켜고 끌 수 없다 — 모듈 전체가 한 값이다.
- `prevent_destroy`는 destroy 와 replace 가 든 plan 을 거부한다.
  리소스 블록을 코드에서 지우는 것은 막지 않는다 — state 에 lifecycle 이 기록되지 않아 apply 가 실제 객체를 지운다.
- `aws_s3_bucket.bucket`과 `aws_iam_role.name`은 바꾸면 replace 다.
  S3 버킷 이름은 3~63자 소문자 · 전역 유일, IAM Role 이름은 64자 이내다.
- `aws_s3_bucket`은 비어 있지 않으면 destroy 가 거부된다(`force_destroy` 기본 false).
  버저닝이 켜진 버킷은 객체만 지우면 delete marker 와 비현행 버전이 남아 비어 있지 않다 — 콘솔의 "비우기"는 모든 버전과 delete marker 를 함께 지운다.

CNPG barman-cloud plugin 문서 (2026-11-04, [usage](https://cloudnative-pg.io/plugin-barman-cloud/docs/usage/)).

- `ObjectStore.spec.configuration.destinationPath`가 버킷 경로다.
  on-demand 백업은 `Backup` 매니페스트(`method: plugin`) 또는 `kubectl cnpg backup --method=plugin --plugin-name=barman-cloud.cloudnative-pg.io`로 만든다.
- 돌고 있는 Cluster 의 `destinationPath`를 빈 버킷으로 바꿀 때 WAL 아카이빙과 기존 백업 카탈로그가 어떻게 되는지는 이 문서가 말하지 않는다.
  경계 전후를 가로지르는 PITR 은 옛 버킷에 기대고, 새 버킷의 첫 base backup 이 있어야 새 버킷만으로 복구가 된다 — 이것은 barman 의 일반 성질이고, 이 클러스터에서의 동작은 실측해야 한다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 두 번째 호출자 — stg 백업의 판정 번복

**선택: stg 도 PG 백업을 갖는다.** careerhub stg 논의 4-1 의 "백업 선언은 overlay 에서 삭제한다"를 되돌린다 — 그 판정 줄과 digest 두 건(careerhub stg · terraform 구조)을 고친다. stg 의 보존·스케줄은 prod 와 같다(3d · 03:00 KST). (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- prod 안의 다른 CNPG 클러스터 — 지금 없다
- MongoDB 백업과의 짝 맞추기 — Mongo 백업은 범위 밖(3-7)
- 구체 호출자 없이 준비만 — 호출자가 하나인 모듈은 추상화가 아니라 간접화다

</details>

### 3-2. 모듈의 일반성

**선택: CNPG 클러스터 하나의 백업 모듈.** 입력은 네임스페이스 · Cluster 이름 · OIDC Provider ARN · issuer URL 이고, `careerhub`라는 글자는 호출자가 넘긴다. 어느 CNPG 클러스터든 부를 수 있다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- careerhub 전용(`_modules/careerhub/pg-backup`) — careerhub 기본값이 모듈에 박혀 다른 클러스터를 못 부른다
- S3 + IRSA 범용 — barman 이 요구하는 S3 액션 목록과 `-restore` SA 관례가 모듈에서 빠져 호출자가 매번 다시 적는다

</details>

### 3-3. 모듈이 서는 자리 — `prod-careerhub` 로 합친다

**선택: `envs/prod/careerhub`가 `module "auth"` 옆에 `module "cnpg_backup"`을 부른다.** 워크스페이스 `prod-careerhub-backup`은 사라지고 환경 하나 = 워크스페이스 하나가 된다. stateful 버킷을 다른 state 에 두던 변동성 분리는 버킷의 `prevent_destroy`(3-5)가 대신한다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- `envs/prod/careerhub-backup` 루트 유지 · 모듈 추출만 — 워크스페이스가 환경마다 둘이고, stg 도 둘을 더해야 한다
- 이번 논의의 열린 축으로 둔다 — 사람이 답을 갖고 있었다

</details>

### 3-4. 입력 경계 — 루트가 읽고 모듈은 받는다

**선택: 모듈은 순수하다.** `envs/<env>/careerhub`가 `tfc_remote_state`로 `shared-iam`을 한 번 읽고, OIDC Provider ARN 과 issuer URL 을 모듈 입력으로 넘긴다. 모듈은 `tfe` provider 를 모른다 — `careerhub/auth`와 같은 모양이다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- 모듈이 `tfc_remote_state`를 직접 부른다 — 모듈이 `tfe` provider 와 워크스페이스 이름 `shared-iam`에 묶인다

</details>

### 3-5. 보호 — 버킷에 `prevent_destroy`

**선택: 모듈의 `aws_s3_bucket`에 `prevent_destroy = true`.** 변수로 켜고 끄는 것은 Terraform 이 허용하지 않는다(§2) — stg 버킷도 같은 보호를 받고, 지우려면 코드에서 그 줄을 빼는 PR 이 먼저다. 이름 변경(replace)도 같은 문으로 막힌다 — 4-1 의 비용에 들어간다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- 지금처럼 없이 — 워크스페이스를 합치면(3-3) 버킷이 `auth`의 파라미터와 같은 plan 을 지난다. 사람의 plan 확인만으로는 stateful 리소스의 destroy 를 막는 구조가 없다

</details>

### 3-6. 신뢰 SA — `cluster_name` 하나에서 둘을 파생

**선택: 모듈이 `<cluster>`와 `<cluster>-restore`를 만든다.** "복구 클러스터는 `-restore` 접미"가 모듈의 관례가 된다 — #49 가 정한 열거(와일드카드 거부)와 복구 SA 선등록(DR 이 인프라 리드타임에 묶이지 않게)을 그대로 잇는다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- SA 이름 목록을 입력으로 — 결과는 같되 호출자가 관례를 매번 적고, 버킷 이름에 클러스터를 쓰려면 같은 값을 두 입력에 든다
- `cluster_name` + 추가 SA 목록 — restore 를 잊고 부르면 신뢰가 하나만 남는다

</details>

### 3-7. 경로와 이름 · 범위 · goal

**선택: `_modules/cnpg-backup` → `module "cnpg_backup"`.** 평평한 한 차원, `nat`·`tfc_remote_state`와 같은 깊이다. 블록 이름에 무엇의 백업인지가 보인다. (인터뷰, 2026-11-04)

**범위 밖: MongoDB 백업 모듈, 백업 정책 자체(보존 3d · 스케줄 · SSE-S3).** 정책 값은 #49 의 것을 그대로 모듈 기본값으로 받는다. jyoliar-k8s overlay 의 리터럴 수정과 stg 의 백업 선언 복원은 범위 안이다 — 이 논의가 값을 정하고, 티켓이 target 둘(terraform · k8s)로 담는다. (인터뷰, 2026-11-04)

**goal: `platform-terraform-restructure` (topic homelab).** 모듈·합병·state 이행은 terraform 구조의 일이다. stg 백업 판정 번복은 careerhub stg 논의의 그 축 판정 줄을 고치는 것으로 반영한다. (인터뷰, 2026-11-04)

### 3-8. 버킷 설정 — 버저닝 없음

**선택: 새 버킷에 버저닝을 두지 않는다.** 백업 객체의 보존은 barman 의 retention 이 관리한다 — 버저닝은 비현행 버전과 그것을 걷는 라이프사이클 규칙을 더할 뿐이다. SSE-S3 · 공개 차단 · 미완 멀티파트 7d 규칙은 그대로다. (인터뷰, 2026-11-04)

<details><summary>버린 안</summary>

- 지금처럼 버저닝 Enabled + 비현행 30d 규칙 — 실수 삭제의 마지막 방어선이었으나, 복구 단위는 barman 카탈로그라 객체 버전으로는 되살리지 못한다

</details>

## 4. 열린 축 — 논의

### 4-1. 버킷·Role 의 이름 규칙

실측: 지금 규칙 `homelab-cnpg-backup-<env>`는 클러스터를 모르고, prod 이름은 k8s overlay 에 리터럴로 박혀 있다.
`bucket`·`name` 변경은 replace 이고, 모듈의 `prevent_destroy`(3-5)는 replace plan 을 거부한다 — prod 를 새 이름으로 옮기려면 "모듈이 새 버킷을 만들고, 옛 버킷은 모듈 밖에 남긴 뒤 따로 지운다"는 두 단계가 된다.
옛 버킷은 비어 있지 않으면 destroy 가 거부된다(`force_destroy` 기본 false) — 보존 3d 가 지난 뒤 사람이 비우거나 `force_destroy = true`를 한 번 거쳐야 한다.
돌고 있는 Cluster 의 `destinationPath` 교체 뒤 동작은 문서에 없어 실측이 필요하다 — 교체 직후 on-demand `Backup` 하나를 만들어 새 버킷에 base backup 을 세우는 것이 복구 가능 상태로 돌아오는 가장 짧은 길이다.
사람은 이름이 바뀌어도 된다고 했다 — 그래서 비용을 세어 고른다.

- **A. 지금 규칙 유지 — `homelab-cnpg-backup-<env>`** — 모듈이 `env`에서 파생한다. 이기는 조건: 환경마다 CNPG 클러스터가 하나뿐일 때(지금). prod 는 state mv 만으로 `No changes`이고 overlay 는 건드리지 않는다. 지는 조건: 같은 환경에 두 번째 CNPG 클러스터가 서면 이름이 충돌해 모듈을 부를 수 없다 — 그때 규칙을 바꾸면 그 시점의 데이터 이동을 떠안는다. `homelab` 접두는 이 저장소의 어느 다른 이름에도 없다.
- **B. 클러스터 좌표 — `cnpg-backup-<namespace>-<cluster>`** — 모듈이 `namespace`·`cluster_name`에서 파생하고, 무엇의 백업인지가 보이도록 `cnpg-backup`을 접두로 둔다. prod 는 버킷 `cnpg-backup-careerhub-prod-careerhub-postgresql-986069063944`(60자), Role `cnpg-backup-careerhub-prod-careerhub-postgresql`(47자). 버킷 63자 한계까지 3자 남는다 — 네임스페이스와 Cluster 이름의 합이 38자를 넘으면 이 규칙으로 못 짓는다. `env` 입력이 이름에 필요 없어진다 — 네임스페이스가 환경을 이미 든다. 이기는 조건: 모듈이 "CNPG 클러스터 하나"를 말한다는 3-2 와 이름이 일치하고, 어느 환경에 몇 개가 서도 겹치지 않는다. 지는 조건: prod 버킷·Role 재생성 — overlay 두 줄 수정, 새 base backup, 옛 버킷 3d 보존 뒤 삭제, 그 사이 PITR 은 옛 버킷에 기댄다. `careerhub`가 두 번 들어가 길다.
- **C. B 를 기본 규칙으로, 이름 override 입력** — 모듈은 B 로 파생하되 `bucket_name`·`role_name`(기본 null)을 받는다. prod 는 지금 이름을 넘겨 `No changes`, stg 부터 B 규칙으로 선다. 이기는 조건: 데이터 이동 없이 새 규칙을 세우고 싶을 때. 지는 조건: 환경마다 이름 규칙이 달라 "`env`에서 파생, 리터럴 금지"(README)의 예외가 prod 에 영구히 남고, override 입력은 한 호출자만 쓰는 구멍이다.
- D. 안 한다 — A 와 같다. 이름을 안 바꾸는 비용은 A 의 지는 조건이다.

**판정(사람, 2026-11-04): B — `cnpg-backup-<namespace>-<cluster>`. 클러스터 좌표에 `cnpg` 접두를 붙여 어떤 백업인지 이름에 보이게 한다.**

### 4-2. 이행 경로 — 모듈 주소와 워크스페이스를 한 번에 옮기나

실측: 옮길 것은 §2 의 여덟이고, data 들은 옮길 것이 없다.
워크스페이스 간 state 이동은 #157 이 밟은 길이다 — 양쪽 `state pull`, `cloud` 블록 없는 디렉터리에서 로컬 파일 `state mv -state -state-out`, 받는 쪽에 `state push`, 보내는 쪽 `state rm`, plan `No changes`.
`shared-iam`의 `remote_state_consumer_ids`가 `prod-careerhub`를 들기 전에는 `prod-careerhub`의 `tfe_outputs` 읽기가 거부된다 — `tfc/` apply 가 `prod-careerhub`의 첫 run 보다 먼저다.
`prod-careerhub`에 `tfe` provider 블록(`provider "tfe" {}`)과 `another_trigger_patterns`에 `_modules/cnpg-backup/**/*`·`_modules/tfc_remote_state/**/*`가 더해진다.
`prod-careerhub-backup` 삭제는 `tfc/`에서 `module "backup"` 선언 제거 → apply 다 — state 가 비어 있어야 `force_delete = false`가 통과한다.
4-1 이 B 면 이 축의 어느 안에도 "새 버킷 생성 → overlay 전환 → base backup → 옛 버킷 삭제"가 더해진다.
이름이 바뀌면 모듈이 만드는 것은 전부 새 리소스다 — 옮길 state 가 있는 것은 "옛 리소스를 보존하려는" 경우뿐이고, 옛 버킷의 백업(보존 3d)을 보존하지 않으면 state 이동 자체가 필요 없다.

- **A. 한 번에** — PR 하나로 `_modules/cnpg-backup` 신설 + `envs/prod/careerhub`에 호출 + `envs/prod/careerhub-backup` 삭제, `tfc/`는 소비자 변경·trigger 추가·`module "backup"` 제거. state 는 `prod-careerhub-backup` → `prod-careerhub`로 여덟을 `module.cnpg_backup.<type>.<name>`으로 한 번 옮긴다. 이기는 조건: 리소스 이름이 모듈 안에서도 같아(4-1 A·C) mv 만으로 끝날 때 — state 연산 한 회, 워크스페이스 run 한 회. 지는 조건: 4-1 B 와 겹치면 모듈 추출·워크스페이스 이동·버킷 교체 셋이 한 plan 에 섞여 읽기 어렵다.
- B. 두 단계 — 먼저 `envs/prod/careerhub-backup` 안에서 모듈을 추출한다(같은 워크스페이스 안 mv, `No changes`). 다음 PR 로 호출을 `envs/prod/careerhub`로 옮기고 워크스페이스를 합친다. 이기는 조건: 모듈이 맞는지 prod 에서 먼저 확인하고 싶을 때, 또는 4-1 B 의 버킷 교체를 첫 단계에 붙여 워크스페이스 이동과 분리할 때. 지는 조건: state 연산이 두 회, 머지·승인 두 회, 그 사이 `README`의 트리가 중간 상태를 한 번 더 적는다.
- C. stg 먼저 — 모듈을 만들고 `envs/stg/careerhub`가 첫 호출자가 된다. prod 는 뒤에 옮긴다. 이기는 조건: 4-1 B 의 `destinationPath` 교체 동작을 stg 에서 먼저 실측하고 싶을 때. 지는 조건: stg 환경 Feature 가 아직 발행 전이고 그 선행(프로젝트·variable set·`envs/stg/careerhub`)이 이 모듈보다 크다 — prod 가 그동안 옛 모양으로 남아 `README`가 둘을 설명한다.
- D. 안 한다 — 루트와 워크스페이스를 그대로 두고 stg 에서 `envs/stg/careerhub-backup`을 복사한다. 3-3 이 버렸다.
- **E. 신규 생성 · 옛 것 destroy — state 이동 없음** — `envs/prod/careerhub`가 바로 `module "cnpg_backup"`을 부르고 `prod-careerhub`가 새 버킷·Role 을 만든다. overlay 를 새 이름으로 바꾸고 on-demand `Backup` 으로 첫 base backup 을 세운 뒤, 사람이 콘솔에서 옛 버킷을 비우고 `prod-careerhub-backup`에 destroy run 을 건다. 마지막 PR 이 `tfc/`의 선언과 옛 디렉터리를 지운다. 이기는 조건: 옛 버킷의 백업(최근 3d 의 복구 지점)을 보존하지 않아도 될 때 — CLI state 연산이 없고 3d 대기도 없다. 지는 조건: 전환 시점 이전으로의 PITR 을 잃는다 — #79 컷오버의 롤백 창과 겹치면 안 된다.

**판정(사람, 2026-11-04): E — 기존 백업을 보존하지 않는다. 새 워크스페이스에서 신규 생성, overlay 전환·base backup, 콘솔에서 옛 버킷 비우기·destroy run, 선언·디렉터리 제거. (처음 B 였다가 같은 날 바꿨다 — state 이동은 옛 리소스 보존용이었고 보존할 이유가 없었다.)**

## 5. 반대편 — 이 설계가 틀리는 조건

- stg 백업이 다시 범위 밖이 되면 모듈의 두 번째 호출자가 사라진다 — 모듈은 간접화만 남긴다. 그때도 prod 는 모듈 호출 하나로 서 있으니 되돌릴 것은 없지만, 이 논의의 전제가 빈다.
- 워크스페이스 합병은 "stateful 은 다른 state 에"(stg 논의 4-4 E · README 의 `shared-iam` 분리 이유)와 반대 방향이다. `prevent_destroy`는 destroy·replace 만 막는다 — 블록 삭제는 막지 않으므로, `envs/prod/careerhub`에서 `module "cnpg_backup"` 블록을 지우는 PR 은 버킷을 지운다. 사람의 plan 확인이 마지막 문이다.
- 모듈이 "CNPG 클러스터 하나"를 말하지만 Policy 의 S3 액션 목록은 barman-cloud 가 요구하는 것이다. barman 이 아닌 백업 도구(예: 다른 plugin)로 바꾸면 모듈 이름은 맞고 내용은 틀린다.
- `-restore` 관례(3-6)는 복구 훈련이 그 이름을 쓸 때만 산다. 복구 클러스터를 다른 이름으로 세우면 신뢰되지 않고, 그제야 모듈을 고치는 PR 이 복구에 선행한다 — #49 가 피하려던 것이 다른 이름으로 돌아온다.
- 4-1 B · 4-2 E 를 고르면 prod 복구 가능성에 공백이 생긴다 — 새 버킷의 첫 base backup 전까지 새 버킷만으로는 복구가 안 되고, 옛 버킷을 지우면 그 이전 시점으로의 PITR 이 사라진다. #79(컷오버)의 롤백 수단이 백업 복원이므로, 컷오버 창과 겹치면 안 된다.

## 6. 버린 것

- 모듈 없이 디렉터리 복사 — 환경마다 여덟 리소스와 워크스페이스 하나가 늘고, 보존·암호화 수정이 환경 수만큼 PR 이 된다.
- 모듈을 `_modules/careerhub/` 아래에 두는 것 — 백업은 careerhub 의 것이 아니라 CNPG 클러스터의 것이다. `auth`와 나란히 두면 "careerhub 환경 하나 = 모듈 둘"로 읽기는 좋으나 다른 서비스의 PG 가 서면 부를 자리가 없다.
- 백업 정책(보존·스케줄·SSE)을 이 논의에서 다시 여는 것 — #49 가 실측으로 정했고, 바뀐 사실이 없다.
- `prevent_destroy`를 모듈 변수로 — Terraform 이 허용하지 않는다(§2). 두 리소스 블록을 `count`로 가르는 우회는 state 주소가 갈려 mv 가 하나 더 생기고, 읽는 사람이 둘 중 어느 것이 실체인지 세어야 한다.

## 7. 임계선 — ADR감인가

ADR 이 아니다.
모듈 추출은 state mv 로 되돌리고, 워크스페이스 합병도 state mv 로 되돌린다 — 한 시간 안이다.
4-1 B 의 버킷 재생성은 데이터 이동이 따르지만 되돌리기 어려움이 아니라 비용이고, 영향은 한 클러스터의 백업 경로다.
모듈 입력(네임스페이스 · Cluster 이름)이 클러스터 측 이름이라는 점은 ADR-0034(proposed)의 경계와 같은 모양이다 — 이미 README "다른 저장소와의 경계" 표가 합의 값으로 적고 있는 종류라 새 결정이 아니다.

## 8. 다음

- careerhub stg 논의(`261102_1903_renewal-stg-environment-namespace-data-env-axis.md`) 4-1 판정 줄을 고친다 — "백업 선언은 overlay 에서 삭제한다"를 "stg 도 백업을 갖는다 — 버킷·Role 은 `_modules/cnpg-backup` 이 만든다"로. §1 범위와 §2 의 "backup 은 필요 없다" 사실 줄도 그 자리에서 고친다.
- digest 두 건 수정 — `homelab/261104_1558_platform-terraform-env-axis-and-projects.md`(트리 · 워크스페이스 표 · remote state 소비자 · 이행)와 `careerhub/261104_1558_careerhub-stg-environment.md`(§1 terraform 에서 받는 것 · §3 DB · 하지 않는 것).
- 티켓 — #152(Feature, In Progress)의 본문은 "stateful 인 백업 버킷은 `envs/prod/careerhub-backup`으로 따로 둔다"고 적고 있다. 합병은 그 문장을 뒤집으므로 Feature 본문을 고치고 그 아래 Task 하나로 낸다 — PR 셋(terraform 신규 생성 · k8s overlay 전환 · terraform 옛 것 제거)과 콘솔 작업 둘(옛 버킷 비우기 · destroy run). target 은 `jyoliar-platform-terraform`과 `jyoliar-k8s` 둘이다.
- stg 의 백업 — `envs/stg/careerhub`가 `module "cnpg_backup"`을 함께 부르고, stg overlay 가 ObjectStore·ScheduledBackup 을 지우지 않는다. stg 환경 Feature 의 것이다.
- README · CLAUDE.md — 트리 · 워크스페이스 표 · "공유 → 환경" 소비자 · 새 환경 추가 절(모듈 둘). #159 와 같은 방식으로 현 상태만.
