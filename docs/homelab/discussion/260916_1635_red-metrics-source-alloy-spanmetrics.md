---
type: discussion
topic: homelab
subjects: [alloy, tempo, prometheus, spanmetrics, opentelemetry, careerhub-prod, obs-toolkit]
status: done
ref-adrs: []
---

# careerhub 서비스의 RED 는 어디서 나오나 — Alloy spanmetrics 를 고른 이유

## 계기

obs-toolkit 의 메트릭 환원 연산 Task 에 `red(service, window)` 가 들어 있었다.
그 Task 는 기본 질의 템플릿을 "홈랩 규약 `grpc_server_handled_total`" 로 전제했다.
사람이 물었다 — careerhub-prod 서비스가 그런 메트릭을 수집하고 있지 않은 것 같은데, 왜 RED 가 메트릭 티켓에 있나.

## 확인한 사실 — 코드와 실측

**서비스는 트레이스만 낸다.**
auth · api-composer · posting · review · userinfo 다섯 Go 서비스의 `go.mod` 직접 의존은 `otel/sdk` · `otlptracegrpc` · `otelgrpc`/`otelmux` 뿐이다.
`prometheus/client_golang` · `otel/metric` · `go-grpc-prometheus` 는 어디에도 없다.
각 저장소 `observability/tracer.go` 첫 주석: *"트레이서 init + gRPC interceptor만 처리 (Phase 4-B). logs/metrics는 별도 Phase에서."*
샘플러는 `ParentBased(TraceIDRatioBased(1.0))` — 100% 다.

**메트릭이 흐를 길이 없다.**
Alloy 의 `otelcol.receiver.otlp` 출력은 `traces` 뿐이다(`jyoliar-k8s/gitops/base/controllers/alloy/application.yaml`).
Tempo 는 `metricsGenerator.enabled: false` 다(`.../tempo/application.yaml`).
careerhub-prod 의 스크레이프 대상은 `podmonitor/careerhub-postgresql` 하나다.
Prometheus 의 `up{namespace="careerhub-prod"}` 는 결과가 없다.

**있는 이름은 남의 것이었다.**
`grpc_server_handled_total` 은 `{job=kube-etcd}` 2193 시계열 — etcd 것이다.
`http_request_duration_seconds_*` 는 kube-state-metrics 것이다.
Task 는 Prometheus 에 그 이름이 있는 것을 보고 우리 규약이라고 지었다.
코드를 읽고 쓴 전제가 아니었다.

**트레이스는 살아 있다.**
Tempo 에 posting-service · review-service 트레이스가 24h 에 20건 있다(전부 crawler 경로 — provider CronJob → posting-service, review-crawler → review-service).
api-composer · auth 루트 span 은 24h 안에 0 이다.

## RED 가 왜 메트릭 티켓에 있었나

`ai-agent/260830_1657_shared-observability-analysis-plugin.md` §3-4 의 조사 절차가 출처다.
절차의 원리는 *"싼 신호(집계)로 방향을 정한 뒤에만 비싼 신호(줄·span)를 연다"* 이고, 그래서 삼각측량(`red` + `compare`)이 2단계 메트릭에, 트레이스가 5단계에 놓였다.
§3-2 는 환원 연산을 백엔드별 파일(`metrics.py` · `logs.py` · `traces.py`)로 나눴고, 티켓이 그 파일 경계를 따랐다.
`red` 는 RED method 원전(Tom Wilkie — Prometheus 시대의 메트릭 방법론)의 고향에 따라 `metrics.py` 로 갔다.

판정 기준 자체는 틀리지 않았다.
틀린 것은 "우리 시스템에 그 집계가 있다"는 전제였고, 그것을 읽지 않고 지었다.

## "RED 는 트레이스 영역" 도 반은 틀리다

RED 는 **모든 요청에 대한 집계**이고, 트레이스는 **요청 하나의 표본**이다.
"오류율이 기준선 대비 ×121" 은 집계 질문이라 span 을 하나씩 뒤져 답하면 비싸고 샘플링에 종속된다.
그래서 원전이 메트릭이다.

