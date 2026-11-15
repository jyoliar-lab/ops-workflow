---
type: discussion
kind: survey
goal: jobseeker-company-matching
topic: careerhub
subjects: []
status: active
related: [docs/careerhub/discussion/261115_1321_post-application-observable-signals.md]
---

# 서류 지원 후 관측할 수 있는 신호 — 조사 (2026-11-15)

## 질문

서류 지원 뒤 결과 통보가 오기 전, 또는 통보가 끝내 없을 때, 지원자가 "서류가 읽혔는가·관심을 받았는가"를 스스로 관측할 수 있는 신호가 무엇인지 알고자 했다.
이력서에 넣은 웹서비스 링크와 GitHub 조직 프로필 링크, 지원 플랫폼(원티드·점핏)의 상태 표시를 후보 신호로 보고, 각 신호가 무엇을 식별하고 무엇을 못 하는지, 실제 결과와 얼마나 관련되는지, 법·정책상 걸리는 점이 있는지를 웹 자료로 확인했다.
결론이나 권고는 쓰지 않는다.

표기 규칙: [열람]은 직접 열어 확인, [검색발췌]는 검색 요약만 본 것(미확인)이다.
확인일은 별도 표기가 없으면 2026-11-15이다.

## 조사

### 1. GitHub README 이미지 요청으로 방문을 관측할 수 있는가

#### 1-1. Camo 프록시와 원 서버에 남는 정보

| 사실 | 출처 | 인용 | 연도/확인일 | 확인 |
|---|---|---|---|---|
| GitHub는 이미지 호스팅에 Camo를 쓰고, 익명 프록시 URL이 브라우저 정보를 다른 사용자에게 숨긴다. | GitHub Docs, About anonymized URLs — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls | "To host your images, GitHub uses the open-source project Camo." / "Camo generates an anonymous URL proxy for each file which hides your browser details" | 2026-11-15 | [열람] |
| 위 문서는 Camo가 원 서버에 어떤 헤더를 보내는지 말하지 않는다. | 같은 문서 | (해당 서술 없음) | 2026-11-15 | [열람] |
| GitHub는 이미지를 프록시하면 개인정보 보호에 도움이 된다고 밝혔다. | GitHub Blog, Proxying User Images — https://github.blog/2014-01-28-proxying-user-images/ | "will help protect your privacy: your browser information won't be leaked to other third party services" | 2014 | [열람] |
| 한 개인 블로그의 원 서버 접근 로그에 GitHub IP와 UA `github-camo (876de43e)`가 찍혔고 Referer는 `-`였다. | karlcow gist (개인 글) — https://gist.github.com/karlcow/b700cd1eae2ceeca7b967464c90ecf23 | `192.30.252.98 - - [21/Nov/2019:00:45:57 +0000] "GET /tmp/amanite01.webp HTTP/1.1" 200 8810 "-" "github-camo (876de43e)"` | 2019 | [열람] (블로그·단일 사례) |
| 프로필 조회 카운터 프로젝트는 Camo 때문에 방문자의 username·UA·IP를 알 수 없다고 적는다. | antonkomarev/github-profile-views-counter (오픈소스 README) — https://github.com/antonkomarev/github-profile-views-counter | "GitHub proxies all image URLs through the GitHub Camo service." (요약: 방문자 username·UA·IP 접근 불가) | 확인일 | [열람] (페이지 내용은 요약 응답) |
| 같은 README는 이 카운터가 고유 방문자가 아니라 조회(hit) 수라고 한다. | 같은 README | "This is counter of profile views (page hits), not a counter of unique visitors." | 확인일 | [열람] |
| 같은 README는 카운터 조작 가능성을 인정한다. | 같은 README | "Everybody knows that any counters could be faked." | 확인일 | [열람] |
| 한 개발자 블로그는 Referer가 프록시에서 전달되지 않아 쿼리 파라미터로 대신했다고 한다. | 검색 요약(DEV 글로 추정, URL 미확정) | (검색 요약의 서술: Camo does not pass the Referrer header) | 미상 | [검색발췌] |

