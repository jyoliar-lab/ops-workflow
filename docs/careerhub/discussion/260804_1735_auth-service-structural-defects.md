---
type: discussion
topic: careerhub
subjects: [auth-service, api-composer, jwt, google-oauth, postgresql, careerhub-front]
status: active
---

# auth-service의 구조적 결함 — 공개 전환 전에 무엇을 정하고 무엇을 지금 닫나

## 0. 이 논의가 열린 경위

티켓 #7(비-OAuth 로그인 경로)을 진행하려다 열렸다.
"OAuth 인증은 자동화 방안이 아예 없나"를 조사하던 중 **로그인이 어떻게 구현되어 있는지**를 읽게 되었고,
거기서 나온 사실들이 #7의 범위를 넘었다.

착수 동기는 *"prod가 공공 endpoint를 갖기 전인 지금 고쳐야 한다"* 였고, 아래 §1이 그 전제를 확인한다.

---

## 1. 지금 어디까지 열려 있는가 — VPN 안뿐이다

```
$ dig +short @1.1.1.1 careerhub.jyo-liar.com
10.18.100.3          ← RFC1918 사설 주소
```

퍼블릭 리졸버로 물어도 **사설 대역**이 돌아온다. 게이트웨이 LoadBalancer가 kube-vip이고
(`jyoliar-k8s/.../gateway/nginx-proxy.yaml` — `service.type: LoadBalancer`, `implementation: kube-vip`),
그 VIP가 홈랩 내부 주소다. **인터넷에서 라우팅되지 않는다 — 접근자는 VPN·LAN 안의 사람뿐이다.**

노출 경로 자체는 매니페스트로 전부 이어져 있다:

- `.../gateway/httproute.yaml` — hostname `careerhub.jyo-liar.com`, `/auth` → Service `auth-service:80` (`/api` → api-composer, `/` → frontend)
- `.../base/controllers/external-dns/application.yaml` — `sources: [gateway-httproute]` · `provider: cloudflare` · `policy: sync`
- `.../gateway/wildcard-certificate.yaml` — cert-manager, `*.jyo-liar.com`

즉 **배선은 공개 전환 준비가 끝난 상태이고, 막고 있는 것은 VIP가 사설 주소라는 사실 하나다.**
공개로 바꾸는 데 필요한 것은 매니페스트 한 줄 수준이므로, 이 논의가 다루는 결함들은 **그 한 줄이 바뀌는 날 전부 인터넷 앞에 선다.**

부수 관찰 하나 — `policy: sync`가 이 이름을 **퍼블릭 Cloudflare 레코드로 게시**하므로,
`careerhub.jyo-liar.com` → `10.18.100.3`이라는 내부 토폴로지가 외부에서 조회된다. 접근은 안 되지만 이름과 내부 주소는 공개다.

한편 배포 자체는 오래 살아 있다:

```
$ kubectl get deploy -n careerhub-prod
auth-service   2/2   AGE 127d
api-composer   2/2   AGE 134d
```

**따라서 시간이 비용을 밀어 올리는 축은 하나뿐이다** — 스키마와 유저 데이터는 4개월째 실재하므로,
정체성 모델 변경(축 F)은 공개 여부와 무관하게 **지금이 가장 싸다.** 나머지 축은 공개 전환일이 마감이다.

**중요한 미지수:** 실제 가입 유저가 몇 명인가. 축 F 비용이 전적으로 여기 걸린다 — §8 열린 질문 ①.

---

## 2. 결함 — 축별로

원인이 서로 다르므로 축을 섞지 않는다. 각 축이 독립적으로 뒤집힐 수 있다.

### 축 A. 신뢰 경계가 없다 — 대칭키가 두 서비스 사이를 지웠다

**가장 무거운 축이다.** 아래 셋이 곱해진다.

1. **키가 공유된다.** `jwt-secretkey` Secret을 두 Deployment가 `envFrom`으로 받는다 —
   `jyoliar-k8s/.../auth-service/deployment.yaml:84-86`, `.../api-composer/deployment.yaml:56-57`.
   (userinfo·posting·review gRPC의 Deployment에는 주입되지 않는다.)
2. **알고리즘이 대칭키(HS256)다.** `auth_service/restapi/jwtresolver/jwtresolver.go:65,75` —
   검증 키와 서명 키가 같은 바이트열이다. 즉 **검증할 수 있으면 발급할 수 있다.**
3. **api-composer에 발급 코드가 살아 있다.** resolver가 goutils 공통 모듈이 아니라 **복붙 사본**이고
   (`careerhub-api-composer/careerhub/apicomposer/jwtresolver/jwtresolver.go`),
   그 안에 `CreateToken(userId, authorities, createdAt)`이 그대로 있다(`:59-68`).

**결과:** api-composer 컨테이너를 쥔 쪽은 `authorities: ["AUTHORITY_ADMIN"]`을 담은 유효 토큰을 스스로 만들 수 있고,
그 토큰은 `/auth/admin/*`(권한 부여·티켓 발급·전 유저 조회)를 통과한다. 역방향도 같다 —
방어는 애플리케이션 미들웨어 하나(`restapi_http.go:67`)뿐이고, 그 미들웨어가 신뢰하는 키를 상대 서비스가 갖고 있다.
**두 서비스 사이에 신뢰 경계가 존재하지 않는다.**

