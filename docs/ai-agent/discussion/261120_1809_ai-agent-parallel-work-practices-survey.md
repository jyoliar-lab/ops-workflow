---
type: discussion
kind: survey
goal: parallel-agent-work-human-impact
topic: ai-agent
subjects: [claude-code, git-worktree, subagent, agent-teams, agent-view, codex, copilot-coding-agent, cursor, jules, devin, gas-town]
status: done
related:
  - docs/ai-agent/discussion/261120_1810_parallel-agent-work-human-impact.md
---

# AI agent 병렬 작업의 모범 사례 — 조사 (2026-11-20)

## 질문

한 사람이 여러 AI coding agent 세션을 동시에 돌리는 방식이 무엇을 근거로 누구에게서 권장되는지를 알고자 했다.
구체적으로는 (1) 벤더가 권하는 병렬 수·작업 단위·격리·검토 방식, (2) 실무자가 보고하는 병렬 수와 병목, (3) 병렬을 성립시키는 조건으로 제시되는 것, (4) 그 방식에서 인간이 실제로 하는 일과 그 비용에 대한 실증, (5) 병렬을 제한하거나 권하지 않는 목소리를 모았다.
조사일은 2026-11-20이며, 판정·권고는 담지 않는다.

출처 성격 표기: **[벤더]** 벤더의 공식 문서·엔지니어링 글 / **[경험]** 개인의 경험담·의견 / **[실증]** 연구·설문 / **[2차]** 1차 출처를 직접 열지 못하고 2차 보도에 기댄 것.

## 조사

### 1. 벤더가 권하는 병렬 작업 방식

#### 1.1 Anthropic — Claude Code

**[벤더] Best practices for Claude Code** — https://code.claude.com/docs/en/best-practices (게시일 표기 없음, 2026-11-20 열람)

병렬 세션의 격리 단위로 git worktree를 권한다.

> When you have separate pieces of work going at once, give each its own checkout so the edits can't collide.

대규모 기계적 변경에 대해서는 작업을 단위로 쪼개 각각 worktree에서 돌리는 `/batch`를 소개하며, 사람의 승인 지점은 계획 승인이다.

> For one big mechanical change across many files, `/batch migrate every handler to the v2 response helpers` splits the work into 5 to 30 units and shows you the plan. Once you approve it, each unit gets its own worktree and opens a PR or reports what happened.

두 번째 세션을 독립 검토자로 쓰는 방식을 권하며, 이때 사람은 메시지를 옮기는 역할을 한다.

> A second session is also the easiest independent reviewer you can get. One session writes the rate limiter, another reviews `@src/middleware/rateLimiter.ts` without having watched it being written, and you paste the findings back into the first. Same idea as `/code-review`, with you carrying the messages.

subagent의 비용과 효용을 이렇게 서술한다.

> What they cost you is mostly tokens, since every subagent sends its own requests and they count against the same usage as your main conversation. Sometimes it's time as well: a fresh subagent first has to gather context your conversation already had, so it can end up *slower* than doing the task where you are.

> And by default it's the same model (or a smaller one) on the same task. You get parallelism or a fresh pair of eyes out of it, but not a smarter answer.

검토 에이전트의 지적을 전부 받아들이는 것에 대한 경고도 있다.

> A reviewer that's asked to find problems will always find *something*. If you fix every finding, you end up with extra abstraction layers and tests for cases that can't happen.

**[벤더] Common workflows — Run parallel sessions with worktrees** — https://code.claude.com/docs/en/common-workflows (2026-11-20 열람)

> Work on a feature in one terminal while Claude fixes a bug in another, without the edits colliding. Each git worktree is a separate checkout on its own branch, created from an existing commit

**[벤더] Agent view (`claude agents`, research preview)** — https://code.claude.com/docs/en/agent-view (2026-11-20 열람, 페이지 후반부 Limitations 절은 열람 범위 밖)

여러 background 세션을 한 화면에서 감독하는 도구이며, 사람의 역할을 "필요할 때만 개입"으로 서술한다.

> Agent view, opened with `claude agents`, is one screen for all your background sessions: what's running, what needs your input, and what's done. Dispatch new sessions, watch their state at a glance instead of scrolling through transcripts, and step in only when one needs you.

> Dispatch a bug fix, a pull request review, and a flaky-test investigation as three rows, keep working in another window, and check back when a row shows it needs you or has a result.

복귀는 알림 기반이다.

