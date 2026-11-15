---
type: discussion
kind: deliberation
goal: jobsearch-operator-harness
topic: jobsearch-operator
subjects: [jobsearch-operator, sqlite]
status: done
ref-adrs: []
related:
  - docs/careerhub/discussion/261115_1220_posting-selection-by-screening-odds.md
  - docs/careerhub/discussion/261115_1321_post-application-observable-signals.md
---

# 지원 현황을 담는 sqlite 스키마 — jobsearch-operator의 첫 구조

## 1. 문제

구직 서포트 하네스 `jobsearch-operator`가 다룰 지원 현황에 체계가 없다.
어떤 공고에 어떤 이력서로 지원했는지, 상태가 언제 어떻게 바뀌었는지, 그 공고가 무엇을 요구했는지가 한곳에 모여 있지 않다.

담아야 하는 것은 넷이다.
어떤 공고에 어떤 이력서로 지원했는가.
이력서가 겨냥한 직군들과 공고가 구하는 직군들 — 한 이력서가 여러 직군을 겨냥할 수 있고, 공고는 표기된 직군이 하나여도 본문이 다른 직군의 역량을 요구하는 일이 많다. 둘이 어디서 겹치고 엇갈렸는지가 남아야 한다.
지원일과 지원 현황 — 대기, 열람, 서류 합격, 면접 대기, 불합격 같은 상태와 그 상태로 바뀐 날짜.
공고의 제목·요구 기술·경력·자격요건·우대사항을 본문 그대로 — 이력서와 공고의 연관성을 분석할 원자료다.

열려 있던 것은 저장 수단을 정한 뒤의 구조다.
DB 파일을 어떻게 보관할지, 상태와 그 이력을 어떻게 담을지, 공고 본문과 이력서를 어떤 모양으로 넣을지.

## 2. 실측

- `jobsearch-operator`는 비공개 저장소이고 초기 커밋과 `README.md`만 있다(2026-11-15 확인).
- 지원 경로는 원티드와 점핏 두 플랫폼이다.
- 두 플랫폼 모두 공고 상세를 JSON으로 돌려주는 주소가 있다. 커리어허브 수집기가 그 주소를 쓴다 — `workspace/ref/careerhub-posting-provider/careerhub/posting_service/provider/source/wanted/client.go:37`, `.../source/jumpit/client.go:32`.
- 그 응답에서 주요업무·자격요건·우대사항·혜택·채용 절차가 섹션별 문자열로 온다 — `.../source/wanted/apires.go:156-165`, `.../source/jumpit/apires.go:146-155`.
- 요구 경력은 두 플랫폼 모두 최소·최대 연차의 정수로 온다 — `wanted/apires.go:168-171`, `jumpit/apires.go:158-161`.
- 기술 목록은 점핏만 신뢰할 만한 값으로 온다. 커리어허브는 원티드의 기술 목록을 신뢰하지 않아 버린다 — `wanted/apires.go:166`.
- 게시일은 점핏에만 있다 — `wanted/apires.go:172`, `jumpit/apires.go:162`.
- 커리어허브는 공고를 `(site, postingId)`로 식별한다 — `workspace/ref/careerhub-posting-service/careerhub/posting_service/common/domain/jobposting/jobposting.go:73-93`.
- 커리어허브는 이미 저장한 공고가 수정돼도 다시 가져오지 않는다 — `careerhub-posting-provider/careerhub/posting_service/provider/app/send.go:33-39`.
- 웹 페이지를 읽어 주는 agent 도구는 내용을 요약해 돌려준다. 앞선 조사들에서 원문 인용을 얻지 못한 원인이 이것이었다(`docs/careerhub/discussion/261114_1952_resume-posting-matching-techniques-survey.md` §0).
- 이력서 원본은 PDF뿐이다. 텍스트 원본이 없다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 저장 수단