부수 사실:
- 같은 `SECRET_KEY`가 **AES 키로도 재사용**된다 — `restapi_http.go:43` `NewJsonAesCryptor(utils.CreateHash(envVars.SecretKey))`. 한 비밀이 두 용도를 겸한다(축 E와 결합).
- 양쪽 `ParseWithClaims` 어디에도 `jwt.WithValidMethods([]string{"HS256"})`가 없다 — 알고리즘 화이트리스트 미지정.
- 복붙 사본은 **이미 갈라졌다**: auth-service의 `CustomClaims`에는 `AuthorizedBy`/`AuthorizedID`가 있고 composer판에는 없다.
- 키의 출처는 ESO의 `Password` 생성기(`.../apps/secrets/jwt-secretkey.yaml`) — `length: 16`, `refreshPolicy: CreatedOnce`. **자동 로테이션 없음**, 백업 없음(Secret이 사라지면 전 세션 무효).

**하위 gRPC 서비스는 순수 신뢰 내부망이다.** userinfo·posting·review 세 저장소에 `jwt|Authorization|bearer` 검색 결과 0건이고,
gRPC 서버는 OTel 인터셉터만 건다(`careerhub-userinfo-service/.../utils/mwutils.go:19-20`).
사용자 식별은 헤더가 아니라 **요청 메시지의 `userId` 필드**로 내려가며(`api-composer/.../controller/matchJob_strict.go:30-32`, `matchJob.proto:16`),
수신 측은 그것을 무검증 신뢰한다. 이 자체는 흔한 설계지만, NetworkPolicy 부재와 곱해진다.

### 축 B. 토큰이 자기가 무엇인지 말하지 않는다

claims 전문 — `jwtresolver/claims.go:8-15`:

```go
type CustomClaims struct {
	UserId       string `validate:"nonzero"`
	AuthorizedBy domain.AuthorizedBy
	AuthorizedID string
	Authorities  []string
	jwt.RegisteredClaims
}
```

`RegisteredClaims`에서 실제로 채우는 것은 **`ExpiresAt` 하나뿐**이다(`jwtresolver.go:65-90`).
**`iss`·`aud`·`iat`·`jti`·`nbf`·`sub` 전부 없다.** 그리고 **access/refresh를 구분하는 표시가 없다.**

`ParseToken`(`jwtresolver.go:103-129`)이 검사하는 것은 ⓐ HS256 서명 ⓑ `exp` ⓒ `UserId != ""` 세 가지뿐이다.
따라서 **양방향 혼용이 통과한다**:

- **access token을 refresh 자리에** — `RefreshJwt`(`auth_controller.go:254-287`)는 `ParseToken(req.RefreshToken)` 하나만 부르고 `UserId`/`AuthorizedBy`/`AuthorizedID`만 쓴다. access token은 이 셋을 다 갖고 있어 그대로 통과해 새 access token이 나온다.
- **refresh token을 Authorization 헤더에** — 같은 `ParseToken`을 쓰는 `SetClaimsMW`(`middleware/middleware.go:17-41`)가 `UserId`만 요구하므로, **refresh token으로 24시간 동안 `CheckHasClaims` 보호 라우트에 접근된다**(`/auth/authority`, `/auth/withdrawal`, `/auth/ticket/{uuid}`). `Authorities`가 nil이라 admin 라우트만 막힌다.

Bearer 파싱도 전용 파서가 없다 — `jwtresolver.go:105`의 `strings.Replace(tokenString, "Bearer ", "", 1)` 한 줄이 전부이고,
접두사 존재를 요구하지 않으며 문자열 **어느 위치**의 첫 `"Bearer "`든 제거한다.

### 축 C. 발급한 것을 되돌릴 수 없다

- **refresh token rotation 없음.** `RefreshJwt` 응답은 `{accessToken, authorities}`뿐(`dto/dto.go:99-102`) — 새 refresh token을 주지 않는다. 최초 refresh token이 24시간 내내 유일하고 불변인 자격증명이다.
- **폐기 목록·저장 없음.** refresh token을 DB에 쓰거나 읽거나 무효화하는 코드가 없다(쿼리·마이그레이션 전수 확인).
- **로그아웃 엔드포인트 없음.** 등록 라우트 전량에 존재하지 않는다.
- **`RefreshJwt`가 `status`를 보지 않는다.** `FindUserByAuthorized`(`sql/queries/user.sql:6-8`)에 `status` 조건이 없고, `toDomainUser`(`user_service.go:379-388`)는 `Status`를 도메인으로 옮기지도 않는다.
  → **`SUSPENDED`는 무력하다.** 게다가 `SUSPENDED`로 **쓰는 코드 자체가 없다** — 정지 기능이 미구현이다.
  → 탈퇴가 refresh를 막는 것은 status 검사 덕이 아니라 `authorized_by`가 `'DELETED'`로 덮여 조회가 빗나가는 **부작용**이다(축 F).
