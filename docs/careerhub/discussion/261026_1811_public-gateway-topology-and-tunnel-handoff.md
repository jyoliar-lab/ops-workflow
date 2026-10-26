---
type: discussion
kind: deliberation
goal: legacy-public-exposure
topic: careerhub
subjects: [nginx-gateway-fabric, cloudflare-tunnel, cloudflared, external-dns, careerhub-nginx-gateway, careerhub-httproute, oidc-provider, jyoliar-platform-terraform, external-secrets]
status: done
ref-adrs: [ADR-0034]
related:
  - docs/careerhub/discussion/261026_1632_cloudflare-exposure-wiring-and-edge.md
  - docs/careerhub/discussion/261026_1631_cloudflare-tunnel-dns-edge-survey.md
  - docs/careerhub/discussion/260810_1801_path-to-host-based-routing.md
---

# 공개 Gateway 토폴로지 — 터널 하나 · Gateway 한 단인가 두 단인가

## 1. 문제

공개 인터넷으로 나가는 엔드포인트는 Cloudflare Tunnel 하나로 전부 관리한다.
이 전제가 앞 논의(261026_1632)의 두 판정을 뒤집는다 — 새 터널(3-4)과 careerhub-prod 안의 공개 Gateway(4-1).
이 문서가 그 둘을 이어받고, 4-2(cloudflared → Gateway 의 TLS)도 홉 설계에 맞춰 다시 정한다.

새 그림은 이렇다.
기존 `k8s-oidc` 터널을 공개 터널로 쓰고, 그 ingress 설정을 terraform 에서 GitOps 로 옮긴다.
cloudflared 의 ingress 가 호스트별로 목적지를 고른다 — k8s-oidc 는 oidc-server 로 직결, careerhub 는 careerhub-prod 안의 공개 전용 NGF Gateway 로.
공개 서비스가 지금은 careerhub 뿐이므로 여러 호스트를 받는 플랫폼 공개 Gateway 는 두지 않는다 — 공개 서비스가 늘면 그때 구조를 다시 본다.

열려 있던 것은 둘이다.
공개 Gateway 가 careerhub 의 서비스(frontend · api-composer)로 경로 라우팅까지 직접 하는가, 아니면 호스트 단위로 careerhub 전용 Gateway 에 넘기고 경로는 거기서 가르는가.
그리고 그 과정에서 k8s-oidc(클러스터 SA 토큰의 OIDC 발급자 — AWS 가 여기서 JWKS 를 읽는다)의 터널 설정과 DNS 를 k8s 매니페스트로 옮겨도 부트스트랩이 서는가.
둘째는 실측으로 닫혔고(§2-3 · §3-3 · §3-4), 첫째가 이 문서의 열린 축이다.

## 2. 실측

### 2-1. Gateway 와 라우트의 현재 배치

- NGF 2.2.1. Gateway 셋 — `internal-nginx-gateway`(VIP .2, `*.mg`) · `agent-nginx-gateway`(VIP .4, `obs.mg`) 는 `nginx-gateway` ns, `careerhub-nginx-gateway`(VIP .3) 는 `careerhub-prod` ns.
  Gateway 마다 nginx Deployment 가 따로 뜬다.
- HTTPRoute 는 백엔드와 같은 네임스페이스에 살고 플랫폼 Gateway 에 네임스페이스를 넘어 붙는다 — `argocd` · `kagent` · `prometheus` 의 라우트가 `nginx-gateway/internal-nginx-gateway` 에 붙어 있다. ReferenceGrant 는 클러스터에 하나도 없다. 리스너가 `allowedRoutes.namespaces.from: All` 이라 필요 없었다.
- `careerhub-httproute` 는 `parentRefs[0].sectionName: https` 로 HTTPS 리스너에만 붙는다. HTTP 리스너에는 `http-to-https-redirect`(301)만 있다.
- NginxProxy 넷 어디에도 `rewriteClientIP` 가 없다. `externalTrafficPolicy: Cluster` 라 LAN 게이트웨이도 노드 간 SNAT 뒤의 주소를 본다.
- CRD: `backendtlspolicies` · `referencegrants` 있음, `tlsroutes` 없음(experimental 채널).
- `ObservabilityPolicy careerhub-trace` 는 HTTPRoute(`careerhub-httproute`)를 겨냥한다. NginxProxy 의 `telemetry.exporter` 는 Gateway 단위다.

