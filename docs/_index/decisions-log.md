<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# decisions-log — accepted ADR

*accept 순 — 검토가 끝난 시각(`accepted_at`) 기준. **동결(공표) 순서와는 다를 수 있다.***

| id | accepted_at | topic | subjects | parent | 문서 |
|---|---|---|---|---|---|
| ADR-0011 | 2026-07-18T15:12:52+09:00 | careerhub-front | — | — | [ADR-0011 — careerhub-front를 재작성한다 (점진 개선하지 않는다)](../careerhub-front/adr/adr-0011-rewrite-frontend-from-scratch.md) |
| ADR-0012 | 2026-07-18T15:12:53+09:00 | careerhub-front | nextjs, react | ADR-0011 | [ADR-0012 — careerhub-front의 스택으로 Next.js(React)를 채택한다](../careerhub-front/adr/adr-0012-adopt-nextjs-for-frontend.md) |
| ADR-0013 | 2026-07-22T17:44:23+09:00 | careerhub-front | typescript | ADR-0011 | [ADR-0013 — careerhub-front를 TypeScript로 짓는다 (순수 JavaScript로 짓지 않는다)](../careerhub-front/adr/adr-0013-adopt-typescript-for-frontend.md) |
| ADR-0014 | 2026-07-22T17:44:23+09:00 | careerhub-front | openapi, api-composer | ADR-0013 | [ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)](../careerhub-front/adr/adr-0014-derive-rest-types-from-backend-spec.md) |
| ADR-0015 | 2026-07-22T17:44:23+09:00 | careerhub-front | tailwind | ADR-0011 | [ADR-0015 — 스타일 토큰을 Tailwind로 강제한다 (정의에 그치지 않는다)](../careerhub-front/adr/adr-0015-enforce-style-tokens-with-tailwind.md) |
| ADR-0018 | 2026-07-26T18:26:11+09:00 | careerhub | openapi, api-composer | — | [ADR-0018 — REST 계약의 원천을 코드에서 독립한 명세에 두고, 서버를 생성 인터페이스로 구속한다](../careerhub/adr/adr-0018-spec-first-rest-contract-source.md) |
| ADR-0019 | 2026-08-01T15:22:29+09:00 | careerhub | openapi, grpc, protobuf | — | [ADR-0019 — 계약 합의는 구현 완료 전에 공표한다: 공표 지점은 원천의 머지다](../careerhub/adr/adr-0019-publish-contract-agreement-before-implementation.md) |
| ADR-0020 | 2026-08-01T15:22:29+09:00 | careerhub | openapi, grpc, protobuf | — | [ADR-0020 — 계약 원천은 그 계약의 provider 저장소에 두고, 소비자는 공표물에 결합한다](../careerhub/adr/adr-0020-contract-source-in-provider-repo.md) |
| ADR-0027 | 2026-08-10T18:43:00+09:00 | careerhub | auth-service, userinfo-service, postgresql, mongodb | — | [ADR-0027 — 시스템 전역 사용자 정체성은 저장소 독립적으로 발급된 불변 식별자로 한다](../careerhub/adr/adr-0027-storage-independent-user-identifier.md) |
| ADR-0028 | 2026-08-10T18:43:00+09:00 | careerhub | auth-service, api-composer, careerhub-front, oidc, jwt, google-oauth, naver | — | [ADR-0028 — 인증은 외부 IdP 제품이 소유하고, 인가·도메인 상태는 앱이 소유한다](../careerhub/adr/adr-0028-delegate-authentication-to-external-idp.md) |
| ADR-0029 | 2026-08-10T18:43:00+09:00 | careerhub | auth-service, api-composer, jwt, oidc | ADR-0028 | [ADR-0029 — 토큰의 신뢰는 데이터 경로의 로컬 검증으로만 얻는다](../careerhub/adr/adr-0029-data-path-local-token-verification.md) |
| ADR-0030 | 2026-08-10T18:43:00+09:00 | careerhub | zitadel, keycloak, postgresql, auth-service | ADR-0028 | [ADR-0030 — IdP 제품으로 Zitadel을 채택한다](../careerhub/adr/adr-0030-adopt-zitadel-as-idp.md) |
| ADR-0031 | 2026-08-10T18:43:00+09:00 | careerhub | auth-service, api-composer, jwt, oidc | ADR-0028 | [ADR-0031 — 인가 전파는 발급 시점 클레임 주입으로 한다](../careerhub/adr/adr-0031-issuance-time-claim-injection.md) |
