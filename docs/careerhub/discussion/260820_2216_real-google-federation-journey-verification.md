---
type: discussion
topic: careerhub
subjects: [zitadel, google-oauth, careerhub-web, playwright]
status: active
ref-adrs: [ADR-0028, ADR-0030]
---

# 실제 Google 연합 로그인 여정의 검증 — 스모크와 회귀 그물의 이원화

## 0. 문제

`260805_2044`는 인증 라우트 검증용 토큰 획득을 P-a(Zitadel Session API)로 수렴시켰다.
그러나 그 경로는 **연합 여정 자체** — careerhub-web `/auth/start` → Zitadel 로그인 UI → Google → Zitadel IdP intent → `/auth/callback` → 세션 수립 — 를 한 번도 실제로 통과하지 않는다.
이 여정이 깨지는 원인은 대부분 코드 회귀가 아니라 설정·외부 변화다: Zitadel IdP 설정 drift, Google 쪽 변경(동의화면·앱 검증 상태·secret), redirect URI 불일치.
사이드 프로젝트라 트래픽이 낮아, 사후 발견(사용자 신고·에러율)의 지연이 길다.

**사람 방향(확정): 실제 Google 테스트 계정으로 이 여정을 자동 검증하고 싶다.**
실행 환경 계획: ① 로컬 PC에서 회귀 수준 ② 본격화 시 Argo Workflow로 임시 서비스 리소스를 세워 e2e — OAuth 로그인도 거기서 시도.
CI(GitHub Actions/CodeBuild)에서는 e2e를 돌리지 않는다.

## 1. 사실 (코드)

- careerhub-web의 로그인 왕복: `src/app/auth/start/route.ts` → 발급자 → `src/app/auth/callback/route.ts`("Zitadel에 등록된 redirect URI가 이 경로다").
- e2e는 현재 "인증 수단 진입점 제시"까지만 검증한다 — `e2e/scenarios/login.spec.ts` 주석이 그 뒤를 명시적으로 유보.
- CI(`.github/workflows/g1-check.yml`)는 `ubuntu-latest` — 데이터센터 IP.
- Zitadel은 `jyoliar-k8s` gitops(`gitops/base/services/careerhub/apps/zitadel/`)에 산다. 시크릿은 ExternalSecret 패턴.

## 2. 실행 환경 축 — 주거지 IP가 성립 조건을 바꾼다

Google의 자동화 로그인 차단은 신호의 합성이다: IP 평판(데이터센터) × 신규 브라우저 프로필 × headless 지문 × 빈도.

- 데이터센터 IP + 매회 새 프로필 + headless = 구조적으로 거부되는 조합("안전하지 않은 브라우저"·CAPTCHA 비결정 발생).
- **주거지 IP + 지속 프로필(기기 신뢰 쿠키) + headed + 낮은 빈도 = 실무에서 실제로 성립하는 조합.**

사람의 계획(로컬 PC·홈랩 Argo)은 후자다 — `260805_2044` 당시엔 없던 전제고, 원안("Google 계정에 아이디/패스워드")의 치명 축이 소거된다.
단, IP가 전부는 아니다: 브라우저 프로필을 실행 간 지속시키는 것(볼륨 마운트 등)이 성립의 나머지 절반이다.

## 3. 구도 — 여정 스모크 1개와 회귀 그물은 분리한다

Google 로그인을 인증 라우트(8개) 테스트 전체의 세션 소스로 쓰면, 그물 전체가 Google의 비결정성을 상속한다 — 한 번의 챌린지 인터스티셜이 회귀 신호 전체를 적색으로 만든다.

| | 수단 | 성격 |
|---|---|---|
| **여정 스모크 1개** | 실제 Google 테스트 계정으로 전체 여정 1회 통과 — 로그인 성공·세션 수립까지만 확인 | 외부 요인 포함 · 비결정 허용 · 실패 = 조사 신호 |
| **인증 라우트 회귀 N개** | P-a 토큰(`260805_2044`) | 결정적 · 병렬 안전 · 실패 = 회귀 |

스모크 실패는 회귀 실패와 다른 신호다 — Google 쪽 사정일 수 있으므로, 같은 게이트로 묶으면 그물의 신호 대 잡음이 무너진다.

