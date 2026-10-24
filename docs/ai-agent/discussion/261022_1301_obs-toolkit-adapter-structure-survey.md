---
type: discussion
kind: survey
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest, mutmut]
status: done
related: [261019_1623_obs-toolkit-test-quality.md, 261022_1334_obs-toolkit-adapter-interface-scope.md]
---

# obs-toolkit 어댑터 · core 의 구조적 결함 — 코드 조사 (2026-10-22)

## 질문

② 인터페이스 · 시그니처 개선 Task 의 범위를 정하려면 세 가지를 알아야 한다.
어느 코드가 어떤 모양으로 테스트 가능성을 막고 있나.
#127 의 mutation 생존 · 커버리지 미실행이 그 모양의 어디에 떨어지나.
결함들이 서로 어떻게 묶여 있어서, 하나를 고치면 다른 것이 따라오거나 따로 남나.
부모 논의 4-10(②의 Goal 범위)과 2026-10-22 인터뷰의 세 질문(core 경계 · ②의 척도 · doctor 포함)이 이것을 요구했다.

조사 대상은 `workspace/ref/obs-toolkit` HEAD `4e5bad7`(2026-10-21)이다.
수치의 출처는 ops-workflow #127 의 코멘트 다섯 — 측정 1 · 2(mutation), 커버리지, 생존 분류, 완료 보고 — 이고 3차(단일 워커) 기준선을 쓴다.
줄 번호는 전부 HEAD 기준이고 다음 커밋에서 흔들린다 — 인용은 함수 이름으로 산다.

## 조사

### 0. 어댑터의 흐름 — 한 명령이 지나는 다섯 자리

`bin/promql.py` 는 15줄 shim 이고 `main_guard(promql_main)` 만 부른다(`bin/promql.py:15`).
`argv` 를 넘기지 않으므로 `*_main` 은 `sys.argv[1:]` 을 읽는다(`cli.py:314`).
그 뒤 한 명령은 `obs/adapters/cli.py` 안에서 다섯 자리를 지난다.

| 자리 | 하는 일 | 어디 | 입력을 밖에서 줄 수 있나 |
|---|---|---|---|
| 선언 | `argparse` 파서 · 서브파서 · 옵션 · help 문구 | `*_main` 본문 앞 2/3 | — |
| 매핑 | `Namespace` → `*Args` dataclass | `*_main` 끝의 4줄 | 아니오 — `*_main` 전체를 돌려야 닿는다 |
| 환경 획득 | `_client()` → `Client.from_env()` | `cli.py:169-170`, 각 `*_main` 의 끝에서 두 번째 줄 | 아니오 — 모듈 전역 함수 |
| 실행 | `*_run(client, args, at)` — 창 계산 · core 호출 · 렌더 · `RunResult` | `*_run` 여섯 | `client` · `at` 은 예 |
| 종료 | `finish(client, run, kind, max_lines, json)` → `emit` → `spill` | `cli.py:145-160` · `75-91` | `out` · `err` · `env` 인자가 있으나 `*_main` 은 넘기지 않는다 |

일곱 진입점의 모양은 다음과 같다.

| `*_main` | 시그니처 | Args | 선언 줄 | 매핑 방식 | 환경 획득 |
|---|---|---|---|---|---|
| `promql_main` | `argv: Sequence[str] \| None = None` | `PromqlArgs` | 9 | 속성 직접 | `_client()` |
| `metrics_main` | `argv: Sequence[str]` | `MetricsArgs` | 20 | `getattr(a, …, 기본값)` ×8 | `_client()` |
| `logql_main` | `argv … = None` | `LogqlArgs` | 10 | 속성 직접 | `_client()` |
| `logs_main` | `argv: Sequence[str]` | `LogsArgs` | 17 | `getattr` ×9 | `_client()` |
| `traceql_main` | `argv … = None` | `TraceqlArgs` | 10 | 속성 직접 | `_client()` |
| `traces_main` | `argv: Sequence[str]` | `TracesArgs` | 16 | `getattr` ×10 | `_client()` |
| `doctor_main` | `argv … = None` | 없음 | 2 | — | `doctor(load_config(), token_from_env())` |

`promql_main` · `logql_main` · `traceql_main` 은 첫 인자가 서브커맨드면 짝(`metrics_main` 등)으로 위임한다(`cli.py:314-317`).
서브커맨드 셋은 `getattr(a, "since", "1h")` 꼴로 매핑한다 — 서브파서마다 옵션 집합이 달라 `Namespace` 에 없는 속성이 있기 때문이다.

### 1. 결함 ① — Client 주입구가 없다

**모양.** `*_main` 여섯이 `client = _client()` 한 줄로 Client 를 얻는다(`cli.py:332 · 536 · 684 · 858 · 1003 · 1204`).
`_client()` 는 `Client.from_env()` 를 부를 뿐이다(`cli.py:169-170`).
`*_main` 에는 Client · transport · env 를 받는 인자가 없다.

**테스트가 치른 값.** `monkeypatch.setattr(cli, …)` 17곳 전부가 이 결함의 우회다.

