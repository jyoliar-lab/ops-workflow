---
type: discussion
topic: ai-agent
subjects: [claude-code, claude-agent-sdk, langchain, strands-agents]
status: active
ref-adrs: []
---

# 구독제 Claude의 프로그래머블 이용 — SDK·프레임워크별 인증 가능 범위

## 문제

Claude Agent SDK, LangChain, Strands Agents 등으로 Claude를 프로그래머블하게 쓰고 싶다.
통념상 이런 SDK 연동은 구독제(Pro/Max)와 별개인 pay-as-you-go API 키를 요구한다.
**구독제 요금제만으로 프로그래밍 언어를 통한 이용이 가능한가?**

## 탐색 — 경로별 인증 가능 여부 (2026-08 기준, 공식 문서 조사)

| 경로 | 구독제 인증 | API 키 | 비고 |
|---|---|---|---|
| **Claude Code headless** (`claude -p`) | **O** | O (둘 다 가능) | 유일한 구독제 프로그래머블 경로 |
| Claude Agent SDK (TS/Python) | X | 필수 | 정책상 금지 (기술 제약이 아님) |
| LangChain · Strands · Messages API 직접 호출 | X | 필수 | OAuth 자격증명이 Messages API에서 안 통함 |
| Claude Managed Agents | X | 필수 | 구독과 별개의 API 제품 |

### 가능한 경로: Claude Code headless 모드

Claude Code의 `-p`(print) 모드는 구독 자격증명을 그대로 재사용한다.

- **대화형 세션에서 이어 쓰기**: `/login`으로 저장된 Pro/Max OAuth 자격증명을 `-p` 모드가 자동 재사용.
- **CI·스크립트 (비대화형)**: `claude setup-token`으로 1년 유효 토큰을 발급받아 `CLAUDE_CODE_OAUTH_TOKEN` 환경변수로 주입. Pro/Max/Team/Enterprise 플랜 필요.

```bash
# 1회 발급 (브라우저 로그인 필요)
claude setup-token

# CI 등 비대화형 환경에서
export CLAUDE_CODE_OAUTH_TOKEN=<발급받은 토큰>
claude -p "작업 지시" --allowedTools "Read,Edit" --output-format json
```

주의: `--bare` 모드는 OAuth 자격증명·키체인을 읽지 않는다 — bare 모드는 `ANTHROPIC_API_KEY`가 필요하다.

### 불가능한 경로와 이유

**Claude Agent SDK** — 공식 Quickstart가 명시적으로 금지한다:

> "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Please use the API key authentication methods described in this document instead."

지원 인증: `ANTHROPIC_API_KEY` · Amazon Bedrock · Vertex AI · Microsoft Foundry 등 — 전부 API 과금 경로다.

**LangChain · Strands Agents · Messages API 직접 호출** — 이 프레임워크들은 Messages API를 직접 호출하며, 해당 엔드포인트는 `x-api-key` 헤더(API 키) 인증만 받는다. 구독 OAuth 자격증명은 Claude Code·Claude.ai 전용이라 Messages API에서 통하지 않는다. 지원되는 브리지는 없다.

**Claude Managed Agents** — Anthropic이 호스팅하는 샌드박스 에이전트 서비스. API 키 + 베타 헤더(`managed-agents-2026-04-01`)가 필요한 별도 과금 제품이다.

## 수렴

- **구독제만으로 가능한 프로그래머블 경로는 `claude -p` + `CLAUDE_CODE_OAUTH_TOKEN` 하나뿐이다.** 셸 호출 기반 자동화(스크립트·CI·cron)는 이 경로로 충분하다.
- **Agent SDK·LangChain·Strands를 쓰려면 API 키(별도 pay-as-you-go 과금)가 필수다.** 기술 우회가 아니라 Anthropic 커머셜 약관의 정책이므로, 우회 시도는 약관 위반이다.
- 판단 기준: 자동화가 "Claude Code CLI를 감싸는 형태"로 표현 가능하면 구독제로 해결되고, 라이브러리 수준 통합(파이썬/TS 코드 안에서 메시지 API 직접 조작)이 필요하면 API 키를 발급받는다.

## 근거 문서

- [Claude Agent SDK Quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart.md) — API 키 요구 및 구독 인증 금지 정책
- [Claude Code Authentication](https://code.claude.com/docs/en/authentication.md) — `claude setup-token` · `CLAUDE_CODE_OAUTH_TOKEN` · 자격증명 우선순위 · bare 모드 예외
- [Claude API Authentication](https://platform.claude.com/docs/en/manage-claude/authentication) — Messages API의 API 키 인증
- [Claude Managed Agents Overview](https://platform.claude.com/docs/en/managed-agents/overview) — API 키 요구
