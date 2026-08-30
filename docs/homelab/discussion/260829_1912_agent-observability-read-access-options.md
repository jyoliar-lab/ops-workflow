---
type: discussion
topic: homelab
subjects: [prometheus, loki, tempo, grafana, kube-prometheus-stack, mcp-grafana, kagent, ops-workflow-agent, ticket-engineer-agent]
status: done
ref-adrs: []
---

# agent 의 Prometheus·Loki·Tempo 읽기 접근 — 경로 옵션

## 계기

로컬 Claude Code agent(`ops-workflow-agent` · `ticket-engineer-agent`)에게 관측 스택 3종의 읽기를 주고 싶다.
같은 권한을 추후 클러스터 안에 배포되는 agent 도 쓸 여지가 있다.

이 요구는 새것이 아니다.
2026-07-30 장애 조사에서 진단 agent 가 Prometheus HTTP API 를 못 읽어 컨테이너 로그로 우회했고, 그 마찰이 `tmp/staging/260730_prometheus-api-proxy-rbac-friction.md` 와 `260730_2245_prometheus-tsdb-full-double-monitoring-failure.md` §후기 7 에 남아 있다.

## 문제를 다시 말하면

*"권한을 부여한다"* 는 해법의 모양이다.
치르고 있는 비용은 이것이다 — **actual 의 질문("지금 무엇이 노출·기록되고 있나")을 관측 스택이 아니라 사람(Grafana 화면)이 답해야 한다.**
agent 는 그 답을 로그·desired(코드)·웹 검색으로 우회 추정한다.
로그가 조용한 유형의 실패(relabel 드랍·스크레이프 침묵)에서는 우회로도 없다.

## 현재 상태 — 코드가 답하는 것

| 사실 | 출처 |
|---|---|
| 로컬 agent 는 K8s SA(`agents/ops-workflow-agent`) 장수명 토큰 kubeconfig 로 apiserver(`10.18.1.1:6443`)에 접근한다. `view` + `agent-cluster-read` 두 ClusterRole 로 클러스터 전역 읽기. Secret 값 불가 | `jyoliar-k8s/gitops/base/system/agent-credentials/*.yaml` |
| `services/proxy` 는 어느 Role 에도 없다. 실측: Prometheus·Loki·Tempo 셋 다 `Forbidden` | 위 파일 + 실측 (2026-08-29) |
| 세 서비스는 전부 ClusterIP 뿐이다. HTTPRoute 는 Grafana(`grafana.mg.jyo-liar.com`)·kagent UI·argocd 만 | `kubectl get svc -n prometheus`, `kubectl get httproute -A` |
| 로컬 Mac → 클러스터 LAN 은 Tailscale subnet router 경유다. ClusterIP(10.96/12)는 닿지 않고(실측 `000`), 내부 게이트웨이 VIP(10.18.100.2)와 Grafana HTTPS 는 닿는다(실측 `200`) | `onpremise-k8s/docs/tailscale-subnet-router-design.md`, 실측 |
| Loki 는 `auth_enabled: true`, Tempo 는 `multitenancyEnabled: true`. 조회에 `X-Scope-OrgID` 헤더가 필수이고 현재 테넌트는 `careerhub` 하나 | `controllers/loki/application.yaml`, `controllers/tempo/application.yaml`, `controllers/alloy/application.yaml` |
| Grafana 데이터소스가 그 헤더를 박아 넣는다(`httpHeaderName1: X-Scope-OrgID` / `careerhub`). 즉 **테넌트 고정은 지금 Grafana 가 한다** | `controllers/prometheus-operator/application.yaml` §additionalDataSources |
| Prometheus 는 인증 없음. admin API 비활성(`enableAdminAPI: false`, v3.10.0). 단 kube-prometheus-stack 은 `--web.enable-lifecycle` 을 켜므로 `POST /-/reload`·`/-/quit` 가 열려 있다 | 실측 `kubectl get prometheus` |
| Grafana 12.4.1, Google OAuth 로 허용 이메일 1개만 GrafanaAdmin. grafana-operator 가 `GrafanaServiceAccount` CR 로 Viewer 토큰을 발급해 Secret 에 넣는 패턴이 **이미 있다**(`mcp-grafana-reader` → `mcp-grafana-token`) | `system/grafana-config/grafanaserviceaccount.yaml` |
| 클러스터 안에는 `mcp-grafana`(read-only, `--disable-write`) 가 prometheus ns 에 떠 있고 kagent `cluster-inspector` 가 쓴다. 자체 인증은 없고 클러스터 내부 URL 뿐이다 | `services/ai-agents/mcps/grafana/*.yaml`, `system/kagent-config/agent-cluster-inspector.yaml` |
| `careerhub-incident-agent` 는 `PROM_URL=http://monitoring-kube-prometheus-prometheus.prometheus.svc:9090` 으로 **인증 없이 직접** 조회한다 | `services/ai-agents/careerhub-incident-agent/cronjob.yaml`, `careerhub-incident-agent/agent.py:17,50` |
| NetworkPolicy 는 argocd ns 에만 있다. **클러스터 안의 어떤 pod 도 이미 세 서비스를 제한 없이 읽을 수 있다** | `kubectl get networkpolicy -A` |
| 클러스터는 SA 토큰 issuer 를 `https://k8s-oidc.jyo-liar.com` 로 외부 공개한다(static JWKS). SA JWT 를 클러스터 밖에서도 검증할 수 있다 | `bootstrap/oidc-provider/oidc-configmap.yaml` |

