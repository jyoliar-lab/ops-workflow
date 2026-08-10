---
type: discussion
topic: careerhub
subjects: [nginx-gateway-fabric, auth-service, careerhub-front, careerhub-api-composer, careerhub-web, zitadel, cert-manager]
status: active
ref-adrs: [ADR-0030]
---

# careerhub 라우팅 — 경로 기반에서 호스트 기반으로, 그리고 공개면 판정

## 문제

careerhub는 단일 호스트(`careerhub.jyo-liar.com`)에 경로 3분기로 서비스를 노출한다.
`/`→frontend · `/api`→api-composer · `/auth`→auth-service (`jyoliar-k8s/gitops/base/services/careerhub/apps/gateway/httproute.yaml`).
겉으로 드러난 촉발점은 Zitadel 배치 충돌이다 — `/auth` PathPrefix를 auth-service가 점유 중인데 Zitadel 자체 API가 `/auth/v1/*`를 쓴다.
그러나 논의에서 동기가 둘로 갈라졌다.
하나는 충돌 해소 수단이고, 다른 하나는 호스트 기반 노출 자체가 원하는 종착 형태라는 것이다.
후자의 근거: 경로 기반에서는 경로 의존적인 코드를 쓸 때 고려할 것이 많아지고(auth-service는 Go 코드에 `/auth/...` 프리픽스를 하드코딩하고 있다 — `auth_controller.go`), 다른 서비스를 호출한다는 사실이 직관적으로 보이지 않는다.

## 실측

- **프론트(레거시)의 백엔드 주소는 env다.**
  `BACKEND_URL="/api"` · `AUTH_URL="/auth"` (`frontend/deployment.yaml`) — 상대 경로를 절대 URL로 바꾸면 되고 코드 변경이 없다.
- **토큰은 쿠키 저장 + Authorization 헤더 전송이다** (`careerhub-front/src/httputils.js`).
  크로스도메인 쿠키 공유 문제가 애초에 없다.
- **CORS는 양쪽 다 이미 장착돼 있다.**
  auth-service·api-composer 모두 `ACCESS_CONTROL_ALLOW_ORIGIN` env로 제어되는 CORS 미들웨어를 쓴다 (`app.go`, `restapi_http.go`).
- **인증서가 유일한 구조적 걸림이다.**
  `wildcard-certificate.yaml`은 `*.jyo-liar.com` + apex뿐이고, 와일드카드는 한 단계만 커버하므로 `*.careerhub.jyo-liar.com`은 커버 밖이다.
  issuer가 `letsencrypt-dns`(DNS-01)라 SAN 추가로 해결된다 — 1회 비용.
- **선례가 있다.**
  `*.mg.jyo-liar.com`은 이미 전용 와일드카드 인증서(`wildcard-mg-tls`) + 리스너 hostname으로 호스트 기반이 서 있다 (`gateway-patch.yaml`).
  경로 다중화된 호스트는 careerhub가 클러스터에서 유일한 예외다.
- **리뉴얼(careerhub-web)은 아직 공개면을 확정하지 않았다.**
  클라이언트 컴포넌트(`"use client"`)가 0개이고 API 호출은 전부 서버 측이다.
  토큰은 `setAccessTokenProvider` 심 뒤로 격리돼 있다(`src/lib/api/client.ts`).
  `NEXT_PUBLIC_API_BASE_URL`이 브라우저 노출 가능성을 열어뒀으나 실사용은 없다.

## 1차 수렴 — 그리고 반전

처음 벌린 옵션과 1차 판정:

- **A. 안 한다 — 레거시 유지, Zitadel만 신규 호스트로.**
  1차에서 기각했다 — 동기가 충돌 해소만이 아니라 호스트 기반 자체가 종착 형태로 확인되어서다.
- **B. 전면 호스트 분리(front·api·auth 모두).**
- **C. 단계 분리 — front·api 먼저, auth는 소셜 sub 실측 이후.**
  1차 수렴은 C였다.
- **D. 1단 평면 네이밍(`careerhub-api.jyo-liar.com` 식).**
  기각 — 서비스 간 쿠키를 공유하려면 `Domain=.jyo-liar.com`뿐인데, 그것은 `argocd.mg.*` 같은 인프라 호스트에까지 토큰이 새는 스코프다.

