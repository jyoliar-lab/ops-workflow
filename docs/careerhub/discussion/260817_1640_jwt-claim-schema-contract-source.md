---
type: discussion
topic: careerhub
subjects:
  - zitadel
  - jwt
  - auth-service
  - careerhub-api-composer
  - careerhub-web
  - openapi
status: active
ref-adrs:
  - ADR-0031
  - ADR-0018
  - ADR-0020
  - ADR-0014
  - ADR-0029
---

# JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나

## 1. 문제 재정의

가져온 요구는 해법의 모양을 하고 있다 — *"언어 무관 계약 포맷 + 코드 생성"*.
먼저 무엇이 불편한지부터 다시 말한다.

Zitadel이 발급하는 JWT에 auth-service 발급 훅이 싣는 `careerhub:*` 클레임(#52)의 이름·모양이, **기계가독 원천 없이 소비자마다 손 전사되고 있다.**

치르고 있는 비용:

- 클레임의 키→값모양 바인딩이 산문으로만 존재한다.
  훅 스펙(`auth-service/spec/issuance-hook/openapi.yaml`)의 `AppendClaim.key` description이 *"이 표면이 내는 키는 둘뿐이다"* 라고 **문장으로** 말하고, `AuthorityClaim` 스키마는 components에 있지만 어느 키의 값인지는 산문이 잇는다.
- careerhub-web의 `src/lib/auth/claims.ts`는 타입(`Authority`·`SessionClaims`)과 파서를 **손으로** 쓰고, 주석으로 auth-service 스펙을 가리킨다.
  주석 참조에 의한 수동 복제다 — 컴파일도 CI도 이 정합을 검사하지 않는다.
- api-composer는 아직 레거시다(HS256 · `CustomClaims{UserId, Authorities []string}` — `jwtresolver/claims.go`).
  #56(토큰 검증 전환)이 착수되는 순간 **세 번째 손 전사**가 생기고, 값 모양도 `[]string`이 아니라 `[{code, expiresAt}]` 객체 배열로 바뀐다.
- drift의 증상이 소비자마다 다르다.
  web은 fail-loud 파서라 어긋나면 던진다(`ClaimContractError`) — 드러나긴 하지만 **프로덕션 런타임에** 드러난다.
  composer는 인가 판정의 입력이라, 전사가 어긋나면 조용한 권한 오판이 가능하다.

한 가지는 이미 해결돼 있다 — **발급 측의 값 타입은 생성물이다.**
auth-service는 `api.AuthorityClaim`(oapi-codegen 생성)으로 클레임을 조립한다(`issuancehook/service.go:47` · `claims.go:45-48`).
빠진 것은 키 상수(`claims.go:12-15`의 손 선언)와 키→값 바인딩뿐이다.
"발급 코드도 계약 코드로 작성"이라는 요구는 새 구축이 아니라 **절반 남은 것의 완성**이다.

## 2. 기존 결정 지형 — 이 논의가 여는 것과 열지 않는 것

- **ADR-0031** (accepted)이 관할 경계를 그어 뒀다: *"클레임의 이름·모양과 판정 코드는 코드의 관할이다."*
  #46 Out of Scope도 같은 문장을 반복한다.
  이 논의는 그 경계를 재개봉하지 않는다 — 저장소에 사는 기계가독 스키마 원천도 '코드의 관할' 안이다.
  다루는 것은 **코드 관할 안에서 원천을 어디 두고 소비자들이 어떻게 물리느냐**다.
- **ADR-0018·0019·0020** (accepted)이 REST·gRPC 계약의 원천 체계를 이미 세웠다: 원천은 코드 독립 명세, 배치는 provider 저장소, 공표물은 언어 중립 명세, 소비자는 공표 좌표에 핀.
  단 이 계열의 subjects는 전부 RPC 계약이다 — **토큰 payload 같은 비-RPC 계약이 문언상 포괄되는지는 어디에도 판정돼 있지 않다** (ADR-0020의 "프로토콜을 불문하고"가 걸치는지).
  이 논의의 산출이 그 판정이 될 수 있다.
- **기성 파이프라인이 세 저장소 모두에 있다:**
  - auth-service: spec-first + oapi-codegen (`make openapi`, CI 신선도 게이트)
  - api-composer: 동일 (spec-first + oapi-codegen + provider 계약 모듈 go.mod 핀)
  - careerhub-web: `scripts/gen-api-types.sh` — 핀 파일(`contracts/api-composer.pin`) → 공표 좌표에서 스펙 fetch → openapi-typescript 생성 → CI 드리프트 게이트
- **호환·진화 규율은 아직 결정이 아니다** — ADR-0021·0025·0026이 전부 proposed.
  클레임 계약을 세워도 그 진화 규율은 보류 벌의 관할이다.
- **제약 입력**: 축 D discussion(260722_1617)에 토큰 크기 실측이 미완 항목으로 걸려 있다 — 클레임 주입 후 access+refresh가 쿠키 4KB 한계 안인가.
  클레임 스키마에 무엇을 더 싣는 결정이든 이 실측이 선행 입력이다.

## 3. 소비 주체와 필요 층위

| 주체 | 언어 | 역할 | 필요한 것 |
|---|---|---|---|
| auth-service | Go | **발급**(훅 응답 조립) | 키 상수 + 값 타입 — 값 타입은 이미 생성물 |
| careerhub-api-composer | Go | **검증 + 인가 판정** (#56에서 전환) | 키 상수 + 값 타입 + 파싱 |
| careerhub-web | TS | **payload 디코드**(화면 힌트, 검증 안 함 — ADR-0029) | 키 상수 + 값 타입 + 파싱 |

두 층을 가른다 — 이 분해가 #56의 미정 항목과의 경계이기도 하다:

- **스키마 계약** (키·값 모양): 이 논의의 대상.
- **검증·파싱 로직** (JWKS·서명·클레임 추출): #56이 "공통 검증 모듈의 거주지(goutils vs 신규)"로 미정으로 남긴 구현 판단.
  스키마 계약이 서면 그 모듈은 계약 생성물을 **소비하는 쪽**이 된다 — 계약이 로직 공유를 대체하지 않고, 로직 공유가 계약을 대체하지 않는다.

## 4. 옵션

### O0 — 안 한다: 산문 계약 + 소비자별 손 전사 유지

현상 유지의 실질을 정직하게 세면:

- 클레임 2개·필드 2개 규모다. 전사 대상이 작아 실제 drift 확률은 낮다.
- web 파서가 fail-loud라 모양 어긋남은 침묵하지 않는다.
- 도구 체인·공표 좌표·핀 관리 비용이 0이다.

무너지는 조건:

- #56이 세 번째 전사를 만들고, 그쪽 증상은 조용한 인가 오판이다 — fail-loud를 또 손으로 잘 쓰기를 규율에 기대야 한다.
- #54(약관동의 앱 게이트)가 소비 3주체를 그대로 겹쳐 쓰고, 게이트 클레임이 늘 여지가 있다.
  클레임이 늘 때마다 전사 지점이 3배로 늘어난다.
- "규율이 아니라 구조로"라는 이 하네스의 관통 원칙과 정면으로 어긋난다 — 이미 REST 계약에서 같은 문제를 ADR-0018·0020으로 구조화한 전력이 있다.

### O1 — OpenAPI(components) 스키마를 원천으로, 기성 파이프라인에 물린다

JWT payload의 `careerhub:*` 부분을 하나의 객체 스키마로 선언한다.
OpenAPI/JSON Schema의 property 이름에는 `:`가 허용되므로 키가 곧 스키마에 산다 — 키 상수가 산문에서 스키마로 이동한다.

```yaml
CareerhubTokenClaims:
  type: object
  properties:
    "careerhub:authorities":
      type: array
      items: { $ref: '#/components/schemas/AuthorityClaim' }
    "careerhub:agreements_fulfilled":
      type: boolean
  # required 없음 — 원장 밖 사용자는 키 부재가 정상 (#52 계약)
```

생성 체인이 전부 기성이다:

- Go(auth-service·api-composer): oapi-codegen models — 이미 양쪽 Makefile에 있는 도구.
- TS(careerhub-web): `gen-api-types.sh`에 두 번째 핀 추가 — 이미 있는 스크립트의 매개변수화.

배치 하위 선택지 둘:

- **O1a — 훅 스펙에 얹고 훅 스펙을 공표한다.**
  파일 하나·공표 좌표 하나로 끝난다.
  결함: 훅 스펙은 스스로 *"계약의 소유자가 우리가 아니다"* 라고 선언한 Zitadel 전사다(`ContextInfo` 등).
  우리가 소유한 클레임 계약과 소유하지 않은 전사가 한 공표물에 섞이고, Zitadel 제품 갱신에 따른 전사 수정이 클레임 계약 소비자들에게 무의미한 버전 범프를 일으킨다.
  #64가 이미 훅 표면과 운영 표면의 스펙을 분리 관할로 그어 둔 결과와도 결이 어긋난다.
- **O1b — auth-service에 별도 스펙을 신설한다** (예 `spec/token-claims/`), paths 없는 components-only 문서.
  provider = 발급자 = auth-service — ADR-0020의 배치 판정(계약과 구현이 같은 저장소·같은 PR에서 묶이는 원자성)이 그대로 성립한다.
  발급 코드가 이 스키마의 생성물로 조립하면 원자성이 컴파일로 걸린다.
  공표는 기존 관례(태그 prefix `spec/token-claims/vX`) 재사용.
  훅 스펙의 `AuthorityClaim`과의 관계는 $ref 상대 참조(도구 마찰 확인 필요) 또는 훅 스펙 쪽이 생성물을 import하는 방식 — 구현 판단.

### O2 — 순수 JSON Schema를 원천으로

언어 중립 스키마의 정통이고, "HTTP 표면이 아닌 것을 OpenAPI로 부르는" 비정형이 없다.

기각 방향의 논거:

- 생성 도구 체인이 통째로 신규다 — Go(go-jsonschema 등)·TS(json-schema-to-typescript) 모두 세 저장소 어디에도 없다.
- CI 신선도 게이트·공표 관례·핀 스크립트를 새 체인용으로 복제해야 한다.
- OpenAPI 3.x components 스키마는 실질적으로 JSON Schema 방언이다 — O1과의 실차이는 문서의 겉포장이지 표현력이 아니다.
  포장 차이 때문에 도구 2벌을 새로 들이는 것은 비용만 있고 이득이 없다.
- 코퍼스 전체에 JSON Schema 선례가 0건이다 — 표준화 이득도 없다.

### O3 — Protobuf, #29의 계약 모듈 패턴

Go 소비자 배포 선례로는 최상이다 — proto + 생성 코드 + 자체 go.mod, prefix 태그 공표, go.mod 핀 (#29).

기각 방향의 논거:

- proto 필드명에 `:`가 올 수 없다 — `careerhub:authorities`는 `json_name` 우회가 필요하고, JWT는 어차피 JSON이라 매핑이 이중이 된다.
- careerhub-web에 proto→TS 체인이 없다 — 신규 도입이고, 기성 openapi-typescript 경로를 버리는 셈이다.
- `expiresAt: null = 무기한`이라는 계약(required + nullable)을 proto3가 자연스럽게 말하지 못한다(optional의 부재 ≠ null).
- proto의 힘(바이너리 인코딩·RPC)을 하나도 안 쓴다 — JWT payload는 JSON으로 고정돼 있다.

### O4 — 계약 포맷 없이 코드 라이브러리 공유

Go 공용 모듈(goutils 또는 신규)에 타입+파서를 두고, TS는 별도 유지.

기각 방향의 논거:

- Go 둘은 해결되지만 **언어 경계에서 다시 손 전사**가 남는다 — 요구 1(언어 무관 포맷)의 부정이고, 문제의 핵심 지점(web과의 경계)이 그대로다.
- 원천이 특정 언어의 타입 선언이 된다 — ADR-0020이 공표물에 대해 그은 선(*"특정 언어용 생성물은 편의의 파생물이지 공표의 본체가 아니다"*)의 정신과 어긋난다.
- 단, 이 옵션의 절반 — **Go 검증·파싱 로직의 공용 모듈** — 은 죽지 않는다.
  그것은 계약의 대체물이 아니라 계약 생성물의 소비자로서 #56 관할에 남는다(§3의 층 분해).

## 5. 비교

| 축 | O0 안 한다 | O1b 별도 OpenAPI | O2 JSON Schema | O3 proto | O4 코드 공유 |
|---|---|---|---|---|---|
| 언어 경계 해결 | ✗ | ✓ | ✓ | △ (TS 체인 신규) | ✗ |
| 도구 신규 도입 | 0 | **0** (전부 기성) | 2벌 | TS 1벌 + json_name 마찰 | 0 |
| 발급-계약 원자성 (ADR-0020 축) | — | ✓ 같은 저장소·컴파일 | ✓ | ✓ | Go만 |
| drift 검출 시점 | 프로덕션 런타임 | CI (신선도·핀 범프) | CI | CI | Go는 컴파일, TS는 런타임 |
| 되돌리기 비용 | 0 | 낮음 — 생성물을 손 코드로 동결하면 끝 | 중간 (체인 폐기) | 중간 | 낮음 |
| 무너지는 조건 | 소비자·클레임 증가 | 비-RPC 계약에 OpenAPI 포장이 마찰을 일으키는 경우 | — | — | TS 소비 확대 |

## 6. 잠정 관찰 — 수렴 아님

O1b가 유리해 보이는 이유는 포맷의 우열이 아니라 **이 코퍼스와 세 저장소에 이미 깔린 것의 총량**이다.
ADR-0018·0020의 원천 체계, oapi-codegen×2, openapi-typescript 핀 스크립트, CI 신선도 게이트 — 전부 재사용이고 신규 도입이 0이다.
같은 이유로 O2·O3는 "더 정통인 포맷"이어도 여기서는 비용만 산다.

반대편에 서서 — **O0을 너무 빨리 버리지 말 것.**
클레임 2개에 공표 좌표·핀·버전 범프 체계를 얹는 것은 지금 규모에선 과잉일 수 있다.
O1b의 실질 비용은 도구가 아니라 **운영**이다: 클레임 하나 바꿀 때마다 태그 공표 → 소비자 3곳 핀 범프 → 재생성 커밋이 도는 것.
이 비용을 정당화하는 것은 현재가 아니라 #56·#54가 만드는 가까운 미래다 — 그 미래가 확실한지가 판정 지점이다.

## 7. 열린 질문

1. **공표·핀 규율을 REST 계약과 동일하게 갈 것인가** — 태그 공표 + Renovate/수동 범프.
   클레임은 REST와 달리 "발급자가 바꾸면 이미 발급된 토큰과 새 토큰이 공존"하는 시간축이 있다 — 핀이 낡은 소비자는 새 클레임을 그냥 모른 채 지나가는가, 거부하는가.
   (web의 현행 파서는 모르는 키 무시 + 아는 키 모양 검사 — tolerant reader. 이 규율을 계약 문서에 명문화할 것인가는 ADR-0025 보류 벌과 겹친다.)
2. **훅 스펙과의 결합 방식** — $ref 상대 참조가 oapi-codegen·openapi-typescript 양쪽에서 마찰 없이 도는지 실측 필요.
   안 돌면 훅 스펙 쪽에 사본을 두고 CI가 정합을 검사하는 차선이 있다.
3. **api-composer의 파싱을 생성물로 강제하는 방식** — golang-jwt의 claims struct에 생성 모델을 어떻게 물리는가(embedding vs 2단 unmarshal).
   구현 판단이지만 #56 본문에 걸어 둘 가치가 있다.
4. **토큰 크기 실측**(축 D 미완 항목)이 이 계약의 제약으로 먼저 확인돼야 하는가.

## 8. 다음 단계 후보

- 수렴 시 ADR 후보: **"토큰 클레임 계약의 원천을 발급자 저장소의 언어 중립 명세에 둔다"** — ADR-0018·0020의 비-RPC 확장 판정.
  one-way door 성립 여지: 소비자 3곳의 생성 파이프라인이 물리는 순간 포맷·배치 변경의 파급이 3저장소 CI에 걸친다.
  단 §5의 되돌리기 비용이 낮다는 판정이 맞다면 임계선 미달일 수도 있다 — 초안을 써 보며 가른다.
- 티켓 후보(수렴 후): 계약 신설(auth-service) / composer 소비 전환(#56에 병합 가능) / web 소비 전환 — 쪼갬 자체가 별도 발산 거리다.
