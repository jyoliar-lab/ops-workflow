<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-ref-adr — 결정과 얽힌 논의·digest (`ref-adrs` 에서 파생)

*ADR 은 discussion·digest 를 가리키지 않는다(자족성) — 역방향 조회는 이 뷰가 답한다. 둘 다 보관을 약속하지 않으므로 이 목록은 편의이지 근거가 아니다.*

## ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `discussion` · `active`

## ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다

- [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../ops-workflow/discussion/260715_1551_cross-adr-references.md) — `discussion` · `active`

## ADR-0011 — careerhub-front를 재작성한다 (점진 개선하지 않는다)

- [e2e 명세 산출물은 어디에 사나 — 그리고 기존 앱용 배선을 남기나](../careerhub-front/discussion/260803_1329_e2e-spec-artifact-placement.md) — `discussion` · `done`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `discussion` · `active`

## ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `discussion` · `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `discussion` · `done`
- [JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나](../careerhub/discussion/260817_1640_jwt-claim-schema-contract-source.md) — `discussion` · `active`

## ADR-0015 — 스타일 토큰을 Tailwind로 강제한다 (정의에 그치지 않는다)

- [e2e 명세 산출물은 어디에 사나 — 그리고 기존 앱용 배선을 남기나](../careerhub-front/discussion/260803_1329_e2e-spec-artifact-placement.md) — `discussion` · `done`
- [공통 UI 요소와 외부 디자인 프레임워크](../careerhub-front/discussion/260818_1852_shared-ui-and-design-framework.md) — `discussion` · `done`

## ADR-0016 — 리프 티켓은 수정 대상 저장소와 참조 저장소를 명시한다

- [TDD 집행 흐름 — ticket-engineer가 티켓 하나를 테스트부터 끝까지 집행하는 모양 (2026-10-11 시점)](../ops-workflow/digest/261011_1740_tdd-execution-flow.md) — `digest` · `current`
- [약속 게이트의 저장소별 적용 — 테스트가 없는 곳에서 약속은 무엇에 담기나](../ops-workflow/discussion/260910_1900_promise-gate-per-repository-class.md) — `discussion` · `active`
- [TDD 집행 흐름 — ticket-engineer 하네스에 red·green 을 어떻게 세우나](../ops-workflow/discussion/260930_1356_tdd-flow-in-ticket-engineer.md) — `discussion` · `done`
- [TDD 집행 흐름 — 결론](../ops-workflow/discussion/260930_1524_tdd-flow-decisions.md) — `discussion` · `done`
- [인프라 AC 의 세 종류 — 약속이 상태일 때 무엇이 증거인가](../ops-workflow/discussion/260930_1828_infra-ac-kinds.md) — `discussion` · `active`

## ADR-0017 — 리프 티켓은 선행 의존을 명시하고, 열린 선행 위에는 착수하지 않는다

- [agent 코드 생산량과 사람의 이해 병목 — 외부 조사와 이 하네스에의 대입](../ai-agent/discussion/260910_1817_agent-code-comprehension-bottleneck.md) — `discussion` · `active`
- [TDD 집행 흐름 — ticket-engineer가 티켓 하나를 테스트부터 끝까지 집행하는 모양 (2026-10-11 시점)](../ops-workflow/digest/261011_1740_tdd-execution-flow.md) — `digest` · `current`
- [약속 게이트의 저장소별 적용 — 테스트가 없는 곳에서 약속은 무엇에 담기나](../ops-workflow/discussion/260910_1900_promise-gate-per-repository-class.md) — `discussion` · `active`
- [TDD 집행 흐름 — ticket-engineer 하네스에 red·green 을 어떻게 세우나](../ops-workflow/discussion/260930_1356_tdd-flow-in-ticket-engineer.md) — `discussion` · `done`
- [TDD 집행 흐름 — 결론](../ops-workflow/discussion/260930_1524_tdd-flow-decisions.md) — `discussion` · `done`
- [인프라 AC 의 세 종류 — 약속이 상태일 때 무엇이 증거인가](../ops-workflow/discussion/260930_1828_infra-ac-kinds.md) — `discussion` · `active`

## ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다

- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `discussion` · `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `discussion` · `done`
- [JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나](../careerhub/discussion/260817_1640_jwt-claim-schema-contract-source.md) — `discussion` · `active`

## ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `discussion` · `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `discussion` · `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `discussion` · `done`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `discussion` · `done`

## ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다

- [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) — `discussion` · `done`
- [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) — `discussion` · `done`
- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `discussion` · `done`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `discussion` · `done`
- [JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나](../careerhub/discussion/260817_1640_jwt-claim-schema-contract-source.md) — `discussion` · `active`

## ADR-0021 — 계약은 호환 확장으로만 진화한다: 소비자를 깨뜨리는 배포를 금지한다

- [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) — `discussion` · `done`
- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `discussion` · `active`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `discussion` · `done`

## ADR-0022 — discussion은 최소한의 메타데이터를 갖는다

- [논의에서 설계까지 — discussion과 digest가 돌아가는 모양 (2026-10-07 시점)](../ops-workflow/digest/261006_1640_digest-layer-decisions.md) — `digest` · `current`
- [discussion 위에 결론 층을 둔다 — 읽을 수 없는 로그와 얼어붙는 영수증 사이](../ops-workflow/discussion/261006_1549_digest-layer-over-discussion.md) — `discussion` · `done`
- [discussion 작성 스킬 — 질문은 인터뷰로, 문서에는 지형과 판정만](../ops-workflow/discussion/261006_2122_discussion-skill-interview-first.md) — `discussion` · `done`

## ADR-0023 — 사고의 발산은 discussion 문서로 남긴다

- [논의에서 설계까지 — discussion과 digest가 돌아가는 모양 (2026-10-07 시점)](../ops-workflow/digest/261006_1640_digest-layer-decisions.md) — `digest` · `current`
- [discussion 위에 결론 층을 둔다 — 읽을 수 없는 로그와 얼어붙는 영수증 사이](../ops-workflow/discussion/261006_1549_digest-layer-over-discussion.md) — `discussion` · `done`
- [discussion 작성 스킬 — 질문은 인터뷰로, 문서에는 지형과 판정만](../ops-workflow/discussion/261006_2122_discussion-skill-interview-first.md) — `discussion` · `done`
- [digest 작성 스킬 — 수렴을 판정하고 거부할 수 있는 증류](../ops-workflow/discussion/261007_1623_digest-skill-refuse-and-review.md) — `discussion` · `done`
- [digest를 청사진으로 — 결정의 요약이 아니라 결정된 설계의 서술](../ops-workflow/discussion/261007_1947_digest-as-blueprint.md) — `discussion` · `done`

## ADR-0024 — discussion은 보관도 동결도 약속하지 않는다

- [논의에서 설계까지 — discussion과 digest가 돌아가는 모양 (2026-10-07 시점)](../ops-workflow/digest/261006_1640_digest-layer-decisions.md) — `digest` · `current`
- [discussion 위에 결론 층을 둔다 — 읽을 수 없는 로그와 얼어붙는 영수증 사이](../ops-workflow/discussion/261006_1549_digest-layer-over-discussion.md) — `discussion` · `done`
- [digest 작성 스킬 — 수렴을 판정하고 거부할 수 있는 증류](../ops-workflow/discussion/261007_1623_digest-skill-refuse-and-review.md) — `discussion` · `done`
- [digest를 청사진으로 — 결정의 요약이 아니라 결정된 설계의 서술](../ops-workflow/discussion/261007_1947_digest-as-blueprint.md) — `discussion` · `done`

## ADR-0025 — 호환의 정의는 계약이 소유한다: 생성 코드 층위까지, 쌍방 의무로

- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `discussion` · `active`

## ADR-0026 — 구형의 제거는 이행 증명이 게이트다: 표시가 아니라 티켓이 제거를 보증한다

- [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) — `discussion` · `active`
- [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) — `discussion` · `done`

## ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다

- [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) — `discussion` · `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `discussion` · `done`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `discussion` · `active`
- [Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정](../careerhub/discussion/260811_1452_zitadel-placement-social-sub-verdict.md) — `discussion` · `active`

## ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다

- [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) — `discussion` · `done`
- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `discussion` · `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `discussion` · `active`
- [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) — `discussion` · `done`
- [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) — `discussion` · `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `discussion` · `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `discussion` · `done`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `discussion` · `active`
- [실제 Google 연합 로그인 여정의 검증 — 스모크와 회귀 그물의 이원화](../careerhub/discussion/260820_2216_real-google-federation-journey-verification.md) — `discussion` · `active`

## ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다

- [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) — `discussion` · `done`
- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `discussion` · `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `discussion` · `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `discussion` · `done`
- [게이트웨이 엣지 JWT 검증 패턴 — 해부와 careerhub 대입](../careerhub/discussion/260806_2054_gateway-edge-jwt-verification-pattern.md) — `discussion` · `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `discussion` · `done`
- [JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나](../careerhub/discussion/260817_1640_jwt-claim-schema-contract-source.md) — `discussion` · `active`

