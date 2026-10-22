---
type: discussion
kind: survey
goal: obs-toolkit-test-quality
topic: ai-agent
subjects: [obs-toolkit, pytest, mutmut]
status: done
ref-adrs: []
related: [261019_1623_obs-toolkit-test-quality.md, 261019_1640_mutation-testing-tools-survey.md, 261020_1303_coverage-vs-mutation-testing-survey.md]
---

# mutation testing — 절차 · 용어 · 결과 해석, 그리고 obs-toolkit 적용 — 조사 (2026-10-21)

## 질문

obs-toolkit 테스트 품질 논의(`261019_1623`)는 mutation 도입을 별도 Task 로 내기로 했다(2026-10-21 채팅 — 커버리지 Task 와도 분리).
그 Task 를 쓰려면 "무엇을 어떤 순서로 하고, 나온 숫자와 목록을 어떻게 읽나" 가 서 있어야 한다.
앞선 조사 `261019_1640` 은 개념 · 도구 생태계 · 비용을 다뤘고 도구로 mutmut 을 골랐다.
이 문서는 그 뒤를 잇는다 — **mutmut 3.8 의 실제 절차와 어휘**, **결과의 해석법**, 그리고 **obs-toolkit 에 그대로 걸었을 때 무엇이 일어나는가**(스크래치 사본에서 실제로 돌렸다).
`workspace/ref/` 는 읽기 전용이라 실행은 사본에서 했고, 참조 저장소에는 아무것도 쓰지 않았다.

출처 표기 — mutmut 소스는 GitHub `boxed/mutmut` 의 `main` 브랜치(2026-10-21 조회)이고, 파일 경로는 `src/mutmut/` 기준이다.
공식 문서는 https://mutmut.readthedocs.io/en/latest/ (2026-10-21 조회).
obs-toolkit 은 `workspace/ref/obs-toolkit` HEAD `99dd35a` 다.

## 조사

### 1. 용어 — 한 표

일반 용어(mutant · killed · survived · 동치 mutant · mutation score · 두 가정)의 1차 출처는 `261019_1640` §1 에 있다.
여기서는 mutmut 이 실제로 쓰는 어휘를 보탠다.

| 용어 | 뜻 | 출처 |
|---|---|---|
| **mutant** | 원본 함수에 변이 하나를 넣은 복제 함수. mutmut 은 소스를 고치지 않고 **함수마다 변이 버전을 같은 파일 안에 함께 생성**한다 | `ARCHITECTURE.rst` "The mutated files contains the original code and the mutants" |
| **mutant 이름** | `<모듈>.x_<함수>__mutmut_<n>` — 메서드는 `x<ǁ><클래스><ǁ><메서드>__mutmut_<n>`. 예: `obs.traces.xǁ_CrispWalkǁvisit__mutmut_12`, `obs.core.x_parse_time__mutmut_3` | `mutation/trampoline_templates.py` `mangle_function_name` · `utils/format_utils.py` `mangled_name_from_mutant_name` |
| **trampoline** | 생성된 파일에서 원래 이름의 함수는 **분기기**가 된다 — 활성 mutant 가 없으면 `_mutmut_orig` 를, 있으면 그 mutant 를 부른다. 활성 mutant 는 프로세스 상태와 `MUTANT_UNDER_TEST` 환경변수로 지정된다 | `ARCHITECTURE.rst` · `mutation/trampoline.py` `wrap_in_trampoline` · `get_mutant_under_test` |
| **mutation operator** | 변이의 종류. mutmut 3.8 의 목록은 §2-2 | `mutation/mutators.py` `mutation_operators` |
| **stats** | 테스트 → 함수 대응표. 테스트를 한 번 돌리며 어느 테스트가 어느 trampoline 을 지났는지(`tests_by_mangled_function_name`)와 테스트별 소요 시간(`duration_by_test`)을 기록한다. `mutants/mutmut-stats.json` 에 저장 | `ARCHITECTURE.rst` "Collecting tests and stats" · `stats.py` `save_stats` |
| **clean run** | 모든 mutant 를 끈 채 전체 테스트 실행. 통과해야 다음으로 간다 | `ARCHITECTURE.rst` "Running clean tests" |
| **forced fail** | 모든 trampoline 이 예외를 던지게 하고 테스트를 돌려 **최소 하나가 실패하는지** 확인한다 — 테스트가 정말 변이된 코드를 부르고 있다는 검증 | `ARCHITECTURE.rst` "Running forced fail test" · `__main__.py` `run_forced_fail_test` |
| **`.meta`** | mutant 별 판정(exit code)과 소요 시간. 변이 파일 옆에 `foo.py.meta` 로 저장되고, 다음 실행이 이것을 읽어 **이미 판정된 mutant 를 건너뛴다** | `ARCHITECTURE.rst` "Collecting mutation results" |
| **killed** | 그 mutant 를 켠 채 돌린 테스트 중 하나라도 실패했다. 변이가 잡혔다 | `stats.py` `status_by_exit_code` — pytest exit 1 · 3 |
| **survived** | 테스트가 전부 통과했다. 변이가 잡히지 않았다 — 읽을 거리의 본체 | 같은 곳 — exit 0 |
| **no tests** | stats 에서 이 함수를 지나는 테스트가 하나도 없었다. 테스트를 돌리지 않고 바로 판정한다 — **실행되지 않은 코드**의 표식이고, 커버리지의 "미실행" 과 같은 정보다 | `__main__.py` `_run` "if not tests: … = 33" · `stats.py` 33 · 5 |
| **timeout** | CPU 시간 상한을 넘겼다(무한 루프 · 폭주). 상한은 §2-1 ⑥ | `stats.py` 24 · -24 · 36 · 152 · 255 |
| **suspicious** | 예상 밖의 exit code — 테스트 실패도 통과도 아닌 종료 | `stats.py` 기본값(`defaultdict(lambda: "suspicious")`) · 35 |
| **skipped** | exit 34. 이 조사에서 발생 지점을 찾지 못했다(아래 "찾지 못한 것") | `stats.py` 34 |
| **caught by type check** | `type_check_command` 로 타입 검사기가 거른 mutant. mypy · pyrefly 만 지원 — **pyright 는 지원하지 않는다** | 문서 "Filter generated mutants with type checker" · `stats.py` 37 |
| **segfault** | 워커 프로세스가 죽었다(SIGSEGV · SIGKILL) | `stats.py` -11 · -9 |
| **not checked** | 아직 돌리지 않았다(중단 · 미실행) | `stats.py` None |
| **이모지 줄** | 진행 표시 `{판정 수}/{전체}  🎉 killed 🫥 no tests  ⏰ timeout  🤔 suspicious  🙁 survived  🔇 skipped  🧙 type check` | `stats.py` `print_stats` |