| 패치 대상 | 곳 | 자리 |
|---|---|---|
| `cli._client` | 10 | `tests/contracts/test_cli.py:340,369,389,457,475,506` · `test_cli_main.py:101` · `tests/format/test_metrics_lines.py:190,208,220` |
| `cli.logs_run` · `traces_run` · `traceql_run` · `metrics_run` | 4 | `test_cli.py:339,368,388,505` — 디스패치를 보려고 run 을 대역으로 |
| `cli.doctor` | 3 | `test_cli_main.py:53,62,73` |

run 패치 4곳은 ① 과 ②(아래)의 합작이다 — Client 를 못 꽂으니 run 자체를 가짜로 바꿔 Args 를 가로챈다.

**#127 이 본 것.** 커버리지가 `cli.py:170`(`Client.from_env()` 호출)을 미실행으로 찍는다(커버리지 코멘트, 미실행 줄 표).
`Client.from_env` 는 생존 19/23(83 %)이고 return 줄(`core.py:558`)이 미실행이다 — 테스트가 전부 `Client(…)` 를 직접 조립하므로 한 번도 돌지 않는다(생존 분류 §3-C).


**예시 — 어떻게 바뀌면 닫히나.** 한 모양일 뿐이고 결정이 아니다.

```python
# 지금 — 환경 획득이 *_main 안에 박혀 있다
def metrics_main(argv: Sequence[str]) -> None:
    ...
    client = _client()                       # Client.from_env() 뿐 — 테스트는 cli._client 를 monkeypatch
    finish(client, lambda: metrics_run(client, args), "promql-%s-failed" % a.cmd, a.max_lines, a.json)

# 예시 — 선택 인자로 받고, 없으면 지금 경로
def metrics_main(argv: Sequence[str], client: Client | None = None) -> None:
    ...
    client = client if client is not None else Client.from_env()
    finish(client, lambda: metrics_run(client, args), "promql-%s-failed" % a.cmd, a.max_lines, a.json)
```

테스트는 이렇게 바뀐다.

```python
# 지금
monkeypatch.setattr(cli, "_client", lambda: client)
cli.promql_main(["red", "svc", "--since", "1h"])

# 예시
cli.promql_main(["red", "svc", "--since", "1h"], client=client)
assert len(t.calls) == 1                     # 나간 요청을 fake transport 에서 읽는다
```

닫히는 것 — `cli._client` 패치 10 · run 패치 4 중 Client 때문인 것. `bin/*.py` 는 그대로다(`main_guard(promql_main)` 이 인자 없이 부르면 `from_env` 경로).

### 2. 결함 ② — argv → `*Args` 매핑이 어느 티어에서도 검사되지 않는다

**모양.** `parse_args` 와 `*Args(…)` 조립이 선언 · `_client()` · `finish` 와 같은 함수 안에 있다.
매핑만 떼어 부를 길이 없다.

```python
# cli.py:885-888 — logs_main
args = LogsArgs(cmd=a.cmd, selector=a.selector, since=getattr(a, "since", "1h"), end=getattr(a, "end", None),
                by=getattr(a, "by", "detected_level"), step=getattr(a, "step", None), k=getattr(a, "k", DEFAULT_TEMPLATES_K),
                ts=getattr(a, "ts", None), span=getattr(a, "span", DEFAULT_AROUND_SPAN), limit=getattr(a, "limit", DEFAULT_AROUND_LIMIT),
                template=getattr(a, "template", None))
```

**기본값이 세 곳에 산다.** `since` 의 `"1h"` 는 `add_argument(default="1h")` · `getattr(a, "since", "1h")` · `LogsArgs.since = "1h"` 세 자리에 있다.
`"1h"` 리터럴은 `cli.py` 에 15번 나온다.
셋 중 하나가 바뀌어도 나머지 둘이 가리므로 어떤 테스트도 모른다.

**`--max-lines` · `--json` 은 Args 를 거치지 않는다.** `finish(client, …, a.max_lines, a.json)` 로 `Namespace` 에서 바로 간다(`cli.py:541` 등 여섯 곳).
run 대역으로 Args 를 가로채는 테스트는 이 둘을 볼 수 없다.

**테스트가 하는 것.** 디스패치 테스트 7개(`test_cli.py:328-396 · 498-511` · `test_cli_main.py` 의 `MAIN_FAILS`)가 run 을 대역으로 바꾸고 받은 Args 를 단언한다.
argv 표본은 함수당 1~4개다.

**#127 이 본 것.** `*_main` 여섯의 생존 286 중 선언 157 · 문구 27 · 환경 획득 1 을 빼면 101 이 남고, 그 101 의 분류는 Args 필드 매핑 78 · `finish(…, a.max_lines, a.json)` → `None` 12 · `sys.argv[1:]` → `[2:]` 6 · 기타 5 다(생존 분류 §3-A).
옵션 하나가 빠지거나 기본값이 바뀌어도 통과한다는 뜻이다.
규칙 파일은 `*_main` 의 테스트를 "디스패치와 stdout 절제만" 으로 정해 두었고(`.claude/rules/python-tests.md` "층마다 검사할 것"), 그 약속은 지켜지고 있다 — 매핑은 그 규칙이 어느 층에도 배정하지 않은 자리다.


**예시 — 어떻게 바뀌면 닫히나.** 한 모양일 뿐이고 결정이 아니다.

