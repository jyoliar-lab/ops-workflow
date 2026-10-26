---
type: digest
goal: legacy-public-exposure
topic: careerhub
subjects: [careerhub-front, auth-service, api-composer, careerhub-httproute, careerhub-nginx-gateway, cloudflare-tunnel, cloudflared, external-dns, nginx-gateway-fabric, jyoliar-platform-terraform, oidc-provider, zitadel]
status: current
ref-adrs: [ADR-0028, ADR-0034]
sources:
  - docs/careerhub/discussion/261026_1610_legacy-public-exposure-auth-disposition.md
  - docs/careerhub/discussion/261026_1631_cloudflare-tunnel-dns-edge-survey.md
  - docs/careerhub/discussion/261026_1632_cloudflare-exposure-wiring-and-edge.md
  - docs/careerhub/discussion/261026_1811_public-gateway-topology-and-tunnel-handoff.md
superseded_by:
---

# 레거시 커리어허브의 임시 공개 — 설계와 전환 순서 (2026-10-26 시점)

## 개요

리뉴얼이 끝나기 전 3~6개월 동안, 지금 배포된 레거시 스택(careerhub-front v0.0.3 · api-composer v0.4.0 · auth-service v0.2.1)을 `careerhub.jyo-liar.com` 으로 공개 인터넷에 내놓는다.
목적은 포트폴리오 링크다 — 채용 담당자가 링크를 열어 채용공고와 회사 리뷰를 둘러볼 수 있으면 된다.
로그인·가입은 제공하지 않는다.
트래픽은 홈랩의 유일한 Cloudflare Tunnel(지금 k8s-oidc 가 쓰는 그 터널)로 들어오고, 터널의 ingress 설정은 terraform 에서 GitOps 로 옮겨 온다.
careerhub 는 자기 네임스페이스 안의 공개 전용 NGF Gateway 로 받고, 홈랩의 공인 IP 와 사설 게이트웨이는 밖에서 보이지 않는다.
게이트웨이에 없는 보호(레이트리밋 · WAF · 봇)는 Cloudflare 가 맡는다.

이 문서는 사례 하나로 설계를 관통한다 — **채용 담당자 K 가 이력서의 링크를 연다.**

## 어휘

- **공개 터널** — 홈랩의 Cloudflare Tunnel 하나. terraform 이 정체성과 비밀을 만들고, ingress 는 클러스터의 ConfigMap 이 든다(로컬 관리). k8s-oidc 와 careerhub 가 같이 탄다.
- **careerhub 공개 Gateway** — careerhub-prod 에 새로 두는 NGF Gateway(`careerhub-public-gateway`). ClusterIP 뿐이고 HTTP 리스너만 있어 인증서가 없다. 터널을 통해서만 닿는다.
- **사설 Gateway** — 지금 있는 `careerhub-nginx-gateway`(VIP 10.18.100.3). Zitadel 호스트(`id.careerhub`)가 계속 여기 산다.
- **레거시 스택** — 위 세 이미지와 그 Deployment. 이 설계는 이들의 코드를 바꾸지 않는다(프론트의 화면 하나만 예외).

## 구성 — 끝난 뒤의 모습

```
K 의 브라우저
  │ https://careerhub.jyo-liar.com   (DNS: 프록시 CNAME → <터널 UUID>.cfargotunnel.com — external-dns 가 HTTPRoute 에서 파생)
  ▼
Cloudflare 엣지  ── Universal SSL · 무료 관리형 WAF · 레이트리밋(/api/*) · AI 크롤러 차단 · Always HTTPS/HSTS
  │ 공개 터널(아웃바운드 연결)
  ▼
cloudflared (cloudflare-system · 2 replica · 자격증명 JSON 은 사람이 스크립트로 넣은 Secret)
  │ ingress (ConfigMap config.yml):
  │   k8s-oidc.jyo-liar.com   → http://oidc-server.oidc-provider.svc.cluster.local:8080      ← 지금과 같다
  │   careerhub.jyo-liar.com  → http://careerhub-public-gateway-nginx.careerhub-prod.svc.cluster.local:80
  │   (그 밖)                 → http_status:404
  ▼
careerhub 공개 Gateway (NGF · ClusterIP · HTTP 리스너 · rewriteClientIP 로 방문자 IP 복원 · OTel → alloy)
  │ careerhub-httproute:  /  → frontend     /api → api-composer      (/auth 룰 없음)
  ▼
frontend v0.0.4 (/login 은 "리뉴얼 중" 안내)   ·   api-composer v0.4.0   ·   gRPC 서비스들
```

