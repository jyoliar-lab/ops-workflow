---
type: discussion
topic: ai-agent
subjects: [obs-toolkit, pytest, pyright]
status: done
ref-adrs: []
tickets: [92, 93, 94, 95, 96, 97, 102, 103, 104, 105, 106, 107, 108, 109]
related: [260910_1817_agent-code-comprehension-bottleneck.md, 260917_1726_obs-toolkit-build-vs-borrow.md, 260917_1742_reduction-ops-without-code.md]
---

# obs-toolkit 테스트 스위트 — 무엇을 향해 재편하고, 무엇이 그 뒤를 지키나

## 0. 계기와 문제 다시 말하기

사람이 가져온 것은 증상 넷이다 — 구조 불일관 · 불필요·중복 검증 · 값·엣지 케이스 누락 · 낮은 가독성.
그리고 질문 둘이다 — *어느 방향으로 리팩토링하나* · *기능이 늘어도 품질이 일관되게 남나*.

증상 넷은 원인이 아니라 결과다.
`260910_1817` §8 이 이미 원인을 짚었다 — **소유하려는 것(약속)과 그것을 담은 인공물(테스트)이 연결되지 않는다.**
그 문서는 PR #1 시점의 59개를 읽었고, 규약 후보(§8-4)와 파생 Task 후보(§8-6)를 남겼으나 발행되지 않았다.
그 사이 #95 · #103 · #104 가 들어와 테스트는 110개가 됐고, 규약 없이 세 배로 자랐다.

그러니 이 문서가 답할 문제는 "테스트를 예쁘게" 가 아니다.
치르고 있는 비용은 셋이고, 전부 실측이다.

| 비용 | 실물 |
|---|---|
| **재녹화 한 번에 단언을 손으로 고친다** | #103(`bd1fa51`) 에서 assert 16줄, #104(`7d9902c`) 에서 29줄이 바뀌었다. fixture 값을 문자 그대로 박은 단언(`len(lines) == 65` · `"kube-apiserver-"` · `"posting-service"`)이 재녹화마다 갱신 대상이다 |
| **사람이 읽을 층이 없다** | 260910 §8 의 답 — 사람은 약속 테스트만 읽고 형식·골격은 CI 에 맡기고 싶다. 지금은 약속·형식·골격이 같은 파일에 같은 밀도로 섞여 있어 "읽을 것" 을 고를 수 없다 |
| **안 도는 분기가 있다** | `--labels` · `--label-values` · `--series` · `tag-values` · `main_guard` · `doctor_main` 은 어느 테스트도 실행하지 않는다(§2-3). 실제 transport 의 오류 경로(`_scrub` · `HTTPError` · `URLError`)도 그렇다 |

그리고 앞에 오는 것이 있다.
#94(logs) · #96(traces) · #97(investigate_bundle) · #102(red) 의 AC 는 전부 *"fixture 로 테스트가 통과한다"* 다.
지금 스타일 그대로 네 티켓이 들어오면 테스트는 200개가 되고, 같은 비용이 두 배가 된다.
**두 번째 질문(앞으로도 일관)이 첫 번째 질문(방향)보다 크다.**

## 1. 실측 — 지금의 `tests/`

`workspace/ref/obs-toolkit` HEAD `7d9902c` 를 읽었다.
로컬에 pytest 가 없어 실행은 못 했고, main 의 CI(`.github/workflows/pytest.yml` — pyright strict + pytest, 3.10/3.14)가 초록인 것을 전제한다.

| | |
|---|---|
| 테스트 | 7 파일 · **110 test** · assert 303 |
| 인프라 | `conftest.py`(144) · `record.py`(366, 녹화기) · `replay.py`(127, 요청 정합 검사) — 637줄, 테스트 본문(1,482줄)의 43% |
| fixture | 13개, 전부 `obs-fixture/1` 봉투(요청+응답). manual 1개(`traceql-trace-error.json`) |
| 소스 | `core.py` 639 · `metrics.py` 369 · `cli.py` 888 |

**좋은 것부터 — 이것은 지키고 재편한다.**

- 녹화·replay 인프라는 설계가 옳다.
  나간 요청 == 녹화 요청 검사(`replay.py`)는 "낡은 응답으로 통과" 를 구조로 막고, `unchecked=<이유>` 는 예외를 코드에 남긴다.
  이건 #103 · #104 의 산물이고 이 재편의 대상이 아니라 **토대**다.