```python
# 지금 — 선언 · 파싱 · 매핑 · 환경 · 종료가 한 함수
def logs_main(argv: Sequence[str]) -> None:
    ap = argparse.ArgumentParser(...)
    sub = ap.add_subparsers(...)
    sp_h = sub.add_parser("histogram", ...)
    sp_h.add_argument("--by", default="detected_level", ...)      # 기본값 ①
    ...
    a = ap.parse_args(argv)
    args = LogsArgs(cmd=a.cmd, selector=a.selector,
                    by=getattr(a, "by", "detected_level"), ...)     # 기본값 ② — LogsArgs.by 의 기본값 ③ 과 중복
    client = _client()
    finish(client, lambda: logs_run(client, args), ..., a.max_lines, a.json)

# 예시 — 선언은 파서를 돌려주는 함수, 매핑은 Namespace 를 받는 순수 함수. 기본값은 dataclass 한 곳
def logs_parser() -> argparse.ArgumentParser:
    ...
    sp_h.add_argument("--by", default=argparse.SUPPRESS, ...)      # 안 주면 Namespace 에 없다 — 기본값은 LogsArgs 가 안다
    ...

def logs_args(a: argparse.Namespace) -> LogsArgs:
    given = {k: v for k, v in vars(a).items() if k in LOGS_FIELDS}   # 서브커맨드마다 있는 것만
    return LogsArgs(**given)

def logs_main(argv: Sequence[str], client: Client | None = None) -> None:
    a = logs_parser().parse_args(argv)
    args = logs_args(a)
    ...
```

테스트는 Client 없이 매핑만 본다.

```python
# 지금 — run 을 대역으로 바꿔 Args 를 가로챈다 (test_cli.py:328-346)
monkeypatch.setattr(cli, "logs_run", fake_run)
monkeypatch.setattr(cli, "_client", lambda: client)
cli.logql_main(["histogram", '{a="b"}', "--by", "app", "--since", "2h"])
assert seen[0].by == "app"

# 예시 — 파서 + 매핑만. 요청도 Client 도 없다
a = cli.logs_parser().parse_args(["histogram", '{a="b"}', "--by", "app", "--since", "2h"])
assert cli.logs_args(a) == cli.LogsArgs(cmd="histogram", selector='{a="b"}', by="app", since="2h")
assert cli.logs_args(cli.logs_parser().parse_args(["templates", '{a="b"}'])).k == DEFAULT_TEMPLATES_K   # 기본값은 한 곳
```

`--max-lines` · `--json` 도 같은 길이다 — `Namespace` 에서 `finish` 로 바로 가지 않고 공통 dataclass(예: `Output(max_lines, json)`)를 거치면 매핑 테스트가 함께 본다.

닫히는 것 — run 패치 4 · 생존 101 중 필드 매핑 78 · `finish(…, a.max_lines, a.json)` 12. 기본값 중복 세 곳이 한 곳이 된다.

### 3. 결함 ③ — `RunResult` 가 위치 튜플이다

**모양.** `RunResult: TypeAlias = "tuple[Evidence[Lines], str, Window]"`(`cli.py:46`).
`finish` 가 `ev, kind, window = run()` 으로 푼다(`cli.py:151`).
저장소 규칙 `python-typehints.md` 의 "필드가 정해져 있으면 dataclass" 에 어긋난다.

**테스트가 치른 값.** 자리로 읽는 곳이 33곳이다.

| 파일 | 곳 | 꼴 |
|---|---|---|
| `tests/contracts/test_cli.py` | 8 | `ev, _, _ =` 4 · `[0].value.lines` 4 |
| `tests/contracts/test_metrics.py` | 4 | `ev, got, _ =` · `_, _, window =` |
| `tests/contracts/test_logs.py` | 3 | `ev, kind, _ =` · `_, _, window =` |
| `tests/contracts/test_traces.py` | 2 | `ev, kind, _ =` |
| `tests/format/*` | 16 | `ev, _, _ =` · `ev, kind, _ =` |

**이력.** #111 이 네 자리로 늘리고 #119 가 세 자리로 줄이면서 자리 번호를 단언한 테스트가 두 번 갈렸다(부모 논의 §2).


**예시 — 어떻게 바뀌면 닫히나.** 이름만 붙이는 것(③ 단독)과 값까지 돌려주는 것(③ + ④)은 다른 모양이다. 둘 다 한 모양일 뿐이고 결정이 아니다.

```python
# 지금
RunResult: TypeAlias = "tuple[Evidence[Lines], str, Window]"
ev, _, _ = cli.logql_run(client, cli.LogqlArgs(query="{a=\"b\"}"), at=AT)        # 자리로 읽는다
_, _, window = cli.metrics_run(client, cli.MetricsArgs(cmd="red", service="svc", baseline="prev"), at=AT)

# 예시 (③ 단독) — 필드에 이름만. 첫 필드는 여전히 Lines
@dataclass(frozen=True)
class RunResult:
    evidence: Evidence[Lines]
    kind: str
    window: Window

r = cli.metrics_run(client, cli.MetricsArgs(cmd="red", service="svc", baseline="prev"), at=AT)
assert r.window.baseline is not None            # 자리 번호가 사라진다. #111 · #119 식의 갈림이 없다
```

③ 단독은 자리 읽기 33곳을 이름으로 바꾸지만, run 층에서 볼 수 있는 것은 여전히 줄뿐이다.
④ 까지 가면 `RunResult` 의 첫 필드가 환원 값이 되고 렌더가 run 밖으로 나간다 — 다음 절.