**선택: sqlite.** 지원 건·상태 전이·공고·이력서가 서로 엮여 있어 관계로 묻는 일이 많다. (처음에는 지원 건마다 마크다운 파일 하나였다가 바꿨다.) (인터뷰, 2026-11-15)

<details><summary>버린 안</summary>

- 지원 건마다 마크다운 파일 하나(frontmatter + 본문) — 상태 전이와 이력서·공고의 교차 질의가 손 집계가 된다
- 표 한 장 — 공고 본문을 둘 자리가 없다
- 지원 건마다 폴더 — 파일이 건당 서너 개로 늘고 전체 현황을 따로 모아야 한다

</details>

### 3-2. 쓰는 주체

**선택: 하네스 agent가 대화로 받아 기록한다. 자주 쓰는 기능은 필요해질 때 스크립트로 만들고, 스크립트가 생긴 기능은 그것을 거친다.** 사람은 SQL을 직접 쓰지 않는다. (인터뷰, 2026-11-15)

<details><summary>버린 안</summary>

- 처음부터 전용 명령으로만 쓴다 — 무엇이 자주 쓰이는지 써 보기 전에 만들게 된다
- 사람이 직접 쓴다 — 기록이 밀린다

</details>

### 3-3. 담는 공고의 범위

**선택: 지원을 고려해 고른 공고다 — 지원한 것, 아직 지원하지 않은 것, 접은 것.** 선별 대상이 된 공고 전체가 아니다. agent에게 선별을 맡기는 단계는 아직 멀고, 그때는 agent가 커리어허브에서 직접 찾는다. (인터뷰, 2026-11-15)

<details><summary>버린 안</summary>

- 지원한 공고만 — 접은 공고와 그 이유가 남지 않아 선별 기준을 되짚을 수 없다
- 선별 대상 전체 — 수천 건의 사본을 들고 있을 이유가 없다. 커리어허브가 이미 갖고 있다

</details>

### 3-4. 공고 본문의 출처

**선택: 플랫폼의 원문을 직접 가져와 보관한다. 가져오는 일은 agent가 한다.** 실제로 보고 판단한 그 내용이 남아야 한다. 커리어허브 수집분은 공고가 수정돼도 갱신되지 않는다. (인터뷰, 2026-11-15)

<details><summary>버린 안</summary>

- 커리어허브 수집분을 복사한다 — 수정이 반영되지 않고, 원티드의 기술 목록이 빠져 있다
- 두 출처를 모두 보관한다 — 커리어허브와는 `(플랫폼, 공고 ID)`로 언제든 이을 수 있어 사본이 필요 없다

</details>

### 3-5. 범위

**선택: 면접 이후의 상세 기록, 지원 후 관측 신호, 연관성 분석 자체는 이번에 다루지 않는다.** 면접 이후는 상태 전이로만 남긴다. 분석은 원자료를 담는 구조까지만 정한다. (인터뷰, 2026-11-15)

### 3-6. 산출물

**선택: DDL 초안까지.** 컬럼·타입·제약을 적은 스키마 초안이 이 문서에 있고, 실제 파일은 `jobsearch-operator`에서 만든다. (인터뷰, 2026-11-15)

## 4. 열린 축 — 논의

### 4-1. DB 파일을 어떻게 보관하나

sqlite의 DB는 바이너리 파일 하나다.
git은 바이너리의 차이를 보여주지 못한다.
쓰는 주체가 한 대의 컴퓨터에 있는 agent 하나라 동시 수정 충돌은 없다.

- A. **DB 파일을 그대로 커밋한다** — 스키마는 `schema.sql`로 따로 두고, DB 파일도 저장소에 넣는다.
  손댈 것이 가장 적고 백업이 푸시로 끝난다. 상태 전이는 DB 안의 이력 테이블에 남으므로 git의 차이가 없어도 "언제 무엇이 바뀌었나"를 잃지 않는다.
  커밋마다 무엇이 바뀌었는지 git에서 읽을 수 없고, 저장소가 커밋마다 파일 전체만큼 자란다. 공고 수백 건 규모에서는 문제가 되지 않는다.