**점수.** mutmut 은 `results` 명령에서 백분율을 찍지 않는다 — 상태별 **개수**를 보인다.
CI 용 `export-cicd-stats` 는 `killed · survived · total · no_tests · skipped · suspicious · timeout …` 개수를 JSON 으로 쓴다(`__main__.py` `save_cicd_stats`).
점수를 계산한다면 분모를 무엇으로 할지가 선택이다 — `261019_1640` 의 정의(Jia & Harman)는 분모가 **비동치 mutant** 이고, 동치 판별은 결정불가능하므로 실무에서는 `killed / (total − no_tests)` 또는 `killed / total` 을 쓴다.
어느 쪽이든 **전 · 후 비교는 같은 식**이어야 한다.

### 2. 절차 — `mutmut run` 이 하는 일

#### 2-1. 여섯 단계

`ARCHITECTURE.rst` 와 `__main__.py` `_run` 이 말하는 순서다.

| 단계 | 하는 일 | 실패하면 |
|---|---|---|
| ① **Generating mutants** | `source_paths` 를 `mutants/` 로 복사하고 그 안의 `*.py` 를 libcst 로 변이한다. `also_copy` 와 기본 목록(`tests/` · `test/` · `setup.cfg` · `pyproject.toml` · lock 파일들 · 루트의 `test*.py`)도 복사한다. `sys.path` 앞에 `mutants/` 를 넣고 **원본 경로는 `sys.path` 에서 제거**한다 — 테스트가 원본을 import 할 수 없게 | `configuration.py` 기본 `also_copy` · `utils/file_utils.py` `setup_source_paths` |
| ② **Running stats** | 선택된 테스트 전부를 `MUTANT_UNDER_TEST=stats` 로 한 번 돌린다. pytest 플러그인이 테스트마다 지나간 trampoline 과 소요 시간을 기록한다. **어떤 mutant 에도 테스트가 대응되지 않으면 여기서 멈춘다.** 테스트가 하나라도 실패하면 "failed to collect stats" 로 exit 1 | `__main__.py` `run_stats_collection` · `runners/harness.py` `run_stats` |
| ③ **이전 결과 적재** | `.meta` 를 읽어 이미 판정된 mutant 를 표시한다. 소스가 바뀐 함수의 mutant 는 무효화된다(함수별 해시 · 호출 의존 추적, 3.7.0) | `HISTORY.rst` 3.7.0 |
| ④ **Running clean tests** | mutant 를 모두 끄고 테스트를 돌린다. 실패하면 "Failed to run clean test" 로 exit 1 | `__main__.py` `_run` |
| ⑤ **Running forced fail test** | 모든 trampoline 이 던지게 하고 돌린다. 하나도 실패하지 않으면 "Unable to force test failures" 로 exit 1 — 테스트가 변이 코드를 안 부르고 있다는 뜻 | `__main__.py` `run_forced_fail_test` |
| ⑥ **Running mutation testing** | mutant 마다 **그 함수를 지났던 테스트만** 골라 fork 한 워커에서 `pytest -x -q -p no:randomly` 로 돌린다. 예상 시간이 짧은 mutant 부터, `--max-children`(기본 `os.cpu_count()`) 개 병렬. 판정은 즉시 `.meta` 에 저장되므로 **중단해도 다음 `run` 이 이어서 한다** | `__main__.py` `_run` · `harness.py` `_pytest_args_regular_run` |

⑥ 의 **CPU 시간 상한**은 `ceil((그 mutant 의 테스트 예상 시간 + timeout_constant) × timeout_multiplier × 2)` 초다 — 기본 상수 1.0 · 배수 15.0.
넘기면 SIGXCPU 로 끝내고 timeout 으로 판정한다(`__main__.py` `_run` · `workers/timeout.py`).
문서는 이 두 값을 "unstable — minor 버전에서 바뀔 수 있다" 로 표시한다.

`-x` 가 걸려 있으므로 **첫 실패에서 멈춘다** — mutant 하나에 대해 "어느 테스트들이 죽였나" 는 남지 않고 "죽었다" 만 남는다.
`__main__.py` 의 TODO 가 "which tests killed mutants … Those that kill zero mutants are redundant!" 를 미래 기능으로 적어 두었다 — 3.8 에는 없다.

#### 2-2. 변이 연산자 — mutmut 3.8 이 만드는 것