### 4. 결함 ④ — `*_run` 이 렌더까지 하므로 Args → core 전달이 검사되지 않는다

**모양.** 환원 서브커맨드 열둘 전부가 core 를 부른 직후 `_evidence(<x>_lines(ev.value, window))` 로 줄을 만들어 돌려준다(`metrics_run` `cli.py:481-496` · `logs_run` `771-787` · `traces_run` `1150-1162`).
`_evidence` 는 빈 목록을 `["(결과 없음)"]` 로 바꾼다(`cli.py:182-183`) — 렌더 규칙이 run 안에 있다.
`kind` 문자열(spill 디렉터리 이름)도 run 이 만든다.

run 이 core 에서 받는 값의 타입은 열둘이다 — `Summary` · `Comparison` · `Top` · `Red` · `Histogram` · `Templates` · `Context` · `FirstSeen` · `Exemplars` · `CriticalPath` · `ServiceGraph` · `TraceDiff`.
원시 조회 셋(`promql_run` · `logql_run` · `traceql_run`)은 `MetricResult` · `LogResult` · `list[str]` · `list[TraceHit]` · `list[Span]` · `list[TagScope]` 를 받아 같은 자리에서 줄로 만든다.
run 층에서 돌려주는 것은 전부 `Evidence[Lines]` 하나다.

**테스트가 치른 값.** run 층 테스트가 볼 수 있는 것은 줄과 나간 요청뿐이다.
창 · 기준선을 검사하려면 튜플의 Window 자리를 읽어야 한다(`test_metrics.py:600-622` 의 `_, _, window =` 넷) — #120 의 내부 단언 넷이 이것이다.
contracts 가 `*_lines` 렌더 문구에 단언을 거는 29곳(부모 §2)의 절반은 run 경유다 — run 이 줄만 주므로 줄에 걸 수밖에 없다.

**#127 이 본 것.** `*_run` 여섯의 생존 126 중 문구 57 · 미실행 10 을 빼면 59 이고, 그 분류는 core 호출 인자(`k=` · `step=` · `limit=` · `quantile=` · `window`) 제거 · `None` 23 · `_evidence(<lines>)` → `_evidence(None)` 13 · validate · 기타 23 이다(생존 분류 §3-B).
`traces_run` 의 `exemplars(…, k=a.k, …)` 에서 `k` 를 지워도 통과한다 — CLI 옵션이 core 에 닿는다는 약속이 어디에도 없다.
`x_traces_run__mutmut_29`(`limit` 인자 제거)는 병렬 실행에서 가짜 killed 로 뒤집힌 다섯 중 하나다(측정 1).


**예시 — 어떻게 바뀌면 닫히나.** ③ 과 함께다. 한 모양일 뿐이고 결정이 아니다.

```python
# 지금 — run 이 줄까지 만든다
def metrics_run(client: Client, a: MetricsArgs, at: float | None = None) -> RunResult:
    ...
    if a.cmd == "red":
        w = window.with_baseline(a.baseline)
        ev_r = red(client, a.service, w)
        return _evidence(red_lines(ev_r.value, w)), "promql-red", w      # 값은 여기서 사라진다

# 예시 — run 은 환원 값과 "어떻게 그릴지" 를 돌려주고, 그리는 것은 finish 가
@dataclass(frozen=True)
class RunResult(Generic[V]):
    evidence: Evidence[V]
    kind: str
    window: Window
    render: Callable[[V, Window], list[str]]      # 렌더러를 값과 짝지어 싣는다 — 반환 타입이 열두 갈래 union 이 되는 것을 피하는 한 모양

def metrics_run(client: Client, a: MetricsArgs, at: float | None = None) -> RunResult[Any]:
    ...
    if a.cmd == "red":
        w = window.with_baseline(a.baseline)
        return RunResult(red(client, a.service, w), "promql-red", w, red_lines)

def finish(client, run, failed_kind, max_lines, as_json, env=None, out=print, err=_stderr) -> None:
    r = run()
    lines = r.render(r.evidence.value, r.window) or ["(결과 없음)"]    # _evidence 의 빈 결과 규칙도 여기로
    emit(lines, client.log, r.kind, max_lines, ...)
```

테스트는 줄 대신 값을 본다.

```python
# 지금 — red 의 약속을 줄에서 읽는다 (contracts 가 *_lines 문구에 거는 29곳의 자리)
ev, _, _ = cli.metrics_run(client, cli.MetricsArgs(cmd="red", service="svc"), at=AT)
assert any("×" in line for line in ev.value.lines)

# 예시 — 환원 값으로. k · step · limit 이 core 에 닿았는지도 값 · 요청에서 보인다
r = cli.metrics_run(client, cli.MetricsArgs(cmd="top", query="up", k=3), at=AT)
assert len(r.evidence.value.rows) <= 3
assert "topk(3" in _params(t.calls[0])["query"]
```

`RunResult[Any]` 가 싫으면 서브커맨드별 반환을 가르는 길도 있다 — 그것이 부모 §5 가 말한 "union · Generic 의 복잡도" 이고, 작업자가 정할 몫이다.

닫히는 것 — 자리 읽기 33 · Window 자리 읽기 4 · run 경유 문구 단언 · 생존 59 중 core 인자 23 · `_evidence(None)` 13. contracts 에서 `*_lines` 를 부를 이유가 사라진다(③ 테스트 리팩토링의 전제).

