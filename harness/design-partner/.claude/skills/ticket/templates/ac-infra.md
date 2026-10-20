<!-- AC 조각 — 인프라(IaC · GitOps) 저장소. task.md · bug.md 의 "## Acceptance Criteria" 주석 아래에 이 파일의 내용을 붙이고,
     이 머리 주석은 지운다.
     약속은 상태다 — 선언이 X 이고, 실 시스템이 X 로 수렴하고, X 에 머문다. 행마다 "어느 시점의 상태인가" 로 그룹을 고른다.
     빈 그룹은 "없음" — 그룹을 지우지 않는다("지속: 없음" 은 창 관측이 필요 없다는 판단이다).
     번호는 그룹을 넘어 이어 붙인다(AC-1 · AC-2 …) — 집행자가 그 번호로 행을 가리킨다.
     절차(롤백 지점 · 기록 의무 · 선행 조사)는 어느 그룹에도 들어가지 않는다 — Technical Notes · Requirements(Bug 는 Context)에.
     GPL 로 쓴 스크립트(smoke_test.py 류)의 동작을 약속하는 행이 있으면 ac-app.md 의 "### 동작" 그룹을 가져와 더한다. -->

### 형상

<!-- 적용 전 — 선언(렌더 결과: kustomize build · terraform plan)에 대한 단언. 증거는 저장소 단언(kubeconform · conftest ·
     terraform test plan)이 있으면 그것, 없으면 diff 자체. -->

- [ ]

### 수렴

<!-- 적용 직후 — 실 시스템이 선언대로인가(PROGRAMMED=True · Synced/Healthy · dig 결과). 증거는 명령 한 번 + 출력 — 완료 코멘트에. -->

- [ ]

### 지속

<!-- 적용 뒤 창 — 머무는가. 창과 지키는 알림 규칙을 함께 적는다("1주 · AlloyMemoryHigh"). 1회 실측은 증거가 아니다 —
     창 끝의 재확인(날짜)이다. -->

- [ ]
