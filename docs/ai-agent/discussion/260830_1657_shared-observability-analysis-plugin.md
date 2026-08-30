---
type: discussion
topic: ai-agent
subjects: [claude-code, claude-code-skills, kagent, strands-agents, prometheus, loki, tempo, ops-workflow-agent, ticket-engineer-agent]
status: active
ref-adrs: []
ticket: 90
related: [260830_1642_shared-harness-code-across-repos.md, 260830_1725_portable-context-isolation-conventions.md, 260829_2022_mcp-grafana-context-load-minimization.md, ../../homelab/discussion/260829_2038_raw-observability-api-read-only-enforcement.md]
---

# 관측 분석 기능을 범용 공통 모듈로 — 구조와 구현 제안

## 계기

앞 논의(`260830_1642`)는 "두 하네스가 같은 코드를 갖는다" 를 문제로 잡고 공식 공유 수단(플러그인)을 확인했다.
이 문서는 **관측 분석 기능 하나**로 범위를 좁히고 두 요구를 받는다.

1. 로그·트레이스·메트릭 분석은 데이터가 커서 컨텍스트를 쉽게 오염시키면서도 정확한 분석을 요구한다. 체계가 필요하고, 체계는 볼륨이 커진다. 그 볼륨을 하네스마다 사본으로 둘 수 없다.
2. Claude Code 만이 아니라 **여러 agent 애플리케이션이 같은 기능을 쓸 수 있어야 한다.** kagent 가 쓸 수 있으면 완벽하다.

하네스 메커니즘(티켓 절 파서 등)의 공유는 이 문서의 범위 밖이다 — 나중에.
#90 의 `obs-query`(스크립트 3개, 출력 절제)는 이 기능의 씨앗이지 완성이 아니다.

후속 조사(`260830_1725` — 컨텍스트 분리의 범용 규약)의 결론을 이 문서에 **반영했다**: 규약은 없고 MCP `tools/call` 의 구조적 격리가 최소공통분모이며, 결과 바운딩은 코어의 책임이고, 해석의 자리(호스트 / 코어 내 LLM)는 호스트가 고른다.

## 1. 소비자 — 누가 어떻게 도구를 붙이는가 (실측)

| 소비자 | 런타임 | 도구를 붙이는 방식 | 지금 관측 접근 |
|---|---|---|---|
| ops-workflow · ticket-engineer 하네스 | Claude Code (로컬 macOS) | 스킬 + PATH 의 스크립트(Bash). MCP 는 도구 정의 상주 비용 때문에 안 쓰기로 함(`260829_2022`) | #90 `obs-query` — Grafana 프록시 GET, 로컬 사본 둘 |
| kagent Agent (`cluster-inspector` 등) | 클러스터 내, `kagent.dev/v1alpha2 Agent` CR | **`RemoteMCPServer`(STREAMABLE_HTTP) + `toolNames` 화이트리스트**. 절차는 `systemMessage` 텍스트 | `grafana-mcp-server`(mcp-grafana) 의 raw 도구 4개 — `query_prometheus`·`query_loki_logs`… |
| `careerhub-incident-agent` | 클러스터 내 K8s Job, **Strands Agents(Python)** | Python 함수 `@tool` 직접 등록. `PROM_URL` env 로 Prometheus 직결 | Prometheus 만, 직결 |

셋의 공통점: **모두 결국 함수를 부른다** — Bash 로, MCP 로, Python import 로.
셋의 차이는 **호출 껍데기**뿐이다.
그러므로 공통화의 단위는 "Claude Code 플러그인" 이 아니라 **껍데기 없는 코어**이고, 플러그인·MCP 서버·Python 패키지는 그 코어의 어댑터다.

## 2. 구조 — 코어 하나, 어댑터 셋

