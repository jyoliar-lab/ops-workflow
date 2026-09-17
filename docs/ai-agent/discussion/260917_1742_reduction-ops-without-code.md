---
type: discussion
topic: ai-agent
subjects: [obs-toolkit, prometheus, promql, loki, logql, tempo, traceql, alloy, python-stdlib]
status: active
ref-adrs: []
tickets: [94, 95, 96, 101, 102]
related: [260917_1726_obs-toolkit-build-vs-borrow.md, 260830_1657_shared-observability-analysis-plugin.md]
---

# 환원 연산 12개 — 코드 없이 되는 것과 안 되는 것 (#94 · #95 · #96)

## 0. 질문과 기준

*"외부 의존성 도입 없이, 코드 개발 없이 구현 가능한 것은 무엇인가."*
세 티켓의 연산 12개(+ #102 `red`)를 하나씩 놓고 네 바구니로 갈랐다.

| 바구니 | 뜻 | 코드 |
|---|---|---|
| **질의** | 백엔드가 이미 계산한다. 코어는 질의 문자열을 조립하고 응답을 계약(dataclass)에 담는다 | 계산 0 |
| **설정** | 백엔드 기능이 있으나 **꺼져 있다**. `jyoliar-k8s` 값 하나로 켠다 — 코드가 아니라 GitOps | 계산 0 + 설정 티켓 |
| **stdlib** | 표준 라이브러리 함수 호출로 끝난다 | 수 줄 |
| **코드** | 백엔드도 stdlib 도 없다. 알고리즘을 짠다 | 수십 줄 |

어느 바구니든 **남는 층이 있다** — 파서(이미 있음) · `Evidence` · "데이터 없음 ≠ 0" 판정 · CLI 표.
그것은 티켓 Requirements 가 요구하는 계약이라 0 이 되지 않는다.
이 문서가 세는 것은 **계산**이다.

## 1. 실환경 — 무엇이 있고 무엇이 꺼져 있나

| 백엔드 | 버전(실측) | 켜진 것 | 꺼진 것 |
|---|---|---|---|
| Prometheus | kube-prometheus-stack 82.10.3 → 3.x | 서브쿼리 · `*_over_time` · `deriv` · `offset` · `topk` | — |
| Loki | 3.6.7 (chart 6.55.0, SingleBinary, 512Mi) | `volume_enabled: true` · `detected_level` · `count_over_time` | **`pattern_ingester.enabled: false`** (live ConfigMap `loki` 38행) |
| Tempo | 2.10.5 (chart 2.1.2, 1Gi) | `/api/search` · TraceQL 인트린식(`trace:duration` · `status`) · `/api/traces/<id>` | **`metricsGenerator.enabled: false`** → TraceQL metrics(`/api/metrics/query_range`) · service-graphs 메트릭 둘 다 없음 |
| Alloy | 1.15.0, DaemonSet 5 파드 | **spanmetrics 파이프라인 완료(#101, 2026-09-16 close)** — `traces_span_metrics_calls_total` · `traces_span_metrics_duration_seconds`(**native histogram**), 라벨 `service_name` · `span_name` · `span_kind` · `status_code` · `env` · `alloy_node`. Prometheus 3.10.0 remote-write 수신 | `otelcol.connector.servicegraph` 없음 — 아래 §2-3 이유로 **넣어도 안 된다** |

앱은 `alloy.prometheus.svc.cluster.local:4317`(ClusterIP) 로 보낸다 — 한 트레이스의 span 이 5 파드에 흩어진다.

## 2. 연산별 판정

### 2-1. #95 metrics — 전부 **질의**

| 연산 | 티켓이 요구한 계산 | 백엔드 | 남는 것 |
|---|---|---|---|
| `summarize` | n · min · p50 · p95 · max · last · 기울기 | `count_over_time` · `min_over_time` · `quantile_over_time(0.5/0.95, …)` · `max_over_time` · `last_over_time` · `deriv` — 전부 서브쿼리 `(Q)[1h:60s]` 위에서. `deriv` 는 문서상 *simple linear regression* | 질의 6개 조립 · 응답 join · NaN 판정 |
| `compare` | 같은 질의 두 창 → p95 비율 · Δ | `quantile_over_time(0.95, (Q)[1h:60s])` 와 `… offset 1d` — 한 평가 시각에서 두 값. **"같은 step 정렬" 요구사항이 사라진다** | 비율 · Δ 나눗셈, 기준선 0 · 없음 판정 |
| `top` | 레이블 축 상위 k | `topk(k, agg by (by) (Q))` — PR 이 이미 이렇게 했다 | 없음 |
| `red` (#102) | R · E · D | #101 이 낸 메트릭으로 전부 PromQL — R `sum by (service_name) (rate(traces_span_metrics_calls_total[5m]))` · E 같은 식에 `status_code="STATUS_CODE_ERROR"` / 전체 · D `histogram_quantile(0.95, sum by (service_name) (rate(traces_span_metrics_duration_seconds[5m])))` — native 라 `le` 없이 값. `compare` 의 `offset` 도 그대로 얹힌다 | 질의 3개 조립. `rate` 창 ≥ 5m(#101 관찰: flush 60s) |

**실측(2026-09-17 08:54Z, Grafana 프록시 경유 · Prometheus 3.10)** — 위 표가 종이 위 주장이 아니라는 확인.

- 일곱 통계 + 기준선 p95 를 `label_replace(…, "stat", "<이름>", "", "") or …` 로 이어 **한 번의 `/api/v1/query`** 로 받았다: HTTP 200 · 0.15s · 20 시계열 × 8 = 160 값. 질의 길이 1,239자. PR #4 는 같은 것을 `query_range` 두 번 · 2,440 점(raw.json 83KB/질의)으로 받는다.
- **예산이 갈린다** — `core.MAX_QUERIES = 20` 은 `Client.get` 횟수를 센다. 통계마다 질의를 따로 던지면 `summarize` 하나가 7 회, `compare` 가 14 회라 예산 20 이 한 번에 바닥난다. `or` 로 묶어야 PR 과 같은 1~2 회다.
- **계약이 서버 응답만으로 선다** — `offset 60d`(보존 밖) → `p95_base` 시계열이 **부재**(0 이 아니다) · 없는 namespace + `prev` → `result: []`. "기준선 없음" · "데이터 없음" 판정은 그대로 클라이언트 몫이되, 계산은 없다.
- **같은 시각 A/B**(PR 코드 `--end` 고정 vs 서버 `time=`): 20 pod 전부 짝이 맞고 `min` · `last` 동일, `p50` · `p95` 차이 < 1%. `n` 은 61 vs 60 — `query_range` 는 양 끝을 다 세고 서브쿼리는 step 정렬이라 한 점이 빠진다. `max` 최대 7% · `slope` 상대 차가 큰 pod 는 그 한 점 때문이다(기울기 절대값이 1e-9 라 상대 차는 의미가 없다 — 같은 최소제곱이다). 즉 **차이는 방법이 아니라 경계 한 점**이다.

**stdlib 로 되는 것(계산을 굳이 클라이언트에 둔다면)**: `statistics.quantiles(vals, n=20, method='inclusive')[18]` = p95, `statistics.linear_regression(ts, vs).slope` = 기울기(3.10+). 로컬 3.14 로 값 일치 확인.
PR #4 의 `percentile` · `slope` 40줄이 이 두 호출이다.

### 2-2. #94 logs — 셋은 **질의**, 하나는 **설정 또는 stdlib**

| 연산 | 티켓이 요구한 계산 | 백엔드 | 판정 |
|---|---|---|---|
| `histogram` | 축별 건수 + 시간축 스파크라인, 축 카디널리티 상한 | `query_range` `topk(k, sum by (detected_level) (count_over_time({sel}[<step>])))` — Prometheus 형 matrix 응답이라 **PR #4 의 `parse_metric` 이 그대로 읽는다**. 스파크라인은 값 8개 → `▁▂▃▅▇` 문자 매핑 한 줄 | **질의** |
| `around` | 특정 시각 ± d 의 줄 | `query_range` `start=ts-d` `end=ts+d` `limit` — 지금 `logql.py` 의 인자 변환일 뿐 | **질의** |
| `first_seen` | 패턴의 첫 발생 시각 | `query_range` `{sel} |~ "<regex>"` **`direction=forward` `limit=1`** → 첫 줄의 timestamp 가 답. 마스킹 템플릿 → regex 는 `re.escape` 뒤 `<_>` → `.*` 치환 두 줄 | **질의** |
| `templates` | 마스킹 · 결정론적 군집 · 건수 · 비율 · 첫/마지막 시각 · 예시 1줄 | **Loki Patterns API `GET /loki/api/v1/patterns?query=&start=&end=&step=`** — Drain 기반(`pkg/pattern/drain`) 패턴 + 패턴별 `samples` 시계열. 건수 · 비율 · 첫/마지막 시각이 응답에서 바로 나온다. **단 `pattern_ingester.enabled: true` 가 필요하다 — 지금 꺼져 있다** | **설정** |
| `templates` (대안) | 〃 | 클라이언트: 줄을 받아 `re.sub` 로 숫자 · hex · IP · RFC3339 · 따옴표 마스킹 → `collections.Counter` → `most_common(k)`. 첫/마지막은 Counter 를 채우며 `min/max`. 티켓 Technical Notes 가 *"Drain 류의 단순 변형이면 충분"* 이라 했다 — 그 "단순 변형" 이 정확히 `re` + `Counter` 다 | **stdlib** ~30줄 |

Patterns API 가 안 주는 것: **예시 1줄**(패턴만 온다 → `first_seen` 질의로 한 줄 가져오면 된다).
Patterns API 의 미확인: 패턴 보존 기간(ingester 메모리 기반이라 최근 창만일 수 있다) · SingleBinary 512Mi 에서의 메모리 증가 · 테넌트 헤더(`auth_enabled: true` — Grafana 프록시가 얹는다, 지금 `query_range` 와 같은 경로).

### 2-3. #96 traces — 둘은 **질의/설정**, 둘은 **코드**

| 연산 | 티켓이 요구한 계산 | 백엔드 | 판정 |
|---|---|---|---|
| `exemplars` | 느린 / 오류 / 정상 각 k | 검색 세 번: `{ resource.service.name="x" && trace:duration > T }` · `{ … && status = error }` · `{ … && status != error && trace:duration < T }`, `limit=k`. `trace:*` 인트린식은 문서가 *more performant* 라고 권한다. **서버 정렬은 없다** → `sorted(hits, key=duration)[:k]`. 임계 `T` 는 ① 사람이 주거나 ② **#101 의 spanmetrics 로 PromQL 한 줄** — `histogram_quantile(0.95, sum by (service_name) (rate(traces_span_metrics_duration_seconds[1h])))` — 설정 없이 지금 된다. ③ 검색 N 건의 `statistics.quantiles`(표본 편향). TraceQL metrics `quantile_over_time` 은 **#101 이 이미 기각**했다 — Tempo 2.10.5 `Log2Bucketize` 가 2의 거듭제곱 버킷이라 어떤 히스토그램보다 거칠다 | **질의** + `sorted` |
| `service_graph` | 엣지별 건수 · p95 · 오류율 | **Tempo metrics-generator `service-graphs`** → Prometheus `traces_service_graph_request_total` · `_failed_total` · `_server_seconds` → PromQL `sum by (client, server) (increase(…[24h]))` · `histogram_quantile(0.95, …)` · failed/total. **`metricsGenerator.enabled: true` + `processors: [service-graphs]`** 가 필요하다 — tempo-0 단일 파드라 양쪽 span 이 한 곳에 모여 페어링이 된다 | **설정** |
| `service_graph` (안 되는 대안) | 〃 | Alloy `otelcol.connector.servicegraph` — 문서 caveat: *"processing both sides of an edge"* 가 한 인스턴스에서 일어나야 한다. 우리 앱은 ClusterIP 로 DaemonSet 5 파드에 흩뿌린다 → `unpaired_spans_total` 만 는다. #101 이 spanmetrics 에 쓴 "노드별 부분 집계 → `sum by`" 우회가 여기서는 **안 통한다**(엣지는 합산이 아니라 짝이다) | ✗ |
| `service_graph` (클라이언트) | 〃 | 검색 N 건 → 트레이스 N 개 GET → parent-child 서비스 엣지 → `Counter` + `statistics.quantiles`. 트래픽 N 배, 표본 편향 | stdlib 이지만 **비싸다** |
| `critical_path` | CRISP — LFC 재귀 · 1ms 임계 · 경계 자르기 · self time | **백엔드 없음.** Tempo API 에 없고 Grafana · Jaeger UI 만 그린다. `parse_spans` 는 이미 있다(`cli.py`). 트리 구성 = `dict[parent_id → children]`, 정렬 = `sorted(key=end_ns)` | **코드** ~60~80줄 — 이 세 티켓에서 **유일한 진짜 알고리즘** |
| `diff` | 같은 루트의 두 트레이스를 span 이름으로 정렬해 시간 차 | 백엔드 없음. 이름 → duration `dict` 두 개의 join. 같은 이름이 반복되면 `difflib.SequenceMatcher` 로 순서 정렬 | **stdlib** ~30줄 |

## 3. 총계

| 판정 | 연산 |
|---|---|
| **질의** (계산 0) | `summarize` · `compare` · `top` · `red` · `histogram` · `around` · `first_seen` · `exemplars` — **8 / 13** |
| **설정** 켜면 질의 | `templates`(Loki pattern ingester) · `service_graph`(Tempo metrics-generator) — 2 |
| **stdlib** 수 줄 | `templates` 대안(`re` + `Counter`) · `diff`(`dict` / `difflib`) · exemplars 의 정렬 · 임계 |
| **코드** | `critical_path` — 1 |

세 티켓이 자체 구현을 전제한 계산 중 **알고리즘이 진짜 필요한 것은 하나**다.
나머지는 질의 조립이거나, 설정 하나가 꺼져 있어서 클라이언트로 내려온 것이다.

바뀌는 것이 하나 더 있다 — **fixture**.
`query_range` 원본 대신 서버 환원 결과를 녹화하면 fixture 가 시계열당 값 하나가 된다(#95 PR 의 10k 줄 → 수십 줄).
`critical_path` 의 fixture 만 트레이스 원본이어야 한다 — 그것이 유일하게 원본을 계산하는 함수라서.

## 4. 설정 두 개의 대가 — 코드는 0 이지만 공짜가 아니다

| 설정 | 어디 | 얻는 것 | 대가 · 미확인 |
|---|---|---|---|
| Loki `pattern_ingester.enabled: true` | `jyoliar-k8s/…/loki/application.yaml` values | `templates` 전체 + `first_seen` 의 samples | SingleBinary 512Mi 위에 Drain 상태가 얹힌다 — 메모리 실측 필요. 패턴 보존 창 미확인. 실패해도 stdlib 대안(~30줄)이 있다 |
| Tempo `metricsGenerator.enabled: true` + `processors: [service-graphs]` **만** | `jyoliar-k8s/…/tempo/application.yaml` values + remote-write URL(#101 이 연 `enableRemoteWriteReceiver` 를 그대로 쓴다) | `service_graph` 전체 | 1Gi 파드에 generator WAL. **`span-metrics` 는 켜지 않는다** — RED 는 #101 의 Alloy spanmetrics 가 이미 내고 있고 native histogram 이라 더 정밀하다. **`local-blocks`(TraceQL metrics)도 켜지 않는다** — #101 이 정밀도(`Log2Bucketize`)로 기각했고, 이 문서에서 그것이 필요한 연산이 없다(exemplars 임계는 spanmetrics 로 푼다). service-graphs 히스토그램은 explicit bucket 이라 p95 오차가 버킷 폭이다 — 엣지 지연은 "어느 홉이 늘었나" 의 순위용이지 기준선 비교용이 아니므로 감수한다 |

둘 다 **target 이 `jyoliar-k8s`** 라 obs-toolkit 티켓 안에서 할 수 없다 — 별도 Task 감이고, 그 Task 가 닫히기 전까지 `templates` · `service_graph` 는 stdlib 대안 또는 대기다.

## 5. 티켓에 미치는 것 (수정은 사람의 것)

- **#95** — Requirements *"두 질의는 같은 step 으로 정렬"* 은 `offset` 으로 가면 사라진다. AC 의 실환경 명령은 그대로 통과한다(출력 계약 불변). PR #4 는 계약 · 파서 이동 · 기준선 규약을 남기고 계산만 걷어내는 후속이 가능하다.
- **#94** — Technical Notes 가 이미 *"서버에서 좁힐 수 있으면 클라이언트 군집 전에 쓴다"* 라고 적었다. 그 답이 Patterns API 다. `histogram` 은 신규 파서 없이 `parse_metric` 재사용.
- **#96** — Technical Notes 가 *"TraceQL metrics 가 켜져 있으면 `service_graph` 의 절반을 서버가"* 라고 했다. 실측: 꺼져 있고, 답은 TraceQL metrics 가 아니라 **service-graphs processor** 다(켜면 절반이 아니라 전부). TraceQL metrics 는 #101 이 기각했으므로 Technical Notes 의 그 줄은 낡았다. Alloy 대안은 토폴로지 때문에 불가 — 본문에 남길 가치가 있는 "버린 이유".
- **#102** — `red` 의 세 질의는 #101 완료 코멘트의 이름표(`traces_span_metrics_*` · `service_name` · `status_code`)를 그대로 쓴다. raw 조회 시 native histogram 은 `value` 가 아니라 `histogram` 필드로 온다(#101 관찰) — `histogram_quantile` 로 감싸면 `parse_metric` 이 읽는 `value` 로 돌아오므로 파서 변경이 없다.
- 공통 — 각 티켓의 *"fixture 2건 이상"* 은 원본 녹화가 아니라 **서버 환원 응답** 녹화로 읽어야 한다.

## 6. 사람에게

1. 설정 두 개를 켤 것인가 — 각각 `jyoliar-k8s` Task. 켜지 않으면 `templates` 는 stdlib 30줄, `service_graph` 는 보류(클라이언트 방식은 비싸다).
2. `exemplars` 의 "느린" 임계를 누가 정하나 — 사람 인자 · **spanmetrics p95(PromQL, 지금 됨)** · 검색 표본 p95. 제안은 둘째를 기본으로, 첫째를 인자로. 단 spanmetrics 는 `service_name` 단위라 서비스 없는 검색식(`--q` 에 `resource.service.name` 이 없을 때)은 셋째로 떨어진다.
3. `templates` 를 **두 경로 다** 둘 것인가(Patterns API 우선, 없으면 stdlib) — 코드가 는다. 하나만 두면 어느 쪽인가.
4. `critical_path` 는 짠다 — 이 문서가 바꾸지 않는다. 다만 이것이 유일한 알고리즘 코드가 되므로, 260910 의 "약속 목록 + 테스트" 검수 규약을 여기에 집중할 수 있다.