`mutation/mutators.py` `mutation_operators` 의 전부다.
괄호는 obs-toolkit 소스의 해당 구문 수(AST 집계, 2026-10-21 — §5-1).

- **숫자 리터럴** `n → n + 1`(정수 · 실수 · 허수). (숫자 227)
- **문자열 리터럴** 세 가지 — `"x" → "XXxXX"` · 소문자화 · 대문자화. **삼중따옴표 문자열은 건너뛴다**("docs or other things that mutation is meaningless for"). 변이 결과가 원문과 같으면 만들지 않는다 — **한글 · 숫자 · 기호만의 문자열은 대소문자 변이가 생기지 않아 `XX` 하나만** 나온다. (문자열 1,217 — 그중 cli.py 가 615)
- **이름** `True ↔ False` · `deepcopy → copy`. (bool 68)
- **대입** `a = b → a = None` · `a = None → a = ""`. 어노테이션만 있는 `a: T` 는 건너뛴다.
- **복합 대입** `a += b → a = b` 와 연산자 교체(`+= ↔ -=` 등).
- **단항** `not x → x` · `~x → x`. (단항 76)
- **호출 인자** — 인자 하나를 `None` 으로 · 인자가 둘 이상이면 하나씩 제거. `dict(a=b)` 의 키워드에 `XX`. (키워드 인자 619)
- **문자열 메서드 교체** `lower ↔ upper` · `lstrip ↔ rstrip` · `find ↔ rfind` · `ljust ↔ rjust` · `index ↔ rindex` · `removeprefix ↔ removesuffix` · `partition ↔ rpartition` · 조건부 `split ↔ rsplit`.
- **람다** 본문을 `None` 으로(본문이 `None` 이면 `0`). (람다 25)
- **키워드** `is ↔ is not` · `in ↔ not in` · `break → return` · `continue → break`.
- **이항 · 비교 · 불리언 연산자** `+ ↔ -` · `* ↔ /` · `// → /` · `% → /` · `** → *` · 비트 연산 · `< ↔ <=` · `> ↔ >=` · `== ↔ !=` · `and ↔ or`. (이항 468 · 비교 209 · 불리언 79)
- **match** — case 하나씩 제거(둘 이상일 때).
- **삼항식** 조건에 `and False` · `or True` 를 붙여 양쪽 가지로 강제(3.8.0).

없는 것 — **return 문 삭제 · 조건문 삭제 · 함수 본문 비우기** 같은 문장 수준 변이는 없다.
`return x` 는 `x` 안의 연산자 · 리터럴이 변이될 뿐이다.
데코레이터 제거는 TODO 다.

#### 2-3. 건너뛰기

- `# pragma: no mutate` 한 줄 · `# pragma: no mutate block`(정의 · 복합문 전체) · `# pragma: no mutate start` / `end` 구간. 짝이 안 맞으면 `PragmaParseError`. (문서 "Skipping via code comments")
- `do_not_mutate_patterns` — 소스 줄에 대한 정규식 목록(예: `logger\.`). (문서 "Skipping via regex")
- `only_mutate` · `do_not_mutate` — 파일 glob.
- `mutate_only_covered_lines = true` — coverage.py 로 한 번 돌려 **실행된 줄만** 변이한다. `# pragma: no cover` 줄도 뺀다(3.8.0). 커버리지 측정이 별도 프로세스에서 돈다.

#### 2-4. 명령

| 명령 | 무엇 | 출처 |
|---|---|---|
| `mutmut run [패턴…]` | 전체 또는 와일드카드(`"obs.traces*"`)로 고른 mutant 만. 이름을 명시하면 이미 판정된 것도 다시 돌린다 | `__main__.py` `run` · 문서 "Wildcards" |
| `mutmut results [--all]` | mutant 마다 `이름: 상태` 한 줄. 기본은 **killed 를 뺀 것만** — 생존 · no tests · timeout · suspicious 목록이 곧 출력이다 | `__main__.py` `results` |
| `mutmut show <이름>` | 그 mutant 의 상태와 **원본 대비 diff** | `__main__.py` `show` |
| `mutmut browse [--show-killed]` | 터미널 UI. 모듈 → 함수 → mutant 로 내려가며 diff 를 본다. `r` 재실행 · `f` 함수 재검사 · `m` 모듈 재검사 | 문서 "Workflow" |
| `mutmut apply <이름>` | 변이를 **실제 소스에** 쓴다 — 그 상태에서 테스트를 써 보려고. 커밋돼 있어야 한다 | 문서 "You should REALLY have the file … committed" |
| `mutmut print-time-estimates [패턴…]` | mutant 마다 예상 시간(대응 테스트 시간 합)을 `<no tests>` 포함해 출력 — **돌리기 전에 비용을 본다** | `__main__.py` `print_time_estimates` |
| `mutmut tests-for-mutant <이름>` | 그 mutant 에 대응된 테스트 목록 | `__main__.py` `tests_for_mutant` |
| `mutmut export-cicd-stats` · `badge` | 상태별 개수 JSON · shields.io 배지 | `__main__.py` |

`python -m mutmut run` 이 아니라 **`mutmut run`** 으로 부른다 — 전자는 모듈이 재실행돼 경고를 낸다(`__main__.py` GH-466 주석).

#### 2-5. 설정 — `pyproject.toml` `[tool.mutmut]`

주요 키와 기본값(`configuration.py`).