## ADR-0030 — IdP 제품으로 Zitadel을 채택한다

- [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) — `discussion` · `done`
- [auth-service가 굳이 필요한가 — Keycloak이 원장까지 갖는 프레임의 재검토](../careerhub/discussion/260805_1635_auth-service-elimination-via-keycloak.md) — `discussion` · `done`
- [Zitadel 도입은 auth-service의 요구사항을 얼마나 해소하는가 — 항목별 판정과 잔여 목록](../careerhub/discussion/260805_1801_zitadel-coverage-of-auth-requirements.md) — `discussion` · `active`
- [Zitadel 전환 시 테스트 전용 로그인 경로는 어떻게 되는가 — 티켓 #7 재판정](../careerhub/discussion/260805_2044_test-login-path-under-zitadel.md) — `discussion` · `done`
- [외부 IdP 환경의 동의(consent) 구현 — 업계 사례 조사](../careerhub/discussion/260805_2103_consent-implementation-idp-industry-survey.md) — `discussion` · `active`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `discussion` · `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `discussion` · `done`
- [careerhub 라우팅 — 경로 기반에서 호스트 기반으로, 그리고 공개면 판정](../careerhub/discussion/260810_1801_path-to-host-based-routing.md) — `discussion` · `active`
- [Zitadel masterkey — 운영 중 변경(회전)은 어떻게 되는가](../careerhub/discussion/260810_1910_zitadel-masterkey-rotation-paths.md) — `discussion` · `active`
- [리뉴얼은 prod에 바로 — 병행 스택·컷오버·스키마 동결의 정제](../careerhub/discussion/260810_2252_renewal-parallel-stack-prod-cutover.md) — `discussion` · `active`
- [Zitadel 배치 실측 — 서브패스 가부와 소셜 sub 보존 조건 판정](../careerhub/discussion/260811_1452_zitadel-placement-social-sub-verdict.md) — `discussion` · `active`
- [Keycloak operator·plugin으로 클레임 훅 타겟의 GitOps 주입이 가능한가](../careerhub/discussion/260811_2134_keycloak-operator-claim-hook-feasibility.md) — `discussion` · `rejected`
- [실제 Google 연합 로그인 여정의 검증 — 스모크와 회귀 그물의 이원화](../careerhub/discussion/260820_2216_real-google-federation-journey-verification.md) — `discussion` · `active`

## ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다

- [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) — `discussion` · `done`
- [Zitadel의 비-JWT 인증 경로와 권한 변경의 즉시 발효](../careerhub/discussion/260806_1931_zitadel-non-jwt-auth-and-immediacy.md) — `discussion` · `done`
- [Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나](../careerhub/discussion/260807_0158_zitadel-epic-work-breakdown.md) — `discussion` · `done`
- [Zitadel 발급 훅 target/execution 등록 — GitOps 경로 조사](../careerhub/discussion/260811_2031_zitadel-actions-target-gitops-registration.md) — `discussion` · `done`
- [JWT 클레임 스키마 계약 — 원천을 어디에 어떤 포맷으로 두나](../careerhub/discussion/260817_1640_jwt-claim-schema-contract-source.md) — `discussion` · `active`

## ADR-0034 — terraform은 GitOps가 생성한 인프라에 의존하지 않는다

- [Zitadel 발급 훅 target/execution 등록 — GitOps 경로 조사](../careerhub/discussion/260811_2031_zitadel-actions-target-gitops-registration.md) — `discussion` · `done`

## ADR-0035 — 수렴한 논의의 결론은 digest 문서로 증류한다

- [논의에서 설계까지 — discussion과 digest가 돌아가는 모양 (2026-10-07 시점)](../ops-workflow/digest/261006_1640_digest-layer-decisions.md) — `digest` · `current`
- [discussion 위에 결론 층을 둔다 — 읽을 수 없는 로그와 얼어붙는 영수증 사이](../ops-workflow/discussion/261006_1549_digest-layer-over-discussion.md) — `discussion` · `done`
- [discussion 작성 스킬 — 질문은 인터뷰로, 문서에는 지형과 판정만](../ops-workflow/discussion/261006_2122_discussion-skill-interview-first.md) — `discussion` · `done`
- [digest 작성 스킬 — 수렴을 판정하고 거부할 수 있는 증류](../ops-workflow/discussion/261007_1623_digest-skill-refuse-and-review.md) — `discussion` · `done`
- [digest를 청사진으로 — 결정의 요약이 아니라 결정된 설계의 서술](../ops-workflow/discussion/261007_1947_digest-as-blueprint.md) — `discussion` · `done`

