---
type: discussion
topic: ops-workflow
subjects: [adr]
status: active
---

# ADR 선행 사례 조사 — 무엇이 표준이고, 무엇이 우리 발명이고, 무엇이 실패하는가

ADR 도입을 결정하는 ADR(초안 ADR-0002)을 얼리기 전에, **바깥이 ADR을 무엇이라고 부르는지** 확인했다. 목적은 셋이다.

1. 우리가 **ADR이라는 이름을 빌려 쓰면서 다른 것을 하고 있지는 않은지** — 이름을 빌리면 남의 기대도 함께 빌린다
2. 우리 규약 중 **무엇이 선행 사례이고 무엇이 우리 발명인지** — 발명한 것은 스스로 정당화해야 하고, 빌린 것은 근거를 인용하면 된다
3. **이 관행이 실제로 어떻게 실패하는지** — 도입 결정은 실패 모드를 알고 내려야 한다

조사: Nygard 원문(2011) · adr.github.io · AWS Prescriptive Guidance · Microsoft Azure WAF · MADR · 템플릿 6종 · 도구 생태계 · 공개 기업 사례 · **공개 ADR 저장소 실측** · 학술 문헌 · 비판론.

> **경고 — 이 문서에는 우리 규약에 불리한 증거가 들어 있다.** 그것이 이 조사의 요점이다. 유리한 것만 모으면 조사가 아니라 변론이다.

---

## 0. "ADR 도입을 ADR로 쓴다"는 어색한 게 아니라 관행이다

- `adr-tools`의 `adr init`은 **ADR 0001 "Record architecture decisions"** 를 자동 생성한다. 상태 `Accepted`.
- Arachne의 첫 문서는 **`adr-001-use-adrs.md`**.
- **공개 저장소 1,280곳**이 이 파일(`0001-record-architecture-decisions.md`)을 가지고 있다 — 이것이 사실상 **공개 ADR 도입의 상한선**이다.

체계는 **자기 자신을 첫 항목으로 삼아야 완결된다.** 자기참조가 아니라 **부트스트랩**이다.

---

## 1. ADR이란 무엇인가

**Nygard (2011-11-15)** — 원본. 동기가 우리와 같다:

> "Large documents are never kept up to date. Small, modular documents have at least a chance at being updated."

근거를 모르는 후임에게는 **두 선택지밖에 없다**:

> "**Blindly accept the decision.** … If the project accumulates too many decisions accepted without understanding, then the development team becomes afraid to change anything and **the project collapses under its own weight.**"
> "**Blindly change it.** … changing the decision without understanding its motivation or consequences could mean damaging the project's overall value without realizing it."
> "It's better to avoid either blind acceptance or blind reversal."

**adr.github.io**: *"An ADR captures **a single AD** and its rationale."* / *"The collection … constitute its **decision log**."*
**AWS**: *"…describes the architectural decision, its context, and its consequences. **ADRs have states and therefore follow a lifecycle.**"*
**Fowler**: *"a short document that captures and explains **a single decision**."* — 그리고 값어치가 둘이라고 본다: 기록물 그 자체, 그리고 ***"the act of writing them helps to clarify thinking."***

**"왜"에 대한 강조는 전 계보가 공유한다.** AWS의 설명이 가장 날카롭고, 이유가 우리 생각과 다르다:

> "…focuses on the reason for the decision rather than how the team implemented it. … **prevents other architects who weren't involved in the decision-making process to overrule that decision in the future.**"

→ **"왜"를 적는 것은 문서화가 아니라 방어다.** 1인 저장소에서 "그 자리에 없던 사람"은 **6개월 뒤의 나**이고, **agent**다.

**★ Nygard의 근거 기반은 놀랄 만큼 얇다.** 그의 "Experience Report"는 **3개월, 개발자 6~10명**이다. 이 관행 전체가 그 위에 서 있다.

---

## 2. 구조 — 템플릿은 하나가 아니라 스펙트럼이다

**"ADR 템플릿"이라는 단일 표준은 없다.** 무게가 5단계로 갈린다.

| 템플릿 | 무게 | 섹션 | 최적화 대상 |
|---|---|---|---|
| **Y-statement** (Zdun) | XXS — **한 문장** | *"In the context of `<use case>`, facing `<concern>`, we decided for `<option>` and neglected `<other options>`, to achieve `<quality>`, accepting `<downside>`, because `<rationale>`."* | 많이·싸게 남기고 나중에 상세화 |
| **Nygard** | XS — **1~2쪽** | Title · Status · Context · Decision · Consequences | 서사 · 최소 의식 |
| **MADR minimal** | S | Context and Problem Statement · Considered Options · Decision Outcome | 버린 선택지의 가시화 |
| **MADR full** (4.0.0) | M | + Decision Drivers · Consequences · **Confirmation** · Pros and Cons · More Information + frontmatter(`decision-makers`/`consulted`/`informed`) | 트레이드오프 투명성 · RACI |
| **Tyree & Akerman** | XL — **14필드** | Issue · Decision · Status · Group · Assumptions · Constraints · Positions · Argument · Implications · Related decisions/requirements/artifacts/principles · Notes | 전사 아키텍처 · 리뷰 보드 |

그 외 ISO/IEC/IEEE 42010(9항목) · Alexandrian(4부) · Business case(SWOT·비용) · Planguage(QA 지향).

**Nygard의 문체 규정**: Context는 **가치중립**("simply describing facts"), Decision은 **능동 명령형**("We will …"), Consequences는 **긍정만이 아니라 전부**. 그리고:

> "**Bullets are acceptable only for visual style, not as an excuse for writing sentence fragments.** (Bullets kill people, even PowerPoint bullets.)"

AWS는 더 강하게: *"The decision **must clearly state, in imperative language** … Avoid using words such as 'should'."*

### 우리 템플릿의 위치

우리는 **Context · Decision · Alternatives · Consequences · 무효화 조건**을 쓴다.

- Nygard 최소 3종 만족 ✅
- `Alternatives`는 **MADR의 핵심 기여**를 흡수 — MADR이 존재하는 이유가 정확히 이것이다
- **`무효화 조건`은 어느 템플릿에도 없다.** MADR의 *More Information*("define … **if/when it should be re-visited**")이 가장 가깝지만 optional이다. → **우리 발명.** ADR-0001 dogfood에서 이 필드가 자기 문서의 결함을 짚어낸 실적이 있다(skill 마찰 로그 §8①).

### ★ 우리에게 없는 섹션 둘

**AWS의 `Compliance`** (예시 ADR의 실제 섹션): *"The main and develop branches **must be marked as Protected**. … At least one approval is required."*
**MADR의 `Confirmation`**: *"Describe **how the implementation of/compliance with the ADR can/will be confirmed.** … a test with a library such as **ArchUnit** can help validate this."*

→ **두 계보 모두 "이 결정을 어떻게 검증·강제하는가"를 문서 안에 둔다.** 우리 모델에는 이 자리가 **없다** — 전부 코드·스크립트·게이트로 밀어냈다(§8).

이 자리를 두고 도구 생태계가 자란다: **ArchUnit**(Java) · **Deptrac**(PHP — *"enforce architectural decisions"*, CI에서 PR 차단) · **dependency-cruiser**(JS) · **Konsist**(Kotlin) · **OPA+Conftest**(fail-closed). 정식화된 한 줄: **"A decision record documents the decision, while a fitness function assures the decision."**

**단 그 대가도 보고돼 있다**: *"you must make sure that the original ADR and its executable rules **stay in sync** … which may be challenging."* — **동결 문서와 살아 있는 규칙이 갈라진다.**

⚠️ **주의 — 흔히 인용되는 짝이 실은 근거가 없다.** ThoughtWorks Radar의 *architectural fitness function* 항목은 **ADR을 한 번도 언급하지 않는다**(그리고 **TRIAL에서 멈췄다. ADOPT에 간 적 없다**). "모든 ADR에 fitness function을" 은 **블로그 레벨의 열망**이지 문서화된 조직 관행이 아니다.

---

## 3. 스케일 — ★ 실측했다

인용문이 아니라 숫자다. 공개 저장소 **284곳 / ADR 4,682건**을 표본하고, **362건**의 단어 수를 셌다.

### 개수 — **중앙값 6건**

```
min=1   p25=3   MEDIAN=6   p75=13   p90=29   mean=16.5

1-2건    20.8%
3-5      25.4%
6-10     22.2%
11-20    14.8%
21-50    12.0%
50+       4.9%
```

**ADR 폴더를 가진 프로젝트의 중앙값이 6건이다. 68%가 10건 이하. 50건 넘는 곳은 5% 미만.**

학술 문헌이 같은 결론에 독립적으로 도달한다 — Buchgeher et al., *IEEE Access* (2023):

> "the **adoption of ADRs is still low** … **About 50% of all repositories with ADRs contain just one to five ADRs, suggesting that the concept has been tried but not yet definitively adopted.**"

### 카덴스 — **월 0.72건. 6주에 한 건.**

