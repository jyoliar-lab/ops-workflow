---
type: discussion
topic: palworld
subjects:
  - palworld-server
status: rejected
---

# 팰월드 1.0 서버를 홈랩 쿠버네티스에

## 문제 재진술

2026-07-10 팰월드 1.0 정식 출시. 최신 버전 전용 서버를 **지속적으로** 돌리고 싶다.
"홈랩 k8s에 띄운다"는 이미 해법의 모양이다 — 진짜 요구는:

- 친구들과 접속할 수 있는 **상시(또는 준상시) 팰월드 서버**
- 게임 업데이트를 따라가는 **낮은 운영 비용**
- 세이브 데이터를 잃지 않는 **영속성·백업**

홈랩 k8s는 그 요구를 담는 그릇 후보 중 하나다. 아래에서 그릇 선택 자체도 옵션으로 벌린다.

---

## 확인된 사실

### 게임 측 (1.0 이후, 웹 조사 2026-07-26)

| 항목 | 내용 |
|---|---|
| RAM | 공식 권장 **16GB** — 소규모 서버도. 메모리는 시간이 지나며 증가(누수성). 풀 인원·대형 거점은 32GB |
| CPU | **단일스레드 바운드** — 코어 수보다 클럭. 고클럭 4~6코어면 충분 |
| 스토리지 | 서버 본체 12~15GB + 세이브·백업, 총 ~30GB |
| 관리 API | **RCON 폐기 예고** → REST API로 전환. 컨테이너 이미지도 v2.1.0부터 RCON deprecated |
| 1.0 신기능 | 서버 클러스터링, 인게임 보이스, 길드 역할 권한, PvP 기본 설정 조정 |
| 포트 | 게임 트래픽 **UDP 8211** (+ REST API TCP 8212) |

### 생태계

- **`thijsvanloef/palworld-server-docker`** — 사실상 표준 이미지. 1.0 지원 확인됨(1.0 런치 스레드 운영 중, 7월에도 활발한 유지보수). 자동 업데이트·자동 백업·스케줄 재시작 기능 내장
- **Helm chart**: `Twinki14/palworld-server-chart`(위 이미지의 공식 chart, v2.1.0) 외 USA-RedDragon·kriegalex·caleb-devops 등 커뮤니티 chart 다수

### ARM 호환성 (2026-07-26 확인 — 결정적 제약)

