---
type: discussion
kind: deliberation
goal: prod-sync-gate-and-sync-alerts
topic: homelab
subjects: [argocd, applicationset, careerhub-prod, prometheus, alertmanager, jyoliar-k8s]
status: active
ref-adrs: []
related:
  - docs/homelab/discussion/261111_1800_argocd-sync-policy-metrics-notifications-survey.md
---

# prod 반영을 사람이 쥐고, 어긋난 Argo CD 앱을 알럿으로 안다

## 1. 문제

jyoliar-k8s의 main 머지는 곧 prod 배포다.
ApplicationSet 전부가 auto-sync(prune · selfHeal)이기 때문이다.
지금까지 이것 때문에 사고가 난 적은 없다.
그러나 stg 환경이 같은 저장소 · 같은 base 위에 서면, stg나 base를 고친 PR이 의도하지 않았는데 prod까지 반영되는 길이 생긴다.
사람이 diff를 보지 않은 변경이 공개 서비스에 들어가는 것이 잃는 것이다.
selfHeal이 손으로 한 조치를 곧바로 되돌리는 것도 prod에서는 원하지 않는다.

그래서 prod의 반영은 사람이 Argo CD에서 sync로 연다.

자동 반영을 걷어내면 "어긋나면 알아서 맞춘다"가 사라지고, 어긋난 상태가 방치될 수 있다.
지금도 Synced가 아닌 앱은 Argo CD 화면을 열어 봤을 때에만 알게 된다.
그래서 어긋남을 알럿으로 받는다 — prod만이 아니라 모든 앱에 대해서다.

열려 있던 것은 셋이다.
알럿을 어느 경로로 만들 것인가.
환경에 따라 심각도를 어떻게 달리할 것인가.
prod의 ApplicationSet 정의 자체는 여전히 자동으로 반영되는데, 그 길을 어디까지 막을 것인가.

## 2. 실측

**sync 정책 (jyoliar-k8s `gitops/overlays/baremetal/`, 2026-11-11)**

- ApplicationSet 9개 전부의 template에 `automated`가 있다 — `root` · `bootstrap` · `controllers` · `system` · `services` · `careerhub-prod` · `careerhub-prod-apps` · `careerhub-dev` · `ai-agents`.
- prod의 중첩은 이렇다: `services`(ApplicationSet) → Application `careerhub-prod`(AppProject와 ApplicationSet `careerhub-prod`를 담는다) → Application 3개(mongodb · postgresql · apps) → apps가 ApplicationSet `careerhub-prod-apps`를 담는다 → Application 10개.
- `careerhub-prod`는 `prune: true` · `selfHeal: true`, `careerhub-prod-apps`는 `prune: false` · `selfHeal: true`다.
- base의 `zitadel/application.yaml`(Application `zitadel-helm`)에도 `automated`가 있다 — ApplicationSet이 아니라 매니페스트로 선언된 중첩 Application이고, base라서 stg와 공유된다.
- 생성된 prod Application에는 `resources-finalizer.argocd.argoproj.io`가 붙어 있다. `preserveResourcesOnDeletion`과 `applicationsSync`는 저장소 어디에도 없다.

**반영 순서 — 선언만 있고 동작하지 않는다**

- ApplicationSet 7개가 `strategy: RollingSync`와 phase 라벨을 선언한다.
- 그 기능(Progressive Syncs)은 클러스터에서 꺼져 있다 — `argocd-cmd-params-cm`에 `applicationsetcontroller.enable.progressive.syncs` 키가 없고(`gitops/base/bootstrap/argocd/argocd-cmd-params-cm-patch.yaml`), 컨트롤러의 해당 환경변수가 빈 값이다.
- `careerhub-prod-apps`의 `status.applicationStatus`가 비어 있고, prod Application의 마지막 sync는 Application 자신의 auto-sync가 걸었다(`initiatedBy.automated: true`).
- 즉 지금 머지되면 모든 앱이 순서 없이 각자 sync한다.

**알럿의 재료**