| 키 | 기본 | 뜻 |
|---|---|---|
| `source_paths` | 추측(`src/` 등) | 변이할 디렉터리. 옛 이름 `paths_to_mutate` 는 deprecated |
| `pytest_add_cli_args_test_selection` | `[]`(pytest 가 `tests/` 를 찾는다) | 테스트 **선택** 인자 — 디렉터리 · `-k` · `--deselect`. stats · clean · forced fail 에 쓰이고, mutant 실행에는 대응 테스트 id 가 대신 들어간다. 옛 `tests_dir` 는 deprecated |
| `pytest_add_cli_args` | `[]` | 그 밖의 pytest 인자. 모든 실행에 붙는다 |
| `also_copy` | 위 기본 목록 | `mutants/` 로 더 복사할 경로 — **테스트가 경로로 읽는 데이터** |
| `max_stack_depth` | `-1`(무제한) | 테스트가 함수에 "대응된다" 고 칠 호출 깊이 상한(소스 안 프레임만 센다) |
| `timeout_constant` · `timeout_multiplier` | `1.0` · `15.0` | §2-1 ⑥. unstable |
| `process_isolation` | `fork` | 워커를 어디서 fork 하나. `forkserver` 는 pytest 를 main 프로세스에 안 들인다(3.8.0) |
| `use_setproctitle` | macOS `false` | macOS 에서 fork-safe 하지 않아 자동 비활성 |
| `debug` | `false` | pytest 출력 전부 보임 |

요구 조건 — **fork 가 되는 OS**(Windows 는 WSL), Python ≥ 3.10(PyPI `requires_python`), 의존성 `click` · `coverage` · `libcst` · `pytest` · `setproctitle` · `textual`(PyPI `requires_dist`, 2026-10-21 조회).
3.8.0 은 2026-09-12 릴리스이고 Python 3.15 까지 지원한다(`HISTORY.rst`).

### 3. 결과를 읽는 법

#### 3-1. 전 · 후 비교에서 보는 것

"테스트를 줄였는데 변별력이 안 떨어졌다" 의 증거는 **점수 한 쌍이 아니라 집합 한 쌍**이다.

1. **전제 — 같은 소스 · 같은 설정 · 빈 `mutants/`.** mutant 집합은 소스가 정하므로 소스가 같으면 `total` 이 같다. `total` 이 다르면 비교 자체가 성립하지 않는다 — 소스가 바뀐 것이다. 설정(선택 인자 · 타임아웃)이 바뀌어도 무효화된다(`config_fingerprint`, `HISTORY.rst` 3.7.0). 증분 재사용을 피하려면 `mutants/` 를 지우고 시작한다.
2. **`mutmut results` 의 비-killed 목록을 전 · 후로 diff 한다.** 전에 killed 였는데 후에 survived 가 된 mutant 가 **잃은 변별력**이고, 그 함수가 지워진 테스트의 자리다. 전에 survived 였고 후에도 survived 면 리팩토링과 무관한 원래의 구멍이다. 후에 새로 killed 가 된 것은 더해진 단언이다.
3. **no tests 의 증감**은 실행 범위의 증감이다 — 함수 단위의 커버리지다. 커버리지 Task 가 줄 단위로 같은 것을 더 곱게 잰다.
4. **점수**는 그 뒤에 한 줄로 적는 요약이다 — 식을 함께 적는다.

`-x` 때문에 "어느 테스트가 죽였나" 는 기록되지 않는다(§2-1).
그래서 전 · 후의 **생존 목록 diff** 가 유일하게 구체적인 비교다 — 기준선의 `mutants/` 디렉터리를 이름을 바꿔 보관해 둬야 후에 `show` 로 다시 볼 수 있다.

#### 3-2. 생존 mutant 한 건을 읽는 법

`mutmut show <이름>` 의 diff 를 보고 셋 중 하나로 분류한다.
Google 은 처음 드러낸 mutant 의 85% 가 비생산적이었다고 적었다(`261019_1640` §4) — **생존 = 결함이 아니다.**

| 분류 | 판별 | 다음 |
|---|---|---|
| **약속 누락** | 변이가 바꾼 동작이 사용자에게 보이는 약속인데 어느 테스트도 그 성질을 단언하지 않는다. 예 — 정렬 방향 `<` → `<=` 가 동률 처리를 바꾸는데 동률 케이스가 없다 | 경계 시나리오 후보. 테스트를 더할지는 사람이 정한다 — 더하면 범위 확장이다 |
| **동치 · 사실상 동치** | 변이해도 관찰 가능한 결과가 같다. 예 — 로그 문구 · 내부 상수의 `+1` 이 출력에 안 나타남 · `"XX…XX"` 가 docstring 아닌 설명 문자열 | 무시하거나 `# pragma: no mutate` · `do_not_mutate_patterns` 로 다음 실행에서 뺀다 |
| **비생산적** | 잡을 수는 있지만 잡으려면 **구현을 베끼는 테스트**를 써야 한다. 예 — 질의 문자열 전문 · 내부 호출 순서 | 두지 않는다. Google 의 "change-detector" 경고(`261019_1640` §6) |

**survived 가 아닌 상태의 뜻**

- **no tests 가 많은 모듈**은 변별력 문제가 아니라 실행 범위 문제다 — 그 함수는 어떤 테스트도 지나지 않는다. 커버리지 리포트의 빨간 줄과 같은 정보다.
- **timeout** 은 변이가 루프 조건을 바꿔 무한 루프가 된 경우가 대부분이다 — 소스의 문제가 아니라 그 변이가 죽어야 하는데 테스트가 끝나지 않은 것이다. 보통 killed 로 쳐도 된다(실행이 "다르게" 됐으므로)는 해석과, 분모에서 뺀다는 해석이 있다 — 식을 정해 적는다.
- **suspicious** 는 테스트 자체가 깨진 것(import 오류 · 설정 오류)이 흔하다 — 먼저 그 테스트를 `debug=true` 로 돌려 본다.