정리: 원 서버가 보는 것은 GitHub 인프라 IP와 `github-camo` UA다(위 로그 사례).
방문자 IP·UA를 원 서버가 받는다는 근거는 찾지 못했다.
GitHub 공식 문서에 Camo→원 서버 요청 헤더 명세는 없다([열람]).

#### 1-2. Camo 캐싱과 매 방문 요청 여부

| 사실 | 출처 | 인용 | 연도/확인일 | 확인 |
|---|---|---|---|---|
| 공식 문서는 캐시 퍼지가 강제로 모든 사용자가 재요청하게 하므로 아껴 쓰라 하고, 이미지가 갱신되지 않으면 원 서버의 Cache-Control이 `no-cache`인지 보라고 한다. | GitHub Docs, About anonymized URLs (위 URL) | "Purging the cache forces every GitHub user to re-request the image, so you should use it very sparingly." | 2026-11-15 | [열람] |
| 한 실험 로그에서 새로고침은 원 서버에 요청을 만들지 않았고 GitHub가 304를 `X-Cache: HIT`, `Cache-Control: public, max-age=31536000`로 응답했다. Shift+새로고침은 `X-Cache: MISS`로 원 서버에 도달했다. | karlcow gist (위 URL) | "A reload of the page didn't create any HTTP requests on the origin server." / "So the image really lives in the github caching systems." | 2019 | [열람] (개인 실험) |
| 원 서버가 이미지를 삭제해도 GitHub가 계속 서빙했다. | 같은 gist | (위 결론 문장) | 2019 | [열람] |
| 카운터 제작자 글은 캐시를 피하려면 "cache headers 또는 non-200 응답"이 필요하다며 `Cache-Control: max-age=0, no-cache, no-store, must-revalidate`를 예로 든다. | rushter.com, How to track and display profile views on GitHub — https://rushter.com/blog/github-profile-markdown/ | 요약 응답: 이미지가 "specify cache headers or return non-200 response (e.g., an HTTP 404 page)"여야 한다 | 연도 미확인 | [열람] (블로그, 페이지 내용은 요약 응답) |
| PlantUML 포럼에서 `cache=no`를 써도 오래된 이미지를 보았고, 해결로 `curl -X PURGE`로 camo URL을 퍼지했다는 보고가 있다. | forum.plantuml.net — https://forum.plantuml.net/7163/githubs-aggressive-caching-prevent-diagrams-updated-markdown | "GitHub caches the generated images using a service of their own named "Camo"" | 2020 | [열람] (커뮤니티) |
| 검색 요약은 "no-cache를 보내도 Camo가 무시했다"는 보고(`public, max-age=604800` 응답)와 쿼리 문자열 변경 우회를 전한다. | 검색 요약(PlantUML 포럼 등) | (검색 요약의 서술) | 미상 | [검색발췌] |

정리: 매 방문마다 원 서버에 요청이 간다는 근거는 없다.
캐시가 요청 수를 줄인다는 사례가 있고(1건 [열람]), no-cache로 항상 해결된다는 공식 보증은 찾지 못했다.
공식 문서는 `no-cache`를 갱신 문제의 점검 항목으로만 언급한다.

#### 1-3. 방문 카운터류의 한계 (봇·선가져오기)

| 사실 | 출처 | 인용 | 확인 |
|---|---|---|---|
| 봇 요청이 집계에 섞인다. | rushter.com (위 URL) | "there will be some extra requests from bots, but having such statistics is better than nothing." | [열람] (요약 응답) |
| 카운터는 새로고침도 hit로 센다. | antonkomarev README (위 URL) | (요약: 새로고침도 hit 증가, 방문자 식별 불가) | [열람] (요약 응답) |
| GitHub 자체의 선가져오기(prefetch)가 집계를 부풀리는지에 관한 자료는 찾지 못했다. | — | 근거 없음 | — |

