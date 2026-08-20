---
type: discussion
topic: ai-agent
subjects: [codex, antigravity, gemini-cli, github-copilot, cursor]
status: active
ref-adrs: []
---

# 타사 LLM 구독제의 프로그래머블 이용 — Codex · Antigravity · Copilot · Cursor

## 문제

Claude Pro/Max의 프로그래머블 경로가 `claude -p` + `CLAUDE_CODE_OAUTH_TOKEN` 하나뿐임을 확인했다
([[260817_1512_subscription-auth-programmatic-claude-access]] 참조).
타사 — ChatGPT의 Codex, Google의 Antigravity 등 — 는 **구독제만으로 스크립트·CI·SDK 이용이 어디까지 가능한가?**

## 탐색 — 벤더별 현황 (2026-08 웹 조사 기준, 수치·정책 변동 잦음)

### OpenAI Codex (ChatGPT Plus/Pro/Team/Enterprise) — 가장 완전한 지원

벤더 중 유일하게 **CLI·SDK·CI 전부를 구독 인증으로 공식 문서화**했다.

- **인증**: `codex login`이 "Sign in with ChatGPT" 브라우저 OAuth 실행. Free/Go/Plus/Pro/Business/Edu/Enterprise 전 플랜에 Codex 포함. 자격증명은 `~/.codex/auth.json`(또는 OS 키링)에 캐시.
- **headless**: `codex exec "<프롬프트>"` — 비대화형 모드, 저장된 CLI 인증을 재사용하며 CI에서 동작.
- **비대화형 로그인 옵션(공식)**: `codex login --device-auth`(디바이스 코드, 베타) · `--with-access-token`(Enterprise 액세스 토큰을 stdin으로) · `--with-api-key`.
- **CI에서 구독 인증(공식 문서 있음)**: 신뢰 머신에서 로그인 → `auth.json`을 시크릿 매니저에 저장 → 러너에서 `~/.codex/auth.json`으로 복원. 토큰은 자동 갱신되어 파일에 다시 써지므로 **런 사이에 파일을 지속시켜야 하고, 하나의 auth.json을 동시 잡에서 공유하면 안 된다.** 단 같은 문서가 "대부분의 CI에는 여전히 API 키 권장"이라고 명시 — 지원되지만 권장하지 않는(사설 신뢰 인프라용) 경로.
- **SDK**: 공식 Codex SDK 존재 — TypeScript `@openai/codex-sdk`, Python `openai-codex`. 로컬 Codex 에이전트 바이너리를 감싸므로 **CLI가 캐시한 구독 인증을 그대로 상속**한다.
- **GitHub Actions**: 공식 `openai/codex-action`이 `openai_api_key` 또는 `codex_config` 중 하나를 요구하며, ChatGPT Plus/Pro 구독자용 device-auth/`auth.json` 경로를 문서화.
- **한도**: 로컬·클라우드 태스크가 5시간 롤링 윈도 + 주간 한도를 공유. 2026-04-02부터 토큰 사용량 기반 정산으로 전환(Plus ≈ 주당 몇 세션, Pro $100 ≈ 5x, $200 ≈ 20x — **수치 변동 잦음**).
- **API 키가 필요한 것**: Responses/Chat Completions API 직접 호출 등 Codex 에이전트 표면 밖 전부. ChatGPT OAuth 토큰을 서드파티 도구에서 재사용하는 커뮤니티 심(shim)들은 개인 코딩 보조 외 용도(서비스·재판매·멀티유저)로는 비승인.

### Google: Gemini CLI → Antigravity (2026년 중반 대격변)

**주의**: 2026-05-19 Google이 Gemini CLI의 Antigravity CLI(바이너리 `agy`) 전환을 발표했고, **2026-06-18부로 Gemini CLI는 무료 티어·Google AI Pro/Ultra(소비자 구독) 지원을 중단**했다. Gemini CLI는 오픈소스로 남지만 **엔터프라이즈 경로 전용**(Gemini Code Assist Standard/Enterprise 라이선스, `GEMINI_API_KEY`, Vertex/ADC)이다. 이관 과정에서 유료 사용자 접근 장애 사례가 보고되는 등 **아직 정리 중인 상태**.

**Antigravity** (데스크톱 앱 + VS Code 기반 IDE + `agy` CLI + Python SDK):

- **인증**: CLI/IDE는 Google 계정 브라우저 OAuth (SSH 원격에서는 URL + 6자리 OTP 흐름). 무료 개인 티어 + Google AI Pro($19.99/mo)·Ultra 티어로 한도 상향. Gemini 3 외에 Claude·GPT-OSS-120B 모델도 구동.
- **headless**: `agy -p` / `--print` — `--output-format text|json|stream-json`, `--model`, `--effort`, `--continue`, 설정 파일의 `permissions.allow` 허용목록 등 옵션 제공.
- **CI에서 구독 인증: 미지원.** 공식 문서가 "headless는 캐시된 자격증명을 쓰므로 먼저 대화형 `agy` 세션으로 인증하라"고 명시하며, 비인증 비대화형 실행은 에러로 종료된다. CI·컨테이너용 공식 경로는 `ANTIGRAVITY_API_KEY`(AI Studio 발급, **pay-as-you-go**)뿐. 구독 토큰 환경변수 지원은 열려 있는 기능 요청 상태다. (Codex처럼 자격증명 디렉터리를 시딩하는 우회는 가능하겠지만 Google은 문서화·보증하지 않음.)
- **SDK**: `pip install google-antigravity` — **API 키/ADC 전용, 구독 OAuth 미지원.** 사실상 pay-as-you-go 표면.

