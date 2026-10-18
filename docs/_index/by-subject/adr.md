<!-- 생성물. 손으로 고치지 않는다 (CLAUDE.md §7) — build-index.py 가 만든다 (hook 자동 · /docs-index). -->

# by-subject / adr (20)

topic·type 을 가로지른다 — 세부 주제 검색의 유일한 수단이다.

| id | type | topic | status | 문서 |
|---|---|---|---|---|
| ADR-0002 | adr | ops-workflow | proposed | [ADR-0002 — 결정의 근거를 ADR로 남긴다](../../ops-workflow/adr/adr-0002-record-decisions-as-adr.md) |
| ADR-0003 | adr | ops-workflow | proposed | [ADR-0003 — ADR 본문은 다섯 부분으로 이루어진다](../../ops-workflow/adr/adr-0003-adr-body-structure.md) |
| ADR-0004 | adr | ops-workflow | proposed | [ADR-0004 — ADR은 본문을 읽지 않고 답할 메타데이터를 갖는다](../../ops-workflow/adr/adr-0004-adr-metadata-fields.md) |
| ADR-0005 | adr | ops-workflow | proposed | [ADR-0005 — ADR 본문은 Markdown(GFM)으로 적는다](../../ops-workflow/adr/adr-0005-markdown-gfm-body.md) |
| ADR-0006 | adr | ops-workflow | proposed | [ADR-0006 — ADR 본문은 proposed를 벗어나면 통째로 얼어붙는다](../../ops-workflow/adr/adr-0006-accepted-adr-freezes-whole.md) |
| ADR-0007 | adr | ops-workflow | proposed | [ADR-0007 — ADR의 크기는 공동무효 단위로 정한다](../../ops-workflow/adr/adr-0007-adr-size-by-cotermination.md) |
| ADR-0008 | adr | ops-workflow | proposed | [ADR-0008 — ADR 메타데이터는 YAML frontmatter로 인코딩한다](../../ops-workflow/adr/adr-0008-yaml-frontmatter-encoding.md) |
| ADR-0022 | adr | ops-workflow | proposed | [ADR-0022 — discussion은 최소한의 메타데이터를 갖는다](../../ops-workflow/adr/adr-0022-discussion-minimal-metadata.md) |
| ADR-0023 | adr | ops-workflow | proposed | [ADR-0023 — 사고의 발산은 discussion 문서로 남긴다](../../ops-workflow/adr/adr-0023-record-divergence-as-discussion.md) |
| ADR-0032 | adr | ops-workflow | proposed | [ADR-0032 — 정책 ADR은 proposed로 운영한다: 검증은 하네스가, accept는 미룬다](../../ops-workflow/adr/adr-0032-policy-adr-defers-accept.md) |
| ADR-0035 | adr | ops-workflow | proposed | [ADR-0035 — 수렴한 논의의 결론은 digest 문서로 증류한다](../../ops-workflow/adr/adr-0035-distill-conclusions-into-digest.md) |
| ADR-0036 | adr | ops-workflow | proposed | [ADR-0036 — ADR의 생명주기는 네 상태로 돌고, 결정은 supersede로만 바뀐다](../../ops-workflow/adr/adr-0036-adr-lifecycle-states-and-transitions.md) |
| — | digest | ops-workflow | current | [논의에서 설계까지 — discussion과 digest가 돌아가는 모양 (2026-10-07 시점)](../../ops-workflow/digest/261006_1640_digest-layer-decisions.md) |
| — | discussion | ops-workflow | active | [ADR 선행 사례 조사 — 무엇이 표준이고, 무엇이 우리 발명이고, 무엇이 실패하는가](../../ops-workflow/discussion/260714_1417_adr-prior-art-survey.md) |
| — | discussion | ops-workflow | active | [ADR 문서를 무슨 포맷으로 적을 것인가](../../ops-workflow/discussion/260715_1401_adr-document-format.md) |
| — | discussion | ops-workflow | active | [ADR은 다른 ADR을 어디까지, 어떻게 참조하는가](../../ops-workflow/discussion/260715_1551_cross-adr-references.md) |
| — | discussion | ops-workflow | active | [티켓 Draft 상태와 착수 게이트 — 게이트를 발행에서 착수로 옮긴다](../../ops-workflow/discussion/260806_2235_ticket-draft-status-and-start-gate.md) |
| — | discussion | ops-workflow | active | [정책 ADR은 proposed로 오래 산다 — 의도된 운영 방식의 기록](../../ops-workflow/discussion/260806_2317_policy-adr-stays-proposed.md) |
| — | discussion | ops-workflow | done | [discussion 위에 결론 층을 둔다 — 읽을 수 없는 로그와 얼어붙는 영수증 사이](../../ops-workflow/discussion/261006_1549_digest-layer-over-discussion.md) |
| — | discussion | ops-workflow | done | [digest를 청사진으로 — 결정의 요약이 아니라 결정된 설계의 서술](../../ops-workflow/discussion/261007_1947_digest-as-blueprint.md) |
