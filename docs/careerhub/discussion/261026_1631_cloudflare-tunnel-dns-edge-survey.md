---
type: discussion
kind: survey
goal: legacy-public-exposure
topic: careerhub
subjects: [cloudflare-tunnel, cloudflared, external-dns, nginx-gateway-fabric, jyoliar-platform-terraform]
status: done
related:
  - docs/careerhub/discussion/261026_1632_cloudflare-exposure-wiring-and-edge.md
---

# Cloudflare Tunnel · external-dns · 엣지 보호 — 조사 (2026-10-26)

## 질문

논의 문서(261026_1632)의 네 축이 사실을 요구했다.
① external-dns(gateway-httproute 소스, v0.20.0)가 HTTPRoute 호스트명을 터널 CNAME(프록시)으로 낼 수 있는가, 그 선언은 어느 리소스에 붙는가.
② cloudflared의 설정을 클러스터 매니페스트에 둘 수 있는가(로컬 관리) — terraform 리소스와 어떻게 나뉘는가, origin TLS 옵션은 무엇인가.
③ Cloudflare Free 플랜에서 쓸 수 있는 엣지 보호(WAF · 레이트리밋 · 봇 · AI 크롤러 · 헤더 변환)의 한도는 무엇이고, 검색엔진 봇은 어떻게 다뤄지는가.
④ NGF(nginx-gateway-fabric)에서 Gateway를 하나 더 두는 비용과 ClusterIP 노출, 프록시 뒤 클라이언트 IP 복원 수단.

조사일은 전부 2026-10-26 이다.

## 조사

### 1. external-dns — 호스트명은 Route, target은 Gateway

출처: https://kubernetes-sigs.github.io/external-dns/v0.20.0/docs/sources/gateway/ · https://kubernetes-sigs.github.io/external-dns/latest/docs/annotations/annotations/ · https://kubernetes-sigs.github.io/external-dns/latest/docs/tutorials/cloudflare/

- **target 애노테이션은 Gateway에서 읽는다.** v0.20.0 문서: *"If a matching parent Gateway has an `external-dns.alpha.kubernetes.io/target` annotation, uses the values from that. Otherwise, iterates over that parent Gateway's `status.addresses`."*
  최신 문서도 같다: *"Gateway resource reads only `target` annotation,"* Route는 *"read all other annotations."*
  → HTTPRoute 단위로 target을 바꿀 수 없다. 같은 Gateway에 붙은 모든 Route가 같은 target을 받는다.
- **target 값이 IP가 아니면 CNAME이 된다.** *"Specifies a comma-separated list of values to override the resource's DNS record targets (RDATA)."* IPv4는 A, IPv6는 AAAA, 그 밖은 CNAME.
- **프록시 여부는 Route 단위 애노테이션이다.** Cloudflare 튜토리얼: `cloudflare-proxied: "true"` 애노테이션은 *"This setting will override the global `--cloudflare-proxied` setting."* 프록시 레코드의 TTL은 *"set the TTL annotation to 1 (automatic), or do not set it."*
- **접두사.** v0.22.0 전은 `external-dns.alpha.kubernetes.io/`, 이후 기본은 `external-dns.kubernetes.io/`. 배포본은 v0.20.0 이므로 alpha 접두사다.
- **리소스 제외.** `controller` 애노테이션: *"If this annotation exists and has a value other than `dns-controller` then the source ignores the resource."*
- **문서가 말하지 않는 것.** 같은 이름의 소유 레코드가 A→CNAME 으로 타입이 바뀔 때의 적용 순서(생성이 삭제보다 먼저면 Cloudflare 가 CNAME 충돌로 거부한다). 실측 항목이다.

### 2. cloudflared — 원격 관리와 로컬 관리, origin 옵션

출처: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/local-management/ · …/local-management/configuration-file/ · …/get-started/create-local-tunnel/ · …/configure-tunnels/remote-management/ · …/cloudflared-parameters/origin-parameters/ · https://raw.githubusercontent.com/cloudflare/terraform-provider-cloudflare/v5.18.0/docs/resources/zero_trust_tunnel_cloudflared.md

