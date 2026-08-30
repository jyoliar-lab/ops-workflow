---
type: discussion
topic: ai-agent
subjects: [claude-code, claude-code-skills, kagent, strands-agents, claude-agent-sdk]
status: active
ref-adrs: []
ticket: 90
related: [260830_1657_shared-observability-analysis-plugin.md, 260817_1512_subscription-auth-programmatic-claude-access.md, 260829_2022_mcp-grafana-context-load-minimization.md]
---

# 컨텍스트 분리를 코어가 소유할 수 있는가 — 범용 규약 조사

## 계기

앞 논의(`260830_1657`)는 관측 분석 기능을 "코어 하나 + 어댑터 셋" 으로 나눴다.
그런데 그 설계에서 **컨텍스트 오염 방지는 어댑터(Claude Code 의 fork, kagent 의 응답 크기)에 걸려 있었다.**
사람의 요구는 다르다 — 스크립트만이 아니라 **컨텍스트 분리 자체가 코어에 있어야** 한다. 어느 호스트(Claude Code · kagent · Codex · Strands · ADK …)가 불러도 같은 보장을 받도록.
그래서 물었다: **subagent 든 fork 든, 프레임워크를 가로지르는 컨텍스트 분리 규약이 있는가.**

조사일 2026-08-30. 1차 출처(스펙·공식 문서)를 읽었고, 인용은 원문이다.

## 1. 답 — 규약은 없다. 구조적 부산물만 있다

**"서브태스크를 별도 컨텍스트에서 돌리고 요약만 되돌린다" 를 규정한 벤더 중립 규약은 없다.**
MCP 의 Agents Working Group 헌장(2026-08-04)이 스스로 말한다:
> "Today, these systems are typically exposed as ordinary tools or through framework-specific integrations, leaving durable execution, capability discovery, delegation, and multi-turn interaction to ad hoc conventions."

표준화는 그 WG 에서 **진행 중**이고("agent-as-tool, remote-agent, and supervisor/sub-agent patterns, to determine whether an Agents Extension is needed"), 아직 없다.

그러면 무엇이 있나. 후보 셋을 보면 답이 갈린다.

### 1-1. MCP `tools/call` — 최소공통분모. 격리는 아키텍처의 부산물

우리 소비자 다섯(Claude Code · kagent · Codex · Strands · ADK)이 **전부 MCP 클라이언트**다.
MCP 아키텍처가 격리를 원칙으로 적는다:
> "Servers should not be able to read the whole conversation, nor 'see into' other servers — Servers receive only necessary contextual information; Full conversation history stays with the host"

즉 서버가 안에서 무엇을 하든(원본 수 MB 를 읽든, 자기 LLM 루프를 돌리든) **호출자는 `content`/`structuredContent` 만 본다.**
이것이 "코어가 격리를 소유한다" 의 유일한 범용 형태다 — 규약이 아니라 **구조**로.

세 제약이 따른다.
1. **서버 안의 LLM 은 자기 토큰으로 돈다.** 클라이언트 토큰을 빌리는 sampling 은 **2026-07-28 개정에서 deprecated**(SEP-2577: "Low adoption")이고, 다섯 소비자 중 지원 클라이언트는 **0** 이다(Claude Code ❌ · Codex ❌ · kagent ❌ 콜백 미배선 · Strands ❌ not planned · ADK 는 라이브러리만).
2. **결과 크기 바운딩은 스펙이 아니라 서버 책임이다.** 스펙에 크기 지침이 없다. 호스트별 대응이 다르다 — Claude Code 는 25k 토큰 초과 시 파일 참조로 치환(`MAX_MCP_OUTPUT_TOKENS`), **kagent 은 무제한**(A2A 서브에이전트 결과도 "truncation 없음"). 코어가 스스로 줄이지 않으면 kagent 에서 오염된다.
3. **장기 실행은 Tasks 확장에 기대는데 지원 클라이언트가 0** 이다(2025-11 실험판과 wire 비호환으로 재정의됨). 당분간 동기 호출 + 자체 예산, 또는 핸들 반환("Stateful Tools" 비규범 절)으로 폴링.

스펙이 주는 도구 셋이 마침 우리 설계와 맞는다:
- `outputSchema` + `structuredContent` — "Servers MUST provide structured results that conform to this schema." → `Finding`·`Bundle` 을 스키마로 고정.
- `resource_link` — "the tool will return a URI that can be subscribed to or fetched by the client" → 원본은 포인터로만.

### 1-2. A2A — 격리를 명시한 유일한 규약. 그러나 절반만 쓴다