| 저장소 | ADR | 기간 | **월간** |
|---|---|---|---|
| BrighterCommand/Brighter | 86 | 2022-10 → 2026-07 | 1.92 |
| bbc/tams | 49 | 2024-04 → 2026-02 | 2.22 |
| 1024pix/pix | 56 | 2019-04 → 2025-10 | 0.72 |
| athensresearch/athens | 26 | 2021-04 → 2022-08 | 1.65 **(이후 사망)** |
| arachne-framework | 17 | 2016-05 → 2016-12 | 2.50 **(이후 사망)** |
| **backstage/backstage** | **15** | 2020-04 → 2025-08 | **0.24** |

**★ 형태가 언제나 같다: 창립기 폭발 → 가늘어짐 → 침묵.**
- **log4brains**(도구 저자 자신의 저장소): 2020년 9~10월에 13건 → 이후 **3년 반 침묵** → 2024년 말 2건
- **Arachne**: 7개월에 17건 → 영원히 0
- **Backstage**(CNCF, 기여자 수천, 6년): **15건. 4.3개월에 한 건.**
- **Microsoft 자신의 엔지니어링 플레이북**: **ADR 2건** — 그중 하나는 템플릿이다

### 길이 — **중앙값 613 단어**

```
min=48   p25=333   MEDIAN=613   p75=1129   p90=2014   max=11276

<250 단어  (<1쪽)   18.2%
250-500   (~1쪽)   21.5%
500-1000  (1-2쪽)  31.5%
1000-2000 (2-4쪽)  18.2%
2000+     (4쪽+)   10.5%
```

**72%가 Nygard의 "1~2쪽"을 지킨다. 28%가 넘긴다.** 그런데 **추세가 나쁘다**:

- **짧은 쪽**: GOV.UK 평균 **237~267 단어**(어떤 건 **66 단어**). Backstage 383.
- **긴 쪽**: **Jaeger — 2026년에 쓴 ADR 전부가 평균 1,852 단어**, 전건이 600 단어 초과. Brighter의 최장은 **11,276 단어**.
- → **ADR 관행이 새로울수록 ADR이 길다. 최근 ADR은 설계 문서처럼 읽힌다.**

**★ 우리 ADR-0001·0002 초안은 이 분포의 상위 25%에 있다.** AWS의 리뷰 규격(**10~15분 묵독**)이 사실상의 길이 상한인데, 우리 초안은 거기 걸린다. **우리가 담는 게 더 많은 것인지, 그냥 긴 것인지 판정해야 한다**(§9).

---

## 4. 대상 — 무엇이 ADR감인가

**Nygard의 원 정의** (그대로 전승된다 — Richards & Ford → AWS):

> "…decisions that affect the **structure, non-functional characteristics, dependencies, interfaces, or construction techniques**."

**우리 §4②의 트리거 4종은 이 목록에서 나왔고, `construction techniques`(라이브러리·프레임워크·도구·프로세스) 하나가 빠져 있다.** 의도인지 확인 필요(§9).

**Microsoft**: *"Only include choices that affect the system's structure, key quality attributes, or **are difficult to reverse**."* ← **되돌림 비용 기준을 명시하는 유일한 대형 벤더. 우리 편이다.**

**Zimmermann의 유의성 7기준**: 사업가치·리스크 / 핵심 이해관계자 관심사 / 비정상적 품질 요구 / 통제 불가 외부 의존 / 횡단 영향 / 팀 최초 경험 / 문제 이력. 요약: **"All architecture is design, but not all design is architecture."** 그리고 **"not all decisions are worth capturing; triages are required."**

**Spotify는 판정을 위임하고, 실질적으로 넓게 쓴다**: *"it is up to each team to align on what defines a significant impact"* → 그런데 플로차트 결론은 **"Almost always!"**

**MADR은 유의성 논쟁 자체를 버렸다**: *"Do not take the term 'architecture' too seriously … we believe that **any (important) decision** should be captured."* (그래서 2022년 이름을 "**Any** Decision Record"로 바꿨다가 **2024년 다시 Architectural로 되돌렸다.** 생태계 자신이 이 경계에서 흔들린다.)

### ★ one-way door — 출처를 정확히

우리 §4②의 임계선은 Bezos에서 왔다. **원문(2015년 주주서한):**

> "Some decisions are consequential and irreversible or nearly irreversible – **one-way doors** … **Type 1** decisions. But most decisions aren't like that – they are changeable, reversible – they're **two-way doors**."

그리고 그가 경고한 실패 모드가 있다:

> "As organizations get larger, there seems to be a tendency to **use the heavy-weight Type 1 decision-making process on most decisions, including many Type 2 decisions.** The end result is slowness, unthoughtful risk aversion, failure to experiment sufficiently, and consequently **diminished invention**."

**중요**: **Bezos는 ADR을 한 번도 언급하지 않는다.** "one-way door → ADR 임계선"은 **커뮤니티의 추론**이다. 그리고 **AWS 자신의 ADR 가이드는 one-way door를 쓰지 않는다** — AWS 기준은 순수 **범주적**이다(5축에 해당하면 쓴다).

→ **우리 임계선은 *범주 + 비용* 이중 필터**(범주에 해당해도 "한 시간이면 되돌린다"면 ADR 아님)이고 **AWS는 범주 단일 필터**다. **우리가 더 좁다.** Microsoft만 우리와 같다.

### 입도 — 거의 아무도 다루지 않는다

**AWS: 침묵. adr.github.io: 침묵.** 가장 가까운 것이 Nygard의 두 문장:

> "Each record describes a set of forces and **a single decision** in response to those forces."
> "**One ADR describes one significant decision** for a specific project."

그리고 그는 **부분 폐기가 왜 불필요한지**를 쪼개는 규칙이 아니라 **연쇄**로 답한다:

> "**The consequences of one ADR are very likely to become the context for subsequent ADRs.** … the large-scale responses create spaces for the smaller scale to fit into."

즉 결정은 **앞으로 이어지지, 뒤로 부분 철회되지 않는다.**

**★ 딱 하나, Microsoft가 입도 규칙을 갖고 있다 — 그리고 축이 우리와 다르다:**

> "**Break one decision into multiple** if an architectural decision is going to result in **multiple phases**, such as short-term, mid-term, long-term approaches. **Log each phase as its own decision record.**"

Microsoft의 분해 축은 **시간(단계)**, 우리 축은 **공동무효(같이 죽는가)**. 겹치지 않는다. **우리 축이 더 정밀하고, 선례가 없다.**

**부분 supersede를 논한 자료는 단 하나도 없다.** 허용도 금지도 아니다 — **아무도 그 질문에 도달하지 않았다.** (`adr-tools`의 자유 링크 동사 `adr link 12 Amends 10 "Amended by"` 가 유일하게 근접하는데, 대상의 `Accepted`를 건드리지 않는 **약한 관계**다.)

**Microsoft에는 우리에게 없는 것이 하나 더 있다**: *"**Record the confidence level** of the decision. Sometimes an architecturally significant decision is made with relatively low confidence."* → **동결 모델에서 "확신이 낮은데 얼린다"가 무엇을 뜻하는지**는 생각해 볼 값이 있다(§9).

---

## 5. 불변성 — ★ 계보가 서로 싸운다. 그리고 실무는 교리를 안 지킨다

우리는 동결을 ADR의 본질로 취급해 왔다. **그것은 사실이 아니다.**

**① Nygard는 불변성을 규정한 적이 없다.** 원문에 있는 것은:

> "If a decision is reversed, we will **keep the old one around, but mark it as superseded.**"
> "ADRs will be numbered **sequentially and monotonically. Numbers will not be reused.**"

**"accepted ADR을 고치지 말라"는 말은 어디에도 없다.** 오히려 그의 계보 도구들은 accepted ADR의 `## Status`를 **자유롭게 재작성한다** — 그게 supersede 구현이다.

**② 강한 동결 진영 — Fowler · AWS · Microsoft.**

Fowler: *"**Once an ADR is accepted, it should never be reopened or changed** - instead it should be superseded."*
AWS: *"When the team accepts an ADR, **it becomes immutable**."* / *"…after the team **accepts or rejects** them."* ← **reject에도 동결.** 우리는 accept에만 건다.
Microsoft: *"The ADR serves as an **append-only log**. Don't go back and edit accepted records."* + *"**Avoid making decision records design guides.**"* ← 우리 §4①의 정확한 지지자

**③ 그리고 정면 반대 — 가장 널리 읽히는 자료(★16.4k)가 불변성을 시도했다 철회했다.**

joelparkerhenderson, *"Suggestions for writing good ADRs"*: *"**Immutable: Don't alter existing information in an ADR.**"*
같은 저장소, *"Teamwork advice for ADRs"*:

> "**In theory, immutability is ideal. In practice, mutability has worked better for our teams.** We insert the new info into the existing ADR, with a date stamp… This kind of approach leads to a '**living document**' that we all can update."

**④ MADR은 가변 전제.** frontmatter가 `date: {YYYY-MM-DD **when the decision was last updated**}` 다.

