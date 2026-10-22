---
type: discussion
kind: survey
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest, mutmut]
status: done
ref-adrs: []
related: [261019_1623_obs-toolkit-test-quality.md, 261019_1640_mutation-testing-tools-survey.md]
---

# 테스트 커버리지와 mutation testing — 무엇이 다르고, 서로 무엇을 대체하지 못하나

## 질문

obs-toolkit 테스트 리팩토링 Task 는 전 · 후로 mutation 점수를 한 번씩 재기로 했다(obs-toolkit 테스트 품질 논의 4-1).
그 자리에 커버리지도 함께 둘 것인가, 둘 중 하나로 충분한가를 정하려면 두 척도가 무엇을 재고 무엇을 못 재는지를 알아야 한다.
이 문서는 둘의 정의 · 서로 말하지 못하는 것 · 둘의 관계 · 실천에서의 분담을 1차 자료로 조사한다.
mutation testing 자체의 정의 · 도구 · 비용은 앞선 조사 `261019_1640` 이 다뤘으므로 여기서는 반복하지 않는다.

## 조사

### 1. 두 척도가 재는 것

**커버리지는 "실행됐는가" 를 센다.**
coverage.py 의 branch 문서는 문장 커버리지 위에 분기 커버리지를 더하며, 모든 줄이 실행돼도 `if` 가 한 번도 거짓이 되지 않으면 분기 커버리지가 그것을 잡는다고 설명한다 — "Statement coverage would show all lines of the function as executed."(옮김: 문장 커버리지는 그 함수의 모든 줄이 실행됐다고 보여 줄 것이다.)
— coverage.py, *Branch coverage measurement*, https://coverage.readthedocs.io/en/latest/branch.html, 조회 2026-10-20.

강한 기준일수록 "어떤 조합으로 실행됐는가" 를 더 센다.
항공 소프트웨어 표준 DO-178C 는 소프트웨어 등급에 따라 문장 · 결정 · MC/DC 커버리지를 요구하고, LDRA 의 해설은 "for level A software MC/DC is obligatory"(옮김: 등급 A 소프트웨어에는 MC/DC 가 의무다) 라 적는다. 근거 절은 "DO-178C Section 6.4.4 details requirements for the achievement of 100% MC/DC, decision, and statement coverage"(옮김: DO-178C 6.4.4 절이 100% MC/DC · 결정 · 문장 커버리지 달성 요건을 상세히 정한다).
— LDRA, *DO-178C & Structural Coverage Analysis*, https://ldra.com/ldra-blog/do-178c-structural-coverage-analysis/, 2025-04-25, 조회 2026-10-20. 표준 원문은 확인하지 못했다(아래 "찾지 못한 것").

**mutation testing 은 "틀린 것을 잡는가" 를 센다.**
소스에 작은 인공 결함(변이)을 심고 테스트가 그것을 실패로 드러내는지를 본다.
Google 의 2018 논문은 이것이 다른 커버리지 기준들을 포함한다고 쓴다 — "It is widely considered the strongest test criterion in terms of finding the most faults and it subsumes a number of other coverage criteria."(옮김: 가장 많은 결함을 찾는다는 점에서 가장 강한 테스트 기준으로 널리 여겨지며, 다른 여러 커버리지 기준을 포함한다.)
— Petrović · Ivanković, *State of Mutation Testing at Google*, ICSE-SEIP 2018, https://research.google/pubs/state-of-mutation-testing-at-google/, 조회 2026-10-20.

### 2. 커버리지가 말하지 못하는 것 — 단언(오라클)의 품질

**실행과 검사는 다르다.**
PIT 는 이 차이를 한 문장으로 적는다 — "Traditional test coverage (i.e line, statement, branch, etc.) measures only which code is executed by your tests. It does not check that your tests are actually able to detect faults in the executed code."(옮김: 전통적 테스트 커버리지(라인 · 문장 · 분기 등)는 테스트가 어느 코드를 실행했는지만 잰다. 테스트가 실행된 코드의 결함을 실제로 잡아낼 수 있는지는 검사하지 않는다.)
가장 극단적인 예로 "tests with no assertions"(옮김: 단언이 없는 테스트) 를 든다.
— pitest.org, *Why?*, https://pitest.org/, 조회 2026-10-20.

