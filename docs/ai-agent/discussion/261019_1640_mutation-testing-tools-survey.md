---
type: discussion
kind: survey
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest, mutmut]
status: done
ref-adrs: []
related: [261019_1623_obs-toolkit-test-quality.md]
---

# mutation testing — 무엇이고 도구는 무엇이 있나 — 조사 (2026-10-19)

## 질문

논의 문서 `261019_1623_obs-toolkit-test-quality.md` 의 축 4-1 이 묻는다.
"거짓 안전감" — 테스트가 많아 보이지만 약속 위반을 잡는지 믿기 어려운 상태 — 를 재는 척도로 mutation testing 을 쓸 수 있는가.
그러려면 그것이 무엇이고, 어떤 생태계에 어떤 도구가 있고, 비용이 얼마이며, 무엇을 못 하는지를 알아야 한다.
이 문서는 그 사실만 모은다. 판정은 없다.

## 조사

### 1. 정의와 기원

**정의.** 프로그램에 작은 인공 결함(mutant)을 하나씩 심고, 테스트 스위트가 그것을 잡는지로 스위트의 적절성을 잰다.
— Petrović · Ivanković · Fraser · Just, *Practical Mutation Testing at Scale: A view from Google*, https://arxiv.org/abs/2102.11378, 조회 2026-10-19.
인용: "Mutation analysis assesses a test suite's adequacy by measuring its ability to detect small artificial faults, systematically seeded into the tested program. Mutation analysis is considered one of the strongest test-adequacy criteria."

**어휘.** 테스트가 mutant 를 잡으면 killed, 못 잡으면 survived 다.
— PIT, *Basic Concepts*, https://pitest.org/quickstart/basic_concepts/, 조회 2026-10-19.
인용: "Killed means a test caught the mutation successfully." / "Survived means the mutation was not detected by the covering test."

**점수.** mutation score 는 죽인 mutant 수를 비동치 mutant 전체로 나눈 비율이다.
— Jia & Harman, *An Analysis and Survey of the Development of Mutation Testing* (IEEE TSE 2011), https://web.eecs.umich.edu/~weimerw/2020-481F/readings/mutation-testing.pdf, 조회 2026-10-19.
인용: "The mutation score (MS) is the ratio of the number of killed mutants over the total number of non-equivalent mutants."

**기원.** 1971년 Lipton 의 학생 논문에서 시작했고, 분야의 탄생은 1978년 DeMillo · Lipton · Sayward 와 1977년 Hamlet 의 논문이다.
— Jia & Harman (위 URL), 조회 2026-10-19.
인용: "The history of Mutation Testing can be traced back to 1971 in a student paper by Richard Lipton [144]. The birth of the field can also be identified in papers published in the late 1970s by DeMillo et al. [66] and Hamlet [107]."
1978년 논문의 서지는 *Hints on Test Data Selection: Help for the Practicing Programmer*, Computer 11(4), 34–41 이다.
— Cummings, *Development and Analysis of Mutation Testing* 의 서지 인용, https://users.cs.northwestern.edu/~chrdimo/teaching/eecs396-w19/16.pdf, 조회 2026-10-19.
최초의 도구는 Budd 의 박사 연구다.
— Wikipedia, *Mutation testing*, https://en.wikipedia.org/wiki/Mutation_testing, 조회 2026-10-19.
인용: "The first implementation of a mutation testing tool was by Timothy Budd as part of his PhD work"

**두 가정.** 기법이 서는 전제가 둘이다.
Competent Programmer Hypothesis — 프로그래머는 정답에 가까운 프로그램을 쓰므로 결함은 작은 구문 변경으로 표현된다.
— Jia & Harman (위 URL), 조회 2026-10-19.
인용: "The CPH was first introduced by DeMillo et al. in 1978 [66]. It states that programmers are competent, which implies that they tend to develop programs close to the correct version."
Coupling Effect — 단순 결함을 가려내는 테스트 데이터는 복잡한 결함도 암묵적으로 가려낸다.
— Jia & Harman (위 URL, 1978 원문 재인용), 조회 2026-10-19.
인용: "Test data that distinguishes all programs differing from a correct one by only simple errors is so sensitive that it also implicitly distinguishes more complex errors"

**동치 mutant.** 원본과 의미가 같은 mutant 는 어떤 테스트로도 못 죽이고, 그 판별은 결정불가능하다.
— Jia & Harman (위 URL), 조회 2026-10-19.
인용: "To detect if a program and one of its mutants programs are equivalent is undecidable, as proved in the work of Budd and Angluin [35]. As a result, the detection of equivalent mutants alternatively may have to be carried out by humans."

