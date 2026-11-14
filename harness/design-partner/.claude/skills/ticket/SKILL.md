---
name: ticket
description: GitHub Issue를 발행하고 계층을 연결한다 (Issue Type 지정 · sub-issue 링크 · Epic 티켓의 ADR 게이트). "티켓을 만든다", "epic/feature/task/bug를 발행한다", "하위 이슈로 붙인다" 일 때 사용한다. 규약은 CLAUDE.md §5.
---

# 티켓 발행

## 1. 타입을 판정한다 — 판단이다

| 타입 | 성격 | 전제 |
|---|---|---|
| **Epic** | 컨테이너 | **공표된 근거 ADR** (superseded·rejected 불가) |
| **Feature** | 컨테이너 (**선택적**) | 없음. ADR은 선택 — 명시하면 같은 게이트를 지난다 |
| **Task** / **Bug** | 리프 | 없음. ADR은 선택(직접 이행 시) — 명시하면 같은 게이트를 지난다 |

**accepted 요구는 발행이 아니라 착수의 문이다.** proposed 근거로도 발행할 수 있다.

- **Feature는 리프를 묶는 그룹화 컨테이너다.** Epic 밑에서도, Epic 없이 최상위에서도 쓸 수 있다.
- **조사에는 티켓이 없다**(§5). *계획된* 조사를 백로그에 올릴 때만 `Task`(완료 조건 = discussion 문서 커밋).
- `story`·`spike`는 **없다**.

## 2. 발행한다 — `create.py`

```bash
create.py \
  --type epic|feature|task|bug \
  --title "..." \
  --body-file <path> \
  [--adr ADR-0001]... \              # 반복 가능. Epic 필수 · Feature·리프 선택
  [--target-repo owner/name]... \    # task·bug 는 이것 또는 --no-target-repo 가 필수
  [--no-target-repo] \               # 수정 대상 부재의 명시적 선언 (신규 저장소 생성 등)
  [--ref-repo owner/name]... \       # 참조 저장소 (선택 · 비완전 목록)
  [--blocked-by N]... \              # 선행 티켓. task·bug 는 이것 또는 --no-deps 가 필수
  [--no-deps]                        # 선행 없음의 명시적 선언
```

새 티켓은 Project #1에 **타입별 초기 Status**로 들어간다(ADR-0033의 로스터): **Epic·Feature·Task = `Draft`** · **Bug = `Todo`**. 이후 전이는 사람의 것이다(§4).

### 본문 — `templates/`의 타입별 템플릿에서 시작한다

`epic.md`(Feature도 이것 — 컨테이너 공통) · `task.md` · `bug.md`.
리프의 **Acceptance Criteria 절은 저장소 부류의 조각으로 채운다** — `ac-app.md`(애플리케이션 기본 묶음: 동작 · 검사 · 선언) · `ac-infra.md`(인프라 IaC · GitOps 기본 묶음: 선언 · 수렴 · 지속) · `ac-doc.md`(산문 — 하네스 · 정책 문서 기본 묶음: 판독 · 검사). 조각의 내용을 AC 절 주석 아래에 붙이고 조각의 머리 주석은 지운다. 각 그룹의 뜻과 증거는 조각의 그룹 주석이 말한다. 조각에 공통인 규칙:

- **그룹의 뜻은 저장소 부류와 무관하다** — 집행자는 저장소가 아니라 그룹 이름을 읽는다. 조각은 기본 묶음일 뿐이다 — 묶음 밖 그룹이 필요하면 다른 조각에서 가져온다: 코드를 호출한 결과 · 저장소 안의 기계 검사는 `ac-app`(동작 · 검사), 실행 환경에서 재는 약속(성능 · 배포 상태 · 운영 지표 · 외부 의존의 비결정 동작)은 `ac-infra`(수렴 · 지속), 사람이 읽어야 판정되는 약속(문서 · 프롬프트 · 화면)은 `ac-doc`(판독).
- **행은 의도를 적는다 — 의도보다 엄격한 기계적 결과로 바꿔 적지 않는다.** "prod 가 영향받지 않는다" 를 "렌더가 바이트 단위로 같다" 로 적으면 집행자가 그 문구에 맞춰 구조를 고른다. 확인 방법은 행 끝에 덧붙인다 — 조건이 아니라 증거의 자리다.
- 기본 묶음의 빈 그룹은 "없음" — 지우지 않는다. 가져온 그룹은 비면 가져오지 않는다.
- 번호는 그룹을 넘어 이어 붙인다(AC-1 · AC-2 …) — 집행자가 그 번호로 행을 가리킨다.
- 절차(롤백 지점 · 기록 의무 · 선행 조사 · 테스트의 자리와 형태)는 어느 그룹에도 들어가지 않는다 — Technical Notes(Bug 는 Context)에. 러너 · 메타테스트 · 집행 흐름이 이미 강제하는 것을 옮겨 적지 않는다.

**초안은 `tmp/github-issues/<슬러그>.md` 에 쓴다**(gitignored).

- **공통 절(Summary · Context · Goal · Acceptance Criteria · References)은 이름까지 한 벌이다.** (Bug에는 Goal이 없다 — Expected Behavior가 그 질문에 답한다.)
- **선택 절(Requirements · Technical Notes · Environment · Evidence)은 지우지 않고 부재를 "없음"으로 명시한다.**
- **References는 조사에서 얻은 외부 정보 전용이다.** ADR·discussion 등 내부 문서를 넣지 않는다.
- **discussion 링크는 티켓 어디에도 넣지 않는다.** 필요한 맥락은 Context로 옮겨 적는다. 근거 ADR이 없는 리프는 Context가 유일한 "왜"다. 충분히 쓴다.
- **'근거 ADR'·'저장소' 절은 템플릿에 없다.** 스크립트가 구조화 절로 박는다(아래). 본문에 손으로 다시 적지 않는다.

### 근거 ADR — `--adr`

- **Epic은 공표된 근거 ADR이 필수다**(§5) — `superseded`·`rejected`·미공표는 안 된다.
- **근거가 여럿이면 `--adr`을 반복한다.** 게이트는 전부에 걸린다 — 하나라도 걸리면 거부.
- **리프의 근거는 선택이다 — 이행 추적의 자리다.** 하위 축 결정을 **직접 이행**할 때만 명시한다. 부모 컨테이너의 근거를 되풀이하지 않는다. 명시하면 타입 불문 같은 게이트를 지난다.
- 굳은 결정을 이행하는 일이 낱개 하나면 그냥 리프로 발행하고 명시한다. Epic은 묶을 낱개가 여럿일 때 세운다.
- **스크립트가 두 곳에 박는다**: 이슈 본문 **'근거 ADR' 절**과 Project **`ADR` 필드**.
- **문서 쪽에는 되쓰지 않는다**(§1 브리지).

### 저장소 맥락 — `--target-repo` · `--no-target-repo` · `--ref-repo` (ADR-0016 파일럿)

- **리프는 저장소 맥락에 답해야 발행된다.** *어디를 고치는가* — `--target-repo`(다수 가능)로 지정하거나, 대상이 아직 없으면(신규 저장소 생성 등) `--no-target-repo`로 부재를 명시적으로 선언한다.
- **target은 살아 있는 사실이다.** 작업 중 수정 대상이 늘면 본문 절과 필드를 먼저 갱신한다(필수). 갱신의 실행은 `set-repos.py`(아래).
- **ref는 구조 파악의 출발점이다.** 비완전 — 집행자는 나열 밖도 참조할 수 있다. 갱신은 권장이지 의무가 아니다.
- **컨테이너에는 담지 않는다.**
- **스크립트가 두 곳에 박는다**: 이슈 본문 **'저장소' 절**(YAML 펜스 블록)과 Project **`Target Repos` 필드**.

