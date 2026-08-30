---
type: discussion
topic: homelab
subjects: [prometheus, loki, tempo, nginx-gateway-fabric, ops-workflow-agent, ticket-engineer-agent]
status: done
ref-adrs: []
---

# 네이티브 관측 API 를 직접 부르면서 read-only 를 구조로 거는 방안

## 계기

앞선 두 논의(`260829_1912_agent-observability-read-access-options.md`, `ai-agent/260829_2022_mcp-grafana-context-load-minimization.md`)의 귀결:

- PromQL·LogQL·TraceQL 은 모델이 잘 아는 언어다. MCP 도구 없이 **네이티브 API 를 curl 로** 부르는 쪽이 컨텍스트도 싸고 표현력도 온전하다.
- 그런데 지금 read-only 를 보장하는 것은 mcp-grafana 의 `--disable-write`(도구 집합)뿐이다. 네이티브 API 를 직접 열면 그 보장이 사라진다.
- Grafana 조회 API(`/api/ds/query`)는 모델에 낯설어 제외한다. Grafana raw 프록시는 `Any` 메서드를 통과시켜 read-only 가 아니다.

질문: **네이티브 엔드포인트를 직접 부르되, 쓰기가 "규율"이 아니라 "구조"로 막히는 길은 무엇인가.**

## 무엇이 쓰기인가 — 백엔드별 실측

| 백엔드 | 쓰기·상태변경 엔드포인트 | 지금 상태 | 출처 |
|---|---|---|---|
| Prometheus `:9090` | `POST /-/reload`, `POST /-/quit` (`--web.enable-lifecycle`) · `/api/v1/admin/tsdb/*` | lifecycle **켜짐**(StatefulSet args 실측) · admin API **꺼짐** | `kubectl get sts prometheus-… -o jsonpath`, `enableAdminAPI: false` |
| Loki `:3100` | `POST /loki/api/v1/push` · `DELETE /loki/api/v1/delete`(deletion_mode 필요) | push **열림** · delete **비활성**(config 에 `deletion_mode` 없음) | `kubectl get cm loki` |
| Tempo `:3200` | `POST/PATCH/DELETE /api/overrides`(user-configurable overrides 필요) · `/live-store/prepare-*downscale` | overrides **비활성**(`user_configurable_overrides` 없음) | `kubectl get cm tempo`, Tempo API docs |

**셋 다 읽기는 전부 GET 이고, 쓰기는 전부 POST/PUT/PATCH/DELETE 다.**
따라서 *"GET 만 통과시킨다"* 가 백엔드 셋에 공통으로 성립하는 read-only 경계다.
Prometheus 의 `/api/v1/query` 는 POST 도 받지만(긴 쿼리용) GET 으로 충분하다.

## 인프라가 답하는 것

- 게이트웨이는 NGINX Gateway Fabric **2.2.1**(`nginx-gateway` ns 실측). HTTPRoute 의 `matches[].method`·`matches[].path`·`RequestHeaderModifier`(set/add/remove) 를 지원한다(NGF 호환표). 단 룰당 RequestHeaderModifier 는 **첫 번째 하나만** 적용된다.
- NGF 의 `AuthenticationFilter`(basic auth, OSS 가능)는 2.6.x 의 것이고, 클러스터의 CRD 목록에 **없다**. `SnippetsFilter` CRD 는 있지만 컨트롤러 args 에 `--snippets-filters` 가 없어 **꺼져 있다**. → 2.2.1 게이트웨이에는 지금 인증 수단이 없다.
- apiserver 의 `services/proxy` 는 `httputil.ReverseProxy` 로 상류에 넘긴다(k8s `apimachinery/pkg/util/proxy/upgradeaware.go`). hop-by-hop 외 헤더는 그대로 전달되므로 `X-Scope-OrgID` 도 넘어간다 — 앞선 논의의 "미확인"을 소스로 해소했다. RBAC 의 subresource verb 는 HTTP 메서드에 대응한다(`get`=GET, `create`=POST …).
- 로컬 → 클러스터는 Tailscale subnet router 경유. 내부 게이트웨이 VIP(`10.18.100.2`)와 apiserver 는 닿고, ClusterIP 는 안 닿는다.

