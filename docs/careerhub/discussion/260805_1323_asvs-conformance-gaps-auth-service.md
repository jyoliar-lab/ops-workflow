---
type: discussion
topic: careerhub
subjects: [auth-service, api-composer, careerhub-front, jwt, oidc, google-oauth, naver, postgresql]
status: active
ref-adrs: []
---

# 제품을 안 들이고 auth-service만 고친다면 — 규격이 실제로 요구하는 것과, 줄 고치기로는 안 닫히는 것

## 0. 전제와, 이 문서가 앞의 것들과 다른 점

**전제는 고정이다.** `260804_1831_auth-rebuild-implementation-approach.md`가 **기성 IdP 제품도 외부 인가 서비스도 들이지 않는다**로 수렴했다(status `done`). 그러므로 아래 어디에도 "제품을 사면 이게 없어진다"는 선택지는 두지 않는다 — 그 판단은 이미 났고, 다시 여는 조건은 그 문서 ⑦이 갖고 있다.
`260805_1308_storage-independent-user-identifier.md`의 수렴(저장소 독립 불변 식별자)도 전제로 깔린다.

**`260804_1735_auth-service-structural-defects.md`와 무엇이 다른가.**
1735는 **코드에서 출발**해 원인이 같은 것끼리 축(A~G)으로 묶었다. 이 문서는 **규격에서 출발**한다 — OWASP ASVS 5.0의 요구사항을 원문으로 놓고, 그중 무엇이 careerhub에 걸리는지 판정한 뒤, 걸리는 것을 코드에 맞춘다. 출발점이 반대라서 세 가지가 새로 나온다:

- **순서가 달라진다.** 1735는 "축 A가 가장 무겁다"로 정렬했다. 규격은 **등급(L1/L2/L3)** 으로 정렬하고, 그러면 L1(기준선)을 못 맞추는 것 넷이 앞으로 나온다 — 그중 둘은 1735에서 축 C에 묻혀 있던 것이다.
- **관할 챕터가 우리가 생각한 곳이 아니다.** §1.1 — careerhub 자체 JWT는 V10(OAuth)의 관할이 아니라 **V9(자체완결 토큰)** 의 관할이다. 그리고 V9가 우리 결함에 정확히 이름을 붙여 둔다.
- **줄 고치기로 안 닫히는 것이 갈라진다.** §4 — 확장점·파서·비밀·저장소의 **모양** 문제다. 1735의 "(가) two-way door" 목록은 전부 줄 단위였는데, 규격 항목 중 상당수는 그 목록에 들어갈 수 없다.

**출처는 원문을 받아 읽었다** — ASVS 5.0의 `5.0/en/0x19-V10-OAuth-and-OIDC.md`·`0x18-V9`·`0x16-V7`·`0x15-V6`·`0x12-V3`·`0x25-V16`을 GitHub API로 직접 내려받아 인용한다. 아래 인용문은 전부 그 원문이다.

---

## 1. 적용 판정 — V10의 어느 절이 걸리나

V10은 절이 일곱 개이고, **역할별로 갈려 있다.** careerhub는 OIDC relying party(= OAuth client)이고 인가 서버가 아니다.

| 절 | 대상 | 항목 수 | careerhub |
|---|---|---:|---|
| V10.1 Generic | 전부 | 2 | **걸린다** |
| V10.2 OAuth Client | 클라이언트 | 3 | **걸린다** |
| V10.3 OAuth Resource Server | 리소스 서버 | 5 | **걸리지 않는다** — §1.1 |
| V10.4 OAuth Authorization Server | 인가 서버 | 16 | 비해당 |
| V10.5 OIDC Client | RP | 5 | **걸린다** |
| V10.6 OpenID Provider | OP | 2 | 비해당 |
| V10.7 Consent Management | 인가 서버 | 3 | 비해당 |

**걸리는 것은 10개다**(2+3+5). 비해당은 21개(16+2+3).
→ 260804_1831 §1이 표로 적어 둔 *"클라이언트 10개 / 인가 서버 21개"* 가 원문과 정확히 맞는다. **그 수치는 확인됐다.**

그리고 챕터 서두가 "사라"고 말하는 대상이 어느 쪽인지도 원문에서 다시 확인된다:

> *"Given the complexity of the area, it is vitally important for a secure OAuth or OIDC solution **to use well-known industry-standard authorization servers** and apply the recommended security configuration."*

`authorization servers`다. 우리는 그것을 만들지 않는다.

### 1.1 우리 JWT는 OAuth 액세스 토큰이 아니다 — 그래서 V10.3이 아니라 V9다

**api-composer가 auth-service의 JWT를 검증하는 구조는 OAuth 리소스 서버처럼 보인다.** 실제로 미들웨어 모양도 그렇다(`careerhub-api-composer/careerhub/apicomposer/middleware/middleware.go` — `Authorization` 헤더 → `ParseToken` → 401). 그래서 V10.3(리소스 서버 5개 항목)을 자기 것으로 읽고 싶어진다.

