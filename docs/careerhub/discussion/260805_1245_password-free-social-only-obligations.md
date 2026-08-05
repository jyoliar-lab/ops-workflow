---
type: discussion
topic: careerhub
subjects: [auth-service, google-oauth, naver, careerhub-front]
status: active
---

# 비밀번호 없이 소셜 로그인만 제공해도 되는가 — 의무와, 대신 지는 대가

## 물음

careerhub는 로그인이 Google OAuth 하나뿐이고 **비밀번호가 아예 없다.** 앞으로 Naver를 붙이려 한다.
개인정보(이메일·이름)를 수집하는 서비스인데, **아이디/비밀번호 로그인을 반드시 제공해야 한다는 규범이 있는가.**

---

## 1. 답 — 의무가 아니다

국제 표준에도 한국 법령·고시에도 *"비밀번호를 제공하라"* 는 규범이 없다.
표준은 비밀번호를 **여러 인증수단 중 하나**로 열거하고, 한국 고시는 **"비밀번호를 쓴다면 이렇게 하라"** 는 조건부 조항만 둔다.

### 한국 법령

**「개인정보의 안전성 확보조치 기준」**(개인정보보호위원회고시)에서 **이용자 인증에 걸리는 유일한 조항**은 제5조⑤다:

> "개인정보처리자는 개인정보취급자 또는 **정보주체의 인증수단을 안전하게 적용하고 관리하여야 한다.**"

**"인증수단"이라고만 쓴다.** 수단을 특정하지 않으므로 소셜 로그인도 여기 해당하고, 규격대로 구현하면 충족이다.

흔히 이 조항과 혼동되는 것이 제6조②의 *"인증서, 보안토큰, 일회용 비밀번호 등 안전한 인증수단"* 인데,
**이것은 이용자가 아니라 취급자(관리자) 조항이다.** 현행판은 괄호로 못박았다:

> "제6조(접근통제) ② … 정당한 접근 권한을 가진 자(**다만, 정보주체는 제외한다**)가 정보통신망을 통해 외부에서 개인정보처리시스템에 접속하려는 경우 인증서, 보안토큰, 일회용 비밀번호 등 안전한 인증수단을 적용하여야 한다."

직전 판본에서도 대상은 "개인정보취급자"였다. **그리고 그 "안전한 인증수단" 목록에 비밀번호는 들어 있지도 않다.**

비밀번호를 다루는 제7조①은 조건부다:

> "① … 다만, **비밀번호를 저장하는 경우에는** 복호화되지 아니하도록 일방향 암호화하여 저장하여야 한다."

**「정보통신망법」 172개 조문 전문에 "비밀번호"가 0건이다** — 2020년 데이터 3법 개정으로 개인정보 조항이 개인정보 보호법으로 이관되면서 이용자 인증수단 규정이 남지 않았다.

**본인확인 의무도 해당 없다.** 게시판 본인확인(정보통신망법 제44조의5)은 민간 사업자에 걸리던 제2호가 **헌법재판소 위헌 결정으로 삭제**되어 공공기관등만 남았다. 청소년유해매체물·전자금융거래·전자서명 어느 쪽에도 해당하지 않는다.

**소셜 로그인 단독 제공을 제한하는 한국 규범은 발견하지 못했다.**
오히려 규제기관이 소셜 로그인을 정상 방식으로 전제한다. 개인정보보호위원회 소셜로그인 실태점검 결과(2025-02):

> "소셜로그인을 위하여 소셜계정이 이용사이트에 이용자 개인정보를 제공하는 과정에서는 **특별한 문제점이 발견되지 않았다**"
> "소셜계정을 탈퇴한 이용자의 개인정보 파기는 적정하게 이뤄지지 않고 있는 것으로 나타났다"

지적 대상은 IdP 쪽(카카오·구글·애플·메타)의 탈퇴 시 파기였고, **비밀번호 로그인 요구는 권고에 포함되지 않았다.**

### 국제 표준

**NIST SP 800-63B**에서 비밀번호는 AAL1의 **7개 선택지 중 하나**다 — *"AAL1 authentication SHALL use **any of the following**"* 뒤에 password·look-up secret·out-of-band device·single-factor OTP·multi-factor OTP·single-factor cryptographic·multi-factor cryptographic이 나열된다.
AAL3은 multi-factor cryptographic 하나만으로 충족되므로 **비밀번호 없이도 최고 등급에 도달한다.**

표준 자신의 평가는 오히려 부정적이다: **"Passwords are not phishing-resistant."**
그리고 동기화 패스키(passkey)를 다루는 Appendix B는 normative이고 AAL2까지 정식 수용한다 — 방향은 비밀번호 강화가 아니라 그 반대다.

