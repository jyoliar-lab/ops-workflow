---
type: discussion
kind: survey
goal: jobseeker-company-matching
topic: careerhub
subjects: []
status: active
related: []
---

# 이력서–채용공고 매칭 기법 — 조사 (2026-11-14)

## 질문

이력서와 채용공고를 맞춰 보는 기법에는 어떤 것이 있고, 각각 무엇을 잘하고 무엇에 실패하는가를 학술·기술 관점에서 알고자 했다.
직군·국가는 좁히지 않았다.
결론이나 기능 제안 없이 사실과 근거만 모은다.

## 조사

### 0. 읽기 전에 — 출처 신뢰도 규칙

이번 조사의 도구는 WebSearch와 WebFetch뿐이다.
WebFetch는 페이지를 작은 모델로 요약해 돌려주므로 초록 원문을 그대로 얻지 못한 경우가 많다.
그래서 "인용"은 두 종류로 구분한다.

- **[인용]**: 도구 결과에 따옴표로 원문이 확인된 문장.
- **[요약]**: 도구가 바꿔 말한 내용. 원문 대조가 필요하다.

논문 PDF를 직접 읽은 것은 하나도 없다.
전부 초록·검색 스니펫·블로그 본문 수준이다.
"미확인"은 직접 열어 확인하지 못했다는 뜻이다.
26xx 번호 arXiv·2026년 논문은 검색 결과에 나온 그대로 적었고 독립 검증하지 못했다.

### 1. 기법의 계보와 기법별 비교

#### 1.1 비교표

| 기법 | 입력 | 강점 | 실패 양상 | 근거 |
|---|---|---|---|---|
| 키워드·불리언 일치 | 공고·이력서의 문자열 | 빠르고 설명이 쉽다. 트라이 기반 태거를 LinkedIn이 실사용 | 분류 체계가 표현을 다 덮어야 한다. 동의어·암묵 표현을 놓친다 | 2.1 |
| TF-IDF/BM25 | 텍스트 | 하이브리드 검색의 한 축으로 쓰임 | 단독 한계를 보고한 1차 자료는 못 찾음 | 2.3(미확인) |
| 기술 온톨로지 (ESCO, LinkedIn Skills Graph) | 추출 기술을 정규형으로 매핑 | 동의어 통합, 상하위·형제 관계로 확장 | 수동 유지는 신조어에 뒤처진다는 지적 | 2.1, 2.2 |
| 임베딩 유사도 (two-tower 등) | 텍스트·행동 신호 → 벡터 | 의미 유사 검색, 대규모 검색 | 이름·길이·빈도 같은 비의도 요인에 편향 | 2.3, 5.1 |
| 학습 기반 person-job fit (PJFNN 등) | 과거 지원 기록의 공고·이력서 쌍 | 공고 요구사항 중 후보가 충족하는 것을 학습 | 라벨이 과거 의사결정에 의존 | 1.3, 4 |
| 상호 추천 (reciprocal) | 양방향 선호 예측 | 매치 라벨 희소성 보완 시도 | 방향별 예측을 합치면 오차가 전파된다는 주장 | 3.1 |
| LLM 매칭·평가·생성 | 이력서·공고 원문 | 문맥 이해, 설명·생성 | 위치·이름 편향, 비일관성, 프롬프트 주입, 자기선호 | 5 |

#### 1.2 서베이

- Qin et al., "A Comprehensive Survey of Artificial Intelligence Techniques for Talent Analytics", arXiv 2307.03195, 2023. https://arxiv.org/abs/2307.03195
  [요약] 딥러닝이 person-job fit의 새 패러다임을 열었다고 서술. 검색 스니펫 수준, 미확인.
- Otani, Bhutani, Hruschka, "Natural Language Processing for Human Resources: A Survey", arXiv 2410.16498, 2024(2025-03 개정). https://arxiv.org/abs/2410.16498
  [인용] "Advances in Natural Language Processing (NLP) have the potential to transform HR processes."