- **원격 관리.** *"store their configuration on Cloudflare,"* 대시보드·API·Terraform 으로 관리. 토큰은 *"For remotely-managed tunnels only"* 이고 `TUNNEL_TOKEN` 으로 준다. 현재 k8s-oidc 터널이 이 형태다(`tunnel.tf` `config_src = "cloudflare"`).
- **로컬 관리.** `cloudflared tunnel create <NAME>` 이 UUID 와 자격증명 JSON(`~/.cloudflared/<UUID>.json`)을 만든다. 설정은 YAML — *"Configuration files that contain ingress rules must always include a catch-all rule that concludes the file."* 실행은 `cloudflared tunnel --config <file> run <UUID>`. 문서는 이것을 *"local development, testing, or legacy configurations"* 용으로 적는다.
- **terraform 쪽.** `config_src`: *"If `local`, manage the tunnel using a YAML file on the origin machine."* `tunnel_secret`: *"Must be at least 32 bytes and encoded as a base64 string."* 즉 terraform 이 터널 정체성과 비밀만 만들고 ingress 는 origin 쪽 YAML 이 드는 조합이 공식 지원된다.
- **ingress 규칙.** `hostname` · `service`(`https://…`, `http_status:404` 등) · `originRequest`. 규칙 단위 `originRequest` 가 전역을 덮는다.
- **origin TLS 옵션.** `originServerName`: *"Hostname that `cloudflared` should expect from your origin server certificate."* 비우면 service URL 의 호스트명을 쓴다. `noTLSVerify`: *"When `true`, TLS verification is disabled."* `http2Origin`: HTTPS origin 에만 적용. `httpHostHeader`: origin 으로 보내는 Host 헤더 지정.
- **문서가 말하지 않는 것.** 자격증명 JSON 의 필드명, 원격 관리 터널에서 로컬 ingress 가 무시되는지 여부. 두 방식을 섞지 않으면 문제가 안 된다.

### 3. Cloudflare Free 플랜의 엣지 보호

출처: https://developers.cloudflare.com/waf/managed-rules/ · https://developers.cloudflare.com/waf/rate-limiting-rules/ · https://developers.cloudflare.com/bots/get-started/bot-fight-mode/ · https://developers.cloudflare.com/use-cases/solutions/stop-malicious-bots/ · https://developers.cloudflare.com/bots/additional-configurations/block-ai-bots/ · https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/ · https://developers.cloudflare.com/rules/transform/ · https://developers.cloudflare.com/ssl/edge-certificates/universal-ssl/limitations/

| 기능 | Free | 비고 |
|---|---|---|
| WAF 관리형 룰셋 | Cloudflare Free Managed Ruleset — *"Available on all Cloudflare plans … high-impact and widely exploited vulnerabilities"* | Cloudflare Managed Ruleset · OWASP 는 Pro 부터 |
| 레이트리밋 | 규칙 1개 · 집계 10초 · 완화 10초 · 특성 IP 만 | 문서가 Free 의 액션 종류를 적지 않는다 |
| Bot Fight Mode | *"included with Free plans"* | *"Cannot be bypassed with custom rule Skip actions"* · *"may challenge API or mobile app traffic"* · JS Detections 강제 |
| 검증 봇 허용 | Super Bot Fight Mode(Pro+)의 것 — *"adds verified bot allowlisting"* | Free 에서는 BFM 을 끄거나 업그레이드가 선택지 |
| AI 봇 차단 | Search · Agent · Training 세 분류별 Block / Block on pages with ads / Allow | 2026-09-15 부터 신규 도메인은 Training·Agent 가 광고 페이지에서 기본 차단 |
| 관리형 robots.txt | *"available on all plans"* — AI 정책이 Block 이면 Cloudflare 가 robots.txt 앞에 관리 지시문을 붙인다 | AI 크롤러 전용. 전체 크롤러 차단은 못 한다 |
| Transform Rules | 활성 규칙 10개 | 응답 헤더를 리터럴로 설정 가능 — `X-Robots-Tag` 는 제한 목록에 없다 |
| Universal SSL | apex 와 1단 서브도메인만 | `id.careerhub.jyo-liar.com` 같은 2단은 ACM(Total TLS) 또는 커스텀 인증서 |
| 터널 | 기존 k8s-oidc 터널이 같은 계정에서 돌고 있다 | 이 계정의 플랜에서 터널이 성립함은 실측이다 |

