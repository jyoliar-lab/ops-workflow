<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-type / adr (35)

| id | status | topic | subjects | 문서 |
|---|---|---|---|---|
| ADR-0001 | proposed | ops-workflow | github-issues, github-projects | [ADR-0001 — 작업 추적과 결정 기록을 두 개의 플레인으로 가른다](../../ops-workflow/adr/adr-0001-two-plane-control-knowledge.md) |
| ADR-0002 | proposed | ops-workflow | adr | [ADR-0002 — 결정의 근거를 ADR로 남긴다](../../ops-workflow/adr/adr-0002-record-decisions-as-adr.md) |
| ADR-0003 | proposed | ops-workflow | adr | [ADR-0003 — ADR 본문은 다섯 부분으로 이루어진다](../../ops-workflow/adr/adr-0003-adr-body-structure.md) |
| ADR-0004 | proposed | ops-workflow | adr | [ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다](../../ops-workflow/adr/adr-0004-adr-metadata-fields.md) |
| ADR-0005 | proposed | ops-workflow | adr, markdown | [ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다](../../ops-workflow/adr/adr-0005-markdown-gfm-body.md) |
| ADR-0006 | proposed | ops-workflow | adr | [ADR-0006 — ADR 본문은 proposed를 벗어나면 통째로 얼어붙는다](../../ops-workflow/adr/adr-0006-accepted-adr-freezes-whole.md) |
| ADR-0007 | proposed | ops-workflow | adr | [ADR-0007 — ADR의 크기는 공동무효 단위로 정한다](../../ops-workflow/adr/adr-0007-adr-size-by-cotermination.md) |
| ADR-0008 | proposed | ops-workflow | adr, yaml | [ADR-0008 — ADR 메타데이터는 YAML frontmatter로 인코딩한다](../../ops-workflow/adr/adr-0008-yaml-frontmatter-encoding.md) |
| ADR-0009 | proposed | ops-workflow | github-issues, issue-types | [ADR-0009 — 작업 이슈는 정확히 하나의 타입을 갖는다](../../ops-workflow/adr/adr-0009-single-type-per-work-item.md) |
| ADR-0010 | proposed | ops-workflow | github-issues, issue-types | [ADR-0010 — 이슈 타입은 묶는 것과 수행하는 것으로 갈린다](../../ops-workflow/adr/adr-0010-container-and-leaf-types.md) |
| ADR-0011 | accepted | careerhub-front | — | [ADR-0011 — careerhub-front를 재작성한다 (점진 개선하지 않는다)](../../careerhub-front/adr/adr-0011-rewrite-frontend-from-scratch.md) |
| ADR-0012 | accepted | careerhub-front | nextjs, react | [ADR-0012 — careerhub-front의 스택으로 Next.js(React)를 채택한다](../../careerhub-front/adr/adr-0012-adopt-nextjs-for-frontend.md) |
| ADR-0013 | accepted | careerhub-front | typescript | [ADR-0013 — careerhub-front를 TypeScript로 짓는다 (순수 JavaScript로 짓지 않는다)](../../careerhub-front/adr/adr-0013-adopt-typescript-for-frontend.md) |
| ADR-0014 | accepted | careerhub-front | openapi, api-composer | [ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)](../../careerhub-front/adr/adr-0014-derive-rest-types-from-backend-spec.md) |
| ADR-0015 | accepted | careerhub-front | tailwind | [ADR-0015 — 스타일 토큰을 Tailwind로 강제한다 (정의에 그치지 않는다)](../../careerhub-front/adr/adr-0015-enforce-style-tokens-with-tailwind.md) |
| ADR-0016 | proposed | ops-workflow | github-issues, github-projects | [ADR-0016 — 리프 티켓은 수정 대상 저장소와 참조 저장소를 명시한다](../../ops-workflow/adr/adr-0016-leaf-ticket-declares-repo-context.md) |
| ADR-0017 | proposed | ops-workflow | github-issues, ticket-engineer | [ADR-0017 — 리프 티켓은 선행 의존을 명시하고, 열린 선행 위에는 착수하지 않는다](../../ops-workflow/adr/adr-0017-leaf-ticket-declares-dependencies.md) |
| ADR-0018 | accepted | careerhub | openapi, api-composer | [ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다](../../careerhub/adr/adr-0018-spec-first-rest-contract-source.md) |
| ADR-0019 | accepted | careerhub | openapi, grpc, protobuf | [ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다](../../careerhub/adr/adr-0019-publish-contract-agreement-before-implementation.md) |
| ADR-0020 | accepted | careerhub | openapi, grpc, protobuf | [ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다](../../careerhub/adr/adr-0020-contract-source-in-provider-repo.md) |
| ADR-0021 | proposed | careerhub | openapi, grpc, protobuf | [ADR-0021 — 계약은 호환 확장으로만 진화한다: 소비자를 깨뜨리는 배포를 금지한다](../../careerhub/adr/adr-0021-contract-evolves-by-compatible-extension.md) |
| ADR-0022 | proposed | ops-workflow | discussion, adr | [ADR-0022 — discussion은 최소한의 메타데이터를 갖는다](../../ops-workflow/adr/adr-0022-discussion-minimal-metadata.md) |
| ADR-0023 | proposed | ops-workflow | discussion, adr | [ADR-0023 — 사고의 발산은 discussion 문서로 남긴다](../../ops-workflow/adr/adr-0023-record-divergence-as-discussion.md) |
| ADR-0024 | proposed | ops-workflow | discussion | [ADR-0024 — discussion은 보관도 동결도 약속하지 않는다](../../ops-workflow/adr/adr-0024-discussion-no-retention-no-freeze.md) |
| ADR-0025 | proposed | careerhub | openapi, grpc, protobuf | [ADR-0025 — 호환의 정의는 계약이 소유한다: 생성 코드 층위까지, 쌍방 의무로](../../careerhub/adr/adr-0025-contract-owns-compatibility-definition.md) |
| ADR-0026 | proposed | careerhub | openapi, grpc, protobuf, careerhub-web | [ADR-0026 — 구형의 제거는 이행 증명이 게이트다: 표시가 아니라 티켓이 제거를 보증한다](../../careerhub/adr/adr-0026-removal-gated-by-proven-migration.md) |
| ADR-0027 | accepted | careerhub | auth-service, userinfo-service, postgresql, mongodb | [ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다](../../careerhub/adr/adr-0027-storage-independent-user-identifier.md) |
| ADR-0028 | accepted | careerhub | auth-service, api-composer, careerhub-front, oidc, jwt, google-oauth, naver | [ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다](../../careerhub/adr/adr-0028-delegate-authentication-to-external-idp.md) |
| ADR-0029 | accepted | careerhub | auth-service, api-composer, jwt, oidc | [ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다](../../careerhub/adr/adr-0029-data-path-local-token-verification.md) |
| ADR-0030 | accepted | careerhub | zitadel, keycloak, postgresql, auth-service | [ADR-0030 — IdP 제품으로 Zitadel을 채택한다](../../careerhub/adr/adr-0030-adopt-zitadel-as-idp.md) |
| ADR-0031 | accepted | careerhub | auth-service, api-composer, jwt, oidc | [ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다](../../careerhub/adr/adr-0031-issuance-time-claim-injection.md) |
| ADR-0032 | proposed | ops-workflow | adr | [ADR-0032 — 정책 ADR은 proposed로 운영한다: 검증은 하네스가, accept는 미룬다](../../ops-workflow/adr/adr-0032-policy-adr-defers-accept.md) |
| ADR-0033 | proposed | ops-workflow | github-issues, github-projects | [ADR-0033 — 티켓 Status는 여섯이다: 진행 단계와 확신만 표현한다](../../ops-workflow/adr/adr-0033-ticket-status-roster-and-meaning.md) |
| ADR-0034 | proposed | homelab | jyoliar-platform-terraform, jyoliar-k8s, argocd | [ADR-0034 — terraform은 GitOps가 생성한 인프라에 의존하지 않는다](../../homelab/adr/adr-0034-terraform-gitops-dependency-direction.md) |
| ADR-0035 | proposed | ops-workflow | digest, discussion, adr | [ADR-0035 — 수렴한 논의의 결론은 digest 문서로 증류한다](../../ops-workflow/adr/adr-0035-distill-conclusions-into-digest.md) |