- Tang et al., "Explainable Person–Job Recommendations: Challenges, Approaches, and Comparative Analysis", Frontiers in AI, 2025. https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1660548/full
  검색 결과에 provisionally accepted로 표시. 본문 미확인.

#### 1.3 학습 기반 person-job fit

- Zhu et al., "Person-Job Fit: Adapting the Right Talent for the Right Job with Joint Representation Learning" (PJFNN), ACM TMIS, 2018, arXiv 1810.04040. https://arxiv.org/abs/1810.04040
  [요약] CNN 기반으로 과거 지원 이력에서 공동 표현을 학습하고, 후보가 충족하는 공고 요구사항을 식별한다. 수치 미확인.
- APJFNN(계층적 attention)은 1차 자료를 열지 못했다. 미확인.

### 2. 기술(skill) 추출과 정규화

#### 2.1 LinkedIn Skills Graph 추출 파이프라인

- 출처: LinkedIn Engineering, "Extracting skills from content to fuel the LinkedIn Skills Graph", 2023. https://www.linkedin.com/blog/engineering/skills-graph/extracting-skills-from-content
- [요약] 문서를 섹션으로 분할(어느 섹션에 나오느냐가 가중치에 영향)하고, 트라이 태거와 multilingual BERT 기반 two-tower 의미 태거를 병행하고, Skills Graph의 부모·자식·형제 관계로 확장하고, 정규형으로 매핑한다.
  예: "data analytics"와 "data analysis"를 같은 기술로 본다.
- [요약] 트라이 태거는 빠르지만 분류 체계가 모든 표현을 덮는 데 의존한다고 서술.
- [인용] "Knowledge Distillation reduces the model size by 80% without compromising performance."
- 보고된 A/B 수치 (기업 블로그 자기보고):
  - 채용 추천: 지원자 +0.1391%, 예측 확정 채용 +0.4606%.
  - 직무-회원 기술 매칭: 적격 지원 +0.87%, 적격 지원율 +0.40%, 예측 확정 채용 +0.24%.
- 주의: "predicted confirmed hires"는 모델 예측값이지 관측된 채용이 아니다.

#### 2.2 ESCO 기반 추출·정규화 연구

- "Efficient Text Encoders for Labor Market Analysis" (ConTeXT-match, Skill-XL), arXiv 2505.24640, 2025. https://arxiv.org/abs/2505.24640
  [요약] 기술 정규화를 극단적 다중 라벨 분류로 보고 bi-encoder + 토큰 수준 대조 손실을 쓴다.
  [인용, 검색 스니펫] "benchmarks for skill extraction have traditionally been formalized as span labeling tasks, without linking the identified spans to respective skills in a taxonomy"
- 암묵 기술: [인용, 검색 스니펫] "need to handle explicit and implicit skill descriptions". 암묵 기술 추론 방법은 구체적으로 못 찾음.
- 제로샷 LLM 추출: ACL Anthology 2025.genaik-1.15 (스니펫만, 미확인).
- 신조어: EACL 2026 industry 논문(aclanthology.org/2026.eacl-industry.65)이 수동 분류 체계 유지의 한계를 다룬다고 함. 미확인.
- 숙련도(proficiency) 추정: 1차 자료가 나오지 않았다. 미확인.

#### 2.3 임베딩·하이브리드

- "Semantic Candidate-Job Matching: A Comparative Evaluation of Dense Embedding Models in Hybrid Retrieval", arXiv 2609.23307. 제목만 확인.
- LinkedIn JUDE: 2차 요약(ZenML)에 따르면 적격 지원 +2.07%, 총 지원 +1.91%, dismiss-to-apply 비율 -5.13%. 재인용, 원문 미확인. https://zenml.io/llmops-database/jude-large-scale-llm-based-embedding-generation-for-job-recommendations
- Indeed 엔지니어링 블로그(2026-06): 검색 질의·클릭·저장·지원 시작을 임베딩으로 묶는다는 설명만 확인. 평가 수치 미확인. https://engineering.indeedblog.com/blog/2026/06/distilling-long-tail-user-behavior-into-scalable-embeddings-for-job-search/

