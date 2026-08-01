---
type: discussion
topic: homelab
subjects: [prometheus, grafana, kube-prometheus-stack]
status: active
---

# 룰이 참조하는 메트릭의 부재 감지 — 공식 기능·공식 가이드·대안 도구 조사

## 계기

2026-07-30 장애(→ `260730_2245_prometheus-tsdb-full-double-monitoring-failure.md`)에서 알럿 룰의 데이터 원천(`kubelet_volume_stats_*`)이 수개월간 부재했음에도 아무것도 통보하지 않았다. #25 AC④(타겟 absent 알럿)를 넘어 **범용 감지 방안**을 찾는 과정에서 pint를 먼저 조사했고(사이드카 결합 문제 → CronJob+relaxed 파서로 수렴 중이었음), 이 문서는 그 후속 질문 둘을 다룬다:

1. **Prometheus 자체가 공식으로 제공하는 기능은 없는가?**
2. **Prometheus 개발자들은 이 케이스를 어떻게 해결하라고 가이드하는가?**

## ① Prometheus 공식 제공 — "자동 감지"는 없고, 명시 도구만 있다

**결론: 룰이 참조하는 시계열의 존재를 자동 검증하는 기능은 서버·promtool 어디에도 없다.** 빈 셀렉터는 에러가 아니라 정상 평가다(공집합 의미론). promtool은 문법 검사(`check rules`)와 합성 데이터 유닛테스트(`test rules`)까지만 — 라이브 데이터 대조는 없다.

공식 제공물은 "부재를 명시적으로 다루는 재료"다:

| 재료 | 성격 |
|---|---|
| `absent()` / `absent_over_time()` | 부재→발화 반전 함수. **기대(무엇이 있어야 하는가)는 룰 저자가 명시**해야 한다 |
| `up` | job/instance 수준 생존 — target 소멸·스크레이프 실패용 |
| `scrape_samples_scraped` · `scrape_series_added` | 스크레이프당 샘플 수 메타메트릭. 급감 카나리아의 재료 |

이 부재는 누락이 아니라 **설계 입장**으로 읽힌다: 시스템은 "지금 없는 메트릭" 중 어느 것이 사고인지 알 수 없다(대상이 정당하게 0개인 경우와 구분 불가). 기대 집합은 어딘가에 명시되어야 하고, Prometheus는 그 명시 수단(absent 계열)까지만 제공한다.

## ② 개발자 가이드 — Robust Perception 3계층 (Brian Brazil, 코어 메인테이너)

사실상의 공식 관행 문서다. 계층이 낮을수록 근본 해법:

**계층 0 — 계측에서 고친다: "메트릭은 항상 존재하게 하라"** ([Existential issues with metrics](https://www.robustperception.io/existential-issues-with-metrics/))
앱 시작 시 메트릭을 0으로 초기화해서 명멸 자체를 없애는 것이 1순위 권고. 쿼리 워크어라운드(`or up * 0`로 결측 주입)는 "not exactly trivial"한 차선. → **우리 사례엔 적용 불가**: kubelet은 우리가 계측하는 코드가 아니고, 회귀는 상류에서 왔다. 이 가이드는 "자기 앱"에는 유효하지만 서드파티 exporter의 부재에는 무력하다.

**계층 1 — job 수준: `absent(up{job="..."})`** ([Absent alerting for jobs](https://www.robustperception.io/absent-alerting-for-jobs/))
target 자체의 소멸. kube-prometheus-stack의 `KubeAPIDown`류가 이 패턴이다.

**계층 2 — target은 사는데 특정 메트릭이 사라짐: `unless`** ([Absent alerting for scraped metrics](https://www.robustperception.io/absent-alerting-for-scraped-metrics/))
```promql
up{job="myjob"} == 1 unless my_metric
```
**이번 장애가 정확히 이 계층이다.** `up==1` 가드가 내장되어 target 다운 시 이중 알럿이 안 나고, `absent()`와 달리 인스턴스별로 잡힌다.

우리 케이스 적용 시 뉘앙스 하나: volume stats는 **PVC가 attach된 노드에만** 존재하는 게 정상이라, 인스턴스별 `unless`는 PVC 없는 노드에서 오탐이 난다. 클러스터 수준 집계가 필요하다:
```promql
count(up{job="kubelet", metrics_path="/metrics"} == 1) > 0
  unless count(kubelet_volume_stats_available_bytes) > 0
```
→ **"기대의 스코프"(인스턴스별인가, 클러스터에 하나라도인가)는 메트릭마다 다르다** — 범용 룰이 어려운 또 하나의 이유.

## ③ 대안 도구 생태계

| | 방식 | 룰 입수 경로 | 상주/CI | 부재 통보 경로 | 활성도(2026-07) |
|---|---|---|---|---|---|
| **pint** (Cloudflare) | 룰 파일 lint + 라이브 대조(`promql/series`) | **파일** (CRD는 relaxed 파서) | watch 데몬 + CI | `pint_problem` 메트릭 or exit code | ★1.0k, 활발 |
| **promcheck** (cbrgm) | 룰의 셀렉터별 라이브 probe | **실행 중 Prometheus API에서 직접** (파일 불요!) | **exporter 모드** + CLI | `promcheck_validation_selectors_total{status="failed"}` | ★95, 커밋 최근 |
| **promruval** (FUSAKLA/Seznam) | 룰 메타데이터·표현식 검증, v2+ 라이브 `/api/v1/series` 대조 | 파일 (CRD 지원 언급 없음) | **CI 전용** | exit code | ★167, 유지됨 |
| **Grafana-managed alerts** | 알럿 평가를 Grafana로 이관 — **NoData가 1급 상태** | — | 상주 | NoData → 알림 라우팅 설정 가능 | 공식 기능 |
| **무도구 PromQL** | `unless` 패턴 N개(계층 2) / offset 차분 / `scrape_samples_scraped` 급감 카나리아 | — | 룰 자체 | 일반 알럿 | — |

### promcheck — 구조적으로 주목

> "run promcheck as a Prometheus exporter, scrape its metrics and alert in case selectors do not return results anymore" · "validate rules from a running Prometheus instance"

**룰을 Prometheus API(`/api/v1/rules`)에서 직접 가져오므로 파일 접근이 아예 필요 없다** — pint 논의의 핵심 난점(rulefiles ConfigMap 이름 결합 / CRD 덤프 단계)이 **문제 자체로서 소멸**한다. 독립 Deployment + ServiceMonitor + 메타 알럿 1개로 완결. k8s 배포 예제 동봉.

유보: 프로젝트 규모가 작다(★95, 개인 메인테이너). 채택 전 확인 필요 — 검사 주기·부하 특성, false positive 처리(정당한 빈 셀렉터의 화이트리스트), kube-prometheus-stack 환경 동작 검증.

### Grafana NoData — 큰 이동의 대가

Grafana-managed 알럿은 평가 결과가 비면 **NoData 상태**로 전이하고 이를 알림으로 라우팅할 수 있다 — "부재의 1급 취급"이라는 점에서 유일하게 언어 의미론을 벗어난 해법. 그러나 알럿 정의 146개를 PrometheusRule에서 Grafana로 이관하는 것이 전제라, 이번 문제 하나를 위한 이동으로는 과대하다. 신규 알럿부터 Grafana-managed로 만드는 점진 경로는 있을 수 있으나 이원화 비용이 생긴다.

### 무도구 카나리아의 한계 (정직하게)

`scrape_samples_scraped` 급감 감지는 **대량 소실만** 잡는다. 이번 회귀의 소실분은 kubelet의 수천 샘플 중 ~112개(16 PVC × ~7 메트릭)로 수 % 수준 — 노이즈에 묻힌다. offset 차분(`group by (__name__) (... offset 1d) unless ...`)이 이름 단위라 더 정확하지만, 명멸 메트릭 오탐과 쿼리 비용 관리가 필요하다.

## 수렴 관찰 (판정은 사람)

기대 집합의 조달처로 다시 정리하면:

- **사람 목록** — 공식 가이드의 `unless`/`absent` N개. 핵심 몇 개면 충분할 때 이긴다. 목록 노후화가 약점 (#25 AC④는 이것의 최소형)
- **룰 자신** — pint(파일 경유) vs **promcheck(API 직접)**. 룰이 늘어도 자동 커버. 상시 감시가 필요할 때 이긴다. promcheck가 결합 면에서 우위, 프로젝트 신뢰도 면에서 pint가 우위
- **과거의 자신** — offset 차분. 도구 도입이 부담일 때의 절충
- **평가기 교체** — Grafana NoData. 이 문제만으로는 과대

이전 pint 논의의 잠정 결론(D안: CronJob + relaxed)에 대해 이 조사가 바꾸는 것: **promcheck exporter가 D안과 douban식 Deployment의 장점(결합 제로 + 상시 + 룰명 라벨)을 동시에 갖는 후보로 새로 등장했다.** 남은 판단거리는 "소규모 프로젝트 의존을 받아들일 것인가"와 "pint의 성숙도를 결합 비용을 치르고 살 것인가" 사이의 트레이드오프다.

## 미결 → 수렴

- [x] **방향 확정(사람): promcheck exporter 채택** → Task #26 발행 (2026-07-31). #25(k8s 업그레이드)보다 우선 진행 — 업그레이드 전의 실재 사각(`kubelet_volume_stats_available_bytes` 부재)을 promcheck의 실검증 대상으로 삼는다
- [ ] promcheck 실검증 — #26의 AC로 이관 (시험 배포 → 고의 부재 룰 발화 확인 → 화이트리스트 동작 확인)
- [ ] #25 AC④(전용 absent 알럿)의 대체 여부 — #26 완료 후 재평가 (사람)

## Sources

- [Prometheus docs — querying functions (absent/absent_over_time)](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Robust Perception — Absent alerting for jobs](https://www.robustperception.io/absent-alerting-for-jobs/)
- [Robust Perception — Absent alerting for scraped metrics](https://www.robustperception.io/absent-alerting-for-scraped-metrics/)
- [Robust Perception — Existential issues with metrics](https://www.robustperception.io/existential-issues-with-metrics/)
- [cbrgm/promcheck](https://github.com/cbrgm/promcheck)
- [FUSAKLA/promruval](https://github.com/FUSAKLA/promruval) · [validations 문서](https://github.com/FUSAKLA/promruval/blob/master/docs/validations.md)
- [cloudflare/pint](https://cloudflare.github.io/pint/) (전 조사: relaxed 파서로 PrometheusRule 직접 파싱 — #460·#876)
- [douban/charts — pint Helm 차트](https://github.com/douban/charts/tree/master/charts/pint) (전 조사)
