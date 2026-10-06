---
type: digest
topic: ops-workflow
subjects: [discussion, digest, adr, claude-code-skills]
status: current
ref-adrs: [ADR-0035, ADR-0023, ADR-0024]
sources: [../discussion/261006_1549_digest-layer-over-discussion.md]
superseded_by:
---

# discussion 위의 결론 층 — digest (2026-10-06 시점)

## 결론

| 축 | 결론 | 어디에 사는가 |
|---|---|---|
| 타입 | discussion을 한 차례 증류한 결론 문서 `digest`를 둔다 | ADR-0035 · CLAUDE.md §3 |
| 지위 | 규범력 없음. 첫 독자는 사람. 현황은 ADR·티켓·코드만으로 파악돼야 한다. digest는 **수렴 직후부터 ADR·티켓이 생기기 전까지**의 다리 — 그 창에서 discussion 대신 읽는다 | ADR-0035 |
| 단위 | 틀 하나 = 1건. 틀은 결론 표의 행 — 논의가 정하려던 것들의 목록. 한 틀에 이르는 discussion이 여럿이면 한 digest가 덮는다(`sources`) | ADR-0035 |
| 가변성 | 보관·동결 약속 없음. 결론이 바뀌면 **고쳐 쓰는 것이 기본**. 틀 자체가 바뀔 때(방향 폐기 · 선택 축 추가·제거)만 새 digest로 교체(`superseded_by`). 교체는 사용자 승인 | ADR-0035 · `digest` 스킬(승인) |
| 생명주기 | `current` → `superseded` | ADR-0035 |
| 메타데이터 | 공통 4 + `ref-adrs` · `sources` · `superseded_by`. 하한 | ADR-0035 · CLAUDE.md §7 |
| 경로 | `docs/{topic}/digest/YYMMDD_HHmm_<slug>.md` — 증류 시각 | CLAUDE.md §7 |
| 골격 | 결론 표(축·결론·어디에 사는가, 화면 하나 상한) · **문제와 계기**(필수) · 버린 대안 · 기댄 사실 · 외부 조사 · 미결. 표 밖은 길이 자유, 시간순 누적 금지 | `digest` 스킬 |
| 자족성 | discussion이 제거돼도 결론 표와 문제·계기만으로 맥락이 선다. 본문은 discussion을 가리키지 않는다 — 경로는 `sources`에만 | `digest` 스킬 |
| 보관 관계 | digest와 discussion의 제거 순서·전제는 정하지 않는다 — 둘 다 ADR-0024 지위, 관리 판단 | 아직 없음 — 의도적 |
| 저작 | design-partner. **사람이 수동 호출**. 티켓 발행과 무관 | `digest` 스킬(`disable-model-invocation`) · design-partner |
| 독자 | 사람 · context-scout 2순위 · design-partner(새 논의 전). ticket-engineer 변경 없음 | context-scout SKILL.md |
| discussion 저작 | 인터뷰 먼저 · 선택지는 검토 가능한 형태로 · 질문–답은 채팅 · 문서는 옵션·축·버린 이유 | `discussion` 스킬 |
| 기존 문서 | 45건 `active` 그대로. 차례로 digest로 증류 | 아직 없음 — 별도 작업 |

## 문제와 계기

ops-workflow가 내는 보고·설계 산출물이 산만하다는 인상에서 시작했다.
사용자가 짚은 원인은 discussion 작성에 프로세스가 없다는 것이었다.
첫 판이 조사·옵션·사용자에게 던지는 질문을 한 문서에 한꺼번에 내놓고, 그 뒤 답·역질문·재답·결정이 같은 파일에 덧붙어 가독성이 무너졌다.

인터뷰에서 불편의 순간은 agent가 질문을 던지는 순간으로 좁혀졌다.
질문–답 왕복은 문서가 아니라 채팅에 있어야 하고, 문서에는 결과·버린 대안·이유만 남아야 했다.

처음 틀은 "임시 보고서로 선택지를 검토한 뒤 결과만 담은 discussion을 한 번에 쓴다"였다.
사용자가 이를 뒤집었다 — ADR-0024를 보면 지금의 discussion이 이미 보관도 동결도 약속하지 않는 임시 파일의 지위다.
그러므로 discussion은 로그로 두고, 그것을 한 차례 증류한 결론 문서 타입을 새로 두는 쪽이 맞다.

구조적 배경은 셋이다.
ADR은 되돌리기 어려운 결정 하나의 영수증이라 동결 비용이 있고, 수렴과 ADR·티켓 사이에는 창이 있다.
그 창에서 결론의 유일한 기록은 discussion 로그이고, context-scout와 ticket-engineer는 그 로그를 읽지 않는다.
결론만 추린 discussion(`260930_1524`)이 자구책으로 이미 나타났고 쓰이자마자 인용됐다 — 수요는 있었고 그릇이 없었다.

## 버린 대안과 이유

- **임시 보고서 → 결과만 담은 discussion.** discussion의 지위(발산의 장)를 바꾸고 그 앞에 또 임시 파일을 세운다. 지금의 discussion이 이미 그 임시 파일이다(ADR-0024).
- **discussion 상단에 결론 절을 고쳐 쓴다.** 한 파일 안의 생존형 절 — 누적이 다시 이긴다.
- **proposed ADR을 결론 그릇으로.** 원자적 결정 1건의 그릇이라 체인의 결론 여럿을 못 담는다.
- **주제별 결론 문서를 계속 갱신.** ADR-0023 ④가 기각한 생존형 문서다.
- **약한 규범력.** 동결·심사 없는 문서에 규범이 고인다.

## 기댄 사실

- discussion 73건 중 45건이 `active`. 큰 문서는 400~750줄.
- `260930_1524`가 결론 문서의 전례이고 쓰이자마자 인용됐다.
- context-scout·ticket-engineer는 discussion을 읽지 않는다 — ADR이 안 된 결론은 agent에게 보이지 않는다.

## 외부 조사

없음.

## 미결

- 기존 discussion의 소급 증류 — 어느 체인부터.
- 고쳐 쓴 digest에서 현재 결론이 읽히는가 — 읽히지 않으면 ADR-0035 무효화 조건.
