---
type: discussion
kind: survey
goal: parallel-agent-work-human-impact
topic: ai-agent
subjects: [task-switching, attention-residue, interruption, media-multitasking, vigilance-decrement, automation-complacency, out-of-the-loop, fan-out, wip-limit]
status: done
related:
  - docs/ai-agent/discussion/261120_1810_parallel-agent-work-human-impact.md
---

# 인간의 병렬 작업(멀티태스킹)에 관한 연구 — 조사 (2026-11-20)

## 질문

AI agent 이전 시대에 "여러 작업을 병렬로 진행하면 효율이 떨어지고 뇌 건강에도 나쁘다"고 알려진 통념이 실제로 어떤 1차 문헌에 기대고 있는지 확인하고자 했다.
작업 전환 비용·주의 잔여·중단과 재개·미디어 멀티태스킹·"뇌 건강" 주장·병렬 프로젝트 수와 생산성·반대 증거·자동화 감독의 인지 부하를 범위로 삼았다.
각 주장마다 효과 크기, 실험 조건, 표본, 연구 설계(실험/관찰/상관)의 한계를 함께 모으고, 대중적으로 과장·오인용된 수치는 원 출처와 대조했다.
이 문서는 사실만 모으며 판정·권고는 하지 않는다.

## 조사

### 0. 출처 확인 방식

- "원문 확인"은 논문 PDF 본문, PubMed/Crossref/Semantic Scholar의 초록, 또는 저자 본인의 문서를 직접 열어 읽었다는 뜻이다.
- 블록 인용은 그렇게 연 원문에서 그대로 옮긴 것이다.
- 검색 결과 요약이나 2차 출처(기사·블로그)에만 기댄 내용은 그 자리에 **(2차 출처)** 또는 **(원문 미확인)**으로 표시했다.

---

### 1. 작업 전환 비용 (task switching cost)

#### 1.1 Rubinstein, Meyer & Evans (2001)

- 출처: Rubinstein, J. S., Meyer, D. E., & Evans, J. E. (2001). Executive control of cognitive processes in task switching. *Journal of Experimental Psychology: Human Perception and Performance*, 27(4), 763–797. DOI 10.1037/0096-1523.27.4.763. 본문 PDF: https://leaddev.com/wp-content/uploads/2023/01/xhp274763.pdf (원문 확인)
- 설계: 실험 4건이고, 도형 분류 규칙 전환(실험 1·4)과 산술 연산 전환(실험 2·3)을 다뤘다.
- 표본은 실험별로 대학생 12명, 36명, 36명, 24명이다.

> In 4 experiments, participants alternated between different tasks or performed the same task repeatedly. [...] Task alternation yielded switching-time costs that increased with rule complexity but decreased with task cuing. These factor effects were additive, supporting a model of executive control that has goal-shifting and rule-activation stages for task switching.

- 효과 크기(전환 블록 RT − 반복 블록 RT):
  - 실험 1(도형 분류)은 "substantial switching-time costs (M = 975 ms, SE = 71 ms)"였다.
  - 실험 2(산술)는 "the overall mean switching-time cost was 653 ms"였다.
  - 실험 3(산술)은 "(M = 614 ms, SE = 237 ms)"였다.
  - 과제 단서(cue)가 있으면 전환 비용이 줄었다("switching-time costs were reliably lower with task cues present rather than absent ... mean difference = 467 ms").
- 한계: 수백 ms~1초 규모의 반응시간 차이이고, 단순하고 인위적인 실험실 과제에서 측정했다.
- 논문 자체에는 "생산 시간의 몇 %"와 같은 업무 수준 환산치가 없다(본문에서 "percent"·"40" 검색 결과 해당 진술 없음).

#### 1.2 "전환으로 생산 시간의 40%를 잃는다" — APA 페이지

- 출처: APA, "Multitasking: Switching costs", Date created: 2006. https://www.apa.org/topics/research/multitasking (Wayback 사본으로 원문 확인 — 현행 페이지는 자동 요청 차단)

> Meyer has said that even brief mental blocks created by shifting between tasks can cost as much as 40 percent of someone's productive time.

- 이 문장은 "Meyer has said"라는 발언 인용 형식이고, 페이지는 그 40% 수치에 대해 특정 실험이나 측정을 출처로 대지 않는다.
- 같은 페이지는 실험실 비용의 크기를 다음과 같이 적는다.

> Although switch costs may be relatively small, sometimes just a few tenths of a second per switch, they can add up to large amounts when people switch repeatedly back and forth between tasks.

- 즉 실험으로 측정된 것은 전환당 수백 ms이고, "40%"는 그것을 업무 시간으로 외삽한 발언이다.
- 이 40%가 어떤 계산이나 측정에서 나왔는지는 찾지 못했다(원문 미확인).

#### 1.3 Monsell (2003) — 리뷰

- 출처: Monsell, S. (2003). Task switching. *Trends in Cognitive Sciences*, 7(3), 134–140. DOI 10.1016/s1364-6613(03)00028-7 (PubMed 초록 원문 확인)

> Subjects' responses are substantially slower and, usually, more error-prone immediately after a task switch. This 'switch cost' is reduced, but not eliminated, by an opportunity for preparation. It seems to result from both transient and long-term carry-over of 'task-set' activation and inhibition as well as time consumed by task-set reconfiguration processes.

- 핵심은 준비 시간이 있어도 사라지지 않는 잔여 전환 비용(residual switch cost)이다.
- 리뷰의 근거 실험도 "a small set of simple tasks" 사이의 빈번한 전환이다.

#### 1.4 자발적 전환도 비용이 있다 — Arrington & Logan (2004)

- 출처: Arrington, C. M., & Logan, G. D. (2004). The cost of a voluntary task switch. *Psychological Science*, 15(9), 610–615. DOI 10.1111/j.0956-7976.2004.00728.x (PubMed 초록 원문 확인)

> Task alternations were slower than task repetitions, and this switch cost was greater at the short RSI than at the long RSI (310 and 94 ms, respectively). Additionally, subjects produced more task repetitions than expected if the tasks were performed in a random sequence.

- 스스로 과제를 고르는 조건에서도 전환 비용이 남고, 준비 간격이 길면 크게 줄어든다(310 → 94 ms).

---

### 2. 주의 잔여 (attention residue)

#### 2.1 Leroy (2009)

- 출처: Leroy, S. (2009). Why is it so hard to do my work? The challenge of attention residue when switching between work tasks. *Organizational Behavior and Human Decision Processes*, 109(2), 168–181. DOI 10.1016/j.obhdp.2009.04.002 (EconPapers 초록 원문 확인. 본문은 유료라 미확인)

> As revealed by two experiments, people need to stop thinking about one task in order to fully transition their attention and perform well on another. Yet, results indicate it is difficult for people to transition their attention away from an unfinished task and their subsequent task performance suffers. Being able to finish one task before switching to another is, however, not enough to enable effective task transitions. Time pressure while finishing a prior task is needed to disengage from the first task and thus move to the next task and it contributes to higher performance on the next task.

- 실험 2건이다.
- 미완료 과제에서 떠날 때 다음 과제 수행이 떨어지고, 과제를 끝내는 것만으로는 부족하며 이전 과제의 시간 압박이 이탈을 돕는다는 것이 요지다.
- 표본 크기와 효과 크기는 본문을 열지 못해 확인하지 못했다(원문 미확인).
- 2차 사이트에서 돌아다니는 "인지 성능 40% 저하" 같은 수치는 이 논문 초록에 없고, 출처를 찾지 못했다.

#### 2.2 Leroy & Glomb (2018) — "ready-to-resume" 계획

- 출처: Leroy, S., & Glomb, T. M. (2018). Tasks interrupted: How anticipating time pressure on resumption of an interrupted task causes attention residue and low performance on interrupting tasks and how a "ready-to-resume" plan mitigates the effects. *Organization Science*. DOI 10.1287/orsc.2017.1184 (Crossref 초록 원문 확인)