- 팰월드 서버 바이너리는 **x86_64 전용**. ARM에서는 **box64 에뮬레이션**으로 돌린다. 표준 이미지가 라즈베리파이를 공식 지원(`ARM64_DEVICE=rpi5`)
- ⚠ **1.0은 현재 ARM에서 깨져 있다** — [issue #874](https://github.com/thijsvanloef/palworld-server-docker/issues/874): 기존 box64가 1.0 서버 바이너리를 실행하지 못하고, 신규 box64는 SteamCMD 다운로드가 멈춤. 수리 진행 중(2026-07)
- box64는 대형 게임 업데이트마다 깨질 수 있다 — **매 업데이트가 도박**이 되는 구조적 취약성
- 에뮬레이션 오버헤드: 단일스레드 바운드 게임을 2~4배 감속으로 돌리는 셈

### 클러스터 측 (`jyoliar-k8s` · `jyoliar-k8s-ansible` 읽음)

| 항목 | 현재 상태 | 근거 |
|---|---|---|
| 배포 체계 | ArgoCD + Kustomize(base/overlays) + ApplicationSet 부트스트랩 | `jyoliar-k8s/CLAUDE.md`, `gitops/overlays/baremetal/root-appset.yaml` |
| 앱 배치 | `gitops/base/services/`에 careerhub·ai-agents 두 축 | `gitops/base/services/` |
| 스토리지 | Longhorn (platform 단계 설치) | `platform/base/longhorn/` |
| 인그레스 | nginx-gateway(Gateway API) + cloudflare-tunnel — **전부 HTTP 계열** | `gitops/base/controllers/nginx-gateway/`, `gitops/base/bootstrap/cloudflare-tunnel/` |
| LB | baremetal overlay에서 `type: LoadBalancer` 사용 중, 구현체는 kube-vip | `gitops/overlays/baremetal/system/nginx-gateway-config/nginx-proxy.yaml`, `jyoliar-k8s-ansible/kubernetes/roles/kube-vip/` |
| 노드 | DC1: 마스터 3(101~103) + 워커 3(104~106), 10.0.25.0/24 사설망 | `jyoliar-k8s-ansible/kubernetes/inventory` |
| 노드 하드웨어 | **전부 ARM 라즈베리파이** — 2core/8GB × 2, 4core/16GB × 2 | 사람 확인 (2026-07-26, 코드에 없음) |
| AppProject 게이트 | 외부 Helm repo는 AppProject `sourceRepos`에 사전 등록 필요 | `jyoliar-k8s/CLAUDE.md` |

**핵심 마찰:**

1. **ARM이 결정적 제약이다.** 전 노드가 라즈베리파이 — x86_64 전용 서버를 box64로 에뮬레이션해야 하고, 그 경로가 1.0에서 현재 깨져 있다(위). 고쳐져도 최대 노드(4core/16GB)의 RAM 전부를 요구 스펙이 잡아먹는다.
2. **UDP 노출 경로가 없다.** 현 인그레스는 전부 HTTP용이다. cloudflare-tunnel은 게임 UDP를 못 나른다(Spectrum은 유료). UDP 8211을 밖으로 내는 길을 새로 뚫어야 한다.

---

## 옵션 A — 어디에 띄우나 (그릇)

> 전제 갱신(2026-07-26): 플레이어는 **당장 1인**, 이후 최대 3인. 전 노드 ARM 라즈베리파이.

| | A1. 홈랩 k8s (지금 하드웨어, box64) | A4. x86 워커 증설 후 k8s | A3. 유료 게임서버 호스팅 | A0. 전용 서버 안 띄운다 (로컬 월드·세션 호스트) |
|---|---|---|---|---|
| 성립 여부 | **현재 불가** — 1.0이 box64에서 깨짐(#874). 수리 후에도 매 업데이트가 도박 | 확실히 됨 (네이티브 x86_64) | 확실히 됨 | 확실히 됨 — 1~4인은 세션 호스트로 충분 |
| 금전 비용 | 전기료뿐 | 미니PC(N100급 16GB) 15~25만원 일시 | 월 1~3만원대 (16GB급) | 0 |
| 성능 | 에뮬레이션 2~4배 감속 + 최대 노드 RAM 전부 점유 | 네이티브, 여유 | 여유 | 호스트 PC 성능 |
| 얻는 것 | 홈랩 실험 경험 | 홈랩 경험 + 클러스터에 x86 축 확보(다른 x86 전용 워크로드에도 열림) | 게임만 | 게임만 |
| 잃는 것 | 안정성, 클러스터 절반의 RAM | 초기 비용, 노드 관리 1대 증가 | 통제력 일부, 월 고정비 | **상시 월드 없음** — 호스트가 꺼지면 월드도 멈춤 |

- **A1은 "지금은" 탈락이다.** 성립 자체가 안 된다(#874). 고쳐진 뒤에도 이건 "안정 서버"가 아니라 **"라즈베리파이에서 팰월드가 도나" 실험**으로 자리매김해야 한다 — 그 실험이 목적이면 유효한 선택.
- **A2(k8s 밖 단독 VM)는 소멸했다** — 홈랩 하드웨어가 전부 ARM이라 그릇만 바꿔서는 같은 문제다.
- **A4가 새로 생겼다**: ARM 문제와 RAM 문제를 동시에 풀고, "홈랩 k8s에서 돌린다"는 원래 목표도 지킨다. 유일한 진짜 비용은 하드웨어 값. 이기는 조건: *홈랩에서 돌리는 경험이 목적이고, 일시 비용 지불 의사가 있을 때*.
- **A3가 이기는 조건**: *목적이 게임 자체이고, 상시 월드가 필요할 때.* 1~3인이면 8GB급 저가 플랜도 가능.
- **A0가 이기는 조건**: *당장 혼자이고, 상시 월드(접속 안 해도 거점이 돌아가는 것)가 필요 없을 때.* 팰월드 co-op은 세션 호스트로 4인까지 초대 가능 — 지금 인원 계획(최대 3인)이면 기능적으로 부족함이 없다. **전용 서버가 주는 것은 사실상 "상시 월드" 하나다.**

## 옵션 B — 배포 방식 (A1 전제)

| | B1. 공식 Helm chart (Twinki14) | B2. 직접 매니페스트 (StatefulSet + Kustomize) | B3. 게임서버 오퍼레이터 (Agones 등) |
|---|---|---|---|
| 기존 패턴 정합 | ArgoCD Helm Application — AppProject sourceRepos 등록 필요 | 기존 base/overlays 패턴과 동일 — 이질감 0 | 신규 컨트롤러 도입 |
| 유지 비용 | chart 업데이트 추종 (upstream이 이미지 개정 흡수) | 이미지 태그·env 변경을 직접 추종 | 오퍼레이터 자체가 관리 대상 |
| 유연성 | values로 제한 | 무제한 | 게임서버 다수 운영 시에만 가치 |
| 되돌리기 | 쉬움 | 쉬움 | 어려움(CRD·컨트롤러 잔재) |

- **B3는 버린다**: 서버 1대에 오퍼레이터는 과잉이다. 게임서버가 3종을 넘고 세션 스케일링이 필요해질 때 다시 꺼낸다.
- B1 vs B2는 취향에 가깝고 되돌리기도 싸다 — **one-way door 아님, ADR 불요**. 단 B1 선택 시 sourceRepos 등록을 같은 커밋에 포함(저장소 규칙).

## 옵션 C — UDP 8211 노출 (진짜 갈림길)

| | C1. kube-vip Service LB (UDP) | C2. NodePort + 라우터 포트포워딩 | C3. hostPort/hostNetwork + 노드 고정 | C4. cloudflare-tunnel |
|---|---|---|---|---|
| 성립 여부 | kube-vip UDP 지원 여부 **검증 필요** | 확실히 됨 | 확실히 됨 | **불성립** — 게임 UDP 불가(Spectrum 유료) |
| 기존 패턴 정합 | 높음 (nginx-proxy가 이미 이 경로) | 라우터 설정이 IaC 밖에 생김 | 스케줄링 제약(노드 핀) 발생 | — |
| 장애 시 | VIP가 따라감 | 노드 IP 고정 필요 → 특정 노드 의존 | 노드 죽으면 수동 개입 | — |
| 되돌리기 | 쉬움 | 쉬움 (라우터 설정 잔재만) | 쉬움 | — |

- **C4 탈락 확정.** 나머지는 전부 가역 — **티켓·코드 관할이지 ADR감이 아니다**(되돌리기 한 시간 내).
- 어느 쪽이든 **공유기/방화벽에서 UDP 8211 인바운드**를 열어야 한다(10.0.25.0/24는 사설망). 이건 k8s 밖 작업 — ufw role이 ansible에 있으니 그쪽 관할일 수 있음.
- 공개 방식: **공유기 포트포워딩 선호 확인**(사람, 2026-07-26). VPN 초대제 대안은 접었다 — 당장 1인이라 공개 범위 리스크 자체가 작다. 인원이 늘 때 재론.

## 옵션 D — 영속성·수명 관리

크게 갈리지 않는 축 — 방향만 기록:

- **세이브**: Longhorn PVC(RWO) 30GB+. 이미지 내장 백업(BACKUP_ENABLED) + Longhorn 스냅샷 이중화.
- **메모리 누수 대응**: 이미지 내장 스케줄 재시작 사용. k8s memory limit로 OOM 재시작을 안전망으로 — 단 limit를 너무 조이면 정상 플레이 중 죽는다.
- **게임 업데이트**: 이미지의 UPDATE_ON_BOOT + 스케줄 재시작 조합이 표준 관행. ArgoCD와 충돌 없음(이미지 태그가 아니라 서버 바이너리가 갱신되는 구조).
- **RCON 금지**: 신규 구축이므로 처음부터 REST API(8212)만 쓴다. 폐기 예고된 것에 새로 의존하지 않는다.

---

## 미결 — 사람에게 묻는 것

답변됨 (2026-07-26):

- ~~누가 접속하나~~ → **당장 1인, 이후 최대 3인.** 크로스플레이 요구 없음(현재까지).
- ~~노드 사양~~ → **전부 ARM 라즈베리파이**: 2core/8GB × 2, 4core/16GB × 2.
- ~~공개 방식~~ → **공유기 포트포워딩** 선호.

남은 것:

1. **상시 월드가 필요한가?** 접속 안 해도 월드가 돌아가는 것 — 전용 서버의 유일한 실질 가치. 필요 없으면 A0(세션 호스트)로 족하다.
2. **홈랩에서 돌리는 것 자체가 목적의 일부인가?** 그렇다면 A4(x86 워커 증설) 또는 A1-실험(box64 수리 대기). 아니면 A3 또는 A0.
3. (A4로 기울 경우) **미니PC 지출 의사** — 15~25만원 일시 vs A3 월 1~3만원. 손익분기 약 1년.

## 판정 메모 (ADR 후보)

- 그릇 선택(A)은 세이브 파일만 옮기면 하루 안에 이사 가능 — 그 자체로는 one-way door가 아니다.
- 단 **A4(x86 워커 증설)를 고르면 얘기가 달라진다**: "ARM 단일 클러스터에 x86 노드를 들인다"는 팰월드보다 큰 결정이다(이미지 빌드·nodeSelector 규율·전력 구성에 파급, 하드웨어 지출). **이것이 이 논의의 유일한 ADR 후보다.**
- A1·A3·A0로 수렴하면 ADR 없이 리프 티켓(Task) 몇 개로 충분하다. Epic을 세울 규모가 아니다.

## 수렴 (2026-07-26)

**결론: 전용 서버를 운영하지 않는다. 당분간 로컬 PC(세션 호스트)로만 플레이한다.** → 이 discussion은 `rejected`.

- 홈랩 k8s(A1)는 **성립 자체가 안 된다** — 전 노드 ARM Pi에서 1.0이 box64로 깨져 있고(#874), 고쳐져도 에뮬레이션 감속 + 최대 노드 RAM 전점유라 "상시·안정"과 정면충돌.
- A4(x86 증설)는 15~25만원 + ARM 클러스터에 x86 축을 들이는 ADR급 결정 — 게임 하나를 위해 지불할 근거가 부족했다.
- 유료 호스팅(A3)도 **지금은 진행하지 않는다** — 당장 1인 플레이라 전용 서버의 실질 가치(상시 월드)가 월 고정비를 정당화하지 못한다.
- 로컬 시작이 안전한 근거: 세이브는 사후에 전용 서버로 이전 가능하다(아래 "추가 조사"). 지금의 플레이가 버려지지 않는다.

### 이 문서의 용도 — 전용 서버 재론 시의 재진입점

**나중에 전용 서버가 필요해지면(친구 합류, 상시 월드 욕구) 이 문서로 돌아온다.** 그때 다시 조사하지 않아도 되도록 남긴 것: 그릇 옵션 비교(A축), 그 시점의 유력 후보는 **A3(유료 호스팅)**, 이사 절차는 "추가 조사" 절.

| 옵션 | 되살아나는 조건 |
|---|---|
| A3 (유료 호스팅) | 전용 서버가 필요해지는 순간의 기본 선택지 — 즉시 가능, 월 1~3만원 |
| A1 (Pi + box64) | #874 해소 + 커뮤니티에서 rpi5 1.0 안정 보고. 단 "실험"으로만 |
| A4 (x86 증설) | 팰월드 외에 x86 전용 워크로드가 하나 더 생겨 지출 근거가 합산될 때 |

**파생물 없음**: one-way door가 없어 ADR 불요, 실재하는 클러스터 작업이 없어 티켓도 없다(§5). C(UDP 노출)·D(k8s 운영) 축의 조사는 재론 시를 위해 위에 남긴다.

## 추가 조사 — 로컬 세이브 → 전용 서버 이전 (2026-07-26)

> 질문: 개인 PC(싱글/세션 호스트)로 진행한 세이브를 나중에 전용 서버로 올릴 수 있나?

**가능하다. 1.0에서도 표준 관행이다 — 단 공식 기능이 아니라 커뮤니티 도구 경로다.**

- **월드 자체(거점·팰·게스트 캐릭터)는 폴더 복사로 그대로 이전된다**: `%LocalAppData%\Pal\Saved\SaveGames\<SteamID>\<WorldID>` → 서버의 `SaveGames/0/<DedicatedServerName>`
- **호스트 캐릭터만 GUID 재매핑이 필요하다**: co-op에서 호스트 player ID는 `...0001`로 고정인데, 전용 서버에선 Steam 계정별 ID가 부여된다. 그냥 옮기면 월드는 뜨는데 내 캐릭터에 접근이 안 된다
- **절차**: 서버에 일회용 캐릭터로 1회 접속(새 ID 생성) → 변환 도구로 호스트 `.sav` 재매핑 → 두 파일 업로드 → 재접속
- **도구는 반드시 현행 버전 대응본으로**: TroubleChute 브라우저 변환기(1.0 대응), `quadrantbs/palworld-hostfix-toolkit`(신 포맷 대응). ⚠ 구형 `xNul/palworld-host-save-fix`는 현행 포맷에서 불충분 — 캐릭터는 살아도 **팰이 조용히 전멸**하는 사례 보고
- **주의**: 대형 업데이트마다 세이브 포맷이 바뀌어 도구가 깨진 이력이 있다(2026 여름 업데이트가 기존 도구 전부를 깨뜨림). 이전 직전 **전체 백업 필수** + 그 시점 게임 버전에 맞는 도구인지 확인. Steam 세이브는 단순, Xbox/Game Pass는 추가 변환 필요

**함의 — A0↔A3 경계가 부드러워진다**: 지금 로컬로 시작해도 퇴로가 있다. "전용 서버를 언제 세우나"는 되돌릴 수 없는 갈림길이 아니라 **호스트 캐릭터 재매핑 1회짜리 이사 비용**이다. 역방향(서버→로컬)도 같은 도구군으로 가능.

### 이전을 염두에 둔 플레이 수칙

원리: 이전 시 재작성되는 것은 **호스트 GUID 참조**(캐릭터·길드·팰 소유권·상자 잠금)뿐이고, 서버가 무시하는 것은 **`WorldOption.sav`**(로컬 월드 설정)다. 수칙은 전부 여기서 역산된다.

1. **월드 설정 커스텀 내역을 게임 밖에 기록** — 서버는 `WorldOption.sav`를 무시하고 `PalWorldSettings.ini`를 쓴다. 배율을 바꿨다면 이전 시 ini에서 수동 재현해야 한다. 기본값 플레이면 문제 없음
2. **Steam 버전으로 플레이** — Xbox/Game Pass 세이브는 변환 단계·제약 추가
3. **GUID 참조 구조를 단순하게** — 옮길 월드는 하나, 1인 길드 유지, **관람 우리는 이전 직전 비우기**(구도구 시절 팰 유실 대표 사례 — 팰은 팰박스로)
4. **순정 세이브 유지** — 모드·세이브 에디터는 변환 도구의 포맷 전제를 깨뜨릴 수 있다
5. **월드 폴더 전체 백업 습관**(`Level.sav`·`LevelMeta.sav`·`LocalData.sav`·`WorldOption.sav`·`Players/`) — 특히 게임 업데이트 직전
6. **이전 타이밍**: 대형 업데이트 직후 금지(도구가 포맷 따라잡은 뒤) · 이전 시점에 로컬↔서버 게임 버전 일치

## 출처

- [Host Havoc — Palworld 1.0 Dedicated Server Setup](https://hosthavoc.com/blog/palworld-dedicated-server-setup)
- [Space-Node — Palworld 1.0 Server Requirements 2026](https://space-node.net/blog/palworld-1-0-server-requirements-hardware-2026)
- [dedicatedgameservers.net — Palworld 1.0 Full Launch](https://dedicatedgameservers.net/articles/palworld-in-2026/)
- [G-PORTAL — Palworld 1.0 Update](https://www.g-portal.com/wiki/en/palworld-1-0-update-whats-new-on-your-server-gportal/)
- [thijsvanloef/palworld-server-docker — 1.0 Launch Thread #834](https://github.com/thijsvanloef/palworld-server-docker/issues/834)
- [thijsvanloef/palworld-server-docker — 1.0 arm64/box64 hang #874](https://github.com/thijsvanloef/palworld-server-docker/issues/874)
- [palworld-server-docker — Known Issues (box64·ARM64_DEVICE)](https://palworld-server-docker.loef.dev/known-issues)
- [thijsvanloef/palworld-server-docker README](https://github.com/thijsvanloef/palworld-server-docker)
- [Twinki14/palworld-server-chart (Artifact Hub)](https://artifacthub.io/packages/helm/palworld-server-chart/palworld)
- [Physgun — Move Co-op Save to Dedicated Server](https://physgun.com/blog/game-hosting/palworld/move-palworld-coop-save-to-dedicated-server/)
- [TroubleChute — Palworld Save Converter (1.0 대응)](https://hub.tcno.co/games/palworld/converter/)
- [quadrantbs/palworld-hostfix-toolkit](https://github.com/quadrantbs/palworld-hostfix-toolkit)
- [xNul/palworld-host-save-fix (구형 — 현행 포맷 불충분)](https://github.com/xNul/palworld-host-save-fix)