#### 1-4. 조직 프로필 README에서도 통하는가

- 공개 조직 프로필 README는 `.github` 저장소의 `profile/README.md`다 — GitHub Docs, Customizing your organization's profile, https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/customizing-your-organizations-profile, "In your organization's `.github` repository, create a `README.md` file in the `profile` folder." [열람]
- 조직 프로필 README가 외부 이미지를 Camo로 프록시하는지를 직접 보인 자료는 찾지 못했다. 근거 없음.
- 위 Docs 페이지에는 analytics·traffic 언급이 없다 [열람].

#### 1-5. GitHub 자체 통계 (Traffic)

| 사실 | 출처 | 인용 | 확인 |
|---|---|---|---|
| Traffic은 push 권한자가 보며, 최근 14일, 조회·고유 방문자, 레퍼러(검색엔진·GitHub 제외)를 보여준다. | GitHub Docs, Viewing traffic to a repository — https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository | "Anyone with push access to a repository can view its traffic" / "You can navigate to referring sites, excluding search engines and GitHub itself" | [열람] |
| 위 페이지는 조직 프로필을 언급하지 않는다. | 같은 문서 | (해당 서술 없음) | [열람] |
| REST API로 views·clones·popular paths·referrers를 가져온다. 쓰기 권한이 필요하고 14일이다. | GitHub Docs, REST metrics traffic — https://docs.github.com/en/rest/metrics/traffic | `GET /repos/{owner}/{repo}/traffic/views`, "for repositories that you have write access to", "the last 14 days" | [열람] |
| Traffic이 `.github` 저장소의 조직 프로필 README 조회를 집계하는지는 공식 자료에서 찾지 못했다. | — | 근거 없음 | — |

#### 1-6. GitHub 정책상 추적 픽셀

- GitHub Acceptable Use Policies에 추적 픽셀·트래킹을 직접 다루는 조항은 없었다 [열람 — 요약 응답]. https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
- 가장 가까운 조항: "violates the privacy of any third party, such as by posting another person's personal information without consent."(제3자 프라이버시) 와 "Any person, entity, or service collecting data from the Service must comply with the GitHub Privacy Statement."(서비스에서 데이터를 수집하는 경우). [열람 — 요약 응답]
- 이 조항들이 README 추적 픽셀에 적용된다는 GitHub의 해석은 찾지 못했다. 근거 없음.

### 2. 이력서 링크로 열람을 관측하는 방법들

| 사실 | 출처 | 인용/요약 | 확인 |
|---|---|---|---|
| DocSend류는 링크 클릭 시점에 방문을 기록한다. 이메일 열람이 아니라 링크 방문이다. | 검색 요약(ellty·Dropbox Help 등) | "Tracking happens when the link is clicked, not when the email is opened."(요약) | [검색발췌] |
| 이메일 입력을 요구하지 않으면 방문은 익명이다. 요구하면 방문자 이메일, 방문 시각, 페이지별 체류 시간 등이 남는다. | 검색 요약. 공식 도움말 URL 후보: https://help.dropbox.com/plans/what-is-dropbox-docsend | (요약) | [검색발췌] |
| 엄격한 프라이버시 브라우저·기업 방화벽·JS 비활성화 시 분석 데이터가 없을 수 있다. | 검색 요약(리뷰 글) | (요약) | [검색발췌] |
| Apple Mail Privacy Protection은 추적 이미지를 프리패치해 실제 열람 없이 "열림"을 만든다. Gmail 이미지 프록시도 비슷한 기계 열람을 만든다. 클릭 추적은 상대적으로 덜 영향 받는다. | 검색 요약(MoEngage, Bird, Suped — ESP 벤더 블로그) | (요약) | [검색발췌] (벤더 자료) |
| Microsoft Safe Links 등 보안 게이트웨이가 링크를 자동 클릭·프리패치해 가짜 클릭을 만든다. 한 사람이 동시에 여러 링크를 누르는 군집 패턴이 징후다. | 검색 요약(Suped, 벤더 블로그 등) | (요약) | [검색발췌] (벤더 자료) |
| 지원 건별 UTM·고유 경로·단축 URL·리다이렉트 서버가 식별하는 단위(회사/사람/시각/횟수)에 관한 공식·학술 자료는 찾지 못했다. | — | 근거 없음 | — |