### 2-2. 터널과 DNS 의 현재 소유

- `jyoliar-platform-terraform/cloudflare/tunnel.tf`: 터널 `k8s-oidc`(`config_src = "cloudflare"`) · 원격 ingress(`k8s-oidc.jyo-liar.com` → `http://oidc-server.oidc-provider.svc.cluster.local:8080`, catch-all 404) · CNAME `k8s-oidc` → `<UUID>.cfargotunnel.com`(proxied).
  토큰은 `outputs.tf` 의 `tunnel_token` 출력이다.
- 클러스터의 cloudflared(`cloudflare-system`, 2 replica)는 `TUNNEL_TOKEN` 을 Secret `cloudflare-tunnel-token` 에서 받는다.
  그 Secret 을 만드는 ExternalSecret 은 없다. ansible(onpremise-k8s)에도 없다 — 부트스트랩 때 손으로 넣는 seed 다.
- terraform provider 5.18.0 의 `config_src` 는 `RequiresReplaceIfConfigured` — 값을 바꾸면 터널이 재생성되어 UUID 가 바뀐다. `tunnel_secret` 은 재생성을 강제하지 않는다.

### 2-3. 부트스트랩 사슬 — 무엇이 무엇을 기다리나

```
수동 seed: ArgoCD repo ssh key · cloudflare-tunnel-token
  → bootstrap phase 1: argocd · cloudflared · oidc-provider
  → 터널 연결 → k8s-oidc.jyo-liar.com 응답
  → AWS STS 가 IRSA 토큰 검증 시 discovery · JWKS 를 읽는다
  → ESO 가 SSM 을 읽는다 → phase 2(ClusterSecretStore · repo-creds)
  → controllers(nginx-gateway · external-dns · cert-manager …) → system → services
```

- `iam/oidc.tf` 의 AWS OIDC provider 는 호스트명과 Cloudflare 엣지 인증서 지문에 기댄다. 터널 UUID · ingress 의 위치와 무관하다.
- NGF 와 external-dns 는 controllers 단계 — ESO 뒤다.
  k8s-oidc 트래픽이 NGF 를 지나면 재구축 때 NGF 가 뜨기 전엔 ESO 가 못 뜨고, NGF 설치는 ESO 뒤다 — 순환.
  k8s-oidc CNAME 을 external-dns 가 소유하면 클러스터가 없을 때 레코드를 만들 주체가 없다. `policy: sync` 라 해체 중 HTTPRoute 가 사라지면 레코드도 사라진다.
- k8s-oidc CNAME 의 값은 터널 UUID — 클러스터 주소가 아니라 terraform 자신의 데이터다. ADR-0034 가 이관 대상으로 든 "클러스터 서비스의 DNS record"(VIP 를 가리키는 것)와 다르다.
  반면 ingress 는 `oidc-server.oidc-provider.svc` 라는 클러스터 주소를 들고 있어 그쪽이 이관 대상이다.

### 2-4. 조사가 준 제약(→ 261026_1631)

- external-dns 의 `target` 애노테이션은 Gateway 단위, `cloudflare-proxied` 는 Route 단위.
- cloudflared 는 terraform 이 정체성·비밀(`config_src=local` · `tunnel_secret`)만 들고 ingress 는 origin 쪽 YAML(`config.yml`, 첫 매치 우선, catch-all 필수)이 드는 조합을 지원한다.
- BackendTLSPolicy 는 CA 를 Secret 으로 받는다. TLS passthrough 는 TLSRoute(없음)가 필요하다.

### 2-5. 홉 지연 — nginx 홉 하나는 1~2ms 다

지금 `careerhub-nginx-gateway` 를 지나 api-composer 에 닿은 트레이스 다섯 건(2026-10-26 06:54~06:55Z, Tempo)에서 게이트웨이 루트 span 과 api-composer 서버 span 의 차이를 읽었다.
그 차이가 nginx 홉 하나의 비용(프록시 처리 + 업스트림 연결)이다.