정확한 물음은 백엔드가 아니라 **집계를 어디서 하나**다.
이 시스템에서는 요청 단위 원천이 트레이스뿐이므로, 트레이스에서 집계를 끌어내는 것이 코드 변경 0 인 유일한 길이다 — 사람의 직관이 맞는 부분이다.
그러나 그 집계가 Prometheus 에 떨어지면 `red` 는 그대로 PromQL 함수다.
"트레이스에서 파생" 과 "PromQL 로 읽는다" 는 양립한다.

## 옵션 — 집계의 자리

| 집계 위치 | 코드 변경 | 샘플링을 낮추면 | 이 시스템에서 |
|---|---|---|---|
| **A. 안 한다** — `red` 를 빼고 summarize · compare · top 만 | 0 | — | 조사 절차의 첫 단계(삼각측량)가 빈 채로 남는다 |
| **B. 프로세스 안** — OTel MeterProvider + OTLP metric exporter. `otelgrpc`/`otelmux` 는 MeterProvider 만 꽂으면 `rpc.server.duration` 등을 이미 낸다 | 5 저장소 + 5 Deployment env + Alloy metrics 파이프라인 + Prometheus receiver | **무관** — 전수 카운트 | tracer.go 가 "별도 Phase" 로 예고한 길 |
| **C. Tempo metrics-generator** — span-metrics 프로세서가 `traces_spanmetrics_*` 를 remote-write | 0 | **R 이 비율만큼 줄고 구제 불가** — generator 는 Tempo 에 도착한 span 만 센다. SDK head 샘플링이든 Alloy tail 샘플링이든 앞단에서 버려진 것은 못 본다 | Tempo values + Prometheus receiver. 멀티테넌트라 per-tenant 설정 |
| **D. Alloy `otelcol.connector.spanmetrics`** | 0 | **connector 를 샘플러 앞에 두면 무관** — "메트릭은 전수, 저장은 표본" 을 분리할 수 있는 유일한 자리. Tempo 문서가 명시적으로 권하는 배치("configure the spanmetrics connector before the tail_sampling processor") | Alloy config + Prometheus receiver. DaemonSet 5 파드라 노드 식별 external label 필요 |
| **E. TraceQL metrics** — `{ } \| rate() by (resource.service.name)` 를 질의 시점에 | 0 | C 와 같음 | Tempo 2.10.5 라 언어는 있으나 `local-blocks` 프로세서가 필요 → 결국 generator 를 켜야 한다. C 와 인프라 변경이 같고 `red` 가 사는 파일만 다르다 |

축은 셋이다 — **코드 변경 범위**(0 vs 5 저장소) × **샘플링 종속** × **누가 떠안나**(앱 저장소 vs 인프라 저장소).

**샘플링 아래서 무엇이 살아남나**(균일 랜덤 가정).
E 비율(errors / calls)과 D 분위수는 거의 보존된다.
R 절대값은 샘플링 비율만큼 축소된다.
`compare` 의 기준선 대비는 두 창의 비율이 같으면 살아남지만, **기준선 창과 지금 창 사이에 샘플링을 바꾸면 ×N 이 가짜로 뜬다** — 아무도 모르는 채로.

## 고른 것 — D, 그리고 버린 이유

**D 를 골랐다.**
지금은 100% head 샘플링이라 C 와 D 의 숫자가 같다.
샘플링을 낮출 날을 대비하면 D 만이 답이고, 그때 샘플링을 SDK 에서 Alloy 의 connector 뒤로 옮겨야 한다.
그 이동은 5 저장소의 `tracer.go` 를 고치는 것이 아니라 값 하나(1.0 유지)이므로 비용이 없다.
결정은 결국 **"샘플링의 자리를 SDK 에서 파이프라인으로 옮긴다"** 로 귀결되는데, 되돌리는 데 한 시간이라 ADR 임계선 아래로 봤다(사람 판정).

**C(Tempo generator)를 버린 이유.**
가장 싸 보이지만 샘플링 앞단에 서지 못한다.
같은 사실을 Prometheus 로 한 번 더 복사하는 것은 D 도 마찬가지이지만, D 는 복사본이 전수라는 점이 다르다.

**B(SDK 메트릭)를 지금 열지 않은 이유.**
샘플링에 독립인 유일한 길이지만, 100% 를 유지하는 동안 이득이 0 이고 5 저장소를 건드린다.
샘플링을 낮추게 되어 D 의 "connector 앞" 배치로도 부족한 날이 오면 그때 연다.