**핵심 관찰 둘.**

1. 로컬 agent 와 클러스터 내 agent 의 문제는 다르다.
   로컬은 **도달 자체**가 막혀 있고(ClusterIP 불가 · proxy 거부), 클러스터 내는 도달이 **이미 완전히 열려 있다**(NetworkPolicy 부재).
   "둘 다 쓸 수 있는 하나의 권한"을 설계한다는 것은 클러스터 내 agent 에게는 *권한 부여*가 아니라 *제한 도입*(신원·테넌트·감사)을 뜻한다.
2. 클러스터 안에 이미 두 개의 서로 다른 접근 패턴이 공존한다 — kagent 는 **Grafana 경유**(SA 토큰 · 테넌트 서버측 고정), incident-agent 는 **네이티브 API 직결**(무인증 · 테넌트 헤더 없음 → Loki·Tempo 는 못 읽는 셈).
   로컬용 경로를 하나 더 만들면 세 가지가 된다.

## 옵션

### A. 안 한다 — 로그 우회를 표준 경로로

- 비용: 위 "문제" 절 그대로. 마찰 로그가 두 번 남았다.
- 이기는 조건: agent 진단이 드물고, 매번 사람이 Grafana 를 대신 봐 줄 수 있을 때.

### B. K8s RBAC 로 `services/proxy` `get` 을 서비스 이름 한정 허용

prometheus ns 에 Role 하나 — `resources: [services/proxy]`, `resourceNames: [monitoring-kube-prometheus-prometheus, loki, tempo]`, `verbs: [get]` — 와 agent 별 RoleBinding.
마찰 로그의 후보 (a) 그대로다.

- **읽기 전용 경계**: proxy 서브리소스의 verb 는 HTTP 메서드에 대응한다(`get`=GET · `create`=POST …). `get` 만 주면 `POST /-/reload`·`/-/quit` 는 apiserver 가 거른다. 마찰 로그가 우려한 "proxy 너머 쓰기 엔드포인트"는 이걸로 닫힌다. PromQL 의 POST 형식 조회는 못 쓰지만 GET 으로 충분하다.
- **Loki·Tempo 헤더**: `kubectl get --raw` 는 헤더를 못 붙인다. `kubectl proxy` 를 띄우고 `curl -H 'X-Scope-OrgID: careerhub'` 로 간다. apiserver 프록시가 임의 헤더를 상류로 넘기는지는 **확인이 필요**하다(미확인).
- 되돌리기: Role 삭제. 한 시간 미만. **ADR 아님.**
- 영향 범위: apiserver 가 로그·트레이스 조회의 데이터 경로가 된다(홈랩 규모에서는 무시 가능하나 감사 로그가 시끄러워진다).
- 테넌트: agent 가 헤더를 임의로 정한다. 단일 테넌트인 지금은 무의미하고, 둘째 테넌트가 오면 구멍이다.
- **클러스터 내 agent 에게는 아무 의미가 없다.** 이미 직결이 열려 있다.
- 이기는 조건: 지금의 마찰을 가장 싸게 풀고, 클러스터 내 agent 문제는 실재할 때 따로 풀기로 할 때.

### C. Grafana 를 단일 정문으로 — agent 별 Grafana SA(Viewer) 토큰