- 구조 테스트가 가장 잘 읽힌다 — `test_get_only.py`(AST 로 HTTP import 를 센다), `test_fixture_carries_no_physical_or_token`, `test_token_only_from_env`.
  한 주장을 한 테스트가 하고, 입력이 작다.
  260910 §8-1 의 관찰이 그대로 유효하다: **agent 는 읽히는 테스트를 쓸 줄 안다 — 규약이 없어 섞어 쓸 뿐이다.**
- `test_metrics.py` 의 `_vector` · `_stat` 헬퍼(L28-35)로 만든 손 입력 테스트 — `test_compare_missing_series_and_zero_do_not_divide`(L179) — 가 파일에서 제일 읽힌다.
  네 시계열 a·b·c·d 가 각각 무엇을 대표하는지 주석 한 줄로 보이고, 기대값이 산술 없이 읽힌다.
  **이 모양이 약속 테스트의 표본이다.**
- 모든 테스트에 docstring 이 있다(4개 예외).

## 2. 진단 — 증상 넷을 실물로

### 2-1. 구조 불일관

| 실물 | 어디 |
|---|---|
| 같은 상수 · 헬퍼가 네 벌이고 **내용이 다르다** | `PHYSICAL` — `test_core.py:22`(6단어, `"prometheus"` 포함) · `test_metrics.py:17`(4단어) · `test_cli.py:17`(6단어) · `test_replay.py:14`(`PHYS`, URL 접두). `_no_physical` 은 세 파일에 각각. `test_fixtures.py:13` 은 `test_cli` 것을 import 한다 — 테스트 파일이 테스트 파일에 의존한다 |
| transport 대역이 둘이고 규칙이 다르다 | `FakeTransport`(conftest L29) 는 **URL 조각 포함** 라우팅, `ReplayTransport` 는 정규화 요청 키 비교. 조각 라우팅의 `"api/v1/query?"` 트릭(`test_metrics.py:184, 247` — `?` 로 `query_range` 를 배제한다)은 260910 §8-4 가 지적한 그대로 남아 있다 |
| 파일 경계가 두 축이다 | `test_core` · `test_config` · `test_metrics` · `test_cli` 는 **모듈** 축, `test_fixtures` · `test_replay` · `test_get_only` 는 **인프라·구조** 축. `Window.with_baseline` 은 `test_core.py:44` 와 `test_metrics.py:330` 양쪽에 있다 |
| 기준 시각이 제각각 | `test_metrics` 의 `AT = 100000.0`, `test_core` 의 `10000.0` · `100.0`, replay 는 `t.at`. `test_window` 의 `(4600.0, 8200.0, 3600.0)` 은 `10000 - 1800 - 3600` 을 독자가 계산해야 한다 |
| 재녹화 날짜가 단언에 산다 | `test_cli.py:33` `# 2026-09-22 재녹화: 65 타깃 전부 up`, `test_metrics.py:237` `# 재녹화(2026-09-22): 상위는 kube-apiserver`, `test_cli.py:127` `루트: ngf:careerhub-prod:careerhub-nginx-gateway /`. 실환경의 우연이 테스트의 기대값이다 |
| 실패 시 어느 조건인지 모른다 | `and` 로 이은 assert **138 / 303**(46%). `test_metrics.py` 는 93 중 54. `test_cli.py:31` 한 줄에 조건 5개 |

### 2-2. 중복 · 불필요

| 실물 | 어디 |
|---|---|
| 같은 산출을 세 층에서 다시 단언한다 | `top` 의 출력 형상(`^\d+  \{pod=` · `topk%2810`)을 `metrics.top`(`test_metrics.py:226`) → `cli.metrics_run`(L271) → `cli.promql_main`(L286) 이 각각 검사한다. 층마다 검사할 것은 **그 층이 더한 것**(디스패치 · stdout 절제)뿐이어야 한다 |
| `unchecked=` 이유 문장이 다섯 번 복사됐다 | `test_metrics.py:119, 157, 165, 217, 262` — 같은 62자 |
| `--help` 물리 비노출을 두 파일이 한다 | `test_cli.py:238`(`test_no_physical_flags`, 세 명령) 와 `test_metrics.py:310`(`test_help_mentions_operations_without_physical`) |
| 상수를 두 번 정의하고 테스트로 같음을 강제한다 | `CPU_QUERY` — `test_metrics.py:18` 과 `record.py:243`. `test_fixtures.py:183` 이 둘이 같은지 검사한다. 출처가 하나면 테스트가 필요 없다 |
| 존재 검사 | `test_gitignore_and_rules`(`test_cli.py:298`) — 규칙 파일과 CI yml 이 *있다*. `ReplayTransport.__dataclass_fields__["unchecked"].default is None`(`test_replay.py:84`) — 기본값을 introspection 으로. `cli.auto_step is metrics.auto_step`(`test_metrics.py:61`) — re-export 의 identity |
| e2e 가 단위를 다시 센다 | `test_replay_fixture_end_to_end`(`test_replay.py:116`) 가 `len(ev.value.lines) == 65` 를 또 단언한다 — replay 인프라 테스트가 fixture 내용에 묶였다 |

