---
type: discussion
kind: deliberation
goal: external-homelab-monitoring
topic: homelab
subjects: [alertmanager, prometheus, cloudflare-tunnel, discord, careerhub, jyoliar-k8s, jyoliar-platform-terraform]
status: active
ref-adrs: []
related:
  - docs/homelab/discussion/261106_2031_external-watchdog-receivers-survey.md
  - docs/homelab/discussion/260730_2245_prometheus-tsdb-full-double-monitoring-failure.md
---

# 홈랩 바깥의 감시 주체 — 무엇을 어디서 보게 할까

## 1. 문제

홈랩의 알럿은 전부 홈랩 안에서 난다.
Prometheus 가 클러스터 내부 메트릭을 보고, Alertmanager 가 홈랩의 인터넷을 거쳐 Discord 로 보낸다.
그래서 공유기가 죽거나 ISP 가 끊기면 Alertmanager 는 장애를 알아도 보낼 수 없고, 정전·화재로 클러스터가 통째로 사라지면 알 주체 자체가 없다.
2026-07-30 에는 Prometheus 디스크가 차면서 경보 체계가 스스로 침묵했다 — 그때 "근본 해소는 외부 관측" 이라는 관찰이 남았다(related 의 7월 논의 §구조적 관찰 5번).

잃는 것은 careerhub 사용자의 다운타임이다.
외부 사용자가 있는 서비스라 가용성 자체가 손실이고, 내가 알아채는 시점이 사용자보다 늦으면 안 된다.

이 논의가 정하는 것은 **바깥에서 무엇을 보게 할지, 그 주체를 어디에 둘지, 홈랩 쪽 배선을 얼마나 바꿀지**다.
바깥 감시는 기존 룰과 겹치는 것을 다시 잡지 않는다.
한 신호에서 조사가 시작되어 연쇄적으로 원인에 닿을 수 있으면 충분하다 — "Alertmanager 가 침묵한다" 를 알면 조사해서 "클러스터가 사라졌다" 에 닿는다.

열려 있던 것은 셋이었다 — 신호의 집합, 주체의 거처, Alertmanager 배선.
조사 문서(related)가 사실을 댔고 아래 §4 가 옵션을 벌린다.

## 2. 실측

- Alertmanager 는 Watchdog 을 `alertname` 매처로 `info-slack-notifications` 에 `repeatInterval: 24h` 로 보낸다. 수신처는 Discord 의 Slack 호환 webhook 이다 — `workspace/ref/jyoliar-k8s/gitops/overlays/baremetal/system/prometheus-config/alertmanagerconfig.yaml` · `workspace/ref/jyoliar-platform-terraform/shared/alert/main.tf`.
- Watchdog 의 **부재를 판정하는 바깥 주체는 없다.** 티켓 #39 는 Watchdog 을 "데드맨 스위치로 사용 중" 이라 적지만 스위치의 바깥 반쪽이 없다.
- Prometheus 룰은 kube-prometheus 표준 룰과 promcheck 메타 룰뿐이다. **터널·공개 엔드포인트 도달성을 보는 룰은 없다** — `workspace/ref/jyoliar-k8s/gitops/base/system/prometheus-config/rules/` · `controllers/promcheck/`.
- 공개 경로는 Cloudflare Tunnel 하나다. `careerhub.jyo-liar.com` 과 `k8s-oidc.jyo-liar.com` 둘이 ingress 에 있다 — `workspace/ref/jyoliar-k8s/gitops/base/bootstrap/cloudflare-tunnel/config.yml`. 터널은 `shared-cloudflare` 워크스페이스가 소유한다.
- 클라우드 발판은 AWS(IAM·SSM·S3·terraform cloud)와 Cloudflare(zone·tunnel) 둘이다. Discord 서버·채널·webhook 은 `shared-alert` 가 terraform 으로 선언한다.
- 노드 8대 전부 한 집의 한 공유기 뒤에 있다(`kubectl get nodes`, 10.18.x.x). 집안에는 독립 실패 도메인이 없다.
- 알럿 라우팅·수신 채널·외부 의존을 정한 ADR 은 없다. ADR-0034(proposed) 는 클라우드 측 재료를 terraform 이 맡는다는 DAG 를 그리지만 아직 결정이 아니다.
- 조사 문서가 가져온 사실은 그 문서 끝의 목록이다. 결론에 쓰인 것: 심장박동과 바깥 탐침은 서로의 사각을 메운다 / Cloudflare Tunnel Health Alert 는 무료·Discord 가능·terraform 선언 가능이나 판정 지연 미확인 / Cloudflare Health Checks 는 예산 밖 / 무료 SaaS 는 Healthchecks.io(20)·Better Stack(10 합산·3분)·UptimeRobot(50·5분·heartbeat 유료)·Cronitor(5) / AWS 직접 구축은 비용 0 에 가깝되 코드 소유 / Alertmanager 변경은 라우트·receiver 하나씩.