kagent 가 이미 쓰는 패턴을 로컬 agent 로 넓힌다.
`GrafanaServiceAccount` CR 을 agent 별로 GitOps 에 추가하고, 토큰은 kubeconfig 처럼 로컬에서 조립한다(agent 는 Secret 을 못 읽으므로 사람이 꺼내 준다 — `ops-workflow#19` 와 같은 절차).
조회는 `https://grafana.mg.jyo-liar.com/api/ds/query`(또는 `/api/datasources/proxy/uid/…`) 로, 클러스터 안에서는 `http://monitoring-grafana.prometheus.svc` 로 — **같은 신원 모델, 같은 API**.

- **테넌트 고정이 서버측**이다. agent 는 헤더를 모른다. 둘째 테넌트가 와도 데이터소스만 추가하면 된다.
- 로컬 도달 경로가 **이미 있다**(Tailscale → 내부 게이트웨이 → HTTPS). 네트워크 변경 없음.
- 클러스터 내 agent 도 같은 경로를 쓸 수 있다 — 다만 강제되지는 않는다(직결이 여전히 열려 있으므로 규율에 의존한다. NetworkPolicy 를 얹어야 구조가 된다).
- **Grafana 가 진단 경로의 단일 의존이 된다.** Grafana 가 죽으면 agent 는 눈이 먼다. 260730 장애에서 Grafana 는 살아 있었으나 이는 우연이다.
- Viewer 는 모든 데이터소스를 본다. agent 별로 좁힐 수 없다(Grafana 의 데이터소스 권한은 Enterprise 기능이다).
- Grafana 조회 API 는 네이티브 Prometheus/Loki API 와 모양이 다르다. LLM 이 덜 익숙하다. `mcp-grafana` 를 로컬 MCP 로 붙이면 흡수되지만 그러려면 `mcp-grafana` 에 HTTPRoute 와 **인증 계층**이 필요하다(지금은 무인증 내부 URL). → 하위 옵션 C′.
- 되돌리기: 토큰 회수 + CR 삭제. 싸다. 그러나 *"agent 관측 읽기의 정문은 Grafana 다"* 라는 계약 위에 클러스터 내 agent 들이 쌓이기 시작하면 되돌리기가 비싸진다 — **그 시점부터 ADR 이다.**
- 이기는 조건: 테넌트가 둘 이상이 될 전망이 실재하고, Grafana 의존을 감수할 수 있을 때. kagent 와 경로를 통일하고 싶을 때.

### D. 네이티브 API 앞에 인증 프록시 — K8s SA JWT 검증 + 테넌트 주입

작은 리버스 프록시(kube-rbac-proxy 류 또는 nginx + JWKS)를 prometheus ns 에 두고 `prom.mg / loki.mg / tempo.mg` HTTPRoute 로 내부 게이트웨이에 건다.
요청의 Bearer 토큰을 TokenReview 또는 `k8s-oidc.jyo-liar.com` JWKS 로 검증하고, SA 신원에 따라 `X-Scope-OrgID` 를 서버측에서 박는다.

- **신원 모델이 하나(K8s SA)** 로 통일된다. 로컬 agent 는 이미 가진 kubeconfig 토큰을 그대로 쓰고, 클러스터 내 agent 는 projected SA 토큰을 쓴다. 토큰 배포 절차가 새로 안 생긴다.
- 네이티브 API 보존. Grafana 의존 없음. 테넌트 서버측 고정.
- NetworkPolicy 로 직결을 막으면 클러스터 내 agent 에게도 **구조로** 강제된다.
- **새 컴포넌트를 만들고 운영한다.** 가장 비싸다. kube-rbac-proxy 는 SubjectAccessReview 까지 하지만 헤더 주입은 없어 조합이 필요하다.
- 이 프록시의 URL·인증 방식은 여러 소비자가 의존하는 **인터페이스**다. one-way door 에 가깝다. **ADR.**
- 이기는 조건: 클러스터 내 agent 가 실재하고 여럿이며, 테넌트 격리를 구조로 강제해야 할 때.

### 비교 축