```
obs-toolkit/  (가칭 · 독립 저장소)
├── obs/                        # ★ 코어 — 순수 Python, 표준 라이브러리만
│   ├── core.py                 #   Client(GET 유일) · Window · Evidence · budget · spill
│   ├── metrics.py logs.py traces.py   # 환원 연산 (§3-2)
│   ├── investigate.py          #   절차를 코드로 (§3-4) → Bundle · (선택) 코어 내 LLM → Finding
│   └── adapters/
│       ├── cli.py              #   promql/logql/traceql/obs-investigate 명령 — Claude Code 로컬
│       ├── mcp.py              #   MCP 서버 (streamable HTTP · stdio) — 셸 없는 호스트(kagent). 도구 ≈ 9개, outputSchema 필수
│       ├── a2a.py              #   A2A 서버 (선택) — kagent·ADK·Strands 가 `type: Agent` 로 부를 때
│       └── strands.py          #   @tool 래퍼 (선택 의존)
├── prompts/                    # 해석 규칙·Finding 계약·절차 설명 — 단일 원천 markdown (코어 내 LLM 도 이것을 쓴다)
├── tests/ + fixtures/          # 녹화 응답으로 도는 pytest (§3-6)
├── .claude-plugin/plugin.json  # 저장소 루트 = 플러그인 루트
├── skills/obs-query/ skills/obs-investigate/ agents/obs-analyst.md hooks/hooks.json
├── deploy/                     # Dockerfile (코어 + mcp 의존) — 매니페스트는 jyoliar-k8s 가 가진다
└── pyproject.toml              # 패키지 `obs` · extras: [mcp], [strands]
```

### 2-1. 어댑터별 연결

| 소비자 | 어댑터 | 설치·연결 | 원본 파일의 자리 |
|---|---|---|---|
| Claude Code 하네스 | `cli` + 플러그인 | 하네스 `settings.json` 의 `extraKnownMarketplaces` + `enabledPlugins` 로 선언. SessionStart hook 가 `PATH`·`PYTHONPATH=${CLAUDE_PLUGIN_ROOT}` 를 env 파일로 export | `${CLAUDE_PROJECT_DIR}/tmp/obs/` |
| kagent | `mcp` 서버 (+ 선택 `a2a`) | `deploy/Dockerfile` 이미지 → jyoliar-k8s 에 Deployment + Service + `RemoteMCPServer`(prometheus ns, 기존 `grafana-mcp-server` 와 같은 패턴). Agent CR 은 `toolNames` 로 고른다 | 서버 pod 의 임시 저장. 도구 응답은 `structuredContent`(환원물) + `resource_link`(원본 URI) — **kagent 은 도구 결과를 자르지 않으므로**(실측: A2A 서브에이전트 결과도 truncation 없음) 바운딩은 전적으로 코어의 `budget` 이다 |
| Strands (`incident-agent`) | Python import | `pip install obs-toolkit[strands]`(git URL·태그 고정). `from obs.adapters.strands import tools` | Job 의 로컬 디스크 |

코어가 표준 라이브러리만 쓰는 이유가 여기 있다 — Claude Code 쪽은 **설치가 없다**(플러그인 디렉터리가 곧 패키지).
MCP SDK·Strands 는 extras 라 컨테이너에서만 깔린다.

### 2-2. 인증·경로 — agent 는 물리를 모른다

**agent 는 논리 이름만 안다.** `metrics` · `logs` · `traces`(테넌트가 늘면 `logs:careerhub` 처럼 접미). 호스트·프록시 경로·데이터소스 uid 는 코어의 **설정 해석 계층**(`core.Config`)이 푼다 — env → 설정 파일(`~/.config/obs-toolkit/` 또는 `${CLAUDE_PLUGIN_DATA}`, 클러스터는 ConfigMap/Secret) → 내장 기본값. 사람이 한 번 놓으면 agent 는 영원히 모른다.

세 규칙이 따른다.
1. 호출 인터페이스(CLI 인자·MCP 도구 인자·Python 시그니처)에 URL·uid 가 없다. `--uid` 같은 물리 인자를 두지 않는다 — 논리 이름을 받는다.
2. **오류도 물리를 말하지 않는다.** `401 — logs 백엔드 인증 실패. 사람에게: 토큰 확인(obs doctor)` 처럼 논리 이름·상태·다음 행동만. URL 은 사람용 진단 명령 `obs doctor` 가 보여준다.
3. **문서(SKILL.md · systemMessage)에 경로를 쓰지 않는다.** 경로는 운영 지식이고 그 자리는 코드(GitOps)와 `doctor` 출력이다 — ops-workflow §2 "어떻게 동작하나는 문서가 답하지 않는다" 와 같은 원리.

