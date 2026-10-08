---
name: adr-accept
description: ADR의 동결선 전이 — accept·unaccept·supersede. "이 ADR을 accept한다", "공표 전 accept를 되돌린다", "ADR-00NN을 ADR-00MM으로 supersede한다"일 때 사용한다. adr-judge 하네스 전용. 저작·번호 발급·동결 검사(freeze-check)는 루트 `adr` 스킬. 규약은 CLAUDE.md §3·§4, 심판 기준은 adr-judge 프롬프트 §1.
---

# adr-accept — 동결선을 넘기는 문

세 스크립트는 **frontmatter 필드만** 건드린다 — 본문에 손댈 방법이 없다. 그것이 동결(ADR-0006)을 규율이 아니라 구조로 만든다. 손으로 `status:` 줄을 고치지 않는다.

(스크립트는 SessionStart hook가 PATH에 올린다 — bare name으로 실행한다.)

## 1. accept

심판 다섯(adr-judge 프롬프트 §1)을 넘긴 `proposed` 초안만 넘긴다. **정책 토픽(`topic: ops-workflow`)은 다섯을 넘겨도 사람이 accept를 명시 지시했을 때만**이다(ADR-0032 — 정책 ADR은 proposed가 현행 규범).

```bash
accept.py ADR-0001
```

이 스크립트가 하는 일:

- 파일명 규약(소문자 kebab·3~6 단어)과 `status: proposed`를 확인한다 — accept는 좋은 이름의 관문이다.
- `status`와 `accepted_at`을 함께 기록한다. **`accepted_at`은 권위 있다** — *검토가 언제 끝났는가*에 문서가 스스로 답한다. 손으로 적지 않는다: 틀리면 문서가 거짓말을 하고, 대조할 바깥이 없다.

**여기서부터 본문(결정의 의미)이 동결된다**(ADR-0006). 유예 기간은 없다. 무엇이 얼고 안 어는지는 루트 `adr` 스킬 §4.

> **`accepted_at`은 동결 시각이 아니다.** *검토가 끝난 것*(문서의 사실, 시각)과 *되돌릴 수 없게 된 것*(공표, 저장소의 사실, 상태)은 다른 사실이다. **accept 한 날과 커밋한 날이 어긋나는 것은 정상이다** — 도구는 둘을 대조하지 않는다.

## 2. unaccept — 공표 전에만

```bash
unaccept.py ADR-0001    # push 된 accept 는 거부한다(exit 1)
```

동결은 **공표(push) 시점에 발효한다.** 아직 push되지 않은 accept는 아무도 보지 못한 결정이므로 되돌릴 수 있다. 공표된 뒤로는 supersede만이 결정을 바꾸는 길이다.

## 3. supersede

**부분 supersede는 없다.** 옛 ADR 전체가 `superseded`가 되고, 여전히 유효한 부분은 **새 ADR에 재진술**한다. 새 ADR이 먼저 accept되어 있어야 한다.

supersede 전에 그 ADR을 근거로 삼은 티켓을 읽는다 — `gh issue list --search "ADR-0001"`. 열린 티켓이 있으면 사람에게 알린다. 티켓은 고치지 않는다.

```bash
supersede.py --old ADR-0001 --by ADR-0007
```

이 스크립트는 옛 ADR의 **두 필드(`status`·`superseded_by`)만** 건드린다.

- **`superseded_by`는 여럿 가능하다**(뭉친 결정을 쪼개며 폐기). `status: superseded`와 짝이다 — 한쪽만 있으면 깨진 상태다.
- 역방향(`supersedes`)은 두지 않는다: 파생 가능하고, 전체 폐기 선언이 흩어지면 부분 폐기와 구분되지 않는다.

**exit 1은 우회하지 않는다.**

## 4. 쓴 다음

- `docs/`는 **지식 플레인**이다 — **커밋은 사람이 승인한다**(§6). agent가 무인으로 밀어 넣지 않는다.
- 인덱스는 신경 쓰지 않는다 — 세 스크립트가 돌면 hook이 `_index/`를 자동 재생성한다(§7).