A2A(1.0.x, Linux Foundation → AAIF 2026-08)는 **불투명 실행을 설계 원칙으로 적는다**:
> "From the client's perspective, the remote agent operates as an _opaque_ (black-box) system, meaning its internal workings, memory, or tools are not exposed."

반환도 우리 모양이다 — `Task{status, artifacts[], history[]}`.
채택: **kagent(모든 agent 가 A2A 서버 + `type: Agent` 클라이언트) · ADK · Strands · MS Agent Framework · CrewAI.**
미채택: **Claude Code · Codex · OpenAI Agents SDK**("we don't have immediate plans").
그러므로 A2A 는 "kagent 계열이 코어를 agent 로 부르는 경로" 지 범용은 아니다.
kagent v0.8 이 A2A agent 를 MCP 서버로도 노출하듯, **코어를 A2A 서버로 두고 MCP 로도 내는 이중 노출**이 실무 답이다.

### 1-3. Agent Skills 표준 — 격리 개념이 없다

agentskills.io(40+ 클라이언트: Claude Code · Codex · Copilot · Gemini CLI · Cursor · OpenCode …)의 정규 필드는 `name · description · license · compatibility · metadata · allowed-tools` 여섯뿐이다.
"progressive disclosure" 만 규정하고 subagent·fork 는 없다.
`context: fork` · `agent` · `background` 는 **Claude Code 전용 확장**이다 — 스펙 외 필드로 올리면 타 도구가 거부한다.
→ SKILL.md 는 "언제 어떤 도구를 어떻게 부르는가" 의 **지시서**까지다. 격리를 스킬에 걸 수 없다.

## 2. 호스트별 격리 프리미티브 — 어댑터가 얹는 층

| 호스트 | 프리미티브 | 격리 | 돌아오는 것 |
|---|---|---|---|
| Claude Code | subagent(`.claude/agents`) · `context: fork` 스킬 · 플러그인 `plugin:agent` | "runs in its own context window … returns only the summary". fork 는 이력 상속하되 "The fork's own tool calls still stay out of your conversation" | 최종 텍스트 |
| Codex CLI | `spawn_agent` 계열(stable · 기본 on) | 별도 thread. 가이드: "Return summaries from subagents instead of raw intermediate output" | 통합 응답 |
| kagent | `tools: - type: Agent`(A2A) · `isolateSessions: true` | 매 호출 새 context_id | `{"result", "subagent_session_id"}` — **무제한** |
| Strands | `.as_tool()` | "reset the agent's conversation context between invocations"(기본) | 텍스트 |
| ADK | `AgentTool` | 새 세션 + state 사본. "Agent B's answer is passed back to Agent A" | 마지막 content |
| OpenAI SDK | `agent.as_tool()` | "conversation state is not inherited automatically" | 최종 출력 |
| LangGraph/Deep Agents | subagent · supervisor `output_mode` | "Subagents quarantine heavy subtasks and return only final results" | 최종 메시지 |

전부 **같은 모양**(고립 컨텍스트 · 최종 결과만)이지만 **전부 호스트 전용**이다.
반대 방향 프리미티브도 있다 — OpenAI handoff("gets to see the entire previous conversation history"), Strands Swarm(공유 컨텍스트), ADK `sub_agents`(제어 이전). 격리가 아니라 위임이다. 헷갈리지 않는다.

## 3. 무엇을 내려보내고 무엇을 올려보내나 — 지침의 합의

규약은 없어도 **지침은 수렴**한다. 코어의 입력·출력 스키마가 여기서 나온다.

- 내려보낼 것(Anthropic 멀티에이전트 리서치): "Each subagent needs an **objective, an output format, guidance on the tools and sources to use, and clear task boundaries**." → `investigate` 의 입력 = 증상(objective) · 범위(boundaries) · 창(source) · Finding 스키마(format).
- 올려보낼 것(Anthropic 컨텍스트 엔지니어링): "returns only a condensed, distilled summary of its work (**often 1,000-2,000 tokens**)… the detailed search context remains isolated within sub-agents" → Finding 목록의 예산이 곧 이 수치다.
- 반론(Cognition, "Don't build multi-agents"): "Share context, and share full agent traces" — **쓰기 작업**에서 결정 충돌을 막기 위한 원칙이다. 관측 분석은 읽기 전용이고 결정은 결정 층(사람·주 agent)에 있다. 격리가 맞다.
- 비용(LangChain): 멀티에이전트는 "up to 15× more tokens". 격리는 공짜가 아니다 — 그래서 결정론적 환원이 먼저고 LLM 은 마지막이다.

## 4. 코어 설계로 번역 — 격리를 코어에 두는 두 수준

