---
type: discussion
topic: careerhub
subjects: [grpc, protobuf, api-composer, posting-service, review-service, userinfo-service]
status: done
ref-adrs: [ADR-0018, ADR-0019, ADR-0020, ADR-0021]
---


> **결말(2026-08-01)** — 패턴의 프로토콜 횡단 일반화가 ADR-0019·0020(accept)과 ADR-0021(보류)로 갈렸고, gRPC 이행은 Feature #29와 그 아래 Task 8건으로 넘어갔다. 공표 좌표 규약(태그 prefix = 계약 디렉터리)과 계약별 모듈 입도는 Epic #28 코멘트에 확정 기록됐다.
# 계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가

## 계기와 아픔

REST 경계 논의(`260730_1524_spec-change-propagation-to-frontend.md`)에서 3층 체계 — **합의 단위**(계약 선행 머지·expand-contract·rename 규약) / **전파**(소비자 핀 범프) / **게이트**(breaking 검출·버전 강제) — 가 수렴 중이다. 이 패턴이 프론트↔백엔드에 한정될 이유가 없다는 제기: **gRPC 경계(서비스↔api-composer, 서비스↔job)에도 같은 문제와 같은 해법이 있는가.** 패턴 자체는 ADR로 고정할 만하다는 판단도 함께 제기됐다.

## 코드에서 확인한 현재

### 용어 — provider/consumer는 repo의 속성이 아니라 경계별 역할이다

**provider = 그 계약이 기술하는 동작을 구현·서빙하는 쪽**(REST·gRPC에서는 서버, 비동기 계약에서는 producer). **consumer = 그 계약으로 호출·수신하는 쪽.** 계약 테스트 진영(Pact)의 표준 어휘를 따른다. 같은 repo가 계약마다 다른 역할이다 — api-composer는 REST 계약의 provider이자 3개 서비스 proto의 consumer다. 주의: `careerhub-posting-provider`의 "provider"는 도메인 이름(공고 수집기)이고 계약 관점에서는 **consumer**(posting-service·review-service의 클라이언트)다 — ADR-β 초안은 이 어휘 충돌을 피해 정의를 명시하고 시작해야 한다.

### 경계 지도 — proto는 경계마다 사본 2부다

| provider (server) | consumer (client) | proto | 사본 상태 |
|---|---|---|---|
| posting-service | api-composer | restapi.proto | 동일 |
| review-service | api-composer | review.proto | 동일 |
| userinfo-service | api-composer | matchJob·scrapJob.proto | 동일 |
| posting-service | posting-provider (job) | provider grpc.proto | 동일 |
| posting-service | skillscanner (job) | scanner grpc.proto — `RegisterScannerGrpcServer`가 posting-service에, client가 skillscanner에 | 동일 |
| auth-service | **org 내 미확인** — 외부 소비자 또는 사장된 계약 (사람 확인 필요) | mailer user.proto (GetUserEmails) | 사본 짝 없음 |
| review-service | review-crawler (job) | crawler review.proto | 동일 |
| review-service | posting-provider (job) | provider.proto (AddCrawlingTask) | 동일 |

- **원천이 선언되어 있지 않다.** REST의 `openapi.yaml`(ADR-0018이 원천으로 선언, 백엔드 repo 소유)과 달리, proto는 양쪽 repo에 대등한 사본으로 존재하고 누가 원본인지 어디에도 없다. 생성도 각 repo가 `make proto`(protoc 수동 실행)로 따로 한다.
- **7쌍 전부 현재 동일** — drift는 아직 없다. 그러나 이는 손 복사 규율의 산물이고, drift를 감지하는 장치(REST의 CI 신선도 게이트 등가물)는 전무하다. 사본 관리의 알려진 최악 실패 모드: 양쪽이 독립 수정되어 **같은 field number를 다른 타입으로 재사용** → wire 수준 silent corruption.
- **서버들이 `Unimplemented*Server`를 임베딩한다**(`restapi_server.go:22` 등, protoc-gen-go-grpc v1.0+ 기본 요구). 함의는 아래.

### REST와의 구조 비대칭 — ⓪층(원천 선언)이 선결이다

REST는 ADR-0018이 원천을 선언한 **뒤에** 합의·전파·게이트를 논했다. gRPC는 그 전제부터 없다. 적용 층위: **⓪ 원천 선언 → ① 합의 단위 → ② 전파 → ③ 게이트.**

