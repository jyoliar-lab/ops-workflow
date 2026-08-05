---
type: discussion
topic: careerhub
subjects: [auth-service, zitadel, keycloak, jwt, auth0, okta, cognito, azure-ad-b2c, firebase-auth]
status: active
ref-adrs: [ADR-0028, ADR-0030]
---

# 외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사

## 0. 물음과 판정 기준

`260805_1635` §9가 수렴시킨 형태 — **동의 원장 = 앱 DB(auth-service) · 발급 훅으로 충족 여부를 클레임에 주입 · 서비스는 403 게이트 · 재동의는 앱의 버전 대조** — 가 업계 실무와 정합하는지, 반례가 있는지를 사례로 검증한다. ADR-0028(동의 원장은 앱, 접합은 발급 시점 클레임 주입)이 `proposed`로 걸려 있으므로, 이 조사는 그 accept 심사의 재료다.

조사 축: ① 주요 IdP 제품(Auth0·Okta·Cognito·Azure AD B2C/Entra External ID·Firebase Auth·Keycloak·Zitadel)의 공식 패턴 ② 커뮤니티 실무 ③ 규제(GDPR·한국법) 요건이 저장 위치에 주는 제약.

## 1. 결론 먼저 — 수렴형은 업계 다수형과 동형이고, 반례는 조건부다

동의 구현은 세 원형(archetype)으로 갈린다:

| 원형 | 진실의 위치 | 게이트 위치 | 대표 |
|---|---|---|---|
| **A. IdP 안 완결형** | IdP 프로필/디렉터리 속성 | IdP 로그인 흐름 안 | Azure AD B2C custom policy, Auth0 Forms/Redirect Actions, Keycloak required action SPI |
| **B. 앱 원장 + 발급 훅 전파형** | 앱 DB | 각 서비스(클레임 검사) + 앱 온보딩 | Cognito(pre-token-generation Lambda), Okta(token inline hook), Firebase(Firestore→claims), Zitadel(Actions) |
| **C. CMP 외장형** | 전문 동의 플랫폼(OneTrust 등) | 앱 | Auth0×OneTrust 공식 통합 |

**careerhub 수렴형은 B의 정석이다.** 그리고 B는 소수 우회로가 아니라, **제품 설계 자체가 전제하는 방향**이다 — 조사한 전 제품이 "토큰 발급 직전 외부 상태를 클레임으로 싣는 훅"(pre-token-generation / OnTokenIssuanceStart / beforeUserSignedIn / token inline hook / Actions)을 1급으로 제공하고, 각 생태계에서 그 훅의 대표 용례가 정확히 이것이다.

**"동의 여부를 클레임에"의 위상을 정확히 하면** — 동의 전용 **표준 클레임·내장 동의 모델은 어느 제품에도 없다**(OIDC의 consent는 스코프 동의 전용). 그러나 "동의 상태를 토큰 클레임으로 전파하라"는 것은 **각 제품 공식 문서가 반복 제시하는 정규 경로다**: Auth0(메타데이터 → custom claim, 동의 상태에 대한 공식 커뮤니티 답변이 직접 권장) · Okta(프로필 속성 → 클레임 매핑 공식 문서 + token inline hook) · Cognito(pre-token-generation 공식 문서·블로그) · B2C(공식 `service-consent` 샘플이 동의 목록을 scope 클레임으로) · Entra External ID(동의 체크박스 attribute의 클레임 반환 명시) · Firebase(blocking functions의 customClaims) · Zitadel(metadata 권고 + Actions). 표준화되지 않은 것은 **의미론**(클레임 이름·모델)이지 **수단**(클레임 전파)이 아니다.

## 2. 제품별 실측 — 어디에 두고, 어떻게 강제하고, 재동의는 어떻게

### Auth0 — IdP 안 게이트를 제공하는 유일한 CIAM급, 그러나 구멍과 자기 부정이 있다