| 축 | A | B | C | D |
|---|---|---|---|---|
| 되돌리기 비용 | — | 낮음 | 낮음 → 소비자가 늘면 높음 | 높음 |
| 영향 범위 | — | apiserver | Grafana | 새 컴포넌트 + 게이트웨이 |
| 로컬 agent 도달 | ✗ | ○ | ○ | ○ |
| 클러스터 내 agent | 이미 열림 | 무의미 | 가능·비강제 | 가능·강제 가능 |
| 테넌트 고정 위치 | — | agent(헤더) | Grafana | 프록시 |
| 진단 경로의 단일 의존 | 사람 | apiserver | Grafana | 프록시 |
| 접근 패턴 수(클러스터 전체) | 2 | **3** | 1 로 수렴 가능 | 1 로 수렴 가능 |
| 새로 만드는 것 | 없음 | Role 1 | CR 1/agent | 컴포넌트 1 + Route 3 |

## 사람에게 묻는 것 — 코드에 없는 것

1. **둘째 테넌트는 실재하는 전망인가.** Alloy 주석은 "신규 텐넌트 합류 시 노드 그룹 분리"를 말한다. 전망이 실재하면 테넌트 고정 위치가 결정 축이 되어 B 가 탈락한다. 아니면 B 로 충분하다.
2. **클러스터 내 agent 의 "이용할 여지"는 어느 쪽인가.** 도달(이미 있음)인가, 신원·감사·격리(없음)인가. 후자라면 이것은 권한 *부여*가 아니라 *제한* 설계이고 NetworkPolicy 가 함께 온다.
3. **Grafana 를 진단 경로의 단일 의존으로 둘 수 있는가.** C 의 값이 여기서 갈린다.
4. **셋을 한꺼번에 여는가, Prometheus 부터인가.** 마찰의 실체는 Prometheus 였다. Loki·Tempo 는 헤더 문제가 얹혀 B 에서 검증이 하나 더 필요하다.

## 상대편에 서서

요구 문장("추후 클러스터 내 agent 도 이용")은 통일 메커니즘(D)을 향해 기울어 있다.
반대편의 근거: **클러스터 내 agent 는 지금 하나(incident-agent, suspend 상태) 이고 이미 무제한으로 읽는다.**
통일 메커니즘이 사는 값은 신원·테넌트 격리인데, 그것이 필요한 조건(둘째 테넌트 · 다수의 클러스터 내 agent)이 아직 없다.
없는 조건을 위해 컴포넌트를 세우면 그 컴포넌트가 낡을 때까지 아무도 그 인터페이스를 쓰지 않을 수 있다.

반대로 B 에 대한 반론: 세 번째 접근 패턴을 낳는다.
kagent(Grafana)·incident-agent(직결)·로컬(apiserver proxy) — 나중에 통일할 때 셋을 걷어야 한다.
C 는 그중 하나(kagent 의 것)를 넓히는 것이라 패턴 수를 늘리지 않는다.

## 미확인 사항

- apiserver `services/proxy` 가 `X-Scope-OrgID` 같은 임의 헤더를 상류로 전달하는가(B 의 Loki·Tempo 성립 조건).
- `kubectl auth can-i get services/proxy -n prometheus` 는 `yes` 를 돌려주는데 실제 호출은 `Forbidden` 이다. 서브리소스 can-i 평가의 오차로 보이나 원인은 확인하지 않았다.
- Grafana `/api/ds/query` 가 Viewer 토큰으로 Loki·Tempo 데이터소스까지 조회 가능한지(권한 모델상 가능해야 하나 실측 안 함).

## 2026-08-29 답 — 축이 정해졌다

1. 둘째 테넌트: 당장은 없으나 careerhub 외 서비스가 들어올 여지는 충분하다. → 테넌트 고정 위치가 축이 된다. **B 탈락.**
2. 클러스터 내 agent 의 여지는 **도달**이다(추후 트러블슈팅 자동화 agent 가 같은 방안을 쓰면 좋겠다는 것). 신원·격리 요구가 아니다. → **D 과대.**
3. Grafana 정문(C)은 사람이 제일 먼저 떠올린 방안이다.
4. 셋 모두. 우선순위 Prometheus > Loki > Tempo.

남는 것은 C 다.
사람이 이미 답을 갖고 왔으므로 **C 가 틀리는 조건**을 찾았다.

### C 의 구멍 — Grafana 데이터소스 프록시는 메서드를 가리지 않는다

Grafana 소스(`pkg/api/api.go`) 확인:
`/api/datasources/proxy/uid/:uid/*` 는 `datasourceRoute.Any(...)` 로 등록되고 권한 평가는 `datasources:query` 하나다.
즉 **Viewer 토큰으로 어떤 HTTP 메서드든 상류에 그대로 도달한다.**

