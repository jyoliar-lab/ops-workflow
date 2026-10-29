---
type: discussion
kind: deliberation
goal: cluster-vulnerability-remediation
topic: homelab
subjects: [cri-o, nginx-gateway-fabric, oidc-provider, cloudflared, auth-service, cloudnative-pg, postgresql, pgbouncer, mongodb, zitadel, kubernetes, argocd, longhorn, coredns, cert-manager, external-secrets, grafana-alloy, grafana, prometheus, tailscale]
status: active
ref-adrs: []
related:
  - docs/homelab/discussion/261029_1359_pre-exposure-component-vulnerability-survey.md
  - docs/careerhub/discussion/261026_1811_public-gateway-topology-and-tunnel-handoff.md
---

# 공개 전 취약점 처리 — 치명도 · 해결 · 난이도의 순위

## 1. 문제

전수 조사(261029_1359)가 세어 보니 공개 경로에서 깨끗한 것은 careerhub-front v0.0.5 와 api-composer v0.4.1 둘뿐이고, 나머지는 거의 전부 뒤처져 있다.
패치가 끊긴 라인이 일곱(Kubernetes 1.34 · Longhorn 1.7 · CloudNativePG 1.28 · Go 1.25 · Go 1.21 · distroless base-debian11 · nginx 1.28 · Argo CD 3.2)이고, 전 노드의 CRI-O 가 Critical 컨테이너 탈출 CVE 범위이며, 데이터 계층은 비인증 DoS · 인증 RCE 가 겹쳐 있다.
이것을 전부 공개 전에 끝낼 수는 없다 — 노드 작업(CRI-O · kubeadm · 커널)은 8대를 한 대씩 비워야 하고, Longhorn 은 마이너를 네 번 건너야 하며, Go 1.21 서비스는 빌드부터 다시 통과시켜야 한다.
그래서 정해야 하는 것은 셋이다 — **무엇이 우리에게 치명적인가**(노출 경로 × 결과 × 전제 조건), **어떻게 고치는가**(목표 버전과 설치 경로), **지금 운영 상황에서 얼마나 어려운가**(중단 · 데이터 · 노드 작업 · CRD/메이저).
그 셋을 한 표로 세우고, 표에서 "공개 전에 끝낼 것" 의 선을 어디에 긋는지, 나머지를 어떤 묶음과 순서로 가는지를 가른다.
인터뷰는 사용자 지시로 생략했다(2026-10-29) — 아래 순위는 agent 의 평가이고, 선을 긋는 것과 묶음은 사람의 판정이다.
이 논의의 goal 은 레거시 공개(`legacy-public-exposure`)와 별개다 — 공개가 일부 조치의 시점을 앞당길 뿐이고, 표의 전부가 결국 수행 대상이다.

## 2. 실측

취약점 사실은 전부 조사 문서(261029_1359)에 있고 여기서는 되풀이하지 않는다.
난이도 판정의 근거가 되는 **설치 경로와 운영 조건**은 이 문서가 2026-10-29 에 읽었다.

### 2-1. 세 개의 설치 평면

| 평면 | 도구 | 여기 사는 것 | 갱신 방법 |
|---|---|---|---|
| 노드 | Ansible (`onpremise-k8s/kubernetes` · `vpn`) | kubeadm · kubelet · CRI-O(apt, `crio_version` 핀) · 커널 · Tailscale(install.sh, 핀 없음) | playbook 실행 — `kubeadm-upgrade.yaml`(첫 마스터 apply → 나머지 `serial: 1` node) · `crio.yaml` · 커널 playbook 은 없음(unverified) |
| 플랫폼 | helmfile (`jyoliar-k8s/platform`) | Longhorn 1.7.2 · external-secrets 1.2.1 · kubelet-csr-approver 1.2.2 (wrapper chart 의존성 핀) | `helmfile apply` — Argo CD 밖, 사람이 돌린다 |
| GitOps | Argo CD (`jyoliar-k8s/gitops`) | 나머지 전부 — helm 차트 `targetRevision`(cert-manager · external-dns · CNPG · barman · zitadel · grafana-operator · loki · tempo · alloy · kube-prometheus-stack · kagent) · raw URL 핀(Argo CD `v3.2.1/manifests/ha/install.yaml` · NGF `v2.2.1/deploy` + Gateway API CRD `v1.4.0` · MongoDB operator `1.7.0/public`) · 이미지 태그(cloudflared · oidc nginx · 앱 8개 · PG · pgbouncer · MongoDB `spec.version`) | 파일의 한 줄을 고쳐 머지 — Argo CD 가 동기화 |

