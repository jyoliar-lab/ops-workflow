<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-topic / careerhub (12)

| id | type | status | subjects | 문서 |
|---|---|---|---|---|
| ADR-0018 | adr | accepted | openapi, api-composer | [ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다](../../careerhub/adr/adr-0018-spec-first-rest-contract-source.md) |
| ADR-0019 | adr | accepted | openapi, grpc, protobuf | [ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다](../../careerhub/adr/adr-0019-publish-contract-agreement-before-implementation.md) |
| ADR-0020 | adr | accepted | openapi, grpc, protobuf | [ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다](../../careerhub/adr/adr-0020-contract-source-in-provider-repo.md) |
| ADR-0021 | adr | proposed | openapi, grpc, protobuf | [ADR-0021 — 계약은 호환 확장으로만 진화한다: 소비자를 깨뜨리는 배포를 금지한다](../../careerhub/adr/adr-0021-contract-evolves-by-compatible-extension.md) |
| ADR-0025 | adr | proposed | openapi, grpc, protobuf | [ADR-0025 — 호환의 정의는 계약이 소유한다: 생성 코드 층위까지, 쌍방 의무로](../../careerhub/adr/adr-0025-contract-owns-compatibility-definition.md) |
| ADR-0026 | adr | proposed | openapi, grpc, protobuf, careerhub-web | [ADR-0026 — 구형의 제거는 이행 증명이 게이트다: 표시가 아니라 티켓이 제거를 보증한다](../../careerhub/adr/adr-0026-removal-gated-by-proven-migration.md) |
| — | discussion | active | adsense, posting-provider, review-crawler, posting-skillscanner | [careerhub 는 무엇으로 돈을 버나 — 그리고 그게 성립하나](../../careerhub/discussion/260717_1853_revenue-model-and-viability.md) |
| — | discussion | done | openapi, api-composer | [api-composer OpenAPI 스펙의 원천 — code-first vs spec-first](../../careerhub/discussion/260726_1653_openapi-spec-source-of-truth.md) |
| — | discussion | active | openapi, api-composer, careerhub-web | [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) |
| — | discussion | active | grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) |
| — | discussion | active | openapi, grpc, protobuf, careerhub-web | [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) |
| — | discussion | active | openapi, grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) |