한 줄 요약(추론 없이 위 사실만): 링크 기반 관측은 "링크 요청이 있었다"까지만 기록하고, 요청 주체가 사람인지 자동 스캐너인지는 별도 판별이 필요하다는 보고가 있다(검색발췌).

### 3. 채용 담당자는 이력서 링크를 누르는가

| 사실 | 출처 | 인용 | 연도 | 확인/근거 수준 |
|---|---|---|---|---|
| Ladders 시선추적 연구: 서류 첫 스크리닝은 평균 7.4초. 표본 수는 기사에 없다. | HR Dive — https://www.hrdive.com/news/eye-tracking-study-shows-recruiters-look-at-resumes-for-7-seconds/541582/ | "Today's recruiters skim resumes for an average of 7.4 seconds." | 2018 | [열람] 벤더 연구, 방법 미공개 |
| 링크 클릭 비율을 측정한 신뢰할 만한 조사는 찾지 못했다. 블로그의 수치(예: "12,843건 분석 37% 감소", "50개 이력서 34%")는 출처·방법 불명이다. | 검색 요약 | — | — | 근거 없음 / [검색발췌] |
| 한 웹 가이드는 채용 담당자가 링크를 열어 첫 화면만 빠르게 보는 경향이 있다고 말한다. | bizforms 가이드 — https://www.bizforms.co.kr/guide/list/resume/resume084.asp | (요약) | 미상 | [검색발췌] 실무 팁, 조사 아님 |
| 개발자 채용에서 GitHub 확인 비율의 수치는 찾지 못했다. UFMG 2024 프리프린트가 채용담당자의 GitHub 프로필 사용을 다루지만 PDF를 텍스트로 읽지 못했다. | https://homepages.dcc.ufmg.br/~figueiredo/publications/latam2024preprint.pdf | 검색 요약: "GitHub profiles offer a more nuanced and comprehensive understanding of a developer's skills than traditional methods" | 2024 | [검색발췌] 표본·수치 미확인 |
| 원티드 개발자 리포트가 기업의 개발자 평가 항목(이력서·깃헙 등)을 다루지만 PDF를 텍스트로 읽지 못했고 검색 요약의 수치는 해석 불가였다. | https://static.wanted.co.kr/images/data_report/Wanted_report_developer.pdf | — | 미상 | [검색발췌] 수치 사용하지 않음 |
| 서류 1차 스크리닝 대 면접 직전 중 링크를 여는 시점에 관한 자료는 찾지 못했다. | — | — | — | 근거 없음 |

### 4. 플랫폼이 제공하는 지원 후 신호