- **게이트**: Post-Login Action에서 폼 렌더(Forms, no-code) 또는 외부 페이지 리다이렉트(`api.redirect.sendUserTo` + 서명 JWT 왕복). 저장은 `app_metadata`(공식 예시: `are_privacy_policies_accepted` + timestamp).
- **★ 구조적 구멍**: Redirect Action은 `prompt=none`·refresh token 교환·ROPG에서 **실행되지 않는다** — IdP 안 게이트만으로는 재동의를 100% 강제할 수 없고, **앱 쪽 백스톱 게이트가 어차피 필요**하다는 것이 공식 문서의 한계에서 도출된다.
- **★ 자기 부정**: Auth0 메타데이터 문서 스스로 "검색·갱신 빈도 높은 용도 부적합, 상세 데이터는 **외부 시스템에 두고 Auth0에는 외부 식별자만** 저장하라"고 권고. 마케팅 동의 공식 블로그도 동의를 클레임에 싣지 않고 외부 API로 넘긴다.
- **재동의**: 공식 미지원. 실무는 `privacy_policies_version` 비교(IAMSE 사례) 또는 버전 이력 배열 `termsAcceptanceHistory: [{version, registeredAt}]`(willianantunes 사례) — 전부 자가 구현.

### Okta — ToS 동의 네이티브 기능이 없다 (공식 확인)

- 지원 담당 공식 답변: *"There is no native option to accomplish this within Okta."* Okta의 "consent"는 OAuth 스코프 동의 전용이다.
- 조립형 답: 커스텀 프로필 속성 + Expression Language 클레임 매핑, 또는 **앱 DB 저장 + token inline hook**(발급 시 외부 서비스 호출 → `com.okta.tokens.*` 커맨드로 클레임 주입). 후자가 careerhub P2와 동형.

### AWS Cognito — 공식 문서·블로그가 B형을 명시적으로 민다

- custom attribute(`custom:tos_accepted` 류)의 한계가 공식 문서에 열거된다: **생성 후 삭제·변경 불가**, required 강제 불가(= 가입 시 동의 강제 불가), 인덱스가 없어 "미동의 사용자 전원 조회" 불가. 문서 원문이 *"자주 변하는 사용자 데이터는 DynamoDB 같은 별도 저장소에"* 라고 권고.
- **AWS Security Blog 공식 사례가 정확히 P2다**: 발급 시 pre-token-generation Lambda가 DynamoDB를 조회해 `claimsToAddOrOverride`로 클레임 주입.
- 2025-08 신기능(Managed Login의 ToS/PP 링크)조차 **암묵 동의 + 사용자별 수락 기록 없음** — 사용자별 동의 기록을 IdP 안에 남기는 1급 기능이 여전히 없다.

### Azure AD B2C — A형의 유일한 완성형, 그러나 후속 제품이 그 경로를 버렸다

- 공식 샘플(`sign-in-sign-up-versioned-tou`)이 디렉터리 extension attribute(`extension_termsOfUseConsentDateTime`/`...Version`)에 저장하고, **로그인 저니 안에서 버전 비교 → 재수락 페이지 → 미수락 시 토큰 미발급**까지 정책 XML로 완결한다. 조사 범위에서 IdP 안 재동의까지 내장 경로로 되는 유일한 사례.
- 그러나 **약관 버전 올리기 = 정책 XML 상수 수정 후 재배포**이고, 같은 공식 문서가 "통상은 앱이 동의를 앱 안에서 처리하며 디렉터리 참여는 선택"이라 전제한다.
- **★ 후속작이 이 경로를 버렸다**: B2C는 2025-05 신규 판매 종료, 후속 Entra External ID에는 custom policy가 없다. 가입 체크박스 수집까지는 내장이나 **버전 재동의는 내장 경로가 없어** custom authentication extension(**외부 REST 훅** — `OnTokenIssuanceStart` 포함)이나 앱 게이트로 외부화된다. A형의 대표조차 세대 교체에서 B형 방향으로 이동했다.

### Firebase Auth — B형이 강제되는 극단

- IdP에 둘 곳 자체가 없다. 커뮤니티 정설(Doug Stevenson 패턴)이 명문화한 원칙: **"Firestore가 질의·감사 가능한 진실, 클레임은 ID 토큰 속 캐시"** — 클레임만으로는 "미동의 전원 조회" 같은 질의가 불가능하기 때문. 상태 변경 → 클레임 미러링 → **클라이언트가 즉시 토큰 강제 갱신**(`getIdToken(true)`)으로 신선도 지연을 제거하는 것까지 패턴에 포함된다(§9 모서리 1과 동일 처방).