- B. **텍스트 덤프를 커밋하고 DB는 다시 만든다** — DB 파일은 무시하고, 쓸 때마다 `.dump` 결과를 커밋한다.
  변경이 git에서 줄 단위로 읽히고 검토할 수 있다.
  덤프를 빠뜨리면 DB와 저장소가 어긋난다. 쓰는 쪽이 매번 덤프까지 해야 한다.
- C. **DB는 커밋하지 않는다** — 저장소에는 스키마와 도구만 두고 DB는 로컬에만 둔다.
  저장소가 가볍다.
  백업이 따로 없으면 디스크 사고 한 번에 기록이 사라진다. 비공개 저장소를 만든 이유와 어긋난다.
- D. **sqlite를 쓰지 않는다** — 3-1의 버린 안으로 돌아간다.
  차이가 줄 단위로 읽힌다.
  교차 질의가 손 집계가 된다.

**판정(사람, 2026-11-15): A. DB 파일을 그대로 커밋한다.**

### 4-2. 상태와 그 이력을 어떻게 담나

요구는 "지금 상태"와 "어느 날짜에 그 상태로 바뀌었나" 둘 다다.

- A. **전이 이력만 쌓고 현재 상태는 거기서 뽑는다** — 전이 한 건이 한 행이고, 현재 상태는 가장 최근 전이를 보여주는 뷰다.
  진실이 한 곳이라 어긋날 수 없다. 열람부터 결과까지 며칠 걸렸는지가 그대로 나온다.
  현재 상태를 볼 때마다 뷰를 거친다. 이 규모에서는 비용이 아니다.
- B. **지원 건에 현재 상태 컬럼을 두고 이력도 쌓는다** — 읽기가 단순하다.
  두 곳을 함께 고쳐야 해서 한쪽만 고치면 어긋난다. 트리거로 묶으면 막을 수 있지만 구조가 하나 는다.
- C. **상태마다 날짜 컬럼을 둔다** — `applied_at`, `viewed_at`, `passed_at`처럼 가로로 편다.
  표 한 장으로 다 보인다.
  상태가 하나 늘 때마다 컬럼을 더해야 하고, 같은 상태를 두 번 거치는 경우(면접이 여러 차례)를 담지 못한다.

**판정(사람, 2026-11-15): A. 전이 이력만 쌓고 현재 상태는 뷰로 뽑는다.**

### 4-3. 상태의 종류를 어디에 정하나

예로 든 상태는 대기, 열람, 서류 합격, 면접 대기, 불합격이고 "등등"이 붙어 있다.
지원 전 단계(고려 중, 접음)도 3-3 때문에 필요하다.

- A. **상태 정의 테이블을 둔다** — 상태를 행으로 정의하고 전이 이력이 그것을 참조한다.
  상태를 더할 때 행 하나만 넣으면 된다. 각 상태가 끝난 상태인지, 어느 단계에 속하는지를 같이 적을 수 있다.
  테이블이 하나 는다.
- B. **CHECK 제약으로 고정한다** — 허용 값을 스키마에 박는다.
  오타가 원천적으로 막힌다.
  sqlite는 CHECK를 고치려면 테이블을 다시 만들어야 한다. 상태가 아직 "등등"인 단계에서는 자주 걸린다.
- C. **자유 문자열로 둔다** — 플랫폼이 보여주는 표현을 그대로 적는다.
  제약이 없어 당장 편하다.
  "열람"과 "열람됨"이 섞이면 집계가 깨진다.

**판정(사람, 2026-11-15): A. 상태 정의 테이블을 둔다.**

### 4-4. 공고 본문을 어떤 모양으로 담나

두 플랫폼이 주는 섹션이 대체로 같다(주요업무·자격요건·우대사항·혜택·채용 절차).
같은 공고를 고려할 때와 지원할 때 두 번 볼 수 있고, 그 사이에 공고가 수정될 수 있다.