| 플랫폼 | 확인된 내용 | 출처 | 확인일 | 확인 |
|---|---|---|---|---|
| 원티드 | 기업이 이력서를 열람하면 진행상태가 "지원→열람"으로 바뀌고 알림(종 아이콘)이 온다. | 원티드 도움말 "지원 현황은 어디에서 확인 하나요?" https://help.wanted.co.kr/hc/ko/articles/360035483932 (직접 열기는 403) — 검색 요약 인용: "지원완료 현황에서 진행상태가 지원→열람으로 변경된 부분을 확인할 수 있습니다." | 2026-11-15 | [검색발췌] |
| 원티드 | 지원자 화면에는 접수/서류통과/최종합격/불합격 상태만 노출되어, 기업의 내부 단계(2차 면접 등)가 서류통과로 보일 수 있다. 서류 통과 후 대기 안내는 최소 7일~최대 2주. | 원티드 도움말 "지원 현황의 단계별 의미가 궁금해요" https://help.wanted.co.kr/hc/ko/articles/13089576213657 (직접 열기는 403) | 2026-11-15 | [검색발췌] |
| 원티드 | 열람/지원완료 후 7일이 지나도 소식이 없으면 "리마인더 전송"으로 인사담당자에게 피드백 요청 메일을 보낼 수 있다. 지원 후 이력서를 수정해도 기업에 알림이 가지 않는다. | 원티드 도움말(위 검색 요약) | 2026-11-15 | [검색발췌] |
| 원티드 | 기업에는 전일 미열람 지원 건이 있으면 다음 날 알림 메일이 간다. | 원티드 도움말(검색 요약) | 2026-11-15 | [검색발췌] |
| 점핏 | 이력서 열람 여부와 지원 현황은 점핏 웹/앱 "마이점핏"에서 확인 가능하다는 운영담당자 답변이 있다(2022년경). 같은 이메일 계정으로 가입해야 보인다는 답변이 있다. 사람인으로 지원했으면 사람인 입사지원현황에서 본다는 답변이 있다. 공식 도움말·FAQ는 찾지 못했다. | 사람인 커리어 Q&A — https://career.saramin.co.kr/feed/view/44732 (질문 2022-02-16, 답변 없음 [열람]) 및 검색 요약 | 2026-11-15 | [검색발췌] 커뮤니티 수준 |
| 점핏(기업 측) | 기업 서비스 가이드에 "열람/미열람 : 열람여부 지원자만 모아볼 수 있습니다." 기능이 있다. | 점핏 기업서비스 이용가이드 https://cdn.jumpit.co.kr/jumpit/jumpit_biz_guide_202202.pdf | 2022 | [검색발췌] |
| 잡코리아 | 잡코리아 이력서로 지원한 경우 지원현황에서 열람 상태를 확인하고, 기업 담당자가 조회하면 "열람"으로 바뀐다. 기록은 최대 3개월 확인 가능. 채용관리 도구(나인하이어)에서 상세를 처음 열거나 상세를 열지 않고 합/불 처리해도 같은 [열람] 상태로 바뀐다. | 잡코리아 FAQ https://m.jobkorea.co.kr/help/faq 와 나인하이어 도움말 | 2026-11-15 | [검색발췌] |
| 사람인 | 사람인 알림 설정에 입사지원 접수/열람/발표 알림 항목이 있다. 직접 지원 건의 열람 알림 정의는 공식 FAQ에서 찾지 못했다. | https://m.saramin.co.kr/my-saramin/set-notif | 2026-11-15 | [검색발췌] |
| 링크드인 | 프로필 조회자 공개 범위는 "Your name and headline" / "Private profile characteristics" / "Private mode". 무료 계정은 조회 이력을 보려면 이름·헤드라인 공개를 선택해야 한다. | LinkedIn Help https://www.linkedin.com/help/billing/answer/47992 — "If you have a Basic (free) account, you must choose Your name and headline if you want to see the viewer history." | 2026-11-15 | [열람] |
| 리멤버 | 프로필 열람 알림에 관한 공식 안내는 찾지 못했다. | — | 2026-11-15 | 근거 없음 |

### 5. 관측 신호와 실제 결과의 관계

- 지원 상태 "열람"이 이후 서류 통과와 얼마나 관련되는지를 다룬 자료는 찾지 못했다. 근거 없음.
- 이력서 링크 클릭·프로필 조회와 서류 통과의 관계를 다룬 자료도 찾지 못했다. 근거 없음.
- 잡코리아 쪽 채용관리 도구 도움말은 상세를 열지 않고 합/불을 처리해도 지원자에게는 [열람]으로 보인다고 한다(검색발췌). 이는 "열람" 표시가 실제 읽음과 일치하지 않을 수 있다는 한 사례다.
- 인접 분야(영업 이메일): 열람 신호가 결과를 약하게만 예측한다는 취지의 서술이 벤더 자료에 있다. 예: 콜드 메일 오픈율은 20~40%대인데 시니어 구매자 응답률은 2% 미만이라는 서술. [검색발췌], 벤더 블로그, 통제 설계 없음.
- 같은 분야에서 Apple MPP가 오픈율 신뢰도를 떨어뜨린다는 서술은 다수 벤더에 반복된다 [검색발췌].
- 동료심사 연구에서 "열람과 결과의 상관계수"를 보고한 자료는 찾지 못했다. 근거 없음.