## 사상(mapping) — REST 체계는 거의 1:1로 이식된다

| REST 체계 | gRPC 등가물 |
|---|---|
| 스펙 PR 머지 = 합의 | proto 원천 repo PR 머지 = 합의 |
| 501 stub (손으로 작성) | **`UnimplementedXServer` embedding — codegen이 공짜로 제공.** proto에 메서드를 추가·재생성하면 서버는 무변경으로 컴파일되고 미구현 호출은 자동 `UNIMPLEMENTED`(12) |
| oasdiff breaking 게이트 | **`buf breaking`** (`bufbuild/buf-action@v1`). oasdiff의 등가 카테고리는 `WIRE_JSON`; `FILE`은 생성 코드 호환까지 보는 더 엄격한 층 |
| expand-contract | 필드: **`optional`로 추가**(proto3 explicit presence) → `[deprecated = true]` → 삭제 시 **`reserved` 번호·이름 선언**. 메서드: 추가 → deprecated → 삭제. `FIELD_NO_DELETE_UNLESS_NUMBER_RESERVED`가 절차를 기계 강제 |
| rename 규약 ("의미 바뀌면 이름 바꾼다") | **원조가 이쪽이다** — protobuf의 "field number 재사용 금지"가 같은 원리. field rename은 wire-호환이지만 JSON·생성 코드 비호환(`FIELD_SAME_NAME`이 잡음) |
| mock (Prism / MSW) | 테스트: 손 fake + `bufconn`(in-memory) 또는 grpcmock. standalone: **FauxRPC**(proto만으로 fake 서버 즉시 기동 — Prism 등가) |
| 폴링 핀 범프 (O2) | **Go는 git tag가 곧 레지스트리** — 생성 Go 코드를 commit+semver tag하면 `go get`으로 소비, Renovate `gomod` manager가 표준 지원 |

**gRPC가 유리한 지점 둘**: stub이 수작업이 아니라 codegen 기본값이고, breaking 검출이 카테고리 체계로 더 정밀하다.