**전형적 연산자.** 산술 · 관계 연산자 치환, 문장 삭제, 조건 경계, 반환값 치환, 상수 치환.
— Wikipedia (위 URL), 조회 2026-10-19.
인용: "Replacement of some arithmetic operations with others, e.g. + with *, - with /" / "Replacement of some Boolean relations with others, e.g. > with >=, == and <="
— PIT, *Mutators*, https://pitest.org/quickstart/mutators/, 조회 2026-10-19.
인용: "The conditionals boundary mutator replaces the relational operators <, <=, >, >=" / "The void method call mutator removes method calls to void methods." / "Replaces return values with an 'empty' value for that type as follows" / INLINE_CONSTS: "Changes literal values assigned to non-final variables."
— cargo-mutants, *Getting Started*, https://mutants.rs/getting-started.html, 조회 2026-10-19.
인용: "replace copy_symlink -> Result<()> with Ok(Default::default())"

### 2. 라인 · 브랜치 커버리지와 무엇이 다른가

커버리지는 코드가 실행됐는지만 재고, mutation 은 결함이 생겼을 때 테스트가 알아채는지를 잰다.
— PIT 홈페이지, https://pitest.org/, 조회 2026-10-19.
인용: "Traditional test coverage (i.e line, statement, branch, etc.) measures only which code is executed by your tests." / "mutation testing is the gold standard against which all other types of coverage are measured"
— Stryker Docs, https://stryker-mutator.io/docs/, 조회 2026-10-19.
인용: "Well... code coverage doesn't tell you everything about the effectiveness of your tests." / "The higher the percentage of mutants killed, the more _effective_ your tests are."

### 3. 도구 — 생태계별

| 도구 | 언어 | 유지 상태(마지막 릴리스 · 조회 2026-10-19) | 특징 | URL |
|---|---|---|---|---|
| mutmut | Python | 유지 — 3.8.0 (2026-09-12) | 사용 편의 중심, pytest 기반. 소스가 바뀐 함수의 mutant 만 재실행. 상태를 `mutants/` 디렉터리에 보존. `mutmut run` · `browse` · `apply` | https://github.com/boxed/mutmut · https://mutmut.readthedocs.io/en/latest/ |
| cosmic-ray | Python | 유지 — 8.7.0 (2026-08-09), 커밋 2026-10-15 | 분산 · 동시 실행 튜토리얼 제공 | https://github.com/sixty-north/cosmic-ray · https://pypi.org/project/cosmic-ray/ |
| MutPy | Python | 사실상 비유지 — 0.6.1 (2019-11-17), 마지막 커밋 같은 날 | AST 기반 | https://github.com/mutpy/mutpy |
| PIT (pitest) | Java/JVM | 유지 — 1.30.1 (2026-10-14) | 바이트코드 mutation. 라인 커버리지로 mutant 별 테스트 선택. 증분 분석(실험적). ant · maven · gradle | https://pitest.org/ · https://github.com/hcoles/pitest |
| StrykerJS | JS/TS | 유지 — v10.0.0 (2026-08-14) | 증분 파일(`reports/stryker-incremental.json`). 임계 high/low/break. 대시보드 | https://stryker-mutator.io/docs/stryker-js/configuration/ |
| Stryker.NET | C# | 유지 — 5.0.0 (2026-09-11) | git 기반 `since`(변경 코드만). `with-baseline`. break 미달 시 exit 1 | https://stryker-mutator.io/docs/stryker-net/configuration/ |
| Stryker4s | Scala | 유지 — v1.1.1 (2026-07-30) | Stryker 공통 설계 | https://github.com/stryker-mutator/stryker4s |
| go-mutesting | Go | 정체 — 마지막 커밋 2021-06-10 | 테스트로 안 덮인 코드 찾기가 주목적. 저자가 구현 보장 없음을 명시 | https://github.com/zimmski/go-mutesting |
| gremlins | Go | 저빈도 — v0.6.0 (2025-12-06), 0.x | 소형 모듈 · 마이크로서비스 대상. 대형 모듈은 수 시간 | https://github.com/go-gremlins/gremlins |
| ooze | Go | 커밋 2026-08-19, 마지막 태그 v0.3.1 (2023-05-04) | 일반 Go 테스트로 실행(`ooze.Release(t)`). 연산자 확장 인터페이스 | https://github.com/gtramontina/ooze |
| cargo-mutants | Rust | 유지 — v27.1.0 (2026-06-02), "semi-actively-maintained" | 코드 수정 불필요. `--in-diff` 로 PR 변경분만. 기본 타임아웃 = 베이스라인 5배 | https://github.com/sourcefrog/cargo-mutants · https://mutants.rs/ |
| Mull | C/C++ | 유지 — 0.34.2 (2026-10-17) | LLVM 비트코드 수준 mutation. 단일 바이너리에 모든 mutant 를 넣고 플래그로 선택 | https://github.com/mull-project/mull · https://mull.readthedocs.io/ |
| Dextool Mutate | C/C++ | 저빈도 — v5.3 (2025-09-09) | libclang 기반. mutant 스키마타(1회 컴파일). 중단 재개 · 변경분만 재검사 | https://github.com/joakim-brannstrom/dextool |
| mutant | Ruby | 유지 — v0.17.0 (2026-09-17) | 오픈소스 무료, 상업용 구독($30/월 · $250/년/개발자). 증분 모드 | https://github.com/mbj/mutant |

