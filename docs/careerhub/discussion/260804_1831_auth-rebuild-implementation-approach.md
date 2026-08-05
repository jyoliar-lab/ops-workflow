---
type: discussion
topic: careerhub
subjects: [auth-service, google-oauth, oidc, jwt, api-composer, naver, dex, zitadel, keycloak, openfga]
status: done
---


> **결말(2026-08-05)** — **기성 IdP 제품도 외부 인가 서비스도 도입하지 않는다. auth-service 안에서 고친다**(크게는 구조 개선, 일이 커지면 리뉴얼).
> 판단 근거는 소셜 전용이라 제품 값의 절반이 사표라는 것에 더해, 논의 중 사람이 짚은 두 가지다 — **Dex는 OIDC 클라이언트 코드를 줄이지 못하고**, **사용자 원장을 나누면 지금 원자적인 트랜잭션이 두 시스템에 걸친다**. 아래 "✔ 수렴" 절에 근거와 **다시 열 트리거**를 적었다.
> 이 판단 자체는 현 상태 유지라 되돌리기가 싸므로 ADR을 파생시키지 않는다. 임계선을 넘는 축(서명 키 체계·정체성 저장 모델·세션 매체)은 이 문서 밖에 남는다.

# auth-service를 다시 짓는다면 로그인을 무엇으로 구현하나 — 직접 구현과 기성 IdP 사이

## 물음

auth-service의 인증 설계가 여러 곳에서 어긋나 있고, 손을 댈 거면 크게 대는 편이 낫겠다는 판단이 섰다.
그래서 묻는다: **다시 짓는다면 무엇으로 짓나. 다중 IdP 로그인을 구현할 때 보통 무엇을 쓰나.**

전제는 이렇다. 로그인은 **소셜 전용**이고 비밀번호가 아예 없다. 지금은 Google 하나이고 Naver를 추가하려 한다.
백엔드는 Go, 저장소는 PostgreSQL, 배포는 arm64 홈랩 쿠버네티스다.
그리고 auth-service 안에는 인증 외에 **권한(authority)·초대티켓(ticket)·약관동의(agreement)** 도메인이 함께 들어 있다.

---

## 1. "인증 솔루션"이라는 범주가 실은 둘이다

이 구분을 놓치면 조사 결과를 통째로 잘못 읽게 된다.

| | 하는 일 | OWASP ASVS 5.0 V10의 요구사항 수 |
|---|---|---:|
| **OIDC 클라이언트 (Relying Party)** | "Google·Naver에서 **로그인 결과를 받아** 내 사용자를 식별한다" | **10개** |
| **인가 서버 (Authorization Server / OpenID Provider)** | "**내가** 인증하고 토큰을 발급한다. 남의 앱이 내 토큰을 쓴다" | **21개** |

careerhub는 전자다. 프론트와 백엔드가 같은 도메인에 있고, 제3자 앱에 토큰을 내주지 않는다.

**그리고 업계가 "직접 만들지 말고 가져다 쓰라"고 말하는 대상은 후자다.** ASVS 5.0의 OAuth·OIDC 장이 그 문장을 갖고 있다:

> *"Given the complexity of the area, it is vitally important for a secure OAuth or OIDC solution **to use well-known industry-standard authorization servers** and apply the recommended security configuration."*

**클라이언트를 직접 구현하지 말라는 1차 출처는 찾지 못했다.**
흔히 인용되는 *"인증을 직접 만들지 마라(don't roll your own auth)"* 라는 문장은 **OWASP Authentication Cheat Sheet에 존재하지 않는다** — 원본 마크다운을 받아 `roll your own`·`build your own`·`from scratch`·`own implementation`을 전수 검색해 확인했다. Secure Product Design·Cryptographic Storage 치트시트에도 없다.

실제로 존재하는 가장 강한 근거는 2025년에 새로 생긴 **OWASP Top 10:2025 A07**이다:

> *"**Ideally**, use a premade, well-trusted system to handle authentication, identity, and session management. Transfer this risk **whenever possible** by buying and utilizing a hardened and well tested system."*

같은 목록의 다른 항목들이 *"Do not ship…"*, *"Implement…"* 처럼 단정적인데 **이 항목만 조건부**다. 규범이 아니라 권고다.

**요구사항의 개수보다 성격이 다르다.** 클라이언트 쪽 10개는 전부 *"이 값을 검증해라"* 형태다 — ID Token의 `aud`가 내 client_id인지, `iss`가 일치하는지, `nonce`가 보낸 값과 같은지. 검증 로직 몇 줄~수십 줄 범위다.
반면 인가 서버 쪽 21개는 **별도 시스템을 짓는 일**이다: PAR, JAR, mTLS·DPoP 같은 sender-constrained 토큰, private_key_jwt, 동적 클라이언트 등록 방어, refresh token 회전과 연쇄 폐기, 동의 화면과 동의 철회, 관리자용 토큰 폐기 UI.

**이 둘은 같은 종류의 일이 아니다.**

---

## 2. 이 구조에는 이미 표준 문서상의 이름이 있다

IETF OAuth 워킹그룹의 `draft-ietf-oauth-browser-based-apps-27`(2026-07, **BCP 예정**, IESG 승인 후 RFC 번호 대기)은
**§7.1 "Single-Domain Browser-Based Applications (not using OAuth)"** 라는 절을 갖고 있다. 원문:

> *"**Too often, simple applications are made needlessly complex by using OAuth to replace the concept of session management.** A typical example is the modern incarnation of a server-side MVC application, which now consists of a browser-based frontend backed by a server-side API.*
>
> *In such an application, **the use of OpenID Connect to offload user authentication to a dedicated provider can significantly simplify the application's architecture and development. However, the use of OAuth for governing access between the frontend and the backend is often not needed. Instead of using access tokens, the application can rely on traditional cookie-based session state to keep track of the user's authentication status.**"*

그리고 §7.1.1이 이 패턴의 위협 분석을 붙인다:

> *"Due to the lack of using OAuth, this architecture pattern is **only vulnerable to the following attack scenarios: Proxying Requests via the User's Browser.**"*

문서가 비교하는 여러 패턴 중 **공격면이 가장 좁다.**

즉 **"소셜 로그인으로 인증만 위임하고 자체 세션을 든다"는 임시방편이 아니라, 표준화 기구가 권장 조건과 위협 분석까지 붙여 문서화한 정식 패턴이다.** careerhub가 하려는 것이 정확히 이것이다.

**공정하게, 같은 절이 반대 논거 넷도 함께 적어 뒀다:**

> *"there are still some advantages in using OAuth even in a common-domain architecture:*
> *· Allows more flexibility in the future, such as if you were to later add a new domain to the system.*
> *· Being able to take advantage of existing library support rather than writing bespoke code for the integration.*
> *· Centralizing login and multi-factor authentication support, account management, and recovery at the OAuth server, rather than making it part of the application logic.*
> *· Splitting of responsibilities between authenticating a user and serving resources"*