#### 3-3. 어디서 거짓 신호가 나나

- **스냅샷 갱신 모드.** obs-toolkit 의 format 티어는 `OBS_TEST_UPDATE=1` 이면 스냅샷을 **다시 쓰고 통과**한다. 그 환경변수가 켜진 채 mutmut 을 돌리면 렌더러의 모든 변이가 survived 로 나온다 — 측정 전에 반드시 끈다.
- **소스를 읽는 테스트.** 소스 파일을 AST 로 검사하는 테스트는 **변이된 사본**을 읽는다. 원본에서는 참이던 단언이 사본에서 거짓이 되어 stats 단계가 멈춘다(§5-2 에서 실제로 났다). 선택에서 뺀다.
- **flaky 테스트.** 결과가 무의미해진다(`261019_1640` §6). obs-toolkit 은 fake transport · replay 로 결정론적이다.
- **`-x`.** 한 mutant 에 대응된 테스트 중 첫 실패에서 멈추므로 빠르지만, 같은 mutant 를 여러 테스트가 잡는지는 모른다 — "중복 테스트" 는 mutation 으로 직접 보이지 않고, **지운 뒤 점수가 안 떨어지는 것**으로만 보인다.

### 4. 비용 — 무엇이 시간을 정하나

- mutant 수 × 그 mutant 에 대응된 테스트의 시간이다. **대응 테스트만** 돌리므로 함수 하나를 1,000개 테스트가 지나면 그 함수의 mutant 는 하나당 1,000개를 돈다.
- 워커는 fork 라 pytest import 비용은 한 번이지만, mutant 마다 `pytest.main` 이 새로 수집한다 — 테스트 수가 많을수록 mutant 당 고정비가 는다.
- `print-time-estimates` 가 돌리기 전에 mutant 별 예상 시간을 준다. `no tests` 는 비용 0 이다.
- 줄이는 손잡이 — `only_mutate` 로 모듈을 좁힌다 · 와일드카드로 함수를 고른다 · `mutate_only_covered_lines` · `do_not_mutate_patterns` 로 설명 문자열(argparse `help=`)을 뺀다.

### 5. obs-toolkit 에 대입 — 실측

#### 5-1. 소스가 낳는 mutant

mutmut 이 생성한 mutant 수(스크래치 사본, 2026-10-21).

| 모듈 | 비주석 줄 | trampoline(함수 · 메서드) | mutant |
|---|---|---|---|
| `obs/adapters/cli.py` | 1,006 | 59 | **3,391** |
| `obs/core.py` | 517 | 39 | 902 |
| `obs/logs.py` | 242 | 13 | 602 |
| `obs/metrics.py` | 365 | 24 | 731 |
| `obs/traces.py` | 517 | 36 | 1,299 |
| 합 | 2,651 | 171 | **6,925** |

cli.py 가 절반이다 — 문자열 615개(argparse `help=` · 서브커맨드 설명 · 렌더 문구)가 `XX` 변이를 낳고, 키워드 인자 275개가 `None` 치환 · 제거 변이를 낳는다.
삼중따옴표의 `*_DOC` 상수는 건너뛰어졌다.
한글 문구는 대소문자 변이가 생기지 않아 문자열당 하나다.

생성 자체는 수 초다.

#### 5-2. 그대로 걸면 멈추는 곳 — 테스트 둘

설정 `source_paths = ["obs"]` · `also_copy = ["fixtures", "bin", "skills"]` 로 첫 실행을 했더니 **② stats 단계에서 exit 1** 이 났다.
원인은 테스트 둘이고, 둘 다 obs 의 약속이 아니라 **저장소 모양**을 검사하는 테스트다.

- `tests/contracts/test_get_only.py::test_core_never_sets_http_method` — `obs/core.py` 를 AST 로 읽어 `urllib.request.Request(...)` 의 위치 인자가 하나뿐임을 단언한다. 변이된 사본에는 인자를 지운 mutant 함수가 **같은 파일 안에** 있으므로 `len(args) == 0` 인 호출이 생겨 거짓이 된다. 소스를 읽는 테스트는 mutant 사본과 양립하지 않는다.
- `tests/infra/test_plugin_skeleton.py::test_plugin_manifests` — `ROOT / ".claude-plugin" / plugin.json` 을 읽는다. `ROOT` 는 `tests/record.py` 기준 `parents[1]` 이라 사본에서는 `mutants/` 가 되고, `.claude-plugin/` 은 복사되지 않아 `FileNotFoundError`.

같은 이유로 **fixture 경로도 `also_copy` 가 필요하다** — `FIXTURES = ROOT / "fixtures"` 가 `mutants/fixtures` 를 가리키므로 `fixtures/` 를 복사하지 않으면 replay 테스트 전부가 깨진다. `bin/` 은 `test_plugin_skeleton` 이 shim 을 subprocess 로 띄우고, `skills/` 는 `test_get_only` 가 훑는다.

해결은 선택이다 — **contracts · format 두 티어만 고르고 소스 스캔 테스트 하나를 deselect 한다.**
infra 티어는 하네스(녹화기 · replay · 메타테스트 · 플러그인 골격) 검사라 obs 함수를 지나지 않고, 따라서 어떤 mutant 에도 대응되지 않는다 — 넣어도 stats · clean 에서만 돌고 변별력에는 0 이다.