## 4. 임시 리소스 × Google redirect URI — 설계 제약

Google OAuth client의 redirect URI는 **사전 등록·와일드카드 불가**다.
Google에 등록되는 URI는 앱이 아니라 **Zitadel의 콜백**이다(연합 홉: Google → Zitadel).
Argo가 세우는 임시 리소스의 범위에 따라 갈린다:

| | 무엇 | 성립 여부 |
|---|---|---|
| **Z-a. 임시 환경에 Zitadel까지** | 매 실행 임시 호스트의 Zitadel | ✂ Google 연합 불성립 — 임시 호스트를 Google에 등록할 수 없다 |
| **Z-b. 공유 Zitadel(고정 호스트) + 임시 앱** | Google 홉은 고정, 앱 redirect URI(임시 호스트)만 Zitadel에 동적 등록 | 성립 — 단 등록의 수명 관리(생성·회수)가 하네스 일이 된다 |
| **Z-c. 임시 환경 호스트 자체를 고정** | 스테이징 1식을 재사용(동시 1실행) | 성립 — 등록 관리 소거, 대신 병렬 실행 불가 |
| **Z-d. Zitadel 인스턴스는 임시, 호스트는 고정** | 매 실행 새 Zitadel을 세우되 `id.test-careerhub.jyo-liar.com`으로 노출 | 성립 — 고정 호스트라 Google 등록 1회로 끝. **사람 판정 (아래)** |

ADR-0030의 sector identifier 논리 그대로다 — 연합의 정체성은 Zitadel **호스트**에 붙지, 인스턴스 수명에 붙지 않는다.
따라서 Z-a의 불성립은 "임시라서"가 아니라 "호스트가 임시라서"였다 — 호스트만 고정하면 인스턴스는 매번 새로 세워도 된다.

**판정(사람): Z-d.** 임시 리소스에 Zitadel을 포함하되 호스트는 `id.test-careerhub.jyo-liar.com` 고정.

Z-d의 귀결 셋:

1. **매 실행 제로에서 시딩한다** — Google IdP 설정(테스트 client secret), 테스트 유저(P-a용 로컬 password 유저 포함), `IAM_LOGIN_CLIENT` 서비스 계정, Actions v2 타깃까지. 기존 `jyoliar-k8s`의 zitadel-config job 패턴의 연장이며, **"IaC가 빈 Zitadel을 동작 상태까지 세울 수 있다" 자체가 매 실행 검증된다** — 부수 효과가 아니라 이득이다.
2. **동시 1실행 제약** — 고정 호스트 하나에 인스턴스 둘을 물릴 수 없다. Argo 실행 간 배타 락이 필요하다.
3. **매 실행이 최초 로그인이다** — Zitadel엔 이 Google 계정의 연결 이력이 없으므로, 여정 스모크는 항상 신규 가입·자동 등록 경로를 탄다. 결정적이라 오히려 좋으나, "기존 유저 재로그인" 시나리오는 이 스모크가 못 덮는다(필요하면 시딩으로).

## 5. 운영 단서 — 테스트 계정

- **2FA는 장애물이 아니라 완화책이다**: TOTP secret을 저장하면 코드 생성이 결정적으로 자동화되고, 계정에 2FA가 있는 편이 Google의 의심 챌린지 빈도를 낮춘다.
- **정지·잠금은 대비의 문제다**: 복구는 수동(사람)이므로, 스모크는 "실패 = 알람"으로 두고 그물을 영구 적색으로 만들지 않는 처리(스킵·별도 채널)가 필요하다.
- 자격증명(패스워드·TOTP secret) 보관은 기존 ExternalSecret 패턴의 연장선.

## 6. 조사 — Google 공식의 "테스트 계정"은 무엇이고, 자동 로그인을 허용하는가

**Google 공식 문서에 "테스트 계정" 제도는 있다 — 그러나 푸는 문제가 다르다.**

