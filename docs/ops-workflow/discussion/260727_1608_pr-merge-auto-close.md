---
type: discussion
topic: ops-workflow
subjects: [github-issues, github-projects, ticket-engineer]
status: done
---

# PR 머지와 티켓 종료 — close는 판단인가 의례인가

이 문서는 **"PR 머지 = 작업 완료"라면 티켓 close·Status 전이를 플랫폼에 연동할 수
있는가**에 대한 조사·발산이다. 정책을 *정하지* 않는다 — (a) close가 지금 정책 어디에
어떻게 서 있는지, (b) GitHub의 네이티브 메커니즘이 무엇을 지원하고 어디서 부러지는지,
(c) 특히 **다중 target 티켓에서 곤란해지는 지점**을 드러내고, 사용자와 정할 논점을
남긴다.

> 조사 원천: **CLAUDE.md §5·§8** · **ADR-0017**(proposed — 선행 완료 기준으로 close를
> 언급) · **ticket-engineer 하네스**(`ticket-report` preflight · `ticket-run.py`) ·
> GitHub docs(closing keywords · linked branches · Projects built-in workflows).

---

## 1. 문제 — 머지 뒤에 남는 두 번의 클릭

현행 완료 흐름은 이렇다:

```
agent: AC 대조 코멘트 게시 (ticket-report)
  → 사람: 코멘트·PR 검수 → 머지
  → 사람: Project Status → Done        ← 이 둘이 문제의 자리
  → 사람: 티켓 close                    ←
```

검수는 이미 머지 **앞**에 산다 — `ticket-report`가 Acceptance Criteria 항목별 대조를
코멘트로 공표하고, 사람은 그것을 근거로 머지한다. 머지가 검수의 종점이라면, 그 뒤의
Status 전이와 close는 **판단이 아니라 의례**다. 의례의 비용은 클릭 두 번이 아니다:

- **잊힌다.** 판단 없는 행위는 미뤄지고, 미뤄진 close는 후행 티켓의 착수 게이트를
  **부당하게 막는다**(ADR-0017 — 선행이 열려 있으면 착수 거부). 게이트가 "검수 안 됨"이
  아니라 "클릭 안 함"을 감지하는 순간, 게이트의 신호가 거짓말을 한다.
- **"agent에게 시키나"는 답이 아니다.** agent 대행 close는 §8의 구조 기둥 — *"도구에
  close 기능이 없어서 수동 close가 지켜진다"* — 을 허문다. 게다가 사람이 여전히
  지시해야 하므로 의례는 사라지지 않고 자리만 옮긴다.
- **제3의 길이 플랫폼에 있다.** 트리거가 **사람의 머지 행위**인 자동화 — close 권위는
  사람에게 남고, 표현(별도 클릭)만 사라진다.

## 2. 현재 정책 지형 — close는 어디에 적혀 있나

| 자리 | 내용 | 지위 |
|---|---|---|
| CLAUDE.md §5 | *"close도 항상 사람이 한다 — PR 머지 ≠ 티켓 종료"* | 규약 |
| CLAUDE.md §8 | *"도구에 close 기능이 없어서 수동 close가 지켜진다"* | 구조 강제 목록 |
| ADR-0017 (**proposed**) | 선행 완료 기준 = close(사람 검수 후에만). 버린 대안 ③: *"머지는 검수가 아니다 — 머지와 종료 사이에 사람의 검수가 산다"* | 언급 — 주제는 의존성 |
| ticket-engineer `ticket-report` | preflight ③이 PR 본문의 **close 키워드 부재**를 검사(있으면 보고 거부) · 절차 5 *"이후는 사람의 것 — 검수·머지·close"* | 하네스 |
| ticket-engineer `ticket-run.py` | "PR 머지 + 티켓 열림" → exit 3(사람 개입) | 하네스 |