| 트레이스 | 경로 | 게이트웨이 span | api-composer span | 홉 비용 | 업스트림 시작 오프셋 |
|---|---|---|---|---|---|
| `59405d5d…` | `/api/job_postings/{site}/{postingId}` | 25.0ms | 23.4ms | 1.6ms | +1.5ms |
| `1eb73c26…` | 같은 경로 | 15.0ms | 13.9ms | 1.1ms | +1.2ms |
| `45f6dd27…` | `/api/skills` | 19.0ms | 17.7ms | 1.3ms | +2.1ms |
| `93c36c30…` | `/api/my/scrap-job` | 9.0ms | 7.6ms | 1.4ms | +1.2ms |
| `d4c2aee5…` | `/api/categories` | 3.0ms | 0.9ms | 2.1ms | +2.0ms |

홉 하나가 1~2ms 이고, 대부분이 업스트림 span 이 시작되기 전(연결 수립)에 든다.
두 단이면 2~4ms 가 더해진다.
Cloudflare 엣지(icn)에서 홈랩까지의 왕복이 그보다 한 자리 크므로, 홉 수는 방문자가 느끼는 지연을 가르지 않는다.
표본은 LAN 에서 보낸 요청이고 트래픽이 거의 없는 시각이라 부하 아래의 값은 아니다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 터널의 수

**선택: 하나 — 기존 `k8s-oidc` 터널을 공개 터널로 쓴다.** 공개 엔드포인트는 터널 하나로 전부 관리한다는 전제. 261026_1632 §3-4(새 터널)를 뒤집는다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- careerhub 전용 새 터널 + cloudflared 한 벌 더 — 자격증명 격리는 터널을 공유해도 cloudflared 와 자격증명을 cloudflare-system 에만 두면 얻어진다. 남는 이익(운영 격리 · 걷어내기)이 터널 둘의 비용을 넘지 않는다

</details>

### 3-2. 공개 Gateway 의 자리

**선택: careerhub-prod 안에 careerhub 전용 공개 Gateway(`careerhub-public-gateway`, ClusterIP · HTTP 리스너만).** cloudflared ingress 가 `careerhub.jyo-liar.com` 을 이 Gateway 의 Service 로 직결한다. external-dns `target` 애노테이션(`<UUID>.cfargotunnel.com`)은 이 Gateway 에, `cloudflare-proxied` 는 `careerhub-httproute` 에. 사설 `careerhub-nginx-gateway` 는 `id.careerhub` 만 남긴 채 그대로다. (인터뷰, 2026-10-26. 처음 플랫폼 부품으로 잡았다가 바꿨다 — 공개 서비스가 careerhub 뿐이라 공유 부품이 비어 있다)

<details><summary>버린 안</summary>

- `nginx-gateway` ns 의 플랫폼 공개 Gateway — 여러 공개 호스트를 한 Gateway 로 받는 모양. k8s-oidc 가 직결(3-3)이라 지금 받을 호스트는 careerhub 하나뿐이다. 공개 서비스가 둘 이상이 될 때 다시 연다
- 기존 `careerhub-nginx-gateway` 에 `target` 애노테이션 — `id.careerhub` 까지 터널 CNAME 이 된다(261026_1632 §4-1 B)

</details>

### 3-3. k8s-oidc 의 경로

**선택: cloudflared ingress 직결 유지.** `config.yml` 에 `k8s-oidc.jyo-liar.com → http://oidc-server.oidc-provider.svc.cluster.local:8080` 한 줄. NGF 가 부트스트랩 임계 경로에 들어오지 않는다. 3-2 와 합치면 ingress 는 호스트별 두 줄(k8s-oidc · careerhub)과 catch-all 404 다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 공개 Gateway 경유 — 재구축 순환(§2-3). 수동 절차로 풀 수는 있으나 부트스트랩 경로에 부품을 더할 이유가 없다

</details>

### 3-4. k8s-oidc CNAME 의 자리

**선택: terraform 에 남긴다 — seed.** 값이 터널 UUID 라 terraform 데이터이고, 클러스터가 서기 전에 있어야 한다(§2-3). ingress 만 GitOps 로 간다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- external-dns 이관 — HTTPRoute 또는 DNSEndpoint 가 필요하고, 해체 → 재구축에서 레코드가 비는 창이 생긴다. 수동 복구 절차를 문서화해야 성립한다

</details>

### 3-5. 클러스터 안 홉의 암호화

