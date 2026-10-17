---
type: discussion
kind: survey
goal: careerhub-web-test-layers
topic: careerhub-front
subjects: [careerhub-web, next.js, vitest, jest, jsdom, happy-dom, undici, msw, openapi-fetch, playwright, node.js]
status: done
related: [261017_2030_careerhub-web-tdd-loop-layers.md]
---

# Next.js 16 앱의 네트워크 없는 테스트 층 — 도구 조사 (2026-10-17)

## 질문

논의 문서 `261017_2030_careerhub-web-tdd-loop-layers.md`의 열린 축 넷이 사실을 요구했다.
① 단위·컴포넌트 러너와 DOM 환경은 Next 16 · React 19 · Node 24에서 무엇이 서는가.
② 프로세스 안에서 fetch를 가로채는 대역은 무엇이 있고, 네트워크 유출을 구조로 막을 수 있는가.
③ `next/headers`의 `cookies()`와 `redirect()`를 부르는 Route Handler를 서버 기동 없이 돌릴 수 있는가.
④ 버린 후보(브라우저 기동형 컴포넌트 테스트 · 러너 없는 `node:test`)가 정말 지는가.

조사일은 전부 2026-10-17이다.
npm 버전·공표일은 `npm view`로 레지스트리에서 직접 읽었다.

## 조사

### 1. Next.js 공식 가이드가 말하는 것