> we predict that when people anticipate resuming their interrupted work under time pressure, they will find it difficult to switch their attention to the interrupting task, leading to attention residue and low performance. A ready-to-resume intervention, in which one briefly reflects on and plans one's return to the interrupted task, mitigates this effect such that attention residue is reduced and performance on the interrupting task does not suffer. Data collected across four studies support these hypotheses.

- 2009 논문이 *이전 과제의 잔여가 다음 과제를 해친다*였다면, 2018 논문은 *중단된 과제로 돌아갈 일을 예상하는 것*이 중단 과제(새 과제)의 수행을 해친다는 방향이다.
- 연구 4건이다.

---

### 3. 중단(interruption)과 재개 비용

#### 3.1 "23분 15초"의 실제 출처와 의미

- 출처 A(수치 자체): Gallup Business Journal, "Too Many Interruptions at Work?" (Jennifer Robison의 Gloria Mark 인터뷰, 2006-06-08). https://news.gallup.com/businessjournal/23146/too-many-interruptions-work.aspx (원문 확인. 아래는 페이지에서 그대로 옮긴 구절)

> most interrupted work was resumed on the same day -- 81.9 percent -- and it was resumed, on average, in 23 minutes and 15 seconds.

> There are about two intervening tasks before you go back to your original task

- 같은 인터뷰에서 표본을 "shadowed 36 managers, financial analysts, software developers, engineers, and project leaders for three days"라고 설명한다.
- 즉 23분 15초는 **동료평가 논문의 수치가 아니라 인터뷰에서 말한 수치**다.
- 의미는 "같은 날 재개된 중단 작업에 한해, 중단 시점부터 그 작업으로 돌아오기까지의 평균 경과 시간"이다.
- 그 사이에 평균 두 개 정도의 다른 작업을 거친다.
- 따라서 "집중력을 회복하는 데 23분이 걸린다"(인지적 재몰입 시간)로 흔히 옮겨지는 해석은 원래 의미와 다르다.
- 원래 수치는 **다른 일을 하다가 원래 일로 돌아오기까지의 시간**이다.

- 출처 B(가장 가까운 동료평가 논문): Mark, G., González, V. M., & Harris, J. (2005). No task left behind? Examining the nature of fragmented work. *CHI 2005*, 321–330. DOI 10.1145/1054972.1055017. PDF: https://www.interruptions.net/literature/Mark-CHI05-p321-mark.pdf (원문 확인)

> We present data from detailed observation of 24 information workers that shows that they experience work fragmentation as common practice. [...] people average little time in working spheres before switching and 57% of their working spheres are interrupted. [...] Though most interrupted work is resumed on the same day, more than two intervening activities occur before it is.

> When people did resume work on the same day, it took an average length of time of 25 min. 26 sec (sd=54 min. 48 sec.). [...] before resuming work, our informants worked in an average of 2.26 (sd=2.79) working spheres.

> 77.2% of interrupted work was resumed on the same day.

- 논문 수치는 25분 26초(표준편차 54분 48초), 같은 날 재개율 77.2%, 표본 24명이다.
- 인터뷰 수치는 23분 15초, 81.9%, 36명이어서 둘이 일치하지 않는다.
- 23분 15초에 정확히 대응하는 논문은 찾지 못했다(원문 미확인).
- 표준편차가 평균의 두 배를 넘으므로 분포가 크게 치우쳐 있다.
- 한 working sphere에 머무는 평균 시간은 "11 min. 4 sec., (sd=18 min. 9 sec.)"였다.
- 외부 중단 쪽이 더 빨리 재개되었다.

> Externally interrupted working spheres are resumed on the average in a shorter time (22 min. 37 sec., sd=53 min. 52 sec.) than internally interrupted working spheres, (29 min. 1 sec., sd=55 min. 43 sec.), t(987)=1.92, p<.055.

- 한계: 관찰(셰도잉) 연구이고, 한 회사 IT 서비스 조직의 24명이다.
- 측정 대상은 경과 시간이고 인지 비용이 아니다.

#### 3.2 Mark, Gudith & Klocke (2008) — 중단되면 더 빨리, 더 스트레스 받으며 일한다

- 출처: Mark, G., Gudith, D., & Klocke, U. (2008). The cost of interrupted work: more speed and stress. *CHI 2008*, 107–110. DOI 10.1145/1357054.1357072. PDF: https://www.interruptions.net/literature/Mark-CHI08.pdf (원문 확인)

> We found that context does not make a difference but surprisingly, people completed interrupted tasks in less time with no difference in quality. Our data suggests that people compensate for interruptions by working faster, but this comes at a price: experiencing more stress, higher frustration, time pressure and effort.

- 설계: 피험자 48명(81%가 독일 대학생, 평균 26세)의 피험자 내 설계다.
- 조건은 이메일 응답 과제에서 중단 없음 / 같은 맥락 중단 / 다른 맥락 중단이고, 중단은 2분 간격이었다.
- 과제 시간(중단 처리 시간 제외)은 기준 22.77분, 같은 맥락 20.31분, 다른 맥락 20.60분이었다.
- 오류 수와 공손성에는 차이가 없었고, 이메일 길이는 기준 조건이 가장 길었다.
- NASA-TLX(1–20) 스트레스는 기준 6.92, 같은 맥락 9.46, 다른 맥락 9.13이었다(p<.001).
- 좌절·시간 압박·노력도 중단 조건에서 높았다.

> After only 20 minutes of interrupted performance people reported significantly higher stress, frustration, workload, effort, and pressure. We cannot say whether people would cope over time or if these measures would only increase.

- 한계: 약 20분 단위 블록의 실험실 과제다.
- 스트레스는 자기보고이고, 장기 효과는 측정하지 않았다(저자 명시).

#### 3.3 Czerwinski, Horvitz & Wilhite (2004) — 일지 연구, 그리고 흔한 오인용

- 출처: Czerwinski, M., Horvitz, E., & Wilhite, S. (2004). A diary study of task switching and interruptions. *CHI 2004*, 175–182. DOI 10.1145/985692.985715. PDF: https://www.interruptions.net/literature/Czerwinski-CHI04-p175-czerwinski.pdf (원문 확인)
- 표본: "Eleven experienced Microsoft Windows™ users (3 female)", 1주간의 일지 연구다.

> Tasks that required "returning to" after an interruption were rated significantly more difficult to switch to than others, F(1,497)= 8.453, p<.001

> The returned-to tasks were over twice as long as those tasks described as more routine, shorter-term projects (average task length = 120 minutes v. 45 minutes, respectively)

- "두 배"는 **되돌아가야 했던 과제가 원래 더 긴 과제였다**(평균 120분 대 45분)는 기술 통계다.
- 이는 중단 때문에 과제가 두 배 오래 걸렸다는 인과 측정이 아니다.
- 그런데 Parnin & Rugaber(2009, §6.4) 서론은 이 논문을 다음과 같이 인용한다.

> Czerwinski's study [7] showed that tasks resumed after an interruption were more difficult to perform and took twice as long.

- 원 논문의 서술(과제 길이의 차이)과 인용문의 서술(중단으로 인한 소요 시간 증가)은 서로 다르다.

#### 3.4 Iqbal & Horvitz (2007) — 알림 이후 복귀

- 출처: Iqbal, S. T., & Horvitz, E. (2007). Disruption and recovery of computing tasks: Field study, analysis, and directions. *CHI 2007*, 677–686. DOI 10.1145/1240624.1240730. PDF: https://www.erichorvitz.com/CHI_2007_Iqbal_Horvitz.pdf (원문 확인)
- 표본: Microsoft 직원 27명의 PC에 로깅 도구를 설치한 현장 연구다.