**선택: 평문 허용 — 설정이 가장 적은 쪽.** cloudflared → careerhub 공개 Gateway 는 `http://careerhub-public-gateway-nginx.careerhub-prod.svc.cluster.local:80`, 공개 Gateway 는 HTTP 리스너만 두고 인증서를 들지 않는다. 방문자 쪽 TLS 는 Cloudflare 가 한다. 261026_1632 §4-2(HTTPS 443 + originServerName)를 뒤집는다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 홉마다 TLS — 공개 호스트마다 리스너 · 인증서(careerhub 인증서는 네임스페이스가 달라 ReferenceGrant 또는 재발급, k8s-oidc 용은 새로), 2단이면 BackendTLSPolicy 와 CA Secret 까지. "호스트 추가 = HTTPRoute 하나" 가 깨진다
- TLS passthrough — TLSRoute CRD 가 없고 experimental 채널은 들이지 않는다

</details>

### 3-6. 터널 설정의 이관

**선택: 원격 관리 → 로컬 관리.** terraform 은 `config_src = "local"` + `tunnel_secret`(`random_bytes` 32바이트를 state 에 두고 넘긴다 — 대체돼도 값이 고정이다)으로 정체성·비밀만, ingress 는 `cloudflare-system` 의 ConfigMap `config.yml`. cloudflared 는 토큰 대신 자격증명 JSON(`AccountTag` · `TunnelID` · `TunnelSecret`)으로 돈다. 자격증명의 전달은 지금과 같은 한 길 — terraform 출력을 `platform/overlays/create-tunnel-token.sh` 가 Secret 으로 넣는다. 스크립트는 토큰 한 줄 대신 JSON 파일을 받도록만 바뀐다. SSM · ExternalSecret 은 두지 않는다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- SSM + ExternalSecret 으로 자동화 — 부트스트랩 때는 어차피 손이고, 수동 Secret 과 ExternalSecret 의 소유권이 겹치며, phase 1 앱에 ESO 의존 리소스가 들어가 재구축 때 Degraded 로 보인다

</details>

전환 절차와 공백:
`config_src` 변경은 터널 재생성이다 — UUID 가 바뀌고 CNAME 은 terraform 이 같이 바꾼다.
새 자격증명으로 cloudflared 를 다시 띄울 때까지 k8s-oidc 가 끊긴다.
ESO · ECR pull 은 토큰 갱신 시점에만 OIDC 를 부르므로 몇 분의 공백은 흡수된다 — 갱신 주기(ESO `refreshInterval: 1h`)와 겹치지 않게 시간을 잡는다.
공개 Gateway 의 `target` 애노테이션은 새 UUID 로 적는다.

## 4. 열린 축 — 논의

### 4-1. careerhub 라우팅 — 한 단인가 두 단인가

실측: Gateway API 에서 경로 규칙은 HTTPRoute 의 것이고 HTTPRoute 는 앱 네임스페이스가 소유한다.
공개 Gateway 가 HTTP 리스너만 두면 호스트명도 인증서도 Gateway 쪽 변경이 아니다 — 한 단에서도 careerhub 의 경로가 바뀔 때 플랫폼 리소스는 바뀌지 않는다.
두 단의 추가 홉 비용은 1~2ms 다(§2-5) — 방문자 지연을 가르는 크기가 아니다.