**⑤ AWS조차 자기모순.** 불변이라면서 **모든 ADR에 changelog를 요구**하고(*"Each ADR must have a status and a **changelog**"*), accept 시 owner가 손으로 `timestamp + **version** + stakeholders`를 적는다. **"version"이 있는 불변 문서**는 형용모순이다.

**⑥ ★ 그리고 실무는 교리를 안 지킨다.**

- **GDS는 명시적 예외를 둔다**: 아직 **구현되지 않았다면** *"it may be appropriate to **update your existing ADR**"*; **구현이 시작된 뒤에만** supersede가 의무다.
- **영국 정부의 2025년 신 프레임워크는 아예 갱신을 지시한다**: *"**regularly review and update the ADR** to reflect any changes in the context or consequences."* — 국가 규모 프레임워크가 append-only 교리를 정면으로 어긴다.
- **Oxide는 published RFD의 불변성을 명시적으로 거부**한다: *"just because something is in the published state does not mean that it cannot be updated and corrected."*
- **Backstage의 ADR001에는 커밋이 11개** 붙어 있다.
- 실측 supersede 비율은 낮다 — log4brains 2/19(~10%), Backstage 1/15.

> **→ 불변성은 교리이고, 실무는 "누가 구현하기 전까진 고친다"이다.**

### ★ 그런데 반례를 정확히 세면 하나뿐이다 — 그리고 쟁점은 `append` 하나다

위 목록은 **너무 헐겁게 셌다.** 다시 세면 그림이 완전히 달라진다.

**먼저, 아무도 반대하지 않는 것부터.** *"결정을 바꾸려면 새 ADR을 쓰고 옛 것을 supersede한다"* — **반대 진영조차 이것을 반대하지 않는다.** Nygard도, GDS도, jph도 같은 말을 한다.

**즉 논쟁은 "결정을 고칠 수 있는가"가 아니다. "기록(본문)에 손을 댈 수 있는가" 하나다.** 그리고 답은 — **그들도 자유롭게 못 고친다.**

| | **편집 가능한 창** | **허용되는 편집의 종류** | 결정 변경 방법 |
|---|---|---|---|
| **우리** | accept ~ **공표 전** (`unaccept.py`) | **없음** (본문·경로 전부) | 새 ADR + supersede |
| **GDS** | **구현 시작 전까지** | *"clarifications or additional consequences"* — **결정 번복은 불가** | 새 ADR (구현 후엔 **의무**) |
| **jph** | 상시 | **append만** — *"새 정보를 **날짜 도장**과 **결정 이후에 도착했다는 표시**를 달아 삽입"* | 새 ADR **또는** append |
| **영국정부 2025** | 상시 | 맥락·결과 갱신 | 명시 없음 |

**Oxide는 반례가 아니다.** RFD는 **제안서**(forward-looking)이고 우리 `discussion`에 대응한다. **장르가 다르다.**
**MADR도 반례가 아니다.** **템플릿**이지 거버넌스가 아니다. `date: last updated` 필드의 존재가 입장 표명은 아니다.
**Backstage의 "본문 수정"도 반례가 아니다** — 옛 ADR의 제목에 `[superseded]`를 박는 것이므로, **상태 표시**다. 우리 허용 편집과 같다(경로/제목을 건드린다는 점만 우리가 더 엄격하다).

**영국정부 2025는 매체가 강요한 결과로 보인다.** 템플릿이 **`.docx`** 이고 4단계 승인을 통과하는 거버넌스 문서다. **Word 파일에는 git 이력이 없다** — 갱신하지 않으면 옛 맥락을 되찾을 수 없고, 갱신하면 옛 맥락이 사라진다. 어느 쪽이든 진다. → **지식 보존에 대한 숙고된 입장이라기보다 저장 매체의 귀결이다.** 우리에겐 반증이 아니라 **"왜 git이어야 하는가"의 근거**다(ThoughtWorks의 *"위키 말고 소스 컨트롤"* 과 같은 축).

**→ 진짜 반례는 jph 하나이고, 그가 하는 것은 `append`다.**

### 그리고 `append`는 이름만 다른 부분 폐기다

jph가 하는 것을 정확히 보면 **결정을 고치는 게 아니다.** 사후에 도착한 정보(벤더 가격 변동 · 실사용 결과 · 새 팀원의 정보)를 **날짜를 박아 덧붙인다.** 원 결정과 원 근거는 그대로다.

**그 자체로는 오염이 아니다.** 그런데 둘이 깨진다.

**① append는 부분 폐기의 다른 이름이다.**
덧붙는 정보가 **결정을 흔드는 정보**일 때, append는 이런 문서를 만든다:

> *"우리는 X로 정했다(2024). — 덧붙임(2025): 그런데 X의 전제가 깨졌다."*

이 문서는 **통째로 참도 아니고 통째로 폐기된 것도 아니다.** 읽는 사람과 agent가 매번 *"어느 절반이 유효한가"* 를 판정해야 한다. **우리가 ⑥에서 명시적으로 금지한 바로 그것이다.** jph의 "living document"는 **부분 폐기를 뒷문으로 들여온 것**이다.

**② append는 supersede를 해야 할 압력을 흡수한다.**
새 ADR은 비싸고 append는 싸다. **싼 탈출구가 있으면 사람은 그리로 간다.**
**실측이 이를 뒷받침한다 — 관측된 supersede 비율이 10% 수준이다**(log4brains 2/19, Backstage 1/15). 결정이 정말 90% 살아 있었을 리 없다. **낡은 결정이 supersede되지 않고 그냥 거기 있는 것이다.**

→ **그러므로 §9④의 비판(*"불변성 교리가 코퍼스를 썩게 만든다"*)은 인과가 거꾸로다.** 썩게 만드는 것은 **싼 탈출구**다. **동결은 supersede를 강제하고, append는 supersede를 면제한다.**

> **동결은 오염 차단인 동시에 supersede 강제 장치다.** 탈출구를 없애야 사람이 정직하게 새 ADR을 쓴다.

### ★ GDS는 반례가 아니라, 같은 원리의 다른 계산이다

**GDS의 선**: *"구현이 시작됐다면 새 ADR을 써라. 아직 구현되지 않았다면 고쳐도 된다."*
**그들의 암묵적 원리**: **아무도 아직 이 결정에 의존하지 않았다면, 고쳐도 깨질 것이 없다.**

**우리 선**: 공표(push).
**우리 원리**: **똑같다.** 우리 시스템에서 *"누군가 의존하기 시작하는 순간"* 이 언제인가 — **push다.** §5의 게이트가 **`origin/main`의 accepted ADR**을 요구하고, **그 순간부터 티켓이 이 ADR을 인용하며 태어나기 때문이다.**

→ **우리는 GDS와 같은 원리를 쓰고, 우리 시스템에 맞게 계산했을 뿐이다.** 그들의 선이 *구현*인 이유는 **그들에게 티켓 게이트가 없어서**다.
→ 즉 우리 공표-발효 규칙은 GDS의 **선례를 따른 것**이면서 동시에 **더 이르다.** 더 이른 이유가 있다: 우리는 accept 즉시 티켓이 태어나므로, 의존이 그만큼 일찍 시작된다.

### 정리 — 우리 위치 (수정)

| 입장 | 누구 |
|---|---|
| **강한 동결** (accept 후 본문 불가) | Fowler · AWS · Microsoft · log4brains · **우리** |
| **의존 시작 전까지만 가변** — 원리는 우리와 같음 | **GDS** |
| **동결 + append 허용** ← **유일한 진짜 반대 진영** | **joelparkerhenderson** |
| 매체 탓으로 가변 | 영국 정부 프레임워크(2025, `.docx`) |
| 반례 아님 (장르·성격이 다름) | Oxide(RFD=제안서) · MADR(템플릿) · Backstage(상태 표시) |
| 침묵 (supersede 관행만) | **Nygard 원본** |

→ **동결 반대 진영은 처음 세었던 것보다 훨씬 작다.** 그리고 **유일한 쟁점은 `append`이며, 그것은 우리 ⑥(부분 폐기 불허)이 이미 답한 문제다.**

### ★ 동결 발효 시점 — 선례가 있었다

우리 §3의 *"동결은 공표(push) 시점에 발효한다"* 는 dogfood 중에 발명한 규칙이다. **정확한 선례가 있다.**

**GDS Way**: *"there is no need to record a 'status' for an ADR when it is first proposed. **The status of your ADR's pull request (PR) reflects the status of the decision.**"* / *"**an ADR in the `main` branch of your GitHub repository is accepted.**"*
**Arachne**: *"Master branch reflects steering group consensus."* — 그리고 **accept 이후에만 구현 코드를 커밋한다.**

→ **"main에 있는 것이 accepted다"** 는 확립된 관행이다. 우리 규칙은 임의 발명이 아니었다.
→ **덤**: GDS는 **PR 자체를 `proposed` 상태로 쓴다** — status 필드를 accept 전까지 아예 두지 않는다. **우리보다 단순하다.** 우리가 `proposed`를 파일에 적는 이유를 다시 볼 값이 있다(§9).