## 3. 인터뷰에서 닫힌 축

### 3-1. 바깥이 잡는 것

**선택: 기존 룰과 겹치지 않는 최소 신호만.** 바깥 감시는 원인을 말하지 않아도 된다 — 한 알럿에서 조사가 시작되어 연쇄적으로 닿으면 된다. (인터뷰, 2026-11-06)

<details><summary>버린 안</summary>

- 바깥에서 내부 알럿을 재현(노드·파드·디스크까지) — 기존 룰과 겹치고, 바깥 주체가 커져 그 자체가 관리 대상이 된다
- 장면별 전용 신호(공유기용·정전용·관측 스택용 각각) — 셋 다 "Alertmanager 가 침묵한다" 한 신호로 드러난다

</details>

### 3-2. 탐지 지연

**선택: 5~15분.** careerhub 사용자보다 먼저 알아야 한다. 짧은 일시 장애도 알림으로 온다. (인터뷰, 2026-11-06)

<details><summary>버린 안</summary>

- 1시간 — 지속 장애만 보겠다는 뜻인데, 사용자 다운타임이 손실이라 맞지 않는다
- 하루 — 지금 Watchdog 24h 와 같다. 바꾸는 의미가 없다

</details>

### 3-3. 비용

**선택: 무료~월 수 달러.** 유료 플랜이 전제인 길(Cloudflare Health Checks Pro, 상시 VPS/EC2)은 처음부터 뺀다. (인터뷰, 2026-11-06)

### 3-4. 수신 채널

**선택: 지금 Discord 서버.** 바깥 감시 제품은 Discord webhook 을 지원해야 한다. Discord 자체가 단일 장애점이라는 문제는 이 논의 밖이다(3-5). (인터뷰, 2026-11-06)

### 3-5. 이번에 다루지 않는 것

**선택: 복구·DR 자체 · 사용자용 상태 페이지 · 기존 내부 알럿 룰의 재설계 · 감시자의 감시 · Discord 외 2차 수신 채널.** 2차 수신 채널은 기존 Alertmanager 에도 걸리는 별개 관점이라 같은 목표의 다음 논의로 뗀다. 내부 룰은 바깥 감시로 이어지는 최소 변경(라우팅)만 허용한다. (인터뷰, 2026-11-06)

## 4. 열린 축 — 논의

### 4-1. 신호의 집합 — 심장박동인가, 바깥 탐침인가, 둘인가

실측: 심장박동(Alertmanager → 바깥 ping)은 인터넷 단절·클러스터 소실·관측 스택 고장을 한 침묵으로 잡고, 공개 경로만 끊긴 경우(터널·엣지·게이트웨이)를 놓친다.
바깥 탐침(바깥 → `careerhub.jyo-liar.com`)은 그 반대다.
내부 룰은 공개 경로 도달성을 보지 않으므로 탐침은 기존 룰과 겹치지 않는다.
홈랩 사례들은 둘을 함께 둔다.

- **A. 심장박동 하나** — 이기는 조건: 사용자 다운타임의 지배적 원인이 "홈랩 전체가 안 보임"(인터넷·전원)일 때. 지는 조건: cloudflared 나 게이트웨이만 죽은 장애가 실제로 나면 바깥은 침묵하고 사용자만 안다
- **B. 바깥 탐침 하나** — 이기는 조건: 손실의 정의가 오직 "사용자가 못 쓴다" 일 때 가장 직접적인 신호다. 지는 조건: 2026-07-30 형(서비스는 살았는데 관측 스택이 죽음)을 다시 놓친다 — 바로 이 논의를 낳은 장면이다
- **C. 둘 다** — 이기는 조건: 두 사각이 서로 다른 층이라 하나로 안 덮이고, 무료 티어 안에서 둘 다 든다(조사 §4·§5). 지는 조건: 알림이 겹쳐 한 장애에 두 알럿이 오는 것을 노이즈로 느낄 때 — 다만 둘은 다른 뜻이라 조사의 출발점이 갈린다
- **D. Cloudflare Tunnel Health Alert 로 심장박동을 대신하고 탐침만 더함** — 이기는 조건: 새 공급자 없이 Cloudflare 안에서 끝내고 싶고, 터널 Down 판정 지연이 5~15분 안에 들어올 때. 지는 조건: 판정 지연이 미확인이고, 관측 스택만 죽은 경우는 터널이 살아 있어 못 잡는다 — 심장박동의 대체가 아니라 탐침 쪽의 보강이다
- E. 안 한다 — 현상 유지의 비용: 공유기·정전 장애는 사용자 제보나 다음 날 발견으로만 드러난다. 7월 장애의 "자기관측 사각" 이 그대로 남는다

