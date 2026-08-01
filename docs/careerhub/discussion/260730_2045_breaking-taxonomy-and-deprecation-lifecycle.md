---
type: discussion
topic: careerhub
subjects: [openapi, grpc, protobuf, careerhub-web]
status: active
ref-adrs: [ADR-0021, ADR-0025, ADR-0026]
---

# 비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대

## 계기 — ADR-0021(proposed)의 비결정 지점 3개

ADR-0021 초안 검토에서 "어딘가 비결정론적이고 완전하지 않다"는 지적이 나왔다. 재독 결과 미결이 세 곳이다:

1. **"비호환"의 판정 기준이 외주화되어 있다.** Context가 "breaking 검출 도구들이 정적으로 판정하는 것"이라고만 말한다 — 필드 제거·타입 변경·필수화 세 예시뿐, 목록의 소유자가 없다. 도구 기본값이 곧 정책이 되는데 도구마다·설정마다 판정이 다르다. *어느 수준의 호환성*(wire / 생성 코드 / JSON)을 지키는지가 미결.
2. **deprecated의 수명이 무한정이다.** Decision은 "구형은 폐기 예정으로 표시"까지만 말하고, Consequences가 스스로 자백한다 — *"제거를 잊으면 병존이 고착된다 — 폐기 표시가 제거를 보증하지 않는다."* **언제까지**(시간인가 이벤트인가)와 **누가 잊지 않게 하는가**(사람 기억인가 CI인가)가 둘 다 비어 있다.
3. **"이행 완료의 증명"이 소비자 유형에 따라 성립하지 않는다.** "소비자의 컴파일·핀 갱신으로 증명"은 코드 생성 소비자에만 통한다. 웹 프론트의 **브라우저 캐시된 구 번들**은 컴파일 증명 밖이다 — Context가 스스로 지적한 캐시 문제가 contract 단계의 안전 증명에서는 다뤄지지 않았다.

이 문서는 그 세 구멍을 닫기 위한 업계 규범·도구 조사(2건 병렬, 2026-07-30)의 결과와 옵션을 기록한다. **ADR-0021 수정은 아직 하지 않는다** — 보강 후보만 정리하고 사람의 결정을 기다린다.

---

## 조사 1 — 하위 호환을 깨뜨리는 변경의 구체 분류

### 1-1. 기계 판정의 핵심 원리: 방향성 비대칭

oasdiff가 명문화한 원리 — 요청과 응답은 반대로 판정된다:

| | 호환 | 파괴 |
|---|---|---|
| **요청** (수용 범위) | 넓힌다 — optional 필드/파라미터 추가, 제약 완화 | 좁힌다 — 필수 필드 추가(**기본값이 있어도**), optional→required, 타입 변경, min/max 강화, nullable 제거, enum 값 제거 |
| **응답** (보장) | 유지·강화한다 — 속성 추가 | 약화한다 — 필수 속성 제거, 타입 확장, nullable화, 성공 상태코드 제거 |

- oasdiff의 판정 기준: 서버 구현의 관용이 아니라 **스펙이 선언한 계약** 기준. "이전에 유효했던 요청을 무효로 만드는 변경은, 서버가 실제로는 수용하더라도 breaking." 심각도 3단계(ERR/WARN/INFO), 총 500여 체크.
- 출처: https://www.oasdiff.com/docs/breaking-changes · https://github.com/oasdiff/oasdiff/blob/main/docs/BREAKING-CHANGES.md

### 1-2. protobuf: buf breaking의 4단 호환성 사다리

"비호환"은 단일 개념이 아니라 **어느 층을 지키는가의 선택**이다 (엄격→관대, 각각 아래의 상위집합):

| 카테고리 | 보호 대상 | 대표 규칙 |
|---|---|---|
| `FILE` (기본값) | 파일 단위 생성 코드 | `FIELD_NO_DELETE`, `FIELD_SAME_TYPE`, `RPC_NO_DELETE` |
| `PACKAGE` | 패키지 단위 생성 코드 | 같은 패키지 내 파일 간 이동 허용 |
| `WIRE_JSON` | wire + JSON 인코딩 | `FIELD_NO_DELETE_UNLESS_NAME_RESERVED`, `FIELD_SAME_NAME`(JSON은 필드명이 계약) |
| `WIRE` | 바이너리 wire만 | `FIELD_NO_DELETE_UNLESS_NUMBER_RESERVED`(번호만 계약, 이름은 자유) |