셋째 항목이 careerhub에 걸리는 유일한 것인데, **비밀번호가 없으므로 중앙화할 MFA·계정 복구가 애초에 없다.**

---

## 3. 그러면 실무에서 보통 무엇을 쓰나

소셜 로그인만 받는 경우, **지배적 선택은 IdP 제품이 아니라 RP 라이브러리다.** Google 자신의 OpenID Connect 문서가 제품이 아니라 라이브러리를 권한다:

> *"Given the security implications of getting the implementation correct, **we strongly encourage you to take advantage of a pre-written library or service.**"*

Go 생태계에서 실제로 쓸 수 있는 것들을 확인했고, **셋 다 서로 다른 구멍이 있다.**

| | `markbates/goth` | `coreos/go-oidc` | `zitadel/oidc`의 `pkg/client/rp` |
|---|:--:|:--:|:--:|
| 프로바이더 어댑터 | **74종** (`naver`·`kakao`·`line`·`apple` 포함) | 없음 | 없음 |
| OIDC discovery | 부분 | 있음 | 있음 |
| ID Token 서명 검증 | **프로바이더마다 다름** | 있음 | 있음 |
| `nonce` 생성·저장·대조 | 없음 | **검증은 호출자 책임** | **있음** |
| PKCE challenge 생성 | **저장소 전체에 없음** | 없음 | 있음 |
| PKCE verifier·state 왕복 보관 | 부분 | 없음 | **있음** |

확인한 두 함정:

- **`go-oidc`는 nonce를 검증하지 않는다.** 소스 주석 원문: *"Verify parses a raw ID Token, verifies it's been signed by the provider… **Verify does NOT do nonce validation, which is the caller's responsibility.**"*
- **`goth`는 프로바이더마다 검증 수준이 다르다.** `apple`은 JWKS를 받아 `aud`/`iss`까지 검증하는데, `openidConnect` 프로바이더는 **서명 검증 없이 payload를 base64 디코드만 한다.** PKCE challenge를 만드는 코드는 저장소 어디에도 없다.

**즉 라이브러리를 쓰더라도 "무엇을 검증하는지"는 직접 확인해야 한다.** 프로토콜 배관은 줄여주지만 검증 책임을 대신 져 주지 않는다.

참고로 JavaScript 진영의 성숙한 두 라이브러리는 **계정 연결 정책에서 정반대 결론에 도달했다.**
Auth.js: *"**it is not secure to automatically link accounts between arbitrary providers on sign-in**, which is why this feature is generally not provided by an authentication service and is not provided by Auth.js."*
better-auth: *"**Account linking is enabled by default**… if the provider confirms the user's email as verified."*
**두 성숙한 프로젝트가 갈렸다는 사실 자체가, 이것이 라이브러리가 정해줄 수 없는 우리 결정이라는 신호다.**

---

## 4. 기성 IdP 제품 — 무엇을 사는 것이고, careerhub에 맞나

**제품이 파는 것의 대부분은 비밀번호를 다루는 일이다** — 비밀번호 정책·해싱·다중 인증(MFA)·계정 복구·이메일 검증·동의 화면.
**소셜 전용이면 이 값이 통째로 사표가 된다.** 그러고도 계정 연결 정책과 세션 수명주기는 여전히 직접 정해야 하고, 권한·초대티켓·약관동의는 어느 경우에도 앱에 남는다.

그래도 후보를 실측했다. 홈랩 노드는 arm64 8대(8GB×5, 16GB×3)이고 현재 사용률이 6~36%라 **메모리가 절대적 병목은 아니다.**

| 제품 | 런타임 | 공식 메모리 수치 | 판정 |
|---|---|---|---|
| **Authelia** | Go | 매우 가벼움 | **하드 탈락** — 아래 |
| **Keycloak** | JVM (Quarkus) | Operator 기본 **requests 1700MiB / limits 2GiB** | 조건 불리 |
| **Zitadel** | Go | **앱 512MB** | 유일하게 조건이 맞음 |
| **Dex** | Go | 이미지 44MB | 성격이 다름 (아래) |
| **Logto** | Node.js | **8 GiB** | 탈락 |
| **Authentik** | Python/Django | 문서 2GB, 실측 반론 이슈 열림 | 탈락 |
| **SuperTokens** | JVM core + Go SDK | 기본 힙 제한 미설정 | 탈락 (아래) |

**Authelia는 소셜 로그인을 받을 수 없다.** 공식 문서 원문: *"You can configure your applications to use Authelia as an OpenID Connect 1.0 Provider. **We do not currently operate as an OpenID Connect 1.0 Relying Party.**"* 1차 인증 백엔드가 LDAP과 비밀번호 파일 둘뿐이다. 요구와 정면으로 어긋난다.

**Keycloak은 arm64 이미지가 있다.** 웹 검색 상위는 대부분 "arm64 미지원"이라고 말하지만 낡은 정보이고, 레지스트리 매니페스트를 직접 조회하니 20.0부터 26.7까지 전 태그가 `linux/amd64 · linux/arm64 · linux/ppc64le`였다. **탈락 사유는 아키텍처가 아니라 메모리와 운영 부담이다.** 공식 사이징 문서: *"The base memory usage for a Pod including caches of Realm data and 10,000 cached sessions is **1250 MB of RAM**."* Operator 문서: *"the default `requests` memory is set to **`1700MiB`**, and the `limits` memory is set to `2GiB`."*

그리고 **커뮤니티판에는 장기 지원이 없다.** 공식 보안 정책 원문:

> *"**If you are unable to regularly upgrade Keycloak, we encourage you to consider Red Hat build of Keycloak, which offers long term support of specific versions of Keycloak.**"*

프로젝트 리드 본인이 2024년에 쓴 글이 더 직접적이다:

> *"With four major releases of Keycloak every year it can be a daunting task to keep deployments up to date. Especially, since **the number of breaking changes have drastically increased the last couple years**. Combine this with the importance of patching deployments quickly for vulnerabilities, this can leave many deployments **open to known vulnerabilities as the time and effort required to update to the latest release is too costly.**"*

업그레이드 가이드를 직접 파싱하니 22.0 이후 마이그레이션 항목이 누적 **423개**(릴리스당 28~46개)였다. 다만 **과장하지 않겠다** — 별도로 표기된 "breaking changes"는 마이너당 2~5개다. 정확한 서술은 *"릴리스마다 30~46개 항목을 읽고 내 배포에 해당하는지 판정해야 한다"* 이지 *"릴리스마다 40개가 깨진다"* 가 아니다. 그래도 이것이 **무료 Keycloak의 실제 가격표**다. 개인 프로젝트가 상시로 낼 종류의 비용은 아니다.