### 2-3. 누락 — 소스를 대조해 안 도는 것

소스 세 파일의 분기를 테스트와 대조했다.
전부 나열하면 Task 본문이 되므로, **군집**과 대표 예만 둔다.

| 군집 | 대표 (파일:줄) | 왜 문제인가 |
|---|---|---|
| **A. 한 번도 실행되지 않는 CLI 분기** | `cli.py:367-381` `promql --labels/--label-values/--series` · `L669-680` logql 의 같은 셋 · `L811-816` `traceql tag-values` · `L266-272` `main_guard`(ObsError → stderr · exit 1) · `L877-888` `doctor_main`(exit 0/1 · `--json`) · `logql_main` · `traceql_main` 의 `--help` 밖 경로 전부 | fixture 도 FakeTransport 도 없다. `promql --labels` 의 `match[]` 가 `doseq=True` 로 나가는지(`core.Client.get`)는 `record.parse_params` 만 검사한다 |
| **B. 실제 transport 의 오류 경로** | `core._scrub` · `_urllib_transport` 의 `HTTPError`(`e.read()` 본문) · `URLError`(호스트 지움) · `OSError` | "연결 실패 문구에 호스트가 없다" 는 **약속**인데, 검사하는 테스트(`test_transport_failure_is_logical`)는 `FakeTransport(fail=…)` 로 **그 코드를 우회**한다. 로컬 서버(`test_core.py:259`)는 200 만 돌려준다 |
| **C. 파서 형상 변형** | `cli.py:157-158` OTLP v2(`resourceSpans` · `trace.resourceSpans` · `instrumentationLibrarySpans`) · `L140-145` `_attr_value` 의 int/double/bool · `L598-606` `common_labels` 가 **스트림 둘 이상**에서 차이를 뽑는 경우 · `L750-752` span 없음 · 루트 없음/여럿 · `L312-322` 즉시 조회에 range vector | `test_logql_streams`(`test_cli.py:81`) 의 docstring 은 "공통 레이블은 머리에 한 번" 을 약속하지만 fixture 는 스트림 **하나**(L90 `len(parsed.streams) == 1` — 주석이 "limit=5 가 한 스트림에서 찼다" 고 스스로 말한다). **재녹화가 테스트를 조용히 약화시켰다** |
| **D. 설정 엣지** | `proxy_prefix` 의 env/file 해석 · `uids` 가 dict 아님 · 최상위가 객체 아님(`[]`) · 파일 값 `""` → 기본값 · **`OBS_CONFIG` 가 없는 파일을 가리키면 조용히 무시된다**(`config_file_candidates` → `_read_config_file` 의 `is_file()` continue) | 마지막 것은 `test_bad_config_file_is_an_error` 의 근거 문장 — *"사람이 놓은 설정이 몰래 버려지면 안 된다"* — 와 정면으로 어긋난다. 의도인지 버그인지는 코드에 없다(§8 질문 3) |
| **E. 경계값** | `Budget.charge_bytes` 의 `==` 상한 · `parse_time` 의 naive RFC3339 · `+09:00` 오프셋 · `""` · `parse_duration(" 5m ")` · `fmt_val` 의 NaN · `≥1e15` · 숫자 아님 · `spill` 의 같은 마이크로초 충돌(`-2` 접미) · `spill_ref` 의 base 밖 경로 · `_json_message` 300자 절단 · `check_status` 의 `warnings` stderr · `summarize/compare` 의 명시 `step` | 각각 한 줄짜리 테스트감이다. 없는 이유는 어려워서가 아니라 **규약이 "엣지를 세라" 고 하지 않아서**다 |

### 2-4. 가독성

앞의 것들이 겹쳐서 나타나는 결과다.
따로 남는 것은 둘이다.

- docstring 이 **티켓 맥락**을 인용한다 — "AC 2 의 fixture 판", "재시험 보고(#93 코멘트)의 새 마찰 2".
  쓰인 날엔 정확하지만, #93 이 닫힌 지금 독자는 AC 2 가 무엇인지 티켓을 열어야 안다.
  docstring 은 **약속을 현재형으로** 말해야 하고, 출처는 커밋 메시지의 것이다.