### 5. 결함 ⑤ — 환경 획득이 core 전체에 흩어져 있다

**모양.** `env = os.environ if env is None else env` 꼴이 core 에 다섯, 같은 뜻의 분기가 어댑터에 셋 있다.

| 자리 | 함수 | 꼴 |
|---|---|---|
| `core.py:220` | `load_config` | `env is None → os.environ` |
| `core.py:250` | `token_from_env` | 같음 |
| `core.py:367` | `spill_root` | 같음 — `CLAUDE_PROJECT_DIR` |
| `core.py:420` | `spill_ref` | 같음 |
| `core.py:552` | `Client.from_env` | 같음 |
| `core.py:642` | `doctor` | 같음 |
| `cli.py:272 · 480 · 780` | `promql_run` · `metrics_run` · `logs_run` | `now() if at is None else at` |
| `cli.py:1246` | `doctor_main` | `doctor(load_config(), token_from_env())` — env 인자 자체가 없다 |

`finish` · `emit` 에는 `env` 인자가 있으나(`cli.py:146 · 76`) `*_main` 이 넘기지 않아 `spill` 까지 `None` 으로 흘러 `os.environ` 을 읽는다.
즉 이음새의 절반은 이미 있고, 진입점이 그것을 쓰지 않는다.

**테스트가 치른 값.** `monkeypatch.setenv` 15곳(그중 `CLAUDE_PROJECT_DIR` 10) · `cli_env` fixture 5곳.
어댑터에 env 인자가 없으니 테스트가 프로세스 환경을 바꾼다.
`at` 은 이미 주입 가능하므로(`*_run` 셋의 `at` 인자) 시각 쪽은 테스트가 고정한다 — `now() if at is None` 분기만 안 돈다.

**#127 이 본 것.** 환경 획득 생존 14 + `from_env` 미실행 10(생존 분류 §2 · §3-C).
부모 4-10 이 말한 "기본값 `None` 이면 함수 안에서 환경을 읽는 분기" 가 이것이고, 부모 §2 의 왜곡 ① 과 같은 꼴이다.
측정 1 은 `mutants/tmp/obs/` 에 호출 디렉터리 22~28개가 남는다고 적었다 — env 읽기를 깬 mutant 가 cwd 로 spill 한 흔적이고, 이 결함이 측정 환경까지 더럽힌다는 뜻이다.


**예시 — 어떻게 바뀌면 닫히나.** 어댑터 쪽만 고치는 것과 core 기본값까지 없애는 것은 다른 범위다. 한 모양일 뿐이고 결정이 아니다.

```python
# 지금 — 진입점이 env 를 모르고, 아래의 함수들이 각자 os.environ 을 읽는다
def metrics_main(argv: Sequence[str]) -> None:
    ...
    client = _client()                                                         # from_env() → os.environ
    finish(client, lambda: metrics_run(client, args), kind, a.max_lines, a.json)   # env=None → spill 이 os.environ

# 예시 (어댑터만) — 환경은 진입점이 한 번 읽고 아래로 명시해 넘긴다. core 는 그대로
def metrics_main(argv: Sequence[str], env: Mapping[str, str] | None = None,
                 client: Client | None = None, at: float | None = None) -> None:
    env = os.environ if env is None else env                                   # 읽는 자리는 여기 하나
    ...
    client = client if client is not None else Client.from_env(env)
    finish(client, lambda: metrics_run(client, args, at=at), kind, a.max_lines, a.json, env=env)

# 예시 (core 까지) — core 함수의 env=None 기본값을 없앤다. 호출자 전부가 env 를 넘겨야 한다
def spill(kind: str, payload: object, summary: Sequence[str], env: Mapping[str, str], cwd: Path | None = None, ...) -> Path: ...
def load_config(env: Mapping[str, str], home: Path | None = None) -> Config: ...
```

테스트는 프로세스 환경을 건드리지 않는다.

```python
# 지금
monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
monkeypatch.setattr(cli, "_client", lambda: client)
cli.promql_main(["summarize", "up"])

# 예시
cli.promql_main(["summarize", "up"], env={"CLAUDE_PROJECT_DIR": str(tmp_path)}, client=client, at=AT)
assert (tmp_path / "tmp" / "obs").is_dir()
```

어댑터만 고치면 `setenv` 15 · `cli_env` 5 가 사라지고, core 의 `env is None` 분기는 남는다(생존 14 그대로 — 그 분기를 지나는 테스트가 없으므로).
core 까지 고치면 분기 자체가 없어지고 생존 14 도 없어지지만, `load_config` · `token_from_env` · `spill` · `spill_root` · `spill_ref` · `doctor` · `Client.from_env` 의 시그니처와 그 호출자 전부가 바뀐다.


**시계 — ⑤ 의 한 갈래.** 시간을 읽는 자리는 다섯이다.

| 자리 | 꼴 | 테스트가 고정하는 법 |
|---|---|---|
| `core.py:286` `now()` | 정의 — `datetime.now(utc).timestamp()` | — |
| `core.py:316` `Window.last(…, at)` | `now() if at is None else at` | `at=` |
| `cli.py:272 · 480 · 780` `promql_run` · `metrics_run` · `logs_run` | 같은 꼴 | `at=` — 테스트 72곳 |
| `core.py:386` `spill` | `datetime.now(utc).strftime(…)` 직접 — `now()` 도 `at` 도 안 거친다 | 고정할 길이 없다 |