**Zitadel은 조건이 맞는 유일한 풀 IdP다.** Go, PostgreSQL 14~18, arm64 이미지 확인, 공식 문서가 *"**ZITADEL itself requires approximately 512MB of RAM and can operate with less than one CPU core.**"* 라 적는다. 같은 문서가 *"Be aware of **CPU spikes when hashing passwords**"* 라고 경고하는데, **비밀번호를 안 쓰면 그 항목이 빠져 워크로드가 더 유리해진다.** 비밀번호 로그인을 끄고 외부 IdP만 허용하는 구성이 가능하고, 계정 연결이 내장이며, Generic OAuth 설정으로 Naver를 붙일 수 있다. **다만 라이선스가 AGPL-3.0**이다(2025년 3월 v3부터 Apache 2.0에서 변경). 자체 호스팅 개인 프로젝트에 실무상 문제는 없지만 의식하고 골라야 한다.

**Dex는 성격이 다르다 — 유저 저장소가 아니라 브로커다.** 공식 문서: *"acts as a **shim** between a client app and the upstream identity provider."* 44MB짜리 Go 바이너리이고, **업스트림 정체성을 감추지 않고 그대로 넘겨준다:**

> `federated_claims` | *"The connector ID and the user ID assigned to the user at the provider."*
> ```json
> "federated_claims": { "connector_id": "github", "user_id": "110272483197731336751" }
> ```

즉 **앱이 계속 자기 DB로 사용자를 소유하고, Dex는 IdP 파편화만 흡수한다.** 앱은 OIDC 클라이언트 코드를 한 벌만 유지하면 된다. 한계 셋: 계정 연결을 하지 않고(해당 기능 요청 이슈가 closed다), Naver 전용 커넥터가 없어 generic OIDC로 붙여야 하며, 홉이 하나 늘어 장애면이 추가된다.

**SuperTokens는 계정 연결이 유료 기능**이고 core가 별도 JVM 프로세스다. 공식 helm chart 저장소는 *"THIS REPOSITORY IS DEPRECATED AND NO LONGER MAINTAINED."* 상태다.

**SaaS는 별도의 이유로 어긋난다.** 자체 호스팅이 불가능하고 사용자 데이터가 밖으로 나가며, 한국 리전은 Supabase에만 있다. 무료 티어의 **소셜 커넥션 개수 제한**도 걸린다 — Auth0 문서의 Entity Limit Policy는 *"**Free tenants only support a maximum of two social connections.**"* 라 적는데 같은 회사 가격 페이지는 "Unlimited Social Connections"라 적어 **공식 문서 두 곳이 서로 모순된다.** Clerk의 무료 등급은 소셜 커넥션 3개다.

---

## 5. 반대편 — 직접 지어서 틀린 기록, 그리고 지금 코드가 이미 틀린 것

한쪽 결론으로 몰지 않기 위해 반대 근거를 같은 무게로 찾았다.

**직접 구현으로 옮긴 회사의 공식 회고 중 1차 출처로 확인된 것은 1건이다.** Rhesis AI(2026-03), 이유는 비용이 아니라 폐쇄망 배포 요구였다. 그 글이 양쪽을 다 말한다:

> *"Let's be clear upfront: Auth0 is a genuinely good product. … **If we were building a pure cloud SaaS, we'd probably still be using it.**"*
>
> *"when you use Auth0, security is their problem. They have a dedicated security team, they run bug bounties, they deal with CVEs so you don't have to. **The moment you own your auth stack, all of that is on you.** … **We found this out firsthand. Shortly after rolling out our native authentication, ethical security researchers identified vulnerabilities in our implementation and reported them to us responsibly. They found things we'd missed.** Nothing was exploited, but it was a wake-up call. … **Assume your first implementation has bugs, because it will.**"*

**반대 방향("직접 구축 → 기성품")의 회사 공식 회고는 찾지 못했다.** 이 비대칭 자체가 관찰이다 — "이사 갔다"는 글감이 되고 "잘 쓰고 있다"는 안 된다. 회고 코퍼스는 구조적으로 불만 편향을 갖는다.

**그리고 사도 위험이 사라지지 않는다는 반례가 둘 있다.**
Okta 자신의 침해(2023): *"a threat actor gained unauthorized access to files inside Okta's customer support system associated with **134 Okta customers**"*, 그중 5개 고객의 세션이 실제로 탈취됐다.
Sign in with Apple 제로데이(2020): *"**I could request JWTs for any Email ID from Apple and when the signature of these tokens was verified using Apple's public key, they showed as valid.**"* — **IdP를 완벽히 올바르게 연동한 클라이언트도 털렸다.** 산다는 것은 위험 제거가 아니라 이전이고, 이전받은 쪽도 틀린다.

**그런데 이 논의에서 가장 무거운 반대 근거는 외부가 아니라 우리 코드다.** 아래 6절의 필수 목록에 비추면 현재 auth-service는 다음을 어긴다:

- **ID Token을 아예 받지 않는다.** 요청 scope가 `userinfo.email`·`userinfo.profile`뿐이라 `openid`가 없고, 따라서 id_token이 발급되지 않는다. 대신 access token으로 userinfo를 조회해 그 응답으로 로그인시킨다.
- **PKCE도 nonce도 없다.**
- **state의 CSRF 방어가 무효다.** 세션 서명 키가 소스에 박힌 문자열이라 누구나 유효한 서명 세션 쿠키를 만들 수 있다.
- **HS256 서명 키를 api-composer와 공유한다.** 대칭키이므로 검증할 수 있는 쪽은 발급도 할 수 있다.
- **로그아웃도, 토큰 폐기도, 로그인 시 세션 재발급도 없다.**

**즉 "직접 지어도 되는 종류의 일"이라는 결론과 "지금 것이 그 기준을 못 맞춘다"는 사실은 동시에 참이다.** 이 논의가 답해야 할 것은 전자이고, 후자는 어느 길을 가도 해소해야 한다.

---

## 6. 직접 짓는다면 반드시 있어야 하는 것

전제: 서버사이드 **기밀 클라이언트**, authorization code flow, `scope=openid`, 자체 쿠키 세션. 인가 서버는 만들지 않는다.

### 로그인 응답을 신뢰하기 위해

| | 요구 | 근거 |
|---|---|---|
| 1 | **ID Token을 반드시 받고 검증한다.** userinfo 응답만으로 로그인시키지 않는다 | 아래 별도 절 |
| 2 | ID Token의 `iss`가 발급자 식별자와 **정확히 일치**하는지 | OIDC Core §3.1.3.7 |
| 3 | ID Token의 `aud`에 **내 client_id가 포함**되는지. 신뢰하지 않는 audience가 섞여 있으면 거부 | 같은 절 |
| 4 | `exp` 검증 (현재 시각이 그 이전인지) | 같은 절 |
| 5 | **서명 검증.** 단 토큰 엔드포인트에서 직접 받은 경우 TLS 서버 검증으로 대체 가능(MAY) | 같은 절 |
| 6 | **PKCE 또는 nonce 중 최소 하나.** nonce를 택하면 토큰 엔드포인트에서 받은 ID Token의 nonce를 검증하고, **검증이 성공하기 전까지 어떤 토큰도 사용하지 않는다** | RFC 9700 §2.1.1, §4.5.3.2 |
| 7 | **CSRF 방어.** PKCE 지원이 확인되면 PKCE로, OIDC면 nonce로, 아니면 `state`에 1회용 값을 담아 **사용자 에이전트 세션에 묶는다** | RFC 9700 §2.1, §4.7.1 |
| 8 | 위 값들은 **거래마다 새로 만들고, 추측 불가능하며, 클라이언트와 브라우저 세션에 묶인다** | RFC 9700 §2.1.1 |
| 9 | **사용자 식별은 `iss` + `sub` 조합.** 이메일로 매칭하지 않는다 | 아래 별도 절 |
| 10 | **IdP가 2개 이상이면 mix-up 방어가 필수** | 아래 8절 |
| 11 | redirect_uri를 최대한 좁게 등록하고, **콜백 경로 하위에 임의 URL로 보내는 리다이렉터를 두지 않는다** | RFC 9700 §2.1, §4.1.3 |
| 12 | 인가 응답은 **HTTPS 전용** | RFC 9700 §2.6 |
| 13 | **implicit 흐름과 resource owner password 흐름 금지** | RFC 9700 §2.1.2, §2.4 |