효과: 게이트웨이 호스트·uid 가 바뀌어도 스킬·프롬프트는 안 바뀐다. 로컬 Claude Code 와 클러스터 내 kagent 가 **같은 호출**로 다른 물리 경로를 탄다. agent 가 URL 을 모르면 스크립트 밖에서 `curl` 로 우회 조립할 단서도 준다(강제는 아니다 — 강제는 게이트웨이·Grafana 다).

물리는 이렇다(사람의 기록용 — agent 가 볼 문서가 아니다).
`OBS_GRAFANA_URL` + `OBS_GRAFANA_TOKEN`.
로컬은 `https://obs.mg.jyo-liar.com`(agent 게이트웨이, GET 만), 클러스터 내는 `http://monitoring-grafana.prometheus.svc`(#84 가 예고한 경로).
토큰은 같은 Grafana SA(`read-for-agent`, #86) — 로컬은 `settings.local.json`, 클러스터는 Secret → env.
⚠ 클러스터 내 경로는 게이트웨이를 지나지 않는다. Prom·Loki 는 Grafana 가 메서드를 거르지만 **Tempo 는 코어의 GET 유일 진입점이 유일한 겹**이다(`260829_2038`). 코어에 다른 메서드를 만드는 함수가 없다는 것을 테스트가 지킨다.

### 2-3. "MCP 는 안 쓴다" 와의 정합

`260829_2022` 가 버린 것은 **mcp-grafana 의 raw 도구 집합**이다 — 도구가 많고 응답이 원본이라 컨텍스트를 두 번 먹는다.
여기서 kagent 에 주는 MCP 는 다르다.
- 도구가 **환원 연산 ≈ 9개**(`red`·`compare`·`histogram`·`templates`·`exemplars`·`critical_path`·`investigate_bundle`·`investigate`·`raw`)로 적다.
- 응답이 **환원물**이다 — `outputSchema` 로 고정된 `structuredContent` 수십 줄, 원본은 서버에 남고 `resource_link` 로만 가리킨다. MCP 스펙에 결과 크기 지침이 없으므로 이 바운딩은 코어가 집행한다.
- 로컬 Claude Code 는 여전히 CLI 를 쓴다 — MCP 서버를 등록하지 않는다. MCP 는 **파일 시스템·셸이 없는 소비자(kagent)를 위한 어댑터**다(`260829_2022` 의 "CLI > MCP" 는 셸이 있는 호스트의 비교이고, 거기서는 여전히 참이다 — `260830_1725` §5).

즉 결정은 "MCP 를 쓰지 않는다" 가 아니라 "**원본을 돌려주는 도구를 모델에 노출하지 않는다**" 로 다시 적히고, 그 결정은 어댑터가 아니라 코어(환원 연산만 공개)가 지킨다.

### 2-4. pin·갱신·steward

- 저장소는 태그로 릴리스한다. Claude Code 마켓플레이스 항목은 `sha`, 컨테이너 이미지는 태그, pip 는 git 태그 — 셋이 **같은 커밋**을 가리키는지가 conformance 의 검사 항목이 된다.
- `obs-toolkit` 은 정책이 실리지 않는 순수 기능이다. steward 가 관리하되 지위는 "피관리 하네스" 가 아니라 **공용 라이브러리**다 — 갱신 계기는 정책 변경이 아니라 기능·정확도다. steward 의 쓰기 경계에 넣을지는 사람이 정한다(§7).
- 피관리 agent 는 플러그인 캐시(`~/.claude/plugins/…`)를 고칠 수 없다 — 설치 위치가 프로젝트 밖이라 각 하네스의 guard-write 가 이미 거부한다. "자기 도구를 스스로 고치지 않는다" 가 공짜로 강제된다.

## 3. 기능 — 정확한 분석을 컨텍스트 밖에서

### 3-1. 원칙: 세 층, 아래층만 원본을 본다

```
[원본]  Prometheus·Loki·Tempo 응답 (KB~MB)
   │  결정론적 환원 — 코어 (obs/*.py)            ← 원본을 보는 유일한 층. 계산이지 해석이 아니다
[환원물]  집계·패턴·분위수·임계경로·차이 (수십 줄) + 원본 포인터
   │  해석 — 모델. 자리는 호스트가 고른다: 호스트 모델(Claude Code fork analyst / kagent Agent / Strands agent)
   │         또는 코어 내 LLM(`investigate`, 자기 키 — 결과를 안 자르는 호스트용)   ← 환원물을 여러 개 보고 가설을 세운다
[소견]   Finding 목록 (구조화 · 근거 첨부 · 재현 가능)
   │
[결정]   주 대화 · 티켓 코멘트 · Discord 게시 — 원본도 환원물도 보지 않는다
```

정확도는 **위층이 아니라 아래층에서** 나온다.
모델이 로그 5,000줄을 읽고 "많이 실패했다" 고 하는 것보다, 코어가 "`level=error` 312건, 그중 템플릿 `dial tcp … i/o timeout` 287건(92%), 첫 발생 14:02:11" 을 내는 쪽이 옳고 싸다.
모델의 일은 그 숫자들을 **연결**하는 것이고, 그 일은 어느 모델·어느 런타임이든 같다 — 그래서 범용이 된다.

### 3-2. 환원 연산 — 코어가 갖는 것

전부 표준 라이브러리 Python, dataclass 로 타입을 고정한다. 모든 함수는 `Window` 를 받고 `Evidence` 를 돌려준다.

**메트릭 (`metrics.py`)**
- `summarize(series)` — 시계열마다 n·min·p50·p95·max·last·기울기.
- `compare(query, window, baseline)` — 같은 질의를 두 창(지금 / 1일 전 같은 시각 / 직전 창)에 던져 **차이**만 낸다. "이상" 은 절대값이 아니라 기준선 대비다.
- `top(query, k, by)` — 레이블 축 상위 k. 카디널리티 폭발을 코어가 막는다.
- `red(service, window)` — Rate·Errors·Duration 세 질의를 한 번에. 서비스 삼각측량의 표준 진입.

**로그 (`logs.py`)**
- `histogram(selector, window, by=level|app|pod)` — `count_over_time` 으로 **줄을 받기 전에 분포**를 본다. (`detected_level` 레이블이 실측에서 보였다 — #90.)
- `templates(selector, window, k)` — 줄을 받되(상한 있음) 숫자·ID·시각을 마스킹해 **템플릿으로 군집**한다(Drain 류의 단순 변형). "템플릿 · 건수 · 첫/마지막 시각 · 예시 1줄". 5,000줄이 20줄이 된다.
- `around(selector, ts, ±duration, limit)` — 특정 시각 전후 문맥. 트레이스·메트릭이 찍은 시각으로 들어온다.
- `first_seen(template, window)` — 이 패턴이 언제 시작됐나. 변화점이 단서다.

**트레이스 (`traces.py`)**
- `exemplars(q, window, k)` — 느린 것·오류·정상을 각각 k 개. "대표" 를 코어가 고른다.
- `critical_path(trace)` — span 트리의 임계경로만. #90 의 "느린 span top" 을 부모-자식 관계로 바로잡은 것.
- `service_graph(traces)` — 호출 그래프와 엣지별 p95·오류율. 어느 홉이 문제인가.
- `diff(trace_slow, trace_normal)` — 같은 루트 이름의 두 트레이스를 span 이름으로 정렬해 차이만.

**공통 (`core.py`)**
- `Client.get` — GET 유일 진입점(#90 그대로).
- `Config` — 논리 이름(`metrics`·`logs`·`traces`) → 물리(base URL·uid·토큰) 해석. env → 설정 파일 → 내장 기본값. agent 쪽 인터페이스에는 물리가 없다(§2-2).
- `doctor` — 사람용 진단: 해석된 물리 경로·연결·인증을 보여준다. 오류 메시지가 agent 에게 숨기는 것을 여기서 사람이 본다.
- `Window` — 시작·끝·기준선을 한 값으로. "언제" 가 소견에 자동으로 붙는다.
- `Evidence` — `query · window · backend · value · raw_ref`. `raw_ref` 는 어댑터가 정한다(파일 경로 / `bundle_id`).
- `budget` — 한 조사에서 나갈 총량·질의 횟수 상한. 넘으면 멈추고 "좁혀라" 고 말한다.

### 3-3. 출력 계약 — Finding

모델이 결정 층에 돌려주는 것은 산문이 아니라 이 목록이다. 계약은 `prompts/finding.md` 한 곳에 있고 SKILL.md·kagent `systemMessage`·Strands 프롬프트가 그것을 **인용**한다.

```python
@dataclass
class Finding:
    claim: str                 # "posting-service 의 gRPC 오류율이 14:02 부터 12% → 이전 창 0.1%"
    evidence: list[Evidence]   # 질의·창·값·원본 포인터 — 재실행 가능
    signals: list[str]         # metrics / logs / traces 중 뒷받침한 것
    confidence: str            # high(두 신호 이상 일치) / medium(한 신호) / low(추정)
    next_check: str | None     # 확인하려면 다음에 볼 것
```

- **신호 둘 이상이 일치할 때만 high.** 메트릭이 오류율 상승을 말하고 로그 템플릿이 같은 시각에 시작하고 트레이스 임계경로가 같은 홉을 가리키면 high 다.
- **"데이터 없음" 과 "0" 을 구분한다.** 코어가 구분해 내고 Finding 도 구분해 적는다. 없는 데이터를 정상으로 읽는 것이 가장 흔한 오진이다.
- **모든 claim 에 Evidence 가 붙는다.** 없으면 `low` 로 강등되고 "추정" 이라고 적힌다.
- 결정 층은 Finding 을 **그대로** 옮긴다 — 티켓 코멘트(ops-workflow §6: 관찰은 티켓에), Discord(incident-agent).

### 3-4. 절차를 코드로 — `investigate()`

사람의 요구 "체계적인 구조" 는 여기다.
절차를 프롬프트 텍스트로 두면 소비자마다 복제되고 모델마다 다르게 밟는다.
그래서 **결정론적 부분은 코드**로 내린다 — `investigate(symptom_scope, window) -> Bundle`:

1. **범위 고정** — 서비스/네임스페이스 + 시각 → `Window` 와 기준선. 조사 id 발급.
2. **삼각측량 (메트릭)** — `red()` + `compare()`. 후보 서비스와 **변화 시각**.
3. **분포 (로그 집계)** — 후보에 `histogram(by=level)`·`histogram(by=pod)`.
4. **패턴 (로그 템플릿)** — 오류 창에 `templates()` + `first_seen`. 여기서 처음 로그 **줄**(템플릿당 예시 1줄).
5. **경로 (트레이스)** — 변화 시각·오류 조건으로 `exemplars()` → `critical_path()` → 정상 대표와 `diff()`.
6. **번들** — 2~5 의 환원물 전부 + `manifest`(던진 질의 전부, 재현용). 예산 초과면 어디서 멈췄는지 포함.

모델의 일은 7 뿐이다 — **교차 확인과 Finding 작성**: 2·4·5 의 시각과 대상이 일치하나. 일치하면 high, 어긋나면 그 어긋남이 다음 Finding 이다.
싼 신호(집계)로 방향을 정한 뒤에만 비싼 신호(줄·span)를 여는 순서가 코드에 박혀 있어, 어느 소비자가 불러도 같은 예산으로 같은 것을 본다.

이 결정론적 절차가 **`investigate_bundle`** 이고, CLI 명령·MCP 도구·Python 함수로 똑같이 노출된다.

그 위에 **`investigate`** 를 둔다 — 같은 번들을 만든 뒤 **코어 안의 LLM(자기 키)** 이 7 을 수행해 `Finding[]` 만 돌려준다.
시도 과정까지 코어에 남으므로 호스트에 subagent 가 없거나 결과를 안 자르는 호스트(kagent)에서도 오염이 0 이다.
비용은 별도 키·과금이다 — MCP sampling(호스트 토큰 차용)은 2026-07-28 개정에서 deprecated 라 빌릴 수 없다(`260830_1725` §1-1, `260817_1512`).
선택 활성이다 — 키가 없으면 `investigate_bundle` 만 산다.

| 도구 | 안에 LLM | 반환 | 누가 쓰나 |
|---|---|---|---|
| `investigate_bundle` | 없음 | `Bundle` | Claude Code(fork 가 받아 호스트 모델이 해석 — 구독 토큰, 코어 키 불필요) |
| `investigate` | 있음(자기 키) | `Finding[]` | kagent 등 결과를 안 자르는 호스트, 또는 세 소비자의 Finding 품질을 같게 하고 싶을 때 |

kagent 의 `systemMessage` 는 "증상을 받으면 `investigate` 를 부르고 Finding 을 그대로 보고한다" 한 단락이면 된다.

### 3-5. 두 진입점 — 언제 어느 것을

| | 원시 연산 (`red`·`templates`… / `obs-query`) | `investigate_bundle` / `investigate` (/ `obs-investigate` fork) |
|---|---|---|
| 무엇 | 환원 연산 하나 = 질의 한두 개. 요약 + 원본 포인터 | 절차 전체. 번들 하나 |
| 언제 | 답이 한 질의로 나온다 — `up`, 파드 로그 30줄, 트레이스 하나 | "왜 느린가", "무엇이 바뀌었나" — 답을 모른다 |
| Claude Code | 주 대화가 직접. 질의당 ≤40줄 | fork(`obs-analyst`)가 `investigate_bundle` 을 받아 Finding 만 반환. 시도는 버려진다 |
| kagent | 도구 하나 호출 | `investigate` 한 호출 — Finding 이 응답. 번들·시도는 코어에 남는다 |

주 agent 가 원시 연산을 세 번 이상 부르고 있다면 `investigate(_bundle)` 를 불렀어야 할 신호다 — 스킬 본문과 `systemMessage` 에 그렇게 적는다.

SKILL.md 는 Agent Skills 오픈 스펙의 6필드(`name·description·license·compatibility·metadata·allowed-tools`)만 써서 쓴다 — Codex·Copilot·Gemini CLI 등 40+ 클라이언트가 같은 형식을 읽는다.
`context: fork`·`agent` 는 Claude Code 전용 확장이라 **플러그인 쪽 스킬에만** 얹는다(스펙 외 필드는 타 도구가 거부한다).

### 3-6. 테스트 — 클러스터 없이

환원 연산과 `investigate` 는 순수 함수다(HTTP 는 `Client` 하나로 격리).
실제 응답을 녹화해 `fixtures/` 에 두고(토큰·호스트 없음) pytest 로 검증한다.
GET 유일성도 테스트다 — `Client` 외에 `urllib`·`http` 를 import 하는 모듈이 없어야 통과.
정확도의 절반은 여기서 산다: 군집이 잘못 묶이거나 임계경로가 틀리면 그 위의 모든 해석이 틀린다.
실제 장애(postmortem 대상)의 응답을 회귀 fixture 로 쌓는다 — 오진 사례가 테스트가 된다.

## 4. 이행 — 단계

| 단계 | 내용 | 산출 |
|---|---|---|
| **0. 코어 + CLI** | `obs-toolkit` 저장소 · `obs/core.py` + CLI 어댑터 · #90 스크립트 이관(플러그인 루트·PATH·루트 경로 수정) · 두 하네스 `enabledPlugins` + 사본 삭제 | #90 의 스킬이 플러그인으로. 하네스 diff 는 settings 한 블록 |
| **1. 환원 연산** | `metrics/logs/traces.py` + fixture 테스트 | `templates`·`compare`·`critical_path` 동작 |
| **2. 절차** | `investigate_bundle` + `Bundle`·`Finding` + `prompts/` · Claude Code 는 `obs-investigate` fork + `obs-analyst` | 증상 → 번들 → Finding 이 한 호출로 |
| **3. kagent** | `adapters/mcp.py`(outputSchema·resource_link·budget) + `deploy/Dockerfile` → jyoliar-k8s 에 Deployment·`RemoteMCPServer` · `cluster-inspector` 의 grafana 도구를 이것으로 교체 · 오염 실측 후 필요하면 `investigate`(코어 내 LLM) 활성 · 선택 `a2a.py` | kagent 가 같은 코어를 쓴다. mcp-grafana 는 남겨도 되고 걷어도 된다 |
| **4. Strands** | `adapters/strands.py` · `incident-agent` 의 Prometheus 직결을 코어로 | 셋째 소비자 |
| **5. 정확도** | 기준선 자동 선택 · `service_graph` · 장애 회귀 fixture | high 비율이 오르고 오진 사례가 fixture 가 된다 |

0 은 #90 의 후속, 1~5 는 각각 리프 티켓 감이다. 3 과 4 는 target 이 다른 저장소(jyoliar-k8s · incident-agent)다.
0 과 1 사이에 #90 을 머지해도 된다 — 복사본이 잠깐 살아 있는 비용보다 이관을 기다리는 비용이 크다.

## 5. 버리는 안

- **Claude Code 플러그인만** — kagent·Strands 가 못 쓴다. 플러그인은 어댑터 하나여야 한다.
- **MCP 서버만** — 로컬 Claude Code 에 도구 정의 상주 비용을 다시 낸다(`260829_2022`). 로컬은 CLI. 반대로 **CLI 만** 도 안 된다 — kagent 에는 셸이 없다.
- **호스트 토큰을 빌리는 코어 내 LLM(MCP sampling)** — deprecated 이고 우리 소비자 중 지원 클라이언트 0. 코어 내 LLM 은 자기 키다.
- **mcp-grafana 위에 환원을 얹는다** — 환원은 어차피 우리가 짜야 하고, 그 아래 raw 도구가 모델에 그대로 보인다.
- **절차를 프롬프트로만** — 소비자마다 복제되고 예산이 안 지켜진다. 결정론적 부분은 코드.
- **하네스마다 사본** — 이 문서의 계기.
- **LLM 에게 로그 군집을 맡긴다** — 템플릿 추출은 결정론적이어야 재현된다. 모델은 군집 **이름 붙이기**까지만.

## 6. 미확인

- 플러그인 스킬이 `context: fork` + `agent:` 로 **같은 플러그인의 agent** 를 지정할 때 이름 공간 — 문서에서 확인 못 함. ops-workflow 의 `context-scout` 가 프로젝트 수준에서 같은 패턴을 쓰고 있어 fork 자체는 검증됐다.
- `CLAUDE_PLUGIN_ROOT` 가 플러그인 hook 밖 Bash 에서 보이는가(앞 논의). 안 보이면 SessionStart 에서 env 파일로 넘긴다 — 검증된 메커니즘.
- kagent 은 도구 응답을 자르지 않는다(확인됨 — `260830_1725`). 남은 것은 `KAgentMcpToolset` 이 `structuredContent` 를 모델에 어떻게 싣는가(텍스트 직렬화? JSON?) — `cluster-inspector` 로 실측.
- Tempo TraceQL metrics(`/api/metrics/query_range`)가 이 버전에서 켜져 있는가. 켜져 있으면 `service_graph` 의 절반을 서버가 계산한다.
- Strands 의 `@tool` 이 dataclass 반환을 어떻게 직렬화하는가 — JSON 으로 내리면 된다.

## 7. 결정할 것 — 사람에게

1. 저장소 이름·조직(`jyoliar-lab/obs-toolkit`?)과 패키지 이름.
2. steward 의 관리 대상에 넣을 것인가(쓰기 경계 `$OBS_TOOLKIT_ROOT` — hook 개정은 사람의 일) — 아니면 일반 코드 저장소로 두고 ticket-engineer 가 티켓으로 고치는가. 제안은 **후자** — 정책이 안 실린 순수 기능이라 steward 의 이유(§0)가 없다.
3. #90 PR 을 지금 머지하고 0 단계에서 이관할 것인가, 0 단계로 PR 을 다시 자를 것인가.
4. kagent 의 mcp-grafana 를 걷을 것인가(3 단계 후).
5. `investigate`(코어 내 LLM)를 처음부터 넣을 것인가, kagent 오염 실측 후 넣을 것인가 — 그리고 그 키·모델 공급 방식(`260830_1725` §7, `260817_1512`). 제안: `investigate_bundle` 먼저.