### 3. 양방향성과 쏠림·혼잡

#### 3.1 상호 추천

- Goda, Hayashi, Saito, "A Best-of-Both Approach to Improve Match Predictions and Reciprocal Recommendations for Job Search", arXiv 2409.10992, 2024. https://arxiv.org/abs/2409.10992
  [요약] 직접 매치 예측은 라벨이 극히 희소해 성능이 낮고, 양방향 선호를 따로 예측해 합치면 모델 간 오차 전파가 생긴다고 주장.
  희소하지만 정확한 매치 라벨과 조밀하지만 덜 정확한 예측을 섞은 pseudo-match 점수를 제안.
  오프라인 실험만, 초록에 수치 없음.

#### 3.2 혼잡과 필드 실험

- Le Barbanchon, Hensvik, Rathelot, "How can AI improve search and matching? Evidence from 59 million personalized job recommendations", 2023(WP). https://www.povertyactionlab.org/media/file-research-paper/how-can-ai-improve-search-and-matching-evidence-59-million-personalized
  페이지에서 초록이 안 열렸다. 아래는 검색 요약(IZA 학회판, 최종본과 다를 수 있음).
  - 스웨덴 최대 구인 게시판, 구직자·공고 양쪽 무작위 설계, 클릭 이력 기반 개인화 추천.
  - 추천 노출 후 6개월 고용 +0.7%, 매칭 확률 약 +10%, 추천된 공고에서의 순 고용 효과는 약 2%.
  - 인기 낮은 공고, 지리·직종 범위를 넓히는 추천에서 효과가 컸다.
  - 혼잡 효과는 전체 효과에서 유의한 몫이 아니었다는 세미나 소개 문구(IAB).
- Behaghel, Dromundo, Gurgand, Hazard, Zuber, IZA DP 16781, 2024 (프랑스 La Bonne Boîte 추천기 대규모 실험). https://docs.iza.org/dp16781.pdf
  PDF 파싱 실패. 검색 요약: 구직자를 원래 시장 밖으로 돌리면 여유 있는 시장에서 혼잡이 줄었다. 수치·원문 미확인.
- 충돌: 한쪽은 "혼잡이 유의한 몫이 아니다", 다른 쪽은 "방향 조정으로 혼잡이 줄었다"로 요약돼 있다.
  설계·시장 상황이 달라 직접 비교 불가이며 둘 다 원문 미확인.
- Bied, Crépon et al. (ECML-PKDD FEAST 2021): 최적 수송으로 혼잡 완화. 검색 요약만, 미확인.
- Nandy et al., "A/B Testing for Recommender Systems in a Two-sided Marketplace", arXiv 2106.00762, 2021 (LinkedIn). https://arxiv.org/abs/2106.00762
  [요약] 양면 시장에서 한쪽 처치가 다른 쪽 결과로 번져 SUTVA가 깨진다.

### 4. 정답 라벨 문제

1차 자료를 충분히 확보하지 못한 절이다.

- 지원·클릭·면접·채용·입사 후 성과 중 무엇을 라벨로 쓰는지 비교한 연구는 열어보지 못했다.
- 간접 증거:
  - Goda et al.(3.1): 매치 라벨의 극단적 희소성. [요약]
  - LinkedIn(2.1): 지표가 관측 채용이 아닌 "predicted confirmed hires".
  - Le Barbanchon 실험(3.2): 클릭·매칭 +10% 대비 순 고용 약 2%. 클릭 라벨과 결과 사이의 격차를 시사한다.
- 과거 채용 결정 편향 학습, 노출 편향에 대한 직접 근거는 못 찾았다.

### 5. LLM 기반 심사·매칭 (2023~2026)