Stryker 문서는 같은 말을 묻는다 — "when was the last time you saw a test without an assertion, purely to increase the code coverage?"(옮김: 순전히 커버리지를 올리려고 단언 없이 쓴 테스트를 마지막으로 본 게 언제인가?)
— Stryker, *What is mutation testing?* §"But wait, what about code coverage?", https://stryker-mutator.io/docs/, 조회 2026-10-20.

Google Testing Blog 도 같은 선을 긋는다 — "Code coverage does not guarantee that the covered lines or branches have been tested correctly, it just guarantees that they have been executed by a test."(옮김: 커버리지는 덮인 줄이나 분기가 올바르게 테스트됐음을 보장하지 않는다. 테스트가 그것을 실행했다는 것만 보장한다.)
그리고 그 빈 자리를 채우는 수단으로 mutation testing 을 지목한다 — "A better technique to assess whether you're adequately exercising the lines your tests cover, and adequately asserting on failures, is mutation testing."(옮김: 테스트가 덮는 줄을 충분히 돌리고 실패에 충분히 단언하는지를 평가하는 더 나은 기법은 mutation testing 이다.)
— Bender · Arguelles · Ivanković, *Code Coverage Best Practices*, Google Testing Blog, 2020-08-07, https://testing.googleblog.com/2020/08/code-coverage-best-practices.html, 조회 2026-10-20.

**학술적으로는 "오라클 품질" 이라 부른다.**
Schuler · Zeller 는 문제를 이렇게 정의한다 — "A known problem of traditional coverage metrics is that they do not assess oracle quality - that is, whether the computation result is actually checked against expectations."(옮김: 전통적 커버리지 척도의 알려진 문제는 오라클 품질, 즉 계산 결과가 실제로 기대값과 대조되는지를 평가하지 않는다는 것이다.)
— Schuler · Zeller, *Assessing Oracle Quality with Checked Coverage*, ICST 2011, https://doi.org/10.1109/ICST.2011.32, 초록은 OpenAlex 에서 조회 2026-10-20.

**커버리지 수치는 결함 검출력의 좋은 지표가 아니다 — 실증.**
Inozemtseva · Holmes 는 다섯 시스템(최대 724,000줄)에 대해 테스트 스위트 31,000개를 만들어 문장 · 결정 · 수정 조건 커버리지를 재고, 결함 검출력은 mutation testing 으로 쟀다.
결과 — "We found that there is a low to moderate correlation between coverage and effectiveness when the number of test cases in the suite is controlled for. In addition, we found that stronger forms of coverage do not provide greater insight into the effectiveness of the suite."(옮김: 스위트의 테스트 수를 통제하면 커버리지와 검출력 사이에는 낮거나 중간 정도의 상관만 있었다. 또한 더 강한 형태의 커버리지가 스위트의 검출력에 대해 더 큰 통찰을 주지도 않았다.)
결론 — "coverage, while useful for identifying under-tested parts of a program, should not be used as a quality target because it is not a good indicator of test suite effectiveness."(옮김: 커버리지는 프로그램의 덜 테스트된 부분을 찾는 데는 유용하지만, 테스트 스위트 검출력의 좋은 지표가 아니므로 품질 목표로 쓰여서는 안 된다.)
— Inozemtseva · Holmes, *Coverage Is Not Strongly Correlated with Test Suite Effectiveness*, ICSE 2014, https://doi.org/10.1145/2568225.2568271, PDF https://www.cs.ubc.ca/~rtholmes/papers/icse_2014_inozemtseva.pdf, 조회 2026-10-20.

Marick 의 1997년 경고가 같은 내용이다 — "If a part of your test suite is weak in a way that coverage can detect, it's likely also weak in a way coverage can't detect."(옮김: 테스트 스위트의 어느 부분이 커버리지가 잡아낼 수 있는 방식으로 약하다면, 커버리지가 잡아내지 못하는 방식으로도 약할 가능성이 높다.)
— Marick, *How to Misuse Code Coverage*, 1997(1999 개정), 사본 https://manualzilla.com/doc/5972971/how-to-misuse-code-coverage, 조회 2026-10-20. Fowler 가 같은 문장을 인용한다 — https://martinfowler.com/bliki/TestCoverage.html, 2012-04-17, 조회 2026-10-20.