- Prometheus: `POST /-/reload` · `POST /-/quit` (kube-prometheus-stack 이 `--web.enable-lifecycle` 을 켜 둔다 — config-reloader 사이드카가 쓰므로 끌 수 없다). `/-/quit` 은 pod 재시작을 유발한다.
- Loki: `POST /loki/api/v1/push` — 데이터소스가 박는 `X-Scope-OrgID: careerhub` 그대로 **테넌트에 가짜 로그를 쓸 수 있다.**
- Tempo: 데이터소스 URL 이 `:3200` 이고 OTLP 수신은 `:4317/4318` 이라 프록시로는 push 가 안 된다.

**"read-only 정문"이라는 C 의 전제는 raw 프록시 경로에서는 성립하지 않는다.**

> ⚠ **정정(같은 날, `260829_2038` 에서)**: 라우트 등록만 읽고 검증 함수를 안 읽었다. `ds_proxy.go` `validateRequest` 는 **Prometheus·Loki 데이터소스에 POST/PUT/DELETE 를 거부한다**(플러그인 routes 미정의 가정). 위의 `POST /-/quit`·Loki push 구멍은 **Prom·Loki 에는 없다.** Tempo 만 메서드 검증이 없다. C-1 의 평가는 그쪽 문서를 따른다.
`--disable-write` 가 read 를 보장하는 것은 mcp-grafana 의 도구 집합 안에서뿐이다.

### C 안에서 클라이언트 경로 셋

| | 경로 | read 보장 | API 모양 | 추가로 필요한 것 |
|---|---|---|---|---|
| **C-1 raw 프록시** | `/api/datasources/proxy/uid/<uid>/api/v1/query` | ✗ (위 구멍) | **네이티브** PromQL/LogQL/TraceQL API 그대로 | 없음 |
| **C-2 `/api/ds/query`** | POST, Grafana 프레임 포맷 | ○ (조회 전용 엔드포인트) | Grafana 고유 — LLM 이 덜 익숙, 응답 파싱 필요 | 없음 |
| **C-3 mcp-grafana 노출** | HTTPRoute + 로컬 MCP 클라이언트 | ○ (`--disable-write`, 도구 화이트리스트) | MCP 도구(kagent 와 동일) | HTTPRoute 1 + **mcp-grafana 앞 인증**(지금 무인증 내부 URL) |

C-1 은 가장 편하고 가장 구멍이 크다.
구멍의 실질 피해는 홈랩 규모에서 "Prometheus 재시작 · 테넌트 로그 오염" 이고, 로컬 agent 토큰은 사람의 Mac 에만 있다.
그래도 §6 의 원칙 — *규율이 아니라 구조로* — 에 어긋난다. read 가 구조로 보장되는 것은 C-2·C-3 이다.

C-3 은 kagent 와 클라이언트까지 완전히 같아진다(패턴 수 1).
대신 mcp-grafana 에 인증을 얹어야 하는데, 이는 사실상 옵션 D 의 축소판(프록시 1개 + Route 1개)이다.

### 이 결정은 ADR 인가

*"agent 의 관측 읽기는 Grafana 데이터소스를 경유하고, 신원은 Grafana SA, 테넌트 고정은 데이터소스가 한다"* —
추후 트러블슈팅 agent 가 이 위에 쌓이고, 테넌트가 늘면 데이터소스가 늘어난다.
되돌리려면 소비자 전부의 접근 코드를 바꿔야 한다 — 라고 agent 는 판정했다.

**사람의 판정: ADR 아니다.**
ADR 은 나중에 잘못됐음을 알아도 돌이키기 어려운 결정(상용 서비스의 DB 선택 등)이다.
agent 에게 줄 도구는 새로 만들어 바꾸면 되고 기존 도구를 버리지 않으면 된다.
데이터 손실·고객 이탈 같은 치명적 피해 리스크가 없다.
→ **ADR 없이 리프 티켓으로 간다.** 임계선 규약 자체는 마찰 로그(`tmp/staging/260829-adr-threshold-one-hour-too-low.md`)로 넘겼다.

incident-agent 의 Prometheus 직결은 이 결정과 어긋난 채 남는다.
질문 2 의 답(도달만)에 따라 강제하지 않되, 결정이 accept 되면 옮길지는 별도 판단이다.

### 사람의 선택 (2026-08-29)

- 클라이언트 경로: **C-3** (mcp-grafana 노출).
- 토큰: 무기한 + 유출 의심 시 회전. read-only 이고 VPN 안에서만 닿게 할 것이라 유출 피해가 작다.
- 리프가 많으면 Feature 로 묶는다.

