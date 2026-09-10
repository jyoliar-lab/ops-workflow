---
type: discussion
topic: ai-agent
subjects: [claude-code, ticket-engineer-agent, ticket-report, ticket-pr, obs-toolkit, github-issues, pytest]
status: active
ref-adrs: [ADR-0017]
ticket: 93
pr: jyoliar-lab/obs-toolkit#1
related: [../../ops-workflow/discussion/260727_1608_pr-merge-auto-close.md, 260830_1657_shared-observability-analysis-plugin.md]
---

# agent 코드 생산량과 사람의 이해 병목 — 외부 조사와 이 하네스에의 대입

## 계기

agent 의 코드 생산량이 커지면서 **사람이 코드를 이해하는 인지 부하**가 병목이 됐다.
사람이 가져온 문제는 이것이고, 이 문서는 (a) 이 병목을 다른 조직이 어떻게 다루는지 외부 조사하고, (b) 그것을 이 하네스의 실측에 대입해 옵션을 벌린다.
정하지 않는다 — 정할 것이 있으면 §7 의 질문에 사람이 답한 뒤다.

ADR-0017 이 남긴 재검토 신호가 이 자리다: *"검수 병목이 상례가 된다면 … 완료 기준(종료)과 검수 절차의 관계를 재검토해야 한다."*(`adr-0017` L85).
`260727_1608` 은 close 의 의례성을 다뤘고, 이 문서는 그 앞 단계 — **검수 자체의 비용** — 를 다룬다.

조사일 2026-09-10.
외부 자료는 1차 출처(엔지니어링 블로그·논문·공식 문서)를 우선했고, 벤더 텔레메트리와 2차 보도는 그렇게 표시했다.

## 1. 실측 — 병목이 지금 어디에 서 있나

### 1-1. PR 하나의 형상

