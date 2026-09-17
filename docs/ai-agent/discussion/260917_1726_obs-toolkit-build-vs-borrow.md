---
type: discussion
topic: ai-agent
subjects: [obs-toolkit, prometheus, promql, claude-code-plugins, python-stdlib, loki]
status: active
ref-adrs: []
tickets: [92, 93, 95, 101, 102]
pr: jyoliar-lab/obs-toolkit#4
related: [260830_1657_shared-observability-analysis-plugin.md, 260910_1817_agent-code-comprehension-bottleneck.md]
---

# obs-toolkit — 직접 짜는가, 빌리는가: 계산의 자리와 의존성 경계

## 0. 계기 — 문제를 다시 말한다

PR obs-toolkit#4(#95 `summarize` · `compare` · `top`)를 보며 나온 질문은 *"이 정도 기능은 라이브러리가 있지 않나"* 였다.
그 뒤에 있는 실제 불편은 두 가지다.

- **관리 비용.** 코어 633줄 · CLI 847줄 · metrics 335줄에 테스트 1,233줄이 붙었고, 앞으로 `red`(#102) · 로그 `templates` · 트레이스 `critical_path` 가 같은 방식으로 더 쌓인다.
  한 사람이 검수하고, agent 가 고치는 코드다 — 260910 이 적은 이해 병목이 그대로 적용된다.
- **바퀴 재발명 의심.** 분위수 · 최소제곱 기울기 · 두 창 비교는 어디에나 있는 계산이다.

"표준 라이브러리만" 은 260830 §2-1 이 전제로 도입했고(*Claude Code 쪽은 설치가 없다 — 플러그인 디렉터리가 곧 패키지*), #93 Requirements 첫 줄에 문장으로 박혔다.
그러나 **ADR 이 없고, 260830 §5 "버리는 안" 에 라이브러리 채택안은 후보로 오른 적이 없다.**
저울질된 적 없는 전제를 여기서 처음 저울에 올린다.

## 1. 읽은 것 — 추측이 아니라 인용

### 1-1. PR 의 335줄은 무엇으로 되어 있나 (`obs/metrics.py`, refs/pr/4)

| 구간 | 줄 수(대략) | 성격 | 라이브러리가 대체하나 |
|---|---|---|---|
| Prometheus 형 파서(`Series` · `MetricResult` · `parse_metric` · `check_status`) | ~60 | cli.py 에서 **이동**한 것, 신규 아님 | 아니오 — Loki 응답도 같은 파서를 쓴다 |
| 환원물 dataclass(`SeriesSummary` · `Delta` · `Comparison` · `Top` …) | ~80 | 이 툴킷의 **계약** — "데이터 없음 ≠ 0", `base is None`, `ratio is None` | 아니오 — 도메인 계약이다 |
| **순수 계산** `percentile` · `slope` · `finite_points` | **~40** | 분위수 선형보간 · 최소제곱 | **예 — 표준 라이브러리에 이미 있다**(1-2) |
| 조합 `summarize_series` · `diff_summaries` · `top_query` | ~70 | 짝짓기 · 정렬 · PromQL 문자열 조립 | 부분 — 서버가 대신할 수 있다(1-3) |
| 연산 진입 `summarize` · `compare` · `top` | ~60 | `Client` 주입 · `Window` · 기준선 검증 | 아니오 |

즉 **"라이브러리로 대체 가능한" 것은 40~110줄**이고, 나머지 200줄 이상은 이 툴킷 고유의 계약과 파서다.
라이브러리를 들여도 그 200줄은 남는다.

### 1-2. 표준 라이브러리 안에서도 다시 짰다

`pyproject.toml` 은 `requires-python = ">=3.10"` 이다.
Python 3.10 표준 라이브러리 `statistics` 는 다음을 이미 갖는다.

- `statistics.quantiles(data, n=20, method='inclusive')[18]` — 이웃 선형보간 p95. 로컬 3.14 로 확인: `[1,2,3,4,5]` → `4.8`, PR 의 `percentile(vals, 0.95)` 와 같은 값.
- `statistics.linear_regression(x, y).slope` — 최소제곱 기울기(3.10 신설). `[0,1,2],[1,3,5]` → `2.0`.

PR 의 `percentile` · `slope` 는 이 둘을 손으로 다시 쓴 것이다(도크스트링이 *"numpy 기본과 같다"* 라고 스스로 적었다).
**"표준 라이브러리만" 이 문제가 아니라, 표준 라이브러리를 안 찾아본 것이 문제였다.**
이것은 의존성 정책이 아니라 리뷰 항목이다 — 착수 전 "이 계산이 stdlib · 백엔드에 있는가" 를 묻는 단계가 ticket-engineer 에 없다.

### 1-3. 계산은 이미 서버에 있다 — PromQL

홈랩 Prometheus 는 kube-prometheus-stack 82.10.3(`jyoliar-k8s/gitops/base/controllers/prometheus-operator/application.yaml`) — Prometheus 3.x 다.
`summarize` 가 내는 일곱 값과 `compare` 의 기준선은 전부 PromQL 한 줄로 서버가 계산한다.

| PR 의 계산 | PromQL(서브쿼리 `[1h:60s]` 위에서) |
|---|---|
| p50 · p95 | `quantile_over_time(0.95, (Q)[1h:60s])` |
| min · max · last | `min_over_time` · `max_over_time` · `last_over_time` |
| slope(최소제곱, 값/초) | `deriv((Q)[1h:60s])` — 문서: *simple linear regression* |
| n | `count_over_time` |
| compare 의 기준선 창 | 같은 식에 `offset 1d` — **두 번째 `query_range` 가 필요 없다** |
| top | 이미 `topk(k, agg by (by) (Q))` 로 감싸 서버에 넘긴다 — PR 이 이 방향을 절반 택했다 |

부수 효과가 크다.
PR 11,053 additions 중 **10,056줄(91%)이 fixture** 다 — `query_range` 원본(20 시계열 × 61점) 두 벌.
계산이 서버로 가면 fixture 는 시계열당 한 점, 수십 줄이 된다.
`compare` 의 "두 질의를 같은 step 으로 정렬한다" 요구사항과 그 검증 코드도 사라진다 — 서버가 한 평가 시각에서 두 값을 낸다.

### 1-4. "라이브러리" 의 지형 — 이 도메인엔 없다

| 후보 | 주는 것 | 우리에게 맞지 않는 이유 |
|---|---|---|
| `prometheus-api-client`(4n4nd) | `PrometheusConnect`(HTTP · `requests` 필수) · `Metric` 산술 · pandas DataFrame 변환(extras) | HTTP 층은 우리 `Client`(GET 유일 · Grafana 프록시 · 물리 은닉)와 **충돌**한다. 요약 · 기준선 비교 함수는 없다 |
| `prometheus-pandas` | `query_range` → DataFrame | Jupyter 용. pandas 가 본체 |
| pandas · numpy | `quantile` · `polyfit` | 40줄을 위해 ~60MB 와 설치 경로를 연다. 그 40줄은 stdlib 이 이미 준다(1-2) |

**결론: "summarize · compare · top" 을 주는 파이썬 라이브러리는 없다.**
있는 것은 (a) 우리 것과 겹치는 HTTP 래퍼, (b) 범용 수치 라이브러리, 둘뿐이다.
그리고 (b) 가 주는 것은 stdlib 과 PromQL 이 이미 준다.

### 1-5. 설치 경로 — 전제는 여전히 사실이다

- 플러그인은 `hooks/session-env.sh` 가 `PATH` · `PYTHONPATH` 만 올린다. `bin/promql.py` shim 이 조상 디렉터리에서 `obs/core.py` 를 찾아 `sys.path` 에 넣는다 — **설치 단계가 없다.**
- 이 머신에 `uv` 가 없다(`which uv` → not found). PEP 723 인라인 의존성으로 "설치 없이 의존성" 을 하려면 uv 가 하네스 머신마다 있어야 한다.
- 순수 파이썬 패키지는 `obs/_vendor/` 로 동봉(vendoring)할 수 있다. pandas · numpy 는 C 확장이라 불가.

## 2. 옵션 — 다섯, 그중 하나는 "안 한다"

| | 옵션 | 무엇을 바꾸나 |
|---|---|---|
| **A** | **안 한다** — 지금처럼 stdlib 로 직접 짠다 | 없음. `red` · `templates` · `critical_path` 도 같은 방식 |
| **B** | **계산을 백엔드에 위임한다** — 코어는 PromQL 을 조립하고 결과를 계약(dataclass)에 담기만 | `percentile` · `slope` · `diff_summaries` 삭제. `summarize` 는 `*_over_time` 질의 묶음, `compare` 는 `offset`. `top` 이 이미 이 모양이다 |
| **C** | **외부 라이브러리 + 설치 경로** — uv 또는 SessionStart `pip install` | 하네스마다 uv · 오프라인 실패 모드 · 3 소비자(플러그인 · kagent 이미지 · Strands pip)의 pin 정합 |
| **D** | **순수 파이썬만 vendoring** — 알고리즘이 진짜 필요한 곳에 한정 | 지금은 대상 없음. 로그 `templates`(Drain) 에서 처음 물린다 |
| **E** | **코드가 아니라 질의 템플릿** — SKILL.md 가 PromQL 식을 주고 agent 가 `promql.py` 로 던진다 | metrics.py 의 연산 세 개가 문서 몇 줄이 된다. 계약 · 예산 · 테스트가 코드에서 빠진다 |

## 3. 축으로 비교

| 축 | A 안 한다 | B 서버 위임 | C 라이브러리+설치 | D vendoring | E 질의 템플릿 |
|---|---|---|---|---|---|
| **되돌리기 비용** | — | 한 시간대 — 코드 내부. `Evidence` · `Window` 계약 불변 | **높음** — 하네스 settings · hook · 이미지 · pip 가 같이 바뀐다. one-way door(§4②) | 중간 — 디렉터리 하나, 라이선스 표기 | 낮음 |
| **영향 범위** | obs-toolkit 만 | obs-toolkit 만 | 3 소비자 + 하네스 머신 | obs-toolkit 만 | SKILL.md + agent 행동 |
| **관리 코드(제기된 불편)** | 계속 는다 — 연산마다 계산 + fixture | **가장 적다** — 계산 0, fixture 수십 줄 | 계산은 줄고 설치 · pin 관리가 는다 | 동봉 코드는 우리가 안 고치되 갱신은 우리 일 | 코드 최소, 대신 프롬프트 관리 |
| **정확도의 주인** | 우리 40줄 + 테스트 | **Prometheus** — 검증된 구현 | 라이브러리 | 라이브러리 | agent 가 식을 틀리면 끝 |
| **"데이터 없음 ≠ 0" 계약** | 코드가 지킨다 | 코드가 지킨다(빈 결과 · NaN 판정은 여전히 클라이언트) | 라이브러리는 모른다 — 우리가 감싼다 | 동일 | **agent 에게 맡긴다** — 260830 §5 가 버린 것 |
| **Loki · Tempo 로 확장** | 같은 방식 | LogQL 도 `*_over_time` · `offset` 있음. TraceQL metrics 는 미확인(260830 §6) | pandas 는 로그 군집을 안 준다 | Drain3 가 순수 파이썬 — **여기서 D 가 산다** | 로그 군집은 질의로 못 한다 |
| **네트워크 · 컨텍스트** | 61점 × 시계열 두 벌 → spill | 시계열당 값 몇 개 | A 와 같음 | A 와 같음 | B 와 같음 |

## 4. 판정 — 질문을 바꾼다

*"라이브러리가 있나"* 의 답은 **없다** 다(1-4).
그러나 그 답이 A 를 정당화하지 않는다 — 질문이 틀렸다.
맞는 질문은 *"**이 계산을 누가 하는 게 맞나**"* 이고, 후보는 셋이다: 우리 코드 · 표준 라이브러리 · 백엔드.

- 이 툴킷의 가치는 계산이 아니라 **계약**이다 — 원본을 컨텍스트에 싣지 않는다 · 데이터 없음과 0 을 가른다 · 물리를 숨긴다 · 예산을 집행한다(260830 §3-1).
  그 계약은 어느 라이브러리도 주지 않고, 우리 코드여야 한다.
- 계산은 우리 것이 아니어야 한다.
  metrics 는 **백엔드(B)** 가 이미 다 한다.
  백엔드가 못 하는 계산(로그 템플릿 군집)만 **순수 파이썬 동봉(D)** 이 후보다.
  stdlib 에 있는 것은 stdlib 을 쓴다 — 이건 옵션이 아니라 리뷰 규칙이다(1-2).
- C 는 얻는 것(40줄)에 비해 문(설치 경로 · 3 소비자 pin)이 너무 크다.
  **C 를 열 이유가 생기는 시점은 C 확장이 필요한 계산이 나올 때이고, 지금 보이는 로드맵(260830 §3-2)에 그런 것은 없다.**
- E 는 260830 §5 "절차를 프롬프트로만" 과 같은 이유로 버린다.
  다만 E 의 절반은 옳다 — `top` 처럼 **코어가 질의를 조립하는 것**과 agent 가 조립하는 것은 다르다. 전자가 B 다.

**제안: A → B.** `red`(#102) 를 이 방식으로 먼저 짜고, `summarize` · `compare` 를 B 로 다시 자르는 것을 후속 Task 로 낸다.
B 는 되돌리기 한 시간대라 **ADR 이 아니라 티켓**이다.

## 5. 임계선에 걸리는 것 — ADR 후보 하나

"코어의 의존성 경계" 는 §4② 의 **의존성 도입·제거**에 정확히 해당하고, 지금까지 전제로만 있었다.
초안 후보의 골격은 이렇다(아직 쓰지 않았다 — 사람과 §7 이 끝난 뒤).

> **Decision** — obs-toolkit 코어의 런타임 의존성은 표준 라이브러리로 한정한다.
> 계산은 백엔드(PromQL · LogQL)에 위임하는 것을 우선하고, 백엔드가 제공하지 않는 알고리즘만 순수 파이썬 패키지를 동봉(vendoring)해 쓴다.
> 설치 단계를 전제하는 의존성(C 확장 · pip/uv)은 어댑터 extras 에만 허용한다.
> **Why** — Claude Code 플러그인은 설치 단계가 없고, 세 소비자가 같은 커밋을 가리켜야 하며(260830 §2-4), 계산의 정확도는 검증된 구현(백엔드)에 두는 편이 우리 테스트보다 싸고 옳다.

Alternatives 는 §2 의 C · E 가 된다.
공동무효 판정: "stdlib 한정" 과 "계산은 백엔드에" 는 함께 뒤집히나?
uv 를 하네스 표준으로 들이면 전자가 뒤집히지만 후자는 남는다 — **두 결정일 수 있다.** 초안을 써 보고 가른다.

## 6. 앞에 오는 것 — 정책이 실제로 물리는 지점

| 다음 일 | 계산 | 어디에 |
|---|---|---|
| `red`(#102) | R · E · D 세 질의 | 전부 PromQL — #101(완료) 의 `traces_span_metrics_*` native histogram 위에서. B 그대로 |
| 로그 `histogram` · `around` · `first_seen` | `count_over_time` · 시각 창 | LogQL — B |
| 로그 `templates` | **Drain 류 군집** — 260830 §3-2 가 "단순 변형" 으로 적음 | 백엔드 없음. Drain3(순수 파이썬)를 동봉하나, 단순 마스킹으로 자체 구현하나 — **D 의 첫 실전** |
| 트레이스 `critical_path` | span 트리 순회 | 백엔드 없음. 순수 파이썬 수십 줄 — 자체 구현이 맞다 |

의존성 정책이 **처음으로 무는 것은 `templates`** 다. metrics 는 그 앞의 연습이었다.

## 7. 사람에게 — 코드에 없는 것

1. **"코드 관리하는 것도 일" 의 실체.** 검수(테스트 · 약속 목록 읽기)인가, 머지 판단인가, agent 가 고칠 때의 이해 병목인가.
   B 는 코드 줄 수를 줄이지만, 검수 대상이 파이썬에서 PromQL 식으로 옮겨간다 — 그게 더 읽기 쉬운가는 사람의 답이다.
2. **uv 를 하네스 머신의 표준 도구로 받아들일 것인가.** 받아들이면 C 의 문이 열리고 §5 의 결정이 둘로 갈린다. 지금 이 머신에는 없다.
3. **PR #4 의 처리.** 머지하고 B 를 후속 Task 로 내는가(계약 · 파서 이동 · 기준선 규약은 그대로 살고 계산만 바뀐다), 아니면 PR 을 되돌려 B 로 다시 짜는가.
   전자는 fixture 10k 줄이 잠시 main 에 산다. 후자는 #102 가 기다린다.
4. **`templates` 에서 Drain3 동봉을 허용할 것인가.** 이 답이 §5 초안의 "vendoring 허용" 문장을 결정한다.

## 8. 버린 것

- **pandas 를 들인다** — 40줄을 위해 60MB 와 설치 경로. stdlib 이 같은 값을 낸다.
- **`prometheus-api-client` 를 들인다** — 우리 `Client` 와 정확히 같은 층을 다시 산다. 물리 은닉 · GET 유일이 깨진다.
- **연산을 SKILL.md 의 질의 예시로만 둔다(E)** — 예산 · 데이터 없음 판정 · 테스트가 프롬프트로 간다. 260830 §5 와 같은 이유.
- **"표준 라이브러리만" 을 그대로 두고 아무것도 안 한다(A)** — 전제는 맞았지만, 그 전제 아래서 stdlib 도 백엔드도 안 쓰고 짠 것이 이번 PR 이다. 전제가 아니라 착수 전 질문이 빠져 있었다.