- A. **공고와 본문 사본을 나누고, 사본은 섹션별 컬럼과 원본 JSON을 함께 둔다** — 공고는 정체(플랫폼·공고 ID·회사)만, 사본은 가져온 시각마다 한 행이다. 지원 건은 지원 시점의 사본을 가리킨다.
  섹션별로 바로 질의할 수 있고, 원본 JSON이 있어 컬럼에 담지 않은 것을 나중에 꺼낼 수 있다. 수정 전후가 둘 다 남는다.
  테이블이 둘이고 본문이 두 벌(컬럼과 JSON)로 들어간다.
- B. **공고 한 행에 섹션별 컬럼만 둔다** — 다시 가져오면 덮어쓴다.
  가장 단순하다.
  지원 뒤 공고가 수정되면 내가 본 내용이 사라진다. 컬럼에 없는 것은 다시 얻을 수 없다.
- C. **섹션을 행으로 편다** — `(사본, 섹션 이름, 본문)` 꼴이다.
  플랫폼마다 섹션이 달라도 스키마가 바뀌지 않는다.
  두 플랫폼의 섹션이 사실상 같아 얻는 것이 없고, 한 공고를 읽으려면 늘 모아야 한다.

**판정(사람, 2026-11-15): B. 공고 한 행에 섹션별 컬럼만 둔다.**

### 4-5. 이력서를 어떻게 담나

원본이 PDF뿐이다.
분석에는 텍스트가 필요하고, 제출한 것이 무엇이었는지는 파일로 증명돼야 한다.

- A. **파일은 저장소에 두고 DB에는 버전·경로·해시와 추출한 텍스트를 둔다** — PDF는 `resumes/` 아래 파일이고, DB는 그 파일을 가리키며 텍스트 사본을 함께 가진다.
  PDF는 git이 파일로 관리하고, 분석은 DB 안의 텍스트로 한다. 해시가 있어 파일이 바뀌면 드러난다.
  추출한 텍스트가 PDF의 배치(단, 표)를 잃을 수 있다.
- B. **DB에는 버전과 경로만 둔다** — 텍스트는 분석할 때마다 뽑는다.
  DB가 가볍다.
  분석 때마다 추출 결과가 달라질 수 있어 같은 이력서에 대한 분석이 재현되지 않는다.
- C. **PDF를 DB에 통째로 넣는다** — 파일이 흩어지지 않는다.
  DB가 커지고 PDF를 열어 보려면 꺼내야 한다.

**판정(사람, 2026-11-15): B. DB에는 버전과 경로만 둔다.**

### DDL 초안 — 판정을 반영한 것

이름은 초안이다.