- 출력 형식의 정규식이 단언 안에 산다 — `r"^n=60  min=\S+  p50=\S+  p95=\S+  max=\S+  last=\S+  slope=[+-]\S+/s  \{pod="`(`test_metrics.py:113`).
  이건 스냅샷을 정규식으로 손으로 쓴 것이다.
  `conftest.py:96-144` 의 `OBS_TEST_DUMP` 는 이미 출력을 파일로 떨어뜨린다 — **비교 단계만 없는 스냅샷 장치**가 이미 있다.

### 2-5. 원인은 하나로 모인다

증상 넷은 **읽기 티어가 없다** 로 모인다.
그리고 티어가 없는 이유 하나가 더 아래에 있다 — **replay 테스트가 1급 테스트로 쓰인다.**

티켓 AC 가 *"fixture 로 테스트가 통과한다"* 라서, agent 는 실응답 fixture 를 돌려 나온 값을 단언하는 테스트를 **먼저** 쓴다.
그 테스트는 필연적으로 실환경의 우연(65 타깃 · 20 pod · kube-apiserver 가 1위)을 기대값으로 갖고, 한 fixture 로 최대한 많이 검사하려다 주장이 열 개가 되며, 재녹화마다 깨진다.
약속은 그 사이에 끼어 들어간다 — `test_summarize_fixture_one_query`(`test_metrics.py:96`) 의 10개 assert 중 "GET 1회(예산)" 와 "물리 비노출" 이 약속이고, 나머지는 형상이다.

**약속 테스트는 손으로 만든 최소 입력으로, replay 테스트는 형상·스냅샷으로.**
이 역할 분리가 서면 나머지는 정리 문제다.

## 3. 비교 축

옵션을 형용사로 비교하지 않기 위해 축을 먼저 둔다.

| 축 | 뜻 |
|---|---|
| **재녹화 비용** | fixture 를 다시 녹화했을 때 사람이 손대는 단언 수. 지금 ~15-30줄/회 |
| **사람이 읽는 양** | 검수 때 읽어야 하는 테스트 수. 목표는 약속의 수(~35)에 비례, 코드량에 무관 |
| **새 테스트가 규약을 벗어날 수 있나** | 규율(rules.md)인가 구조(CI 가 거부)인가 — CLAUDE.md §8 |
| **#94 · #96 · #102 착수와의 관계** | 재편이 끝나야 착수 가능한가, 병행 가능한가 |
| **되돌리기** | 전부 한 시간대다 — 이 논의에 one-way door 는 없다(§10) |

## 4. 옵션 — 방향

### O0. 안 한다

지금 비용을 그대로 치른다.
네 티켓이 같은 스타일로 들어와 재녹화 비용과 읽기 불가가 두 배가 되고, 260910 §8-3 의 검수 흐름(약속 테스트만 읽는다)은 시작할 수 없다 — 읽을 층이 없으니.
**O0 가 이기는 조건:** obs-toolkit 이 이 네 티켓 뒤로 더 자라지 않고, 재녹화가 다시 없을 때.
로드맵(260830 §3-2 · 260917_1742 §6)은 그 반대다.

### O1. 제자리 정리

`and` 분리 · `PHYSICAL` 단일화 · 중복 제거 · 누락 채우기.
파일 배치는 그대로.
싸고 빠르지만 **"앞으로도 일관"** 에 답하지 않는다 — 정리한 자리에 다음 티켓이 같은 스타일을 다시 쌓는다.
사람이 읽을 층도 생기지 않는다.
**O1 이 이기는 조건:** 티어 개념 자체를 사람이 원하지 않을 때(§8 질문 1 에 "아니오").

### O2. 티어 재편 — 약속 · 형식 · 인프라

260910 §8-4 의 제안이다.
테스트를 **실패했을 때 사람이 무엇을 하나**로 세 층에 나눈다.

| 티어 | 실패하면 | 입력 | 단언 | 독자 |
|---|---|---|---|---|
| **contracts** | 약속이 깨졌다 — 사람이 생각한다. 스냅샷 갱신으로는 지울 수 없다 | 손으로 만든 최소 입력(`_vector` 류) · 명시 라우트의 FakeTransport | 성질 — "없다" · "거부한다" · "0 이 아니다" · "1회다" | **사람** |
| **format** | 출력이 바뀌었다 — 의도했으면 스냅샷 갱신, 아니면 버그 | 녹화 fixture(replay — 요청 정합은 공짜로 따라온다) | 스냅샷 파일 + 형상 불변식(줄 수는 fixture 를 파서로 다시 세어 유도) | CI. 사람은 PR 의 스냅샷 diff 만 |
| **infra** | 하네스가 깨졌다 — 녹화기 · replay · 골격 · 규약 | — | 구조(AST · 파일 · manifest) | CI |