---

## 6. 기업 실사용 — 1차 출처로 확인된 것만

| 조직 | 무엇을 | 특기사항 |
|---|---|---|
| **GitHub** | **모바일 팀만** 채택. *"future you"* 를 위해 쓴다 | **프로세스를 전혀 기술하지 않는다** — 저장 위치·리뷰어·승인·타임박스 전부 없음 |
| **Spotify** | **RFC → ADR 연쇄.** 큰 변경은 RFC로 논의 → 결론나면 ADR. 과거 결정도 **소급 작성** | 판정은 팀에 위임. 실질은 *"Almost always"* |
| **AWS** | **유일하게 완전히 명세된 공개 프로세스.** 200+ ADR / 3년 | 리뷰가 **동기 회의**(10~15분 묵독). PR이 아니다 |
| **Microsoft** | append-only log. 되돌림 비용 기준. 확신도 기록 | **자기 플레이북엔 ADR이 2건뿐** |
| **GOV.UK / GDS** | **PR = 상태 기계.** main 머지 = accepted | ADR 평균 **237~267 단어** — 가장 짧고 가장 규율 있다 |
| **Arachne** | 전역 순차 번호. 운영위 합의. **accept 후에만 구현 커밋** | **7개월 17건 → 프로젝트 사망** |
| **Lullabot** (50인 에이전시) | **공개 ADR 71건**, log4brains 사이트 | 내용이 *"Use Stylelint"* · *"pin GitHub Actions to a commit hash"* — **유의성 기준 한참 아래.** 범위 침식의 산 표본 |
| **ThoughtWorks Radar** | **ADOPT (Vol.17, 2017-11)** · Vol.18(2018-05) | ⚠️ **그 뒤 8년간 레이더에서 사라졌다. 재평가 없음** |

**확인 실패 — 흔히 인용되지만 1차 출처가 없다**: **Zalando**(ADR 저장소 0건 — API 가이드라인과 혼동) · **adidas**(SAP LeanIX 고객사례로만) · Netflix · Meta · Shopify · Uber. **인용하지 않는다.**

**Google은 ADR을 쓰지 않는다.** **design doc**을 쓴다 — 그리고 그 결과를 스스로 이렇게 표현한다: 변경이 새 문서로 격리되며 *"**미국 헌법에 수정조항이 잔뜩 붙은 것**과 비슷한 상태"* 가 된다고. **부분 supersede를 허용한 세계의 모습이다** — 본문 + 수정조항을 매번 합성해 읽어야 한다.

### RFC / PEP / KEP — 다른 동물이다

| 프로세스 | 개수 | 월간 | 성격 |
|---|---|---|---|
| Kubernetes KEP | ~595 | ~6 | 제안 + **구현 계획 + 졸업 기준(alpha/beta/GA)**. 계획서다 |
| Rust RFC | 639 | ~4.4 | 제안 + **FCP(final comment period)** + rfcbot 합의 |
| Python PEP | 772 | ~2.5 | 제안 + 명세. Accepted 후 *"**historical document** rather than a living specification"* ← **우리와 같은 결론** |
| **ADR (중앙값 프로젝트)** | **6** | **0.72** | **뒤를 보는 영수증** |

**KEP·RFC·PEP는 5~10배 많고 문서당 한 자릿수 무겁다.** 앞을 보는 **제안** 프로세스이고 yes/no를 내리는 권위가 있다. ADR은 뒤를 보는 **기록** 프로세스다.

**Spotify의 RFC→ADR 연쇄가 우리 `discussion`→`adr` 연쇄와 정확히 같은 구조다.** 우리 2종 체계에 선례가 있다.
**KEP는 우리가 안 하기로 한 것**(살아 있는 계획 문서)의 예시다 — 그 자리는 우리에게 **티켓**이다.

**Candost Dagdeviren**이 가장 날카롭게 가른다: RFC는 *"consensus-based"* · 긴 피드백 기간. ADR은 ***"100% consent-based"*** · *"short feedback period to gather **strong objections**"* · ***"should stay close to the codebase."***

→ ADR의 정당성 근거는 **합의(consensus)가 아니라 동의(consent) — "강한 반대가 없음"** 이다. 조사 전체에서 *"N일 침묵 = 동의"* 규칙을 **명문화한 조직은 하나도 없었다**(Oxide의 RFD 3~5영업일이 유일한 타임박스).

### 보드 없이 정당성을 세우는 모델 — Architecture Advice Process