```toml
[tool.mutmut]
source_paths = ["obs"]
also_copy = ["fixtures", "bin", "skills"]
pytest_add_cli_args_test_selection = [
  "tests/contracts", "tests/format",
  "--deselect", "tests/contracts/test_get_only.py::test_core_never_sets_http_method",
]
```

사본의 나머지 630개 테스트는 변이 사본 위에서 통과했다(원본 모드 · `OBS_TEST_UPDATE` 해제).

#### 5-3. 전체 실행 — 결과

§5-2 의 설정으로 스크래치 사본에서 `mutmut run` 을 끝까지 돌렸다(macOS · Python 3.14.2 · 워커 10 · 2026-10-21).
이것은 **지금 HEAD(`99dd35a`) 위의 수치**이지 리팩토링의 기준선이 아니다 — 기준선은 인터페이스 Task 가 머지된 소스 위에서 다시 잰다(`261019_1623` 4-1).

**시간.** 13:13:55 → 13:16:12, 전체 **2분 17초**.
그중 ⑥ mutation 단계가 약 115초(`60.44 mutations/second`), stats 의 CPU 시간 4.8초, 나머지는 생성 · clean · forced fail 이다.
비용이 걱정거리가 아니다 — 전 · 후 두 번은 물론, 모듈 단위로 여러 번 돌려도 된다.

**상태 분포.**

| 상태 | 수 |
|---|---|
| killed 🎉 | 5,922 |
| survived 🙁 | 985 |
| no tests 🫥 | 18 |
| timeout ⏰ · suspicious 🤔 · skipped 🔇 | 0 · 0 · 0 |
| 합 | 6,925 |

점수는 식에 따라 `killed / total` = 85.5 %, `killed / (total − no tests)` = 85.7 % 다.
timeout · suspicious 가 0 이라 식 선택이 결과를 거의 바꾸지 않는다 — 결정론적 스위트의 이점이다.

**모듈별.**

| 모듈 | mutant | killed | survived | no tests | 생존 비율 |
|---|---|---|---|---|---|
| `obs/adapters/cli.py` | 3,391 | 2,844 | 543 | 4 | 16.0 % |
| `obs/core.py` | 902 | 696 | 206 | 0 | 22.8 % |
| `obs/logs.py` | 602 | 544 | 58 | 0 | 9.6 % |
| `obs/metrics.py` | 731 | 672 | 59 | 0 | 8.1 % |
| `obs/traces.py` | 1,299 | 1,166 | 119 | 14 | 9.2 % |

환원 · 연산 모듈 셋(logs · metrics · traces)은 생존이 10 % 아래이고, 어댑터(cli)와 I/O 층(core)이 높다.
생존을 **함수별**로 세면 상위가 전부 진입점과 I/O 다 — `logs_main` 85 · `metrics_main` 74 · `traceql_run` 37 · `logql_main` 35 · `traceql_main` 33 · `traces_main` 30 · `core.spill` 29 · `core.doctor` 28 · `core._urllib_transport` 23 · `promql_run` 22 · `promql_main` 21 · `Client.get` 20.
`*_main` 여섯만 278개로 생존의 28 % 다 — argparse 정의부의 `help=` 문자열 · `default=` · `metavar=` 키워드 인자가 그 자리다.

**stats 가 말하는 것.** trampoline 171개 중 169개에 테스트가 대응됐고, 선택된 테스트 중 536개가 어느 함수든 지났다.
함수당 대응 테스트는 중앙값 16 · 최대 267 이다 — 최대는 모든 연산이 지나는 공통 함수이고, 그 함수의 mutant 하나가 267개 테스트를 돈다(그래도 전체가 2분이다).
**no tests 둘은 `cli._stderr` 와 `traces._clip`** 이다 — contracts · format 어느 테스트도 이 두 private 함수를 실행하지 않는다. 죽은 코드이거나 검사되지 않은 가지다.

**생존 표본 여섯 — §3-2 의 분류를 실제로 적용하면.**

| mutant | diff | 분류 | 읽기 |
|---|---|---|---|
| `obs.core.x_parse_time__mutmut_4` | `text.strip() in ("", "now")` → `("XXXX", "now")` | 약속 누락 | 빈 문자열이 "지금" 으로 읽힌다는 성질을 어느 테스트도 넣지 않는다. 경계 시나리오 후보 |
| `obs.traces.x_exemplars_of__mutmut_3` | `raise ObsError("k 는 1 이상…" % k)` → `ObsError(None)` | 비생산적 | 테스트는 예외의 **종류**만 단언한다. 문구를 단언하면 문구가 약속이 된다 — 두지 않는 것이 맞다 |
| `obs.adapters.cli.x_metrics_run__mutmut_2` | `now() if at is None else at` → 항상 `at` | 동치(테스트 관점) | 테스트는 언제나 `at` 을 주입한다 — `now()` 가지는 설계상 테스트 밖이다. `# pragma: no mutate` 후보 |
| `obs.adapters.cli.x_red_lines__mutmut_4` | `window_str(base) if base is not None else "?"` → 항상 `window_str(base)` | 동치 또는 누락 | `red` 의 기준선이 `None` 인 경로가 실제로 있나를 코드가 답한다 — 없으면 죽은 가지, 있으면 누락 |
| `obs.logs.x_parse_logs__mutmut_16` | matrix 결과의 `streams=[]` → `streams=None` | 동치에 가까움 | matrix 일 때 `streams` 를 읽는 호출자가 없다. 타입상은 거짓이지만 pyright 는 사본을 보지 않는다 |
| `obs.metrics.x_check_status__mutmut_8` | 오류 본문의 `"\n"` → `"⏎"` 치환 문자열 변이 | 사소 | 오류 본문에 개행이 든 응답을 만든 테스트가 없다. 약속이라기보다 표시다 |

