---
type: discussion
kind: deliberation
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest]
status: active
ref-adrs: []
related: [261019_1623_obs-toolkit-test-quality.md]
resumes-after: [ops-workflow ② 인터페이스 · 시그니처 개선 Task, ops-workflow ③ 테스트 리팩토링 Task]
---

# pytest 테스트케이스 그룹화 — 묶음 · setup · teardown 을 어떤 장치로 표현하나

## 1. 문제

obs-toolkit 의 contracts 테스트는 전부 모듈 수준 함수다.
관련 테스트를 묶는 장치는 `# ── exemplars_of ──` 꼴 구분선 주석과 함수명 prefix 뿐이고, 둘 다 pytest 가 모른다.
그래서 세 장면에서 아프다.
실패를 읽을 때 — pytest 출력에 함수명만 찍혀 어느 묶음의 어느 케이스인지 이름을 해독해야 한다.
PR 을 검수할 때 — 101 함수짜리 파일에서 같은 약속의 변주를 함수명으로만 가려 읽는다.
테스트를 쓸 때 — 묶음이 공유하는 Given 을 테스트마다 다시 만든다.
잃는 것은 검수 시간과 중복 Given 이다.

Go 의 `t.Run` · JS 의 `describe` 가 주는 것 중 빠졌다고 느끼는 것은 셋이다 — 묶음 단위 setup · 이름의 계층 · 묶음만 골라 실행.
출발의 전제는 "pytest 에는 그런 기능이 없다" 였다.
실측은 전제를 고쳤다 — pytest 는 테스트 클래스로 셋을 다 주고, 그 위에 플러그인이 있다.
문제는 기능의 부재가 아니라 어느 장치를 고를 것인가와, 그것을 지금 정할 수 있는가다.

이 논의는 2026-10-22 에 **보류**됐다.
부모 논의가 정한 ② 인터페이스 · 시그니처 개선과 ③ 테스트 리팩토링이 아직 앞에 있고, 둘이 테스트의 경계와 Given 의 모양을 바꾼다.
그 위에서 묶음을 정해야 두 번 옮기지 않는다.
열린 축의 옵션은 재개 때 조사와 함께 다시 벌린다.

## 2. 실측

코드는 `workspace/ref/obs-toolkit`, HEAD `4e5bad7`(2026-10-21) 기준이다.

**현재의 묶음 장치**

- 테스트 클래스 0 개. `tests/` 의 클래스 5 개는 전부 대역 · 헬퍼(`FakeTransport` · `FakeLoki` · `LocalServer` …)다.
- 묶음은 구분선 주석이다 — `tests/contracts/test_traces.py` 101 함수 · 1,378 줄에 주석 17 개. 파일별 함수 수는 cli 39 · core 47 · logs 58 · metrics 57 · traces 101.
- 묶음 공통 Given 은 모듈 헬퍼로 푼다 — `test_traces.py` 에 `_sm` · `_th` · `_eq` · `_exemplar_routes` 류 약 30 개. 같은 두 줄(`sample = [_sm(…)]` · `th = {Endpoint(…): _th(…)}`)이 테스트마다 반복된다(`test_traces.py:361-420`).
- contracts 의 fixture 는 4 개뿐이다(`test_core.py` 의 로컬 서버 3 · `test_cli_main.py` 의 `cli_env` 1). 마커 · `pytestmark` 는 0 이다.
- `.claude/rules/python-tests.md` 는 티어와 여섯 규칙만 말하고, 파일 안의 묶음에 대해 침묵한다. 메타테스트(`tests/infra/test_conventions.py`)도 주석 묶음을 보지 않는다.

**흐트러짐 — 주석 묶음이 지켜지는가**

- contracts 336 함수 중 주석 묶음이 없는 것 18(`test_config.py` 11 · `test_cli_main.py` 4 · `test_get_only.py` 2 · `test_fixtures.py` 1) — 작은 파일이라 묶음을 두지 않은 쪽이다.
- 묶음 이름과 함수명이 기계적으로 어긋나는 것 62. 대부분은 이름 변형이다(`thresholds_of` 아래 `test_thresholds_*`). 다른 주제가 한 묶음에 든 실례는 소수다 — `spill` 아래 `prune` 둘(`test_core.py`) · `trace 의 오류 원인` 아래 `error_reason` 둘(`test_cli.py`).
- 사람은 흐트러짐을 겪은 기억이 없다. 실측도 "주석은 대체로 지켜진다" 쪽이다 — 흐트러짐은 이 논의의 비용이 아니다.

**pytest 가 주는 것 — 플러그인 없이**

