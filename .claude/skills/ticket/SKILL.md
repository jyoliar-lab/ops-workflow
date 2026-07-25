---
name: ticket
description: GitHub Issue를 발행하고 계층을 연결한다 (Issue Type 지정 · sub-issue 링크 · 컨테이너 티켓의 ADR 게이트). "티켓을 만든다", "epic/feature/task/bug를 발행한다", "하위 이슈로 붙인다" 일 때 사용한다. 규약은 CLAUDE.md §5.
---

# 티켓 발행

> **잠정판(관측 장비).** 고쳤다면 고친 이유를 마찰 로그에 남긴다.

**close 하는 스크립트가 없다.** 빠뜨린 것이 아니다. PR 머지 ≠ 티켓 종료(§5)이고, 그 사이에 사용자 검수가 산다. **close는 언제나 사람이 한다.** `gh issue close`를 대신 부르지 않는다.

## 1. 타입을 판정한다 — 판단이다

| 타입 | 성격 | 전제 |
|---|---|---|
| **Epic** | 컨테이너 | **accepted 근거 ADR** |
| **Feature** | 컨테이너 (**선택적**) | **accepted ADR** — Epic 근거 ADR의 하위 축 |
| **Task** / **Bug** | 리프 | 없음. ADR은 선택(직접 이행 시) — 명시하면 accepted여야 한다 |

- **Feature는 "epic이 방대해서" 만들지 않는다.** Task가 20개여도 결정이 하나면 Feature는 없다. 독립적으로 뒤집힐 수 있는 하위 축의 결정(sub-ADR)이 생겼을 때만 만든다.
- **조사에는 티켓이 없다**(§5). *계획된* 조사를 백로그에 올릴 때만 `Task`(완료 조건 = discussion 문서 커밋).
- `story`·`spike`는 **없다**. 스크립트가 거부한다.

## 2. 발행한다 — `create.py`

```bash
create.py \
  --type epic|feature|task|bug \
  --title "..." \
  --body-file <path> \
  [--adr ADR-0001]... \              # 반복 가능. 컨테이너 필수 · 리프 선택(직접 이행하는 결정만)
  [--target-repo owner/name]... \    # task·bug 는 이것 또는 --no-target-repo 가 필수
  [--no-target-repo] \               # 수정 대상 부재의 명시적 선언 (신규 저장소 생성 등)
  [--ref-repo owner/name]...         # 참조 저장소 (선택 · 비완전 목록)
```

`gh issue create` + GraphQL `updateIssueIssueType` + Project 등록. `gh issue create`에는 `--type` 플래그가 없다 — Issue Type 지정은 GraphQL로만 된다.

새 티켓은 Project #1에 **`Status: Backlog`** 로 들어간다. 도구는 초기값만 넣는다 — 이후 전이는 사람의 것이다(§5).

### 본문 — `templates/`의 타입별 템플릿에서 시작한다

`epic.md`(Feature도 이것 — 컨테이너 공통) · `task.md` · `bug.md`.

- **공통 절(Context · Goal · Acceptance Criteria · References)은 이름까지 한 벌이다.** 같은 질문은 같은 자리·같은 이름에서 답한다. 닫는 사람과 집행자가 그 이름을 찾는다. (Bug에는 Goal이 없다 — Expected Behavior가 그 질문에 답한다.)
- **선택 절(Requirements · Technical Notes · Environment · Evidence)은 지우지 않고 부재를 "없음"으로 명시한다.** 빈 절은 누락인지 비해당인지 말하지 못한다.
- **References는 조사에서 얻은 외부 정보 전용이다.** ADR·discussion 등 내부 문서를 넣지 않는다.
- **discussion 링크는 티켓 어디에도 넣지 않는다.** 비구조 문서는 정보 전달에 부적합하다 — 필요한 맥락은 Context로 옮겨 적는다. 근거 ADR이 없는 리프는 Context가 유일한 "왜"다. 충분히 쓴다.
- **'근거 ADR'·'저장소' 절은 템플릿에 없다.** 스크립트가 구조화 절로 박는다(아래). 본문에 손으로 다시 적지 않는다 — 사본은 낡는다.

### 근거 ADR — `--adr`