Andrew Harmel-Law (ThoughtWorks Radar TRIAL 2025 · *Facilitating Software Architecture*, O'Reilly):

> "**anyone can make an architectural decision**" — 단 *"everyone who will be **meaningfully affected**"* 와 *"people with **expertise** in the area"* 에게 조언을 구할 것
> "**we are not looking for consensus here**, but we are looking for a broad range of inputs and voices."
> 결정자는 *"**in no way obliged to agree with the advice**"* — 그러나 *"must seek it out, and they must **listen to and record it**."*
> 그의 ADR에는 **`Advice` 섹션이 의무**다 — *"reflects the raw outputs from following the Advice Process."*
> Architecture Advisory Forum은 **결정하지 않는다**: *"The only thing other attendees can do is offer advice."*

→ **accept의 정당성이 승인(approval)일 필요는 없다**는 것을 보여준다. 리뷰 보드가 없는 것이 결함이 아니다.

**⚠️ 그러나 이 모델을 채택하지 않는다 — §11② 참조.** `Advice` 섹션을 의무화하면(= discussion을 accept의 전제로 삼으면) **ADR이 discussion에 의존성을 갖게 되고, 그것이 두 개의 원칙을 동시에 깬다.** 우리가 취하는 것은 이 모델의 **결론**(정당성 ≠ 승인)뿐이고, **장치**(의무 Advice 섹션)는 취하지 않는다.

⚠️ ThoughtWorks가 드는 근거 — *"**Architecture Review Boards is counterproductive** … correlating with **low organizational performance**"* — 는 **검증에 실패했다.** DORA의 공표된 결과는 **change approval board(CAB)** 에 대한 것이지 *architecture* review board가 아니다. **약한 근거로 취급한다.**

---

## 7. ADR 작성 이후 — 다운스트림

**① decision log = 파생물.** 생태계 만장일치: **레코드가 원본, 인덱스는 생성물.**
`adr generate toc` · `adr-log -i`(마커 주입) · `pyadr toc` · log4brains/adr-viewer(정적 사이트) · Backstage 플러그인(**인덱스가 파일이 아니라 포털 질의**다).
→ **우리 `_index/`는 정확히 이 관행이다. 발명 아님** ✅

⚠️ **도구 계층은 얇고 썩고 있다.** `adr-tools`(★5.5k) 2024년 4월 이후 정지. `log4brains`(★1.5k) 2024년 12월 이후 정지, 이슈 57건 미결. **활발한 것은 MADR뿐.** 대부분의 팀은 그냥 `docs/adr/*.md` + GitHub 파일 브라우저를 쓴다.

**② 읽기는 2단계.** AWS: *"skim the **headlines** … then **read** the ADRs to dive deep."* → **제목이 자족적이어야 한다.** AWS 예시 제목은 명사구가 아니라 **완결 문장**이다. (Nygard는 반대로 "short noun phrases".) 우리는 문장형 — AWS 쪽인데 **규약에 안 적혀 있다.**

**③ 강제 = 코드 리뷰. 전부 사람.**
> AWS: *"a code reviewer might find changes that violate one or more ADRs. In this case, **the reviewer asks the author … and shares a link to the ADR**."*
> **AWS 가이드 전체에 자동화 언급이 0건이다.** 상태 전이 · 타임스탬프 · 버전 · supersede — 전부 owner가 손으로.

→ **우리 §8("규율이 아니라 구조로 강제한다")은 AWS와 정반대다.** AWS는 100% 규율, 0% 구조. **우리는 여기서 선행 사례를 넘어선다** — 그리고 1인이므로 **필수**다. **리뷰어가 없으면 규율은 아무것도 강제하지 못한다.**

**④ ★ ADR ↔ 티켓 연결은 문헌에 존재하지 않는다.**
조사 결론: **어느 조직도 ADR↔이슈 연결 방향에 대한 가이드를 발행하지 않았고, 도구도 없다.** 문서화되는 연결은 언제나 **ADR ↔ 코드**다.

가장 근접한 둘:
- **GDS**: *"consider using your **issue tracker** to make sure that decisions made are **followed through and put into effect**"* — *"the work isn't done until the decision is implemented."*
- **CommonGrants**: **티켓이 먼저다** — 이슈 생성 → 이슈 번호로 브랜치 → ADR 작성 → PR 리뷰. **우리와 정확히 반대 방향.**

→ **우리 §5의 게이트(`accepted founding ADR` 없이는 Epic 없음)는 선행 사례가 전혀 없다.** Arachne이 가장 가깝지만 그것은 **코드**를 막는 것이지 **티켓**을 막는 것이 아니다. **완전한 우리 발명이며, 지배적 관행은 반대 방향이다.**

**⑤ 재검토.** AWS·Microsoft 모두 **새 ADR + supersede가 유일 경로**. 정기 재검토 없음, 만료 없음.

---

## 8. ★ ADR × AI agent — 2026년의 축. 그리고 우리와 정면 충돌한다

이 저장소는 agent가 읽는 것을 전제로 설계됐다. **바깥도 지금 여기 와 있고, 우리와 반대 방향으로 가고 있다.**

### ① Vercel `adr-skill` — "ADR은 agent를 위한 실행 명세다"

> "ADRs created with this skill are **executable specifications for coding agents**" — "**A human approves the decision and an agent implements it.**"
> ADR은 *"must contain everything needed for implementation **without follow-up questions**"*
> **"The ADR must include an implementation plan"** — 건드릴 파일 · 따를 패턴 · 쓸 테스트 · 체크박스 검증

**이것은 우리 §4①(구체적 수치·리소스명·필드값을 쓰지 않는다)의 정확한 반대다.** 그리고 **Microsoft(*"Avoid making decision records design guides"*)의 정확한 반대이기도 하다.** 두 진영이 agent를 두고 갈린다.

**그런데 Vercel이 규정한 "agent가 ADR을 제안해야 하는 트리거"는 우리와 같다**: 새 의존성 도입 · 남들이 따라야 할 새 패턴 · 비자명한 트레이드오프가 있는 선택 · **기존 accepted ADR과 모순되는 코드를 쓰려 할 때** · 코드 주석에 "왜"를 길게 쓰고 있는 자신을 발견할 때.

그리고 읽기 워크플로: *"scan titles and statuses (**focus on accepted ADRs**) → read relevant ADRs fully → respect decisions."* → **`accepted`가 참/거짓 이분이어야 한다는 우리 ADR-0002 ⑥의 전제를, 바깥 도구가 독립적으로 확인해 준다.**

### ② 실증 — LLM이 ADR 위반을 잡아낼 수 있는가

**arXiv:2602.07609** (2026-02, ADR 980건 / 저장소 109곳):

> "The models achieved substantial agreement and strong accuracy for **explicit, code-inferable decisions**. Accuracy falls short for **implicit or deployment-oriented decisions** … Therefore, **LLMs can meaningfully support validation of architectural decision compliance; however, they are not yet replacing human expertise.**"

→ **LLM이 ADR의 fitness function 노릇을 할 수 있다 — 단 그 결정이 코드로 표현될 때만.** 우리 §2의 `Compliance` 공백에 대한 부분적 답이다. 그리고 **정확히 우리가 못 하는 것**을 지목한다: *deployment-oriented decisions*는 못 잡는다. 우리 ADR 대부분이 그 종류다(프로세스·규약).

### ③ ★ agent 컨텍스트는 전량이 아니라 최근 3~5건이 최적이다

**arXiv:2604.03826** (2026-04, ADR 4,500건 / 저장소 750곳):

> "a small **recency window (typically 3–5 prior records)** providing the best balance between quality and efficiency"
> "**complete decision history offers negligible benefits** compared to a strategically selected subset"
> "**context engineering, rather than model scale alone, is the dominant factor**"

→ **`_index/decisions-log.md`를 역시간순으로 만든 것이 옳았고, "전량을 agent에 먹인다"는 헛수고다.** 꼬리 3~5건이 본체다.

### ④ ★ 우리 §6(자기오염 차단)의 외부 근거

> "**Agent-generated ADRs from codebase scans will capture what was decided but may fabricate the why**" — 항상 Context와 Consequences는 사람이 검토하라.

그리고 실사용 증언 (HN):
> "I run Claude Max daily, and tried letting Opus write an ADR with known requirements. After searching through codebase, git history, etc it spat out a surface level reasonable ADR, **with the customary bloated text.**"

→ **agent는 "무엇을 정했는지"는 복원하지만 "왜"는 지어낸다.** 우리 §6("agent의 관찰은 티켓에 쌓이고, 사람이 증류해야 지식이 된다")에 대한 **가장 좋은 외부 인용**이다.

### ⑤ 그리고 이것이 ADR을 다시 살렸다

> "agentic coding tools are refactoring services that humans spent years getting right **with no memory of why the original design existed**, making ADRs now **load-bearing infrastructure** for any team where an AI agent touches production."

**1인 개발자가 ADR을 쓰는 근거로 지금 가장 많이 인용되는 것이 이것이다** — 사람과의 소통이 아니라 **agent의 기억 상실**을 막는 것.

---

## 9. ★ 실패 모드 — 이 관행은 어떻게 죽는가

**유리한 증거만 모으면 조사가 아니다.** 이 절은 도입 결정의 반대편이다.

**① 포기 곡선 — 구조적이다.**
> "ADRs are **adopted with enthusiasm, written carefully for several months, and then quietly abandoned** — either because the process feels burdensome, or because the records accumulate without anyone reading them."
> 그 진단: *"**not a cultural failure but a structural guarantee of decay built into the format itself**"* — ADR은 *"static, point-in-time documents asked to perform a living-artefact function."*

**우리 실측이 이를 뒷받침한다**: Arachne 7개월 사망 · Athens 15개월 사망 · log4brains 3년 반 침묵 · govuk-docker 41개월에 4건.

→ **우리 반론**: 그 진단("정적 문서에 살아 있는 역할을 시킨다")은 **정확히 우리가 구조로 제거한 문제**다 — 우리는 문서에 살아 있는 역할을 안 시킨다(생존형 문서 없음, `ticket:` 필드 삭제, 상태는 티켓이 담당). **그러나 포기 곡선 자체는 우리에게도 온다.** 6개월 뒤 이 저장소에 ADR이 안 늘고 있다면, 그것이 규율 실패인지 **결정이 실제로 다 굳은 것인지** 구분할 방법이 필요하다.

**② "모든 결정이 아키텍처면, 아무 결정도 아키텍처가 아니다."**
Pureur & Bittner (InfoQ): ***"if every decision is architectural, no decision is architectural."*** 처방: **되돌림 비용 × 복잡도가 높은 것에만** ADR을 쓰고, 나머지는 **별도 로그**로.
**Lullabot의 71건**이 산 표본이다 — *"Use Stylelint"* 가 ADR로 들어가 있다.
→ **우리 임계선(§4②)이 이 실패를 겨냥한 장치다.** dogfood에서 실제로 결정 2건을 걸러냈다.

**③ 아무도 안 읽는다.**
> *"They sat in docs/adr/. Nobody read them before opening a PR."* — **"The gap isn't documentation — it's surfacing. The right moment to surface a decision isn't onboarding or sprint planning. It's when someone is actively editing the code the decision protects."**
> 그래서 만들어진 것: **Decision Guardian** — PR이 보호된 파일 glob을 건드리면 관련 ADR을 **PR 코멘트로 자동 게시**하는 GitHub Action.

→ **우리에게 직격이다.** 우리 브리지는 **티켓 → 문서** 단방향이고, **코드를 건드리는 순간에 결정을 들이미는 장치가 없다.** 이것이 §2의 `Compliance` 공백과 같은 구멍이다.

**④ 썩은 ADR은 없느니만 못하다 — 그리고 불변성이 그 원인이라는 지적.**
> *"An ADR written in 2021 to justify a technology choice is not merely irrelevant in 2025 — **it is actively misleading**."*
> ★ *"**the immutability doctrine is what makes the corpus rot** — an accepted ADR cannot be corrected, only buried under a supersede that nobody links back to."*

**→ 인과가 거꾸로다(§5 참조).** 썩게 만드는 것은 동결이 아니라 **싼 탈출구(append)** 다. 동결은 supersede를 **강제**하고, append는 supersede를 **면제**한다. **실측 supersede율 10%는 append를 허용하는 세계의 숫자다.**

**단 이 반론이 남기는 진짜 위험은 따로 있다.** 우리 답은 *"`status` 하나로 유효성이 판정된다"* 인데, **그것은 supersede가 실제로 걸릴 때만 참이다.** 우리 `supersede.py`가 기계라는 것은 방어책이지만, **"supersede를 해야 한다는 것을 깨닫는 것"** 은 여전히 사람의 일이다. **동결은 탈출구를 막을 뿐, 사람이 낡은 결정을 알아차리게 해주지는 않는다.** ← 이것이 남는 구멍이고, `무효화 조건` 필드가 겨냥하는 곳이다.

**⑤ 사후 작성 = 연극.**
> *"the retroactive ADR has **the form of the decision record but not the substance**."* / *"**ADRs as theatre** … the folder sits there as a polite gesture toward documentation discipline."*
⚠️ **그런데 Spotify는 소급 작성을 명시적으로 권장한다.** 두 진영이 정면 충돌한다. **우리 ADR-0001·0002가 바로 소급 작성이다**(이미 만든 하네스를 사후에 결정으로 적었다). 이 비판은 우리를 겨눈다.

**⑥ 입도 문제는 미해결로 공인돼 있다.**
> *"there's a huge trade off in having **many records (which become essentially write-only as nobody will trawl through)** or **too few (which leave gaps or become very large)**."*
→ **우리 공동무효 테스트가 이 미해결 문제에 대한 답이다.** 선례가 없는 이유가 이것이다 — 아무도 답을 못 냈다. **우리 답이 맞는지는 dogfood로만 알 수 있다.**

**⑦ 더 싼 대체재가 있다.** 커밋 메시지(*"When it's part of the git history, the history itself tells you whether those changes stuck around or were superseded"*) · 두툼한 GitHub 이슈 · 엑셀 표.
그리고 **대형 OSS 인프라는 대부분 ADR을 안 쓴다** — Kubernetes · Istio · Grafana · Vault · Prometheus · Argo · Cilium · OpenTelemetry 전부 RFC/KEP/design-doc이다.

**⑧ 실제 인기는 글보다 훨씬 낮다.** ADR은 HN 프론트페이지에 사실상 오른 적이 없다. 학술 결론과 일치: *"adoption is still low."* → **쓰이는 것보다 쓰여지는 글이 많은 관행이다.**

**⑨ ★ 죽는 이유 1위는 "규칙을 안 정한 것"이다.**
> *"The reason teams stop writing ADRs is almost always that **nobody decided when an ADR is required, who reviews it, or where it lives** in the daily workflow."*

→ **우리는 셋 다 답이 있다** — 언제(임계선 §4②) · 누가(사람, accept 게이트) · 어디(`docs/{topic}/adr/`, 기계가 강제). **이 실패 모드는 우리에게 오지 않는다.** 조사 전체에서 우리 규약을 가장 강하게 정당화하는 한 줄이다.

그리고 **ECSA 2024 액션 리서치**(마이크로서비스 기업 3개월 개입, 인터뷰 7건)의 결론도 같은 방향이다:
> *"**the decision on where documentation is stored has a massive influence on its perceived usefulness.**"*
→ 위키·Confluence·Notion에 두면 안 읽힌다. **소스 컨트롤**이 답이다(ThoughtWorks Radar도 같은 말). 우리는 이미 거기 있다.

**⑩ Zimmermann의 ADR 안티패턴 11종** — 우리 초안을 자기점검할 체크리스트다:
> **Fairy Tale**(장점만) · **Sales Pitch**(마케팅 어투) · **Free Lunch Coupon**(장기 대가 은닉) · **Dummy Alternative**(선호안을 검증된 것처럼 보이게 하는 가짜 선택지) · **Sprint**(선택지 하나, 단기 효과만) · **Tunnel Vision**(운영·유지보수 이해관계자 무시) · **Maze**(제목과 내용 불일치) · **Blueprint/Policy in Disguise**(저널이 아니라 **명령형 요리책 어투**) · **Mega-ADR**(다쪽짜리 상세 덤프) · **Novel/Epic**(SAD 한 권을 ADR 하나에) · **Magic Tricks**(거짓 긴급성, 사이비 정량 점수)

**★ 우리 ADR-0002는 `Blueprint/Policy in Disguise`와 `Mega-ADR`에 해당할 소지가 있다** — ①~⑦로 번호 매긴 규범 목록이고, 어투가 저널이 아니라 명령형이다. 그리고 `Dummy Alternative` 위험도 있다: `Alternatives`의 선택지들이 **실제로 검토된 것인지, 기각을 정당화하려고 세운 것인지** 스스로 물어야 한다(§11①이 그 시험이다 — 가장 강한 반론을 몰랐다면 그 선택지는 진짜로 검토된 게 아니다).

**⑪ 책임 회피 도구로 쓰인다.** Pureur & Bittner: *"by putting a decision in an ADR they can **absolve themselves from consequences**."* 1인 저장소에서는 해당 없다 — 회피할 상대가 없다. **1인이 얻는 몇 안 되는 이점.**

### 1인 개발자에게 ADR이 값어치가 있는가 — 실사용자 증언

**반대**:
> *"**They're overkill for small personal projects** but can be helpful in big teams."*
> *"But I have a fear. **What if nobody bothers to read it?** … I am a solo developer on this project."*
> *"ADRs can be written excessively after-the-fact, by a single person. **I have seen them degenerate into bureaucracy.**"*

**찬성 — 그리고 근거가 소통이 아니다**:
> *"**Nothing like being able to answer 'what the hell was I thinking 6 months ago?'**"*
> *"I'm a solo developer … I also try to use ADRs, which basically **force me and others to think about and defend a decision**."*
> *"**we have a limited capability of keeping stuff in our heads.**"*

> **→ 1인에게 ADR의 값어치는 소통 채널이 아니라 ① 강제 사고 장치 ② 기억 보철 ③ (2026년) agent의 기억 상실 방지다. n=1에서 소통을 근거로 드는 사람은 아무도 없다.**

**우리 ADR-0002는 이 셋 중 무엇을 근거로 삼는가? 지금 본문에 안 적혀 있다.**

---

## 10. 대조표 — 빌린 것 / 발명한 것 / 충돌하는 것

**빌린 것 (인용 가능)**
- "왜"만 담는다 — Nygard · AWS · Microsoft
- accept = 동결, supersede만이 변경 경로 — Fowler · AWS · Microsoft
- 상태 4종 — 전 계보
- 유의성 트리거 5축 — Nygard → Richards & Ford → AWS
- 되돌림 비용 기준 — **Microsoft** (Bezos는 ADR을 말한 적 없다)
- 전역 순차 번호, 재사용 금지 — Nygard
- `adr-NNNN-<slug>.md` 소문자 kebab — adr-tools / MADR
- **인덱스는 생성물** — 생태계 만장일치
- **동결 발효 = main 브랜치** — **GDS Way**
- discussion → ADR 연쇄 — **Spotify (RFC→ADR)**
- 소스 컨트롤에 둔다(위키 아님) — ThoughtWorks Radar
- **`accepted` 이분법이 agent 소비의 전제** — Vercel adr-skill이 독립 확인
- **agent 관찰을 사람이 검증해야 한다** — *"agents may fabricate the why"*

**발명한 것 (선례 없음 — dogfood로만 검증된다)**
- **공동무효 입도 테스트** · sub-ADR · `parent:` (Microsoft의 *단계* 분해가 유일한 이웃이고, 축이 다르다)
- **부분 supersede 명시적 금지** (아무도 이 질문에 도달하지 않았다)
- **`무효화 조건` 섹션**
- **임계선의 비용 필터** (Microsoft만 같은 편)
- **`topic` / `subjects` 분리**, frontmatter 스키마
- **동결 검사 · accept · supersede의 기계화** (AWS는 100% 수작업)
- **★ ADR → 티켓 게이트** — 문헌에 전혀 없고, **지배적 관행은 반대 방향**(티켓 → ADR).
  → **근거가 생겼다**(§11③): *굳지 않은 결정 위에서 일하면 업무의 방향이 흔들린다.* ADR은 영수증이면서 **그 아래 붙는 작업의 경계**다 — 단 **제약**이지 **지시**가 아니다
- **agent 쓰기 권한 경계** (§6)

**충돌하는 것 (알고도 다른 길을 골랐음을 명시해야)**
- **AWS 예시 ADR은 Decision에 구체 규칙을 박는다** (branch protection, 승인 1건 이상) → 우리 §4①과 충돌. **Backstage의 실제 ADR에는 라이브러리 버전 핀까지 들어 있다.** 단 **Microsoft는 우리 편**
- **★ Vercel adr-skill은 ADR에 구현 계획·파일 경로·측정 가능한 제약을 요구한다** → §4①의 정면 반대. **그리고 그것이 지금 agent 진영의 주류다**
- **AWS는 문서 내 `changelog`·`version`을 요구** → 동결과 양립 불가
- **AWS는 reject에도 동결을 건다** → 우리는 accept에만
- **joelparkerhenderson의 `append`(living document)** → **유일한 진짜 반대 진영.** 나머지(GDS·영국정부·Oxide·MADR)는 재검토 결과 **반례가 아니다**(§5)
- **Spotify는 소급 작성을 권장** → 소급 작성을 "연극"이라 부르는 비판과 충돌. **우리 ADR-0001·0002가 소급 작성이다**
- **`construction techniques`** 가 우리 트리거 목록에서 빠져 있다

---

## 11. 미결 — ADR-0002를 얼리기 전에 답해야 할 것

**★ ① `Alternatives ②`가 틀린 것을 기각하고 있다. — [논의 완료, 반영 필요]**

초안은 *"동결하지 않고 갱신한다"* 를 **통째로** 기각한다. 그런데 §5의 재검토 결과 **아무도 그런 주장을 하지 않는다** — *"결정을 바꾸려면 새 ADR + supersede"* 는 **반대 진영조차 동의한다.** 즉 **존재하지 않는 선택지를 기각하고 있다** = Zimmermann의 `Dummy Alternative`.

**동결이 잠그는 것은 결정이 아니라 기록이다.** 결정은 언제든 바뀔 수 있고, 바꾸는 법은 supersede다. **동결은 과거의 결정 기록을 사후 오염으로부터 차단하는 것이다.**

→ **`Alternatives ②`를 둘로 쪼갠다:**

- **②-a 동결하지 않고 결정을 덮어쓴다** → 기존 논거로 기각 (*그때 무엇을 알았고 무엇을 버렸는지가 지워진다*). **다만 이 진영은 실재하지 않는다** — 정직하게 그렇게 적는다.
- **②-b ★ 동결하되 `append`를 허용한다** (jph의 living document — 사후 정보를 날짜 도장과 함께 덧붙인다) → **이것이 유일한 실재하는 반대 진영이고, 진짜로 기각해야 할 선택지다.**

  **기각 논거 둘:**
  1. **`append`는 부분 폐기의 다른 이름이다.** "X로 정했다 / 덧붙임: X의 전제가 깨졌다" 는 문서는 통째로 참도, 통째로 폐기도 아니다. **⑥(부분 폐기 불허)이 이미 이것을 금지한다** — ⑥을 받아들이면 append는 자동으로 죽는다.
  2. **`append`는 supersede 압력을 흡수한다.** 새 ADR은 비싸고 append는 싸다. **실측 supersede율 10%**(log4brains 2/19, Backstage 1/15)가 그 결과다. **동결은 supersede를 강제하는 장치이기도 하다.**

→ **그리고 GDS를 반례가 아니라 선례로 인용한다**(§5): 그들의 원리(*"아무도 아직 의존하지 않았다면 고쳐도 된다"*)는 우리와 **같고**, 선이 다른 이유는 **우리에게 티켓 게이트가 있어 의존이 더 일찍 시작되기 때문**이다.

**★ ② `accepted`는 무엇을 통과한 것인가. — [논의 완료, 반영 필요]**

**결론: `accepted`는 그 결정의 정당성 검토가 끝났다는 뜻이고, 검토의 방식은 규정하지 않는다.**
여럿이 논의했든 혼자 따져봤든, **검토가 끝났다는 판단은 사람이 내린다.** 팀이냐 1인이냐는 검토 방식의 차이일 뿐, `accepted`의 의미를 바꾸지 않는다.

**선행 사례가 이를 지지한다.** Nygard의 원문이 정확히 이것이다:
> "A decision may be 'proposed' **if the project stakeholders haven't agreed with it yet**, or 'accepted' **once it is agreed**."

**그는 상태의 의미만 규정하고, 합의에 이르는 방법은 규정하지 않는다.** AWS의 리뷰 회의 · Arachne의 운영위 · Harmel-Law의 Advice Process는 **각자의 집 규칙**이지 ADR의 본질이 아니다(`adr-tools`는 아예 생성 즉시 `Accepted`로 찍는다).

### ★ 그리고 ADR은 discussion에 의존하지 않는다

**Advice Process를 채택하지 않는다.** `Advice` 섹션을 의무화하는 것 = **discussion을 accept의 전제조건으로 삼는 것**이고, 그것이 **두 원칙을 동시에 깬다.**

**① 생성 의식이 생겨 빈 문서를 양산한다.** `CLAUDE.md`가 discussion에 skill을 만들지 않은 이유가 정확히 그것이다 — *"생성 의식(ritual)이 생기면 **빈 문서를 양산**한다."* **전제조건으로 만드는 순간 그게 의식이 된다.** 사고가 없어도 discussion을 만들게 된다. **규약이 자기 원칙을 어길 뻔했다.**

**② 동결 문서가 살아 있는 문서에 의존하게 된다.** **discussion은 살아 있다** — `status: active` 인 동안 계속 갱신된다(이 문서와 마찰 로그가 산 증거다). 동결된 ADR이 살아 있는 discussion을 가리키면 **`ticket:` 필드를 뺐던 것과 똑같은 실패**가 난다.

→ 그래서 규칙이 **세 번째로 같은 모양으로 확인된다**:

| 가리키는 쪽 (살아 있음) | 가리켜지는 쪽 (얼음) |
|---|---|
| 티켓 | ADR |
| **discussion** | **ADR** |

> **얼어붙은 것은 아무것도 가리키지 않는다.**

ADR-0001의 브리지 결정(*"가리키는 쪽은 살아 있는 쪽이어야 한다"*)이 **discussion 축에서도 그대로 성립한다.**

**→ ADR-0002에 discussion 언급은 넣지 않는다.** 대신 **accept의 의미 한 줄**은 넣어야 한다 — ⑤가 *"Accept가 동결선이다"* 라고 선언하는 이상, **그 선이 무엇을 뜻하는지 말하지 않으면 불완전하다.** 그리고 안 적으면 *"1인이라 리뷰어가 없으니 accept는 형식일 뿐"* 이라고 읽힌다(사람에게도, agent에게도).
**"검토 방식을 규정하지 않는다"는 것 자체가 결정이다. 침묵과 다르다.**

**남는 대가 (인정하고 넘어간다).** ADR이 단독으로 서면 검토의 흔적이 `Alternatives` 안에만 남고, **선택지가 진짜로 검토된 것인지 들러리인지 확인할 방법이 없다**(`Dummy Alternative` 위험 · §9⑩, 소급 작성 비판 · §9⑤).
→ **그러나 discussion을 강제해도 이 위험은 사라지지 않는다** — 들러리 선택지를 세울 사람은 들러리 discussion도 쓴다. **기계가 검증할 수 없는 정직성이고, 게이트를 하나 더 세운다고 생기지 않는다.** 그러므로 **강제하지 않는다.** 대가는 `Alternatives`를 정직하게 쓰는 문제로 남는다 — B1이 그 시험을 하나 줬다: **가장 강한 반론을 모른 채 기각한 선택지는, 검토된 선택지가 아니다.**

*(discussion 문서의 성격·수명주기 자체는 별도 논의로 미룬다.)*

**★ ③ 이 ADR은 누구를 위해 존재하는가. — [논의 완료, 반영 필요]**

**독자는 셋이고, 확실성이 다르다.**

| 독자 | 확실성 | 무엇을 요구하나 |
|---|---|---|
| **본인 (6개월 뒤의 나)** | 확실 | *"왜 그랬는지"* 의 복원 |
| **agent** | 확실 | **`accepted`의 참/거짓 이분** · 짧고 인용 가능한 형태 |
| **동료** | **예정 없음** | (가정적) |

**★ 세 번째를 설계 목표로 삼지 않는다.** **가상의 독자는 요구가 무한하다** — 배경을 얼마나 설명해야 충분한지 정할 수 없어 문서가 계속 길어진다. **실측이 정확히 그 궤적이다**(§3): *"ADR 관행이 새로울수록 ADR이 길다."*
→ **동료는 우연적 수혜자이지 설계 대상이 아니다. 그리고 비용이 0이다** — Nygard가 *"미래의 개발자와 나누는 대화처럼 쓰라"* 고 했는데 **6개월 뒤의 나가 이미 미래의 개발자다.** 본인과 agent를 위해 잘 쓰면 동료에게도 통한다. **따로 더 쓸 것이 없다.**

### ★ agent는 이미 하중을 받는 독자인데, 어디에도 안 적혀 있다

**ADR-0002 ⑥이 이미 agent를 근거로 쓰고 있다:**
> *"`accepted`가 문서 전체에 대해 참/거짓 이분이어야 **agent가 신뢰할 수 있다**"*

**그런데 그 문서는 agent를 독자로 소개한 적이 없다. 결론에서만 쓰고 전제를 숨겼다** → **부분 폐기 불허(⑥)의 논거가 공중에 떠 있다.** 독자 목록이 Context에 들어가야 ⑥이 성립한다.

그리고 agent를 독자로 두는 것에서 **이미 규약 여럿이 파생돼 있다**:
- **`accepted` 이분법**(⑥) — Vercel agent skill도 독립적으로 같은 요구를 한다(*"focus on accepted ADRs"*)
- **§6 자기오염 차단** — *"agents may **fabricate the why**"*
- **`decisions-log.md`의 시간순** — 실증: agent 컨텍스트는 **최근 3~5건이 최적**, 전량은 무의미(§8③)

### ★ 그리고 독자가 아닌 값어치 둘 — 하나가 우리 최대 발명의 근거다

**① 강제 사고 (쓰는 시점의 값).**
**Fowler는 이것을 기록물과 동등한 두 값어치 중 하나로 든다**: *"**the act of writing them helps to clarify thinking**."* 1인 개발자 증언도 같다: *"ADRs **force me to think about and defend a decision**."*

**→ 이것이 최대 비판을 무력화한다.** §9③의 *"아무도 안 읽는다"* 는 **값어치가 읽는 시점에만 있다고 전제할 때만** 치명적이다. **절반이 쓰는 시점에 실현되면, 다시 안 읽혀도 ADR은 이미 값을 했다.**
**⚠️ 함정**: 값이 쓰는 데 있다면 **많이 쓸수록 좋다는 유혹**이 생긴다 → `Mega-ADR`·`Novel` 안티패턴. **강제 사고의 본질은 분량이 아니라 "왜"와 "무엇을 버렸는지"를 말하도록 강제받는 것이다. Y-statement 한 문장도 강제 사고다.** (→ §11⑥)

**② 업무 방향성 (다운스트림의 값). ★ §5 게이트의 잃어버린 근거다.**

§7④에서 확인했듯 **ADR→티켓 게이트는 문헌에 선례가 전혀 없고, 지배적 관행은 반대 방향**(티켓 먼저 → ADR 나중)이다. **그 근거가 여기 있다:**

> **굳지 않은 결정 위에서 일하면 업무의 방향이 흔들린다.**
> ADR은 뒤를 보는 영수증이면서, **동시에 그 아래 붙는 모든 작업의 경계를 긋는다.** 그래서 컨테이너 티켓이 accepted ADR을 전제한다.

**⚠️ 여기서 선을 정확히 그어야 한다** — 이 논거가 §4①(값·구현을 담지 않는다)을 무너뜨리는 데 쓰일 수 있다. **Vercel 진영이 정확히 그 길로 갔다**(*"ADR은 agent를 위한 실행 명세이며 구현 계획을 담아야 한다"*, §8①).

> **ADR은 지시(instruction)로 앞을 향하지 않는다. 제약(constraint)으로 앞을 향한다.**
> *무엇을 하라*가 아니라 ***무엇이 정해졌으므로 어디를 벗어나면 안 되는가***를 준다.

**이 구분이 §4①과 §5 게이트를 동시에 지킨다.** 방향성을 준다는 이유로 구현을 담기 시작하면 **설계 문서가 된다.**

**★ ④ `Compliance`/`Confirmation` 공백 — 두 방향에서 같은 구멍이 뚫린다.**
- 우리는 검증·강제를 코드·게이트로 밀었는데, **게이트가 없는 결정**(예: "ADR은 왜만 담는다")은 강제 방법이 아무 데도 안 적힌다
- 그리고 *"nobody read them before opening a PR"* — **코드를 건드리는 순간에 결정을 들이미는 장치가 없다**
→ 섹션을 추가할 것인가, 강제 불가를 인정할 것인가, Decision Guardian 식 장치를 코드 저장소에 둘 것인가.

**⑤ 소급 작성 비판이 우리를 겨눈다.** ADR-0001·0002는 **이미 만든 하네스를 사후에 결정으로 적은 것**이다. Spotify는 이를 권장하고, 비판론은 "연극"이라 부른다. **어느 쪽인지 스스로 답해야 한다.** (변론 가능한 답: 하네스를 만드는 과정 자체가 discussion이었고 그 마찰 로그가 남아 있다.)

**⑥ 우리 ADR이 길다.** 실측 중앙값 613 단어, 우리는 상위 25%. GOV.UK는 **237~267 단어**로 같은 일을 한다. **담는 게 많은 것인가, 그냥 긴 것인가.** Zimmermann의 안티패턴 목록이 이를 겨눈다 — **Mega-ADR** · **Novel/Epic** · **Blueprint or Policy in Disguise**(*"cookbook/commanding tone instead of journal style"*). **우리 ADR-0002의 ①~⑦ 번호 매긴 규범 목록은 정확히 이 안티패턴처럼 보인다.**

**⑦ 트리거에서 `construction techniques`가 빠진 것은 의도인가.** 라이브러리·프레임워크·도구 채택이 ADR감이 아니라면, ADR-0001이 *"도구 이름을 본문에 박지 않는다"* 고 한 것과 어떻게 다른가. (도구 **선택**은 결정이고 도구 **이름**은 값이다 — 이 구분이 성립하는지)

**⑧ `proposed`를 파일에 적을 필요가 있는가.** **GDS는 PR 자체를 `proposed` 상태로 쓴다** — status 필드는 accept 전까지 존재하지 않는다. 우리는 파일에 적고 `accept.py`가 고친다. **더 단순한 길이 있었다.**

**⑨ 제목 규약이 갈리는데 우리 규약에 없다.** Nygard=명사구, AWS=완결 문장. 우리는 문장형이다.

**⑩ 확신도(confidence level)를 기록할 것인가.** Microsoft가 요구한다. **동결 모델에서 "확신이 낮은데 얼린다"가 무엇을 뜻하는가** — 무효화 조건 필드가 이미 그 역할의 일부를 하는지 볼 것.

---

## 12. 결론 — 이 조사가 바꾸는 것

**우리는 ADR이라는 이름을 빌리되, 가장 엄격한 진영에 서 있고, 그 진영조차 하지 않는 것을 한다** — 입도 규칙 · 부분 폐기 금지 · 기계 강제 · ADR→티켓 게이트.

그것이 틀렸다는 뜻은 아니다. **우리가 푸는 문제가 그들과 다르기 때문**일 수 있다:

| | 그들 | 우리 |
|---|---|---|
| 독자 | 팀 · 미래의 팀원 | **6개월 뒤의 나 · agent** |
| accept의 정당성 | 팀 합의 (집 규칙) | **정당성 검토 완료 — 방식은 규정하지 않는다** |
| 강제 주체 | 코드 리뷰어 (사람) | **스크립트** (리뷰어가 없으므로) |
| 동결의 값어치 | 이력 보존 | **agent가 신뢰할 참/거짓 이분** |

**이 표의 오른쪽 열이 ADR-0002가 적어야 할 것이다.** 지금 초안은 동결을 **그 자체로 옳은 것**처럼 논증하는데, **동결이 옳은 것은 우리 조건에서다.** 그 조건을 적지 않으면, ADR-0002는 자기가 딛고 선 전제를 숨긴 문서가 된다.

**최소 3건을 고치고 얼린다**:
1. `Alternatives ②`를 **②-a(결정 덮어쓰기 — 실재하지 않는 진영) / ②-b(`append` — 진짜 상대)** 로 쪼개고, 실재하는 쪽을 제대로 기각 (§11①)
2. **accept의 의미 한 줄** — *"정당성 검토가 끝났다는 뜻이며, 검토 방식은 규정하지 않는다"*. **discussion은 언급하지 않는다** (§11②)
3. **Context에 독자를 적는다** — **6개월 뒤의 나 · agent**. (동료는 우연적 수혜자이지 설계 대상이 아니다.) **⑥이 이미 agent를 근거로 쓰면서 독자로 소개한 적이 없다** — 전제를 숨긴 채 결론에서만 쓰고 있다 (§11③)
4. **값어치가 읽는 시점에만 있지 않다는 것** — 쓰는 과정이 "왜"를 강제하고, 그 결과 **그 결정 아래 붙는 작업의 경계가 그어진다.** 단 그 경계는 **제약**이지 **지시**가 아니다 (§11③)

**그리고 이 조사가 뒤집은 것 둘을 기록해 둔다.**

**① 동결 반대 진영은 실제보다 커 보였다.**
> **모두가 동의하는 것**: 결정을 바꾸려면 **새 ADR + supersede**.
> **유일한 쟁점**: 기록에 `append`할 수 있는가.
> **우리 답**: 못 한다 — **append는 부분 폐기이고(⑥), supersede를 면제해 코퍼스를 썩힌다.**

**"동결은 결정을 얼리는 것이 아니라 기록을 얼리는 것"** — 이 한 줄이 없어서 반대 진영이 실제보다 커 보였다. **ADR-0002 본문에 이 문장이 먼저 와야 한다.**

**② 선행 사례를 그대로 들이면 우리 원칙을 어길 뻔했다.**
Advice Process(의무 `Advice` 섹션)를 채택했다면 **discussion에 생성 의식이 생겨 빈 문서를 양산**하고, **동결 문서가 살아 있는 문서에 의존**하게 됐다. **선행 사례의 결론은 취하되, 장치는 취하지 않는다.**
→ 그리고 그 대가로 규칙 하나가 세 번째로 확인됐다: **얼어붙은 것은 아무것도 가리키지 않는다.**

**그리고 이 조사가 뒤집은 것 하나를 기록해 둔다.** 처음에 세었을 때 동결 반대 진영은 커 보였다(jph 철회 · GDS · 영국정부 · Oxide · MADR). **정확히 세어 보니 하나였다.**

> **모두가 동의하는 것**: 결정을 바꾸려면 **새 ADR + supersede**.
> **유일한 쟁점**: 기록에 `append`할 수 있는가.
> **우리 답**: 못 한다 — **append는 부분 폐기이고(⑥), supersede를 면제해 코퍼스를 썩힌다.**

**"동결은 결정을 얼리는 것이 아니라 기록을 얼리는 것"** — 이 한 줄이 없어서 반대 진영이 실제보다 커 보였다. ADR-0002 본문에 **이 문장이 먼저 와야 한다.**

**그리고 발명(공동무효 입도 · 부분 폐기 금지 · ADR→티켓 게이트 · 무효화 조건)은 인용할 권위가 없다 — dogfood로만 검증된다.** 그중 둘(무효화 조건 · 동결 발효 시점)은 이미 첫 dogfood에서 값을 했다.