110개를 대략 나누면 35 · 40 · 35 다 — 세어 봐야 정확하다.
**O2 가 답하는 것:** 사람이 읽는 양(contracts 만), 재녹화 비용(값은 스냅샷에만 산다).
**O2 가 혼자서는 답하지 않는 것:** 새 테스트가 규약을 벗어날 수 있나 — 디렉터리는 안내지 강제가 아니다. 그래서 O3 이 붙는다.

### O3. 구조로 강제 — 메타테스트 · 스냅샷 · 규약 파일

O2 의 티어를 **CI 가 지키게** 한다.
저장소에 이미 표본이 있다 — `test_get_only.py` 는 AST 로 "HTTP 는 core 만" 을 센다.
같은 방식으로 테스트 자체를 센다.

| 장치 | 무엇을 거부하나 | 구조인가 규율인가 |
|---|---|---|
| `tests/infra/test_conventions.py` (AST 메타테스트) | `test_*` 에 docstring 없음 · assert 의 `BoolOp(And)` · contracts 디렉터리의 테스트가 `replay(` 를 부름 · `PHYSICAL` 이 conftest 밖에 정의됨 · 단언 줄의 재녹화 날짜 주석 | **구조** — 위반하면 CI 빨강 |
| **래칫 allowlist** | 메타테스트가 현재 위반을 이름·개수로 들고 있다. 새 위반은 즉시 실패, 기존 위반은 줄어들기만 한다. 비면 allowlist 를 지운다 | 구조 — 게이트를 **먼저** 올릴 수 있게 하는 장치. 빅뱅 없이 T2 를 가능하게 한다(§7) |
| **스냅샷 파일** `tests/format/snapshots/<test>.txt` | `OBS_TEST_DUMP` 를 비교 단계가 있는 `assert_snapshot(request, lines)` 로. `OBS_TEST_UPDATE=1` 만 다시 쓴다 | 구조 — 갱신은 명시적이고 diff 가 PR 에 보인다. contracts 에는 스냅샷이 없으므로 "스냅샷 갱신으로 약속을 지운다" 가 성립하지 않는다 |
| `ReplayTransport(unchecked="")` 거부 | 빈 이유 | 구조 — `__post_init__` 한 줄 |
| `FakeTransport` 라우트 키를 `(backend, native path)` 정확 일치로 | `"api/v1/query?"` 트릭 | 구조 — `record.strip_physical` 이 이미 URL 에서 그 키를 뽑는다. 재사용 |
| `.claude/rules/python-tests.md` | — | **규율** — agent 가 쓸 때 읽는 문서. 혼자서는 약하고, 메타테스트가 뒤를 받칠 때 산다 |
| 티켓 AC 문구 | *"fixture 로 통과한다"* → *"약속 표(약속 · contracts 테스트 이름) + format 스냅샷 1건 이상"* | 규율 — 발행자(이 저장소)의 관행. 260910 §8-3 의 착수 승인 표와 같은 것 |

**O3 가 답하는 것:** 두 번째 질문. #94 · #96 · #102 는 게이트 뒤에 들어오므로 새 테스트가 규약을 받는다.
**O3 의 비용:** 메타테스트가 너무 똑똑해지면 그 자체가 읽히지 않는다 — 거부 규칙은 위 표의 다섯 개로 묶고, "contracts 는 성질만 단언한다" 같은 판단 규칙은 규율(문서)에 둔다.

### O4. 도구 게이트 — mutation testing · coverage 임계

260910 §8-5 의 열린 질문이다.
coverage 는 A 군집(안 도는 분기)을 숫자로 보이게 하지만 agent 가 쉽게 채운다.
`mutmut` 은 "물어뜯는가" 를 사람이 안 읽고 알게 하지만 dev 의존 하나가 늘고 느리다(코어 stdlib-only 는 런타임 얘기라 충돌은 없다).
**O4 는 방향이 아니라 O2+O3 뒤의 계기판이다.** 먼저 넣으면 지금 스타일의 테스트가 늘어난다.

### 판정

O2 + O3 이 짝이다 — O2 없이 O3 는 강제할 티어가 없고, O3 없이 O2 는 다음 티켓에서 무너진다.
O1 은 O2 의 부분집합(정리 단계)으로 흡수된다.
O4 는 뒤에, 사람이 원할 때.