`at` 주입은 이미 절반이다 — 모자란 것은 "`None` 이면 안에서 읽는다" 분기와 `spill` 의 직접 읽기 둘뿐이다.

#127 의 생존 중 시계의 것은 둘이다.
`metrics_run #113` — `now() if (at is None) and False else at`. 테스트가 늘 `at=` 을 주니 `now()` 분기가 한 번도 안 돌고, 망가뜨려도 통과한다(생존 분류 §3-B "validate · 기타"). `Window.last` · `promql_run` · `logs_run` 의 같은 분기도 같은 처지다.
`spill #14` — `now(utc)` → `now(None)`. 디렉터리 이름이 UTC `Z` 라는 약속이 비검사다(생존 분류 §3-C). `at` 과 무관하다 — `spill` 이 시계를 직접 읽는다.

시계를 고정하는 길은 셋이다.

| 길 | 모양 | 비용 |
|---|---|---|
| 주입 | `transport` 와 같은 꼴 — `clock: Callable[[], float] = now` 를 받거나, `*_main` 이 한 번 읽어 `at: float` 로 내려보낸다. `*_run` · `Window.last` 의 `None` 분기가 사라진다. `spill` 은 `stamp` 또는 `clock` 을 인자로 | 의존성 0. 이 저장소가 transport 에서 이미 쓰는 패턴. `spill` 은 core 시그니처 변경 |
| 모듈 패치 | `monkeypatch.setattr(core, "now", …)` | `cli.py` 가 `from obs.core import now` 로 가져와 `cli.now` 도 따로 패치해야 하고, `spill` 의 `datetime.now` 는 클래스라 패치가 안 된다. ① 의 `_client` 패치와 같은 냄새 — 부모 3-4 의 "obs 모듈 패치 0" 후보 규칙과 어긋난다 |
| 동결 플러그인 | `freezegun` · `time-machine` — `datetime.now` 를 프로세스 전체에서 얼린다 | 의존성 하나 · pyright stub · mutmut 의 fork 환경에서의 동작 확인. 시계 읽기가 다섯 곳뿐이라 잡을 양에 비해 도입 비용이 크다 |

**예시 — 주입.** 한 모양일 뿐이다.

```python
# 지금
def metrics_run(client: Client, a: MetricsArgs, at: float | None = None) -> RunResult:
    base_ts = now() if at is None else at                 # 테스트가 늘 at 을 주니 now() 갈래는 죽은 길

def spill(kind, payload, summary=(), env=None, cwd=None, keep=SPILL_KEEP) -> Path:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")   # 고정 불가

# 예시 — 진입점이 한 번 읽고, 아래는 값만 받는다
def metrics_main(argv, env=None, client=None, at: float | None = None) -> None:
    at = now() if at is None else at                      # 시계를 읽는 자리는 여기 하나 (⑤ 의 env 와 같은 줄에)
    finish(client, lambda: metrics_run(client, args, at), ..., env=env, at=at)

def metrics_run(client: Client, a: MetricsArgs, at: float) -> RunResult:
    base_ts = at                                          # 분기가 없다 — 생존할 mutant 도 없다

def spill(kind, payload, summary, env, at: float, cwd=None, keep=SPILL_KEEP) -> Path:
    stamp = _dt.datetime.fromtimestamp(at, _dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
```

테스트는 지금처럼 `at=AT` 을 주되, `spill` 의 디렉터리 이름이 `AT` 의 UTC 표기로 시작한다는 것을 처음으로 단언할 수 있다.

사람의 선택(2026-10-22 채팅): **주입.** 범위는 ⑤ 와 함께 간다 — `*_run` 쪽은 어댑터, `spill` 쪽은 core 시그니처.

### 6. 결함 ⑥ — 선언과 배선이 한 함수에 있다

**모양.** `*_main` 의 줄 수와 그중 선언 줄 수는 §0 의 표다 — `metrics_main` 43줄 중 20 · `logs_main` 67 중 17 · `traces_main` 41 중 16.
help 문구 · 기본값 · choices 가 배선(매핑 · 환경 획득 · finish)과 같은 함수에 산다.

**테스트가 하는 것.** `--help` 는 format 스냅샷 15개(`tests/format/test_help.py`)와 contracts 의 `HELP_SCREENS` 8개(`test_cli.py:242`)가 본다.
그런데도 선언 161 이 생존했다 — 스냅샷이 top-level 화면만 담고 서브파서의 옵션별 `help=` 까지 전부 덮지 않거나, mutmut 의 테스트 선택이 그 화면을 지나지 않는 것 중 하나다.
어느 쪽인지는 이 조사에서 확정하지 않았다 — 열린 사실이다.

**#127 이 본 것.** 선언 161 은 전부 argparse 호출의 문구 · 기본값이고 "동작이 아니다" 로 분류됐다(생존 분류 §2).
#127 은 `do_not_mutate_patterns` 로 argparse 를 빼는 예외를 제안했고(분모 6925 → 약 6760, 점수 85.4 → 약 87.5 %), 승인 전이라 넣지 않았다(§5-5).
선언이 배선과 한 함수에 있는 한 예외는 패턴(`add_argument` · `help=`)으로 걸어야 하고, 분리하면 파일 하나의 예외가 된다 — 부모 4-10 A 의 둘째 절반.