**공개면 질문이 1차 수렴을 되돌렸다.**
"종착 그림에서 각 서비스가 브라우저에서 직접 호출될 필요가 있는가"를 물었더니(아래 절), 레거시 front·api 분리는 컷오버까지만 사는 한시적 공개에 대한 투자로 판명됐다.
최종 판정: **레거시는 손대지 않는다 — 경로 기반인 채 컷오버 때 루트째 소멸한다.**
호스트 기반 원칙은 폐기가 아니라 적용 대상이 바뀐 것이다: **신규 공개면(Zitadel · careerhub-web · dev 환경)부터 적용한다.**
A가 레거시에 한해 부활했고, B·C는 대상 소멸로 함께 기각됐다.

## 공개면 판정 — 누가 브라우저에 닿는가

종착 그림의 공개면은 **careerhub-web과 Zitadel 둘뿐**이다.

- **careerhub-web — 공개.**
  자명하다.
- **Zitadel — 공개가 구조적 필연.**
  리뉴얼 로그인은 표준 리다이렉트 OIDC(Authorization Code + PKCE)이고, 이 흐름은 브라우저가 IdP의 authorization endpoint·로그인 UI로 직접 리다이렉트된다.
  소셜 로그인도 Google/Naver가 브라우저를 Zitadel 콜백으로 돌려보낸다.
  비공개 IdP로는 리다이렉트 로그인이 성립하지 않는다.
- **auth-service — 공개 불필요, 이동도 불필요.**
  인증은 외부 IdP 제품이 소유하므로(ADR-0028) auth-service는 레거시와 함께 소멸한다.
  따라서 호스트를 옮기지 않고 루트의 `/auth`에서 그대로 죽는다.
  이로써 "auth 분리는 소셜 sub 실측에 게이트된다"는 1차 수렴의 순서 제약이 **"auth는 분리 대상이 아니다"로 해소**됐다 — redirect_uri 호스트 질문은 Zitadel의 호스트에만 남는다.
- **api-composer — 내부 전용(BFF)으로 판정.**
  모든 데이터가 careerhub-web 서버를 경유한다(SSR 렌더 + 인터랙티브 fetch는 route handler 프록시).
  근거: 토큰이 브라우저에 존재하지 않게 되어 토큰 저장 결정의 XSS 축이 통째로 사라지고, CORS가 소멸하며, 공개면이 최소가 된다.
  받아들인 대가: 인터랙티브 호출마다 web 서버 한 홉을 경유한다 — 현 서비스 규모에서 토큰 무브라우저의 이득이 더 크다고 판정했다.
  기각한 대안(공개 유지): 브라우저가 Bearer로 직접 호출 — 홉은 없지만 토큰이 JS 접근 가능 영역에 살아야 하고 CORS·공개면이 남는다.

**리뉴얼 토큰 저장 전제에 미치는 효과.**
1차 수렴 시점에는 호스트 분리로 토큰 저장 전제가 "크로스오리진 + 공통 부모 도메인 쿠키"로 바뀐다고 봤다.
BFF 판정이 이를 다시 단순화했다 — 브라우저 관점에서는 web 호스트 단일 오리진뿐이므로, **host-only HttpOnly 세션 쿠키**로 충분해진다.
이에 따라 2단 네임스페이스의 부모 도메인 쿠키 근거는 약해졌으나, 결정 자체는 선례 동형성(mg)·환경 격리(아래)·미래 옵션 보존으로 충분히 선다.

## 종착 그림

- 공개면: `careerhub-web`(호스트명은 컷오버 시 확정) + Zitadel(호스트는 배치 실측 이후 확정).
- 네임스페이스: 신규 공개 호스트는 **2단 `*.careerhub.jyo-liar.com`** 아래 — 인증서에 해당 와일드카드 SAN 추가.
- api-composer·기타 백엔드: 클러스터 내부 전용 — 공개 호스트 없음.
- 레거시(front·api-composer 공개분·auth-service): 현행 경로 기반 루트 그대로 두고 컷오버 때 함께 소멸.
- IdP(Zitadel)는 careerhub 전용으로 본다 — 호스트 소속은 `*.careerhub` 계열이 자연스럽되 확정은 실측 이후.

## 환경 네임스페이스 — dev는 제품의 하위가 아니라 형제로

추후 dev 환경 도입 시 `*.dev.careerhub.jyo-liar.com`(제품 하위 중첩)이 후보로 나왔으나 기각하고, **`*.dev-careerhub.jyo-liar.com`(형제 네임스페이스)** 로 정한다.