### C-3 를 코드로 확인하니 걸리는 것 둘 (mcp-grafana 0.15 README · `main`)

1. **mcp-grafana 에 Tempo 도구가 없다.** Prometheus·Loki 는 있고 Pyroscope 는 있으나 TraceQL 조회 도구는 없다.
   C-3 만으로는 우선순위 3위 Tempo 를 못 덮는다.
   Tempo 보완 후보: (T-a) `/api/ds/query` 를 curl 로 — 구조로 read (T-b) raw 프록시 — Tempo 는 `:3200` 에 push 가 없어 Prometheus·Loki 와 달리 구멍이 없다 (T-c) mcp-grafana 에 Tempo 도구가 들어올 때까지 보류.
   T-a·T-b 는 모두 agent 손에 Grafana SA 토큰이 있어야 한다.
2. ~~mcp-grafana 는 요청별 자격증명을 받지 않는다~~ — **README 요약에 의존한 오판. 소스가 반대로 말한다.**
   `mcpgrafana.go` `extractKeyGrafanaInfoFromReq`: 헤더 `X-Grafana-Service-Account-Token`(구 `X-Grafana-API-Key`) 의 토큰을 우선 쓰고, **없으면 env `GRAFANA_SERVICE_ACCOUNT_TOKEN` 으로 폴백**한다.
   → agent 별 Grafana SA 신원은 C-3 에서도 성립한다(Claude Code 는 `claude mcp add --transport http -H ...`).
   → 다만 mcp-grafana 자체에 인증 게이트는 없다. 지금 인스턴스는 env 토큰이 있으므로 HTTPRoute 만 열면 **헤더 없는 요청도 `mcp-grafana-reader` 로 조회된다**(폴백).
   토큰을 필수로 만들려면 env 토큰을 빼면 된다 — 인증은 Grafana 가 한다(401). 새 컴포넌트 불필요.
   (a) 외부용 인스턴스를 env 토큰 없이 하나 더 띄워 그것만 노출 — kagent 무변경, 인스턴스 2개
   (b) 단일 인스턴스에서 env 토큰을 빼고 kagent `RemoteMCPServer` 도 `headersFrom`(CRD 필드 확인)으로 헤더 전송 — 소비자 전부 같은 방식, kagent 변경 얹힘
   agent 입장: (a)는 임시가 영구 되기 쉽고, 소비자 셋뿐인 지금이 (b)로 통일하기 제일 싸다.

사람의 답: **(b)** 단일 인스턴스 env 토큰 제거 + kagent `headersFrom` · Tempo 는 **T-b** raw 프록시 · Grafana SA 는 두 하네스가 **하나를 공유** · ticket-engineer 하네스는 `jyoliar-lab/ticket-engineer`.

## 쪼갬 — 왜 이렇게, 무엇을 버렸나

Feature #84 아래 리프 4 (#85 클러스터 인증·노출 / #86 Grafana SA / #87 하네스 등록·Prom·Loki 검증 / #88 Tempo curl).
트리 자체는 GitHub 이 답한다 — 여기는 버린 쪼갬만.

- **Prometheus·Loki·Tempo 를 각각 리프로** 자르는 안을 버렸다. 클러스터 쪽 일은 셋에 공통(#85·#86)이고, 갈리는 것은 클라이언트 경로(MCP vs curl)뿐이라 그 축으로 잘랐다.
- **하네스 두 개를 리프 두 개로** 자르는 안을 버렸다. 같은 org 의 설계 agent 가 둘 다 담당하고 배선이 같아야 하므로 target 둘인 리프 하나가 맞다.
- **외부용 mcp-grafana 인스턴스 분리(a)** 를 버렸다 — 임시가 영구가 되기 쉽고, 소비자 셋뿐인 지금이 통일하기 제일 싸다.
- **agent 별 Grafana SA** 를 버렸다 — 사람의 판단. 두 하네스는 토큰 하나를 공유한다.
- **incident-agent 직결 이관·NetworkPolicy** 는 범위 밖으로 뒀다. 클러스터 내 agent 의 요구는 도달뿐이다.

## 남는 것

- ADR 임계선 재정의 → `tmp/staging/260829-adr-threshold-one-hour-too-low.md`
- mcp-grafana 에 Tempo 도구가 들어오면 #88 의 curl 절차는 MCP 도구로 대체한다.
