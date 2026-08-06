---
type: discussion
topic: careerhub
subjects: [zitadel, jwt, oidc, auth-service, api-composer]
status: active
ref-adrs: [ADR-0028, ADR-0029, ADR-0030, ADR-0031]
---

# Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효

## 질문

ADR-0030(Zitadel 채택)·ADR-0031(발급 시점 클레임 주입)은 JWT + 데이터 경로 로컬 검증(ADR-0029) 위에 서 있다. 검토 중 세 질문이 나왔다:

1. Zitadel은 JWT 외의 방식(메모리 세션 등)으로도 인증을 지원하는가
2. 그 경로에서도 클레임 주입이 작동하는가
3. 권한 변경의 즉시 발효를 토큰으로는 어떻게 구현하고, 토큰 아닌 방식으로는 어떻게 하는가

이하는 공식 문서·소스 기준 조사 결과와, 그것이 현 proposed 초안들을 흔드는지에 대한 판정이다. 문서에서 직접 확인하지 못한 것은 **미확인**으로 표시한다.

## 조사 ① — Zitadel의 인증 경로는 JWT 하나가 아니고, JWT는 기본값도 아니다

- **opaque 액세스 토큰 + introspection — 이것이 기본값이다.** Zitadel의 기본 토큰 타입은 opaque Bearer이고([opaque tokens](https://zitadel.com/docs/concepts/knowledge/opaque-tokens)), 리소스 서버는 [introspection endpoint](https://zitadel.com/docs/guides/integrate/token-introspection)로 검증한다. 앱 단위 Token Settings에서 Bearer(opaque) ↔ JWT를 전환한다([console](https://zitadel.com/docs/guides/manage/console/applications-overview)). 즉 ADR-0029의 로컬 검증은 **설정으로 선택해서 켜는 구성**이다.
- **JWT 액세스 토큰 + 로컬 검증** — 현 초안의 전제. 위 전환의 다른 쪽.
- **Session API (v2)** — OIDC 대신 쓸 수 있는 Zitadel 고유(비표준) API. 다만 용도가 **커스텀 로그인 UI 구축**이고, 반환물은 session ID + opaque session token이며, [OIDC/SAML 토큰과의 교환이 불가능하다](https://zitadel.com/docs/guides/integrate/login/login-users). 서비스 간 인가 전파 수단이 아니다.
- **BFF 서버사이드 세션** — 프로토콜상 OIDC code flow는 그대로 돌고, 토큰은 백엔드가 보관하며 브라우저에는 세션 쿠키만 두는 구성([IETF draft-ietf-oauth-browser-based-apps](https://datatracker.ietf.org/doc/draft-ietf-oauth-browser-based-apps/), RFC Ed Queue). Zitadel 쪽에는 SDK 예제(Express·Flask) 수준으로 존재하고, 공식 권장 문서는 **미확인**. 이것은 Zitadel의 기능이 아니라 **앱 아키텍처의 선택**이다.
- 참고: Zitadel 호스티드 로그인의 쿠키는 IdP 쪽 SSO 세션용(user-agent 쿠키)이지 앱의 인증 수단이 아니다.

**"메모리 세션 방식 인증이 가능한가"에 대한 답: 가능하지만 Zitadel이 주는 것은 아니다.** Zitadel이 직접 주는 비-JWT 경로는 opaque+introspection이고, 세션 방식은 앱이 code flow 결과를 자기 세션 저장소에 옮겨 담는 BFF 구성으로 성립한다.

## 조사 ② — 클레임 주입은 "토큰"이 아니라 "발급물"에 걸린다

Actions v2의 function 트리거는 `preaccesstoken` · `preuserinfo`(+`presamlresponse`)이고([usage](https://zitadel.com/docs/guides/integrate/actions/usage)), 각각 실리는 곳이 다르다([complement-token](https://zitadel.com/docs/apis/actions/complement-token)):

| 트리거 | 주입이 실리는 곳 |
|---|---|
| `preaccesstoken` | JWT 액세스 토큰 **만** ("token type is `jwt`") |
| `preuserinfo` | ID 토큰 · userinfo 응답 · **introspection 응답** |

- **opaque + introspection 구성에서도 주입은 작동한다** — `preuserinfo` 경로로, introspection 응답에 실린다.
- **BFF 세션 구성에서도 작동한다** — code flow가 돌므로 앱은 ID 토큰/userinfo로 주입분을 받아 세션에 담으면 된다.
- 작동하지 않는 곳은 Session API 단독 경로뿐 — 애초에 OIDC 발급물이 없다.
- 주의: 실리는 곳의 직접 문장 근거는 Actions **v1** 문서이고, v2는 [마이그레이션 가이드](https://zitadel.com/docs/guides/integrate/actions/migrate-from-v1)의 1:1 대응으로 도출했다. v2 문서 자체의 재명시는 **미확인**.

**실행 시점이 발급물마다 다르다 (소스 확인).** ID 토큰·JWT 액세스 토큰에는 발급 시 1회 실행이지만, userinfo·introspection 응답은 **endpoint가 호출될 때마다** 조립되고 그때마다 action이 실행된다 — [introspect.go](https://github.com/zitadel/zitadel/blob/main/internal/api/oidc/introspect.go)가 요청마다 `TriggerTypePreUserinfoCreation`으로 [userinfo 조립](https://github.com/zitadel/zitadel/blob/main/internal/api/oidc/userinfo.go)을 부르며, 요청 간 캐시가 없다. **즉 opaque+introspection 구성의 주입은 "발급 시점" 주입이 아니라 "조회 시점" 주입이다** — 인가 데이터 공급자(auth-service)가 매 introspection에 호출된다. 별도 "인가 서비스 지정"이라는 설정 어휘는 없지만, 이 execution target 등록이 실질적으로 그 역할이다. 검증 endpoint 자체를 타 서비스로 교체하는 기능은 없다(introspection은 항상 Zitadel 자신).

오독 주의 — **target의 호출 주체는 어느 구성에서든 항상 Zitadel이다.** 리소스 서버(api-composer)가 auth-service를 직접 부르는 일은 없다: 리소스 서버는 Zitadel만 부르고, Zitadel이 응답(또는 토큰)을 조립하는 과정 안에서 auth-service를 대신 부른다. 다만 O1에서는 이 대리 호출이 요청마다 일어나므로, 가용성 관점의 실질 의존은 직접 호출과 등가다(Zitadel+auth-service 둘 다 살아야 요청이 성공) — 통신 토폴로지의 단순함(상대가 Zitadel 하나)과 가용성 결합은 별개 축이다.

**함의: 주입이라는 수단은 JWT 전제에 묶여 있지 않다 — 그러나 "발급 시점"이라는 성격은 묶여 있다.** 검증 방식을 opaque(원격)로 바꿔도 주입 자체는 살아남지만, 위의 실행 시점 때문에 그 주입은 조회 시점 주입이 된다. 접합 방식과 검증 방식은 반쯤만 독립 축이다: JWT+로컬 검증에서만 ADR-0031의 결정("요청 경로에 인가 목적의 조회를 두지 않는다")이 그 모양대로 성립한다.

## 조사 ③ — 즉시 발효: Zitadel이 주는 것과 안 주는 것

핵심 사실 셋.

**1. Zitadel의 모든 취소 수단은 introspection 경로에서만 관측된다.** revocation endpoint(RFC 7009, access/refresh 모두, refresh 취소 시 대응 access도 연쇄 취소), Session API의 세션 종료, 사용자 비활성화·삭제 — 전부 서버 상태는 즉시 바뀌지만, [introspection이 그것을 검사하고](https://zitadel.com/docs/apis/openidoauth/endpoints) 로컬 JWT 검증은 `exp`까지 볼 수 없다. 구조적이다 — ADR-0029가 산 "회수의 지연"의 정확한 모양.

**2. 권한(role) 변경은 토큰도 세션도 자동 취소하지 않는다.** 보안 이벤트별 토큰 취소의 일관화는 [open 이슈(#8288)](https://github.com/zitadel/zitadel/issues/8288)로 남아 있고, "privilege 변경 시 취소"가 그 요구 목록에 들어 있다는 것 자체가 현재는 안 된다는 방증이다. → **ADR-0031의 Consequence("상태 변경 직후 토큰 갱신 트리거가 앱 흐름의 일부가 되어야 한다")는 실측으로 확인된 필수 요건이다.** 제품이 대신해 주지 않는다.

**3. careerhub에서 권한 변경 이벤트의 원천은 IdP가 아니라 앱이다.** 인가 원장은 앱 소유이므로(ADR-0028), 권한 부여·회수·동의 완료를 가장 먼저 아는 것은 auth-service 자신이다. 즉시 발효를 위해 IdP의 이벤트 기능을 기다릴 필요가 없다 — **변경을 아는 자가 곧 전파를 시작할 수 있는 자다.**

**4. 취소의 "기록 + 트리거"는 제품에 실재한다.** 취소·종료·비활성화는 이벤트소싱 저장소에 이벤트로 영구 기록되고 — 소스 확인: [`oidc_session.access_token.revoked` · `oidc_session.refresh_token.revoked`](https://github.com/zitadel/zitadel/blob/main/internal/repository/oidcsession/oidc_session.go), [`session.terminated`](https://github.com/zitadel/zitadel/blob/main/internal/repository/session/session.go), [`user.deactivated`/`locked`/`removed`](https://github.com/zitadel/zitadel/blob/main/internal/repository/user/user.go) — Actions v2 execution은 function 외에 **event 조건**(개별 이벤트 / 이벤트 그룹 / 전체)으로 외부 endpoint를 async 호출할 수 있다([usage](https://zitadel.com/docs/guides/integrate/actions/usage)). 즉 **"취소 이벤트 → 서비스의 로컬 deny-list" 배선의 재료가 제품 쪽에 전부 있다.** 사실 1은 "로컬 검증 혼자서는 기록을 못 본다"이지 "기록·훅이 없다"가 아니다. 단 event target의 async 호출은 상태코드·응답을 다루지 않는다고 문서가 명시 — 전달 보장·재시도 세부는 **미확인**이므로, 훅을 쓰더라도 토큰 수명(TTL)이 전달 실패의 백스톱이어야 한다(ADR-0029 Consequence의 "주기 조정이 전달 실패의 백스톱" 그대로).

부가 실측:

- 액세스 토큰 수명 **기본 12h**, 설정은 인스턴스 단위(Default Settings / Admin API — [defaults.yaml](https://github.com/zitadel/zitadel/blob/main/cmd/defaults.yaml)). 앱 단위 수명 설정은 **미확인**. 발효 지연의 상한이 이 값이므로 수치는 코드·설정 관할이되, 기본값이 이 용도에 길다는 사실은 인지가 필요하다.
- **back-channel logout 지원**: v2.65 beta → **v4.11 GA**([#11277](https://github.com/zitadel/zitadel/issues/11277)). 단 이벤트 어휘가 "세션 종료"뿐 — 권한 변경 전파 수단이 아니다.
- 로그아웃 후 refresh token은 살려두는 설계라는 공식 블로그 서술이 있음 — 최신 버전 동작은 **미확인**.
- Zitadel의 SSF/CAEP(권한·보안 이벤트 push 표준) transmitter 지원은 **미확인**(문서에서 발견 못 함).

## 옵션 — 발효 지연의 스펙트럼

축: **발효 지연** / **요청 경로 결합**(무엇이 전 요청의 장애점이 되나) / **주입 경로**.

| | 발효 지연 | 요청 경로 결합 | 주입 경로 | 현 초안과의 관계 |
|---|---|---|---|---|
| **O0. JWT + 로컬 검증 + TTL 수용** | 토큰 수명 상한 | 없음 (JWKS는 캐시되는 제어 경로) | `preaccesstoken` | ADR-0029·0031 그대로 |
| **O1. opaque + introspection** | 즉시 (취소·**권한 변경까지** — 주입이 조회 시점이라) | **IdP가 전 요청의 SPOF** + **auth-service도 introspection 경로에 실림**(요청마다 서비스→Zitadel→auth-service) | `preuserinfo` → introspection 응답, **호출마다 실행** | ADR-0029가 기각한 체크타임의 IdP 경유판 — ADR-0031이 발급 경로에 한정한 제품→앱 결합이 요청 경로로 확대된다 |
| **O2. BFF 서버사이드 세션** | 즉시 (저장소 직접 갱신·파기) | 세션 저장소 | `preuserinfo` → ID 토큰/userinfo → 세션에 복사 | 프론트 아키텍처 전환 + **서비스 간 전파는 별도로 남는다** |
| **O3. O0 + 앱발 이벤트 보강** | 준즉시 (전파 지연) | 없음 (로컬 조회 유지) | `preaccesstoken` + 로컬 플래그/버전 | ADR-0029 Consequence가 예약해 둔 강화 경로 |

O3의 업계 패턴들 (좁힐수록 상태·인프라 의존이 는다):

- **짧은 TTL + refresh 재주입** — 발효 지연 = TTL. 표준 근거 [RFC 9700](https://www.rfc-editor.org/info/rfc9700/). 인프라 추가 없음, IdP 발급 부하 증가.
- **권한 버전 클레임 + 경량 대조** — 토큰에 사용자별 버전을 싣고 서비스는 저지연 저장소에서 버전 int만 비교, 불일치 시 401 → 강제 refresh. 실계 사례 [Zalando Plan B](https://github.com/zalando-stups/planb-docs/blob/master/revocations.rst)(per-user issued_before). 캐시 저장소가 새 의존.
- **jti/사용자 deny-list** — [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html) 권고 패턴. 취소분만 담아 작고 자연 만료. 캐시 장애 시 fail-open/closed 선택 문제. **deny-list를 채우는 이벤트 원천이 양쪽에 실재한다**:
  - **IdP발 (탈퇴·정지·강제 로그아웃·refresh 재사용 감지)**: Actions v2 event 훅(③-4)이 민다. event 조건은 Zitadel **내부** 이벤트에만 발화한다("any event **in ZITADEL**") — 외부 이벤트 인바운드 구독(SSF receiver 류)은 **미확인**이며, 아래 어느 배선에서도 필요하지 않다.
  - **앱발 (권한·동의 변경)**: 원천이 원장 소유자(auth-service) 자신이다. 공통 골격 — 어떤 배선이든 구 토큰이 401을 받으면 클라이언트가 refresh하고, **새 클레임 재주입은 이미 있는 발급 경로(`preaccesstoken`)가 한다**. refresh token 존치가 요건이다(재로그인 없는 재발급). 참고로 앱은 access token 원문을 갖고 있지 않아 RFC 7009 revoke를 대신 부를 수 없고, 부를 수 있는 취소 수단(세션 종료·refresh 취소)은 로그아웃·재로그인을 강제해 권한 *부여*의 UX로 과하다 — "취소"는 Zitadel에서가 아니라 서비스들의 판정에서 죽이면 충분하다.

### 앱발 전파의 두 배선 — A(직행) vs B(Zitadel 허브)

설계 요구 하나가 배선을 가른다: **타 서비스(api-composer 등)의 외부 의존 상대를 가급적 Zitadel 하나로 한정하고 싶다.**

| | **A. 앱발 직행** | **B. Zitadel 허브** |
|---|---|---|
| 배선 | auth-service → 서비스 webhook/버전 저장소 직접 갱신 | auth-service → `SetUserMetadata`(버전 범프 등 **신호만**) → 내부 이벤트 `user.metadata.set`(소스 확인: [metadata.go](https://github.com/zitadel/zitadel/blob/main/internal/repository/user/metadata.go), `user.` + `metadata.set`) → event execution → 서비스 webhook |
| 서비스의 인바운드 상대 | auth-service (+Zitadel) | **Zitadel 하나** |
| 전달 제어 | 앱이 소유 (재시도·순서를 앱이 구현) | 제품 채널 — async 호출의 재시도·순서 보장 **미확인** |
| 부작용 | 없음 | 없음 (metadata 쓰기는 로그아웃을 유발하지 않음) |
| 실패 시 | 전파만 멎고 TTL 백스톱으로 퇴화 (fail-safe) | 동일 |
| 경계 판정 | — | **ADR-0028("인가 데이터를 IdP에 넣지 않는다")을 스친다** — 버전 번호가 인가 *데이터*인가 *신호*인가. 신호(원장 없이는 무의미한 단조 카운터)로 판정하는 쪽이 유력하나 accept 심사감 |

- A의 결합 비용은 보기보다 작다: 수신 webhook은 수동 endpoint라 **가용성 결합이 ~0**이고, auth-service는 이미 발급 경로의 클레임 공급자라 간접 의존이 존재한다. A가 사는 것 = 신호 경로 단순·전달 소유. B가 사는 것 = **토폴로지 단순**(서비스 쪽 인바운드 통합·인증 대상이 Zitadel 하나).
- **B의 채택 선행 조건**: event execution의 전달 semantics(재시도·순서·유실률) 실측 + `user.metadata.set`을 개별 구독할 수 있는지 확인.
- 이 배선 선택("인가 신호가 IdP를 경유하는가")은 ADR-0028의 경계를 건드리므로, 요구가 현실화되어 채택하는 시점에 **ADR 후보**다 — 지금은 두 배선을 나란히 남긴다.
- **401 + claims challenge (이벤트 구동 취소)** — [Microsoft CAE](https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-continuous-access-evaluation)가 산업 절충점: 토큰 수명을 오히려 늘리고(28h) "시간이 아니라 이벤트가 취소를 구동". 클라이언트·서버·IdP 3자 프로토콜 합의 필요.

## 판정 — 초안이 흔들리는가

**뒤집는 사실은 없었다. 오히려 조사(②·③-2)가 두 초안의 문장을 실측으로 뒷받침한다:**

- ADR-0031의 무효화 조건("주입이 불가능해지는 경우")은 멀다 — 주입 훅은 JWT·opaque 양쪽 경로에 실재한다. 단 "발급 시점"이라는 성격은 JWT+로컬 검증(ADR-0029)과 한 몸이다: opaque로 가면 주입이 조회 시점으로 바뀌어 ADR-0031이 금지한 "요청 경로의 인가 조회"가 IdP 경유로 되살아난다. **두 초안은 각자 서는 게 아니라 서로를 전제한다.**
- ADR-0031이 Consequence로 적어 둔 "갱신 트리거는 앱 흐름의 책임"은 선택이 아니라 필수였다(제품이 안 해 준다).
- ADR-0029의 트레이드(즉시 발효 ↔ 요청 경로 무결합)는 Zitadel에서도 정확히 같은 모양으로 성립한다 — O1이 그 반대편이고, 이미 Alternatives에서 기각된 것과 같은 것이다.

**초안에 안 적혀 있고 알아둘 것:**

- JWT는 Zitadel의 기본값이 아니다 — ADR-0029의 결정이 앱 설정(Token Type = JWT)을 함의한다. 설정 자체는 코드 관할.
- 즉시 발효가 언젠가 요구가 되면, 경로는 O1(결정 개정 — ADR-0029 무효화 조건 그대로)이 아니라 **O3가 먼저다**: 재료가 양쪽에 다 있다 — 권한·동의 변경은 앱이 원천이고(③-3), 탈퇴·정지·취소는 Actions v2 event 훅이 밀어준다(③-4). ADR-0029를 개정하지 않고 갈 수 있고, 이 순서는 ADR-0029 Consequence에 이미 예약되어 있다.
- **이 검토의 위치**: 현 초안(O0) 유지를 전제로, 권한 변경의 준즉시 발효가 **예상 요구**라는 판단 아래 O3의 배선을 미리 정찰한 것이다. O3 안에서의 배선 선택(A 직행 vs B Zitadel 허브)은 열어 둔다 — 채택 시점에 ADR 후보이며, B는 전달 semantics 실측이 선행 조건이다.

**미확인 잔여** (필요해지는 시점에 재조사): 앱 단위 토큰 수명 설정 · Actions v2 문서의 introspection 반영 재명시 · event execution의 전달 보장(재시도·순서)과 구독 가능한 이벤트의 노출 범위 · 관리자가 특정 사용자의 access token을 지정 취소하는 API의 존재 여부 · SSF/CAEP 지원(송신·수신 양방향) · 로그아웃 후 refresh token의 최신 동작.

## 버린 것

- **Session API를 서비스 간 인가 전파 수단으로 검토하는 것** — OIDC 토큰과 교환 불가, 용도가 커스텀 로그인 UI 구축. 애초에 이 문제의 후보가 아니다.
- **게이트웨이/sidecar PDP (OPA · SpiceDB/Zanzibar 계열)** — careerhub의 인가는 평평한 사용자 단위 목록(ADR-0031 전제)이라, 관계형 PDP가 푸는 문제(리소스 단위 권한·관계·New Enemy Problem)가 존재하지 않는다. 고가용 인프라 비용만 산다. ADR-0031의 무효화 조건(리소스 단위 세분화)이 현실화될 때의 후보로만 남긴다.
- **O2(BFF 세션)를 즉시 발효 목적으로 채택하는 것** — 프론트 경로의 발효는 즉시가 되지만 api-composer 등 서비스 간 판정에는 여전히 토큰(또는 다른 전파)이 필요해, 문제의 절반만 풀면서 아키텍처 전환 폭이 가장 크다. 토큰 보안(브라우저 저장 제거) 목적의 별도 논의라면 모를까, 이 질문의 답은 아니다.