### GitHub Copilot — 구독제 프로그래머블 지원

- Copilot CLI: `copilot -p "<프롬프트>"` + `--allow-tool`, `--no-ask-user` 등 비대화형 옵션.
- **CI 인증 공식 지원**: "Copilot Requests" 권한이 있는 fine-grained PAT를 `COPILOT_GITHUB_TOKEN`(권장)으로 주입하면 프롬프트 없이 인증. 로컬은 `gh` CLI 인증 폴백.
- 2026-06-01부터 프리미엄 리퀘스트 → **GitHub AI Credits**(1크레딧=$0.01, 토큰 기반) 과금으로 전환 중 (**변동 잦음**).
- 별도로 **Copilot coding agent**: 이슈를 Copilot에 할당(GitHub·Jira·Slack·API)하면 Actions 러너에서 실행되어 PR을 여는 할당형 프로그래머블 경로.

### Cursor — 구독제 프로그래머블 지원

- Cursor CLI(`cursor-agent`): `-p/--print` 모드, `--output-format text|json|stream-json`, 무인 편집용 `--force`.
- CI 인증은 `CURSOR_API_KEY` — 이름은 API 키지만 **대시보드에서 발급하는 계정 귀속 키로, 구독 플랜의 월 포함 사용량을 소모**한다(OpenAI/Google의 API 키와 달리 구독 기반). Free 플랜 키도 headless CLI는 가능(Background Agent API는 유료 플랜).

## 수렴 — 벤더 간 비교

| 벤더 | headless 명령 | 구독 인증(로컬) | 구독 인증(CI) | 구독으로 SDK | API 키가 필요한 것 |
|---|---|---|---|---|---|
| Anthropic (기준선) | `claude -p` | OAuth | `CLAUDE_CODE_OAUTH_TOKEN` (공식) | Agent SDK 불가(정책 금지) | Agent SDK · Messages API |
| OpenAI Codex | `codex exec` | ChatGPT OAuth → `auth.json` | **공식 문서화** (단 "API 키 권장") | **가능** (`@openai/codex-sdk` 등) | 원시 API, 권장 CI 경로 |
| Google Antigravity | `agy -p` | Google OAuth (SSH OTP 지원) | 미지원 — API 키(`ANTIGRAVITY_API_KEY`) | 불가 — SDK는 API 키 전용 | SDK · CI · Gemini API |
| Gemini CLI (26/06 이후) | `gemini -p` | 소비자 티어 제거(엔터프라이즈 전용) | API 키/ADC만 | 해당 없음 | 비엔터프라이즈 전부 |
| GitHub Copilot | `copilot -p` | GitHub 로그인/PAT | `COPILOT_GITHUB_TOKEN` PAT (공식) | Copilot SDK (GitHub 토큰) | 없음 (플랜 내 크레딧) |
| Cursor | `cursor-agent -p` | `agent login` | `CURSOR_API_KEY` (구독 소모형) | Background Agent API (유료 플랜) | 없음 (키가 플랜 사용량 소모) |

요약하면:

- **구독제 프로그래머블 지원 폭: Codex > Copilot ≈ Cursor > Claude > Antigravity.** OpenAI만 SDK까지 구독 인증으로 열어 두었고, Google은 반대로 headless-in-CI조차 API 키를 요구한다.
- 공통 패턴: **"자사 코딩 에이전트 CLI의 headless 모드"까지는 구독으로 열어 주고, 원시 모델 API는 전 벤더가 별도 과금**이다.
- 토큰 추출·자격증명 복사류 우회는 모든 벤더에 존재하지만, **벤더가 문서화한 것은 OpenAI의 auth.json-in-CI 패턴뿐** — 나머지는 미지원이며 ToS 위험이 있다.

## 불확실성 표시

1. 쿼터 수치(Codex 5시간 윈도, Antigravity 티어 배수, Copilot 크레딧)는 2026년에만 수차례 변경 — 인용 시 날짜를 확인할 것.
2. Gemini → Antigravity 이관은 진행 중이며 문서가 활발히 개정되고 있다.
3. OpenAI 문서 도메인이 `learn.chatgpt.com`으로 최근 이전 — URL 재변경 가능.

## 근거 문서

- OpenAI: [Codex Auth](https://learn.chatgpt.com/docs/auth) · [CI/CD Auth](https://learn.chatgpt.com/docs/auth/ci-cd-auth) · [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk) · [codex-action](https://github.com/openai/codex-action) · [Codex rate card](https://help.openai.com/en/articles/20001106-codex-rate-card)
- Google: [Gemini CLI → Antigravity 전환 공지](https://github.com/google-gemini/gemini-cli/discussions/27274) · [Antigravity vs Gemini CLI](https://cloud.google.com/blog/topics/developers-practitioners/choosing-antigravity-or-gemini-cli) · [agy headless](https://antigravity.google/docs/cli/headless) · [antigravity-sdk-python](https://github.com/google-antigravity/antigravity-sdk-python) · [플랜 변경](https://antigravity.google/blog/changes-to-antigravity-plans)
- GitHub: [Copilot CLI 인증](https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli) · [사용량 기반 과금 전환](https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/)
- Cursor: [CLI headless](https://cursor.com/docs/cli/headless) · [사용량 한도](https://cursor.com/help/models-and-usage/usage-limits)