도구별 근거 인용.

- mutmut — https://mutmut.readthedocs.io/en/latest/, 조회 2026-10-19. 인용: "Mutmut is a mutation testing system for Python, with a strong focus on ease of use." / "Between runs, mutmut only re-tests mutants in functions whose source changed." / "Mutmut keeps the data of what it has done and the mutants in the mutants/ directory." 릴리스 3.8.0 은 https://github.com/boxed/mutmut/releases.atom.
- cosmic-ray — https://pypi.org/project/cosmic-ray/, 조회 2026-10-19. 인용: "Cosmic Ray is a mutation testing tool for Python 3."
- MutPy — https://pypi.org/pypi/MutPy/json, 조회 2026-10-19. 인용: "Mutation testing tool for Python 3.x source code." 마지막 커밋은 https://github.com/mutpy/mutpy/commits/master.atom ("Bump version to 0.6.1", 2019-11-17).
- PIT — https://github.com/hcoles/pitest, 조회 2026-10-19. 인용: "Pitest (aka PIT) is a state of the art mutation testing system for Java and the JVM." / https://pitest.org/: "works with ant, maven, gradle and others"
- Stryker 제품군 — https://stryker-mutator.io/docs/, 조회 2026-10-19. 인용: "It uses one design mentality to implement mutation testing on three platforms." 대시보드 — https://stryker-mutator.io/docs/General/dashboard/: "The Stryker dashboard is a dashboard for mutation testing"
- go-mutesting — https://github.com/zimmski/go-mutesting, 조회 2026-10-19. 인용: "Its main purpose is to find source code, which is not covered by any tests." / "I do not guarantee to implement anything soon."
- gremlins — https://github.com/go-gremlins/gremlins, 조회 2026-10-19. 인용: "Gremlins is a mutation testing tool for Go." / "As of now, Gremlins doesn't work very well on very big Go modules, mainly because a run can take hours to complete."
- ooze — https://github.com/gtramontina/ooze, 조회 2026-10-19. 인용: "This is a test as you'd write any other Go test." / "Ooze supports Go 1.25 and every stable Go release through the current version."
- cargo-mutants — https://github.com/sourcefrog/cargo-mutants, 조회 2026-10-19. 인용: "cargo-mutants helps you improve your program's quality by finding places where bugs could be inserted without causing any tests to fail." / "As of August 2026 this is an semi-actively-maintained spare time project"
- Mull — https://github.com/mull-project/mull · https://mull.readthedocs.io/en/latest/HowMullWorks.html, 조회 2026-10-19. 인용: "Mull is a practical mutation testing and fault injection tool for C and C++." / "Mull finds and creates mutations of a program in memory, on the level of LLVM bitcode." / "The resulting program is compiled into a single binary which is run multiple times, one run per mutation."
- Dextool — https://github.com/joakim-brannstrom/dextool (plugin/mutate/README.md), 조회 2026-10-19. 인용: "Uses mutant schemata to compile and link once per SUT, rather than once per mutant." / "Can reuse previous results when the SUT changes by only testing the change."
- mutant (Ruby) — https://github.com/mbj/mutant, 조회 2026-10-19. 인용: "Mutant is mutation testing for Ruby." / "Free for open source. Use `--usage opensource` for public repositories." / "Commercial use requires a subscription ($30/month or $250/year per developer)."

### 4. 대규모 적용 사례 — Google

코드 리뷰 시점에 변경분의 mutant 만 보여 주고, 커버되지 않은 줄과 "arid" 줄(흥미 없는 줄)은 억제한다. 6,000명이 쓴다.
— Petrović & Ivanković, *State of Mutation Testing at Google* (ICSE-SEIP 2018), https://research.google/pubs/state-of-mutation-testing-at-google/, 조회 2026-10-19.
인용: "We focus on a code-review based approach and consider the effects of surfacing mutation results on developer attention." / "omitting lines of code without statement coverage and lines that are determined to be uninteresting - we dub these arid lines." / "The described system is used by 6,000 engineers in Google on all code changes they author or review"