```sql
PRAGMA foreign_keys = ON;

-- 직군 정의. 이력서의 대상 직군과 공고의 구인 직군이 함께 참조한다. 이력서·공고 하나에 직군 여럿이 붙는다
CREATE TABLE job_role (
  code   TEXT PRIMARY KEY,
  label  TEXT NOT NULL
);

INSERT INTO job_role (code, label) VALUES
  ('devops',  'DevOps'),
  ('backend', 'Backend');

-- 이력서 버전 (4-5 B)
CREATE TABLE resume (
  id          INTEGER PRIMARY KEY,
  label       TEXT NOT NULL UNIQUE,          -- 'v1', 'v2'
  file_path   TEXT NOT NULL,                 -- 저장소 기준 경로
  note        TEXT,                          -- 이 버전에서 바꾼 것
  created_at  TEXT NOT NULL                  -- ISO 8601
);

-- 공고. 다시 가져오면 덮어쓴다 (4-4 B)
CREATE TABLE posting (
  id              INTEGER PRIMARY KEY,
  platform        TEXT NOT NULL,             -- 'wanted' | 'jumpit'
  external_id     TEXT NOT NULL,             -- 플랫폼의 공고 ID. 커리어허브의 (site, postingId)와 같다
  url             TEXT NOT NULL,
  company_name    TEXT NOT NULL,
  title           TEXT NOT NULL,
  intro           TEXT,
  main_tasks      TEXT,
  qualifications  TEXT,
  preferred       TEXT,
  benefits        TEXT,
  hiring_process  TEXT,
  tech_stack      TEXT,                      -- 플랫폼이 준 기술 목록(JSON 배열). 없으면 NULL
  career_min      INTEGER,
  career_max      INTEGER,
  location        TEXT,
  published_at    TEXT,
  due_at          TEXT,
  captured_at     TEXT NOT NULL,             -- 본문을 가져온 시각
  UNIQUE (platform, external_id)
);

-- 이력서가 겨냥한 직군. 한 이력서에 여럿
CREATE TABLE resume_role (
  resume_id  INTEGER NOT NULL REFERENCES resume(id),
  role_code  TEXT NOT NULL REFERENCES job_role(code),
  PRIMARY KEY (resume_id, role_code)
);

-- 공고가 구하는 직군. 한 공고에 여럿
CREATE TABLE posting_role (
  posting_id  INTEGER NOT NULL REFERENCES posting(id),
  role_code   TEXT NOT NULL REFERENCES job_role(code),
  source      TEXT NOT NULL CHECK (source IN ('labeled', 'body')),  -- 공고에 표기된 직군인가, 본문이 요구하는 직군인가
  PRIMARY KEY (posting_id, role_code)
);

-- 상태 정의 (4-3 A)
CREATE TABLE status (
  code         TEXT PRIMARY KEY,
  label        TEXT NOT NULL,                -- 한국어 표시
  stage        TEXT NOT NULL,                -- 'pre' | 'document' | 'interview' | 'closed'
  is_terminal  INTEGER NOT NULL DEFAULT 0
);

INSERT INTO status (code, label, stage, is_terminal) VALUES
  ('considering',      '고려 중',   'pre',       0),
  ('dropped',          '접음',      'pre',       1),
  ('applied',          '대기',      'document',  0),
  ('viewed',           '열람',      'document',  0),
  ('document_passed',  '서류 합격', 'document',  0),
  ('interview_wait',   '면접 대기', 'interview', 0),
  ('interview_passed', '면접 합격', 'interview', 0),
  ('offer',            '최종 합격', 'closed',    1),
  ('rejected',         '불합격',    'closed',    1),
  ('withdrawn',        '지원 취소', 'closed',    1);

-- 고려한 공고 한 건. 지원 전에는 지원 관련 칸이 비어 있다 (3-3)
CREATE TABLE application (
  id                   INTEGER PRIMARY KEY,
  posting_id           INTEGER NOT NULL UNIQUE REFERENCES posting(id),
  resume_id            INTEGER REFERENCES resume(id),               -- 지원할 때 채운다
  applied_at           TEXT,
  note                 TEXT
);

-- 상태 전이 이력. 진실은 여기 한 곳 (4-2 A)
CREATE TABLE status_event (
  id              INTEGER PRIMARY KEY,
  application_id  INTEGER NOT NULL REFERENCES application(id),
  status_code     TEXT NOT NULL REFERENCES status(code),
  occurred_at     TEXT NOT NULL,             -- 그 상태가 된 날짜
  recorded_at     TEXT NOT NULL,             -- 기록한 시각
  note            TEXT                       -- 접은 이유, 불합격 사유 등
);

CREATE INDEX idx_status_event_application ON status_event (application_id, occurred_at);

-- 현재 상태 (4-2 A)
CREATE VIEW application_current AS
SELECT a.id            AS application_id,
       p.platform,
       p.company_name,
       (SELECT group_concat(role_code, ',') FROM posting_role
         WHERE posting_id = p.id AND source = 'labeled') AS posting_labeled_roles,
       (SELECT group_concat(role_code, ',') FROM posting_role
         WHERE posting_id = p.id AND source = 'body')    AS posting_body_roles,
       r.label         AS resume,
       (SELECT group_concat(role_code, ',') FROM resume_role
         WHERE resume_id = r.id)                         AS resume_roles,
       a.applied_at,
       e.status_code,
       s.label         AS status_label,
       e.occurred_at   AS status_since
FROM application a
JOIN posting p ON p.id = a.posting_id
LEFT JOIN resume r ON r.id = a.resume_id
JOIN status_event e ON e.id = (
  SELECT id FROM status_event
  WHERE application_id = a.id
  ORDER BY occurred_at DESC, id DESC
  LIMIT 1)
JOIN status s ON s.code = e.status_code;
```

