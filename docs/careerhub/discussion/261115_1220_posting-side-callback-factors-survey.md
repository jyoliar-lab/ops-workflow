---
type: discussion
kind: survey
goal: jobseeker-company-matching
topic: careerhub
subjects: []
status: active
related: [docs/careerhub/discussion/261115_1220_posting-selection-by-screening-odds.md]
---

# 공고 쪽 요인과 서류 통과 확률 — 조사 (2026-11-15)

## 질문

같은 지원자라도 공고에 따라 서류 통과(콜백·면접 초대) 확률이 달라지는지 알고자 했다.
달라진다면 공고 쪽에서 관찰 가능한 어떤 요인(지원 시점, 경쟁 강도, 공고의 나이·상태, 요건 충족 정도, 고용주 특성, 심사 방식)과 관련되는지 근거를 모았다.
결론이나 기능 제안은 쓰지 않는다.
표기: [열람] = 본문·초록을 직접 열어 확인, [검색발췌] = 검색 요약만 봄(미확인).
이번 조사는 WebSearch 요약이 주였고 직접 열람은 일부뿐이다. 수치 대부분은 [검색발췌]다.
한국 자료는 "KR", IT·개발 직군 자료는 "IT"로 표시한다. IT 직군 전용 자료는 이번에 찾지 못했다.

## 조사

### 1. 지원 시점 — 일찍 지원하면 유리한가

