---
type: discussion
kind: deliberation
goal: careerhub-web-test-layers
topic: careerhub-front
subjects: [careerhub-web, playwright, vitest, jest, undici, msw, github-actions, ticket-engineer, tdd-loop]
status: active
ref-adrs: [ADR-0012, ADR-0013, ADR-0014, ADR-0020]
related: [261017_2025_nextjs-unit-test-tooling-survey.md, 260722_1618_regression-net-and-merge-gate.md, ../../ops-workflow/discussion/260930_1524_tdd-flow-decisions.md, ../../ops-workflow/discussion/260910_1900_promise-gate-per-repository-class.md]
---

# careerhub-web의 테스트 층 — TDD 루프가 도는 층과 회귀 그물로 남는 층

## 1. 문제

애플리케이션 개발 티켓의 워크플로우가 TDD 집행 흐름(digest `ops-workflow/digest/261011_1740_tdd-execution-flow.md`)으로 바뀌었다.
그 흐름은 착수 때 "변경 전에 · 저장소 안에서 · 이번 변경의 약속을 · 실패하는 테스트로 쓸 수 있는가"를 묻고, 테스트 골격(러너 · 설정 · CI 잡)이 없는 저장소를 비대상으로 친다.
careerhub-web이 가진 러너는 Playwright e2e 하나이고, 그것은 실행 중인 앱과 운영 백엔드를 겨눈다.
그래서 다음 careerhub-web 티켓에서 ticket-engineer는 `TDD: 비대상 — 러너 없음`을 적게 된다.

인터뷰에서 합의한 문제는 둘이다.
첫째, 비대상으로 남으면 약속의 소유가 없다 — 시나리오 표의 승인이 없으니 사람이 전체 diff를 읽어 검수한다.
둘째, 회귀가 머지 뒤에 드러난다 — 주소 변환 · 세션 · 캐시 헤더 같은 서버 로직의 회귀를 지금은 운영 e2e나 사용자가 발견한다.
그리고 사람은 "운영 API를 직접 부르는 e2e만 있는" 지금보다 체계적인 프론트엔드 테스트 설계를 원한다.

이 논의의 산출물은 **구성 방안의 비교와 판정**이다.
티켓 발행 · ADR 초안은 판정 뒤 다음 호출의 것이다.
범위 밖은 셋이다 — 시각 회귀 자동화 · e2e를 G1 게이트에 올리는 것 · non-prod 환경 신설.
인증 라우트의 e2e 자동 검증은 #7의 것이고, 인증 **로직**(세션 · 클레임 · OIDC)의 네트워크 없는 층은 이 논의 안이다.

열려 있던 것은 "어느 층을 TDD 루프에 넣나"였고 인터뷰에서 닫혔다(§3-1).
그 뒤 남은 것은 도구와 모양이다(§4).

## 2. 실측

읽은 것은 `workspace/ref/careerhub-web`(2026-10-17 · HEAD `fb138cf`)과 `workspace/ref/ticket-engineer`(HEAD `67d085f`)이다.
외부 도구의 사실은 조사 문서 `261017_2025_nextjs-unit-test-tooling-survey.md`에 있고, 여기엔 결론에 쓰인 것만 둔다.