- **이미 발급된 access token은 어떤 경우에도 만료(최대 10분)까지 유효하다** — 검증 경로가 DB를 보지 않는다.
- **권한이 토큰에 박힌다.** 검증 측은 클레임만 읽는다(`middleware.go:56-73`). 권한 회수는 최대 10분 지연된다.
  (`SetAccessTokenDuration`은 public이고 `duration < 0`만 거부한다 — **0을 허용**한다. 프로덕션 호출부는 없다.)

### 축 D. OAuth 왕복에 방어가 없다

**① 세션 서명 키가 소스에 박혀 있다** — `auth_controller.go:48`:

```go
store: sessions.NewCookieStore([]byte("secret")),
```

`envVars.SecretKey`도, 어떤 env도 참조하지 않는다. `NewAuthController` 시그니처에 세션 키 파라미터 자체가 없다.
→ **누구나 임의 `state`를 담은 유효 서명 세션 쿠키를 만들 수 있다. state의 CSRF 방어가 무효다.**
keyPair가 1개라 blockKey가 nil이므로 쿠키 값은 서명만 되고 **암호화되지 않는다**.

**② 서버 측 state 수명이 5분이 아니라 30일이다.**
`session.Options.MaxAge = 300`(`auth_controller.go:146-149`)은 브라우저에 내려주는 `Max-Age` **속성**일 뿐이다.
서버 측 유효기간은 codec의 maxAge인데, `NewCookieStore`가 기본값 `86400*30`으로 설정한다.

**③ 세션 쿠키에 `Secure`·`HttpOnly`·`SameSite`가 전부 미설정이다.** 리포 전체 grep 0건.

**④ PKCE가 없다.** `google.go:41-43` `AuthCodeURL(state)` — `AuthCodeOption`이 하나도 붙지 않고, 교환도 `Exchange(ctx, code)` opts 없음.
`golang.org/x/oauth2 v0.35.0`은 `S256ChallengeOption()`을 제공하는 버전이지만 미사용.

**⑤ `openid` scope가 없다** — `google.go:15-19`는 `userinfo.email`·`userinfo.profile`뿐.
따라서 **id_token을 아예 받지 않고**, 대신 access token으로 userinfo REST를 GET한다(`google.go:63-83`). nonce도 없다.
(id_token 서명 검증이 "빠진" 게 아니라 **애초에 id_token이 없다** — 표준 OIDC mock IdP를 그대로 끼울 수 없는 이유이기도 하다.)

**⑥ `postMessage(..., "*")`.** `after_auth.html` 전문:

```html
<script>
    const authToken = "{{ .AuthToken }}";
    window.opener.postMessage({authToken}, "*");
    window.close();
</script>
```

수신 측(`careerhub-front/src/view/login/index.svelte:54-58`)도 `e.origin`을 검사하지 않는다.
게다가 렌더링이 `html/template`이 아니라 **`text/template`**이다(`auth_controller.go:10`) — 현재 값이 base64라 탈출이 안 될 뿐, 안전장치가 없다.
CSP·X-Frame-Options·Referrer-Policy 헤더 설정도 없다.

**⑦ `/auth/callback/google`에 메서드 제약이 없다**(`auth_controller.go:57` — `.Methods(...)` 미지정).

**⑧ CORS의 `AllowCredentials()`가 조건 없이 켜져 있다**(`restapi_http.go:74`). origin은 단일 env값이고 값 검증이 없다.

### 축 E. `authToken` 봉투 = 만료 없는 bearer 자격증명

봉투 평문은 `{UserInfo, oauth2.Token}`(`ooauth/ooauth.go:18-21`)이고, AES-GCM으로 봉해 브라우저에 내려간다.

**봉투 안에 만료·발급시각·jti·일회성 표시가 없다.** `oauth2.Token.Expiry`가 안에 있지만 **복호 후 어디서도 읽지 않는다.**
소비처 3곳(`SignIn` `:166-171`, `Agree` `:191-196`, `SignUp` `:223-228`)이 전부 무상태 복호 후 즉시 신뢰하고,
사용 기록 DB도 캐시도 카운터도 없다.

> **즉 한 번 발급된 `authToken`은 `SECRET_KEY`가 바뀌지 않는 한 영구히 재사용 가능하다.**

그리고 `UserInfo`의 `validate:"nonzero"` 태그(`ooauth.go:12-15`)는 **한 번도 실행되지 않는다** —
`validator.Validate` 호출부는 전부 `jwtresolver` 내부(JWT claims 대상)이고, `UserInfo`가 전달되는 경로가 없다.
`SignIn`은 복호 결과를 곧장 DB 쿼리에 넣는다. body 크기 제한(`http.MaxBytesReader`)도 없다.

