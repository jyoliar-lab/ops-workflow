<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-subject / auth-service (27)

topic·type 을 가로지른다 — 세부 주제 검색의 유일한 수단이다.

| id | type | topic | status | 문서 |
|---|---|---|---|---|
| ADR-0027 | adr | careerhub | accepted | [ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다](../../careerhub/adr/adr-0027-storage-independent-user-identifier.md) |
| ADR-0028 | adr | careerhub | accepted | [ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다](../../careerhub/adr/adr-0028-delegate-authentication-to-external-idp.md) |
| ADR-0029 | adr | careerhub | accepted | [ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다](../../careerhub/adr/adr-0029-data-path-local-token-verification.md) |
| ADR-0030 | adr | careerhub | accepted | [ADR-0030 — IdP 제품으로 Zitadel을 채택한다](../../careerhub/adr/adr-0030-adopt-zitadel-as-idp.md) |
| ADR-0031 | adr | careerhub | accepted | [ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다](../../careerhub/adr/adr-0031-issuance-time-claim-injection.md) |
| — | discussion | careerhub-front | done | [careerhub-front 리뉴얼 — 결정 축 벌리기](../../careerhub-front/discussion/260717_1456_frontend-renewal-decision-axes.md) |
| — | discussion | careerhub-front | done | [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) |
| — | discussion | careerhub-front | active | [회귀를 무엇이 잡나 — 그리고 그물이 무언가를 실제로 막나](../../careerhub-front/discussion/260722_1618_regression-net-and-merge-gate.md) |
| — | discussion | careerhub | active | [auth-service의 구조적 결함 — 공개 전환 전에 무엇을 정하고 무엇을 지금 닫나](../../careerhub/discussion/260804_1735_auth-service-structural-defects.md) |
| — | discussion | careerhub | done | [auth-service를 다시 짓는다면 로그인을 무엇으로 구현하나 — 직접 구현과 기성 IdP 사이](../../careerhub/discussion/260804_1831_auth-rebuild-implementation-approach.md) |
| — | discussion | careerhub | active | [비밀번호 없이 소셜 로그인만 제공해도 되는가 — 의무와, 대신 지는 대가](../../careerhub/discussion/260805_1245_password-free-social-only-obligations.md) |
| — | discussion | careerhub | done | [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) |
| — | discussion | careerhub | active | [제품을 안 들이고 auth-service만 고친다면 — 규격이 실제로 요구하는 것과, 줄 고치기로는 안 닫히는 것](../../careerhub/discussion/260805_1323_asvs-conformance-gaps-auth-service.md) |
| — | discussion | careerhub | active | [인증에 무엇이 요구되고, 지금 코드의 어디가 왜 어긋나는가 — 그리고 그중 무엇이 진짜 의무인가](../../careerhub/discussion/260805_1334_auth-requirements-to-code-mapping.md) |
| — | discussion | careerhub | active | [결정 후보 — 무엇을 정하고, 무엇이 닫히고, 어느 티켓이 그때까지 못 나가나](../../careerhub/discussion/260805_1550_auth-decision-candidates-and-ticket-conflicts.md) |
| — | discussion | careerhub | done | [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) |
| — | discussion | careerhub | active | [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) |
| — | discussion | careerhub | done | [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) |
| — | discussion | careerhub | active | [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) |
| — | discussion | careerhub | done | [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) |
| — | discussion | careerhub | done | [게이트웨이 엣지 JWT 검증 패턴 — 해부와 careerhub 대입](../../careerhub/discussion/260806_2054_gateway-edge-jwt-verification-pattern.md) |
| — | discussion | careerhub | done | [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) |
| — | discussion | careerhub | active | [careerhub 라우팅 — 경로 기반에서 호스트 기반으로, 그리고 공개면 판정](../../careerhub/discussion/260810_1801_path-to-host-based-routing.md) |
| — | discussion | careerhub | active | [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) |
| — | discussion | careerhub | active | [Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정](../../careerhub/discussion/260811_1452_zitadel-placement-social-sub-verdict.md) |
| — | discussion | careerhub | done | [Zitadel 발급 훅 target/execution 등록 — GitOps 경로 조사](../../careerhub/discussion/260811_2031_zitadel-actions-target-gitops-registration.md) |
| — | discussion | careerhub | rejected | [Keycloak operator·plugin으로 클레임 훅 타겟의 GitOps 주입이 가능한가](../../careerhub/discussion/260811_2134_keycloak-operator-claim-hook-feasibility.md) |
