<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-ref-adr — 결정과 얽힌 논의 (discussion `ref-adrs` 에서 파생)

*ADR 은 discussion 을 가리키지 않는다(자족성) — 역방향 조회는 이 뷰가 답한다. discussion 은 보관을 약속하지 않으므로 이 목록은 편의이지 근거가 아니다.*

## ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `active`

## ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `active`

## ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `done`

## ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다

- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `done`

## ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `done`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `done`

## ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `done`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `done`

## ADR-0021 — 계약은 호환 확장으로만 진화한다: 소비자를 깨뜨리는 배포를 금지한다

- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `done`
- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `active`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `done`

## ADR-0025 — 호환의 정의는 계약이 소유한다: 생성 코드 층위까지, 쌍방 의무로

- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `active`

## ADR-0026 — 구형의 제거는 이행 증명이 게이트다: 표시가 아니라 티켓이 제거를 보증한다

- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `active`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `done`