## 5. 제안 형상 — 한 자리에

```
tests/
├── conftest.py            PHYSICAL(단일) · FakeTransport(명시 라우트) · replay · assert_snapshot
├── record.py · replay.py  그대로 (토대)
├── contracts/             사람이 읽는다 — 손 입력 · 성질 단언 · 한 테스트 = 한 약속
│   ├── test_physical.py       물리 비노출(출력 · 오류 문구 · fixture · --help) · 토큰은 env 만 · 문구에 안 실림
│   ├── test_get_only.py       (이동)
│   ├── test_errors.py         상태별 문구 규약(agent 의 것 / 사람의 것) · 읽기 시간 초과 · 연결 실패 — 실제 transport 경로 포함(B)
│   ├── test_config.py         해석 순서 · 조용히 안 버림(D 포함)
│   ├── test_budget_spill.py   예산 · spill 상한 · 방금 쓴 것 보호
│   └── test_metrics.py        데이터 없음 ≠ 0 · 기준선 없음 · 0 으로 안 나눔 · 연산당 GET 1회 · k 상한 · offset 표현 불가 거부
├── format/                CI 가 읽는다 — replay + 스냅샷 + fixture 유도 불변식
│   ├── snapshots/*.txt
│   ├── test_promql.py · test_logql.py · test_traceql.py · test_metrics_lines.py · test_doctor.py · test_help.py
│   └── test_parsers.py        형상 변형(C) — 손 입력이지만 약속이 아니라 형태
└── infra/                 하네스 — 녹화기 · replay · 골격 · 규약
    ├── test_fixtures.py · test_replay.py (이동)
    ├── test_repo.py           shim · manifest · SKILL.md
    └── test_conventions.py    메타테스트 + 래칫
```

디렉터리를 마커(`@pytest.mark.contract`) 대신 고른 이유 — `ls` 와 PR diff 에 티어가 보이고, **`pytest tests/contracts` 한 줄이 곧 "사람이 읽을 것"** 이다.
마커는 도구 없이는 안 보이고 `--strict-markers` 와 "모든 테스트에 마커 하나" 메타테스트가 추가로 필요하다.
모듈 축은 디렉터리 안의 파일명으로 남는다(`contracts/test_metrics.py` · `format/test_metrics_lines.py`).

세 층이 같은 산출을 다시 단언하는 문제(§2-2 첫 줄)는 이렇게 푼다 — `metrics.top` 의 성질은 contracts, `top_lines` 의 모양은 format 스냅샷, `promql_main` 은 **디스패치와 stdout 절제만**(top 의 줄 형식을 다시 보지 않는다).

## 6. 앞으로도 일관 — 무엇이 지키나

두 번째 질문에 대한 답을 한 표로.

| 무너질 수 있는 지점 | 지키는 것 | 구조/규율 |
|---|---|---|
| 새 테스트가 `and` · docstring 없음 · 날짜 주석으로 온다 | 메타테스트 | 구조 |
| 새 약속 테스트가 replay 로 온다 | 메타테스트(contracts 에서 `replay(` 거부) | 구조 |
| 새 fixture 값이 단언에 박힌다 | format 은 스냅샷만 — 문자 그대로의 값은 스냅샷 파일에 산다. contracts 는 fixture 를 안 쓴다 | 구조(디렉터리 규칙 + 메타테스트) |
| 재녹화가 테스트를 조용히 약화시킨다(C 군집의 스트림 하나) | contracts 가 손 입력이라 재녹화와 무관. format 스냅샷 diff 가 "무엇이 바뀌었나" 를 사람에게 보인다 | 구조 |
| 다음 티켓의 agent 가 티어를 모른다 | `python-tests.md` + 티켓 AC 문구 | 규율 |
| 약속 목록이 검수 없이 자란다 | 착수 시 약속 표 승인(260910 §8-3 — ticket-engineer 관할, 이 트리 밖) | 규율 |

구조로 못 거는 것이 둘 남는다 — "이 테스트가 정말 약속인가" 와 "약속이 빠졌나".
전자는 사람이 contracts 를 읽을 때 판단하고, 후자는 O4(mutation) 아니면 반증 subagent(260910 §8-3)의 일이다.
지금 정하지 않는다.

## 7. 쪼갬 — 어떻게 자르나

### 벌린 것

