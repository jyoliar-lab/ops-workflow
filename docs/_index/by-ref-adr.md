<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-ref-adr — 결정과 얽힌 논의 (discussion `ref-adrs` 에서 파생)

*ADR 은 discussion 을 가리키지 않는다(자족성) — 역방향 조회는 이 뷰가 답한다. discussion 은 보관을 약속하지 않으므로 이 목록은 편의이지 근거가 아니다.*

## ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `active`

## ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `active`

## ADR-0011 — careerhub-front를 재작성한다 (점진 개선하지 않는다)

- [e2e 명세 산출물은 어디에 사나 — 그리고 기존 앱용 배선을 남기나](../careerhub-front/discussion/260803_1329_e2e-spec-artifact-placement.md) — `done`

## ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `done`

## ADR-0015 — 스타일 토큰을 Tailwind로 강제한다 (정의에 그치지 않는다)

- [e2e 명세 산출물은 어디에 사나 — 그리고 기존 앱용 배선을 남기나](../careerhub-front/discussion/260803_1329_e2e-spec-artifact-placement.md) — `done`

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

## ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다

- [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) — `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `done`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `active`
- [Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정](../careerhub/discussion/260811_1452_zitadel-placement-social-sub-verdict.md) — `active`

## ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다

- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `active`
- [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) — `done`
- [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) — `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `done`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `active`

## ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다

- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `done`
- [게이트웨이 엣지 JWT 검증 패턴 — 해부와 careerhub 대입](../careerhub/discussion/260806_2054_gateway-edge-jwt-verification-pattern.md) — `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `done`

## ADR-0030 — IdP 제품으로 Zitadel을 채택한다

- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `active`
- [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) — `done`
- [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) — `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `done`
- [careerhub 라우팅 — 경로 기반에서 호스트 기반으로, 그리고 공개면 판정](../careerhub/discussion/260810_1801_path-to-host-based-routing.md) — `active`
- [Zitadel masterkey — 운영 중 변경(회전)은 어떻게 되는가](../careerhub/discussion/260810_1910_zitadel-masterkey-rotation-paths.md) — `active`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `active`
- [Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정](../careerhub/discussion/260811_1452_zitadel-placement-social-sub-verdict.md) — `active`

## ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다

- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `done`