- **컨테이너는 accepted·공표된 근거 ADR이 필수다**(§5). `--adr` 없이 epic·feature를 만들려 하거나 그 ADR이 `accepted`가 아니면 스크립트가 거부한다(exit 1). **우회하지 않는다** — 굳지 않은 결정으로 일하지 않는다.
- **근거가 여럿이면 `--adr`을 반복한다.** 게이트는 전부에 걸린다 — 하나라도 미accept면 거부.
- **리프의 근거는 선택이다 — 이행 추적의 자리다.** 하위 축 결정을 **직접 이행**할 때만 명시한다(#11이 ADR-0015의 린트를 배선하는 것처럼). 부모 컨테이너의 근거를 되풀이하지 않는다 — 사본은 낡는다. 명시하면 타입 불문 같은 게이트를 지난다: 답하지 않아도 되지만, 답하면 참이어야 한다.
- accepted 결정을 이행하는 일이 낱개 하나면 그냥 리프로 발행하고 명시한다. Epic은 묶을 낱개가 여럿일 때 세운다 — 빈 컨테이너는 냄새다.
- **스크립트가 두 곳에 박는다**(§1 브리지):
  - 이슈 본문 **'근거 ADR' 절** — YAML 블록(기계용) + HEAD/permalink 링크(사람이 읽고 문서로 건너간다)
  - Project **`ADR` 필드** — 기계가 정확히 필터한다. 컨테이너의 값은 존재 근거(권위), 리프의 값은 이행 추적(비완전 — 명시된 것만 걸린다)
- **문서 쪽에는 되쓰지 않는다.** 동결 문서는 살아 있는 필드를 담지 못한다. 브리지는 이슈가 문서를 가리키는 단방향이다.

### 저장소 맥락 — `--target-repo` · `--no-target-repo` · `--ref-repo` (ADR-0016 파일럿)

- **리프는 저장소 맥락에 답해야 발행된다.** *어디를 고치는가* — `--target-repo`(다수 가능)로 지정하거나, 대상이 아직 없으면(신규 저장소 생성 등) `--no-target-repo`로 부재를 명시적으로 선언한다. 침묵은 스크립트가 거부한다 — 빈 자리는 누락인지 부재인지 말하지 못한다.
- **target은 살아 있는 사실이다.** 작업 중 수정 대상이 늘면 본문 절과 필드를 먼저 갱신한다(필수). 갱신을 시작하는 것은 도구 밖이다(집행자·사람의 규약). 갱신의 실행은 `set-repos.py`(아래).
- **ref는 구조 파악의 출발점이다.** 비완전 — 집행자는 나열 밖도 참조할 수 있다. 갱신은 권장이지 의무가 아니다.
- **컨테이너에는 담지 않는다.** 묶음은 여러 저장소에 걸칠 수 있다 — 집행 맥락은 리프의 것이다.
- **스크립트가 두 곳에 박는다**:
  - 이슈 본문 **'저장소' 절** — YAML 펜스 블록. 사람과 집행 도구가 같은 표기 하나를 읽는다.
  - Project **`Target Repos` 필드** — *"이 저장소를 고치는 열린 리프"* 를 기계가 필터한다.

### 사후 기입·갱신 — `set-adr.py` · `set-repos.py`

```bash
set-adr.py --issue <N> --adr ADR-NNNN... | --clear

set-repos.py --issue <N> \
  --target-repo owner/name... | --no-target-repo \
  [--ref-repo owner/name]...
```

두 스크립트의 공통 규칙:

- 발행과 **같은 게이트**를 지나 **같은 두 자리**(본문 절 + Project 필드)를 다시 쓴다.
- 절이 있으면 **통째로 교체**, 없으면 소급 기입. 부분 수정이 아니라 전체 답을 다시 낸다. 절은 언제나 하나다.
- **블록을 손으로 고치지 않는다.** 집행 도구의 파서가 엄격해서(emit 되는 부분집합만 수용) 형식 이탈을 거부한다. 갱신은 언제나 스크립트다.

`set-adr.py`:

- `--clear`는 **리프 전용** — 컨테이너의 근거는 존재의 전제라 철회할 수 없다. 근거가 틀렸다면 올바른 전체 목록을 `--adr`로 다시 낸다.

`set-repos.py`:

- **ADR-0016 이전에 발행된 리프**(저장소 절이 없는 티켓)에는 절을 소급 기입한다 — docs-tickets가 기존 티켓에 저장소를 연결할 때 이것을 쓴다.
- 구식 산문 절도 YAML 블록으로 교체된다 — 이 스크립트 한 번이 곧 마이그레이션이다.
- 컨테이너(Epic·Feature)와 Project 미등록 이슈는 거부한다.

## 3. 계층을 잇는다

```bash
link-sub.py --parent <N> --child <M>
```

GraphQL `addSubIssue`. 계층은 **3층에서 멈춘다**(§5) — GitHub의 제약이지 ADR 깊이의 함수가 아니다. 스크립트가 검사한다: 리프(Task·Bug)는 부모가 될 수 없고, Feature 밑에는 Feature가 오지 않는다.

```
근거 ADR ★accepted★ ──→ Epic
                          ├─ Task            ← 평시: 바로 연결
 하위 축 ADR ★accepted★ ─→ └─ Feature         ← 독립 하위 축의 결정이 생겼을 때만
                                └─ Task
```

## 4. 하지 않는 것

- **close**(§5) — 스크립트가 없다. 사람이 한다.
- **`Closes #N`** 을 PR·커밋에 쓰지 않는다.
- **Status 전이** — 초기값(`Backlog`) 이후는 건드리지 않는다. 사람이 보드에서 옮긴다.