**예시 — 어떻게 바뀌면 닫히나.** ② 의 매핑 함수를 꺼내면 반쯤 생기는 경계를 끝까지 밀어 파일로 가르는 모양이다. 한 모양일 뿐이고 결정이 아니다.

```
# 지금
obs/adapters/cli.py        1,253줄 — 선언 · 매핑 · 환경 · run · 렌더 · finish 전부

# 예시
obs/adapters/parsers.py    선언만 — promql_parser() · metrics_parser() · … (argparse 호출 · help 문구 · choices)
obs/adapters/cli.py        매핑 · *_main · *_run · finish — 배선만
```

```toml
# pyproject.toml — 선언 파일 하나를 mutation 에서 뺀다. 지금은 add_argument · help= 패턴으로 걸어야 한다
[tool.mutmut]
do_not_mutate = ["obs/adapters/parsers.py"]
```

닫히는 것 — 선언 161 이 소스 안의 `# pragma` 없이, 설정 한 줄로 분모에서 빠진다. 파일을 가르지 않고 ② 의 `*_parser()` 함수만 꺼내도 "선언 = 함수 하나" 는 되지만, mutmut 의 예외는 함수 단위가 아니라 파일 · 패턴 단위다 — 파일로 가르는 이유는 그것뿐이다.

### 7. `doctor_main` — 같은 결함, 다른 범위

`doctor_main` 은 14줄이다(`cli.py:1240-1253`).
`doctor(load_config(), token_from_env())` 로 config · token 을 환경에서 직접 얻고(결함 ① · ⑤ 의 doctor 판), 결과를 `print` 로 바로 찍고 `sys.exit` 한다.
`finish` · `emit` · `spill` 을 쓰지 않는다 — 사람용이라 호출 디렉터리를 남기지 않는다.
Args dataclass 가 없다 — 옵션이 `--json` 하나다.

테스트 셋(`test_cli_main.py:47-85`)이 `cli.doctor` 를 모듈 패치하고 `cli_env` 로 env 를 바꾼다 — 17곳 중 3.
core 의 `doctor` 는 생존 28/102 이고 그 내용은 `Probe` 필드 · 토큰 없을 때의 `continue` 다(생존 분류 §3-C) — `doctor_main` 이 아니라 `doctor` 의 약속이고, "doctor 는 사람용이라 어디까지 약속인지는 사람이 정한다" 로 분류됐다.
`doctor_main` 자체는 생존 상위 30 에 없다.


**예시 — 어떻게 바뀌면 닫히나.** ① · ⑤ 의 처방을 그대로 받는다. 한 모양일 뿐이고 결정이 아니다.

```python
# 지금
def doctor_main(argv: Sequence[str] | None = None) -> None:
    ...
    rep = doctor(load_config(), token_from_env())          # env · transport 를 줄 길이 없다 — 테스트는 cli.doctor 를 monkeypatch
    ...
    sys.exit(0 if rep.ok else 1)

# 예시
def doctor_main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None,
                transport: Transport | None = None, out: Callable[[str], None] = print) -> None:
    env = os.environ if env is None else env
    ...
    rep = doctor(load_config(env), token_from_env(env), env=env, transport=transport)
    ...
    sys.exit(0 if rep.ok else 1)
```

```python
# 지금
monkeypatch.setattr(cli, "doctor", _fake_doctor(_report(False)))
cli.doctor_main(["--json"])

# 예시 — 진짜 doctor 가 fake transport 로 probe 한다. 보고서를 손으로 만들 필요가 없다
with pytest.raises(SystemExit) as ei:
    cli.doctor_main(["--json"], env=base_env, transport=FakeTransport(config=config, routes={}, fail="연결 거부"))
assert ei.value.code == 1
```

닫히는 것 — `cli.doctor` 패치 3 · `cli_env` 의 doctor 몫. `doctor` 자체의 생존 28(`Probe` 필드)은 core 의 약속이라 여기 밖이다.

### 8. 건강한 이음새 — 바꾸지 않을 것

- `Client.transport` 주입(`core.py:545`) — fake transport 가 꽂히는 자리. `make_client` · `make_loki` · `replay` fixture 전부 이것을 쓴다.
- core 연산이 `client` 를 인자로 받는다 — `summarize(client, …)` · `exemplars(client, …)`.
- `*_run` 의 `at` 인자 — 시각 고정.
- `finish` 의 `out` · `err` · `env` 인자(`cli.py:145-146`) — 있으나 `*_main` 이 안 쓴다.
- `main_guard(fn)` — 진입점이 함수를 받는다(`cli.py:173`).
- `*Args.validate()` 가 요청 앞에서 돈다(`LogsArgs` · `TracesArgs`) — 거부가 Client 없이 검사된다.
- `Evidence[V]` 가 제네릭이다(`core.py:355`) — typed 반환의 그릇이 이미 있다.

### 9. 결함 간 의존 — 무엇이 무엇과 묶이나