| 쪼갬 | 왜 버렸나 / 왜 남겼나 |
|---|---|
| **빅뱅 한 Task** — 규약 · 이동 · 누락을 한 PR 에 | 버렸다. 3천 줄 diff 가 다시 온다 — 260910 §1-1 의 병목을 그대로 재현한다. 검수가 불가능한 PR 은 close 되지 않는다(ADR-0017) |
| **모듈별 Task** — core · metrics · cli 순 | 버렸다. 티어가 모듈 경계를 가로지르므로 모듈별로 자르면 같은 파일을 두 번 옮긴다 |
| **누락 먼저** — 빈 곳부터 채운다 | 버렸다. 규약 없이 채우면 지금 스타일이 늘어난다. 채우는 것은 게이트 뒤다 |
| **게이트 먼저(래칫)** → 이동 → 채움 | **남겼다.** T1 이 올라가면 T2 의 완료 기준이 "allowlist 가 빈다" 로 기계적이 되고, #94 · #96 · #102 가 T2 를 기다리지 않아도 새 테스트는 규약을 받는다 |

### 제안 트리 — 리프 셋, 전부 #92(Feature · In Progress)의 하위

| | 무엇 | 완료 기준의 뼈대 | 선행 |
|---|---|---|---|
| **T1 규약 + 게이트** | `python-tests.md` · `tests/infra/test_conventions.py`(메타테스트 + 현재 위반 allowlist) · conftest 정리(`PHYSICAL` 단일 · FakeTransport 명시 라우트 · `unchecked=""` 거부 · `assert_snapshot`) · 세 디렉터리 생성 | 메타테스트가 CI 에서 돈다. 기존 110개는 allowlist 로 통과한다. 소스(`obs/`) diff 0 | 없음 |
| **T2 티어 이동 + 정리** | 110개를 세 디렉터리로. `and` 분리 · 중복 제거(§2-2 표) · 날짜 주석 → 스냅샷 · docstring 현재형 · fixture 유도 불변식 | allowlist 가 비고 삭제된다. 소스 diff 0. 테스트 수는 늘거나 줄 수 있으나 약속 수(contracts)는 목록으로 PR 본문에 | T1 |
| **T3 누락 채우기** | §2-3 의 A~E 군집. B 는 로컬 서버가 4xx/5xx 와 연결 거부를 내게 확장 | 군집마다 최소 1 테스트, 전부 티어 규약 안에서. D 의 `OBS_CONFIG` 는 §8 질문 3 의 답에 따라 테스트 또는 Bug | T1 (T2 와 병행 가능) |

결정 축은 하나라 sub-ADR 의미의 Feature 는 아니다.
다만 `ticket` 스킬은 근거 없는 **그룹화 Feature** 를 허용하고, 사람은 셋을 한 단위로 추적하길 원했다 — 그래서 Feature 로 묶었다(아래 "발행됨").
T3 는 A~E 로 다섯 리프로 더 쪼갤 수도 있다 — "한 자리에서 읽을 약속 수" 로 보면 다섯이 맞을 수 있고, 발행 시점에 판정한다.

**#94 · #96 · #102 와의 관계** — 선행에 T1 을 넣을지는 사람의 것이다(§8 질문 4).
넣으면 그 티켓들의 새 테스트가 처음부터 티어에 들어간다.
안 넣으면 T2 가 그것들까지 옮긴다 — T2 가 커진다.

### 발행됨 — 2026-09-24