> For email, the average time to return to any suspended application (time spent on the diversion) was 9 minutes and 33 seconds (S.D.=13m, 15s). For IM, the return time was 8 minutes (S.D.=11m, 32s) on average. We note that return times refer to the time until accessing the application associated with the primary task, not resumption of a suspended task.

> On average, 27% of the alerts resulted in users being diverted from these prior active windows for more than 2 hours into the resumption phase.

- 사람들은 알림에 응답하기 전에 하던 일을 마무리하는 경향을 보였다(§7 반대 증거에서 다시 인용).

#### 3.5 수 초짜리 중단의 효과 — Altmann, Trafton & Hambrick (2014), Monk et al. (2008)

- 출처: Altmann, E. M., Trafton, J. G., & Hambrick, D. Z. (2014). Momentary interruptions can derail the train of thought. *Journal of Experimental Psychology: General*, 143(1), 215–226. DOI 10.1037/a0030986 (PubMed 초록 원문 확인)

> Interruptions averaging 4.4 s long tripled the rate of sequence errors on post-interruption trials relative to baseline trials. Interruptions averaging 2.8 s long--about the time to perform a step in the interrupted task--doubled the rate of sequence errors. Nonsequence errors showed no interruption effects, suggesting that global attentional processes were not disrupted.

- 출처: Monk, C. A., Trafton, J. G., & Boehm-Davis, D. A. (2008). The effect of interruption duration and demand on resuming suspended goals. *Journal of Experimental Psychology: Applied*, 14(4), 299–313. DOI 10.1037/a0014402 (PubMed 초록 원문 확인)

> Three experiments using an interleaved tasks interruption paradigm showed that longer and more demanding interruptions led to longer resumption times in a hierarchical, interactive task.

- 이론적 배경은 Altmann & Trafton(2002) "Memory for goals" 모델이다(*Cognitive Science*, 26(1), DOI 10.1207/s15516709cog2601_2, Crossref 초록 원문 확인).
- 이 모델은 보류된 목표가 활성화 감쇠로 잊히고 단서(cue)로 다시 인출된다고 본다.

> The model embodies three predictive constraints: (1) the interference level, which arises from residual memory for old goals; (1) the strengthening constraint, which makes predictions about time to encode a new goal; and (3) the priming constraint, which makes predictions about the role of cues in retrieving pending goals.

(인용문의 번호 "(1)"이 두 번 나오는 것은 원문 그대로다.)

- 한계: 모두 실험실 절차 과제다.
- 효과는 "순서상 위치 잃기" 오류에 특정되고, 전반적 주의 저하는 관찰되지 않았다(Altmann 2014).

#### 3.6 화면 집중 지속 시간 "47초" — Mark et al. (2016)

- 출처: Mark, G., Iqbal, S. T., Czerwinski, M., Johns, P., & Sano, A. (2016). Neurotics can't focus: An in situ study of online multitasking in the workplace. *CHI 2016*. DOI 10.1145/2858036.2858202. PDF: https://ics.uci.edu/~gmark/Home_page/Publications_files/CHI%2016%20Multitasking%20and%20Focus.pdf (원문 확인)

> Forty information workers' online activity was tracked over two work weeks. The median duration of online screen focus was 40 seconds. [...] Shorter focus duration was associated with lower assessed productivity at day's end.

- 표 1에 따르면 전체 컴퓨터 사용에서 화면 하나에 머문 시간은 평균 47.0초(sd 21.4), 중앙값 40.2초다.
- "47초"는 **한 화면(창·사이트)에 머문 시간**의 평균이다.
- 이는 "인간의 주의 지속 능력"의 측정치가 아니다.
- 2004년 "2분 30초", 2012년 "75초"라는 비교 수치는 Mark의 인터뷰·저서 홍보 기사에서 나온다(2차 출처, 원 논문 미확인).

#### 3.7 이메일 차단 실험 — Mark, Voida & Cardello (2012)

- 출처: Mark, G., Voida, S., & Cardello, A. (2012). "A pace not dictated by electrons": An empirical study of work without email. *CHI 2012*. DOI 10.1145/2207676.2207754. PDF: https://onlabor.org/wp-content/uploads/2017/03/CHI202012.pdf (원문 확인)

> We report on an empirical study where we cut off email usage for five workdays for 13 information workers in an organization. [...] without email, people multitasked less and had a longer task focus, as measured by a lower frequency of shifting between windows and a longer duration of time spent working in each computer window. Further, we directly measured stress using wearable heart rate monitors and found that stress, as measured by heart rate variability, was lower without email.

- 한계: 13명, 5일, 무작위 대조군이 없는 전후 비교다.

---

### 4. 미디어 멀티태스킹

#### 4.1 Ophir, Nass & Wagner (2009)

- 출처: Ophir, E., Nass, C., & Wagner, A. D. (2009). Cognitive control in media multitaskers. *PNAS*, 106(37), 15583–15587. DOI 10.1073/pnas.0903620106. PMC2747164 (초록·본문 원문 확인)

> Results showed that heavy media multitaskers are more susceptible to interference from irrelevant environmental stimuli and from irrelevant representations in memory. This led to the surprising result that heavy media multitaskers performed worse on a test of task-switching ability, likely due to reduced ability to filter out interference from the irrelevant task set.

- 표본: 설문(Media Multitasking Index)으로 평균 ±1 SD 밖의 극단 집단만 선발했다.

> The invitation yielded 22 LMMs and 19 HMMs who gave informed consent and participated in the study for course credit.

- 효과: "HMMs' switch cost was 167 ms greater than that of LMMs, t (28) = −2.62, P < 0.01"였다.
- 한계: 횡단적 집단 비교(상관)이고, 극단 집단 선발에 집단당 20명 내외다.
- 이 연구는 "멀티태스킹을 하면 능력이 떨어진다"는 인과가 아니라 "많이 하는 사람이 특정 과제에서 다르다"는 연관만 보인다.

#### 4.2 재현 실패와 메타분석

- 출처: Wiradhany, W., & Nieuwenstein, M. R. (2017). Cognitive control in media multitaskers: Two replication studies and a meta-analysis. *Attention, Perception, & Psychophysics*, 79(8), 2620–2641. DOI 10.3758/s13414-017-1408-4 (PubMed 초록 원문 확인)

> Our replication studies included a total of 14 tests that had an average replication power of 0.81. Of these 14 tests, only five yielded a statistically significant effect in the direction of increased distractibility for people with higher scores on the media-use questionnaire, and only two of these effects held in a more conservative Bayesian analysis. Supplementing these outcomes, our meta-analysis on a total of 39 effect sizes yielded a weak but significant association between media multitasking and distractibility that turned nonsignificant after correction for small-study effects.

- 출처: Parry, D. A., & le Roux, D. B. (2021). "Cognitive control in media multitaskers" ten years on: A meta-analysis. *Cyberpsychology*, 15(2), Article 7. DOI 10.5817/CP2021-2-7. PDF: https://cyberpsychology.eu/article/download/13303/32657 (원문 확인)

> Following a systematic search and selection process, 118 assessments were included in the meta-analysis. Overall, the pooled effect size of the association, across measurement approaches and cognitive control functions, is small. [...] Overall, the review suggests that, ten years on, we are no closer to understanding 'cognitive control in media multitaskers.'

> For performance-based assays the effect size is negligible but statistically significant (z = .091, 95% CI [.044, .139], p = .001) [...] In this sensitivity analysis, the pooled effect for performance-based assays was no longer statistically significant (z = .032, 95% CI [-.024, .088], p = .260).

- 전체 풀링 효과는 z = .192이고, 자기보고 측정은 z = .200, 수행 기반 측정은 z = .091이며 출판편향 보정 후에는 유의하지 않다.
- 2023년 *Educational Psychology Review*의 3수준 메타분석이 "moderate" 음의 연관을 보고했다는 검색 요약이 있으나 원문은 열지 않았다(원문 미확인, DOI 10.1007/s10648-023-09746-0).

