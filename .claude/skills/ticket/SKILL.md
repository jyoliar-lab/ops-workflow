---
name: ticket
description: GitHub Issue를 발행하고 계층을 연결한다 (Issue Type 지정 · sub-issue 링크 · 컨테이너 티켓의 ADR 게이트). "티켓을 만든다", "epic/feature/task/bug를 발행한다", "하위 이슈로 붙인다" 일 때 사용한다. 규약은 CLAUDE.md §5.
---

# 티켓 발행

> **잠정판(관측 장비).** 고쳤다면 고친 이유를 마찰 로그에 남긴다.

**close 하는 스크립트가 없다.** 빠뜨린 것이 아니다 — **PR 머지 ≠ 티켓 종료**(§5). 그 사이에 사용자 검수가 산다. **close는 언제나 사람이 한다.** `gh issue close`를 대신 부르지 않는다.

## 1. 타입을 판정한다 — 판단이다

| 타입 | 성격 | 전제 |
|---|---|---|
| **Epic** | 컨테이너 | **accepted 근거 ADR** |
| **Feature** | 컨테이너 (**선택적**) | **accepted ADR** — Epic 근거 ADR의 하위 축 |
| **Task** / **Bug** | 리프 | 없음 |

- **Feature는 "epic이 방대해서" 만들지 않는다.** Task가 20개여도 결정이 하나면 Feature는 없다. **독립적으로 뒤집힐 수 있는 하위 축의 결정(sub-ADR)이 생겼을 때만** 만든다.
- **조사에는 티켓이 없다**(§5). 탐색·사고는 지식 플레인의 활동이다 — `discussion` 문서의 `status`가 스스로 상태를 표현한다. *계획된* 조사를 백로그에 올릴 때만 `Task`(완료 조건 = discussion 문서 커밋).
- `story`·`spike`는 **없다**. 스크립트가 거부한다.

## 2. 발행한다

```bash
create.py \
  --type epic|feature|task|bug \
  --title "..." \
  --body-file <path> \
  [--adr ADR-0001] \                 # epic·feature 는 필수
  [--target-repo owner/name]... \    # task·bug 는 이것 또는 --no-target-repo 가 필수
  [--no-target-repo] \               # 수정 대상 부재의 명시적 선언 (신규 저장소 생성 등)
  [--ref-repo owner/name]...         # 참조 저장소 (선택 · 비완전 목록)
```

`gh issue create` + GraphQL `updateIssueIssueType` + Project 등록. (`gh issue create` 에는 `--type` 플래그가 없다 — Issue Type 지정은 GraphQL로만 된다.)

**컨테이너 티켓은 accepted ADR을 전제한다**(§5). `--adr` 없이 epic·feature를 만들려 하면, 또는 그 ADR이 `accepted`가 아니면 **스크립트가 거부한다**(exit 1). **우회하지 않는다** — 굳지 않은 결정으로 일하지 않는다.

**근거 ADR은 스크립트가 두 곳에 박는다**(§1 브리지) — **이슈 본문**(사람이 읽고 문서로 건너간다)과 **Project의 `ADR` 필드**(기계가 정확히 필터한다). **문서 쪽에는 되쓰지 않는다** — 동결 문서는 살아 있는 필드를 담지 못한다. 브리지는 이슈가 문서를 가리키는 단방향이다.

**리프는 저장소 맥락에 답해야 발행된다**(ADR-0016 파일럿). *어디를 고치는가* — `--target-repo`(다수 가능)로 지정하거나, 대상이 아직 없으면(신규 저장소 생성 등) `--no-target-repo`로 **부재를 명시적으로 선언**한다. 침묵은 스크립트가 거부한다 — 빈 자리는 누락인지 부재인지 말하지 못한다. `--ref-repo`는 구조 파악의 출발점(**비완전** — 집행자는 나열 밖도 참조할 수 있다). 스크립트가 두 곳에 박는다 — **이슈 본문 '저장소' 절**(사람·집행자가 읽는다)과 **Project `Target Repos` 필드**(*"이 저장소를 고치는 열린 리프"* 를 기계가 필터한다).

- **target은 살아 있는 사실이다** — 작업 중 수정 대상이 늘면 본문 절과 필드를 **먼저 갱신한다(필수)**. 갱신은 발행 도구 밖이다 — 집행자·사람의 규약이다.
- **ref 갱신은 권장**이지 의무가 아니다.
- **컨테이너에는 담지 않는다** — 묶음은 여러 저장소에 걸칠 수 있다. 집행 맥락은 리프의 것이다.

새 티켓은 Project #1에 **`Status: Backlog`** 로 들어간다. **도구는 초기값만 넣는다** — 이후 전이는 사람의 것이다.

## 3. 계층을 잇는다

```bash
link-sub.py --parent <N> --child <M>
```

GraphQL `addSubIssue`. 계층은 **3층에서 멈춘다**(§5) — **GitHub의 제약**이지 ADR 깊이의 함수가 아니다. 스크립트가 검사한다: 리프(Task·Bug)는 부모가 될 수 없고, Feature 밑에는 Feature가 오지 않는다.

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
