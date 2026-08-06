---
type: discussion
topic: ops-workflow
subjects: [github-issues, github-projects, adr, ticket-engineer]
status: active
ticket:
---

# 티켓 Draft 상태와 착수 게이트 — 게이트를 발행에서 착수로 옮긴다

## 문제

ADR·discussion만으로는 결정에 확신을 갖기 어렵다. 결정의 타당성은 **구체적인 실행 계획**을 세워 봐야 드러나는데, 계획의 자연스러운 표현형은 티켓(무엇을, 어떤 순서로, 어디를 고치며)이다. 그런데 현행 게이트는 Epic 발행에 accepted ADR을 요구한다 — **결정이 굳기 전에는 계획을 티켓으로 펼 수 없다.**

결과적으로 "결정 → 계획"의 일방향만 지원되고, **"계획을 펴 보며 결정을 검증한다"는 순환**이 막혀 있다. 티켓 초안 발급이 가능해지면 티켓 자체가 결정의 검증 도구가 된다.

한 줄로: 지금은 *"결정이 굳기 전엔 계획 자체를 못 편다"* — 바꾸면 *"계획은 펼 수 있되, 굳기 전엔 착수할 수 없다"*.

## 설계

### ① Status 로스터를 개편한다 — `Draft`를 넣고 8개를 5개로

```
현행: Backlog · Todo · Triage · In Progress · Diagnosed · Recovering · In Review · Done  (8)
개편: Draft · Todo · In Progress · In Review · Done  (5)

Epic·Feature·Task:  Draft(초기) → Todo(사람 전환) → In Progress → In Review → Done
Bug:                Todo(초기) → In Progress → In Review → Done
```