`FIELD_SAME_NAME`이 WIRE에 없는 것이 층위 차이의 지도다 — 필드 rename은 wire-호환이지만 JSON·생성 코드 비호환. careerhub는 gRPC-gateway 없는 바이너리 gRPC지만 소비자가 생성 Go 코드를 소비하므로(G1′ 방향, `260730_1620`) `FILE`이 자연스럽다 — 단 **카테고리 선택 = buf 설정은 코드 관할**이고, "생성 코드 호환까지가 계약"이라는 **층위 선언**만 ADR감이다.

출처: https://buf.build/docs/breaking/rules/

### 1-3. Zalando의 쌍 구조 — 호환 확장은 소비자 의무가 있어야 성립한다

- **#107** (provider: 호환 확장 선호 — optional 추가, `x-extensible-enum` 확장)과 **#108** (consumer: **tolerant reader 의무** — 미지 필드 무시)은 쌍이다. "응답 필드 추가 = 호환"은 소비자가 미지 필드를 무시할 의무를 질 때만 성립하는 계약.
- **ADR-0021에는 현재 소비자 의무 조항이 없다** — 계약의 반쪽이 비어 있다.
- #109는 "시맨틱 변경"을 제거와 동급 금지로 명시. #110(최상위는 항상 JSON 객체 — 배열 금지)도 확장 가능성 규칙.
- 출처: https://opensource.zalando.com/restful-api-guidelines/ (#106–#112)

### 1-4. 기계가 못 잡는 파괴 — semantic compatibility의 사각지대

Google AIP-180의 3중 구분: **source**(컴파일) / **wire**(통신) / **semantic**("합리적 개발자가 기대할 것을 계속 받는다") 호환성. diff 도구는 앞의 둘만 검사한다. 세 번째의 부류:

- 값 포맷·생성 알고리즘 변경 (OUTPUT_ONLY 필드라도)
- 기본값 변경, 기본값의 직렬화 방식 변경 (존재/부재 자체에 의미를 부여하는 소비자)
- **문자열 길이 상한 "완화"조차 breaking** — 소비자 저장·검증 가정을 깬다. 방향성 규칙(1-1)의 예외.
- 에러 응답·상태코드의 행동 변경 (스펙 밖 선언이면 diff가 침묵)
- 근원은 Hyrum's Law: 관측 가능한 모든 행동이 사실상의 계약. Stripe가 "응답 속성 순서 변경·ID 접두사 변경은 호환"을 **문서로 명시 선언**하는 것은 이 회색지대를 계약 문서로 선점하는 방어다.

출처: https://google.aip.dev/180 · https://www.hyrumslaw.com/ · https://docs.stripe.com/upgrades

### 1-5. 분해 불가능한(또는 분해가 무의미한) 파괴 — 4부류

ADR-0021은 현재 "모든 비호환은 호환 단계로 분해 가능"을 암묵 전제한다. 조사가 확인한 예외:

1. **보안·컴플라이언스 강제 — 병존(expand) 자체가 위반인 경우.** PCI의 TLS 1.0 하드 컷오프(2018), GitHub 패스워드 기본인증 폐지(2020). 업계 모델은 "단계적 분해"가 아니라 **"단계적 경보 후 일괄 파괴"** — GitHub의 brownout(의도적 일시 차단으로 미이행 소비자 각성 → 확정일 차단).
2. **버그가 계약이 된 경우 (bug-for-bug compatibility).** 올바른 동작과 버그 동작을 병존시키는 expand는 잘못된 계약의 공식화다. Stripe는 버그 동작을 구버전에 동결하고 신버전에서만 수정. 보안 관련이면 1로 합류.
3. **protobuf의 영구 소각.** field number 재사용은 wire 디코딩을 모호하게 만들어 파싱 오류·**데이터 손상·PII 유출**까지(protobuf 공식 문서). 되돌리는 절차가 없고 `reserved`가 유일한 방어. 또 **package/서비스명은 gRPC 라우팅 경로(`/{package}.{Service}/{method}`)에 박혀** wire-호환이어도 변경 즉시 파괴.
4. **회색지대: 응답 enum 값 추가.** provider는 호환이라 선언하지만(Zalando `x-extensible-enum`, Stripe "새 event type은 호환") 소비자의 exhaustive switch·closed 역직렬화(Java `valueOf`)는 깨진다. GraphQL Inspector는 breaking/safe 이분법을 버리고 **"Dangerous" 제3 범주**를 둔다 — 호환 여부가 provider 쪽에서 판정 불가능하다는 도구적 인정. 해법은 소비자 의무(unknown 값 처리)의 계약 명문화뿐(1-3과 합류).