### 3. mutation testing 이 대체하지 못하는 것 — 커버리지만이 주는 것

**① 실행되지 않은 코드의 위치.**
Marick — "If a line has never been executed, it's a safe bet you didn't catch any bugs lurking in it."(옮김: 한 번도 실행되지 않은 줄이 있다면, 거기 숨은 버그를 하나도 못 잡았다고 봐도 틀림없다.)
Fowler — "Test coverage is a useful tool for finding untested parts of a codebase."(옮김: 테스트 커버리지는 코드베이스에서 테스트되지 않은 부분을 찾는 유용한 도구다.)
Google — "a low code coverage number does guarantee that large areas of the product are going completely untested by automation on every single deployment."(옮김: 낮은 커버리지 수치는 제품의 넓은 영역이 매 배포마다 자동화로 전혀 테스트되지 않고 있음을 확실히 보장한다.)
세 출처가 같은 쓸모를 말한다 — 커버리지의 낮은 수치는 확실한 신호이고, 높은 수치는 약한 신호다.
변이는 실행되지 않은 코드에서는 전부 살아남으므로 "어디가 안 돌았나" 를 변이 결과에서 다시 읽어내야 하고, 커버리지는 그것을 직접 준다.
— 출처는 §2 와 같다.

**② 비용과 보편성.**
Google 은 커버리지의 장점을 비용으로 적는다 — "It is not a perfect measure of test quality, but it does offer a reasonable, objective, industry standard metric with actionable data. It does not require significant human interaction, it applies universally to all forms of code"(옮김: 테스트 품질의 완벽한 척도는 아니지만, 실행 가능한 데이터를 가진 합리적이고 객관적인 업계 표준 지표다. 사람의 개입이 거의 필요 없고 모든 형태의 코드에 보편적으로 적용된다.).
반대로 mutation 은 "Traditional mutation analysis is computationally prohibitive which hinders its adoption as an industry standard."(옮김: 전통적 mutation 분석은 계산 비용이 감당하기 어려워 업계 표준으로 채택되는 것을 가로막는다.)
— Google Testing Blog(위) · Petrović · Ivanković 2018(위).

**③ mutation 도구의 전제 — 커버리지가 먼저 있어야 한다.**
PIT 는 변이마다 돌릴 테스트를 고르는 데 라인 커버리지를 쓴다 — "PIT performs a traditional line coverage analysis for the tests" 뒤 "uses this data along with the timings of the tests to pick a set of test cases targeted at the mutated code."(옮김: PIT 는 테스트에 대해 전통적인 라인 커버리지 분석을 수행하고, 그 데이터를 테스트 실행 시간과 함께 써서 변이된 코드를 겨냥한 테스트 집합을 고른다.)
— pitest.org, *Basic concepts* §"Running the tests", https://pitest.org/quickstart/basic_concepts/, 조회 2026-10-20.
Google 의 파이프라인은 커버리지 없는 줄을 변이 대상에서 뺀다 — "drastically reduces the number of mutants by omitting lines of code without statement coverage"(옮김: 문장 커버리지가 없는 줄을 빼서 변이 수를 크게 줄인다).
그리고 커버리지 계산 자체가 실패하는 곳에서는 변이도 없다 — "The system processes about 30% of all diffs across Google that have statement coverage calculated. About 15% of coverage statement calculations fail across Google."(옮김: 이 시스템은 Google 전체에서 문장 커버리지가 계산된 diff 의 약 30% 를 처리한다. Google 전체에서 문장 커버리지 계산의 약 15% 는 실패한다.)
— Petrović · Ivanković 2018(위).

**④ 규제 · 계약의 인공물.**
DO-178C 류의 표준이 요구하는 것은 구조 커버리지(문장 · 결정 · MC/DC)이지 mutation 점수가 아니다(§1 의 LDRA).
mutation 점수를 요구하는 표준은 이번 조사에서 찾지 못했다.