이 초안이 담지 않은 것이 둘 있다.
선별 기준의 버전(앞선 지원과 뒤의 지원에서 달랐던 기준)은 자리를 두지 않았다 — 기준 자체가 아직 글로 정리돼 있지 않다.
무응답은 상태로 두지 않았다 — `applied_at`과 오늘 날짜에서 계산되는 값이고, 상태로 적어 두면 뒤늦은 연락과 어긋난다.

## 5. 반대편 — 이 설계가 틀리는 조건

- 지원이 수십 건에서 끝나면 표 한 장이면 충분했다. 스키마를 고치는 품이 얻는 것보다 클 수 있다.
- agent가 대화로 쓰는 한 전이 규칙을 강제하는 것이 없다. 순서가 뒤바뀐 전이나 날짜가 빠진 기록이 들어갈 수 있다.
- 플랫폼의 상세 주소는 공개 계약이 아니다. 응답 모양이 바뀌면 본문을 가져오는 일이 깨진다. 원본 응답을 보관하지 않으므로 컬럼에 담지 않은 것은 되찾을 수 없다.
- 이력서 텍스트를 분석 때마다 PDF에서 뽑으므로, 추출 결과가 달라지면 같은 이력서에 대한 분석이 재현되지 않는다.
- 지원 뒤 공고가 수정된 것을 다시 가져오면 지원 시점에 본 내용이 덮어써진다.
- 한 공고에 한 번만 지원한다고 가정했다. 같은 공고에 이력서를 바꿔 다시 지원하면 `application`의 유일 제약이 걸린다.
- DB를 그대로 커밋하면 잘못된 기록이 들어간 것을 git에서 알아챌 수 없다.

## 6. 버린 것

- **커리어허브 DB에 지원 기록을 넣는다** — 커리어허브에는 지원·이력서 개념이 없고, 한 사람의 구직 기록을 서비스 스키마에 넣을 근거가 없다.
- **선별 대상 공고 전체의 사본** — 커리어허브가 이미 갖고 있고 `(플랫폼, 공고 ID)`로 이을 수 있다.
- **이력서를 항목(경력·기술·기간)으로 쪼개 넣는다** — 분석 방법이 정해지지 않았다. 지금은 원문 텍스트까지만 담는다.

## 7. 임계선 — ADR감인가

ADR감이 아니다.
한 사람이 쓰는 비공개 저장소의 스키마이고, 수십 건 규모에서는 테이블을 다시 만들어 옮기는 데 한 시간이 걸리지 않는다.
이 스키마가 커리어허브의 사용자 기능(지원 기록 저장)으로 옮겨 갈 때는 다른 결정이고, 그때 임계선을 다시 본다.

## 8. 다음

- 위 DDL 초안을 `jobsearch-operator`에 `schema.sql`로 둔다. 그 저장소에 쓰는 일은 그쪽 하네스나 사람이 한다.
- 지금까지의 지원 12건과 이력서 두 버전을 첫 데이터로 넣는다.
- 지원 후 관측 신호를 담을 자리는 `docs/careerhub/discussion/261115_1321_post-application-observable-signals.md`의 판정 뒤에 더한다.
- 구조가 잡히면 `jobsearch-operator`의 규약(CLAUDE.md)과 기록 절차를 별도 논의로 연다.
