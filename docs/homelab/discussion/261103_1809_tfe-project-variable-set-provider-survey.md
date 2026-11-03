---
type: discussion
kind: survey
goal: careerhub-env-separation
topic: homelab
subjects: [terraform-cloud, tfe-provider, variable-set, jyoliar-platform-terraform]
status: done
related: [docs/homelab/discussion/261103_1809_tfc-project-and-variable-set-redesign.md]
---

# tfe provider의 프로젝트 · variable set 자원 — 조사 (2026-11-03)

## 질문

프로젝트와 variable set을 `tfc/` 메타 루트에서 코드로 선언·import하려 한다.
기존 프로젝트의 개명, 워크스페이스의 프로젝트 이동, 기존 variable set과 그 변수의 import가 재생성 없이 되는가.
변수 값이 여러 곳에서 올 때 어느 것이 이기는가.

## 조사

### 자원별 인자와 import

| 자원 | 핵심 인자 | import 식 | 출처 |
|---|---|---|---|
| `tfe_project` | `name`(3~40자, 영숫자·공백·`-`·`_`) · `description` · `tags` · `auto_destroy_activity_duration` | `terraform import tfe_project.x prj-…` | [project.html.markdown](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/website/docs/r/project.html.markdown) |
| `tfe_variable_set` | `name` · `global`(기본 false) · `priority`(기본 false) · `parent_project_id`(소유 프로젝트, 선택) · `workspace_ids`(deprecated) | `terraform import tfe_variable_set.x varset-…` | [variable_set.html.markdown](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/website/docs/r/variable_set.html.markdown) |
| `tfe_project_variable_set` | `project_id` · `variable_set_id` — "controls whether a project has access to a variable set, not whether a project owns the variable set" | `terraform import tfe_project_variable_set.x '<org>/<project id>/<variable set name>'` | [project_variable_set.html.markdown](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/website/docs/r/project_variable_set.html.markdown) |
| `tfe_variable` (variable set 소속) | `variable_set_id`(`workspace_id`와 택일) · `key` · `value` 또는 `value_wo` · `category` · `sensitive` | `terraform import tfe_variable.x <org>/<variable set id>/<variable id>` | [variable.html.markdown](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/website/docs/r/variable.html.markdown) |

- `tfe_variable_set`의 `workspace_ids`는 deprecated다 — "Use the `tfe_workspace_variable_set` resource instead."
- `parent_project_id`를 두면 `global`은 false여야 한다.
- 문서에는 `project_ids` 인자가 없다 — 프로젝트 연결은 `tfe_project_variable_set`만이다.

### 무엇이 재생성을 부르나 — provider 소스

문서가 말하지 않아 소스에서 읽었다(2026-11-03, `main` 브랜치).

- `tfe_workspace.project_id` — [resource_tfe_workspace.go](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/internal/provider/resource_tfe_workspace.go) 스키마에 ForceNew가 없고, Update 함수가 `d.HasChange("project_id")`를 `WorkspaceUpdateOptions.Project`로 넘긴다.
  **워크스페이스의 프로젝트 이동은 in-place다.**
- `tfe_project.name` — [resource_tfe_project.go](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/internal/provider/resource_tfe_project.go)에서 `RequiresReplace`가 붙은 속성은 `organization`뿐이다.
  **프로젝트 개명은 in-place다.**
- `tfe_variable_set` — [resource_tfe_variable_set.go](https://raw.githubusercontent.com/hashicorp/terraform-provider-tfe/main/internal/provider/resource_tfe_variable_set.go)에서 `ForceNew`는 `organization`과 `parent_project_id`다.
  **콘솔에서 조직 소유로 만든 variable set을 import한 뒤 프로젝트 소유로 바꾸면 재생성이다.** `name`·`priority`·`global` 변경은 in-place다.

### 변수 우선순위

출처: [HCP Terraform — Variables, Precedence](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/variables#precedence) (2026-11-03).

- 워크스페이스 변수는 비(非)priority variable set의 같은 키를 항상 덮는다 — "always overwrite variables from variable sets that have the same key."
- `priority = true`인 set의 변수는 더 좁은 범위의 같은 키보다 이긴다 — "over any variables with the same key set at a more specific scope." 코드에 하드코딩한 값까지 막지는 못한다.
- 같은 범위의 set 둘이 같은 키를 정의하면 **이름의 사전순**이 이긴다 — "uses values from the variable set with lexical precedence … regardless of which variable set has been edited most recently."

## 논의 문서로 가져가는 것

- 프로젝트 개명·워크스페이스의 프로젝트 이동은 in-place다 — 재생성 없이 트리를 다시 그릴 수 있다.
- variable set과 그 변수는 id로 import된다. 프로젝트 연결은 `<org>/<project id>/<set 이름>`으로 import된다.
- 조직 소유 set을 프로젝트 소유(`parent_project_id`)로 바꾸는 것만 재생성이다 — 기존 set을 import하려면 조직 소유를 유지한다.
- 워크스페이스에 같은 키의 변수가 남아 있으면 set 값을 조용히 덮는다. `priority = true`가 그것을 막는다.
- 한 프로젝트에 같은 키를 가진 set이 둘 붙으면 이름 사전순이 이긴다 — 프로젝트당 `env` set은 하나여야 한다.
