---
type: discussion
kind: survey
goal: jobseeker-company-matching
topic: careerhub
subjects: []
status: active
related: []
---

# 이력서–채용공고 매칭 제품 사례와 사용자 반응 — 조사 (2026-11-14)

## 질문

실제 제품들은 이력서와 채용공고를 어떻게 맞춰 주고 있는가.
무엇을 입력으로 받고 무엇을 출력하는가.
구직자와 기업은 그것을 어떻게 받아들였는가.
이 조사는 결론이나 기능 제안 없이 사실과 근거만 모은다.
도구는 WebSearch·WebFetch만 썼고 로컬 저장소는 읽지 않았다.
표기: [직접확인] 해당 URL을 열어 문장을 확인함. [검색요약] 검색 결과 요약으로만 접함. [미확인] 확인하지 못함.
제품 기능은 자주 바뀌므로 각 항목에 자료 날짜를 적었다.

## 조사

### 제품별 비교표

| 제품 | 입력 | 출력 | 과금 | 알려진 반응·효과(출처 성격) |
|---|---|---|---|---|
| LinkedIn | 프로필, 이력서, 공고 자격, 스크리닝 질문 | 매칭 수준, Top Applicant(Premium), 부족 자격 요약 | 구직자 Premium 구독 | 부적격 지원 억제가 목표(자사). 정확도의 독립 평가 없음 |
| Indeed | 공고 내용, 이력서 DB | 매칭 후보 목록, 초대 이메일 | 구독 + contact 상한, 초과 건당 | "17배 더 지원"(자사 마케팅, 측정법 미표기) |
| ZipRecruiter | 설문, 이력서, 거절 피드백, 고용주 thumbs-up | 4단계 매치 표시, 이력서 전달 | 고용주 구독(세부 미확인) | 부적합 지원 47% 감소(자사 2021, 미검증) |
| Hired | 후보 프로필, 기업 입찰 | 기업이 후보에게 제안 | [미확인] | 청산 보도, 경기 취약 주장(제3자 블로그) |
| Wellfound | 프로필, 연봉·지분·단계 선호 | 기업의 직접 연락, AI 소싱 | 채용자 구독·대행(세부 미확인) | 제3자 리뷰뿐 |
| Triplebyte | 기술 평가 결과 | 평가 기반 기업 소개 | [미확인] | 2023-03 마켓플레이스 종료, 평가 기술만 Karat 이전 |
| Otta/WTTJ | 선호 설문, 행동 | 선호 기반 추천 | [미확인] | 2024-01 WTTJ 인수, 브랜드 흡수 |
| 잡코리아 | 클릭·검색·성향 데이터 | 공고 추천, 인재 추천, 적합도·서류합격 예측 | [미확인] | 지원 +104%(자사 2025-10) |
| 사람인 | 대화, 이력서 | 공고 추천, 서류합격 코칭 | [미확인] | 사용량 +165.5%(자사) |
| 원티드 | 이력서, 행동 데이터 | AI 합격 예측, 포지션 추천 | [미확인] | 마케팅 문구만 확인 |

### LinkedIn

**Job Match·Top Applicant**
- 출처: LinkedIn Help, "Find how you match up with jobs on LinkedIn", https://www.linkedin.com/help/linkedin/answer/a7120158 (연도 미표기, 2026-11 조회) [직접확인].
- 인용: "Premium members will receive a job match level to see how they compare against other applicants".
- 인용: Premium 회원은 "can receive a Top Applicant rating if they have a higher chance of hearing back from the job poster."
- 입력은 프로필, 이력서, 공고의 필수·우대 자격, 채용자의 스크리닝 질문이다(같은 페이지).
- Top Applicant의 임계 기준(10명 이상 공고에서 상위 50%)은 제3자 글에만 있다 [미확인].

**출시 보도**
- 출처: Engadget, "LinkedIn wants you to apply for fewer jobs", 2025-01-15, https://www.engadget.com/social-media/linkedin-wants-you-to-apply-for-fewer-jobs-140049139.html [직접확인].
- 인용: 목표는 "help surface the jobs a person is most qualified for and discourage people from applying to roles they aren't".
- 인용: 채용 담당자들이 "practically begging unqualified applicants to stop flooding their inboxes"라는 설명이 있다.
- 이 설명은 LinkedIn 측 주장을 옮긴 것이다.