**OWASP ASVS 5.0**의 V6.2도 전문에서 스스로 조건부임을 밝힌다:

> "**this section contains requirements for making sure that passwords are created and handled securely.**"

개별 항목이 전부 `Verify that user set passwords are…` / `Verify that users can change their password.` 형태로 **비밀번호의 존재를 전제**한다. "제공하라"는 항목은 없다.

---

## 2. 오히려 규제 표면이 줄어든다

비밀번호를 두지 않으면 다음이 **애초에 발동하지 않는다.**

- 고시 제7조① 단서(일방향 암호화 저장) — 저장할 비밀번호가 없다
- ASVS V6.2 전체(생성·변경·블록리스트·강도) — 해당 없음
- ASVS V6.4의 복구 항목 상당수 — password·activation code 전제라 해당 없음

**즉 "비밀번호를 안 만드는 것"은 규제 회피가 아니라 리스크 표면 축소다.**

덧붙여, 정보주체 **1만명 미만**을 처리하는 소상공인·개인·단체는 고시 제4조① 단서로 **내부 관리계획 수립을 생략할 수 있다.**

---

## 3. 대신 지는 의무 — 정확히 하나다

비밀번호를 두지 않는 대가로 생기는 **명시적 의무는 하나**이고, 그것은 인증수단이 아니라 **정책의 문서화**다.

**NIST SP 800-63C**(Federation) §3.8, relying party 대상 **SHALL**:

> "**The RP SHALL document the practices and policies that it enacts when an RP subscriber account reaches a state of having zero associated federated identifiers; no means of access, including alternative authenticators; and no means of recovery**, including account linking and account resolution. In such cases, the RP subscriber account **SHOULD be disabled or terminated**."

같은 절이 대체 인증수단은 **MAY**로 둔다:

> "The RP **MAY** allow a subscriber to access their RP subscriber account using direct authentication processes by allowing the subscriber to add and remove authenticators in the RP subscriber account."

> **즉 표준이 요구하는 것은 "비밀번호를 두어라"가 아니라 "접근수단이 0이 된 계정을 어떻게 할지 정하고 적어두어라"이다.**

같은 표준이 단일 IdP 위험 자체는 인정한다(§8): *"users may be fearful of losing access to multiple RPs if a single IdP is unavailable, either temporarily or permanently."*
그런데 그 처방으로 비밀번호를 요구하지는 않는다.

---

## 4. 이 의무가 추상적이지 않은 이유

Google 공식 정책:

> "if a Google Account has not been used or signed into for at least **2 years**, we may delete the account and its contents"

**Google 계정이 삭제되면 그것을 유일한 접근 경로로 삼은 careerhub 계정은 영구히 잠긴다.**
지금 코드에는 이 상황에 대한 처리도, 정책도 없다.

그리고 이 사용자의 데이터는 사라지지 않는다 — 스크랩과 매칭조건이 careerhub 쪽 저장소에 `userId`로 묶인 채 남는다.
**주인이 영원히 돌아올 수 없는 문서가 쌓인다.**

정할 것은 셋이다: 그 계정을 **비활성화할 것인가 파기할 것인가**, 파기한다면 **언제**, 그리고 **사전에 알릴 방법이 있는가**(이메일이 유일한 연락 수단인데 그 이메일이 곧 사라진 Google 계정이다).

---

## 5. Naver를 붙일 때 새로 생기는 규범

**① 발급자별 네임스페이스 — ASVS 6.8.1**

> "Verify that, if the application supports multiple identity providers (IdPs), **the user's identity cannot be spoofed via another supported identity provider (eg. by using the same user identifier).** The standard mitigation would be for the application to register and identify the user using **a combination of the IdP ID (serving as a namespace) and the user's ID in the IdP**."

현재 스키마의 `UNIQUE(authorized_by, authorized_id)`가 이미 이 형태다 — 유지하면 된다.
**같은 항목이 이메일 단독 매칭을 계정 탈취 경로로 지목한다.** 현재 스키마에 남아 있는 `UNIQUE(email)`은 이 관점에서도 다시 봐야 한다.

**② 계정 연결의 조건 — NIST SP 800-63C §3.8.1, 둘 다 SHALL**

> "If the RP allows a subscriber to link multiple subscriber accounts in this way, **the RP SHALL require an authenticated session with the subscriber account for all linking functions.**"

> "The RP SHALL provide a **notice to the subscriber** when: A new federated identifier is added to an existing RP subscriber account, or A federated identifier is removed from an RP subscriber account, but the account is not terminated."

즉 **연결은 로그인한 상태에서만 허용**하고, **추가·제거를 사용자에게 알려야** 한다. 지금은 알림 채널 자체가 없다.

