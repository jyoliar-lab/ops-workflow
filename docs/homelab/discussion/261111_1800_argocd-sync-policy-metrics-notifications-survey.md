---
type: discussion
kind: survey
goal: prod-sync-gate-and-sync-alerts
topic: homelab
subjects: [argocd, applicationset, argocd-notifications, prometheus]
status: done
related:
  - docs/homelab/discussion/261111_1801_prod-manual-sync-and-sync-state-alerts.md
---

# Argo CD의 sync 정책 · 메트릭 · 알림 · ApplicationSet 삭제 동작 — 조사 (2026-11-11)

## 질문

논의 문서의 세 축이 Argo CD 제품의 사실에 기댄다.
수동 sync에서 반영 순서를 지킬 수단이 있는가(Progressive Syncs).
"Synced가 아닌 앱"을 알럿으로 만들 재료가 메트릭과 Notifications 중 어디에 있는가.
ApplicationSet이 만든 Application은 정의가 바뀌거나 항목이 빠질 때 어떻게 되는가.

조사 대상은 클러스터가 돌리는 버전(v3.2.1)에 맞춰 `release-3.2` 문서다.
조사일은 전부 2026-11-11이다.

## 조사

### Progressive Syncs (RollingSync)

출처: <https://argo-cd.readthedocs.io/en/release-3.2/operator-manual/applicationset/Progressive-Syncs/>

기능은 기본으로 꺼져 있고, 켜는 길은 셋이다.

> Pass `--enable-progressive-syncs` to the ApplicationSet controller args.

> Set `applicationsetcontroller.enable.progressive.syncs: true` in the Argo CD `argocd-cmd-params-cm` ConfigMap.

켜면 ApplicationSet 컨트롤러가 sync를 직접 걸고, 생성된 Application의 auto-sync는 강제로 꺼진다.

> RollingSync will force all generated Applications to have autosync disabled.

> Warnings are printed in the applicationset-controller logs for any Application specs with an automated syncPolicy enabled.

> Sync operations are triggered the same way as if they were triggered by the UI or CLI

컨트롤러가 sync를 거는 계기는 앱의 OutOfSync 상태다.

> RollingSync will capture external changes outside the ApplicationSet resource, since it relies on watching the OutOfSync status of the managed Applications.

앞 단계가 전부 Healthy가 돼야 다음 단계로 넘어간다.

> All Applications in each group must become Healthy before the ApplicationSet controller will proceed to update the next group of Applications.

단계에 `maxUpdate: 0`을 두면 컨트롤러는 그 단계의 앱을 건드리지 않고 사람의 sync를 기다린다.
문서의 예시 설명이 그 쓰임을 보인다.

> The rollout will wait for all `env-qa` Applications to be manually synced via the `argocd` CLI

어느 단계에도 잡히지 않은 앱은 rolling sync에서 빠진다.

> If an Application is not selected in any step, it will be excluded from the rolling sync and needs to be manually synced through the CLI or UI.

안정성에 대한 문서의 경고가 있다.

> It may be removed in future releases or modified in backwards-incompatible ways.

문서가 말하지 않는 것이 하나 있다.
사람이 뒤 단계의 앱을 먼저 sync했을 때 컨트롤러가 그것을 막는지는 적혀 있지 않다.

### 메트릭

출처: <https://argo-cd.readthedocs.io/en/release-3.2/operator-manual/metrics/>

application controller의 메트릭은 Service `argocd-metrics`의 8082 포트에서 나온다.

> Scraped at the `argocd-metrics:8082/metrics` endpoint.

앱 상태는 `argocd_app_info` 하나에 실린다.

> Information about Applications. It contains labels such as `sync_status` and `health_status`

문서가 이 메트릭에 대해 이름으로 짚는 라벨은 `sync_status`와 `health_status` 둘이다.
공용 라벨 표에 `project`와 `dest_server`가 있으나, 문서는 그것이 어느 메트릭에 붙는지 묶어 말하지 않는다.

sync 작업의 이력은 카운터다.

> Counter for application sync history.

공용 라벨 표가 `phase`를 정의한다.

> Phase of a sync operation. Possible values are: Error, Failed, Running, Succeeded, Terminating.

Application의 condition을 싣는 `argocd_app_condition`은 application controller에 `--metrics-application-conditions` 플래그를 줘야 나온다.
Application에 붙인 라벨을 Prometheus 라벨로 옮기는 `argocd_app_labels`도 기본은 꺼져 있다.