사설 Gateway 와 `id.careerhub.jyo-liar.com`(Zitadel)은 지금 그대로다 — A 레코드는 사설 VIP 를 가리키고, 터널 ingress 에 없으며, 밖에서 닿지 않는다.
auth-service Deployment 는 계속 돌지만 어느 Gateway 에서도 라우팅되지 않는다.
`k8s-oidc.jyo-liar.com` 의 CNAME 은 terraform 이 계속 든다 — 값이 터널 UUID 라 클러스터가 서기 전에 있어야 하는 seed 다.

선언의 자리는 넷으로 나뉜다.

| 무엇 | 어디 | 모양 |
|---|---|---|
| 공개 터널의 정체성과 비밀 · k8s-oidc CNAME | terraform `cloudflare/` | `cloudflare_zero_trust_tunnel_cloudflared`(`config_src = "local"`, `tunnel_secret` = state 의 `random_bytes`) · 자격증명 JSON 을 출력으로 · `cloudflare_dns_record` k8s-oidc |
| 자격증명 Secret | 사람 — `platform/overlays/create-tunnel-token.sh` | terraform 출력의 JSON 파일을 `cloudflare-system` 의 Secret 으로. 부트스트랩 seed 이고 비밀을 회전할 때만 다시 넣는다 |
| 터널 ingress · cloudflared | jyoliar-k8s `cloudflare-system`(bootstrap phase 1) | ConfigMap `config.yml` · Deployment(`cloudflared tunnel --config … run <UUID>`, 자격증명 파일 마운트) |
| careerhub 공개 Gateway · HTTPRoute · DNS 의도 | jyoliar-k8s `careerhub-prod` | Gateway + NginxProxy · `careerhub-httproute` 의 parentRef · Gateway 의 `target` 애노테이션 · Route 의 `cloudflare-proxied` |
| 실제 careerhub DNS 레코드 | external-dns | Gateway `target`(`<UUID>.cfargotunnel.com`) → CNAME, Route `cloudflare-proxied: "true"` → 프록시 |
| 엣지 보호 | terraform `cloudflare/` | `cloudflare_ruleset`(`http_ratelimit`) · `cloudflare_bot_management` · `cloudflare_zone_setting` × 3. 무료 관리형 WAF 룰셋은 자동이라 리소스가 없다 |

## 데이터 흐름 — K 의 요청 하나

1. K 가 링크를 연다. 리졸버는 `careerhub.jyo-liar.com` 의 프록시 CNAME 을 따라 Cloudflare 엣지 주소를 돌려준다. 홈랩 주소는 어디에도 나오지 않는다.
2. 엣지가 Universal SSL 로 TLS 를 종료하고, 무료 관리형 WAF 룰셋과 AI 크롤러 차단을 지난다. HTTP 로 왔다면 Always HTTPS 가 먼저 https 로 돌린다.
3. 엣지가 공개 터널로 요청을 넘긴다. 클러스터의 cloudflared 가 이미 열어 둔 아웃바운드 연결이라 홈랩에 열린 포트는 없다.
4. cloudflared 가 ingress 규칙에서 호스트 `careerhub.jyo-liar.com` 을 맞추고 careerhub 공개 Gateway 의 Service 에 HTTP 로 넘긴다. Host 헤더가 그대로 가므로 HTTPRoute 호스트 매칭이 선다. 클러스터 안 이 구간은 평문이다.
5. 공개 Gateway 의 nginx 는 TCP 상대가 cloudflared 파드(`10.244.0.0/16` 안)임을 보고 `X-Forwarded-For` 를 오른쪽에서 훑어 K 의 실제 주소를 클라이언트 주소로 삼는다. 액세스 로그와 OTel 트레이스에 그 주소가 남는다.
6. `/` 는 frontend 로, 프론트가 부르는 `/api/job_postings…` 는 api-composer 로 간다. 토큰이 없으므로 api-composer 는 비로그인 응답(스크랩 정보 null)을 준다. K 는 공고 목록 · 상세 · 회사 리뷰를 본다. nginx 홉은 하나이고 그 비용은 1~2ms 다.
7. K 가 헤더의 "회원가입/로그인" 을 누르면 `/login` 화면이 "리뉴얼 중 — 로그인·가입 일시 중단" 안내를 보인다. 프론트는 `/auth` 를 한 번도 부르지 않는다. 누가 `/auth/...` 를 직접 치면 공개 Gateway 에 그 룰이 없어 404 다.
8. 같은 IP 에서 `/api/*` 가 10초 안에 임계를 넘으면 엣지가 10초 동안 막는다. 홈랩까지 오지 않는다.

