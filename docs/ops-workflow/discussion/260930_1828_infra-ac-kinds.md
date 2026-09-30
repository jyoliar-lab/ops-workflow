---
type: discussion
topic: ops-workflow
subjects: [ticket-engineer, ticket-start, ticket-report, github-issues, jyoliar-k8s, kustomize, ansible, terraform, argocd, prometheus, pytest]
status: active
ref-adrs: [ADR-0016, ADR-0017]
ticket:
related: [260910_1900_promise-gate-per-repository-class.md, 260930_1524_tdd-flow-decisions.md, 260930_1356_tdd-flow-in-ticket-engineer.md]
---

# 인프라 AC 의 세 종류 — 약속이 상태일 때 무엇이 증거인가

`260910_1900` §7 이 사람에게 남긴 질문 중 Q1(인프라에서 소유하고 싶은 것 — 렌더인가 실행 상태인가) · Q2(1회 실측을 약속 인공물로 인정하나)에 대한 답이다. 답은 "둘 중 하나" 가 아니라 **AC 의 종류에 따라 갈린다**. 사람 판정 2026-09-30.

## 1. 발단

#109(obs-toolkit Bug)의 AC 넷 중 하나 — "위 두 경우가 `tests/contracts/` 의 테스트로 못 박혀 있다 — 규약을 따른다" — 는 동작이 아니라 **인공물의 자리·형태**에 대한 조건이었다. tdd-loop(red 커밋 · verifier 커버리지 표)와 저장소의 메타테스트가 이미 강제하는 것을 AC 로 옮겨 적은 것 — 티켓판 "원천이 둘".