### 선행 의존 — `--blocked-by` · `--no-deps` (ADR-0017 파일럿)

- **리프는 선행 의존에 답해야 발행된다.** 선행 티켓을 `--blocked-by`(반복 가능)로 걸거나, 없으면 `--no-deps`로 무의존을 명시적으로 선언한다.
- **GitHub 네이티브 의존 관계(blocked by)에 건다** — 본문 절·Project 필드는 없다. **사이드바에서 손으로 걸지 않는다** — 갱신은 언제나 `set-deps.py`다(발행과 같은 게이트).
- **선행은 열린 리프만.** 닫힌 이슈·컨테이너는 게이트가 거부한다. 컨테이너 티켓은 의존을 담지 않는다.
- **열린 선행 위의 착수는 집행 도구가 거부한다** — 선행의 완료 기준은 close(사람 검수)다. 작업 중 미기재 선행을 발견하면 `set-deps.py`로 **먼저 갱신한다(필수)**.

### 사후 기입·갱신 — `set-adr.py` · `set-repos.py` · `set-deps.py`

```bash
set-adr.py --issue <N> --adr ADR-NNNN... | --clear

set-repos.py --issue <N> \
  --target-repo owner/name... | --no-target-repo \
  [--ref-repo owner/name]...

set-deps.py --issue <N> --blocked-by <M>... | --no-deps
```

세 스크립트의 공통 규칙:

- 발행과 **같은 게이트**를 지나 **같은 자리**를 다시 쓴다 (`set-adr`·`set-repos`는 본문 절 + Project 필드, `set-deps`는 네이티브 의존 관계).
- **통째로 교체** — 부분 수정이 아니라 전체 답을 다시 낸다.
- **손으로 고치지 않는다** — 갱신은 언제나 스크립트다.

`set-adr.py`:

- `--clear`는 **Epic 외 전용**이다. 근거가 틀렸다면 올바른 전체 목록을 `--adr`로 다시 낸다.

`set-repos.py`:

- **'저장소' 절이 없는 리프**에는 절을 새로 기입하고, 산문으로 쓰인 절은 YAML 블록으로 교체한다 — 기입과 갱신이 같은 자리를 지난다. 기존 티켓에 저장소를 연결할 때 이것을 쓴다.

`set-deps.py`:

- `--blocked-by` 나열이 **선행의 전부**가 된다 — 나열 밖 기존 관계는 제거된다. `--no-deps`는 전부 제거(무의존).

## 3. 계층을 잇는다

```bash
link-sub.py --parent <N> --child <M>
```

스크립트가 거부하는 것은 둘뿐이다(ADR-0010) — **리프는 부모가 될 수 없다 · Epic은 하위가 될 수 없다.** 깊이 상한은 없다(§5) — Feature 밑에 Feature도 온다. **3층을 권장한다.**

```
근거 ADR ★공표★ ──→ Epic          ← accepted 요구는 착수의 문(집행 도구)
                          ├─ Task            ← 평시: 바로 연결
                          └─ Feature         ← 리프를 더 묶을 때 (ADR 선택)
                                └─ Task

Feature                                      ← Epic 없이 최상위에서도 가능 (ADR 선택)
  ├─ Task
  └─ Feature                                 ← 더 묶을 수 있다 — 필요할 때만. 권장은 3층
        └─ Task
```

## 4. 하지 않는 것

- **close**(§5) — 스크립트가 없다. 사람이 한다.
- **`Closes #N`** 을 PR·커밋에 쓰지 않는다.
- **Status 전이** — 타입별 초기값(`Draft`·`Todo`) 이후는 건드리지 않는다. 사람이 보드에서 옮긴다 — Draft 해제(확신 판정)도, 종착(`Done`·`Cancelled`)도 사람이다. 폐기는 티켓 삭제가 아니라 `Cancelled`다(ADR-0033).