### 4-2. 주체의 거처 — SaaS 인가, 이미 쓰는 클라우드인가, 집 밖의 내 기계인가

실측: 조사 §4~§7.
비교 축은 **실패 도메인의 독립성 · 소유하는 코드의 양 · 무료 티어의 변동 위험 · 코드로 선언 가능한가** 넷이다.

- **A. 무료 SaaS 하나(심장박동 + 탐침 겸용)** — Better Stack(10 합산·3분) 또는 Cronitor(5·5분). 이기는 조건: 새 공급자 하나로 4-1 C 를 끝내고, 소유 코드가 0 이며, 홈랩·Cloudflare·AWS 어느 것과도 실패 도메인을 공유하지 않는다. 지는 조건: 무료 티어가 바뀌거나 Discord 통합이 무료에 없을 때(가입해야 닫히는 사실). 공급자 하나가 더 는다
- **B. 무료 SaaS 둘(심장박동 Healthchecks.io + 탐침 UptimeRobot)** — 이기는 조건: 각 역할에서 가장 넓은 무료 티어를 쓰고 싶을 때(20 checks · 50 monitors). 지는 조건: 계정·비밀·통합을 둘 관리한다. 한 제품으로 되는 일을 둘로 벌린다
- **C. 이미 쓰는 클라우드 안에 직접 구축(AWS Lambda + CloudWatch 알람, 또는 Cloudflare Worker Cron + KV)** — 이기는 조건: 새 공급자를 늘리기 싫고 terraform 으로 전부 선언하고 싶을 때. 비용은 0 에 가깝다. 지는 조건: 감시기 코드(수신·판정·Discord 발송)를 소유하고 패치한다 — 감시기의 버그가 침묵으로 나타난다. Cloudflare 안이면 서빙 경로와 실패 도메인을 공유하고, KV 쓰기 1,000/일이 ping 주기를 2분 이상으로 묶는다
- **D. 집 밖 기계에 Uptime Kuma·Gatus** — 이기는 조건: 이미 집 밖에 상시 기계가 있을 때. 지는 조건: 없다 — VPS·EC2 상시 비용은 예산을 넘거나 경계에 있고, "two things to patch" 다
- E. 안 한다 — 4-1 E 와 같다

A·B 는 ADR-0034 가 그리는 DAG 밖의 제4 공급자다.
그 선언을 terraform 에 둘지(커뮤니티·자사 provider 존재, 조사 §9), 콘솔에 둘지는 이 축의 판정 뒤에 티켓이 정한다 — 되돌리기 쉬운 일이다.

### 4-3. Alertmanager 배선 — 심장박동을 어떻게 흘릴까 (4-1 에서 심장박동을 고를 때만)

실측: Watchdog 은 지금 Discord 로 24h 마다 간다.
바깥으로 분 단위로 보내려면 라우트 하나·receiver 하나를 더하고, `continue: true` 로 Discord 라우트를 살린다.
`repeat_interval` 은 `group_interval` 의 배수여야 한다.
Healthchecks.io 는 POST 를 받고 분당 5회까지다.

- **A. Watchdog 을 바깥 receiver 로도 흘린다(라우트 추가 · `continue: true`)** — 이기는 조건: 룰 변경 0, Discord 의 하루 한 번 Watchdog 유지. 지는 조건: 없음 — 가장 작은 변경이다
- B. Watchdog 의 Discord 라우트를 바깥 receiver 로 교체 — 이기는 조건: Discord 의 매일 Watchdog 메시지를 노이즈로 볼 때. 지는 조건: 바깥 주체가 죽으면 Watchdog 이 어디에도 안 보이고, #39 의 "Watchdog 은 Slack 수신이 유지되어야 한다" 를 뒤집는다
- C. 별도 always-firing 룰(`ExternalHeartbeat`)을 둔다 — 이기는 조건: Watchdog 의 의미(내부 파이프라인 정상)와 바깥 심장박동을 구분하고 싶을 때. 지는 조건: 같은 `vector(1)` 이 둘이 되고 룰 층을 건드린다(3-5 의 경계)

## 5. 반대편 — 이 설계가 틀리는 조건