**그런데 아니다.** V10 서두가 access token을 이렇게 정의한다:

> *"The OAuth authorization server (AS) is a server application that **issues access tokens to OAuth clients**. These access tokens allow OAuth clients to access RS resources, either on behalf of an end-user or on the OAuth client's own behalf."*

> *"Access tokens, which shall only be consumed by the RS…"*

우리 JWT는 **인가 서버가 발급한 것이 아니고, 위임 인가(delegated authorization)를 나르지도 않는다.** 그것은 auth-service가 자기 사용자에게 발급한 **세션 자격증명**이다. 260804_1831 §2가 인용한 `draft-ietf-oauth-browser-based-apps` §7.1이 바로 이 구성을 *"not using OAuth"* 라고 부른다.

**그래서 관할이 옮겨간다:**

| 우리가 보던 곳 | 실제 관할 |
|---|---|
| V10.3 OAuth Resource Server (L2·L3) | **V9 Self-contained Tokens** (L1 3 + L2 4) + **V7 Session Management** |

**이 교정이 공짜가 아닌 이유는 등급이다.** V10.3은 전부 L2·L3인데, V9.1의 세 항목은 **전부 L1**이다. 즉 이름을 바로 잡는 순간 같은 결함이 "고급 요구"에서 **"기준선 미달"** 로 옮겨간다.

그리고 V9가 우리 결함에 이름을 붙여 둔다 — 아래 §2·§3에서 그대로 쓴다.

> **부수 판정:** 이름을 무엇으로 정할지 자체가 결정거리다. api-composer를 "리소스 서버"라고 부르기 시작하면 V10.3.5(sender-constrained token, DPoP/mTLS)까지 목표로 딸려 오고, "같은 앱의 백엔드"라고 부르면 V7·V9만 남는다. **§8 열린 질문 ②.**

---

## 2. L1을 못 맞추는 것 — 기준선 아래

ASVS L1은 최소 등급이다. 아래는 **L1 항목인데 현재 코드가 못 맞추는 것**이고, 등급을 어디로 잡든(§5) 전부 해당한다.

| # | 요구 (원문 요지) | 현재 코드 |
|---|---|---|
| **9.1.2** | *"only algorithms **on an allowlist** can be used to create and verify self-contained tokens… must not include the 'None' algorithm"* | **없다.** 양쪽 keyfunc이 `func(token *jwt.Token) { return j.secretKey, nil }` 로 알고리즘을 보지 않는다 — `auth-service/.../jwtresolver/jwtresolver.go:106-108`, `careerhub-api-composer/.../jwtresolver/jwtresolver.go:96-98`. `jwt.WithValidMethods` 미사용 |
| **7.4.1** | *"when session termination is triggered (such as logout or expiration), the application disallows any further use of the session… Applications using self-contained tokens will need a solution such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or **rotating a per-user signing key**"* | **로그아웃 라우트 자체가 없다.** 등록 라우트 전량(`auth_controller.go:56-61`, `user_controller.go:30-32`, `ticket_controller.go:22`, `admin_controller.go:29-34`)에 `logout` 문자열이 0건 |
| **7.4.2** | *"the application terminates **all active sessions** when a user account is disabled or deleted"* | 없다. 탈퇴가 refresh를 막는 것은 `authorized_by='DELETED'` 덮어쓰기의 **부작용**이고, 발급된 access token은 만료까지 유효하다(1735 축 C) |
| **7.2.4** | *"generates a new session token on user authentication, including re-authentication, and **terminates the current session token**"* | 새 토큰은 발급하지만 **기존 것을 종료하지 않는다.** 폐기 수단이 없으므로 원리적으로 불가능하다 |
| **3.4.2** | CORS `Access-Control-Allow-Origin`이 고정값이거나 allowlist 검증 | `AllowCredentials()`가 조건 없이 켜져 있고 origin은 단일 env값·무검증(`restapi_http.go:74`) |
| **3.4.1** | HSTS `max-age` 최소 1년 | **양쪽 레이어 어디에도 없다.** 앱에도, `jyoliar-k8s` 매니페스트 전량에도 `Strict-Transport-Security`·`add_header`·`ResponseHeaderModifier` 검색 결과 0건 |

**충족하는 L1도 적어 둔다** — 한쪽으로만 몰지 않기 위해:
`9.1.1`(서명·MAC 검증 후 신뢰) 충족 · `9.2.1`(`exp` 검증) 충족 · `10.4.x` 16개 전부 비해당 · `7.2.3`(reference token 128비트)은 reference token을 안 쓰므로 비해당(단 §4④에서 되살아난다).