### 수준 1 — 구조적 격리: 코어 = 자기 바운딩 MCP 서버

원본이 서버를 떠나지 않는다. 도구 응답은 `outputSchema` 로 고정된 환원물(수십 줄)과 `resource_link`(원본 포인터)뿐이다.
`budget` 은 서버가 집행한다 — 호스트가 25k 에서 자르든(Claude Code) 안 자르든(kagent) 결과는 같다.
**모델의 해석은 호스트에 남는다** — 호스트 모델이 환원물을 보고 Finding 을 쓴다.
격리되는 것: 원본. 격리 안 되는 것: 환원물 여러 개를 오가는 **시도 과정**(호스트 subagent 가 있으면 거기서, 없으면 주 대화에).

### 수준 2 — 완전 격리: 코어가 해석까지 품는다

`investigate` 가 환원 뒤에 **서버 안의 LLM(자기 키)** 으로 Finding 을 쓰고, 호출자는 Finding 만 받는다.
시도 과정까지 서버에 남는다 — 호스트에 subagent 가 없어도 같다. 이것이 사람의 요구에 가장 가깝다.
비용: **별도 API 키·과금**(sampling 이 죽었으므로 호스트 토큰을 못 빌린다 — `260817_1512` 가 다룬 구독 vs API 문제가 여기서 다시 선다) · 모델이 코어에 고정된다(호스트가 Opus 여도 코어의 모델이 해석) · 코어에 프롬프트·평가가 생긴다.
이득: kagent 처럼 결과를 안 자르는 호스트에서도 오염이 0 · 세 소비자의 Finding 품질이 **같다**(같은 모델·같은 프롬프트·같은 fixture 로 평가).

### 제안 — 둘 다, 도구를 나눠서

| 도구 | 수준 | 안에 LLM | 반환 |
|---|---|---|---|
| `red` · `compare` · `histogram` · `templates` · `exemplars` · `critical_path` … | 1 | 없음 | 환원물 + `resource_link` |
| `investigate_bundle` | 1 | 없음 | `Bundle`(환원물 전부 + manifest) |
| `investigate` | 2 | **있음**(자기 키, 선택 활성) | `Finding[]` |

- 호스트에 좋은 subagent 가 있으면(Claude Code) `investigate_bundle` 을 fork 에서 받아 호스트 모델이 해석한다 — 구독 토큰으로, 코어 키 없이.
- 없거나 자르지 않으면(kagent) `investigate` 를 부른다 — 키가 코어에 있다.
- 같은 코어, 같은 환원, 같은 Finding 스키마. 다른 것은 **누가 마지막 해석을 하는가** 뿐이고, 그것은 호스트가 고른다.

### 노출 — 셋

1. **CLI** — 셸이 있는 호스트(Claude Code 로컬). 도구 정의 상주 없이, 같은 함수. 앞 결론(`260829_2022`) 그대로.
2. **MCP 서버**(streamable HTTP · stdio) — 셸이 없는 호스트(kagent). 도구 ≈ 9개. `outputSchema` 필수.
3. **A2A 서버** — kagent·ADK·Strands 가 `type: Agent` 로 부를 때. `investigate` 를 Task 로, Finding 을 Artifact 로.

Skills(SKILL.md)는 **스펙 6필드만** 써서 배포한다 — "언제 `investigate_bundle` 을 부르고 언제 `investigate` 를 부르는가". 격리 필드는 넣지 않는다(타 도구가 거부).
Claude Code 용 `context: fork` 는 플러그인 쪽 스킬에만 얹는다 — 어댑터의 일이다.

## 5. "CLI 가 모범 사례" 와 상충하는가 — 범위를 긋는다

앞 조사(`260829_2022`)는 MCP 를 버렸고 근거는 둘이었다.

| 근거 | 지금 |
|---|---|
| ① 도구 정의 상주 비용 — 공식 가이드 "CLI tools … don't add any per-tool listing" | **유효.** Claude Code 로컬에서 MCP 서버를 물면 도구 ≈9개의 설명이 안 쓰는 세션에도 상주한다 |
| ② raw 응답이 컨텍스트에 그대로 — mcp-grafana 의 도구가 원본을 돌려줬다 | **해소.** 환원 코어는 전송이 무엇이든 환원물만 돌려준다. MCP 의 문제가 아니라 mcp-grafana 의 문제였다 |

상충은 ①에 한정되고, ①은 **셸이 있는 호스트**에서만 성립하는 비교다.
kagent 에는 셸이 없어 CLI 라는 선택지가 없다 — "CLI > MCP" 가 성립할 조건이 거기엔 없다.

