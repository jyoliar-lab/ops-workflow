---
type: discussion
kind: deliberation
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest, mutmut]
status: active
ref-adrs: []
related: [260923_2005_obs-toolkit-test-suite-refactor.md, 261019_1640_mutation-testing-tools-survey.md, ../../ops-workflow/discussion/261019_1939_tdd-loop-floor-and-app-ac.md]
tickets: [92, 94, 102, 105, 107, 109, 111, 119, 120]
---

# obs-toolkit 테스트 품질 — 무엇이 낮추고 있고, 티켓은 어떤 모양인가

## 1. 문제

obs-toolkit 의 `tests/` 는 소스 3,342줄에 테스트 6,268줄(하네스 포함 7,128줄), 테스트 함수 438개(수집 약 620개)다.
그 양이 사람의 검수를 느리게 한다 — PR 마다 contracts 를 읽는데, 무엇이 약속인지 보이지 않거나 같은 것이 여러 이름으로 반복된다.
fake · mock 의존이 높아 테스트가 내부 배선을 못 박고, 기존 테스트가 다음 티켓에서 수정되는 일이 잦다.
잃는 것은 사람의 검수 시간과 거짓 안전감이다 — 테스트가 많아 보이지만 약속 위반을 잡는지 믿기 어렵다.

출발 가설은 "ticket-engineer 의 tdd-loop 가 AC 에 맞춰 시나리오를 억지로 만들어 품질을 떨어뜨린다" 였다.
실측은 가설을 좁혔다 — AC 행 규칙 자체는 주범이 아니고, 층 규칙에 바닥이 없는 것과 상태형 AC, 그리고 tdd-loop 이전의 유산이 원인이다.
하네스 쪽 원인과 그 델타(4-2 ~ 4-6)는 2026-10-19 에 별도 논의로 분리했다 — `../../ops-workflow/discussion/261019_1939_tdd-loop-floor-and-app-ac.md`, 이하 **B**.
이 문서는 obs-toolkit 쪽 — 경계의 정의 · 소스 인터페이스 · 리팩토링 티켓 — 만 다룬다. 축 번호는 분리 전의 것을 둔다.

열려 있던 것은 둘이었다.
"공개 인터페이스 기준" 의 경계가 어디인가 — 밖에서 쓰는 것은 CLI 뿐이라 정의가 필요했다.
리팩토링의 방향을 어디서 정하나 — 사람은 티켓 안에서 정하길 원한다.
즉석에서 발견한 개선 여지가 티켓 범위 밖이라 막히는 것을 피하기 위해서다.

앞선 논의 260923 은 세 티어 · 메타테스트 · 스냅샷으로 구조를 세웠고, mutation testing(미결 5) 을 열어 두었다 — 4-1 이 닫는다. AC 문구(미결 6) 는 B 의 것이다.
261011 red-review 논의 3-11 은 과단언 · 값 복사를 검토자가 지우지 않고 "다음 티켓의 일" 로 넘겼다.
이 논의의 리팩토링 Task 가 그 다음 티켓의 자리다.

## 2. 실측

코드와 티켓에서 읽은 것이다. 경로는 `workspace/ref/obs-toolkit` 기준.

**규모**

- 모듈별 테스트 배율 — traces 2.3 · logs 3.2 · metrics 2.2 · core 1.4 · cli 0.8. 합 1.9.
- 티어별 함수 — contracts 336 · format 48 · infra 54. 스냅샷 62, 녹화 fixture 37.
- 메타테스트(`tests/infra/test_conventions.py`)는 여섯 규칙만 본다 — docstring · `and` · contracts 의 replay · `PHYSICAL` 위치 · 날짜 주석 · 티어 밖 파일. 아래 지적 대부분은 그 밖이다.

**기준 ① 공개 인터페이스 vs 내부**