**축 A와의 결합:** AES 키는 `sha256(SECRET_KEY)`이고 `SECRET_KEY`는 api-composer도 갖고 있다.
→ **api-composer는 임의 `sub`에 대한 유효 `authToken`도 만들 수 있다.**
(이 사실이 #7의 O3 — "있는 문의 열쇠를 쓴다" — 의 근거이자 동시에 그것을 위험하게 만드는 이유다. §6.)

### 축 F. 정체성 모델이 다중 IdP를 못 받는다

`sql/migrations/00001_init_schema.sql:3, 32-45`:

```sql
CREATE TYPE user_authorized_by AS ENUM ('GOOGLE', 'DELETED');

CREATE TABLE "user" (
  user_id serial, name varchar(45), authorized_by user_authorized_by,
  authorized_id varchar(45), email varchar(255), ...,
  UNIQUE (email),                          -- ①
  UNIQUE (authorized_by, authorized_id)    -- ②
);
```

**② 는 옳다.** (provider, subject) 복합 유니크는 외부 7개 구현이 전부 쓰는 표준형이다(§3).
`SignIn(ctx, userinfo)`가 `*ooauth.UserInfo{AuthorizedBy, AuthorizedID, Email, Username}`를 받는 것,
AES 봉투가 그 구조체를 나르는 것도 **provider-agnostic seam**이다 — 다중 IdP를 향한 설계 의도가 코드에 이미 있다.

문제는 그 위의 넷이다.

**① `UNIQUE(email)`이 다중 IdP를 물리적으로 막는다.**
같은 사람이 Google에 이어 다른 IdP로 들어오면 ②는 통과하지만 ①에서 INSERT가 터진다.
사용자에게는 그냥 "가입 실패"로 보인다. 링크도 분리도 아닌 **에러**다.

**③ 테이블이 1:1이다.** `authorized_by`/`authorized_id`가 `"user"` 행 안에 있다 — 유저 하나에 IdP 하나.
외부 표준형은 `user` 1:N `identities` 별도 테이블이다(§3).

**④ enum이 provider 축과 lifecycle 축을 섞는다.** `'DELETED'`는 IdP가 아니라 탈퇴 상태인데,
`status` 컬럼에 이미 `DELETED`가 따로 있다. IdP를 늘릴 때마다 `ALTER TYPE ADD VALUE`를 치게 되고 축이 더 흐려진다.

**⑤ 탈퇴가 정체성을 파괴한다.** `Withdrawal`(`user_service.go:346-377`)이
`name`·`authorized_id`·`email` **세 컬럼 모두**를 `"DELETED_" + user_id`로 덮는다.
→ 같은 Google 계정으로 재가입하면 이전 계정과의 연결(권한·동의·티켓 사용 이력의 소유자 매핑)이 **복원되지 않는 새 유저**가 된다.
→ 형식상 이메일이 아닌 값이 `email` 컬럼을 점유하고, 이를 막는 CHECK 제약은 없다.
→ 유니크 충돌 회피 수단이 전용 컬럼이나 부분 인덱스가 아니라 **값 인코딩**이다.

**⑥ 죽은 `auth_server` 테이블**(`00001_init_schema.sql:6-11`) — sqlc가 struct는 만들었으나 참조하는 쿼리가 0건이다.
IdP를 행으로 정규화하려던 흔적이 enum으로 대체되고 껍데기만 남았다. 다중 IdP를 다시 여는 지금이 둘 중 하나를 고를 자리다.

**⑦ 컬럼 폭·타입 캐스팅.** `authorized_id varchar(45)`, `name varchar(45)`에 길이 검증·잘림 처리가 없다 —
초과 시 Postgres `22001`이 그대로 올라와 **500**이 된다(`22001`을 다루는 코드 없음).
`db.UserAuthorizedBy(userinfo.AuthorizedBy)`(`user_service.go:33`)는 **무검증 문자열 캐스팅**이라, enum에 없는 값은 DB에 닿아서야 실패한다.

**부수적으로 드러난 것들** (같은 축은 아니지만 같은 곳에 있다):

- **가입 시 기본 권한이 없다.** `InsertUserAuthority` 진입점은 관리자 `AddUserAuthorities`와 `UseTicket` 둘뿐. 갓 가입한 유저의 `authorities`는 빈 배열이다.
- **`AUTHORITY_ADMIN`을 부여하는 애플리케이션 경로가 없다.** `AddUserAuthorities`/`RemoveAuthority`가 admin 조작을 차단하고, 시드 마이그레이션에 `authority` 행이 하나도 없다 → **DB 직접 조작으로만 부트스트랩된다.**
- **`SignUp`이 필수 동의를 강제하지 않는다.** `user_service.go:27-58`에 `is_required` 검사가 없어, `agreements: []`로도 유저 행이 생긴다. 그 유저는 이후 `SignIn`마다 `necessary_agreements`로 분기한다.
- **동의에 시각·버전이 없다.** `user_agreement`에 `agreed_at`도 버전 참조도 없다 — **언제 어떤 문안에 동의했는지가 DB에 남지 않는다.** 약관을 고쳐도 같은 `agreement_id`면 기존 동의가 새 문안 동의로 간주된다.
- **필수 약관 추가는 전원 소프트 락아웃**이다. 조회 기준이 `is_agree = true`라 명시적 거부와 미동의가 구별되지 않는다.
- **`sql/init_schema.sql`(MySQL 문법 96줄)이 죽은 채 남아 있다.** 임베드 대상이 아니고 참조하는 코드가 0건이다. 살아있는 것은 `sql/migrations/`(goose+Postgres)다.
- 여러 쿼리로 조립되는 읽기들이 트랜잭션 밖에서 실행된다(`FindNecessaryAgreements`, `GetAllUsers` 등) — 스냅샷 일관성이 없다.

### 축 G. 사고가 나도 안 보인다

- **토큰 원문이 로그에 적재된다.** `jwtresolver.go:113,115` — `fmt.Errorf("%s %s", err.Error(), tokenString)`.
  이 에러가 `middleware.go:24`·`ctrl_utils.go:14`의 `llog.LogErr`로 흘러 **Authorization 헤더 값과 refresh token 전문**이 Loki에 남는다.
  서명 불일치도 이 분기라, 키 롤링 직후에는 **유효한 토큰이 그대로 기록된다.**
- **위조 시도에 500을 준다.** auth-service는 파싱 에러·서명 불일치에 500(`middleware.go:25`), api-composer는 같은 상황에 401(`middleware.go:32`).
  두 서비스의 실패 시맨틱이 불일치하고, 위조 시도가 5xx 에러율 지표를 오염시킨다.
- **만료 토큰은 무로그**다(`isValid=false`로 삼켜짐).
- **인증 관련 메트릭·알람이 없다.** 로그인 실패율·토큰 위조 시도에 대한 룰을 찾지 못했다.
- `state` 불일치도 500이고, 그때 state 값 두 개가 로그에 남는다(`auth_controller.go:92`).
- `GetClaimsOrPatal`은 claims 부재 시 `panic`인데(`ctrl_utils.go:22-29`), **panic recover 미들웨어가 등록되어 있지 않다.**
- **dev 환경이 없다.** `.../dev/careerhub-dev-appset.yaml:14-15`에서 `careerhub-dev-apps`가 **주석 처리**되어 있고 `dev/apps/` 디렉터리 자체가 없다. dev에는 MongoDB뿐이다 → **실질 단일 환경이고, 어떤 변경도 prod에서 처음 돈다.**

---

## 3. 외부 기준선 — 다중 IdP는 어떻게 저장하는가

7개 독립 구현이 이름만 다르고 구조가 같다.

| 구현 | provider 축 | subject 축 | 제약 |
|---|---|---|---|
| Supabase `auth.identities` | `provider` | `provider_id` | UNIQUE (provider_id, provider) |
| Keycloak `FEDERATED_IDENTITY` | `IDENTITY_PROVIDER` | `FEDERATED_USER_ID` | PK (USER_ID, IDENTITY_PROVIDER) |
| django-allauth `SocialAccount` | `provider` | `uid` | unique_together |
| Auth.js `Account` | `provider` | `providerAccountId` | @@unique / 복합 PK |
| Ory Kratos | `provider` | `subject` | `"google:j8kf7a3"` 단일 문자열 |
| GitLab `identities` | `provider` | `extern_uid` | uniqueness scope |
| Gitea `external_login_user` | `LoginSourceID` | `ExternalID` | 복합 PK |

**핵심 셋:**

1. **`(provider, subject)` 복합 유니크가 표준이고, 대개 `(provider, user_id)` 유니크가 하나 더 붙는다**(한 유저는 IdP당 링크 1개 — Keycloak은 아예 그걸 PK로 잡았다).
2. **email은 조인 키가 아니다.**
   OIDC Core는 `sub`+`iss`만이 안정 식별자이며 *"other Claims such as email... MUST NOT be used as unique identifiers for the End-User"* 라고 못박는다.
   Google은 *"you **shouldn't** use the `email` field in the ID token as a unique identifier... Always use the `sub` field"*.
   미검증 email 자동 링크는 2026년에도 CVE를 낳고 있다 — **CVE-2026-53516**(Better Auth, CVSS 8.3): 공격자가 피해자 email을 미검증 상태로 선점해두면 OAuth 콜백의 auto-link가 피해자 identity를 공격자 계정에 붙인다.
   Auth0: *"You **should not automatically link accounts based on the user's emails**."*
   Supabase: *"it would also be an insecure practice to automatically link an identity to a user with an unverified email address."*
3. **세션 토큰은 자체 발급이고, IdP 토큰은 검증 후 버리는 입력이다.** `sub`에는 내부 user id(Supabase UUID) 또는 provider 접두 합성 id(Auth0 `google-oauth2|123...`)를 넣는다.
   **권한은 IdP가 아니라 자체 DB에서** 온다(Supabase는 `public.user_roles`를 두고 발급 hook에서 claim으로 주입).
   IdP access/refresh token 저장은 **"IdP API를 대신 호출할 것인가"로만 정당화된다** — Supabase는 *"Provider tokens are intentionally not stored in your project's database"* 로 의도적으로 저장하지 않는다.

**→ careerhub의 ②는 이미 표준형이다. 어긋난 것은 ①(email 유니크)·③(1:1)·④(축 혼재)다.**
그리고 축 E는 3번 기준으로 보면 **저장하지 않아도 될 IdP 토큰을 봉투에 담아 브라우저로 왕복시키는** 구조다.

---

## 4. 임계선 판정 — 무엇이 결정이고 무엇이 지금 할 일인가

CLAUDE.md §4②(되돌리기 어려움 × 영향 범위)로 가른다.

### (가) 결정을 기다리지 않는다 (전부 two-way door)

되돌리는 데 한 시간이 안 걸리고, 어떤 결정이 나든 방향이 바뀌지 않는 것들이다.
**공개 전환 전에 닫아두면 사실상 공짜이고, 전환 후에는 각각이 사고 표면이 된다.**

| # | 무엇 | 근거 |
|---|---|---|
| 1 | `sessions.NewCookieStore([]byte("secret"))` → env 주입(JWT 키와 **다른** 비밀) + `Secure`/`HttpOnly`/`SameSite` + 서버측 maxAge | `auth_controller.go:48,146-149` |
| 2 | api-composer의 `CreateToken` 삭제 | 데드코드인데 위조 능력을 준다. 축 A의 3요소 중 **가장 싼 하나** |
| 3 | 토큰 원문 로깅 제거 | `jwtresolver.go:113,115` — Loki에 유효 자격증명이 쌓인다 |
| 4 | 위조/파싱 실패 500 → 401 | `middleware.go:25`. composer와 시맨틱 통일 |
| 5 | `/auth/admin/*`를 공개 대상 HTTPRoute에서 분리 | 지금은 VPN 뒤라 급하지 않지만, **공개 전환의 전제**다. 매니페스트 변경만 |
| 6 | PKCE + `jwt.WithValidMethods` + `text/template`→`html/template` + `postMessage` origin 고정 + 콜백 `.Methods("GET")` | 각각 한 줄~몇 줄 |
| 7 | `sql/init_schema.sql`(죽은 MySQL DDL) 삭제 | 두 개의 진실 제거 |

**1번(하드코딩된 `"secret"`)과 3번(토큰 원문 로깅)은 VPN 안이어도 지금 값이 이미 쌓이고 있으므로 먼저 볼 후보다** —
전자는 지금 발급되는 모든 세션 쿠키가 그 키로 서명되고 있고, 후자는 Loki에 유효 자격증명이 계속 적재된다.

### (나) 결정이 필요하다 — one-way door 후보

| 축 | 결정 질문 | 왜 되돌리기 어려운가 |
|---|---|---|
| **A** | 서명 키 체계 | 검증자 전부가 함께 바뀐다. 발급/검증 분리 여부가 서비스 신뢰 경계의 정의다 |
| **F** | 정체성 저장 모델 | 데이터 마이그레이션. **유저가 늘수록 비싸진다** — 시간이 한 방향으로만 흐르는 유일한 축 |
| **F'** | 계정 연결 정책 | 잘못 고르면 계정 탈취. 사용자 계정이 생긴 뒤엔 되돌려도 이미 합쳐진 것이 안 갈라진다 |
| **C** | 세션 폐기 모델 | 상태 저장(폐기 목록·rotation) 여부가 auth-service의 상태성을 정의한다 |
| **E** | 프론트로 세션을 넘기는 방식 | `careerhub-front` discussion `260722_1617_token-storage-after-server-exists.md`가 여는 축과 **같은 축이다** — 거기서 이어 다뤄야 한다 |

**마감이 둘 있다.** F는 **유저 수**가 밀어 올리므로 이미 좁아지는 중이고(→ §8 ①),
나머지 축은 **공개 전환일**이 마감이다 — 그날 이후엔 결정과 이행이 운영 중 변경이 된다(→ §8 ⑧).

---

## 5. 옵션 — (나)의 축별 발산

### 축 A — 서명 키 체계

- **A0. 유지 + 데드코드 제거만.** (가)2로 위조 경로는 닫히지만 **키 공유 자체는 남는다.** api-composer가 라이브러리를 다시 붙이면 되살아난다. 이기는 조건: 두 서비스를 같은 신뢰 도메인으로 인정할 때. 지는 조건: 그 인정이 문서 어디에도 없다는 것.
- **A1. 비대칭(RS256/ES256) + JWKS 공개.** auth-service만 개인키를 갖고, 검증자는 공개키만 받는다. **"검증할 수 있으면 발급할 수 있다"가 구조적으로 깨진다** — CLAUDE.md §8의 "할 수 없게 만든다"에 정확히 해당. 비용: 키 배포·회전 경로 신설, resolver 양쪽 수정.
- **A2. 불투명 토큰 + introspection.** 폐기(축 C)가 공짜로 따라오지만 auth-service가 데이터 경로에 들어가고 SPOF가 된다.
- **A3. 공통 모듈로 resolver 통합(goutils).** 복붙 분기를 없애지만 **키 공유는 그대로**다 — A1과 직교하며, A1 없이 A3만 하면 오히려 발급 능력이 더 널리 퍼진다.

### 축 F — 정체성 저장 모델

- **F0. 유지.** 다중 IdP를 포기한다. `UNIQUE(email)`이 남으므로 두 번째 IdP는 붙일 수 없다.
- **F1. `UNIQUE(email)` 제거만.** 가장 싸다. 같은 사람이 IdP별로 별개 계정 2개가 된다(Auth.js가 이걸 `OAuthAccountNotLinked`로 막는 그 상태). 링크는 포기.
- **F2. `identities` 테이블 분리** — 외부 표준형. `user`는 내부 정체성만 갖고, `(provider, subject)`가 별도 행. `FindUserByAuthorized` 등 쿼리·도메인 타입이 함께 바뀐다. enum도 이때 축을 가른다(provider ≠ lifecycle).
- **F3. F2 + `auth_server` 테이블 되살리기** — provider를 enum이 아니라 행으로. IdP 추가가 마이그레이션이 아니라 데이터가 된다. 죽은 테이블이 원래 그 자리였다.

### 축 F' — 계정 연결

- **자동 링크(email 일치)** — §3의 CVE가 정확히 이것이다. 채택하려면 **IdP의 verified 클레임과 로컬 행의 검증 상태를 둘 다** 봐야 한다.
- **명시적 링크** — 로그인한 상태에서만 연결 허용(Auth0·Keycloak 기본값). 안전하지만 UX 공정이 는다.
- **링크 안 함** — F1과 짝. 별개 계정 2개.

### 축 C — 폐기

- **C0. 유지**(무상태). 정지·로그아웃이 원리적으로 불가능한 상태를 받아들인다.
- **C1. refresh rotation + 재사용 감지.** 상태 저장이 최소로 는다. 탈취 감지가 덤으로 온다.
- **C2. 폐기 목록/세션 테이블.** 즉시 무효화가 가능해진다. auth-service가 상태를 갖는다.
- **C0을 고르더라도 `RefreshJwt`가 `status`를 보게 하는 것은 (가)로 내려간다** — 한 줄이고 되돌리기 쉽다.

### 축을 가로지르는 옵션 — 직접 짓지 않는다

- **X. auth-service를 기성 IdP로 대체한다**(Keycloak 자체호스팅 / Auth0·Clerk 등 SaaS).
  §2의 축 A~E가 **한꺼번에** 사라진다 — 키 체계·토큰 클레임·폐기·PKCE·계정 연결이 전부 제품의 관할이 되고,
  다중 IdP는 설정이 된다(§3의 Keycloak `FEDERATED_IDENTITY`가 그 결과물이다).
  대가: `user`·`authority`·`ticket`·`agreement`가 서로 얽혀 있어(§2 축 F 부수) **인증만 떼어내는 경계가 자명하지 않다**.
  홈랩 자체호스팅이면 운영물이 하나 늘고, SaaS면 외부 의존과 비용이 생긴다.
  이 옵션은 축 A·C·F·F'를 동시에 소거하므로, **그 넷을 각각 정하기 전에 먼저 판정하는 것이 순서상 맞다.**

---

## 6. 이 논의가 #7·#8에 미치는 것

**#7(비-OAuth 로그인 경로)의 문안이 흔들린다.**
"비-OAuth 로그인 경로가 존재하는가"는 코드상 **이미 참**이다 — `SECRET_KEY`를 쥔 쪽은 `authToken`을 위조하거나 JWT를 직접 서명할 수 있다(축 A·E).
따라서 #7의 실제 미결은 *"새 문을 낼 것인가"*가 아니라 **"테스트 하네스가 프로덕션 서명키를 쥐는 것을 허용할 것인가"** 다.

그리고 §3의 조사가 더 나은 형태를 준다 — **OmniAuth `:developer` strategy**:

> *"The Developer strategy... has zero security and should **never** be used in a production setting."*
> ```ruby
> provider :developer if Rails.env.development?
> ```

설계점 둘이 정확히 우리 것과 맞는다: ⓐ 다른 provider와 **동일한 identity 계약**을 지켜 코드 경로가 갈라지지 않게 하고,
ⓑ **provider 등록 자체를 환경 조건으로 감싼다**(런타임 플래그가 아니라 등록 시점에 없앤다).

→ **`AuthorizedBy`에 값을 하나 더 얹는 것**이 되고, 다중 IdP로 갈 거라면 **어차피 하는 일**이라 테스트 전용 비용이 거의 남지 않는다.
단 **축 F의 결정이 선행이다** — enum이냐 테이블이냐, 축을 가를 것이냐에 따라 "값 하나 더"의 모양이 달라진다.

**#8(인증 토큰 접근을 단일 모듈로 격리)** 은 이 논의와 충돌하지 않는다 — 오히려 축 E가 바뀔 때 프론트 쪽 변경면을 한 곳으로 모아준다.

**dev 부재(축 G)가 세 티켓 모두의 공통 선행이다.** `260722_1618_regression-net-and-merge-gate.md` §9 미결 ①이
*"#7과 dev 증설이 실체를 가질 때 벌린다"* 로 보류해 둔 그 축이고, 여기서 이유가 하나 더 붙는다 —
**지금은 어떤 인증 변경도 prod에서 처음 돈다.**

---

## 7. 검토하고 버린 것

- **(가)와 (나)를 "인증 전면 재설계" 한 덩어리로 묶는 것** — (가)는 결정을 기다릴 이유가 없고 전부 two-way door다. 묶으면 결정이 도는 동안 값이 계속 쌓인다(하드코딩 키로 서명된 세션 쿠키, Loki에 적재되는 토큰 원문). **둘을 분리하는 것이 이 논의의 형태인 이유다.**
- **가짜 IdP(mock-oauth2-server·Keycloak)로 갈아끼워 테스트를 여는 안** — #7 조사에서 외부 1차 출처들이 수렴한 방향이지만, careerhub에서는 이득이 작다. OAuth 왕복이 **auth-service 서버 안에서 끝나** 프론트 e2e가 검증할 왕복이 거의 없고, `google.Endpoint`·userinfo URL이 하드코딩(`google.go:18,32`)이라 코드 수정이 선행이며, **`openid` scope가 없어 id_token 기반 mock IdP를 그대로 끼울 수도 없다**(축 D⑤).
- **실제 Google 로그인 UI 자동화** — 사람이 이미 포기 판정. Google이 자동화 브라우저를 정책 문서로 차단하고(*"Are being controlled through software automation rather than a human"*), 성립시키려면 여섯 겹 조건(AutomationControlled 무력화·UA 위조·slowMo·TOTP 전용 계정·프로덕션 전용·무재시도)이 동시에 필요하다.
- **resolver를 goutils로 올려 공통화하는 것만으로 축 A를 닫는 것** — 키 공유가 남으므로 닫히지 않는다(A3). A1과 함께가 아니면 발급 능력만 더 퍼진다.
- **auth-service 저장소의 기존 개선 문서들로 갈음하는 것** — `docs/2603251254_refactoring-plan.md`·`docs/2603251601_auth-workflow-proposal.md`는 **계층 유출과 API 역할 분리**를 다룬다(그리고 후자는 이미 구현됐다). 인증 설계 자체(키·토큰·정체성)는 그 문서들 밖이다.

---

## 8. 열린 질문 — 사람의 것

1. **실 가입 유저가 몇 명인가.** 축 F 마이그레이션 비용이 전적으로 여기 걸린다. 0에 가까우면 F2/F3이 지금 거의 공짜고, 유의미하면 창이 좁아지는 중이다. (확인 경로: DB 직접 조회 또는 `/auth/admin/user` — admin 자격이 필요해 이 조사에서는 하지 않았다.)
2. **다중 IdP는 언제의 일인가.** "앞으로 넓힌다"가 이번 분기인지 내년인지에 따라 F1(싸게 막기)과 F2/F3(제대로)의 선택이 갈린다.
3. **api-composer와 auth-service를 같은 신뢰 도메인으로 볼 것인가.** 예라면 A0으로 충분하고, 아니라면 A1이 유일한 구조적 답이다. **이 질문에 대한 답이 어디에도 기록되어 있지 않다는 것 자체가 결함이다.**
4. **`/auth/admin/*`를 공개 대상에 둘 것인가.** 관리 화면을 어디서 쓰는지(VPN 안에서만? 밖에서도?)가 (가)5의 형태를 정한다. VPN 안으로 영구히 묶을 수 있다면 가장 싼 답이다.
5. **정지(SUSPENDED)·즉시 로그아웃이 필요한 기능인가.** 필요 없으면 축 C는 C0으로 닫고 상태성을 안 들인다. 필요하면 C1/C2가 ADR 후보로 선다.
6. **동의 시각·버전 부재를 감수할 것인가.** 약관 동의 이력이 남지 않는 것은 서비스 성격(개인 프로젝트 vs 공개 서비스)에 따라 판단이 갈린다. 되돌릴 수 없는 종류다 — 과거 시각은 소급 복원되지 않는다.
7. **dev 환경을 세울 것인가, 언제.** (가)를 prod에서 바로 칠 것인지의 문제이기도 하다. 지금은 VPN 뒤라 prod에서 바로 치는 위험이 낮다 — **그 자체가 지금 움직일 이유다.**
8. **공개 전환은 언제인가.** §1대로 배선은 이미 서 있고 막고 있는 것은 사설 VIP 하나다. 이 날짜가 축 A·C·D·E의 실질 마감이고, (가) 전체의 마감이다. **날짜가 정해져 있지 않다면, 정하는 것 자체가 이 논의의 산출물이 될 수 있다.**
9. **auth-service를 계속 직접 지을 것인가**(§5 옵션 X). 축 A·C·F·F'를 각각 정하기 전에 먼저 답해야 하는 질문이다.

## 다음 단계 후보 (수렴 시)

- **(가)는 결정 없이 티켓으로 나갈 수 있다** — target `jyoliar-careerhub/auth-service`(1·3·4·6·7), `careerhub-api-composer`(2), `jae2274/jyoliar-k8s`(5). 근거 ADR 불요(리프).
- 옵션 X(기성 IdP 대체)가 살아 있으면 **A·C·F·F' 초안보다 먼저 판정한다** — 채택 시 그 넷이 소거되므로 먼저 쓰면 버리는 초안이 된다.
- 축 A가 A1로 수렴하면: ADR 초안 — *"서비스 간 토큰 신뢰를 비대칭 서명으로 가른다"*. 영향 범위가 저장소를 넘고 되돌리기가 비싸다.
- 축 F가 F2/F3로 수렴하면: ADR 초안 — *"정체성을 user에서 분리한다"*. 마이그레이션 티켓이 뒤따른다.
- 축 F'는 F와 **공동무효**로 보인다(§4③ 판정 필요) — 링크 정책 없이 identities 분리는 의미가 절반이고, 분리 없이 링크 정책은 표현할 자리가 없다. 한 ADR일 가능성이 높다.
- 축 E는 **새 논의를 열지 않는다** — `careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md`가 이미 그 축이다. 거기에 축 D⑥(`postMessage "*"`)와 축 E(봉투 영구 유효)를 재료로 넣는다.
