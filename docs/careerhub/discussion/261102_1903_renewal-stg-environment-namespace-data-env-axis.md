---
type: discussion
kind: deliberation
goal: careerhub-env-separation
topic: careerhub
subjects: [careerhub-stg, careerhub-dev, careerhub-prod, jyoliar-k8s, jyoliar-platform-terraform, argocd, mongodb, cloudnativepg, zitadel, external-secrets, careerhub-web]
status: done
ref-adrs: [ADR-0034]
related:
  - docs/careerhub/discussion/260810_1801_path-to-host-based-routing.md
  - docs/careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md
  - docs/careerhub/discussion/261102_1903_stg-env-external-dependencies-survey.md
  - docs/homelab/discussion/261102_2007_terraform-env-vs-shared-resource-separation-survey.md
  - docs/homelab/discussion/261103_1429_terraform-restructure-migration-plan.md
  - docs/homelab/discussion/261104_1636_cnpg-backup-module-and-workspace-merge.md
---

# 리뉴얼을 위한 careerhub stg 환경 — 네임스페이스·데이터·환경 축

## 1. 문제

레거시 커리어허브가 `careerhub-prod`에서 공개됐다(#133, 2026-10-30).
그 전까지 prod는 내부망 전용이었고 변경이 곧 검증이었으므로 다른 환경이 필요하지 않았다.
공개 뒤 변경이 운영을 건드리는 장면은 셋이다 — gitops 이미지 태그를 올리면 그 즉시 공개 사용자에게 노출되고, CNPG·PostgreSQL·pgbouncer·Zitadel 인상을 리허설할 자리가 없고, 수집 로직을 바꾸면 CronJob이 prod 데이터에 바로 쓴다.
그러나 사람이 짚은 비용은 하나다 — **리뉴얼 커리어허브(careerhub-web·Zitadel·신 세대 composer·auth-service)를 배포해 동작을 검증할 환경 자체가 없다.**

이 논의는 `260810_2252`가 "리뉴얼 이후의 별도 논의"로 보류하며 **"진짜 dev 환경"(격리 데이터 플레인)** 이라 부른 것을 여는 것이다.
이름은 `stg`로 정했다(§3-1) — 세우는 것은 상시 pre-prod이고, dev라는 이름은 수명주기를 거짓말한다.
보류의 근거였던 "환경 구조의 공수가 크고 리뉴얼 방향 확립이 선행해야 한다"는, 리뉴얼 방향이 섰으므로 소멸했다.

끝났을 때 손에 있어야 하는 것은 다음이다.
같은 홈랩 클러스터의 별도 네임스페이스에 리뉴얼 스택이 Argo CD로 서 있다.
posting·review 수집 데이터가 prod에서 한 번 복사돼 있고, 사용자 데이터(userinfo·auth·Zitadel 원장)는 비어 있다.
수집 CronJob은 멈춰 있되 사람이 수동으로 돌릴 수 있다.
Zitadel이 환경 전용 인스턴스로 포함된다.
접근은 VPN 내부에서만 하고 공개 노출은 없다.
terraform의 환경 축이 코드로 정리돼, 새 환경이 쓰는 SSM 파라미터가 그 구조에서 나온다.

인터뷰 전에 열려 있던 것은 환경의 이름(dev/staging)·DB replica 수·terraform 구조였다.
이름은 인터뷰에서 닫혔고(§3-1), 나머지 둘은 열린 축으로 남았다(§4-1·§4-4).

이번에 다루지 않는 것 — CI의 stg 자동 배포, 관측·알림의 환경 분리, NetworkPolicy 격리, stg MongoDB 백업, 리뉴얼 컷오버 절차의 재편.
마지막 것은 이 논의가 전제를 바꾸므로 §8에서 별도 논의로 가리킨다.

## 2. 실측

**gitops의 환경 축 — 둘이 겹쳐 있다.**

- `jyoliar-k8s`의 `overlays/{env}`는 클러스터 단위다(`baremetal` 하나). 서비스 환경은 그 아래 `gitops/overlays/baremetal/services/careerhub/{prod,dev}`로 갈린다 — README가 "careerhub prod · dev"를 명시한다.
- dev 뼈대는 이미 있다. `services/careerhub/dev/careerhub-dev-appset.yaml`은 `careerhub-dev-mongodb`만 살리고 `careerhub-dev-apps`는 주석이다(커밋 e05b0c8 "잘못된 경로 참조로 sync 오류"). `dev/apps/` 디렉터리는 없다. AppProject `careerhub-dev`는 destination을 `careerhub-dev` 네임스페이스로 제한한다.
- dev Mongo overlay는 1멤버·arbiter 0·5Gi/1Gi·podAntiAffinity 해제다(`dev/mongodb/mongodb-patch.yaml`).
- PriorityClass `database-dev`(500)·`database-prod`(1000)가 `base/system/prerequisites`에 이미 있다 — dev DB를 예견한 자리다.

**클러스터 actual (2026-11-02, kubectl).**

- `careerhub-dev` 네임스페이스: `careerhub-mongodb-0` 1멤버가 93일 가동 중, 데이터 볼륨 actual 2.67Gi, ExternalSecret 8건(admin·readonly·{posting,review,userinfo}×{app,migrator}) 동기화됨.
- `careerhub-prod` 토폴로지: PG 2인스턴스(10Gi + WAL 2Gi) + pooler 1, Mongo 2멤버 + arbiter 1(30Gi + 3Gi), api-composer·auth-service·gRPC 3종 각 2 replica, frontend 1, zitadel 1 + zitadel-login 1, Gateway 2(LAN·공개).
- 실 데이터는 작다 — Mongo 4.3~4.5Gi/멤버, PG 0.44Gi + WAL 1.4~1.7Gi. 선언 스토리지는 Mongo 99Gi·PG 24Gi다.
- 리소스 요청: careerhub-prod 합계 CPU 3.3·메모리 약 3.0Gi. 거의 전부 DB다 — Mongo 3 pod 각 CPU 1·763Mi, Zitadel 0.25·512Mi + login 0.05·256Mi. 앱 pod는 요청이 0이다.
- 노드 8대(Raspberry Pi, 4 CPU, 8~16Gi). CPU 요청률은 w0가 76%, 나머지 20~41%. 메모리 요청률은 전부 20% 이하.
- Longhorn 스토리지 노드는 s0·s1 둘뿐이다(각 468Gi, 가용 약 350Gi). 복제 2라 모든 볼륨이 두 노드에 한 복제씩 놓인다 — 볼륨을 더해도 분산되지 않고 두 노드에 쌓인다.

**DB 선언과 환경 의존.**

- PG base kustomization은 `objectstore.yaml`·`scheduledbackup.yaml`을 포함하고 `cluster.yaml`은 barman plugin과 IRSA projected token을 선언한다 — **백업 없는 환경은 overlay에서 이를 걷어내야 한다.**
- Mongo base는 사용자 8명을 선언하고 `mongodb-readonly`는 `readAnyDatabase`다 — prod 읽기 복사의 자격증명이 이미 있다.
- 앱의 DB 접속은 네임스페이스 안 Service 이름이다 — gRPC 3종 `MONGO_URI`(Secret), auth-service `DB_HOST=careerhub-postgresql-pooler`, Zitadel은 `careerhub-postgresql-rw` 직결. 네임스페이스를 복제하면 그대로 동작한다.
- 수집 CronJob 4개(`base/services/careerhub/apps/jobs/cronjob.yaml`): posting-provider-wanted·jumpit 19:09 UTC, skillscanner·review-crawler 19:39 UTC, `concurrencyPolicy: Forbid`, `suspend` 미선언. `ai-agents/careerhub-incident-agent/cronjob.yaml`이 `suspend: true` + 수동 실행 선례다.

**접근 경로.**

- prod LAN Gateway `careerhub-nginx-gateway`는 kube-vip LoadBalancer(10.18.100.3)다. 인증서 `wildcard-careerhub-tls`는 SAN 둘(`careerhub.jyo-liar.com` + `*.careerhub.jyo-liar.com`) — 와일드카드가 apex를 덮지 않아서다.
- external-dns는 `gateway-httproute` 소스로 Cloudflare에 레코드를 만들고, LAN Gateway 뒤 호스트는 **공개 DNS에 사설 IP**로 실린다 — `id.careerhub.jyo-liar.com → 10.18.100.3`, `argocd.mg.jyo-liar.com → 10.18.100.2`(dig). VPN은 Tailscale subnet router(`onpremise-k8s/vpn`)다.
- kube-vip 풀은 `10.18.100.2-254`, 사용 중 3개.
- 공개 경로는 cloudflared 터널 ingress 두 줄(k8s-oidc·careerhub)이다 — 새 환경은 여기를 건드리지 않는다.
- 호스트명의 모양은 `260810_1801`이 판정했다 — 환경은 제품 하위가 아니라 형제 네임스페이스(`*.<env>-careerhub.jyo-liar.com`)다. 근거는 쿠키 서픽스 상속과 Gateway API 와일드카드의 다중 레이블 매칭이다. 그때의 예시 이름은 `dev`였다.

**Zitadel과 자격증명.**

- masterkey는 SSM `/jyo-liar/k8s/baremetal/careerhub/prod/zitadel/masterkey`(terraform `zitadel/masterkey.tf`, `prevent_destroy`)에서 ExternalSecret으로 온다. `ExternalDomain`은 `id.careerhub.jyo-liar.com`.
- 구성 Job은 IdP Google 클라이언트를 `google-oauth` Secret에서 읽고, 그 Secret은 `/jyo-liar/k8s/baremetal/careerhub/prod/oauth/google-client`(terraform `oauth/google.tf`)의 ExternalSecret이다 — **레거시 auth-service와 Zitadel이 같은 Google 클라이언트를 공유한다.**
- Google 클라이언트 자체는 terraform 밖이다 — `var.google_client_id/secret`로 주입된 값을 SSM에 심을 뿐이다. 코드로 만들 수 없음은 조사 문서 §1이 확인했다.

**terraform의 환경 축.**

- `env`는 TFC 워크스페이스 변수다. 이름 파생에 쓰는 곳은 `backup`(`homelab-cnpg-backup-${env}`, `cnpg_sa_namespace = careerhub-${env}`)·`vpc`·`vpn`이다.
- `prod`가 리터럴인 곳은 셋 — `oauth/google.tf`·`zitadel/masterkey.tf`(`careerhub/prod/…`)·`oauth/admin.tf`(`admin/prod/…`). 마지막 것은 이름만 prod이고 실체는 클러스터 서비스(argocd 등)의 OAuth라 클러스터 스코프다.
- env와 무관한 클러스터 스코프: `iam`(external-secrets Role, `ecr-image-puller`의 sub 조건이 `system:serviceaccount:*:ecr-image-puller`라 어느 네임스페이스든 통과), `ci`(ECR은 환경 공용), `cloudflare`, `alert`.
- 따라서 **새 환경이 요구하는 환경별 terraform 산출물은 셋이다** — Zitadel masterkey 파라미터, Google 브로커를 쓰면 `oauth/google-client` 파라미터, 그리고 CNPG 백업 버킷·Role(처음 범위 밖이었다가 2026-11-04 되돌렸다 — `homelab/261104_1636`).
- ADR-0034(proposed)는 terraform이 클러스터 안을 모른다고 규정한다 — stg Zitadel의 내부 구성은 GitOps 구성 Job이고 terraform은 SSM seed까지다.

**리뉴얼 쪽 현황.**

- careerhub-web은 배포 매니페스트가 0건이다(#78 Draft, 호스트 apex 승계 판정 260824). stg에 web을 올리려면 #78이 만들 base 매니페스트가 선행한다.
- #79에 따르면 식별자 백필은 이미 실행됐고 레거시 로그인은 사실상 죽어 있다. prod는 회원가입·로그인을 제공하지 않는다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 환경의 이름

**선택: `stg`(staging의 줄임) — 상시 가동하는 pre-prod 하나.** prod와 같은 토폴로지로 서고, 리뉴얼이 prod에 가기 전에 먼저 서는 자리이자 업그레이드·태그 인상의 예행 자리다. 리뉴얼 검증이 여기서 일어나는 것은 모순이 아니다 — 리뉴얼은 다음 prod다. 리소스 이름·DNS·SSM 경로·TFC `env` 값 전부에 `stg` 키워드를 쓴다(네임스페이스 `careerhub-stg`, 경로 `/…/careerhub/stg/…`). (인터뷰, 2026-11-02. 처음 `dev`로 닫혔다가 바꿨다 — 질문의 선택지가 "dev 샌드박스 / staging 게이트"로 갈려 있어 상시 pre-prod 하나라는 그림이 들어갈 자리가 없었다.)

<details><summary>버린 안</summary>

- `dev` — 상시 개발 환경을 뜻하는 이름인데, 세우는 것은 prod 동형의 pre-prod다. 이름이 수명주기를 거짓말하고, prod 동일 replica라는 전제와도 어긋난다
- `staging` 전체 표기 — 리소스·DNS 이름이 길어진다. 줄임말로 통일한다
- dev와 staging 둘로 나눠 세운다 — 리소스가 prod의 세 벌이고, 샌드박스 역할은 상시 환경이 아니라 임시 환경의 것이다(§8)

</details>

### 3-2. 레거시 구성요소의 포함

**선택: 올리지 않는다.** careerhub-front·Google OAuth 직접 처리 세대의 auth-service·그 Google 클라이언트 배선은 컷오버 때 소멸할 것이라 stg 자리가 없다. stg의 앱은 careerhub-web·Zitadel·api-composer·auth-service(신 세대)·gRPC 3종·수집 jobs·Mongo·PG다. (인터뷰, 2026-11-02)

<details><summary>버린 안</summary>

- 레거시도 올린다 — 컷오버 전 태그 인상 예행이 가능해지지만, 소멸할 것에 Google 클라이언트 한 벌을 더 들인다
- auth-service만 — 겸직 서버의 레거시 표면은 신 세대 이미지에서 이미 철거됐다(#79)

</details>

### 3-3. 호스트명

**선택: `260810_1801`의 형제 네임스페이스 모양을 승계하고 환경 키워드만 `stg`다 — web은 `stg-careerhub.jyo-liar.com`, Zitadel은 `id.stg-careerhub.jyo-liar.com`, 인증서 SAN은 apex + `*.stg-careerhub.jyo-liar.com` 둘.** prod와 동형이다. (인터뷰, 2026-11-02)

<details><summary>버린 안</summary>

- `*.stg.careerhub.jyo-liar.com`(제품 하위 중첩) — 쿠키 상속·와일드카드 매칭으로 기각된 바 있다(`260810_1801`)
- `*.dev-careerhub.jyo-liar.com` — `260810_1801`의 예시 이름. 3-1에서 이름이 바뀌었다

</details>

### 3-4. 접근 경로

**선택: prod의 LAN Gateway와 동형 — careerhub-stg에 kube-vip LoadBalancer Gateway를 두고, external-dns가 사설 IP를 공개 DNS에 싣고, Tailscale VPN으로 들어간다.** 공개 Gateway·터널 ingress는 만들지 않는다. (인터뷰, 2026-11-02)

<details><summary>버린 안</summary>

- 터널 공개 + Cloudflare Access — 공개 노출 없음이 요구다
- `/etc/hosts`·포트포워드 — Zitadel redirect URI와 인증서가 실제 호스트명을 요구한다

</details>

### 3-5. 수집 CronJob

**선택: stg overlay에서 `suspend: true` 패치. 수동 실행은 `kubectl create job --from=cronjob/<name>`.** incident-agent가 같은 모양이다. (인터뷰, 2026-11-02)

<details><summary>버린 안</summary>

- CronJob을 빼고 Job 템플릿만 — base 공유를 깨고, 수동 실행 명령이 환경마다 달라진다
- 스케줄을 먼 날짜로 — suspend가 있는데 우회할 이유가 없다

</details>

### 3-6. 데이터 복사 주기

**선택: 처음 한 번.** 그 뒤 stg 데이터는 수동 수집으로 쌓이고, prod와 갈라지는 것을 받아들인다. (인터뷰, 2026-11-02)

<details><summary>버린 안</summary>

- 필요할 때 재실행 — 복사 절차를 재실행 가능하게 만들어 두면 공짜로 얻어지는 선택지라, 4-2의 옵션에서 재실행 가능성을 따진다
- 정기 자동 — prod 읽기 부하가 정기적으로 생기고, 샌드박스에는 과하다

</details>

### 3-7. 기존 careerhub-dev MongoDB

**선택: 지우고 새로 세운다.** 1멤버 93일, 내용 미상. `careerhub-dev` 네임스페이스와 그 ApplicationSet·AppProject 뼈대는 stg로 이름을 바꿔 쓰거나 지운다 — 티켓 수준의 일이다. (인터뷰, 2026-11-02)

### 3-8. Zitadel의 포함

**선택: 포함 — 환경 전용 인스턴스.** 원장은 사용자 데이터라 복사하지 않고, 빈 인스턴스에 구성 Job이 stg용 선언(IdP·project·redirect URI)을 수렴시킨다. (인터뷰, 2026-11-02)

### 3-9. 사용자 데이터

**선택: userinfo DB·auth DB·Zitadel 원장은 복사하지 않는다.** 제약으로 받았다. (인터뷰, 2026-11-02)

## 4. 열린 축 — 논의

### 4-1. stg DB 토폴로지 — replica·스토리지·백업 처분

실측: prod는 PG 2 + pooler 1, Mongo 2 + arbiter 1이고, 요청의 거의 전부가 DB다(Mongo 3 pod = CPU 3·2.2Gi).
Longhorn은 s0·s1 두 노드에만 있어 볼륨은 늘려도 분산되지 않는다.
PG base는 백업을 전제하고, stg도 그것을 그대로 쓴다(처음 범위 밖이었다가 2026-11-04 되돌렸다).
사람의 전제는 "replica prod와 동일"이고, 3-1(상시 pre-prod)과 정합이다 — 업그레이드 리허설을 떠안는 환경이 이것 하나다.

- **A. prod 동일** — PG 2 + pooler 1, Mongo 2 + arbiter 1, 선언 스토리지 그대로(Mongo 30Gi·PG 10Gi). 이기는 조건: 스위치오버·롤링 업그레이드·pgbouncer 변경을 prod 전에 볼 자리가 이것뿐일 때 — 지금이다. 지는 조건: CPU 요청 +3(w0가 이미 76%라 배치가 s0·s1·w1·w2로 밀린다)과 스토리지 선언 +123Gi(복제 2라 두 노드에 +246Gi, 가용 각 350Gi)를 상시로 든다. 실 데이터는 5Gi 안이라 선언만 큰 것이다.
- B. 최소 — PG 1 + pooler 1, Mongo 1멤버·arbiter 0, 선언 5~10Gi, 요청 축소. 이기는 조건: 리허설을 다른 환경이 맡을 때 — 지금은 없다. 지는 조건: 스위치오버·롤링을 보지 못해 취약점 논의(`homelab/261029_1413`) 4·10번의 "dev 없음"이 그대로 남는다.
- **C. prod 토폴로지·작은 선언** — 인스턴스 수와 요청은 prod와 같되 선언 스토리지만 줄인다(Mongo 10Gi·PG 5Gi 수준). 이기는 조건: 스토리지 노드 둘에 +246Gi를 선언으로 묶어 두기 싫을 때. 실 데이터 5Gi 안이라 당장은 맞는다. 지는 조건: prod가 자라 stg 선언을 넘으면 stg에서 먼저 터진다 — 그때 늘리면 된다(Longhorn은 온라인 확장이 된다).
- D. 안 한다 — stg가 prod DB를 공유한다. 격리의 반대이고 `260810_2252`가 거부한 것이다.

하위 선택 — PG 백업 선언의 처분: stg overlay는 ObjectStore·ScheduledBackup을 그대로 두고 `destinationPath`·`AWS_ROLE_ARN`만 stg 버킷·Role로 바꾼다 — 버킷·Role은 `_modules/cnpg-backup`(`homelab/261104_1636`)이 `envs/stg/careerhub`에서 만든다. PriorityClass는 `database-prod`보다 낮은 값을 하나 더 두거나 기존 `database-dev`(500)를 쓴다 — 이름을 바꾸는 것은 티켓의 것이다.

**판정(사람, 2026-11-02): C — prod 토폴로지(PG 2 + pooler 1 · Mongo 2 + arbiter 1)에 선언 스토리지만 줄인다. PG 백업은 prod와 같게 둔다 — stg 버킷·Role은 `_modules/cnpg-backup`이 만든다(처음 "overlay에서 삭제"였다가 2026-11-04 되돌렸다, `homelab/261104_1636`).**

pooler: 신 세대 auth-service도 `DB_HOST=careerhub-postgresql-pooler`를 보므로 어느 안에서도 1개는 남긴다. 매니페스트 분기를 피하는 값이 pooler 하나보다 크다.

### 4-2. 수집 데이터(posting·review)의 복사 방법

실측: 복사 대상은 Mongo의 posting·review DB이고 userinfo는 제외다.
prod에 `mongodb-readonly`(readAnyDatabase)가 있고, NetworkPolicy가 없어 stg pod가 `careerhub-mongodb-svc.careerhub-prod`에 닿는다.
실 데이터는 멤버당 4.5Gi 이하다.
도구 이미지는 조사 문서 §4 — 운영 이미지에 mongodump가 있을 가능성이 높고 미확인이다.

- **A. mongodump → mongorestore Job** — stg 네임스페이스의 1회성 Job이 prod readonly로 두 DB를 덤프하고 stg admin으로 복원한다. 자격증명은 prod readonly Secret의 사본(1회 수동 — ExternalSecret 생성형은 환경마다 값이 달라 참조로 공유되지 않는다). 이기는 조건: 데이터 ≤5Gi·1회(3-6). 재실행 가능해 3-6의 "필요할 때 다시"도 공짜로 얻고, stg가 깨졌을 때 게이트로 되돌리는 수단이 된다(§5). 지는 조건: 도구 이미지가 없으면 별도 이미지가 하나 늘어난다.
- B. Longhorn 볼륨 클론·백업 복원으로 PVC 복제 — 전체가 복제돼 userinfo까지 따라오고, replica set의 `local` DB가 prod 멤버 호스트명을 들고 있어 rs 재구성이 필요하다. 지는 조건: 거의 항상. 이기는 조건: 수십 Gi로 커져 논리 복사가 느릴 때 — 지금은 아니다.
- C. 안 한다 — 복사 대신 stg에서 수집 Job을 수동 1회 돌려 채운다. 외부 사이트를 다시 크롤하고, 리뷰 수집 범위·시간이 미지이며, prod와 데이터가 다르다. 이기는 조건: A가 막혔을 때의 fallback.

mongosync는 Community 지원이 불확실하고 1회 복사에 과하다 — 옵션에 올리지 않는다.

**판정(사람, 2026-11-02): A — mongodump → mongorestore Job. 재실행 가능하게 만든다.**

### 4-3. stg Zitadel의 로그인 수단

실측·조사: prod Zitadel의 Google IdP는 레거시 auth-service와 같은 Google 클라이언트를 쓴다(§2).
Google 클라이언트는 어떤 길로도 코드가 되지 않는다 — 환경별 클라이언트는 환경마다 콘솔 수동 1회다(조사 §1).
한 클라이언트에 redirect URI를 여럿 둘 수 있지만 Google의 권고는 환경별 클라이언트다(조사 §2).
Zitadel 로컬 로그인은 정책 스위치가 있고 기본 상태는 실측이다(조사 §3).

- **A. 환경별 Google 클라이언트** — 콘솔에서 stg용 클라이언트를 만들고(redirect URI `https://id.stg-careerhub.jyo-liar.com/…`), SSM `/…/careerhub/stg/oauth/google-client`에 심는다(4-4의 모양을 따른다). 이기는 조건: 환경 경계 = 자격증명 경계 원칙. prod 직전 자리에서 prod와 같은 소셜 로그인 경로를 본다. 지는 조건: 환경이 늘 때마다 콘솔 수동 1회가 반복된다 — 자동화 불가가 확인됐으니 받아들이는 비용이다.
- B. prod 클라이언트 공유 — prod 클라이언트에 stg redirect URI를 추가하고 같은 SSM 파라미터를 읽는다. 수동 단계가 없다. 지는 조건: client secret이 환경 경계를 넘어 stg 침해가 prod 로그인 위장으로 이어진다. 4-4에서 환경별 경로를 만들어 놓고 값은 같은 것을 두 번 심는 모순이 생긴다.
- C. Zitadel 로컬 계정만 — stg에 Google IdP를 선언하지 않고 username/password로 들어간다. 외부 의존 0. 지는 조건: 소셜 로그인 경로(브로커 콜백·자동 연결·클레임 주입)가 prod 직전까지 미검증으로 남는다 — pre-prod라는 역할과 어긋난다.
- D. 안 한다 — Zitadel 없이. 3-8과 충돌한다.

**판정(사람, 2026-11-02): A — stg 전용 Google 클라이언트(콘솔 수동 1회), SSM `/…/careerhub/stg/oauth/google-client`.**

### 4-4. terraform의 환경 축 구조

실측: stg가 요구하는 환경별 산출물은 Zitadel masterkey 파라미터와(4-3 A를 고르면) Google 클라이언트 파라미터 둘이다.
`backup`은 이미 `env` 파생이고 저장소 CLAUDE.md는 "env는 이름의 재료, 같은 워크스페이스가 다른 환경으로 한 벌 더 설 수 있게"라고 선언한다.
리터럴 `prod`는 세 파일이고 그중 `oauth/admin.tf`는 클러스터 스코프의 오분류다.
사람의 전제는 "클러스터 스코프와 환경 스코프가 분리돼 있지 않아 재설계가 필요하다"였다 — 분리돼 있지 않은 것은 맞지만, 재설계가 요구되는 범위는 파일 셋의 경로 문자열이다.
모범사례 조사(`homelab/261102_2007` 조사 문서)는 환경별 루트의 표현(디렉터리냐 워크스페이스냐)을 가르지 않고, 공유 리소스의 처리만 일치시킨다 — 별도 루트·환경 축 없음·출력으로만 단방향 전달. A·B 어느 쪽이든 `oauth/admin.tf`의 공유 루트 이동과 공유 루트에서의 `env` 변수 제거는 같다.

- **A. 워크스페이스 복제** — 디렉터리는 그대로 두고 TFC 워크스페이스를 환경마다 띄운다(`zitadel`·`oauth` 디렉터리에 prod·stg 워크스페이스, `env` 변수만 다르다). SSM 경로를 `var.env`로 파생시켜 리터럴을 지운다. 저장소의 선언과 `backup`의 모양 그대로다. "디렉터리 하나 = 워크스페이스 하나" 관례가 "디렉터리 하나 = 워크스페이스 묶음"으로 바뀐다 — README 한 줄. 이기는 조건: 환경별 리소스가 적고(지금 둘) 종류가 같을 때. 지는 조건: 환경별 리소스가 종류별 디렉터리에 흩어져 "stg에 뭐가 있나"를 TFC에서만 볼 수 있다.
- **B. 디렉터리 분리** — `cluster/{iam,ci,cloudflare,alert,…}`와 `envs/{prod,stg}/` 또는 `careerhub-env` 모듈을 환경별 루트가 호출한다. 사람의 제안이다. E가 이것을 모범사례로 구체화한 형태다. 이기는 조건: 환경별 리소스가 늘어 묶음으로 보고 싶을 때, 또는 세 번째 환경이 서서 A의 워크스페이스 매트릭스가 커질 때. 지는 조건: 지금은 산출물 둘에 모듈·루트 3층을 세우는 비용이 더 크고, 기존 워크스페이스의 state 이동(`terraform state mv` 또는 재생성 — masterkey는 `prevent_destroy`라 재생성 불가, 반드시 이동)이 따른다. `oauth/admin.tf`의 재분류(cluster로)는 어느 안에서도 해야 하는 일이다.
- C. 단일 워크스페이스에 `for_each` envs — 상태 하나에 prod·stg가 공존하고 stg 추가가 변수 한 줄이다. 지는 조건: stg 실험의 plan이 prod 리소스와 같은 state를 지나 blast radius가 합쳐진다. `backup`을 stateful이라 따로 뗀 원칙과 역방향이다.
- D. 안 한다 — SSM을 손으로 넣는다. 저장소 규칙(AWS CLI 금지)과 desired=코드 원칙(CLAUDE.md §2)을 깬다. 현상 유지의 비용은 "stg의 자격증명이 코드 밖에 산다"이고, 다음 환경 때 같은 수동이 반복된다.
- **E. 모범사례 합성 — 공유 루트는 환경 축 없이, 환경 루트는 얇게, 변동성으로 한 번 더 가른다** — 조사 문서(`homelab/261102_2007`)의 세 뼈대를 이 저장소에 그대로 올린 형태다. 공유 리소스는 Gruntwork의 `_global`처럼 환경 축 없는 루트에, 환경별 리소스는 Google의 `environments/<env>/`처럼 모듈을 부르는 얇은 루트에, 그 안에서 stateful(백업 버킷)과 그 외를 HashiCorp의 변동성 기준으로 다른 state에 둔다. 워크스페이스 이름은 `<app>-<layer>-<env>`를 따른다.

  **트리.**

  ```
  _modules/
    tfc_remote_state/            # 기존
    nat/                         # 기존
    careerhub-env/               # 신규 — 환경 하나의 careerhub 재료. var.env 를 받는다
      masterkey.tf               #   random_password + aws_ssm_parameter ".../careerhub/${var.env}/zitadel/masterkey" (prevent_destroy)
      google-client.tf           #   aws_ssm_parameter ".../careerhub/${var.env}/oauth/google-client"
      variables.tf               #   env · google_client_id · google_client_secret
      outputs.tf                 #   파라미터 이름(경로)만 — 값은 내보내지 않는다
  shared/                        # 환경 축 없음 — 모든 환경이 소비한다. env 변수를 받지 않는다
    iam/                         # 기존 iam/ 이동 — OIDC Provider · IRSA Role(external-secrets · ecr-image-puller)
    ci/                          # 기존 ci/ 이동 — ECR · CodeBuild
    cloudflare/                  # 기존 cloudflare/ 이동 — zone · 터널 · 엣지 · external-dns 토큰
    alert/                       # 기존 alert/ 이동 — Discord 채널 · webhook
    admin-oauth/                 # 기존 oauth/admin.tf 이동 — argocd 등 클러스터 서비스의 Google 클라이언트. 경로 "admin/prod" 의 prod 는 이름만 남은 오분류라 "admin/" 으로
  envs/
    prod/
      careerhub/                 # 얇은 루트 — module "careerhub" { source = "../../../_modules/careerhub-env"  env = "prod" … }
      backup/                    # 기존 backup/ 이동 — stateful(S3 버킷) 이라 careerhub 와 state 를 섞지 않는다(변동성). iam 출력을 tfc_remote_state 로 읽는다(지금과 같다)
    stg/
      careerhub/                 # 같은 모듈, env = "stg". 백업은 범위 밖이라 stg/backup 은 지금 만들지 않는다
  lab/
    vpc/  vpn/                   # AWS 모의 환경(env=onpremise) — 홈랩 환경 축 밖이라 따로 둔다
  ```

  **환경 루트의 전부.** `envs/stg/careerhub/main.tf` 는 이것으로 끝난다.

  ```hcl
  module "careerhub" {
    source               = "../../../_modules/careerhub-env"
    env                  = "stg"
    google_client_id     = var.google_client_id       # 워크스페이스 변수(sensitive) — 콘솔에서 만든 stg 클라이언트
    google_client_secret = var.google_client_secret
  }
  ```

  **워크스페이스(HCP Terraform).** 디렉터리 하나 = 워크스페이스 하나는 유지되고, 이름이 좌표를 드러낸다.

  | 워크스페이스 | working directory | 비고 |
  |---|---|---|
  | `shared-iam` · `shared-ci` · `shared-cloudflare` · `shared-alert` · `shared-admin-oauth` | `shared/<name>` | 기존 워크스페이스의 working directory 만 바꾼다 — state 는 그대로 |
  | `careerhub-secrets-prod` | `envs/prod/careerhub` | 신규 — 기존 `zitadel`·`oauth` 워크스페이스에서 state 를 옮겨 받는다 |
  | `careerhub-secrets-stg` | `envs/stg/careerhub` | 신규 — 변수 넣고 apply 하면 파라미터 둘이 생긴다 |
  | `careerhub-backup-prod` | `envs/prod/backup` | 기존 `onpremise-backup` 의 working directory 변경 + 개명 |

  **공유 → 환경 전달.** 환경 루트가 공유 루트를 읽을 때만 `tfc_remote_state` 를 쓴다 — `envs/prod/backup` 이 `shared-iam` 의 `k8s_oidc_provider_arn` 을 읽는 지금 모양 그대로다. 반대 방향(공유 루트가 환경 루트를 읽는 것)은 없다 — 조사 문서 §6.

  **이행 — 세 번의 state 이동이 핵심이고 전부 되돌릴 수 있다.**
  1. `git mv` 로 `iam`·`ci`·`cloudflare`·`alert`·`backup`·`vpc`·`vpn` 을 옮기고, 각 워크스페이스의 working directory 설정을 바꾼다. plan 이 "No changes" 여야 한다. 공유 루트의 `env` 변수·`default_tags` 의 `env` 는 여기서 걷어낸다(태그 변경은 in-place 라 plan 에 보이되 재생성은 없다).
  2. `_modules/careerhub-env` 를 쓰고 `envs/prod/careerhub` 워크스페이스를 만든 뒤, `zitadel` 워크스페이스의 `random_password.zitadel_masterkey`·`aws_ssm_parameter.zitadel_masterkey` 와 `oauth` 워크스페이스의 `aws_ssm_parameter.google_client` 를 새 워크스페이스로 옮긴다(`terraform state pull` → `state mv -state … -state-out …` → `state push`, 그 뒤 옛 워크스페이스에서 `state rm`). **masterkey 는 `prevent_destroy` 이고 값이 바뀌면 Zitadel 이 기동 불능이라 import 로 다시 만드는 길이 없다 — 이동만 된다.** 이동 뒤 plan 이 "No changes" 인 것이 합격선이다.
  3. `oauth/admin.tf` 의 파라미터를 `shared-admin-oauth` 로 같은 방식으로 옮긴다. 경로를 `admin/prod` 에서 `admin/` 로 바꾸는 것은 파라미터 재생성이라 소비자(ExternalSecret 패치)와 같은 PR 이어야 한다 — 지금 하지 않고 이름만 옮겨도 된다.
  4. `envs/stg/careerhub` 워크스페이스를 만들고 stg 클라이언트 변수를 넣고 apply 한다. 이것이 stg 가 받는 전부다.

  **세 번째 환경이 서면** `envs/<env>/careerhub/` 디렉터리 하나와 워크스페이스 하나다. 공유 루트는 손대지 않는다.

  이기는 조건: 저장소 트리가 그 자체로 분류표가 되길 원할 때 — "공유인가 환경별인가" 를 경로가 답하고, 공유 루트에 `env` 가 없다는 것이 코드로 드러난다. 모범사례 셋이 전부 이 모양을 가리킨다. 지는 조건: 네 안 중 선행 작업이 가장 크다 — 디렉터리 이동 7건·working directory 변경·state 이동 3건이 리소스 둘을 위해 지금 일어난다. masterkey 이동은 되돌릴 수 있지만 실수의 대가가 Zitadel 기동 불능이다. 워크스페이스 수는 A 와 같다(컴포넌트 × 환경) — 줄어드는 것이 아니라 이름과 자리가 바뀌는 것이다.

A를 고르면 E로 넘어가는 조건을 함께 적는 것이 이 축의 판정에 포함된다 — 환경 사이에 구성 차이가 생기거나(튜토리얼의 기준), 환경별 리소스 종류가 셋을 넘거나, 세 번째 환경이 서는 시점이 후보다. E는 A와 공유 리소스 처리가 같으므로, A에서 먼저 하는 `admin.tf` 이동과 공유 루트의 `env` 제거는 E로 가는 길의 1단계이기도 하다.

**판정(사람, 2026-11-03): E — 공유 루트는 환경 축 없이, 환경 루트는 얇게, 변동성으로 한 번 더 가른다. 이행 절차는 별도 논의(§8)에서 계획한다.**

## 5. 반대편 — 이 설계가 틀리는 조건

- 리뉴얼 개발 중에 stg를 "깨져도 되는 자리"로 쓰기 시작하면 게이트 역할이 침식된다. 사람이 한 명이라 규율로만 막힌다 — 그래서 복사(4-2)가 재실행 가능해야 한다. 깨지면 다시 부트스트랩할 수 있어야 게이트로 돌아온다.
- 상시 pre-prod 하나로는 "빠르게 띄우고 지우는" 검증을 못 한다. 그 요구가 실제로 생기면 stg를 늘리는 것이 아니라 다른 부류의 환경이다(§8).
- 데이터 복사 1회(3-6)는 stg 데이터가 prod와 갈라지는 것을 전제한다. 스키마 마이그레이션 검증에는 "prod 모양의 데이터"가 필요하므로, 갈라진 뒤에는 재복사 요구가 돌아온다 — 4-2 A의 재실행 가능성이 이 반론의 비용을 낮춘다.
- 환경별 Google 클라이언트(4-3 A)의 수동 단계는 환경이 늘 때마다 반복된다. 자동화 불가가 확인됐으므로 반복을 받아들이거나, 그때 B·C로 간다.
- NetworkPolicy가 범위 밖이라 stg pod는 prod DB에 닿는다. "격리 데이터 플레인"은 데이터 사본의 격리이고 네트워크 격리가 아니다 — stg에서 prod 접속 문자열을 실수로 쓰는 것을 막는 장치는 없다.
- 앱 pod에 리소스 요청이 없다. stg가 더해지면 실제 사용량이 요청에 잡히지 않아 노드 압박을 늦게 안다 — w0는 이미 CPU 요청 76%다.
- careerhub-web 매니페스트가 없다(#78). stg가 서도 web이 없으면 "리뉴얼 검증 자리"는 Zitadel·composer까지만이다.

## 6. 버린 것

- **별도 클러스터** — Pi 8대 위에서 컨트롤 플레인을 하나 더 두는 비용이 정당화되지 않는다. 제약으로 받았다.
- **prod 데이터 플레인을 공유하는 환경** — `260810_2252` 반론 ①이 "격리의 반대"라 거부한 것이고, 이번에도 그렇다.
- **레거시까지 stg에 미러** — 컷오버 때 소멸하는 것에 Google 클라이언트와 매니페스트를 투자한다.
- **dev와 staging을 둘 다 상시로 세운다** — 리소스가 prod의 세 벌이고, 샌드박스 역할은 상시 환경의 것이 아니다(3-1).
- **"리뉴얼은 prod에 바로"(`260810_2252`의 보류)** — 보류 근거가 소멸해 뒤집었다. 그 논의의 컷오버 절차는 이 결정으로 전제가 바뀐다(§8).

## 7. 임계선 — ADR감인가

대부분은 코드와 티켓이다 — 토폴로지(4-1)·복사 방법(4-2)·suspend(3-5)·overlay 배치는 되돌리는 데 한 시간이고 데이터가 없다.
terraform 구조(4-4)도 state 이동이 따르지만 되돌릴 수 있다 — 티켓 수준이다.

ADR 후보는 하나다 — **"환경은 네임스페이스·데이터 플레인·자격증명 경로가 함께 갈리는 단위다"**(SSM 경로 `/…/careerhub/<env>/…`, 환경별 OAuth 클라이언트, 환경별 Zitadel 인스턴스).
이것이 one-way door인가는 4-3·4-4의 판정에 달렸다 — 4-3 B(prod 클라이언트 공유)를 고르면 이 규정은 성립하지 않고, A를 고르면 세 환경에 걸치는 계약이 되어 뒤집을 때 자격증명 재발급이 따른다.
판정 뒤에 `adr` 스킬의 체크리스트로 가른다.
ADR-0034(terraform은 클러스터 안을 모른다)는 이번 설계와 정합이고 수정 대상이 아니다.

## 8. 다음

- **순서 — terraform 구조 개선(4-4 E)이 먼저, stg 환경 구축은 그 뒤다**(사람, 2026-11-03). 구조 개선의 이행 계획은 `homelab/261103_1429`이 다룬다.
- **쪼갬(사람, 2026-11-03).** stg 구축은 Feature 하나이고, terraform 구조 개선 Feature와 부모로 묶지 않는다 — 둘은 다른 저장소의 다른 흐름이다.
  Feature 사이에는 선행을 걸 수 없으므로(선행은 리프의 것) 순서는 **stg Feature의 발행 자체를 terraform Feature 완료 뒤로 미루는 것**으로 지킨다.
  리프의 밑그림은 여덟이다 — `careerhub-dev` 폐기와 뼈대 개명 · DB overlay(토폴로지·작은 스토리지·백업 선언 삭제) · Gateway·인증서·HTTPRoute · 수집 데이터 복사 Job · `careerhub-secrets-stg`(terraform, Google 콘솔 클라이언트 포함) · apps overlay(secrets 경로·gRPC·composer·auth-service·jobs suspend) · Zitadel overlay와 구성 선언 · careerhub-web stg 배포(#78 선행).
  terraform에 실제로 걸리는 리프는 `careerhub-secrets-stg` 하나다 — 나머지는 k8s만 고친다.
  버린 쪼갬 — 두 Feature를 Epic으로 묶는 것(공표된 근거 ADR이 없고, 묶는 것이 두 저장소를 한 흐름으로 보이게 한다) · 리프 단위 자연 의존으로 k8s 리프를 먼저 여는 것(사람이 발행 시점으로 순서를 잡는 쪽을 택했다).
- 그 뒤 티켓 — Epic의 근거 ADR이 없으므로 Feature "careerhub stg 환경 구축" 아래 리프로 낸다. 리프의 종류는 stg DB overlay(Mongo·PG·백업 삭제 패치)·apps stg overlay(dev appset 뼈대의 개명 포함)·Gateway·인증서·HTTPRoute·jobs suspend·Zitadel stg overlay와 선언·데이터 복사 Job·terraform env 파생과 stg 워크스페이스·기존 careerhub-dev Mongo 폐기다. 트리는 GitHub에 산다.
- **#78 재조정** — careerhub-web 매니페스트가 base + overlay 모양이어야 stg가 소비한다. #78은 apex(prod)만 보고 있다.
- **컷오버 재논의** — 별도 discussion(goal은 리뉴얼 컷오버). `260810_2252`·#79의 전제(검증은 prod 중단 창 안에서)가 "검증은 stg에서"로 바뀐다. prod가 로그인을 제공하지 않으므로 중단 창의 의미도 달라진다.
- **임시 test 환경** — 필요할 때 부트스트랩하고 끝나면 지우는 환경은 사람이 아이디어 단계로 둔 것이다. 이 논의에서 검토하지 않았고, 같은 goal의 다음 관점이 될 수 있다.
- 하네스 마찰 1건은 `tmp/staging/`에 남겼다 — 읽기 전용 kubectl이 pod exec(`du`·`which`)에서 막혀 실 데이터 크기와 도구 유무를 Longhorn 메타데이터와 외부 조사로 대신했다.
