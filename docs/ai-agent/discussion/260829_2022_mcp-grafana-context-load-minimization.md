---
type: discussion
topic: ai-agent
subjects: [claude-code, mcp-grafana, ops-workflow-agent, ticket-engineer-agent, prometheus, loki]
status: active
ref-adrs: []
---

# mcp-grafana 를 두 하네스에 붙일 때의 컨텍스트 부하와 최소화 방안

## 계기

Feature #84 는 로컬 하네스(ops-workflow · ticket-engineer)에 `mcp-grafana` 를 MCP 서버로 붙인다(#87).
mcp-grafana 는 도구가 많다.
그 도구 정의가 두 하네스의 컨텍스트에 얼마나 실리는지, 최소화할 길은 무엇인지가 이 문서의 질문이다.

## 측정 — 도구 정의의 크기

mcp-grafana 바이너리를 로컬에서 stdio 로 띄워 `tools/list` 응답(JSON)을 쟀다.
토큰은 JSON 기준 약 3.6 자/토큰으로 환산한 추정치다 — 실제 tokenizer 값이 아니다.

| 구성 | 도구 수 | JSON | 추정 토큰 |
|---|---|---|---|
| v1.3.0 기본 | 72 | 95 KB | ~26k |
| v1.3.0 `--disable-write` | 57 | 70 KB | ~19k |
| **v0.15.2 `--disable-write` (배포본)** | **49** | **55 KB** | **~15k** |
| v1.3.0 `-enabled-tools prometheus,loki,datasource` | 15 | 23 KB | ~6.4k |
| v0.15.2 같은 3 카테고리 | 14 | 19 KB | ~5.3k |
| v1.3.0 prometheus 만 | 6 | 10 KB | ~2.7k |
| v1.3.0 loki 만 | 6 | 11 KB | ~3.0k |
| v1.3.0 datasource 만 | 3 | 2.5 KB | ~0.7k |

도구 하나가 크다 — `query_loki_logs` 2.4~3.6 KB, `query_prometheus` 1.7 KB, `alerting_manage_rules` 3~6 KB.
쓰지 않을 카테고리(alerting · oncall · sift · pyroscope · dashboard · incident …)가 배포본 49개 중 35개다.

`-enabled-tools` 는 **카테고리** 목록이지 도구 이름 목록이 아니다.
서버측 최소 입도는 카테고리다 — prometheus 카테고리를 켜면 6개가 다 온다.

## Claude Code 는 어떻게 싣나 — 전부 실리지 않는다

Claude Code 는 MCP 도구 정의를 **기본적으로 지연 로드**한다(tool search).
세션 시작 시 컨텍스트에 들어가는 것은 **도구 이름과 서버 instructions 뿐**이고, 전체 JSON 스키마는 그 도구를 실제로 쓸 때 `ToolSearch` 로 불러온다.
이 세션 자체가 그 증거다 — context7 도구가 "deferred" 로 떠 있고 스키마는 호출 전에 따로 로드했다.

따라서 상주 비용은 위 표의 15k 가 아니라 **이름 49개 분(수백 토큰)** 이고, 실제로 쓰는 도구의 스키마(1.7~3.6k)가 **호출 시점에** 얹힌다.
한 번 로드된 스키마는 그 세션 안에 남는다.

`/context all` 이 MCP 도구별 토큰을 보여 준다.
#87 이 끝나면 두 하네스에서 이것으로 실측해 이 표의 추정을 대체한다.

전 도구 로드 우려는 대부분 Claude Code 쪽에서 이미 해소된다 — **남는 비용은 (1) 이름 목록 (2) 호출한 도구의 스키마 (3) 도구 출력**이다.
(3) 이 가장 크다.
로그 조회 한 번이 1000줄을 돌려주면 스키마 몇 개 분을 한 번에 넘는다.

## 옵션

### A. 아무것도 안 한다 — 지연 로드에 맡긴다

- 상주 비용 수백 토큰. 쓰는 도구만 스키마가 붙는다.
- 이름 49개가 매 턴 보이므로 모델이 관계없는 도구(oncall · incident …)를 고를 여지가 생긴다 — 토큰보다 **선택 잡음**이 비용이다.
- 이기는 조건: 실측 결과가 작고, 잘못 고르는 일이 관찰되지 않을 때.

### B. 서버측 카테고리 트림 — `-enabled-tools prometheus,loki,datasource`

- 49 → 14 도구. 이름 목록도 스키마 총량도 1/3.
- **공유 인스턴스라 kagent 에도 걸린다.** kagent `cluster-inspector` 의 화이트리스트는 `query_prometheus` · `query_loki_logs` · `list_datasources` · `list_prometheus_metric_names` 네 개뿐이라 이 세 카테고리 안이다 — 잃는 것이 없다.
- 서버 플래그라 하네스별로 다르게 줄 수는 없다. 하네스별 차등은 아래 E(클라이언트 deny)가 맡는다.
- 배포본 0.15.2 도 `-enabled-tools` 를 지원한다. #85 의 인자 변경 한 줄이다.
- 이기는 조건: 거의 항상. A 위에 얹는 것이라 잃는 것이 없다.