주의할 것: ADR-0017의 **주제는 리프 간 의존성**이고 close 기준은 그 완료 판정의 언급이다.
close 의미론이 바뀌어도 ADR-0017의 결정 실질(의존 명시·침묵 거부·착수 게이트)은 그대로다
— proposed 상태이므로 해당 문구는 **본문 수정**으로 고칠 수 있다(supersede 불요).
한편 ADR-0017 자신이 재검토 신호를 남겼다: *"검수 병목이 상례가 된다면 — 완료
기준(종료)과 검수 절차의 관계를 재검토해야 한다."* 이 discussion이 그 신호의 응답이다.

## 3. 전제의 재검토 — 검수는 어디 사는가

ADR-0017 대안 ③의 기각 사유는 *"머지와 종료 사이에 사람의 검수가 산다"*였다. 현행
절차의 실측은 다르다 — 검수의 재료(AC 대조 코멘트)는 머지 **전에** 공표되고, 사람은
검수하고 나서 머지한다. 머지와 종료 사이에 남는 것은 검수가 아니라 의례다.

단, 이것이 **모든 티켓에서 참인가**가 관건이다. 머지 *후*에야 가능한 검증 — 배포 결과
확인, 운영 지표 관찰 — 이 완료 조건에 들어 있는 티켓이라면 merge ≠ done이고, 그런
부류에서 자동 close는 검수를 건너뛴다. **(→ Q1)**

보존되는 것도 분명히 하자. 자동 close의 트리거는 사람의 머지다:

- agent의 도구에 close가 생기지 않는다 — §8의 기둥은 그대로다.
- close의 권위는 여전히 사람에게 있다 — 한 행위(머지)가 두 의미(수용+종료)를 싣는
  것뿐이다. 바뀌는 것은 §5의 **표현**(*"PR 머지 ≠ 티켓 종료"*)이지, *"close는 사람의
  판단을 따른다"*는 실질이 아니다.

## 4. GitHub 메커니즘 — 조사 결과

이 시스템의 구조(티켓 이슈는 ops-workflow에, PR은 target 저장소에)에서:

| 메커니즘 | 교차 repo | 판정 |
|---|---|---|
| **close 키워드** — PR 본문 `Closes jyoliar-lab/ops-workflow#N` | **지원** (default branch로 머지 시) | ✓ 유일한 네이티브 경로 |
| linked branch(Development 섹션) 자동 close | 같은 repo 한정 | ✗ 이 구조에 부적용 — 착수 시 linked branch 도입 여부와 **독립** |
| Projects 내장 워크플로 *"Item closed → Status: Done"* | 해당 없음 (이슈 close에 연동) | ✓ Done 전이는 agent 없이 해결 |

- **델타가 작다.** preflight ③은 이미 PR 본문에 `jyoliar-lab/ops-workflow#N` **참조**를
  요구한다. 채택 시 델타는 참조를 close 키워드로 **승격**하고 검사를 반전(부재→존재)하는
  것이다.
- **생애주기가 대칭이 된다.** 발행(Backlog) → 착수 스크립트가 In Progress(사람이 지시한
  전이의 대행) → 사람의 머지가 close→Done(사람이 행한 판단의 연쇄). 모든 전이가 사람
  행위에 뿌리를 두고, 클릭은 없다.
- **실험으로 확인할 것**: 교차 repo 키워드 close의 권한 조건(머지하는 사람에게 이슈
  저장소 권한이 필요한가) · 실동작. 파일럿 투입 전 1회 실험이면 충분하다.

## 5. 곤란한 지점 — 다중 target 티켓

close 키워드는 **PR 단위**이고, GitHub는 "이 이슈에 연결된 모든 PR의 머지"를 기다리지
않는다 — **키워드를 단 첫 PR이 머지되는 순간 티켓이 닫힌다.** target이 여럿인 티켓
(PR 여럿)에서 이것은 조기 close이고, 후행 착수 게이트가 거짓으로 통과된다 — §1이
없애려는 거짓 신호의 반대 방향 판이다.