### 6. 법·윤리

| 사실 | 출처 | 인용/요약 | 확인 |
|---|---|---|---|
| 한국 개인정보보호법은 그 정보만으로 특정인을 알아볼 수 없어도 "다른 정보와 쉽게 결합하여 알아볼 수 있는 정보"를 개인정보로 본다. | 검색 요약(2차 자료). 법령 원문 https://www.law.go.kr 는 직접 열지 않음 | "해당 정보만으로는 특정 개인을 알아볼 수 없더라도 다른 정보와 쉽게 결합하여 알아볼 수 있는 정보" | [검색발췌] |
| IP 주소의 개인정보 해당 여부는 맥락에 따라 달라지고, 명시적 개인정보보호위원회 결정은 검색에서 확인되지 않았다. 학계·시민단체 의견서는 IP를 개인정보로 봐야 한다고 주장한다. | 검색 요약(innoforest 글, peoplepower21 의견서, core.ac.uk 논문) | (요약) | [검색발췌] 2차 자료 |
| 개인정보보호위원회 2024-01-24 의결 문서(워크넷)는 IP 분석을 접근통제 의무로 서술할 뿐 IP의 개인정보 여부를 판단하지 않는다. | https://www.law.go.kr/LSW/ppcInfoP.do?ppcSeq=7759 | "시스템에 접속한 IP 주소 등을 분석하여 불법적인 개인정보 유출 시도를 탐지하고 대응하여야 하며" | [열람] |
| EU CJEU Breyer(C-582/14, 2016-10-19): 사업자가 추가 정보로 방문자를 식별할 법적 수단이 있으면 동적 IP는 개인정보가 될 수 있다. | 검색 요약(Simmons & Simmons, Inside Privacy 등) | (요약) | [검색발췌] |
| EDPB Guidelines 2/2023 (ePrivacy Art. 5(3) 기술적 범위) v2.0이 존재한다. 추적 픽셀·링크 추적이 범위에 들어가는지의 본문은 읽지 못했다. | https://www.edpb.europa.eu/our-work-tools/documents/public-consultations/2023/guidelines-22023-technical-scope-art-53-eprivacy_en | "Guidelines 2/2023 on Technical Scope of Art. 5(3) of ePrivacy Directive" (제목만 확인) | [열람] 본문 미확인 |
| 한국의 추적 픽셀 규제·판례, 개인이 자기 사이트 로그를 보는 것과 특정인 식별 추적의 구분에 관한 감독기관 자료, 채용 담당자가 추적을 알아챘을 때의 반응 자료는 찾지 못했다. | — | — | 근거 없음 |

### 근거가 약하거나 찾지 못한 것

