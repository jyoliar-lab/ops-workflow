<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-subject / api-composer (25)

topic·type 을 가로지른다 — 세부 주제 검색의 유일한 수단이다.

| id | type | topic | status | 문서 |
|---|---|---|---|---|
| ADR-0014 | adr | careerhub-front | accepted | [ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)](../../careerhub-front/adr/adr-0014-derive-rest-types-from-backend-spec.md) |
| ADR-0018 | adr | careerhub | accepted | [ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다](../../careerhub/adr/adr-0018-spec-first-rest-contract-source.md) |
| ADR-0028 | adr | careerhub | accepted | [ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다](../../careerhub/adr/adr-0028-delegate-authentication-to-external-idp.md) |
| ADR-0029 | adr | careerhub | accepted | [ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다](../../careerhub/adr/adr-0029-data-path-local-token-verification.md) |
| ADR-0031 | adr | careerhub | accepted | [ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다](../../careerhub/adr/adr-0031-issuance-time-claim-injection.md) |
| — | discussion | careerhub-front | done | [careerhub-front 리뉴얼 — 결정 축 벌리기](../../careerhub-front/discussion/260717_1456_frontend-renewal-decision-axes.md) |
| — | discussion | careerhub-front | rejected | [계측 — 무엇을 신뢰할 수 있고, 어디서 보내나 (축 H)](../../careerhub-front/discussion/260717_1617_measurement-trust-and-transport.md) |
| — | discussion | careerhub-front | active | [아픔을 무엇이 "할 수 없게" 만드나 — 린트·토큰·테스트, 그리고 빠져 있던 둘](../../careerhub-front/discussion/260717_2041_what-enforces-frontend-quality.md) |
| — | discussion | careerhub-front | active | [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) |
| — | discussion | careerhub-front | active | [회귀를 무엇이 잡나 — 그리고 그물이 무언가를 실제로 막나](../../careerhub-front/discussion/260722_1618_regression-net-and-merge-gate.md) |
| — | discussion | careerhub-front | done | [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) |
| — | discussion | careerhub | done | [api-composer OpenAPI 스펙의 원천 — code-first vs spec-first](../../careerhub/discussion/260726_1653_openapi-spec-source-of-truth.md) |
| — | discussion | careerhub | done | [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) |
| — | discussion | careerhub | done | [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) |
| — | discussion | careerhub | done | [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) |
| — | discussion | careerhub | active | [auth-service의 구조적 결함 — 공개 전환 전에 무엇을 정하고 무엇을 지금 닫나](../../careerhub/discussion/260804_1735_auth-service-structural-defects.md) |
| — | discussion | careerhub | done | [auth-service를 다시 짓는다면 로그인을 무엇으로 구현하나 — 직접 구현과 기성 IdP 사이](../../careerhub/discussion/260804_1831_auth-rebuild-implementation-approach.md) |
| — | discussion | careerhub | done | [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) |
| — | discussion | careerhub | active | [제품을 안 들이고 auth-service만 고친다면 — 규격이 실제로 요구하는 것과, 줄 고치기로는 안 닫히는 것](../../careerhub/discussion/260805_1323_asvs-conformance-gaps-auth-service.md) |
| — | discussion | careerhub | active | [인증에 무엇이 요구되고, 지금 코드의 어디가 왜 어긋나는가 — 그리고 그중 무엇이 진짜 의무인가](../../careerhub/discussion/260805_1334_auth-requirements-to-code-mapping.md) |
| — | discussion | careerhub | active | [결정 후보 — 무엇을 정하고, 무엇이 닫히고, 어느 티켓이 그때까지 못 나가나](../../careerhub/discussion/260805_1550_auth-decision-candidates-and-ticket-conflicts.md) |
| — | discussion | careerhub | done | [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) |
| — | discussion | careerhub | active | [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) |
| — | discussion | careerhub | done | [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) |
| — | discussion | careerhub | done | [게이트웨이 엣지 JWT 검증 패턴 — 해부와 careerhub 대입](../../careerhub/discussion/260806_2054_gateway-edge-jwt-verification-pattern.md) |