| 후보 | 내용 | 판정 |
|---|---|---|
| ① 전 PR에 키워드 | 첫 머지가 닫는다 | ✗ 조기 close — 탈락 |
| ② 마지막 PR에만 키워드 | "마지막"은 PR 생성 시점에 모르고, 머지 순서는 사람 임의다 | ✗ 취약 — 탈락 |
| **③ 단일 target만 자동, 다중은 현행 유지** | 분기 기준(target 수)은 티켓 '저장소' 절에 이미 있고, preflight가 이미 읽는다 — 기계 판정 가능 | **권고** |
| ④ 별도 자동화(Actions 등)로 "전 PR 머지 시 close" | 교차 repo 이벤트 배선·새 기계. 네이티브 우선의 결에 반함 | ✗ 현 단계 과잉 |

③의 성격: 규칙이 갈라지지만 **분기가 기계적**이다 — 집행자의 추론이 아니라 target
수라는 이미 선언된 사실(ADR-0016)에서 결정된다. preflight가 target 수를 보고 단일이면
키워드 존재를, 다중이면 부재를 요구하면, 두 경로 모두 구조 검사로 남는다. 다중 target
티켓의 close는 지금처럼 사람이 한다 — 마지막 머지가 어느 것인지는 사람만 알기 때문이고,
그 판단이 실재하는 한 close는 의례가 아니라 판단이다(§1의 논리가 거꾸로 이 잔존을
정당화한다).

## 6. 사용자와 정해야 할 논점

- **Q1 — 머지 후 검증이 실재하는 티켓 부류가 있는가.** 없다고 보면 단일 target 전면
  자동 close. 있다면 그 부류의 표지(완료 조건에 머지-후 검증이 적힌 티켓?)를 정하고
  자동 close에서 제외하는 방식 — 표지가 기계 판정 가능한지가 관건.
- **Q2 — 다중 target 처리.** §5의 ③(단일만 자동)으로 가는가? ④(별도 자동화)를 미래
  후보로 기록만 해 두는가?
- **Q3 — 강제 지점.** preflight ③의 반전(단일 target: 키워드 존재 검사 / 다중: 부재
  검사)으로 충분한가? `ticket-run.py`의 "PR 머지+티켓 열림 → exit 3"은 다중 target
  경로에서만 의미가 남는다 — 단일 경로에서는 그 상태 자체가 과도기(머지≈close 사이)
  아니면 이상 신호다.
- **Q4 — 정책 문서 델타.** 채택 시: CLAUDE.md §5 문장 개정(*"PR 머지 ≠ 티켓 종료"* →
  단일/다중 분기 반영) · ADR-0017 본문 수정(proposed — 완료 기준 언급부와 대안 ③ 기각
  사유를 현실에 맞게) · §8 구조 목록 갱신(*"도구에 close 기능이 없다"*는 그대로 참 —
  close하는 것은 agent 도구가 아니라 플랫폼이다). Projects 워크플로("closed → Done")
  활성 확인도 델타의 일부.

## 7. 다음 걸음 제안

1. 사용자와 Q1·Q2를 정한다 — 이 둘이 결정의 뼈대다.
2. 교차 repo close 키워드 실험 1회 (권한·실동작 확인).
3. 채택 시 델타는 한 작업 단위로: ops-workflow(CLAUDE.md §5 · ADR-0017 본문 수정 ·
   `_index` 재생성) + ticket-engineer(preflight ③ 반전 · `ticket-report`/`ticket-start`
   문서 개정) — ADR-0017은 파일럿 중이므로 steward `pilots.md`의 해당 행도 갱신.
4. Projects 내장 워크플로(closed → Done) 활성 상태 확인 — 꺼져 있으면 켠다(사람).

---

## 8. 결정 기록 (260727) — 자동 close 기각 · 착수는 linked branch로

사용자가 Q1에 답했다: **머지 후 검증이 실재한다 — 자동 close는 전면 기각.**