#### 5.1 인구통계 편향 — 결과가 충돌한다

- Veldanda et al., "Are Emily and Greg Still More Employable than Lakisha and Jamal? Investigating Algorithmic Hiring Bias in the Era of ChatGPT", arXiv 2310.05135, 2023. https://arxiv.org/abs/2310.05135
  [인용] "Overall, LLMs are robust across race and gender."
  이력서-직종 매칭·요약 과제. 임신 여부·정치 성향에서는 차이. 모델: GPT-3.5, Bard, Claude, Llama.
- Wilson & Caliskan, "Gender, Race, and Intersectional Bias in Resume Screening via Language Model Retrieval", AIES 2024, arXiv 2407.20371. https://arxiv.org/abs/2407.20371
  [요약] 텍스트 임베딩(MTE) 모델, 9개 직종, 500+ 이력서·500+ 공고.
  백인 연상 이름을 85.1%, 여성 연상 이름을 11.1% 사례에서 유의하게 선호.
  흑인 남성은 최대 100% 사례에서 불리. 문서 길이·이름 빈도가 결과에 영향.
  주의: 챗형 LLM이 아니라 임베딩 검색 모델이다. 언론 일부는 "LLM"으로 표기한다.
- Gao, Jiang, Yan (2026 프리프린트, alphaXiv 2606.28978): 14개 LLM 감사, 모델 세대별 편향 방향이 달라졌다고 함. 검색 요약, 동료심사 미확인.
- Armstrong et al., "The Silicone Ceiling: Auditing GPT's Race and Gender Biases in Hiring" (GPT-3.5 대상). 수치 미확인.
- Glazko et al., "Identifying and Improving Disability Bias in GPT-Based Resume Screening", FAccT 2024, arXiv 2402.01732. https://arxiv.org/abs/2402.01732 — 설계만 확인, 결과 수치 미확인.
- FAIRE, arXiv 2504.01420, 2025. 수치 미확인.
- 충돌 정리: Veldanda는 인종·성별 효과가 작다, Wilson & Caliskan은 크다.
  모델 종류(생성 LLM 대 임베딩), 과제, 연도가 다르다.

#### 5.2 일관성·위치·프롬프트 민감도

- Rozado, arXiv 2505.17049 (2025): 22개 LLM 중 대부분이 프롬프트에서 먼저 나온 후보를 고르는 위치 편향.
  후보 라벨을 균형화하면 성별 이름 선호가 사라진다는 보고. 검색 요약. https://arxiv.org/abs/2505.17049
- "Fragile Preferences: A Deep Dive into Order Effects in LLMs", arXiv 2506.14092: 세 항목 비교에서 중간 선택지 선호, 품질이 높으면 초두 편향, 낮으면 후반 선호. 검색 요약. https://arxiv.org/abs/2506.14092
- Varshney & Ganuthula, arXiv 2507.08019: Claude·GPT·Gemini 모두 인간 전문가와 유의하게 달랐고 회사 맥락 민감도가 모델마다 달랐다(GPT 강, Claude 약). 검색 요약. https://arxiv.org/abs/2507.08019
- 동일 이력서 재실행 시 판정이 4~6% 뒤집혔다는 수치는 Noon 블로그(업체, 동료심사 아님, 이력서 70개)다. 약한 근거.
- 같은 이력서 점수가 66~99로 흔들렸다는 보도(hyper.ai)는 1차 확인 못 함.

#### 5.3 이력서 쪽 LLM 작성·키워드 주입

- Xu, Li, Jiang, "AI Self-preferencing in Algorithmic Hiring", AIES 2025, arXiv 2509.00462. https://arxiv.org/abs/2509.00462
  [요약] LLM은 인간이 쓴 이력서보다 자기가 생성한 이력서를 67~82% 선호(버전별로 수치가 다르다는 검색 요약이 있음: v1 68~88%, AIES 초록 68~92%).
  24개 직종 시뮬레이션에서 같은 LLM을 쓴 지원자가 동등 자격의 인간 작성 지원자보다 shortlisting 확률이 23~60% 높았다.
  자기인식을 겨냥한 개입으로 편향 50% 이상 감소(다른 버전 요약은 60%).