- **Test users**는 OAuth 동의화면(현 Google Auth Platform의 Audience)의 기능이다 ([Manage App Audience](https://support.google.com/cloud/answer/15549945)).
  publishing status가 **Testing**인 앱은 최대 100명의 test user만 인가할 수 있고, 인가 시 미검증 앱 경고가 뜨며, **인가는 동의 시점부터 7일 뒤 만료**된다(refresh token 포함).
  즉 이것은 **미검증 앱의 동의(consent) 게이트**이지, 자동화 로그인 허용 제도가 아니다.
- **로그인 전용이면 그 제약이 대부분 적용되지 않는다.** 공식 문서의 예외 둘:
  ① 앱이 기본 프로필 scope(name·email·profile — 즉 openid 로그인)만 요청하면 **test user 목록에 없어도 인가할 수 있다**(같은 문서).
  ② 7일 refresh token 만료도 "요청 scope가 name·email·프로필로 한정되면 적용되지 않는다" ([OAuth 2.0 공식 문서](https://developers.google.com/identity/protocols/oauth2) 직접 인용 확인).
- **비민감 scope만 쓰면 검증 없이 In production 전환도 가능하다** ([OAuth App Verification Help Center](https://support.google.com/cloud/answer/13463073), [sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification)) — 검증 의무는 sensitive·restricted scope에만 붙는다.
- **자동화 브라우저 로그인을 승인하는 공식 경로는 없다.** 로그인 페이지의 봇 감지("이 브라우저 또는 앱은 안전하지 않을 수 있습니다")는 의도된 정책이고, **test user 여부와 무관하게 적용**된다.
  Google이 공식으로 제공하는 테스트 수단은 동의 게이트(위)까지다 — 자격증명 자동 입력의 성립은 §2의 조합(주거지 IP·지속 프로필)에 달린 문제로 남는다.
- 부수 확인: refresh token은 계정×client당 100개 한도(초과 시 최고령 무효화) — 스모크가 offline access를 요구하지 않는 한 무관.

**귀결 — 열린 질문 ④의 판단 재료:** careerhub의 Google 홉은 로그인 전용(기본 scope)이므로, 테스트 client를 분리해도 **검증 의무가 없고 Testing 모드의 페널티(7일 만료·test user 목록)도 사실상 비켜간다.**
분리 비용이 애초 우려보다 낮다.
실측 확인 항목 하나: Testing 상태의 로그인 전용 앱에서 미검증 경고 화면이 실제로 뜨는지(뜨면 자동화가 한 화면 더 지난다).

## 검토하고 버린 것

- **GitHub Actions(데이터센터 IP)에서 Google 로그인 구동** — 봇 감지가 구조적으로 거부. 사람도 CI에서 e2e를 돌리지 않을 계획이라 충돌 없음.
- **Google 로그인을 인증 테스트 전체의 세션 소스로** — 그물이 Google의 비결정성을 상속. 여정 검증의 가치는 스모크 1개로 전부 얻는다(§3).
- **임시 환경에 Zitadel 동반 기동 + Google 연합**(Z-a) — redirect URI 등록 불가로 불성립(§4).
- **여정 검증을 안 하고 관측 알람으로만**(사후 탐지) — 저트래픽이라 발견 지연이 길고, 사람이 능동 검증을 선택했다.

## 열린 질문 — 사람의 것

1. ~~Argo e2e의 임시 리소스 범위~~ — **답했다: Z-d**(Zitadel 포함·호스트 고정). §4 판정.
2. 스모크 실패를 실행 전체의 판정과 분리하는가 — 스모크는 Google 쪽 사정으로도 깨지므로, 실행 결과를 "회귀 없음 ∧ 여정 확인 실패" 같이 나눠 읽을 수 있어야 한다. 구현은 Playwright project/tag 분리 수준.
3. Google 로그인 상태의 실행 간 지속 수단 — 새 프로필 매 실행은 Google에게 "매번 새 기기"로 보여 챌린지 확률을 올린다. 프로필 볼륨(PVC) 지속 또는 storageState(쿠키) 저장·복원 중 택일.
4. 테스트용 Google OAuth client를 운영 client와 분리하는가 — 분리하면 테스트 실험이 운영 client의 평판·검증 상태를 건드리지 못한다. 단 testing 모드 client는 동의화면에 미검증 경고가 끼어들어 자동화가 한 화면 더 지나야 한다.