> While agent view is open, Claude Code also sends a notification through your configured terminal notification channel when a local background session starts needing your input, finishes, or fails.

검토는 전문(transcript)이 아니라 요약 패널과 PR 상태로 하도록 설계되어 있다.

> Most of the time the peek panel is enough and you don't need to open the full transcript.

> For a task that ends in a pull request, check this label for the result: review and merge the pull request when its number turns green.

병렬 수에 대한 수치 상한은 없고, 독립성과 파일 충돌 회피를 조건으로 든다.

> Use agent view when you have several independent tasks Claude can work on without you watching every step.

> Outside a git repository, sessions write to the working directory directly and aren't isolated from each other, so avoid dispatching parallel sessions that edit the same files.

**[벤더] Agent teams (experimental)** — https://code.claude.com/docs/en/agent-teams (2026-11-20 열람)

벤더 문서 중 병렬 수에 대한 가장 구체적인 권고가 여기 있다.

> Start with 3-5 teammates for most workflows. This balances parallel work with manageable coordination. If you have 15 independent tasks, 3 teammates is a good starting point.

> Scale up only when the work benefits from having teammates work simultaneously. Three focused teammates often outperform five scattered ones.

적합/부적합 작업:

> Agent teams add coordination overhead and use significantly more tokens than a single session. They work best when teammates can operate independently. For sequential tasks, same-file edits, or work with many dependencies, a single session or subagents are more effective.

작업 단위:

> **Just right**: self-contained units that produce a clear deliverable, such as a function, a test file, or a review

> Having 5-6 tasks per teammate keeps everyone productive and lets the lead reassign work if someone gets stuck.

처음 쓰는 사람에게는 코드 작성이 없는 작업부터 권한다.

> If you're new to agent teams, start with tasks that have clear boundaries and don't require writing code: reviewing a PR, researching a library, or investigating a bug.

사람의 역할로 감독·방향 수정을 명시한다.

> Check in on teammates' progress, redirect approaches that aren't working, and synthesize findings as they come in. Letting a team run unattended for too long increases the risk of wasted effort.

권한 요청이 사람에게 몰리는 마찰도 언급한다.

> Teammate permission requests bubble up to the lead, which can create friction. Pre-approve common operations in your permission settings before spawning teammates to reduce interruptions.

**[벤더] How we built our multi-agent research system** — https://www.anthropic.com/engineering/multi-agent-research-system (2025-06-13)

연구(research) 작업에서 다중 agent의 이득과, coding 작업에서의 한계를 함께 서술한다.

> multi-agent systems use about 15× more tokens than chats

> most coding tasks involve fewer truly parallelizable tasks than research

> domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today

#### 1.2 OpenAI — Codex

**[벤더] Codex cloud 문서** — https://learn.chatgpt.com/docs/cloud (developers.openai.com/codex/cloud에서 리다이렉트, 2026-11-20 열람)

작업마다 별도 작업 공간을 두는 격리와, 사람의 검토 후 커밋/PR 흐름을 서술한다.
병렬 실행 수나 best-of-N에 대한 서술은 이 페이지에 없었다.

> Each task has its own workspace and can keep working while your computer is asleep.

> Inspect changed files and check results, request follow-up changes, and commit or open a pull request when you're ready.

**[벤더/2차] How OpenAI uses Codex** — https://openai.com/business/guides-and-resources/how-openai-uses-codex/ — **원문 미확인**(HTTP 403).
검색 요약에 따르면 이 가이드는 "약 한 시간 분량의 사람 작업, 또는 수백 줄 규모"의 잘 범위 지어진 작업을 권한다고 하나, 원문 문장은 확인하지 못했다.
Codex CLI의 `--attempts`(best-of-N) 등 병렬 시도 기능에 대한 설명도 3자 블로그에서만 확인되어 여기서는 다루지 않는다.

#### 1.3 GitHub — Copilot coding agent (cloud agent)

**[벤더] Get the best results** — https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results (2026-11-20 열람)

> GitHub Copilot provides better results when assigned clear, well-scoped tasks.

적합하지 않은 작업으로 보안·PII·인증 관련, 정의가 모호한 작업, 그리고 **개발자가 배우고자 하는 작업**을 든다.

> Tasks where the developer wants to learn to achieve a deeper understanding.

검토는 사람 PR과 동일한 절차로 한다고 서술한다.

> The process for getting the pull request to a mergeable state is exactly the same

이 문서는 여러 작업의 병렬 실행을 직접 다루지 않는다.