## 옵션

### A. apiserver `services/proxy` 에 `get` 만 — RBAC 가 메서드를 거른다

prometheus ns 에 Role: `resources: [services/proxy]`, `resourceNames: [monitoring-kube-prometheus-prometheus, loki, tempo]`, `verbs: [get]`. agent 별 RoleBinding.
클라이언트는 `kubectl proxy` 를 띄우고 `curl -H 'X-Scope-OrgID: careerhub' http://127.0.0.1:8001/api/v1/namespaces/prometheus/services/loki:3100/proxy/loki/api/v1/query_range?...`.

- **read-only 는 apiserver RBAC 가 건다.** POST 는 `create` 권한이 없어 거부된다. 구조다.
- **신원·감사가 있다.** 이미 가진 K8s SA 토큰을 그대로 쓰고, apiserver audit 에 agent 별로 남는다. 새 토큰·새 컴포넌트 **0**.
- 클러스터 내 agent 도 자기 SA 의 projected 토큰으로 같은 경로를 쓸 수 있다(자연스럽진 않다 — 직결이 열려 있으니).
- **테넌트는 agent 가 고른다.** RBAC 는 헤더를 못 본다. 둘째 테넌트가 오면 구멍이다.
- 로그·트레이스 응답이 apiserver 를 지난다. 홈랩 규모에서는 무시할 만하나 감사 로그가 시끄럽다.
- 이기는 조건: 신원·감사를 지키고 싶고, 테넌트 격리는 아직 필요 없을 때.

### B. 게이트웨이 HTTPRoute — 메서드·경로 allowlist + 테넌트 헤더 주입

`internal-nginx-gateway` 에 호스트 셋: `prom.mg` · `loki-careerhub.mg` · `tempo-careerhub.mg`.
각 HTTPRoute 룰은 `method: GET` + 읽기 경로 prefix(`/api/v1/query`, `/api/v1/series`, `/api/v1/label`, `/loki/api/v1/query`, `/loki/api/v1/label`, `/api/search`, `/api/traces` …)만 매치하고, Loki·Tempo 룰에 `RequestHeaderModifier: set X-Scope-OrgID: careerhub` 를 건다.
매치 밖 요청은 게이트웨이가 404 로 떨어뜨린다.

- **read-only 는 게이트웨이가 건다.** GET 이 아니거나 allowlist 밖 경로는 백엔드에 닿지 않는다. 구조다.
- **테넌트가 서버측에 고정된다.** `set` 은 클라이언트가 보낸 헤더를 덮어쓴다. 둘째 테넌트는 호스트를 하나 더 낸다(`loki-<tenant>.mg`). 앞선 논의에서 B(RBAC)를 탈락시킨 사유가 여기서 해소된다.
- **Grafana 가 경로에서 빠진다.** Grafana 다운이 agent 를 눈멀게 하지 않는다.
- 로컬·클러스터 내 agent 모두 같은 URL 을 쓴다(게이트웨이 VIP 는 pod 에서도 닿는다). 새 컴포넌트 **0** — HTTPRoute 셋과 external-dns 레코드뿐.
- **신원·인증이 없다.** NGF 2.2.1 에는 `AuthenticationFilter` 가 없고 SnippetsFilter 는 꺼져 있다. VPN(Tailscale) 이 경계다 — tailnet 의 어느 장치든 읽는다. 감사는 nginx access log 의 출발 IP 뿐이다.
- 나중에 인증을 얹는 길은 있다: NGF 를 2.6.x 로 올려 `AuthenticationFilter`(htpasswd Secret, agent 별 사용자) 를 걸면 신원이 생긴다. 게이트웨이 업그레이드는 별개의 일이다.
- allowlist 는 유지 비용이 있다 — 새 읽기 엔드포인트를 쓰려면 룰을 늘린다. 반대로 말하면 노출면이 명시적이다.
- 이기는 조건: 테넌트 격리와 Grafana 비의존이 신원보다 중요할 때. 그리고 "VPN 안은 신뢰한다"는 판단이 유효할 때.