- 5~15분 목표로 분 단위 탐침을 하면 집 ISP 의 짧은 흔들림이 전부 알림이 된다. 노이즈가 쌓여 알림을 끄게 되면 없는 것보다 나쁘다 — grace 를 얼마로 둘지는 운영하며 맞춘다.
- 바깥 주체가 Discord 로만 알리면 Discord 장애는 여전히 침묵이다. 이 논의는 그것을 밖으로 뺐지만(3-5), 빼서 사라진 게 아니다 — 다음 논의가 닫아야 한다.
- 무료 SaaS 는 계약이 아니다. 2026년에도 무료 티어가 바뀌었다(조사 §4). 바뀌면 감시가 조용히 꺼질 수 있다 — 그래서 "감시자의 감시" 를 밖으로 뺀 것이 길게는 틀릴 수 있다.
- 심장박동 침묵이 홈랩이 아니라 SaaS 쪽 장애일 수 있다. 그때 조사는 헛걸음이지만, 헛걸음은 침묵보다 싸다.
- 4-1 D(Cloudflare 안에서 끝내기)는 Cloudflare 가 죽는 날 careerhub 와 감시가 같이 죽는다. Cloudflare 장애는 대개 공개적으로 요란하니 실질 위험은 낮지만, "감시 주체는 감시 대상과 같이 죽지 않는다" 는 원리에 어긋난다.
- 바깥 탐침은 `careerhub.jyo-liar.com` 의 HTTP 응답만 본다. 200 은 오는데 기능이 깨진 장애는 못 잡는다 — 그것은 내부 룰의 몫이고, 이 논의의 신호는 "닿는가" 까지다.

## 6. 버린 것

- **Cloudflare Health Checks** — 바깥 탐침으로 가장 자연스럽지만 Pro(도메인당 월 $20~25) 다. 예산(3-3) 밖.
- **AWS Route 53 Health Check** — 월 $2.75 로 예산 안이지만, 결과가 CloudWatch 알람으로만 나와 Discord 까지 Lambda 가 더 필요하다. 그 Lambda 를 짓는다면 CloudWatch 심장박동(4-2 C)까지 같이 짓는 게 맞고, 안 짓는다면 SaaS 탐침이 더 싸다.
- **CloudWatch Synthetics** — 무료 100 run/월. 5분 주기엔 턱없이 모자란다.
- **집안의 두 번째 기계로 상호 감시** — 공유기가 엣지라 독립 실패 도메인이 아니다(kubelab #1021 의 10월 갱신이 같은 결론).
- **홈랩 안의 alertdog·data-dead-mans-switch** — Watchdog 수신기를 홈랩 안에 돌리면 같이 죽는다. 바깥에 돌릴 기계가 있어야 의미가 있고, 그러면 4-2 D 다.
- **Grafana Cloud Synthetic Monitoring** — 무료 100k execution 으로 5분 탐침은 넉넉하지만, 한 점검을 위해 관측 플랫폼 계정을 하나 더 두는 것이다. 홈랩의 관측은 이미 자체 스택이다.

## 7. 임계선 — ADR감인가

ADR 이 아니다.
바깥 수신처를 고르고 라우트 하나를 더하는 일은 되돌리는 데 한 시간이 안 걸린다 — check 를 지우고 라우트를 빼면 끝이다.
영향 범위도 알림 경로 하나다.
ADR-0034 가 accept 되면 "클라우드 측 재료는 terraform" 이라는 결정이 바깥 수신처의 선언 위치를 정하겠지만, 그것은 저쪽 ADR 의 몫이지 이 논의의 새 결정이 아니다.

하나만 적어 둔다 — "감시 주체는 감시 대상과 실패 도메인을 공유하지 않는다" 는 원리는 되돌리기 쉬운 설정이 아니라 자세다.
그래도 ADR 로 올리지 않는다.
어기면 비용이 드는 것이 아니라 감시가 안 될 뿐이고, 그것은 다음 장애가 알려 준다.
사람이 다르게 보면 `adr` 스킬로 판정한다.

## 8. 다음

판정이 나면 다음이 생긴다.
Epic 은 없다 — 근거 ADR 이 없고(§7), 일은 한 흐름의 리프 몇 개다.

- 4-2 의 판정에 따라 **수신처를 만들고 비밀을 Parameter Store 에 두는 Task** — target 은 `jyoliar-careerhub/jyoliar-platform-terraform`(terraform 으로 선언할 때) 또는 사람의 콘솔 작업(선언하지 않을 때).
- 4-3 의 판정에 따라 **AlertmanagerConfig 에 라우트·receiver 를 더하는 Task** — target `jyoliar-careerhub/jyoliar-k8s`. 위 Task 에 선행 의존.
- 4-1 에 탐침이 들어가면 **바깥 탐침을 등록하는 Task** — 홈랩 쪽 변경 0.
- 같은 목표의 다음 관점 — **Discord 외 2차 수신 채널**(기존 Alertmanager 와 바깥 주체 둘 다). 이 논의의 3-5 가 뗀 것.
- 조사 문서의 "가입해야 닫히는 사실"(Discord 통합이 무료 티어에 있는가)은 첫 Task 의 착수 시점에 사람이 확인한다 — 문서에 추정으로 적지 않는다.