출처: https://github.blog/news-insights/company-news/token-authentication-requirements-for-api-and-git-operations/ · https://protobuf.dev/programming-guides/proto3/ · https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md · https://the-guild.dev/graphql/inspector/docs/essentials/diff

---

## 조사 2 — deprecated는 언제까지, 무엇이 강제하나

### 2-1. 업계 기준은 두 계열 — 갈림의 조건이 명확하다

**시간 기반** (통제 밖·열거 불가 소비자):

| 조직 | 기준 |
|---|---|
| Kubernetes | GA는 **같은 major 내 제거 불가**, beta는 deprecated 후 9개월/3릴리스 |
| Google AIP-181 | stable은 major 수명 내 파괴 금지, beta는 경험칙 **90일** |
| GitHub | 구버전 최소 **24개월**, ~12개월 전 공지, Sunset+Deprecation 헤더 송신 |
| Salesforce | 버전당 최소 **3년** |
| Stripe | 계정별 버전 핀 — 강제 이행 없음, 구버전 사실상 무기한 |

**이벤트 기반** (열거 가능 소비자 + 증명 가능한 이행):

- Zalando [185]: "**모든 클라이언트가 sunset 날짜에 동의해야** shut down 가능" — 시간이 아니라 동의가 게이트.
- Google 모노레포(SWE at Google 15장): "done = **참조 0 도달**", 빌드 그래프가 소비자를 열거, 전문가 팀이 소비자 코드를 직접 이행.

**핵심 발견: 시간 기반의 정당화 근거는 전부 "열거 불가 소비자"다.** careerhub는 소비자 전원이 org 내부 + 이행이 컴파일·핀으로 증명 가능 → 이벤트 기반의 성립 조건에 정확히 해당하고, ADR-0021의 직감은 업계 수렴점과 일치한다. (이 조건의 소멸 = ADR-0021의 기존 무효화 조건 "통제 밖 소비자 다수"와 동일 — 그때 시간 기반의 계산이 다시 선다.)

출처: https://kubernetes.io/docs/reference/using-api/deprecation-policy/ · https://google.aip.dev/181 · https://docs.github.com/en/rest/about-the-rest-api/breaking-changes · https://opensource.zalando.com/restful-api-guidelines/#deprecation · https://abseil.io/resources/swe-book/html/ch15.html

### 2-2. 순수 이벤트 기반의 구멍 둘 (careerhub 조건)

1. **웹 프론트는 순수 이벤트 기반이 성립하지 않는다.** 컴파일·핀 증명은 "신 번들이 구형을 안 쓴다"까지만 증명한다. **브라우저에 캐시된 구 번들**은 프론트 배포 후에도 구형을 읽는다 → 웹이 소비하는 경계에는 "프론트 배포 + **구 번들 생존 창 경과**"라는 시간 하한이 이벤트 위에 얹혀야 한다. 창의 길이는 캐시 정책·세션 패턴의 함수 — **수치는 §4①대로 코드 관할**, "웹 소비 경계에는 시간 하한이 있다"는 원칙만 결정감.
2. **이벤트 기반의 알려진 실패 모드가 "제거를 잊음"이다.** 시간 기반 조직들은 기한이 자동 집행된다 — K8s는 타입 정의의 마커 주석(`+k8s:prerelease-lifecycle-gen:removed=1.25`)에서 생성된 `APILifecycleRemoved()`를 apiserver가 읽어 **removed 릴리스 도달 시 서빙을 자동 중단** — 잊는 것이 구조적으로 불가능한 유일한 참조 구현. 이벤트 기반은 별도 장치가 없으면 사람 기억이다.

### 2-3. 기계 가독 sunset 표현 — 표준