> ★ **9.1.2와 7.4.1이 L1이라는 사실이 1735의 우선순위를 흔든다.** 1735는 `WithValidMethods` 부재를 축 A의 "부수 사실"로, 로그아웃 부재를 축 C(= 결정을 기다리는 one-way door)로 뒀다. 규격 기준으로는 전자가 **기준선 미달**이고, 후자는 *"결정이 필요한 옵션"* 이 아니라 **L1 요구**다. 즉 축 C에서 "C0(유지)"은 규격을 목표로 삼는 한 선택지가 아니다 — 셋(폐기 목록·발급시각 하한·사용자별 키 회전) 중 하나를 **골라야** 한다. 7.4.1 원문이 그 셋을 직접 열거한다.

---

## 3. L2에서 어긋나는 것

L2를 목표로 삼는지가 §5의 결정이다. 삼는다면 아래가 전부 걸린다.

### 3.1 토큰 — V9

| # | 요구 | 현재 |
|---|---|---|
| **9.2.2** | *"validates the token to be the **correct type** and is meant for the intended purpose before accepting the token's contents. For example, only access tokens can be accepted for authorization decisions and only ID Tokens can be used for proving user authentication"* | **정면으로 어긋난다.** claims에 종류 표시가 없고(`claims.go` 전문 — `UserId`·`AuthorizedBy`·`AuthorizedID`·`Authorities`+`RegisteredClaims`), 파서가 하나뿐이라 access↔refresh 양방향 혼용이 통과한다(1735 축 B) |
| **9.2.3** | *"only accepts tokens which are intended for use with that service (audience)"* | `aud`를 담지도 검사하지도 않는다 |
| **9.2.4** | *"if a token issuer uses **the same private key for issuing tokens to different audiences**, the issued tokens contain an audience restriction that uniquely identifies the intended audiences"* | **이 항목이 축 A의 규격상 이름이다.** 같은 HS256 키를 auth-service와 api-composer가 나눠 갖는데 audience 구분이 없다 |

### 3.2 OAuth/OIDC 클라이언트 — V10.1·V10.2·V10.5

| # | 요구 | 현재 |
|---|---|---|
| **10.1.2** | *"client-generated secrets, such as… 'code_verifier', 'state' or OIDC 'nonce', are not guessable, are **specific to the transaction**, and are securely bound to both the client and the user agent session"* | **두 곳에서 깨진다.** ⓐ 세션 서명키가 소스 하드코딩(`auth_controller.go:48`)이라 바인딩이 위조 가능하다. ⓑ **transaction별이 아니다** — state가 세션의 단일 키 `session.Values["state"]`에 저장되므로(`auth_controller.go:145-147`), 같은 브라우저에서 로그인을 두 번 시작하면 뒤엣것이 앞엣것을 덮는다. IdP가 둘이 되면 이 경합이 정상 사용 중에도 생긴다 |
| **10.2.1** | code flow의 CSRF 방어 (PKCE 또는 state) | state는 있으나 위 ⓐ로 무효. PKCE 없음 |
| **10.2.2** | *"if the OAuth client can interact with **more than one** authorization server, it has a defense against mix-up attacks"* | 지금은 IdP가 하나라 비해당. **Naver를 붙이는 순간 발동**(260804_1831 §8) |
| **10.2.3** (L3) | 필요한 scope만 요청 | 현재 2개(`userinfo.email`·`userinfo.profile`). `openid` 추가가 오히려 필요한 방향 |
| **10.5.1** | ID Token replay 방어 — `nonce` 대조 | **불가능.** ID Token을 안 받는다 |
| **10.5.2** | *"uniquely identifies the user from ID Token claims, usually the 'sub' claim"* | **불가능.** 현재는 userinfo REST 응답의 `sub`를 쓴다(`ooauth/google.go:78`) — 검증된 토큰이 아니라 **API 응답**이다 |
| **10.5.3** | issuer URL이 사전 설정값과 정확히 일치하는지 | discovery를 안 쓰고 `google.Endpoint`가 하드코딩이라 형식상 노출은 없으나, 검증 지점 자체가 없다 |
| **10.5.4** | ID Token의 `aud`가 `client_id`와 같은지 | **불가능.** 같은 이유 |

> **10.5.1·10.5.2·10.5.4가 한 원인에서 나온다** — `openid` scope 부재. 세 항목을 각각의 티켓으로 쪼갤 수 없고, 하나의 구조 변경(§4①)이 셋을 함께 연다. **공동무효 후보다.**

### 3.3 IdP 연동 — V6.8

| # | 요구 | 현재 |
|---|---|---|
| **6.8.1** | 다중 IdP에서 *"the user's identity cannot be spoofed via another supported identity provider"* — IdP ID를 네임스페이스로 | **충족.** `UNIQUE (authorized_by, authorized_id)`. 단 `UNIQUE(email)`이 반대 방향으로 남아 있다(260805_1245 §5①) |
| **6.8.2** | 인증 assertion의 **서명 존재와 무결성**을 항상 검증, 미서명은 거부 | **해당 assertion이 없다.** 로그인 근거가 서명된 assertion이 아니라 REST 응답이다 |
| **6.8.4** | `acr`·`amr`·`auth_time`으로 인증 강도를 확인하거나, *"the application must have a **documented fallback approach** that assumes that the minimum strength authentication mechanism was used"* | claim을 받을 자리가 없다 → **문서화된 대체 방침**이 요구된다. 없다 |