#### 1.4 Cursor — worktree·best-of-n

**[벤더] Worktrees** — https://cursor.com/docs/configuration/worktrees (2026-11-20 열람)

> Use worktrees when you want to start several agents on the same repo without conflicts.

> `/best-of-n` runs the same task across multiple models at once.

> Each run gets its own worktree, so the candidates stay isolated from each other and from your main checkout.

비교·채택은 사람이 한다.

> `/best-of-n` compares runs only. It does not merge changes back into your main checkout for you.

동시 agent 수 상한은 문서에 없고, worktree 정리 상한(기본 25개/머신)만 있다.
"Run up to eight agents in parallel on a single prompt"라는 Cursor 2.0 changelog 문구는 3자 글에서만 인용되었고 **원문 미확인**이다.

#### 1.5 Google — Jules

**[2차] TechCrunch, "Google's AI coding agent Jules is now out of beta"** — https://techcrunch.com/2025/08/06/googles-ai-coding-agent-jules-is-now-out-of-beta (2025-08-06)

> an asynchronous, agent-based coding tool

> capped at 15 individual daily tasks and three concurrent ones

유료 등급의 동시 작업 수(15·60)는 3자 비교 페이지에만 있어 **원문 미확인**이다.
Jules 공식 문서는 열지 못했다.

#### 1.6 Cognition — Devin

**[벤더] When to Use Devin** — https://docs.devin.ai/essential-guidelines/when-to-use-devin (2026-11-20 열람)

> Tasks with test suites, CI checks, or verifiable outcomes yield the best results.

> Splitting large requests into smaller, manageable chunks helps Devin stay on track.

> Carve out independent tasks and run them simultaneously.

> Review findings Devin escalated, check CI, and decide whether the PR is ready to merge.

같은 문서는 약 3시간 이하 작업을 적합 범위로 든다(도구 요약에 의한 의역, 원문 문장 미인용).

#### 1.7 벤더 권고 비교

| 벤더 | 격리 단위 | 병렬 수 언급 | 작업 단위 | 사람의 검토·승인 지점 |
|---|---|---|---|---|
| Anthropic (Claude Code) | git worktree, cloud 세션 | agent teams: 3~5 시작 / `/batch`: 5~30 단위 / agent view: 수치 없음 | 독립적·명확한 산출물, 같은 파일 편집 회피 | 계획 승인(plan mode·`/batch`), 권한 요청, PR 검토·머지(agent는 머지 안 함) |
| OpenAI (Codex cloud) | 작업별 workspace | 공식 페이지에서 확인 못함 | (원문 미확인) 약 1시간 분량 | 변경 파일 검사 후 커밋/PR |
| GitHub (Copilot) | — (병렬 미언급) | 미언급 | 명확·범위 지어진 이슈, 수용 기준 포함 | PR 검토, `@copilot` 코멘트로 반복 |
| Cursor | worktree | 수치 없음(정리 상한 25) | best-of-n은 같은 작업 다중 실행 | 후보 비교 후 사람이 apply |
| Google (Jules) | Cloud VM | 무료 3 동시(2차) | — | — |
| Devin | 세션별 머신 | 수치 없음 | 약 3시간 이하, 검증 가능 | 에스컬레이션 검토, CI 확인, 머지 판단 |

### 2. 실무자 경험

**[경험] Simon Willison, "Embracing the parallel coding agent lifestyle"** — https://simonwillison.net/2025/Oct/5/parallel-coding-agents/ (2025-10-05)

> I frequently have multiple terminal windows open running different coding agents in different directories.

병목을 검토로 지목한다.

> the natural bottleneck on all of this is how fast I can review the results.

병렬에 적합한 작업으로 연구, 작은 유지보수, 자신의 명세에서 출발한 작업을 든다.

> Research tasks answer questions or provide recommendations without making modifications to a project that you plan to keep.

> Code that started from your own specification is a lot less effort to review.

중대한 변경은 한 번에 하나만 검토·반영한다고 쓴다(도구 요약의 부분 인용: "reviewing and landing one significant change at a time").

**[경험] Simon Willison, Lenny's Podcast "An AI state of the union"** — https://simonwillison.net/2026/Apr/2/lennys-podcast/ (2026-04-02)

> I can fire up four agents in parallel and have them work on four different problems. And by like 11 AM, I am wiped out for the day.

> using coding agents well is taking every inch of my 25 years of experience

> There's a personal skill we have to learn in finding our new limits