### 자체 세션을 안전하게 들기 위해

| | 요구 | 근거 |
|---|---|---|
| 14 | **로그인 시 세션 식별자를 재발급**하고 기존 것을 종료한다 (session fixation) | ASVS 7.2.4 (L1) |
| 15 | 세션 쿠키에 `Secure`·`HttpOnly`, `__Host-` 접두사, `Domain` 미설정 | ASVS 3.3.x |
| 16 | `SameSite` 또는 anti-forgery 토큰으로 CSRF 방어 | ASVS 3.3.2 |
| 17 | **로그아웃 시 서버 측에서 세션을 무효화한다.** 자체완결 토큰(JWT)을 쓴다면 종료 토큰 목록·사용자별 발급시각 하한·사용자별 서명키 회전 중 하나가 필요하다 | ASVS 7.4.1 (L1) |
| 18 | **계정이 비활성화·삭제되면 그 사용자의 전 세션을 종료한다** | ASVS 7.4.2 (L1) |
| 19 | 불투명 세션 식별자면 **CSPRNG로 최소 128비트** | ASVS 7.2.3 |
| 20 | JWT를 쓴다면 **허용 알고리즘 목록을 고정**하고 `none`을 거부하며 대칭·비대칭을 혼용하지 않는다 | RFC 8725 §3.1 |
| 21 | 대칭키는 CSPRNG로 만들고 **최소 160비트 엔트로피**. 비밀번호나 하드코딩 문자열 금지 | RFC 8725 §3.5 |
| 22 | **대칭 서명 키를 다른 서비스·다른 audience·다른 issuer와 공유하지 않는다** | 아래 별도 절 |
| 23 | ID Token·IdP access token·자체 세션 토큰의 **검증 규칙을 서로 배타적으로** 만든다. 한쪽 토큰이 다른 쪽 자리에서 통과하면 안 된다 | RFC 8725 §3.11, §3.12 |

### 1번이 왜 타협 불가인가

RFC 6819는 이 안티패턴에 **이름을 붙여** 기술한다 — §4.4.2.6 *"Threat: Token Substitution (OAuth Login)"*:

> *"An attacker could attempt to log into an application or web site using a victim's identity. **Applications relying on identity data provided by an OAuth protected service API to login users are vulnerable to this threat. This pattern can be found in so-called 'social login' scenarios.**"*
>
> *"The attacker now manipulates the authorization response and substitutes their access token (bound to their identity) for the victim's access token. **This token is accepted by the identity API, since the audience, with respect to the resource server, is correct.** But since the identifier returned by the identity API is determined by the identity in the access token, **the attacker is logged into the target application under the victim's identity.**"*

RFC 6749 §10.16이 이를 규범으로 못박는다:

> *"Any specification that uses the authorization process as a form of delegated end-user authentication to the client (e.g., third-party sign-in service) **MUST NOT use the implicit flow without additional security mechanisms that would enable the client to determine if the access token was issued for its use (e.g., audience-restricting the access token).**"*

**핵심은 이것이다 — access token에는 나를 가리키는 `aud`가 없다.** 그 `aud`는 리소스 서버를 가리킨다. 그래서 access token만으로는 *"이 토큰이 나에게 발급된 것인가"* 를 판정할 수 없다. **ID Token의 `aud`가 client_id라는 것이 ID Token의 존재 이유다.**

OIDC Core §5.3.2가 userinfo의 지위를 확정한다:

> *"**Due to the possibility of token substitution attacks, the UserInfo Response is not guaranteed to be about the End-User identified by the `sub` element of the ID Token. The `sub` Claim in the UserInfo Response MUST be verified to exactly match the `sub` Claim in the ID Token; if they do not match, the UserInfo Response values MUST NOT be used.**"*

문장의 구조가 결정적이다 — **userinfo의 신뢰성이 ID Token과의 대조에 의존한다.** ID Token을 받지 않으면 대조할 기준이 없어지므로 이 요구를 만족시킬 방법 자체가 사라진다.

Google도 같은 말을 한다: *"**A modified client application can send arbitrary user IDs to your server to impersonate users, so you must instead use verifiable ID tokens** to securely get the user IDs of signed-in users on the server side."*

### 9번이 왜 이메일이 아닌가

OIDC Core §2의 `sub` 정의: *"REQUIRED. Subject Identifier. A **locally unique and never reassigned** identifier **within the Issuer** for the End-User."*
유일성의 범위가 **발급자 안**으로 한정된다. 그래서 키는 `sub` 단독이 아니라 `(iss, sub)` 조합이어야 한다.

같은 규격이 이메일을 명시적으로 배제한다:

> *"Issuers **MAY re-use an `email` Claim Value across different End-Users**… Therefore, other Claims such as `email`, `phone_number`, and `preferred_username` **MUST NOT be used as unique identifiers** for the End-User."*

Google도 같다: *"you **shouldn't** use the `email` field in the ID token as a unique identifier for a user. Always use the `sub` field as it is unique to a Google Account even if the user changes their email address."*

**이메일로 자동 연결하는 것이 실제 취약점이 된 사례가 있다.** 2026년 공개된 Better Auth의 계정 탈취(CVSS 8.3): 공격자가 피해자 이메일을 미검증 상태로 미리 선점해 두면, OAuth 콜백의 자동 연결이 **IdP 쪽의 검증 여부만 보고 로컬 행의 검증 상태는 읽지 않아** 피해자의 소셜 정체성이 공격자 계정에 붙었다.

**그리고 이메일 기반 연결이 아예 성립하지 않는 경우가 실재한다** — Apple은 사용자가 이메일 가리기를 택하면 릴레이 주소를 주고, Kakao는 이메일이 선택 동의라 아예 오지 않을 수 있다.

### 22번이 왜 필요한가

RFC 7515 §10.5가 원리를 말한다:

> *"**Validation of a MAC only provides corroboration that the message was generated by one of the parties that knows the symmetric MAC key.** … **MAC validation cannot be used to prove origination to a third party.**"*