`jyoliar-lab/obs-toolkit#1`(#93 의 산출물, 2026-09-08 개설):

| | |
|---|---|
| 규모 | 31 파일 · +2,886 / −1 · 커밋 3 |
| 코드의 무게중심 | `obs/adapters/cli.py` 639줄 · `obs/core.py` 429줄 — 둘이 코드의 대부분 |
| 나머지 | 테스트 4파일(59 tests) · 픽스처 7파일(실측 녹화) · 골격(plugin.json · hooks · SKILL.md · CI) |
| 검수 상태 | 개설 후 이틀, 리뷰 0 · 코멘트 0 · OPEN |

한 Task 가 2.9k 줄을 냈고, 그 PR 이 읽히지 않은 채 서 있다.
이것이 병목의 실물이다.

### 1-2. 하네스가 이미 주는 검수 표면

사람이 코드 대신 읽을 수 있는 것이 무엇인지, 하네스(`workspace/ref/ticket-engineer`)에서 읽었다.

| 표면 | 어디서 나오나 | 성격 |
|---|---|---|
| **AC 대조 코멘트** | `ticket-report` 2단계 — AC 항목 \| 충족 방식 \| 근거(코드 위치·확인 방법). #93 에는 5,321자 코멘트가 달렸다 | 증거 서술. 단 **일한 agent 가 스스로 쓴다** — 자기 채점이다 |
| **PR 본문** | `ticket-pr.py` 가 `Closes` 키워드만 강제한다(`build_body`). 구조·길이·읽는 순서에 대한 규약은 없다 | #1 은 "무엇 / 확인 / 범위 밖" 을 agent 가 자발적으로 썼다 |
| **착수 요약** | `ticket-start` 6단계 — 경계·상태·이해한 작업 계획을 사용자에게 보인다. *"계획이 티켓과 어긋날 소지가 보이면 진행 전에 묻는다"* | **게이트가 아니다.** 사람이 승인하지 않아도 진행한다 |
| **테스트·픽스처** | `tests/` 59건 · `fixtures/` 는 실환경 응답 녹화 | 픽스처는 좋은 증거다. 테스트는 **구현한 agent 가 썼다** |
| **저작 표식** | 커밋 트레일러 `Co-Authored-By` + 세션 링크 | 식별은 되나 리뷰 강도 조절에 쓰이지 않는다 |
| **CI** | pyright strict + pytest(3.10 · 3.14) | 기계 검증. 통과가 곧 "맞다" 는 아니다 |

정리하면 — **하네스는 사람을 검증 루프의 마지막 자리에 구조적으로 놓는다**(CLAUDE.md §5 close 는 사람 · §6 사람 검수).
그 자리에서 사람이 읽을 것은 코드와 agent 의 자기 보고 둘뿐이고, 둘 다 읽는 비용이 코드량에 비례한다.
Anthropic 의 best practices 가 경고하는 그 상태다: *"Without a check it can run, 'looks done' is the only signal available, and you become the verification loop."*

### 1-3. 병목의 절반은 쪼갬에서 왔다

#93 은 리프 Task 하나였다.
그 Task 의 Goal 은 코어(7개 개념) · CLI 어댑터 · 플러그인 골격 · 테스트·CI 를 한 번에 담았다.
쪼갬은 design-partner(이 agent)의 일이므로 이것은 agent 산출물의 문제이기 전에 **발행 단위의 문제**다.
외부 데이터가 일관되게 말하는 것(§2-3)이 바로 이 지점이다 — 큰 PR 은 느리게 읽히는 게 아니라 **안 읽힌다.**

## 2. 외부 조사 — 무엇을 하고 있나

### 2-1. 문제의 이름부터 다르다

조사한 조직 전부가 같은 진단을 낸다 — 생성은 싸졌고 리뷰는 안 싸졌다.
그런데 "병목" 이 가리키는 비용이 셋으로 갈린다.

| 비용 | 증상 | 이렇게 부르는 곳 |
|---|---|---|
| **지연(latency)** | PR 이 큐에 선다 | Meta(24시간 내 리뷰율 하락), Anthropic(*"reviews were the bottleneck"*), Faros·LinearB 텔레메트리 |
| **이해(comprehension)** | 머지 뒤에도 그 코드를 아무도 모른다 | Shopify(*comprehension debt*), Osmani, Storey(*cognitive debt · intent debt*), Anthropic RCT |
| **정확성(correctness)** | "거의 맞는" 코드 | Stack Overflow 2025(66% *"almost right, but not quite"*), CodeRabbit·GitClear 텔레메트리 |

대부분의 조직은 **지연**을 푼다.
**이해**를 정면으로 다룬 곳은 Shopify 와 Meta(MetaMateCR 실험) 정도다.
사람이 가져온 문제는 "이해" 인데, 시장의 답은 대부분 "지연" 을 향한다 — 이 어긋남이 §7 첫 질문의 이유다.

### 2-2. 대응 4갈래

**① AI 가 먼저 읽고 사람은 나중에 읽는다.**
GitHub Copilot code review(전체 리뷰의 1/5, 29% 는 침묵), Uber uReview(주 65k diff 의 90%, 코멘트별 confidence), Microsoft 내부(PR 90%+, 완료 시간 −10~20%), Anthropic Code Review(1,000줄+ PR 의 84% 에서 finding, 리뷰당 ~20분 · $15–25).
공통 설계 원칙은 **침묵**이다 — 병목이 사람의 주의력이므로 노이즈가 곧 비용이다.
양날이다: AI 리뷰어가 조용하면 사람이 그냥 승인하는 행태(Pragmatic Engineer 2026-07), AI 제안을 채택하면 복잡도가 오히려 는다는 관찰(Zhong et al. arXiv 2603.15911).
- https://github.blog/ai-and-ml/github-copilot/60-million-copilot-code-reviews-and-counting/
- https://www.uber.com/us/en/blog/ureview/
- https://claude.com/blog/code-review

**② 위험으로 분류해 저위험은 사람 리뷰를 생략한다.**
Meta RADAR(arXiv 2605.30208): 사람당 landed 코드가 +105.9%/yr, *"a workflow that relies on humans reading most diffs does not scale."* 저자·소스 유형 → 자격 게이트 → ML 위험 점수(DRS) → LLM 리뷰 → 결정적 검증. 53.5만 diff 검토, revert 율 1/3, incident 율 1/50.
Anthropic(2026-07): 코드베이스를 **리스크 티어**로 나누고 티어별 자동화 수준 결정, 자동 승인분의 일부를 사람이 샘플 리뷰.
GitHub(2026-09-01): Copilot 리뷰의 approve 산입을 관리자 opt-in 으로 허용.
2025 년까지 "사람이 최종 승인" 이던 선이 2026 년에 **리스크 조건부 생략**으로 움직였다.
- https://arxiv.org/abs/2605.30208
- https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle

**③ 읽는 대상을 코드에서 다른 것으로 옮긴다.**
세 갈래다.
- **스펙·계획** — Kiro(requirements/design/tasks 승인 뒤 코드), Spec Kit, plan mode. 사람 검토 시점을 코드 **앞**으로 당긴다.
- **증거** — Anthropic best practices: *"Have Claude show evidence rather than asserting success … Reviewing evidence is faster than re-running the verification yourself."* GitHub 리뷰어 가이드: pre-change 동작에서 **실패하는 테스트**를 요구. Meta JiTTests: 변경별 임시 테스트로 사람 리뷰 부하 70% 감소 주장.
- **결과 지표** — Spotify Confidence: *"human review of every change is impossible"* → 판단을 코드 리뷰에서 실험 guardrail 로 이동(실험의 42% 가 guardrail 로 롤백). Shopify: reversion rate.
- https://code.claude.com/docs/en/best-practices
- https://github.blog/ai-and-ml/generative-ai/agent-pull-requests-are-everywhere-heres-how-to-review-them/
- https://confidence.spotify.com/blog/when-ai-writes-the-code

**④ 사람 리뷰를 유지하되 병목을 인정하고 측정한다.**
Shopify(*"We still require a human PR reviewer"*, comprehension debt 를 최대 장기 리스크로 지목), Stripe(주 1,300+ PR, *"All code is human-reviewed"* — 사람에게 오기 전 CI 자동 수정 2사이클), Google(*"approved by engineers"* 를 항상 붙인다).
- https://www.bvp.com/atlas/inside-shopifys-ai-first-engineering-playbook
- https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2

### 2-3. 실증 — 무엇이 근거가 있나

| 주장 | 근거 | 강도 |
|---|---|---|
| 생성만 위임하면 이해도가 떨어진다 | Anthropic RCT(n=52): 이해도 퀴즈 −17%p, d=0.74. 개념 질문·설명 동시 요청 패턴은 보존 | **실험** — 이해 병목의 거의 유일한 실험 근거 |
| AI 산출물을 사람이 검증하려 들면 리뷰가 느려진다 | Meta MetaMateCR: 리뷰어에게 AI 패치를 보이자 TimeInReview +5.5%(p=.029), 저자에게만 보이자 소멸 | **실험** — 이해 비용의 정량화 |
| 큰 PR 은 안 읽힌다 | Graphite 50줄 vs 250줄(~40% 빠름, revert −15%) · DORA 2025 역량 모델의 *small batches* · Faros PR 크기 +154% | 벤더 상관 + 설문 |
| AI 는 PR 을 키우고 리뷰 큐를 막는다 | LinearB 8.1M PR: AI PR 첫 픽업 4.6배 지연 · Faros 리뷰 시간 +91%~+441% | **단일 벤더 상관** — 독립 재현 없음 |
| 체감과 실측이 반대일 수 있다 | METR RCT(n=16): 체감 +20%, 실측 −19%. 2026 후속은 CI 가 0 을 포함 | 실험이나 표본 작음 |
| 계획·walkthrough 를 읽으면 코드를 덜 읽어도 된다 | **측정 없음.** 유일한 실무 평가(Böckeler)는 부정적 — *"I'd rather review code than all these markdown files"* | 없음 |
| 테스트가 사람의 통제점이 된다 | Beck(TDD, 테스트 삭제 사례) · Meta JiTTests(자사) · 반증: agent 가 쓴 테스트 양은 해결률과 무관(arXiv 2603.13724) | 실무 권위 + 자사 |

- https://www.anthropic.com/research/AI-assistance-coding-skills
- https://arxiv.org/abs/2507.13499
- https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
- https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html

### 2-4. 실무자 프레임 — 수렴하는 것

- **위험에 비례해 검증 수단을 고른다.** Böckeler: 리뷰 수준 = Probability × Impact × Detectability. *"Would you ship this if you were on call tonight?"* Detectability 의 입력이 테스트·정적 타입·**코드베이스 친숙도**다 — 이해가 검출력의 재료다. https://martinfowler.com/articles/exploring-gen-ai/to-vibe-or-not-vibe.html
- **줄이 아니라 구조를 소유한다.** Osmani(*comprehension debt*): *"catch AI mistakes at architectural scale rather than line-by-line"* · Google Cloud CTO Office: 일회용 코드는 스타일을 따지지 말고 아키텍처 청사진에 리뷰를 집중. https://addyosmani.com/blog/comprehension-debt/
- **책임은 사람에게 남는다 — 그리고 저절로 무너진다.** Willison 2025-10: *"proudly and confidently accountable"* → 2026-05 고백: 단순 작업은 이제 안 읽는다, *"semi-black box"*, normalization of deviance 를 자각. https://simonw.substack.com/p/vibe-coding-and-agentic-engineering
- **OSS 메인테이너는 부담을 제출자에게 되돌린다.** Linux kernel `coding-assistants.rst`(`Assisted-by:` 트레일러, 제출자가 전부 검증), Ghostty `AI_POLICY.md`(*"the human-in-the-loop must fully understand all code"*, 수용된 이슈에만 PR). 이 저장소의 하네스는 제출자가 agent 이므로 **되돌릴 곳이 하네스 자신**이다.

이 수렴의 교훈은 하나로 압축된다 — Willison 이 보여주듯 "다 읽는다" 는 규율은 모델이 좋아질수록 무너지므로, **규율이 아니라 구조**(배치 크기·테스트·제약·티어)로 강제해야 한다.
CLAUDE.md §8 과 같은 말이다.

### 2-5. 도구 지형 — 이 하네스에 닿는 것만

| 범주 | 대표 | agent 중립 | 판단 |
|---|---|---|---|
| AI 리뷰어 | CodeRabbit · Greptile · Qodo/PR-Agent(오픈소스·자체 호스팅) · Claude Code `/code-review` · Copilot review | 대부분 중립 | 리뷰어 "하나 더" 는 지연을 줄이지 이해를 늘리지 않는다 |
| 읽는 순서·내러티브 | CodeRabbit Change Stack · Devin Review · Amp("파일 중 설명하는 것을 먼저") | 부분 | **효과 측정 없음** — 편의 기능으로 본다 |
| 계획 게이트 | Claude Code plan mode(`Ctrl+G` 편집) · Kiro · Spec Kit | Spec Kit 만 중립 | 대체가 아니라 앞에 추가된다 |
| 검증 강화 | mutation testing(Stryker·mutmut) · property-based · 별도 검증 subagent | 중립 | coverage 는 agent 가 쉽게 채운다 — *"Test strength will matter more than test volume"* |
| 분류·표식 | Qodo effort 1–5 · CodeRabbit Triage · `Assisted-by:`/`Generated-By:` 트레일러 | 중립 | 이미 `Co-Authored-By` 를 쓴다. 확장은 되돌리기 쉬워 ADR 감이 아니다 |

- https://www.coderabbit.ai/blog/code-is-no-longer-the-bottleneck-understanding-is
- https://www.awesome-testing.com/2026/08/mutation-testing-for-agent-written-code

## 3. 이 하네스에 대입 — 옵션

솔로 운영이라 대기업의 답을 그대로 못 쓴다.
리뷰어를 늘릴 수 없고, 리뷰 시간의 텔레메트리가 없고, 리스크 점수 ML 도 없다.
그러나 대기업의 답이 결국 "읽을 양을 구조로 줄이고, 읽는 대상을 옮기고, 위험으로 고른다" 라면 그 셋은 솔로에서도 성립한다.

축은 넷이다 — **어느 비용을 줄이나**(지연 / 이해 / 정확성) · **되돌리기 비용** · **누가 떠안나** · **근거 강도**.

### A. 안 한다 — 계속 전부 읽는다

현상 유지의 비용을 먼저 센다.
- PR 이 큐에 선다(#1: 이틀, 0 리뷰). 후속 Task 는 ADR-0017 착수 게이트에 막힌다 — #93 뒤에 환원 연산 3 Task · investigate · MCP 어댑터가 줄 서 있다.
- 읽어도 소유가 안 된다 — Anthropic RCT 가 말하는 "생성 위임 → 이해 저하" 는 읽기만으로 회복되지 않는다.
- Willison 의 궤적을 밟는다 — 규율은 유지되지 않고, 어느 날 안 읽고 머지하는 것이 정상이 된다. 그때는 이 문서 같은 것도 없이 무너진다.
- 이기는 조건: 생산량이 다시 줄거나, 이 프로젝트가 잠깐의 실험이라 소유가 필요 없을 때.

### B. 읽을 단위를 줄인다 — 쪼갬과 PR 크기

- **Task 발행 단위를 줄인다.** #93 은 코어·CLI·플러그인·CI 를 하나로 냈다. "한 Task = 사람이 한 자리에서 읽을 수 있는 diff" 를 쪼갬의 판정 기준에 넣는다. 이것은 design-partner 의 일이지 하네스 변경이 아니다.
- **`ticket-pr.py` 에 크기 신호.** 강제 상한(exit 1)이 아니라 경고 — 임계는 사람이 정한다. 근거는 Graphite·DORA(§2-3)이나 벤더 상관이다.
- 축: 지연 ↓ · 이해 ↑(작으면 읽힌다) · 되돌리기 비용 0 · 떠안는 이 = design-partner(쪼갬) · 근거 중.
- 반대편: 작은 PR 이 많아지면 PR 수만큼 **검수 왕복이 는다** — 솔로에서는 왕복 자체가 부하다. 그리고 픽스처·골격처럼 "크지만 읽을 필요 없는" 줄이 크기 신호를 오염시킨다.

### C. 읽는 대상을 옮긴다 — 계획 · 증거 · 반증

셋을 따로 볼 수 있다.

**C-1. 계획 승인 게이트.** `ticket-start` 6단계 착수 요약을 "보인다" 에서 "승인받는다" 로 올린다.
사람은 코드 전에 *무엇을 어떤 구조로* 를 읽는다.
- 축: 이해 ↑(의도 시점의 소유) · 지연 ↔(왕복 1회 추가) · 되돌리기 0 · 떠안는 이 = 사람(대화 1회).
- 반대편: **측정된 효과가 없다**(§2-3). Böckeler 는 계획 문서 리뷰가 코드 리뷰보다 지루하다고 했다. 백그라운드 실행 흐름(`ticket-run.py`)과 충돌한다 — 승인 대기가 곧 정지다. Anthropic 문서도 *"If you could describe the diff in one sentence, skip the plan"* 이라 한다.

**C-2. 증거 계약.** AC 대조 코멘트를 "충족 방식" 서술에서 **재현 가능한 증거**로 바꾼다 — 실행한 명령과 출력, 변경 전에 실패하고 변경 후에 통과하는 테스트, 실측 재현.
#1 의 PR 본문 "확인" 절은 이미 이 방향이다(`obs-doctor ✓ … (2026-09-08 08:22 UTC)`, 실측 3종 재현) — 자발적인 것을 규약으로 올리는 일이다.
- 축: 정확성 ↑ · 지연 ↓(증거는 코드보다 빨리 읽힌다 — Anthropic) · 이해 ↔ · 되돌리기 0 · 떠안는 이 = agent.
- 반대편: 증거를 만든 것도 같은 agent 다. 테스트 조작(Beck 의 "테스트 삭제") 은 증거를 오염시킨다. 그래서 C-3 이 필요하다.

**C-3. 반증 subagent.** `ticket-report` 에 fresh context 의 별도 subagent 가 **diff 만 보고 티켓 AC 대비 갭·범위 밖 변경·테스트 약화**를 보고하는 단계를 넣는다.
Anthropic 이 권하는 형태(*"a fresh model try to refute the result, so the agent doing the work isn't the one grading it"*)이고, 대기업의 "AI 리뷰어 선행" 을 솔로 규모로 옮긴 것이다.
- 축: 정확성 ↑ · 지연 ↓ · 이해 ↔ · 되돌리기 0 · 떠안는 이 = agent(토큰).
- 반대편: 양날(§2-2 ①) — 반증이 조용하면 사람이 안 읽고 승인한다. 그러면 이해 비용은 안 줄고 **읽지 않는 것이 정당화**된다. 이것이 C 전체의 함정이다: **지연은 줄이면서 이해는 그대로 두고, 이해를 안 하는 것을 편하게 만든다.**

### D. 위험 티어로 읽기를 생략한다

저장소·경로별로 "사람이 읽는다 / 증거만 본다 / CI 만 본다" 를 나눈다.
#1 에 대입하면: `core.py`·`cli.py` 는 읽는다, `tests/` 는 반증 결과만, `fixtures/`·골격·CI yaml 은 CI 통과만.
판정 기준은 이미 있다 — §4② one-way door(되돌리기 어려움 × 영향 범위)를 코드에 적용하면 된다.
- 축: 이해 ↑(읽을 곳에 집중) · 지연 ↓ · 되돌리기 낮음(티어는 표) · 떠안는 이 = 사람(티어 판정) · 근거 강(Meta·Anthropic 이 이 길로 갔다).
- 반대편: 티어를 누가 매기나. 사람이면 리뷰 부하가 판정 부하로 옮겨간다. agent 가 매기면 자기 판정이다. 그리고 "일회용" 을 선언한 코드가 살아남아 프로덕션이 되는 것이 GitClear 가 보는 churn 의 정체다.

### E. 이해를 유지하는 사용 방식 — 코드 뒤에 설명을 요구한다

Anthropic RCT 에서 이해도를 보존한 패턴은 "생성 후 후속 질문 · 코드+설명 동시 요청" 이었다.
머지 전 사람이 agent 에게 **의도 순서의 안내(walkthrough)** 를 요구하고, 그 대화를 거쳐 읽는다 — 도구가 아니라 습관이다.
- 축: 이해 ↑(유일한 실험 근거) · 지연 ↔ · 되돌리기 0 · 떠안는 이 = 사람(시간).
- 반대편: 시간을 **더** 쓴다. 병목이 시간이면 이건 답이 아니다. 그리고 습관은 규율이고, 규율은 무너진다(§2-4).

### 옵션이 이기는 조건

| 병목이 실제로… | 이기는 옵션 |
|---|---|
| **지연**(PR 이 서서 후속이 막힌다) | B + C-2 + C-3 — 읽을 양을 줄이고 증거로 대체한다 |
| **이해**(머지해도 내 코드가 아니다) | B + D + E — 작게, 읽을 곳을 고르고, 설명을 거쳐 읽는다. C 는 오히려 해롭다 |
| **정확성**(맞는지 모르겠다) | C-2 + C-3 + mutation testing — 증거의 강도를 올린다 |
| 셋 다 | 없다. 하나를 골라야 한다 — 그래서 §7 |

## 4. 사람의 반대편에 서서

사람은 "이해 부하가 병목" 이라 했다.
그 프레임이 틀리는 조건을 둘 댄다.

1. **병목이 이해가 아니라 지연일 수 있다.** #1 이 이틀 서 있는 것은 이해하기 어려워서가 아니라 **읽기 시작하는 비용**(2.9k 줄을 앞에 두는 것) 때문일 수 있다. 그렇다면 답은 E 가 아니라 B 다. 대기업 대부분이 이 진단을 냈다.
2. **"이해" 의 수준이 정해지지 않았다.** `core.py` 의 모든 줄을 소유해야 하나, 아니면 `Config` 해석 순서 · `Client.get` 유일성 · spill 상한이라는 **구조적 약속**만 소유하면 되나. 후자라면 이미 테스트가 그것을 검사한다(`test_get_only.py` 가 AST 로 GET 유일성을 검사). 그러면 병목은 이해가 아니라 **"내가 무엇을 소유하기로 했는지" 가 적혀 있지 않은 것**이다 — Storey 의 *intent debt*.

그리고 반대로, 이 문서가 스스로에게 서는 반대편: 조사의 결론 대부분은 "오래된 좋은 관행의 재확인"(작은 배치·TDD·아키텍처 제약)이다.
새로운 것은 그 관행이 **AI 시대에 규율로는 유지되지 않는다**는 관찰 하나다.

## 5. 버린 것

- **AI 리뷰어 SaaS 도입**(CodeRabbit 등) — 저장소가 여럿이고 솔로라 비용 대비 낮고, 벤더 벤치마크는 서로 모순된다(Greptile 자체 82% vs Tenki 측정 36%). 반증 subagent(C-3)가 같은 자리를 채운다.
- **스펙 주도(Kiro·Spec Kit)** — 티켓 본문(Goal · Requirements · AC)이 이미 스펙이다. 마크다운을 더 만드는 것은 Böckeler 의 실패를 재현한다.
- **"AI 는 approve 못 한다" 규칙 명문화** — 이미 구조다. `guard-write.py` 가 `gh pr merge` 를 거부한다(ticket-engineer CLAUDE.md L60). 적을 것이 없다.
- **리뷰 시간 텔레메트리** — 측정 대상이 사람 하나다. PR 개설~머지 간격은 `gh` 로 언제든 뽑는다.

## 6. 임계선 — ADR 감인가

옵션 B~E 는 전부 되돌리는 데 한 시간이 안 걸린다 — 스킬 문장 · 스크립트 경고 · 쪼갬 기준.
§4② 로는 **ADR 이 아니라 티켓**이다.

하나만 다르다 — **"사람은 무엇을 읽고 무엇을 읽지 않기로 하나"**(D 의 티어 원칙).
이것이 정해지면 ADR-0017 의 완료 기준(close = 사람 검수)의 *검수* 가 무엇인지가 바뀐다.
검수의 정의를 바꾸는 것은 후속 결정들의 인용 근거가 되고, 한 번 "읽지 않는다" 를 공표하면 되돌릴 때 이미 안 읽은 코드가 남는다.
one-way door 에 가깝다.
초안을 써 봐야 갈리므로 여기서는 후보로만 둔다 — §7 첫 두 질문에 답이 있어야 쓴다.

## 7. 사람에게 묻는다 — 코드에 없는 것

1. **어느 비용인가.** #1 앞에서 겪는 것은 (a) 시작할 엄두가 안 난다 (b) 읽어도 남지 않는다 (c) 맞는지 모르겠다 — 중 무엇인가. 답이 옵션을 가른다(§3 마지막 표).
2. **무엇을 소유하려 하나.** `core.py` 의 줄인가, 구조적 약속(GET 유일 · 논리 이름만 · spill 상한)인가. 후자라면 그 약속의 목록이 곧 "읽을 곳" 이다.
3. **일회용이 있나.** 픽스처 · 골격 · CI · 스킬 shim 을 안 읽어도 되는 것으로 선언할 수 있나. 있다면 D 가 즉시 성립한다.
4. **왕복을 감수하나.** C-1(계획 승인)은 백그라운드 흐름을 끊는다. 대화 1회가 늘어도 되나, 아니면 무인 실행이 우선인가.

답이 오면 — B 의 쪼갬 기준은 design-partner 가 바로 적용하고, C-2·C-3·B 의 크기 신호는 ticket-engineer 하네스의 Task 로 발행할 수 있다(리프라 ADR 불요).
D 는 초안을 써서 임계선을 판정한다.

## 8. 사람의 답 — 병목은 코드가 아니라 **테스트 코드의 소유**다

§7 에 답이 왔다(2026-09-10).

1. (b) 읽어도 남지 않는다 — **특히 테스트 코드.** 비즈니스 코드는 따라가며 읽히는데, 제일 중요한 테스트가 이해되지 않는다.
2. 구조적 약속만 소유하면 충분하다 — 그런데 그 약속을 검사하는 테스트가 소유되지 않는다.
3. 픽스처·골격·CI·shim 은 읽지 않아도 된다.
4. 계획 승인 왕복 1회를 감수한다.

문제가 바뀌었다.
"코드가 너무 많다" 가 아니라 **"소유하려는 것(약속)과 그것을 담은 인공물(테스트)이 연결되지 않는다"** 이다.
§3 의 옵션 중 C 는 이 문제에 답이 아니었고(증거를 만드는 것이 곧 테스트인데, 그 테스트가 안 읽힌다), 답은 B·D·E 를 **테스트에 국한해** 합친 모양이다.

### 8-1. 테스트가 왜 안 읽히나 — PR #1 의 `tests/` 를 읽고

추측하지 않고 696줄(59 tests)을 읽었다.
좋은 것부터: **모든 테스트에 docstring 이 있고, 그 docstring 이 행위를 말한다**("AC 3 의 첫 실측 `up` — …", "토큰은 env 에서만 — …").
의도 층은 이미 있다.
안 읽히는 이유는 그 아래 층이다.

| 원인 | 실물 | 비용 |
|---|---|---|
| **한 테스트에 여러 주장** | `test_window`: 생성·baseline·label·to_dict 4가지. `test_parse_metric_shapes`: vector·scalar·garbage 3가지. `test_traceql_search_then_trace`: 두 명령을 잇는다 | 테스트 이름이 무엇을 약속하는지 하나로 말하지 못한다. 실패하면 어느 약속이 깨졌는지 모른다 |
| **`and` 로 이은 assert** | `assert isinstance(ev, Evidence) and isinstance(ev.value, Lines) and ev.backend == "metrics" and ev.query == "up" and kind == "promql"` (`test_cli.py` L30) — 한 줄에 5개 조건. 파일 전반 | 읽을 때 조건을 머릿속에서 풀어야 하고, 실패하면 pytest 가 어느 조건인지 못 보여준다 |
| **픽스처에서 유도된 숫자** | `len(lines) == 5` · `"start=8200.0"` · `1788825600.0` · `"n=6 min=65 max=65"` | 왜 5인지·8200 이 어디서 왔는지는 픽스처와 산술을 알아야 한다. 같은 파일의 `test_logql_streams` 는 *"숫자를 하드코딩하지 않는다"* 며 픽스처를 파서로 다시 읽는다 — 규약이 없어 테스트마다 다르다 |
| **인프라의 숨은 규칙** | `FakeTransport` 가 URL 조각 포함으로 응답을 고른다. `"api/v1/query?"` 와 `"api/v1/query"` 의 차이(`?` 유무로 instant 와 range 를 가른다 — `query_range` 가 `query` 를 포함하므로)는 읽어서 발견해야 한다 | conftest 를 먼저 이해해야 어느 테스트도 읽힌다 |
| **약속 테스트와 형식 스냅샷이 섞여 있다** | `lines[3] == "오류 span: 0"` · `"uid metrics   prom  (env:OBS_UID_METRICS)"`(공백 정확히) 같은 출력 형식 검사가, `test_error_messages_never_carry_token` 같은 약속 검사와 같은 파일·같은 밀도로 있다 | 소유해야 할 것(약속)과 안 읽어도 될 것(형식)이 구분되지 않는다 — 사람의 답 2·3 이 정확히 이 지점이다 |

반대로 **가장 잘 읽히는 테스트는 구조 테스트**다 — `test_get_only.py`(HTTP 는 core 만 · Request 호출 정확히 하나 · 메서드 문자열 없음), `test_get_logical_names_only`, `test_error_messages_never_carry_token`, `test_token_only_from_env`.
이들이 곧 사람이 소유하려는 "구조적 약속" 이고, 하나의 주장을 하나의 테스트가 한다.
즉 **agent 는 읽히는 테스트를 쓸 줄 안다 — 규약이 없어서 섞어 쓸 뿐이다.**

### 8-2. 외부 자료가 이 지점에 대해 말하는 것

- Beck: 통제 수단은 코드 읽기가 아니라 **테스트가 사람의 의도를 붙드는 것**. 한 번에 한 테스트. agent 의 테스트 삭제·조작을 경계(§2-4).
- Anthropic RCT: 이해도를 보존한 패턴은 "코드+설명 동시 요청" — docstring 은 이미 그것이다. 부족한 것은 설명이 아니라 **단위**다.
- mutation testing 부활: coverage 는 agent 가 쉽게 채운다. *"Test strength will matter more than test volume"*(§2-5). 59개가 물어뜯는지는 세어 보기 전엔 모른다.
- Böckeler 의 SDD 비판: 마크다운을 더 만들면 리뷰가 더 지루해진다. 계획 게이트(답 4)에 올릴 것은 설계 문서가 아니라 **짧은 목록**이어야 한다.

### 8-3. 수렴하는 모양 — 사람은 테스트 *목록*을 소유한다

```
착수   agent: 티켓 AC → "약속 목록 + 각 약속을 검사할 테스트 이름" 표
       사람: 표를 승인한다 (왕복 1회 — 답 4)              ← 소유의 시점
구현   agent: 코드 + 테스트. 테스트 규약(8-4)을 따른다
보고   agent: AC 대조표의 근거 칸 = 테스트 이름 (코드 위치가 아니라)
       반증 subagent: 승인된 목록 ↔ 실제 테스트 대조 · 약화·동어반복 검출
검수   사람: 약속 테스트만 읽는다. 형식·구조·골격은 CI 결과만 (답 3)
```

사람이 읽는 양은 **약속의 수**에 비례하지 코드량에 비례하지 않는다.
#1 에 대입하면 약속은 대략 8개다 — GET 유일 · 논리 이름만 · 출력에 물리 없음 · 토큰은 env 만·문구에 안 실림 · 해석 순서 env→파일→기본값 · 설정 오류는 조용히 안 넘어감 · spill 상한 · 예산.
59 테스트 중 이 8개를 검사하는 것은 15개 안팎이고, 나머지는 형식·파서·골격이다.

### 8-4. 테스트 규약 — 후보

`.claude/rules/python-typehints.md` 와 같은 자리에 `python-tests.md` 로.
되돌리기 비용 0 이므로 ADR 이 아니라 규칙 파일이다.

- **한 테스트 = 한 주장.** 이름과 docstring 이 그 주장 하나를 말한다. "그리고" 가 들어가면 둘로 쪼갠다.
- **assert 를 `and` 로 잇지 않는다.** 조건마다 한 줄. 실패가 조건을 가리키게.
- **픽스처에서 나온 숫자는 유도를 보인다** — 픽스처를 파서로 다시 읽거나(`test_logql_streams` 방식), 픽스처를 작게 손으로 만든다. 맨 숫자를 두지 않는다.
- **약속 · 형식 · 구조를 파일로 나눈다** — `test_contracts.py`(사람이 읽는다) · `test_format.py`(출력 스냅샷) · `test_repo.py`(골격·manifest). 파일 이름이 곧 읽기 티어다(답 3).
- **conftest 의 트릭은 트릭이 아니게** — URL 조각 매칭 대신 명시적 라우트 키.

### 8-5. 남는 질문 — 이번엔 짧다

- **테스트 목록 승인을 어디에 두나.** `ticket-start` 6단계(착수 요약)를 게이트로 올리고 거기에 표를 넣는가, 아니면 별도 단계인가. 백그라운드 `ticket-run.py` 흐름은 이 게이트에서 멈춘다 — 감수한다고 했다.
- **mutation testing 을 넣는가.** `mutmut` 은 의존성 하나다(코어는 표준 라이브러리만이지만 dev 의존은 별개). 넣으면 "테스트가 물어뜯는가" 를 사람이 안 읽고 안다. 안 넣으면 반증 subagent 의 판단에 기댄다.
- **#1 자체를 어떻게 하나.** 머지 전에 테스트를 규약대로 재편하는 후속 커밋을 받을지, 머지하고 별도 Task 로 할지. 전자는 #93 이 더 길어지고, 후자는 규약 없는 테스트가 main 에 들어간다.

### 8-6. 임계선 재판정

§6 에서 후보로 둔 것이 구체화됐다 — **"검수 = 승인된 약속 목록과 그것을 검사하는 테스트를 읽는 것이며, 코드 자체를 읽는 것이 아니다."**
이것은 ADR-0017 이 말하는 close 의 전제(사람 검수)의 *내용*을 정한다.
한 번 공표하면 그 뒤 머지된 코드는 이 정의로 검수된 것이고, 되돌린다고 안 읽은 코드가 읽히지 않는다.
초안을 쓸 만하다 — 다만 8-5 첫 질문(게이트 자리)의 답이 Decision 에 들어가지 않도록(그건 하네스 관할) 주의한다.

파생 후보(발행은 사람의 확인 뒤):
- **obs-toolkit** Task — `python-tests.md` 규약 + `tests/` 를 약속·형식·구조로 재편
- **ticket-engineer** Task — `ticket-start` 착수 요약에 약속↔테스트 표 + 승인 게이트
- **ticket-engineer** Task — `ticket-report` 대조표의 근거 칸을 테스트 이름으로 · 반증 subagent 단계
- **ops-workflow** — design-partner 쪼갬 기준에 "한 Task = 한 자리에서 읽을 약속 수" (이 저장소의 agent 정의 — 티켓이 아니라 이 세션에서 고칠 수 있다)
