# ops-workflow

사이드 프로젝트·홈랩 운영의 **컨트롤 플레인**(GitHub Issues·Projects)과 **지식 플레인**(`docs/`)을 담는 저장소. 규약은 [`CLAUDE.md`](CLAUDE.md)에 있다 — 이 파일은 사람을 위한 **하네스 구조 안내**이고, agent는 읽지 않는다.

아래 경로는 전부 **저장소 루트 기준**이다.

## 하네스 — 역할별 프롬프트와 스킬

agent 세션은 **항상 저장소 루트에서** 연다. 역할은 `--add-dir`로 덧붙인다 — 그래서 사람과 agent가 말하는 경로는 전부 루트 기준이고, `$CLAUDE_PROJECT_DIR`도 루트다.

```bash
cd ~/IdeaProjects/ops-workflow
claude --add-dir harness/design-partner     # 발산·초안·쪼갬·티켓 발행
claude --add-dir harness/adr-judge          # accept 심판·supersede·ADR 간 정합
claude                                      # 역할 없이: 하네스 유지보수 · /docs-index
```

Claude Code는 cwd의 `CLAUDE.md`·`.claude/*`에 더해, `--add-dir`로 덧붙인 디렉터리의 `.claude/skills/`·`.claude/agents/`를 읽는다. 그 디렉터리의 `CLAUDE.md`는 `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`일 때 읽는데, 이 플래그는 루트 `.claude/settings.json`의 `env`에 들어 있다 (2026-10-08 실측: 역할 CLAUDE.md와 전용 스킬이 로드되고, 다른 역할의 것은 보이지 않는다).

```
ops-workflow/
├── CLAUDE.md                       규약 — 모든 세션이 읽는다
├── .claude/
│   ├── rules/                      규약의 일부
│   ├── skills/                     공통 스킬: adr(저작) · context-scout · _lib
│   ├── agents/                     공통 서브에이전트: context-scout-runner
│   ├── hooks/                      hook 본체
│   ├── scripts/ · commands/        build-index.py · /docs-index
│   ├── settings.json               hook 등록 · 권한 · env 플래그 — 모든 세션 공통
│   └── settings.local.json         PC별 env(KUBECONFIG 등) · 권한 승인
├── docs/ · tmp/ · workspace/
└── harness/
    ├── design-partner/
    │   ├── CLAUDE.md               역할 프롬프트 — 규약 다음에 붙는다
    │   └── .claude/skills/         ticket · discussion · digest
    └── adr-judge/
        ├── CLAUDE.md
        └── .claude/skills/         adr-accept (accept · unaccept · supersede)
```

| 하네스 | 하는 일 | 전용 스킬 | 티켓 |
|---|---|---|---|
| **design-partner** | 발산 · `proposed` ADR 초안 · 쪼갬 · 티켓 발행. 코드를 읽는다(`workspace/ref`) | ticket · discussion · digest | write |
| **adr-judge** | accept 심판 · supersede · ADR 간 충돌·정합 · `subjects` 어휘 | adr-accept | read only |

`/context`로 로드된 `CLAUDE.md` 둘(루트 + 역할)과 스킬 목록을 확인할 수 있다. adr-judge에서는 `ticket`·`digest`가 보이지 않아야 정상이다.

### 경계와 PATH

- hook·권한은 루트 `.claude/settings.json` 하나다. 역할별 차이는 프롬프트와 스킬 가시성으로 낸다 — `refresh-refs`는 어느 역할에서도 돈다(ff-pull, 수 초).
- 쓰기 경계(`guard-write.py`)는 git 루트다. `docs/_index/`·`workspace/`·저장소 밖은 거부, `gh issue close`는 거부, `git commit`·`push`는 사람에게 묻는다.
- 스킬 스크립트는 `session-path.sh`가 PATH에 올린다 — 루트와 **모든** 하네스의 `.claude/skills/**/scripts` + `.claude/scripts` + `.claude/hooks`. hook은 어느 역할이 덧붙었는지 모르므로 전부 올린다. PATH는 경계가 아니다.
- hook·스크립트는 그래도 `git rev-parse --show-toplevel`로 루트를 역산한다 — 하위 디렉터리에서 열어도 깨지지 않게.