### 3.4 문서화가 요구인 것 — 이 저장소의 일

**규격이 코드가 아니라 문서를 요구하는 자리가 있다.** 이 저장소가 그 자리다.

| # | 요구 |
|---|---|
| **7.1.1** | 세션 **비활성 타임아웃과 절대 최대 수명**을 문서화. NIST SP 800-63B 재인증 요구에서 벗어나면 그 근거도 |
| **7.1.2** | 계정당 **동시 세션 수**와, 상한 도달 시 동작을 문서화 |
| **7.1.3** | 페더레이션 생태계에서 세션을 만드는 **모든 시스템**과, 수명·종료 조정 통제를 문서화 |
| **6.1.1** | rate limiting·anti-automation·adaptive response를 **어떻게 구성하고 어떻게 악의적 락아웃을 막는지** 문서화 |
| **6.1.3** | 인증 경로가 여럿이면 각각의 통제와 인증 강도를 문서화 |
| **16.1.1** | 로깅 인벤토리 — 무엇을 어디에 얼마나 남기는지 |

현재 이 여섯 항목의 답이 **어디에도 없다.** 그리고 이것은 규격 미달이기 전에 1735 §8③이 지적한 것과 같은 종류다 — *"이 질문에 대한 답이 어디에도 기록되어 있지 않다는 것 자체가 결함이다."*

**주의 — 이게 곧 ADR이라는 뜻은 아니다.** CLAUDE.md §3은 생존형 문서를 두지 않는다. "타임아웃 30분"은 코드가 답할 값이고(§4①), ADR이 담을 것은 *"세션을 무엇으로 들고 어떻게 끝내는가"* 같은 되돌리기 어려운 축뿐이다. **규격이 요구하는 "문서화"를 이 저장소의 문서 3종으로 어떻게 받을지는 그 자체가 판단거리다 — §8 열린 질문 ⑤.**

### 3.5 로깅·anti-automation

| # | 요구 | 현재 |
|---|---|---|
| **16.2.5** | 민감정보 로깅 — *"session tokens, may only be logged by being hashed or masked"* | **토큰 원문이 적재된다** — `jwtresolver.go:113,115`의 `fmt.Errorf("%s %s", err.Error(), tokenString)`. **api-composer 쪽은 이미 고쳐졌다**(해당 사본에 `tokenString` 연결이 없고 401로 끊는다) — 두 사본이 갈라진 또 하나의 증거 |
| **16.3.1** | *"all authentication operations are logged, including successful and unsuccessful attempts"* | **성공 로그인 이벤트가 없다.** 지금 로그는 에러 로그뿐이다 |
| **16.3.2** | 실패한 인가 시도 로깅 | 403을 쓰는 `CheckHasAuthority`(`middleware.go:57-72`)에 로그가 없다 |
| **16.5.1** | 예기치 않은 오류에 **일반 메시지** | auth-service는 파싱 실패에 500(`middleware.go:24-26`) — api-composer는 같은 상황에 401 + `MessageUnauthorized` 일반 문구. **시맨틱이 갈렸다** |
| **6.3.1** | credential stuffing·brute force 방어를 문서대로 구현 | rate limit·throttle 구현이 저장소 전체에 없다(`golang.org/x/time`이 `go.sum`에만 있고 코드 참조 0건) |

---

## 4. 구조적 개선 포인트 — 줄 고치기로는 안 닫히는 것

**여기가 이 문서의 핵심이다.** 위 항목 중 상당수는 1735의 "(가) two-way door" 목록에 들어갈 수 없다 — **모양을 바꿔야 닫힌다.**

### ① `Ooauth` 인터페이스가 안티패턴을 계약으로 굳혔다

확장점 전문(`auth_service/restapi/ooauth/ooauth.go`):

```go
type Ooauth interface {
	GetAuthServer() domain.AuthorizedBy
	GetLoginURL(state string) string
	Oauth2Config() *oauth2.Config
	GetToken(ctx context.Context, code string) (*oauth2.Token, error)
	GetUserInfo(ctx context.Context, authToken *OauthToken) (*UserInfo, error)
}
```

**세 군데가 구조적으로 잘못돼 있다.**

- **`GetUserInfo(ctx, *OauthToken) (*UserInfo, error)`** — "액세스 토큰으로 userinfo를 긁어 정체성을 만든다"가 **프로바이더 확장점의 계약**이다. RFC 6819 §4.4.2.6이 *"Token Substitution (OAuth Login)"* 이라고 이름 붙인 바로 그것이고, 260804_1831 §6이 "1번이 왜 타협 불가인가"로 한 절을 할애한 것이다.
  → **Naver를 붙인다는 것은 이 메서드를 한 번 더 구현한다는 뜻이다.** 즉 **확장점이 결함을 복제한다.** 지금까지는 프로바이더가 하나라 결함도 하나였다.
