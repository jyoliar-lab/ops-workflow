---
type: discussion
topic: careerhub
subjects: [openapi, grpc, protobuf, api-composer, posting-service, review-service, userinfo-service]
status: done
ref-adrs: [ADR-0019, ADR-0020, ADR-0021, ADR-0026]
---


> **결말(2026-08-01)** — 런타임 어긋남의 방어를 **소비자 배포 게이트 한 자리**로 수렴시켰다(501 stub 유지 · 소비자 코드 무변경 · provider 릴리스 무차단). 임계선(§4②)에 못 미쳐 ADR로 세우지 않고 티켓으로 넘긴다 — 되돌리는 데 한 시간이면 되는 스크립트다. (b) 구형 제거의 방어는 보류 중인 ADR-0021·0026 벌의 관할로 남는다.
# 런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가

## 아픔 — 빌드 타임 구속이 보증하지 않는 것

ADR-0020의 핀 결합과 생성 코드는 **"소비자가 어느 계약으로 빌드됐나"** 만 보증한다.
**"지금 떠 있는 provider가 그 계약을 서빙하나"** 는 아무것도 보증하지 않는다.

게다가 ADR-0019가 "공표됐으나 미구현"을 정상 상태로 만들었으므로, 이 어긋남은 사고가 아니라 **설계된 상태**다.
어긋남의 세 시나리오:

- **(a)** consumer가 새 계약 핀으로 배포됐으나 provider의 구현·배포가 아직 — ADR-0019가 만드는 정상 상태
- **(b)** provider가 구형을 제거 배포했으나 consumer가 아직 구형 사용 — 보류 중인 ADR-0026(제거 게이트)의 영역
- **(c)** 롤백으로 provider가 과거 버전으로 되돌아감 — 순서로 풀 수 없는 사건

## 조사에서 얻은 핵심 — 순서에는 일반해가 없다

업계에서 이 문제는 **deployment ordering constraint**(lockstep deployment)로 불린다.
결정적 통찰: **단일한 순서 규칙이 존재하지 않는다** — 순서는 변경의 *방향*에 따라 뒤집힌다.

Confluent가 이를 가장 명시적으로 정식화했다: BACKWARD 호환 변경은 consumer 먼저, FORWARD 호환 변경은 producer 먼저, FULL 호환이면 *"upgrade consumers and producers independently in any order"*.

통합하면 — **능력을 더하는 쪽이 먼저 배포되고, 능력을 빼는 쪽이 마지막에 배포된다.**
(a)는 provider 먼저, (b)는 consumer 먼저다.
(c)는 순서 규칙으로 풀리지 않는다 — 롤백은 순서를 사후에 위반하는 사건이다.

그래서 업계의 지배적 답은 순서 강제가 아니다.
Fowler의 Parallel Change 원문이 직접 말한다: *"it can also remove the need for complex deployment orchestration of different services due to version dependencies between them."*
AIP-180은 규범으로 못박는다: *"Old clients must be able to work against newer servers."*

**즉 (a)와 (c)는 호환 규율로 소거되고, 호환으로 소거되지 않는 잔여는 (b) 하나뿐이다.**

## 코드에서 확인한 현재

**① 배포 순서 장치는 이미 있는데, 계약 의존을 담고 있지 않다 — 그리고 그것이 옳다.**
`jyoliar-k8s`의 ArgoCD ApplicationSet이 RollingSync 3단계로 배포한다: phase 1(gateway·secrets) → phase 2(review·posting·userinfo gRPC · api-composer · frontend · auth) → phase 3(jobs).
provider 3개와 consumer(api-composer·frontend)가 **같은 phase 2**에 있다 — 순서가 계약 방향으로 서 있지 않다.
조사 결과에 비추면 이것은 결함이 아니라 정상이다: 서비스 간 계약 순서를 sync wave로 강제하는 것은 독립 배포성을 깨고(microservices.io: *"they're not independently deployable—you've recreated the release coordination overhead of a monolith"*), 롤백을 막지 못하며, 방향 의존적 순서를 정적 wave로 표현할 수 없다.
sync wave는 인프라 계층 순서(CRD·DB migration)의 도구다.