여섯 중 **테스트를 더할 만한 것은 하나(`parse_time` 의 빈 문자열)** 이고, 나머지는 무시 · pragma · 코드 확인이다.
985개를 전부 이렇게 읽는 것은 일이 아니다 — 함수별로 묶어 `*_main` 의 argparse 생존을 `do_not_mutate_patterns`(`help=` · `metavar=`)로 먼저 걷어내면 읽을 양이 3분의 2 아래로 준다.

#### 5-4. 생존이 몰린 함수의 diff 분류 — 잡음인가, 구조인가, 누락인가

생존 상위 함수 11개의 mutant 를 diff 로 분류했다(2026-10-21, 스크래치 사본 · `mutmut show` 전수).
분류 기준 — 변이가 건드린 것이 argparse 문구(`help=` · `description=` · `metavar=`)인가, 호출 인자(`None` 치환 · 제거)인가, 문자열 리터럴인가, 삼항 조건인가, 비교 · 분기인가.

| 함수 | 생존 | argparse 문구 | 인자 None · 제거 | 문자열 | 삼항 · 분기 · 기타 |
|---|---|---|---|---|---|
| `cli.logs_main` | 85 | 41 | 35 | 8 | 1 |
| `cli.metrics_main` | 74 | 47 | 13 | 6 | 8 |
| `cli.traceql_run` | 37 | — | 10 | 13 | 14 |
| `cli.promql_run` | 22 | — | 5 | 8 | 9 |
| `core.spill` | 29 | — | 9 | 2 | 18 |
| `core.doctor` | 28 | — | 17 | 2 | 9 |
| `core._urllib_transport` | 23 | — | 12 | 4 | 7 |
| `core.Client.get` | 20 | — | 8 | 3 | 9 |
| `traces.critical_path_of` | 16 | — | 9 | 1 | 6 |
| `logs.around` | 15 | — | 4 | 4 | 7 |
| `core.load_config` | 15 | — | 6 | 6 | 3 |

읽으면 세 갈래다.

**갈래 ① 선언 — 비즈니스 코드가 아니다.** `*_main` 생존의 절반 남짓이 argparse 문구다.
이것은 CLI 의 선언이고 `*_main` 함수 본문 안에 배선(Args 조립 · Client 획득 · `finish`)과 섞여 있다.
그래서 예외를 걸려면 함수 안에 줄 단위 `# pragma: no mutate` 를 뿌려야 한다 — 선언과 배선이 한 함수에 있다는 신호다.
파서 구성을 별도 모듈로 떼면 예외는 `do_not_mutate` 의 파일 하나가 된다.

**갈래 ② 환경 획득 분기 — 구조다.** `now() if at is None else at`(`promql_run` · `metrics_run`) · `os.environ if env is None else env`(`doctor`) · `_client()` 가 같은 꼴이다 — 매개변수 기본값 `None` 이면 함수 안에서 환경을 읽는다.
변이가 그 `None` 가지를 끊어도 살아남는다 — 어떤 테스트도 그 가지를 실행하지 않는다.
`261019_1623` §2 의 왜곡 ①(Client 주입구 부재)과 같은 결함이다.
환경 획득을 `*_main` 한 곳으로 올리면 이 생존은 pragma 없이 사라진다.

**갈래 ③ 누락 — 잡음이 아니다.** 리팩토링으로 숨기면 안 되는 것들이다.

- `_urllib_transport` 의 `Request(url, headers=…)` 에서 `headers` 를 지운 mutant, `doctor` 의 `Client(token=token)` 에서 `token` 을 지운 mutant 가 살아남았다. **토큰 헤더가 실제로 나간다는 것을 contracts · format 어느 테스트도 단언하지 않는다** — 전송 층 테스트는 타임아웃 · 프록시만 본다.
- `traceql_run` · `promql_run` 의 요청 파라미터 키 `"q"` · `"start"` 를 `"XXqXX"` 로 바꿔도 살아남는다. `FakeTransport` 의 라우트 키가 `(backend, path)` 라 파라미터를 보지 않고, 테스트가 파라미터의 성질을 따로 단언하지 않는다. `261019_1623` 3-1 의 "성질은 보낸 요청의 파라미터에 단언한다" 가 비어 있는 자리다.
- `*_main` 의 Args 조립 — `getattr(a, "since", "1h")` · `default=DEFAULT_BASELINE` 의 기본값 변이가 전부 살아남는다. CLI 의 기본 창 · 기준선은 사용자 약속인데 main 테스트가 `*_run` 을 패치해 Args 만 보므로 기본값이 요청까지 흘러가는지 모른다. 주입구가 생기면 **검사 가능해지는** 것이지 사라지는 것이 아니다.
- `around` 의 `span <= 0` → `<= 1`(경계값 1 미검사) · `critical_path_of` 의 빈 트레이스 반환 필드 미단언 · `check_status(body, "metrics")` 의 백엔드 이름 `None`(문구에만 쓰임).
- `ObsError("문구")` → `ObsError(None)` · `"XX문구XX"` 류는 전 모듈에 고르게 있다. 문구는 약속이 아니라는 설계상 의도된 생존이다. 구조로 없애려면 예외 종류(하위 클래스 · 코드 필드)를 두는 설계 변경이고, `do_not_mutate_patterns` 의 `raise ObsError\(` 한 줄이 싼 길이다.

#### 5-5. 저장소 쪽 조건