**대칭키에서는 검증자가 곧 발급자다.** 여러 서비스가 같은 HS256 키를 나눠 가지면 어느 쪽이든 상대의 이름으로 토큰을 위조할 수 있고, 발급과 검증의 분리가 **원리적으로 불가능**해진다.

OWASP JWT 치트시트가 규칙으로 정리한다: *"**A different secret must be used for each (issuer, audience) pair. If, for example, the same secret is reused for different audiences, one audience can forge a token (impersonating the issuer).**"*

**균형을 위해 덧붙이면** — 같은 치트시트가 대칭키가 적합한 경우도 명시한다: *"The issuer of the token is the audience. In this case, there is no problem of secret rotation/distribution."* **단일 서비스가 자기 세션 토큰을 자기가 발급하고 자기가 검증하면 HS256이 적합하다.** 문제는 나눠 갖는 순간 시작된다.

---

## 7. 반대로, 하지 않아도 되는 것

이 목록이 이 논의의 실질적 결론이다.

| 하지 않는 것 | 왜 |
|---|---|
| OAuth2 인가 서버 구현 | 우리는 인가 서버가 아니다. ASVS의 해당 21개 요구가 전부 비해당 |
| redirect_uri 정확 매칭 로직 | 인가 서버의 의무다. 우리는 좁게 등록하고 리다이렉터를 안 만들면 된다 |
| DPoP·mTLS 등 sender-constrained 토큰 | 인가 서버·리소스 서버 대상. 자체 쿠키 세션에 무관 |
| PAR·JAR | 인가 서버 대상 |
| refresh token 회전과 재사용 탐지 | 인가 서버의 책임. 자체 세션을 쓰면 **IdP의 refresh token을 보관할 이유가 없다** |
| 동의 화면·동의 철회 | 인가 서버 대상 |
| 토큰 introspection | 자체 세션이 불투명 식별자면 조회가 곧 검증이다 |
| JWKS 캐시·키 회전 처리 | code flow에서 토큰 엔드포인트로 직접 받으면 TLS 검증이 서명 검증을 대체할 수 있다(MAY). 라이브러리가 해주면 그냥 켠다 |
| **비밀번호 정책·해싱·MFA·계정 복구** | 소셜 전용이면 통째로 IdP에 이전된다. **"직접 만들지 마라"가 실제로 해결해 주는 부분이 정확히 여기다** |

---

## 8. Naver를 붙이는 순간 새로 생기는 의무

**IdP가 둘 이상이 되면 mix-up 공격 방어가 필수가 된다.** RFC 9700 §2.1:

> *"When an OAuth client can interact with more than one authorization server, **a defense against mix-up attacks is REQUIRED.**"*

지금은 Google 하나라 해당이 없다. 방어 수단은 둘인데, 첫째(RFC 9207의 `iss` 파라미터)는 대부분의 소셜 IdP가 지원하지 않으므로 현실적으로 §4.4.2.2가 남는다:

> *"clients **MUST use a distinct redirection URI for each issuer** they interact with. Clients MUST check that the authorization response was received from the correct issuer by comparing the distinct redirection URI for the issuer to the URI where the authorization response was received on. If there is a mismatch, the client MUST abort the flow."*

**현재 콜백이 `/auth/callback/google`로 경로에 프로바이더 이름이 박혀 있는데, 그 구조가 오히려 이 방어에 맞는다.** 프로바이더별로 경로를 갈라 두고 수신 경로를 대조하면 된다.

---

## 9. `sub` 유형 제약은 이 선택에 따라 사라진다

발급자별 `subject_types_supported`를 직접 조회한 결과다.

| IdP | 값 |
|---|---|
| Google | **`public`** |
| Naver | `pairwise` |
| Kakao | `pairwise` |
| Apple | `pairwise` |
| GitHub | OIDC discovery 없음 (순수 OAuth2, 전역 고정 숫자 id) |

`pairwise`는 `sub`가 클라이언트마다 다르다는 뜻이다. 그런데 **무엇을 기준으로 다른가**가 핵심이고, 규격이 그것을 명확히 정한다. OIDC Core §8.1:

> *"When pairwise Subject Identifiers are used, the OpenID Provider MUST calculate a unique `sub` (subject) value **for each Sector Identifier**."*
>
> *"If the Client has not provided a value for `sector_identifier_uri` in Dynamic Client Registration, **the Sector Identifier used for pairwise identifier calculation is the host component of the registered `redirect_uri`.**"*
>
> *"Distinct Sector Identifier values MUST result in distinct Subject Identifier values. **The algorithm MUST be deterministic.**"* 제시된 예시 알고리즘: `sub = SHA-256(sector_identifier || local_account_id || salt)`

**즉 키는 client_id가 아니라 sector identifier이고, 기본값은 redirect_uri의 호스트다.** client_id는 계산식에 등장하지 않는다.

그리고 규격은 이 문제를 풀 장치를 이미 갖고 있다 — `sector_identifier_uri`의 목적 설명:

> *"It provides a way for a group of websites under common administrative control to have **consistent pairwise `sub` values independent of the individual domain names**. It also provides a way for **Clients to change `redirect_uri` domains without having to re-register all of their users**."*

**그래서 소프트웨어를 무엇으로 바꾸든 그 자체로는 `sub`가 바뀌지 않는다.** 바뀌는 조건은 둘뿐이다.

| 무엇을 바꾸나 | 규격대로 구현한 발급자 | client_id 기준으로 단순 구현한 발급자 |
|---|---|---|
| 소프트웨어만 교체 (호스트·client_id 유지) | **`sub` 유지** | **`sub` 유지** |
| client_id만 새로 발급 (호스트 유지) | **`sub` 유지** | `sub` 변경 |
| redirect_uri 호스트 변경 | `sub` 변경 | **`sub` 유지** |
| 둘 다 변경 | 변경 | 변경 |

**→ client_id와 redirect_uri 호스트를 둘 다 유지하면 어느 구현에서든 `sub`가 살아남는다.**
발급자가 규격을 어떻게 구현했는지 확인하지 못했더라도, 둘 다 유지하는 쪽을 택하면 그 미확인이 위험이 되지 않는다.

현재 배포는 `careerhub.jyo-liar.com` 한 호스트 아래 `/auth`·`/api`·`/` 경로로 갈라져 있다.
IdP 제품을 들이더라도 **같은 호스트의 다른 경로**(예: `/idp`)에 올리면 호스트가 바뀌지 않는다.
반대로 `auth.jyo-liar.com` 같은 별도 서브도메인에 올리는 흔한 배치를 택하면, 규격 준수 발급자에서 기존 연결이 끊긴다 —
**즉 배치 위치가 곧 정체성 결정이 된다. 이것이 이 절에서 실제로 지켜야 할 한 가지다.**

