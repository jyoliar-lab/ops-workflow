---
type: discussion
topic: homelab
subjects: [prometheus, alertmanager, kubelet, longhorn, kube-prometheus-stack]
status: active
---

# Prometheus TSDB 만석과 이중 감시 실패 — 2026-07-30 장애 기록

## 이 문서의 자리

postmortem 타입의 정책·규약이 아직 없어, 장애의 상세 기록을 discussion으로 남긴다. **이 문서는 postmortem의 증류 원천이다** — 규약이 서면 사람이 이것과 원자료(#24·#25 코멘트)를 토대로 postmortem을 저작한다. 그 시점에 이 문서는 `done`으로 전이한다.

- 원자료: [#24](https://github.com/jyoliar-lab/ops-workflow/issues/24) (본 장애 · closed) · [#25](https://github.com/jyoliar-lab/ops-workflow/issues/25) (파생 결함 · open)
- 장애 발생일: **2026-07-30** — 최초 관측 증거는 05:01 UTC (조회 범위 48h 내 첫 실패 로그. 실제 시작은 더 이를 수 있음)

## 증상 → 원인 매핑 (요약)

| 보인 것 | 실제 |
|---|---|
| `[FIRING] KubeAPIDown critical` — "Target disappeared from Prometheus target discovery" | apiserver는 정상. **Prometheus TSDB 볼륨 만석**으로 `up` 샘플 기록이 끊겨 absent 기반 알럿이 오발화 |
| apiserver 하나의 문제처럼 보임 | **전 target 메트릭 수집이 중단**된 상태. KubeAPIDown은 여러 증상 중 가장 먼저 보인 하나일 뿐 |
| "조기 경보(`KubePersistentVolumeFillingUp`)가 안 왔으니 라우팅 문제겠지" | 라우팅은 결백. **k8s v1.34.0 상류 회귀로 `kubelet_volume_stats_*` 메트릭이 클러스터 전체 부재** — 알럿의 데이터 원천이 처음부터 없었다 |

한 문장 요약: **감시 대상(TSDB 디스크)이 죽었는데, 그것을 감시하던 알럿은 이미 수개월 전부터 죽어 있었고, 그 죽음을 감시하는 것은 아무것도 없었다.**

## 인과 사슬 — 두 겹

### 1겹: TSDB 만석 → KubeAPIDown 오발화

1. 설정: `retention: 30d`(시간 기반만) + PVC 30Gi + **`retentionSize` 미설정** (`jyoliar-k8s` baremetal overlay). 30일치 데이터가 30Gi를 넘는 순간 막을 장치가 없는 구조.
2. 운영 110일차, TSDB가 30Gi 도달. WAL 쓰기 실패 시작 (`no space left on device`).
3. **교착**: compaction은 병합 대상만큼의 임시 공간이 필요한데 그 공간이 없어 실패 반복 → 스스로 공간을 회수하지 못함. head compaction이 안 되니 WAL truncate도 안 됨 — 방치하면 영구 지속.
4. 모든 scrape commit·recording rule 기록 실패 → `up` 샘플 부재 → `absent(up{job="apiserver"})` 참 → KubeAPIDown critical 발화.

### 2겹: 조기 경보는 왜 침묵했나

1. kube-prometheus-stack 기본 룰 `KubePersistentVolumeFillingUp`(critical: 가용<10%/5m · warning: 가용<25% + 4일 예측/1h)은 배포되어 있었다 — 이론상 만석 며칠 전 경보가 왔어야 한다.
2. 그러나 룰의 데이터 원천 `kubelet_volume_stats_*`가 **클러스터 전체에서 존재하지 않았다**.
3. 원인: **Kubernetes v1.34.0의 kubelet 메트릭 등록 회귀** ([kubernetes/kubernetes#133847](https://github.com/kubernetes/kubernetes/issues/133847), 수정 [PR #133890](https://github.com/kubernetes/kubernetes/pull/133890) → **v1.34.2 백포트**). CSI 종류 무관(Ceph RBD·Longhorn·EKS 모두 보고). 이 클러스터는 전 노드(8대) v1.34.0 — 정확히 회귀 구간.
4. 결과: PVC 사용률 알럿 4종(용량 2·inode 2)이 1.34.0 도입 시점부터 **무통보로 무력화**. 메트릭 부재를 감시하는 메타 알럿도 없었다(전체 146개 알럿 중 `absent()` 사용 2곳뿐).

## 타임라인 (UTC, 2026-07-30)

| 시각 | 사건 |
|---|---|
| ≤05:01 | WAL 쓰기 실패 최초 관측 (로그 조회 범위 48h 내 첫 기록 — 실제 시작은 더 이를 수 있음) |
| ~05:01+ | 전 target scrape commit 실패 지속 · compaction 실패 반복 (교착) |
| (시각 미상) | AlertManager → `KubeAPIDown` critical 수신 (사람) |
| 12:4x–12:55 | 진단: apiserver 정상 확인 → Prometheus 로그에서 `no space left` 확정 → GitOps에서 `retentionSize` 부재 확인 → #24 발행 |
| 13:07 | 복구 방안 (a) 채택(사람) · PR jae2274/jyoliar-k8s#11 머지 — `retentionSize: 34GB` + PVC 30→40Gi |
| 13:10:59 | 수동 절차(PVC patch → sync → StatefulSet orphan 재생성) 후 pod 재기동 |
| 13:11:42 | WAL 손상 세그먼트(`00005186` — 만석 중 쓰다 만 파일) 자동 수리 |
| 13:12:55 | compaction 성공(3블록 병합, 12.6s) — 교착 해소. 이후 에러 0건, `KubeAPIDown` resolve |
| (이후) | 조기 경보 침묵 조사 → k8s 1.34.0 회귀 확정 → #25 발행 · #24 close(사람) |

## 진단에서 버린 가설들 — 왜 버렸나

이 절이 다음 장애에서 제일 값지다. 같은 증상을 만나면 이 순서로 소거할 수 있다.

| 가설 | 판정 | 버린 근거 |
|---|---|---|
| apiserver 실제 다운 | ❌ | `/healthz` ok · endpoint 3/3 · 노드 8대 Ready — **알럿 문면을 믿지 말고 먼저 대상의 생사부터** |
| (2겹) 알럿 룰 자체가 없다 | ❌ | `KubePersistentVolumeFillingUp` 4종 배포 확인 |
| (2겹) warning이 라우팅에서 버려진다 | ❌ | AlertmanagerConfig가 severity별(critical/warning/info) Slack 라우팅 · `matcherStrategy: None`이라 ns 제한도 없음 |
| (2겹) 발송 실패 | ❌ | Alertmanager 7일 로그 error/fail 0건 |
| (2겹) ServiceMonitor가 메트릭을 drop | ❌ | kubelet SM의 drop은 `(csi_operations\|storage_operation_duration)_seconds_bucket` 히스토그램 버킷뿐 |
| (2겹) kubelet 설정이 수집 비활성 (`volumeStatsAggPeriod: 0`) | ❌ | ansible `KubeletConfiguration`은 `serverTLSBootstrap: true`뿐 — 기본 수집 주기(1m) 유지 |
| (2겹) Longhorn CSI가 `NodeGetVolumeStats` 미지원 | ❌ | v1.7.2 — v1.1.0부터 지원 |
| (2겹) 발화했는데 Slack에서 놓침 / stale-resolve로 위장 | ❌ | Slack `#alerts` 이력 0건 · `ALERTS` 시계열 0건 (사람 확인) |
| (2겹) **메트릭 자체가 태어나지 않음 — k8s 1.34.0 회귀** | ✅ | `kubelet_volume_stats_available_bytes` 전체 부재(사람 확인) + 상류 이슈 #133847과 버전·증상 정확 일치 |

## 복구 기록 (사실)

- 채택안: **(a) PVC 확장 + `retentionSize` 추가** — 데이터 보존. (b) 용량 유지+수동 블록 삭제, (c) PVC 재생성(히스토리 포기)은 기각.
- `retentionSize: 34GB` = 새 PVC 40Gi(≈42.9GB)의 ~79% — WAL이 크기 계산에 포함되므로 PVC 대비 10~15%+ 여유를 둔 값.
- 우려했던 수동 블록 삭제는 불필요했다 — PVC 확장으로 여유가 생기자 compaction이 즉시 성공하며 교착이 스스로 풀렸다.
- WAL 손상(만석 중 쓰다 만 세그먼트)은 기동 시 자가 수리됐고, 폐기된 샘플은 어차피 기록 실패 구간이라 실질 손실 없음.
- 잔여: longhorn replica `actualSize` 59.5Gi > spec 40Gi — sparse 파일은 trim 없이 노드 디스크에서 안 줄어듦. 필요 시 longhorn filesystem trim(RecurringJob) — 미조치.

## 구조적 관찰 — postmortem 증류 후보

1. **시간 기반 retention만으로는 디스크를 지킬 수 없다.** `retention`(시간)과 `retentionSize`(크기)는 별개 안전장치이고, 후자가 없으면 증가율이 예산을 넘는 순간 만석이 필연이다. 크기 상한은 PVC보다 10~15% 낮게(WAL 포함 계산).
2. **만석은 점진이 아니라 절벽이다.** compaction의 임시 공간 수요 때문에 가용 10~15%에서 0%로 분 단위 급락이 가능하다 — "10% 남으면 알럿"은 생각보다 늦다.
3. **absent 기반 알럿은 데이터 경로 장애 때 오발화한다.** `KubeAPIDown`의 문면("target disappeared")은 대상의 죽음과 관측 경로의 죽음을 구분하지 못한다. 이 알럿을 받으면 첫 질문은 "apiserver가 죽었나"가 아니라 "Prometheus가 살아 있나"여야 한다.
4. **알럿의 침묵은 정상과 구분되지 않는다.** 데이터 원천이 사라져도 룰은 에러 없이 빈 결과를 평가할 뿐이다 — 무소식은 희소식이 아니라 무신호다. 핵심 알럿에는 데이터 원천의 존재 자체를 감시하는 메타 알럿(`absent()`)이 짝으로 필요하다. (→ #25 AC ④)
5. **자기관측 사각**: Prometheus 디스크 알럿의 데이터 경로는 죽어가는 Prometheus 자신을 통과한다. 최종 실패 시점에 경보 체계가 스스로 침묵하는 구조라, 클러스터 내부 알럿만으로는 최후 수 분의 사각이 남는다. (완화: warning(4일 예측)이 살아 있으면 실질 위험은 낮음 — 근본 해소는 외부 관측이지만 홈랩 규모에서 비용 대비 판단 필요)
6. **마이너 버전 업그레이드가 감시를 조용히 죽일 수 있다.** 1.34.0 회귀는 기능(볼륨 동작)은 멀쩡하고 관측만 죽였다 — 기능 테스트로는 잡히지 않는 유형. 업그레이드 후 "핵심 메트릭 존재 확인" 체크가 있었다면 수개월의 사각이 없었다.
7. **(하네스 관찰 — staging/ 마찰 로그와 연동)** 진단 agent의 RBAC이 `services/proxy`·`nodes/proxy`를 거부해 Prometheus API·kubelet 노출을 직접 못 본다. 이번엔 로그·desired(코드)·웹 검색으로 우회 확정했지만, "지금 무엇이 노출되는가"는 actual의 질문인데 그 답을 사람(Grafana)에게 위임해야 했다.

## 후속 상태

- [x] 복구: PR jae2274/jyoliar-k8s#11 (머지·검증 완료) — #24 closed
- [ ] **#25 (open)**: ① 전 노드 k8s ≥1.34.2 업그레이드 (target: onpremise-k8s) ② `kubelet_volume_stats_available_bytes` 존재 검증 ③ 부재 감시 알럿 신설 + Slack 라우팅 (target: jyoliar-k8s)
- [ ] longhorn trim (미티켓 — 노드 디스크 압박 시)
- [ ] postmortem 규약 수립 후 이 문서에서 증류 (사람)
