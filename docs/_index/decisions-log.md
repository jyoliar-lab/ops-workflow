<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — docs-index skill 이 만든다. -->

# decisions-log — accepted ADR

*accept 순 — 검토가 끝난 시각(`accepted_at`) 기준. **동결(공표) 순서와는 다를 수 있다.***

| id | accepted_at | topic | subjects | parent | 문서 |
|---|---|---|---|---|---|
| ADR-0011 | 2026-07-18T15:12:52+09:00 | careerhub-front | — | — | [ADR-0011 — careerhub-front를 재작성한다 (점진 개선하지 않는다)](../careerhub-front/adr/adr-0011-rewrite-frontend-from-scratch.md) |
| ADR-0012 | 2026-07-18T15:12:53+09:00 | careerhub-front | nextjs, react | ADR-0011 | [ADR-0012 — careerhub-front의 스택으로 Next.js(React)를 채택한다](../careerhub-front/adr/adr-0012-adopt-nextjs-for-frontend.md) |
| ADR-0013 | 2026-07-22T17:44:23+09:00 | careerhub-front | typescript | ADR-0011 | [ADR-0013 — careerhub-front를 TypeScript로 짓는다 (순수 JavaScript로 짓지 않는다)](../careerhub-front/adr/adr-0013-adopt-typescript-for-frontend.md) |
| ADR-0014 | 2026-07-22T17:44:23+09:00 | careerhub-front | openapi, api-composer | ADR-0013 | [ADR-0014 — 프론트가 쓰는 REST 타입을 백엔드 스펙에서 생성한다 (손으로 선언하지 않는다)](../careerhub-front/adr/adr-0014-derive-rest-types-from-backend-spec.md) |
| ADR-0015 | 2026-07-22T17:44:23+09:00 | careerhub-front | tailwind | ADR-0011 | [ADR-0015 — 스타일 토큰을 Tailwind로 강제한다 (정의에 그치지 않는다)](../careerhub-front/adr/adr-0015-enforce-style-tokens-with-tailwind.md) |