같은 눈으로 인프라 티켓 여덟 건(#78 · #79 · #80 · #81 · #89 · #99 · #100 · #101)의 AC 를 보면, 애플리케이션과 달리 **약속이 상태**이고 그 상태가 한 종류가 아니다.

## 2. 애플리케이션과 인프라 — 약속이 다르다

| | 애플리케이션 | IaC / GitOps |
|---|---|---|
| 약속 | 동작 — Given X, When 호출, Then Y | 원하는 상태 — 선언이 X 이고, 실 시스템이 X 로 수렴하고, X 에 머문다 |
| 검증 시점 | 머지 전, 한 번 | 셋 — 적용 전(형상) · 적용 직후(수렴) · 적용 뒤 창(지속) |
| 증거 | 테스트 파일 — 저장소에 남는다 | 종류마다 다르다(§3) |
| red → green | 항상 | 형상 단언 · GPL 스크립트에서만. 선언값 변경은 먼저 실패할 것이 없다 |

외부 근거(조사 2026-09-30):
- Terraform `terraform test` 는 `plan` 모드(단위 격 — 실 리소스 없음)와 `apply` 모드(통합 격)를 갈라 놓는다. 1.7 mock 으로 프로바이더 없이 로직만. → 형상 단언에 red/green 자리가 있다.
- OpenGitOps 원칙 "continuously reconciled" — 수렴은 런타임 성질. **머지 ≠ 수렴.**
- ArgoCD 는 Sync 와 Health 가 별개 신호(Synced 이면서 Degraded 가능). Flux `Ready` 는 롤아웃 완료 뒤에만.
- Google SRE(canarying): 테스트 환경은 프로덕션과 같지 않다 — 설정 변경도 카나리 대상, 완료 판정은 소수 SLI 와 롤백 조건.
- Kief Morris: 선언 코드 수준의 단위 테스트는 가치가 낮다(문법 오류는 apply 가 잡는다). GPL 로 쓴 IaC 에서는 TDD 가 맞는다.
- 인프라 AC/DoD 를 규정한 1차 문헌은 찾지 못했다 — 아래 종류 구분은 도구의 의미와 우리 티켓에서 유도한 것이다.

## 3. 인프라 AC 의 네 종류 — 실측

| 종류 | 티켓의 예 | 검증 | 증거 인공물 |
|---|---|---|---|
| **형상**(적용 전) | #78 "필수 env 전부가 GitOps 선언에서 파생(수동 주입 0)" · #79 "Google OAuth 배선이 배포에 없다" · #80 "Corefile 이 git 선언으로 관리된다" | 렌더 결과(`kustomize build` · `terraform plan`)에 대한 단언 | 저장소 단언(kubeconform · conftest · `yq` · `terraform test` plan) — **가능**하나 있어야 하는 것은 아니다. 없으면 diff 자체 |
| **수렴**(적용 직후) | #89 `kubectl get gateway … PROGRAMMED=True` · `dig obs.mg` → VIP · "ArgoCD Synced/Healthy" · #99 `chronyc sources` 대상이 CP | 명령 한 번 | 티켓 코멘트의 **명령 + 출력** — 1회 실측. 이 종류에는 그것밖에 없다 |
| **지속**(창) | #100 "1주 관측 피크 80% 이하 · restart 0" · #101 "remote-write 거부 없음 · 새 트레이스가 계속 잡힌다" · #81 "사건 구간에 알림 조건 성립" | 창이 끝나야 닫힌다 | **알림 규칙 이름** + 창 끝의 재확인(날짜). 1회 실측은 증거가 아니다 |
| **절차** | #79 "롤백 지점 확보" · #101 "완료 코멘트에 메트릭 이름을 남긴다" · #80 "선행 확인: …" | — | AC 가 아니다. Technical Notes · Requirements 의 것 |

애플리케이션 티켓은 첫째 한 종류(동작)만 있어야 한다. #109 의 AC-3 은 절차였고, AC-4(`obs-doctor.py` 가 exit 1)는 AC-1 의 증상을 경계 층에서 다시 적은 것 — 틀리진 않지만 새 테스트가 나오지 않는다.

## 4. 결정

1. **AC 는 동작 또는 상태다 — 절차는 AC 가 아니다.** 롤백 지점 · 기록 의무 · 선행 조사 · 테스트의 자리와 형태는 Technical Notes · Requirements 로. 강제 지점(러너 · 메타테스트 · tdd-loop)이 말하는 것을 AC 에 옮겨 적지 않는다.
2. **인프라 AC 는 행마다 종류를 박는다** — `형상` · `수렴` · `지속(창)`. 지속 행은 창과 지키는 알림 규칙을 함께("1주, `AlloyMemoryHigh`").
3. **§7 Q1 · Q2 의 답** — 소유하고 싶은 것은 셋 다이고, 1회 실측은 **수렴에서만** 증거다. 지속은 알림 규칙으로, 형상은 저장소 단언이 있으면 그것으로.
4. **TDD 판정 · 대조표 근거는 손대지 않는다.** `ticket-start` 의 기준 한 문장이 형상 단언 스위트 · GPL 스크립트(`smoke_test.py`)를 이미 대상으로 판정하고, 대조표의 근거는 AC 행이 종류를 말하면 그 행이 시킨다 — 하네스에 규칙을 더하면 템플릿의 사본이 된다.

## 5. 하네스 델타

- docs-tickets `ticket/templates/bug.md` · `task.md` — AC 주석에 결정 1 · 2. ticket-engineer 델타는 없다(결정 4).

## 6. 미결

- 지속 행의 창이 끝나기 전에 티켓을 닫나 — 지금은 사람이 정한다. 알림 규칙이 있으면 창 전에 닫아도 규칙이 지킨다는 논리가 서지만 합의 전이다.
- 형상 단언 스위트를 jyoliar-k8s 에 세우나(kubeconform · conftest) — 비용 계산은 사람의 것(`260910_1900` §4).
- 이 구분이 ADR 감인가 — 테스트 정책 ADR(`260930_1524` §5)이 답할 질문에 "인프라 AC 의 종류와 증거" 를 더한다.