- Argo CD 메트릭은 Prometheus에 없다 — `argocd_`로 시작하는 시리즈 0건, `argocd` 네임스페이스의 스크레이프 대상 0건.
- Service `argocd-metrics`(8082, 포트 이름 `metrics`, 라벨 `app.kubernetes.io/name: argocd-metrics`)는 떠 있고 ServiceMonitor가 없다.
- Prometheus는 `release: monitoring` 라벨이 붙은 ServiceMonitor · PrometheusRule만 고르고, 네임스페이스는 가리지 않는다(`serviceMonitorNamespaceSelector: {}`).
- Argo CD는 upstream `ha/install.yaml`(v3.2.1)을 kustomize로 patch해 깐다(`gitops/base/bootstrap/argocd/`) — 차트가 아니라서 ServiceMonitor는 직접 선언해야 한다.
- `argocd-notifications-controller`는 떠 있으나 `argocd-notifications-cm`이 비어 있다 — 쓰이지 않는다.
- 알림 경로: PrometheusRule → Alertmanager → severity별 receiver(`critical` · `warning` · `info`) → Discord의 Slack 호환 webhook. 그 밖의 severity는 blackhole로 떨어진다(`alertmanagerconfig.yaml`).
- 기존 룰의 severity 분포는 critical 10 · warning 45 · info 4다.
- 지금 클러스터의 Application 61개는 전부 Synced/Healthy다.

**앞선 관찰 (티켓)**

- #82 — 2026-08-27 DNS 장애 때 `zitadel-helm`이 `Sync=Unknown`으로 고착됐고 Health는 내내 Healthy였다. 알럿이 아니라 작업 세션의 실측으로 발견됐다.
- #143 — "알림 규칙은 `KubePodCrashLooping`뿐이라 … Argo OutOfSync는 잡지 못한다."
- #112 · #114 — obs-bench의 장애 주입이 careerhub-prod의 `selfHeal: true`를 전제로 설계됐다.

제품 쪽 사실(Progressive Syncs · 메트릭 · Notifications · ApplicationSet의 삭제 동작)은 조사 문서에 있다.

## 3. 인터뷰에서 닫힌 축

### 3-1. auto-sync를 걷어낼 범위

**선택: careerhub-prod 계열만.** `careerhub-prod` · `careerhub-prod-apps` 두 ApplicationSet과 prod의 `zitadel-helm`이다. 공용 층(bootstrap · controllers · system)과 다른 서비스(ai-agents), stg는 자동으로 둔다. (인터뷰, 2026-11-11)

<details><summary>버린 안</summary>

- 공용 층까지 수동 — cert-manager · external-dns 같은 것의 변경마다 손이 가고, stg와 prod를 가르는 의미가 흐려진다

</details>

### 3-2. 반영을 여는 수단

**선택: Argo CD의 sync뿐.** UI나 CLI로 사람이 누른다. (인터뷰, 2026-11-11)

<details><summary>버린 안</summary>

- PR 승인 규칙 · 별도 배포 도구 — 게이트를 하나 더 들이지 않는다
- 이미지 태그 인상 봇 · CI의 sync 호출 — 자동 반영 도구는 이번에 다루지 않는다

</details>

### 3-3. selfHeal

**선택: prod에서는 함께 내려놓는다.** `automated`를 지우면 selfHeal도 사라진다. 손으로 한 조치가 되돌려지지 않는 것은 원하는 바이고, 남은 어긋남은 알럿이 알린다. (인터뷰, 2026-11-11)

<details><summary>버린 안</summary>

- selfHeal만 남긴다 — Argo CD에서 selfHeal은 `automated` 아래의 설정이라 따로 남길 수 없다

</details>

### 3-4. 반영 순서

**선택: 구조로 강제하지 않는다.** 순서가 필요한 것은 최초 구축 때이고, 평소 변경은 앱 단위라 재시도로 맞춰진다. 지금도 순서는 지켜지고 있지 않았다(§2). Progressive Syncs를 켜지 않는다. (인터뷰, 2026-11-11)

<details><summary>버린 안</summary>

- Progressive Syncs를 켜고 첫 단계만 사람이 연다 — 켜는 순간 RollingSync를 선언한 7개 ApplicationSet 전부의 동작이 바뀌어 "공용 층은 자동 유지"와 부딪히고, 문서가 스스로 제거될 수 있다고 적은 기능이다

</details>

### 3-5. 알럿으로 받을 상태

**선택: 넷 전부.** OutOfSync가 오래 간다 · 비교 자체가 실패한다(Sync=Unknown) · sync 작업이 실패한다 · Health가 나쁘다. (인터뷰, 2026-11-11)

### 3-6. OutOfSync를 조용히 두는 시간

**선택: 20분, 모든 앱에 똑같이.** prod든 stg든 공용 층이든 20분 넘게 OutOfSync면 알린다. 규칙이 하나다. (인터뷰, 2026-11-11)

<details><summary>버린 안</summary>

- prod만 20분 · 나머지는 더 짧게 — 규칙이 환경마다 갈린다
- prod만 알린다 — 자동인 곳의 어긋남이 다른 신호로 드러나길 기다리게 된다

