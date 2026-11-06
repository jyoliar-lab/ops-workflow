---
type: discussion
kind: survey
goal: external-homelab-monitoring
topic: homelab
subjects: [alertmanager, prometheus, cloudflare-tunnel, discord, careerhub, healthchecks-io, better-stack, uptime-kuma]
status: active
related: [docs/homelab/discussion/261106_2031_external-monitoring-outside-homelab.md]
---

# 홈랩 바깥의 감시 주체 — 선행 사례와 수신처 조사 (2026-11-06)

## 질문

논의 문서의 열린 축 셋이 사실을 요구했다.
첫째, 바깥에서 잡을 **신호**는 무엇인가 — 심장박동(dead man's switch)과 바깥 탐침(black-box probe)은 각각 어떤 장애를 잡고 무엇을 놓치는가.
둘째, 그 신호를 받아 판정하는 **주체는 어디에** 두는가 — 무료~월 수 달러 안에서 SaaS·이미 쓰는 클라우드(AWS·Cloudflare)·자가 호스팅 중 무엇이 가능한가.
셋째, 홈랩 쪽 **배선**은 얼마나 바뀌는가 — Alertmanager 가 Watchdog 을 바깥으로 흘리려면 무엇을 고쳐야 하는가.
조사일은 전부 2026-11-06 이다.

## 조사

### 1. 원리 — 감시 주체는 감시 대상과 같이 죽으면 안 된다

Google SRE book 6장은 두 감시를 구분한다.
black-box 는 "Testing externally visible behavior as a user would see it" 이고, white-box 는 "Monitoring based on metrics exposed by the internals of the system" 이다.
"black-box monitoring is symptom-oriented and represents active—not predicted—problems" 라 하고, Google 의 결론은 "We combine heavy use of white-box monitoring with modest but critical uses of black-box monitoring" 이다.
페이저로 가는 경로는 "need to be very simple and robust" 여야 한다고도 적는다.
출처: [sre.google — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/).

지금 홈랩의 알럿은 전부 white-box 다 — Prometheus 룰이 클러스터 내부 메트릭을 보고, Alertmanager 가 홈랩 안에서 Discord 로 보낸다.
"modest but critical" 한 black-box 몫이 비어 있다.

PromLabs 의 메타 모니터링 교재는 왜 바깥이어야 하는지를 직접 말한다.
"the Alertmanager through which notifications are supposed to get delivered to you might be down" 이고, "your entire organization's network might be disconnected from the internet!" 이라서다.
처방은 항상 발화하는 룰(`vector(1)`)을 "an external service with a repeat interval of a only a few (x) minutes" 로 라우팅하고, 바깥 서비스가 "will notice that no more alert notifications are coming in and will send you a notification about it" 하게 하는 것이다.
출처: [training.promlabs.com — End-to-End Watchdog Alerts](https://training.promlabs.com/training/monitoring-and-debugging-prometheus/metrics-based-meta-monitoring/end-to-end-watchdog-alerts/).

kube-prometheus 의 Watchdog 런북도 같은 말이다.
"This is an alert meant to ensure that the entire alerting pipeline is functional." "If not firing then it should alert external systems that this alerting system is no longer working." 완화책은 "the DeadMansSnitch integration in PagerDuty" 류의 바깥 수신처다.
출처: [runbooks.prometheus-operator.dev — Watchdog](https://runbooks.prometheus-operator.dev/runbooks/general/watchdog/).

한 관측성 블로그는 자기점검의 한계를 한 문장으로 적는다 — "A self-check is only ever as trustworthy as the system running it."
출처: [dev.to — A dead man's switch for your monitoring stack](https://dev.to/irinobservability/a-dead-mans-switch-for-your-monitoring-stack-2335) (게시 연도 미표기).

### 2. 패턴 둘 — 무엇을 잡고 무엇을 놓치나

| | 심장박동 (dead man's switch) | 바깥 탐침 (black-box probe) |
|---|---|---|
| 방향 | 안 → 밖. Alertmanager 가 주기적으로 바깥에 ping | 밖 → 안. 바깥이 공개 엔드포인트를 주기적으로 요청 |
| 침묵이 뜻하는 것 | Prometheus·Alertmanager·홈랩 인터넷·클러스터 전체 중 어딘가 죽었다 | 사용자가 지금 서비스를 못 쓴다 |
| 잡는 것 | 인터넷 단절 · 클러스터 전체 소실 · 관측 스택 자체의 고장 | 터널·Cloudflare 엣지·게이트웨이·앱 어느 층이든 공개 경로의 단절 |
| 놓치는 것 | 관측 스택은 살았는데 공개 경로만 끊긴 경우(터널만 죽음 등) | 공개 경로는 살았는데 관측 스택만 죽은 경우(2026-07-30 형) |
| 원인을 말하나 | 아니다 — 침묵만 안다. 연쇄 조사의 출발점 | 아니다 — 증상만 안다 |

둘은 서로의 사각을 메운다.
홈랩 글 하나는 셋째 길(두 번째 Uptime Kuma 상호 감시)까지 포함해 셋을 비교하고, 바깥 HTTP 점검이 "also catches DNS or reverse-proxy breakage that the cron heartbeat misses" 라고 적는다.
결론은 심장박동 + 바깥 HTTP 점검 둘을 함께 두는 것이 "cost nothing and cover most home labs" 다.
출처: [dev.to — Who monitors your Uptime Kuma? Three ways to watch the watcher](https://dev.to/tanod/who-monitors-your-uptime-kuma-three-ways-to-watch-the-watcher-146f) (10월 8일, 연도 미표기 · 저자가 자기 서비스 Tanod Monitor 를 홍보함).

### 3. 홈랩 사례

**selfhostr (2026-05-28).** 홈랩 전체가 꺼질 때를 위해 "a second Uptime Kuma instance on a small VPS, outside your home" 을 권한다.
VPS 쪽에는 공개 주소를 찌르는 HTTP/Ping 모니터와, 홈랩이 cron 으로 `curl -fsS -o /dev/null "MONITOR_URL"` 를 보내는 Push 모니터 둘을 둔다.
VPS 가격은 적지 않았다.
출처: [selfhostr.com — Monitor Your Homelab in 2026](https://selfhostr.com/tutos/monitorer-homelab-uptime-kuma-grafana-2026/).

**mlorentedev/kubelab #1021 (2026-08-12 개설, 2026-10-25 갱신).** 알림 파이프라인에 "no heartbeat/watchdog monitor" 라서 조용한 죽음이 다음 실제 장애의 누락 페이지로만 드러난다는 문제를 적었다.
안 둘 — 집안의 다른 기기(RPi3 Uptime Kuma) vs 집 밖(healthchecks.io 무료 티어).
갱신에서 RPi4 가 네트워크 엣지가 되자 "If the edge fails, rpi3's Uptime Kuma goes silent too" 라며 집안 안은 독립 실패 도메인이 아니라고 결론지었다.
출처: [github.com — kubelab issue #1021](https://github.com/mlorentedev/kubelab/issues/1021).
이 홈랩과 같은 모양이다 — 공유기 하나가 엣지다.

**Unity data-dead-mans-switch · alertdog.** Watchdog 알럿을 받아 부재를 판정하는 자가 호스팅 수신기들이다.
alertdog 은 "If none arrive, it will raise an alert, either via alertmanager, or if that is not possible via PagerDuty" 다.
출처: [github.com — data-dead-mans-switch](https://github.com/Unity-Technologies/data-dead-mans-switch) · [pkg.go.dev — alertdog](https://pkg.go.dev/github.com/errm/alertdog).
둘 다 "어디에 돌리나"는 답하지 않는다 — 홈랩 안에 돌리면 의미가 없다.

### 4. 심장박동 수신처 — SaaS

| 서비스 | 무료 티어 | 가장 싼 유료 | Discord 수신 | 출처 |
|---|---|---|---|---|
| **Healthchecks.io** | Hobbyist $0: "Monitor 20 jobs" · "100 log entries per job" · Supporter($5)는 "same limits" | Business $20/mo (100 checks · SMS 50 · 전화 20) | 있음 — README 가 Discord 를 통합으로 나열. 호스팅판 페이지는 Discord·Signal·SMS·Telegram 을 나열 | [pricing](https://healthchecks.io/pricing/) · [README](https://raw.githubusercontent.com/healthchecks/healthchecks/master/README.md) · [healthchecks.io](https://healthchecks.io/) |
| **Better Stack** | "10 monitors & heartbeats" 합산 · 상태 페이지 1 · "Slack & e-mail alerts" · 3분 점검(비교 글) | Responder $29/mo(연) · $34/mo(월) — 전화·SMS 는 여기부터 | 조사에서 무료 티어 Discord 는 확인 못 함 — 가격표는 Slack·이메일만 적음 | [pricing](https://betterstack.com/uptime/pricing) · [vs UptimeRobot (2026-05-22 갱신)](https://betterstack.com/community/comparisons/better-stack-vs-uptimerobot/) |
| **Dead Man's Snitch** | Lone Snitch: "single solitary Snitch" 1개 | Little Birdy $5/mo: 3 snitch · "Basic Intervals". Integrations 는 Private Eye $19 부터 | 무료·$5 에선 없음 | [plans](https://deadmanssnitch.com/plans) |
| **Cronitor** | Hacker $0: 5 monitors · 최단 5분 · 이메일·Slack(비교표엔 Discord·Teams·webhook) | Business: 모니터당 $2 + 사용자당 $5 | 비교표 기준 있음 | [pricing](https://cronitor.io/pricing) |
| **UptimeRobot** | 50 monitors · 5분 · "Only 5 integrations" · SMS/음성 "Not included, can be added" | Solo $9/mo(연) | heartbeat 는 유료 — 자사 블로그가 "Heartbeat (cron) monitoring is a PRO feature" | [pricing](https://uptimerobot.com/pricing/) · [blog](https://uptimerobot.com/blog/new-feature-heartbeat-monitoring/) |

Healthchecks.io 의 동작 모델은 Period 와 Grace Time 둘이다.
"Period is the expected time between pings." "Grace Time is the additional time to wait before sending an alert when a check is late."
상태는 New → Up → Late → Down 이고, Down 이 되면 통합으로 알린다.
출처: [docs — Configuring checks](https://healthchecks.io/docs/configuring_checks/) · [docs](https://healthchecks.io/docs/).

ping 엔드포인트는 "HEAD, GET, and POST request methods" 를 받고, POST 본문은 "limited to the first 100 kB for each received ping" 로 저장한다.
속도 제한은 한 check 당 분당 5회이며, 넘으면 기록되지 않거나 IP 가 차단될 수 있다.
출처: [docs — Pinging API](https://healthchecks.io/docs/http_api/).
Alertmanager webhook 은 POST 라서 그대로 맞는다.

**주의 — 무료 티어의 세부는 출처가 엇갈린다.** 가격표 페이지의 Hobbyist 열은 "20 jobs" 와 "100 log entries" 둘만 적는다.
팀 인원·SMS 크레딧 수치는 3자 사이트마다 다르고(5 SMS vs 없음), 한 글은 2026년 5월에 무료 SMS 가 빠졌다고 적는다 — [hyperping](https://hyperping.com/blog/healthchecks-io-alternatives).
Discord·webhook 통합이 무료 티어에서 열려 있는가는 공식 가격표가 말하지 않는다 — 가입해 확인해야 닫히는 사실이다.
무료 티어는 계약이 아니라서 바뀐다 — 이것이 SaaS 심장박동의 구조적 비용이다.

### 5. 바깥 HTTP 탐침 — SaaS

| 서비스 | 무료 티어 | 점검 주기 | 비고 | 출처 |
|---|---|---|---|---|
| **UptimeRobot** | 50 monitors · HTTP·port·ping·keyword | 5분 | SMS/음성은 크레딧 구매. 상업용 허용 여부는 3자 출처가 엇갈림 | [pricing](https://uptimerobot.com/pricing/) |
| **Better Stack** | 10 (heartbeat 와 합산) | 3분 | 심장박동과 탐침을 한 계정에 둘 수 있음 | [비교 글](https://betterstack.com/community/comparisons/better-stack-vs-uptimerobot/) |
| **Cronitor** | 5 monitors | 5분 | 심장박동·탐침 둘 다 | [pricing](https://cronitor.io/pricing) |
| **Grafana Cloud Synthetic Monitoring** | "100k API test executions ... per month". execution = "one minute of synthetic check runtime multiplied by the number of locations used" | 1분까지 | 1개 지역·5분 점검이면 월 약 8,640 execution 으로 여유. 다만 한 점검을 위해 Grafana Cloud 계정·스택 하나를 더 두는 셈 | [pricing](https://grafana.com/pricing/) · [blog 2024-12-03](https://grafana.com/blog/the-evolution-of-grafana-cloud-synthetic-monitoring-new-features-pricing-updates-and-more/) |

### 6. 이미 쓰는 플랫폼 안의 것 — Cloudflare · AWS

이 홈랩의 공개 경로는 Cloudflare Tunnel 이고, 클라우드 재료는 AWS 다(`workspace/ref/jyoliar-platform-terraform/README.md`).
새 공급자 없이 되는 길이 있는지 봤다.

**Cloudflare Tunnel Health Alert — 무료, 설치 없음.**
"All Cloudflare Zero Trust plans" 에 포함되고, 터널 상태 "Healthy / Inactive / Down / Degraded" 의 변화를 이메일·webhook·3자 서비스로 알린다.
webhook 수신처는 "Webhooks are available on all plans" 이며 Discord 가 지원 수신처다 — "The secret is part of the URL."
출처: [Tunnel notifications](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/monitor-tunnels/notifications/) · [Available notifications](https://developers.cloudflare.com/notifications/notification-available/) · [Configure webhooks](https://developers.cloudflare.com/notifications/get-started/configure-webhooks/).
terraform 으로는 `cloudflare_notification_policy` 의 `alert_type = tunnel_health_event` 이고 "The delivery mechanisms supported are email, webhooks, and PagerDuty" 다 — [provider docs](https://raw.githubusercontent.com/cloudflare/terraform-provider-cloudflare/master/docs/resources/notification_policy.md).
cloudflared 는 홈랩 안에서 바깥으로 연결을 유지하므로, 인터넷 단절·클러스터 소실·cloudflared 죽음 모두 Cloudflare 쪽에서 "Down" 으로 보인다 — 사실상 **공짜 심장박동**이다.
한계 둘. Down 판정까지 걸리는 시간은 문서에서 찾지 못했다(미확인).
그리고 감시 주체가 서빙 경로(Cloudflare)와 같은 실패 도메인이다 — Cloudflare 가 죽으면 careerhub 도 죽고 알림도 죽는다.

**Cloudflare Health Checks(바깥 HTTP 탐침) — 유료.**
가용성 표: Free "No" · Pro 10개 · Business 50개.
알림도 "Professional plans or higher" 다.
Pro 는 도메인당 월 $20(연)~$25(월) 로 3자 출처가 모인다 — 공식 가격 페이지는 조사에서 직접 열지 못했다.
출처: [Health Checks](https://developers.cloudflare.com/health-checks/) · [activepieces 2026](https://www.activepieces.com/blog/cloudflare-pricing-2026-plans-and-what-you-pay).
예산(월 수 달러) 밖이다.

**Cloudflare Workers Cron Trigger — 직접 만드는 심장박동·탐침.**
Workers Free 는 요청 100,000/일 · 호출당 CPU 10ms 이고, Cron Trigger 는 분 단위 cron 식으로 `scheduled()` 를 돈다.
KV Free 는 읽기 100,000/일 · **쓰기 1,000/일** 이다 — Alertmanager 가 1분마다 ping 을 쓰면 1,440/일로 넘친다. 2분 주기(720/일)면 들어간다.
출처: [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) · [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
코드를 소유하게 되고, 실패 도메인은 역시 Cloudflare 다.

**AWS Route 53 Health Check — 바깥 HTTP 탐침.**
비 AWS 엔드포인트 "$0.75 per health check per month", 선택 기능(HTTPS·문자열 일치·빠른 주기·지연 측정)은 "$2.00 per optional health check feature per month".
HTTPS 하나만 켜도 월 $2.75 다.
출처: [Route 53 pricing](https://aws.amazon.com/route53/pricing/).
결과는 CloudWatch 알람으로만 나오고, Discord 로 가려면 SNS → Lambda 가 하나 더 필요하다.

**AWS CloudWatch 알람 + Lambda — 직접 만드는 심장박동.**
Alertmanager → Lambda 함수 URL → `PutMetricData`, 알람은 missing data 를 breaching 으로 두면 침묵을 잡는다.
커스텀 메트릭은 무료 10개 · 이후 $0.30/개, 표준 알람은 무료 10개 · 이후 $0.10/개, Lambda 는 "one million requests and 400,000 GB-seconds per month" 무료.
출처: [CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/) · [Lambda pricing](https://aws.amazon.com/lambda/pricing/).
비용은 0 에 가깝지만 Lambda 둘(수신·Discord 발송)·IAM·알람을 코드로 소유한다.
CloudWatch Synthetics 는 무료 100 run/월 뒤 유료라 5분 주기(월 8,640 run)엔 맞지 않는다.

### 7. 자가 호스팅 — 집 밖의 작은 기계

**Uptime Kuma.** Push 모니터는 `/api/push/<pushToken>` 로 받고 메서드는 무관하다.
`interval`·`retryInterval`·`resendInterval` 필드가 있다.
출처: [wiki — Internal API](https://github.com/louislam/uptime-kuma/wiki/Internal-API) · 3자 설정 예: [borgmatic docs](https://torsion.org/borgmatic/reference/configuration/monitoring/uptime-kuma/).
공식 Push 문서 페이지는 조사에서 찾지 못했다.

**Gatus.** "a developer-oriented health dashboard ... using HTTP, ICMP, TCP, and even DNS queries".
알림은 Discord·Telegram·ntfy·Pushover·이메일 등.
`external-endpoints[].heartbeat.interval` 이 심장박동이다 — "If no update is received within this interval, alerts will be triggered." 최소 10s.
출처: [Gatus README](https://raw.githubusercontent.com/TwiN/gatus/master/README.md).

**Healthchecks 자가 호스팅.** "Healthchecks provides a reference Dockerfile and prebuilt Docker images for every release." TLS 종단은 안 한다.
출처: [README](https://raw.githubusercontent.com/healthchecks/healthchecks/master/README.md).

셋 다 **놓을 곳**이 문제다.
집 밖 VPS 가격은 이번에 조사하지 않았다.
AWS 에 EC2 를 하나 두면 `lab/vpn` 이 이미 그 모양을 갖고 있지만(`workspace/ref/jyoliar-platform-terraform/lab/vpn/main.tf`), 상시 인스턴스는 무료 티어 밖이다.
"Free, but it's two things to patch" — 두 번째 Kuma 를 권하는 글조차 유지 부담을 적는다([dev.to tanod](https://dev.to/tanod/who-monitors-your-uptime-kuma-three-ways-to-watch-the-watcher-146f)).

### 8. 홈랩 쪽 배선 — Alertmanager 가 바뀌는 양

지금 Watchdog 은 `alertname = Watchdog` 매처로 `info-slack-notifications`(Discord) 에 `repeatInterval: 24h` 로 간다 — `workspace/ref/jyoliar-k8s/gitops/overlays/baremetal/system/prometheus-config/alertmanagerconfig.yaml`.
바깥 수신처로 분 단위로 보내려면 다음 사실이 걸린다.

- `route.continue` — 기본 `false`. "Whether an alert should continue matching subsequent sibling nodes." 심장박동 라우트를 Watchdog 라우트 앞에 두고 `continue: true` 로 하면 Discord 24h 라우트도 살아남는다.
- `repeat_interval` — 기본 `4h`. "Since the repeat_interval is checked after each group_interval, it should be a multiple of the group_interval." 분 단위 심장박동이면 그 라우트의 `group_interval` 도 같이 낮춘다. 3자 예시는 `group_wait: 0s` · `repeat_interval: 1m` 을 쓴다.
- `webhook_config.url` — "The endpoint to send HTTP POST requests to." ping URL 은 비밀이라 Secret 참조로 넣는다.
- 출처: [Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/) · [cos-alerter 예시](https://pypi.org/project/cos-alerter/).

변경은 AlertmanagerConfig 에 라우트 하나·receiver 하나를 더하는 것이고 룰은 건드리지 않는다.
바깥 HTTP 탐침은 홈랩 쪽 변경이 0 이다.

### 9. 코드로 선언할 수 있나

| 대상 | terraform | 출처 |
|---|---|---|
| Cloudflare 알림 정책 | 공식 provider `cloudflare_notification_policy` | [docs](https://raw.githubusercontent.com/cloudflare/terraform-provider-cloudflare/master/docs/resources/notification_policy.md) |
| Better Stack | `BetterStackHQ/better-uptime` — 자사 org 소유 · `betteruptime_monitor`. heartbeat 리소스명은 README 에 없음 | [README](https://raw.githubusercontent.com/BetterStackHQ/terraform-provider-better-uptime/master/README.md) |
| Healthchecks.io | `kristofferahl/healthchecksio` — 커뮤니티 provider · "A provider used to manage Healthchecks.io resources." | [README](https://raw.githubusercontent.com/kristofferahl/terraform-provider-healthchecksio/master/README.md) |
| AWS | 공식 provider | — |
| UptimeRobot · Cronitor · Dead Man's Snitch | 미조사 | — |

### 10. 출처의 신뢰도

가격·무료 티어는 3자 비교 사이트(대개 경쟁사 마케팅·자동 생성 페이지)가 서로 다른 수치를 낸다.
위 표는 공식 페이지에서 직접 읽은 것을 우선했고, 3자 출처만 있는 칸은 그렇게 적었다.
무료 티어는 2026년 중에도 바뀌었다(Healthchecks.io SMS) — 어느 것을 고르든 가입 시점에 다시 확인해야 한다.

## 논의 문서로 가져가는 것

- 기존 알럿은 전부 white-box 다. 바깥에서 보는 black-box 몫은 비어 있고, SRE 관행은 그 몫을 "modest but critical" 로 둔다.
- 심장박동은 인터넷 단절·클러스터 소실·관측 스택 고장을 한 신호로 잡고, 공개 경로만 끊긴 경우를 놓친다. 바깥 탐침은 그 반대다. 홈랩 사례들은 둘을 함께 둔다.
- 집안의 다른 기기는 독립 실패 도메인이 아니다 — 공유기가 엣지다(kubelab #1021).
- Cloudflare Tunnel Health Alert 는 무료·설치 없음·Discord webhook 가능·terraform 선언 가능하고, 터널 Down 은 심장박동 침묵과 거의 같은 뜻이다. 단, Down 판정 지연은 미확인이고 Cloudflare 와 실패 도메인을 공유한다.
- Cloudflare Health Checks 는 Pro(월 $20~25) 라 예산 밖이다.
- 무료 SaaS 심장박동은 Healthchecks.io(20 checks) 가 가장 넓고, Better Stack(10 합산·3분 탐침) 은 심장박동과 탐침을 한 계정에 둔다. Dead Man's Snitch 는 1개, UptimeRobot 은 heartbeat 유료.
- 무료 SaaS 탐침은 UptimeRobot 50개/5분, Better Stack 10개/3분, Cronitor 5개/5분. 5~15분 탐지 목표에 전부 들어온다.
- AWS 로 직접 만들면 비용은 0 에 가깝지만 Lambda·알람·IAM 을 소유한다. Route 53 HTTPS 탐침은 월 $2.75 이고 Discord 로 가려면 Lambda 가 더 필요하다.
- Alertmanager 변경은 라우트 하나(`continue: true` · 낮은 `group_interval`/`repeat_interval`)와 webhook receiver 하나다. 룰은 안 바뀐다. Healthchecks.io 는 POST 를 받고 분당 5회까지다.
- Discord 통합이 무료 티어에서 열려 있는가(Healthchecks.io·Better Stack)는 가입해야 닫힌다.