- 동료심사 연구로 "게시 후 N일 안 지원 vs 콜백"을 측정한 것은 찾지 못했다.
- 블로그 수치가 있다: "submissions made within the first 2 hours of a job publication achieve a 12.7% callback rate, compared to a 1.8% callback rate for applications submitted more than 72 hours post-listing."
  - 출처: jobloo.co "Best Day and Time to Apply for Jobs: 2026 Data" (https://jobloo.co/blog/best-day-time-to-apply-jobs-data/), 2026. [검색발췌]
  - 데이터 출처·측정 방법이 적혀 있지 않다고 검색 요약이 전한다. 벤더·블로그 자료.
- TalentWorks 2017 분석(약 1,600건 지원 기반)이 초기 지원의 면접 확률이 높다고 보고했다는 2차 인용이 있다.
  - 출처: DEV Community "Why applying in the first hour gets more replies" (https://dev.to/fzsheik/why-applying-in-the-first-hour-gets-more-replies), 연도 미확인. [검색발췌] (원문 fetch는 404, 원 TalentWorks 보고서는 못 찾음)
  - 검색 요약에 따르면 그 글 스스로 콜백 근거는 지원 흐름 근거보다 덜 엄밀하다고 적었다.
- 한 채용 대행사 분석은 공고 나이에 따라 지원률은 대체로 일정했고, 오래된 공고는 노출(impression)이 줄었다고 했다.
  - 출처: Haley Marketing "Age of job posting affect performance on job boards" (https://www.haleymarketing.com/2020/08/03/age-job-posting-affect-performance-job-boards/), 2020. [검색발췌]
  - 변수 하나·소수 공고 분석이라고 요약에 적혀 있다. 콜백이 아니라 노출·지원 수 관련이다.
- 한국에서 지원 시점별 서류 합격률 자료는 찾지 못했다. 근거 없음.
- "일찍 지원하면 유리하다"의 원 출처는 특정하지 못했다.

### 2. 경쟁 강도 — 지원자 수와 지원 행동·콜백

- Gee의 LinkedIn 현장실험은 지원자 수 표시가 지원 완료 확률을 바꿨다고 보고한다.
  - "This paper presents the results from a 2.3 million person field experiment that varies whether or not a job seeker sees the number of applicants for a job posting. This intervention increases the likelihood that a person will finish an application by 3.5%. Women have a larger increase in their likelihood of finishing an application than men."
  - 출처: Gee, "The More You Know: Information Effects on Job Application Rates in a Large Field Experiment", IZA DP 10372, 2016 (Management Science 2019). https://econpapers.repec.org/RePEc:iza:izadps:dp10372 [열람 — 초록]
  - 하버드 Growth Lab 요약에 따르면 효과가 경험 적은 구직자와 덜 알려진 회사 공고에서 더 컸다. https://gap.hks.harvard.edu/more-you-know-information-effects-job-application-rates-gender-large-field-experiment [검색발췌]
  - 이 실험의 결과변수는 지원 행동이다. 콜백 확률은 초록에 없다.
- 공고당 지원자 수와 개별 콜백 확률의 직접 관계는 이번에 찾지 못했다.
- 임금이 높은 공고가 지원자를 더 끌고 모두의 채용 확률을 낮춘다는 지향 탐색(directed search) 증거가 있다.
  - "high-wage ads attract more applicants as in directed search models." (칠레 trabajando.com 자료)
  - 출처: Banfi & Villena-Roldán, "Do High-Wage Jobs Attract More Applicants? Directed Search Evidence from the Online Labor Market", J. of Labor Economics 2019. https://mpra.ub.uni-muenchen.de/91756/ [검색발췌]
  - 같은 요약에서 임금 명시 공고는 표본의 13.4%였다. 공고문의 요건이 임금 정보를 암묵적으로 전달하는 듯하다고 했다.
- Faberman & Kudlyak은 Snagajob 지원 단위 데이터(2010.9–2011.9)에서 구직 기간이 길수록 주당 지원 수가 줄지만 장기 구직자는 전체 기간 상대적으로 더 많이 지원한다고 보고했다.
  - 출처: "The Intensity of Job Search and Search Duration", FRB SF WP 2016-13. https://www.frbsf.org/economic-research/publications/working-papers/2016/13/ [검색발췌]
  - 콜백이 아니라 지원 강도 연구다.

### 3. 공고의 나이·상태 — 장기 공고, 재게시, 유령 공고, time-to-fill

- 유령 공고 비율 추정은 출처마다 정의가 달라 크게 갈린다.

| 출처 | 수치 | 정의·측정 | 표시 |
|---|---|---|---|
| Greenhouse (2024, 벤더) | 한 분기 공고의 약 18–22%가 가짜이거나 미충원 | 자사 플랫폼 데이터. 산식 공개 여부 미확인 | [검색발췌] Gizmodo https://gizmodo.com/1-in-5-online-job-postings-are-either-fake-or-never-filled-study-finds-2000549706 |
| Revelio Labs (2023) | 채용/공고 비율이 2018년 0.75에서 2023년 0.5 미만 | 공고를 6개월 내 신규 채용과 매칭 | [검색발췌] https://www.reveliolabs.com/news/macro/ghost-job-postings/ |
| MyPerfectResume (2025.11, 벤더) | 2025.6 구인 공고의 30%가 채용으로 이어지지 않음 | BLS JOLTS 기반이라고 요약됨 | [검색발췌] https://www.cpapracticeadvisor.com/2025/11/12/ghost-jobs-up-to-1-in-3-job-listings-dont-result-in-hires/173044/ |
| Ashby (2024, 벤더) | 2024년 오픈 공고의 82%가 채용으로 이어짐 | 자사 고객 데이터 | [검색발췌] https://www.ashbyhq.com/talent-trends-report/reports/ghost-jobs |
| Resume Builder (2024) | 채용 담당자 39%가 지난 1년간 허위 공고를 올린 적 있다고 응답 | 설문 | [검색발췌] 위 요약 경유 |

- 위 표는 서로 충돌한다(Ashby 82% 채용 대 JOLTS 기반 약 30% 무채용).
- 공고가 채용 없이 닫혔다고 곧 유령 공고는 아니라고 Ashby가 단서를 붙였다는 요약이 있다. [검색발췌]
- 유령 공고에 지원했을 때의 응답률(콜백 확률)을 직접 잰 연구는 찾지 못했다. 근거 없음.
- 오래 열린 공고·재게시·상시 채용 공고에 대한 응답률 연구도 찾지 못했다. 근거 없음.
- Davis·Faberman·Haltiwanger는 JOLTS 사업장 단위 자료로 "recruiting intensity" 지수를 만들었다.
  - 요약: 채용률(fill rate)은 고용주 성장률에 따라 가파르게 오르고, 규모가 클수록 떨어지며, 산업별로 약 4배 차이난다. 지수가 표준 매칭 함수의 붕괴를 부분 설명한다.
  - 출처: Davis, Faberman, Haltiwanger, "The Establishment-Level Behavior of Vacancies and Hiring", NBER WP 16265 (2010), QJE 128(2), 2013. https://www.nber.org/papers/w16265 [열람 — 초록 요약]
  - 미충원 기간이 길수록 요건을 낮추는지(선별 기준 완화)는 이 열람 범위에서 확인되지 않았다. 검색 요약도 확인하지 못했다고 했다.
- 한국 자료: 유령 공고·time-to-fill 자료는 찾지 못했다.

### 4. 요건 충족 정도 — 일부만 충족, 연차 범위 밖, 과잉 자격

- "남성은 자격요건 60%를 충족하면 지원하고 여성은 100%를 충족해야 지원한다"는 통념의 출처는 불명확하다.
  - HBR 글은 "Men apply for a job when they meet only 60% of the qualifications, but women apply only if they meet 100% of them."이라 쓰고 출처를 달지 않았다고 확인됐다.
  - 출처: Tara Mohr, HBR "Why Women Don't Apply for Jobs Unless They're 100% Qualified", 2014. https://hbr.org/2014/08/why-women-dont-apply-for-jobs-unless-theyre-100-qualified [열람 — 해당 문장에 출처 표기 없음]
  - 검색 요약은 Hewlett Packard 내부 보고서에서 왔다고 전하나 원 보고서는 확인하지 못했다. [검색발췌]
  - 이 통념은 지원 행동에 대한 것이고 콜백 확률에 대한 데이터가 아니다.
- "요건의 몇 %를 충족해야 콜백이 오는가"를 실증한 데이터는 찾지 못했다. 근거 없음.
- 요구 연차 범위 밖 지원의 콜백 데이터도 찾지 못했다. 근거 없음.
- 과잉 자격은 벨기에 현장실험에서 불이익이 아니라 이득으로 나왔다.
  - 요약: 과잉 자격 석사 졸업생이 면접 직접 초대 확률 19%, 어떤 긍정 반응이든 받을 확률 11% 더 높았고, 병목 직종에서 이득이 더 컸다.
  - 출처: Verhaest et al., "Do Employers Prefer Overqualified Graduates? A Field Experiment", Industrial Relations 2018. https://onlinelibrary.wiley.com/doi/full/10.1111/irel.12212 [검색발췌] (원문 fetch 403)
  - 한 나라·졸업생 대상 실험이다. 과잉 자격 불이익을 보인 다른 실험은 이번에 찾지 못했다.
- 일반 콜백 편차: 이력서 감사 연구에서 같은 경력이라도 학위 유무·기관 유형에 따라 콜백이 달랐다.
  - 요약: 영리 온라인 기관 경영학사는 비선택적 공립 기관 대비 콜백 22% 낮았다.
  - 출처: Deming et al., "The Value of Postsecondary Credentials in the Labor Market: An Experimental Study", AER 2016 (NBER w20528). https://www.nber.org/papers/w20528.pdf [검색발췌]
- 실업 기간과 콜백: 콜백률이 실업 첫 8개월 동안 빠르게 떨어지고 이후 안정된다는 요약이 있다.
  - 출처: NBER WP 21689 "Factors Determining Callbacks to Job Applications by the Unemployed: An Audit Study" (저자·연도는 검색 결과에서 미확인). https://www.nber.org/system/files/working_papers/w21689/w21689.pdf [검색발췌]
  - 지원자 쪽 요인이며 공고 쪽 요인은 아니다. 참고로만 둔다.
- 공고별 과제 특성에 따라 콜백 격차가 달라진다는 대규모 감사 프리프린트가 있다.
  - 요약: 9,220개 공고, 36,880건 지원. "Subjective evaluation widens callback gaps while objective precision compresses them."
  - 출처: arXiv 2604.01933 "Hiring Discrimination and the Task Content of Jobs: Evidence from a Large-Scale Resume Audit", 2026. https://arxiv.org/abs/2604.01933 [검색발췌] (프리프린트, 동료심사 여부 미확인)
  - 공고의 성격(재량이 큰 직무인지)에 따라 같은 지원자의 콜백 양상이 달라질 수 있음을 시사하는 사실이다. 요건 충족 비율을 직접 다룬 것은 아니다.

### 5. 필수 vs 우대 요건의 무게, 요건 개수와 선별 엄격성

- 필수·우대 요건의 실제 무게를 잰 연구는 찾지 못했다. 근거 없음.
- 공고에 나열된 요건 개수와 선별 엄격성의 관계를 잰 연구도 찾지 못했다. 근거 없음.
- 공고문 요건은 실제 지원자의 특성과 정렬되어 있다는 결과가 있다: "Job ad requirements are aligned with their applicants' traits, as predicted in directed search models with heterogeneity." (칠레 자료)
  - 출처: Banfi & Villena-Roldán 2019 (위와 동일). [검색발췌]
- Hidden Workers 보고서의 2차 보도: 고용주 다수가 job description에 정확히 맞지 않는 자격 있는 지원자가 걸러진다고 인정했다는 서술이 있다.
  - 출처: Fuller et al., HBS·Accenture "Hidden Workers: Untapped Talent", 2021. 원문 PDF 위치는 검색 결과의 nahr.shrm.org/sites/default/files/hiddenworkers09032021.pdf (열람 실패, 리다이렉트). 2차 보도 https://www.hrdive.com/news/report-applicant-tracking-systems-may-exclude-whole-segments-of-candidates/606614/ [검색발췌]
  - 설문(구직자 8,720명·임원 2,275명, 미·영·독) 기반 자기보고다. 검색 결과 간에 "88%"의 의미가 달라 원문 확인 전에는 인용하지 않는다. 원문 PDF는 열람하지 못했다(리다이렉트).

### 6. 고용주 특성 — 규모·성장 단계, 노동시장 여건

- 노동시장 여력과 요건 상향: 대침체기 공고의 학력·경력 요건이 올랐고, 노동 공급이 더 늘어난 주·직종에서 더 크게 올랐다.
  - "Using a proprietary database of online job postings, we find that education and experience requirements rose during the Great Recession." 2007–2010 요건 상승의 18–25%를 실업자 증가가 설명한다.
  - 출처: Modestino, Shoag, Ballance, "Upskilling: Do Employers Demand Greater Skill When Workers Are Plentiful?", Review of Economics and Statistics 102(4), 2020 (Boston Fed WP 14-17). https://econpapers.repec.org/RePEc:tpr:restat:v:102:y:2020:i:4:p:793-805 [검색발췌] (PDF fetch 시도했으나 바이너리로 읽지 못함)
  - 워킹페이퍼 버전은 수치가 다르다(약 30%라는 요약도 있음). 출판본 수치를 쓴다.
- 반대 해석: 요건 상승이 일시적 기회주의가 아니라 생산 구조 재편이며 경기 회복 후에도 유지됐다.
  - 출처: Hershbein & Kahn, "Do Recessions Accelerate Routine-Biased Technological Change? Evidence from Vacancy Postings", AER 108(7), 2018 (NBER w22762). https://www.nber.org/papers/w22762.pdf [검색발췌]
  - 두 연구는 요건 상승의 원인 해석이 다르다. 둘 다 미국 대침체기 자료다.
- 반대 방향(구인난일 때 요건 완화, downskilling)을 직접 잰 연구는 이번에 확인하지 못했다. 위 Modestino 연구가 대칭이라는 암시만 있고 이번에 검증하지 않았다.
- Indeed Hiring Lab: 시니어 공고(약 5년 이상 경력) 비중은 약 14%로 2026.5 기준 전년 대비 약 14.7% 증가했고, 신입 공고(0–1년)는 약 46%로 2022년 정점 이후 감소했다.
  - "only about 14% of postings are for senior positions nationwide". 
  - 출처: Indeed Hiring Lab, "The labor market is tilting toward seniority", 2026-07-23. https://hiringlab.indeed.com/2026/07/23/the-labor-market-is-tilting-toward-seniority/ [열람] (벤더 데이터, 방법론은 해당 글이 연결)
  - 공고 요구 연차 분포의 시장 수준 사실이다. 콜백과의 관계는 아니다.
- 회사 규모·스타트업 대 대기업의 서류 선별 엄격성 비교는 찾지 못했다. 근거 없음.
- Davis 등: 사업장이 클수록 채용률(fill rate)이 낮다는 결과는 위 3절에 있다. [열람 — 초록 요약]

### 7. 채용 담당자의 서류 심사 방식

- 아이트래킹: Ladders 2012 연구는 이력서 초기 검토에 평균 6초, 2018 갱신판은 7.4초를 보고했다.
  - "Job recruiters spend only six seconds on average reviewing an individual candidate's resume"; 시간의 약 80%가 이름, 현재·이전 직함과 회사, 재직 기간, 학력에 쓰였다.
  - 출처: TheLadders (벤더) 보도 https://www.recruiter.com/i/theladders-reveals-research-reporting-that-resumes-spend-six-seconds-with-a-recruiter/ , 2012 [검색발췌]
  - 표본 약 30명이고, 비판(소규모, 오래됨)이 있다는 요약이 있다. 방법 공개 정도는 확인하지 못했다.
- ATS 사용: Hidden Workers 보고서는 RMS를 쓰는 고용주의 90% 이상이 1차 선별·순위에 이를 쓴다고 했다(중숙련 94%, 고숙련 92%라는 2차 요약).
  - 출처: 위 5절과 동일. [검색발췌]
  - 자기보고 설문이다. knockout 질문의 빈도 자체는 이번에 찾지 못했다.
- KR: 사람인 인사담당자 262명 조사에서 86.6%가 서류 실수를 탈락 처리하며, 가장 치명적인 실수는 자격조건 미달(42.3%)이었다. 출처: 캠퍼스 잡앤조이 기사(원 URL 미확보, 연도 2010년대). [검색발췌]
- KR: 잡코리아 인사담당자 794명 설문에서 60.3%가 스펙이 충분해도 자기소개서 문제로 서류 탈락시킨 경험이 있다고 했다. 출처: 메트로신문 https://www.metroseoul.co.kr/article/2014091700182 , 2014. [검색발췌]
- KR: 잡코리아 설문에서 인사담당자 59.8%가 불합격 통보를 하지 않는다고 답했다. 출처: https://www.superookie.com/contents/5cef6e508b129f61482e826e , 연도 미확인. [검색발췌]
- 한국 설문은 모두 벤더(구직 사이트) 자료이며 표본 추출·측정 방법 공개 여부는 확인하지 못했다.

### 근거가 약하거나 찾지 못한 것

- 지원 시점(게시 후 경과 일수)과 콜백의 관계: 동료심사·1차 자료 없음. 블로그·벤더 수치뿐이고 출처 불명이다.
- "일찍 지원하면 유리하다"의 원 출처: 특정하지 못함.
- 공고당 지원자 수와 개별 콜백 확률: 직접 근거 없음. Gee는 지원 행동만 측정한다.
- 유령·장기·재게시·상시 공고에 지원했을 때의 응답률: 근거 없음. 유령 공고 비율 추정은 정의별로 충돌한다.
- 미충원 기간이 길수록 요건을 낮추는지: 이번에 확인하지 못함.
- 요건 N% 충족 시 콜백, 요구 연차 범위 밖 지원, 필수·우대 무게, 요건 개수와 엄격성: 근거 없음.
- 과잉 자격의 콜백 불이익: 찾은 현장실험(벨기에)은 이득을 보고한다. 불이익 근거는 못 찾음.
- 회사 규모·스타트업 대 대기업 선별 엄격성, ATS knockout 질문의 빈도: 근거 없음.
- IT·개발 직군 전용 자료: 없음. 한국 자료는 2010년대 설문 기사뿐이며 지원 시점 자료는 없다.
- 열람한 것은 Gee 초록, NBER w16265 초록 요약, HBR Mohr 글, Indeed Hiring Lab 글뿐이다. 나머지는 모두 검색 요약이며 원문 대조가 필요하다.

## 논의 문서로 가져가는 것

- 공고 게시 후 경과 시간과 콜백의 관계를 재는 동료심사 연구는 찾지 못했다.
- 초기 지원이 유리하다는 수치(12.7% 대 1.8% 등)는 출처·측정이 불명인 블로그 자료다.
- Gee의 LinkedIn 실험에서 지원자 수 표시는 지원 완료 확률을 3.5% 높였고, 경험이 적은 구직자·덜 알려진 회사에서 효과가 컸다(요약 기준).
- 지원자 수 정보의 효과는 지원 행동에 대한 것이며 콜백 확률에 대한 증거가 아니다.
- 유령 공고 비율 추정은 정의에 따라 약 18~38% 사이로 갈리며, 대부분 벤더·2차 자료다.
- 유령 공고 응답률을 직접 잰 근거는 찾지 못했다.
- 노동 공급이 많을 때 요건이 오른다는 증거(Modestino 등 2020)와 그것이 구조적 재편이라는 해석(Hershbein·Kahn 2018)이 공존한다.
- "남성 60% 대 여성 100%" 통념은 HBR 원글에도 출처가 없고 지원 행동에 대한 서술이다.
- 요건 일부 충족자의 콜백 확률을 잰 데이터는 찾지 못했다.
- 벨기에 현장실험(Verhaest 등 2018)에서 과잉 자격 석사 졸업생은 면접 초대가 19% 더 많았다(요약 기준).
- 이력서 초기 검토 시간은 6~7초대라는 벤더 아이트래킹 수치가 있고 표본은 작다.
- 한국 인사담당자 설문에서 자격조건 미달이 서류 탈락 사유 1위(42.3%)로 나온 것이 있으나 벤더 설문이며 연도가 오래됐다.