> To enable it, add the `--metrics-application-labels` flag to the Argo CD application controller.

문서의 ServiceMonitor 예시는 `app.kubernetes.io/name: argocd-metrics`로 Service를 고르고 포트 이름 `metrics`를 긁는다.

### Notifications

출처: <https://argo-cd.readthedocs.io/en/release-3.2/operator-manual/notifications/catalog/>

카탈로그의 기본 트리거는 여덟이다.

| 트리거 | 설명(원문) |
|---|---|
| on-created | Application is created. |
| on-deleted | Application is deleted. |
| on-deployed | Application is synced and healthy. Triggered once per commit. |
| on-health-degraded | Application has degraded |
| on-sync-failed | Application syncing has failed |
| on-sync-running | Application is being synced |
| on-sync-status-unknown | Application status is 'Unknown' |
| on-sync-succeeded | Application syncing has succeeded |

OutOfSync를 잡는 트리거는 카탈로그에 없다.
카탈로그 페이지에는 "어떤 상태가 N분 이어지면"에 해당하는 지속 시간 조건도 없다 — 트리거는 상태가 바뀌는 순간에 선다.
직접 쓴 트리거로 OutOfSync를 잡을 수 있는지, 지속 시간을 흉내 낼 수 있는지는 이 조사에서 확인하지 않았다.

### ApplicationSet이 Application을 고치고 지우는 범위

출처: <https://argo-cd.readthedocs.io/en/release-3.2/operator-manual/applicationset/Controlling-Resource-Modification/>

ApplicationSet의 변경은 생성된 Application으로 흘러간다.

> Changes made to the ApplicationSet will propagate to the Applications managed by the ApplicationSet

컨트롤러가 Application에 할 수 있는 일은 정책으로 좁힌다.
기본은 `sync`다.

> `sync` is the default, which is used if the `--policy` parameter is not specified

| 정책 | 원문 |
|---|---|
| `create-only` | Prevents ApplicationSet controller from modifying or deleting Applications. |
| `create-update` | Prevents ApplicationSet controller from deleting Applications. Update is allowed. |
| `create-delete` | Prevents ApplicationSet controller from modifying Applications. Delete is allowed. |
| `sync` | Create, Update and Delete are allowed. |

Application이 지워지면 그 아래 리소스도 지워진다.

> all of the child resources of the Application will be deleted as well

이것을 막는 설정이 `preserveResourcesOnDeletion`이다.

> To prevent an Application's child resources from being deleted when the parent Application is deleted

출처: <https://argo-cd.readthedocs.io/en/release-3.2/operator-manual/applicationset/Application-Deletion/>

> This syncPolicy parameter prevents the finalizer from being added to the Application.

generator가 더는 만들지 않는 Application을 컨트롤러가 지운다는 것을 문서는 한 문장으로 못 박지 않는다.
`create-only`와 `create-update`가 "삭제를 막는다"고 정의된 데서 따라 나오는 해석이다.

## 논의 문서로 가져가는 것

- Progressive Syncs는 기본으로 꺼져 있고, 켜면 생성된 Application의 auto-sync를 강제로 끄고 컨트롤러가 단계 순서대로 sync를 건다.
- 컨트롤러는 앱의 OutOfSync를 보고 sync를 건다 — template의 `automated`를 지워도 컨트롤러가 거는 sync는 멈추지 않는다.
- `maxUpdate: 0`인 단계는 사람의 sync를 기다린다 — 사람이 뒤 단계를 먼저 누르는 것을 막는다는 보장은 문서에 없다.
- Progressive Syncs는 문서가 스스로 "제거되거나 호환되지 않게 바뀔 수 있다"고 적은 기능이다.
- 앱의 Sync 상태(OutOfSync · Unknown)와 Health 상태는 `argocd_app_info`의 라벨 `sync_status` · `health_status`로 나온다.
- sync 작업 실패는 카운터 `argocd_app_sync_total`의 `phase`(Error · Failed)로 나온다.
- 메트릭 엔드포인트는 `argocd-metrics:8082/metrics`다.
- Notifications의 기본 트리거에는 OutOfSync가 없고, 카탈로그에 지속 시간 조건이 없다.
- ApplicationSet의 기본 정책은 `sync`라 Application의 생성 · 갱신 · 삭제가 전부 허용되고, Application이 지워지면 그 아래 리소스도 지워진다.
- `preserveResourcesOnDeletion: true`는 Application이 지워져도 리소스를 남긴다.
