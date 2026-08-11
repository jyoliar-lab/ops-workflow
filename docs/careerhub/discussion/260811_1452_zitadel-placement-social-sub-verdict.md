---
type: discussion
topic: careerhub
subjects: [zitadel, auth-service, google, naver, cert-manager]
status: active
ref-adrs: [ADR-0030, ADR-0027]
---

# Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정

## 문제

ADR-0030 Context는 "제품을 기존 호스트 아래 경로에 두고 기존 client_id를 물려주면 기존 사용자의 IdP 연결이 보존된다"를 배치 제약으로 적었다.
그러나 인프라 정찰에서 `/auth` 경로 충돌과 Zitadel 서브패스 미지원 개연이 걸렸고, 라우팅 논의(`260810_1801`)는 "Zitadel 호스트만 실측에 걸려 있다"로 미결을 좁혔다.
이 문서는 그 실측의 결과다 — 두 축을 판정한다: ① Zitadel이 서브패스에서 서빙될 수 있는가, ② 기존 IdP 연결 보존이 실제로 요구하는 조건은 무엇인가.

## 실측 ① — 서브패스 서빙: 불가

Zitadel v4.16.3(2026-08-07, 조사 시점 최신 stable) 기준.

- **공식 구조가 도메인 루트를 전제한다.**
  `ExternalDomain`은 protocol/host/port 단위 설정이고, 경로 포함 예시·옵션이 문서에 없다.
  Zitadel은 도메인 루트 기준으로 `/oidc/v1/` · `/oauth/v2/` · `/.well-known/openid-configuration` · `/ui/console/` · `/ui/v2/login` · `/auth/v1/` 등 고정 prefix를 점유하고, OIDC issuer는 경로 없는 도메인 그 자체다.
  (zitadel.com/docs/self-hosting/manage/custom-domain, zitadel.com/docs/apis/introduction)
- **개발자가 미지원을 명시했다.**
  Discussion #6757에서 핵심 개발자(eliobischof): "I'm afraid ZITADEL doesn't support configuring all endpoint paths."
  서브패스 요청 이슈 #11680·#10142는 ETA 없이 `To-be-closed` 상태다 — v4에서도 구현되지 않았고 로드맵 신호가 없다.
