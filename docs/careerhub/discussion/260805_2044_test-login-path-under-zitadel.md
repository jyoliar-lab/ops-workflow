---
type: discussion
topic: careerhub
subjects: [zitadel, auth-service, careerhub-front, oidc]
status: done
ref-adrs: [ADR-0028, ADR-0030]
---

# Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정

## 0. 문제

티켓 [#7](https://github.com/jyoliar-lab/ops-workflow/issues/7)은 careerhub-front 재작성 검증(12개 라우트 중 8개가 인증 요구)의 선행으로, **auth-service에 비-OAuth 로그인 경로(테스트 전용)를 코드로 추가**하는 그림이다. 그런데 ADR-0030(proposed)이 인증 발급을 Zitadel로 옮기는 방향이다 — 티켓의 전제(auth-service가 발급자)가 무너진다.

두 가지를 판정한다: ① Zitadel이 비대화형 로그인을 제품으로 지원하는가 ② **그 경로로 발급된 토큰이 발급 훅(Actions v2 클레임 주입 — ADR-0028의 P2 접합)을 통과하는가.** ②가 갈리면 테스트 토큰은 운영 토큰과 클레임이 달라져 인증 라우트 검증의 등가성이 깨진다.

## 1. 조사 ① — Zitadel의 비대화형 로그인 지원

**ROPC(Resource Owner Password Grant)는 명시적 미지원**이다 ([grant-types 문서](https://zitadel.com/docs/apis/openidoauth/grant-types)) — "아이디/비번을 토큰 endpoint에 직접"은 없다. 대신 세 경로가 제품에 있다:

| 경로 | 무엇 | 등가성 |
|---|---|---|
| **P-a. Session API (v2)** | `POST /v2/sessions`(loginName check) → `PATCH`(password check) → OIDC auth request를 세션으로 finalize → **표준 authorization_code 교환**. 브라우저·로그인 UI 없이 순수 API | ★ 최등가 — 발급의 마지막 단계가 운영 로그인과 **동일한 grant**다. `IAM_LOGIN_CLIENT` 권한의 서비스 계정 필요 |
| **P-b. Token Exchange + Impersonation** (RFC 8693) | 서비스 계정 토큰을 테스트 유저의 토큰으로 교환. token exchange는 기본 활성, **impersonation은 인스턴스 Security Settings + 전용 롤(`*_IMPERSONATOR`)로 이중 게이트** | 더 간단하나 토큰에 `act` 클레임(impersonator 표시)이 붙는다 — 검증 미들웨어가 무시하면 무해하나 운영 토큰과의 차이는 차이다 |
| **P-c. 서비스 계정 직발급** (JWT profile · client credentials · PAT) | machine user의 자기 토큰 | **부적합** — human 유저가 아니라 온보딩 게이트·주입 클레임이 다르다. 인증 라우트 검증 목적에 안 맞는다 |

전제 하나: 앱 구성이 소셜 전용이어도 **테스트 유저는 Zitadel 로컬 password 유저**로 둘 수 있다(제품이 로컬 유저를 지원). 이게 정확히 "테스트 전용 계정" 요구와 일치한다.

## 2. 조사 ② — 발급 훅 통과 여부: **통과한다 (소스 확인)**

문서는 grant type별 커버리지를 명시하지 않아 소스(main 브랜치)로 확인했다. 근거 체인:

- **Token Exchange** — `internal/api/oidc/token_exchange.go`가 교환 토큰 생성 시 `s.getUserInfo(...)`를 만들어 `createIDToken`/`createJWT`에 넘긴다.
- **클레임 조립** — `internal/api/oidc/userinfo.go`의 `userinfoFlows()`가 그 안에서 **Actions v1(`actions.Run`)과 v2 실행 타깃(`execution.QueryExecutionTargetsForFunction` → `execution.CallTargets`) 둘 다** 실행한다. 트리거는 `PreUserinfoCreation`·`PreAccessTokenCreation` — 정확히 클레임 주입 함수들이고, 소스 주석이 이 둘 외 트리거는 없다고 못박는다. `AppendClaims`로 커스텀 클레임이 얹힌다.
- **Session API 경로** — 별도 확인이 필요 없다. 발급의 마지막 단계가 **표준 authorization_code 교환**이므로 브라우저 로그인과 발급 경로가 동일하다. 세션 수립 수단(password check vs IdP intent)만 다르고 토큰 조립은 같은 길이다.

**결론: P-a·P-b 모두 운영과 동일한 클레임 주입 경로를 탄다.** ADR-0030 Consequences의 "훅 세대 정렬"(L51) 우려는 login v1+Actions v2 조합의 공백이었고, 테스트 경로가 새 공백을 만들지는 않는다.

잔여 단서 둘 (티켓 수행 시 실측 확인 항목):

- main 브랜치 소스 기준이다 — 배포 버전 고정 시 재확인.
- `preaccesstoken`이 access token에 실리려면 access token이 **JWT 타입**이어야 한다. ADR-0028이 로컬(JWKS) 검증을 전제하므로 어차피 JWT 설정이다 — 정합.

## 3. 티켓 #7 재판정

Goal("비대화형 로그인 진입점")은 IdP가 무엇이든 유효하다. 수단이 통째로 바뀐다:

| 현행 티켓 | Zitadel 방향에서 |
|---|---|
| auth-service에 코드 경로 추가 | **✂ 소거** — 코드를 짤 것이 없다. 제품 기능이다 |
| `target-repos: auth-service` | **↻** IaC/배포 저장소(Zitadel 설정: 테스트 org/유저, `IAM_LOGIN_CLIENT` 서비스 계정) + 테스트 하네스가 사는 저장소(토큰 획득 헬퍼) |
| "플래그·환경 게이트로 운영 비활성" | **↻ 격상** — 운영 인스턴스에 테스트 유저·impersonation 정책이 **부재**하면 경로 자체가 없다. 코드 규율이 아니라 구조(§8)로 닫힌다 |
| "`withAccessToken()` 호환" | **↻** "운영과 동일 발급 경로의 표준 OIDC 토큰 + 발급 훅 통과"(§2에서 구조 확인 — AC는 실측 확인으로) |
| "테스트 프레임워크 선택은 이 티켓이 아니다" | **● 유지** |

경로는 **P-a(Session API)를 기본형**으로 판정한다 — 운영 발급과 grant 수준에서 동일하고, `act` 클레임 같은 차이가 없다. P-b는 P-a가 막힐 때의 보조.

## 4. 갈림길 — 순서. 사람의 것

ADR-0030은 아직 proposed고, 티켓 #7은 프론트 재작성 검증의 선행이다. Zitadel 전환과 프론트 재작성의 순서에 따라:

| | 무엇 | 비용 |
|---|---|---|
| **A. 티켓 재작성, 전환에 후행** | 위 §3대로 고쳐 Zitadel 전환 뒤 수행 | 버릴 코드 0. 대신 인증 라우트 검증이 전환 완료까지 막힌다 |
| **B. 현행대로 지금 수행** | auth-service에 임시 경로를 만들고 전환 때 버린다 | 버릴 코드 + e2e 로그인 헬퍼 재작성 2회 |
| **C. 검증 순서를 뒤집는다** | 비인증 4개 라우트부터 회귀 그물, 인증 8개는 전환 후. 티켓은 A로 재작성하되 긴급도가 내려간다 | 인증 라우트의 회귀 노출 기간이 길어진다 |

A·C를 고르면 티켓 본문 수정은 **ADR-0030 accept 뒤**가 맞다 — 굳지 않은 결정으로 티켓을 다시 쓰면 초안 반려 시 두 번 고친다(§5 "굳지 않은 결정으로 일하지 않는다"의 리프판).

**판정(사람): A.** 티켓 #7은 Zitadel 전환에 후행한다. 본문 수정은 ADR-0030 accept·공표 뒤 — 그때 이 문서 §3의 재작성안을 쓴다.

## 열린 질문 — 사람의 것

1. ~~Zitadel 전환과 프론트 재작성, 무엇이 먼저인가~~ — **답했다: 전환이 먼저(A).** §4 판정.
2. 테스트 유저·서비스 계정을 **어느 저장소가 소유하는가**(IaC vs 테스트 하네스의 시딩) — 티켓 재작성 시 target-repos가 여기서 정해진다. **티켓 수정 시점으로 이월.**

## 검토하고 버린 것

- **P-c(서비스 계정 직발급)로 때우는 것** — 비대화형으로는 가장 싸지만 machine user 토큰이라 온보딩 게이트·클레임이 human과 다르다. "인증 라우트를 유저처럼 통과"라는 Goal에 못 미친다.
- **auth-service 임시 경로를 전환 후에도 보험으로 유지하는 것** — 두 발급자가 병존하면 검증 미들웨어·훅 정합이 이중화된다. `260805_1801`이 7-3 수렴을 폐기한 것과 같은 이유로, 전환하면 버린다.
- **티켓 #7을 지금 바로 고쳐 쓰는 것** — ADR-0030이 proposed다. 반려되면 티켓을 두 번 고친다. 이 문서가 재작성안을 들고 대기하는 것으로 충분하다.