- **`GetLoginURL(state string) string`** — 입력이 `state` 하나, 출력이 URL 하나다. **PKCE `code_verifier`도 `nonce`도 돌려줄 자리가 없다.** 즉 **시그니처가 PKCE·nonce의 부재를 인코딩하고 있다.** 10.1.2·10.2.1·10.5.1을 닫으려면 이 시그니처가 바뀐다 — "google.go에 `S256ChallengeOption()`을 붙인다"로 끝나지 않는다.
- **`Oauth2Config() *oauth2.Config`가 인터페이스에 있다** — `ClientSecret`을 담은 설정 객체가 확장점 밖으로 나간다. 실제로 `GetLoginURL`·`GetToken`이 자기 안에서 이걸 다시 부르므로(`google.go:41,49`) 외부 노출의 필요가 없다.

**→ 개선의 모양:** 확장점을 *"토큰을 주면 사용자 정보를 준다"* 에서 **"왕복을 시작하고, 왕복을 끝내면 검증된 정체성만 나온다"** 로 다시 그린다. 대략:

```go
BeginAuth() (redirectURL string, tx AuthTransaction, err error)      // state·nonce·verifier를 tx가 소유
CompleteAuth(ctx, code string, tx AuthTransaction) (*VerifiedIdentity, error)
```

핵심은 **미검증 IdP 토큰이 인터페이스 밖으로 안 나오는 것**이다. 그러면 새 프로바이더 구현자가 안전한 경로만 채울 수 있다 — CLAUDE.md §8의 *"할 수 없게 만든다"* 가 코드 안에서 성립하는 자리다.

부수: `json.Unmarshal(userInfo, &authUser)`의 반환 에러를 버린다(`google.go:75`) — 파싱 실패 시 빈 `UserInfo`가 그대로 흘러간다. `validate:"nonzero"` 태그는 이 경로에서 실행되지 않는다(1735 축 E).

### ② 토큰 파서가 하나다 — 9.2.2는 파서 분리를 요구한다

`ParseToken(tokenString)` 하나가 **access·refresh·`Authorization` 헤더·요청 바디**를 전부 받는다. 검사하는 것은 서명·`exp`·`UserId != ""` 셋뿐이다.

9.2.2를 만족한다는 것은 *"이 토큰이 이 자리에 놓일 종류인가"* 를 검증한다는 뜻이고, 그러려면 **종류가 토큰 안에 있어야 하고, 검증 경로가 자리마다 갈라져야 한다.** 이것은 claims 구조체 + 발급 + 파서 + 호출부 전부를 건드린다.

**그리고 이 변경은 ①과 짝이다** — ID Token(IdP가 준 것)·자체 access token·자체 refresh token 셋이 동시에 도는 순간 *"세 종류가 서로의 자리에서 통과하지 않는다"* 가 요구가 된다(260804_1831 §6-23, RFC 8725 §3.11·§3.12).

### ③ 비밀 하나가 여러 용도를 겸한다

- `SECRET_KEY` → JWT HS256 서명 키
- 같은 값의 `sha256` → `authToken` 봉투 AES-GCM 키(`restapi_http.go:43`)
- 세션 쿠키 서명 → 별도지만 **하드코딩 `"secret"`**(`auth_controller.go:48`)

9.2.4가 요구하는 것은 audience 구분이지만, **더 싼 답은 용도별로 키를 나누는 것**이다(OWASP JWT 치트시트: *"A different secret must be used for each (issuer, audience) pair"*). 이건 값 하나 바꾸는 일이 아니라 **키 발급·주입·회전 경로를 만드는 일**이다 — 현재 ESO `Password` 생성기 하나가 `CreatedOnce`로 만들어 두 Deployment에 `envFrom`으로 뿌린다(1735 축 A). 그 배선이 바뀐다.

### ④ ★ 트랜잭션 저장소와 세션 저장소가 같은 하나의 결정이다

**이게 이 문서에서 가장 값진 발견이다.**

- **10.1.2**는 state·nonce·PKCE verifier가 *"specific to the transaction"* 이기를 요구한다. 지금은 서명 쿠키의 단일 키에 산다 → **트랜잭션 레코드가 필요하다.**
- **7.4.1**은 자체완결 토큰을 쓸 때 폐기 수단(목록·발급시각 하한·사용자별 키 회전) 중 하나를 요구한다 → **세션 상태가 필요하다.**
- **7.4.2**는 계정 비활성/삭제 시 전 세션 종료를 요구한다 → 같은 상태를 조회·무효화할 수 있어야 한다.