**② 배포된 버전이 전부 git에 있다 — 어긋남이 계산 가능하다.**
`kustomization.yaml`이 `newTag: v0.3.0` 식으로 실제 떠 있는 이미지 버전을 GitOps 저장소에 핀한다.
그러면 사슬이 전부 git에서 해석된다: GitOps repo가 각 서비스의 배포 버전을 말하고 → consumer repo의 그 태그에서 go.mod가 요구 계약 버전을 말하고 → provider repo의 그 태그에서 계약 모듈의 버전이 나온다.
**브로커도 런타임 조회도 없이 git 사실만으로 "지금 떠 있는 조합이 정합한가"를 판정할 수 있다.**

**③ 없는 것**: api-composer·posting-service 어디에도 health/readiness 엔드포인트가 없다 — 런타임에 "나는 어느 계약을 서빙한다"를 말하는 채널이 현재 0이다.

## Pact `can-i-deploy` — 정식 해법과, 우리에게 이미 있는 등가물

이 문제의 업계 정식 해법은 Pact 브로커의 `can-i-deploy`다.
정적 호환성 검사가 아니라 **"현재 그 환경에 실제로 떠 있는 버전 조합"** 에 대한 질의라는 점이 핵심이다 — *"all the versions of the integrated applications that are already in that environment"*.
환경의 실상은 `record-deployment`가 유지하고, 롤백도 같은 호출로 반영한다.
덤으로 Pact에는 **pending pacts**가 있다 — *"the contract will change to express the desired functionality before the implementation exists in the provider"* — ADR-0019의 "공표됐으나 미구현"과 정확히 같은 개념을 1급 상태로 모델링한 것이다.

브로커가 제공하는 것은 결국 셋이다: ⓐ 소비자 등록부 ⓑ 환경별 실배포 버전 레지스트리 ⓒ 둘을 조회하는 배포 전 게이트.

**그런데 careerhub에서는 ⓐ가 이미 무료다.**
Pact가 브로커를 필요로 하는 이유는 소비자의 기대가 *코드에 없고* 런타임 행동에만 있기 때문인데, ADR-0020의 핀 결합 덕에 **go.mod가 곧 소비자 등록부**이기 때문이다.
그리고 ⓑ는 위 ②로 GitOps 저장소가 이미 갖고 있다.
**남는 것은 ⓒ(대조 스크립트) 하나뿐이다.**

Pact 공식 문서의 적합 조건(양쪽을 같은 조직이 개발 · 소비자 수가 적어 개별 관리 가능)은 우리가 전부 만족하지만, 부적합해서가 아니라 **중복이어서** 브로커를 들이지 않는다 — 게다가 브로커는 SPOF이자 상시 운영물이고, `record-deployment` 호출 누락 시 **틀린 근거로 green을 주는** 실패 모드를 갖는다.

## 옵션

### R0. 안 한다 — 호환 규율만 믿는다
(a)(c)는 호환으로 소거되고 (b)는 사람이 조심한다.
이기는 조건: 계약 변경이 드물고 소비자가 손에 꼽힐 때 — 지금이 그렇다.
지는 조건: 어긋남이 실제로 나도 **알 방법이 없다**. 조용히 화면이 비는 것으로만 드러난다.

