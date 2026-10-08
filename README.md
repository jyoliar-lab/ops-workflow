# ops-workflow

사이드 프로젝트·홈랩 운영의 **컨트롤 플레인**(GitHub Issues·Projects)과 **지식 플레인**(`docs/`)을 담는 저장소. 규약은 [`CLAUDE.md`](CLAUDE.md)에 있다 — 이 파일은 사람을 위한 **하네스 구조 안내**이고, agent는 읽지 않는다.

아래 경로는 전부 **저장소 루트 기준**이다.

## 하네스 — 역할별 작업 디렉터리

agent는 **`harness/<역할>/`에서 세션을 연다.** Claude Code는 cwd와 그 상위의 `CLAUDE.md`를 전부 읽고, `.claude/skills/`·`.claude/agents/`·`.claude/rules/`는 cwd에서 저장소 루트까지 올라가며 읽는다. 반면 `.claude/settings.json`은 **cwd의 것만** 읽고, `.claude/settings.local.json`은 **git 루트의 것**을 읽는다 (2026-10-08 실측).

```
ops-workflow/
├── CLAUDE.md                       규약 — 모든 하네스가 읽는다
├── .claude/
│   ├── rules/                      규약의 일부 (모든 하네스)
│   ├── skills/                     공통 스킬: adr(저작) · context-scout · _lib
│   ├── agents/                     공통 서브에이전트: context-scout-runner
│   ├── hooks/                      hook 본체 — 여기 한 곳에만 둔다
│   ├── scripts/ · commands/        build-index.py · /docs-index (루트 세션용)
│   ├── settings.json               루트 세션(유지보수)용 hook 등록·권한
│   └── settings.local.json         PC별 env(KUBECONFIG 등)·권한 승인 — 모든 하네스가 읽는다
├── docs/ · tmp/ · workspace/       루트에 하나. 하네스 밑에 만들지 않는다
└── harness/
    ├── design-partner/
    │   ├── CLAUDE.md               역할 프롬프트 — 규약 다음에 붙는다
    │   └── .claude/
    │       ├── settings.json       hook 등록 4종 · 티켓 스크립트 권한 · obs-toolkit 플러그인
    │       └── skills/             ticket · discussion · digest
    └── adr-judge/
        ├── CLAUDE.md
        └── .claude/
            ├── settings.json       hook 등록 3종(refresh-refs 제외) · accept/supersede 권한
            └── skills/             adr-accept
```

| 하네스 | 하는 일 | 전용 스킬 | 티켓 |
|---|---|---|---|
| **design-partner** | 발산 · `proposed` ADR 초안 · 쪼갬 · 티켓 발행. 코드를 읽는다(`workspace/ref`) | ticket · discussion · digest | write |
| **adr-judge** | accept 심판 · supersede · ADR 간 충돌·정합 · `subjects` 어휘 | adr-accept | read only |

### 세션 열기

```bash
cd harness/design-partner && claude     # 발산·초안·티켓
cd harness/adr-judge && claude          # 심판·supersede
claude                                  # 루트: 하네스 유지보수 · /docs-index
```

`/context`로 로드된 `CLAUDE.md` 둘(루트 + 하네스)과 스킬 목록을 확인할 수 있다. adr-judge에서는 `ticket`·`digest`가 보이지 않아야 정상이다.

### 경로와 경계

- `$CLAUDE_PROJECT_DIR`은 **세션을 연 디렉터리**(하네스 cwd)다 — 저장소 루트가 아니다. hook과 스크립트는 `git rev-parse --show-toplevel`로 루트를 역산한다(`.claude/hooks/*`, 각 `scripts/_bootstrap.py`).
- 쓰기 경계(`guard-write.py`)는 git 루트다. `docs/_index/`·`workspace/`·저장소 밖은 거부, `gh issue close`는 거부, `git commit`·`push`는 사람에게 묻는다.
- 스킬 스크립트는 `session-path.sh`가 PATH에 올린다 — 루트 `.claude/skills/**/scripts` + 해당 하네스의 `.claude/skills/**/scripts` + `.claude/scripts` + `.claude/hooks`.

### 역할 추가

1. `harness/<역할>/CLAUDE.md`에 역할 프롬프트를 쓴다.
2. `harness/<역할>/.claude/settings.json`을 만든다 — 기존 하네스의 hook 등록 블록을 복사하고 권한을 역할에 맞게 고른다.
3. 전용 스킬은 `harness/<역할>/.claude/skills/`에, 공통으로 쓸 것은 루트 `.claude/skills/`로 올린다.
4. 스크립트가 `_lib`를 쓰면 `scripts/_bootstrap.py`를 복사하고 `import _bootstrap`으로 시작한다.

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