</details>

### 3-7. 수신처와 라우팅

**선택: 지금 것을 그대로 쓴다.** 기존 Alertmanager와 Discord webhook 경로로만 받고, severity 체계와 배선을 다시 짜지 않는다. 홈랩 바깥 감시 논의와 섞지 않는다. (인터뷰, 2026-11-11)

### 3-8. 이번에 다루지 않는 것

**선택: 영구 OutOfSync의 정리는 따로 한다.** 차트 기본값 때문에 늘 어긋나 보이는 리소스를 찾아 고치는 일(#53의 선례)은 이 논의 밖이다. 지금은 61개 전부 Synced라 알럿을 켜는 데 걸림이 없다. (인터뷰, 2026-11-11)

## 4. 열린 축 — 논의

### 4-1. 알럿을 만드는 경로

네 상태 중 셋(OutOfSync · Unknown · Health)은 `argocd_app_info`의 라벨로 나오고, sync 실패는 카운터 `argocd_app_sync_total`의 `phase`로 나온다(조사 문서).
Notifications의 기본 트리거에는 OutOfSync가 없고, 카탈로그에 지속 시간 조건이 없다(조사 문서).
"20분"(§3-6)은 Prometheus에서는 `for: 20m` 한 줄이다.

- **A. Prometheus — ServiceMonitor로 수집하고 PrometheusRule로 알린다.**
  이기는 조건: 지속 시간이 필요하고, 수신처 · severity 라우팅 · 룰 검증(promcheck)을 지금 것 그대로 쓰려 할 때.
  지는 조건: Argo CD의 application controller나 Prometheus가 죽으면 시리즈가 사라져 알럿도 조용해진다 — 부재를 따로 잡아야 한다.
  치르는 값: ServiceMonitor 하나와 룰 한 묶음. sync 실패 룰은 이벤트형 카운터라 promcheck 화이트리스트(③ 이벤트형)에 패턴을 더해야 할 수 있다.
- B. Argo CD Notifications — 컨트롤러가 이미 떠 있다.
  이기는 조건: 알림에 앱의 맥락(리비전 · 커밋 · Argo CD 링크)을 싣고 싶고, 상태가 바뀌는 순간에 받는 것으로 충분할 때.
  지는 조건: OutOfSync 트리거를 직접 써야 하고 "20분 이어지면"을 표현할 수단이 확인되지 않았다. 알림 경로가 Alertmanager 옆에 하나 더 생겨 §3-7과 어긋난다.
- C. 둘 다 — 지속 조건은 Prometheus, 순간 통지는 Notifications.
  이기는 조건: "반영할 것이 생겼다"는 즉시 통지를 따로 원할 때.
  지는 조건: 같은 사건이 두 경로로 두 번 온다.
- D. 안 한다 — 화면을 열어 볼 때만 안다.
  현상 유지의 비용: prod의 auto-sync를 걷어낸 뒤에는 반영을 잊은 변경과 drift가 기한 없이 남는다. #82의 Unknown 고착이 되풀이돼도 모른다.

### 4-2. 환경에 따른 심각도

심각도는 환경에 따라 달리하기로 했고, 어떻게 달리할지가 열려 있다(인터뷰, 2026-11-11).
지금 라우팅은 `critical` · `warning` · `info` 세 갈래이고, 기존 룰에서 critical은 10개뿐이다(노드 RAID · 파일 디스크립터 · PV 오류 같은 것).

환경을 가르는 열쇠는 Application의 AppProject다 — `careerhub-prod` · `careerhub-prod-apps`는 prod, stg의 AppProject는 stg, `bootstrap` · `controllers` · `system`은 공용 층이다.
`argocd_app_info`에 `project` 라벨이 실리는지는 문서가 못 박지 않았다 — 수집을 붙인 뒤 실측해야 닫힌다.
실리지 않으면 `--metrics-application-labels`로 Application 라벨을 옮기는 길이 있다(조사 문서).

공용 층을 어느 쪽으로 볼지가 이 축 안의 갈림이다 — 공용 층이 어긋나면 prod도 그 위에서 흔들린다.

- **A. 고장과 대기를 가르고, 환경은 고장에만 얹는다.**
  OutOfSync 20분은 어디서든 `info`("반영할 것이 남았다").
  Unknown · sync 실패 · Health 불량은 prod와 공용 층에서 `warning`, stg에서 `info`.
  이기는 조건: prod의 수동 반영 때문에 OutOfSync 알럿이 자주 올 것이고, 그것이 고장 알럿을 묻지 않아야 할 때.
  지는 조건: prod의 drift(손으로 고친 것)도 OutOfSync라 `info`에 섞인다.
- B. 환경만으로 가른다.
  네 알럿 모두 prod와 공용 층은 `warning`, stg는 `info`.
  이기는 조건: 규칙이 단순해야 할 때. "어느 환경인가"만 보면 채널이 정해진다.
  지는 조건: prod에서 머지 뒤 20분마다 `warning`이 온다 — 반영 대기가 고장과 같은 채널에 선다.
- C. prod의 고장은 `critical`.
  Unknown · sync 실패 · Health 불량이 prod면 `critical`, 공용 층은 `warning`, stg는 `info`. OutOfSync는 A와 같다.
  이기는 조건: prod의 반영 고장을 기존 critical(하드웨어 · 스토리지)과 같은 무게로 받겠다는 판단이 설 때.
  지는 조건: Health 불량은 기존 Kubernetes 알럿(`KubePodCrashLooping` 등, 전부 `warning`)과 같은 사건을 가리킨다 — 같은 사건이 `warning`과 `critical`로 두 번 온다.
- D. 가르지 않는다 — 전부 `warning`.
  현상 유지에 가장 가깝고 실측(`project` 라벨)을 기다리지 않아도 된다.
  비용: stg의 실험이 prod의 고장과 같은 소리를 낸다. stg가 선 뒤 알럿 피로가 여기서 온다.

### 4-3. prod의 ApplicationSet 정의가 자동으로 닿는 길

§3-1대로 두 ApplicationSet의 template에서 `automated`를 지우면 그 아래 Application 13개는 사람이 sync한다.
그러나 ApplicationSet `careerhub-prod`의 **정의 자체**는 `services` 층의 Application `careerhub-prod`가 나르고, 그 Application은 여전히 자동이다(§3-1이 `services` 층을 자동으로 두었다).

그 길로 닿는 변경은 둘이다.
template의 변경(`targetRevision` · `path` · `syncPolicy`)은 Application의 spec으로 흘러가되 클러스터 리소스에는 닿지 않는다 — sync가 수동이기 때문이다.
항목의 삭제는 다르다 — ApplicationSet의 기본 정책 `sync`는 Application의 삭제를 허용하고, 지워지는 Application에 finalizer가 붙어 있어 그 아래 리소스도 지워진다(§2 · 조사 문서).
`careerhub-prod-appset.yaml`의 generator에서 `careerhub-prod-postgresql` 한 줄을 지운 PR이 머지되면 prod PostgreSQL이 사람의 sync 없이 지워진다.
이 길은 지금도 있다 — auto-sync를 걷어내도 남는다는 것이 이 축이다.

안쪽 ApplicationSet `careerhub-prod-apps`는 사정이 다르다.
그 정의를 나르는 Application(`careerhub-prod-apps`)이 §3-1로 수동이 되므로, 항목 삭제도 사람의 sync를 거친다.

- **A. `preserveResourcesOnDeletion: true`를 prod의 두 ApplicationSet에 둔다.**
  항목이 빠져 Application이 지워져도 리소스는 남는다.
  이기는 조건: "prod 리소스는 사람의 sync 없이 지워지지 않는다"를 구조로 만들고 싶을 때. 한 줄이다.
  지는 조건: 정말로 앱을 걷어낼 때 리소스를 손으로 지워야 한다. 기존 Application의 finalizer가 이 설정으로 떼어지는지는 실측이 필요하다.
- B. `applicationsSync: create-update`를 prod의 두 ApplicationSet에 둔다.
  컨트롤러가 Application을 지우지 못한다 — 항목을 지워도 Application이 남는다.
  이기는 조건: Application 자체도 남겨 Argo CD 화면에서 "정의에서 빠졌는데 살아 있는 앱"을 보고 싶을 때.
  지는 조건: 앱을 걷어내는 절차가 두 단계(항목 삭제 → Application 수동 삭제)가 되고, 남은 Application은 어느 정의에도 없는 고아다.
- C. `services` 층의 `careerhub-prod` Application도 수동으로 한다.
  이기는 조건: prod에 닿는 모든 길을 사람의 sync 뒤에 두려 할 때 — template 변경까지 막힌다.
  지는 조건: `services` ApplicationSet은 세 항목(dev · prod · ai-agents)이 template 하나를 쓴다. 항목별로 syncPolicy를 가르려면 template를 조건부로 만들거나 prod를 따로 떼야 하고, §3-1의 "다른 서비스는 자동"과 맞추는 비용이 든다.
- D. 안 한다 — PR 검토가 문이다.
  현상 유지의 비용: 지금과 같다. 바깥 ApplicationSet의 항목은 셋뿐이고 거의 바뀌지 않는다.
  다만 stg 뼈대 작업이 같은 디렉터리의 ApplicationSet을 고쳐 쓰는 시기라, 실수가 나기 가장 쉬운 때에 안전망이 없다.

## 5. 반대편 — 이 설계가 틀리는 조건

- **공용 층은 여전히 자동이다.** CNPG 오퍼레이터나 게이트웨이 컨트롤러의 변경은 사람의 sync 없이 prod의 DB와 트래픽에 닿는다. "남의 변경이 prod에 닿는다"는 careerhub 매니페스트에 대해서만 막힌다.
- **20분은 수동 반영과 부딪힐 수 있다.** prod는 머지 뒤 20분 안에 누르지 않으면 매번 알럿이 온다. 변경을 모아서 반영하는 습관이 생기면 이 알럿은 소음이 되고, 소음이 된 알럿은 drift를 가린다.
- **Health 알럿은 기존 알럿과 겹친다.** 파드가 죽으면 `KubePodCrashLooping`과 Argo CD의 Degraded가 같은 사건으로 두 번 온다.
- **알럿의 재료가 감시 대상 안에 있다.** application controller가 죽으면 `argocd_app_info`가 사라지고, 사라진 시리즈는 조건을 만족시키지 않는다. 부재를 잡는 룰이 없으면 가장 나쁜 고장에서 조용하다.
- **prod의 selfHeal에 기댄 것이 있다.** obs-bench의 장애 주입(#112 · #114)은 selfHeal이 주입을 되돌린다는 전제로 짜였다. 전제가 사라지면 그 설계의 일부(주입 창 동안 controller를 0으로 내리는 절차)가 필요 없어지거나 달라진다.
- **base를 고치는 stg 작업이 prod를 OutOfSync로 만든다.** 렌더 결과가 같으면 뜨지 않지만, 다르면 stg 작업자가 prod의 반영 대기를 만든 것이다. 그 PR의 저자가 prod sync까지 책임지는지가 정해져 있지 않다.

## 6. 버린 것

- **AppProject의 sync window로 자동 반영만 막는 길.** `automated`를 남긴 채 prod AppProject에 상시 deny window를 걸고 수동 sync만 허용하는 방식이다. 결과는 `automated`를 지우는 것과 같은데 설정이 한 겹 더 생기고, "왜 자동인데 안 되나"를 읽는 사람이 window를 찾아가야 한다. 시간대별로 여닫을 필요가 생기면 그때 다시 본다.
- **동작하지 않는 `strategy: RollingSync` 선언의 정리.** 7개 ApplicationSet의 죽은 선언은 읽는 사람을 속이지만, 걷어내는 일은 이 논의의 목표(prod 반영을 사람이 쥔다 · 어긋남을 안다)에 닿지 않는다.

## 7. 임계선 — ADR감인가

ADR감이 아니다.
`automated` 한 블록을 되살리면 원래대로이고, 알럿 룰은 지우면 끝이다 — 되돌리는 데 한 시간이 걸리지 않는다.
"prod는 사람이 반영한다"는 운영 방침이지만 되돌리기 어려운 것을 낳지 않는다.
§4-3의 A · B도 설정 한 줄이다.

결정의 "왜"는 티켓의 Context로 간다.

## 8. 다음

- 열린 축 셋이 판정되면 Feature 하나 아래 리프 둘로 낸다 — 알럿(수집과 룰)이 먼저이고 auto-sync 제거가 그 뒤다. 걷어내기 전에 "어긋난 것을 사람이 안다"가 서 있어야 한다.
- §4-2는 `project` 라벨의 실측을 기다린다 — 알럿 리프가 수집을 붙인 뒤에야 닫을 수 있으면, 판정을 "수집 뒤 확정"으로 두고 리프의 요구사항에 실측을 넣는다.
- stg 뼈대 리프(#164)가 같은 ApplicationSet을 고친다 — auto-sync 제거가 먼저 끝나면 #164의 owner 정정이 prod에 반영될 때 수동 sync가 한 번 든다.
- obs-bench(#112 · #114)의 전제가 바뀐다는 것을 그 티켓에 알린다.
- application controller의 부재를 잡는 일은 홈랩 바깥 감시 논의(`external-homelab-monitoring`)의 신호 축과 닿는다 — 여기서 정하지 않는다.