**Qualified Applicant 모델**
- 출처: LinkedIn Engineering, "Quality matches via personalized AI for hirer and seeker preferences", 2020-07-30, https://www.linkedin.com/blog/engineering/ai/quality-matches-via-personalized-ai [직접확인].
- 인용: 모델은 지원 시 "predict the probability of a positive recruiter action"을 목표로 한다.
- 전역 모델과 회원별·공고별 모델을 결합하고 개인화 부분은 매일 재학습한다.
- 라벨은 채용자 반응이다.
- 보고된 결과는 오프라인 AUC +27%와 채용자 상호작용률의 두 자릿수 증가이며 자사 보고다.
- 이 모델이 Top Applicant와 같은 것이라고 LinkedIn이 명시한 문서는 찾지 못했다 [미확인].

**구직자 반응**
- 개인 Medium 글이 Top Applicant 배지와 Show Match Details가 어긋난 사례를 보고했다(https://medium.com/@estrellakuo/linkedin-premium-a-closer-look-at-top-applicant-and-job-match-features-e7ad4e71bbcb) [검색요약, 단일 사례].
- Slashdot 토론은 냉소적 반응이 많았다(https://tech.slashdot.org/story/25/01/15/1858257, 2025-01) [검색요약, 일화].
- 신뢰·정확도에 대한 독립 조사는 찾지 못했다.

### Indeed

- 출처: Indeed Hire, "Matched Candidates", https://www.indeed.com/hire/matched-candidates (연도 미표기) [직접확인].
- 입력은 공고 내용이고 이력서 DB를 검색해 후보를 대시보드에 띄운다.
- 출력은 매칭 후보와 초대 이메일이다.
- 인용(마케팅 주장): "Candidates you invite to apply are 17 times more likely to apply to your job than those who only see it in search."
- 구독 등급별 contact 상한이 있고 초과분은 구매한다. 세부 가격은 이 페이지에 없다.
- Staffing Industry Analysts는 Indeed가 pay-per-application 가격을 중단한다고 보도했다(2023-12, https://www.staffingindustry.com/Editorial/Industrial-Staffing-Report/Dec.-21-2023/Indeed-is-pulling-pay-per-application-pricing) [검색요약].
- 중단 이유는 확인하지 못했다 [미확인].

### ZipRecruiter

- 출처: ZipRecruiter, "Who is Phil", https://ZipRecruiter.Com/who-is-phil [검색요약].
- Phil은 경험·관심사·커리어 목표를 보는 여러 알고리즘으로 일자리를 정하고, 고용주에게 이력서를 제시한다.
- 고용주가 지원서를 보거나 thumbs up을 주면 알림을 준다.
- 2021 보도자료는 Great/Good/Fair/Not a Match 표시가 부적합 공고 지원을 평균 47% 줄였다고 주장한다(https://www.businesswire.com/news/home/20210319005398/en) [검색요약, 원문 403, 자사 주장].

### Hired·Wellfound·Triplebyte

- 출처(Hired): Underdog.io 블로그, 2025-10-14, https://underdog.io/blog/the-rise-and-fall-of-vettery-and-hired [직접확인, 관련 업체 블로그].
- 인용: "Hired was burning cash."
- 인용: "The 'reverse auction' model loses its appeal when jobs are scarce."
- 재무 근거는 글에 없다.
- 출처(Wellfound): https://wellfound.com/about [검색요약].
- 스타트업이 후보에게 직접 연락하는 구조이고 AI 소싱(Reach)·대행(Autopilot) 상품이 있다.
- 매칭 점수 산정 방식은 확인하지 못했다 [미확인].
- 출처(Triplebyte): Karat 인수 발표, 2023-03-16, https://www.businesswire.com/news/home/20230316005225/en [검색요약, 원문 403].
- Karat이 평가 기술과 팀을 인수했고 후보 마켓플레이스는 2023-03-31 종료됐다는 요약이다.
- 폐업 원인의 1차 설명은 찾지 못했다 [미확인].

### Otta / Welcome to the Jungle

- 출처: WTTJ 보도자료, 2024-01, https://press.welcometothejungle.com/news/uk-recruitment-platform-otta-acquired-by-welcome-to-the-jungle [검색요약].
- Otta는 선호·기술·가치 기반 매칭 서비스였고 2024-01 WTTJ가 인수했다.
- WTTJ 고용주 페이지는 공고 데이터에 행동·의도 신호를 결합한다고 설명한다(https://employers.welcometothejungle.com/uk/solutions/matching) [검색요약, 마케팅 설명].
- 후보에게 보이는 점수·이유의 형태는 확인하지 못했다 [미확인].

### 국내

**잡코리아**
- 출처: 디지털인사이트, "입사지원 두 배 증가 잡코리아 AI 추천 2.0 성과 공개", 2025-10-20, https://ditoday.com/입사지원-두-배-증가-잡코리아-ai-추천-2-0-성/ [직접확인].
- 인용: "구직자들의 한달 간 입사 지원 수가 104% 증가했다."
- 인용: "실제 입사 지원 전환율은 50%를 상회한 것으로 나타났다."
- 입력은 "2700만 구직자와 244만 기업의 클릭, 검색, 구인구직 성향 등"이다.
- 회사 발표이며 독립 검증이 없다.
- 지원 증가가 매칭 품질 향상의 증거인지는 이 자료로 알 수 없다.
- 원픽이 기업에 적합도 평가·서류합격 예측을 제공한다는 보도가 있다(https://ditoday.com/?p=125273) [검색요약].

**사람인**
- 2026-03 '커리어 매칭 에이전트', 2026-05 'AI 서류합격 코칭' 출시 보도(https://m.ddaily.co.kr/page/view/2026070815521328429) [검색요약].
- 사용량 전월 대비 165.5% 증가는 회사 발표다.

**원티드**
- 원티드랩 인재풀 페이지가 "실시간 AI 합격 예측 서비스"를 소개한다(https://www.wanted.co.kr/events/talentpool) [검색요약, 마케팅 주장].
- 점수·등급의 노출 형태는 확인하지 못했다 [미확인].

**리멤버·점핏·프로그래머스·로켓펀치**
- 조사하지 못했다 [미확인].

### 구직자용 일치도 검사와 지원 폭주

- Jobscan이 일치율 75~80%를 권장한다는 서술은 제3자 인용이다 [검색요약].
- Rezi의 ATS myths 페이지는 점수가 최적화 도구일 뿐이라고 한다(https://www.rezi.ai/posts/ats-myths) [검색요약].
- Teal·Jobscan 1차 문서는 열지 못했다 [미확인].
- Enhancv가 채용 담당자 25명을 조사해 92%가 ATS는 자동 탈락시키지 않는다고 답했다(https://itbrief.co.uk/story/study-reveals-ats-rarely-auto-rejects-cvs-debunks-75-myth) [검색요약, 표본 작음, 이해관계 업체].
- Greenhouse 인용: "In the first quarter of 2024, our customers received an average of 222 applications per job opening," 2021년 말의 거의 3배(https://www.greenhouse.com/uk/blog/ai-has-doubled-recruiters-workloads, 2024) [직접확인, 자사 고객 데이터].
- 자동 지원 도구가 맞춤 이력서로 대량 지원한다는 보도가 있다(https://www.nbcnewyork.com/news/tech/ai-is-supposed-to-make-applying-to-jobs-easier-but-it-might-be-creating-another-problem/5992986/) [검색요약].
- 일치도 도구나 LLM이 폭주에 얼마나 기여했는지의 정량 근거는 찾지 못했다 [미확인].

### 점수 표시와 구직자 행동

- 공개된 효과 수치는 거의 전부 사업자 자체 주장이다(ZipRecruiter 47%, 잡코리아 +104%, Indeed 17배).
- AEA 2024 발표(7,837명 무작위)는 거절 메시지에 fit 사유를 주면 재지원의 성별 격차가 줄 수 있다고 한다(https://aeaweb.org/conference/2024/program/paper/ssSYbRBb) [검색요약, 초록 미열람].
- 이 연구는 사전 점수 표시가 아니라 거절 문구의 효과다.
- Gee의 LinkedIn 실험(200만 명 이상)에서 이전 지원자 수 표시가 지원 시작 확률을 1.9~3.9% 높였다(https://conference.nber.org/conf_papers/f93759/f93759.pdf) [검색요약].
- 매칭 점수가 과도한 자기 선별을 일으키는지를 직접 측정한 공개 연구는 찾지 못했다 [미확인].

### 기업 쪽 수용과 자동 심사

- 출처: Fuller·Raman 외, "Hidden Workers: Untapped Talent" (HBS·Accenture), 2021-09. 보고서 원문은 열지 못했다 [미확인].
- TechRadar가 인용한 문장: "A large majority (88%) of employers agree, telling us that qualified high-skills candidates are vetted out of the process because they do not match the exact criteria established by the job description." (https://techradar.com/news/automated-hiring-software-is-rejecting-millions-of-suitable-job-candidates) [검색요약, 페이지 본문은 열리지 않음].
- 88%는 임원 설문의 동의 비율이며 실제 탈락률이 아니다.
- 표본은 숨은 노동자 8,720명과 임원 2,275명(미국·영국·독일)이라는 2차 보도가 있다(https://hbswk.hbs.edu/item/how-to-tap-the-talent-automated-hr-platforms-miss) [검색요약, 403].
- 자동 필터 사용 비율은 출처마다 달라 원문 확인이 필요하다 [미확인].
- 기업이 추천 후보 품질을 어떻게 평가하는지의 독립 자료는 찾지 못했다 [미확인].

### 실패·편향·규제

**Amazon (2018)**
- 출처: Reuters, Jeffrey Dastin, 2018-10-10, CNBC 재게재 https://www.cnbc.com/2018/10/10/amazon-scraps-a-secret-ai-recruiting-tool-that-showed-bias-against-women.html [직접확인].
- 인용: 도구는 "scores ranging from one to five stars"를 부여했다.
- 시스템은 "women's"가 든 이력서를 감점했고 두 여자대학 졸업자도 낮췄다.
- Amazon 직접 인용은 "committed to workplace diversity and equality"이다.
- 과거 10년 이력서(대부분 남성)로 학습했다는 설명은 2차 요약이다.

**UW LLM 이력서 순위 연구 (2024)**
- 출처: UW News, 2024-10-31, https://www.washington.edu/news/2024/10/31/ai-bias-resume-screening-race-gender/ [직접확인].
- 인용: 모델들이 "favored white-associated names 85% of the time".
- 흑인 연상 이름 선호 9%, 남성 52% 대 여성 11%였다.
- 이름 120개, 공고 500개 이상, 300만 건 이상 비교이며 연구용 모델이다. 상용 제품의 결과가 아니다.

**Mobley v. Workday**
- 2025-05-16 N.D. Cal.이 ADEA 집단소송을 예비 인증했다는 보도(https://www.akingump.com/en/insights/ai-law-and-regulation-tracker/district-court-grants-preliminary-certification-of-collective-action-for-discrimination-claim-against-ai-based-system) [검색요약, 원문 403].
- 대리인 이론으로 벤더 책임을 다룬다는 요약이다.
- 이후 경과와 본안 결과는 확인하지 못했다 [미확인].

**NYC Local Law 144**
- 출처: DLA Piper, 2026-01-30, 뉴욕주 감사원 보고서(2025-12) 해설, https://www.dlapiper.com/insights/publications/2026/01/critical-audit-of-nyc-ai-hiring-law-signals-increased-risk-for-employers [직접확인].
- 감사는 집행이 "ineffective"라고 결론지었다.
- 인용: "75 percent of test calls made to the New York City 311 hotline regarding AEDT issues were improperly routed and never reached the DCWP."
- DCWP는 32건 감사를 검토해 "only one issue of non-compliance"를 찾았고 감사원은 "at least 17 potential issues"를 찾았다.
- 과태료 액수는 출처마다 달라 확인하지 못했다 [미확인].

**EU AI Act**
- 지원서 분석·필터링과 후보 평가가 Annex III 고위험으로 분류된다는 서술이 다수 2차 자료에 있다.
- Digital Omnibus로 적용일이 2026-08-02에서 2027-12-02로 미뤄졌다는 보도가 있다(https://datamatters.sidley.com/2026/06/22/eu-lawmakers-reach-provisional-agreement-to-delay-key-eu-ai-act-obligations/, 2026-06) [검색요약].
- 최종 채택 여부는 자료가 엇갈린다 [미확인].
- 법령 원문은 열지 않았다.

**한국**
- AI 기본법이 2026-01 시행됐고 채용이 고영향 AI 영역의 예로 거론된다는 보도(https://v.daum.net/v/20260304084731731, 2026-03) [검색요약].
- 사람의 실질 검토가 있으면 제외될 수 있다는 해설이 있다.
- 개인정보 보호법상 자동화된 결정 설명 요구는 완전 자동화 결정에만 작동한다는 블로그 해설이 있다 [검색요약, 법령 원문 미확인].
- 조문·시행령·개인정보위 지침은 확인하지 못했다 [미확인].

### 수익 모델과 매칭 품질

- Indeed는 구독·contact 과금(Smart Sourcing)과 시작된 지원당 과금(Sponsored Jobs)을 함께 운영한다(Indeed 절의 출처).
- LinkedIn Qualified Applicant의 학습 라벨은 채용자 반응이다(LinkedIn 절의 출처).
- 과금 방식이 매칭 품질에 미치는 영향을 직접 다룬 1차 자료는 찾지 못했다 [미확인].

### 근거가 약하거나 찾지 못한 것

- Hidden Workers 보고서 원문과 HBS 페이지 본문(403). 수치는 2차 보도 기준이다.
- Business Wire 원문(Triplebyte·ZipRecruiter)과 Akin Gump 페이지(403).
- Top Applicant의 정확한 기준과 Job Match 점수 산정 방식.
- Job Match의 신뢰·정확도에 대한 독립 조사와 기업 측 추천 후보 품질 평가.
- 점수 표시가 자기 선별을 유도하는지에 대한 직접 실험.
- Teal·Rezi·Jobscan 1차 문서.
- Triplebyte 폐업 원인, Wellfound·Otta의 매칭 세부, Hired·Triplebyte·국내 3사의 과금 구조.
- 리멤버·점핏·프로그래머스·로켓펀치, 사람인·원티드의 점수 노출 형태.
- 국내 법령 조문과 지침, EU Digital Omnibus 최종 채택, Mobley 이후 경과.
- LLM 대량 지원의 정량 기여.
- 사업자 효과 수치는 전부 자사 발표이며 독립 검증이 없다.

## 논의 문서로 가져가는 것

- LinkedIn의 지원 시 예측 대상은 채용자의 긍정 반응 확률이다(2020 엔지니어링 블로그).
- LinkedIn은 부적격 지원을 줄이는 것을 Job Match의 목표로 밝혔다(2025-01 Engadget).
- Indeed의 매칭 후보 상품은 구독과 contact 상한으로 과금한다(Indeed Hire 페이지).
- 사업자가 공개한 효과 수치(47%, 17배, +104%)는 전부 자사 발표이고 독립 검증이 없다.
- Greenhouse 고객의 공고 1건당 평균 지원 수는 2024 Q1에 222건이다.
- Hidden Workers 보고서의 88%는 임원의 동의 비율이다(2차 보도).
- Amazon의 자체 도구는 학습 데이터 편향 문제로 폐기됐다(Reuters 2018).
- 연구용 LLM 3종은 이력서 순위에서 백인 연상 이름을 85% 선호했다(UW 2024).
- NYC LL144 집행은 2025-12 감사에서 비효과적이라고 평가됐다.
- 한국은 2026-01 AI 기본법 시행 중이며 채용 적용 범위와 계도기간은 2차 자료로만 확인했다.
- 점수 표시가 자기 선별에 미치는 영향의 직접 실험은 찾지 못했다.