집 안에서 여는 사람도 같은 길을 간다 — 이름이 프록시 CNAME 이라 LAN 에서도 Cloudflare 를 거친다.
같은 터널의 다른 줄인 k8s-oidc 는 이 흐름과 무관하게 지금처럼 oidc-server 로 직결된다.

## 전환 순서 — 무엇이 먼저고 무엇이 같이 가나

네 줄기가 있다. 셋은 서로 독립이라 같이 시작하고, 클러스터 작업이 그 셋을 기다린다.
터널 설정 이관(B → C-1)은 k8s-oidc 를 잠깐 끊으므로, 그 단계만 시각을 고른다.

```
A. 프론트 태그            B. terraform — 터널 로컬 관리 전환        D. terraform — 엣지 보호
 /login 안내 화면          config_src=local · tunnel_secret           ruleset(레이트리밋) · bot_management
 → v0.0.4 이미지           → 터널 재생성(UUID 변경) · CNAME 갱신      · zone_setting(HTTPS · TLS · HSTS)
                           → 자격증명 JSON 을 SSM 에
      │                         │                                       │
      │                         ▼                                       │
      │                 C-1. cloudflared 를 새 자격증명·ConfigMap 으로   │
      │                      (cloudflare-system · k8s-oidc 공백 수 분)   │
      │                      → 터널 연결 확인 · k8s-oidc 응답 확인       │
      │                         ▼                                       │
      │                 C-2. careerhub 공개 Gateway (careerhub-prod ·   │
      │                      트래픽 0) → PROGRAMMED 확인                 │
      ▼                         ▼                                       │
      └──────────►  C-3. 전환  ◄─────────────────────────────────────────┘
                     HTTPRoute 를 공개 Gateway 로 · /auth 룰 제거
                     · frontend 태그 인상 · DNS 가 CNAME 으로
                                │
                                ▼
                     C-4. 밖에서 확인 · 실측 항목 닫기
```

### A. 프론트 — `/login` 을 안내 화면으로 (독립)

careerhub-front 의 `/login` 화면을 "리뉴얼 중" 안내로 바꾸고 태그를 낸다.
헤더 링크와 `/my/*` · `/admin/*` 라우트는 그대로 둔다 — 토큰이 없으면 401 → `/login` 으로 흘러 같은 안내에 닿는다.
산출물은 ECR 의 `careerhub-front:v0.0.4` 하나다.

### B. terraform — 터널을 로컬 관리로 (독립 · k8s-oidc 공백의 시작)

`cloudflare/tunnel.tf` 에서 터널 리소스를 `config_src = "local"` + `tunnel_secret`(`random_bytes` 32바이트, state 에 고정)으로 바꾸고, 원격 ingress 리소스(`…_config`)를 지운다.
`config_src` 변경은 터널 재생성이라 UUID 가 바뀐다 — k8s-oidc CNAME 리소스는 새 UUID 를 따라간다. 비밀은 입력값이라 바뀌지 않는다.
출력을 `tunnel_token` 에서 자격증명 JSON(`AccountTag` · `TunnelID` · `TunnelSecret`, sensitive)으로 바꾼다.
apply 한 순간부터 옛 토큰으로 붙어 있던 cloudflared 는 끊긴다 — C-1 을 바로 잇는다.
산출물은 **새 터널 UUID**(C-2 의 `target` 값)와 **자격증명 JSON**(C-1 에서 스크립트에 넣을 값)이다.

### D. terraform — 엣지 보호 (독립)

존 설정이라 DNS 가 바뀌기 전에 apply 해 둘 수 있다. B 와 같은 `cloudflare/` 모듈이지만 터널 리소스와 독립이라 따로 apply 해도 된다.

- `cloudflare_ruleset` — `phase = "http_ratelimit"`, 규칙 1개: `expression` 으로 호스트 `careerhub.jyo-liar.com` 과 경로 `/api/*` 를 좁히고, `ratelimit { characteristics = ["ip.src"], period = 10, requests_per_period = <임계>, mitigation_timeout = 10 }`. Free 의 한도(규칙 1 · 10초 · IP)를 값으로 지킨다.
- `cloudflare_bot_management` — `ai_bots_protection = "block"`, `fight_mode = false`(켜지 않기로 한 판정이 코드에 남는다).
- `cloudflare_zone_setting` × 3 — `always_use_https = "on"` · `min_tls_version = "1.2"` · `security_header`(HSTS).
- 무료 관리형 WAF 룰셋은 Free 존에 자동 배포라 리소스가 없다. apply 뒤 대시보드에서 적용 상태만 확인한다.