Argo CD 의 redis 8.2.2 · haproxy 3.0.8 · dex 2.43.0 은 `ha/install.yaml` 에 묶여 있다 — Argo CD 를 올리면 셋이 같이 간다.
MongoDB operator 와 NGF 는 raw URL 핀이라 CRD 와 배포 매니페스트가 같은 한 줄에서 바뀐다.
NGF 2.8.0 은 Gateway API 1.6.3 을 요구한다(CHANGELOG) — 지금 CRD 는 v1.4.0 이다.

### 2-2. 운영 조건

- 노드 8대 — control-plane 3(raspberrypi-0 · 1 · 2, 10.18.1.x) · worker 5(s0 · s1 10.18.2.x · w0 · w1 · w2 10.18.3.x). 전부 arm64 Raspberry Pi.
- 노드별 패치 수준이 다르다 — CRI-O 1.34.5(5대) · 1.34.6(w0) · 1.34.9(w1 · w2), 커널 6.12.47 · 62 · 75. 1.34.9 패치 업그레이드(#25)는 2026-07-31 에 ClusterConfiguration 정비(#27) 뒤 playbook 으로 끝냈다.
- Longhorn 볼륨 20개 · 복제 2 · 스케줄 가능 노드 5(worker 만) — 한 노드를 비워도 복제 하나가 남는다. 업그레이드 체커는 꺼져 있다.
- 단일 레플리카 — frontend · zitadel · zitadel-login · careerhub-nginx-gateway-nginx · pooler. 노드를 비우면 이들은 잠깐 끊긴다.
- 이중 — api-composer · auth-service · gRPC 셋 · PostgreSQL(2 인스턴스) · MongoDB(2 멤버 + arbiter).
- NetworkPolicy 는 `argocd` 네임스페이스에만 8개 — **나머지는 평면 네트워크**다. 공개 경로의 앱 pod 가 뚫리면 MongoDB · PostgreSQL · pgbouncer · etcd(노드 네트워크) 에 바로 닿는다.
- careerhub-prod 앱 pod 는 `default` ServiceAccount 에 RoleBinding 이 없다(SA 토큰은 자동 마운트). 즉 앱 pod 침해만으로는 pod 를 만들 수 없다 — CRI-O 탈출의 전제(pod 생성)는 Argo CD · kagent · CI 같은 다른 발판이 필요하다.
- careerhub-dev 에 같은 MongoDB 8.0.19 가 1 멤버로 있다 — 서버 업그레이드 리허설이 가능하다. PostgreSQL · ZITADEL 에는 dev 가 없다.
- 앱 저장소의 버전 인상은 #139 · #140 · #141 의 모양(브랜치 → 태그 → gitops 태그 인상)이 이미 있다.

## 3. 인터뷰에서 닫힌 축

없음 — 인터뷰를 생략했다(사용자, 2026-10-29).
범위는 사용자의 지시대로 클러스터 전체이고, 공개 경로만이 아니다.

## 4. 열린 축 — 논의

### 4-1. 순위 — 치명도 × 해결 × 난이도

평가 축은 셋이다.
**치명도**는 "우리에게" 다 — 인터넷 도달 여부(공개 경로 · 이미 공개 · LAN · 내부) × 결과(계정/클러스터 탈취 · RCE · 데이터 · DoS) × 전제(비인증 · 인증 · 클러스터 권한) × 연쇄(뚫린 뒤 다음 칸으로 가는가).
**난이도**는 설치 평면과 운영 조건에서 나온다 — 하: 한 줄 고치고 동기화 · 중: 재시작 · 스위치오버 · CRD · 단일 레플리카 끊김 · 코드 변경과 릴리스 · 상: 노드를 비우는 작업 × 8 · 마이너를 여러 번 건넘 · 메이저 경계 · 데이터 마이그레이션.
**최고 등급**은 그 컴포넌트에 걸린 취약점 중 가장 높은 공식 등급이다 — 벤더 또는 GHSA 의 Critical · High · Medium, CVSS 점수가 있으면 함께, nginx 는 자체 척도(Major · Medium). Go 취약점 DB(GO-·) 는 등급을 매기지 않으므로 그 자리에 적는다. 등급은 조사 문서의 값이고 "우리에게" 의 치명도와 다르다 — 순위는 등급이 아니라 치명도 열이 정한다.
"공개 전" 열은 agent 의 제안이고 4-2 가 판정한다.

| 순위 | 컴포넌트 (실행 → 목표) | 최고 등급 | 왜 우리에게 치명적인가 | 어떻게 고치는가 | 난이도 | 공개 전 |
|---|---|---|---|---|---|---|
| 1 | **nginx:1.28-alpine** (oidc-provider) → 1.30.6-alpine | Major (CVE-2026-42533, `map` 설정 시) · Medium 다수 — 정적 설정에서 확정 도달 없음 | `k8s-oidc.jyo-liar.com` 으로 **이미 인터넷에 열려 있고** 1.28 라인은 2026-03 이후 수정이 없다. 정적 서버라 확정 도달 CVE 는 없지만, 공개 경로에서 패치 없는 파서를 두는 셈이다 | `base/bootstrap/oidc-provider/deployment.yaml` 이미지 태그 한 줄 | **하** — 정적 파일 서빙이라 설정 호환 위험 없음 | 예 |
| 2 | **cloudflared** 2026.2.0 → 2026.10.5 | 등급 미부여 — Go stdlib 권고 ~40건(CVE-2026-32283 비인증 TLS DoS 등) · quic-go CVE 3건 · 자체 VULN 3건 | 공개 경로의 첫 홉. Go 1.24.13 빌드라 stdlib 권고 ~40건 범위이고 8개월치 보안 범프를 못 받았다. 아웃바운드만 열지만 Cloudflare 가 중계한 모든 요청이 이 바이너리의 HTTP/2 를 지난다 | `base/bootstrap/cloudflare-tunnel/deployment.yaml` 태그 — #136 이 같은 파일을 건드리므로 거기 얹을 수 있다 | **하** — 재시작 수 초, 터널 재연결 | 예 |
| 3 | **NGF 2.2.1 (nginx 1.29.2)** → 2.8.0 (nginx 1.31.7) | Major (CVE-2026-42533) · Medium 10여 건 — 생성 설정 기준 확정 도달 없음 | 공개 경로의 HTTP 파서. 생성 설정 기준 확정 도달 CVE 는 없으나 `map` 생성 여부가 미확인이고, 1.29 는 mainline 이라 2026년 권고 수정이 전혀 들어오지 않는다. 공개 Gateway(#137)를 이 버전으로 새로 만드는 것은 처음부터 뒤처진 채 시작하는 것이다 | `base/controllers/nginx-gateway/kustomization.yaml` 의 URL 세 줄(Gateway API CRD v1.4.0 → 1.6.3 · NGF crds · deploy) + 두 패치 파일의 드리프트 확인. 2.2 → 2.8 은 여섯 마이너라 릴리스 노트의 breaking 을 읽어야 한다 | **중** — CRD 메이저 안 마이너 인상 · 컨트롤러 재시작 · 데이터플레인 pod 재생성(LAN Gateway 셋 다 수 초 끊김) · 단일 레플리카 | 예 — #137 보다 앞에 |
| 4 | **CloudNativePG** 1.28.1 → 1.30.1 · **PostgreSQL** 18.3 → 18.6 · **pgbouncer** 1.25.1 → 1.26.1 | **Critical ×2** (CNPG CVE-2026-44477 · 55769) · High (55765) · PG CVSS 8.8 ×10 · **8.2 비인증** (CVE-2026-14679) · pgbouncer 는 CVSS 미표기 | 평면 네트워크라 공개 앱 pod 에서 바로 닿는다. pgbouncer 는 **비인증 크래시 4건**(pre-auth 도달)과 SCRAM 사칭, PG 는 **비인증 8.2점** 1건, CNPG 는 임의 DB 로그인으로 **슈퍼유저 → OS RCE** 2건. auth-service 의 pgx SQL 주입(GO-2026-5004)과 이으면 공개 경로에서 PG pod RCE 까지 한 줄이다. 1.28 라인은 EOL 이라 1.28.4 는 임시방편이다 | 운영자: `cloudnativepg-helm` 차트 0.27.1 → 1.30.1 대응 차트(번호 unverified). PG: `cluster.yaml` 의 `imageName` 18.6. pgbouncer: Pooler 의 이미지 1.26.1 | **중** — 운영자 업그레이드가 인스턴스 매니저를 롤링 재시작(2 인스턴스라 스위치오버 1회) · PG 마이너 인상도 롤링 · pgbouncer 1.26 의 `search_path` 추적 변경은 앱으로 시험해야 함 · dev 환경 없음 | 예 — pgbouncer · PG 18.6 은 반드시, 운영자 1.30 은 가능하면 |
| 5 | **MongoDB** 8.0.19 → 8.0.34 (+ operator 1.7.0 → 1.14.0) | **CVSS 9.2** (CVE-2026-82067) · **8.7 비인증** ×2 (82064 · 82075) · 나머지 ~75건 등급 미표기 | 공개 경로의 데이터 저장소이고 평면 네트워크. **비인증 DoS**(CVE-2026-82064) 와 **authorization 이 꺼진 채 기동**(CVE-2026-82067, 설정 의존 · 운영자 생성 설정의 해당 여부 unverified), `updateUser` 권한 상승 등 ~80건. 운영 DB 가 15 패치 뒤 | 서버: `MongoDBCommunity.spec.version` 8.0.34 — 운영자가 롤링(멤버 2 + arbiter). careerhub-dev 에서 먼저. 운영자: kustomization 의 raw URL 1.7.0 → 1.14.0(CRD 포함) — 7 마이너의 CRD 변경 unverified | **중**(서버) · **중~상**(운영자) — 서버는 리허설 가능 · 운영자는 CRD 변경 확인이 먼저 · 서버를 먼저 올리고 운영자는 뒤에 | 서버는 예 · 운영자는 아니오 |
| 6 | **CRI-O** 1.34.5/6/9 → 1.34.15 | **Critical** (CVE-2026-62146, CVSS 미표기) · **Critical 9.9** (92574) · Critical (15801) · Medium ×2 | 전 노드가 Critical 컨테이너 탈출(CVE-2026-62146) 범위. 전제가 pod 생성 권한이라 공개 앱 pod 침해 **단독으로는** 못 쓰지만, Argo CD(순위 9) · kagent · CI 어느 하나가 뚫리면 노드 탈취로 이어지는 **2차 경로의 마지막 칸**이다. 노드별 버전이 셋이라 이미 미완의 롤링이 있었다 | Ansible `crio_version` 핀 → 1.34.15, `crio.yaml` playbook. advisory 가 노드의 컨테이너를 전부 비우라고 적으므로 drain 이 필요 | **상** — drain × 8 · 단일 레플리카 끊김 8회 · Longhorn 복제 2 로 한 대씩만 · CRIU 복원 설정 확인(unverified) · 소요 반나절 | 아니오 — 공개 직후 첫 노드 창 |
| 7 | **Kubernetes** 1.34.9 → 1.34.13 (→ 1.35.x) | Medium 5.9 (CVE-2026-2270) · etcd Medium ×4 · Low ×2 | 1.34 가 2026-10-27 EOL. 1.34.13 이 마지막 패치이고 CVE-2026-2270(내부 권한) 포함. 그 뒤는 보안 패치가 없는 제어면이다 | 1.34.13: `kubeadm-upgrade.yaml`(검증된 절차, 7월에 1.34.9 로 수행). 1.35: 같은 playbook + CRI-O 1.35 + flannel · kube-vip 호환 확인 | **중**(1.34.13 — 절차 있음 · 노드당 kubelet 재시작) · **상**(1.35 — 마이너 경계 · CRI-O 도 함께) | 아니오 — CRI-O 와 같은 노드 창에 1.34.13 을 묶는다 |
| 8 | **auth-service** v0.2.1 → Go 1.27.3 · jwt ≥5.3.1 · pgx ≥5.9.2 · x/net ≥0.60.0 · grpc ≥1.83.1 · kin-openapi ≥0.144.0 · base-debian13 | 등급 미부여(Go 취약점 DB) — reachable 21건 중 SQL 주입 · HTTP/2 서버 DoS · JWT 메모리 소진 | reachable 21건 — JWT 파싱 · SQL 주입 · HTTP/2 서버 5건. **전환(#138) 뒤 공개 경로에서 빠지지만** 지금은 LAN `/auth` 로 열려 있고, Go 1.25 계열에서는 stdlib 5건이 영영 안 고쳐진다. 체크아웃(jwt 5.3.1)이 태그(5.2.1)보다 앞서 있어 태그만 내면 1건은 닫힌다 | #139 와 같은 모양의 티켓 — go.mod 인상 · `golang:1.27` · `base-debian13` · 태그 · gitops 인상 | **중** — 코드 빌드 · 테스트 통과 · 릴리스 1회 | 아니오 — 공개 경로에서 빠지는 것이 먼저(#138). 단 #138 이 미뤄지면 예 |
| 9 | **Argo CD** 3.2.1 → 3.3.18+ (3.5.6) — redis · haproxy · dex 동반 | **Critical ×5** (CVE-2026-113709 · 113708 · 113672 · 77459 · 42880) · High ×3 · redis High (CVE-2025-62507) · dex High(범위 unverified) | 지원 종료 라인 · repo-server RCE critical 3건 · Secret 추출. 인증 사용자가 전제이고 LAN/Tailscale 만이지만, **Argo CD 는 클러스터 전체에 쓰기 권한이 있다** — 여기가 뚫리면 CRI-O(6)의 전제가 채워진다. redis XACKDEL RCE 도 같이 닫힌다 | `base/bootstrap/argocd/kustomization.yaml` 의 raw URL 한 줄 — 자기 자신을 동기화한다. 3.2 → 3.3 → 3.4 → 3.5 의 업그레이드 노트(CRD · RBAC 기본값 변경) 확인 | **중** — 자기 관리 업그레이드 · 컴포넌트 전부 재시작 · 동기화 잠깐 멈춤 · 되돌림은 URL 복원 | 아니오 — 공개 직후 |
| 10 | **ZITADEL** 4.15.3 → 4.20.0 | **Critical ×4** · **High ×12** · Medium ×2 · Low ×2 | critical 4 · high 12, 대부분 **비인증 계정 탈취**. 지금 인터넷 경로는 없고 LAN Gateway 뒤다. 그러나 k8s API 서버의 OIDC 발급자라 **계정 탈취 = 클러스터 관리자 신원 탈취**다. 공개 경로에 올릴 계획이 생기는 순간 1순위가 된다 | `zitadel-helm` 차트 10.0.4 → 4.20.0 대응 차트(번호 unverified). setup job 이 DB 마이그레이션을 돌린다 | **중** — 단일 레플리카 · 마이그레이션 · 로그인 V2 변경 가능성 · dev 없음 · PG 가 뒤(4)에 있으니 순서는 PG 뒤 | 아니오 — 단, 4-2 의 선택에 따라 예 |
| 11 | **CoreDNS** 1.12.1 → 1.14.7 | **High 7.5 비인증** (CVE-2026-26018) · High ×10여 건은 비기본 플러그인 한정 | Corefile 의 `loop` 로 비인증 DoS(CVE-2026-26018)에 닿는다. 클러스터 DNS 가 죽으면 공개 서비스 전부가 죽는다. 도달은 클러스터 네트워크에서만 | kubeadm 이 관리 — `kubeadm upgrade` 가 1.34.13 의 번들 CoreDNS 로 올린다(1.34.13 번들 버전 unverified). 그 뒤에도 1.12 면 Deployment 이미지를 직접 핀 | **하~중** — 7 과 같은 창 | 아니오 — 7 과 함께 |
| 12 | **cert-manager** 1.20.1 → 1.20.5 | High (CVE-2026-62290) | ClusterIssuer DNS 자격증명 탈취 — `challenges` 생성 권한이 전제라 내부 | `cert-manager-helm` targetRevision | **하** | 아니오 |
| 13 | **external-secrets** 1.2.1 → 1.3.2 (→ 2.x) | High ×2 (CVE-2026-26287 · 34984) · Medium · Low | Secret 유출 — ESO 리소스 생성 권한이 전제. 모든 자격증명이 이것을 지난다 | helmfile wrapper 의존성 1.3.2(패치) 또는 2.14.0(메이저) | **하**(1.3.2) · **중**(2.x CRD) | 아니오 |
| 14 | **Longhorn** 1.7.2 → 1.11+ | 해당 advisory 없음 — EOL 이 위험 | EOL 이고 모든 상태(DB · 메트릭 · 로그)가 여기 있다. 업스트림 advisory 는 없다 — 위험은 "패치가 없다" 는 구조적인 것 | helmfile 의존성 1.7 → 1.8 → 1.9 → 1.10 → 1.11 **한 마이너씩**, 각 단계마다 엔진 라이브 업그레이드 + 볼륨 20개 건강 확인 | **상** — 네 번의 업그레이드 · 데이터 · 되돌림 어려움 · 반나절 × 4 | 아니오 — 별도 계획 |
| 15 | **Alloy** 1.15.0 → 1.21.3 · **grafana-operator** 5.23 → 5.25 + **Grafana** 12.4.14 · **Prometheus** (kube-prometheus-stack 82.10.3 → 최신) · **Loki** 3.7.x | Alloy High 7.7 (CVE-2026-75889) · Prometheus High ×2 · Grafana High ×6 (최고 7.7) · Loki Medium 7.5 · operator Medium | Alloy 는 ServiceMonitor 쓰기 권한으로 SA 토큰 유출, Prometheus 는 API 클라이언트의 remote-read DoS, Grafana 는 ~20건(비인증 2건은 공개 대시보드 사용 시만). 전부 Tailscale/LAN | 차트 targetRevision 들 · Grafana CR 에 `spec.version` 명시 · kube-prometheus-stack 은 CRD 를 함께 올려야 함 | **하**(Alloy · operator · Loki) · **중**(kube-prometheus-stack CRD) | 아니오 |
| 16 | **review-crawler** · **skillscanner** (Go 1.21) · **posting-provider** (Go 1.25) · 8개 서비스의 **base-debian11** | 등급 미부여(Go 취약점 DB) — reachable stdlib 33 ~ 34건 · x/net/html XSS · DoS 8건 · base-debian11 은 미조사 | 내부 전용. crawler 는 외부 HTML 을 파싱하므로 x/net/html 8건이 실질 입력면이다. base-debian11 은 26개월 재빌드 없음 | 저장소별 go.mod · Dockerfile 인상과 태그. 1.21 → 1.27 은 의존성이 같이 뛰어 빌드가 깨질 수 있다 | **중~상**(crawler · skillscanner) · **하**(base 이미지 줄만) | 아니오 |
| 17 | **Tailscale** (버전 미상) → 1.104.4 | 공지에 등급 없음 — 서브넷 라우터 해당 2건(TS-2026-011 · 002) | 사이트 간 노드 연결의 전부. 2026년 공지 대부분이 SSH · Serve 활성 노드 한정이라 서브넷 라우터는 도달이 낮다. 문제는 **버전을 모른다** 는 것 | 노드에서 `tailscale version` → `vpn` 역할에 버전 핀 추가 → apt 업그레이드 | **하** — 다만 ssh 와 Ansible 실행이 필요 | 아니오 — 확인은 예 |
| 18 | **커널** 6.12.47/62/75 → 통일 | unverified — 버전별 CVE 목록을 만들지 못함 | 노드별로 다르고 최신 6.12.114 에서 39 ~ 67 릴리스 뒤. 컨테이너 탈출의 2차 요인 | `apt full-upgrade` + 재부팅 × 8 — 6.12 유지(RPi 저장소에 6.12.75 이후가 있는지 unverified) 또는 6.18.50 | **상** — 재부팅 × 8 · 6.18 은 Longhorn · flannel 검증 필요 | 아니오 — CRI-O 창에 묶으면 drain 은 한 번 |
| 19 | 잔재 — `default/nginx`(`nginx:latest`, NodePort 31111) · curl 8.12.1 init · kagent beta · kube-vip 0.8.7 · metrics-server · kubelet-csr-approver · external-dns · haproxy | curl High (CVE-2026-92392) · 나머지 advisory 없음 | 공격면 축소 · 위생 | 삭제 한 번 · 태그 한 줄 · 차트 한 줄 | **하** | `default/nginx` 삭제는 예 |

순위의 뼈대를 한 줄로 말하면 — **공개 경로 위의 "패치 없는 파서" 셋(1 · 2 · 3)과 평면 네트워크로 노출되는 데이터 계층(4 · 5)이 공개 전이고, 노드 작업(6 · 7 · 11 · 18)과 제어 도구(9 · 10)가 공개 직후의 첫 두 창이며, EOL 스토리지(14)와 내부 Go 서비스(16)는 별도 계획이다.**

### 4-2. 공개 게이트 — 표의 어디까지를 공개 전에 끝내는가

실측이 말하는 것 — 공개 경로 위의 셋(1 · 2 · 3)은 전부 난이도 하~중이고 합쳐 하루다.
데이터 계층(4 · 5)은 난이도 중이지만 dev 리허설(MongoDB)과 롤링(PG)이 가능하다.
노드 작업(6 · 7)은 상이고, 공개 앱 pod 침해 단독으로는 전제가 채워지지 않는다.

- **A. 1 ~ 5 (공개 경로 + 데이터 계층)** — 공개 경로에 패치 없는 파서가 없고, 평면 네트워크의 비인증 DoS · RCE 연쇄가 닫힌 뒤 연다. 이기는 조건: 공개가 2 ~ 3일 늦어도 된다. 지는 조건: PG · pgbouncer 인상에서 앱 회귀가 나와 공개가 주 단위로 밀린다.
- B. 1 ~ 3 만 (공개 경로) — 하루 안에 열 수 있다. 이기는 조건: 공개 일정이 먼저이고 데이터 계층은 첫 주에 바로 뒤따른다. 지는 조건: 공개 직후 앱 취약점으로 pod 가 뚫리면 DB 가 비인증 DoS 범위 그대로다.
- C. 1 ~ 7 (노드 작업까지) — 컨테이너 탈출 경로까지 닫고 연다. 이기는 조건: 공개가 2주 늦어도 되고 노드 창을 지금 잡을 수 있다. 지는 조건: 노드 창이 늘어지면 공개 자체가 표류한다 — 그리고 6 의 전제는 공개 앱이 아니라 Argo CD 쪽이다.
- D. 안 한다 — 지금 버전 그대로 연다. 현상 유지의 비용: 이미 공개된 k8s-oidc 의 nginx 1.28 이 그대로이고, 새로 만드는 공개 Gateway 가 처음부터 패치 없는 라인으로 시작한다.

**판정(사람, 2026-10-29): B. 공개 전에는 1 ~ 3(oidc nginx · cloudflared · NGF)만 끝낸다. 데이터 계층(4 · 5)부터는 공개 뒤이고, 그 순서와 묶음은 4-3 · 4-4 에서 정한다.**

### 4-3. 공개 직후의 묶음과 순서

실측이 말하는 것 — 노드를 비우는 작업은 drain 당 단일 레플리카 끊김이 따르므로 **한 번 비울 때 할 수 있는 것을 다 한다**.
Argo CD 와 CRI-O 는 연쇄의 앞뒤라 어느 쪽을 먼저 닫아도 연쇄는 끊긴다.

- **A. 노드 창 하나에 CRI-O 1.34.15 + kubeadm 1.34.13(CoreDNS 동반) + 커널 통일 + Tailscale 확인** — drain × 8 을 한 번만 한다. 이기는 조건: 반나절 ~ 하루의 창을 확보할 수 있다. 지는 조건: 한 노드에서 셋 중 하나가 실패하면 원인 분리가 어렵다.
- B. CRI-O 만 먼저, kubeadm · 커널은 다음 창 — 원인 분리가 쉽다. 지는 조건: drain × 8 이 두세 번이 된다.
- C. Argo CD(9) 를 노드 창보다 먼저 — 한 줄 변경으로 연쇄의 앞 칸을 끊고 노드 창을 여유 있게 잡는다. 이기는 조건: Argo CD 3.3+ 의 업그레이드 노트에 걸리는 것이 없다. 지는 조건: 자기 관리 업그레이드가 꼬이면 모든 동기화가 멈춘다 — 되돌림은 URL 복원이지만 그 커밋을 반영할 Argo CD 가 죽어 있을 수 있다.

### 4-4. EOL 라인의 처분 — 패치가 아니라 이전

- **Kubernetes 1.35** — 1.34.13 뒤 보안 패치가 없다. 다음 노드 창(4-3 다음)에 1.35 + CRI-O 1.35 를 묶는 것이 자연스럽다. 이기는 조건: flannel 0.28 · kube-vip 1.x 호환을 먼저 올려 둔다.
- **Longhorn 1.7 → 1.11+** — 네 단계. 각 단계가 반나절이고 데이터가 걸린다. 선택지는 (a) 공개 뒤 한 달 안에 주 1단계 (b) 1.35 이전 전에 몰아서 (c) 안 한다 — 볼륨 20개의 복제 2 가 유일한 안전망인 채로 둔다.
- **CloudNativePG 1.30** — 4 에서 운영자까지 올렸으면 끝. 1.28.4 로 멈췄다면 여기서 1.30 을 따로 잡는다.
- **auth-service 의 Go 1.25 · Go 1.21 둘** — #138 뒤 auth-service 의 거취(유지 · 폐기)가 정해져야 Go 인상 티켓이 의미가 있다. crawler · skillscanner 는 내부 배치라 1.35 이전 뒤로 미뤄도 노출이 늘지 않는다.
- **distroless base-debian13** — 각 서비스의 다음 릴리스에 한 줄씩 얹는다. 따로 창을 잡지 않는다.

## 5. 반대편 — 이 순위가 틀리는 조건

- ZITADEL 을 공개 경로(공개 Gateway 뒤)에 올릴 계획이 조금이라도 있으면 10 은 1 이 된다 — 비인증 계정 탈취가 곧 클러스터 관리자다.
- 공개 앱 pod 의 `default` SA 가 어디선가 RoleBinding 을 받으면(향후 추가 · kagent 류) CRI-O(6)의 전제가 공개 경로에서 바로 채워진다 — 그때 6 은 공개 전이다. 이 문서는 impersonate 권한이 없어 `auth can-i` 를 돌리지 못했고 RoleBinding 부재로만 판단했다.
- NGF 가 생성하는 nginx.conf 에 `map` 블록이 있으면 CVE-2026-42533(Major)이 공개 경로에서 확정 도달이다 — 3 이 1 로 올라간다. 생성된 conf 를 한 번 읽으면 닫힌다.
- MongoDB 운영자가 만드는 설정이 CVE-2026-82067 의 대소문자 조건에 걸리면 "authorization 꺼진 채 기동" 이 현실이고 5 가 4 를 앞선다 — 운영 mongod 의 `security.authorization` 실효값을 확인하면 닫힌다.
- Cloudflare 엣지 보호(#135 의 WAF · rate limit)가 HTTP/2 결함류를 걸러 준다면 2 · 3 의 긴급도는 낮아진다 — 그러나 Free 플랜의 보호 범위(261026_1631)로는 파서 결함을 막는 것이 아니다.
- 공개 뒤 트래픽이 사실상 없다면 DoS 류의 무게는 전부 내려간다 — 남는 것은 RCE · 탈취뿐이고 그러면 순위는 4(CNPG) · 9(Argo CD) · 10(ZITADEL) 이 앞으로 온다.

## 6. 버린 것

- **"전부 최신으로 한 번에"** — 세 평면 · 노드 8대 · EOL 네 단계가 한 창에 들어가지 않고, 실패했을 때 원인을 가를 수 없다.
- **"공개 전에 전부"** — 공개가 표류한다. 공개 경로 밖의 것은 공개 뒤에 해도 노출이 늘지 않는다는 것이 실측(평면 네트워크와 SA 권한)의 결론이다.
- **WAF 로 대체** — 엣지 보호는 파서 결함과 인증 RCE 를 막지 못한다. 보완이지 대체가 아니다.
- **nginx 1.28 → 1.28 유지 + 설정으로 회피** — 설정으로 비해당을 만들 수 있는 CVE 는 그렇지만, 라인이 죽은 것은 설정으로 살리지 못한다.
- **CRI-O 만 핀을 올리고 drain 없이 재시작** — advisory 가 컨테이너를 비우라고 적는다. 오염된 sandbox 상태가 재시작 뒤에 발동하는 결함이라 비우지 않으면 패치가 의미 없다.

## 7. 임계선 — ADR감인가

순위와 묶음은 티켓이다 — 되돌리는 데 한 시간이면 ADR 이 아니다.
ADR 후보는 하나다 — **"지원 종료 라인을 운영에 두지 않는다 — 공개 경로 컴포넌트는 패치 라인 안에 있어야 한다"** 는 운영 원칙.
이것은 되돌리기 어려운 결정이 아니라 반복 집행되는 규율이라 ADR 의 일차 기준(one-way door)에는 못 미친다.
다만 이번처럼 일곱 라인이 동시에 EOL 인 상태가 다시 오지 않게 하려면 **버전 갱신의 주기와 책임**을 어디에 두는지가 결정이다 — Renovate 류의 자동 PR 을 gitops 에 붙이는 것은 구조로 강제하는 길이고, 그것을 택하면 ADR 감이다.
이 문서는 거기까지 열지 않는다 — 별도 관점이다.

## 8. 다음

- 4-2 의 판정이 나면 "공개 전" 묶음을 Feature #133 아래 리프로 낸다 — oidc nginx 태그 · cloudflared 태그(#136 에 얹을지 별도일지) · NGF 2.8 + Gateway API 1.6.3 · pgbouncer 1.26.1 · PG 18.6 · CNPG 운영자 · MongoDB 8.0.34(dev 먼저) · `default/nginx` 삭제.
- 4-3 의 판정이 나면 노드 창 티켓 하나(onpremise-k8s 대상) — CRI-O · kubeadm 1.34.13 · 커널 · Tailscale 확인 — 와 Argo CD 인상 티켓.
- 4-4 는 각각 별도 Feature 다 — Kubernetes 1.35 이전 · Longhorn 네 단계 · Go 1.21/1.25 서비스 인상. 티켓 시점은 사람이 정한다.
- 반대편(§5)의 확인 가능한 셋은 공개 전에 닫는다 — NGF 생성 conf 의 `map` 유무 · mongod 의 `security.authorization` 실효값 · ZITADEL 공개 계획 유무.
- 갱신 주기 · 자동 PR 은 새 discussion 이다 — goal 이 다르다.