**셋 다 "auth-service가 인증 관련 상태를 갖는다"는 같은 성질을 요구한다.** 1735는 이것을 축 C(폐기) 하나로만 봤는데, 규격에서 보면 **OAuth 왕복 쪽(축 D)에서도 같은 요구가 나온다.** 즉 축 C와 축 D의 일부가 **공동무효 관계**다(CLAUDE.md §4③) — 상태를 들이기로 하면 둘 다 열리고, 안 들이기로 하면 둘 다 닫히지 않는다.

> **판정 후보:** 축 C를 단독 ADR로 쓰려던 계획(1735 §4-나)이 흔들린다. 결정 문장은 *"세션을 폐기 가능하게 한다"* 가 아니라 **"auth-service는 인증 트랜잭션과 세션의 상태를 소유한다"** 쪽일 수 있다. 그러면 폐기·rotation·state 바인딩·동시 세션 상한(7.1.2)이 전부 그 아래의 코드 관할이 된다.

### ⑤ 세션과 토큰이 코드에서 같은 것이다

규격은 **V7(세션)과 V9(토큰)을 갈라 본다.** 코드는 하나로 본다 — `jwtresolver`가 발급·검증·미들웨어(`CheckHasRole`)까지 겸한다. 260804_1831 §10이 *"불투명 세션 식별자를 기본값으로"* 로 기울어 둔 축이고, 그 선택이 서면 이 겸직이 갈라진다.

### ⑥ 관측이 인증 이벤트를 모른다

16.3.1·16.3.2가 요구하는 것은 "에러를 잘 남겨라"가 아니라 **인증·인가 이벤트를 남겨라**다. 지금 코드에는 성공 경로에 로그 지점이 아예 없다. 이건 한 줄 추가가 아니라 **무엇을 이벤트로 볼지 정하는 일**이고, 16.1.1(인벤토리 문서화)과 함께 온다.

### ⑦ anti-automation이 없고, 그것을 어디에 둘지도 안 정해져 있다

6.1.1은 **문서화**를 요구하고 6.3.1은 **구현**을 요구한다. 지금은 둘 다 없다. 그리고 이건 앱 안일 수도(미들웨어) 게이트웨이일 수도(nginx-proxy) 있어서 **배치 결정**이 선행한다 — 매니페스트에도 해당 설정이 없음을 확인했다.

---

## 5. ★ 등급 목표 자체가 정해져 있지 않다 — 이것이 나머지 전부의 스코프다

**ASVS는 L1/L2/L3 세 등급이고, careerhub가 어디를 목표로 하는지가 어디에도 없다.** 그런데 이 답이 §2·§3의 범위를 통째로 바꾼다:

| 목표 | 무엇이 걸리나 |
|---|---|
| **L1** | §2의 여섯 항목만. §3은 **전부 비해당** — PKCE도 nonce도 ID Token도 audience도 L2다 |
| **L2** | §2 + §3 전부. 사실상 이 문서 전체 |
| **L3** | 위 + sender-constrained token(DPoP/mTLS)·PAR·per-response CSP 등. 개인 프로젝트 규모에서 근거 없음 |

**옵션과 이기는 조건:**

- **G1. L1을 목표로 한다.** 가장 싸다. 알고리즘 allowlist·세션 종료·CORS·HSTS만 닫는다. **이기는 조건:** 서비스가 VPN 뒤에 계속 있거나, 공개해도 노출 데이터가 이메일·이름뿐이라는 판단이 설 때. **지는 조건:** ID Token 부재(§3.2)가 남는다 — 그건 L2 항목이지만 **로그인의 근거 자체가 위조 가능하다는 뜻**이라, 등급으로 유예하기에 성격이 다르다.
- **G2. L2를 목표로 한다.** 이 문서 전체가 작업 목록이 된다. **이기는 조건:** 공개 전환을 실제로 할 때. 260804_1831 §6이 "필수"로 뽑은 23개 목록이 대체로 L2 수준이므로, **이미 그 문서가 사실상 L2를 전제했다.**
- **G3. L2를 목표로 하되 예외를 명시적으로 적는다.** ASVS 자신이 이 형태를 허용한다 — 6.3.3이 *"Relaxing any of the considerations in this requirement requires a **fully documented rationale** and a comprehensive set of mitigating controls"*, 6.8.4가 *"documented fallback approach"*. **이기는 조건:** 대부분. 소셜 전용이라 6.2(비밀번호)·6.4(복구)·6.3.3(MFA)이 통째로 IdP에 이전되는데, 그것이 "충족"인지 "문서화된 예외"인지 판정이 필요하기 때문이다(260805_1245가 그 판정의 재료를 이미 모아 뒀다).

**→ 이것이 이 논의의 가장 값싼 산출물이다.** 한 줄이면 정해지고, 정하는 순간 나머지 전부의 스코프가 갈린다. 그리고 **되돌리기가 싸다**(목표를 올리는 데 마이그레이션이 없다) → §4② 임계선 미달, **ADR이 아니라 티켓·문서 한 줄**일 가능성이 높다.