`zone_setting` 과 `bot_management` 는 존 전역이라 `id.careerhub` · `*.mg` 에도 걸린다 — 전부 HTTPS 호스트라 무해하다. 호스트를 가려야 하는 레이트리밋만 `expression` 이 좁힌다.

### C-1. cloudflare-system — 새 자격증명과 ConfigMap 으로 (B 직후)

- 자격증명 Secret — B 의 출력 JSON 을 `create-tunnel-token.sh` 로 `cloudflare-system` 에 넣는다(스크립트는 `--from-literal=token=` 대신 `--from-file=credentials.json=` 로 고친다). 지금 토큰을 넣는 것과 같은 자리 · 같은 손이다.
- ConfigMap `config.yml` — `tunnel: <UUID>` · `credentials-file` · ingress 세 줄(k8s-oidc → oidc-server:8080 · careerhub → 공개 Gateway Service:80 · `http_status:404`). `cloudflared tunnel ingress validate` 를 적용 전에 돌린다.
- Deployment — `TUNNEL_TOKEN` 대신 자격증명 파일 마운트, 실행 인자 `tunnel --config /etc/cloudflared/config.yml run <UUID>`.

확인할 것은 둘이다 — cloudflared 로그에 터널 연결 등록이 찍히는가, `https://k8s-oidc.jyo-liar.com/.well-known/openid-configuration` 이 다시 응답하는가.
B 의 apply 부터 여기까지가 k8s-oidc 의 공백이다. ESO · ECR pull 은 토큰 갱신 시점에만 OIDC 를 부르므로 몇 분은 흡수되지만, ESO 의 갱신 주기(1시간)와 겹치지 않게 시각을 고른다.

### C-2. careerhub-prod — 공개 Gateway 를 트래픽 없이 (C-1 뒤)

- Gateway `careerhub-public-gateway` + NginxProxy — `service.type: ClusterIP` · HTTP 리스너(80)만 · `telemetry.exporter` 는 사설 Gateway 와 같게 · `rewriteClientIP: {mode: XForwardedFor, setIPRecursively: true, trustedAddresses: [10.244.0.0/16]}` · 애노테이션 `external-dns.alpha.kubernetes.io/target: <새 UUID>.cfargotunnel.com`.
- 이 시점에는 붙은 HTTPRoute 가 없다. PROGRAMMED 를 확인한다.
- careerhub ingress 줄(C-1)은 이미 이 Service 를 가리키고 있다 — Gateway 가 뜨기 전엔 cloudflared 가 502 를 내지만 DNS 가 아직 사설 A 라 밖에서 오는 요청은 없다.

### C-3. 전환 — 한 커밋 (A · C-2 · D 를 기다린다)

jyoliar-k8s 커밋 하나로 셋이 같이 바뀐다.

- `careerhub-httproute` 의 `parentRefs` 를 공개 Gateway 로 옮기고(`sectionName` 은 HTTP 리스너 이름으로), `/auth` 룰을 지우고, `external-dns.alpha.kubernetes.io/cloudflare-proxied: "true"` 를 단다.
- `http-to-https-redirect` 의 호스트에서 `careerhub.jyo-liar.com` 을 뺀다 — 리다이렉트는 엣지가 한다. `id.careerhub` 는 남긴다.
- frontend Deployment 의 이미지를 `v0.0.4` 로 올린다.

ArgoCD 가 적용하면 external-dns 가 다음 주기에 `careerhub.jyo-liar.com` 의 소유 레코드를 사설 A 에서 프록시 CNAME 으로 바꾼다.
같은 이름에서 타입이 바뀌는 적용 순서는 문서에 없어 첫 동기화 로그를 본다 — Cloudflare 가 CNAME 충돌로 거부하면 옛 A 레코드를 한 번 손으로 지우고 다음 주기를 기다린다.
이 커밋 이후 사설 Gateway 는 `id.careerhub` 만 서빙한다.

### C-4. 밖에서 확인 (C-3 뒤)