#### 4.3 리뷰와 후속 연구

- 출처: Uncapher, M. R., & Wagner, A. D. (2018). Minds and brains of media multitaskers: Current findings and future directions. *PNAS*, 115(40), 9889–9896. DOI 10.1073/pnas.1611612115 (PubMed 초록 원문 확인). Ophir 2009의 공저자(Wagner)가 쓴 리뷰다.

> While the literature is still sparse, and is marked by both convergent and divergent findings, the balance of evidence suggests that heavier media multitaskers exhibit poorer performance in a number of cognitive domains, relative to lighter media multitaskers (although many studies find no performance differences between groups). [...] further research is needed [...] to determine the direction of causality

- 출처: Madore, K. P., et al. (2020). Memory failure predicted by attention lapsing and media multitasking. *Nature*, 587, 87–91. DOI 10.1038/s41586-020-2870-z (PubMed 초록 원문 확인)

> Electroencephalography and pupillometry measures of attention were recorded as eighty young adults (mean age, 21.7 years) performed a goal-directed episodic encoding and retrieval task. [...] Heavier media multitasking is associated with a propensity to have attention lapses and forget.

- 출처: Sanbonmatsu, D. M., Strayer, D. L., Medeiros-Ward, N., & Watson, J. M. (2013). Who multi-tasks and why? *PLoS ONE*, 8(1), e54402. DOI 10.1371/journal.pone.0054402 (PubMed 초록 원문 확인). 인과 방향의 반대 가능성(자기 선택)을 보여 준다.

> The findings indicate that the persons who are most capable of multi-tasking effectively are not the persons who are most likely to engage in multiple tasks simultaneously. To the contrary, multi-tasking activity as measured by the Media Multitasking Inventory and self-reported cell phone usage while driving were negatively correlated with actual multi-tasking ability. Multi-tasking was positively correlated with participants' perceived ability to multi-task ability which was found to be significantly inflated.

---

### 5. "뇌 건강" 주장

#### 5.1 회백질 밀도 — Loh & Kanai (2014)

- 출처: Loh, K. K., & Kanai, R. (2014). Higher media multi-tasking activity is associated with smaller gray-matter density in the anterior cingulate cortex. *PLoS ONE*, 9(9), e106698. DOI 10.1371/journal.pone.0106698. PMC4174517 (원문 확인)
- 표본: "75 healthy adults (mean age = 24.6, SD = 5.0, 38 males)"이고, fMRI 연결성 분석은 그중 40명이다.

> Individuals with higher Media Multitasking Index (MMI) scores had smaller gray matter density in the anterior cingulate cortex (ACC).

> Although it is conceivable that individuals with smaller ACC are more susceptible to multitasking due to weaker ability in cognitive control or socio-emotional regulation, it is equally plausible that higher levels of exposure to multitasking situations lead to structural changes in the ACC. A longitudinal study is required to unambiguously determine the direction of causation.

- 저자 스스로 인과 방향을 알 수 없다고 명시한다.
- 대중 기사에서 흔히 쓰이는 "멀티태스킹이 뇌를 손상시킨다/뇌를 줄인다"는 표현은 이 연구의 설계(단면 상관, 자기보고 MMI)가 뒷받침하는 범위를 넘는다.
- 종단 연구로 재현되었는지는 확인하지 못했다(원문 미확인).

#### 5.2 "이메일·문자로 IQ 10점 하락" — Glenn Wilson / HP (2005)

- 출처: Glenn Wilson, "THE 'INFOMANIA' STUDY" (저자 본인의 해명 노트, 2010-01-16). https://litfl.com/wp-content/uploads/2020/12/Infomania_experiment_for_HP.pdf (현행 URL은 차단. Wayback 사본으로 원문 확인)

> In 2005 I was commissioned by Porter-Novelli, the London publicists of Hewlett-Packard, to supervise a small in-house experiment on the negative effects of "always-on" technology, dubbed "infomania".

> Eight Porter Novelli employees (4 male and 4 female) were tested twice – once in quiet conditions and once in distracting conditions (mobile phones ringing and e-mails arriving).

> Results showed clearly that technological distraction diminished IQ test performance (mean scores dropped from 143.38 achieved under quiet conditions to 132.75 under "noisy" conditions).

> This study was widely misrepresented in the media, with the number of participants for the two aspects of the report being confused and the impression given that it was a published report (the only publication was a press release from Porter-Novelli). Comparisons were made with the effects of marijuana and sleep loss based on previously published studies not conducted by me. The legitimacy of these comparisons is doubtful because the infomania effect is almost certainly one of temporary distraction, whereas sleep loss and marijuana effects on IQ might conceivably be more fundamental, even permanent.

- 실체: 표본 8명, PR 회사 직원, 동료평가 논문 없음(보도자료만 존재), 측정 대상은 **방해 상황에서의 일시적 수행 저하**다.
- "10점"은 143.38 → 132.75의 차이다.
- 함께 보도된 "1000명 대상" 수치는 같은 캠페인의 TNS 여론조사이고, 실험 표본이 아니다.
- "마리화나보다 해롭다" 비교는 저자가 하지 않았고, 저자 스스로 그 정당성을 의심한다.
- 이 수치를 "멀티태스킹이 IQ를 영구히 떨어뜨린다"는 근거로 쓰는 것은 저자 본인의 해명과 어긋나는 오인용이다.

#### 5.3 스트레스·코르티솔·작업기억

- 멀티태스킹 자체가 코르티솔(HPA 축)을 올린다는 직접 증거는 확인되지 않았다.
  - 출처: Becker, L., Kaltenegger, H. C., Nowak, D., Weigl, M., & Rohleder, N. (2023). Biological stress responses to multitasking and work interruptions: A randomized controlled trial. *Psychoneuroendocrinology*, 156, 106358. DOI 10.1016/j.psyneuen.2023.106358 (PubMed 초록 원문 확인)

> N = 186 healthy participants [...] took part in this pre-registered study. [...] Salivary alpha-amylase (sAA) levels as a marker for SNS reactivity significantly changed in work interruptions, parallel dual-tasking, and multitasking conditions. [...] no significant changes over time and no differences between the conditions were identified for three biological markers: cortisol as marker for HPA axis activity as well as for two immune system markers [...] Overall, our findings show that dual- and multitasking are perceived as stressful and are associated with an activation of the SNS, but not with responses of HPA axis or immune system.

- 급성 생리 반응(심박·혈압)은 관찰된다.
  - 출처: Wetherell, M. A., & Carter, K. (2014). The multitasking framework: the effects of increasing workload on acute psychobiological stress reactivity. *Stress and Health*, 30(2), 103–109. DOI 10.1002/smi.2496 (PubMed 초록 원문 확인)

> Psychological (mood and perceived workload) and physiological (heart rate and blood pressure) stress reactivity was observed in response to a 15-min period of multitasking at different levels of workload intensity in a sample of 20 healthy participants. Multitasking stress elicited increases in heart rate and blood pressure, and increased workload intensity elicited dose-response increases in levels of perceived workload and mood.

- 반대 방향(스트레스가 전환 능력을 해친다)의 증거가 있다.
  - 출처: Plessow, F., Kiesel, A., & Kirschbaum, C. (2012). The stressed prefrontal cortex and goal-directed behaviour. *Experimental Brain Research*, 216(3), 397–408. DOI 10.1007/s00221-011-2943-1 (PubMed 초록 원문 확인)

> forty-eight healthy volunteers were either challenged with a standardised stress-induction protocol (the Trier Social Stress Test) or underwent a standardised control situation. [...] At the time interval of elevated cortisol levels, stressed individuals persistently showed larger performance differences between task switches and task repetitions (switch costs) than controls.

- 스트레스와 전전두엽의 관계(멀티태스킹 특정 연구가 아님):
  - 출처: Arnsten, A. F. T. (2009). Stress signalling pathways that impair prefrontal cortex structure and function. *Nature Reviews Neuroscience*, 10(6), 410–422. DOI 10.1038/nrn2648 (PubMed 초록 원문 확인)