출처: Next.js Testing 개요 (https://nextjs.org/docs/app/guides/testing · lastUpdated 2026-02-03), Vitest 가이드 (https://nextjs.org/docs/app/guides/testing/vitest · lastUpdated 2026-08-25), Jest 가이드 (https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/02-guides/testing/jest.mdx).

- 테스트 종류를 다섯으로 가른다 — Unit · Component · Integration · E2E · Snapshot.
- **비동기 서버 컴포넌트는 단위 테스트 밖이다.** 인용: *"Since `async` Server Components are new to the React ecosystem, some tools do not fully support them. In the meantime, we recommend using End-to-End Testing over Unit Testing for `async` components."*
- Vitest 가이드도 같은 말을 한다. *"Vitest currently does not support them. While you can still run unit tests for synchronous Server and Client Components, we recommend using E2E tests for `async` components."*
- Vitest 설치 목록: `vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/dom vite-tsconfig-paths` (TypeScript 프로젝트는 마지막 것이 필요).
- Vitest 설정은 `plugins: [tsconfigPaths(), react()]` · `test.environment: 'jsdom'` 둘뿐이다.
- 가이드의 스크립트는 `"test": "vitest"`이고, 가이드 자신이 *"Vitest will watch for changes in your project by default"* 라고 적는다 — CI·루프용은 `vitest run`이어야 한다.
- 테스트 파일 위치: *"The example above uses the common `__tests__` convention, but test files can also be colocated inside the `app` router."*
- Jest는 `next/jest` 변환기를 제공한다. *"automatically configures Jest by setting up `transform` with the Next.js Compiler, auto-mocking stylesheets, image imports, and `next/font`. It also loads environment variables from `.env` files."*
- Next 컴파일러(SWC) 소스: 테스트 러너 아래(`jest: true`)에서는 `serverActions`·`serverComponents` 변환을 끈다 — `"use server"`가 단위 테스트에서 동작하지 않는다 (https://github.com/vercel/next.js/blob/canary/packages/next/src/build/swc/options.ts). careerhub-web은 Server Action을 쓰지 않고 Route Handler를 쓰므로 지금은 걸리지 않는다.
- 공식 예제 `examples/with-vitest`의 devDependencies는 `vitest ^3.2.4` · `jsdom ^26.1.0` · `@testing-library/react ^16.3.0` · `@vitejs/plugin-react ^5.0.1`이다 — 예제가 최신 메이저보다 두 단계 뒤다 (https://raw.githubusercontent.com/vercel/next.js/canary/examples/with-vitest/package.json).

### 2. 러너와 DOM 환경의 현재 버전

| 패키지 | 최신 | 공표일 | 비고 |
|---|---|---|---|
| vitest | 5.0.5 | 2026-10-15 | 5.0 발표 2026-09-03. **Node ≥ 22.12.0 · Vite ≥ 6.4.0** |
| jest | 30.5.2 | 2026-09-18 | 30.0 발표 2025-06-04. TypeScript ≥ 5.4 |
| @vitejs/plugin-react | 6.1.2 | 2026-10-05 | |
| jsdom | 30.1.3 | 2026-10-15 | |
| happy-dom | 21.0.3 | 2026-10-15 | |
| @testing-library/react | 16.3.3 | 2026-08-27 | 16.1에서 React 19 지원. 16.0부터 `@testing-library/dom`이 peer |
| @testing-library/dom | 10.4.2 | 2026-09-13 | |
| @testing-library/user-event | 14.6.8 | 2026-10-13 | |
| vite-tsconfig-paths | 6.1.1 | 2026-02-11 | |

**Vitest 5.0** (https://vitest.dev/blog/vitest-5 · 2026-09-03).
깨지는 변경: `clearMocks` 기본값 `true` · await 하지 않은 비동기 단언(`resolves`·`rejects`)은 테스트 실패 · `expect.poll`은 timeout에 reject · locator가 strict 기본 · `bench`가 top-level import에서 빠짐 · 커스텀 matcher 타입의 제네릭 순서 변경.
jsdom·happy-dom 지원 자체의 변경은 없다 — 벤치마크에 둘이 나올 뿐이다.

**Jest 30** (https://jestjs.io/blog/2025/06/04/jest-30 · 2025-06-04).
Node 14·16·19·21 지원 종료 · `jest-environment-jsdom`이 jsdom 21→26 · `expect` 별칭 제거 · 비열거 속성이 `toEqual`에서 제외 · 네이티브 ESM에서 `import.meta` 지원 · `.mts`·`.cts` 네이티브 · Jest가 패키지당 단일 파일로 번들돼 내부를 건드리는 도구가 깨질 수 있다.

**jsdom vs happy-dom** (https://vitest.dev/guide/environment · Vitest 5 문서).
인용: happy-dom은 *"considered to be faster than jsdom, but lacks some API"*.
파일 단위로 `// @vitest-environment jsdom` 주석으로 환경을 바꿀 수 있다 — 전역 기본값을 하나 두고 예외를 파일에서 뒤집을 수 있다는 뜻이다.

**React Testing Library 16** (https://github.com/testing-library/react-testing-library/releases).
16.0.0: *"`@testing-library/dom` was moved to a peer dependency and needs to be explicitly installed."*
16.1.0: *"Add support for React 19."*
16.3.2: `onCaughtError` 타입을 React 19에 맞췄다.

### 3. 프로세스 안 fetch 대역

**Node의 fetch는 undici다.**
`@mswjs/interceptors` README: *"In Node.js, the global `fetch` is powered by Undici; in the browser, it is the native `window.fetch`."* (https://raw.githubusercontent.com/mswjs/interceptors/main/README.md)
Node에 번들된 undici는 코드에서 import할 수 없으므로 `MockAgent`를 쓰려면 `undici`를 devDependency로 따로 설치한다 (https://codewithhugo.com/node-test-native-fetch-intercept-undici/).

**undici MockAgent** (https://raw.githubusercontent.com/nodejs/undici/main/docs/docs/api/MockAgent.md · undici 8.12.2 · 2026-10-15).
- *"A `MockAgent` is a Dispatcher that intercepts HTTP requests made through undici."*
- `setGlobalDispatcher()`: *"only affects undici APIs that use the global dispatcher, such as `request()` and `fetch()`."* undici 사이트는 *"Global dispatcher is shared among compatible undici modules, including undici that is bundled internally with node.js"* 라고 덧붙인다 (https://undici.nodejs.org/#/docs/best-practices/mocking-request.md).
- `disableNetConnect()`: *"Causes every request that is not matched by a mock interceptor to throw, disallowing real HTTP requests."*
- `enableNetConnect([matcher])`: 문자열·RegExp·함수로 허용 호스트를 좁힌다.
- `assertNoPendingInterceptors()`: 등록했는데 안 쓰인 인터셉터가 있으면 던진다.
- 호출 이력은 기본 꺼짐 · `enableCallHistory()` 뒤 `getCallHistory()`가 *"every request made through the MockAgent (whether intercepted or not)"* 를 돌려준다.
- 문서의 예는 전부 `request()`다 — `fetch()`와 함께 쓴 공식 예제는 없다. GitHub discussion #1661은 `enableNetConnect`에 호스트를 줘도 전부 가로채였다는 보고 하나를 남겼다 (https://github.com/nodejs/undici/discussions/1661) — 버전별 실측이 필요하다.

**MSW 3** (https://github.com/mswjs/msw/releases · 3.0.0 = 2026-09-28 · 최신 3.0.3 = 2026-10-10).
- 깨지는 변경: `onUnhandledRequest` → **`onUnhandledFrame`** · **Node ≥ 22** (18·20 폐기) · TypeScript ≥ 5.9 · **ESM 전용** · Node에서 쿠키를 더 관리하지 않는다.
- `onUnhandledFrame` 전략 (https://mswjs.io/docs/api/setup-server/listen): `"warn"`(기본 — 경고 후 그대로 보냄) · `"error"`(*"Print an error and halt the frame execution"*) · `"bypass"`.
- 가로채는 방식: 브라우저는 Service Worker, Node는 *"class extension instead of module patching"* (https://mswjs.io/docs/). `@mswjs/interceptors`의 `FetchInterceptor`가 *"Intercepts the global `fetch` function"* 을 맡는다.
- 가로채기 범위: *"the interception of requests in the current process"*.

**openapi-fetch가 권하는 것** (https://openapi-ts.dev/openapi-fetch/testing · https://openapi-ts.dev/openapi-fetch/api).
- `createClient`에 `fetch` 옵션이 있다 — *"Fetch instance used for requests (default: `globalThis.fetch`)"*. 요청 단위로도 덮을 수 있다.
- 테스트 페이지: 요청을 **들여다볼** 때는 `fetch` 옵션에 `vi.fn()` 같은 spy를 넣는다. 응답을 **모사**할 때는 *"Mock Service Worker is highly recommended for mocking API responses in tests."*
- 순서 제약: *"server.listen must be called before `createClient` is used"*.
- careerhub-web의 `src/lib/api/client.ts`는 `createClient({ baseUrl })`를 모듈 최상위에서 부르고 `fetch` 옵션을 노출하지 않는다 — 함수 수준 주입을 택하면 그 파일에 이음매를 여는 코드 변경이 선행한다.

### 4. Route Handler를 서버 없이 돌리기

- Next의 오류 문서: `cookies()` 등 Dynamic API를 요청 범위 밖에서 부르면 *"Dynamic API was called outside request"* 다. 테스트가 핸들러를 맨손으로 부르면 요청 범위가 없어 이 오류를 만난다 (https://nextjs.org/docs/messages/next-dynamic-api-wrong-context).
- Next가 제공하는 테스트 유틸은 `next/experimental/testing/server`의 `isRewrite`·`getRewrittenUrl`·`getRedirectUrl`로, **proxy(middleware) 전용**이다. Route Handler의 요청 범위를 만들어 주는 공식 유틸은 없다 (https://github.com/vercel/next.js/blob/v16.2.9/docs/01-app/03-api-reference/03-file-conventions/proxy.mdx).
- 길 ⓐ — `vi.mock('next/headers', …)`로 `cookies()`가 가짜 저장소를 돌려주게 하고, `redirect()`가 던지는 오류를 잡아 목적지를 단언한다. 2차 출처들이 공통으로 쓰는 모양이다 (https://arcjet.com/learn/test-nextjs-api-routes 등). careerhub-web은 `next/headers`를 `src/lib/auth/store/server-cookie.ts` 한 파일에서만 부르므로, 그 파일 대신 `SessionStore` 포트의 가짜 구현을 끼우는 쪽이 더 얕다.
- 길 ⓑ — `next-test-api-route-handler` 5.0.7 (2026-08-16 · https://raw.githubusercontent.com/Xunnamius/next-test-api-route-handler/main/README.md). `appHandler`에 route 모듈을 넘기면 *"uses Next.js's internal resolvers to precisely emulate route handling"* 하고, `cookies`·`headers`·`redirect`가 핸들러 안에서 동작한다 (*"Yep, those fancy helper functions work too!"*). 제약: *"NTARH must always be the first import in your test file"* · Next가 전역 fetch를 패치하므로 NTARH가 `globalThis.fetch`를 import 시점에 캐시하고 복원하지 않는다 — §3의 fetch 대역과 순서가 얽힌다. App Router 지원은 `next@14.0.4`부터이고 각 Next 릴리스에 대해 자동 테스트된다고 적는다.
- `next/navigation`의 `useRouter`는 클라이언트 컴포넌트 테스트에서 `vi.mock("next/navigation", …)`으로 stub 한다 — 공식 레시피는 없고 discussion #48937이 가장 많이 인용된다 (https://github.com/vercel/next.js/discussions/48937).

### 5. 버린 후보의 근거

- **Playwright Component Testing** (https://playwright.dev/docs/test-components). 실험 패키지(`@playwright/experimental-ct-react`)는 *"have been removed and are no longer published"* 이고, 쓰던 사람은 *"stay on Playwright 1.62"* 라고 적는다. 컴포넌트는 실제 브라우저에서 돌고 Vite dev server가 필요하다. `@playwright/test` 최신은 1.64.1(2026-10-14)이고 careerhub-web은 1.62.1(2026-07-30)에 고정돼 있다 — 이 저장소는 CT 패키지를 쓰지 않으므로 올려도 걸리는 것이 없다.
- **Vitest Browser Mode**. 4.0(2025-10-22)에서 안정화됐고 `@vitest/browser-playwright` 같은 provider가 필요하다 (https://www.infoq.com/news/2025/12/vitest-4-browser-mode). 브라우저를 띄우므로 "프로세스 밖으로 나가지 않는다"는 경계 밖이다.
- **`node:test` + 타입 스트리핑**. Node 24는 `.ts`의 타입을 기본으로 벗기지만 *"there is no support for JSX files"* 이고 tsconfig의 paths도 읽지 않는다 (https://www.mintlify.com/nodejs/node/api/typescript · https://wallabyjs.com/whatsnew/node-test-native-type-stripping.html). `.tsx` 컴포넌트 테스트에는 결국 `tsx` 같은 로더가 붙어 "러너 없음"이 아니게 된다.

## 논의 문서로 가져가는 것

- 비동기 서버 컴포넌트(`src/app/**/page.tsx`)는 단위 렌더 대상이 아니다 — Next 공식 입장이다. 그 약속은 e2e 또는 그것이 부르는 순수 함수에 산다.
- Next 공식 Vitest 경로는 의존 6개 · 설정 2줄이다. 스크립트는 `vitest run`이어야 한다(`vitest`는 watch).
- Vitest 5는 Node ≥ 22.12를, MSW 3은 Node ≥ 22를 요구한다 — careerhub-web CI의 Node 24와 맞는다. 둘 다 2026년 9월에 나온 어린 메이저다.
- Jest 30은 `next/jest`로 Next 컴파일러(SWC)·`.env`를 자동 연결한다. ESM은 "개선"이지 완전하지 않다.
- 프로세스 안 fetch 대역은 둘이다. undici `MockAgent`는 `disableNetConnect()`로 **매치 안 된 요청을 던지게** 해 네트워크 유출을 구조로 막고 의존이 하나다. MSW 3은 `onUnhandledFrame: "error"`로 같은 효과를 내고 openapi-fetch 문서가 권하며 브라우저 쪽 코드에도 같은 핸들러를 쓸 수 있다.
- MockAgent와 `fetch()`를 함께 쓴 공식 예제는 없다 — jsdom 환경에서 전역 fetch가 undici dispatcher를 그대로 쓰는지는 실측해야 닫힌다.
- Route Handler의 `cookies()`는 요청 범위 밖에서 던진다. 공식 유틸은 없고, careerhub-web은 `next/headers` 호출이 한 파일에 갇혀 있어 `SessionStore` 가짜로 우회할 수 있다. NTARH는 전역 fetch를 패치하므로 fetch 대역과 import 순서가 얽힌다.
- Playwright CT는 제거됐고 Browser Mode는 브라우저를 띄운다 — 둘 다 닫힌 경계 밖이다. `node:test`는 JSX를 못 돈다.