---

## 6. 옵션 — §4의 구조 축별 발산

### 축 ① 프로바이더 확장점

- **① -0. 유지 + `openid` scope만 추가.** ID Token을 받되 `GetUserInfo`는 그대로 둔다. 가장 싸지만 **10.5.x를 못 닫는다** — 검증 지점이 인터페이스 밖에 없어 프로바이더마다 다시 짜게 된다. Naver 구현자가 안 하면 그만이다.
- **① -1. 확장점을 `BeginAuth`/`CompleteAuth`로 다시 그린다.** 미검증 토큰이 밖으로 안 나온다. **이기는 조건:** IdP가 둘 이상이 되는 것이 확정일 때(→ 확정이다, Naver). **지는 조건:** 지금 인터페이스를 쓰는 컨트롤러·서비스가 함께 바뀐다.
- **① -2. `coreos/go-oidc`나 `zitadel/oidc`의 `pkg/client/rp`를 확장점 자리에 끼운다.** 260804_1831 §3의 표가 각 라이브러리의 구멍을 이미 실측해 뒀다(`go-oidc`는 nonce 미검증, `goth`는 프로바이더마다 다름). **이기는 조건:** 우리 확장점을 라이브러리 모양에 맞출 용의가 있을 때. **주의:** Naver는 어느 쪽도 네이티브 지원이 없어 generic OIDC로 붙게 된다.
- **① -3. Naver를 붙이기 전까지 미룬다.** 지금 프로바이더가 하나라 결함도 하나다. **지는 조건:** Naver 구현이 현재 인터페이스로 먼저 들어가면 그때는 두 벌을 고쳐야 한다 — **순서가 비용을 정한다.**

### 축 ④ 상태 소유

- **④ -0. 무상태 유지.** 7.4.1·7.4.2(L1)를 못 맞춘다. 등급 목표가 L1이어도 **L1에서 걸린다.**
- **④ -1. 최소 상태 — 사용자 행에 `sessions_valid_after` 하나.** 7.4.1이 명시적으로 허용하는 셋 중 하나(*"disallowing tokens produced before a per-user date and time"*). 로그아웃·정지·탈퇴가 전부 이 컬럼 UPDATE로 닫힌다. **테이블이 안 늘고 무한히 자라지 않는다.** 단 10.1.2(트랜잭션별 state)는 안 닫힌다.
- **④ -2. 세션 테이블 + 트랜잭션 테이블.** 불투명 세션 식별자로 가는 길(260804_1831 §10의 기본값)과 같다. 7.x와 10.1.2가 함께 닫힌다. 상태가 는다.
- **④ -3. 세션은 ④-1, 트랜잭션은 짧은 수명 저장소(캐시/DB) 별도.** 둘의 수명이 다르다는 점(세션 시간~일 / 트랜잭션 분)을 인정하는 안. **이기는 조건:** ④-2의 전면 전환이 부담일 때.

### 축 ② 토큰 종류

- **② -0. 유지.** 9.2.2 미충족. refresh↔access 혼용이 남는다.
- **② -1. claims에 종류 필드 + 파서에서 대조.** 최소 변경. `typ` 헤더나 커스텀 claim.
- **② -2. 종류별 타입·발급·검증 분리.** 컴파일 타임에 자리를 틀리게 만든다. **④-2로 가면 refresh token 자체가 없어질 수 있어** — 이 축과 ④가 상호작용한다.

---

## 7. 검토하고 버린 것

- **V10.3(리소스 서버) 요구를 api-composer에 적용하는 것** — 우리 JWT는 인가 서버가 발급한 access token이 아니다(§1.1). 적용하면 DPoP/mTLS(10.3.5, L3)까지 스코프에 들어와 규모에 안 맞는 일을 한다. 단 **이름을 어떻게 부를지는 열어 둔다**(§8②).
- **"ASVS 전 항목 준수"를 목표로 잡는 것** — 등급 개념을 무시하는 것이고, 챕터 절반이 애초에 비해당(인가 서버 21개)이다. §5의 등급 선택이 선행이다.
- **§3의 항목들을 개별 티켓으로 평평하게 쪼개는 것** — 10.5.1·10.5.2·10.5.4는 원인이 하나(§3.2)이고, 7.4.1·7.4.2·10.1.2는 요구하는 성질이 하나다(§4④). 평평하게 쪼개면 **같은 구조 변경을 세 티켓이 각각 절반씩 하게 된다.**
- **1735의 "(가) two-way door" 목록에 §4의 항목을 얹는 것** — (가)의 정의가 *"되돌리는 데 한 시간이 안 걸리고 어떤 결정이 나든 방향이 안 바뀌는 것"* 인데, ①②④는 셋 다 그 정의를 못 만족한다. **다만 반대 방향의 교정은 있다** — 9.1.2(알고리즘 allowlist)와 16.2.5(토큰 원문 로깅)는 (가)에 이미 있고 **L1이므로 순서가 앞으로 온다.**
- **api-composer 쪽 사본을 기준으로 auth-service를 맞추는 것** — composer 사본이 401·일반 문구·토큰 미로깅으로 **일부는 이미 낫다**(§3.5). 그러나 그 사본에도 `WithValidMethods`가 없고 `CreateToken`이 살아 있다. 어느 쪽도 기준이 아니다.
- **규격 문서화 요구(§3.4)를 그대로 문서 6개로 만드는 것** — CLAUDE.md §3에 생존형 문서가 없다. 어떻게 받을지는 §8⑤.

