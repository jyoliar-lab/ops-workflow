---
type: digest
goal: careerhub-env-separation
topic: careerhub
subjects: [careerhub-stg, careerhub-prod, jyoliar-k8s, argocd, zitadel, mongodb, cloudnativepg, external-secrets, jyoliar-platform-terraform]
status: current
ref-adrs: [ADR-0034]
sources:
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
  - docs/careerhub/discussion/261102_1903_stg-env-external-dependencies-survey.md
superseded_by:
---

# careerhub stg 환경 — 네임스페이스 · 데이터 · 환경 축 (2026-11-04 시점)

## 개요

careerhub는 지금 `careerhub-prod` 하나로 공개 서비스를 하고 있고, 그 옆에 상시 pre-prod 환경 `stg`를 세운다.
stg는 prod와 같은 토폴로지로 서서 리뉴얼 스택(careerhub-web·Zitadel·신 세대 composer와 auth-service)이 prod에 가기 전에 먼저 서는 자리이자, DB·오퍼레이터 업그레이드와 이미지 태그 인상을 prod보다 먼저 보는 자리다.
환경이 둘이 되면 환경마다 따로 서는 자격증명(Zitadel masterkey·Google OAuth 클라이언트)이 필요하다.
그것은 terraform 저장소 `jyoliar-platform-terraform`이 환경 축을 갖게 된 뒤, 환경 루트 하나를 더해 만든다.
이 문서는 stg 환경이 클러스터와 terraform 양쪽에서 어떻게 서는지를 서술한다.
관통하는 사례는 **stg Zitadel의 masterkey 한 개**다 — 그것이 어디서 선언되고, 어떤 워크스페이스가 만들고, 어떻게 클러스터에 닿는가.

## 어휘

- **env** — 환경 이름. `prod`·`stg`. 네임스페이스(`careerhub-<env>`)·SSM 경로(`/jyo-liar/k8s/baremetal/careerhub/<env>/…`)·DNS(`<env>-careerhub.jyo-liar.com`)·terraform 디렉터리(`envs/<env>/`)·HCP Terraform 프로젝트(`<env>-careerhub`)에 같은 글자로 들어간다.
- **환경 루트** — terraform 저장소에서 한 환경의 리소스만 가진 얇은 루트. `envs/<env>/careerhub`. 모듈 `_modules/careerhub/auth`를 불러 그 환경의 masterkey와 Google 클라이언트 파라미터를 만든다.
- **프로젝트** — HCP Terraform에서 환경 루트의 워크스페이스가 사는 폴더. 프로젝트가 소유한 variable set이 `env`·`region`을 주므로 워크스페이스에는 그 변수가 없다.

## 1. terraform에서 받는 것

stg의 terraform 쪽은 환경 루트 하나를 더하는 일이다.
`envs/stg/careerhub`가 `module "auth"`로 `_modules/careerhub/auth`를 부르고, `tfc/`에 프로젝트 `stg-careerhub`·그것이 소유한 variable set `stg`(`env = stg`·`region = ap-northeast-2`)·워크스페이스 `stg-careerhub`(working directory `envs/stg/careerhub`, trigger에 모듈 경로)를 선언한다.
모듈은 prod와 같은 것이고 `env` 값만 프로젝트에서 달리 들어온다.

```hcl
module "auth" {
  source               = "../../../_modules/careerhub/auth"
  env                  = var.env
  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
}
```

이 루트가 만드는 것은 셋이다 — `random_password` 하나와 SSM 파라미터 둘.
`/jyo-liar/k8s/baremetal/careerhub/stg/zitadel/masterkey`(32자, SecureString)와 `/jyo-liar/k8s/baremetal/careerhub/stg/oauth/google-client`(ID·secret의 JSON).
둘 다 `prevent_destroy`이고 `env = stg`·`managed_by = terraform` 태그가 붙는다.
prod의 것은 `/…/careerhub/prod/…`에 있고, 두 Zitadel은 서로의 값을 모른다.

Google 클라이언트 ID·secret은 sensitive라 콘솔에서 `stg-careerhub` 워크스페이스 변수로 넣는다.
`env`·`region`은 넣지 않는다 — 프로젝트 `stg-careerhub`의 variable set이 이미 준다.

## 2. 사례 — stg masterkey 한 개의 여정

사람이 Google 콘솔에서 stg용 OAuth 클라이언트를 만든다.
redirect URI는 `https://id.stg-careerhub.jyo-liar.com/…`이다.
그 ID와 secret을 `stg-careerhub` 워크스페이스의 sensitive 변수로 넣는다.

`envs/stg/careerhub/main.tf`를 담은 PR이 `main`에 머지된다.
`stg-careerhub`가 plan을 만든다 — `random_password` 하나, SSM 파라미터 둘.
사람이 apply를 승인하면 두 파라미터가 생긴다.
AWS 콘솔에서 파라미터만 봐도 `env = stg` 태그로 stg의 것이고 terraform이 만든 것임이 읽힌다.
terraform의 일은 여기서 끝난다 — 클러스터 안에서 그 값이 어떻게 쓰이는지 terraform은 모른다.

클러스터에서는 `careerhub-stg` 네임스페이스의 ExternalSecret이 `ClusterSecretStore/aws-parameter-store`를 통해 그 경로를 읽는다.
읽기 권한은 공유 루트 `shared/iam`의 external-secrets Role이 `/jyo-liar/k8s/*` 전체에 주고 있어 환경이 늘어도 바뀌지 않는다.
Secret `zitadel-masterkey`가 만들어지고, stg Zitadel pod가 그것으로 자기 DB를 암호화한다.
같은 네임스페이스의 Secret `google-oauth`는 Zitadel 구성 Job이 읽어 Google IdP를 등록한다.

## 3. stg 환경

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
`ExternalDomain`은 `id.stg-careerhub.jyo-liar.com`, masterkey와 Google IdP 클라이언트는 1절의 두 파라미터다.
구성 Job이 stg용 선언(IdP·project·careerhub-web 앱·redirect URI `https://stg-careerhub.jyo-liar.com/…`)을 빈 인스턴스에 수렴시킨다.

**접근.** 공개 노출은 없다.
`careerhub-stg`에 kube-vip LoadBalancer Gateway가 서고, 인증서는 `stg-careerhub.jyo-liar.com`과 `*.stg-careerhub.jyo-liar.com` 두 SAN이다.
external-dns가 HTTPRoute에서 레코드를 만들어 공개 DNS에 사설 IP를 싣고, 사람은 Tailscale VPN으로 들어간다.
cloudflared 터널 ingress는 바뀌지 않는다.

## 4. 그 뒤

terraform 저장소의 구조 개선이 먼저 끝나고, 그 위에 1절의 환경 루트가 선다.
stg가 서면 리뉴얼의 검증 자리가 stg가 되고, prod 컷오버의 그림은 그 전제로 다시 그린다.
필요할 때 띄우고 끝나면 지우는 임시 환경은 이 설계에 없다.

## 이 설계가 하지 않는 것

- CI가 stg에 자동 배포하지 않는다 — 태그 인상은 사람의 PR이다.
- 관측·알림은 환경별로 갈라지지 않는다.
- NetworkPolicy가 없다 — stg pod는 prod DB에 네트워크로 닿는다.
- stg DB 백업이 없다.
- terraform 저장소의 공유 루트·프로젝트·이행 순서는 이 설계가 정하지 않는다.