> Even quite mild acute uncontrollable stress can cause a rapid and dramatic loss of prefrontal cognitive abilities, and more prolonged stress exposure causes architectural changes in prefrontal dendrites.

  - 이 리뷰의 근거는 주로 동물 연구다(초록 수준에서 확인. 본문 비율은 원문 미확인).
  - 멀티태스킹이 그런 "만성 스트레스"에 해당하는지를 연결한 연구는 이번 조사에서 찾지 못했다.

- 정신건강과의 상관:
  - 출처: Becker, M. W., Alzahabi, R., & Hopwood, C. J. (2013). Media multitasking is associated with symptoms of depression and social anxiety. *Cyberpsychology, Behavior, and Social Networking*, 16(2), 132–135. DOI 10.1089/cyber.2012.0291 (PubMed 초록 원문 확인)

> Participants (N=318) completed measures of their media use, personality characteristics, depression, and social anxiety. Regression analyses revealed that increased media multitasking was associated with higher depression and social anxiety symptoms, even after controlling for overall media use and the personality traits of neuroticism and extraversion.

  - 한계: 횡단 설문 상관 연구다.

---

### 6. 병렬 프로젝트 수와 생산성 (소프트웨어 개발)

#### 6.1 Weinberg의 context switching 표

- 원전: Weinberg, G. M. *Quality Software Management, Vol. 1: Systems Thinking* (1991/1992). 원서를 열지 못했다(**원문 미확인**).
- 2차 출처들이 전하는 표의 수치는 서로 다르다.
  - 널리 퍼진 판본은 "프로젝트 2개 → 각 40%, 전환 손실 20% / 3개 → 각 20%, 손실 40% / 4개 → 각 10%, 손실 60% / 5개 → 각 5%, 손실 75%"이다(검색 결과 요약, 2차 출처).
  - https://agilecoachingcards.pages.dev/toolkit/project-switching/ 는 "2개 ~20%, 3개 ~25%, 4개 ~40%, 5개 ~65%" 손실로 다르게 적는다(2차 출처, WebFetch 요약).
- 성격: 2차 출처들은 이 표를 컨설팅 경험에서 나온 휴리스틱(rule of thumb)으로 소개한다.
- 통제된 측정이라는 기록은 찾지 못했다.
- 실증 검증 시도(§6.2)는 이 휴리스틱이 과대 추정이라고 보고했다.

#### 6.2 Tregubov et al. (2017) — Weinberg 휴리스틱의 실증 점검

- 출처: Tregubov, A., Boehm, B., Rodchenko, N., & Lane, J. A. (2017). Impact of task switching and work interruptions on software development processes. *ICSSP 2017*, 134–138. DOI 10.1145/3084100.3084116 (초록은 neverworkintheory.org 리뷰 페이지에 전재된 것으로 확인: https://neverworkintheory.org/2021/09/19/impact-of-task-switching-and-work-interruptions.html. ACM 본문은 미확인)

> In this research we study cross-project multitasking among the developers working on multiple projects in an educational setting. We propose a way to evaluate the number of cross-project interruptions among software developers using self-reported work logs. This paper describes the research that found: a) software developers involved in two or more projects on average spend 17% of their development effort on cross-project interruptions, b) the amount of effort spent on interruptions is overestimated by the G. Weinberg's heuristic, c) the correlation between the number of projects and effort spent by developers on cross-project interruptions is relatively weak, and d) there is strong correlation between the number of projects and the number of interruptions developers reported.

- 한계: 교육 환경(학생 팀 프로젝트)이고 자기보고 작업 로그다.

#### 6.3 GitHub·산업 저장소의 멀티프로젝트 생산성

- 출처: Vasilescu, B., et al. (2016). The sky is not the limit: Multitasking across GitHub projects. *ICSE 2016*, 994–1005. PDF: https://www.cs.ucdavis.edu/~filkov/papers/icse2016focus.pdf (원문 확인)

> Developers who work on many projects have higher productivity if they focus on few projects per day. Developers that switch projects too much during the course of a day have lower productivity as they work on more projects overall. Despite these findings, developers perceptions of the benefits of multitasking are varied.

> • Within limits, multitasking is associated with higher productivity, but developers' perception is mixed.
> • Productivity does not decrease so long as developers work on 4 or fewer projects per week.

  - 표본: 1,255명 개발자의 커밋 데이터와 128명 설문이다.
  - 한계: 관찰 데이터이고, 생산성은 커밋 산출량 기반이다(품질은 미측정).
  - 측정 정의의 세부는 본문에서 별도로 확인하지 않았다.
- 출처: Kohl, K., Vasilescu, B., & Prikladnicki, R. (2020). Multitasking across industry projects: A replication study. arXiv:2006.12636 (원문 확인)

> We found out that industry developers multitask as much as OSS developers focusing more (on fewer projects), and working more repetitively from one day to the next is associated with higher productivity, but there is no effect for higher multitasking. [...] Short context change, less than three minutes, did not impact results from industry developers; however, more than that, it brings a feeling of left the previous tasks behind.

#### 6.4 프로그래밍 작업 재개 — Parnin & Rugaber

- 출처: Parnin, C., & Rugaber, S. (2009/2011). Resumption strategies for interrupted programming tasks. ICPC 2009, 확장판은 *Software Quality Journal* 19(1), 2011. PDF(ICPC판): https://sites.cc.gatech.edu/reverse/repository/resumptionstrategies.pdf (원문 확인)

> we perform exploratory analysis on 10,000 recorded programming sessions of 85 programmers to understand the variety of strategies used by programmers for resuming programming tasks. In our study, we find that only 10% of the programming sessions have coding activity start in less than a minute, only 7% of the programming sessions involve no navigation to other locations prior to editing

- 같은 논문 서론은 산업 현장 연구(Solingen)를 다음과 같이 인용한다.

> Solingen [36] characterizes interruptions at several industrial software companies and observed that an hour a day was spent managing interruptions, and developers typically required 15 minutes to recover from an interruption.

  - Solingen 원 논문은 열지 않았다(원문 미확인, 재인용).
- 같은 서론의 Czerwinski 인용("took twice as long")은 원 논문 서술과 다르다(§3.3).

#### 6.5 WIP(진행 중 작업) 제한의 실증

- 출처: Sjøberg, D. I. K. (2018). An empirical study of WIP in kanban teams. *ESEM 2018*. DOI 10.1145/3239235.3239238 (Semantic Scholar 초록 원문 확인)

> Limiting the amount of Work-In-Progress (WIP) is considered a fundamental principle in Kanban software development. However, no published studies from real cases exist that indicate what an optimal WIP limit should be. [...] A quantitative case study was conducted in a software company that provided information about more than 8,000 work items developed over four years by five teams. [...] WIP correlates with lead time; that is, lower WIP indicates shorter lead times, which is consistent with claims in the literature. However, WIP also correlates with productivity, which is inconsistent with the claim in the literature that a low WIP (still above a certain threshold) will improve productivity.

- 팀 단위 흐름 지표(리드타임)와 개인 인지 비용은 서로 다른 층위의 측정이다.
- 이 연구는 개인의 전환 비용을 측정하지 않았다.

---

### 7. 반대 증거와 조건 — 멀티태스킹이 해롭지 않거나 유리한 경우

#### 7.1 연습된 단순 과제의 동시 수행

- 출처: Schumacher, E. H., et al. (2001). Virtually perfect time sharing in dual-task performance: Uncorking the central cognitive bottleneck. *Psychological Science*, 12(2), 101–108. DOI 10.1111/1467-9280.00318 (PubMed 초록 원문 확인). 공저자에 Meyer(§1.1)가 있다.