**⑤ 실제 결함과의 거리.**
변이는 인공 결함이다.
Just 외는 357개 실제 결함으로 검증해 "a statistically significant correlation between mutant detection and real fault detection, independently of code coverage"(옮김: 코드 커버리지와 독립적으로, 변이 검출과 실제 결함 검출 사이에 통계적으로 유의한 상관) 를 보이면서도 "reveal some inherent limitations"(옮김: 몇 가지 내재적 한계를 드러낸다) 라 적었다.
— Just · Jalali · Inozemtseva · Ernst · Holmes · Fraser, *Are Mutants a Valid Substitute for Real Faults in Software Testing?*, FSE 2014, https://doi.org/10.1145/2635868.2635929, 초록은 OpenAlex 에서 조회 2026-10-20.
동등 변이(어떤 테스트도 죽일 수 없는 변이)와 그것이 점수에 주는 잡음은 앞선 조사 `261019_1640` §6 에 있다.

### 4. 둘의 관계 — 포함 · 예측 · 중간 지점

**포함.** mutation 은 커버리지 기준들을 포함한다(§1 의 Petrović). 변이가 든 줄이 실행되지 않으면 그 변이는 죽지 않으므로, mutation 점수는 커버리지의 상한 아래에 있다.

**예측.** 그러나 한 스위트를 평가할 때 문장 커버리지는 mutation 점수의 싼 예측자다.
Gopinath 외 — "statement (not block, branch, or path) coverage predicts mutation kills best."(옮김: 블록 · 분기 · 경로가 아니라 문장 커버리지가 변이 사살을 가장 잘 예측한다.)
그들은 실무자가 여러 스위트를 비교하지 않고 하나를 평가한다는 점에서 Inozemtseva 와 다른 설정을 썼다 — "Practitioners, however, seldom compare suites --- they evaluate one suite."(옮김: 그러나 실무자는 스위트들을 비교하는 일이 드물다. 하나의 스위트를 평가한다.)
— Gopinath · Jensen · Groce, *Code coverage for suite evaluation by developers*, ICSE 2014, https://doi.org/10.1145/2568225.2568278, 초록은 OpenAlex 에서 조회 2026-10-20.
두 논문은 모순이 아니다 — 같은 크기의 스위트들 사이에서 커버리지는 검출력을 잘 가르지 못하고(Inozemtseva), 한 스위트의 대략적 검출력을 싸게 짐작하는 데는 문장 커버리지가 가장 낫다(Gopinath).

**중간 지점 — checked coverage.**
Schuler · Zeller 는 "실행된 문장" 이 아니라 "단언에 영향을 준 실행된 문장" 을 세는 척도를 제안했다 — "the dynamic slice of covered statements that actually influence an oracle"(옮김: 실행된 문장 가운데 실제로 오라클에 영향을 주는 동적 슬라이스).
실험 결과 — "checked coverage is a sure indicator for oracle quality - and even more sensitive than mutation testing, its much more demanding alternative."(옮김: checked coverage 는 오라클 품질의 확실한 지표이며, 훨씬 더 비용이 큰 대안인 mutation testing 보다도 민감하다.)
동적 슬라이싱이 필요해 도구가 드물다(아래 "찾지 못한 것").
— Schuler · Zeller 2011(위).

### 5. 실천에서의 분담

Google 은 둘을 다른 자리에 둔다.
커버리지는 전사 지침 숫자로 — "at Google we offer the general guidelines of 60% as 'acceptable', 75% as 'commendable' and 90% as 'exemplary'"(옮김: Google 은 60% 를 "수용 가능", 75% 를 "칭찬할 만함", 90% 를 "모범적" 으로 보는 일반 지침을 제시한다) — 그러나 "we like to stay away from broad top-down mandates"(옮김: 광범위한 하향식 강제는 피하고자 한다).
mutation 은 코드 리뷰 시점에 변경분의 변이만 — "We focus on a code-review based approach and consider the effects of surfacing mutation results on developer attention."(옮김: 코드 리뷰 기반 접근에 집중하고, 변이 결과를 드러내는 것이 개발자의 주의에 미치는 영향을 고려한다.)
— Google Testing Blog 2020(위) · Petrović · Ivanković 2018(위).

Fowler 는 커버리지 수치를 목표로 두는 것 자체를 경계한다 — "I would be suspicious of anything like 100% - it would smell of someone writing tests to make the coverage numbers happy"(옮김: 100% 에 가까운 수치는 의심스럽다. 누군가 커버리지 숫자를 맞추려고 테스트를 쓴 냄새가 난다.).
— Fowler 2012(위).