### C. 전용 인증 프록시 (kube-rbac-proxy 류)

TokenReview + SubjectAccessReview 로 K8s SA 를 검증하고 HTTP 메서드를 verb 에 대응시키며, 뒤에 nginx 로 테넌트 헤더를 박는다.
A 의 신원과 B 의 테넌트 고정을 다 갖지만 **컴포넌트를 새로 만들고 운영한다.**
앞선 논의의 D 와 같다. 소비자가 셋인 지금은 과대하다.

### D. 백엔드 자체의 쓰기면을 닫는다 — 어느 옵션에나 얹는 심층 방어

- Prometheus: `--web.enable-lifecycle` 을 없애려면 operator 의 `reloadStrategy: ProcessSignal`(SIGHUP 리로드) 로 바꾼다. 그때 operator 가 플래그를 빼는지는 **소스에서 확인하지 못했다**(`pkg/prometheus` 에서 문자열을 못 찾음 — 다른 패키지에 있을 것). 검증 항목이다.
- Loki: deletion 비활성(현재 그대로). push 는 못 닫는다 — Alloy 가 쓴다.
- Tempo: user-configurable overrides 비활성(현재 그대로).
- Loki 를 SimpleScalable 로 나눠 `read` 타깃만 노출하는 안은 **버렸다** — 오브젝트 스토리지(S3 호환)가 전제라 이 문제 하나를 위한 이동으로는 과대하다.

### F. Grafana 데이터소스 프록시로 raw 호출 + Grafana SA 인증 + 게이트웨이 GET 한정 (사람의 제안)

`https://grafana.mg/api/datasources/proxy/uid/<uid>/<네이티브 경로>` 를 Grafana SA 토큰(Bearer)으로 부른다.
Grafana 는 그 뒤에 네이티브 API 를 그대로 붙이고, 데이터소스에 설정된 `X-Scope-OrgID` 를 얹는다.
게이트웨이는 이 prefix 에 GET 만 통과시킨다.

**소스를 다시 읽으니 앞선 판단이 절반 틀렸다.**
`pkg/api/pluginproxy/ds_proxy.go` `validateRequest`:

```go
switch proxy.dataSource.PluginType() {
case DS_PROMETHEUS, DS_AMAZON_PROMETHEUS, DS_AZURE_PROMETHEUS, DS_LOKI:
    switch proxy.ctx.Req.Method {
    case "DELETE", "PUT", "POST":
        return fmt.Errorf("non allow-listed %ss not allowed on proxied %s datasource", ...)
```

- **Prometheus·Loki 데이터소스의 프록시는 Grafana 자체가 POST/PUT/DELETE 를 거부한다**(플러그인이 routes 로 allow-list 하지 않는 한 — 코어 Prometheus·Loki 플러그인의 routes 정의는 확인하지 못했다. 미확인 항목).
  라우트 등록이 `Any` 인 것은 맞지만 그 아래 검증이 메서드를 거른다.
  앞선 논의(`260829_1912`)에서 "Viewer 토큰으로 `POST /-/quit`·Loki push 가 열린다"고 한 것은 **틀렸다** — 라우트 등록만 보고 검증 함수를 안 읽었다.
- **Tempo 는 그 switch 에 없다.** Tempo 프록시는 메서드를 안 거른다. 다만 Tempo `:3200` 의 쓰기(`/api/overrides`)는 비활성이라 지금은 실질 구멍이 없다.
- 데이터소스 커스텀 헤더(`httpHeaderName1: X-Scope-OrgID`)는 `pkg/services/datasources/service/datasource.go` 가 HTTP 클라이언트 옵션(`Header: s.getCustomHeaders(...)`)으로 넣고, 프록시도 그 transport 를 쓴다. 테넌트는 서버측 고정이다.