> Their results show that after relatively modest amounts of practice, at least some participants achieve virtually perfect time sharing in the dual-task performance of basic choice reaction tasks. The results also show that observed interference between tasks can be modulated by instructions about differential task priorities and personal preferences for daring (concurrent) or cautious (successive) scheduling of tasks.

#### 7.2 Supertasker

- 출처: Watson, J. M., & Strayer, D. L. (2010). Supertaskers: Profiles in extraordinary multitasking ability. *Psychonomic Bulletin & Review*, 17(4), 479–485. DOI 10.3758/PBR.17.4.479 (PubMed 초록 원문 확인)

> We tested 200 participants in a high-fidelity driving simulator in both single- and dual-task conditions. [...] Whereas the vast majority of participants showed significant performance decrements in dual-task conditions [...], 2.5% of the sample showed absolutely no performance decrements with respect to performing single and dual tasks.

- 후속 연구 Medeiros-Ward, Watson & Strayer(2015, *Psychon Bull Rev* 22(3), DOI 10.3758/s13423-014-0713-3, PubMed 초록 확인)는 supertasker의 전전두 영역 동원이 "more efficient"하다고 보고했다.
- 2012년 게이머 대상 연구(60명)에서 supertasker 기준을 충족한 사람이 없었다는 검색 요약이 있으나 원문은 열지 않았다(원문 미확인).
- 같은 연구 그룹의 운전 연구는 대다수에게 비용이 있음을 보인다.
  - 출처: Strayer, Drews & Johnston (2003), *J Exp Psychol Appl* 9(1), DOI 10.1037/1076-898x.9.1.23. 핸즈프리 통화가 전방 차량 제동 반응과 시각 정보 기억을 손상시켰다(PubMed 초록 확인).

#### 7.3 자발적 인터리빙과 완결 지점에서의 전환

- 출처: Payne, S. J., Duggan, G. B., & Neth, H. (2007). Discretionary task interleaving: Heuristics for time allocation in cognitive foraging. *Journal of Experimental Psychology: General*, 136(3), 370–388. DOI 10.1037/0096-3445.136.3.370 (PubMed 초록 원문 확인)

> When participants allocated time across 2 tasks [...], they made frequent switches. This allowed them to allocate more time to the more productive task [...] there was a tendency to switch tasks after subgoal completion.

- 출처: Iqbal & Horvitz (2007, §3.4)는 사람들이 알림에 응답하기 전에 하던 단위를 마무리한다고 보고했다.

> users completed paragraphs at a rate of 0.78/min (S.D.=0.49) during the pre-interruption phase. On receiving an IM alert, the paragraph completion rate was 10.9/min (S.D.=5.2) during the preparation phase if the response was immediate. [...] These results suggest that users typically prefer to complete conceptual and/or motor subtasks before switching

- 출처: Adamczyk, P. D., & Bailey, B. P. (2004). If not now, when? The effects of interruption at different moments within task execution. *CHI 2004*, 271–278. DOI 10.1145/985692.985727. PDF: https://hci.rwth-aachen.de/materials/conferences/CHI2004/1p271.pdf (원문 확인)

> Our results show that our predicted best points for interruption consistently produced less annoyance, frustration, and time pressure, required less mental effort, and were deemed by the user more respectful of the their primary task. In terms of annoyance, the best moment for interruption showed a 56% reduction from the worst condition, and was 43% lower than the random condition.

  - "best points"는 과제 구조상의 굵은 단위 경계(coarse breakpoint)다.
- 자발적 전환과 외부 중단의 비교:
  - Mark et al.(2005)에서는 외부 중단 쪽이 더 빨리 재개되었다(22분 37초 대 29분 1초, p<.055, §3.1).
  - Czerwinski et al.(2004)는 표본에서 "users chose when to switch tasks or worked off a to-do list a majority of the time"이라고 적는다.
  - Arrington & Logan(2004)은 자발적 전환에도 비용이 있음을 보였다(§1.4).

#### 7.4 수행 지표에 따라 결과가 달라진다

- 출처: Adler, R. F., & Benbunan-Fich, R. (2012). Juggling on a high wire: Multitasking effects on performance. *International Journal of Human-Computer Studies*, 70(2), 156–168. PDF: https://www.interruptions.net/literature/Adler-IntJHumComputStud12.pdf (원문 확인)

> Our results show an inverted-U pattern for performance efficiency (productivity) and a decreasing line for performance effectiveness (accuracy). [...] If performance is measured with productivity, different multitasking levels are associated with an inverted-U curve where medium multitaskers perform significantly better than both high and low multitaskers. However, if performance is measured with accuracy of results, the relation is a downward slopping line, in which increased levels of multitasking lead to a significant loss in accuracy.

- 다른 조건부 결과들:
  - Mark et al.(2008): 중단 조건에서 오히려 더 빨리 끝냈고 품질 차이가 없었으나, 스트레스는 올랐다(§3.2).
  - Vasilescu et al.(2016): "Within limits, multitasking is associated with higher productivity"였다(§6.3).
  - Sjøberg(2018): WIP와 생산성이 양의 상관이었다(§6.5).
  - Kohl et al.(2020): 3분 미만의 짧은 맥락 변경은 영향이 없었다(§6.3).
  - Leroy(2009): 이전 과제에 시간 압박이 있으면 이탈이 쉬워졌다(§2.1).

---

### 8. 감독·모니터링 작업의 인지 부하

#### 8.1 경계 감소 (vigilance decrement)

- 원전은 Mackworth, N. H. (1948). The breakdown of vigilance during prolonged visual search. *Quarterly Journal of Experimental Psychology*, 1(1). DOI 10.1080/17470214808416738이다.
- 원문은 열지 않았다(원문 미확인). 아래는 이를 인용한 1차 문헌들이다.
- 출처: Bainbridge, L. (1983). Ironies of automation. *Automatica*, 19(6), 775–779. DOI 10.1016/0005-1098(83)90046-8. PDF: https://gwern.net/doc/sociology/technology/1983-bainbridge.pdf (원문 확인)

> We know from many 'vigilance" studies (Mackworth, 1950) that it is impossible for even a highly motivated human being to maintain effective visual attention towards a source of information on which very little happens, for more than about half an hour. This means that it is humanly impossible to carry out the basic function of monitoring for unlikely abnormalities

(인용 부호의 불일치와 "Mackworth, 1950" 표기는 원문 그대로다.)

- 출처: Warm, J. S., Parasuraman, R., & Matthews, G. (2008). Vigilance requires hard mental work and is stressful. *Human Factors*, 50(3), 433–441. DOI 10.1518/001872008X312152 (PubMed 초록 원문 확인)

> Vigilance tasks have typically been viewed as undemanding assignments requiring little mental effort. [...] Subjective reports also show that the workload of vigilance is high and sensitive to factors that increase processing demands. [...] physiological and subjective reports confirm that vigilance tasks reduce task engagement and increase distress and that these changes rise with increased task difficulty. [...] This research applies to most human-machine systems that require human monitoring, particularly those involving automated subsystems.

- 출처: Cummings, M. L., Gao, F., & Thornburg, K. M. (2016). Boredom in the workplace: A new look at an old problem. *Human Factors*, 58(2), 279–300. DOI 10.1177/0018720815609503 (PubMed 초록 원문 확인)

> Given the ubiquity of boredom across a wide spectrum of work environments--exacerbated by increasingly automated systems that remove humans from direct, physical system interaction and possibly increasing tedium in the workplace [...] Boredom is closely related to vigilance, attention management, and task performance.

#### 8.2 자동화의 아이러니, out-of-the-loop, 자동화 안주

- Bainbridge(1983)는 자동화가 운영자에게 감시와 이상 시 인수라는 두 일을 남기고, 둘 다 자동화 때문에 더 어려워진다고 논한다(§8.1 동일 출처). 감시 부분의 인용은 위와 같다.

> The human monitor has been given an impossible task.