- 숨은 프롬프트 주입: "Measuring Real-World Prompt Injection Attacks in LLM-based Resume Screening", arXiv 2605.28999 (검색상 USENIX Security 2026). https://arxiv.org/abs/2605.28999
  [요약] hireEZ 약 20만 이력서 중 약 1%에서 숨은 주입.
  90% 이상이 명령문이 아니라 기술·키워드 같은 데이터 형태.
  채용 결과에 영향을 줬는지는 라벨이 없어 측정하지 않았다고 함.
- arXiv 2512.20164: 이력서 끝·메타데이터 위치가 취약했다는 요약. 미확인.
- 통제 실험 요약(논문 특정 못 함, 재인용): 후보 품질이 균질하고 주입자가 적을 때 주입이 순위를 안정적으로 올리고, 품질이 다양하면 평균 효과는 작지만 약한 후보가 강한 후보를 앞지르기도 한다.

### 6. 설명 가능성

- Schellingerhout, Barile, Tintarev, "Creating Healthy Friction: Determining Stakeholder Requirements of Job Recommendation Explanations", arXiv 2409.15971, 2024. https://arxiv.org/abs/2409.15971
  [요약] 30명 사전 등록 과제 실험에서 실제 설명이 무작위 설명 대비 의사결정 속도·정확도를 유의하게 개선하지 못했다.
  신뢰·유용성·투명성은 실제 설명 쪽으로 기울었으나 유의하지 않았다.
  설명은 설득 도구가 아닌 "healthy friction"을 주는 의사결정 지원이라고 결론.
  구직자는 짧은 텍스트 설명, 채용담당자는 그래프형 시각 설명을 선호.
- "Let's Get You Hired: A Job Seeker's Perspective on Multi-Agent Recruitment Systems for Explaining Hiring Decisions", arXiv 2505.20312, 2025. https://arxiv.org/abs/2505.20312
  [요약] 지원자가 기존 경험보다 시스템을 더 신뢰했고 신뢰와 actionability가 양의 상관. 표본·방법 미확인, 질적 성격.
- 정리: 설명이 지각된 신뢰를 올린다는 보고는 있으나, 행동·결과 수준의 효과를 보인 대규모 실험은 못 찾았다.

### 7. 공개 데이터셋·벤치마크·실서비스 보고

| 자원 | 내용 | 근거 |
|---|---|---|
| RecSys Challenge 2016 (XING) | 반합성 샘플, 노출 1,078,627건·상호작용 8,826,678건(논문 표 기준), 366팀 | arXiv 1612.00959 https://arxiv.org/abs/1612.00959 (스니펫) |
| RecSys Challenge 2017 (XING) | 오프라인 단계 사용자 1.5M, 아이템 1.3M, 상호작용 3.22억 건+ | 스니펫, 미확인 |
| CareerBuilder 2012 Kaggle | 익명화된 지원 데이터. CIKM 연계는 확인 못 함 | know-center.at 2020 논문 스니펫, 미확인 |
| RJDB | GPT-4로 생성한 5만+ 이력서-공고 합성 벤치마크 (arXiv 2311.06383). 합성이라는 점이 한계 | 스니펫. BOSS Zhipin 소속 여부 미확인 |
| Skill-XL | ESCO 기술 정규화 벤치마크 | arXiv 2505.24640 |
| BOSS Zhipin GIRL | LLM이 이력서로 가상 공고를 생성해 실제 공고와 매칭, SFT→보상모델→PPO (arXiv 2307.02157). 공개 데이터 여부 미확인 | https://arxiv.org/abs/2307.02157 (검색 요약) |
| BOSS Zhipin MockLLM | 모의 면접·양면 평가 멀티에이전트 (arXiv 2405.18113) | 검색 요약 |