- 클래스 — `class TestExemplarsOf:` 아래 `def test_…(self)`. nodeid 가 `파일::클래스::함수` 가 되어 실패 보고 · `-v` 에 묶음이 찍히고, `-k TestExemplarsOf` 로 묶음만 돈다. 클래스 안에 클래스를 둘 수 있다.
- 묶음 setup — 클래스 안의 `@pytest.fixture`(scope 는 function 또는 class) 또는 `setup_method` / `teardown_method`. `describe` 의 `beforeEach` 에 가장 가까운 것은 클래스 안 function 스코프 fixture 다.
- 구조와 무관하게 남는 것 — 메타테스트의 `_owner` 가 최상위 함수만 본다(`test_conventions.py:46`). 클래스 메서드가 되면 위반의 키가 파일 단위로 뭉개진다. 묶음 장치를 바꾸면 메타테스트도 같이 바뀐다.

**부모 논의와의 관계**

- 부모 `261019_1623` 3-1 이 테스트가 부르는 층을 다시 정했고, ③ 이 조립기 직접 호출 34 곳을 연산 층으로 올리고 중복 정의를 지운다. 묶음의 단위(어느 함수의 약속들인가)는 그 재배치 뒤에 안정된다.
- ② 가 `*_main` 주입구를 만들면 `monkeypatch.setattr(cli, …)` 17 곳이 사라진다. 그 자리의 Given 모양이 바뀌므로 묶음 setup 의 후보도 바뀐다.

## 3. 인터뷰에서 닫힌 축

### 3-1. 범위 — 그룹화 · setup · teardown 만, 시나리오는 그대로

**선택: 별개 Task 로, 각 테스트 파일의 내부 구조만 바꾼다.** 단언 · 테스트의 추가 · 제거 없이 기존 시나리오를 그대로 둔다. 약속 누락 · 인터페이스 개선과 섞지 않는다. (인터뷰, 2026-10-22)

<details><summary>버린 안</summary>

- ③ 테스트 리팩토링 Task 안에서 함께 — ③ 은 경계 재배치 · 중복 제거가 목적이라 diff 가 이미 크고, 묶음까지 섞이면 검수가 두 종류의 변경을 한 diff 에서 읽는다.
- 묶으며 중복 케이스도 정리 — 그것은 ③ 의 일이다. 시나리오를 건드리면 mutation 짝의 전 · 후 비교가 흐려진다.

</details>

### 3-2. 대상 티어 — contracts 만

**선택: contracts 티어에만 적용한다.** format 은 파일당 최대 15 함수 · 스냅샷 비교라 묶음이 필요 없고, infra 는 하네스 자체라 모양이 다르다. (인터뷰, 2026-10-22)

<details><summary>버린 안</summary>

- 세 티어 전부 — 규약이 한 줄 더 단순해지지만, 작은 파일에 묶음을 강제하면 묶음 하나짜리 클래스가 생긴다.

</details>

### 3-3. 시점 — ② · ③ 완료 뒤

**선택: ② 인터페이스 · 시그니처 개선과 ③ 테스트 리팩토링이 끝난 뒤 도입을 다시 고려한다.** 지금은 방향이 명확하지 않다 — 둘이 테스트의 경계와 Given 을 바꾸므로 그 위에서 묶음을 정해야 한 번에 옮긴다. (인터뷰, 2026-10-22)

<details><summary>버린 안</summary>

- ③ 의 선행으로 — 묶음을 먼저 입히면 ③ 이 재배치하며 묶음을 다시 짠다. 두 번 옮긴다.
- ③ 과 동시에 — 3-1 에서 버렸다.

</details>

### 3-4. 산출물의 모양 — 코드와 pytest 결과 양쪽에서 묶음이 보인다

**선택: 시각적으로(파일 안에서), 그리고 테스트 결과에서도 명시적으로 묶인 테스트케이스.** 가독성과 작성 편의가 목표다. 외부 라이브러리 도입도 검토 대상이다. (인터뷰, 2026-10-22)

주석 묶음은 이 기준을 못 채운다 — 결과에 안 나온다.
그래서 "안 한다" 는 현상 유지가 아니라 기준을 접는 것이다.

<details><summary>버린 안</summary>

- 파일 안의 시각적 묶음만 — 지금의 주석이 이미 그것이고, 실패를 읽을 때의 증상이 남는다.
- 표준 pytest 만 — 플러그인을 조사 없이 배제할 이유가 없다. 비용(의존성 · pyright strict · 유지)은 조사가 잰다.

</details>

## 4. 열린 축 — 논의

재개 때 조사 문서(`kind: survey`)와 함께 옵션을 다시 벌린다.
아래는 2026-10-22 시점의 밑그림이고 판정은 없다.
플러그인에 대한 서술은 조사 전이라 출처가 없다 — 조사 문서가 채운다.

### 4-1. 묶음 장치

