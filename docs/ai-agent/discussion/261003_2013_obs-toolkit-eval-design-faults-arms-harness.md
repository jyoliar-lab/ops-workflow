---
type: discussion
topic: ai-agent
subjects: [obs-toolkit, claude-code, careerhub-prod, argocd, prometheus, loki, tempo]
status: active
ref-adrs: []
tickets: [92, 96, 97, 98, 102]
related: [261003_1949_obs-toolkit-troubleshooting-eval.md, 260817_1512_subscription-auth-programmatic-claude-access.md]
---

# obs-toolkit 측정 설계 — 장애 종류 · 주입 · 비교군 · 하네스

## 0. 이 문서의 자리

`261003_1949` 가 *무엇을 재고 왜 층 기여인가* 를 정했다 — 층 기여는 한 층을 더했을 때 바로 아래 arm 보다 얼마나 더 맞혔나다.
이 문서는 그 §4(시나리오) · §5(러너) 를 **설계 네 항목**으로 내린다 — 사람이 낸 순서 그대로.

1. 문제로 낼 장애 종류
2. 장애 주입 방법
3. 비교군 — 미포함 / base 층 / 응용 층 / `investigate_bundle` 층
4. 실행 하네스 — obs-toolkit 의 성능**만** 재기 위한 환경

전제는 앞 문서에서 넘어온 둘이다 — prod 주입 가능(외부 제공 아님) · 구독제 `claude -p` 로 토큰·창 소모 측정 가능(§5-1 실측).
티켓은 내지 않는다 — 사람이 "아직 Task 단계가 아니다" 라고 했다.

## 1. 실측 — 설계가 기대는 사실

전부 오늘(10-03) 읽거나 돌린 것이다.

### 1-1. 트래픽이 거의 없다 — 가장 큰 제약

| 질의 | 결과 |
|---|---|
| `group by (job) (up)` | careerhub 앱 job 이 **없다** — 앱은 Prometheus 에 직접 스크레이프되지 않는다 |
| `count by (__name__) ({service_name=~"posting-service\|api-composer\|…"})` | `traces_span_metrics_calls_total` · `traces_span_metrics_duration_seconds` 140 시리즈 — **RED 는 spanmetrics 로만** 있다. 이름은 `traces_span_metrics_*` — Alloy 설정의 connector 이름에서 짐작한 `traces_spanmetrics_*` 로는 안 잡힌다. toolkit 은 아직 이 이름을 어디에도 적지 않았고, #102 `red` 가 처음 박게 된다 |
| `traceql.py search --since 72h` | 트레이스는 **10-01 19:19–19:39 에만** — posting-service `ProviderGrpc` · `ScannerGrpc`, review-service `crawler_grpc` |
| `kubectl get cronjob -n careerhub-prod` | `posting-provider-jumpit` · `posting-provider-wanted`(19:09) · `posting-skillscanner` · `review-crawler`(19:39) — 하루 한 번 |
| 로그 24h | `careerhub-mongodb-svc` 외에는 사실상 0 |
| cAdvisor CPU | 앱 파드 전부 ~0.0005 core |

**뜻**: HTTP 경로(gateway → frontend → api-composer → gRPC 셋)는 요청이 **0** 이다.
거기에 고장을 심어도 RED · 로그 · 트레이스 어디에도 증상이 안 찍힌다 — 보이는 것은 kube-state(restart · replicas)와 cAdvisor 뿐이다.
배치 경로(cron → posting/review-service → mongo/postgres)는 **하루 한 번** 증상이 찍힌다.
**트래픽 없는 장애는 문제가 아니다** — 주입 설계(§3)에 부하 생성이 들어간다.

### 1-2. GitOps 가 주입을 되돌린다

`careerhub-prod-appset.yaml:49-50` · `apps/careerhub-prod-apps-appset.yaml:74-75` — **`selfHeal: true`**(apps 는 `prune: false`).
`kubectl patch deploy` 로 심은 고장은 Argo CD 가 **되돌린다**.
Application 의 syncPolicy 를 끄는 것도 ApplicationSet 이 다시 덮는다.
주입은 **git 을 거치거나**, **Argo 가 모르는 층**(파드 안 · DB 안)이거나, **Argo 를 잠시 멈추고** 해야 한다.
**사람의 답(10-03): 주입 창 동안 `argocd-application-controller` 의 replica 를 0 으로 둔다.**
controller 가 없으면 되돌릴 주체가 없다 — ApplicationSet 이 syncPolicy 를 덮는 문제도 같이 사라진다(덮는 쪽도 controller 다).
그러면 `kubectl patch` 로 limit · env · image 를 바로 바꿀 수 있어 M1(git 커밋)은 선택이 된다.

### 1-3. 층 경계는 CLI 서브커맨드에 있다

`obs/adapters/cli.py`:

| 층 | 명령 | 어디 |
|---|---|---|
| **base** — 원본 조회(요약 + spill) | `promql.py '<q>'` · `--range` · `--labels` · `--series`, `logql.py '<q>'`, `traceql.py search\|trace\|tags\|tag-values` | `promql_main` L376 · `logql_main` L674 · `traceql_main` L987 |
| **응용** — 환원 연산 | `promql.py summarize\|compare\|top`(L517), `logql.py histogram\|templates\|around\|first-seen`(L835), (#96) `traceql.py exemplars\|critical_path\|…`, (#102) `red` | 같은 shim, 서브커맨드로 분기 |
| **조사** — `obs-investigate` | #97 · #98 — 아직 없다 | |

한 shim 안에서 서브커맨드로 갈리므로 층을 나누는 것은 **플러그인을 바꾸는 것이 아니라 허용 명령을 바꾸는 것**이다(§4).

### 1-4. headless 격리 수단 (Claude Code 2.1.288 `--help`)

- `--bare` 는 구독 OAuth 를 **읽지 않는다**(API 키 전용) — 구독 전제와 충돌, 못 쓴다.
- `--safe-mode` — CLAUDE.md · 스킬 · 설치 플러그인 · hook · MCP · 메모리 전부 끔, **인증·권한·내장 도구는 정상**. 단 `--plugin-dir` 가 safe-mode 에서 로드되는지 **미확인**.
- `--setting-sources user,project,local` 로 설정 출처 선택 · `--settings <file>` 로 arm 별 env · 권한 주입 · `--strict-mcp-config`.
- `--plugin-dir` · `--allowedTools` · `--disallowedTools`(`Bash(promql.py summarize:*)` 꼴) · `--append-system-prompt-file` · `--json-schema` · `--model` · `--max-turns` · `--max-budget-usd`.
- `CLAUDE_CONFIG_DIR` 로 설정 디렉터리를 비울 수 있고, 그때 로그인은 `CLAUDE_CODE_OAUTH_TOKEN`(`claude setup-token`)으로 넣는다(`260817_1512`).

### 1-5. 그 밖에

- ~~NetworkPolicy 가 careerhub 매니페스트에 없다 → 추가 객체로 심으면 Argo 가 지우지 않는다.~~ **사람의 답(10-03): CNI 가 Flannel 이라 NetworkPolicy 가 집행되지 않는다.** 객체는 만들어지되 아무 효과가 없다 — 끊김 주입은 다른 층이 필요하다(§3 "끊김").
- 파드 netns 층은 열려 있다 — `careerhub-prod` 에 Pod Security 라벨이 없고 posting-service 의 securityContext 가 비어 있다. `kubectl debug --profile=netadmin`(k8s 1.34 · kubectl 1.35)으로 ephemeral container 를 붙이면 그 파드의 netns 안에서 `iptables` · `tc` 가 선다 — CNI 와 무관하다. 단 agent SA 는 `pods/ephemeralcontainers` · `pods/exec` 둘 다 거부(`kubectl auth can-i`)이므로 사람의 kubeconfig 로만.
- mongo 의 사용자 · Service 는 **MongoDBCommunity operator 소유**다(`replicaset.yaml` `users:` · Service ownerRef = MongoDBCommunity). 사용자 권한 · Service selector 를 손으로 바꾸면 operator 가 되돌릴 가능성이 크다 — 미확인. `fsyncLock` 은 automation config 밖이라 남는다.
- `promql.py compare` 의 기본 기준선은 `1d` — **어제 같은 시각**이 기준이다. 이틀 연속 같은 시각에 주입하면 기준선이 오염된다.
- 토큰은 `OBS_GRAFANA_TOKEN` env 로만, 게이트웨이는 GET 만(코어 · 서버 이중).
- kubeconfig 는 `agents:ops-workflow-agent` SA — 클러스터 전역 읽기, Secret 값 · 쓰기 거부.

## 2. ① 장애 종류

### 설계 원칙

문제 집합은 "흔한 장애 목록" 이 아니라 **채점 축을 하나씩 켜는 집합**이어야 한다.
`261003_1949` §2 의 축과 #97 `correlations` 의 네 검사(시각 일치 · 서비스 일치 · 파드 일치 · 대응 신호 부재)가 기준이다.

- **신호 하나짜리** — 메트릭에만 · 로그에만 · 트레이스에만 보이는 장애가 각각 하나.
- **신호 교차짜리** — 셋이 같은 시각 · 같은 서비스를 가리키는 장애.
- **증상과 원인이 떨어진 것** — 원인은 DB, 증상은 두 홉 위 서비스. 임계경로 · 의존 추적이 없으면 못 푼다.
- **없음 vs 0** — 신호가 *끊긴* 장애(수집기 고장). "판정 불가" 를 말할 줄 아는지.
- **배포 모양 vs 보이지 않는 주입** — k8s API 에 흔적이 남는 것(이미지 · env 변경)과 안 남는 것(DB 안 · 파드 안). 전자는 `kubectl` 만으로 풀릴 수 있어 층 기여 가 작게 나온다 — 그것도 결과다.
- **clean** — 아무 것도 없는 창. 정밀도의 유일한 척도.

### 후보 — 배치 경로 중심(§1-1)

| id | 장애 | 주입(§3 참조) | 기대 증상 — metrics / logs / traces / k8s | 켜는 축 |
|---|---|---|---|---|
| **F0 clean** | 없음 | 아무 것도 안 한다 | 평소 | 정밀도 |
| **F1 crash** | posting-service 가 뜨자마자 죽는다 | M1 — 잘못된 `MONGO_URI` 키 이름 또는 `RUN_MODE` 오타 | restarts↑ / 기동 오류 템플릿 / 없음 / CrashLoopBackOff | 로그·k8s 교차. **배포 모양** |
| **F2 dependency** | posting-service → mongo 끊김 | M2 — posting-service 파드 netns 에서 mongo 포트 DROP(§3 "끊김") | calls 유지 · error↑ / 연결 오류 템플릿 첫 발생 / 오류 span / deploy 는 안 바뀜 — ephemeral container 만 파드 spec 에 남는다 | 시각 · 서비스 · 파드 일치. **보이지 않는 주입**(흔적은 §3 참조) |
| **F3 latency** | posting-service 느려짐, 오류 없음 | M1 — CPU limit 을 50m 로 | duration p95↑ · throttling↑ / 없음 / 임계경로가 posting-service self time / 변경 generation | 트레이스 축. "오류율은 그대로" 를 말하는지 |
| **F4 far cause** | mongo 가 느리고 증상은 posting-service | M2 — mongo 에 `fsyncLock` | posting-service duration↑ / posting 쪽은 조용, mongo 로그에 slow query / 임계경로가 **mongo span** / 흔적 없음 | 원인-증상 분리. #96 `critical_path` 의 존재 이유 |
| **F5 absence** | 트레이스 수집이 멎음 | M1 — Alloy 를 0 으로 (또는 OTLP endpoint env 오타) | spanmetrics 끊김(0 이 아니라 **없음**) / 앱 로그 정상 / 검색 결과 0 / alloy 파드 수 0 | 없음 vs 0 · "판정 불가" |
| **F6 deploy regression** | 잘못된 이미지 태그로 배포 | M1 — `POSTING_SERVICE` 이미지 태그를 존재하지 않는 것으로 | 없음 / 없음 / 없음 / ImagePullBackOff · ReplicasMismatch | `kubectl` 만으로 풀린다 — 층 기여 의 **하한** 측정용 |

첫 라운드는 **F0 · F2 · F3 · F4 네 개**가 맞다.
F1 · F6 은 k8s 가 답을 말해 줘서 도구의 층 기여 가 안 보이고, F5 는 #97 의 "판정 불가" 가 생긴 뒤 의미가 있다.
F2 · F4 가 "보이지 않는 주입" 이라 **도구가 없으면 못 푸는 문제**다 — 층 기여 가 가장 크게 벌어질 자리이고, 벌어지지 않으면 도구가 틀린 것이다.

HTTP 경로(api-composer · auth · zitadel · frontend)는 부하 생성기가 생긴 뒤 둘째 라운드로.

## 3. ② 장애 주입 방법

### 기제 — Argo 와의 관계로 갈린다

| 기제 | 무엇 | Argo | 흔적 | 되돌리기 |
|---|---|---|---|---|
| **M1 git** | `jyoliar-k8s` prod overlay 에 커밋 → Argo sync | 통과 | deploy generation · 이벤트 · git log — **배포 모양** | `git revert` → sync. 분 단위 |
| **M2 Argo 가 모르는 층** | 파드 netns(`kubectl debug --profile=netadmin` + `iptables` · `tc`) · DB 클라이언트(`mongosh` · `psql`)로 DB 안 조작 · cron 을 `kubectl create job --from=cronjob/…` 로 손 실행 | 안 본다(DB 안 · netns 는 Argo 밖) | deploy 안 바뀜. ephemeral container 는 파드 spec · 이벤트에 보인다 | 규칙 삭제(`iptables -D` · `tc qdisc del`) · `fsyncUnlock` |
| **M3 controller 0 + patch** | `kubectl scale sts argocd-application-controller -n argocd --replicas=0` → `kubectl patch`(limit · env · image) → 창 끝에 되돌리고 replica 복구 | 멈춰 있다 — 되돌릴 주체가 없다 | deploy generation · 이벤트 — M1 과 같은 **배포 모양**. 더해서 argocd 파드 수 0 이 kube-state 에 보인다 | 역 patch → controller 복구. **복구를 잊으면 클러스터 전체가 drift 한다** — 스크립트의 `off` 가 둘 다 한다 |

### 끊김 — NetworkPolicy 없이

Flannel 은 NetworkPolicy 를 집행하지 않는다(§1-5).
"posting-service 만 mongo 에 못 닿는다" 를 만드는 길은 넷이고, 첫 라운드는 첫째다.

| 길 | 어떻게 | Argo · operator | 흔적 | 메모 |
|---|---|---|---|---|
| **netns 규칙**(택) | `kubectl debug -n careerhub-prod <posting pod> --image=nicolaka/netshoot --profile=netadmin -- sh -c 'iptables -I OUTPUT -p tcp --dport 27017 -j DROP; sleep 1200'` — 같은 수단으로 `tc qdisc add … netem delay 300ms` 면 **지연** 주입도 된다 | 둘 다 모른다 | ephemeral container 가 파드 spec(`ephemeralContainers`) · 이벤트(`Started container debugger`)에 남는다. 파드가 재시작되면 사라진다 | CNI 무관. `off` 는 규칙 삭제 또는 sleep 만료. **노드가 아니라 그 파드의 netns 다** — 표 아래 |
| **DNS 블랙홀** | CoreDNS `hosts` 로 `careerhub-mongodb-svc…` 를 잘못된 주소로 | CoreDNS 가 Argo 관리면 M1 이 된다 — 미확인 | 네임스페이스 전체 · 다른 소비자까지 영향 | #80 이 보여준 CoreDNS 의 취약성 위에 올리는 것이라 **버린다** |
| **mongo 쪽 거부** | `updateUser` 로 `authenticationRestrictions`(clientSource) 또는 역할 회수 | operator 가 automation config 로 사용자를 **되돌릴 가능성** — 미확인 | k8s 흔적 0 | 되돌림이 확인되면 버린다. 안 되돌리면 가장 깨끗한 "보이지 않는 주입" 이다 |
| **Chaos Mesh** | NetworkChaos(partition · delay) · PodChaos · StressChaos 를 CR 로 | 설치는 M1(git). CR 자체는 Argo 밖 | daemon 이 특권으로 돈다 | CNI 무관 · 선언적 · 되돌리기 = CR 삭제. **둘째 라운드 이후** 평가가 반복될 때 — 첫 라운드엔 설치가 더 크다 |
| M1 로 후퇴 | `MONGO_URI` 호스트를 틀리게 커밋 | 통과 | **배포 모양** — "보이지 않는 주입" 을 잃는다 | 위가 전부 막힐 때만 |

netns 규칙은 **워커 노드에 거는 장애가 아니다.**
ephemeral container 는 대상 파드의 network namespace 를 공유하므로 규칙은 그 파드의 커널 netns 에만 산다 — 같은 노드의 다른 파드 · 노드 호스트 netns 는 그대로다.
노드 호스트 netns 에 거는 것은 다른 장애(그 노드 위 전부가 끊긴다)이고, 둘째 라운드의 "노드 수준" 후보다.
사람의 말대로 **찾기 어려운 문제**다 — `kubectl get` 으로는 deploy · replicas · restart 어디에도 변화가 없고, `describe pod` 의 ephemeral container 한 줄과 관측 데이터만 말한다.
변형 하나가 공짜다 — posting-service 파드 둘 중 **하나에만** 걸면 오류가 한 파드에 몰린다.
#97 의 "파드 일치" 검사(③ histogram by pod 와 ⑤ 오류 트레이스의 파드)를 켜는 문제이고, 둘 다 걸면 "서비스 일치" 문제다.

**주입은 언제나 사람이 한다** — agent SA 는 읽기 전용이다.
다만 "손 kubectl" 이 아니라 **스크립트**로 한다 — `on`/`off` 두 동작, 실행하면 truth 가 떨어진다.

```
inject/F3-latency.sh on   → kubectl/git 조작 + cases/F3/truth.yaml 에 {target, kind, since} 기록
inject/F3-latency.sh off  → 되돌리고 until 기록
```

truth 는 주입한 손이 쓴다 — 사람이 따로 적으면 시각이 어긋난다.

### 부하 — 트래픽이 없으면 장애도 없다(§1-1)

처음엔 cron(`posting-provider-*`)을 `kubectl create job --from=cronjob/…` 로 당기려 했다.
사람이 물었다(10-04) — "간단한 호출은 curl 로 만들어도 되지 않나".
확인했다: 게이트웨이(`careerhub.jyo-liar.com`)의 인증 없는 GET `/api/categories` 한 번이 **gateway → api-composer → posting-service gRPC(`RestApiGrpc/Categories`)** 로 이어지는 트레이스를 남긴다(span 4 · 20ms).
장애를 심는 층(posting-service → mongo)에 닿는다.

| 수단 | 판정 |
|---|---|
| **`curl` 루프**(택) | 외부 사이트에 요청이 안 간다 · rps 와 길이를 정한다 · 장애마다 같은 모양. `inject/load.sh --rps N --minutes M` 가 인증 없는 GET 셋(`/api/categories` · `/api/job_postings` · `/api/job_postings/count`)을 섞어 던진다 |
| cron 손 실행 | wanted · jumpit 에 실제 요청이 간다. 버린다 |
| k6 | `curl` 로 충분한 동안은 아니다 |

이로써 §1-1 의 "HTTP 경로는 요청 0" 은 제약이 아니라 **통제 변수**가 된다 — 평소 0 이라 부하는 전부 하네스가 만든 것이고, 모양이 같다.

### 창 규약 — 주입과 실행을 분리한다

1. **기준선 확보** — 주입 하루 전 같은 시각이 깨끗해야 한다(`compare` 기본 `1d`). 같은 시각에 이틀 연속 주입하지 않는다.
2. `on` → 부하 → **20분 유지** → `off`. truth 에 `since` · `until`.
3. 실행은 그 뒤 **72시간 안**(Tempo retention) 언제든 — 프롬프트에 창(`since`–`until`)을 **절대 시각으로** 준다.
4. 같은 장애의 arm 4 × 시도 3 = 12 세션이 **같은 데이터**를 본다 — 라이브 분산이 사라진다.

창을 절대 시각으로 주는 것은 "지금 이상하다" 보다 쉬운 문제다.
그래도 이렇게 가는 이유는 **재현성**이다 — 12 세션이 다른 데이터를 보면 arm 비교가 아니라 시각 비교가 된다.
어려운 변형("지난 1시간, 지금") 은 코퍼스가 안정된 뒤 난이도 축으로 더한다.

### 알럿

주입 창마다 Alertmanager silence 를 건다 — Discord 에 가짜 장애가 쌓이는 것을 막는다. Alertmanager 의 접근 경로는 arm 쪽 어디에도 적지 않는다.

## 4. ③ 비교군

### arm 넷

| arm | agent 가 가진 것 | 재는 것 |
|---|---|---|
| **A0 미포함** | `kubectl`(읽기 SA) + `curl` + 게이트웨이 접근 정보(env 로 URL · 프록시 prefix · uid · 토큰) | 모델의 바닥. 데이터 접근은 **같다** — 없는 것은 코어뿐 |
| **A1 base** | A0 + `promql.py '<q>'` · `logql.py '<q>'` · `traceql.py search\|trace\|tags` | base 층의 층 기여 — A1 이 A0 보다 더 맞힌 만큼(spill · 요약 · 논리 이름) |
| **A2 응용** | A1 + `summarize\|compare\|top` · `histogram\|templates\|around\|first-seen` · (#96 · #102 뒤) `critical_path` · `red` | 응용 층의 층 기여 — A2 가 A1 보다 더 맞힌 만큼(환원 연산) |
| **A3 조사** | A2 + `obs-investigate`(#97 · #98 뒤) | 조사 층의 층 기여 — A3 가 A2 보다 더 맞힌 만큼(고정 순서 번들 + fork 격리) |

A0 에 게이트웨이 접근을 주는 것이 핵심이다.
안 주면 base 층의 층 기여는 "데이터를 볼 수 있나" 의 차이가 되고, 그건 도구의 가치가 아니라 **권한의 가치**다.
A0 의 `curl` 은 GET 만 통과하는 게이트웨이를 그대로 치므로 쓰기 위험은 없다.

### 층을 어떻게 가르나 — 빌드로, 권한으로가 아니라

처음엔 권한(`permissions.deny`) + SKILL 변형 + help 일치 셋으로 가르려 했다.
사람이 바로잡았다(10-04) — **하위 층 arm 은 상위 층의 기능을 아예 몰라야 한다.**
권한으로 가리면 "있는데 못 쓰는" 상태다: agent 가 `--help` 에서 보고 시도하면 그 턴과 토큰은 도구의 비용이 아니고, 거부 메시지가 상위 층의 존재를 알린다.
그러므로 arm 플러그인은 **상위 층의 코드 · 서브커맨드 · SKILL 줄이 물리적으로 없는 빌드**이고, `permissions.deny` 에는 toolkit 명령이 들어가지 않는다(공통 금지 — WebFetch · WebSearch · git — 만).

코드를 읽으면 경계는 얇다 — `promql_main` 이 `argv[0] in METRICS_SUBCOMMANDS` 면 `metrics_main` 으로 넘기고, 응용 층은 `obs/metrics.py` · `obs/logs.py` 와 `cli.py` 안의 `metrics_main` · `logs_main` 이다.
그러나 `cli.py` 가 `obs.metrics` · `obs.logs` 를 모듈 수준에서 import 하므로 **파일 삭제만으로는 base-only 가 안 나온다.**

| 길 | 어떻게 | 문제 |
|---|---|---|
| **과거 sha** | A1 = `0bd2737`(#4 metrics 이전 — base 만 있던 시점) | base 도 그 뒤 바뀌었다(spill 형식 · raw list · OBS_CONFIG · 404). A2 와의 차에 base 의 변화가 섞인다 — 교란. **스파이크의 조립 확인에만** 쓴다 |
| **toolkit 쪽 층별 패키징**(택) | base 가 응용을 import 하지 않게 모듈을 가르고(`cli.py` 는 base, 응용은 별도 모듈), 응용은 "있으면 등록". arm 빌드는 **파일 삭제만**으로 변형을 낸다 | obs-toolkit 리팩토링 — #92 밑 새 리프. 그 전엔 라운드의 A1 이 없다. #115 의 선행 |

arm 플러그인 디렉터리는 손으로 만들지 않는다 — `arms/build.sh` 가 pin 한 sha 에서 **지워서** 만든다(파일 + SKILL 표의 줄).
지울 목록은 toolkit 의 층 경계(모듈 · 매니페스트)에서 도출한다 — 손으로 나열하면 #96 · #102 가 들어올 때 낡는다.

### arm 사이에서 **같아야** 하는 것

| | 값 |
|---|---|
| 모델 | 고정 id 하나(alias 아님 — 라운드 중 바뀌지 않게) |
| 프롬프트 | 같은 문장 — 네임스페이스 · 창(절대 시각) · "원인 컴포넌트 · 시각 · 근거를 아래 스키마로" |
| 출력 계약 | `--json-schema` 로 같은 Finding 스키마(§6) |
| `kubectl` · `Agent` 도구 · `Read`/`Grep`(작업 디렉터리 안) | 전부 허용 — 호스트의 것이지 도구의 것이 아니다 |
| `--max-turns` · `--max-budget-usd` · timeout | 같다. 상한에 걸린 시도는 "미완" 으로 따로 센다 |
| 금지 | WebFetch · WebSearch · git · `jyoliar-k8s` 저장소 · 다른 시도의 `tmp/obs` · evals 디렉터리 자체 |

**Finding 규칙(`prompts/finding.md`)은 어느 arm 의 것인가** — 미결.
스키마는 채점을 위해 공통이어야 한다.
그러나 "신호 둘 이상 일치 → high" 같은 **규칙**은 toolkit 의 산출물(#97)이다.
A0 에 주면 도구의 가치 일부를 대조군에 넘기는 것이고, 안 주면 A0 의 보정 점수가 규칙 부재 때문에 낮게 나온다.
제안 — **스키마만 공통, 규칙은 A2 부터**. 그리고 보정 축은 A2 를 A1 과 비교하는 대신 "규칙만 준 A1" 과 비교해 한 번 더 가른다(둘째 라운드).

## 5. ④ 실행 하네스 — obs-toolkit 만 변하게

### 무엇을 빼야 하나

지금 이 저장소에서 agent 를 돌리면 함께 실리는 것 — `CLAUDE.md`(§1~§8) · `context-scout` 등 스킬 · `design-partner` agent 정의 · hook · 메모리 · `settings.local.json` 의 다른 env.
이 중 어느 것도 obs-toolkit 이 아니다.
**평가 세션은 빈 디렉터리에서, 빈 설정으로, 플러그인 하나만 얹고 돈다.**

### 저장소 — `jyoliar-lab/obs-bench`

평가 하네스는 obs-toolkit 안의 `evals/` 가 아니라 **별도 저장소**다(사람의 답 · 10-04 생성).
이유는 둘이다 — obs-toolkit 은 피평가물이라 평가 코드가 섞이면 arm 을 만들 때 자기 자신을 잘라내야 하고, 주입 스크립트 · 결과 디렉터리는 플러그인의 것이 아니다.
아래 경로는 전부 obs-bench 루트 기준이다.

| 디렉터리 | 무엇 |
|---|---|
| `arms/` | `build.sh`(obs-toolkit 을 pin 해 arm 플러그인 생성) · arm 별 `settings.json` · 생성된 `plugin/` |
| `control/inject/` | 장애별 `on/off` 스크립트 — Argo controller 0/복구 · netns 규칙 · `fsyncLock` · `load.sh`(curl 부하) · silence |
| `control/cases/` | 장애별 `truth.yaml`(주입이 쓴다) · 프롬프트 |
| `frame.md` · `finding.schema.json` | 공통 과제 틀 · Finding 스키마 |
| `run.sh` · `grade.py` | 러너 · 채점 |
| `control/` | 제어 트리 — `inject/` · `cases/`(truth). arm 세션은 여기를 모른다 |

**작업 트리는 저장소 밖, 형제 디렉터리다**(사람의 결정 · 10-04) — `../obs-bench-runs/<case>/<arm>/<n>/work`, arm 플러그인은 `../obs-bench-arms/<arm>/`.
세션의 cwd · 플러그인 · settings · frame 어디에도 제어 트리를 가리키는 경로 · 이름("모의" · "평가" · "truth" · "주입" · Alertmanager 경로)이 없다.
권한으로 막지 않는다 — 그 구현은 지나치게 복잡하고(컨테이너 · 샌드박스 · egress), 우연한 발견은 당장 감안한다.
**존재를 알 수 없게 유도**하는 것이 설계다. agent 는 실환경이라고 가정한 채 답한다 — frame 은 운영 중 실제로 올 요청의 문장으로 끝난다.

obs-toolkit 은 **sha 로 pin** 한다 — "어느 toolkit 을 쟀나" 가 결과의 일부다. #98 이 하네스에 요구하는 pin 과 같은 모양이다.

### 조립

```
CLAUDE_CONFIG_DIR=$RUN/config          # 빈 설정 — 메모리 · 사용자 settings · 설치 플러그인 없음
CLAUDE_CODE_OAUTH_TOKEN=…              # claude setup-token — 구독으로 로그인(260817_1512)
cd $RUN/work                           # 빈 작업 디렉터리 — CLAUDE.md 없음 · tmp/obs 가 여기 떨어진다
claude -p "$(cat prompt/F3.md)" \
  --settings arms/A2/settings.json \     # env(OBS_GRAFANA_TOKEN · KUBECONFIG) + 공통 금지(permissions.deny — toolkit 명령은 없다)
  --plugin-dir arms/A2/plugin \          # 생성된 arm 플러그인(A0 는 생략)
  --append-system-prompt-file frame.md \ # 과제 틀 + Finding 스키마 설명
  --json-schema finding.schema.json \
  --model <고정 id> --max-turns 40 --max-budget-usd 5 \
  --strict-mcp-config --setting-sources "" \
  --output-format stream-json --verbose > $RUN/stream.jsonl
```

시도 하나 = 디렉터리 하나(`results/<case>/<arm>/<n>/`, obs-bench): `stream.jsonl` · `result.json` · `work/tmp/obs/`(spill) · `$CLAUDE_CONFIG_DIR/projects/…/*.jsonl`(전사).
전사는 채점(도구 호출 열 · 거부된 호출 수 · subagent 사용)의 원자료다.

### 미확인 — 스파이크가 답할 것

1. `CLAUDE_CONFIG_DIR` 를 비웠을 때 `CLAUDE_CODE_OAUTH_TOKEN` 으로 구독 로그인이 되나.
2. `--setting-sources ""` 가 user settings 를 실제로 끄나(`--safe-mode` 와 `--plugin-dir` 의 공존 여부도).
3. base 층만 있는 플러그인 변형이 파일 삭제만으로 만들어지나 — 지금 구조로는 아니다(위). 스파이크는 과거 sha 로 조립만 확인하고, 가를 파일 · 함수 목록을 낸다.
4. `--json-schema` 출력이 Finding 스키마대로 나오나 — 그리고 A0 처럼 도구 없는 arm 에서도.
5. 플러그인 hook(`session-env.sh`)이 `--plugin-dir` 경로에서 PATH 를 올리나(#93 에서 bare name 실행은 확인됐으나 headless + 빈 config 에서는 아니다).
6. `claude plugin eval` 을 쓸 거면 — 샌드박스 Bash 가 게이트웨이 · 클러스터로 **네트워크**가 되나, `env` 가 `EVAL_*` 만 통과한다는 제약 아래 토큰이 들어가나.

### `plugin eval` 과의 관계

`plugin eval` 의 ablation 은 **with/without 둘**이다 — arm 넷을 내지 못한다.
arm 별 플러그인 디렉터리를 target 으로 세 번 돌리면 A1·A2·A3 각각의 "without" 이 A0 가 되어 층 기여 는 나온다.
그러나 §2 의 기계 채점(근거 재실행 · 보정 표)은 `plugin eval` 의 grader 여섯 종으로 안 된다.
그래서 **R2(위 조립)가 주 러너**이고, `plugin eval` 은 미확인 6 이 풀리면 "with/without 요약" 용 보조다.

### 실행 규약

- 시도 = 3, 순서는 (case × arm) 를 섞는다 — 시간대 · 캐시 상태가 한 arm 에 몰리지 않게.
- concurrency = 1 — 같은 한도를 나눠 쓰고(`plugin eval --help`), `tmp/obs` 도 시도마다 새 디렉터리다.
- 라운드 전후 `rate_limit_event.unifiedWindows` 를 한 번씩 읽어 창 소모를 적는다(`261003_1949` §5-1).
- 상한(`--max-turns` · budget) 에 걸린 시도는 점수 0 이 아니라 **미완**으로 따로 센다 — 상한은 측정 장치지 채점 기준이 아니다.

### 크기

첫 라운드 — case 4 × arm 3(A3 없음) × 시도 3 = **36 세션**.
세션당 토큰은 스파이크가 잰다.
`261003_1949` §5-1 의 고정비(약 12k 토큰의 cache write)에 플러그인 · kubectl 출력이 얹히면 세션당 수십만 토큰이 평범할 것이다 — 한 라운드가 5시간 창 하나를 넘길 수 있고, 그러면 **라운드를 case 단위로 쪼개 날을 나눈다**.

## 6. Finding 스키마 — 채점의 공통 입력

#97 의 계약을 그대로 쓰되 채점용 필드를 분리한다.

```yaml
verdict: fault | no_fault | undetermined      # F0 는 no_fault, F5 는 undetermined 가 정답
component: {kind: service|pod|db|collector, name: …}
since: <RFC3339>                             # 변화 시각
claim: <한 문장>
evidence: [{backend, query, window, value, ref}]   # ref = 재실행 가능한 질의 포인터
signals: [metrics, logs, traces, k8s]        # 근거가 선 신호
confidence: high | medium | low
next_check: <한 문장>
```

채점(`grade.py`, 기계):

| 축 | 계산 |
|---|---|
| 국소화 | `component.name` == truth.target |
| 시각 | since 와 truth.since 의 차가 2분 이내 |
| 재실행 | evidence 의 query 를 창 그대로 다시 돌려 value 가 같은가 — A0 의 curl 질의도 같은 방식으로 |
| 보정 | (confidence, 국소화 정오) 2×2 — 틀린 high 는 감점 1, 맞은 low 는 0, 맞은 high 는 가점 1 |
| clean | F0 에서 `verdict == no_fault` |
| 비용 | `usage` · `modelUsage` · `num_turns` · 거부된 호출 수(전사) |

LLM 심판은 `claim` 의 산문 품질 하나에만, 둘째 라운드부터.

## 7. 반대편 — 이 설계가 틀리는 조건

1. **배치 경로 하나로 일반화한다.** posting-service → mongo 한 홉에서 층 기여 가 커도 HTTP 다단 경로에서 같다는 보장은 없다. 첫 라운드의 결론은 "이 경로에서" 다.
2. **절대 시각 창은 문제를 쉽게 만든다.** 실제 장애는 "언제부터인지" 가 질문의 반이다. 재현성을 위해 받아들이되, 난이도 축을 나중에 연다(§3).
3. **A0 에 게이트웨이 접근 정보를 주는 순간 "agent 는 물리를 모른다"(#92) 가 대조군에서 깨진다.** 의도된 것이다 — 그 설계의 가치를 재려면 대조군은 그 설계가 없어야 한다.
4. **k8s 가 답을 말하는 장애(F1 · F6)에서 층 기여가 0 에 가깝게 나오면** 도구가 쓸모없는 것이 아니라 문제가 도구의 영역 밖인 것이다. 그래서 첫 라운드에서 뺐다.
5. ~~**cron 을 손으로 당기면 외부 사이트를 실제로 긁는다.**~~ 부하를 `curl` 로 바꿔 풀렸다(§3 "부하").
6. **모델이 라운드 중 바뀌면** 모든 층 기여 가 무효다. id 를 고정하고 `modelUsage` 의 모델명을 시도마다 검사한다.

## 8. 사람에게 — 코드에 없는 것

1. ~~**cron 손 실행을 부하로 쓰나.**~~ **답(10-04): `curl` 로 만든다.** 게이트웨이 GET 이 posting-service 까지 닿는 것을 확인했다(§3 "부하").
2. ~~**주입 스크립트의 집**~~ **답(10-04): `jyoliar-lab/obs-bench`** — 평가 하네스 전체가 별도 저장소다(§5 "저장소"). M1(git 커밋)만 `jyoliar-k8s` 를 건드리는데, M3(controller 0) 이 생겨 M1 은 선택이다.
3. **Finding 규칙을 A0·A1 에 주나**(§4 미결). 제안은 "스키마만 공통".
4. **모델** — 어느 id 하나로 고정하나.
5. **주입 창의 Alertmanager silence** — 건다. 반대가 없으면 그렇게.
6. **F2 를 netns 규칙(`kubectl debug --profile=netadmin`)으로 심는 데 동의하나.** 사람의 kubeconfig 에 `pods/ephemeralcontainers` 생성이 있어야 하고, 클러스터에 특권 ephemeral container 를 막는 admission 이 없어야 한다 — 전자는 사람이 알고, 후자는 한 번 붙여 보면 안다. mongo 쪽 거부가 operator 에 되돌려지는지도 같은 손으로 확인할 수 있다.
7. **첫 라운드 case 넷(F0 · F2 · F3 · F4)** 에 동의하나. F4 의 `fsyncLock` 이 과하면 F4 를 "pooler 연결 수 조이기" 로 바꾼다 — 단 pooler 는 Argo 가 관리하므로 M1 이 된다.

## 9. 뒤에 올 것 — 발행하지 않는다

사람이 "아직 Task 단계가 아니다" 라고 했고, 10-04 에 "초안을 내 보자" 로 옮겨 왔다.
제안한 쪼갬은 아래다 — 기준은 **선행 관계**(앞의 결과가 뒤의 입력인가)와 **target**(한 티켓이 한 저장소인가).
전부 리프(Task)이고 target 은 obs-bench 다.

| | 주제 | 산출 | 선행 |
|---|---|---|---|
| **T1 하네스 스파이크** | 빈 config 헤드리스 + 구독 OAuth 로 플러그인 하나만 얹어 한 세션 | §5 미확인 여섯의 답 · 평가 세션 하나의 토큰 · 창 소모 — 코멘트로 | 없음 |
| **T2 arm 빌드 + 공통 틀** | `arms/build.sh` · arm 별 `settings.json` · `frame.md` · `finding.schema.json` | arm A0 · A1 · A2 가 플래그 하나로 선택된다 | T1 (schema 결과) · obs-toolkit 층별 패키징 리프 |
| **T3 주입 스크립트 + truth** | F0 · F2 · F3 · F4 의 `on/off` · controller 0/복구 · netns · `fsyncLock` · curl 부하 · silence · truth 자동 기록 | 사람이 한 줄로 주입 · 복구하고 truth 가 떨어진다 | 없음 — T1 과 병행 |
| **T4 러너 + 채점** | `run.sh` · `grade.py` · 층 기여 표 | fixture 한 건으로 채점이 돈다 | T2 |
| **T5 첫 라운드 실행** | F0 · F2 · F3 · F4 × A0 · A1 · A2 × 3 시도 | 첫 층 기여 표 + 설계 피드백(#97 순서 · Budget · Finding 규칙) — 코멘트로 | T3 · T4 |
| **T6 A3 arm** (뒤) | `obs-investigate` 를 같은 코퍼스에 | 조사 층의 층 기여 | #98 · T5 |

T1 이 **답이 뒤를 바꾸는** 유일한 Task 라 T2 · T4 보다 먼저 닫힌다.
T5 를 코드 Task 와 가른 이유는 완료 기준이 다르기 때문이다 — T2 · T4 는 "돈다", T5 는 "표와 피드백이 적혔다".
T5 는 탐색이 아니라 실행이고 산출이 있어 리프다(CLAUDE.md §5 "조사에는 티켓이 없다" 와 충돌하지 않는다).

### 발행됨 — 2026-10-04

사람이 #105 처럼 그룹화 Feature 로 묶기로 했다.
트리는 GitHub 에 산다(#112 와 그 하위 #113~#118) — 여기 베끼지 않는다.
남기는 것은 제안과 달라진 점과 그 이유다.

- **Feature #112 를 #92 밑에 두었다.** 근거 ADR 없는 그룹화 Feature 이고, Feature 밑 Feature 는 #105 가 연 길이다.
- **전부 Draft 로 냈다.** 사람이 "초안" 이라 했다 — Draft 해제는 사람의 것이다.
- **T3(#114)의 target 을 obs-bench 하나로 좁혔다.** M3(controller 0)이 생겨 git 경유 주입이 필요 없어졌고, jyoliar-k8s 는 ref 로만 걸었다.
- **T6(#118)에 "같은 장애를 다시 심는다" 를 넣었다.** 제안 표에는 없던 것 — 첫 라운드 데이터가 72h 를 넘겨 죽으므로 A3 만 돌릴 수 없고 A2 를 같이 다시 돈다. 선행은 #117 과 #98.
- **T1(#113)에 `spike/run-one.sh` 를 산출로 더했다.** 코멘트만 남기면 조립이 재현되지 않는다.
- 제안의 T 번호와 이슈 번호의 대응 — T1 #113 · T2 #115 · T3 #114 · T4 #116 · T5 #117 · T6 #118 (T3 가 선행이 없어 T2 보다 먼저 나갔다).

## 10. 임계선 — ADR 은 없다

전부 되돌리는 데 한 시간대다 — 스크립트 · 디렉터리 · 플래그 · 스키마.
`261003_1949` §11 의 후보(#97 고정 순서)가 유일하고, 그것은 조사 층의 층 기여가 나와야 흔들린다.