**따라서 `sub` 유형으로 IdP를 고를 이유가 없고, 제품 도입 시점에 순서 제약도 걸리지 않는다.** Naver를 먼저 붙여도 된다.
클라이언트로 남는 쪽을 권하는 근거는 이 절이 아니라 앞의 두 가지다 — 소셜 전용이면 제품이 파는 값의 대부분이 사표가 된다는 것, 그리고 이 구조가 표준 문서에 정식 패턴으로 기술되어 있다는 것.

---

## 10. 세션을 무엇으로 들 것인가

**규범은 어느 쪽도 금지하지 않는다.** ASVS 7.2.2는 자체완결 토큰과 참조 토큰을 **동등하게 허용**한다. 그러므로 *"JWT를 세션에 쓰지 마라"* 를 규범으로 인용하면 과장이다.

다만 **대가가 비대칭이다.** ASVS 7.4.1이 L1(최소 등급)에서 요구한다:

> *"Verify that when session termination is triggered (such as logout or expiration), the application disallows any further use of the session. For reference tokens or stateful sessions, this means invalidating the session data at the application backend. **Applications using self-contained tokens will need a solution such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or rotating a per-user signing key.**"*

그리고 7.4.2가 *"계정이 비활성화되거나 삭제되면 전 세션을 종료한다"* 를 역시 L1로 요구한다.
OWASP JWT 치트시트도 같은 취지로 경고한다: *"**if you use JWTs for user sessions, you will need a solution for managing session invalidation** … your application won't be completely stateless anymore which might defeat the benefits."*

**stateless의 가치는 세션 조회를 할 수 없는 수평 확장 상황에서 나온다.** 이미 매 요청 사용자 정보를 조회하는 구조라면 세션 조회 한 번이 추가 비용이 아니다.

→ **불투명 세션 식별자 + 서버 저장을 기본값으로 두고, JWT는 정당화가 필요한 선택으로 다룬다.** JWT를 유지한다면 위 셋 중 하나를 반드시 고른다. 그중 "사용자별 발급시각 하한"과 "사용자별 서명키 회전"은 사용자 레코드에 필드 하나면 되고, 종료 토큰 목록처럼 무한히 자라지 않는다.

---

## 옵션

### R1. 클라이언트로 남되, 위 6절을 충족하게 다시 짓는다
검증 라이브러리를 쓰되 무엇을 검증하는지 직접 확인하고(3절 표), 세션은 불투명 식별자로 간다.
- **이기는 조건**: 소셜 전용이 유지되고, IdP가 몇 개로 끝나며, 권한·초대티켓·약관동의를 계속 앱이 소유할 때.
- **지는 조건**: 나중에 비밀번호·MFA·조직 SSO가 필요해질 때. 그때는 6절을 지켜도 부족해진다.
- **주의**: "지금 코드를 유지한다"와 다르다. ID Token 도입·PKCE/nonce·키 분리·세션 폐기는 재작성에 가깝다.

### R2. Dex를 앞에 세우고 사용자 저장소는 그대로 둔다
44MB, Go, `federated_claims`로 업스트림 정체성을 통과시켜 현재 도메인 구조를 건드리지 않는다.
- **이기는 조건**: IdP를 계속 늘릴 계획이 확고하고, 앱이 OIDC 클라이언트 코드를 한 벌만 유지하고 싶을 때.
- **지는 조건**: IdP가 둘셋에서 멈출 때. 그러면 홉 하나와 운영물 하나가 순비용이다.
- 계정 연결은 여전히 앱 몫이고, Naver는 generic OIDC로 붙인다. **Dex를 같은 호스트 아래 두고 기존 client_id를 물려주면 기존 연결이 유지된다**(9절).

### R3. Zitadel을 세운다
조건에 맞는 유일한 풀 IdP다. 관리 화면·계정 연결·세션 관리를 사는 대신 AGPL-3.0을 받고 운영물이 하나 는다.
- **이기는 조건**: 인증 자체를 더는 신경 쓰고 싶지 않고, 512MB + 여유를 낼 수 있으며, 나중에 비밀번호나 조직 SSO가 필요해질 가능성이 있을 때.
- **지는 조건**: 소셜 전용이 계속 유지될 때. 제품 값의 절반 이상이 사표가 된다.
- **도입 시점에 순서 제약은 없다.** 같은 호스트 아래 두고 기존 client_id를 물려주면 기존 연결이 유지되므로(9절), Naver를 먼저 붙이든 나중이든 무방하다. 대신 **배치 위치를 처음에 정확히 정해야 한다.**

### R4. 인증만 떼어내지 않고 auth-service를 통째로 다시 쓴다
현재 저장소에는 인증 외에 권한·초대티켓·약관동의가 함께 있고, 그 셋은 어느 옵션에서도 앱에 남는다.
- 즉 **R1~R3 중 무엇을 고르든 "인증 부분만 바뀌고 나머지는 남는" 형태**가 된다. 통째 재작성은 인증 선택과 독립된 별개 축이다.

### R5. `supabase/auth`를 참조하거나 채택한다
Go, MIT, PostgreSQL, arm64, Kakao 네이티브 지원, `identities` 테이블로 프로바이더별 연결을 모델링하고 **검증된 이메일에만** 자동 연결한다. Supabase 스택 없이 단독 실행이 가능하다.
- **채택하지 않더라도 참조 구현으로 읽을 가치가 있다** — 지금 Go로 짓고 있는 바로 그 서비스가 이미 쓰여 있는 셈이다.

---

## ✔ 수렴 — 제품을 들이지 않는다

전제가 한 번 바뀌었다. *"직접 만드는 선택지는 되도록 피하고 싶다. 과하게 신경 써야 할 것이 너무 많다"* 는 판단이 들어와,
**"외부 솔루션을 쓴다면"** 을 전제로 다시 벌렸다. 그리고 그 전제 위에서 오히려 반대 결론에 도달했다.

### ① Dex는 코드를 줄이지 않는다

앞의 옵션 R2는 Dex를 "제품은 세우되 유저 DB는 안 넘긴다"로 평가했는데, **그 평가가 이득을 과대평가했다.**

Dex를 세워도 auth-service는 여전히 authorize 리다이렉트를 만들고, 콜백을 받고, code를 교환하고, ID Token을 검증하고, 세션을 발급해야 한다.
**상대가 Google에서 Dex로 바뀔 뿐 OIDC 클라이언트 코드는 그대로 남는다.**
오히려 홉이 하나 늘어 지연과 장애면이 추가된다.

Dex가 실제로 주는 것은 **"IdP 추가가 커넥터 설정이 된다"** 하나뿐이다.
IdP가 하나인 지금 그 값은 0이고, Naver를 더해 둘이 되어도 크지 않다.

### ② 사용자 원장을 나누면 지금 원자적인 것이 깨진다

풀 IdP(Keycloak·Zitadel)를 들이면 사용자 상태가 **제품과 careerhub로 쪼개진다.**
그런데 현재 세 흐름이 **하나의 PostgreSQL 트랜잭션 안에서 원자적**이다:

