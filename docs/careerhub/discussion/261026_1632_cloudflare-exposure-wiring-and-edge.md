---
type: discussion
kind: deliberation
goal: legacy-public-exposure
topic: careerhub
subjects: [cloudflare-tunnel, cloudflared, external-dns, careerhub-nginx-gateway, careerhub-httproute, nginx-gateway-fabric, jyoliar-platform-terraform, zitadel]
status: done
ref-adrs: [ADR-0034]
related:
  - docs/careerhub/discussion/261026_1631_cloudflare-tunnel-dns-edge-survey.md
  - docs/careerhub/discussion/261026_1610_legacy-public-exposure-auth-disposition.md
  - docs/careerhub/discussion/261026_1811_public-gateway-topology-and-tunnel-handoff.md
---

# 레거시 스택 임시 공개 — Cloudflare 쪽 배선과 엣지 보호

## 1. 문제

앞 논의(261026_1610)가 인증 기능을 떼어내기로 했다.
남은 것은 `careerhub.jyo-liar.com` 을 Cloudflare Tunnel 로 공개 인터넷에 내보내는 배선과, 게이트웨이에 없는 보호(레이트리밋 · WAF · 봇)를 Cloudflare 가 대신하는 묶음을 정하는 일이다.
기간은 3~6개월이고, 컷오버(#79)가 끝나면 이 배선은 신스택(careerhub-web · Zitadel)이 물려받거나 걷힌다.

열려 있던 것은 넷이다.
터널 ingress 와 DNS 레코드를 어느 플레인(terraform · GitOps)이 선언하는가 — ADR-0034(proposed)가 방향을 준다.
Free 플랜에서 어떤 보호를 켜는가.
검색엔진 색인을 막는가, 막는다면 어디서.
Zitadel 호스트(`id.careerhub`)를 이번에 공개하는가.

이 문서는 Cloudflare 와 그 접점(DNS · 게이트웨이)까지다.
크롤링 콘텐츠(Wanted · Jumpit 공고 · Blind 리뷰)의 공개 위험은 다음 관점이다.

## 2. 실측

### 2-1. 지금의 배선

- `careerhub.jyo-liar.com` 과 `id.careerhub.jyo-liar.com` 은 퍼블릭 리졸버에서 사설 VIP `10.18.100.3` 으로 풀린다.
  둘 다 external-dns 가 소유한다 — TXT `_edns.a-careerhub.jyo-liar.com` 에 `owner=homelab-external-dns, resource=httproute/careerhub-prod/careerhub-httproute`.
- external-dns 는 v0.20.0, `sources: [gateway-httproute]` · `policy: sync` · `provider: cloudflare` · `--cloudflare-proxied` 없음(`jyoliar-k8s/gitops/base/controllers/external-dns/application.yaml`).
  레코드는 전부 DNS-only 라 사설 주소가 공개 조회된다.
- careerhub Gateway 하나에 세 HTTPRoute 가 붙는다 — `careerhub-httproute`(apex) · `zitadel` · `zitadel-login`(`id.careerhub`).
  NginxProxy 는 `type: LoadBalancer`(kube-vip)이고, HTTP 리스너는 301 → https 다(`gateway/http-redirect.yaml`).
- 존 네임서버는 Cloudflare 다. 인증서는 cert-manager `letsencrypt-dns`(DNS-01) 와일드카드로 `careerhub.jyo-liar.com` + `*.careerhub.jyo-liar.com`(`gateway/certificate-patch.yaml`).

### 2-2. 터널은 이미 terraform 이 소유한다

- `jyoliar-platform-terraform/cloudflare/tunnel.tf` 가 터널 `k8s-oidc`(`config_src = "cloudflare"`), 원격 ingress(`k8s-oidc.jyo-liar.com` → oidc-server), 프록시 CNAME 을 만든다.
  토큰은 `outputs.tf` 의 data source 로 나가고, 클러스터의 `cloudflared`(ns `cloudflare-system`, 2 replica)는 `TUNNEL_TOKEN` 으로 그 터널에 붙는다.
- cloudflared 로그의 현재 설정: ingress 는 `k8s-oidc` 한 줄과 `http_status:404` 뿐이다.
- external-dns 의 API 토큰도 terraform 이 만들어 SSM 에 심고(`external-dns.tf`), ExternalSecret 이 당긴다 — ADR-0034 가 말하는 "유일한 공식 접점" 패턴이 이미 있다.
- ADR-0034(proposed) Consequences: *"클러스터 서비스의 DNS record가 그 예다 — … 클러스터 측 선언(external-dns 등)으로 옮기는 방향이 이 결정의 파생이다."*

### 2-3. 조사가 준 제약 (→ 261026_1631)

- external-dns 의 `target` 애노테이션은 **Gateway** 에서 읽는다. HTTPRoute 단위로 target 을 가를 수 없다.
  careerhub Gateway 에 붙이면 `id.careerhub` 도 터널 CNAME 이 된다.
- 프록시 여부는 Route 애노테이션(`external-dns.alpha.kubernetes.io/cloudflare-proxied`)이고, 호스트명이 아닌 target 은 CNAME 이 된다.
- cloudflared 는 terraform 이 정체성·비밀(`config_src=local` · `tunnel_secret`)만 들고 ingress 는 origin 쪽 YAML 이 드는 조합을 지원한다.
- origin 은 `https://<gateway-svc>:443` + `originServerName: careerhub.jyo-liar.com` 으로 LE 인증서를 그대로 검증한다. `http://…:80` 은 301 루프다.
- Free: 무료 관리형 룰셋 · 레이트리밋 1개(IP · 10초) · Bot Fight Mode(검증 봇 예외 불가 · API 호출도 챌린지 가능) · AI 봇 분류별 차단 · Transform 10개 · Universal SSL 은 1단 서브도메인까지.
- NGF 는 Gateway 당 nginx Deployment 하나이고, NginxProxy 로 ClusterIP Gateway 를 만들 수 있다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 노출 수단

**선택: Cloudflare Tunnel.** 공유기 포트포워딩은 홈랩 공인 IP 와 게이트웨이를 직접 드러낸다. (인터뷰, 2026-10-26)

### 3-2. Cloudflare 에서 바라는 것

**선택: 공개 배선 + 엣지 보호(WAF · 레이트리밋 · 봇).** 캐시·성능과 Access 접근 통제는 하지 않는다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 엣지 캐시 — 정적 자산이 작고 홈랩 대역이 병목이 아니다
- Cloudflare Access 로 일부 경로 보호 — 보호할 로그인 기능이 이미 없다(261026_1610)

</details>

### 3-3. 선언의 플레인

**선택: ADR-0034 의 방향을 제약으로 삼는다.** careerhub 의 터널 ingress 와 DNS 는 클러스터 쪽 선언으로, terraform 은 seed(터널 정체성 · 비밀)까지. 기존 k8s-oidc 는 건드리지 않는다. (인터뷰, 2026-10-26)

### 3-4. 터널의 수

**선택: 새 터널 — 용도별 분리.** 부트스트랩 신뢰 경로(k8s-oidc)와 공개 웹을 한 토큰·한 디플로이에 섞지 않는다. (인터뷰, 2026-10-26) **— 같은 날 뒤집힘: 261026_1811 §3-1 이 터널 하나(k8s-oidc 공유)로 정했다. "공개 엔드포인트는 터널 하나로" 전제가 인터뷰에서 빠져 있었다.**

<details><summary>버린 안</summary>

- 기존 터널에 ingress 추가 — 가장 싸지만 설정이 `tunnel.tf` 에 있어 3-3 과 어긋나고, 공개 웹의 사고가 OIDC 경로의 cloudflared 를 함께 흔든다

</details>

### 3-5. 공개 뒤 내부 접근

**선택: 집 안에서도 Cloudflare 경유로 충분하다.** split-horizon DNS 를 두지 않는다. (인터뷰, 2026-10-26)

### 3-6. 플랜

**선택: Free 를 기준으로 적고, 유료 항목은 표시만 한다.** 현재 플랜은 확인하지 못했다. (인터뷰, 2026-10-26)

## 4. 열린 축 — 논의

### 4-1. 터널 ingress 와 CNAME 의 자리

실측: `target` 은 Gateway 단위다. 같은 Gateway 의 zitadel 라우트가 끌려온다. terraform 은 `config_src=local` 로 정체성만 들 수 있다.

- **A. 공개 전용 Gateway 를 하나 더 둔다(ClusterIP).** `careerhub-public-gateway` 에 `target: <tunnel-id>.cfargotunnel.com` 애노테이션, `careerhub-httproute` 를 거기 붙이고 `cloudflare-proxied: "true"`. zitadel 라우트는 기존 사설 Gateway 에 남는다. 터널은 terraform 이 `config_src=local` + `tunnel_secret` 으로 만들어 SSM 에 심고, ExternalSecret 이 자격증명 JSON 으로 당긴다. ingress 는 careerhub-prod 의 ConfigMap(`config.yml`)이고 service 는 `https://careerhub-public-gateway-nginx.careerhub-prod.svc:443`. **이기는 조건:** 3-3 · 3-4 를 끝까지 따르고 `id.careerhub` 를 사설로 남길 때 — 지금이다. **지는 조건:** nginx 데이터플레인이 하나 더 돈다. 공개 Gateway 가 LAN 주소를 갖지 않아 터널이 죽으면 내부에서도 못 들어간다(3-5 가 이미 받아들였다).
- B. 기존 careerhub Gateway 에 `target` 애노테이션. 가장 적은 매니페스트. **이기는 조건:** `id.careerhub` 도 터널로 내보낼 때(4-4 B). **지는 조건:** 지금은 zitadel 내부 접근이 터널 404 로 끊긴다.
- C. terraform 이 전부 — 새 터널의 원격 ingress + `cloudflare_dns_record` CNAME, HTTPRoute 에 `controller` 애노테이션으로 external-dns 제외. k8s-oidc 와 동형이라 가장 빠르다. **이기는 조건:** ADR-0034 를 적용하지 않기로 할 때. **지는 조건:** 3-3 과 충돌한다. terraform 이 클러스터 서비스 주소를 든다.
- D. 안 한다 — 포트포워딩. 공인 IP · 게이트웨이 직접 노출, 레이트리밋 없음. 3-1 에서 버렸다.

절차 주의: 같은 이름의 소유 레코드가 A→CNAME 으로 바뀌는 순서는 문서에 없다.
호스트명을 먼저 떼어 A 를 지우게 한 뒤 공개 Gateway 에 붙이는 2단계, 또는 1회 수동 삭제를 실측으로 정한다.

**판정(사람, 2026-10-26): A. 공개 전용 Gateway(ClusterIP) 신설.** — 261026_1811 §3-2 · §4-1 이 이어받아 그대로 선다. 달라진 것은 둘 — 터널은 k8s-oidc 와 공유(3-4 뒤집힘)하고, 이 Gateway 는 HTTP 리스너만 둔다(4-2 뒤집힘).

### 4-2. origin 연결

실측: HTTP 리스너는 301 이라 80 은 루프다. LE 와일드카드가 `careerhub.jyo-liar.com` 을 덮는다.

- **A. `https://…:443` + `originServerName: careerhub.jyo-liar.com`.** 인증서 검증을 그대로 둔다. Host 헤더는 cloudflared 가 보존하므로 HTTPRoute 호스트 매칭이 선다. **이기는 조건:** 기본값.
- B. `noTLSVerify: true`. 인증서 갱신 실패에도 터널은 산다. **지는 조건:** 클러스터 내부 구간이라도 검증을 끌 이유가 없다.
- C. 공개 Gateway 에 HTTP 리스너만 두고 `http://…:80`. TLS 종료가 Cloudflare 한 곳이 된다. **지는 조건:** cloudflared → nginx 구간이 평문이 되고, 4-1 A 의 Gateway 정의가 사설 Gateway 와 달라진다.

**판정(사람, 2026-10-26): A. HTTPS 443 + `originServerName`.** — 같은 날 뒤집힘: 261026_1811 §3-5 가 클러스터 안 홉을 평문(HTTP 리스너만, 인증서 없음)으로 정했다. 이 판정은 careerhub-prod 의 Gateway 가 LE 인증서를 이미 든다는 전제였고, 공개 Gateway 가 플랫폼으로 옮겨가며 전제가 사라졌다.

### 4-3. 엣지 보호 묶음 (Free)

실측: 관리형 룰셋 무료판은 자동이다. 레이트리밋은 1개, IP 특성, 10초. BFM 은 검증 봇 예외가 없고 API 호출도 챌린지할 수 있다.

- **A. 기본 묶음 — 무료 관리형 룰셋 + 레이트리밋 1개(`/api/*`, IP 기준, 10초) + AI 봇 차단(Training · Agent 를 Block) + Always HTTPS · 최소 TLS 1.2 · HSTS.** BFM 은 켜지 않는다. **이기는 조건:** 프론트의 fetch 가 챌린지로 깨지는 위험을 지지 않을 때. **지는 조건:** 무차별 스크래퍼는 레이트리밋 1개가 전부다.
- B. A + Bot Fight Mode. 봇 방어가 는다. **이기는 조건:** 색인을 차단하고(4-4 A/B) 프론트 fetch 가 챌린지를 받지 않음을 실측으로 확인했을 때. **지는 조건:** 색인을 허용하면 Googlebot 에 챌린지 페이지가 나간다(조사 §3). 4-4 의 판정(차단 안 함)으로 이 조건이 성립했다.
- C. Pro 업그레이드 — 관리형 룰셋 전체 + OWASP + 레이트리밋 여러 개 + Super Bot Fight Mode(검증 봇 허용). **이기는 조건:** 색인 허용과 봇 방어를 둘 다 원할 때. **지는 조건:** 반년짜리 임시 노출에 월 비용.
- D. 안 한다 — 터널만. 공인 IP 는 숨지만 홈랩 과부하 방어가 0 이다.

**판정(사람, 2026-10-26): A. 기본 묶음, Bot Fight Mode 없이.**

### 4-4. 검색엔진 색인

실측: 프론트는 해시 라우팅이라 색인될 것이 빈 셸 한 장이다. 프론트 새 태그는 어차피 나간다(261026_1610 §3-2).

- **A. 프론트 `public/robots.txt` `Disallow: /` + `<meta name="robots" content="noindex">`.** 나가는 태그에 얹는다 — 한계비용 0. **이기는 조건:** 포트폴리오 링크로만 들어오면 될 때. **지는 조건:** 프론트 저장소 변경이 하나 더다(같은 PR).
- B. Cloudflare Transform Rule 로 `X-Robots-Tag: noindex, nofollow` 응답 헤더. 프론트 무변경, 전 경로 적용, Free 10개 안. robots.txt 는 못 만든다 — 크롤은 되고 색인만 막는다. **이기는 조건:** 프론트를 안 건드리고 싶을 때. A 와 겹쳐 둬도 해롭지 않다.
- C. 허용. BFM 을 끄거나 Pro 로 간다(4-3). **이기는 조건:** 검색 유입이 목적일 때 — 아니다.
- D. 지금은 차단 정책을 두지 않는다 — 운영 후 필요가 보이면 다시 논의한다. 기본값(허용)과 결과가 같되, 재논의 시점을 "운영 뒤"로 못 박는 점이 다르다.

**판정(사람, 2026-10-26): D. 색인 차단은 이 논의의 것이 아니다 — 운영 후 필요시 재논의.**

### 4-5. `id.careerhub.jyo-liar.com`(Zitadel)의 공개

실측: 레거시 스택은 Zitadel 을 호출하지 않는다. 2단 서브도메인이라 Universal SSL 이 덮지 않는다. #66(관리 표면 차단)은 Draft 다.

- **A. 이번엔 공개하지 않는다.** 사설 Gateway 에 그대로 두고 터널 ingress 에 넣지 않는다. **이기는 조건:** 레거시 공개 기간 — 쓸 곳이 없다. #66 의 "public 도달 가능" 문제가 그냥 사라진다.
- B. 터널에 추가. 컷오버 전 Zitadel 실험을 밖에서 하고 싶을 때. **지는 조건:** ACM(Total TLS) 또는 커스텀 인증서가 필요하고, #66 이 선행이며, 4-1 B 로 끌려간다.
- C. 컷오버(#79) 때 신스택과 함께 정한다 — A 의 결과와 같다.

**판정(사람, 2026-10-26): A. 이번에 공개하지 않는다.**

### 4-6. 프록시 뒤 클라이언트 IP

실측: 터널을 지나면 nginx 가 보는 원격 주소는 cloudflared 파드다. NGF `rewriteClientIP` 가 XFF 를 신뢰 범위 안에서 복원한다.
홈랩의 NginxProxy 네 개(internal · agent · careerhub · 기본) 어디에도 `rewriteClientIP` 는 아직 없다.
방문자 IP 에 관해 앞서 손댄 것은 L4 의 `externalTrafficPolicy` 뿐이다 — kube-vip VIP 노드와 nginx 파드 노드가 다를 때 트래픽이 끊겨 `Local` → `Cluster` 로 바꿨고(jyoliar-k8s `12de638`, 2026-02-16), 그 대가로 노드 간 SNAT 가 생겨 LAN 게이트웨이도 지금 방문자 IP 를 온전히 보지 못한다.
터널 경로는 ClusterIP 라 이 설정과 무관하고, 복원 수단은 L7 헤더(`rewriteClientIP`)뿐이다.
파드 CIDR 은 `10.244.0.0/16` 이고 cloudflared 파드는 노드를 옮겨 다니므로 신뢰 범위는 이 대역 전체가 된다.

- **A. 공개 Gateway 의 NginxProxy 에 `rewriteClientIP: {mode: XForwardedFor, setIPRecursively: true, trustedAddresses: [10.244.0.0/16]}`.** 게이트웨이 로그·트레이스에 실제 방문자 IP 가 남는다. 클러스터 안의 어느 파드든 XFF 를 꾸밀 수 있게 되지만, 신뢰 경계가 이미 클러스터다. Cloudflare 가 XFF 에 방문자 IP 를 싣는지는 첫 요청으로 실측한다(`CF-Connecting-IP` 는 항상 온다). **이기는 조건:** 공개 뒤 트래픽을 Loki 에서 agent 가 읽을 때 — 4-3 의 레이트리밋이 Cloudflare 에서 걸리므로 보호에는 필수가 아니다.
- B. 안 한다. 방문자 IP 는 Cloudflare 대시보드에서만 본다. **이기는 조건:** 반년짜리라 관측을 Cloudflare 에 맡길 때.
- C. 앱이 `CF-Connecting-IP` 를 읽는다. 코드 변경 → 티켓. **지는 조건:** 레거시 코드를 안 건드린다는 앞 논의의 결정과 충돌한다.

**판정(사람, 2026-10-26): A. 방문자 IP 를 게이트웨이에 남긴다 — 뒤에 agent 가 분석할 재료다.**

## 5. 반대편 — 이 설계가 틀리는 조건

- 공개 Gateway 가 ClusterIP 뿐이라 터널 장애 = 전면 장애다. #80(CoreDNS 단일 upstream)의 피해자 목록에 cloudflared 가 이미 있다 — 클러스터 DNS 장애가 공개면까지 끌고 간다.
- 레이트리밋이 IP 기준 1개라, 분산 스크래퍼에는 무력하다. 그때는 4-3 C 로 간다.
- ADR-0034 는 proposed 다. accept 되지 않으면 3-3 은 사람의 취향으로 남고, 4-1 C 가 되살아난다.
- 컷오버 때 apex 를 careerhub-web 이 승계하면 공개 Gateway 와 터널 ingress 는 그대로 쓰이고 HTTPRoute 백엔드만 바뀐다. 다만 `id.careerhub` 를 그때 공개하려면 4-5 B 의 비용(ACM · #66)이 그대로 온다 — 이 논의가 미룬 것이지 없앤 것이 아니다.
- external-dns 의 A→CNAME 전환 순서가 틀리면 레코드가 잠시 비거나 Cloudflare 가 거부한다. 2단계 절차로 피할 수 있지만 실측 전엔 가정이다.

## 6. 버린 것

- **"Cloudflare 설정은 대시보드에서 손으로 켜고 절차 기록으로 남긴다"** — 처음엔 반년짜리 설정에 terraform 리소스를 늘리지 않는다고 봤다가 버렸다. 레이트리밋(`cloudflare_ruleset` · `http_ratelimit`) · AI 봇 차단과 BFM 끔(`cloudflare_bot_management`) · Always HTTPS · 최소 TLS · HSTS(`cloudflare_zone_setting`)는 전부 provider 5.18 에 있고, 존 설정은 클러스터 상태가 아니라 ADR-0034 방향에서 terraform 의 자리다. 이미 `cloudflare/` 모듈이 존·터널·API 토큰을 든다. 무료 관리형 WAF 룰셋만 자동 배포라 리소스가 없다. 존 단위 설정(`zone_setting` · `bot_management`)은 이 존의 모든 호스트에 걸리므로, 호스트를 가려야 하는 것(레이트리밋)만 `expression` 으로 좁힌다.
- **기존 k8s-oidc 터널 재사용** — 3-4 에서 버렸다.
- **포트포워딩** — 3-1 에서 버렸다.

## 7. 임계선 — ADR감인가

아니다.
공개 Gateway · 터널 · 애노테이션은 전부 매니페스트와 terraform 한두 리소스이고, 되돌리면 한 시간 안에 사설 상태로 돌아간다.
Cloudflare 측 설정도 terraform 리소스 몇 개라 destroy 로 돌아간다.
단, 4-1 의 판정은 ADR-0034 의 적용 사례가 된다 — ADR-0034 가 accept 되면 그 Consequences 의 "이관 대상" 목록에 k8s-oidc 터널의 원격 ingress 도 들어간다. 이 논의가 그것을 만들지는 않는다.

## 8. 다음

- 판정이 나면 리프 티켓: terraform(터널 · 엣지 보호 리소스 — 레이트리밋 ruleset · bot_management · zone_setting 셋) · jyoliar-k8s(공개 Gateway · HTTPRoute 재부착 · cloudflared · 애노테이션) · careerhub-front(/login 안내 — 261026_1610 의 프론트 태그). 터널의 모양은 261026_1811 이 이어받아 정했다.
- 같은 goal 의 다음 관점: 크롤링 콘텐츠(Wanted · Jumpit · Blind)의 공개 위험.
- 발행 시점은 사람이 정한다 — 지금은 아니다.