### 역할 추가

1. `harness/<역할>/CLAUDE.md`에 역할 프롬프트를 쓴다.
2. 전용 스킬은 `harness/<역할>/.claude/skills/`에, 공통으로 쓸 것은 루트 `.claude/skills/`로 올린다. 스크립트가 `_lib`를 쓰면 `scripts/_bootstrap.py`를 복사하고 `import _bootstrap`으로 시작한다.
3. 새 스크립트가 있으면 루트 `.claude/settings.json`의 권한에 더한다.
4. `claude --add-dir harness/<역할>`로 연다.

## 구조로 강제하는 것들

`CLAUDE.md` §8("규율이 아니라 구조")의 구현 목록. agent에게는 "막히면 그것이 규약"으로 충분하고, 무엇이 왜 막히는지는 여기에 있다.

| 지켜지는 것 | 강제하는 구조 |
|---|---|
| 이슈당 타입 하나 (ADR-0009) | GitHub Issue Types가 **단일 선택**이다 |
| 자율 agent의 지식 플레인 write 금지 | 자율 agent에 `docs/` write 권한이 **없다** (도구 수준) |
| 수동 close | 어느 스킬에도 close 기능이 **없고**, `guard-write.py`가 `gh issue close`를 거부한다 |
| `accepted` ADR 본문 동결 (ADR-0006) | `freeze-check.py`가 거부한다. `accept.py`·`supersede.py`는 frontmatter 두 필드만 건드린다 |
| 코드 저장소 read only | `guard-write.py`(PreToolUse)가 `workspace/` 이하와 저장소 밖 Write/Edit을 거부한다 |
| `_index/` 손 편집 금지 | `guard-write.py`가 `docs/_index/` 쓰기를 거부하고, `reindex-docs.py`(PostToolUse)가 `docs/**` 변경 뒤 재생성한다 |
| 무인 커밋 금지 | `guard-write.py`가 `git commit`·`git push`를 사람에게 묻는다 |

## 쓰기 권한과 자격증명

| | 컨트롤 플레인 (Issues) | 지식 플레인 (`docs/`) | 시스템·코드 |
|---|---|---|---|
| 자율 agent (진단 — ticket-engineer 등 다른 저장소) | write (티켓 생성·코멘트) | 불허 (도구 수준) | read only |
| 대화형 agent (design-partner · adr-judge) | design-partner write / adr-judge read | write + 사람 승인 게이트 | read only (hook 수준) |
| 사람 | write | write (최종 저자) | write |

**코드 읽기.** 코드 저장소는 `workspace/ref/<repo>`(gitignored)의 읽기 전용 로컬 클론으로 읽는다. 목록은 `.claude/ref-repos.txt`가 정의하고, design-partner 하네스의 SessionStart hook(`refresh-refs.py`)가 없으면 clone, 있으면 ff-pull로 최신화한다. 목록에 없는 저장소가 필요하면 파일에 URL을 추가하고 `refresh-refs.py`를 돌린다 — 손 clone 하지 않는다.

**홈랩 Kubernetes 읽기.** `KUBECONFIG`는 루트 `.claude/settings.local.json`의 `env`로 주입된다(모든 하네스가 읽는다). `kubectl`은 전용 ServiceAccount `system:serviceaccount:agents:ops-workflow-agent`로 동작하며, 권한은 클러스터 전역 읽기 전용이다. Secret 값 읽기와 모든 쓰기는 클러스터 RBAC가 거부한다 — hook이 아니라 서버 쪽 구조로 강제되는 경우다.

**진단 agent의 경계** (다른 저장소의 자율 agent — 참고)

- 한다: 증상 기록용 Bug 티켓 생성 · 저장소·시스템 read 조사 · 확인 내용을 코멘트로 축적
- 하지 않는다: 복구 · 문서 저작 · 티켓 close

**초안 인박스 `tmp/`** 는 untracked다. `tmp/staging/`은 하네스 자체의 마찰 로그, `tmp/github-issues/`는 이슈 본문 초안(`gh --body-file`로 게시). `.gitignore`에는 아직 `tmp/`가 없다 — 감사 패치 참조.