실측 — 클래스는 표준이고 세 요구(setup · 이름 계층 · 선택 실행)를 다 준다. 메타테스트의 `_owner` 가 최상위 함수만 보므로 어느 장치든 메타테스트가 함께 바뀐다.

- A. 테스트 클래스 — 의존성 0, pyright 에 투명, nodeid 에 묶음이 찍힌다 / 메서드마다 `self` 가 붙고, 묶음 이름이 함수명이 아니라 클래스명으로 가므로 기존 prefix 이름이 중복된다(`TestExemplarsOf.test_exemplars_of_…`). 중첩 클래스는 되지만 들여쓰기가 깊어진다.
- B. `pytest-describe` — `describe_exemplars_of()` 안의 중첩 함수. JS 의 `describe` 와 가장 가까운 모양 / 의존성 추가. 중첩 함수가 pyright strict · 메타테스트 AST 훑기 · 기존 여섯 규칙(docstring 등)과 어떻게 맞물리는지는 조사 뒤.
- C. `pytest-subtests` — 한 테스트 안의 `with subtests.test(msg=…)`. Go 의 `t.Run` 격 / 묶음이 아니라 한 테스트의 하위 케이스다. "한 테스트 = 한 주장" 규칙과 충돌할 수 있고, parametrize 가 이미 같은 자리를 맡는다.
- D. 주석 유지 — 비용 0 / 3-4 의 기준을 접는 것이다.

### 4-2. 묶음 setup 의 모양

4-1 에 묶여 있다 — 장치가 setup 의 문법을 정한다.
실측 — 지금의 공유 Given 은 모듈 헬퍼 함수고, 테스트마다 호출한다. 클래스로 가면 클래스 안 fixture 가, describe 로 가면 중첩 fixture 가 후보다.
어느 쪽이든 "묶음 setup 이 Given 을 숨긴다" 와 "Given 이 개념을 이름 부른다"(부모 3-1 의 실측) 사이의 긴장이 있다 — 공통 Given 을 setup 으로 올리면 테스트 본문에서 임계값이 사라진다.

### 4-3. 규약 · 메타테스트로 강제하나

부모 3-4 와 같은 물음이다 — 기계 판정 가능한 것은 규칙으로.
후보 — "contracts 의 `test_*` 는 묶음 밖에 두지 않는다" · "묶음 이름은 부르는 함수명이다".
강제하지 않으면 다음 tdd-loop 가 함수를 모듈 수준에 다시 붙인다(CLAUDE.md §8).

## 5. 반대편 — 이 설계가 틀리는 조건

- ③ 이 중복을 지우고 나면 파일이 작아져 묶음이 필요 없어질 수 있다. 그때는 D 가 맞고 이 논의는 `rejected` 다.
- 묶음 setup 으로 Given 을 올리면 부모 3-1 이 지키려 한 "Given 이 개념을 이름 부른다" 가 깨진다. 가독성을 위해 묶었는데 가독성을 잃는 길이다.
- 클래스 · describe 로 가면 nodeid 가 길어져 스냅샷 파일명 규칙(`request.node.name`)에 닿을 수 있다 — contracts 만이라 지금은 무관하지만 3-2 를 넓히면 문제다.
- 플러그인 하나가 pyright strict 에서 stub 없이 오면 그 비용이 얻는 가독성보다 클 수 있다.

## 6. 버린 것

- **"pytest 에는 그룹화가 없다" 는 전제** — 클래스가 있다. 문제는 부재가 아니라 선택이다.
- **지금 정한다** — ② · ③ 이 경계와 Given 을 바꾸는 동안 묶음을 정하면 두 번 옮긴다(3-3).

## 7. 임계선 — ADR 감인가

ADR 은 없다.
테스트 파일의 내부 구조 · 규약 한 절 · 메타테스트 규칙 하나는 되돌리는 데 한 시간대다(CLAUDE.md §4②).
플러그인 도입도 의존성 하나이고 테스트 전용이라 같다.

## 8. 다음

이 논의는 **② · ③ Task 가 close 된 뒤 재개**한다.
그때까지 `active` 다.

재개하면 —

1. 조사 문서(`kind: survey`) — `pytest-describe` · `pytest-subtests` 와 클래스의 비교. 출처 · 조사일 · pyright strict 와 메타테스트와의 맞물림.
2. 4-1 → 4-2 → 4-3 순으로 옵션을 다시 벌리고 채팅으로 판정한다. ③ 뒤의 파일 크기와 Given 모양을 다시 실측한다.
3. 판정이 나면 Task 초안 하나 — target 은 obs-toolkit, 부모는 Feature #126, 선행은 ③. 동작 AC 없음(TDD 비대상). 검사 행은 4-3 의 규칙이 정한다.