- 모바일 망 등 홈랩 밖에서 링크를 열어 공고 목록 · 상세 · 리뷰가 뜨는지, `/login` 이 안내 화면인지, `/auth/auth-code-urls` 가 404 인지 본다.
- 공개 Gateway nginx 로그(Loki)에서 그 요청의 클라이언트 주소가 방문자 IP 인지 본다. HTTP 리스너에서 `rewriteClientIP` 가 듣지 않으면 공개 Gateway 를 HTTPS 리스너로 바꾸고 cloudflared 의 careerhub 줄을 `https://…:443` + `originServerName` 으로 되돌린다 — 이때만 인증서가 필요하다.
- `/api/*` 를 빠르게 반복해 엣지가 429 를 내는지 본다.
- 집 안(VPN) 브라우저에서도 같은 화면이 Cloudflare 를 거쳐 뜨는지 본다.
- k8s-oidc 가 여전히 응답하고 ESO 의 ExternalSecret 들이 `SecretSynced` 인지 본다.

## 장애 시 동작

- **터널이 끊기면** careerhub 와 k8s-oidc 가 같이 끊긴다. 엣지가 오류 페이지를 내고, 공개 Gateway 는 LAN 주소가 없어 우회 경로가 없다. cloudflared 2 replica 가 유일한 중복이다.
- **클러스터 DNS 가 죽으면** cloudflared 가 두 목적지 모두 못 풀어 같은 결과다. cloudflared 자신도 클러스터 DNS 에 기대 터널에 붙는다.
- **ingress ConfigMap 이 깨지면**(catch-all 누락 · YAML 오류) cloudflared 가 기동하지 못하고 두 호스트가 함께 죽는다 — 적용 전 `ingress validate` 가 막는 선이다.
- **Cloudflare 가 죽으면** 사이트도 죽는다. 이 설계는 Cloudflare 를 단일 진입점으로 받아들인다.
- **auth-service 가 죽어도** 아무 일이 없다. 어느 Gateway 도 그리로 보내지 않는다.
- **공개 Gateway 의 nginx 가 죽어도** k8s-oidc 는 무관하다 — ingress 가 oidc-server 로 직결이라 NGF 를 지나지 않는다.

## 운영 — 공개 기간과 그 끝

- 레거시 코드는 공개 기간 내내 손대지 않는다. 바뀌는 것은 프론트 태그 하나와 매니페스트 · terraform 뿐이다. Cloudflare 측에 손으로 켜는 것은 없다.
- 공개 호스트가 하나 더 생기면 cloudflare-system 의 ConfigMap 에 줄 하나와 그 앱의 Gateway 또는 라우트가 더해진다. 공개 서비스가 둘 이상이 되면 여러 호스트를 받는 플랫폼 공개 Gateway 로 옮기는 논의를 연다.
- 검색엔진은 막지 않는다. 운영 중 필요가 보이면 그때 다시 정한다.
- 컷오버(신스택이 apex 를 승계하는 날)에는 공개 Gateway 와 터널 ingress 가 그대로 쓰이고, `careerhub-httproute` 의 백엔드가 careerhub-web 과 신 api-composer 로 바뀐다. `/auth` 룰의 재도입과 `id.careerhub` 의 공개 여부는 그날의 결정이다.
- 되돌리기는 C-3 커밋의 revert 다 — HTTPRoute 가 사설 Gateway 로 돌아가면 external-dns 가 레코드를 다시 사설 A 로 바꾼다. 공개 Gateway 와 careerhub ingress 줄은 트래픽 0 으로 남는다. 터널의 로컬 관리 전환(B · C-1)은 되돌리지 않는다 — 그것은 공개와 무관하게 유지되는 변경이다.

## 이 설계가 하지 않는 것

- 로그인 · 가입 · 스크랩 · 매칭 — 공개 기간에 없다.
- Zitadel(`id.careerhub`)의 공개 — 사설 Gateway 에 그대로.
- 여러 공개 호스트를 받는 플랫폼 공개 Gateway — 공개 서비스가 careerhub 하나인 동안은 두지 않는다.
- 클러스터 안 홉의 TLS — cloudflared → 공개 Gateway 는 평문이다.
- k8s-oidc 의 DNS 를 GitOps 로 — CNAME 은 terraform 의 seed 로 남는다.
- 엣지 캐시, Cloudflare Access 로 경로 보호, Bot Fight Mode, 검색엔진 색인 차단.
- 집 안에서 VIP 로 직접 들어가는 길 — 모두 Cloudflare 를 거친다.
- 크롤링 콘텐츠(공고 · 리뷰)의 공개 위험 판단 — 아직 열리지 않은 관점이다.
