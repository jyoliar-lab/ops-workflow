---
type: discussion
kind: deliberation
goal: legacy-public-exposure
topic: careerhub
subjects: [auth-service, careerhub-front, api-composer, careerhub-httproute, jwt, google-oauth, zitadel]
status: done
ref-adrs: [ADR-0028]
related:
  - docs/careerhub/discussion/260804_1735_auth-service-structural-defects.md
  - docs/careerhub/discussion/260805_1323_asvs-conformance-gaps-auth-service.md
  - docs/careerhub/discussion/260805_1245_password-free-social-only-obligations.md
  - docs/careerhub/discussion/261026_1632_cloudflare-exposure-wiring-and-edge.md
---

# 레거시 스택 임시 공개 — 인증 기능을 어떻게 처분하나

## 1. 문제

리뉴얼(#43 Zitadel 전환 · #6 프론트 재작성)이 길어져, 구직 활동용 포트폴리오 링크로 쓰기 위해 **레거시 스택**(careerhub-front v0.0.3 · auth-service v0.2.1 · api-composer v0.4.0)을 3~6개월 임시로 공개 인터넷에 노출하려 한다.
노출 방식은 Cloudflare Tunnel 이다.

공개 전에 가려야 했던 것은 하나다.
auth-service 의 알려진 인증 결함이 **커리어허브 안에서만 아픈 것인지, 가입자의 개인정보 노출로 이어지는 것인지**, 그리고 그 심각도에 따라 인증 기능을 제거하고 공개할지였다.

열려 있던 것은 둘이었다.
방문자(채용 담당자)가 로그인·스크랩·매칭까지 체험해야 하는가, 그리고 레거시 auth-service 에 핫픽스를 낼 것인가.
둘 다 실측이 전제를 뒤집은 뒤 인터뷰에서 닫혔다(§3).

## 2. 실측

### 2-1. 배포된 것 — 코드 HEAD 가 아니라 태그가 실체다

- careerhub-prod 의 auth-service 는 `v0.2.1`(태그 2026-08-12)이다.
  자체 HS256 JWT · Google OAuth 직접 처리 · AES 봉투 세대이고, Zitadel 발급 훅(8081)과 `zitadel_sub` nullable 컬럼(`sql/migrations/00003`)만 들어간 과도기다.
  auth-service 저장소 HEAD 는 `v0.2.1..HEAD` 6커밋으로 자체 인증 경로를 철거했으나(#61·#56·#57·#58) 배포되지 않았다.
- api-composer `v0.4.0` 은 `jwt-secretkey` Secret 을 auth-service 와 `envFrom` 으로 공유하고(`careerhub/apicomposer/vars/vars.go`), HS256 로컬 검증만 한다.
  `jwtresolver.go:59` 에 `CreateToken` 복사본이 살아 있다.
- frontend 는 careerhub-front `v0.0.3` 이다.
  access·refresh 토큰, username, authorities, grant_type 다섯을 **비-HttpOnly 쿠키**에 쓴다(`src/httputils.js`).
- Zitadel v4.15.3 이 `id.careerhub.jyo-liar.com` 에 떠 있으나 레거시 스택은 호출하지 않는다.
  컷오버 #79 는 Draft 이고, 그 선행인 careerhub-web 배포 정의(#78)는 0건이다.

### 2-2. 지금은 인터넷에서 닿지 않는다

- `careerhub.jyo-liar.com` 과 `id.careerhub.jyo-liar.com` 은 퍼블릭 리졸버(1.1.1.1)에서도 사설 VIP `10.18.100.3` 으로 풀린다(2026-10-26 실측).
  #66 이 "public 인터넷에서 도달 가능"이라 적은 것은 VPN 안에서의 측정으로 보인다.
- 공개 경로는 `careerhub-httproute` 하나다.
  `/` → frontend, `/api` → api-composer, `/auth` → auth-service:80 (`jyoliar-k8s/gitops/base/services/careerhub/apps/gateway/httproute.yaml:37`).
- careerhub-prod 에 NetworkPolicy 가 없고, 게이트웨이 정책은 ObservabilityPolicy 하나뿐이라 레이트리밋이 없다.
- mailer gRPC(50051)는 auth-service Service 에 포함되지 않는다(Service 포트는 80·8081).
  발급 훅 8081 은 Service 에 있으나 HTTPRoute 가 라우팅하지 않는다.
  둘 다 클러스터 안에서만 닿는다.
- 외부 노출용 `cloudflared`(ns `cloudflare-system`)가 떠 있고 토큰 관리형이라 터널 ingress 설정은 클러스터에서 읽을 수 없다.
  external-dns 가 `--source=gateway-httproute --policy=sync` 로 HTTPRoute 호스트명의 A 레코드를 관리 중이다.

### 2-3. 보관 중인 개인정보의 범위

- auth DB `"user"` 테이블: `name` · `email` · `authorized_id`(Google sub) · 가입일 · 상태 (`sql/migrations/00001_init_schema.sql`).
  부속으로 동의 이력(`user_agreement`)과 권한(`user_authority`).
- userinfo Mongo: `matchJob`(희망 직군·기술·연차 조건, 메일 수신 동의) · `scrapJob`(북마크한 공고와 태그).
  구직 성향 데이터이고 식별자는 `userId` 뿐이다.
- 결제·주소·전화번호·비밀번호는 어디에도 없다.
- 가입자는 #43 기준 1명이다.

### 2-4. 결함이 개인정보에 닿는 경로 — 전부 조건부다

v0.2.1 코드에서 **인증 없이 개인정보를 돌려주는 엔드포인트는 없다.**
이메일·이름·Google sub 를 돌려주는 곳은 `/auth/admin/user` 하나이고(`admin_controller.go:34`), `AUTHORITY_ADMIN` 클레임을 가진 유효 서명 토큰을 요구한다(`restapi_http.go:68`).
서명키는 ESO 생성기의 16자 영숫자(`apps/secrets/jwt-secretkey.yaml`)라 원격 무차별 대입은 현실적이지 않다.

개인정보에 닿는 길은 셋이고 각각 전제가 있다.

| 경로 | 전제 | 닿는 것 |
|---|---|---|
| ① 서명키 유출 → 관리자 토큰 위조 | auth-service 또는 api-composer 컨테이너·Secret 접근 | 전 가입자의 이메일·이름·sub |
| ② 프론트 XSS → 비-HttpOnly 쿠키의 refresh 토큰 탈취(24시간 · 폐기 불가) | 프론트에 XSS 진입점. v0.0.3 에 `{@html}`·`innerHTML` 은 0건 | 피해자 1명의 스크랩·매칭. 관리자면 전 가입자 |
| ③ OAuth state 세션 서명키가 소스에 `"secret"`(`auth_controller.go:48`) → state 위조 → 로그인 CSRF | 피해자가 공격자가 만든 링크를 클릭 | 피해자가 이후 저장하는 스크랩이 공격자 계정에 쌓임 |

③ 만이 서명키 없이 원격에서 성립하는 공격이다.
봉투 `authToken` 의 `postMessage(..., "*")`(`after_auth.html:4`)와 프론트의 origin 미검사(`src/view/login/index.svelte:55`)는 ③ 과 결합해 봉투 자체를 다른 사이트로 흘릴 수 있고, 봉투에 만료가 없어 한 번 새면 영구 재사용된다.

인터넷 노출면이 **아닌** 결함: 토큰 원문 로깅(`jwtresolver.go:113,115` · #48)은 Loki 가 내부망이고, mailer `GetUserEmails` 무인증은 포트가 Service 에 없다.

**판정.** 결함의 본체는 인증 무결성(위조·탈취·폐기 불가)이고 개인정보 직접 노출이 아니다.
다만 **가입을 열어둔 채 공개하면** 제3자의 이메일·이름을 이 인증 뒤에 두는 것이 되어 성격이 바뀐다.

### 2-5. "로그인 체험" 의 전제를 뒤집는 사실 셋

- **매칭은 가입만으로 체험할 수 없다.**
  매칭 연산은 `AUTHORITY_MATCH_JOB` 을 요구하고(api-composer `controller/strict.go:113`), 가입 시 기본 권한이 없다.
  권한은 관리자가 만든 티켓 코드를 마이페이지에 입력해야 생긴다(`user_service.go` `AddUserAuthorities` · `ticket_service.go` `UseTicket`).
- **레거시 가입은 컷오버를 막는다.**
  `SignUp` 은 `zitadel_sub` 를 NULL 로 두고 행을 만든다(`user_service.go` `InsertUser`).
  HEAD 의 `sql/migrations/00005` 는 NULL 행이 하나라도 있으면 실패하도록 짜여 있다.
  백필 #55 는 이미 한 번 실행된 one-way door 다.
- **기존 데이터는 이미 레거시에서 보이지 않는다.**
  #79 에 따르면 scrapJob 12건이 Zitadel sub 로 치환돼, 레거시 composer 는 userinfo 에서 빈 결과를 받는다.
  로그인해도 보여줄 스크랩이 없다.

### 2-6. 프론트가 인증 없이 어디까지 동작하나

- 채용공고 목록·상세·카테고리·스킬·회사·회사리뷰는 `security: [{}, bearerAuth]` 라 비로그인 접근을 허용한다(api-composer `spec/api-composer/openapi.yaml`).
- `withAccessToken` 은 쿠키가 있을 때만 `Authorization` 을 붙이고, 401 이면 `/login` 으로 민다(`src/httputils.js`).
  쿠키가 없는 방문자는 `/auth` 를 한 번도 부르지 않는다.
- `/login` 화면만 `getAuthCodeUrls()` 로 `/auth/auth-code-urls` 를 즉시 부른다(`src/view/login/index.svelte:20`).
  헤더의 진입 링크는 `src/components/Header.svelte:77` 하나다.
- `BACKEND_URL`·`AUTH_URL` 은 빌드 시 치환되는 플레이스홀더이고(`src/const.js`), 컨테이너 기동 시 빌드한다(`Dockerfile`).

## 3. 인터뷰에서 닫힌 축

### 3-1. 인증 기능의 처분

**선택: 공개 기간 동안 인증 기능(로그인·가입)을 제공하지 않는다.** auth-service 코드를 건드리는 것 자체가 구직 준비의 걸림돌이고, 가입을 열면 §2-5 의 비용(컷오버 차단 · 가입자 정리)이 생기며, 열어도 보여줄 것(매칭 · 기존 스크랩)이 없다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 로그인·스크랩·매칭 체험 + 가입 개방 — 처음 고른 안. 매칭은 티켓 없이 안 되고, 가입자마다 컷오버 전 삭제·백필 작업이 생기며, 핫픽스 ①~③(§2-4)이 사실상 필수가 된다
- 로그인은 되되 가입만 게이트웨이에서 차단(기존 1명만) — 로그인 CSRF(③)는 그대로 원격에서 성립하고, 그 1명의 스크랩은 이미 비어 있어 데모 가치가 없다
- v0.2.1 에서 핫픽스 브랜치 — 후보는 ① state 세션키 env 주입+쿠키 속성 ② postMessage origin 고정(프론트 동반) ③ 봉투 만료 검사 ④ 토큰 로깅 제거 ⑤ 500→401 ⑥ PKCE·`WithValidMethods`·`html/template`. main 이 이미 그 코드를 지워 별도 릴리스 라인이 생긴다
- 컷오버 #79 를 앞당긴다 — careerhub-web 배포 정의가 0건(#78)이고, 레거시 front 는 철거된 `/auth/sign-in` 을 부르므로 신 auth-service 와 공존할 수 없다(#79)

</details>

### 3-2. 프론트의 모양

**선택: `/login` 화면을 "리뉴얼 중 — 로그인·가입 일시 중단" 메시지로 바꾼다.** 헤더 링크와 `/my/*`·`/admin/*` 라우트는 두어 401→`/login` 흐름이 자연히 메시지에 닿는다. 변경이 한 파일에 가깝고 리뉴얼 중이라는 신호가 남는다. 새 태그 1회가 필요하다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 로그인 링크·라우트 전부 제거 — 신호가 없고 변경 파일이 는다
- 링크 숨기고 홈 배너 — 라우트가 남아 직접 URL 로 들어오면 기존 화면이 뜬다

</details>

### 3-3. 게이트웨이

**선택: `careerhub-httproute` 에서 `/auth` 룰을 제거한다.** 프론트가 어떻든 인터넷에서 auth-service 에 닿지 않게 만든다 — 숨기는 게 아니라 할 수 없게 하는 쪽(CLAUDE.md §8). 매니페스트 한 룰이고 Deployment 는 그대로 두어 컷오버 때 되살린다. (인터뷰, 2026-10-26)

<details><summary>버린 안</summary>

- 룰 유지, 프론트만 수정 — `/auth/*` 전체가 인터넷에 열린 채 남는다. VPN 안 사용자의 직접 로그인은 가능하지만 그 가치가 없다(§2-5)
- 룰 제거 + auth-service Deployment 0 — 발급 훅 8081 이 죽어 Zitadel 실험이 막힌다

</details>

### 3-4. 노출 경로와 기간 — 전제

**선택: Cloudflare Tunnel 로 3~6개월.** 사람의 제약이다. 터널 앞단(WAF·레이트리밋)과 external-dns 충돌(§2-2)은 이 문서가 다루지 않는다(3-5). (인터뷰, 2026-10-26)

### 3-5. 범위

**선택: 이 문서는 인증 기능 처분까지다.** 노출 역학(터널 ingress · external-dns A 레코드 sync 와의 충돌 · `id.careerhub` 비공개 유지 · 레이트리밋)과 크롤링 콘텐츠(Wanted·Jumpit 공고 · Blind 리뷰)의 공개 위험은 같은 goal 의 다음 관점이다. (인터뷰, 2026-10-26)

## 4. 열린 축 — 논의

없음.
사실 문제(결함 → 개인정보)는 코드 실측으로 닫혔고(§2-4), 고른 방향(3-1·3-3)이 노출면 자체를 없애 옵션 비교가 남지 않는다.

## 5. 반대편 — 이 설계가 틀리는 조건

- 채용 담당자가 로그인 흐름 자체를 보고 싶어 한다면 포트폴리오에서 인증 데모가 빠진다.
  이 경우 답은 레거시 복구가 아니라 #79 다.
- 컷오버가 6개월을 넘기면 "임시"가 상시가 된다.
  `/auth` 룰 제거와 프론트 태그는 git 에 있어 되돌리기는 한 시간이지만, 되돌릴 이유가 생기지 않는 쪽이 문제다.
- api-composer 는 여전히 `SECRET_KEY` 로 HS256 을 검증한다.
  키가 새면 위조 토큰으로 `/api/my/*` 에 닿지만, 백필 뒤라 숫자 userId 로는 빈 결과다.
- 터널 ingress 가 게이트웨이를 거치지 않고 Service 로 직접 가면 HTTPRoute 의 제거가 무의미하다.
  터널은 `careerhub-nginx-gateway` 로만 들어와야 한다 — 다음 관점의 전제다.
- VPN 안 브라우저에 남은 레거시 쿠키는 `/api` 에 토큰을 계속 붙인다.
  만료 뒤 `/auth/refresh` 가 404 가 되어 `/login` 메시지로 떨어지고, 거기서 끝난다.

## 6. 버린 것

- **"심각도를 재서 인증을 남길지 정한다"는 틀 자체.**
  심각도는 가입 개방 여부의 함수였다 — 닫으면 가입자 1명분의 인증 무결성 문제, 열면 제3자 개인정보 문제.
  그리고 열어도 보여줄 기능이 없다는 사실(§2-5)이 드러나자 인증을 남길 이유가 사라졌다.
  틀이 "심각도 판정"에서 "노출면 제거"로 바뀌었다.
- **레거시를 고쳐서 공개한다는 길 전부.** ADR-0028 Consequences 가 "전환 기간이 길어지면 즉효 결함은 별도로 먼저 닫는다"고 했으나, 그 문장은 결함이 노출면에 있을 때의 것이다.
  노출면을 없애면 닫을 결함이 밖에 없다.
  #48(토큰 로깅)은 내부망 문제로 남고 이 논의와 무관하게 열려 있다.

## 7. 임계선 — ADR감인가

아니다.
`/auth` 룰 제거는 매니페스트 revert 로, 프론트는 이전 태그로 한 시간 안에 되돌아간다.
영향 범위는 공개 기간의 방문자뿐이고, 결정(ADR-0028 체인)은 바뀌지 않는다.
티켓·코드로 간다.

## 8. 다음

- 리프 티켓 둘(둘 다 부모 없음 — 근거 ADR 이 없고 Epic 이 아니다).
  careerhub-front `/login` 메시지 화면 + 태그(target `jyoliar-careerhub/careerhub-front`).
  jyoliar-k8s `careerhub-httproute` `/auth` 룰 제거 + frontend 이미지 태그 인상(target `jae2274/jyoliar-k8s`, 앞 티켓 선행).
- 같은 goal 의 다음 관점: 노출 역학(Cloudflare Tunnel ↔ external-dns · `id.careerhub` 비공개 · 레이트리밋)과 크롤링 콘텐츠 공개 위험.