- **A. 한 단 — 공개 Gateway 가 careerhub 서비스로 직접.** `careerhub-httproute`(careerhub-prod)의 `parentRefs` 를 `nginx-gateway/public-nginx-gateway` 로 바꾸고 `/auth` 룰을 지운다. 백엔드는 같은 네임스페이스의 Service 라 ReferenceGrant 가 없다. 방문자 IP 복원은 공개 Gateway 한 곳. 사설 `careerhub-nginx-gateway` 에는 `id.careerhub` 만 남는다. **이기는 조건:** 플랫폼과 앱의 분리를 Gateway API 의 소유 모델(Gateway 는 플랫폼, HTTPRoute 는 앱)이 이미 주고 있다고 볼 때. nginx 홉이 하나뿐이다. **지는 조건:** 같은 호스트를 LAN VIP 와 터널 두 입구에서 같은 라우트로 받고 싶을 때 — 한 HTTPRoute 는 여러 parentRef 를 가질 수 있어 이것도 가능하지만, 그 순간 라우트가 두 Gateway 에 걸친다.
- **B. 두 단 — 기존 `careerhub-nginx-gateway` 에 호스트 단위로 넘긴다.** 공개 Gateway 에는 careerhub-prod 가 소유한 HTTPRoute 하나(`hostnames: [careerhub.jyo-liar.com]`, 규칙 `/` → Service `careerhub-nginx-gateway-nginx:80`). 기존 `careerhub-httproute` 는 그대로 사설 Gateway 에 남되 HTTP 리스너에도 붙여야 한다(`sectionName: https` 제거) 그리고 `http-to-https-redirect` 에서 careerhub 호스트를 뺀다. 방문자 IP 는 공개 Gateway 에서 복원하고, careerhub Gateway 도 `rewriteClientIP` 로 공개 Gateway 파드를 신뢰해야 한 번 더 복원된다. **이기는 조건:** careerhub 의 모든 입구(LAN VIP · 터널)가 한 라우트 집합을 쓰길 바랄 때. 컷오버 · dev 등 careerhub 쪽 변경이 careerhub Gateway 안에서 끝난다. **지는 조건:** nginx 홉이 둘이고, Zitadel 과 같은 Gateway 를 지나 공개 트래픽이 사설 VIP Gateway 의 nginx 를 쓴다. `rewriteClientIP` 설정이 두 곳.
- C. 두 단 — careerhub-prod 에 공개 전용 careerhub Gateway(ClusterIP · HTTP) 를 하나 더 두고 거기로 넘긴다. B 에서 Zitadel · LAN 과의 공유를 끊은 모양. **이기는 조건:** B 의 분리를 원하면서 사설 VIP Gateway 를 공개 트래픽에서 떼고 싶을 때. **지는 조건:** careerhub-prod 에 Gateway 가 둘, nginx 가 셋(공개 · careerhub 공개 · careerhub 사설). 한 단 대비 얻는 것이 "careerhub 라우트의 parentRef 가 careerhub 안에 있다" 뿐이다.
- D. 안 한다 — Gateway 없이 cloudflared ingress 가 호스트마다 서비스로 직결. careerhub 는 경로 분기가 필요해 성립하지 않는다.
- **E. 플랫폼 공개 Gateway 를 두지 않는다 — cloudflared ingress 가 호스트별로 가르고, careerhub 는 careerhub-prod 의 공개 전용 Gateway(ClusterIP · HTTP)가 받는다.** `careerhub-httproute` 의 `parentRefs` 를 그 Gateway 로, `/auth` 룰 제거. nginx 홉 하나. 공개 호스트 추가 = cloudflare-system ConfigMap 한 줄 + 그 앱의 Gateway 또는 라우트. **이기는 조건:** 공개 서비스가 careerhub 하나뿐일 때 — 지금. A 와 같은 홉 수이면서 nginx-gateway ns 에 쓰임새 없는 부품을 두지 않는다. **지는 조건:** 공개 서비스가 둘 이상이 되면 ConfigMap 수정이 반복되고 Gateway 가 앱마다 생긴다 — 그때 A 로 옮긴다.

**판정(사람, 2026-10-26): E. 플랫폼 공개 Gateway 없이, cloudflared → careerhub 공개 Gateway 직결. 한 단·두 단 질문은 소멸 — 공개 서비스가 늘면 다시 연다.**

### 4-2. 방문자 IP 복원의 위치

실측: `rewriteClientIP` 는 TLS Terminate 리스너에만 적용된다고 문서가 적는다 — HTTP 리스너에서의 동작은 실측 항목이다. 신뢰 범위는 파드 CIDR `10.244.0.0/16`.

- **A. 공개 Gateway 한 곳.** 한 단이면 이것으로 끝. 두 단이면 careerhub Gateway 의 로그에는 공개 Gateway 파드 주소가 남는다. **이기는 조건:** 4-1 A.
- B. 두 곳 — 공개 Gateway 와 careerhub Gateway 모두. 두 단에서 careerhub Gateway 의 로그 · 트레이스에도 방문자 IP 가 남는다. **이기는 조건:** 4-1 B/C 이고 careerhub 쪽 nginx 로그를 agent 가 읽을 때.
- C. 안 한다 — 방문자 IP 는 Cloudflare 대시보드에서만. 261026_1632 §4-6 이 이미 "남긴다" 로 판정했으므로 지는 안이다.