**③ 인증 강도 정보의 처리 — ASVS 6.8.4**
IdP가 `acr`·`amr`·`auth_time`을 주지 않으면 **문서화된 대체 방침**을 두어야 한다.

**④ 복수 인증 경로의 문서화 — ASVS 6.1.3 / 6.3.4**
경로가 둘 이상이면 각각의 보안 통제와 인증 강도를 **문서화하고 일관되게 강제**해야 한다.

---

## 6. 앱을 낸다면 (웹에는 해당 없음)

Apple App Store Review Guidelines 4.8:

> "Apps that use a third-party or social login service (such as … **Google Sign-In** …) to set up or authenticate the user's primary account with the app **must also offer as an equivalent option another login service**"

**웹 서비스에는 적용되지 않는다.** 다만 iOS 앱을 내면 Google 단독으로는 심사를 통과하지 못한다.
그리고 **여기서도 요구되는 것은 비밀번호가 아니라 또 하나의 IdP**다(이메일 비공개가 가능한 것).

---

## 7. 현재 코드가 이 절들에 비추어 못 맞추는 것

- **접근수단 0 계정에 대한 정책이 없다** — 코드에도 문서에도 없다(§3의 유일한 SHALL)
- **알림 채널이 없다** — 정체성 추가·제거 통지를 보낼 수단이 없다(§5②)
- **`UNIQUE(email)`이 남아 있다** — Naver를 붙이는 순간 같은 사람의 두 번째 가입이 실패하고, 이메일 기반 매칭의 유혹이 생긴다(§5①)
- **`acr`/`amr`/`auth_time`을 보지 않는다.** 애초에 `openid` scope를 요청하지 않아 ID Token 자체를 받지 않으므로, 이 claim들을 볼 자리가 없다(§5③)
- **탈퇴 흐름이 정체성을 파괴한다** — 탈퇴 시 이름·식별자·이메일을 전부 덮어쓰므로, 같은 Google 계정으로 재가입하면 이전 계정과의 연결이 복원되지 않는다. §3의 정책을 세울 때 이 흐름과 함께 봐야 한다

---

## 판정 — 결정인가 티켓인가

**비밀번호를 두지 않는다**는 것은 지금 상태의 유지이고, 뒤집어도 되돌리기가 어렵지 않다(추가는 언제든 가능하다).
그러므로 그 자체로는 결정 문서의 임계선에 못 미친다.

**임계선을 넘는 후보는 §3의 정책 하나다** — *"접근수단이 0이 된 계정을 어떻게 하는가"*.
파기를 택하면 **되돌릴 수 없고**(지운 데이터는 돌아오지 않는다), 사용자 데이터의 수명을 정하는 일이라 영향 범위가 저장소를 넘는다.
나머지(§5의 네임스페이스·연결 조건·알림)는 이행 항목이므로 티켓이다.

---

## 열린 질문 — 사람의 것

1. **접근수단이 0이 된 계정을 비활성화할 것인가 파기할 것인가.** 파기한다면 유예 기간은. 이것이 이 논의에서 유일하게 되돌릴 수 없는 축이다.
2. **사용자에게 알릴 채널을 만들 것인가.** 정체성 추가·제거 통지가 표준상 SHALL인데 현재 수단이 없다. 이메일뿐이라면, 그 이메일이 사라진 계정에는 닿지 않는다.
3. **계정 연결을 허용할 것인가.** 허용하면 §5②의 두 SHALL이 따라오고, 허용하지 않으면 같은 사람이 IdP별로 별개 계정을 갖는다. 이 답이 `UNIQUE(email)`의 처분을 정한다.
4. **비밀번호를 두지 않는 것을 명문화할 것인가.** 표준이 요구하는 것은 §3의 정책 문서화뿐이지만, "왜 소셜 전용인가"를 적어두면 나중에 같은 논의를 반복하지 않는다.
5. **Naver 외에 무엇을 언제 붙일 것인가.** §5의 규범은 IdP가 둘이 되는 순간 전부 발동한다.

## 다음 단계 후보 (수렴 시)

- 열린 질문 1이 파기 쪽으로 정해지면: ADR 후보다. 되돌릴 수 없고 사용자 데이터의 수명을 정한다.
- 열린 질문 3(계정 연결)은 정체성 저장 모델과 **함께 뒤집힐 가능성**이 높다 — 연결 정책 없이 저장 모델만 정하면 의미가 절반이고, 그 역도 같다. 한 결정으로 묶일지 판단이 필요하다.
- §5의 이행 항목(네임스페이스 유지·연결 시 인증된 세션·추가/제거 알림·`acr` 대체 방침 문서화)은 리프 티켓이다. 근거 ADR은 선택.
- §7의 `UNIQUE(email)` 처분은 열린 질문 3의 답에 종속된다 — 먼저 정하지 않는다.
