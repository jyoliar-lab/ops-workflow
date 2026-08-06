<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-topic / ops-workflow (27)

| id | type | status | subjects | 문서 |
|---|---|---|---|---|
| ADR-0001 | adr | proposed | github-issues, github-projects | [ADR-0001 — 작업 추적과 결정 기록을 두 개의 플레인으로 가른다](../../ops-workflow/adr/adr-0001-two-plane-control-knowledge.md) |
| ADR-0002 | adr | proposed | adr | [ADR-0002 — 결정의 근거를 ADR로 남긴다](../../ops-workflow/adr/adr-0002-record-decisions-as-adr.md) |
| ADR-0003 | adr | proposed | adr | [ADR-0003 — ADR 본문은 다섯 부분으로 이루어진다](../../ops-workflow/adr/adr-0003-adr-body-structure.md) |
| ADR-0004 | adr | proposed | adr | [ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다](../../ops-workflow/adr/adr-0004-adr-metadata-fields.md) |
| ADR-0005 | adr | proposed | adr, markdown | [ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다](../../ops-workflow/adr/adr-0005-markdown-gfm-body.md) |
| ADR-0006 | adr | proposed | adr | [ADR-0006 — ADR 본문은 proposed를 벗어나면 통째로 얼어붙는다](../../ops-workflow/adr/adr-0006-accepted-adr-freezes-whole.md) |
| ADR-0007 | adr | proposed | adr | [ADR-0007 — ADR의 크기는 공동무효 단위로 정한다](../../ops-workflow/adr/adr-0007-adr-size-by-cotermination.md) |
| ADR-0008 | adr | proposed | adr, yaml | [ADR-0008 — ADR 메타데이터는 YAML frontmatter로 인코딩한다](../../ops-workflow/adr/adr-0008-yaml-frontmatter-encoding.md) |
| ADR-0009 | adr | proposed | github-issues, issue-types | [ADR-0009 — 작업 이슈는 정확히 하나의 타입을 갖는다](../../ops-workflow/adr/adr-0009-single-type-per-work-item.md) |
| ADR-0010 | adr | proposed | github-issues, issue-types | [ADR-0010 — 이슈 타입은 묶는 것과 수행하는 것으로 갈린다](../../ops-workflow/adr/adr-0010-container-and-leaf-types.md) |
| ADR-0016 | adr | proposed | github-issues, github-projects | [ADR-0016 — 리프 티켓은 수정 대상 저장소와 참조 저장소를 명시한다](../../ops-workflow/adr/adr-0016-leaf-ticket-declares-repo-context.md) |
| ADR-0017 | adr | proposed | github-issues, ticket-engineer | [ADR-0017 — 리프 티켓은 선행 의존을 명시하고, 열린 선행 위에는 착수하지 않는다](../../ops-workflow/adr/adr-0017-leaf-ticket-declares-dependencies.md) |
| ADR-0022 | adr | proposed | discussion, adr | [ADR-0022 — discussion은 최소한의 메타데이터를 갖는다](../../ops-workflow/adr/adr-0022-discussion-minimal-metadata.md) |
| ADR-0023 | adr | proposed | discussion, adr | [ADR-0023 — 사고의 발산은 discussion 문서로 남긴다](../../ops-workflow/adr/adr-0023-record-divergence-as-discussion.md) |
| ADR-0024 | adr | proposed | discussion | [ADR-0024 — discussion은 보관도 동결도 약속하지 않는다](../../ops-workflow/adr/adr-0024-discussion-no-retention-no-freeze.md) |
| ADR-0032 | adr | proposed | adr | [ADR-0032 — 정책 ADR은 proposed로 운영한다: 검증은 하네스가, accept는 미룬다](../../ops-workflow/adr/adr-0032-policy-adr-defers-accept.md) |
| ADR-0033 | adr | proposed | github-issues, github-projects | [ADR-0033 — 티켓 Status는 여섯이다: 진행 단계와 확신만 표현한다](../../ops-workflow/adr/adr-0033-ticket-status-roster-and-meaning.md) |
| — | discussion | active | claude-code-skills | [skill 초판 마찰 로그](../../ops-workflow/discussion/260712_1731_skill-friction-log.md) |
| — | discussion | active | adr | [ADR 선행 사례 조사 — 무엇이 표준이고, 무엇이 우리 발명이고, 무엇이 실패하는가](../../ops-workflow/discussion/260714_1417_adr-prior-art-survey.md) |
| — | discussion | active | adr | [ADR 문서를 무슨 포맷으로 적을 것인가](../../ops-workflow/discussion/260715_1401_adr-document-format.md) |
| — | discussion | active | adr | [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../../ops-workflow/discussion/260715_1551_cross-adr-references.md) |
| — | discussion | active | github-issues, github-projects, issue-types | [티켓(컨트롤 플레인) 결정을 ADR로 승격하기 — 후보 분해와 논점](../../ops-workflow/discussion/260716_1348_ticket-decisions-adr-candidates.md) |
| — | discussion | done | ticket-engineer | [ticket-engineer 워크스페이스 엣지 케이스 — 낡은 클론·남의 브랜치·중단된 작업](../../ops-workflow/discussion/260722_2030_ticket-engineer-workspace-edge-cases.md) |
| — | discussion | active | github-issues, issue-types | [티켓 본문 구성 — 공통 계약과 타입별 절의 층화 제안](../../ops-workflow/discussion/260723_2039_ticket-body-structure.md) |
| — | discussion | done | github-issues, github-projects, ticket-engineer | [PR 머지와 티켓 종료 — close는 판단인가 의례인가](../../ops-workflow/discussion/260727_1608_pr-merge-auto-close.md) |
| — | discussion | active | github-issues, github-projects, adr, ticket-engineer | [티켓 Draft 상태와 착수 게이트 — 게이트를 발행에서 착수로 옮긴다](../../ops-workflow/discussion/260806_2235_ticket-draft-status-and-start-gate.md) |
| — | discussion | active | adr | [정책 ADR은 proposed로 오래 산다 — 의도된 운영 방식의 기록](../../ops-workflow/discussion/260806_2317_policy-adr-stays-proposed.md) |