**지금 서 있는 검증**
- `package.json`에 `test` 스크립트가 없다. `check` = `tsc --noEmit` + `eslint --max-warnings 0`, `e2e` = `playwright test`. devDependency에 러너 · DOM 환경 · Testing Library가 없다(`package-lock.json` 실측).
- `.github/workflows/g1-check.yml`은 `check`와 `spec-drift` 두 잡이다. 머리 주석이 *"느린 검사(e2e 등)는 이 게이트의 범위가 아니다"* 라고 못 박았다.
- `playwright.config.ts`는 `LEGACY_BASE_URL`(기본값 운영 `https://careerhub.jyo-liar.com`)과, 주어질 때만 `NEXT_BASE_URL`을 겨눈다. 주석: *"결정적 데이터가 없는 동안 이 명세는 차단 게이트가 될 수 없다."*
- e2e는 시나리오 5파일 · 여정 17개다. `e2e/scenarios/`는 앱을 모르고 `e2e/support/driver.ts`의 인터페이스로만 말하며, `e2e/wiring/{legacy,next}/`가 선택자를 흡수한다(ops-workflow#9). `condition-vocabulary-cache.spec.ts` 하나만 화면 뒤의 트래픽을 본다.
- `src/`는 6,705줄이고 그중 1,871줄이 생성물(`schema.d.ts` · `auth-ledger-schema.d.ts`)이다.

**네트워크 없이 돌 수 있는 표면**
- 순수 변환: `src/lib/job-posting/list-search.ts`(359줄 — 주소 ↔ 화면 상태 ↔ 계약 질의), `detail-view.ts`, `src/lib/api/conditions.ts`의 다듬기(옵셔널 제거 · 이름순 정렬 · 회사 검색어 첫 토막).
- 인증 로직: `src/lib/auth/{claims,oidc,session,refresh,login,login-transaction,seal}.ts` 약 900줄. `next/headers`를 부르는 파일은 `store/server-cookie.ts` **하나**이고, `store/index.ts`가 `SessionStore` 포트의 구현을 고르는 유일한 지점이다 — 가짜 저장소를 끼울 이음매가 이미 있다.
- 조립: `src/lib/api/client.ts`가 `openapi-fetch`의 `createClient({ baseUrl })`를 모듈 최상위에서 만들고 `bearerAuth` 미들웨어를 단다. `fetch` 옵션은 노출하지 않는다. 호출 함수(`job-postings.ts` · `conditions.ts` · `reviews.ts` · `agreements.ts` · `scrap-jobs.ts`)는 오류를 `ApiError`류로 바꾸고 `encoded_query`를 base64로 만든다.
- Route Handler 4벌: `src/app/auth/{start,callback,logout}/route.ts` · `src/app/onboarding/submit/route.ts`는 `redirect()`와 `@/lib/auth`를 부르는 얇은 HTTP 층이다. `src/app/api/conditions/serve.ts`는 캐시 헤더와 오류 상태를 만든다.
- 클라이언트 컴포넌트 6개(`"use client"`): `applied-chips` · `career-filter` · `company-search` · `condition-search-box` · `job-categories` · `skill-search`. `condition-search-box.tsx`는 `useRouter`로 이동하고, `skill-search.tsx`는 `src/lib/api/conditions-browser.ts`를 통해 **상대 URL** `fetch("/api/conditions/skills")`를 부른다.
- `src/app/**/page.tsx`는 전부 비동기 서버 컴포넌트다 — Next 공식 입장은 단위 렌더 대상이 아니라는 것이다(조사 §1).

**린트가 테스트 파일에 거는 것**
- `eslint.config.mjs`의 `authModuleGuard`는 `**/auth/*` 내부 import를 `src/lib/auth/**` 밖에서 거부한다. `src/lib/auth` 안의 테스트는 내부를 부를 수 있고, 밖의 디렉터리(`tests/`)에 둔 테스트는 공개면 `@/lib/auth`만 부를 수 있다.
- `tsconfig.json`의 `include`가 `**/*.ts` · `**/*.tsx`라 테스트 파일도 `tsc --noEmit`을 지난다.
- CI의 Node는 24, 로컬은 26이다.

**하네스가 저장소에 요구하는 것** (`ticket-engineer/.claude/skills/ticket-start/SKILL.md` · `tdd-loop/*.md`)
- 테스트 명령은 한 줄이고 CI와 같은 것이다. *"타입 검사가 CI에 있으면 그것도."*
- `tdd-green`은 시나리오 하나를 통과시킬 때마다 그 명령을 전체 실행한다. `ac-verifier`는 커버리지 도구가 저장소에 **이미 있을 때만** 쓴다 — 도구를 설치하지 않는다.
- `strength.md`: 대역은 **정적 응답**이고 손으로 만든 최소 입력이다. 모킹은 테스트마다 격리한다.
- 시나리오 표의 티어 · 의존성 열은 검수용이 아니라 아직 없는 테스트 정책의 증거다.

**앞선 결정**
- ADR-0012는 Next.js를 택하며 *"타입 · 계약 · 테스트를 선택이 아니라 전제로 만든다"* 고 적었다. ADR-0013은 *"타입 검사와 별도로 계약 관리와 통합 테스트는 계속 필요하다."*
- ADR-0014 · ADR-0020: 계약 타입은 생성물이고 consumer는 스펙 사본을 두지 않는다. 생성 타입으로 구속된 픽스처 리터럴은 스펙 사본이 아니다.
- `260722_1618` §4는 유닛 · 컴포넌트 층을 순환 위험이 가장 높은 층으로 놓았다. 그때 순수 로직은 *"38줄뿐"* 이었다 — 지금은 위의 표면이다.
- `260930_1524` §5는 테스트 정책을 **ADR감이되 지금은 쓰지 않는다**로 보류했고, 그 ADR이 답할 것에 *"언제 e2e인가 — careerhub-web #9가 선례"* 를 적었다. 이 논의는 그 ADR의 증거다.
- `260910_1900` §1은 careerhub-web을 부류 ⑤ *"브라우저 — e2e 명세 = 약속"* 으로 분류했다.
- `261011_1705`의 대가 목록: *"green이 비싸지는 저장소(e2e · 실 의존성)에서는 이 비용이 red 승인의 비용을 넘을 수 있다."*

## 3. 인터뷰에서 닫힌 축

### 3-1. TDD 루프가 도는 층

**선택: 네트워크 없이 도는 층만 루프에 넣는다. 경계는 프로세스다 — 프로세스 밖으로 나가지 않으면 루프 안이다.** 프로세스 안 fetch 대역에 대고 도는 조립 층 테스트는 안이고, 서버 · 브라우저 기동이 필요한 것은 밖이다. (인터뷰, 2026-10-17)

<details><summary>버린 안</summary>

- 모사 백엔드를 겨눈 e2e까지 루프에 — green이 시나리오마다 서버 · 브라우저를 띄운다. 사람이 *"일일이 로컬 서버를 띄우는 테스트는 적합하지 않다"* 고 닫았다
- 대역 없는 순수 로직만 — `lib/api`의 조립(인코딩 · 오류 변환 · omitempty 정규화)과 Route Handler가 루프 밖에 남는다
- 실 백엔드(non-prod)까지 — 환경이 없고 범위 밖이다

</details>

### 3-2. e2e · 통합 층의 지위

**선택: 회귀 그물이다. 사람이 로컬에서 돌리고, 겨누는 것은 지금처럼 운영이다.** TDD 루프의 산출물이 아니라 화면 Task의 완료 조건으로 남는다(#9의 모양 그대로). (인터뷰, 2026-10-17)

<details><summary>버린 안</summary>

- CI 비차단 잡으로 PR마다 — 운영을 못 때리므로 모사 백엔드와 next 배선 하나가 더 필요하다. 배선 · 데이터가 늘어난다
- 모사는 CI, 운영은 사람 — 같은 비용에 둘을 유지한다

</details>

### 3-3. "운영 API를 때리지 않는다"의 적용 범위

**선택: TDD 흐름과 CI가 돌리는 테스트에 적용한다.** 기존 e2e가 운영을 겨누는 것은 사람의 수동 검사라 이 제약 밖이다. (인터뷰, 2026-10-17)

<details><summary>버린 안</summary>

- 기존 e2e에도 — legacy · next 배선 모두 겨눌 것이 바뀌어야 하고 #9의 데이터 전제가 흔들린다
- 새 층에만 — 루프가 돌리는 명령이 운영을 부를 길을 열어 둔다

</details>

### 3-4. 컴포넌트 테스트 층

**선택: 둔다. 루프 안이다.** 클라이언트 컴포넌트 6개의 행동("후보를 고르면 그 조건이 걸린 주소로 이동한다")을 jsdom + Testing Library로 검사한다. 비동기 서버 컴포넌트는 Next 공식대로 단위 렌더 밖이다. (인터뷰, 2026-10-17)

<details><summary>버린 안</summary>

- 두지 않는다 — 클라이언트 컴포넌트의 행동이 e2e 회귀 층에만 남고, e2e는 루프 밖이라 그 행동에 약속의 소유가 생기지 않는다

</details>

### 3-5. 표의 행이 약속으로 거슬러 올라가는 요구

**선택: AC에 달린 행은 도메인 언어의 약속으로 거슬러 올라가야 한다. 출처 `추가`인 행은 회귀 그물로 허용하고, 사람은 그 행이 있다는 사실만 본다.** 읽히는가는 층이 아니라 행의 언어가 정한다 — 단위 층의 "조건이 바뀌면 첫 페이지부터"는 읽히고, "세 번째 버튼에 `aria-pressed`"는 읽히지 않는다. (인터뷰, 2026-10-17)

<details><summary>버린 안</summary>

- 모든 행이 거슬러 올라가야 한다 — 구현 세부는 테스트하지 않게 된다. 회귀 그물이 얇아진다
- 요구하지 않는다 — `260722_1618` §4의 순환이 그대로 열린다. 사람이 승인하되 읽지 못하는 행이 늘고, 틀린 약속이 맞는 약속과 똑같이 굳는다

</details>

### 3-6. 사람이 읽는 약속의 언어

**선택: 층에 따라 둘 다.** 사용자 여정은 e2e 시나리오의 언어로, 서버 규칙(주소 · 세션 · 캐시)은 단위 테스트의 언어로 — 약속의 종류가 층을 고른다. (인터뷰, 2026-10-17)

### 3-7. G1

**선택: 루프 층의 테스트는 G1에 차단으로 들어간다.** red 커밋의 빨강은 의도된 것이고 머지 게이트는 마지막 커밋의 런을 본다 — digest의 전제와 같다. #10의 "빠른 검사만" 판정은 유지된다. 루프 층은 그 안에 든다. (인터뷰, 2026-10-17)

### 3-8. 산출물과 범위

**선택: 이 호출은 방안 비교와 판정까지다.** 발행 · 초안은 다음 호출. 범위 밖은 §1의 셋이다. 결정적 데이터는 범위 밖이 아니라 열린 축(§4-3)이다 — 운영을 못 때리면 대역의 데이터가 어디서 오는지는 피할 수 없는 질문이다. (인터뷰, 2026-10-17)

## 4. 열린 축 — 논의

### 4-1. 러너와 DOM 환경

실측(조사 §1 · §2): Next 공식 가이드는 Vitest와 Jest 둘을 둔다.
Vitest 5(2026-09-03 · Node ≥ 22.12)와 Jest 30(2025-06-04)이 현재 메이저다.
비동기 서버 컴포넌트는 어느 쪽에서도 단위 렌더가 안 된다.
RTL 16은 React 19를 지원하고 `@testing-library/dom`을 peer로 요구한다.

- **A. Vitest 5 + jsdom + Testing Library** — Next 가이드의 설치 목록 6개 · 설정 2줄 그대로다. ESM 네이티브라 Next 16 · React 19와 모듈 체계가 같고, `vi.mock`으로 `next/navigation` · `next/headers`를 파일 단위로 바꾼다. 이기는 조건: 빠른 전체 실행이 값일 때(green이 시나리오마다 전체를 돈다). 지는 조건: 어린 메이저의 깨지는 변경(`clearMocks` 기본값 · await 없는 비동기 단언 실패)이 red 검토자의 "동어반복" 판정과 얽혀 오탐을 낼 때 — 5.0.x에서 한 번 더 실측이 필요하다
- B. Jest 30 + `next/jest` + jsdom — `next/jest`가 Next 컴파일러(SWC) · `.env` · CSS 모킹을 자동으로 잇는다. 앱과 같은 컴파일러를 타는 것이 장점이다. 이기는 조건: ESM 전환 비용보다 Next 밀착을 원할 때. 지는 조건: ESM이 "개선"에 머물러 `openapi-fetch` 같은 ESM 의존에서 변환 설정이 늘 때 · `jest-environment-jsdom`이 jsdom 26에 묶여 DOM 환경을 따로 못 올릴 때
- C. 안 한다 — e2e만 유지. 비용: §3-1 · §3-4가 이미 닫혔으므로 이 옵션은 그 판정을 되돌리는 것이다. 매 careerhub-web 티켓이 비대상으로 남고 약속의 소유가 생기지 않는다

happy-dom은 러너의 별도 축이 아니다 — Vitest는 파일 머리 주석으로 환경을 바꿀 수 있어, 기본은 jsdom으로 두고 느린 파일만 뒤집으면 된다(조사 §2).

### 4-2. 프로세스 안 네트워크 경계의 대역

실측(§2 · 조사 §3 · §4): 네트워크로 나가는 자리는 셋이다.
서버 → composer · auth-service(`lib/api/client.ts`의 openapi-fetch), 브라우저 → web 호스트(`conditions-browser.ts`의 상대 URL fetch), 서버 → Zitadel(`lib/auth/oidc.ts` · `refresh.ts`의 토큰 교환).
Node의 fetch는 undici이고, 프로세스 안에서 그것을 가로채는 도구는 undici `MockAgent`와 MSW 3 둘이다.
`MockAgent.disableNetConnect()`는 매치 안 된 요청을 **던지고**, MSW의 `onUnhandledFrame: "error"`도 같다 — 둘 다 "루프는 네트워크로 나가지 않는다"를 규율이 아니라 구조로 만든다.
`createClient`는 `fetch` 옵션을 받지만 `client.ts`가 노출하지 않는다.
Route Handler의 `cookies()`는 요청 범위 밖에서 던지고, 공식 유틸은 없다.

- **A. undici `MockAgent` 전역 dispatcher + `disableNetConnect()`** — 의존 하나(`undici`)이고 Node fetch의 엔진 그 자체다. 테스트마다 `MockAgent`를 만들어 `setGlobalDispatcher`에 걸고 `assertNoPendingInterceptors()`로 안 쓰인 대역을 잡는다. 이기는 조건: 서버 쪽 조립 층(`lib/api` · Route Handler · OIDC 교환)이 대역의 주 대상일 때. 지는 조건: 실측 둘이 어긋날 때 — ⓐ Vitest jsdom 환경에서도 전역 fetch가 undici dispatcher를 그대로 쓰는가, ⓑ `conditions-browser.ts`의 상대 URL `fetch("/api/…")`를 Node fetch가 받는가(Node fetch는 기준 URL이 없어 상대 URL을 거부한다 — 브라우저 쪽 코드는 대역이 아니라 함수 수준 교체가 필요할 수 있다)
- B. MSW 3 `setupServer` + `onUnhandledFrame: "error"` — openapi-fetch 문서가 권하는 길이고, HTTP 핸들러 하나로 서버 쪽(composer 응답)과 브라우저 쪽(`/api/conditions` 응답)을 같은 어휘로 모사한다. 이기는 조건: 컴포넌트 테스트와 조립 테스트가 같은 응답 모사를 공유하길 원할 때. 지는 조건: 2026-09-28에 나온 메이저(ESM 전용 · `onUnhandledRequest` 개명)의 초기 결함을 떠안기 싫을 때 · "class extension" 가로채기가 Next의 fetch 패치(NTARH 비고)와 얽힐 때. `server.listen`이 `createClient` 전에 와야 한다는 순서 제약이 있다
- C. 함수 수준 교체 — `vi.mock("@/lib/api/job-postings")`처럼 호출 모듈을 통째로 바꾸거나, `client.ts`에 `fetch` 주입 이음매를 열어(코드 변경 티켓) 가짜를 넣는다. 세션은 이미 `SessionStore` 포트가 있어 `server-cookie.ts` 대신 메모리 구현을 끼우면 `next/headers`를 부르지 않는다. 이기는 조건: HTTP 수준 라이브러리를 들이지 않고 Route Handler · 컴포넌트의 행동만 검사할 때. 지는 조건: `lib/api` 자체의 약속(base64 인코딩 · 오류 → `ApiError` · omitempty 정규화)이 루프 밖에 남는다 — 그 층은 HTTP 수준 대역 없이는 검사되지 않는다
- D. 안 한다 — 대역 없는 순수 로직만 루프에. 비용: §3-1이 "프로세스 안이면 루프"로 닫았으므로 이 옵션은 그 판정을 좁히는 것이다. `lib/api` · Route Handler · 컴포넌트의 fetch가 전부 e2e에만 남는다

A와 C, B와 C는 배타가 아니다 — 세션은 C(포트의 가짜), HTTP는 A 또는 B가 자연스럽다.
Route Handler의 `redirect()`는 던지는 오류를 잡아 목적지를 단언하는 것으로 충분하고(조사 §4), NTARH는 전역 fetch를 import 시점에 캐시해 A · B와 순서가 얽히므로 들이지 않는 쪽이 단순하다.

### 4-3. 대역 픽스처(결정적 데이터)의 출처

실측(§2 · 조사 §3): `strength.md`는 대역을 손으로 만든 최소 입력 · 정적 응답으로 정한다.
생성 타입 `components["schemas"]["JobPosting"]`으로 선언한 리터럴은 형태가 구속된다.
스펙에 `example`은 0개다(`260722_1618` §9-①).
운영 응답에는 화면이 흡수하는 사정이 있다 — 괄호 붙은 회사명 · 호출마다 다른 직군 순서 · omitempty.

- **A. 손으로 쓴 최소 픽스처, 생성 타입으로 구속** — 행마다 Given을 그 행이 가르는 성질만 담아 쓴다. `strength.md`가 요구하는 모양 그대로이고 ADR-0020과 무관하다(스펙 사본이 아니다). 이기는 조건: 표의 Given이 사람이 읽을 크기여야 할 때. 지는 조건: 운영의 사정(괄호 · 순서 불안정)을 agent가 떠올리지 못해 Given에 그 경우가 없을 때 — `strength.md`의 "Given이 성질을 가르지 못함"이 그 자리를 잡아야 한다
- B. 운영 응답 녹화 replay — 사람이 한 번 운영에서 받아 저장소에 둔 JSON을 대역이 돌려준다. 이기는 조건: 실데이터의 기벽을 Given에 자동으로 싣고 싶을 때. 지는 조건: 녹화물은 저장소에 사는 **응답 사본**이다 — ADR-0020이 금한 스펙 사본은 아니지만 같은 결로 "사본끼리의 정합"이 되고, 갱신 책임이 생기며, 녹화 한 번은 운영 호출이다(사람이 하면 §3-3 밖이지만 재녹화가 agent 손에 들어가면 안 된다). `strength.md`의 "Given은 그 행이 가르는 성질만"과도 결이 다르다 — 수백 묶음의 녹화물에서 어느 성질이 갈리는지 사람이 읽지 못한다
- C. 스키마에서 생성(faker류) — 스펙에 example이 0개라 생성기가 만들 값은 임의값이고, 성질을 가르는 Given(동률 · 경계)을 만들지 못한다. 지는 조건이 지금 성립한다
- D. 안 한다 — 4-2 D와 같다

### 4-4. 배치 · 명명 · 명령

실측(§2 · 조사 §1): `authModuleGuard`는 `src/lib/auth/**` 밖에서 인증 내부 import를 거부한다.
`tsconfig`가 테스트 파일도 typecheck한다.
Next 가이드는 `__tests__`와 colocate 둘 다 허용한다.
Next 가이드의 `"test": "vitest"`는 watch 모드다.
하네스의 테스트 명령은 CI와 같은 한 줄이고 타입 검사도 포함한다.
`260930_1524` §5는 "파일이 층(계산 · 변환 · 조립 · 경계)을 따르나 주제를 따르나"를 테스트 정책 ADR의 미결로 남겼다.

- **A. 소스 옆 colocate(`list-search.test.ts` · `skill-search.test.tsx`), 명령은 `npm run check` = typecheck + lint + `vitest run`** — 인증 내부의 테스트가 `src/lib/auth` 안에 살아 린트 경계와 충돌하지 않는다. README의 "로컬 한 커맨드 = 게이트" 원칙이 그대로 선다. 하네스의 한 줄 명령이 `npm run check`가 된다. 이기는 조건: 저장소의 기존 원칙(한 커맨드 · 경계는 린트)과 겹치고 싸게 시작할 때. 지는 조건: 층별 배치의 실험 데이터를 원할 때 — colocate는 파일이 주제(모듈)를 따른다는 선택이다
- B. `tests/{unit,component,integration}/` 층별 디렉터리 — `260930`의 미결에 실험 데이터를 준다. 지는 조건: `authModuleGuard`가 `tests/`에서 인증 내부 import를 거부하므로 `session.ts` · `oidc.ts`의 내부 테스트가 공개면 `@/lib/auth`를 통해서만 가능해진다 — 린트 예외를 열면 ops-workflow#8의 경계가 테스트 때문에 뚫린다
- C. 모듈 옆 `__tests__/` — Next 예제의 관례다. A와 린트 성질이 같고 디렉터리가 하나 더 생긴다. 이기는 조건: 소스 디렉터리에서 테스트 파일을 한눈에 가르고 싶을 때
- D. 명령을 둘로 — `npm test`(루프)와 `npm run check`(G1). 하네스는 한 줄을 받으므로 둘 중 하나만 루프에 들어가고, 타입 검사가 빠진 쪽을 고르면 ticket-start의 *"타입 검사가 CI에 있으면 그것도"* 와 어긋난다. 지는 조건이 지금 성립한다

## 5. 반대편 — 이 설계가 틀리는 조건

- **한 저장소에 두 모드가 선다.** 화면 Task의 약속이 비동기 서버 컴포넌트와 여정에만 있으면 그 티켓은 여전히 비대상이거나, 표에 순수 함수 행만 남는다. #9의 "명세 선행"은 루프 밖에서 계속되지만 red 검토자 · green의 분리는 받지 못한다. 이 둘을 한 티켓 안에서 어떻게 적는지는 ticket-start의 판정 한 줄이 감당해야 한다 — 저장소가 그것을 `CLAUDE.md`에 선언하지 않으면 매 티켓이 판단거리다.
- **루프를 피하려 로직을 비동기 서버 컴포넌트로 밀어 넣을 수 있다.** 테스트가 안 되는 자리가 곧 테스트 안 해도 되는 자리가 된다. 지금 저장소는 변환을 `lib/`에 두는 구조라 그 유혹이 작지만, 그것은 구조이지 강제가 아니다.
- **§3-5의 추적 요구는 규율이다.** 출처 열이 AC인지 `추가`인지는 사람이 읽어야 알고, 스크립트가 거부하지 않는다. 사람이 `추가` 행을 읽지 않고 승인하는 날이 쌓이면 `260722_1618` §4의 순환이 그 행에서 되살아난다.
- **대역의 값은 agent가 쓴다.** 틀린 Given은 틀린 약속을 굳히고, 운영의 기벽(괄호 회사명 · 순서 불안정)은 Given에 없으면 검사되지 않는다. 운영을 겨누는 e2e가 사람의 손에만 남으므로 그 기벽은 사람이 e2e를 돌릴 때만 드러난다.
- **회귀 층은 사람이 기억할 때만 돈다.** next 배선이 화면 변경에 뒤처져도 울리는 것이 없다. #9의 완료 조건 패턴("해당 시나리오가 next 배선에서 통과")이 사람의 검수 항목으로 살아 있어야 한다.
- **어린 메이저 둘(Vitest 5 · MSW 3)이 2026년 9월에 나왔다.** 초기 결함을 겪으면 그 비용은 ticket-engineer가 아니라 사람이 진다 — 하네스는 도구를 고치지 않는다.
- **jsdom의 fetch와 상대 URL.** 브라우저 쪽 코드(`conditions-browser.ts`)는 상대 URL을 쓰고, Node fetch는 그것을 거부한다. 4-2 A를 고르면 컴포넌트 테스트에서 이 함수는 대역이 아니라 교체(4-2 C) 대상이다 — 실측 전에는 가정이다.

## 6. 버린 것

- **브라우저를 띄우는 컴포넌트 테스트**(Vitest Browser Mode · Playwright Component Testing) — 프로세스 밖으로 나간다. Playwright의 실험 CT 패키지는 1.62 뒤 제거됐고 careerhub-web의 `1.62.1` 고정은 우연이다(조사 §5).
- **러너 없는 `node:test`** — Node 24가 타입은 벗기지만 JSX는 못 돈다. 컴포넌트 층(§3-4)을 두는 순간 로더가 붙어 "러너 없음"이 아니게 된다.
- **모사 백엔드 서버를 띄워 e2e를 루프에** — §3-1이 닫았다. green이 서버 · 브라우저를 시나리오마다 띄우는 비용이 red 승인의 비용을 넘는다(`261011_1705`).
- **e2e를 CI 비차단 잡으로** — §3-2가 닫았다. 운영 금지(§3-3)와 만나면 모사 백엔드 + 배선 하나가 더 필요해진다.
- **테스트 정책 ADR을 지금 쓰는 것** — `260930_1524` §5의 보류를 유지한다. 이 논의는 저장소 하나의 시도이고, 표의 티어 · 의존성 열이 쌓인 뒤 ADR이 읽을 증거다.
- **NTARH(next-test-api-route-handler)** — 전역 fetch를 import 시점에 패치해 fetch 대역과 순서가 얽힌다. `redirect()`의 오류를 잡고 `SessionStore` 가짜를 끼우면 필요가 없다.

## 7. 임계선 — ADR감인가

되돌리기 비용 × 영향 범위로 본다.

- **러너 · DOM 환경(4-1)** — 지금 테스트 파일은 0개다. 되돌리기는 devDependency 교체이고 영향은 이 저장소다. **티켓감.** 테스트가 수백 개 쌓인 뒤에는 되돌리기가 그 수에 비례하지만, 그때의 결정은 "바꾸지 않는다"이지 ADR이 아니다.
- **대역 방식(4-2) · 픽스처 출처(4-3)** — 모든 테스트의 Given 모양을 정하므로 쌓일수록 one-way door에 가까워진다. 그러나 저장소 하나의 것이고, `260930_1524`가 보류한 테스트 정책 ADR("의존성 경계마다의 기본값 — 실제 / 녹화 / fake / mock")이 그것을 담을 자리다. **지금은 티켓과 저장소 `CLAUDE.md`의 선언으로 두고, 이 논의의 판정이 그 ADR의 증거가 된다.**
- **루프 층과 회귀 층의 분리(3-1 · 3-2)** — 되돌리기는 테스트 명령 한 줄과 CI 잡 하나다. **티켓감.** 다만 `260910_1900` 옵션 C("저장소가 자기 약속 인공물을 `CLAUDE.md`에 선언한다")가 정확히 이 자리다 — careerhub-web은 *"약속 인공물 = 루프 층(단위 · 컴포넌트 · 프로세스 안 조립) + e2e 회귀 층"* 을 선언하는 첫 사례가 된다.
- **하네스 델타** — 없다. 테스트 명령 한 줄에 `npm run check`가 들어가면 ticket-start · tdd-green · ac-verifier가 그대로 돈다. "비대상 — 러너 없음"은 구성이 서는 순간 사실이 아니게 된다.

## 8. 다음

판정(§4)이 나면 다음 호출이 낳는 것.

- **careerhub-web 구성 Task** — 러너 · DOM 환경 · 대역 · 배치 규약 · `check`에 테스트 결합 · G1. 변경의 약속은 "실패하는 테스트가 `npm run check`를 빨강으로 만든다"이고, 그 자체가 첫 red다. 파일럿으로 기존 순수 함수(`list-search.ts`) 하나에 표 → red → green을 한 바퀴 돌릴지는 사람이 정한다 — #72(시각 검증 파일럿)와 같은 결이다.
- **저장소 `CLAUDE.md`의 선언** — 약속 인공물이 무엇이고 어느 층이 루프인지. `260910_1900` C의 첫 사례. 같은 Task에 담긴다.
- **테스트 정책 ADR의 증거** — 이 논의의 §3-1 · §4 판정과, 이후 티켓들의 티어 · 의존성 열.
- **adr-judge 인계** — 없다. 이 논의는 proposed 초안을 낳지 않는다.