**주의 지점 둘**:
- **구현 완전성의 컴파일 강제가 없다** — REST strict 인터페이스와 정반대. embedding의 대가로 미구현 메서드를 컴파일러가 못 잡고 런타임 `UNIMPLEMENTED`로만 드러난다(grpc-go #3669의 알려진 트레이드오프). 병렬 개발 중에는 이것이 원하는 성질이고, "구현 완료" 판정만 통합 테스트로 보강하면 된다.
- 클라이언트는 `UNIMPLEMENTED`가 "아직 미구현"인지 "구버전 서버"인지 구분 못 한다(REST 501과 동일한 모호성) — 소비자 배포 게이트는 여전히 사람·파이프라인의 몫.

## ⓪층 옵션 — proto 원천을 어디에 두나

### G0. 안 한다 — 사본 2부 + 손 규율 유지
7쌍 동일이 증명하듯 아직 안 터졌다. 그러나 감지 장치가 없는 채로 경계 7개가 늘어나는 중이고, field number corruption이라는 최악 실패 모드는 조용히 온다. 현상 유지의 비용은 "아직 계산서가 안 왔다"일 뿐이다.

### G1′. provider repo 소유 + nested `api/` Go module 발행 (사례 조사 후 정련형)
각 proto의 원천을 **그 계약을 구현(제공)하는 서비스 repo**로 선언하고, 소비자 사본을 없앤다:

- provider repo 안에 **별도 `go.mod`를 가진 `api/`(또는 proto/) 하위 모듈**을 두고 proto + 생성 코드를 함께 commit. **prefix 태그**(`api/v1.2.3`)로 서비스 본체와 독립 버저닝. 소비자는 그 모듈만 `go get` — 서버 의존 전체를 끌지 않는다. 실사례: **etcd**(`go.etcd.io/etcd/api/v3`, 3.5의 모듈 분할).
- 스펙 변경과 구현 변경이 **같은 repo·같은 PR** — REST spec-first에서 확보한 원자성·컴파일 구속이 그대로 유지된다.
- 전파는 REST와 동형: 소비자 go.mod 핀 + Renovate `gomod`(표준 지원) 범프 PR.
- 게이트 분산 문제는 **org 공용 reusable workflow**(`jyoliar-careerhub/.github`가 이미 있음)로 논리적 단일화 — `bufbuild/buf-action@v1` 하나가 lint·breaking(PR base 대비)을 커버, 호출 repo에는 수 줄 boilerplate.
- **알려진 함정**(Go 공식 문서·etcd 이력): ⓐ prefix 태그 누락(`go get` 실패의 최다 원인) ⓑ `replace ../api` 지시어가 소비자에 전파되지 않아 발행 파손(etcd v3.4가 이걸로 깨져 3.5 분할의 직접 동기가 됨 — `go.work`로 대체) ⓒ api 모듈이 서버 패키지를 역참조하면 분리 무의미(경계 검사는 CI 몫).
- 코드 사실: 현 proto들은 well-known(`google/protobuf/empty.proto`) 외 상호 import가 없다 — per-repo 배치의 알려진 아픈 지점(**cross-module proto 의존은 BSR을 요구**)이 현재 미해당. 공통 타입이 생기는 순간 이 전제가 무너지므로 무효화 조건감이다.

**하위 축 — 공표물이 proto인가 생성 코드인가** (REST 독립 축 A의 gRPC 버전, 논의에서 제기: "protobuf의 장점은 언어 무관성인데 go.mod로 Go 코드를 당기는 게 맞나"):

| | 생성 코드 발행 (provider CI가 생성) | proto pull + consumer 재생성 |
|---|---|---|
| 원천의 언어 중립성 | 동일 (원천은 proto) | 동일 |
| 생성기 버전 | provider가 1회 고정 — 전 소비자 동일 코드 | 소비자별 drift 위험 (OTel "생성물 무보증"의 이유) |
| 소비자 툴체인 | 불요 (`go get`) | 전 consumer CI에 protoc+plugins (현재 Go 소비자 5개 = 5벌) |
| 범프 자동화 | Renovate `gomod` 표준 | 커스텀 핀+스크립트 (표준 매니저 없음) |

**둘은 배타가 아니다** — `api/` 모듈에 proto와 생성 코드를 함께 담고 태그가 둘을 같이 공표하면: 오늘의 Go 소비자는 생성 코드를 `go get`, 미래의 비Go 소비자는 **같은 태그에서 proto를 pull해 재생성**(`buf generate`는 git remote 입력을 직접 지원). 언어 중립성은 원천·태그가 proto를 담는 것으로 보존되고, 생성 Go 코드는 그 위의 소비자 편의 파생물이다. 비Go 소비자가 늘면 언어별 파생 발행을 추가하는 것이 대형 사례들의 진화 경로(googleapis→go-genproto·PyPI, OTel→-go·-java — 재생성을 각 소비자가 아니라 언어별 발행 지점이 대신한다). REST(소비자 생성)와의 차이는 원칙 위반이 아니라 생태계별 구현 판단이다: 프로토콜 횡단 원칙은 "원천·공표물은 언어 중립 스펙"까지고, codegen 위치는 소비자 수·언어 동질성·도구 생태에 따라 갈린다.

### G2. 중앙 proto repo (전 서비스 계약을 한 repo에)
- 장점: 합의·breaking 게이트가 물리적 단일 지점, 소비자 발견성 공짜, cross-service 공통 타입 해석 단순.
- **단점 (조사에서 드러난 결정적 결함)**: ⓐ 계약 변경과 구현 변경이 **두 repo·두 PR로 갈라져 원자성이 깨진다** — 같은 PR에서 스펙↔구현을 컴파일로 묶는 현 REST 구조의 강점을 잃고, 서버가 신 계약으로 언제 따라올지 구조가 강제하지 못한다. ⓑ 중앙 repo 태그가 전 서비스 계약을 묶어 버전 입도가 거칠다. ⓒ 핵심 편익인 "중앙 리뷰 큐"는 1인 org에서 무의미 — repo +1 유지비만 남는다.
- **순수 중앙 원천이 이겼던 조건**(Lyft 중앙 IDL repo, Uber prototool): 다수 팀의 리뷰 수렴 + 모바일 등 **다플랫폼 클라이언트 생성** — 이 org에 부재. 도구 계보도 시사적이다: 중앙 repo 전용 prototool은 archive됐고, 후계인 Buf의 표준 모델은 **per-repo 모듈**("Most projects start with one module rooted at the top of a source-control repository")이다.

### G3. Buf Schema Registry (BSR)
모듈 등록·breaking 정책·generated SDK(`go get buf.build/gen/go/...`)까지 레지스트리가 담당.
- **무료 티어 제약이 실질 장벽**: private repo 1개·type(메시지+enum+RPC 합산) 100개 — 서비스 ~10개면 초과가 쉽다. 합성 버전 문자열이 사람이 읽기 어렵고 Renovate 표준 지원이 매끄럽지 않으며, 빌드가 외부 SaaS 가용성에 의존한다.
- **Buf CLI(lint·breaking·generate)는 BSR 없이 완전 동작** — "CLI 채택, BSR 보류"가 자연스러운 분리다. (참고: prototool은 2022 archive, protolock은 휴면 — 현역 표준은 Buf뿐.)
- 주의: BSR에서도 원천은 git(provider repo)이고 BSR은 발행 좌표다 — G1′과 대립하는 옵션이 아니라 G1′ 위의 발행 계층 선택지다.

### ★ 대형 "중앙 repo" 사례들의 실체 — 원천은 provider, 중앙은 파생물

중앙 계약 repo의 대표로 알려진 사례들을 조사한 결과, **저작 원천이 중앙인 경우는 드물었다**:

| 사례 | 겉보기 | 실체 |
|---|---|---|
| googleapis/googleapis | 중앙 API repo | 내부(google3) 각 팀 원천의 **Copybara export** — README부터 "copies"라 쓴다 |
| k8s.io/api | 독립 계약 repo | `kubernetes/kubernetes` staging(구현 곁)이 authoritative, **publishing-bot 미러** |
| Buf/BSR | 중앙 레지스트리 | 원천은 각 provider repo의 git, BSR은 push 대상 |
| Apollo Federation | 중앙 supergraph | 각 서비스가 subgraph 스키마 소유, 중앙은 **composition 산출물** + 검증 게이트 |
| Backstage 카탈로그 | 중앙 API 포털 | 스펙은 provider repo에, 포털은 **harvest·시각화만** |

수렴점: **"원천은 provider repo, 중앙은 파생 집계(발행·검증·카탈로그)"**. 검토 중인 원칙("스펙은 구현하는 서버가 보유")과 정확히 같은 방향이고, 중앙화의 편익(발견성·게이트)은 필요해질 때 **파생물로** 얹으면 된다 — 원천을 옮기지 않고.

이 수렴은 프로토콜 횡단으로 확인된다 — REST(Bump/Redocly "spec next to code"; GitHub·Stripe의 스펙 repo도 저작 아닌 발행 지점) · gRPC(위 표) · GraphQL(Federation: subgraph 소유 분산 + 중앙은 composition) · 비동기(producer 소유 스키마 + Schema Registry는 런타임 호환 게이트, 중앙 저작형 "canonical data model"은 안티패턴 취급 — 단 이 경계는 본격 조사 전, 비동기 계약 도입 시점에 재조사). **구조적 이유**: 중앙의 기능(발견성·게이트·발행·조합)은 전부 원천에서 파생 가능하지만, provider 소유가 주는 원자성(계약 변경과 구현 변경이 같은 PR에서 컴파일로 묶임)은 파생으로 회복 불가 — 파생 가능한 것을 중앙에, 불가능한 것을 원천에 남기면 원천의 자리는 provider로 정해진다.

**일반화의 경계 조건 (ADR-β 무효화 조건 후보)**:
1. **단일 provider가 없는 계약** — OTLP·CloudEvents 같은 표준 프로토콜은 구현이 여럿이라 중립 repo가 원천이다. β의 적용 범위는 "단일 provider가 존재하는 계약"으로 한정해야 정확하다 (careerhub는 현재 전 계약이 해당).
2. **다팀 리뷰 수렴 + 다플랫폼 대량 생성**(Lyft·Uber 조건)이 생기는 경우 — 중앙 원천의 계산이 다시 선다.
3. **공통 타입의 등장**(proto cross-import) — per-repo 배치의 전제가 무너진다 (G1′에 기술).

또한 REST 논의에서 "중앙 계약 repo"를 기각한 논거(스펙과 구속 코드의 동거가 강점, 분리는 역행)가 gRPC에서도 **그대로 유효**한 것으로 판명됐다 — G2의 결함 ⓐ가 같은 논거다. 두 경계의 결론이 일치한다: 원천은 provider repo다.

## 공표와 전달 — provider 원천에서 변경은 언제 공식화되고 어떻게 흐르나 (사례 조사)

provider 소유가 정해져도 **공표 지점**(무엇이 "계약이 바뀌었다"를 공식화하나)과 **전달 방식**(소비자가 어떻게 받나)은 별개 축이다. 프로토콜 횡단 조사(GitHub/Stripe OpenAPI · k8s/googleapis/BSR/etcd proto · Apollo Federation · Kafka Schema Registry · 패키지 생태)의 수렴점:

**공표 지점 스펙트럼** — 배포 시 ← 릴리스/태그 시 ← **[CI 발행 시 ← 머지 동기]** ← 내부 submit 동기. **다수는 "머지 후 CI가 버전드 아티팩트 발행"에 수렴**한다. 양 극단은 역할이 한정적이다:
- **배포-시 공표(런타임 endpoint·gRPC reflection·`/openapi.json`)는 어느 생태에서도 계약 전달의 정규 경로가 아니다** — 문서화·디버깅 용도로 스스로를 규정한다. 버전 좌표가 없고 공표가 배포와 원자 결합되어 "배포 전 합의"가 구조적으로 불가능하기 때문.
- Apollo는 반대 극단의 주의 사례: **"배포 성공 후에만 publish"를 명문화**한다 — registry(Uplink)가 router의 **런타임 라우팅을 구동**하므로, 미배포 스키마를 공표하면 미구현 필드로 라우팅된다. 여기서 일반 원리가 나온다: **공표물이 런타임을 구동하면 공표는 배포 뒤여야 하고, 빌드만 구동하면(모듈·스펙) 합의 시점 공표가 안전하다.** careerhub의 공표물(스펙·생성 코드 모듈)은 전부 빌드 타임 소비라 후자다.
- **후속 조사 — "런타임 구동 공표"는 필연이 아니라 선택이다** (ADR-0019 심사 중 제기: 그런 구조가 시스템에 추가될 수 있으니 Decision에 예외를 둘 것인가 → 두지 않기로).
  Apollo 사례의 재판정: Uplink는 federation의 구조적 필연이 아니다 — `rover supergraph compose`(빌드 타임 정적 조합) + `--supergraph` 파일이 1급 경로이고, Apollo 스스로 blue-green에서 "immutable schemas within each Docker image"를, air-gapped에서 로컬 파일을 권한다.
  Uplink의 정당 조건도 Apollo가 명시한다: 스키마 팀이 인프라 배포 권한이 없는 조직 — 관리형 편의다.
  Confluent조차 런타임 스키마 등록을 비권장하고("schemas should be managed via a CI/CD pipeline... read-only access") Avro의 런타임 fetch는 인코딩 형식 선택의 하류다(protobuf는 불요).
  실패 모드는 일관된다: 캐시 폴백은 정상 운영만 덮고 **cold start × control plane 장애의 곱사건**에서 무너진다(router 기동 시 Uplink 불가 이슈 실보고) — AWS static stability 원칙이 금지하는 바로 그 모양.
  정밀화: 표적은 "런타임 pull 일반"이 아니라(GitOps도 pull이다) **비버전드 latest 포인터에 대한 기동 경로 임계 의존**이다.
  진짜 불가피한 부류는 계약이 배포 산출물이 아니라 **사용자 데이터**인 플랫폼(서드파티 스키마 업로드)뿐이며, 이 org에서는 공집합.
  → ADR-0019는 예외 없이 양성 서술로 닫고, Context에 "왜 예외가 없는가"를 기록했다.

**전달 방식** — **압도적 다수가 빌드 타임 pull**(go module·npm·buf.lock + Renovate/Dependabot 폴링 PR). **registry가 소비자에게 push하는 webhook 전달은 어느 생태에도 존재하지 않는다** — webhook/dispatch가 보이는 곳은 전부 provider 측 발행 파이프라인 내부이거나 사람용 알림이다. 런타임 fetch가 정규 전달인 유일한 예외는 Kafka Schema Registry(schema id 기반 deserialize fetch). 그리고 신뢰 경계마다 **사람 머지 게이트**(bot PR을 사람이 머지)가 반복 등장한다 — REST 논의의 "자동 PR, 수동 머지" 선과 일치.

**합의(구현 전) 시점 공표를 구조적으로 지원하는 사례는 3개뿐**: Buf BSR(공표=머지 동기, 스키마 repo 분리 가능), Kafka CI pre-register(Confluent 권장 모드 — 구현 전 등록 + `use.latest.version` 역구속), googleapis(공표 트리거가 배포가 아닌 정의 submit). 공통 조건: **계약이 구현에서 생성되지 않는 독립 원천 + 배포와 무관한 자체 공표 좌표.** 계약이 코드에서 생성되는 순간(FastAPI·Stripe·GitHub·reflection) 공표는 구조적으로 구현 뒤로 밀린다 — **careerhub는 ADR-0018(spec-first)로 이 조건을 이미 갖췄다.** 합의 선행 머지(P1·G1′)가 가능한 것은 그 결정의 직접 배당이다.

**careerhub 사상**: 공표 지점 = **원천 repo main 머지**(합의)와 **prefix 태그**(`api/vX.Y.Z`, 소비 좌표) · 전달 = go module/스펙의 **빌드 타임 pull + 봇 범프 PR + 사람 머지** — 업계 수렴점과 정확히 일치하고, REST discussion의 O2 선택을 독립적으로 재확인한다.

**"pull"의 정확한 의미** (논의 중 확인한 오해 소지): consumer가 당기는 것은 가변 원천(main HEAD)이 아니라 **불변 공표물(태그/버전)** 이고, 동작은 둘로 분리된다 — ① 감지·범프: consumer 측 봇이 새 태그를 발견하면 **핀(go.mod 버전) 범프 PR**을 열고 사람이 머지 ② 빌드: 커밋된 핀이 가리키는 버전만 결정론적으로 내려받음. Go는 provider repo의 git 태그가 곧 레지스트리라 물리적으로는 "provider에서 직접" 받지만, 논리적으로 main은 provider의 작업 공간이고 태그가 "소비 가능" 공표다. consumer는 어느 버전에 언제 올라탈지를 핀으로 스스로 선택한다 — 빌드 재현성과 탈결합이 여기서 나온다.

```
posting-service repo (provider)
 ├─ api/            ← 원천: proto + 생성 코드 (별도 go.mod)
 └─ tag api/v1.4.0  ← 공표물: 불변 좌표
        ↑ ①Renovate가 발견 → api-composer에 핀 범프 PR (사람 머지)
        ↑ ②api-composer 빌드가 go.mod 핀 버전을 go get
```

**이중 태그 구조의 REST 이식** (논의에서 제기): 계약 공표 태그와 앱 빌드 태그는 네임스페이스로 분리 공존한다 — gRPC `api/vX.Y.Z` = REST **`spec/vX.Y.Z`**(provider CI가 openapi.yaml 변경 머지 시 `info.version`에서 태그명을 파생해 자동 생성). 이것이 REST discussion 축 C의 두 결손을 동시에 닫는다: 주소성(버전→태그→내용)과 불변 강제(버전 미범프 스펙 변경 → 태그 중복으로 CI 실패). consumer 폴링도 "파일 SHA 감시"가 아니라 "새 `spec/*` 태그 감시"로 단순화 — 감지 대상이 공표 행위가 된다. 기존 빌드 트리거(`v*`)와는 불교차(`api/`·`spec/`는 `v`로 시작하지 않음).

**빌드의 계약 출처 명시(provenance)** (논의에서 제기 — "앱 빌드 태그에 어떤 원천으로 빌드됐는지 코드 외적으로 명시"):
- **⓪ 내장 — 이미 공짜다**: provider 앱은 태그 커밋 트리에 스펙이 들어 있고(같은 repo 소유의 배당), Go consumer는 바이너리에 의존 모듈 버전이 내장된다(Go 1.18+, `go version -m <binary>` → `.../api v1.4.0`) — 산출물 자체가 증언하며 거짓말이 불가능하다.
- **① 표기 채널** (반드시 CI가 ⓪에서 파생 생성 — 손 표기는 거짓말할 수 있는 주장): annotated tag 메시지 · GitHub Release 본문 · 커밋 trailer(googleapis `PiperOrigin-RevId` 패턴) · **OCI 이미지 label**(배포 아티팩트가 직접 들고 다님 — 실행물에 가장 가까움) · build attestation(서명 증명 — 이 규모엔 과함).
- 원칙은 §8과 동형: 내장이 진실, 표기는 파생 뷰. 실용 조합은 ⓪ + OCI label + tag 메시지.

## ADR 입도 — 무엇이 얼 것인가 (공동무효 판정)

- **ADR-α (패턴 원칙)**: 초안 심사 중 **두 건으로 분리됐다** — ①(선합의 공표)과 ②③(호환 진화)은 독립적으로 뒤집힐 수 있어 공동무효가 아니라는 판정(사람). 표현도 교정됐다: 업계 규범 문서(Zalando [106]·AIP-180·GraphQL)는 예외 없이 "**breaking 금지 불변식 + 호환 확장**" 문형이고, "파괴적 변경을 분해한다"는 메커니즘 층(Fowler ParallelChange)의 어휘다. Zalando가 명문화한 구분 채택: **incompatible = 스키마 delta의 속성, breaking = 운영 배포되어 소비자를 깬 사건** — 금지 대상은 후자.
  - **ADR-0019** — 계약 합의는 구현 완료 전에 공표한다(공표 = 원천 머지). references: ADR-0018.
  - **ADR-0021** — 계약은 호환 확장으로만 진화한다(파괴 금지 · 비호환은 expand→migrate→contract 분해 · 의미 변경은 rename). references: ADR-0014, ADR-0018.
- **ADR-β (배치 원칙)**: *"계약 스펙의 원천은 그 계약을 구현(제공)하는 서비스의 repo에 둔다"* — **전 프로토콜 공통**(REST·gRPC·향후 비동기 등). 논의 중 확인된 사실: ADR-0018은 spec-first(원천을 독립 명세에)를 정했을 뿐 **명세가 어느 repo에 사는가는 정한 적이 없다** — `openapi.yaml`이 api-composer에 있는 것은 구현 판단이었다. β는 그 배치를 원칙으로 승격하는 것이며, gRPC 전용 결정이 아니라 0018을 보완하는 횡단 원칙이다. α가 유효한 채로 β만 뒤집힐 수 있고(중앙 원천으로 이행 등), 그 역도 성립 → **별개 ADR**. nested 모듈·태그 방식·발행 계층(BSR 여부)은 β의 관할이 아니라 구현 판단.
- **도구 선택**(Buf CLI, Renovate, FauxRPC, buf breaking 카테고리)·배선 순서는 티켓·코드의 관할 — ADR에 담지 않는다.

## 열린 질문 — 사람의 것

1. **⓪층 선택**: 사례 조사 후 G1′(provider 소유 + nested api 모듈)로 무게가 실렸다 — 사람이 검토하던 방향("스펙은 구현하는 서버가 보유")과 조사의 수렴점이 일치한다. G2는 원자성 결함·1인 org 편익 부재로, G3는 무료 티어 제약으로 후순위. 이 기울기를 확정할 것인가?
2. **ADR-α·β 초안 착수**: 둘 다 프로토콜 횡단 원칙으로 정리됐다. β(배치)는 방향이 사실상 정해졌고, α(변경 규약)는 REST discussion과 이 문서가 재료다 — 초안을 쓸 시점인가.
3. **이행 순서**: REST 경계(#12 계열)를 먼저 굳히고 gRPC는 후행? 아니면 α·β를 공통 원칙으로 세우고 양쪽을 병행?
4. **사실 확인 잔여**: ~~skillscanner 경계의 방향~~(해소 — posting-service가 provider). auth-service mailer proto의 소비자는 org 참조 저장소에 없음 — **외부 소비자인가 사장된 계약인가, 사람의 기억이 필요하다.**

## 다음 단계 후보 (수렴 시)

- ADR-α(변경 규약)·ADR-β(배치 원칙) 초안(`proposed`) — 이 문서와 REST discussion이 Context의 재료다.
- G1′로 수렴하면: β accept 후 이행 Epic — provider별 `api/` 모듈 분리·prefix 태그·소비자 사본 제거→go.mod 전환·공용 buf-action reusable workflow(`jyoliar-careerhub/.github`)·Renovate 배선.
- 발견성이 아파지면(후일): 파생 카탈로그(Backstage 류)를 얹는다 — 원천은 옮기지 않는다.
