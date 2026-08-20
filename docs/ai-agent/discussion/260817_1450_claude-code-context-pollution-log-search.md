---
type: discussion
topic: ai-agent
subjects: [claude-code]
status: active
ref-adrs: []
---

# 대량 로그 검색 시 컨텍스트 오염 최소화 — 직접 검색하되 과정은 잊는 방법

## 문제

- 메인 에이전트가 직접 로그를 검색하면 → 검색 과정에서 읽은 대량 로그가 컨텍스트를 오염시킨다.
- 일반 서브에이전트에게 위임하면 → 메인 에이전트가 검색 의도·맥락을 프롬프트로 온전히 전달하지 못하는 경우가 있다.
- 원하는 동작: **전체 맥락을 가진 주체가 직접 검색하되, 검색 과정은 잊고 최소한의 결과만 남기기.**

## 탐색 — Claude Code가 제공하는 수단 (2026-08 기준, 공식 문서 조사)

"검색 후 해당 구간만 자동으로 잊기" 기능은 존재하지 않는다. 후보는 다음과 같다.

| 수단 | 자동 여부 | 툴 출력 격리/제거 | 평가 |
|---|---|---|---|
| 자동 컴팩션 | O (컨텍스트 한계 근접 시) | 요약 (선택적 제거 불가) | 전체 대화 대상 — 이 용도로 못 씀 |
| `/compact <지시어>` | X (수동) | 요약 | 보존 대상 지정 가능, 매번 수동 |
| `/rewind` + 구간 요약 | X (수동) | 선택 구간 요약 | 검색 구간만 압축 가능 |
| **fork 서브에이전트** | X (명시적 호출) | **완전 격리** | **채택** |
| PreCompact/PostToolUse 훅 | O | 불가 | 컨텍스트에서 툴 출력 제거 기능 없음 |

### 배제된 오해

- 메인 에이전트 세션 중 **툴 출력만 선택적으로 자동 삭제**하는 기능은 없다.
- 훅(PreCompact, PostCompact, PostToolUse, PostToolBatch)으로는 컴팩션 차단·후처리·로깅만 가능하다.
- 자동 컴팩션은 전체 대화를 요약 대상으로 하며, 특정 검색 구간만 골라 잊게 할 수 없다.

## 수렴 — fork 서브에이전트 (`/subtask`)

fork는 일반 서브에이전트와 달리 **메인 에이전트의 전체 대화 컨텍스트를 그대로 상속**하는 특수 서브에이전트다.

공식 문서 인용:

> "A fork is a special subagent that inherits the entire conversation context instead of starting fresh."
>
> "The fork's own tool calls still stay out of your conversation and only its final result comes back, so your main context window stays clean."

상속 범위: 전체 대화 이력 · 시스템 프롬프트 · 도구 세트 · 모델 · 권한 모드.

### 왜 이것이 문제를 해결하는가

1. **맥락 전달 누락이 구조적으로 불가능** — 메인이 맥락을 "요약해서 전달"하는 단계 자체가 없다. fork는 메인이 본 것을 전부 본 상태에서 검색을 시작한다.
2. **검색 과정의 툴 출력이 메인 컨텍스트에 들어오지 않음** — fork가 실행한 Bash 명령, 읽은 로그 파일 등은 모두 격리되고, 최종 요약만 메인 세션으로 반환된다.
3. **비용 효율** — 메인 세션의 프롬프트 캐시를 재사용하므로 일반 서브에이전트보다 저렴하다.

### 사용법

```
/subtask <작업 설명>        # v2.1.212 이상
/fork <작업 설명>           # 이전 버전
```

대화 중 자연어로 "이 검색은 fork로 처리해줘"라고 요청해도 된다.

### 예시 흐름

1. 메인 에이전트가 시스템 구조와 검색 목적에 대한 전체 맥락을 보유.
2. `/subtask 새벽 2~3시(UTC) auth 모듈의 timeout 에러를 로그에서 검색하고, 상위 5건을 타임스탬프·라인 번호와 함께 요약해줘`
3. fork가 수십 번의 grep/로그 읽기를 수행 — 전부 격리됨.
4. fork 반환: "타임아웃 에러 3건 발견, 원인은 커넥션 풀 고갈로 추정" (요약만).
5. 메인 컨텍스트는 중간 로그로 오염되지 않은 상태로 후속 작업 진행.

## 차선 — 메인 에이전트가 반드시 직접 검색해야 할 때

검색 후 수동으로 압축한다.

- **`/compact <지시어>`** — 예: `/compact 최종 검색 결과만 유지하고, 중간에 읽은 로그 내용은 버려`. 삭제가 아닌 요약이며 매번 수동 실행이 필요하다.
- **`/rewind` + 구간 요약** — `Esc Esc` 또는 `/rewind`로 체크포인트를 선택한 뒤 "Summarize from here" / "Summarize up to here". 검색 시작 지점부터의 구간만 압축하는 데 `/compact`보다 적합하다.

## 근거 문서

- [Context window](https://code.claude.com/docs/en/context-window.md) — 자동 컴팩션 동작과 보존 대상
- [Subagents](https://code.claude.com/docs/en/sub-agents.md) — fork 타입, 컨텍스트 상속, 툴 출력 격리
- [Memory](https://code.claude.com/docs/en/memory.md) — `/compact`, `/rewind`
- [Hooks](https://code.claude.com/docs/en/hooks.md) — PreCompact, PostCompact, PostToolUse, PostToolBatch
- [Best practices](https://code.claude.com/docs/en/best-practices.md) — 컨텍스트 관리 전략과 서브에이전트 위임