트리는 GitHub 에 산다(#105 와 그 하위) — 여기 베끼지 않는다.
남기는 것은 제안과 달라진 점과 그 이유다.

- **Feature #105 를 #92 밑에 두었다.** 발행 시점에 `link-sub.py` 가 Feature 밑 Feature 를 거부했는데, 그 제약은 ADR 에 없었다(ADR-0010 은 "컨테이너 밑의 컨테이너" 를 별개 축으로 열어 뒀고, `docs/*/adr/` 에 "Feature" 라는 단어 자체가 없다). "3층은 GitHub 의 제약" 이라는 근거 문장도 사실이 아니었다(GitHub 은 8단). ops-workflow-steward 가 사람 확정으로 거부를 풀고 3층을 권장으로 내렸다(`83546df`). 이 저장소의 첫 Feature-밑-Feature 다.
- **Bug 하나가 늘었다.** §2-3 D 의 `OBS_CONFIG` 미존재 무시를 사람이 버그로 판정해 같은 Feature 의 리프로 냈다. T3 는 그 항목을 건드리지 않는다(중복 방지).
- **#94 · #96 · #102 의 선행을 리프 넷 전부로 걸었다.** 사람은 "Feature 를 선행으로" 라고 했으나 `dep_context.py` 게이트가 컨테이너를 거부한다(선행은 열린 리프만 — ADR-0017). 리프 넷 전부가 close 되는 것이 곧 Feature 완료이므로 뜻이 같다. 기존 선행(#93 · #101)은 닫혀 있어 교체 시 빠졌다.
- Bug 도 T1 을 선행으로 걸었다 — 수정과 함께 들어갈 contracts 테스트가 규약 아래에서 쓰이게. 하루 지연이고, 바꾸는 비용은 싸다.

### 발행하지 않는 것

- ticket-engineer 쪽(착수 승인 표 · 반증 subagent) — 260910 §8-6 의 파생 후보이고 이 트리 밖이다.
- 티켓 AC 문구 변경 — 이 저장소 발행자의 관행이라 티켓이 아니다(§8 질문 6).

## 8. 사람에게 — 코드에 없는 것

1. **티어를 디렉터리로 두는 데 동의하나.** 마커나 파일명 접두가 낫다고 보면 §5 의 이유를 반박해 달라.
2. **스냅샷 파일을 커밋하나.** "아니오" 면 format 티어는 fixture 유도 불변식만 남고, 재녹화 시 "무엇이 바뀌었나" 는 사람이 `OBS_TEST_DUMP` 로 본다 — 지금과 같다.
3. **`OBS_CONFIG` 가 없는 파일을 가리킬 때 조용히 무시되는 것** — 의도인가. 의도면 docstring 에 적고 테스트로 못 박는다. 아니면 Bug 다.
4. **#94 · #96 · #102 의 선행에 T1 을 넣나.** 넣으면 그들이 T1 을 기다린다. T1 은 하루 규모다.
5. **mutation testing(O4)** — 지금 넣나, T3 뒤에 보나, 안 넣나.
6. **티켓 AC 문구** *"약속 표 + 스냅샷"* 을 obs-toolkit 티켓의 관행으로 받나. 받으면 #94 · #96 · #102 의 AC 를 고치는 것도 사람의 일이다(발행된 티켓 본문).

### 답 — 2026-09-24

1. 디렉터리 — 예. 2. 스냅샷 커밋 — 예. 3. `OBS_CONFIG` — 버그, 같은 Feature 에서 처리. 4. 세 티켓의 선행 — 재편 전체 뒤로. 5. mutation testing — 열어 둔다(묻지 않았다 — T3 뒤에 다시). 6. AC 문구 — 열어 둔다(발행된 티켓 본문은 사람의 것).
1·2·4 는 티켓 본문에 들어갔다. 5·6 이 남은 미결이다.

## 9. 버린 것

- **replay 를 contracts 에서도 허용** — "실응답으로 약속을 검사해야 진짜" 라는 직관. 버렸다. 약속은 입력이 작을수록 읽히고, 실응답의 우연은 약속과 무관하다. 실응답이 필요한 약속("나간 요청 == 녹화 요청")은 인프라 티어의 것이고 format 테스트가 공짜로 받는다.
- **테스트 파일을 소스 파일에 1:1** — `test_core.py` ↔ `core.py`. 버렸다. 사람이 읽을 단위는 모듈이 아니라 약속이다(260910 §8 답 2).
- **docstring 에 티켓 AC 번호 유지** — 추적성이 있어 보이지만 닫힌 티켓의 AC 번호는 독자에게 빈 기호다. 출처는 커밋 메시지에.
- **coverage 임계를 먼저** — A 군집을 빨리 잡지만 agent 가 채우는 방식이 지금 스타일이다. 게이트 뒤로.
- **메타테스트에 "contracts 는 정규식 금지" 같은 판단 규칙** — 거부 규칙이 늘면 메타테스트가 읽히지 않는다. 다섯 개로 묶고 나머지는 문서에.

## 10. 임계선 — ADR 은 없다

이 논의의 모든 결정은 되돌리는 데 한 시간대다 — 디렉터리 배치 · 규칙 파일 · 메타테스트 · 스냅샷 파일.
CLAUDE.md §4② 로 ADR 이 아니다.
260910 §8-4 도 같은 판정을 했다.

인접한 ADR 후보 하나는 이 논의 밖에 있다 — 260910 §8-6 의 *"검수 = 승인된 약속 목록과 그것을 검사하는 테스트를 읽는 것"*.
그것은 ops-workflow 의 검수 정의(ADR-0017 의 전제)에 관한 것이고, 이 재편은 그 정의의 **obs-toolkit 판 실물**이지 전제가 아니다.
리프 셋은 그 ADR 없이 발행할 수 있다.
다만 그 ADR 이 쓰이면 "약속 · contracts" 라는 어휘를 같이 쓰는 편이 맞다.