| 흐름 | 한 트랜잭션 안에서 일어나는 일 |
|---|---|
| 가입 | `InsertUser` → 동의 레코드 삽입 → 조회 |
| 탈퇴 | 동의 삭제 → 권한 삭제 → 익명화 UPDATE |
| 티켓 사용 | 행 잠금(`FOR UPDATE`) → 사용 횟수 검사 → 사용 기록 → 권한 부여 |

제품이 사용자를 소유하면 **앞의 둘이 두 시스템에 걸친다.**
가입은 "제품에 사용자 생성 + 앱에 user 행 + 동의 저장"이 되고, 탈퇴는 "제품에서 삭제 + 앱에서 동의·권한 정리"가 된다.
공유 트랜잭션이 없으므로 **보상 로직이나 조정(reconciliation) 작업이 새로 필요해진다 — 지금은 존재하지도 않는 종류의 코드다.**

그리고 이것이 careerhub에서 특히 아픈 이유가 있다(아래 ③).

### ③ 로컬 `user_id`는 어떤 경우에도 살아남아야 한다

이건 설계 취향이 아니라 **데이터가 이미 그렇게 박혀 있어서** 그렇다.

`careerhub-userinfo-service`의 MongoDB 문서가 `userId`를 필드로 갖고 **인덱스까지 잡고 있다** —
`matchjob`은 `userId_1`, `scrapjob`은 복합 인덱스 `userId_1_site_1_postingId_1`.
api-composer가 토큰에서 꺼낸 `UserId`를 gRPC 요청 필드로 내려보내고, userinfo-service가 그 값으로 스크랩·매칭조건을 저장·조회한다.

**즉 auth-service의 `user_id`는 auth-service 안에만 있는 게 아니라 다른 서비스의 데이터에 외래키로 흩어져 있다.**
어떤 제품을 들이든 IdP의 `sub`는 이것을 **대체하지 못하고 옆에 붙는 열이 된다.**
그러므로 제품을 들여도 **앱은 여전히 사용자 원장의 사본을 갖는다** — 그리고 ②의 정합 문제가 그 사본과 제품 사이에서 발생한다.

정합이 깨지면 **주인 없는 스크랩·매칭조건 문서가 남는다.**

### ④ 제품을 들여도 앱에 남는 것 / 제품이 실제로 걷어가는 것

| 앱에 남는다 | 제품이 걷어간다 |
|---|---|
| 로컬 `user` 행과 `user_id`(③) | IdP 추가가 코드가 아니라 설정이 됨 |
| 권한·초대티켓·약관동의 — 전부 도메인이지 인증이 아니다 | ID Token 검증(`iss`·`aud`·`exp`·서명) |
| **Naver 연결끊기 콜백**(아래) | PKCE·nonce·state 왕복 |
| 제품→앱 삭제 전파의 수신·정합(②) | **발급자가 둘 이상일 때의 mix-up 방어** — 앱 입장에서 issuer가 하나가 되므로 요구 자체가 소멸 |
| 정체성 → 로컬 `user_id` 매핑 | 계정 연결 정책 |
| | 로그인 화면 |

**Naver 연결끊기 콜백은 어느 제품을 골라도 직접 짠다.**
사용자가 네이버에서 동의를 철회하거나 탈퇴하면 서비스로 콜백이 오는데, 명세가 `POST` / `application/x-www-form-urlencoded` /
파라미터 `clientId`·`encryptUniqueId`·`timestamp`·`signature` / 응답 `204`이고, 식별자가 암호화되어 온다 —
`AES128/CBC/PKCS5Padding`, 키는 `md5(CLIENT_SECRET)`의 앞 16바이트, 그 위에 HMAC 서명 검증.
네이버 문서가 **"네이버에서는 실패 요청에 대해서 재시도를 수행하지 않습니다"** 라고 못박는다.
Keycloak에도 Zitadel에도 이 콜백을 받는 기능이 없고, 네이버 콘솔에 등록하는 콜백 URL은 하나뿐이다.

### ⑤ Dex와 Zitadel의 차이 (기록용)

둘은 같은 범주가 아니다 — **Dex는 프로토콜 어댑터, Zitadel은 사용자 원장**이다.
Dex의 저장소 인터페이스는 auth request·code·refresh·세션·커넥터 설정이 전부이고, 업스트림 사용자를 위한 프로필 디렉터리가 없다.

| | Dex | Zitadel |
|---|---|---|
| 계정 연결 | **앱 코드**(해당 기능 요청 이슈가 closed) | 제품 |
| 사용자 프로비저닝 | **앱 코드** | 제품 |
| 삭제 전파 | **불필요**(원장이 하나뿐) | 수신 코드 필요 |
| 앱이 보는 정체성 | `federated_claims`로 **업스트림 id를 그대로** 받는다 | 제품의 user ID(업스트림은 내부에) |
| 네이버 콜백 → 사용자 특정 | **로컬 쿼리** | API 조회 또는 별도 저장 |
| 설정 방식 | 선언적 YAML(GitOps 정합) | 콘솔·API(런타임 상태) |
| 백업 | Postgres만, 유실돼도 재로그인이면 복구 | Postgres **+ masterkey**(잃으면 암호화 데이터 전부 상실) |
| 이메일 결측 처리 | 앱 코드 | 확인 못 함 |
| 테스트용 비대화형 로그인 | **`mock` 커넥터 내장** | 별도 방법 |

**코드 최소화만 놓고는 Zitadel이 이긴다**(계정 연결과 프로비저닝을 가져가므로). 그러나 ①~③ 때문에 둘 다 채택하지 않는다.

### ⑥ 인가 축도 같은 결론 — OpenFGA

권한 관리를 외부로 빼는 축도 함께 벌렸다. OpenFGA는 Zanzibar 계열의 관계 기반 접근제어(ReBAC) 엔진이다.

**공정하게 적자면, 모델링 적합성은 나쁘지 않다.** OpenFGA의 conditions는 시간 기반 권한을 1급으로 지원하고,
공식 문서의 대표 예제가 하필 careerhub와 거의 같은 모양이다 — `condition non_expired_grant(current_time, grant_time, grant_duration)`,
용례로 *"Temporal Access Policies — manage user access for a window of time"* 을 든다.

그럼에도 채택하지 않는 이유 셋:

- **careerhub에 ReBAC 문제가 없다.** 권한은 평평한 코드 목록이고 검사는 `slices.Contains(claims.Authorities, ...)` 한 줄이다. 리소스 단위 권한도, 계층도, 공유도, 멀티테넌시도 없다.
- **이미 갖고 있는 PostgreSQL이 그 튜플 스토어다.** `user_authority(user_id, authority_id, expiry_date)`가 튜플이고, 만료를 거르는 조회가 조건 평가다. 바꿔서 새로 얻는 것이 없다.
- **②의 문제를 다시, 더 나쁘게 들여온다.** OpenFGA는 튜플을 자기 데이터스토어에 두므로 티켓 사용 흐름이 두 시스템에 걸린다. 행 잠금까지 걸어둔 흐름을 쪼개는 것이라 가입·탈퇴보다 더 나쁘다.

