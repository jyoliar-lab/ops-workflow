---
type: discussion
topic: ai-agent
subjects: [claude-code, claude-code-skills, ops-workflow-agent, ticket-engineer-agent]
status: active
ref-adrs: []
ticket: 90
---

# 두 하네스가 같은 코드를 갖는다 — 공유 방안

## 계기

#90 에서 `obs-query` 스킬(SKILL.md + 스크립트 4개)을 ops-workflow 와 ticket-engineer 에 **바이트 단위로 같게** 넣었다.
티켓이 "자리·이름·인터페이스가 둘이 같아야 한다"고 요구했고, 방법은 복사였다.
복사는 이번이 처음이 아니다 — 하네스가 둘이 된 뒤로 같은 것이 두 번 적혀 왔고, 그 정합은 사람의 눈과 steward 의 conformance 감사에 기대 왔다.
질문: **두 하네스(그리고 steward)가 스크립트를 공유하는 길은 무엇이고, 무엇은 공유하면 안 되는가.**

## 무엇이 겹치는가 — 실측 (2026-08-30)

세 층이다. 층마다 성격이 다르고, 답도 다르다.

| 층 | 대상 | 상태 | 성격 |
|---|---|---|---|
| **바이트 동일** | `.claude/skills/obs-query/**` (SKILL.md + `_obs`·`promql`·`logql`·`traceql`.py) | `diff -r` 동일 | 정책과 무관한 **메커니즘** — 어느 하네스가 불러도 같은 일을 한다 |
| | `.claude/rules/python-typehints.md` | ticket-engineer = steward. ops-workflow 에는 없다 | 코딩 규칙 — 하네스 무관 |
| **쌍둥이(emit ↔ parse)** | 티켓 본문 `### 저장소` 파서 — ops `ticket/scripts/repo_context.py`(emit+parse) ↔ TE `_lib/repos.py`(parse) | `parse_section` 과 정규식이 복제. 주석에 "쌍둥이 파서 — 표기가 바뀌면 함께 바뀐다. 정합은 steward 의 conformance 감사 대상" | **정책의 구현** — 표기는 ADR-0016 의 표현이다. 한쪽이 쓰고 다른 쪽이 읽으므로 어긋나면 착수·보고 도구가 티켓을 거부한다 |
| | `### 근거 ADR` 파서 — `adr_context.py` ↔ `_lib/adrs.py` | 같다 | 같다 (ADR 계층 게이트) |
| **같은 패턴·다른 경계** | `hooks/guard-write.py` | 헬퍼(`out_deny`·`allow`·`norm`·`under`)는 같고 `main` 의 경계만 다르다(ops: 저장소 안 · TE: `workspace/target`·`tmp/` · steward: 두 대상 repo) | 헬퍼는 메커니즘, `main` 은 **그 하네스의 정체성** |
| | `hooks/session-path.sh` | 한 줄 차이(ops 는 `.claude/scripts` 도 PATH 에) | 메커니즘 |
| | `hooks/refresh-refs.py` | 방향이 다르다 — ops 는 목록(`ref-repos.txt`)이 먼저, TE 는 티켓이 지목한 것만 | 겉만 닮았다. 공유 대상 아님 |

steward 도 같은 `guard-write` 패턴과 `python-typehints` 규칙을 갖는다 — 셋째 사본이다.

## 공식 가이드가 주는 것 — Claude Code 2.1.251 기준

조사 원문: `code.claude.com/docs/en/{plugins,plugins-reference,plugin-marketplaces,discover-plugins,hooks,memory,skills,large-codebases}`.

- **플러그인이 1급 공유 단위다.** skills·agents·hooks(`hooks/hooks.json`)·MCP/LSP·`settings.json` 을 한 디렉터리로 묶어 git 저장소(마켓플레이스)에서 설치한다.
  스킬 이름은 `plugin:skill` 로 네임스페이스가 붙고, 프로젝트 `.claude/settings.json` 의 `extraKnownMarketplaces` + `enabledPlugins` 로 **저장소가 자기 플러그인을 선언**한다 — clone 한 사람·agent 가 자동으로 받는다(2.1.195+).
  마켓플레이스 항목은 `ref`(태그·브랜치)·`sha` 로 **고정**할 수 있다.
  > "When shared skills need their own version history or must work across repositories, package them as a plugin instead." — large-codebases