HTTP 리스너에서 `rewriteClientIP` 가 듣지 않으면 공개 Gateway 를 HTTPS 리스너로 되돌려야 하고, 그때 3-5 가 다시 열린다.

**판정(사람, 2026-10-26): A. careerhub 공개 Gateway 한 곳.**

## 5. 반대편 — 이 설계가 틀리는 조건

- `rewriteClientIP` 가 HTTP 리스너에서 동작하지 않으면 3-5(평문) 와 4-2 가 충돌한다. 실측 하나로 갈린다.
- cloudflared 와 공개 Gateway 가 전부 클러스터 DNS 에 기댄다(#80). CoreDNS 장애가 공개면 전체를 끊는다 — 터널 분리로는 어차피 안 풀리던 문제다.
- 터널 하나를 공유하므로 careerhub 쪽 ingress 를 고칠 때 cloudflared 롤링이 k8s-oidc 경로도 지난다. 2 replica 라 끊기진 않지만 설정 오류(catch-all 누락 · YAML 깨짐)는 둘을 함께 죽인다 — `cloudflared tunnel ingress validate` 를 CI 또는 커밋 전 절차에 둔다.
- 터널 재생성(3-6) 중 AWS 가 JWKS 를 읽지 못하는 창에 ESO 갱신이 겹치면 Secret 갱신이 한 주기 밀린다. 기존 Secret 은 남는다.
- 외부 DNS 에 사설 VIP 가 그대로 공개돼 있다(`careerhub` · `id.careerhub` · `*.mg`). 이 논의는 그것을 바꾸지 않는다.

## 6. 버린 것

- **"터널을 나누면 격리된다"는 틀.** 격리는 자격증명과 cloudflared 가 어느 네임스페이스에 사느냐에서 나왔다. 터널을 공유해도 careerhub-prod 에는 아무것도 주지 않으면 같은 격리다.
- **k8s-oidc 를 다른 공개 호스트와 같은 길로 보내는 것.** 부트스트랩 임계 경로의 부품 수를 늘린다(§2-3). 균일함보다 재구축 가능성이 앞선다.
- **CNAME 까지 전부 GitOps 로.** ADR-0034 의 seed 정의("클러스터가 서기 전에 존재해야 하는 재료")에 정확히 해당하는 것을 옮기면 재구축 순환이 생긴다.
- **플랫폼 공개 Gateway 를 미리 두는 것.** "공개 호스트 추가 = HTTPRoute 하나" 는 공개 서비스가 여럿일 때의 이득이다. 지금은 careerhub 하나이고, k8s-oidc 는 어차피 직결이다. 둘째 공개 서비스가 생길 때 옮겨도 늦지 않다 — 그때의 변경은 ingress 한 줄과 parentRef 하나다.

## 7. 임계선 — ADR감인가

아니다.
Gateway 하나 · ConfigMap 하나 · HTTPRoute 의 parentRef · terraform 리소스의 속성 하나다. 되돌리기는 revert 이고 영향은 공개면뿐이다.
단 두 가지는 ADR-0034 의 적용 사례로 남는다 — 터널 ingress 는 이관하고 CNAME 은 seed 로 남긴 판정. ADR-0034 가 accept 될 때 Consequences 의 경계(어디까지가 seed 인가)를 이 사례가 시험한다.

## 8. 다음

- digest(261026_1715)를 고쳐 쓴다 — 터널 공유와 재생성 단계 · careerhub 공개 Gateway 가 HTTP 만 · cloudflared 는 cloudflare-system 한 벌.
- 실측 하나를 전환 전에 닫는다 — HTTP 리스너에서의 `rewriteClientIP` 동작.
- 티켓은 사람이 시점을 정한다. 모양은 terraform(터널 로컬 관리 전환 · 자격증명 출력 · 엣지 보호 리소스) · jyoliar-k8s(cloudflare-system 의 ConfigMap · cloudflared 실행 인자 · 자격증명 스크립트, careerhub-prod 의 공개 Gateway · careerhub 라우트 · frontend 태그) · careerhub-front(/login 안내).
- 공개 서비스가 둘 이상이 되면 3-2 · 4-1 을 다시 연다 — 플랫폼 공개 Gateway 로 옮기는 논의.