- 출처: Endsley, M. R., & Kiris, E. O. (1995). The out-of-the-loop performance problem and level of control in automation. *Human Factors*, 37(2), 381–394. DOI 10.1518/001872095779064555 (Crossref 초록 원문 확인)

> The out-of-the-loop performance problem, a major potential consequence of automation, leaves operators of automated systems handicapped in their ability to take over manual operations in the event of automation failure. This is attributed to a possible loss of skills and of situation awareness (SA) arising from vigilance and complacency problems, a shift from active to passive information processing, and change in feedback provided to the operator. [...] Results indicated that the shift from active to passive processing was most likely responsible for decreased SA under automated conditions.

- 출처: Parasuraman, R., & Manzey, D. H. (2010). Complacency and bias in human use of automation: An attentional integration. *Human Factors*, 52(3), 381–410. DOI 10.1177/0018720810376055 (PubMed 초록 원문 확인)

> Automation complacency occurs under conditions of multiple-task load, when manual tasks compete with the automated task for the operator's attention. Automation complacency is found in both naive and expert participants and cannot be overcome with simple practice. Automation bias results in making both omission and commission errors when decision aids are imperfect. Automation bias occurs in both naive and expert participants, cannot be prevented by training or instructions, and can affect decision making in individuals as well as in teams.

#### 8.3 한 사람이 여러 자율 체계를 감독할 때 — operator 대 기체 비율

- 출처: Cummings, M. L., & Guerlain, S. (2007). Developing operator capacity estimates for supervisory control of autonomous vehicles. *Human Factors*, 49(1), 1–15. DOI 10.1518/001872007779598109 (PubMed 초록 원문 확인)

> A dual screen simulation that allows a single operator the ability to monitor and control 8, 12, or 16 missiles through high level replanning was tested on 42 U.S. Navy personnel. RESULTS: The most significant finding was that when attempting to control 16 missiles, participants' performance on three separate objective performance metrics and their situation awareness were significantly degraded. CONCLUSION: These results mirror studies of air traffic control that demonstrate a similar decline in performance for controllers managing 17 aircraft as compared with those managing only 10 to 11 aircraft. Moreover, the results suggest that a 70% utilization (percentage busy time) score is a valid threshold for predicting significant performance decay

- 출처: Cummings, M. L., & Mitchell, P. J. (2008). Predicting controller capacity in supervisory control of multiple UAVs. *IEEE Transactions on Systems, Man, and Cybernetics—Part A*, 38(2), 451–460. DOI 10.1109/TSMCA.2007.914757 (PDF 원문 확인, Wayback 사본)
- fan-out 정의(Olsen 등의 선행 모델 인용): 기체를 방치해도 되는 시간(neglect time, NT)과 상호작용 시간(interaction time, IT)으로 FO = NT/IT + 1이다.

> fan-out (FO) is equal to the number of robots that a human can effectively control, neglect time (NT) is the expected amount of time that a robot can be ignored before its performance drops below some predetermined threshold, and interaction time (IT) is the time it takes for a human to interact with the robot to raise the performance to an acceptable level.

> these sources of vehicle WTs include cognitive reorientation and interaction WT (WTI), queues for multiple-vehicle interactions, and loss of situation awareness (SA) WTs. When WTs were included, predictions using a multiple homogeneous and independent UAV simulation dropped by up to 67%, with a loss of SA as the primary source of WT delays. Moreover, this paper demonstrated that even in a highly automated management-by-exception system, which should alleviate queuing and WTIs, operator capacity is still affected by the SA WT, causing a 36% decrease over the capacity model with no WT included.

  - 실험 표본은 12명(남 10, 여 2)이고, UAV 운용 경험자는 없다.
- 출처: Squire, P. N., & Parasuraman, R. (2010). Effects of automation and task load on task switching during human supervision of multiple semi-autonomous robots in a dynamic environment. *Ergonomics*, 53(8), 951–961. DOI 10.1080/00140139.2010.489969 (PubMed 초록 원문 확인)

> Participants were faster to perform the same task than when they chose to switch between different task actions. They also took longer to switch between different tasks when supervising the robots at a high compared to a low LOA. Task load, as manipulated by the number of robots to be supervised, did not influence switch costs.

- 출처: Chen, J. Y. C., & Barnes, M. J. (2012). Supervisory control of multiple robots: Effects of imperfect automation and individual differences. *Human Factors*, 54(2), 157–174. DOI 10.1177/0018720811435843 (PubMed 초록 원문 확인)
  - 지능형 agent(RoboLeader)가 여러 로봇을 조율하고 인간이 그 권고를 감독하는 설계다.

> RoboLeader, when perfectly reliable, was helpful in reducing the overall mission times. The type of RoboLeader imperfection (false-alarm vs. miss prone) affected operators' performance of tasks involving visual scanning (target detection, route editing, and situation awareness). [...] Participants' attentional control and video gaming experience affected their overall multitasking performance.

---

### 9. 통념과 원 출처 대조표

| 흔한 주장 | 원 출처 | 원 출처가 실제로 말하는 것 | 상태 |
|---|---|---|---|
| "전환하면 생산 시간의 40%를 잃는다" | APA 페이지(2006)의 Meyer 발언 인용 | 실험 측정은 전환당 수백 ms(Rubinstein 2001: 614–975 ms). 40%의 계산 근거는 페이지에 없다 | 실험치의 외삽. 근거 미표기 |
| "중단 후 집중 회복에 23분이 걸린다" | Gallup 인터뷰(2006)의 Mark 발언 | 같은 날 재개된 작업이 돌아오기까지의 평균 경과 시간이고, 그 사이 다른 작업 약 2개를 거친다 | 의미가 변형됨. 논문 수치(Mark 2005)는 25분 26초, sd 54분 48초 |
| "멀티태스킹으로 IQ가 10점 떨어진다(마리화나보다 나쁘다)" | Wilson / HP 보도자료(2005) | 8명, 비출판, 방해 상황에서의 일시적 수행 저하. 저자가 2010년 오보라고 해명했다 | 과장·오인용 |
| "멀티태스킹이 뇌(회백질)를 줄인다" | Loh & Kanai(2014) | 75명 단면 상관. 저자가 인과 방향 불명을 명시했다 | 인과로의 과장 |
| "미디어 멀티태스커는 주의 통제가 나쁘다" | Ophir et al.(2009) | 19 대 22명 극단 집단 비교. 메타분석에서 효과가 작거나 편향 보정 후 사라진다 | 재현 약함 |
| "주의 지속 시간이 47초로 줄었다" | Mark et al.(2016) | 정보 노동자 40명이 화면 하나에 머문 시간의 평균(중앙값 40초) | 측정 대상이 변형됨 |
| "프로젝트 하나 늘 때마다 20%씩 손실" | Weinberg(1991/92) 표 | 경험칙. 2차 출처마다 수치가 다르다. Tregubov(2017)는 과대 추정이라고 보고했다 | 원문 미확인. 실증 아님 |
| "중단되면 일이 두 배 오래 걸린다" | Czerwinski et al.(2004) 재인용 | 되돌아간 과제가 원래 더 긴 과제였다(120분 대 45분)는 기술 통계 | 재인용 과정의 변형 |

---

### 10. 확인하지 못한 것 (원문 미확인)

- Leroy(2009) 본문: 표본 크기, 효과 크기, 측정 방식.
- 23분 15초에 정확히 대응하는 동료평가 논문.
- 2004년 "2분 30초", 2012년 "75초" 화면 집중 수치의 원 논문.
- APA 페이지의 "40%"가 어떤 계산·측정에서 나왔는지.
- Weinberg *Quality Software Management* Vol. 1의 표 원문(쪽수·정확한 수치·저자의 성격 규정).
- Tregubov et al.(2017) ACM 본문(초록은 리뷰 페이지 전재본으로만 확인).
- Solingen et al.의 "하루 1시간, 회복 15분" 원 논문(Parnin & Rugaber의 재인용으로만 확인).
- Mackworth(1948) 원문(Bainbridge 1983·Warm 2008의 인용으로만 확인).
- 2012년 게이머 대상 supertasker 비재현 연구.
- 2023년 *Educational Psychology Review* 3수준 메타분석의 효과 크기.
- Loh & Kanai(2014)의 종단 재현 여부.
- Arnsten(2009) 리뷰 근거 중 인간·동물 연구의 비율.
- Vasilescu et al.(2016)의 생산성 측정 정의 세부.