- `_private` 직접 호출은 `tests/contracts/test_cli.py:444` 의 `cli._finish` 하나다.
- `monkeypatch.setattr(cli, "_client", …)` 가 10곳(`test_cli.py:340,369,389,457,475,506` · `test_cli_main.py:101` · `format/test_metrics_lines.py:190,208,220`). 원인은 `*_main` 이 `_client()` 로만 Client 를 얻어 주입구가 없는 소스 설계(`obs/adapters/cli.py:169`)다.
- 모듈 전역 `logs_run` · `traces_run` · `metrics_run` · `doctor` 를 패치해 디스패치를 검사하는 곳 7곳(`test_cli.py:339,368,388,505` · `test_cli_main.py:53,62,73`). import 방식이 바뀌면 동작이 같아도 깨진다.
- 질의 문자열 · URL 을 글자 그대로 박은 단언 약 22곳 — `test_traces.py:183-184,789-792` · `test_logs.py:73,83,120,128,511` · `test_metrics.py:55-56,402,565` · urlencode 세부(`offset+%ds`) 4곳 · 파라미터 순서(`test_core.py:198`).
- "보낸 질의 == 조립 함수 자신의 출력" 동어반복 배선 단언 9건(`test_logs.py:181` · `test_metrics.py:447,651` · `test_traces.py:509,512,525,526,967,968`).
- contracts 가 `*_lines` 를 부르는 사이트 29, 그중 한국어 렌더 문구 리터럴에 거는 테스트 약 24(`test_traces.py:1158-1287` · `test_metrics.py:684-716` · `test_cli.py:53` 등). 문구 수정이 snapshots 가 아니라 contracts 를 깨뜨린다.
- 밖에서 obs/ 를 import 하는 소비자는 없다 — obs-bench 는 CLI 만 부른다. `skills/obs-query/SKILL.md` 도 `promql.py` · `logql.py` · `traceql.py` 명령만 안내한다.

**기준 ② 한 테스트 = 한 동작**

- 단언 7개 이상인 테스트 28개. 예 — `test_metrics.py:75` 14개(선택자 · 집계 · increase · 필터 · histogram · `_bucket` 부재), `test_logs.py:354` 11개, `test_core.py:129` 9개.
- `and` 규칙 우회 — 생성식 안의 `and`(`test_metrics.py:42` · `test_traces.py:1227`)는 메타테스트가 못 본다.
- 무관한 케이스를 섞은 parametrize — `test_traces.py:566`(k · limit · quantile · baseline_range) 등 5곳.

**기준 ③ 중복 · 사소한 검증**

- "인자 틀리면 요청 없이 ObsError" 동형 테스트 16함수 28케이스.
- `_no_physical` 9함수 약 70케이스. `--help` 는 contracts 15 + 서브커맨드 3 + format 스냅샷 15 로 33항목이고 `HELP_SCREENS` 표가 두 파일에 중복 정의.
- 헬퍼 중복 — `_params` · `_path` 3벌, `FIXTURE_FILES` · `NAMES` 2벌.
- 인자 → 필드 통과 단언(`test_logs.py:618-626` · `test_traces.py:538-539,980-981`), 상수 == 리터럴(`test_metrics.py:135`), assert 0개 스모크(`test_metrics.py:437-440`).
- `tests/infra/test_fixtures.py:37` 은 37파일 × 13단언 = 481단언으로 녹화 **형식**을 보고, `:136-170` 은 녹화 파일 안의 질의 모양을 다시 센다. `assert len(NAMES) == 37` 은 이력상 네 번 고쳐졌다.
- format 이 contracts 를 다시 — `format/test_metrics_lines.py:186-230` 이 stdout 꼬리 · summary 머리 · `window_preamble` 문자열을 검사한다.

**AC → 테스트 대응** — tdd-loop 티켓 6건의 행 · 테스트 대조는 B §2 에 있다. 요지 — 약 150개 중 AC 문구를 옮긴 것 약 10개 · red 에서 통과한 가드 8개 · 내부 형태에 결합한 것 약 17개이고, 내부 결합의 원천은 층 규칙의 바닥 없음과 상태형 AC 다.

**소스 인터페이스 — 테스트를 왜곡하는 모양과 아닌 것**