질문별로 어느 척도가 답하는지를 모으면 이렇다.

| 질문 | 커버리지 | mutation |
|---|---|---|
| 어느 코드가 한 번도 안 돌았나 | 직접 답한다 | 생존 변이에서 간접으로 |
| 실행된 코드의 결과를 테스트가 검사하나 | 답하지 못한다 | 직접 답한다 |
| 테스트를 지웠는데 검출력이 그대로인가 | 실행 범위가 같다는 것까지만 | 점수 비교로 답한다 |
| 어느 경계값이 빠졌나 | 답하지 못한다 — 분기는 조건의 참 · 거짓을, MC/DC 는 각 조건이 독립적으로 결과를 바꾸는 것을 요구할 뿐 경계값 자체는 요구하지 않는다. `x < 10` 은 5 와 15 로 분기 커버리지가 차고 10 은 영영 안 돌아도 된다 | 살아남은 `<` → `<=` 변이가 그 경계를 가리킨다 — 10 을 넣고 결과를 단언하는 테스트가 있어야만 죽는다 |
| 비용 | 테스트 한 번 실행 | 변이 수 × 테스트 실행 |
| 전제 | 없음 | 커버리지(변이 대상 선정 · 테스트 선택) |
| 규제가 요구하나 | 요구한다(DO-178C) | 찾지 못했다 |

## 조사에서 찾지 못한 것

- DO-178C 원문(6.4.4 · Table A-7)은 유료 표준이라 확인하지 못했다. 등급별 요구는 2차 자료(LDRA · Rapita) 로만 확인했다.
- Python 에서 checked coverage 를 구현한 유지되는 도구는 찾지 못했다. Schuler · Zeller 의 구현은 Java(JavaSlicer 기반)였다.
- mutation 점수를 요구하는 규제 · 산업 표준은 찾지 못했다.
- obs-toolkit 저장소에 커버리지 도구(pytest-cov 등)가 핀돼 있지 않다 — `pyproject.toml` · CI 워크플로 · README 에 `coverage` · `--cov` 가 없다(2026-10-20 확인). 도구 도입은 tdd-loop 규약상 저장소의 결정이다.

## 논의로 가져가는 것

- 둘은 서로의 대체가 아니라 다른 질문의 답이다. 커버리지는 "어디가 안 돌았나", mutation 은 "돈 곳을 검사하나" 다.
- 커버리지가 mutation 보다 낫거나 대체 불가한 것은 결국 둘이다 — 비용(테스트 한 번)과 실행되지 않은 코드의 색출. 나머지(규제 인공물 · mutation 도구의 전제)는 이 둘의 파생이다. 경계 시나리오의 누락 · 단언의 약함은 어떤 커버리지 기준으로도 보이지 않고 변이로만 보인다.
- 리팩토링 Task 의 전 · 후 측정(4-1 A)에 커버리지를 함께 재면 비용은 테스트 한 번이고, 생존 변이를 "실행됐으나 단언이 약하다" 와 "실행되지 않았다" 로 갈라 읽을 수 있다. 커버리지 없이 점수만 비교하면 점수 하락이 단언을 지운 탓인지 실행 범위가 줄어든 탓인지 분간이 안 된다.
- 리팩토링의 안전 증거는 짝이다 — 실행 범위가 줄지 않았다(커버리지 불변) 그리고 검출력이 줄지 않았다(점수 불변). 둘 중 하나만으로는 반쪽이다.
- 커버리지 수치를 목표나 AC 로 두지 않는다. Inozemtseva · Fowler · Google 이 같은 이유로 말린다. 수치는 측정 기록이지 종료 조건이 아니다.
- green 뒤에 더한 행 · red 에서 통과한 가드의 변별력은 커버리지로 보이지 않는다 — 실행은 이미 되고 있다. 그것을 보는 것은 변이(또는 strength.md 의 사고실험)뿐이다.
- obs-toolkit 에 커버리지 도구가 없으므로, 전 · 후 측정에 커버리지를 넣으려면 도구 도입이 Task 안의 결정이 된다.