- **프록시 URLRewrite 우회는 실패 사례만 실재한다.**
  서브패스 뒤에 두면 내부 리다이렉트가 루트 기준이라 404가 나고(#11680 본문), issuer가 ExternalDomain에서 파생되므로 클라이언트가 본 URL과 어긋나면 discovery가 즉시 깨지며(oauth2-proxy #2380), login v2는 BaseURI에 path가 개입하는 지점마다 URL 조립 버그가 실재한다(#11415).
  서브패스 rewrite를 끝까지 성공시킨 공개 사례는 찾지 못했다.

→ **서브패스 배치는 선택지가 아니다.**
`/auth` PathPrefix 충돌(auth-service 점유 vs Zitadel `/auth/v1/*`)은 논점에서 소멸한다 — 경로를 비켜도 서브패스 자체가 성립하지 않는다.

## 실측 ② — 소셜 sub: 무엇의 함수인가

`260804_1831` §9가 규격 층위를 정리해뒀다 — pairwise sub의 축은 client_id가 아니라 sector identifier(기본값: redirect_uri의 호스트)다.
이번 실측은 그 표의 미확인 칸을 제공자별 실증으로 채운다.

### Google — `public` subject. 배치가 sub에 영향을 줄 수 없다

- `https://accounts.google.com/.well-known/openid-configuration` 실측: `"subject_types_supported": ["public"]`.
- OIDC Core §8의 public 정의: *"This provides the same sub (subject) value to all Clients."* — sub는 client_id의 함수도, redirect_uri 호스트의 함수도 아니다.
- Google 공식 문서: sub는 *"unique among all Google Accounts and never reused"* — 계정에 귀속되는 영구 불변값.
- 같은 프로젝트 내 다른 client_id로 발급받은 id_token에서 sub가 동일함을 보인 공개 실험이 있다(jpassing.com, 2023-02).
  타 프로젝트 간 직접 실험 인용은 미확인이나, public 선언이 규범적으로 보장한다(프로젝트 단위 예외 없음).

→ **기존 Google 사용자의 연결 보존은 배치와 무관하다.**
Zitadel이 어느 호스트에 살든, 어떤 redirect_uri로 Google을 브로킹하든, Google이 돌려주는 sub는 같다.

### 기존 연결의 실체 — Google뿐이다

- auth-service의 소셜 구현은 Google 하나다 (`auth_service/restapi/ooauth/`에 `google.go`만 존재).
- DB 스키마가 구조적으로 증언한다: `CREATE TYPE user_authorized_by AS ENUM ('GOOGLE', 'DELETED')` (`sql/migrations/00001_init_schema.sql:3`) — Naver 사용자는 존재할 수 없는 스키마다.
- 참조 저장소 15개 전체 grep에서 Naver 연동 코드 0건.
- 식별자 저장 형태: `user (authorized_by, authorized_id)` UNIQUE — Google userinfo v3의 `sub`를 `AuthorizedID`로 저장한다 (`google.go`).

→ **"기존 Naver 사용자의 sub 보존"은 공집합이다.**
Naver 축은 기존 보존 문제가 아니라 신규 도입 설계 문제로 성격이 바뀐다.

### Naver — 신규 도입. 식별자의 축은 애플리케이션(Client ID)이다

- 공식 프로필 API 문서 명시: *"'id'값은 각 애플리케이션마다 회원 별로 유니크한 값으로, 같은 네이버 회원이라도 네이버 로그인을 적용한 애플리케이션이 다르면 id값이 다른 점 유념하시길 바랍니다."*
- 2021-05-01 발급 스펙 변경(공지 7524): 이후 등록 앱은 base64형 — 적용 단위가 "애플리케이션(Client ID)"으로 규정돼 있다.
- Naver는 표준 OIDC를 별도 제공한다(`https://nid.naver.com/.well-known/openid-configuration` 실측 — discovery·id_token·`pairwise` 선언·S256). ADR-0030 요구 ①(generic OIDC 브로킹)의 전제가 실증됐다.
- Callback URL만 바꿀 때 id가 유지되는지는 공식 명시가 없다(미확인).
  다만 문서·공지가 일관되게 축을 앱으로 서술하고, 무엇보다 신규 도입이므로 이 미확인은 지금 위험이 아니다.

→ **Naver 앱은 Zitadel의 콜백 호스트가 확정된 뒤 등록하면 된다.**
미래를 위한 기록: 도입 후 Zitadel 호스트를 옮길 일이 생기면 "앱 유지 시 id 보존"을 그때 실측해야 한다 — 앱을 재등록하면 매핑이 전부 끊기는 것은 확실하다.

## 판정

**① 배치: 신규 호스트로 간다 — 서브패스는 불가이고, 갈 이유도 소멸했다.**
호스트는 라우팅 논의의 종착 그림대로 `*.careerhub.jyo-liar.com` 네임스페이스 안에서 고른다.
구체 호스트명·매니페스트는 코드·설정의 관할이다(ADR-0030 Decision의 위임 그대로).

**② 기존 IdP 연결 보존의 진짜 요구는 "배치"가 아니라 "데이터 이전"이다.**
보존 대상은 Google뿐이고 Google은 public subject이므로, 요구는 단 하나로 줄어든다: **Zitadel로 사용자를 이전할 때 기존 `user.authorized_id`(Google sub)를 Zitadel의 Google IdP 연결에 심는 것.**
호스트도, redirect_uri도, 심지어 client_id도 sub를 바꾸지 못한다.
다만 기존 Google client 재사용을 권장한다 — 타 프로젝트 실험 미확인이라는 잔여 불확실성까지 제거되고, 사용자에게 보이는 동의 화면의 앱 정체성도 유지된다.

**③ "redirect_uri 호스트 유지 필수" 시나리오는 발생하지 않는다.**
티켓 코멘트가 예고한 새 미결(레거시 루트 호스트의 장기 존속 재론)은 열리지 않고 닫힌다.
`260810_1801`의 "남은 게이트"는 이것으로 해소됐다 — 실측에 걸려 있던 마지막 미결이었다.

**④ ADR-0030 Context의 배치 제약 서술은 과잉이었다 — 그러나 Decision은 흔들리지 않는다.**
"기존 호스트 아래 경로 + 기존 client_id" 조건은 충분조건이었지 필요조건이 아니다(Google public 실증).
Consequences의 "IdP 연결은 호스트·client_id 유지로 보존된다"도 같은 과잉이다.
Decision(제품 채택)의 세 기둥(발급 훅·업그레이드 노동·자원 적합)과 무관하고, 배치 경로는 명시적으로 코드·설정 관할로 위임돼 있으므로 supersede 사유가 아니다.
동결된 Context의 보정은 이 문서가 담당한다 — ADR-0030을 읽는 사람은 `_index/by-ref-adr.md` 경유로 이 판정에 닿는다.

## Zitadel 배포 리프가 딛는 사실

- 신규 호스트 1개 (`*.careerhub.jyo-liar.com` 안에서 명명) — external-dns 자동 레코드.
- 인증서 `wildcard-jyoliar-tls`(`*.jyo-liar.com` + apex)에 `*.careerhub.jyo-liar.com` SAN 추가 — issuer `letsencrypt-dns`(DNS-01)라 1회 비용 (`gitops/base/services/careerhub/apps/gateway/wildcard-certificate.yaml`).
- Google client에 Zitadel 콜백 URI 추가는 **IaC 밖 수동 단계**다 — client는 GCP Console 수동 생성물이고(`jyoliar-platform-terraform/oauth/variables.tf`: "created manually in GCP Console"), `GOOGLE_REDIRECT_URL`은 SSM 파라미터에 값으로 박혀 있다(`oauth/google.tf`).
  배포 절차에 수동 단계로 명시해야 한다.
- 사용자 이전 시 Google sub 매핑(판정 ②)은 배포 리프가 아니라 이전(마이그레이션) 리프의 요구다.

## 열어둔 것 — 미확인의 정직한 목록

- **Naver pairwise의 정확한 축** (client_id vs redirect_uri 호스트) — 공식 문서로 판별 불가.
  신규 도입이라 지금은 무해하나, 도입 후 호스트 이동 시 실측 필요.
- **Naver OIDC `sub` ≟ 프로필 API `id`** — 동일 여부 문서 미명시.
  Naver 도입 설계 시 확인해야 한다(Zitadel generic OIDC 브로킹은 `sub`를 받는다).
- **Google 타 프로젝트 client 간 sub 동일성의 직접 실험** — 규범 보장(public)은 있으나 실측 인용은 없다.
  기존 client 재사용(판정 ②)이 이 미확인을 무위험화한다.