후속 연구 — 전체가 아니라 변경 코드만 mutate 하고, 개발자 피드백으로 억제 휴리스틱을 키워 생산적 mutant 비율을 15% 에서 89% 로 올렸다.
— *Practical Mutation Testing at Scale* (arXiv 2102.11378 PDF), 조회 2026-10-19.
인용: "Mutation testing is done incrementally, mutating only changed code during code review, rather than the entire code base" / "enabled us to develop heuristics for mutant suppression that improved the ratio of productive mutants from 15% to 89%."
리뷰 UI 에 mutant 마다 "Please fix" · "Not useful" 링크가 있고, 피드백이 달린 mutant 의 82% 가 생산적으로 분류됐다.
인용: "each surfaced mutant displays a Please fix (productive mutant) and a Not useful (unproductive mutant) link." / "82% of all surfaced mutants with feedback were labeled as productive by developers."
초기에는 85% 가 비생산적이었다.
인용: "developers at Google initially classified 85% of reported mutants as unproductive. An unproductive mutant is either trivially equivalent to the original program or it is detectable, but adding a test for it would not improve the test suite"

### 5. 비용과 실천

**비용의 근원.** mutant 수 × 테스트 실행 시간이다.
— Jia & Harman (위 URL), 조회 2026-10-19.
인용: "One problem that prevents Mutation Testing from becoming a practical testing technique is the high computational cost of executing the enormous number of mutants against a test set."
절감 기법은 셋으로 분류된다.
인용: "cost reduction techniques are divided into three types: 'do fewer', 'do faster' and 'do smarter'."

**mutant 별로 그 줄을 덮는 테스트만 실행.**
— PIT, *Basic Concepts* (위 URL), 조회 2026-10-19.
인용: PIT "performs a traditional line coverage analysis for the tests" 뒤 "uses this data along with the timings of the tests to pick a set of test cases targeted at the mutated code."

**무한 루프 대비 타임아웃.**
— PIT (위 URL): "A mutation may time out if it causes an infinite loop."
— cargo-mutants, *Timeouts*, https://mutants.rs/timeouts.html, 조회 2026-10-19: "The default test timeout is 5 times the baseline test time, with a minimum of 20 seconds."
— mutmut docs (위 URL): "Currently calculated as (duration_of_original_tests + timeout_constant) * timeout_multiplier seconds."

**증분.** 이전 결과를 저장해 추론 가능한 분석을 생략한다. 오차가 생길 수 있다.
— PIT, *Incremental Analysis*, https://pitest.org/quickstart/incremental_analysis/, 조회 2026-10-19.
인용: "If this option is activated, PIT will track changes to the code and tests and store the results from previous runs." / "With the exception of 4), all these optimisations introduce a degree of potential error into the analysis."
— StrykerJS, *Incremental*, https://stryker-mutator.io/docs/stryker-js/incremental/, 조회 2026-10-19.
인용: "The next time StrykerJS runs, it will read this JSON file and try to reuse as much of it as possible." / "StrykerJS will do a git-like diff of your code and test files to the previous version"

**변경분만.**
— Stryker.NET, *Configuration* (위 URL), 조회 2026-10-19.
인용: "Use git information to test only code changes since the given target." / "Stryker will only report on mutants within the changed code."
— cargo-mutants, *PR diff*, https://mutants.rs/pr-diff.html, 조회 2026-10-19.
인용: "You can use `--in-diff` to test only the code that has changed in a pull request." / "This can give much faster feedback on pull requests, but can miss some problems that"
cargo-mutants README 는 CI 지침에서 PR 증분 검사와 전체 검사를 나눠 안내한다.
— https://github.com/sourcefrog/cargo-mutants, 조회 2026-10-19. 인용: "incremental testing of pull requests"

**임계치.** StrykerJS 기본은 high 80 · low 60 · break null 이다. Stryker.NET 은 break 0 이고 미달 시 exit 1.
— StrykerJS, *Configuration* (위 URL), 조회 2026-10-19.
인용: "Set `break` to `null` (default) to never let your build fail."
— Stryker.NET (위 URL): "Thresholds should be a number between 0 and 100."
점수 계산에서 error 로 끝난 mutant 는 제외된다.
— Stryker FAQ, https://stryker-mutator.io/docs/General/faq/, 조회 2026-10-19.
인용: "It's the percentage of mutants that have been killed." / "Please note that mutants that resulted in an `error` are not used in the calculation."
성능 1순위는 단위 테스트 자체의 속도다.
인용: "As we're running your tests, the first thing you should do, is to improve the performance of your unit tests."