- **쿠키 상속이 환경 경계를 뚫는다 — 기각의 결정적 근거.**
  쿠키 도메인 매칭은 서픽스 매칭이라, prod가 `Domain=.careerhub.jyo-liar.com`에 심은 쿠키는 `api.dev.careerhub.jyo-liar.com`에도 전송된다.
  prod 세션 토큰이 dev 백엔드로 흐르고, 역방향으로 dev가 공유 부모에 쿠키를 심으면 prod에 먹힌다(session fixation 계열).
  일반화: DNS 계층은 곧 쿠키 상속 계층이다 — 환경(prod/dev)은 상속 경계가 아니라 격리 경계이므로 제품 네임스페이스의 하위에 두지 않는다.
  1단 평면을 기각한 것과 같은 축이다(그때는 스코프 과대, 이번엔 상속의 경계 침범).
- **Gateway API 와일드카드는 다중 레이블 서픽스 매칭이다(규격 확인).**
  Listener·HTTPRoute 명세: "`*.example.com` would match both `test.example.com`, and `foo.test.example.com`".
  중첩이면 prod의 `*.careerhub.jyo-liar.com` 리스너가 dev 트래픽까지 잡는데, 인증서 와일드카드는 한 레이블만 커버하므로 그 트래픽에 인증서 불일치가 난다.
  형제 네이밍은 이 겹침 클래스를 통째로 제거한다.
- **인증서 비용은 무승부.**
  어느 쪽이든 환경마다 와일드카드 SAN 하나씩이다.
- **제3안 — 환경 존 우선(`*.careerhub.dev.jyo-liar.com`)은 보류.**
  prod 격리는 형제안과 동일하게 성립하고 여러 제품이 dev를 갖게 되면 확장성이 좋다.
  지금은 제품이 하나라 형제안이 mg 선례(영역별 평면 2단)와 동형이고 더 단순하다.
  dev 환경이 제품 여럿으로 번질 조짐이 보이면 그때 환경 존으로의 전환을 다시 논한다.

## 남은 게이트 — Zitadel 호스트만 실측에 걸려 있다

브로커 구조에서 Google/Naver가 보는 redirect_uri는 Zitadel의 콜백 호스트다 — **Zitadel의 호스트 선택 = redirect_uri 호스트 선택**이다.
pairwise sub가 redirect_uri 호스트(sector identifier)의 함수라면 호스트 선택이 기존 사용자의 IdP 연결을 가른다 — 사용자 데이터 레벨의 one-way door다.
이 위험 규정은 기존 논의(`260804_1831` §9)와 ADR-0030 Context가 이미 지고 있고, Zitadel 배치 실측이 판정 예정이다.
auth-service가 분리 대상에서 빠지면서, 실측에 걸린 미결은 이 하나로 좁혀졌다.

## ADR을 지금 쓰지 않기로 했다

초안 직전까지 갔다가 접었다 — 이 판정 자체가 기록할 값이다.

- **쓰자는 근거였던 것**: 리뉴얼 설계가 이 네임스페이스·공개면을 딛고, 네이밍이 쿠키 스코프라는 보안 경계를 가른다.
- **접은 근거**: ADR-0030이 이미 "배치 경로는 코드·설정의 관할"이라 선언했고, 신규 호스트·리스너·SAN은 되돌리는 데 한 시간 급이라 임계선(one-way door) 미달이다.
  진짜 one-way인 redirect_uri 호스트는 ADR-0030 Context + 배치 실측이 이미 게이트하고 있어 새 ADR 없이도 성립한다.
- **재소환 조건**: 리뉴얼이 이 전제(공개면 = web+IdP, BFF, host-only 세션 쿠키)를 딛고 설계를 굳히는 시점 — 그때부터 뒤집기가 리뉴얼 설계를 함께 무효화하므로 임계선을 넘는다.
  토큰 저장 결정 언저리에서 이 문서를 근거로 ADR을 세운다.
  공개면 판정(api-composer 내부 전용 포함)도 그 ADR의 범위다.

## 열어둔 것

- careerhub-web의 호스트명과 컷오버 방식.
- Zitadel 호스트 확정 — 배치 실측 판정 대기.
- BFF의 구현 형태(route handler 프록시 범위, 세션 쿠키 설계) — 리뉴얼 코드·토큰 저장 결정의 관할.