그러므로 결론은 "MCP 로 수렴" 이 아니라 **"코어는 전송 무관, 전송은 호스트가 고른다"** 다.

- Claude Code 로컬 — 앞 결론 그대로 **CLI**. MCP 서버를 등록하지 않는다. 같은 코어 함수를 스크립트가 부르므로 기능·격리 보장은 같다.
- kagent — MCP(또는 A2A). 대안이 없다.
- Strands — Python import.

이 절의 초고는 "MCP 가 1차 노출" 이라 적었다 — 과했다. 앞 결론과 정합하는 표현은 **"MCP 는 셸 없는 호스트를 위한 어댑터"** 다.
남는 정직한 비용: 어댑터가 하나 늘어(서버 · 컨테이너 · 배포) 유지 비용이 생기고, 그것은 **kagent 가 실제로 이 기능을 쓸 때만** 정당화된다. kagent 수요가 확실하지 않으면 MCP 어댑터는 뒤 단계로 미루고 코어 + CLI 를 먼저 만든다.

### `260830_1657` 에 대한 수정

- "해석은 모델의 일" → 해석의 **자리를 호스트가 고른다**(수준 1/2). 코어는 둘 다 제공한다.
- `investigate` 의 원본 포인터: 파일 경로(CLI) / `resource_link` URI(MCP) / Artifact(A2A) — 어댑터가 정한다. 코어는 `raw_ref` 추상.
- 노출 순서(§4 "노출 — 셋")는 우선순위가 아니라 목록이다 — Claude Code 는 CLI, kagent 는 MCP/A2A.

## 6. 미확인

- MCP 클라이언트 기능 매트릭스의 **현재본**(2025-11-25 태그본만 조회 가능). Codex·kagent 은 어느 판에도 없다.
- Claude Code 가 도구 9개짜리 MCP 서버를 물었을 때의 실제 상주 토큰 — Claude Code 는 CLI 를 쓰므로 당장은 필요 없는 실측이다. MCP 를 물어야 할 이유가 생기면 그때 잰다.
- kagent `KAgentMcpToolset` 이 `structuredContent` 를 모델에 어떻게 싣는가(텍스트 직렬화? JSON?).
- Strands · ADK 의 SKILL.md 지원 여부.
- Tasks 확장 스펙 전문(GitHub 트리 로드 실패) — overview·SEP-2663 으로 대체.
- 수준 2 의 키: Anthropic API 별도 과금인가, 다른 공급자인가 — `260817_1512` 의 결론에 의존.

## 7. 결정할 것 — 사람에게

1. 수준 2(코어 내 LLM)를 **처음부터** 넣을 것인가, 수준 1 로 시작해 kagent 실측 후 넣을 것인가. 제안: 수준 1 먼저 — `investigate_bundle` 이 있으면 Claude Code 에서는 이미 충분하고, kagent 의 오염 정도를 재 본 뒤 키를 결정한다.
2. 수준 2 의 모델·키 공급 방식.
3. A2A 노출을 kagent 단계(앞 문서 3단계)에 같이 할 것인가.

## 출처

- MCP 2026-07-28: 스펙 https://modelcontextprotocol.io/specification/2026-07-28/{architecture,server/tools,client/sampling,client/elicitation} · 개정 공지 https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/ · SEP-2577 · Tasks 확장 https://modelcontextprotocol.io/extensions/tasks/overview · Agents WG https://modelcontextprotocol.io/community/working-groups/agents
- A2A: https://a2a-protocol.org/latest/{specification,topics/key-concepts} · kagent https://kagent.dev/docs/kagent/examples/a2a-agents/ · kagent 서브에이전트 https://github.com/kagent-dev/kagent/blob/main/docs/architecture/a2a-subagents.md
- Agent Skills: https://agentskills.io/specification · Claude Code 확장 https://code.claude.com/docs/en/skills · Codex https://learn.chatgpt.com/docs/build-skills
- 호스트 프리미티브: Claude Code https://code.claude.com/docs/en/sub-agents · Codex https://learn.chatgpt.com/docs/agent-configuration/subagents.md · Strands https://strandsagents.com/docs/user-guide/concepts/multi-agent/agents-as-tools/ · ADK https://adk.dev/tools-custom/function-tools/ · OpenAI https://openai.github.io/openai-agents-python/tools/ · Deep Agents https://docs.langchain.com/oss/python/deepagents/subagents
- 지침: https://www.anthropic.com/engineering/multi-agent-research-system · https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents · https://cognition.com/blog/dont-build-multi-agents · https://www.langchain.com/blog/context-engineering-for-agents · https://code.claude.com/docs/en/costs