### ⑦ 다시 열 트리거

이 판단은 조건부다. 아래 중 하나가 실제로 생기면 다시 연다.

| 트리거 | 무엇이 다시 살아나나 |
|---|---|
| **IdP가 셋 이상으로 늘어난다** | Dex의 "커넥터 설정" 이득이 실질이 된다 |
| **비밀번호 로그인이나 조직 SSO가 필요해진다** | 풀 IdP 제품의 값이 크게 오른다. 소셜 전용이라는 전제가 깨지는 순간이다 |
| **리소스 단위 권한이 생긴다** | 스크랩 공유·팀/조직·특정 공고만 관리 등. `slices.Contains`로 표현이 안 되면 OpenFGA가 제값을 한다 |
| **인가 검사가 서비스 여러 곳으로 번진다** | 지금은 auth-service와 api-composer **두 곳**이다. 더 늘면 중앙화가 이긴다 |
| **사용자 원장을 careerhub가 소유하지 않아도 되게 된다** | ③의 제약이 사라지면 ②의 비용도 크게 준다 |

## 검토하고 버린 것

- **Authelia** — 소셜 로그인을 받을 수 없다. 공식 문서가 relying party 역할을 지원하지 않는다고 명시한다. 요구와 정면으로 어긋난다.
- **Keycloak** — arm64는 문제가 아니었다(이미지 존재 확인). 버리는 이유는 Operator 기본 요청 1.7GiB와, 커뮤니티판에 장기 지원이 없어 상시 업그레이드 노동을 떠안는다는 점이다. 개인 프로젝트가 계속 낼 비용이 아니다.
- **Logto·Authentik·SuperTokens** — 각각 최소 8GiB 권고, 실측 반론이 열린 무거운 구성, 계정 연결 유료화라는 이유로 조건이 어긋난다.
- **SaaS 전반** — 자체 호스팅 불가, 데이터 외부 이전, 한국 리전 부재. 무료 등급의 소셜 커넥션 개수 제한(Auth0 2개 표기, Clerk 3개)이 늘려갈 IdP 수와 충돌한다.
- **`sub` 유형이 `public`인 IdP만 고르는 것** — 그 기준으로 거르면 Naver·Kakao·Apple이 전부 빠지고 한국 사용자가 실제로 쓰는 수단이 사라진다. 구현 세부가 제품 결정을 지배하게 두는 것이고, 9절대로 **구조를 고르면 이 제약 자체가 없어진다.**
- **"인증은 직접 만들면 안 된다"를 규범으로 삼는 것** — 그 문장은 OWASP Authentication Cheat Sheet에 존재하지 않고, 실재하는 근거(Top 10:2025 A07)는 "Ideally… whenever possible"의 조건부 권고이며, ASVS가 사라고 지목한 대상은 **인가 서버**다. 우리는 클라이언트다.
- **IdP의 refresh token을 보관하는 것** — 자체 세션을 발급하면 IdP 토큰을 다시 쓸 일이 없다. 보관은 IdP의 API를 대신 호출할 때만 정당화된다.
- **Dex를 앞에 세우는 것**(원안 R2) — OIDC 클라이언트 코드가 그대로 남아 코드가 줄지 않는다. 홉만 하나 는다. 남는 이득은 "IdP 추가가 커넥터 설정이 된다" 하나인데 IdP가 둘일 때는 값이 작다.
- **Zitadel·Keycloak 도입**(원안 R3) — 사용자 원장이 쪼개져 지금 원자적인 가입·탈퇴가 두 시스템에 걸친다. 그러고도 로컬 `user_id`는 다른 서비스의 데이터에 박혀 있어 앱이 사본을 계속 갖는다.
- **OpenFGA 등 외부 인가 서비스** — 모델링은 맞지만(시간 기반 conditions 지원) careerhub에 ReBAC 문제가 없고, 기존 PostgreSQL이 이미 같은 역할을 하며, 티켓 사용의 원자성이 깨진다.
- **Authentik** — Python/Django + 워커 + Redis 계열로 후보 중 가장 무겁고, 공식 문서의 리소스 권고를 반박하는 실측 이슈가 열려 있다. 애초에 위 Zitadel·Keycloak과 같은 범주라 같은 이유로 빠진다.

---

## 열린 질문 — 사람의 것

수렴으로 닫힌 것과 남은 것을 갈라 적는다.

**닫혔다**

- ~~비밀번호 로그인이나 조직 SSO가 필요해질 가능성~~ — **소셜 전용을 유지한다.** 이 전제가 깨지는 것은 이제 "다시 열 트리거"의 한 줄이다.
- ~~IdP를 몇 개까지 붙일 것인가~~ — Naver를 더해 둘. 셋 이상이 되면 다시 연다.
- ~~IdP를 들인다면 어느 호스트에 둘 것인가~~ — 제품을 들이지 않으므로 해당 없음. 다시 열 때 되살아나는 질문이다.

**남았다**

1. **현재 가입 사용자가 몇 명인가.** 정체성 저장 모델을 바꿀 때의 마이그레이션 비용이 여기 걸린다. 유일하게 시간이 비용을 밀어 올리는 축이다.
2. **세션을 불투명 식별자로 바꿀 것인가.** 기본값은 그쪽이지만, 자체완결 토큰을 유지한다면 폐기 방식 셋 중 하나를 골라야 한다.
3. **api-composer가 계속 토큰을 검증해야 하나.** 검증이 필요하면 대칭키를 나눠 갖는 현재 구조를 비대칭 서명으로 바꾸는 것이 답이고, 검증이 불필요하면 키를 아예 안 주는 것이 더 싸다.
4. **재작성을 현재 저장소 안에서 할 것인가.** 인증 선택과 독립된 축이다 — 제품을 안 쓰기로 한 것과 무관하게 남는다.
5. **계정 연결을 허용할 것인가.** 제품이 대신 정해주지 않게 되었으므로 이제 우리가 정한다. 이 답이 `UNIQUE(email)`의 처분과 정체성 저장 모델을 함께 정한다.

## 다음 단계 후보

- **6절의 필수 목록이 그대로 작업 목록이 된다.** 항목 대부분이 개별 티켓 크기이고, ID Token 도입(`openid` scope + 검증)·서명 키 분리·세션 폐기가 가장 크다.
- 세션 매체(남은 질문 2)와 서명 키 체계(남은 질문 3)가 **함께 뒤집히는지** 따로 판단해야 한다. 함께라면 한 ADR, 아니면 별개다.
- 계정 연결(남은 질문 5)과 정체성 저장 모델은 **공동무효 관계로 보인다** — 연결 정책 없이 저장 모델만 정하면 의미가 절반이고 그 역도 같다. 한 ADR일 가능성이 높다.
- **다시 열 트리거(⑦)를 어디에 둘 것인가.** 이 문서가 `done`으로 얼면 트리거는 여기 남지만, 실제로 감시되지는 않는다. 티켓이나 다음 논의가 이를 물려받아야 한다.