| 결함 | 단독으로 고칠 수 있나 | 묶이는 것 | 왜 |
|---|---|---|---|
| ① 주입구 | 예 | ⑤ 의 Client 갈래 | 주입구가 생기면 `from_env` 는 `bin/*.py` 경로에서만 돈다 — 미실행은 남지만 진입점의 몫이 된다 |
| ② 매핑 | 매핑 함수를 꺼내는 것은 단독 | ⑥ | 매핑을 `Namespace → Args` 순수 함수로 꺼내면 선언과 배선의 경계가 생긴다. 선언을 별도 자리로 옮기는 것은 그 위의 한 단계 더다 |
| ③ 튜플 | 아니오 | ④ | `RunResult` 를 dataclass 로 바꾸는 순간 첫 필드의 타입을 정해야 하고, 그것이 `Lines` 인가 환원 값인가가 ④ 다 |
| ④ typed 반환 | 아니오 | ③ · 렌더의 자리 | run 이 환원 값을 돌려주면 `*_lines` 호출이 `finish` 쪽으로 가고, 값 타입 열둘 + 원시 여섯을 담을 union · Generic 이 필요하다 |
| ⑤ 환경 산포 | 어댑터 쪽만은 단독 | core 시그니처 | 어댑터가 env 를 명시해 넘기는 것은 cli.py 안의 일이다. core 의 `env=None` 기본값을 없애는 것은 core 시그니처 변경이고 `load_config` · `spill` · `doctor` 의 호출자 전부가 따라온다 |
| ⑥ 선언 분리 | 예 | ② | 매핑 분리의 부산물로 반쯤 생긴다. 파일 분리는 추가 결정 |
| ⑦ doctor | 예 | ① · ⑤ | `doctor_main(argv, env=…, transport=…)` 꼴로 같은 처방. 다만 finish 경로를 안 쓰므로 ③ · ④ 와 무관 |

독립 묶음으로 정리하면 넷이다 — (①) · (② + ⑥) · (③ + ④) · (⑤). ⑦ 은 ① · ⑤ 의 doctor 판이다.
부모 §4③ 의 공동무효 물음으로 보면, ③ 과 ④ 는 함께 뒤집히고 나머지는 따로 뒤집힌다.

### 10. 수치 요약

| 결함 | 테스트의 결합 | mutation 생존(3차) | 커버리지 미실행 |
|---|---|---|---|
| ① 주입구 | 모듈 패치 10 + run 패치 4 | `from_env` 19 | `cli.py:170` · `core.py:558` |
| ② 매핑 | 디스패치 테스트 7(argv 표본 1~4) | `*_main` 101 | — |
| ③ 튜플 | 자리 읽기 33 | — | — |
| ④ run 렌더 | Window 자리 읽기 4 · run 경유 문구 단언 | `*_run` 59 | — |
| ⑤ 환경 산포(시계 포함) | `setenv` 15 · `cli_env` 5 · `at=` 72 | 14 (+ `from_env` 10) · 시계 2 | `core.py:558` |
| ⑥ 선언 | 스냅샷 15 + 8 | 161 | — |
| ⑦ doctor | `cli.doctor` 패치 3 | `doctor` 28(core 의 약속) | — |

## 논의 문서로 가져가는 것

- 결함은 일곱이고 독립 묶음은 넷이다 — (①) · (② + ⑥) · (③ + ④) · (⑤). ⑦ 은 ① · ⑤ 의 doctor 판.
- 부모 논의 §2 의 왜곡 ①②③ 은 여기의 ① · ③ · ④ 다. #127 이 더한 것은 ② 매핑 · ⑤ 환경 산포 · ⑥ 선언이다.
- ② 매핑은 어느 티어에도 배정되지 않은 자리다 — 규칙 파일이 `*_main` 을 "디스패치와 stdout 절제만" 으로 정했고, 매핑은 그 사이에 있다. 생존 101 중 78 이 필드 매핑이다.
- 기본값이 세 자리에 중복된다(`add_argument` · `getattr` · dataclass). `"1h"` 가 `cli.py` 에 15번.
- `--max-lines` · `--json` 은 Args 를 거치지 않고 `Namespace` 에서 `finish` 로 바로 간다 — 생존 12.
- ③ 과 ④ 는 공동무효다 — `RunResult` 의 첫 필드 타입이 곧 run 의 반환 계약이다. 값 타입은 환원 열둘 + 원시 여섯이다.
- ⑤ 의 절반은 이미 있다 — `finish` · `emit` 의 `env` 인자. 진입점이 안 쓴다. core 기본값 제거는 core 시그니처 변경이다.
- 시계는 ⑤ 의 한 갈래다 — `at` 주입이 이미 절반이고, 모자란 것은 `None` 분기(생존 `metrics_run #113` 류)와 `spill` 의 직접 읽기(생존 `spill #14`)다. 사람의 선택은 주입(2026-10-22) — `*_run` 쪽은 어댑터, `spill` 은 core 시그니처.
- ⑥ 의 "스냅샷 23개가 있는데 선언 161 이 생존한 이유" 는 확정하지 못했다 — 서브파서 help 의 미커버 또는 mutmut 테스트 선택. 열린 사실.
- `doctor_main` 은 ① · ⑤ 와 같은 꼴이고 ③ · ④ 와 무관하다. 테스트 결합은 패치 3 · env 5.
- 바꾸지 않을 것 — `Client.transport` · core 연산의 `client` 인자 · `at` · `main_guard(fn)` · `*Args.validate` · `Evidence[V]`.