실서비스 A/B 보고(전부 기업 자기보고 또는 2차 요약):

- LinkedIn 스킬 추출: 원문 확인(2.1).
- LinkedIn JUDE: 2차 요약(2.3).
- Indeed GPT 기반 "Invite to Apply": 시작된 지원 +20%, 면접·채용 +13%라는 2차 요약. Indeed 원문 미확인.
- CareerBuilder 두 단계 임베딩: CTR·nDCG 개선. 수치 미확인.

### 근거가 약하거나 찾지 못한 것

- WebFetch가 초록을 요약해 돌려주므로 원문 [인용]은 일부뿐이다. [요약] 항목은 전부 원문 대조가 필요하다.
- 직접 읽은 PDF는 없다. IZA DP 16781은 바이너리 파싱 실패, Le Barbanchon 페이지에는 초록이 없었다.
- APJFNN, ESCO·O*NET 공식 문서, BM25/TF-IDF 단독 한계를 보고한 1차 자료는 열어보지 못했다.
- 정답 라벨 문제(과거 채용 편향 학습, 노출 편향, 입사 후 성과 라벨)의 직접 근거를 못 찾았다. 4절은 간접 증거뿐이다.
- 숙련도 추정, 암묵 기술 추론 방법의 구체 1차 자료를 못 찾았다.
- Indeed two-tower A/B 수치, BOSS Zhipin·Xing 실서비스 A/B 수치는 못 찾았다.
- 혼잡 효과 근거가 서로 다르게 요약돼 있어(3.2) 어느 쪽이 일반적인지 판단할 수 없다.
- 2026년 논문(2605.28999, 2609.23307, 2608.01731, alphaXiv 2606.28978)은 검색 결과 그대로 옮겼고 존재·내용을 독립 검증하지 못했다.
- 설명 가능성 연구는 표본이 작거나(n=30) 질적이다.
- 한국어 이력서·한국 시장 대상 연구는 조사하지 않았다.

## 논의 문서로 가져가는 것

아래는 전부 초록·블로그 본문·검색 요약 수준의 근거이고 원문 대조가 필요하다.

- 실서비스 기술 추출은 사전 기반 태거와 의미 태거를 병행하고 기술 그래프의 상하위·형제 관계로 확장한다(LinkedIn, 2.1).
- 보고된 실서비스 개선 폭은 적격 지원 +0.87% 수준이고, 채용 지표는 관측값이 아니라 모델 예측값이다(2.1).
- 추천은 클릭·지원을 늘리지만 순 고용 효과는 약 2%로 작다는 무작위 실험 요약이 있다(3.2).
- 매치(성사) 라벨은 극히 희소하고, 양방향 선호를 따로 예측해 합치면 오차가 전파된다는 주장이 있다(3.1).
- 무엇을 정답 라벨로 삼는가를 비교한 직접 근거는 찾지 못했다(4).
- 인구통계 편향은 근거가 충돌한다 — 임베딩 검색 모델은 이름에 따른 큰 차이를 보였고, 생성형 LLM은 인종·성별에 견고했다는 보고가 있다(5.1).
- LLM은 후보 제시 순서에 따라 선택이 달라지는 위치 편향을 보인다는 보고가 있다(5.2).
- LLM은 LLM이 생성한 이력서를 사람이 쓴 것보다 선호한다는 보고가 있다(5.3).
- 이력서의 숨은 프롬프트·키워드 주입이 실제 데이터에서 약 1% 관측됐다는 보고가 있으나 독립 검증하지 못했다(5.3).
- 매칭 이유 설명이 의사결정 정확도를 유의하게 높였다는 근거는 없다(6).
- 혼잡 효과는 실험마다 요약이 엇갈려 일반화할 수 없다(3.2).
- 한국 시장·한국어 이력서 대상 연구는 이 조사 범위 밖이었다.
