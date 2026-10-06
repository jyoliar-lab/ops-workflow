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
| 단위 | 수렴 시점 1회 = 1건. 여러 discussion을 덮는다(`sources`) | ADR-0035 |
| 가변성 | 보관·동결 약속 없음. 결론이 바뀌면 **고쳐 쓰는 것이 기본**. 틀 자체가 바뀔 때(방향 폐기 · 선택 축 추가·제거)만 새 digest로 교체(`superseded_by`). 교체는 사용자 승인 | ADR-0035 · `digest` 스킬(승인) |
| 생명주기 | `current` → `superseded` | ADR-0035 |
| 메타데이터 | 공통 4 + `ref-adrs` · `sources` · `superseded_by`. 하한 | ADR-0035 · CLAUDE.md §7 |
| 경로 | `docs/{topic}/digest/YYMMDD_HHmm_<slug>.md` — 증류 시각 | CLAUDE.md §7 |
| 골격 | 결론 표(축·결론·어디에 사는가) · 버린 대안 · 기댄 사실 · 외부 조사 · 미결. 화면 하나 목표 | `digest` 스킬 |
| 저작 | design-partner. **사람이 수동 호출**. 티켓 발행과 무관 | `digest` 스킬(`disable-model-invocation`) · design-partner |
| 독자 | 사람 · context-scout 2순위 · design-partner(새 논의 전). ticket-engineer 변경 없음 | context-scout SKILL.md |
| discussion 저작 | 인터뷰 먼저 · 선택지는 검토 가능한 형태로 · 질문–답은 채팅 · 문서는 옵션·축·버린 이유 | `discussion` 스킬 |
| 기존 문서 | 45건 `active` 그대로. 차례로 digest로 증류 | 아직 없음 — 별도 작업 |

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