**처음 저울질에서 틀린 것.**
D 를 "C 보다 지저분하다"(DaemonSet 노드별 부분집계)고 먼저 낮춰 봤다.
샘플링 자리를 따져 보고서야 D 만이 분리 가능하다는 것이 드러났다.
"어디서 집계하나" 를 "어디서 샘플링하나" 와 같이 놓기 전에는 보이지 않는 차이다.

## Alloy 부하 실측 — connector 가 아니라 limit 이 문제

D 를 고르기 전에 Alloy 부하를 쟀다(2026-09-16, 7d).

- working set 7일 피크(MiB): s0 126.5 · s1 127.1 · w2 127.8 · w0 121.7 · w1 87.3 — limit 128Mi.
- 5 노드 중 3 곳이 limit 의 99%. OOM 0 · restart 0 — page cache 회수로 버티는 상태.
- CPU 는 limit 200m 의 1.5%.
- 노드 여유는 크다 — w 노드 16 GiB(요청 합 1.1~3.6 GiB), s 노드 8 GiB(요청 합 0.9 GiB).

connector 자체는 가볍다.
트래픽이 24h 20 트레이스이고, 서버 span 이름 상한이 약 74개(gRPC 메서드 40 + HTTP 라우트 34)라 시계열은 많아야 수천, 실제로는 수백이다.
실제 추가분은 `prometheus.remote_write` 의 WAL·큐다 — Alloy 안에 Prometheus 쓰기 경로가 처음 생긴다.
그래서 limit 상향이 spanmetrics 와 무관한 선행 결함으로 먼저 섰다.

## 쪼갬 — 버린 것

- **`red` 를 메트릭 Task 에 남기고 템플릿·AC 만 고치는 안** — 버렸다. 그러면 메트릭 Task 전체가 파이프라인 뒤에 서게 되는데, summarize · compare · top 은 인프라 메트릭(cAdvisor · kube-state)으로 지금 증명된다. `red` 만 떼어 별도 리프로 파이프라인 뒤에 세우면 나머지는 병렬로 간다.
- **파이프라인 일을 obs-toolkit Feature 아래 두는 안** — 버렸다. RED 파이프라인은 obs-toolkit 이 없어도 값어치가 있고 그보다 오래 산다. 홈랩 관측 스택 Feature 아래가 맞다.
- **limit 상향을 파이프라인 Task 에 합치는 안** — 버렸다. 파이프라인 없이도 결함이고, 되돌림·검수 단위가 다르다.
- **SDK 샘플링을 Alloy 로 옮기는 Task** — 내지 않았다. 100% 를 유지하는 동안 실재하지 않는 일이다. 파이프라인 Task 본문에 "샘플러는 connector 뒤" 라는 배치 제약만 남겼다.
- **메트릭 이름을 미리 정하는 것** — 하지 않았다. exporter 가 정하는 이름을 파이프라인 완료 코멘트로 남기고 `red` 의 기본 템플릿이 그것을 따르게 했다. 이 세션이 지어낸 이름이 다음 티켓의 전제가 되는 일 — 원래 Task 가 넘어진 자리 — 을 막기 위해서다.

## 후속 — 히스토그램 해상도 (같은 날)

파이프라인 Task 초안에 "히스토그램은 classic(explicit bucket)" 을 넣었다.
Alloy 문서 예시(`explicit {}`)를 옮긴 것이지 판단이 아니었고, 사람이 "그걸로 정확한 p95 · p99 가 나오나" 를 물어 드러났다.

**explicit bucket 이 왜 안 되나.**
`histogram_quantile` 은 분위수가 떨어진 버킷 안을 선형 보간한다 — 오차가 버킷 폭이다.
connector 기본 레이아웃(`2, 4, 6, 8, 10, 50, 100, 200, 400, 800ms, 1, 1.4, 2, 5, 10, 15s`)에서 p95 가 450ms 면 최대 수백 ms 오차이고, 마지막 버킷 위는 15s 로 포화한다.
`compare` 에는 더 나쁘다 — 두 창의 p95 가 같은 버킷 안이면 ×1.0 이 나와 변화가 사라지고, 경계를 넘으면 과장된 점프가 된다.
샘플링과 같은 종류의 실패다 — 조용히 틀린다.