---

## 8. 열린 질문 — 사람의 것

1. **ASVS 등급 목표를 무엇으로 잡나**(§5). 가장 싸고, 나머지 전부의 스코프를 정한다. **먼저 답해야 하는 질문이다.**
2. **api-composer를 무엇이라고 부르나**(§1.1). "같은 앱의 백엔드"면 V7·V9만 남고, "리소스 서버"면 V10.3이 딸려 온다. 1735 §8③(*"두 서비스를 같은 신뢰 도메인으로 볼 것인가"*)과 같은 질문의 규격 쪽 얼굴이다.
3. **`Ooauth` 확장점을 Naver 전에 고칠 것인가, Naver와 함께 고칠 것인가, 나중으로 미룰 것인가**(§6 축 ①). **순서가 비용을 정한다** — 현재 인터페이스로 Naver가 먼저 들어가면 고칠 대상이 두 벌이 된다.
4. **auth-service가 인증 상태를 소유할 것인가**(§4④·§6 축 ④). 7.4.1·7.4.2가 L1이므로 *"안 한다"* 는 등급 목표가 L1이어도 성립하지 않는다. 남은 선택은 **얼마나** 갖느냐다.
5. **규격이 요구하는 "문서화"(7.1.x·6.1.x·16.1.1)를 이 저장소의 문서 3종으로 어떻게 받나**(§3.4). 값(타임아웃 분)은 코드의 관할이고 ADR은 축만 담는데, 규격은 값의 문서화를 요구한다. **하네스와 규격이 어긋나는 자리이므로 마찰 로그 후보이기도 하다.**
6. **anti-automation을 앱에 둘 것인가 게이트웨이에 둘 것인가**(§4⑦). 배치 결정이 구현보다 먼저다.
7. **성공 인증 이벤트를 무엇으로 정의하나**(§4⑥·16.3.1). 로그인 성공·토큰 갱신·권한 부여 중 무엇까지가 "authentication operation"인지가 로그 인벤토리(16.1.1)의 입력이다.

---

## 다음 단계 후보 (수렴 시)

- **§5(등급 목표)가 먼저 닫힌다.** 되돌리기가 싸므로 ADR이 아니라 티켓 또는 이 문서의 한 줄로 끝날 가능성이 높다. 닫히면 아래 전부의 스코프가 확정된다.
- **§2의 L1 항목 여섯은 결정을 기다리지 않는다** — 1735 §4-(가)와 같은 성질이고, 그중 9.1.2·16.2.5는 이미 그 목록에 있다. target `jyoliar-careerhub/auth-service`·`careerhub-api-composer`·`jae2274/jyoliar-k8s`(HSTS). 근거 ADR 불요(리프).
  - 단 **7.4.1·7.4.2는 L1이지만 (가)가 아니다** — §4④의 결정에 종속된다. L1 목록에서 이 둘만 성격이 다르다.
- **§4④가 ADR 초안 후보로 가장 유력하다.** 결정 문장 후보: *"auth-service는 인증 트랜잭션과 세션의 상태를 소유한다."* 1735의 축 C 단독 ADR 계획을 대체할 수 있다 — **공동무효 판정(§4③)을 실제로 돌려 봐야 한다.**
- **§4①이 두 번째 초안 후보다.** 결정 문장 후보: *"IdP 연동의 확장점은 검증된 정체성만 밖으로 낸다."* 되돌리기 비용은 프로바이더 수에 비례해 오르므로 **Naver 전이 가장 싸다** — 260805_1308의 "지금은 가역, 나중은 불가역" 과 같은 형태의 비용 비대칭이다.
- **§4②·③·⑤는 위 둘에 종속되거나 코드의 관할**로 보인다. ②는 ④의 결과에 따라 refresh token 자체가 사라질 수 있고, ③은 키 배선 티켓이며, ⑤는 세션 매체 결정(260804_1831 남은 질문 2)의 귀결이다.
- **§3.2의 세 항목(10.5.1·10.5.2·10.5.4)은 한 티켓으로 묶는다** — 원인이 하나다.
- 260804_1831의 "다시 열 트리거"(⑦)를 물려받을 자리 문제는 여전히 미해결이다. 이 문서도 그 답이 아니다.