- **Q1의 답**: gitops 저장소라면 **배포 후 결과 확인까지가 완료 기준**인 경우가 흔하다.
  merge ≠ done인 부류는 예외가 아니라 상례다 — ADR-0017 대안 ③의 기각 사유(*"머지와
  종료 사이에 사람의 검수가 산다"*)는 §3의 의심과 달리 **유효했고, 재확인됐다.**
- 따라서 Q2·Q3·Q4는 무효다. 현행 정책 문구(CLAUDE.md §5 *"PR 머지 ≠ 티켓 종료"* ·
  ticket-report preflight의 close 키워드 부재 검사)는 **그대로 유지한다.** ADR-0017
  본문 수정도 불요해졌다.

**대신 이 조사의 부산물 하나를 채택한다** (§4에서 "독립"으로 표시했던 축): **착수 시
원격 브랜치 생성을 GitHub 네이티브 linked branch로 전환한다.** 근거 — 티켓이 어느
브랜치에서 진행되는지가 타임라인 멘션이 아니라 이슈의 **Development 필드**에 서는 쪽이
정보 전달이 좋다. 브랜치에서 만든 PR도 같은 자리에 자동 연결된다.

설계 (ticket-engineer `ticket-run.py` `remote_branch()` 델타):

- **생성**: `gh api POST git/refs` → `gh issue develop <N> -R <이슈 repo>
  --branch-repo <target> --name ticket/<N>-<slug> --base <default>`. 관례(이름·기점·
  원격 생성)는 전부 유지된다 — 바뀌는 것은 생성 경로와 Development 연결뿐.
- **착수 판별은 현행 유지** (원격 `ticket/<N>-*` 접두 매칭). linked 여부와 무관하게
  동작하므로 기존 브랜치의 소급 연결이 **불요**하다(원하면 이슈 Development UI에서
  수동 연결 가능).
- **같은 저장소 가드**: target이 티켓 이슈와 **같은 저장소**면 linked 생성을 하지 않고
  기존 방식(비연결 ref 생성)으로 폴백한다 — 같은 repo의 linked PR이 기본 브랜치에
  머지되면 **이슈가 자동 close**되는데, 그것이 바로 이 문서가 기각한 동작이다. 기각
  결정을 규율이 아니라 구조로 지킨다.
- **실험으로 확인할 것** (다음 실착수 1건 또는 일회용 이슈로): 교차 repo
  `gh issue develop`의 권한 조건 · `--base`가 branch-repo의 브랜치를 가리키는지 ·
  교차 repo linked PR 머지가 이슈를 건드리지 않는지(문서상 같은 repo 한정이나 실측
  확인).

## 9. 실측 (260727, 같은 날) — 교차 repo에서도 자동 close가 일어났다. §8의 전제 오류

§8의 실험 항목이 첫 실착수(#14)에서 그대로 실행됐고, **핵심 가정이 깨졌다.**

관측된 인과 (타임라인·PR 메타데이터로 확인):

1. 착수 시 새 코드가 `ticket/14-review-strict-conversion-pilot`을 **linked branch**로
   생성 — 교차 **org**다(이슈: jyoliar-lab/ops-workflow ↔ 브랜치:
   jyoliar-careerhub/careerhub-api-composer).
2. 그 브랜치의 PR(#3)이 이슈 Development에 **자동 연결**(`connected` 이벤트).
3. **사람이** PR을 기본 브랜치(`prod`)로 머지 → GitHub가 이슈를 **자동
   close**(`closed` 이벤트의 actor = 머지한 사람 · `stateReason: COMPLETED`).
   PR 본문에 close 키워드는 없었다(preflight 통과한 일반 참조뿐) — close는 키워드가
   아니라 **Development 연결 자체**에서 왔다.
4. Project Status는 In Progress 그대로 — *"Item closed → Done"* 내장 워크플로는 이
   Project에서 동작하지 않았다(비활성 추정 — 설정 UI에서 확인 필요, API 미노출).

교정되는 사실: **Development 연결 PR의 머지-자동-close는 같은 repo 한정이 아니다** —
교차 repo·교차 org에서도 일어난다(§4 표의 "같은 repo 한정"은 close *키워드* 문서에서
잘못 옮겨온 것). 따라서 `remote_branch()`의 같은-저장소 가드는 **무의미한 부분
방어**다 — 모든 경로에서 자동 close가 산다.

귀결 — **두 요구는 플랫폼에서 양립하지 않는다.** Development 필드 연결(원함)과 자동
close 없음(§8 결정)은 같은 메커니즘의 두 얼굴이다. GitHub는 "연결하되 닫지 않는"
스위치를 제공하지 않는다. 갈림길:

- **A — linked branch 철회.** 원시 ref 생성으로 복귀(§8 델타 되돌림). Development
  가시성을 포기하고 멘션 참조(현행 preflight 의무)로 산다. §8의 자동 close 기각
  결정과 정합.
- **B — linked branch 유지, 자동 close 수용.** §8 결정의 번복 — 트리거가 사람의
  머지라는 점(권위 보존)은 참이나, gitops류(머지 후 검증이 완료 기준)에서 조기 close가
  구조화되고, 조기 close는 후행 착수 게이트(ADR-0017)를 거짓으로 통과시킨다. reopen은
  사후약이지 방어가 아니다.
- (기각) 머지 전 Development 연결을 사람이 수동 해제 — 없앤 의례보다 나쁜 의례.

*(#14 자체는 사후 처리 불요 — 사용자가 닫으려던 참이었고 close 상태가 의도와 일치.
Status Done 전이만 남았다.)*

## 10. 조사 (260727) — 자동 close를 끄는 저장소 설정이 존재한다 (제3안 C)

§9의 "양립하지 않는다"는 **2025-04-23 이후 거짓**이다. GitHub이 저장소 설정을 추가했다:

- **설정**: Settings → General → **Issues** 절 → *"Auto-close issues with merged
  linked pull requests"* 체크 해제. 기본값은 켜짐(기존 동작 보존).
- **의도가 정확히 이 사례다** — changelog 원문: *"for many teams, merging a PR
  doesn't mean the work is done. There might be QA, validation, or follow-up steps
  before an issue is truly resolved."* §8의 기각 사유(gitops — 배포 후 확인)와 같은
  문장이다.
- **위치가 Issues 절**이므로 "이 저장소의 이슈가 자동 close되는가"를 지배하는 것으로
  읽힌다 → 끄는 곳은 **티켓 이슈가 사는 ops-workflow 한 곳**이면 될 것이다. 단
  교차 repo PR에 대한 지배 여부는 **문서에 명시가 없다** — 실험 1회로 확정한다.
- **주의 — 범위가 넓다**: 커뮤니티 보고에 따르면 이 설정을 끄면 명시적 close
  키워드(Closes/Fixes)까지 무력화된다. 이 시스템에는 무해하다 — preflight가 키워드를
  이미 금지한다. 오히려 방어가 한 겹 늘어나는 셈.
- **API·ruleset 미노출** — UI 수동 설정만 가능하다. 스크립트가 검사·강제할 수 없는
  **수동 불변식**이 된다(§8 패턴의 예외). 티켓 이슈 저장소가 ops-workflow 하나뿐이라
  1회 설정으로 족하나, 설정의 존재를 하네스 문서에 기록해 둔다.

**갈림길 갱신**: C — **linked branch 유지 + ops-workflow에서 이 설정 해제.**
Development 가시성과 자동 close 없음을 모두 얻는다. §8의 결정(자동 close 기각)과
§8의 채택(linked branch)이 둘 다 산다. 채택 절차:

1. **사람이** ops-workflow Settings에서 설정 해제 (API 없음).
2. **실험 1회** — 일회용 이슈 → linked branch(교차 repo) → PR → 기본 브랜치 머지 →
   이슈가 열려 있는지 확인. 열려 있으면 C 확정.
3. C 확정 시 `remote_branch()`의 같은-저장소 가드 제거 — 제어점은 저장소 설정
   하나다(가드는 §9에서 확인됐듯 부분 방어라 남기면 오히려 이중 규범이 된다).

## 11. 종결 (260729) — C 채택·확정. 자동 close는 저장소 설정으로 종료됐다

- **§10 절차 1** — 사람이 ops-workflow Settings에서 *"Auto-close issues with merged
  linked pull requests"*를 **해제했다** (웹 콘솔 · 260729).
- **§10 절차 2** — 사람이 **확인 완료** — 설정 해제 후 linked PR 머지가 이슈를 닫지
  않는다. **C 확정.**
- **§10 절차 3** — `remote_branch()`의 같은-저장소 가드를 제거했다(ticket-engineer
  동반 커밋). 이제 제어점은 저장소 설정 하나다.
- 이 설정은 **API·ruleset 미노출의 수동 불변식**이다(§10) — 기록은 이 문서가
  담당한다(별도 하네스 문서 기재는 하지 않기로 했다). 티켓 이슈 저장소를 옮기거나
  늘리면 그 저장소에서도 같은 설정을 꺼야 한다.

정책 문구 델타는 없다 — §8의 결론(자동 close 기각 · CLAUDE.md §5 유지)이 그대로이고,
linked branch(§8 채택)는 이 설정 아래에서 자동 close 없이 산다. 이 문서는 닫는다.

## 12. 후기 (260814) — 후속 PR의 Development 연결: 키워드 검사를 "부재"에서 "티켓 연결만"으로 반전

운영에서 새 요구가 나왔다: **같은 티켓의 두 번째 이후 PR**(squash 머지 후 후속 작업)은
Development 절에 자동 연결되지 않는다 — linked branch 의 자동 연결은 첫 PR 에서
소진되고, 사람이 이슈 UI gear 로 일일이 연결해 왔다.

조사 결과, **기존 PR 을 Development 에 연결하는 공식 API 는 여전히 없다**(GraphQL 은
`createLinkedBranch`/`deleteLinkedBranch` 뿐 — community discussion #155339, 2026-06
기준 미해결). 유일한 자동화 경로는 **close 키워드**(`Closes jyoliar-lab/ops-workflow#N`,
기본 브랜치 대상 PR)다. §10의 저장소 설정(수동 불변식)이 자동 close 를 막으므로,
키워드는 이제 "닫는 장치"가 아니라 "연결 장치"다 — 수동 gear 연결과 같은 노출이고,
제어점은 동일하게 저장소 설정 하나다.

**채택 델타** (ticket-engineer — §11 방어 한 겹의 의도적 해제):

- PR 생성 관문(`ticket-pr.py` — 260814 신설)이 본문에 `Closes jyoliar-lab/ops-workflow#N`
  을 덧붙인다(멘션 참조의 승격 — 브리지 + Development 연결).
- preflight ③을 반전: 키워드 **부재** 검사 → **티켓 연결만 허용**. 티켓 밖 이슈를 겨눈
  키워드는 계속 거부한다 — 설정 보호는 ops-workflow 한 곳뿐이고, 다른 저장소의 이슈는
  머지 시 정말 닫힌다.
- §8의 결정 실질(자동 close 기각 · close 는 사람)은 그대로다 — 바뀐 것은 하네스의
  방어선 구성이지 정책이 아니다.

**실측으로 확인할 것**(다음 PR 1건): 설정 해제 상태에서 키워드가 close 없이
**Development 연결을 만드는지** — 설정의 문서화된 효과는 "닫지 않음"이고 연결 생성은
남는 것으로 읽히나, 명시 문서가 없다. 연결이 안 생기면 이 델타는 무효(수동 gear 로
복귀)다.