> losing sleep because they're like, my coding agents could be doing work for me

> There's an element of sort of gambling and addiction to how we're using some of these tools.

**[경험/2차] Boris Cherny (Claude Code 제작자)의 작업 방식** — InfoQ, https://www.infoq.com/news/2026/01/claude-code-creator-workflow (2026-01-10). 원 X 스레드(https://x.com/bcherny/status/2007179832300581177)는 **원문 미확인**.
InfoQ에 따르면 로컬 터미널에서 5개, 웹(claude.ai/code)에서 5~10개 세션을 병렬로 돌린다.
InfoQ가 인용한 그의 말:

> If my goal is to write a Pull Request, I will use Plan mode, and go back and forth with Claude until I like its plan.

> The most important tip is to give Claude a way to verify its work through a feedback loop.

"탭에 1~5 번호를 매기고 시스템 알림으로 입력이 필요한 세션을 안다"는 인용은 여러 2차 글에 반복되나 원문 미확인이다.

**[경험] Mitchell Hashimoto, "My AI Adoption Journey"** — https://mitchellh.com/writing/my-ai-adoption-journey (2026-02-05)

background agent를 병렬이 아니라 하나씩 돌린다고 쓴다.

> one at a time, not in parallel

알림으로 호출되지 않도록 알림을 끈다.

> turn off agent desktop notifications

> Don't let the agent notify you.

background agent를 근무일의 약 10~20% 동안만 효과적으로 돌린다고 보고한다(도구 요약에 의한 의역).
위임에 따른 기술 형성 상실을 언급한다.

> not forming skills for the tasks you're delegating to the agent

**[경험/2차] Steve Yegge, Gas Town** — 원 글 "Welcome to Gas Town"(https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04, 2026-01-01경)은 **원문 미확인**(HTTP 403).
2차 보도에 따르면 20~30개의 Claude Code agent를 tmux 기반으로 동시에 조율하는 오케스트레이터이며, 비용 부담을 본인이 언급했다.