- **RFC 9745 `Deprecation` 헤더** (2025-03 표준화): "비권장 시작 시점" (Unix time). 리소스는 계속 동작.
- **RFC 8594 `Sunset` 헤더** (2019): "응답 불능 예정 시점" (HTTP-date). 정보성.
- 역할 구분: 폐기는 2단계 — 1단계(비권장)는 Deprecation, 2단계(제거 확정)에 Sunset 병기. Sunset은 Deprecation보다 앞설 수 없다(MUST NOT).
- **OpenAPI**: 표준 필드 없음 — 관례는 `deprecated: true` + 확장 **`x-sunset`**(RFC3339). oasdiff가 이를 판정에 사용.
- **protobuf: sunset 날짜 표준이 없다.** `[deprecated = true]`는 불리언뿐. buf에도 시간 기반 검사가 없다(4개 카테고리는 전부 두 버전 간 구조 비교). — gRPC 경계의 구조적 비대칭.

출처: https://www.rfc-editor.org/rfc/rfc9745.html · https://www.rfc-editor.org/rfc/rfc8594.html · https://github.com/oasdiff/oasdiff/blob/main/docs/DEPRECATION.md

### 2-4. 강제 장치 — 세 계열 (상보적)

**① 기한 선언 + CI 판정** (REST 한정):
- oasdiff의 sunset 검사(실측 id — 소스에서 확인): `api-removed-before-sunset` / `api-path-removed-before-sunset`(sunset 전 제거 = breaking), `api-deprecated-sunset-missing`(유예 정책 활성 시 sunset 없는 deprecation = breaking), `api-sunset-date-changed-too-small`(날짜 앞당기기 차단), `api-removed-without-deprecation`.
- `--deprecation-days-stable` / `--deprecation-days-beta`: deprecation 시점에 최소 유예 미달 sunset을 거부. **현행 기본값은 0(비활성)** — 설정해야 작동. 구 문헌의 "beta 31일/stable 180일 기본"은 낡은 정보.
- **sunset 도달 후 제거는 허용** — ADR-0021 Consequences가 "구현 판단"으로 미룬 *"이행이 증명된 제거를 명시적으로 통과시키는 절차"* 의 기성품이 이것이다.
- **한계**: oasdiff는 diff 도구라 "변경 없이 날짜만 지난 잔존"은 못 잡는다 → 그건 스펙 전체를 매번 스캔하는 lint의 몫(Spectral custom function 또는 몇 줄 스크립트: `x-sunset < today → fail`). 기성 표준 룰은 없음(자체 스크립트 영역). 또 x-sunset은 operation 수준만 완전 지원 — property 수준 deprecated에는 못 단다(open issue #627).

**② 신규 사용 차단 + 소비자 빌드 강제** (프로토콜 무관):
- 생성 코드의 deprecated 마커 → 소비자 lint: Go `// Deprecated:` → staticcheck **SA1019**(proto `[deprecated=true]`가 생성하는 주석 그대로 인식), TS `@deprecated` JSDoc → `@typescript-eslint/no-deprecated`(구 eslint-plugin-deprecation의 후신).
- 효과 둘: migrate 증명이 "컴파일 통과"에서 "**lint 통과**"로 강화(deprecated를 아직 쓰면 걸린다) + deprecated의 신규 사용(역행) 차단 — Zalando [191] "deprecated API 신규 사용 금지"·Google Tricorder의 기계화 계보.
- 주의: openapi-generator의 deprecated 전파는 생성기·언어별 불완전(Java `@Deprecated` 어노테이션 누락 버그 #12804) — 도입 시 전파 품질 확인 필요.

**③ 관측 기반 확인** ("0 호출" 증명):
- K8s `apiserver_requested_deprecated_apis` 메트릭 + Warning 헤더 + audit 주석. Zalando [188] "sunset 예정 API의 사용량 모니터링은 MUST".
- careerhub 규모에서는 ②의 빌드 증명이 있어 ③은 보조 — 단 **웹 캐시 창(2-2의 구멍 1)의 실측**에는 ③이 유일한 수단이다(구 번들의 구형 호출이 0이 됐는지는 빌드가 아니라 로그만 안다).

### 2-5. gRPC 경계의 비대칭과 이 저장소다운 선택지

proto에는 sunset 표준이 없고 buf에 시간 검사가 없으므로, ①계열은 REST 전용이다. gRPC 쪽 잊힘 방지 후보로 논의에서 나온 것:

> **expand PR 머지 시점에 contract Task 티켓을 함께 발행하는 규약.** 잔여 작업이 사람 기억이 아니라 컨트롤 플레인의 열린 티켓으로 남는다 — §8("규율이 아니라 구조로")의 모양이고, 프로토콜 무관(REST·gRPC 동일)하게 동작하며 추가 도구가 없다. 선행 의존(ADR-0017)으로 "migrate 완료(소비자 핀 범프 머지)"를 걸면 착수 게이트도 규약에 맞물린다.

---

## 옵션

### 축 1 — contract(제거)의 게이트 기준

- **E1. 이벤트 기반 + 웹 캐시 시간 하한** — 이행 증명(핀 갱신·lint 통과)이 게이트, 웹이 소비하는 경계만 "프론트 배포 + 구 번들 생존 창 경과"를 얹는다.
  - 이기는 조건: 지금의 careerhub — 소비자 열거 가능, 이행 증명 가능. 업계 동형(Google·Zalando 내부형)과 일치.
  - 지는 조건: 통제 밖 소비자 등장(= ADR-0021 기존 무효화 조건과 동일).
- **E2. 순수 이벤트 기반** — 캐시 창은 무시하거나 배포 관행으로 흡수. 가장 단순하지만 구 번들이 구형을 읽는 창이 무방비로 남는다 — Context가 지적한 캐시 문제를 contract 단계에서만 눈감는 비일관.
- **E3. 시간 기반** (x-sunset 일수 고정) — deprecation 시 sunset 필수 + 최소 유예 경과 후 제거. 규칙이 가장 단순하고 기계 판정이 완결적. 그러나 현 조건에서는 근거 없는 대기(이행이 끝났는데 날짜를 기다림)가 생기고, 시간 기반의 정당화 전제(열거 불가 소비자)가 부재.

### 축 2 — "제거를 잊음"의 방지 장치 (복수 채택 가능, 상보적)

- **F1. contract Task 동시 발행** — 프로토콜 무관, 추가 도구 0, 컨트롤 플레인이 기억을 대신. 단 티켓 발행 규약이라는 사람 규율이 하나 늘어난다(발행 자체를 CI가 하지 않는 한).
- **F2. x-sunset + CI 스캔** — REST 한정. oasdiff(제거 시점 판정) + 잔존 스캔 스텝(날짜 경과 감지). proto 등가물 없음.
- **F3. 소비자 lint 강제** (SA1019·no-deprecated) — 잊힘 방지라기보다 migrate 증명 강화 + 역행 차단. F1/F2와 상보.

### 축 3 — 반영 위치 (ADR-0021 보강 후보 ⓐ~ⓓ)

이번 세션에서는 **ADR을 수정하지 않는다**(사람 판단). 조사로 확정된 보강 후보만 기록한다:

- **ⓐ 호환성 층위 선언** — "생성 코드 호환까지가 계약"(buf FILE 수준 상당). 층위 없이는 "비호환"이 판정 불능(1-2). 구체 카테고리·설정은 코드 관할.
- **ⓑ 소비자 의무 명문화** — tolerant reader(미지 필드 무시)·unknown enum 값 처리(1-3, 1-5④). "호환 확장" 원칙이 뒤집히면 함께 무효 → §4③상 ADR-0021과 한 몸이라는 판정. 반론 여지: 소비자 의무는 provider 규약과 독립적으로 살 수 있다는 시각도 가능 — 별개 ADR 여부는 사람 판정.
- **ⓒ 분해 불가 예외** — 보안·컴플라이언스 강제와 버그-계약은 expand-contract 밖, 절차는 "경보 후 일괄 파괴"(1-5①②). 원칙의 예외는 원칙과 함께 산다 → 같은 ADR로 판정. 
- **ⓓ contract 게이트의 원칙** — 축 1의 결정 + 축 2의 구조화 방침. 현재의 "그 절차의 형태는 구현 판단"이라는 회피를 원칙 수준까지 닫는다. 수치(캐시 창 일수·유예 일수·도구 설정)는 전부 코드 관할로 남긴다.

코드 관할로 남길 것(§4①): oasdiff·buf 설정값, `--deprecation-days` 일수, 캐시 창 일수, Spectral 룰, lint 배선, contract Task 발행의 자동화 여부.

---

## 검토하고 버린 것

- **"비호환 변경 목록"을 ADR에 열거하는 것** — oasdiff 500여 체크·buf 규칙의 사본은 낡는 생존형 문서다(§2·§3). ADR에 담을 것은 목록이 아니라 **층위 선언과 방향성 원리**뿐이고, 목록의 진실은 도구 설정(코드)이 소유한다.
- **protobuf에 sunset custom option을 정의하는 것** — 업계 표준 부재 상태에서 자체 옵션은 그것을 읽는 자체 검사기까지 요구한다. 이 규모에서는 F1(티켓)이 같은 문제를 도구 0개로 푼다.
- **버전 병존(새 major 세우기)의 재검토** — 조사에서도 시간 기반·버전 병존의 전제(열거 불가 소비자)가 부재함이 재확인됐다. ADR-0021의 기각 논거가 강화됐을 뿐.

## 재설계 프레임 — ADR-0021을 지우고 다시 잡는다면 (후속 논의)

"ADR-0021만으로 정책이 잡히겠는가"라는 제기에서 나온 재정리. 복잡함의 정체는 항목 수가 아니라 **0021이 별개 결정 셋을 혼자 지고 있는 것**이다 — §4③ 공동무효 검사로 확인된다: 층위 선택이 뒤집혀도, 제거 게이트가 뒤집혀도 "호환 확장으로만 진화한다"는 살아 있다 → 별개 결정.

### 주축 — 구형(舊形)의 수명주기 단계

| 단계 | 담당 질문 | 상태 |
|---|---|---|
| 원천 | 계약은 어디에 사는가 | ADR-0018·0020 |
| 탄생 | 언제 합의·공표되는가 | ADR-0019 |
| **정의** | **무엇이 "호환"인가** — 층위(wire/생성 코드/semantic) + 쌍방 의무(provider 호환 확장 ↔ consumer tolerant reader·unknown enum) | **신규 ADR 후보** (조사 1-2·1-3, 보강 후보 ⓐ+ⓑ의 승격) |
| 진화 | 어떻게 바뀌는가 — breaking 금지·expand-contract·rename + 불변식의 예외(보안 강제·버그-계약) | ADR-0021 정련 (ⓒ 편입, 지금보다 얇아짐) |
| **죽음** | deprecated는 언제까지, 제거 게이트는 무엇인가 — 이벤트/시간·증명·잊힘 방지 | **신규 ADR 후보** (축 1·2, 보강 후보 ⓓ의 승격) |

- **"정의"가 독립인 이유**: "호환" 술어의 정의는 진화 규칙이 버전 병존으로 뒤집혀도 필요하다(minor 내 호환 판정은 어느 정책에서든 산다). 0021과 공동무효가 아니라 **의존**(references) 관계.
- **예외(ⓒ)가 "진화"에 남는 이유**: 불변식의 예외라서 불변식이 죽으면 함께 무의미 → 공동무효.
- **"죽음"이 독립인 이유**: 제거 게이트는 소비자 열거 가능성이라는 **자기만의 무효화 조건**을 가진다. 무효화 조건이 다르면 다른 결정이다.

### 횡단 축 — 판정 주체: 기계 / 구조 / 사람

모든 규칙은 세 지대 중 하나에 산다: ① 기계가 판정(diff 도구 — 구조적 파괴) ② 구조로 변환(rename 규약·x-sunset·contract Task — 안 잡히는 것을 잡히게) ③ 사람에게 잔여(순수 의미 변경 — 리뷰). 각 ADR이 자기 규칙을 이 지대에 명시 배치하면 "누가 지키게 하나"의 비결정이 사라진다 — §8을 결정 문서 안에서 실행하는 것.

### 축이 아닌 것

- **프로토콜(REST/gRPC)** — 원칙은 횡단한다(`260730_1620`의 ADR-α·β 판정과 동일). 갈리는 것은 도구뿐 = 코드 관할.
- **소비자 유형(웹 캐시)** — "죽음" 결정 안의 파라미터("빌드 증명이 닿지 않는 소비자에는 시간 하한") 한 조항이지 축이 아니다.
- **도구 선택** — §4① 코드 관할.

→ 이 프레임이 채택되면 위 "축 3(ⓐ~ⓓ 보강)"은 재편된다: ⓐ+ⓑ는 0021 보강이 아니라 **신규 "정의" ADR**로, ⓓ는 **신규 "죽음" ADR**로, ⓒ만 0021에 편입. 0021은 proposed라 분할 비용이 0이다.

## 열린 질문 — 사람의 것

1. **축 1**: contract 게이트를 E1(이벤트 + 웹 캐시 하한)로 확정할 것인가?
2. **축 2**: F1(contract Task 동시 발행)·F2(x-sunset+CI)·F3(소비자 lint) 중 무엇을 채택하나? (상보적 — 복수 가능. F1은 규약 문서화만으로 시작 가능, F2·F3는 각각 티켓감)
3. **축 3**: 재설계 프레임(정의/진화/죽음 3분할)을 채택할 것인가 — 채택 시 ⓐ+ⓑ는 신규 "정의" ADR, ⓓ는 신규 "죽음" ADR, ⓒ만 0021 편입. 미채택 시 ⓐ~ⓓ 전부 0021 보강(단일 ADR 유지).
4. **웹 캐시 창의 실측**: careerhub-web의 실제 번들 캐시 정책·구 번들 생존 기간을 코드·관측에서 확인하는 조사가 선행돼야 E1의 시간 하한이 수치를 얻는다 — 이 확인을 언제 하나.

## 경과 — 3분할 프레임 채택, 초안 3건 저작 (사람 지시)

재설계 프레임이 채택되어 초안이 섰다:

- **ADR-0025**(proposed, 신규) — 정의: 호환의 정의는 계약이 소유한다(생성 코드 층위 + 쌍방 의무 + 의미 잔여의 소재). ⓐ+ⓑ의 승격.
- **ADR-0021**(proposed, 정련) — 진화: 판정을 ADR-0025에 위임하고, 제거 게이트를 ADR-0026으로 넘기고, 분해의 예외(ⓒ — 보안 강제·버그-계약은 예고 후 일괄 전환)를 편입. 지금보다 얇아졌다.
- **ADR-0026**(proposed, 신규, parent: ADR-0021) — 죽음: 제거 게이트 = 이행 증명(**E1** — 빌드 증명 + 웹 캐시 경계의 시간 하한) · 잊힘 방지 = expand 머지 시 contract 티켓 동시 발행(**F1**). ⓓ의 승격.

초안이 취한 입장: 축 1은 E1, 축 2는 F1을 원칙으로(F2·F3는 보강 장치 = 코드·티켓 관할로 남김).

## 경과 2 — 세 초안 보류 판정 (2026-08-01, 사람)

초안 검토에서 **"지금 하기엔 이르다"** 판정이 내려졌다 — reject가 아니라 보류:

- **근거**: ① 결정을 강제하는 압력이 없다 — breaking 게이트가 배선되지 않았고, rename·tolerant reader 부재로 인한 실사건도 없다. 산 것이 없는데 영수증부터 끊은 모양. ② 특히 ADR-0025는 메타 프레임("정의의 소유")에 기울어 무엇을 왜 정했는지가 읽히지 않는다 — 조사 종합에서 태어난 초안의 전형적 결함.
- **처리**: 세 초안(ADR-0021 정련본·0025·0026) 모두 `proposed` 그대로 두고, 각 문서 머리에 보류·재작성 필요 멘트를 남겼다. proposed는 동결 전이므로 재작성 비용은 0.
- **재논의 트리거**: 계약 변경이 실제로 이 규약을 요구하는 시점 — breaking 게이트 배선 착수, 실제 비호환 변경의 필요, deprecated 병존의 실발생. 그때 이 문서(조사 1·2, 옵션 축, 재설계 프레임)가 재료다.
- 열린 질문 1~4는 전부 그 시점으로 이월된다.

## 다음 단계 후보 (수렴 시)

- 축 1·3 확정 시: ADR-0021 초안(proposed·가변) 보강 — ⓐ~ⓓ 중 채택분.
- F2 채택 시: api-composer에 oasdiff sunset 검사 + 잔존 스캔 스텝 Task (기존 논의의 "축 B oasdiff 게이트" 티켓과 자연 병합 — `260730_1524` §독립 축 B).
- F3 채택 시: careerhub-web에 no-deprecated lint · Go 소비자들에 SA1019 배선 Task.
- F1 채택 시: expand-contract 절차 규약을 provider repo 문서(CLAUDE.md류)에 남기는 Task — `260730_1524`의 P1 규약 문서화 Task와 한 벌.