### R1. 무해화 — consumer가 미구현을 정상 경로로 처리 (호환 축의 완성)
gRPC `UNIMPLEMENTED`·REST 501을 에러가 아니라 "그 기능 아직 없음"으로 처리하고, 신기능 호출은 feature flag로 게이팅한다.
선례가 gRPC 자신에게 있다 — health check가 *"unless the call fails with the status UNIMPLEMENTED, in which case health checking will be disabled"* 로 동작한다.
feature flag는 **배포 순서 문제를 런타임 토글로 옮기는** 표준 기법이라 (c)에도 강하다 — 끄면 즉시 복구.
**★ 기각됨** — 아래 "재교정" 절 참조. 한때 ADR-0019의 짝으로 지목했으나, 관행에 반하고 애초에 필요하지도 않은 것으로 판정됐다. 롤백 대비 안전망으로서의 잔여 가치만 남는다.

### R2. 사후 검출 — 관측 (거의 무료)
`grpc_code="Unimplemented"` 카운터와 HTTP 501 카운터에 알림을 건다 — (a)가 실제로 발생 중이라는 직접 신호다.
Go 바이너리는 `debug.ReadBuildInfo()`로 **자기가 어느 계약 버전으로 빌드됐는지 이미 알고 있다**(go.mod 핀이 내장된다) — 노출만 하면 된다.
OTel `service.version` + RPC span의 `rpc.service`를 조합하면 "어느 버전의 consumer가 어느 provider의 어느 메서드를 부르는가"의 실측 그래프가 나온다.
한계: 사후적이고, 호출이 없는 콜드 패스의 불일치는 트래픽으로 영원히 안 보인다.