- Camo가 원 서버로 보내는 헤더 전체와 X-Forwarded-For 포함 여부: GitHub 공식 명세 없음. 단일 개인 로그 1건만 있다.
- 조직 프로필 README(`.github/profile/README.md`)의 외부 이미지가 Camo를 거치는지, 조직 프로필 조회가 저장소 Traffic에 집계되는지: 근거 없음.
- Camo가 `no-cache`를 존중하는지: 상충한다. 공식 문서는 `no-cache`를 점검 항목으로 언급하고, 커뮤니티에는 무시되었다는 보고와 cache-busting 우회 보고가 있다. 둘 다 검증된 규칙이 아니다.
- GitHub의 선가져오기·크롤러가 카운터를 부풀리는 정도: 근거 없음. 봇 혼입은 카운터 제작자 자술만 있다.
- GitHub 정책이 README 추적 픽셀을 금지·허용하는지: 해당 조항 없음, 해석 자료 없음.
- 지원 건별 링크(UTM·단축 URL·리다이렉트)가 식별하는 단위와 한계: 공식·학술 자료 없음.
- 채용 담당자의 링크·GitHub 클릭 비율과 시점: 신뢰할 만한 조사 없음. 블로그 수치는 출처 불명이라 사용하지 않았다.
- 원티드 도움말은 403으로 직접 열지 못해 모두 검색 발췌다. 점핏 지원자용 공식 도움말은 찾지 못했다. 리멤버·사람인 열람 알림은 공식 근거 없음.
- 열람 신호와 서류 통과의 관계: 직접 자료 없음. 인접 분야 자료는 벤더 블로그 수준이다.
- 한국법의 IP 개인정보 해당 여부 판단과 추적 픽셀 규제는 법령·감독기관 원문을 읽지 못했다. EDPB 본문과 PIPC 해석례도 읽지 못했다.
- 사람 식별 가능성이 높은 신호를 수집하는 경우의 윤리에 관한 자료와, 채용 담당자의 추적 인지 반응 자료: 근거 없음.

## 논의 문서로 가져가는 것

- GitHub 공식 문서는 Camo가 방문자의 브라우저 정보를 다른 사용자에게 숨긴다고 서술하고, 원 서버가 받는 헤더는 명시하지 않는다.
- 공개된 개인 로그 1건에서 원 서버는 GitHub IP와 `github-camo` UA를 보았고 Referer는 비어 있었다.
- 같은 로그 실험에서 일반 새로고침은 Camo 캐시(HIT)에서 처리되어 원 서버에 요청이 가지 않았다.
- 공식 문서는 이미지가 갱신되지 않을 때 원 서버의 Cache-Control을 `no-cache`로 두라고 안내하고, 커뮤니티에는 이를 무시했다는 보고가 있다.
- README 이미지 기반 방문 카운터는 hit 수이고 고유 방문자 수가 아니며, 봇 요청이 섞인다는 제작자 자술이 있다.
- 저장소 Traffic은 push 권한자에게 최근 14일의 views·unique·referrers를 주고 API도 같은 범위다. 조직 프로필 README 집계 여부는 공식 자료에 없다.
- GitHub AUP에는 추적 픽셀을 직접 다루는 조항이 없고, 제3자 프라이버시·개인정보 수집 관련 일반 조항이 있다.
- 링크 클릭 추적(DocSend류)은 링크 방문을 기록하고, 이메일 입력을 요구하지 않으면 방문자는 익명이라는 서술이 있다.
- Safe Links 등 보안 스캐너와 Apple MPP가 가짜 클릭·열림을 만든다는 서술이 ESP 벤더 자료에 반복된다.
- 원티드 도움말(검색발췌)은 기업 열람 시 "지원→열람" 상태 변경과 알림이 있고, 지원자 화면 상태는 접수/서류통과/최종합격/불합격으로 단순하다고 서술한다.
- 잡코리아는 기업 조회 시 "열람" 표시, 최대 3개월 조회를 안내하며, 채용관리 도구에서는 상세를 열지 않은 합/불 처리도 [열람]으로 보인다(검색발췌).
- LinkedIn 공식 도움말: 무료 계정은 조회자 이력을 보려면 이름·헤드라인 공개를 선택해야 한다.
- 이력서 스크리닝 평균 시간 7.4초(Ladders 2018, 방법 미공개)가 있고, 링크 클릭 비율·GitHub 확인 비율의 신뢰할 만한 수치는 찾지 못했다.
- 열람·클릭 신호와 서류 통과의 관계를 다룬 자료는 찾지 못했다.
- 한국 법에서 IP 주소는 다른 정보와 쉽게 결합되면 개인정보가 되며 IP 단독의 해석은 2차 자료마다 맥락 의존으로 서술된다. CJEU Breyer는 식별 수단이 있으면 동적 IP가 개인정보라고 판시했다.