Bot Fight Mode 와 검색 봇에 관해 공식 문서는 침묵한다.
제3자 사례 하나(https://daily.dev/posts/how-cloudflare-bot-fight-mode-quietly-killed-our-google-rankings-lbdhmurms)는 Free 의 BFM 이 Googlebot 에 챌린지 페이지(noindex)를 내보내 색인이 붕괴했다고 적는다.
공식 문서의 *"may challenge API or mobile app traffic"* 과 *"Cannot be bypassed with … Skip"* 을 합치면, 색인을 허용하면서 BFM 을 켜는 조합은 Free 에서 안전하지 않다.

### 4. NGF — Gateway 당 데이터플레인, ClusterIP, 클라이언트 IP

출처: https://docs.nginx.com/nginx-gateway-fabric/overview/gateway-architecture/ · https://docs.nginx.com/nginx-gateway-fabric/how-to/data-plane-configuration/

- *"Each Gateway resource corresponds uniquely to a dedicated data plane deployment"* — *"the control plane automatically provisions a dedicated NGINX Deployment and exposes it using a Service."*
  Gateway 를 하나 더 두면 nginx Deployment 와 Service 가 하나 더 생긴다.
- NginxProxy 는 Gateway 의 `infrastructure.parametersRef` 로 Gateway 단위 부착이 가능하고, *"service types, load balancer settings, and PodDisruptionBudgets"* 를 정한다. 같은 네임스페이스여야 한다.
  careerhub 의 현행 NginxProxy 는 `type: LoadBalancer`(kube-vip)다. ClusterIP 로 두면 LAN 주소 없이 터널에서만 닿는 게이트웨이가 된다.
- `rewriteClientIP`: 모드 `ProxyProtocol` · `XForwardedFor`, `trustedAddresses`(CIDR · IP · 호스트명), `setIPRecursively`. *"apply only to TLS `Terminate` listeners."*

## 논의 문서로 가져가는 것

- external-dns 의 target 은 Gateway 단위다. careerhub Gateway 에 붙이면 `id.careerhub`(zitadel 라우트, 같은 Gateway)도 터널 CNAME 이 된다.
- 프록시 여부는 Route 단위, 접두사는 `external-dns.alpha.kubernetes.io/`(v0.20.0).
- A→CNAME 타입 교체의 적용 순서는 문서에 없다 — 실측 또는 2단계 절차.
- cloudflared 는 terraform 이 정체성·비밀(`config_src=local` · `tunnel_secret`)만 들고 ingress 는 origin YAML 이 드는 조합을 지원한다. 원격 관리는 토큰 + Cloudflare 측 설정이다.
- origin 은 `https://` + `originServerName` 으로 LE 인증서를 그대로 검증할 수 있다. `noTLSVerify` 가 필요 없다.
- Free: 관리형 룰셋(무료판) · 레이트리밋 1개(IP · 10초) · BFM(검증 봇 예외 불가 · API 호출 챌린지 가능) · AI 봇 분류별 차단 · 관리형 robots.txt(AI 한정) · Transform 10개 · Universal SSL 은 1단까지.
- 검증 봇 허용은 Pro(SBFM)의 것이다. 색인 허용과 BFM 은 Free 에서 양립하지 않는다.
- NGF 는 Gateway 당 nginx 데이터플레인 하나다. ClusterIP Gateway 가 가능하고, `rewriteClientIP` 로 XFF 를 신뢰 범위 안에서 복원한다.