- **Epic·Feature·Task의 초기 Status = `Draft`.** **Draft와 Todo의 결정적 차이는 "이 작업이 진행되어도 양호한가"의 확신이다** — Draft = 확신 전(계획·검토 중), Todo = 확신 후(진행 가능 — 지금 집는가는 별개). **Draft 해제는 사람이 한다** — 전이 스크립트는 두지 않는다("Status는 사람의 것" §5 유지).
- **`Backlog`는 제거한다.** Backlog가 사라지면 Todo = "진행 가능한 것 전부"가 되고, 긴급도·보류는 상태 축이 아니다 — **보류는 Todo에서 집지 않는 것**이지 별도 상태가 아니다. 확신이 아직 없다면 그것은 보류가 아니라 Draft다. (실례: #29 Feature가 제목에 "(작업 보류)"라 쓰고 Backlog에 앉아 있었다 — 확신이 선 보류이므로 개편 후 자리는 Todo다.)
- **Bug는 Draft 없이 `Todo`로 태어난다.** 버그는 발견 시점의 관찰을 그대로 쓰고, 조사 결과를 코멘트로 갱신하는 것까지가 작업이다 — 즉각 대처가 우선이라 "계획중"이 성립하지 않는다. 초기값을 In Progress로 두지 않는다 — 착수 게이트는 Todo → In Progress 전이 직전에 서므로, 초기값이 In Progress면 게이트를 구조적으로 건너뛴다.
- **Bug 사다리(`Triage`·`Diagnosed`·`Recovering`)는 제거한다.** 출처는 초기 마찰 로그의 구상("계획된 일은 Backlog→Todo, 터진 일은 Triage→Diagnosed")인데, GitHub이 타입별 상태 강제를 지원하지 않아 도구는 단일 초기값(Backlog)만 넣게 됐고 사다리는 배선된 적이 없다 — **Bug가 Backlog로 들어간 것도 결정이 아니라 그 부산물이었다.** 실측: Bug 티켓 전체 3건(#23·24·25)이 전부 즉시 처리·종료됐고 사다리에 머문 티켓이 없다. 조사의 진행("아는가")은 상태가 아니라 코멘트 이력이 담는다 — Bug 독트린과 정합.

### ② 발행 게이트를 완화한다

- 명시된 근거 ADR이 **`superseded`·`rejected`가 아닌 한 발행을 거부하지 않는다.** proposed로도 Epic을 발행할 수 있다.
- **Epic의 근거 목록 존재 요구는 유지한다** — `--adr` 없이 Epic을 발행할 수 없다. 약화되는 것은 ADR의 **상태 조건뿐**이다: "accepted 전제"가 "존재·공표 전제(발행) + accepted(착수)"로 갈라진다.
- **공표(push) 요구는 유지한다.** 미공표 ADR을 걸면 티켓의 문서 링크가 죽은 링크로 태어난다(ADR-0006의 논거) — status의 문제가 아니라 참조 대상의 존재 문제다.
- **리프의 저장소 맥락·선행 의존 답변은 여전히 발행 필수다**(ADR-0016·0017 유지). 완화되는 것은 ADR의 accept 요구뿐이다.

### ③ 착수 게이트를 신설한다 — 강제는 소비 지점에서

ticket-engineer의 착수 스크립트(/ticket-run)가 착수 시점에 검사한다:

1. 대상 티켓에서 **부모 티켓 계층을 거슬러 올라가며** 두 가지를 수집한다: 관련 ADR 전부(리프 자신의 근거 + Feature/Epic 조상의 근거)와 **부모들의 티켓 Status**.
2. 판정:
   - ADR 중 하나라도 accepted가 아니다 → **착수 거부**
   - 자신 또는 어느 부모의 Status가 `Todo`·`In Progress` 밖이다(특히 `Draft`) → **착수 거부**
   - 둘 다 통과 → 진행
3. 진행 시, **`Todo`에 머물러 있는 부모는 `In Progress`로 전환해 준다** — 리프의 착수는 곧 그 묶음의 착수다. 이것은 사람이 지시한 리프 착수의 **파생 전이**이므로 "Status는 사람의 것" 규범과 충돌하지 않는다(현행도 사람이 지시한 착수 전이는 도구가 넣는다 §5).

부모가 `In Review`·`Done`일 때의 착수 거부는 **의도된 동작이다.** 그 상태로의 전이는 사람이 한 것이므로, 그 밑에서 아직 착수할 리프가 남았다면 **사람이 전이를 실수했다는 뜻**이다 — 게이트가 그 실수를 드러내고, 사람이 부모를 진행 가능한 상태로 되돌리면 된다. 도구는 이 방향(되돌림)을 대신하지 않는다 — 파생 전이는 착수 방향(Todo → In Progress)뿐이다.

**두 조건은 독립이다.** ADR accept = *결정이 굳었는가* (기계가 판정) · Draft 해제 = *사람이 확신했는가* (사람이 판정). 착수는 둘 다, **계층 전체에 대해** 요구한다 — 사람이 리프의 Draft를 풀어도 결정이 안 굳었거나 부모가 아직 Draft면 막힌다. 부모의 확신 없이 자식이 먼저 달리는 일이 구조적으로 불가능해진다.

보드 손이동에는 게이트를 걸 수 없으므로 전이 시점 강제는 규율에 의존하게 된다. 착수 시점 강제는 ADR-0017의 *"열린 선행 위에는 착수하지 않는다"* 와 같은 패턴 — **이미 검증된 강제 지점**이다.

부모 거슬러 올라가기는 현행 *"리프는 부모 컨테이너의 근거를 되풀이하지 않는다"*(사본은 낡는다) 규약과 합성된다 — 근거를 복사하지 않아도 리프 착수가 Epic의 근거까지 게이트된다.

## 굳은 지점 (이 논의에서 답이 난 것)

| 논점 | 답 |
|---|---|
| 강제 지점 | 착수 (ticket-engineer /ticket-run). 전이 스크립트 없음 |
| 공표 요구 | 유지 — proposed여도 공표는 돼 있어야 |
| 발행 거부 기준 | superseded·rejected 참조만 거부 |
| Epic의 `--adr` 존재 | 유지 — 약화는 상태 조건뿐 |
| 리프의 target·deps 답변 | 발행 시 여전히 필수 |
| Status 로스터 | 5개: Draft·Todo·In Progress·In Review·Done — Backlog·Bug 사다리 제거 |
| 초기 Status | Epic·Feature·Task = Draft · Bug = Todo |
| Draft/Todo의 경계 | "진행되어도 양호한가"의 확신 — 보류는 상태가 아니라 Todo에서 집지 않는 것 |
| Draft 해제 | 사람 |
| 착수 게이트 검사 범위 | ADR(자신+부모 계층) 전부 accepted **그리고** 자신·부모 전부 Todo/In Progress |
| 부모가 Todo인 채 리프 착수 | 도구가 부모를 In Progress로 전환 — 사람의 리프 착수 지시의 파생 전이 |
| 부모가 In Review·Done | 착수 거부 — 사람의 전이 실수 신호. 사람이 부모를 되돌린다(도구는 되돌리지 않는다) |

## 열린 논점

- **도구의 착수 전이 규범과의 접속.** 현행 도구는 사람 지시로 Todo → In Progress 전이까지 넣는다(§5). 착수 게이트는 이 전이 직전에 선다 — 전이를 넣는 도구와 게이트 스크립트의 관계를 ticket-engineer 하네스에서 정한다.
- **기존 열린 티켓의 재배치.** Backlog에 앉은 열린 티켓들(#4 Epic · #7·#8·#31~#38 Task · #29 Feature)을 Draft/Todo로 옮긴다 — 사람이 보드에서, "확신이 섰는가"를 기준으로. #29(작업 보류)는 확신이 선 보류이므로 Todo다.
- **보드 옵션 정리의 순서.** Status 옵션 제거 시 그 값을 가진 카드의 처리(GitHub은 옵션 삭제 시 값을 비운다) — 재배치를 먼저, 옵션 정리를 나중에.
- **발행 후 supersede된 근거.** 착수 게이트가 자연히 잡는다(superseded ≠ accepted). Draft 티켓의 근거 정리는 set-adr로 — 별도 장치가 필요한지는 운용을 보고 판단.
- **정책 ADR의 proposed 장기 유지와의 교차.** 정책 토픽 ADR은 의도적으로 proposed로 오래 산다(260806_2317 참조). 착수 게이트의 "전부 accepted" 요구는 정책 ADR을 딛는 티켓을 착수 불가로 만든다 — 착수 게이트 ADR 저작 시 이 교차를 다룬다.

## 영향 지도 (수렴·accept 시 하네스 델타)

- **ops-workflow**: `CLAUDE.md` §5(착수 전이 문구 포함) · `create.py`(타입별 초기 Status: Draft/Todo · 게이트 완화) · `adr-gate.py`(거부 기준 변경: superseded·rejected·미공표) · `set-adr.py` · ticket `SKILL.md` · Project Status 필드 개편: `Draft` 추가 + `Backlog`·`Triage`·`Diagnosed`·`Recovering` 제거(보드 설정 — 사람)
- **ticket-engineer**: /ticket-run 착수 게이트 스크립트 — 계층 상향 ADR 수집 + accepted 검사 + Draft 검사
- **선행 조치(이미 반영)**: Feature 티켓의 ADR 연결 필수 해제 — ops-workflow `8569f9a`. 이 방향의 첫 걸음이었다.

## 다음

열린 논점이 수렴하면 ADR로 굳힌다 — 아마 두 축이다: **게이트 시점의 이동**(발행 → 착수)과 **Draft 상태의 신설**. 각각 독립적으로 뒤집힐 수 있는지(공동무효 판정)는 그때 본다. 파일럿으로 하네스에 선투입하면 steward의 `pilots.md`에 기록한다.