**실행 시간의 규모.** 대형 Go 모듈에서는 수 시간이다.
— gremlins (위 URL), 조회 2026-10-19. 인용: "a run can take hours to complete."

### 6. 비판과 한계

- 동치 mutant 는 자동 탐지가 일반적으로 불가능하다. — *Practical Mutation Testing at Scale* (PDF), 조회 2026-10-19. 인용: "Equivalent mutants, which are semantically equivalent to the mutated program, are a plague in mutation testing and cannot generally be detected automatically."
- 도구도 못 가려내므로 손으로 찾거나 100% 를 포기하라고 권한다. — Stryker, *Equivalent mutants*, https://stryker-mutator.io/docs/mutation-testing-elements/equivalent-mutants/, 조회 2026-10-19. 인용: "There is no definitive way for Stryker to find and ignore them." / "or accept that you won't make 100%."
- flaky 테스트가 있으면 결과가 무의미하다. — cargo-mutants, *Getting Started* (위 URL), 조회 2026-10-19. 인용: "If the tests are flaky, meaning that they can pass or fail depending on factors other than the source tree, then the cargo-mutants results will be meaningless."
- 절대 점수는 대규모에서 행동 가능하지 않다. — *Practical Mutation Testing at Scale* (PDF), 조회 2026-10-19. 인용: "we were also unable to find a good way to surface it to the developers in an actionable way, as it is neither concrete nor actionable, and it does not guide testing."
- 비생산적 mutant 를 죽이려 쓴 테스트는 구현을 고정하는 change-detector 가 되어 해로울 수 있다. — 같은 PDF, 조회 2026-10-19. 인용: "it is conceivable that these tests, if written and added, would even have a negative impact because their change-detector nature"
- 사람의 노력(oracle · 동치 판별)도 비용이다. — Jia & Harman (위 URL), 조회 2026-10-19. 인용: "The other problems are related to the amount of human effort involved in using Mutation Testing. For example, the human oracle problem [247] and the equivalent mutant problem [35]."

### 조사에서 찾지 못한 것

- DeMillo · Lipton · Sayward 1978 원문의 공개 PDF — 원문 문장은 Jia & Harman 의 재인용이다.
- "mutation score 게이밍" 에 대한 1차 출처 — 대신 Google 의 "절대 점수는 행동 가능하지 않다" 를 썼다.
- StrykerJS 의 `--since` 옵션 — 현재 문서에 없다. git 기반 `since` 는 Stryker.NET 만 확인됐다.
- mutmut 3 의 `results` 명령 — 문서에 없다. 확인된 것은 `run` · `browse` · `apply` 다.

## 논의 문서로 가져가는 것

- mutation testing 은 "테스트가 결함을 알아채는가" 를 재고, 커버리지는 "코드가 실행됐는가" 만 잰다. 거짓 안전감의 척도로 전자가 맞다.
- 점수의 분모는 비동치 mutant 인데 동치 판별은 결정불가능하다. 100% 는 원래 안 나오고, 점수보다 생존 mutant 목록이 읽을 거리다.
- 중복 테스트는 점수를 올리지 못한다 — 같은 mutant 를 두 테스트가 죽여도 한 번이다. 제거 전후 점수 비교가 "안전한 제거" 의 증거가 될 수 있다.
- Python 에서 유지되는 도구는 mutmut(3.8.0, 2026-09)과 cosmic-ray(8.7.0, 2026-08)다. MutPy 는 2019년에 멈췄다.
- mutmut 은 pytest 위에서 돌고, 바뀐 함수의 mutant 만 재실행하며, 상태를 `mutants/` 에 남긴다. 타임아웃은 원 테스트 시간에 비례한다.
- 비용은 mutant 수 × 테스트 시간이다. 절감은 변경분만 · 덮는 테스트만 · 증분이다. Google 은 전체 점수를 포기하고 리뷰 시점의 변경분 mutant 만 보인다.
- 생존 mutant 를 전부 죽이려 들면 구현 고정 테스트가 생긴다 — Google 이 초기 85% 를 비생산적으로 분류했다. 생존 목록은 걸러 읽어야 한다.
- flaky 테스트가 있으면 결과가 무의미하다. obs-toolkit 은 replay · FakeTransport 로 결정론적이라 이 조건은 만족한다.
