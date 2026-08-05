<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-type / discussion (33)

| status | topic | subjects | ref-adrs | 문서 |
|---|---|---|---|---|
| done | careerhub-front | svelte, svelte-spa-router, rollup, api-composer, auth-service | — | [careerhub-front 리뉴얼 — 결정 축 벌리기](../../careerhub-front/discussion/260717_1456_frontend-renewal-decision-axes.md) |
| active | careerhub-front | nextjs | — | [렌더링 전략 — 화면별로 어디서, 언제 그리나 (축 B)](../../careerhub-front/discussion/260717_1550_rendering-strategy-per-route.md) |
| rejected | careerhub-front | api-composer, userinfo-service | — | [계측 — 무엇을 신뢰할 수 있고, 어디서 보내나 (축 H)](../../careerhub-front/discussion/260717_1617_measurement-trust-and-transport.md) |
| active | careerhub-front | api-composer | — | [아픔을 무엇이 "할 수 없게" 만드나 — 린트·토큰·테스트, 그리고 빠져 있던 둘](../../careerhub-front/discussion/260717_2041_what-enforces-frontend-quality.md) |
| active | careerhub-front | svelte | — | ["문서화된 컨벤션이 지켜지지 않았다"는 거짓이었다 — 코드로 반증](../../careerhub-front/discussion/260722_1510_documented-convention-premise-refuted.md) |
| active | careerhub-front | auth-service, api-composer, nextjs | — | [토큰 저장 — 서버가 생긴 뒤에 다시 여는 축 D](../../careerhub-front/discussion/260722_1617_token-storage-after-server-exists.md) |
| active | careerhub-front | nextjs, auth-service, api-composer | — | [회귀를 무엇이 잡나 — 그리고 그물이 무언가를 실제로 막나](../../careerhub-front/discussion/260722_1618_regression-net-and-merge-gate.md) |
| done | careerhub-front | openapi, careerhub-web, api-composer | ADR-0014, ADR-0019, ADR-0020 | [프론트가 공표 태그에서 TS 타입을 만드는 방법 — 소비자가 당긴다](../../careerhub-front/discussion/260802_1607_frontend-pulls-published-spec-tag.md) |
| done | careerhub-front | careerhub-web, careerhub-front | ADR-0011, ADR-0015 | [e2e 명세 산출물은 어디에 사나 — 그리고 기존 앱용 배선을 남기나](../../careerhub-front/discussion/260803_1329_e2e-spec-artifact-placement.md) |
| active | careerhub | adsense, posting-provider, review-crawler, posting-skillscanner | — | [careerhub 는 무엇으로 돈을 버나 — 그리고 그게 성립하나](../../careerhub/discussion/260717_1853_revenue-model-and-viability.md) |
| done | careerhub | openapi, api-composer | — | [api-composer OpenAPI 스펙의 원천 — code-first vs spec-first](../../careerhub/discussion/260726_1653_openapi-spec-source-of-truth.md) |
| done | careerhub | openapi, api-composer, careerhub-web | ADR-0014, ADR-0018, ADR-0019, ADR-0020 | [백엔드 스펙 변경을 프론트에 전파하는 방법 — 푸시인가 구독인가](../../careerhub/discussion/260730_1524_spec-change-propagation-to-frontend.md) |
| done | careerhub | grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | ADR-0018, ADR-0019, ADR-0020, ADR-0021 | [계약 선합의 패턴의 gRPC 경계 일반화 — proto의 원천은 어디인가](../../careerhub/discussion/260730_1620_contract-pattern-to-grpc-boundaries.md) |
| active | careerhub | openapi, grpc, protobuf, careerhub-web | ADR-0021, ADR-0025, ADR-0026 | [비호환 변경의 분류와 deprecated의 수명 — ADR-0021의 미결정 지대](../../careerhub/discussion/260730_2045_breaking-taxonomy-and-deprecation-lifecycle.md) |
| done | careerhub | openapi, grpc, protobuf, api-composer, posting-service, review-service, userinfo-service | ADR-0019, ADR-0020, ADR-0021, ADR-0026 | [런타임 계약 어긋남 — provider와 consumer가 다른 계약으로 동작하는 것을 무엇이 막는가](../../careerhub/discussion/260801_1806_runtime-contract-skew-prevention.md) |
| active | careerhub | auth-service, api-composer, jwt, google-oauth, postgresql, careerhub-front | — | [auth-service의 구조적 결함 — 공개 전환 전에 무엇을 정하고 무엇을 지금 닫나](../../careerhub/discussion/260804_1735_auth-service-structural-defects.md) |
| done | careerhub | auth-service, google-oauth, oidc, jwt, api-composer, naver, dex, zitadel, keycloak, openfga | — | [auth-service를 다시 짓는다면 로그인을 무엇으로 구현하나 — 직접 구현과 기성 IdP 사이](../../careerhub/discussion/260804_1831_auth-rebuild-implementation-approach.md) |
| active | careerhub | auth-service, google-oauth, naver, careerhub-front | — | [비밀번호 없이 소셜 로그인만 제공해도 되는가 — 의무와, 대신 지는 대가](../../careerhub/discussion/260805_1245_password-free-social-only-obligations.md) |
| active | careerhub | auth-service, userinfo-service, api-composer, postgresql, mongodb, jwt | — | [auth-service의 user_id가 다른 서비스의 인덱스로 쓰이는 것은 적절한가](../../careerhub/discussion/260805_1308_storage-independent-user-identifier.md) |
| active | careerhub | auth-service, api-composer, careerhub-front, jwt, oidc, google-oauth, naver, postgresql | — | [제품을 안 들이고 auth-service만 고친다면 — 규격이 실제로 요구하는 것과, 줄 고치기로는 안 닫히는 것](../../careerhub/discussion/260805_1323_asvs-conformance-gaps-auth-service.md) |
| active | careerhub | auth-service, api-composer, careerhub-front, jwt, google-oauth, postgresql | — | [인증에 무엇이 요구되고, 지금 코드의 어디가 왜 어긋나는가 — 그리고 그중 무엇이 진짜 의무인가](../../careerhub/discussion/260805_1334_auth-requirements-to-code-mapping.md) |
| active | careerhub | auth-service, api-composer, careerhub-front, jwt, google-oauth, postgresql | — | [결정 후보 — 무엇을 정하고, 무엇이 닫히고, 어느 티켓이 그때까지 못 나가나](../../careerhub/discussion/260805_1550_auth-decision-candidates-and-ticket-conflicts.md) |
| active | homelab | prometheus, alertmanager, kubelet, longhorn, kube-prometheus-stack | — | [Prometheus TSDB 만석과 이중 감시 실패 — 2026-07-30 장애 기록](../../homelab/discussion/260730_2245_prometheus-tsdb-full-double-monitoring-failure.md) |
| active | homelab | prometheus, grafana, kube-prometheus-stack | — | [룰이 참조하는 메트릭의 부재 감지 — 공식 기능·공식 가이드·대안 도구 조사](../../homelab/discussion/260731_1233_rule-metric-absence-detection-options.md) |
| active | ops-workflow | claude-code-skills | — | [skill 초판 마찰 로그](../../ops-workflow/discussion/260712_1731_skill-friction-log.md) |
| active | ops-workflow | adr | — | [ADR 선행 사례 조사 — 무엇이 표준이고, 무엇이 우리 발명이고, 무엇이 실패하는가](../../ops-workflow/discussion/260714_1417_adr-prior-art-survey.md) |
| active | ops-workflow | adr | — | [ADR 문서를 무슨 포맷으로 적을 것인가](../../ops-workflow/discussion/260715_1401_adr-document-format.md) |
| active | ops-workflow | adr | ADR-0004, ADR-0005 | [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../../ops-workflow/discussion/260715_1551_cross-adr-references.md) |
| active | ops-workflow | github-issues, github-projects, issue-types | — | [티켓(컨트롤 플레인) 결정을 ADR로 승격하기 — 후보 분해와 논점](../../ops-workflow/discussion/260716_1348_ticket-decisions-adr-candidates.md) |
| done | ops-workflow | ticket-engineer | — | [ticket-engineer 워크스페이스 엣지 케이스 — 낡은 클론·남의 브랜치·중단된 작업](../../ops-workflow/discussion/260722_2030_ticket-engineer-workspace-edge-cases.md) |
| active | ops-workflow | github-issues, issue-types | — | [티켓 본문 구성 — 공통 계약과 타입별 절의 층화 제안](../../ops-workflow/discussion/260723_2039_ticket-body-structure.md) |
| done | ops-workflow | github-issues, github-projects, ticket-engineer | — | [PR 머지와 티켓 종료 — close는 판단인가 의례인가](../../ops-workflow/discussion/260727_1608_pr-merge-auto-close.md) |
| rejected | palworld | palworld-server | — | [팰월드 1.0 서버를 홈랩 쿠버네티스에](../../palworld/discussion/260726_0149_palworld-server-on-homelab-k8s.md) |