- **스크립트 경로는 `${CLAUDE_PLUGIN_ROOT}`** 로 푼다(설치 디렉터리 — 갱신마다 바뀐다). 상태·의존은 `${CLAUDE_PLUGIN_DATA}`(갱신 후 생존).
- **플러그인 hook 는 프로젝트 hook 와 병합**된다 — 같은 이벤트에 둘 다 돈다.
- **rules 는 플러그인에 못 싣는다.** `.claude/rules/` 는 **symlink 를 공식 지원**한다("supports symlinks, so you can maintain a shared set of rules and link them into multiple projects"). user 수준 `~/.claude/rules/` 도 있다.
- **`--add-dir` 는 파일 접근이지 설정 발견이 아니다.** `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 로 CLAUDE.md·rules 는 읽게 할 수 있으나 CLI 플래그에만 적용된다 — 하네스 공유 수단으로는 약하다.
- **git submodule 은 문서에 없다.** 지원 여부·주의점 미확인.

## 옵션

### A. 현상 유지 — 복사 + conformance 감사

지금 방식이다.
쌍둥이 파서는 주석으로 서로를 가리키고, steward 의 conformance 가 어긋남을 잡는다.

- 이긴다: 각 하네스가 자기 안에 닫혀 있다. 새 PC 에서 clone 하나면 끝. 버전 개념이 없어 "지금 main 이 진실" 이 단순하다.
- 진다: 사본이 셋이다(steward 포함). 감사는 어긋난 **뒤에** 잡는다 — 구조가 아니라 규율이다(§8 위반). #90 처럼 두 PR 을 같은 내용으로 여는 비용이 매번 든다.

### B. symlink / submodule

rules 는 symlink 가 공식이다.
스킬·hook 디렉터리 symlink 와 `.claude/` submodule 은 **문서가 말하지 않는다**.

- 이긴다: 가장 싸다. 파일 시스템 수준이라 PATH·import 가 그대로 산다.
- 진다: symlink 는 git 으로 배포되지만 대상 경로가 PC 마다 다르면 깨진다(env 로 못 푼다). submodule 은 "어느 커밋인가" 를 두 저장소가 각자 들고 있어 드리프트가 **submodule 포인터** 로 옮겨갈 뿐이다. 미문서 조합은 다음 버전에서 조용히 깨질 수 있다.
- 자리: **rules 에만.** `python-typehints.md` 같은 하네스 무관 규칙은 user 수준(`~/.claude/rules/`)이나 symlink 로 충분하다.

### C. 공용 플러그인 저장소 — `harness-common`(가칭)

```
harness-common/
├── .claude-plugin/plugin.json          # name · version
├── .claude-plugin/marketplace.json     # 자기 자신을 마켓플레이스로
├── skills/obs-query/{SKILL.md,scripts/}
├── hooks/hooks.json                    # SessionStart: PATH·env 주입
└── lib/{ticket_sections.py, guard.py, ...}   # 쌍둥이 파서·hook 헬퍼
```

두 하네스의 `.claude/settings.json` 이 `extraKnownMarketplaces` + `enabledPlugins` 로 선언한다.
스킬은 `harness-common:obs-query` 가 된다.

- 이긴다: **공식 경로**다. 한 저장소·한 커밋이 진실이고, 두 하네스는 `ref`/`sha` 로 고정한다 — "어느 버전을 쓰는가" 가 명시된다. 스킬·hook·lib 를 한 단위로 묶는다. 하네스 갱신이 PR 하나가 된다.
- 진다: 저장소가 하나 늘고, 갱신 흐름(`/plugin update` 또는 pin 올리기)이 생긴다. **rules 는 못 싣는다**(B 로). 스크립트가 지금 기대는 두 가정이 깨진다 — 아래 "옮기려면".
- steward 와의 관계: `harness-common` 은 **넷째 쓰기 경계**가 된다 — `$HARNESS_COMMON_ROOT` 를 steward 의 guard-write 에 더한다. 지위는 ticket-engineer 와 같다(피관리 하네스 — 정책 실질이 실려도 정상, §6). 쌍둥이 파서가 여기로 오면 "표기 = 정책의 구현" 이 **한 곳**에 있고, ops 의 `ticket` 스킬과 TE 의 `ticket-start` 가 같은 모듈을 import 한다 — conformance 가 볼 쌍이 사라진다.

### D. 파서만 라이브러리로 — 나머지는 A

쌍둥이 중 위험한 것(정책 표기 파서)만 C 의 `lib/` 로 옮기고, 메커니즘(obs-query·hook 헬퍼)은 복사로 둔다.

- 이긴다: 가장 아픈 곳만 고친다.
- 진다: C 의 인프라(플러그인·마켓플레이스·env 주입)를 거의 다 세우고 절반만 쓴다. 그럴 바엔 C.

## 옮기려면 — 스크립트가 기대는 것 둘

1. **PATH.** 두 하네스의 `session-path.sh` 는 `$CLAUDE_PROJECT_DIR/.claude/skills/*/scripts` 만 PATH 에 올린다.
   플러그인 스킬의 `scripts/` 는 `${CLAUDE_PLUGIN_ROOT}` 아래라 안 잡힌다.
   플러그인의 `hooks/hooks.json` 에 SessionStart 를 두고 `${CLAUDE_PLUGIN_ROOT}/skills/*/scripts` 를 `CLAUDE_ENV_FILE` 에 export 하면 된다 — 지금 `session-path.sh` 가 쓰는 것과 같은 메커니즘이다.
   같은 자리에서 `HARNESS_COMMON_ROOT=${CLAUDE_PLUGIN_ROOT}` 를 export 하면 하네스 고유 스크립트(ops `ticket`, TE `ticket-start`)가 `lib/` 를 import 할 경로를 얻는다.
   ⚠ `CLAUDE_PLUGIN_ROOT` 가 플러그인 hook 밖의 일반 Bash 에서도 보이는지는 **미확인** — env 파일 경유가 안전하다.
2. **저장소 루트.** `_obs.py` 는 `REPO_ROOT = Path(__file__).parents[4]` 로 루트를 잡아 `tmp/obs/` 에 원본을 떨어뜨린다.
   플러그인 안에서는 그 산술이 플러그인 캐시 디렉터리를 가리킨다.
   `CLAUDE_PROJECT_DIR` 로 바꿔야 한다 — 어차피 그쪽이 맞다(cwd·설치 위치에 무관).

## 공유하면 안 되는 것

- **guard-write 의 `main`** — 경계는 하네스의 정체성이다. ops 는 "저장소 안 + `_index` 거부", TE 는 "`workspace/target`·`tmp/` 만", steward 는 "두 대상 repo". 헬퍼만 공유하고 경계는 각자 둔다.
- **`refresh-refs.py`** — 방향이 다르다. 닮은 이름에 속지 않는다.
- **CLAUDE.md** — 공유할 문장이 있다면 그것은 하네스 규약이 아니라 정책이고, 정책은 ADR 의 자리다.
- **steward 의 자기 하네스** — §5. 공용 플러그인을 steward 가 설치하더라도 steward 의 `.claude/` 개정은 여전히 사람 몫이다.

## 상대편에 서서

C 에 대한 반론: **셋 중 둘만 같은 것을 위해 저장소·버전·갱신 흐름을 세운다.**
하네스가 둘뿐이고 겹치는 것이 스킬 하나 + 파서 둘 + 헬퍼 몇 개면, 복사 + 감사가 더 싼 것 아닌가.
답: 지금은 그렇다. 그러나 #90 의 요구("둘이 같아야 한다")는 앞으로 관측·진단 계열 스킬마다 반복된다 — 하네스가 actual 을 읽는 도구는 정책과 무관하니 전부 공유 대상이다.
그리고 쌍둥이 파서는 "어긋나면 티켓이 거부된다" 는 성질 때문에 감사가 아니라 **구조**로 하나여야 한다 — §8 의 요구다.

A 에 대한 반론: 감사가 잡는다는 말은 "사람이 conformance 를 돌린다" 는 말이다.
그 사이 두 하네스는 다른 코드로 돈다.

## 수렴 전 확인할 것

- `CLAUDE_PLUGIN_ROOT` 가 플러그인 hook 밖의 Bash 에서 보이는가(안 보이면 env 파일 경유 — 위 1).
- private GitHub 저장소를 마켓플레이스 source 로 쓸 때 인증이 `gh`/git credential 을 따르는가.
- 플러그인 갱신 정책 — `sha` 고정 후 사람이 pin 을 올리는가, `ref: main` 으로 따라가는가. 전자는 "어느 버전" 이 명시되고 후자는 A 의 단순함을 지킨다.
- steward 의 guard-write 에 `$HARNESS_COMMON_ROOT` 를 더하는 개정(사람의 일, §5).

## 영향

- #90: 지금 PR(#91·TE#1)은 복사본이다. C 로 가면 두 PR 의 스킬은 플러그인으로 옮겨가고, 하네스 쪽에는 `enabledPlugins` 선언만 남는다. 지금 머지하고 나중에 옮겨도 되고, 이 논의가 먼저 굳으면 PR 을 다시 자를 수도 있다 — 사람의 선택.
- conformance 스킬: C 라면 감사 대상에 "두 하네스의 `enabledPlugins` pin 이 같은가" 가 들어오고 "쌍둥이 파서 정합" 은 빠진다.
