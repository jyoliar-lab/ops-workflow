<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-topic / careerhub (32)

| id | type | status | subjects | 문서 |
|---|---|---|---|---|
| ADR-0018 | adr | accepted | openapi, api-composer | [ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다](../../careerhub/adr/adr-0018-spec-first-rest-contract-source.md) |
| ADR-0019 | adr | accepted | openapi, grpc, protobuf | [ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다](../../careerhub/adr/adr-0019-publish-contract-agreement-before-implementation.md) |
| ADR-0020 | adr | accepted | openapi, grpc, protobuf | [ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다](../../careerhub/adr/adr-0020-contract-source-in-provider-repo.md) |
| ADR-0021 | adr | proposed | openapi, grpc, protobuf | [ADR-0021 — 계약은 호환 확장으로만 진화한다: 소비자를 깨뜨리는 배포를 금지한다](../../careerhub/adr/adr-0021-contract-evolves-by-compatible-extension.md) |
| ADR-0025 | adr | proposed | openapi, grpc, protobuf | [ADR-0025 — 호환의 정의는 계약이 소유한다: 생성 코드 층위까지, 쌍방 의무로](../../careerhub/adr/adr-0025-contract-owns-compatibility-definition.md) |
| ADR-0026 | adr | proposed | openapi, grpc, protobuf, careerhub-web | [ADR-0026 — 구형의 제거는 이행 증명이 게이트다: 표시가 아니라 티켓이 제거를 보증한다](../../careerhub/adr/adr-0026-removal-gated-by-proven-migration.md) |
| ADR-0027 | adr | proposed | auth-service, userinfo-service, postgresql, mongodb | [ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다](../../careerhub/adr/adr-0027-storage-independent-user-identifier.md) |
| ADR-0028 | adr | proposed | auth-service, api-composer, careerhub-front, oidc, jwt, google-oauth, naver | [ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다](../../careerhub/adr/adr-0028-delegate-authentication-to-external-idp.md) |
| ADR-0029 | adr | proposed | auth-service, api-composer, jwt, oidc | [ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다](../../careerhub/adr/adr-0029-data-path-local-token-verification.md) |
| ADR-0030 | adr | proposed | zitadel, keycloak, postgresql, auth-service | [ADR-0030 — IdP 제품으로 Zitadel을 채택한다](../../careerhub/adr/adr-0030-adopt-zitadel-as-idp.md) |
| ADR-0031 | adr | proposed | auth-service, api-composer, jwt, oidc | [ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다](../../careerhub/adr/adr-0031-issuance-time-claim-injection.md) |
| — | discussion | active | adsense, posting-provider, review-crawler, posting-skillscanner | [careerhub 는 무엇으로 돈을 버나 — 그리고 그게 성립하나](../../careerhub/discussion/260717_1853_revenue-model-and-viability.md) |
| — | discussion | done | openapi, api-composer | [api-composer OpenAPI 스펙의 원천 — code-first vs spec-first](../../careerhub/discussion/260726_1653_openapi-spec-source-of-truth.md) |
| — | discussion | done | openapi, api-composer, careerhub-web | [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) |
| — | discussion | done | grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) |
| — | discussion | active | openapi, grpc, protobuf, careerhub-web | [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) |
| — | discussion | done | openapi, grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) |
| — | discussion | active | auth-service, api-composer, jwt, google-oauth, postgresql, careerhub-front | [auth-service의 구조적 결함 — 공개 전환 전에 무엇을 정하고 무엇을 지금 닫나](../../careerhub/discussion/260804_1735_auth-service-structural-defects.md) |
| — | discussion | done | auth-service, google-oauth, oidc, jwt, api-composer, naver, dex, zitadel, keycloak, openfga | [auth-service를 다시 짓는다면 로그인을 무엇으로 구현하나 — 직접 구현과 기성 IdP 사이](../../careerhub/discussion/260804_1831_auth-rebuild-implementation-approach.md) |
| — | discussion | active | auth-service, google-oauth, naver, careerhub-front | [비밀번호 없이 소셜 로그인만 제공해도 되는가 — 의무와, 대신 지는 대가](../../careerhub/discussion/260805_1245_password-free-social-only-obligations.md) |
| — | discussion | done | auth-service, userinfo-service, api-composer, postgresql, mongodb, jwt | [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) |
| — | discussion | active | auth-service, api-composer, careerhub-front, jwt, oidc, google-oauth, naver, postgresql | [제품을 안 들이고 auth-service만 고친다면 — 규격이 실제로 요구하는 것과, 줄 고치기로는 안 닫히는 것](../../careerhub/discussion/260805_1323_asvs-conformance-gaps-auth-service.md) |
| — | discussion | active | auth-service, api-composer, careerhub-front, jwt, google-oauth, postgresql | [인증에 무엇이 요구되고, 지금 코드의 어디가 왜 어긋나는가 — 그리고 그중 무엇이 진짜 의무인가](../../careerhub/discussion/260805_1334_auth-requirements-to-code-mapping.md) |
| — | discussion | active | auth-service, api-composer, careerhub-front, jwt, google-oauth, postgresql | [결정 후보 — 무엇을 정하고, 무엇이 닫히고, 어느 티켓이 그때까지 못 나가나](../../careerhub/discussion/260805_1550_auth-decision-candidates-and-ticket-conflicts.md) |
| — | discussion | done | auth-service, keycloak, api-composer, userinfo-service, postgresql, google-oauth, naver | [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) |
| — | discussion | active | auth-service, zitadel, api-composer, careerhub-front, userinfo-service, jwt, oidc, google-oauth, naver, postgresql | [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) |
| — | discussion | done | zitadel, auth-service, careerhub-front, oidc | [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) |
| — | discussion | active | auth-service, zitadel, keycloak, jwt, auth0, okta, cognito, azure-ad-b2c, firebase-auth | [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) |
| — | discussion | done | zitadel, jwt, oidc, auth-service, api-composer | [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) |
| — | discussion | done | api-composer, auth-service, jwt, nginx-gateway-fabric | [게이트웨이 엣지 JWT 검증 패턴 — 해부와 careerhub 대입](../../careerhub/discussion/260806_2054_gateway-edge-jwt-verification-pattern.md) |
| — | discussion | done | zitadel, auth-service, careerhub-api-composer, careerhub-web, careerhub-userinfo-service, jyoliar-k8s, jyoliar-platform-terraform, jwt, oidc, postgresql, mongodb | [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) |
| — | discussion | active | nginx-gateway-fabric, auth-service, careerhub-front, careerhub-api-composer, careerhub-web, zitadel, cert-manager | [careerhub 라우팅 — 경로 기반에서 호스트 기반으로, 그리고 공개면 판정](../../careerhub/discussion/260810_1801_path-to-host-based-routing.md) |