**[경험/2차] Steve Yegge, "The AI Vampire"** — 원 글(https://steve-yegge.medium.com/the-ai-vampire-eda6e4f07163, 2026-02) **원문 미확인**.
Simon Willison의 링크 글(https://simonwillison.net/2026/Feb/15/the-ai-vampire/, 2026-02-15)이 이렇게 요약·인용한다.

> Steve reports needing more sleep due to the cognitive burden involved in agentic engineering

> four hours of agent work a day is a more realistic pace

Yegge 원문 인용(Willison 글 경유):

> And you're exhausted. You're tired, Boss.

"하루 3시간 상한" 수치는 3자 요약에만 있어 원문 미확인이다.

**[경험] Maggie Appleton, Gas Town 논평** — https://maggieappleton.com/gastown (2026-01 중순 이후, 정확한 게시일 미표기)

> Design becomes the limiting factor

자신을 "agentically conservative camp"로 두고, 소수의 agent만 돌리며 diff에 주의를 기울인다고 쓴다(도구 요약; "my eyes and hands on the code" 부분 인용).

**[경험] Geoffrey Huntley, "Ralph Wiggum as a 'software engineer'"** — https://ghuntley.com/ralph/ (2025-07-14)

> In its purest form, Ralph is a Bash loop.

> To get good outcomes with Ralph, you need to ask Ralph to do one thing per loop. **Only one thing**.

검색·쓰기는 병렬 subagent로 넓히되, 빌드·테스트(검증)는 한 개로 제한하는 프롬프트를 소개한다(back pressure 때문이라고 설명).

> There is no way this is possible without senior expertise guiding Ralph.

**[경험] Addy Osmani, "Your parallel Agent limit"** — https://addyosmani.com/blog/cognitive-parallel-agents/ (2026-04-07)

> somewhere around three to four threads depending on complexity

> one thread less than feels right

> What scales is your throughput of supervision, not your throughput of understanding.

> Your cognitive bandwidth doesn't parallelize.

> the cost isn't in the switch itself - it's in the recovery time

(전환 비용 근거로 "task-switching research"를 들지만 특정 연구를 명시하지 않는다.)

### 3. 병렬을 성립시키는 조건으로 제시되는 것

출처들이 공통으로 드는 조건을 출처와 함께 나열한다(평가하지 않음).

| 조건 | 제시한 출처 |
|---|---|
| 작업의 독립성·같은 파일 편집 회피 | Claude Code agent teams·agent view, Anthropic multi-agent 글, Devin("Carve out independent tasks"), Cursor worktrees |
| 격리(worktree·작업별 workspace·VM) | Claude Code best practices·common workflows, Cursor, Codex cloud, Jules(2차), Devin |
| 명세·계획 선행 | Claude Code best practices(`SPEC.md`·plan mode·`/batch` 계획 승인), Boris Cherny(2차), Willison("own specification"), Copilot(수용 기준) |
| 자동 검증(테스트·CI·피드백 루프) | Devin, Boris Cherny(2차), Claude Code best practices("Give Claude a check to run"), Huntley(빌드·테스트 back pressure) |
| 작업 크기 제한 | Devin(약 3시간 이하), Codex(약 1시간 — 원문 미확인), agent teams("self-contained units"), Huntley(한 루프 한 일) |
| 알림 기반 복귀 | Claude Code agent view, Boris Cherny(2차) — 반대로 Hashimoto는 알림을 끈다 |
| 사람의 승인 지점 | 계획 승인(`/batch`·plan mode), 권한 요청(agent teams), PR 머지(agent view: agent는 머지·main push 안 함), Devin 머지 판단, Cursor apply |

### 4. 인간 쪽 비용 — 실증 연구·설문

#### 4.1 병렬 agent 사용을 직접 다룬 연구

**[실증] Long et al., "ParallelPilot: Supporting Coordination and Monitoring in Parallel AI Coding"** — arXiv:2609.33113v1 (2026-09-27 제출, Columbia·Microsoft Research AI Frontiers) — https://arxiv.org/html/2609.33113v1

병렬 AI coding 세션을 정기적으로 쓰는 개발자 14명 인터뷰(형성 연구)와, 16명 within-subjects 사용자 연구(20분 블록 2회, 기준선은 GitHub Copilot CLI 또는 Chat)다.

> As coding assistants become increasingly autonomous, developers run multiple sessions in parallel

도구 요약에 따른 수치(7점 척도): 추적 노력 4.63→2.75, 장부 관리 노력 4.63→2.50, 컨텍스트 전환 방해 4.50→2.69, 에이전트 완료·입력 필요 인지 3.63→6.19, 완료 티켓 4.19→5.69(6개 중), 처리량 63% 증가, 최대 동시 agent 수 2.31→3.25.

> These gains were not accompanied by significant improvements in perceived control

참가자 발언(논문 인용):

> like a quarterback across three sessions

> couldn't even remember what I had told Copilot

> I don't wanna wait sequentially for things to happen.

이 연구는 감독 도구의 효과를 측정한 것이며, 병렬 사용 자체의 장기 영향을 측정한 것은 아니다.
본문 후반부(약 97,000자)는 열람하지 못했다.

**[실증] METR, "We are Changing our Developer Productivity Experiment Design"(uplift update)** — https://metr.org/blog/2026-02-24-uplift-update/ (2026-02-24)

후속 연구의 측정 실패 원인 중 하나로 동시 다중 agent 사용을 명시한다.

> our measurements of time-spent on each task are unreliable for the fraction of developers who use multiple AI agents concurrently.

> Some developers reported it was challenging to report time-spent in completing tasks when they used agentic tools,

> because they would often work an unrelated task while waiting for the agent to complete its work.

추정치: 기존 참가자 "a speedup of -18% with a confidence interval between -38% and +9%", 신규 참가자 "the estimated speedup is -4%, with a confidence interval between -15% and +9%".
METR 자신이 이 데이터를 "unreliable signal of the current productivity effect of AI tools"로 표시하며, 그 이유로 선택 효과(AI 없이 일하기를 원치 않아 참여를 거부하는 개발자)를 든다.

> developers choosing not to participate in the study because they do not wish to work without AI

**병렬 agent 사용이 인간에게 미치는 영향(인지 부하·피로·검토 품질·이해도)을 직접 측정한 통제 연구는 이번 조사에서 찾지 못했다.**
ParallelPilot은 감독 인터페이스의 효과를, METR는 생산성 측정의 교란 요인으로서의 병렬 사용을 다룰 뿐이다.

#### 4.2 agent 감독 일반을 다룬 연구

**[실증] Wu et al., "From Delegation to Action Approval: An Exploratory Study of Developers' Practices in Collaborating with AI Coding Agents"** — arXiv:2611.10058 (2026-11-06 제출) — https://arxiv.org/abs/2611.10058

AI coding agent 사용 개발자 203명 설문.

> careful code review does not necessarily extend to action approval

도구 요약에 따른 수치: 생성 코드를 대부분/전부 꼼꼼히 검토한다는 개발자 중 61%가 적어도 한 종류의 agent 행동(셸 명령 등)을 면밀한 검토 없이 자주 승인했다.
전반적 작업 부하는 줄었다고 보고했으나 agent 감독은 여전히 정신적으로 부담스럽다고 보고했다.
"83%가 부하 감소를 보고", "203명 중 101명이 부하 감소와 동시에 10개 감독 활동 중 5개 이상을 매우/극도로 정신적 부담이 크다고 평가"라는 수치는 Substack 2차 글(https://thehybridleader.substack.com/p/how-many-ai-agents-can-you-actually)에서만 확인했고 **논문 원문에서 미확인**이다.
초록 페이지에서 병렬 사용에 대한 서술은 확인하지 못했다.

**[실증] Park et al., "The Work Behind Delegation: A Framework for Supervising AI Coding Agents"** — arXiv:2609.24234 (2026-09-21 제출) — https://arxiv.org/abs/2609.24234

숙련 개발자 19명의 관찰·워크플로 다이어그램으로 Sheridan의 human supervisory control 틀을 7단계로 재구성하고 Reddit 논의에 적용했다.

> developers are shifting from direct implementation toward supervising delegated work

> supervisory demands extend across stages

대응 방식으로 계획 단계에 노력을 집중, 감독 작업 일부를 다른 agent에 위임, 반복 지침을 재사용 자산으로 전환을 보고한다(도구 요약).
병렬 사용은 직접 다루지 않는다.

**[실증] Balepur et al., "(Im)Paired Programming: Coding Agents Improve Productivity but Harm Understanding"** — arXiv:2607.26375 (2026-07-29 제출) — https://arxiv.org/abs/2607.26375

학생 54명, 코드 편집 agent 대 chatbot 비교.
agent가 초기 완료를 돕지만 "harm users' code comprehension"하며, 복사-붙여넣기 프롬프트·자동 수락 같은 저노력 상호작용이 낮은 이해도와 연관된다고 보고한다(초록 요약; 수치는 미확인).
사용자는 이해도가 낮아졌다고 느끼면서도 agent를 선호했다고 한다.
단일 agent 사용이며 병렬은 다루지 않는다.

#### 4.3 속도 지각과 실측

**[실증] METR, "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity"** — https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ (2025-07-10)

숙련 오픈소스 개발자 16명, 246개 이슈 RCT, 주 도구 Cursor Pro + Claude 3.5/3.7 Sonnet.

> When developers are allowed to use AI tools, they take 19% longer to complete issues

개발자들은 사전에 24% 가속을 기대했고, 사후에도 20% 가속됐다고 믿었다(페이지 요약).
현재 페이지에는 결과가 최신이 아니라는 표시가 붙어 있다.

> We have released results that are current as of early 2026.

이 연구는 병렬 agent 이전 시기·도구를 대상으로 한다.

#### 4.4 기술 형성·이해 부채

**[실증] Shen & Tamkin (Anthropic), "How AI assistance impacts the formation of coding skills"** — https://www.anthropic.com/research/AI-assistance-coding-skills (2026-01-29), 논문 arXiv:2601.20245

> recruited 52 (mostly junior) software engineers

> participants in the AI group scored 17% lower than those who coded by hand

평균 점수 50%(AI) 대 67%(수작업), AI 그룹이 약 2분 빨랐으나 통계적으로 유의하지 않았다(페이지 요약).
높은 점수를 낸 참가자는 AI를 이해 형성에 썼다.

> used AI assistance not just to produce code but to build comprehension while doing so.

저자들은 소표본·단기 측정의 예비 연구라고 밝힌다.
단일 AI 지원 사용이며 병렬·agent 감독은 다루지 않는다.

**[실증] Lee et al. (Microsoft Research·CMU), "The Impact of Generative AI on Critical Thinking"** — CHI 2025, DOI 10.1145/3706598.3713778 — https://www.microsoft.com/en-us/research/?p=1135061

> survey 319 knowledge workers

> higher confidence in GenAI is associated with less critical thinking

> higher self-confidence is associated with more critical thinking

> shifts the nature of critical thinking toward information verification, response integration, and task stewardship

coding agent·병렬 사용 특정 연구가 아니라 지식 노동자 일반 대상이다.

**[경험] Addy Osmani, "Comprehension Debt"** — https://addyosmani.com/blog/comprehension-debt/ (2026-03-14)

> Comprehension debt is the growing gap between how much code exists in your system

> What used to be a quality gate is now a throughput problem.

(그가 인용한 "AI 위임 시 이해도 40% 미만 대 개념 질의 시 65% 초과" 수치는 출처 미명시다.)

**[경험] Mario Zechner, "Thoughts on slowing the fuck down"** — Simon Willison 링크 글 경유, https://simonwillison.net/2026/Mar/25/thoughts-on-slowing-the-fuck-down/ (2026-03-25). Zechner 원 글은 **원문 미확인**(Willison 글 내 인용으로만 확인).

> Set yourself limits on how much code you let the clanker generate per day

agent 군단에는 "there is no bottleneck, no human pain"이라 작은 오류가 빠르게 복리로 쌓인다는 주장.
Willison의 논평:

> Cognitive debt is real.

#### 4.5 조직 수준 설문·작업 강도

**[실증] DORA 2025 "State of AI-assisted Software Development"** — Google 블로그 요약 https://blog.google/technology/developers/dora-report-2025/ (2025-09-23). 보고서 PDF 원문은 **미열람**.

> AI adoption among software development professionals has surged to 90%

> AI adoption is now linked to higher software delivery throughput

> Over 80% of respondents indicate that AI has enhanced their productivity.

신뢰는 "a great deal"(4%)·"a lot"(20%)으로 24%.
보고서는 AI를 "mirror and a multiplier"로 서술한다.
안정성(instability) 수치와 "small batches" 관련 서술은 2차 출처에서만 확인되어 미확인이다.
병렬 agent 사용을 따로 측정하지 않는다.

**[실증/2차] Ranganathan & Ye (UC Berkeley Haas), "AI Doesn't Reduce Work—It Intensifies It"** — HBR, 2026-02-09, https://hbr.org/2026/02/ai-doesnt-reduce-work-it-intensifies-it — **원문 미확인**.
2차 보도에 따르면 미국 기술 기업 직원 약 200명을 8개월(2025-04~12) 관찰했고, 작업 범위 확장·일과 삶 경계 흐려짐·멀티태스킹 증가를 보고했다.
LeadDev가 인용한 연구자 문장:

> these experiments accumulated into a meaningful widening of job scope,

**[2차] LeadDev, "'Addictive' agentic coding has developers losing sleep"** — https://leaddev.com/ai/addictive-agentic-coding-has-developers-losing-sleep (2026-03-30, Sage Lazzaro)

실무자 발언:

> the cognitive overhead of managing AI-generated output can increase as well,

> And the weekends just disappear,

Margaret-Anne Storey(University of Victoria):

> It is about whether individual developers and product teams can maintain a coherent mental model

같은 기사가 인용한 설문(각 원 보고서는 **원문 미확인**): Multitudes(500명 이상) AI 사용자의 근무 외 커밋 19.6% 증가, ActivTrak(163,638명, 2023~2025) 토요일 생산 시간 46%·일요일 58% 증가.

### 5. 병렬을 제한하거나 권하지 않는 목소리

| 출처 | 성격 | 내용 |
|---|---|---|
| Anthropic multi-agent research 글 (2025-06-13) | 벤더 | coding은 research보다 진짜 병렬화 가능한 작업이 적다. 컨텍스트 공유·의존이 많은 영역은 다중 agent에 부적합 |
| Claude Code agent teams 문서 | 벤더 | 3~5로 시작, "Three focused teammates often outperform five scattered ones", 순차·같은 파일·의존 많은 작업은 단일 세션 |
| Claude Code best practices | 벤더 | subagent는 더 나은 답을 주지 않고, 컨텍스트 재수집 때문에 더 느릴 수 있다 |
| GitHub Copilot 문서 | 벤더 | 배우려는 작업·모호한 작업·보안 작업은 위임 부적합 |
| Mitchell Hashimoto (2026-02-05) | 경험 | background agent를 하나씩, 알림 끔 |
| Geoffrey Huntley (2025-07-14) | 경험 | 한 루프 한 일, 검증은 subagent 1개로 제한 |
| Addy Osmani (2026-04-07) | 경험 | 본인 상한 3~4, "one thread less than feels right" |
| Simon Willison (2025-10-05·2026-04-02) | 경험 | 중대한 변경은 한 번에 하나 검토, 4개 병렬 시 오전 11시에 소진 |
| Yegge via Willison (2026-02-15) | 경험(2차) | 하루 4시간 agent 작업이 현실적 |
| Mario Zechner via Willison (2026-03-25) | 경험 | 하루 생성 코드량을 검토 가능량으로 제한 |
| Maggie Appleton (2026-01~) | 경험 | 소수 agent, diff 직접 확인, 설계가 제한 요인 |

## 논의 문서로 가져가는 것

- Anthropic 문서는 병렬 세션의 격리 단위로 git worktree를 권하고, 사람의 승인 지점을 계획 승인·권한 요청·PR 머지에 둔다(agent는 머지·main push를 하지 않는다).
- 벤더 문서 중 병렬 수의 구체 권고는 Claude Code agent teams의 "3-5 teammates로 시작"이 유일했고, agent view·Cursor·Devin·Codex cloud 문서에는 수치 상한이 없다.
- 벤더들이 공통으로 드는 병렬 성립 조건은 작업 독립성(같은 파일 회피), 격리, 명확한 범위·수용 기준, 자동 검증(테스트·CI)이다.
- 벤더 도구(agent view)는 사람의 역할을 "필요할 때만 개입"으로 설계하고, 복귀는 알림, 검토는 요약 패널과 PR 상태로 하도록 한다.
- Anthropic은 coding이 research보다 병렬화 가능한 작업이 적다고 쓰고, subagent가 더 나은 답을 주지 않으며 더 느릴 수 있다고 쓴다.
- 실무자 보고 병렬 수: Cherny 로컬 5 + 웹 5~10(2차), Willison 4, Osmani 3~4, Appleton 소수, Hashimoto 1(순차), Yegge 20~30(Gas Town, 2차).
- 실무자들이 지목하는 병목은 검토·감독이다(Willison "how fast I can review the results", Osmani "throughput of supervision", Appleton "Design becomes the limiting factor").
- 실무자 피로 보고: Willison 4개 병렬 시 오전 11시 소진, Yegge 수면 증가·하루 4시간이 현실적(Willison 경유), 수면 상실·중독성 언급(Willison, LeadDev).
- 알림에 대해 상반된 실천이 있다 — Claude Code agent view·Cherny는 알림 기반 복귀, Hashimoto는 알림을 끈다.
- 병렬 agent 사용이 인간에게 미치는 영향을 직접 측정한 통제 연구는 찾지 못했다.
- ParallelPilot(2026-09, n=16)은 병렬 감독 도구가 추적·장부·전환 부담 자기보고를 줄이고 처리량을 63% 높였으나, 통제감·개입 성공·산출물 신뢰는 유의하게 개선되지 않았다고 보고한다.
- METR(2026-02-24)는 여러 agent를 동시에 쓰는 개발자의 작업 시간 측정이 신뢰할 수 없고, agent 대기 중 무관한 작업을 한다는 보고가 있었다고 밝힌다.
- METR 2025 RCT(n=16)는 AI 사용 시 19% 느렸고 개발자는 20% 빨라졌다고 믿었다 — 단 병렬 agent 이전 도구 대상이며 METR 스스로 최신이 아니라고 표시한다.
- Wu et al.(2026-11, n=203)은 코드를 꼼꼼히 검토하는 개발자의 61%가 agent 행동 일부를 면밀한 검토 없이 자주 승인한다고 보고한다.
- Anthropic 기술 형성 RCT(n=52)는 AI 그룹의 이해도 퀴즈 점수가 17% 낮았고 속도 차이는 유의하지 않았으며, 이해 형성에 AI를 쓴 사람은 점수가 높았다고 보고한다.
- Microsoft·CMU(n=319)는 GenAI에 대한 신뢰가 높을수록 비판적 사고가 줄고, 사고의 성격이 검증·통합·과업 관리로 이동한다고 보고한다.
- (Im)Paired Programming(n=54 학생)은 coding agent가 완료를 돕지만 코드 이해를 해친다고 보고한다.
- DORA 2025는 채택 90%, 처리량 증가를 보고하나 AI 신뢰는 24%에 그치며 병렬 사용은 따로 측정하지 않는다.
- 작업 강도에 대해 UC Berkeley(HBR, 2차)는 작업 범위 확장·멀티태스킹 증가를, Multitudes·ActivTrak(2차)는 근무 외·주말 작업 증가를 보고한다.
- Copilot 문서는 개발자가 배우려는 작업을 위임 부적합으로 분류하고, Hashimoto는 위임이 그 작업의 기술 형성을 막는다고 쓴다.