### C. MCP 를 쓰지 않는다 — Grafana `/api/ds/query` 를 스킬·스크립트로

- 하네스에 스킬 하나(`promql.sh` · `logql.sh` · `traceql.sh`)를 두고 curl 로 `/api/ds/query` 를 친다.
- 상주 비용 **0**. 스킬 본문은 호출될 때만 로드된다.
- Claude Code 공식 가이드의 방향과 같다 — *"MCP 보다 CLI·스킬을 우선하라"*.
- Tempo 는 어차피 curl 이다(#88). C 를 택하면 셋이 한 방식이 된다.
- 잃는 것: mcp-grafana 도구의 편의(라벨 탐색 · 메트릭 이름 검색 · 히스토그램 도우미). 모델이 PromQL·LogQL 을 직접 써야 하지만 그건 원래 잘 한다.
- **#84 의 전제를 되묻는다.** 로컬 하네스가 MCP 를 안 쓰면 #85 의 HTTPRoute 는 로컬에 불필요하다(Grafana 는 이미 노출돼 있다). #85 는 클러스터 내 agent 를 위한 것으로 남거나 지금 안 해도 된다. #86(Grafana SA) 은 그대로 필요하다.
- 이기는 조건: 실측 부하가 문제로 확인되거나, 하네스 셋의 접근 방식을 하나로 두고 싶을 때.

### E. 클라이언트 deny 로 도구를 컨텍스트에서 지운다 — 하네스별

- Claude Code 의 `permissions.deny` 에 `mcp__grafana__alerting_*` 같은 **bare-name glob** 을 두면 그 도구는 호출만 막히는 게 아니라 **컨텍스트에서 제거된다**(공식 문서 — 아래 §가이드 인용).
- 서버를 건드리지 않는다. 하네스마다 다른 집합을 볼 수 있다. kagent 무관.
- 도구 이름 단위다 — B 의 카테고리보다 입도가 곱다.
- `settings.json` 에 두면 커밋되어 두 하네스가 같은 규칙을 공유할 수 있다(토큰이 아니므로 커밋해도 된다).
- 잃는 것: 서버가 새 도구를 추가하면 deny 목록이 뒤처진다(allow 목록이 아니라 deny 목록이라 새 도구는 기본 노출). 반대로 allow 만으로는 컨텍스트에서 지워지지 않는다.
- 이기는 조건: B 를 서버에 얹기 싫거나(kagent 와 집합을 달리하고 싶을 때), B 위에 하네스별 미세 조정을 더 얹을 때.

### D. 출력 쪽을 조인다 — 어느 옵션에나 얹는다

- `MAX_MCP_OUTPUT_TOKENS`(Claude Code) 로 도구 출력 상한.
- mcp-grafana `-max-loki-log-limit`, 1.3.0 의 `-loki-guardrail-max-bytes` · `-loki-guardrail-max-range` 로 서버측 상한.
- Grafana Loki 데이터소스의 `maxLines: 1000` 은 사람용 값이다 — agent 경로에는 과하다.
- Claude Code 의 MCP 출력 상한은 기본 25,000 토큰, 경고는 10,000 토큰이다. 로그 조회에는 그보다 훨씬 낮게 잡을 이유가 있다.
- 도구 출력은 스키마보다 크다. **이것이 실질 부하의 주범**이므로 어느 옵션이든 이건 한다.

## Claude Code 공식 가이드가 가리키는 방향

공식 문서(`code.claude.com/docs` — `mcp` · `costs` · `permissions`, 2026-08-29 열람)를 직접 읽었다.
방향은 일관된다 — **컨텍스트에 상주하는 것을 줄이고, 필요한 순간에만 불러오라.**

### 1. MCP 도구는 지연 로드가 기본이고, 그 설계는 스킬과 같은 사상이다

> "Tool search keeps MCP context usage low by deferring tool definitions until Claude needs them. Only tool names and server instructions load at session start, so adding more MCP servers has minimal impact on your context window."

> "If you're building an MCP server, the server instructions field becomes more useful with tool search enabled. Server instructions help Claude understand when to search for your tools, **similar to how skills work**."

즉 Claude Code 는 MCP 서버를 "도구 묶음"이 아니라 **"언제 찾아야 하는지를 설명하는 한 줄 + 필요할 때 펼치는 스키마"** 로 다룬다.
서버 instructions 와 도구 description 은 각 2 KB 에서 잘린다 — *"Keep them concise ... put critical details near the start."*

`ENABLE_TOOL_SEARCH` 의 값: 미설정(전부 지연) · `true` · `auto`(정의 총량이 컨텍스트의 10% 미만이면 선로드, 넘으면 지연) · `auto:N` · `false`(전부 선로드).
서버 하나를 예외로 항상 싣고 싶으면 `.mcp.json` 의 `alwaysLoad: true` — 단 *"Use this for a small number of tools that Claude needs on every turn."*

### 2. 그래도 CLI 가 MCP 보다 싸다고 명시한다

> "**Prefer CLI tools when available**: Tools like `gh`, `aws`, `gcloud`, and `sentry-cli` are still more context-efficient than MCP servers because they don't add any per-tool listing. Claude can run CLI commands directly."

> "**Disable unused servers**: Run `/mcp` to see configured servers and disable any you're not actively using."

지연 로드가 있어도 **이름 목록조차 없는 쪽이 더 싸다**는 것이 공식 입장이다.
옵션 C(curl 스킬)의 근거가 여기 있다.

### 3. 부피 큰 처리는 모델 밖(hook · skill · subagent)으로 내보내라

> "Custom hooks can preprocess data before Claude sees it. Instead of Claude reading a 10,000-line log file to find errors, a hook can grep for `ERROR` and return only matching lines, reducing context from tens of thousands of tokens to hundreds."

> "A skill can give Claude domain knowledge so it doesn't have to explore ... Skills load on-demand only when invoked, so moving specialized instructions into skills keeps your base context smaller. Aim to keep CLAUDE.md under 200 lines."

> "Running tests, fetching documentation, or processing log files can consume significant context. Delegate these to subagents so the verbose output stays in the subagent's context while only a summary returns to your main conversation."

이 셋은 관측 조회에 그대로 맞는다 — 로그 조회는 (a) 스크립트가 먼저 거르고 (b) 스킬로 절차를 싣고 (c) 큰 조회는 subagent 에 맡겨 요약만 받는다.
옵션 D 의 상위 형태다.

### 4. 도구를 컨텍스트에서 지우는 손잡이는 permissions 에 있다

> "Deny and ask rules also accept glob patterns in the tool-name position ... A tool matched by a bare-name glob deny rule is **removed from Claude's context**, the same as a bare tool name."

`mcp__<server>__<tool>` 패턴이고, allow 의 glob 은 `mcp__<server>__` 리터럴 접두 뒤에서만 된다.
옵션 E 의 근거다.

### 5. 출력 상한은 env 하나다

`MAX_MCP_OUTPUT_TOKENS` — 기본 25,000, 경고 10,000. 도구가 `_meta["anthropic/maxResultSizeChars"]` 로 자기 상한을 낼 수도 있다.

### 종합 — 가이드가 이 저장소에 말하는 것

가이드의 우선순위는 **CLI/스킬 > (지연 로드된) MCP > 선로드 MCP** 이고, 어느 경우든 **출력은 모델 앞에서 걸러라**다.
이 저장소는 이미 그 방향에 있다 — `kubectl`·`gh` 는 CLI 로 쓰고, 절차는 스킬에 있으며, CLAUDE.md 는 규약만 담는다.
관측 조회도 같은 결을 따르면 C(curl 스킬 + 필터 스크립트)가 가장 가이드에 가깝고, MCP 를 쓴다면 B+E 로 이름 목록을 줄이고 D 로 출력을 막는 것이 그 다음이다.
어느 쪽이든 mcp-grafana 를 클러스터에 두는 것(#85)은 클러스터 내 agent(kagent · 추후 트러블슈팅 agent)의 값이며, 로컬 하네스의 값과는 분리해서 봐야 한다.

## 부수 발견 — #85 에 걸리는 것

- 배포본은 **0.15.2**, 최신은 **1.3.0** 이다.
- 1.3.0 에는 `-server-auth-token` 이 있다 — 서버 자체가 Bearer 를 검사해 401 을 낸다.
  #85 는 "env 토큰 제거로 Grafana 가 401" 을 택했는데, 업그레이드하면 서버측 게이트라는 선택지가 하나 더 생긴다(둘은 겹칠 수 있다 — 서버 토큰은 문, Grafana 토큰은 신원).
- 1.3.0 에도 Tempo 도구는 없다(도구 목록 실측). #88 의 전제는 유효하다.
- 업그레이드 여부는 #85 착수 시 판단할 일이다. 이 문서는 관찰만 남긴다.

## 상대편에 서서

질문은 "MCP 도구가 컨텍스트를 얼마나 먹나"였고, 답은 "지연 로드라 생각보다 적다"다.
그러면 문제는 사라졌는가.
아니다 — **비용의 자리가 옮겨갔을 뿐이다.** 도구 이름 목록의 선택 잡음과 도구 출력 크기가 남는다.
B·E 는 전자를, D 는 후자를 줄인다. 전부 싸다.
C 는 MCP 자체를 접는 것이라 가장 확실하고 공식 가이드에도 제일 가깝지만, #84 의 로컬 쪽 설계를 되돌린다 — 실측 없이 택할 이유는 아직 없다.

## 미결

- #87 후 `/context all` 실측으로 표를 대체한다.
- B 를 #85 에 얹을지(인자 한 줄) · E 를 #87 에 얹을지 — 사람의 것.
- D 의 값(출력 상한) — 코드의 관할. 티켓에서 정한다.
- C 로 갈지는 실측 뒤.