- **pyright strict.** `[tool.pyright] include = ["obs", "tests", "skills"]` 라 `mutants/` 는 검사 밖이다. 변이 파일의 생성 줄에는 `# type: ignore # mutmut generated` 가 붙는다(`trampoline_templates.py`). `type_check_command` 는 mypy · pyrefly 만 받으므로 pyright 로 타입상 불가능한 mutant 를 미리 거르는 길은 없다 — 그런 mutant(인자 `None` 치환 등)는 대개 실행 중 `TypeError` 로 killed 가 된다.
- **의존성 0 의 원칙.** `pyproject` 의 `dependencies = []` 는 런타임의 것이고 mutmut 은 개발 도구다. CI 가 pytest · pyright 를 워크플로 안에서 핀하듯, mutmut 의 핀 자리는 `pyproject` 의 선택 의존 그룹 또는 README 의 설치 줄이다 — 어디든 **버전을 적는다**(3.8.0).
- **`.gitignore`.** `mutants/` 를 넣는다. 기준선 보관본(이름 바꾼 디렉터리)도 커밋하지 않는다 — 비교는 코멘트에 남는 목록으로 한다.
- **GitHub Actions 에는 넣지 않는다**(2026-10-21 판정). `mutmut run` 은 로컬에서, 결과는 `results` 출력과 요약 줄을 티켓 코멘트에.
- **macOS.** fork 지원 · `setproctitle` 자동 비활성. 이번 실측도 macOS 에서 했다.
- **Python 3.10 · 3.14 matrix.** mutmut 3.8 은 둘 다 지원한다. 측정은 한 버전으로 고정해 적는다 — 버전이 다르면 테스트 시간이 달라 타임아웃 판정이 흔들릴 수 있다.

### 조사에서 찾지 못한 것

- exit 34 `skipped` 가 어느 경로에서 기록되는지 — 읽은 파일(`__main__.py` · `harness.py` · `stats.py`) 안에는 발생 지점이 없다.
- "어느 테스트가 어느 mutant 를 죽였나" 를 남기는 기능 — 3.8 에 없다(TODO 로만 있다).
- mutmut 공식 문서의 결과 상태 정의 — 문서에는 없고 소스 `stats.py` 에만 있다.

## 논의 문서로 가져가는 것

- 절차는 여섯 단계이고 **②·④·⑤ 가 전제 검증**이다 — stats 에 테스트가 하나도 대응되지 않거나, clean 이 실패하거나, forced fail 이 실패하지 않으면 측정 자체가 무효다. Task 의 첫 코멘트는 이 셋이 통과했다는 로그여야 한다.
- obs-toolkit 은 설정 세 줄로 돈다 — 단, **티어 선택(contracts · format)과 소스 스캔 테스트 하나의 deselect, `fixtures/` 복사**가 없으면 stats 에서 멈춘다. 이것은 mutmut 의 제약이 아니라 "소스를 읽는 테스트" 와 "경로로 데이터를 읽는 테스트" 의 성질이다.
- 전체 실행은 **2분 17초**(6,925 mutant · 워커 10)다. 비용은 결정 요인이 아니다 — 모듈 단위 · 반복 실행이 다 된다.
- 지금 HEAD 의 결과는 killed 5,922 · survived 985 · no tests 18 · timeout 0 — 식에 따라 85.5 ~ 85.7 %. 환원 · 연산 모듈은 생존 10 % 아래, 어댑터 16 %, core 23 %.
- 생존의 28 % 가 `*_main` 여섯(argparse 정의부)이다. `do_not_mutate_patterns` 로 `help=` · `metavar=` 줄을 빼고 모듈별로 읽는 것이 맞다 — 그 생존은 약속 누락이 아니다.
- 생존 표본 여섯 중 테스트를 더할 것은 하나였다. 생존 목록은 "고칠 목록" 이 아니라 "읽고 분류할 목록" 이다 — Task 의 AC 에 "생존 0" 류를 두면 안 되는 이유다.
- `no tests` 둘(`cli._stderr` · `traces._clip`)은 어떤 테스트도 실행하지 않는 코드다 — 커버리지 Task 가 줄 단위로 같은 것을 보일 것이다.
- 전 · 후 비교의 단위는 점수가 아니라 **비-killed 목록의 diff** 다. `-x` 때문에 "누가 죽였나" 가 없으므로 기준선 `mutants/` 를 보관해야 후에 `show` 할 수 있다.
- `no tests` 는 함수 단위 커버리지다 — 커버리지 Task 와 겹치는 정보이고, 둘을 함께 읽으면 "실행 안 됨" 과 "실행됐으나 단언 없음" 이 갈린다(`261020_1303`).
- 생존은 세 갈래다 — 선언(argparse 문구 · `*_main` 생존의 절반) · 환경 획득 분기(`at` · `env` · `_client()` 의 `None` 기본값) · 누락. 앞의 둘은 구조로 답할 수 있고(선언 분리 · 환경 획득을 main 으로), 셋째는 테스트로만 답한다. 생존 목록을 "예외 처리할 목록" 으로 읽으면 셋째가 묻힌다 — 분류가 먼저다.
- 누락 중 먼저 볼 것은 **토큰 헤더** 다 — 헤더 · 토큰을 지운 mutant 가 살아남았다. 요청 파라미터 키 · CLI 기본값 · `around` 의 경계값 1 이 그 뒤다.
- pyright 로는 mutant 를 거르지 못한다. 점수 식(`killed / total` 인지 `no tests` 를 뺀 분모인지)은 Task 가 정해 적고, 전 · 후에 같은 식을 쓴다.