그러면 F 는 이렇게 된다:

| 축 | F |
|---|---|
| read-only | **Grafana(Prom·Loki: 메서드 거부) + 게이트웨이(`method: GET`, 이중)** — Tempo 는 게이트웨이만 |
| 테넌트 고정 | 서버측(데이터소스) |
| 신원·감사 | Grafana SA 토큰. 두 하네스 공유 토큰이라 하네스 구분은 없다 |
| Grafana 의존 | **있다** — 사람이 수용 |
| 클러스터 내 agent | `http://monitoring-grafana.prometheus.svc/api/datasources/proxy/…` 같은 경로. 단 게이트웨이를 안 지나므로 GET 한정은 Grafana 의 몫 |
| 새 컴포넌트 | 0 — HTTPRoute 룰 1~2 + Grafana SA(#86 그대로) |
| 클라이언트 | curl, 네이티브 API |

**게이트웨이 GET 한정의 함정 하나.**
Gateway API 는 여러 룰 중 가장 구체적인 매치를 고른다.
`grafana.mg` 에 이미 `/` 룰(사람 UI, POST 필요)이 있으므로, `/api/datasources/proxy/` + `method: GET` 룰을 얹기만 하면 **POST 는 그 룰에 안 걸리고 `/` 룰로 떨어져 Grafana 에 닿는다.**
GET 한정을 구조로 만들려면 같은 prefix 의 **비-GET 을 명시적으로 막는 룰**(백엔드 없는 룰 → 500, 또는 RequestRedirect 로 404 자리로)을 함께 둬야 한다.
사람의 UI 는 이 prefix 에 POST 를 쓰지 않는다(현대 Grafana UI 는 `/api/ds/query` 를 쓴다) — 확인 항목.
혹은 agent 전용 호스트(`obs.mg`)를 따로 내고 그 호스트에는 GET `/api/datasources/proxy/` 룰만 두는 것이 깔끔하다 — 그러나 토큰은 `grafana.mg` 에서도 통하므로 사람 호스트 쪽 차단 룰은 여전히 필요하다.
다만 Prometheus·Loki 는 Grafana 가 이미 거르므로, 게이트웨이 룰이 실제로 지키는 것은 **Tempo 와 "Grafana 가 나중에 바뀔 때"** 뿐이다.

#### F 의 하위 선택 — 게이트웨이를 어디에 두나

**F-1. 기존 `internal-nginx-gateway` 에 룰 추가.**
`grafana.mg` 의 `/` 룰 옆에 `/api/datasources/proxy/` GET 룰 + 비-GET 차단 룰을 얹는다.
사람의 UI 와 같은 nginx pod·같은 VIP·같은 access log 를 쓴다.
사람 경로의 HTTPRoute 를 건드린다 — 차단 룰이 UI 를 막지 않는지 검증이 따른다.

**F-2. agent 전용 Gateway 를 하나 더 낸다(사람의 제안).**
클러스터의 Gateway 는 이미 둘이고(`internal` · `careerhub`), 패턴이 같다 — `Gateway` + `NginxProxy`(LoadBalancer, `implementation: kube-vip` 라벨로 VIP 자동 할당) + 와일드카드 cert.
NGF 2.x 는 Gateway 마다 nginx Deployment 를 따로 띄운다(실측: `internal-nginx-gateway-nginx` pod).
`agent-nginx-gateway`(nginx-gateway ns, `wildcard-mg-tls` 재사용, 호스트 `obs.mg.jyo-liar.com`)를 내고, 거기에는 **GET `/api/datasources/proxy/` → Grafana** 룰만 둔다. 매치 밖은 룰이 없어 404 다.

| 축 | F-1 기존 게이트웨이 | F-2 전용 게이트웨이 |
|---|---|---|
| 사람 경로 변경 | **있다**(grafana.mg 룰 추가·차단 룰) | **없다** |
| 네트워크 경계 | 사람과 같은 VIP | **별도 VIP** → Tailscale ACL·NetworkPolicy 로 "agent 호스트만 이 VIP" 를 구조로 걸 수 있다 |
| 감사 | access log 혼재 | agent 트래픽만의 access log |
| 격리 | 무거운 로그 조회가 사람 UI 와 같은 nginx 를 탄다 | 분리 |
| 비용 | 룰 2개 | nginx pod 1 + VIP 1 + Gateway·NginxProxy·HTTPRoute + external-dns 레코드. 라즈베리파이에서 pod 하나의 값 |
| 토큰 오남용 경로 | `grafana.mg` 에 POST — Grafana 가 Prom·Loki 는 거른다 | 같다 — 토큰은 `grafana.mg` 에서도 통한다. 전용 게이트웨이가 이 구멍을 닫지는 않는다 |

F-2 가 사는 값은 "사람 경로 무변경"과 "VIP 단위 네트워크 경계"다.
후자는 지금 tailnet 이 사람 기기뿐이라 당장 쓰이지 않지만, 추후 클러스터 내 agent 나 다른 호스트의 agent 가 생길 때 **IP 하나로 경계를 긋는 손잡이**가 된다.
F-2 가 닫지 못하는 것은 토큰 자체의 범위다 — Grafana SA 토큰은 어느 경로로든 Grafana 에 통한다. 그것은 Grafana 의 메서드 거부(Prom·Loki)와 백엔드 쓰기면 비활성(Tempo)이 막는다.

**F 가 B 보다 나은 점**: 신원이 있다(토큰) · Prom·Loki 는 이중 방어 · 룰이 하나다(호스트 셋 대신 prefix 하나).
**B 가 F 보다 나은 점**: Grafana 비의존 · 테넌트별 호스트가 명시적 · agent 가 Grafana 의 프록시 의미론(uid 경로)을 몰라도 된다.

### E. 클라이언트 쪽만(hook 으로 `curl -X POST` 차단 등)

규율이지 구조가 아니다. agent 가 다른 도구로 우회할 수 있다. 단독 수단으로는 기각. A·B 위에 얹는 것은 무해하다.

### 비교

| 축 | A. apiserver RBAC | B. 게이트웨이 allowlist | C. 전용 프록시 |
|---|---|---|---|
| read-only 를 거는 곳 | apiserver(verb) | 게이트웨이(method+path) | 프록시 |
| 테넌트 고정 | agent(구멍) | **서버측** | 서버측 |
| 신원·감사 | **K8s SA · audit** | 없음(VPN 경계) | K8s SA |
| Grafana 의존 | 없음 | 없음 | 없음 |
| 클러스터 내 agent | 가능(부자연) | **같은 URL** | 같은 URL |
| 새 컴포넌트 | 0 | 0 | 1 |
| 클라이언트 | `kubectl proxy` + curl | curl | curl |
| 되돌리기 | Role 삭제 | Route 삭제 | 컴포넌트 철거 |

(F 는 위 절의 표 참조 — 신원 있음 · 테넌트 서버측 · Grafana 의존 · 컴포넌트 0.)

## 상대편에 서서

사람의 방향은 "raw 호출 + read-only" 이고 B 가 그것을 가장 싸게 준다.
반론 하나: **read-only 는 무해가 아니다.** careerhub-prod 로그에는 사용자 데이터가 실릴 수 있고, B 는 tailnet 의 어느 장치든 그것을 읽게 한다.
지금 tailnet 은 사람의 기기뿐이라 경계로 충분하지만, 그 전제는 문서가 아니라 Tailscale ACL 이 지켜야 한다.
A 는 그 걱정이 없다 — 토큰이 있는 agent 만 읽는다.

반론 둘: A 와 B 는 배타가 아니다.
Prometheus 는 테넌트가 없으니 A 로도 손색이 없고, 테넌트 고정이 필요한 Loki·Tempo 만 B 로 갈 수도 있다.
다만 경로가 둘이 되는 비용이 있다.

## #84 트리에 미치는 것

B 든 A 든 로컬 하네스가 MCP 를 안 쓰면:

- #85(mcp-grafana 노출)·#86(Grafana SA)·#87(MCP 등록)은 **로컬에는 불필요**해진다. #85 는 클러스터 내 agent 를 위해 남길 수 있으나 지금 할 이유는 줄어든다.
- #88(Tempo raw 프록시 curl)은 Grafana 경유를 전제하므로 대체된다.
- 새 리프: (B) HTTPRoute 셋 + external-dns / (A) Role·RoleBinding, 그리고 두 하네스에 curl 스킬(`promql` · `logql` · `traceql` 스크립트 + 출력 필터).

티켓의 취소·재편은 사람의 것이다. 여기서는 영향만 적는다.

## 미확인

- 코어 Prometheus·Loki 데이터소스 플러그인이 `routes` 로 POST 를 allow-list 하는지(F 의 Grafana 측 메서드 거부가 성립하는 조건). 저장소에서 plugin.json 위치를 못 찾았다.
- Grafana UI 가 `/api/datasources/proxy/` prefix 에 비-GET 을 쓰지 않는지(F 의 게이트웨이 차단 룰이 사람을 막지 않는 조건).

- prometheus-operator `reloadStrategy: ProcessSignal` 이 `--web.enable-lifecycle` 을 실제로 뺀다는 것(D).
- NGF 2.2.1 에서 `method` 매치와 `RequestHeaderModifier` 를 같은 룰에 두었을 때의 동작(호환표는 지원이라 하나 실측 안 함).
- B 에서 Tailscale ACL 이 실제로 어느 장치에 `10.18.100.2` 를 허용하는지.

## 수렴 (2026-08-29)

사람의 선택: **F-2** — Grafana 데이터소스 프록시 raw 호출 + Grafana SA 인증 + agent 전용 Gateway(GET 만).

### 쪼갬 — 무엇을 버렸나

Feature #84 를 제목·본문 교체로 유지했고, #85(mcp-grafana 노출)·#87(MCP 등록)·#88(Tempo curl)은 사유 코멘트를 달아 close 를 사람에게 넘겼다.
#86(Grafana SA)은 그대로 살았다.
새 리프: #89(agent Gateway) · #90(두 하네스 관측 조회 스킬, #86·#89 선행).

- **#84 를 버리고 새 Feature 를 내는 안**을 버렸다. 문제(agent 가 관측 스택을 못 읽는다)와 인증(Grafana SA)은 그대로고 경로만 바뀌었다 — 컨테이너를 갈아 끼우면 #86 의 소속이 흔들린다.
- **기존 티켓 본문을 고쳐 재사용(#87·#88)** 하는 안을 버렸다. 전제(MCP · Tempo 만 curl)가 사라진 티켓을 고쳐 쓰면 타임라인이 거짓말을 한다. 새로 내고 옛것은 사유와 함께 닫는다.
- **셋을 리프 셋으로** 자르는 안은 앞 논의와 같은 이유로 버렸다 — 갈리는 것은 uid 뿐이다.
- **subagent/fork 방향을 AC 로** 올리는 안을 버렸다. 구현 판단이라 Technical Notes 에 방향만 두었다.

## 하네스 쪽 구현 방향 (결정 아님 — 티켓은 강제하지 않는다)

관측 조회의 원본 출력(로그 수백 줄·시계열)은 주 컨텍스트에 남기지 않는 것이 좋다.
Claude Code 공식 가이드 — *"Delegate these to subagents so the verbose output stays in the subagent's context while only a summary returns"* — 와 같은 방향이다.
후보: 조회 스킬을 subagent 로 실행하거나 fork 형 skill 로 두어, 주 대화에는 요약만 돌아오게 한다.
어느 쪽이 맞는지는 하네스 설계 agent 의 구현 판단이다 — 티켓에는 방향만 적고 방식을 정하지 않는다.