**"정확한" 분위수는 어느 히스토그램에도 없다.**
원시 duration 을 다 갖고 정렬해야 정확하고, 그것은 span 그 자체다.
메트릭 쪽의 최선은 오차를 상대값으로 묶는 것이다 — native(exponential) histogram.
버킷 비율 2^(2^-scale) · 상대 오차 ≤ (비율-1)/(비율+1): scale 3 → ±4.3%, 4 → ±2.2%, 5 → ±1.1%.
경계를 미리 고르지 않고, 위로 포화하지 않으며, 라벨 조합당 시계열이 19 개가 아니라 1 개이고, 파드 5개의 히스토그램이 레이아웃 일치 없이 병합된다.
Prometheus 3.10.0 은 native histogram 이 stable(v3.8.0 부터)이라 flag 가 없고, 조건은 Alloy `send_native_histograms = true` 하나다.

**"trace 에서 직접 쿼리" 의 두 얼굴.**
사람이 "이럴 거면 trace 에서 직접 쿼리하는 게 낫지 않나" 를 물었다.
(a) TraceQL metrics `quantile_over_time` — Tempo v2.10.5 `pkg/traceql/engine_metrics.go` 의 `Log2Bucketize` · `Log2Quantile` 이 2의 거듭제곱 버킷으로 반올림하고 지수 보간한다. scale 0 exponential histogram 과 같다 — 여기서 논한 어떤 히스토그램보다 거칠다. 제외.
(b) 원시 span 을 받아 코어가 직접 계산 — 정확하고 인프라 0. search API 가 span 마다 duration 을 준다. 한계는 Tempo frontend 상한(262,144 트레이스 · spanSet 당 100 span · 창 1주)과 볼륨 비례 스캔 비용, 그리고 상한에 닿았을 때의 조용한 편향이다.

**샘플링 아래서는 (b) 도 같이 무너진다.**
원시 span 은 정의상 샘플러 뒤에 있다. 샘플링을 낮추면 R 은 비율만큼 축소되고 분위수는 1/√n 노이즈가 붙는다 — 샘플러 뒤의 히스토그램과 같은 만큼 틀린다.
둘을 가르는 것은 히스토그램만 샘플러 **앞에** 놓을 수 있다는 것뿐이다.
그래서 "버리기 시작하는 시점" 부터는 "버리기 전에 집계" 가 필연이고, 이 스택에서 그 표준 형태가 exponential histogram(DDSketch 류의 상대오차 보장 스케치를 OTel 이 표준화한 것)이다.
볼륨이 커져도 샘플링을 안 하면 필연은 아니다 — 비용 문제일 뿐이다. 다만 Tempo 의 serviceMonitor 가 꺼져 있어(`serviceMonitor.enabled: false`) 절벽까지의 거리를 잴 수단이 없다 — 별개 관찰로 남긴다.

**버린 갈래 — "지금은 원시 span, 샘플링 도입 시 히스토그램".**
지금 볼륨(하루 20건)에서 정확하고 인프라 0 이라 매력적이었고, 파이프라인 Task 의 착수 조건을 볼륨이 아니라 샘플링 결정에 거는 안까지 갔다.
사람이 접었다 — 나중에 히스토그램으로 옮기면 일을 두 번 하고, `red` 의 목적이 정확한 수치가 아니라 기준선 이탈 감지이므로 정확한 값을 포기한다.
정확한 값이 필요한 질문("이 요청은 몇 ms 였나")은 트레이스 연산의 것이고, 두 질문을 한 도구에 싣지 않는다.

**결과.** 파이프라인 Task 의 히스토그램 요구사항을 native(exponential) 로 바꿨고, `red` Task 의 질의에서 `_bucket` · `le` 를 뺐다.
raw native 질의는 API 응답이 `histograms` 필드라 골격의 파서가 그 형태를 알아야 한다 — `red` Task 에 확인 항목으로 넘겼다.

## 남는 것

- 샘플링을 실제로 낮추게 될 때, connector 뒤에 어떤 샘플러를 두는가(`probabilistic_sampler` vs `tail_sampling`)는 그때의 논의다.
- api-composer · auth 경로에 트레이스가 24h 동안 0 인 것은 별개 관찰이다 — 트래픽이 없는 것인지 전파가 끊긴 것인지 확인하지 않았다.
- Tempo 수집량을 잴 메트릭이 없다(`serviceMonitor.enabled: false`). 샘플링 판단이 필요해지는 날 먼저 켜야 한다.