- 건강한 이음새 — `Client.transport` 가 주입 가능하고(`obs/core.py:544`), 연산 함수가 `client` 를 인자로 받으며, 계산(`signals_of` · `clusters_of` · `critical_path_of` · `diff_of`)이 I/O(`red` · `templates` · …)와 분리돼 있다. `*_run` 의 `at` 인자가 시각을 고정한다. 이 부분은 fake 없이 검사된다.
- 왜곡 ① — `*_main` 이 Client 를 모듈 전역 `_client()` 로만 얻는다(`obs/adapters/cli.py:169`). 주입구가 없어 `_client` monkeypatch 10곳과 모듈 전역 `*_run` 패치 7곳이 생겼다.
- 왜곡 ② — `RunResult` 가 위치 튜플이다(`cli.py:46`, `tuple[Evidence[Lines], str, Window]`). #111 이 네 자리로 늘리고 #119 가 세 자리로 줄이면서 자리 번호를 단언한 테스트가 두 번 갈렸다. 저장소 규칙 `python-typehints.md`("필드가 정해져 있으면 dataclass")에 어긋난다.
- 왜곡 ③ — `*_run` 이 조립 층에서 렌더까지 한다. `metrics_run` 은 `Evidence[Red]` 를 받아 즉시 `red_lines` 로 펴서 `Evidence[Lines]` 를 돌려준다(`cli.py:477-497`). run 층에서 창 · 기준선을 검사하려면 값이 이미 줄이 된 뒤라 튜플의 Window 자리를 읽을 수밖에 없다 — #120 의 내부 단언 넷이 이것이다.
- 경계선 — `*_query` 조립기는 순수 함수인데 출력이 질의 문자열이라 검사할 성질이 문자열 자체뿐이다. 글자 그대로 단언 약 22곳의 자리다. 설계 결함이라기보다 질의 문자열이 출력의 모양이라는 쪽에 가깝다.
- 셋이 설명하는 것은 내부 결합 · churn 군집(약 17 + monkeypatch 17)이다. 중복 군집 · infra 481단언 · 다중 단언 28개는 인터페이스와 무관하다.
- refactor 단계의 폭 — tdd-loop 를 밟은 PR 넷(#14 · #15 · #16 · #17)의 refactor 커밋 다섯(`a710150` · `f5c5a41` · `30fea7d` · `e1f3bdb` · `d82223d`)은 소스 1~3파일 · 8~60줄이고 테스트 파일을 한 번도 건드리지 않았다. 고친 것은 전부 private 헬퍼(`_by_endpoint` · 질의 분기 · 창 줄 서식)다. 테스트가 이름 부른 함수는 refactor 가 못 움직이므로, 단언이 내려간 층이 곧 설계가 굳는 층이다.

**이번 티켓의 TDD 판정** — `ticket-start` 기준 "이번 변경에 약속이 없는 경우" 는 비대상이다. 테스트 리팩토링은 새 약속을 만들지 않으므로 tdd-loop 를 밟지 않는다. 단, 인터페이스 변경(4-7)은 시그니처 변경이라 대상이다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 공개 인터페이스의 경계 — 테스트 대상의 정의

**선택: obs/ 의 연산과, 그 연산이 이름 부르는 환원 · 파서까지.** 테스트는 자기 주제의 함수를 부르고 그 아래로 내려가지 않는다. (인터뷰, 2026-10-19. 회색 지대의 읽기는 2026-10-19 채팅에서 확정)

**경계 안 — 직접 부를 수 있는 것.**

| 층 | 무엇 | 예 | 검사하는 것 | 대역 |
|---|---|---|---|---|
| 연산 | `Client` 를 받아 `Evidence` 를 돌려주는 함수 · `*_run` · `*_main` | `red` · `histogram` · `exemplars` · `metrics_run` | 배선 — 나간 요청의 성질(백엔드 · 경로 · 질의 파라미터가 담은 성질 · 순서 · 횟수) · 돌아온 dataclass 의 값 · 실패의 종류 | fake transport. 정적 응답만 돌려주고 호출을 세지 않는다 |
| 환원 · 파서 | 응답 JSON 또는 중간 dataclass 를 받아 dataclass 를 돌려주는 순수 함수. `*_of` 9 · `parse_*` 10 · `check_*` · `series_*` · `split_stats` · `baseline_offset` · `common_labels` · `error_reason` | `exemplars_of` · `thresholds_of` · `clusters_of` · `critical_path_of` · `parse_metric` | 경계 — 동률 · 절단 · 빈 입력 · 폴백 · 거부 | 없음. 손으로 만든 입력 |
| core 유틸 | `parse_time` · `parse_duration` · `Window` · `load_config` · `token_from_env` · `Budget` · `Client.get` · `spill` · `prune` · `http_error_message` · `doctor` | | 각자의 약속 | `Client.get` 만 fake transport |
| 렌더러 | `*_lines` 28개 | `red_lines` · `exemplars_lines` | 출력 줄 | format 티어의 스냅샷으로만. contracts 에서 부르지 않는다 |

환원 · 파서의 입력 타입(`SpanMatch` · `EndpointQuantiles` · `Threshold` · `ClientRow` · `MetricResult` · `LogResult` · `Pattern` …)은 이 선택으로 약속이 된다.
필드를 바꾸면 직접 호출 테스트가 갈린다.
받아들이는 이유 — 환원이 이 저장소의 핵심 로직이고, 그 입출력은 필드 이름을 가진 dataclass 다.
이름 없는 자리(`RunResult` 튜플)와 다르다.
설계가 이미 거기 있는 것이지 테스트가 설계를 굳히는 것이 아니다.

**경계 밖 — 테스트가 이름 부르지 않는 것.**

- 언더스코어 private 38개. core 6(`_explicit_config` `_read_config_file` `_scrub` `_urllib_transport` `_json_message` `Client._unsent`) · logs 3(`_query_range` `_first_line` `_side`) · metrics 2(`_side_rows` `_instant`) · traces 16(`_clip` `_attr_value` `_attrs` `_instant` `_fetch_trace` `_stats_by_endpoint` `_window_length` `_quantile_expr` `_by_endpoint` `_nearest_rank` `_roots` `_orphans` `_CrispWalk` `_ms` `_root` `_times`) · cli 11(`_window_line` `_finish` `_stderr` `_spill_failed` `_common` `_client` `_evidence` `_red_now_cell` `_red_base_cell` `_ms_str` `_span_time`). 지금 직접 만지는 것은 `cli._finish` 1곳(test_cli.py:444)과 `cli._client` monkeypatch 10곳.
- 질의 조립기 10개와 조립 조각 4개. `histogram_query` `pattern_filter` `count_query` `summarize_query` `compare_query` `red_query` `top_query` `threshold_query` `candidates_query` `edge_query` · `subquery` `tagged` `duration_literal` `auto_step`. 출력 전문이 곧 구현이다. 성질은 연산이 보낸 요청의 `query` 파라미터에 단언한다. contracts 직접 호출 34곳이 재배치된다 — 삭제가 아니라 단언 대상이 조립기에서 연산으로 올라간다.
- 내부 형태 3종. `RunResult` 튜플 자리 · `Client.log` 의 순서와 내용 · `window_preamble`. 동작이 아니라 구현의 모양이라 위에서 다시 쓸 것이 없다. 버린다.
- 사소한 메서드(기준 ③). `fmt_ratio` `fmt_signed` `fmt_val` `clip` `labels_str` `Span.duration_ms` `Span.is_error` `Window.seconds` `json_*` 7개. 경계 안이지만 단독 테스트를 두지 않는다.

**호출 규칙 — 한 테스트는 자기 주제의 층 하나만 부른다.**

- 연산의 약속을 검사하는 테스트는 연산을 부른다. `red` 의 결과를 `signals_of` 로 검사하지 않는다 — B 4-3 의 문제는 `signals_of` 를 검사한 것이 아니라 `red` 의 약속을 `signals_of` 로 검사한 것이다.
- 환원의 경계를 검사하는 테스트는 환원을 부른다. `exemplars_of` 의 정렬 동률을 `exemplars` 경유로 쓰지 않는다.
- 연산 테스트는 배선을, 환원 테스트는 경계를 나눠 맡는다. 같은 성질을 두 층에서 검사하지 않는다 — 연산 층에서는 "메트릭 응답의 임계가 분류에 쓰였다" 하나면 되고, 열 가지 정렬 경계는 환원 층의 것이다.
- 환원 테스트가 연산 경유로 쓸 수 없으면 둘 중 하나다. 위에서 도달할 수 없는 가드(`exemplars_of` 의 임계 없는 엔드포인트 거부 — `thresholds_of` 가 모든 엔드포인트에 임계를 주므로 `exemplars` 로는 안 걸린다)이거나, 위에서는 Given 이 너무 큰 경계다. 전자는 삭제 후보고 후자는 남는다.

**실측 — 왜 환원을 직접 부르는가.** test_traces.py 에 두 모양이 나란히 있다.
`exemplars_of` 직접 호출 10개(363-485)의 Given 은 두 줄이고 개념을 이름 부른다 — `_sm("c", "x", 50)` 넷과 `{Endpoint("a", "x"): _th(0.010)}`.
`exemplars` 경유 7개(500-578)의 Given 은 헬퍼 다섯이 중첩된 한 줄이고 Prometheus 벡터와 Tempo 검색 JSON 두 응답을 만든다 — `make_client(_exemplar_routes(_vector(_stat_series("a", "x", "base", "0.010")), _search(("t1", [_hit_span("x", 50, service="a")]))))`.
뒤쪽에서는 "임계 10ms" 가 어디에도 적혀 있지 않다 — base 0.010 이 `thresholds_of` 의 폴백 사슬을 지나 임계가 되는 것을 독자가 알아야 한다.
정렬 단언이 깨지면 용의자가 `parse_span_matches` · `thresholds_of` · `exemplars_of` 셋이고, 정렬 테스트가 폴백 규칙에 몰래 의존해 한 테스트에 동작이 둘이 된다(기준 ②).
환원 열 가지 경계를 전부 연산 경유로 쓰면 contracts 읽기 시간(§1 의 증상)이 늘어나는 쪽이다.

**이 선택이 사는 이유 — refactor 의 여지.** §2 실측대로 tdd-loop 의 refactor 커밋 다섯은 테스트가 이름 부르지 않은 private 헬퍼만 움직였다.
테스트가 부르는 층이 곧 설계가 굳는 층이다.
경계를 연산 + 환원으로 두면 그 아래(질의 조립 · I/O 순서 · 헬퍼)가 refactor 의 것이 된다.
경계를 환원 아래까지 내리면(현상) refactor 는 할 것이 없고, 경계를 연산까지만 올리면 환원 테스트의 Given 이 응답 JSON 이 된다.

<details><summary>버린 안</summary>

- CLI(bin/*.py)만 — 밖의 소비자가 CLI 뿐이라는 사실에는 맞지만, contracts 티어가 거의 사라지고 세 티어 구조가 바뀐다. 환원 계산의 성질을 stdout 으로만 검사하면 format 과 섞인다.
- 연산까지만(환원 · 파서 제외) — fake transport 경유로 전부 쓸 수는 있다(헬퍼가 이미 있다). 그러나 Given 이 응답 JSON 이 되고, 진단 용의자가 셋이 되고, 위에서 도달 못 하는 가드가 생긴다. 환원의 입력 타입을 안 얼리는 대신 환원 테스트의 가독성을 잃는다.
- 언더스코어 없는 전부(현상) — 질의 문자열 · 내부 형태 단언이 계속 허용된다. 지금의 churn 이 그 결과다.

</details>

### 3-2. 목표와 범위

**선택: 목표는 테스트 품질 개선이고, 필요하면 소스의 시그니처 · 인터페이스 변경도 감수한다.** `_client` 주입구 부재처럼 테스트 쪽에서 못 고치는 원인이 있다. infra 티어도 포함한다. obs-bench 의 테스트는 다른 저장소라 제외한다. (인터뷰, 2026-10-19)

<details><summary>버린 안</summary>

- `obs/` diff 0 (#105 방식) — monkeypatch 10곳의 원인이 소스에 있어 그 제약 아래서는 기준 ① 을 못 채운다.
- infra 제외 — 481단언의 형식 검사가 가장 큰 단일 덩어리라 빼면 양이 안 줄어든다.

</details>

### 3-3. 티켓의 모양 — obs-toolkit 쪽은 Task 둘

**선택: obs-toolkit 쪽은 Task 둘(인터페이스 · 시그니처 개선, 테스트 리팩토링)이고, 방향은 티켓 안에서 정한다.** Requirements 가 "발견한 개선은 코멘트로 제안 → 사람 승인 → 진행" 절차를 주고, ticket-engineer §3 의 멈춤이 그 협의 지점이 된다. AC 는 종료 상태만 적는다. 하네스 델타는 B 의 Task 하나이고 둘의 선행이다. 처음 인터뷰에서는 "티켓 둘(리팩토링 · 하네스)" 이었고, 4-7 이 인터페이스 Task 를 갈라 셋이 됐다. (인터뷰, 2026-10-19)

<details><summary>버린 안</summary>

- 측정 티켓을 따로 — 조사에는 티켓이 없다(CLAUDE.md §5). 측정은 이 논의의 §2 가 했고, 티켓 안의 추가 측정은 코멘트에 쌓인다.
- 이 논의에서 방향을 전부 닫고 티켓은 집행만 — 즉석에서 보이는 개선 여지가 범위 밖이 되는 것을 피하려는 사람의 의도와 어긋난다.
- Feature + 리프를 진행하며 발행 — 흐름이 하나(측정 → 정리)라 Feature 가 아니다. 리프가 둘 이상으로 갈리면 그때 retype 한다.

</details>

### 3-4. 기준의 구조화

**선택: 기계 판정 가능한 기준은 메타테스트 규칙으로 박되, 어느 규칙인지는 티켓에서 정한다.** 후보는 `_private` 참조 금지 · `monkeypatch.setattr(cli, …)` 모듈 전역 패치 금지 · contracts 에서 `*_lines` 호출 금지 · 생성식 안의 `and` 다. 규칙 없이 문장만 남기면 다음 티켓의 agent 가 같은 패턴을 다시 넣는다(§8 "구조로 강제"). (인터뷰, 2026-10-19)

<details><summary>버린 안</summary>

- 후보 넷을 지금 확정 — 리팩토링하며 보이는 것이 더 있을 수 있고, 티켓 안 재량을 줄인다.
- 박지 않는다 — #105 가 세운 여섯 규칙 밖의 위반이 이번에 쌓인 것이 증거다.

</details>

## 4. 열린 축 — 논의

4-2 ~ 4-6(기존 테스트 정책 · 층 규칙의 바닥 · AC 의 "상태" · red 검토자 · 가드 행)은 하네스 축이라 B 에 있다. 번호는 양쪽 다 분리 전의 것을 둔다.

### 4-1. 거짓 안전감의 척도 — mutation testing

조사 문서 `261019_1640_mutation-testing-tools-survey.md` 가 개념 · 도구 · 비용을 다룬다. 사람이 그것을 읽은 뒤 정한다.
실측 — #105 는 "재편 뒤 계기판으로 볼지 별도 판단" 으로 미뤘다. 중복 테스트는 mutation 점수를 올리지 못하므로, 제거 전후 점수가 같으면 그 제거가 안전했다는 증거가 된다.

- **A. 리팩토링 전 · 후 1회씩 측정** — 점수와 생존 mutant 목록을 티켓 코멘트에 남긴다. 도구는 CI 에 남기지 않는다. "테스트를 줄였는데 변별력이 안 떨어졌다" 를 보이는 것이 목적일 때 이긴다 / 생존 mutant 를 보고도 손대지 않을 거면 측정 비용만 든다.
- B. 1회 측정 + 생존 mutant 를 이번에 죽인다 — 생존 목록이 약속 누락을 드러내면 contracts 를 더 쓴다. 범위가 "줄이기" 에서 "채우기" 로 넓어진다. #108 이 이미 소스 분기 대조로 누락을 채웠으므로 겹칠 수 있다.
- C. CI 계기판으로 도입 — 주기 워크플로로 점수를 기록한다. 임계는 두지 않는다. 한 번 측정에 수십 분 이상이 들어 per-PR 은 무겁다.
- D. 안 한다 — 거짓 안전감은 사람이 contracts 를 읽어 판단한다. 테스트 수를 줄인 뒤 변별력에 대한 증거가 없다.

**판정(사람, 2026-10-19): A — 리팩토링 전 · 후 1회씩 측정.** 테스트 리팩토링 Task(§8 ③) 안에서 도입한다. 기준선은 ③ 착수 시점, 즉 인터페이스 Task(②) 가 머지된 소스 위에서 잰다 — 전 · 후 점수가 같은 소스 위의 비교여야 하므로 ③ 안에서 소스를 바꾸면 그 시점에 다시 잰다. 점수 · 생존 mutant 목록 · 실행 시간을 티켓 코멘트에 남기고, 생존 목록은 놓친 경계 시나리오의 후보 목록으로 읽는다 — 죽일지는 작업자가 정한다(B 로의 확장은 티켓 안 결정). 도구 · 설정 · `mutants/` 는 저장소에 남기지 않는다(C 아님).

### 4-7. 인터페이스 설계가 선행하나 — 순서

실측 — §2 의 왜곡 ① ② ③ 은 소스 모양이고, 그 위에서 테스트만 고치면 같은 자리에서 같은 테스트가 다시 생긴다. 반대로 `*_run` 반환 꼴 변경은 어댑터 넷과 기존 테스트 대부분을 건드리는 시그니처 변경이라 tdd-loop 대상이다 — 지금 규칙대로면 행이 "가장 낮은 층"(B 4-3)에 붙고 기존 테스트는 "수정 — 더하기만"(B 4-2)으로 구부러진다.

- **A. 인터페이스 Task 를 선행 Task 로 — 하네스 축 뒤에** — B 의 4-2 · 4-3 을 먼저 판정해 하네스를 고치고, 그 뒤 `*_main` 주입구 · `RunResult` dataclass · run 의 typed 반환을 한 Task 로 낸다. 테스트 리팩토링 Task 는 그 선행 위에 선다(ADR-0017 의 선행 의존). 왜곡 자리의 테스트를 두 번 쓰지 않는다 / 리팩토링 착수가 하네스 판정과 인터페이스 Task 둘을 기다린다.
- B. 같은 티켓의 첫 단계로 — 리팩토링 Task 안에서 인터페이스를 먼저 고치고 테스트를 그 위에 다시 세운다. 티켓 하나로 끝난다 / 시그니처 변경이 TDD 대상인데 티켓 전체는 비대상으로 판정돼 흐름이 섞인다. 범위가 "테스트" 에서 "어댑터 재설계" 로 넓어진다.
- C. 테스트 먼저, 인터페이스는 티켓 안 협의로 — 3-3 의 절차대로 engineer 가 왜곡 자리에서 멈추고 제안한다. 즉석 발견을 막지 않는다는 사람의 의도와 맞다 / 왜곡 ①②③ 은 이미 실측됐으므로 "즉석 발견" 이 아니고, 멈춤 세 번이 예정돼 있다.
- D. 인터페이스는 손대지 않는다 — 3-2 를 되돌린다. 테스트만 고친다 / monkeypatch 17곳과 튜플 자리 단언이 남고 기준 ① 을 못 채운다.

**판정(사람, 2026-10-19): A — Task 셋, 순서는 ① 하네스 개선 → ② 인터페이스 · 시그니처 개선 → ③ 테스트 리팩토링.** 각 Task 는 앞 Task 를 선행으로 건다(ADR-0017). 세 티켓 모두 이 논의의 실측(§2)과 개선 방향 의견(3-1 · 3-4 · §2 왜곡 ①②③)을 Context · Technical Notes 에 명시하되, **실제 개선 방안의 결정권자는 Task 작업자다** — 티켓은 "무엇이 문제로 측정됐고 어느 쪽이 유력한가" 를 넘기고, "어떻게 고치나" 를 AC 로 못 박지 않는다. 3-3 의 제안 → 승인 → 진행 절차가 세 티켓에 공통으로 적용된다.

## 5. 반대편 — 이 설계가 틀리는 조건

- 공개 경계를 단위 연산으로 두면 `*_query` 조립기의 PromQL · LogQL 문법 오류는 "나간 요청의 성질" 로만 잡힌다. format 의 replay 는 녹화된 응답이라 실 백엔드의 거부를 재현하지 못한다. 문자열 전문 단언을 지우는 만큼 그 오류는 실환경에서만 드러난다.
- 동형 테스트 28케이스를 parametrize 로 묶으면 검수할 양은 줄지만 실패 메시지의 국소성이 준다. 검수 시간이 "읽는 양" 이 아니라 "실패를 이해하는 시간" 이라면 중복 제거의 이득이 작다.
- 메타테스트 규칙이 늘수록 agent 는 규칙을 피하는 모양(생성식 안의 `and` 가 이미 그 예다)을 찾는다. 규칙 수가 아니라 원리를 가르치는 것이 맞다면 3-4 는 과하다.
- 소스 변경을 허용했으므로 테스트 리팩토링이 소스 리팩토링으로 번질 수 있다. 티켓의 Requirements 가 "소스 변경은 테스트가 요구하는 것만" 으로 묶지 않으면 범위가 샌다.
- 인터페이스 선행(4-7 A)이 맞더라도 왜곡 ③ 의 해법(run 이 typed 값을 돌려준다)은 어댑터 넷의 반환 타입을 union 또는 Generic 으로 만든다. 그 복잡도가 튜플 자리 단언보다 비싸면 ③ 은 두고 ① ② 만 고치는 것이 맞다.

## 6. 버린 것

- **측정만 하는 티켓** — 조사에는 티켓이 없다(CLAUDE.md §5). 이 논의의 §2 가 측정이고, 티켓 안의 추가 측정은 코멘트에 쌓여 사람이 증류한다.
- **CLI 만 공개로** — 사실에는 맞지만 세 티어 구조를 무너뜨린다. 소비자가 MCP 어댑터로 늘 때(#92 설계) 다시 볼 일이다.
- **테스트 수 상한 · 배율 목표** — "소스의 1.5배 이하" 같은 수치는 좋은 테스트를 지우게 한다. 척도는 수가 아니라 4-1 의 변별력이다.

## 7. 임계선 — ADR 감인가

ADR 은 없다.
세 티어 규칙 · 메타테스트 규칙 · ticket-engineer 규칙 파일 · 티켓 템플릿 주석은 전부 되돌리는 데 한 시간대다(CLAUDE.md §4②).
260923 §10 과 같은 판정이다.

하나만 지켜본다 — 3-1 "공개 경계 = obs/ 연산 + 환원 · 파서" 는 모듈 API 와 환원의 입력 타입을 약속으로 승격하는 것이다.
지금은 소비자가 CLI 뿐이라 되돌릴 수 있다.
#92 가 그린 MCP 어댑터가 생겨 같은 함수를 밖에서 부르는 순간, 그 경계는 one-way door 가 되고 ADR 감이 된다.

## 8. 다음

판정이 가른 순서는 Task 셋 · 직렬이다(4-7). 전부 `tmp/github-issues/` 에 초안을 쓰고, 사람이 보고 발행한다.

1. **하네스 개선 Task** — B §8. target 은 ops-workflow 와 ticket-engineer. ② ③ 의 선행이다.
2. **인터페이스 · 시그니처 개선 Task** — target 은 obs-toolkit. §2 의 왜곡 ①(`*_main` 의 Client 주입구) · ②(`RunResult` 위치 튜플) · ③(`*_run` 이 렌더까지)을 Context 에 실측으로 넘기고, 고치는 모양은 작업자가 정한다. tdd-loop 대상(시그니처 변경). 선행은 1. 부모는 #92.
3. **테스트 리팩토링 Task** — target 은 obs-toolkit. Goal 은 3-1 · 3-2, Requirements 는 3-3 의 협의 절차와 3-4 의 후보 규칙, AC 는 종료 상태만 — 그중 한 줄이 4-1 A 의 전 · 후 mutation 측정(점수 · 생존 목록이 코멘트에 있고, 후 점수가 전 점수 아래가 아니다). tdd-loop 비대상. 선행은 2. 부모는 #92.

- **조사 문서** — `261019_1640_mutation-testing-tools-survey.md`. 4-1 은 그것을 읽은 뒤 판정한다.
- 이 문서의 열린 축 4-1 · 4-7 이 판정됐다. Task ② ③ 의 초안을 쓰고 사람이 발행하면 `done` 이다.