### R3. 브로커 없는 `can-i-deploy` — git 매트릭스 × 배포 상태 대조
consumer repo들의 go.mod에서 `consumer → 계약 → 요구 버전` 매트릭스를 생성하고(⓪ 소비자 등록부), GitOps repo의 배포 태그에서 provider의 서빙 계약 버전을 얻어(⑤ 환경 레지스트리), **"요구 버전 ≤ 서빙 버전"을 검사**한다.
exit 1이면 배포가 막힌다 — 이 저장소의 §8("규율이 아니라 구조로 강제한다")과 정합.
(a)(b)(c) 전부를 덮고, 특히 **(c)의 유일한 방어**다: 여기서 **롤백 하한(rollback floor)** — provider가 되돌아갈 수 있는 최저 버전 = 살아 있는 consumer들의 요구 버전 최댓값 — 이 계산되므로, 롤백 판단이 추측이 아니라 조회가 된다.
비용: 스크립트 하나 + CI 배선. 전제: ADR-0020 이행(#29 계열)이 끝나 go.mod 핀이 실재해야 한다.

### ★ R3의 결함과 교정 — 버전 비교는 거짓 green을 준다

논의에서 제기된 반증: consumer가 새 연산을 구현·배포했는데 provider가 **경로는 열어둔 채 501**이면, R3의 "요구 버전 ≤ 서빙 버전" 비교는 통과한다.
원인은 명확하다 — **공표 좌표는 하나인데 알아야 할 사실은 둘이다.**
계약 태그는 *"계약에 이 연산이 있다"* 만 말하고 *"그 연산이 서빙된다"* 는 말하지 않는데, ADR-0019가 그 둘을 의도적으로 분리해 놓았기 때문이다.
즉 R3의 원안은 0019가 만든 구간을 못 보는 검사였다.

**교정 — 좌표를 둘로 가른다.**

| 좌표 | 언제 오르나 | 무엇에 쓰나 |
|---|---|---|
| **합의(agreed)** = 현행 계약 태그 | 명세 머지 시(ADR-0019) | **빌드 핀** — 미구현이어도 결합해 병렬 개발 |
| **서빙(served)** | 그 버전의 전 연산이 구현되었음이 **증명될 때** | **배포 게이트** — consumer 요구 ≤ served |

두 좌표의 간격이 곧 "공표됐으나 미구현" 구간이다 — 0019가 정상이라 선언한 그 구간.
이 분리는 0019의 병렬 개발을 훼손하지 않는다: **개발은 agreed로, 배포는 served로.**

**서빙 좌표는 주장이 아니라 도출이어야 한다** — 사람이 "구현 끝났다"고 선언하면 거짓말할 수 있는 라벨이 하나 더 늘 뿐이다(축 C의 `info.version`이 그랬듯).
코드에서 도출 가능성을 확인했고, 프로토콜별로 방식이 갈린다:

- **gRPC — 호출 순회가 성립한다.** `ServiceDesc`에 전 메서드가 열거되어 있고, `UNIMPLEMENTED`는 **요청 검증 이전 라우팅 계층**에서 반환되므로 빈 요청으로도 판정이 정확하다.
- **REST — 호출 순회는 안 된다.** 내장 명세 검증 미들웨어가 먼저 돌아 501에 닿기 전에 400이 난다.
  대신 stub을 공용 헬퍼로 통일해 **미구현 집합을 코드가 스스로 등록**하게 하면 요청 구성 없이 열거된다.
  연산 전수는 `GetSpec()`이 주고, 내장 명세를 읽어 코드와 대조하는 선례가 이미 있다(`test/controller/spec_parity_test.go`).

**남는 한계 둘:**

- **입도.** 버전 단위 served는 부분 구현을 표현하지 못한다 — 5개 중 3개만 구현되면 그 3개만 쓰는 consumer도 막힌다.
  정밀하게 하려면 **연산 단위 매니페스트**가 필요하고, 이것이 정확히 Pact matrix가 하는 일이다(interaction 단위 검증 결과).
  **순진한 버전 비교가 실패하고 Pact가 성공하는 이유가 이 입도 차이다.**
  현 계약 크기에서는 버전 단위로 시작하고, 막히면 연산 단위로 내려간다.
- **"구현됐지만 틀림"은 못 잡는다.** 501은 아닌데 응답이 엉뚱한 경우 — 어떤 버전 체계도 못 잡으며 계약 테스트의 영역이다. 백스톱은 R2.

### ★★ 재교정 (1차) — 소비자는 미구현을 보고 분기하지 않는다 (R1 기각)

R1에 대한 반론: *"내부 서비스에서 소비자가 provider의 구현 여부에 따라 동작을 바꾸는 것은 이상하다."*
조사 결과 **반론이 맞고 R1은 기각된다.**

- **graceful degradation의 대상은 장애지 미구현이 아니다.** AWS Well-Architected REL05-BP01은 전편이 *unhealthy·unavailable·failure modes*만 다루며 미구현 사례가 없고, *"Generally, fallback strategies should be avoided"* 라고 경고한다.
- **Docker/k8s의 버전 협상은 통제 밖 다중 버전 전제**이며, 그들도 **discovery로 존재를 확인**하지 에러 코드로 capability를 추론하지 않는다 — R1은 그 사례들의 구조조차 따르지 않았다.
- **RFC 9413**: 소비자 측 우회는 문서화·제거 계획·신속한 되돌림이 붙어야 정당하다. 무기한 유지되는 degrade 분기는 테스트되지 않는 죽은 경로가 된다.
- **Pact도 같은 방향** — 소비자를 degrade시키지 않고 **소비자 배포를 차단**하며, "공표됐으나 미구현"을 *정상*이 아니라 **`pending`이라는 별도 상태**로 격리한다.
- **소비자의 병렬 개발 상대는 provider가 아니라 spec 생성 mock일 수 있다.** Prism: *"Mock servers serve as a tool for API consumers to write integration code for an API that doesn't exist yet."*

### ★★★ 재교정 (2차) — 그러나 501 자체는 남는다 (과잉 적용의 철회)

1차 교정 직후, 조사의 "미구현은 부재로 격리한다"(k8s alpha의 404, Fowler keystone)를 근거로 **미구현 연산을 배포 표면에서 제외**하는 안을 세웠다.
**이것은 과잉 적용이었고 철회한다.**

- 조사가 지지한 명제는 *"소비자가 501을 보고 **분기**하면 안 된다"* 이지 *"501이 **존재**하면 안 된다"* 가 아니다. 둘은 다른 주장이고 후자의 근거는 없었다.
- 인용했던 "부재" 사례들은 성립 조건이 다르다: k8s alpha API는 **영영 채택되지 않을 수도 있는 opt-in 기능**의 격리이고, Fowler의 keystone은 **최종 사용자에게 반쯤 만든 UI를 감추는 것**이다.
  이 경우는 내부 계약이고, 소비자가 조직 자신이며, 호출 시점을 통제할 수 있다.
- 표면 제외는 **명세 ≠ 서빙 명세**라는 이중 산출물과 필터 기제를 요구하고, "미구현 목록"이 현실과 drift할 여지를 새로 만든다.
- 반면 **501은 자기 기술적이다** — 별도 목록 없이 배포된 서버가 스스로 "이 연산은 아직"이라고 답한다. 목록과 현실의 drift가 원천적으로 없다.
  gRPC `UNIMPLEMENTED`는 정의가 이에 정확히 부합한다(*"not implemented or is not supported/enabled in this service"*).
  HTTP 501의 RFC 의미는 더 좁지만(*"coming soon"용이 아님*), 내부 계약에서 실질 문제는 아니다.
- 그리고 **"명세의 전 연산이 구현되어야 배포 가능"은 spec-first를 실행 불가능하게 만든다** — 명세 선행 머지의 이점을 그대로 지운다.

### ✔ 수렴 — 게이트는 소비자 배포 한 자리에만 둔다

| 단계 | 규칙 |
|---|---|
| 명세 머지 | 스펙 + 501/`UNIMPLEMENTED` stub → 소비자는 타입 생성해 즉시 개발 시작 (ADR-0019 그대로) |
| provider 릴리스 | **막지 않는다** — A/B 시나리오(무관한 미구현이 긴급 릴리스를 인질로 잡는 것)가 발생하지 않는다 |
| 소비자 코드 | **분기 없음** — 연산이 동작한다고 가정하고 작성 (1차 교정의 요지) |
| **소비자 배포** | **게이트: 호출하는 연산이 배포된 provider에서 미구현이 아닌가** — 유일한 검사 지점 |
| 운영 | 501/`UNIMPLEMENTED` 카운터 = 게이트를 빠져나간 어긋남의 신호 |

게이트가 한 자리에만 서고, 나머지는 전부 기존 구조 그대로 흘러간다.
소비자 코드는 분기하지 않고 **파이프라인이 막으므로**, 1차 교정(소비자 분기 금지)과 충돌하지 않는다.

**남는 구현 판단**: "소비자가 부르는 연산 집합"의 도출(생성 클라이언트 메서드 참조의 정적 훑기 vs 소비자 선언)과, "provider의 미구현 집합"의 조회(배포 인스턴스 probe vs 빌드 시 도출).
gRPC는 `UNIMPLEMENTED`가 요청 검증 이전 라우팅 계층에서 반환되므로 probe가 정확하고, REST는 검증 미들웨어가 먼저 돌아 probe가 어렵다 — 후자는 stub 헬퍼를 통일해 빌드 시 집합을 도출하는 편이 낫다.

### R4. 런타임 확인 — 기동 시 provider 계약 버전 조회
health/version 엔드포인트를 만들고 consumer가 기동 시 대조한다.
**fail-fast는 안티패턴이다** — 의존 서비스 확인을 기동 필수 조건으로 걸면 provider가 잠깐 못 뜰 때 모든 consumer가 CrashLoopBackOff에 빠지는 cascading failure가 된다.
이것이 "control plane in the data path"의 구체형이고, ADR-0019 심사에서 기각한 그 구조와 같은 계보다.
쓴다면 **죽지 않고 메트릭·로그만 남기는** 형태(R2로 수렴).
gRPC server reflection을 이 채널로 승격하는 것도 기각 — 프로덕션 비활성이 보안 권고의 지배적 입장이다.

## 검토하고 버린 것

- **ArgoCD sync wave / Flux dependsOn으로 서비스 간 계약 순서 강제**: 독립 배포성 파괴 · 롤백 무방비 · 방향 의존적 순서를 정적 wave로 표현 불가 · 계약이 늘 때마다 GitOps 매니페스트 수정.
  현재 phase 구성(provider와 consumer가 같은 phase)을 계약 방향으로 재배열하려는 유혹이 있으나, 조사는 그것이 오답이라고 말한다.
- **Pact 브로커 도입**: 주된 가치(소비자 등록부)가 go.mod와 중복 · SPOF · 상시 운영물 · contract test 저작 비용 · OpenAPI와 Pact JSON의 이중 진실.
- **기동 시 fail-fast**: 위 R4.
- **프로덕션 gRPC reflection을 계약 확인 채널로**: 보안 권고 충돌.

- **"미구현 stub의 프로덕션 노출"을 정상 운영으로 수용하는 것**(R1의 전제): 권장하는 1차 자료가 없고, spec-conformance 도구가 기본값으로 반대하며(Schemathesis), 501의 표준 의미와도 어긋난다.
  대안(mock으로 병렬 개발 · 표면에서 부재)이 같은 목적을 더 싸게 달성한다.
- **완성도로 provider 릴리스를 막는 것**: A/B 시나리오에서 무관한 작업이 서로를 막는다.
  단 "게이트를 CI 계약검증에 두는 것" 자체는 실재하는 관행이다(Specmatic coverage가 미구현 엔드포인트로 빌드를 실패시킨다) — 기각하는 것은 **릴리스 단위의 전면 차단**이지 검사 자체가 아니다.

## ★ 드러난 공백 — ADR-0019의 짝이 빠져 있다

조사가 짚은 문장: *"계약 합의가 구현 전에 공표된다는 전제는, consumer가 미구현을 정상 처리한다는 전제와 짝을 이룰 때만 성립한다. 짝이 없으면 그 설계는 배포 순서 강제를 암묵적으로 요구하게 된다."*

ADR-0019(accepted)는 "공표됐으나 미구현이 정상 상태"라고 선언했고 Consequences에 *"소비자는 미구현 신호를 만날 수 있고 … 구현 완료의 판정은 확인의 몫으로 남는다"* 까지 적었다.
그러나 **소비자가 그 신호를 어떻게 다뤄야 하는가는 어디에도 없다.**
소비자가 미구현을 치명적 오류로 다루면 0019의 병렬 개발은 성립하지 않고, 우리는 (a)를 피하기 위해 배포 순서를 강제하게 된다 — 방금 오답으로 판정한 그것을.

**단 그 짝이 무엇인지는 논의 중 두 번 바뀌었고, 최종형은 소비자 측 하나다.**

- 1안 "소비자가 미구현을 정상 경로로 처리한다"(R1) — 기각(1차 재교정).
- 2안 "미구현 연산을 배포 표면에서 제외한다" — 철회(2차 재교정). spec-first의 이점을 지우고 drift 여지를 새로 만든다.
- **최종**: 소비자 코드는 아무것도 하지 않는다(분기 없음). 대신 **소비자 배포가 게이트를 지난다** — 호출하는 연산이 배포된 provider에서 미구현이 아닐 때만 배포된다.

> **ADR-0019의 빠진 짝 = "소비자는 자신이 호출하는 연산이 실제로 서빙될 때만 배포된다."**
> 코드가 분기하는 것이 아니라 파이프라인이 막는 것이므로, 소비자 구현에는 아무 제약도 걸리지 않는다.
> provider 측에는 새 의무가 없다 — 501/`UNIMPLEMENTED` stub이 이미 그 사실을 자기 기술적으로 말한다.

**판정(사람): ADR이 아니라 티켓이다.**
배포 전 검사 스크립트 하나이고, 틀리면 지우면 되며(임계선 §4② 미달), 다른 결정이 인용할 근거도 아니고, 소비자 코드에 제약도 걸지 않는다.
"0019가 ADR이니 그 짝도 ADR"이라는 추론이 잘못이었다 — 0019는 공표 시점의 *의미*를 정한 one-way door였지만, 거기서 파생되는 확인 절차는 운영 안전장치다.
0019 자신도 *"구현 완료의 판정은 컴파일이 아니라 확인(테스트·사람)의 몫으로 남는다"* 라고 적어 **결정 모양이 아니라 구현 모양의 구멍**을 남겼다.

## 머지는 배포가 아니다 — 코드에서 확인

api-composer의 배포에는 사람의 두 행위가 필요하다: `v*` 태그 push(`create-tag.yaml`이 ECR 이미지 빌드)와 GitOps `newTag` 변경(ArgoCD 배포).
**main 머지만으로는 아무것도 배포되지 않는다.**
따라서 "공표됐으나 미구현" 구간은 git(main) 안에 사는 것이지 프로덕션에 사는 것이 아니며, 0019가 그 노출을 강제한 적도 없다.
이것은 trunk-based development의 표준 성질이기도 하다 — *"separating [feature] release from [code] deployment"*.
다만 A/B 시나리오가 보여주듯 **"릴리스 시점의 main에는 미구현이 섞여 있을 수 있다"** 는 남는다 — 그래서 표면 제외(위)가 필요하다.

## 열린 질문 — 사람의 것

1. ~~위 공백의 처리~~ — **해소: 티켓이다**(위 판정). Epic #28 아래 리프로 발행하면 된다. 근거 ADR 명시는 선택(ADR-0019 이행 추적용).
2. **게이트의 두 재료를 어떻게 얻을 것인가** — ⓐ "소비자가 부르는 연산 집합"(생성 클라이언트 메서드 참조의 정적 훑기 vs 소비자 선언) ⓑ "provider의 미구현 집합"(배포 인스턴스 probe vs 빌드 시 도출).
  gRPC는 `UNIMPLEMENTED`가 라우팅 계층에서 나므로 probe가 정확하고, REST는 검증 미들웨어가 먼저 돌아 probe가 어렵다 — 후자는 stub 헬퍼를 통일해 빌드 시 도출하는 편이 낫다.
4. **`require_unimplemented_servers=false`** — Go/gRPC에서 컴파일러를 완성도 게이트로 쓸 것인가.
  ADR-0020으로 계약과 구현이 같은 저장소이므로, 켜면 명세만 머지할 때 빌드가 깨진다 — ADR-0019(합의 선행 머지)와의 긴장을 어떻게 다룰지가 선결.
5. **R2(관측)의 최소 조합** — `UNIMPLEMENTED`/501·404 카운터만으로 시작할 것인가. 홈랩 관측 스택에 이미 무엇이 있는지가 입력.
6. **소비자 병렬 개발에 mock을 세울 것인가** — Prism/MSW. 세우면 "소비자가 미구현 provider를 상대한다"는 상황 자체가 줄어든다(REST discussion `260730_1524`의 열린 질문과 같은 항목).
7. **ADR-0021·0026 보류 벌과의 관계** — (b)의 방어는 결국 그 벌의 관할이다.
  served 좌표와 소비자 연산 집합이 기계화되면 "소비자 0" 판정의 재료가 되어 0026 재논의가 쉬워진다.

## 다음 단계 후보 (수렴 시)

- 공백이 ADR로 판정되면: 초안(미구현 연산은 배포 표면에 없다 + 소비자 배포 게이트) — Context 재료는 이 문서.
- 표면 제외·served 도출 채택이면: provider별 Task(#28 Epic 아래) — 리프, ADR 불요.
- 소비자 배포 게이트 채택이면: 대조 스크립트 Task — target은 ops-workflow 또는 신규 도구 저장소, 선행은 #29 계열.
- mock 채택이면: 프론트 mock 파이프라인 Task(REST discussion의 후보와 동일 건).