## 논의 문서로 가져가는 것

- 실험실의 작업 전환 비용은 전환당 수백 ms~1초 규모이고(Rubinstein 2001: 614–975 ms), 준비 시간이 있어도 완전히 사라지지 않는다(Monsell 2003).
- "전환으로 생산 시간의 40% 손실"은 APA 페이지의 Meyer 발언 인용이며, 그 수치의 측정 근거는 페이지에 없다.
- 미완료 과제에서 떠나면 다음 과제 수행이 떨어진다(attention residue, Leroy 2009, 실험 2건).
- 돌아갈 일을 예상하는 것도 지금 과제의 수행을 해치고, 짧은 "ready-to-resume" 계획이 이를 완화한다(Leroy & Glomb 2018, 연구 4건).
- "23분 15초"는 인터뷰 수치이고 "같은 날 재개된 중단 작업으로 돌아오기까지의 경과 시간(사이에 다른 작업 약 2개)"을 뜻한다. 인지적 재몰입 시간이 아니다.
- 동료평가 논문 수치는 25분 26초(sd 54분 48초, 24명)다(Mark 2005).
- 정보 노동자의 working sphere 57%가 중단되고, 한 sphere 체류 평균은 약 11분이다(Mark 2005).
- 2016년 측정에서 한 화면 체류 시간은 평균 47초, 중앙값 40초다(Mark 2016).
- 중단을 받으면 사람들은 더 빨리 일해 시간·품질 손실을 메우지만 스트레스·좌절·시간 압박·노력이 오른다(Mark 2008, 48명, 20분 블록, 자기보고).
- 2.8~4.4초의 짧은 중단도 순서 과제의 위치 오류를 2~3배로 늘린다(Altmann 2014).
- 중단이 길고 부담이 클수록 재개 시간이 길어진다(Monk 2008).
- 알림의 27%는 이전 작업 창에서 2시간 넘게 이탈시켰다(Iqbal & Horvitz 2007, 27명).
- 프로그래밍 세션 중 1분 안에 코딩이 재개된 것은 10%뿐이다(Parnin & Rugaber, 85명·1만 세션).
- 미디어 멀티태스킹과 주의 통제의 연관은 단면 상관이고 효과가 작다.
- 수행 기반 측정의 효과는 출판편향 보정 후 유의하지 않다(Wiradhany 2017, Parry 2021).
- 멀티태스킹을 많이 하는 사람일수록 실제 멀티태스킹 능력은 낮고 자기 평가는 부풀려져 있었다(Sanbonmatsu 2013). 인과 방향이 반대일 가능성이 있다.
- 회백질 밀도 연구(Loh & Kanai 2014)는 75명 단면 상관이고 저자가 인과 방향을 알 수 없다고 명시했다.
- "IQ 10점 하락"은 8명·비출판·일시적 방해 효과이고, 저자 본인이 언론의 오보라고 해명했다.
- 멀티태스킹·중단은 교감신경 반응(sAA, 심박, 혈압)과 주관적 스트레스를 올린다.
- 다만 무작위 대조 시험(186명)에서 코르티솔(HPA 축)과 면역 지표의 변화는 없었다(Becker 2023, Wetherell 2014).
- 스트레스(코르티솔 상승 구간)는 전환 비용을 키운다(Plessow 2012). 방향이 반대인 증거다.
- Weinberg의 프로젝트 수별 손실 표는 경험칙이고, 2차 출처마다 수치가 다르다.
- 학생 개발자 실증에서는 2개 이상 프로젝트 참여 시 노력의 17%가 교차 프로젝트 중단에 쓰였고, Weinberg 휴리스틱은 과대 추정이었다(Tregubov 2017).
- GitHub 개발자는 주 4개 이하 프로젝트에서 생산성이 떨어지지 않았고, 하루 안의 잦은 프로젝트 전환은 낮은 생산성과 연관되었다(Vasilescu 2016, 관찰 연구).
- 칸반 팀에서 낮은 WIP는 짧은 리드타임과 연관되었지만 WIP는 생산성과 양의 상관이었다(Sjøberg 2018, 5팀·8,000건).
- 연습된 단순 과제는 일부 사람에게서 거의 완벽한 동시 수행이 가능하다(Schumacher 2001).
- 운전+작업기억 이중 과제에서 비용이 없던 사람은 2.5%였다(Watson & Strayer 2010).
- 멀티태스킹 수준과 수행의 관계는 지표에 따라 다르다. 생산량은 역U자, 정확도는 단조 감소였다(Adler & Benbunan-Fich 2012).
- 사람들은 하위 목표 완료 지점에서 전환하는 경향이 있고, 알림을 받으면 하던 단위를 마무리한 뒤 전환한다(Payne 2007, Iqbal 2007).
- 과제 경계(coarse breakpoint)에서의 중단은 최악의 시점보다 짜증을 56% 줄였다(Adamczyk & Bailey 2004).
- 자발적 전환에도 비용이 있다(Arrington & Logan 2004).
- 관찰 연구에서는 외부 중단 작업이 내부(자기) 중단 작업보다 더 빨리 재개되었다(Mark 2005, p<.055).
- 일어나는 일이 드문 대상에 대한 시각적 경계는 약 30분 이상 유지되기 어렵다는 것이 vigilance 연구의 고전적 결론으로 인용된다(Bainbridge 1983 경유, Mackworth 원문 미확인).
- 경계 과제는 "편한 일"이 아니라 높은 작업부하와 스트레스를 수반한다(Warm 2008).
- 자동화 아래의 수동적 정보 처리는 상황 인식(SA)을 떨어뜨려 자동화 실패 시 인수 성능을 낮춘다(out-of-the-loop, Endsley & Kiris 1995).
- 자동화 안주는 다중 과제 부하에서 생기고, 전문가에게도 나타나며 단순 연습으로 극복되지 않는다(Parasuraman & Manzey 2010).
- 자동화 편향은 훈련·지시로 막히지 않는다(Parasuraman & Manzey 2010).
- 한 운영자가 감독하는 자율 미사일이 16기일 때 수행과 SA가 유의하게 떨어졌다.
- 항공관제에서도 17기와 10~11기 사이에 비슷한 저하가 보고되었다.
- 바쁜 시간 비율(utilization) 70%가 성능 붕괴의 문턱으로 제안되었다(Cummings & Guerlain 2007).
- 다중 기체 감독 용량(fan-out = NT/IT + 1)은 대기 시간(재정향·큐·SA 상실)을 넣으면 최대 67% 줄었다.
- 고도로 자동화된 예외 관리 방식에서도 SA 상실 대기 때문에 36%가 줄었다(Cummings & Mitchell 2008).
- 여러 로봇을 감독할 때 과제 간 전환 비용이 존재했다.
- 그 비용은 감독 대상 수(4 대 8)보다 자동화 수준이 높을 때 더 컸다(Squire & Parasuraman 2010).
- 여러 로봇을 조율하는 agent가 완벽할 때는 임무 시간이 줄었다.
- agent의 불완전성 유형(오경보형 대 누락형)은 운영자의 시각 탐색 과제 수행에 영향을 주었다(Chen & Barnes 2012).
- 위 연구 대부분은 실험실 과제, 소표본, 단기 측정, 또는 횡단 상관이다.
- 장기적 "뇌 건강" 손상을 인과로 보인 1차 연구는 이번 조사에서 찾지 못했다.