### Keycloak — IdP 안 게이트의 원형이자, 그 함정의 전시장

- 내장 T&C는 1회성·realm 단위 단일 문서. 개별 동의·매 로그인 재확인·독립 단계 분리는 전부 미해결 요구(#9149, #8750)이고 커스텀 SPI 영역이다.
- **★ 브로커 경유의 순서 함정(#30193)**: 외부 IdP(소셜) 경유 first-broker-login에서 **사용자가 동의하기 전에 이미 username/email이 저장된다** — GDPR 위반 소지로 지적된 구조 문제. IdP 안 게이트형은 소셜 브로커 구성에서 새는 지점이 있다.
- 커뮤니티 담론의 절충: 게이트는 IdP, **증적·정밀 동의는 앱/별도 저장** — "bare Keycloak은 GDPR 미충족"이 오래된 합의.

### Zitadel — 공식 입장이 "밖에서 하라"

- Discussion #4383에서 팀이 *"consent를 ZITADEL에 저장해달라는 요청을 여러 번 받았다(마케팅 구독 포함)"* 고 인정하면서, 현재 답은 **"user metadata에 쓰거나, 고급 동의는 서드파티 도구로"**. 로드맵 미확정(아이디어 단계).
- #6747에서 메인테이너 확인: 내장 ToS 수락은 가입 시에만 표시되고 **외부 IdP 경유 로그인에는 뜨지 않는다** — 소셜 전용인 careerhub에서 Zitadel 내장 동의는 애초에 성립하지 않는다. `260805_1635` §9의 "내장 ToS는 끈다" 판정에 근거가 하나 더 얹힌다.

## 3. 규제 축 — 저장 위치를 앱 쪽으로 미는 독립 압력

- **GDPR Art.7(1)**: 동의의 입증 책임이 서비스에 있다 — 누가·언제·어떤 폼으로·**어떤 버전의 문구에** 동의했는지의 전체 이력 제출 가능해야 함. **ISO/IEC TS 27560:2023**(Kantara Consent Receipt 후속)은 동의를 아예 **타임스탬프 붙은 상태 전이(given/withdrawn/…)의 이벤트 로그**로 모델링한다. → IdP 유저 속성의 단일 boolean은 표준·규제 어느 쪽 요건도 혼자 충족하지 못한다. 동의 레코드는 append-only 이력이어야 하고, 그것은 도메인 DB의 일이다.
- **한국 요건**: 필수/선택 분리(마케팅 동의를 필수에 끼우면 과태료), 만 14세 법정대리인 동의, 광고성 정보 수신 동의의 별도 수취·일시 기록 — 항목 수와 법역 규칙이 많아 **realm 단위 단일 ToS 모델(Keycloak·Zitadel 내장)로는 표현 불가**. 자체 온보딩 + 자체 동의 레코드가 사실상 강제된다. careerhub의 4건 개별 동의(`00002_seed_agreements.sql`)가 정확히 이 요건의 산물이다.
- **CMP 구도가 방증**: Auth0×OneTrust 공식 통합조차 동의의 원본은 CMP에 있고 Auth0는 신원 연결·트리거만 한다. Auth0 마켓플레이스에 "Consent Management" 카테고리가 따로 있다는 것 자체가 — IdP 스스로 동의 관리를 자기 관할 밖으로 공식화한 것이다.

## 4. 수렴형과의 대조 — 항목별 판정

| careerhub 수렴형 (`260805_1635` §9, ADR-0028) | 업계 근거 | 판정 |
|---|---|---|
| 동의 원장 = 앱 DB (`agreement`·`user_agreement`) | Cognito 공식 권고 · Firebase 강제 · Auth0 자기 권고 · Okta 조립형 · Zitadel #4383 · GDPR/27560 이벤트 로그 요건 | **정합 — 다수형** |
| 발급 훅으로 충족 여부 클레임 주입 | 전 제품이 1급 훅 제공, 대표 용례가 "외부 진실 → 클레임" | **정합 — 제품 설계의 전제** |
| 서비스 403 게이트 + 프론트 유도 | Auth0조차 `prompt=none`·refresh 구멍으로 앱 백스톱 필요 · Firebase는 Security Rules가 클레임 검사 | **정합 — IdP 안 게이트를 쓰더라도 어차피 필요** |
| 재동의 = 앱의 버전 대조 | 공식 지원은 B2C 단독(그마저 XML 상수 재배포), 나머지 전부 자가 구현 — 앱 DB에 있으면 앱 로직 한 조각 | **정합 — 오히려 유리** |
| 클레임 = 발급 시점 스냅샷, 신선도는 토큰 수명으로 바운드 | "자주 변하는 상태는 클레임에 넣지 말라 / 넣으면 짧은 수명 + 갱신 트리거"가 실무 정설. Firebase 패턴은 상태 변경 → 강제 토큰 갱신까지 명문화 | **정합 — §9 모서리 1·2와 동일 처방** |
| Zitadel 내장 ToS는 끈다 | #6747: 외부 IdP 경유에 안 뜸 — 소셜 전용이면 켜도 무의미 | **정합 + 근거 보강** |

**반례 없음 — 단 조건부 예외 둘을 기록한다:**

1. **A형이 이기는 조건**: 다중 앱이 하나의 IdP를 공유하고 동의 게이트의 일관성이 앱 협조 없이 보장되어야 할 때(Keycloak #9149의 선호 논거), 그리고 B2C처럼 전용 경로가 완성돼 있을 때. careerhub는 단일 제품군이고 소비자(api-composer·auth-service)가 이미 클레임 게이트를 갖는 구조라 해당 없음. 그리고 A형의 대표(B2C)조차 후속 제품에서 외부 훅 방향으로 이동했다.
2. **카카오싱크 — 역방향 극단**: 서비스의 필수/선택 약관·마케팅 수신 동의를 카카오 로그인 동의창 하나에 병합(원클릭 가입). 단 이것은 IdP가 플랫폼 사업자여서 동의창 자체를 상품화한 경우이고, 동의 결과는 결국 서비스가 API로 수신해 자체 기록한다 — 원장이 IdP로 넘어간 것이 아니다.

## 5. 조사가 얹어준 설계 시사점 (코드 관할, 기록만)

- **클레임에는 게이트용 최소 신호만** — 필수 동의 충족 플래그(또는 `onboarded`)만 싣고, **마케팅(선택) 동의는 클레임에 싣지 않는다**. 마케팅 발송은 비동기라 발송 시점 DB 조회가 가능하고 실시간 정합이 필요하므로 클레임 스냅샷이 오히려 해롭다 — Auth0 공식 블로그도 뉴스레터 동의를 클레임에 싣지 않는다.
- **`user_agreement`는 append-only 이력으로** — 현재 상태 플래그 갱신이 아니라 버전별 동의/철회 이벤트 축적(ISO 27560의 모델, willianantunes의 `termsAcceptanceHistory` 배열과 동형). 단일 boolean으로 설계했다가 버전 재동의를 retrofit하는 것이 흔한 후회 지점으로 언급된다. 현행 스키마가 이미 개별 행 + 시각 기록이므로 방향은 맞다 — 철회·재동의 이벤트가 행 갱신이 아니라 행 추가가 되도록만 확인.
- **동의 완료 → 토큰 강제 갱신**을 프론트 흐름의 명시 단계로(§9 모서리 1의 재확인) — Firebase 생태계는 이것을 `getIdToken(true)` 관용구로 명문화해 두었다.

## 6. 열린 것

- 이 조사는 ADR-0028의 Decision 중 동의 경계("동의 수집·온보딩은 제품 흐름 밖, 앱 게이트")를 **지지하는 재료**다. accept 판단 자체는 심사(docs-tickets·사람)의 것.
- §5의 시사점 셋은 결정이 아니라 구현 참고 — 티켓화 여부는 리뉴얼 작업 분해 시 판단.

## 검토하고 버린 것

- **"동의를 IdP 프로필에 저장" (A형 채택)** — 소셜 브로커 경유에서 게이트가 새고(Keycloak #30193, Zitadel #6747), 개별 4건·버전 이력·철회가 유저 속성 모델로 표현되지 않으며, GDPR 입증 요건(이벤트 이력)을 충족하지 못한다. 소셜 전용 careerhub에서는 성립 자체가 약하다.
- **"CMP 도입" (C형)** — 동의의 원장을 전문 플랫폼에 두는 상용 구도가 있으나, 개인 프로젝트 규모에서 외부 SaaS 의존을 하나 늘릴 이유가 없다. 앱 DB 원장이 같은 역할을 한다.

---

### 출처 (주요)

- Auth0: [Redirect with Actions](https://auth0.com/docs/customize/actions/explore-triggers/signup-and-login-triggers/login-trigger/redirect-with-actions) · [Forms update-policy](https://auth0.com/docs/customize/forms/configure-update-policy-form) · [Metadata 한계·외부 저장 권고](https://auth0.com/docs/manage-users/user-accounts/metadata) · [GDPR Track Consent](https://auth0.com/docs/secure/data-privacy-and-compliance/gdpr/gdpr-track-consent-with-lock) · [뉴스레터 동의 블로그](https://auth0.com/blog/using-auth0-to-collect-consent-for-newsletter-signups/) · [버전 재동의 실무(IAMSE)](https://iamse.blog/2025/03/03/auth0-forms-adding-policy-versioning/) · [Actions 실전(willianantunes)](https://www.willianantunes.com/blog/2022/08/terms-of-use-through-auth0-actions/)
- Okta: [네이티브 불가 공식 답변](https://support.okta.com/help/s/question/0D54z00009bRGRjCAO/how-to-implement-terms-condition-page-using-okta) · [Token inline hook](https://developer.okta.com/docs/guides/token-inline-hook/main/)
- Cognito: [custom attribute 한계·외부 저장 권고](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html) · [DynamoDB→클레임 공식 사례](https://aws.amazon.com/blogs/security/use-amazon-cognito-to-add-claims-to-an-identity-token-for-fine-grained-authorization/) · [Managed Login ToS 링크(암묵 동의)](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-cognito-terms-use-privacy-policy-documents-managed-login)
- Azure: [B2C versioned-ToU 샘플](https://github.com/azure-ad-b2c/samples/blob/master/policies/sign-in-sign-up-versioned-tou/readme.md) · [manage-user-access](https://learn.microsoft.com/en-us/azure/active-directory-b2c/manage-user-access) · [External ID custom extensions](https://learn.microsoft.com/en-us/entra/external-id/customers/concept-custom-extensions)
- Firebase: [Blocking functions](https://firebase.google.com/docs/auth/extend-with-blocking-functions) · [Firestore=truth, claims=cache 패턴](https://medium.com/firebase-developers/patterns-for-security-with-firebase-supercharged-custom-claims-with-firestore-and-cloud-functions-bb8f46b24e11)
- Keycloak: [매 로그인 ToS 미해결](https://github.com/keycloak/keycloak/discussions/9149) · [브로커 경유 GDPR 순서 문제](https://github.com/keycloak/keycloak/discussions/30193) · [required action SPI 사례](https://github.com/eddykaya/keycloak-custom-required-action)
- Zitadel: [Consent Management 공식 입장](https://github.com/zitadel/zitadel/discussions/4383) · [외부 IdP 경유 ToS 미표시](https://github.com/zitadel/zitadel/discussions/6747)
- 규제·표준: [GDPR Art.7](https://gdpr-info.eu/art-7-gdpr/) · [ISO 27560 구현 가이드(W3C DPV)](https://w3c-cg.github.io/dpv/guides/consent-27560) · [개인정보보호위 필수/선택 분리](https://www.privacy.go.kr/front/contents/cntntsView.do?contsNo=94)
- CMP: [OneTrust×Auth0](https://marketplace.auth0.com/integrations/onetrust-consent-management)
- 한국 실전: [카카오싱크 동의 항목](https://cs.kakao.com/helps_html/1073193209?locale=ko)
