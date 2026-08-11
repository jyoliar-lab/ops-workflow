---
type: discussion
topic: careerhub
subjects: [zitadel, auth-service, argocd, jyoliar-k8s]
status: done
ref-adrs: [ADR-0031, ADR-0034]
---

# Zitadel 발급 훅 target/execution 등록 — GitOps 경로 조사

## 문제

ADR-0031(발급 시점 클레임 주입)의 훅 타겟으로 auth-service를 Zitadel에 등록해야 한다.
Actions v2의 target·execution은 k8s 리소스가 아니라 Zitadel DB 안의 상태다 — kustomize·helm이 선언할 대상 자체가 아니다.
Zitadel은 jyoliar-k8s(ArgoCD + helm chart 10.0.4)로 배포되어 있고, terraform 경로는 ADR-0034(proposed)가 배제한다: 클러스터 안 제품의 관리 API 뒤 구성은 terraform 관할이 아니다.
그렇다면 이 등록을 GitOps로 해결한 선례가 있는가 — 이 문서는 그 조사 결과다.

## 전제 사실

- helm chart(10.0.4)는 배포·초기화(FirstInstance)까지만 다룬다.
  Actions 리소스 선언 기능은 없다.
  단, `FirstInstance.Org.Machine`으로 admin machine user를 만들고 그 키를 k8s Secret(`zitadel-admin-sa`)으로 써 주는 부트스트랩은 chart가 지원한다 — 어떤 자동화 경로든 자격증명은 여기서 나온다.
- Zitadel 리소스용 공식 operator/CRD는 없다.
  구 operator(zitadelctl 시대, discussion #2117)는 폐기됐다.
- Zitadel 팀의 공식 입장(discussion #7816): 내부 리소스 구성은 "API 또는 terraform 같은 IaC 도구"로 하라.
  즉 1차 선언 수단은 공식 terraform provider 하나뿐이고, actions v2는 v2.3.0부터(action_target · action_execution_* · action_target_public_key) 지원된다.

## 조사 결과 — 같은 고민의 계보

같은 고민은 실재하고, 해법의 계보는 셋이다.

### ① Crossplane provider — terraform provider를 CRD로 승격

terraform provider를 Upjet으로 감싸 Zitadel 내부 리소스를 k8s CRD로 노출하는 시도가 커뮤니티에 반복적으로 있었다.

| 저장소 | 시기 | 상태 |
|---|---|---|
| Smana/provider-zitadel | ~2024-11 | 방치 |
| infitx-org/zitadel-crossplane-provider | ~2025-06 | v0.1.0. **actions 계열 미포함** 확인 |
| didactiklabs/provider-zitadel (fork: banhcanh, v0.9.0) | ~2025-06 | 개인 프로젝트. banhcanh 저장소는 현재 404 |
| vhdirk/crossplane-provider-zitadel | ~2025-07 | v0.1.0, star 0 |
| **crossplane-contrib/provider-upjet-zitadel** | **2026-04 생성, 2026-07 활동** | **contrib 공식 org. 아래 상술** |

개인 시도들이 난립하다가 2026-04에 **crossplane-contrib 공식 org로 수렴**했다는 것이 조사의 핵심 발견이다.

**crossplane-contrib/provider-upjet-zitadel 실측:**

- terraform provider **v2.12.8**을 감쌌고, 리소스 213종을 CRD로 생성한다.
- **actions v2 계열 8종이 전부 포함된다**: `zitadel_action_target` · `action_execution_event/function/request/response` · `action_target_public_key` · `trigger_actions` · (v1) `action`.
- 즉 이 provider를 들이면 target/execution이 **문자 그대로 GitOps 매니페스트(CRD)** 가 되고, drift 감지·조정까지 컨트롤러가 한다.
- 성숙도는 초기다: v0.1.1(2026-04)이 마지막 릴리스, star 0.
  단 Upjet 생성물이라 코드 대부분이 기계 생성이고, 신뢰의 실체는 감싼 공식 terraform provider 쪽에 있다.
- 실사용 흔적: hops-ops/crossplane-zitadel-provider-stack 같은 배포 스택 패키지가 존재한다.

### ② in-cluster IaC 컨트롤러 — IaC 실행 자체를 클러스터가 소유

terraform/Pulumi 코드는 유지하되, plan·apply를 클러스터 안 컨트롤러가 GitOps로 조정하는 패턴.

- Pulumi Kubernetes Operator로 Zitadel 내부 구성을 관리한 공개 사례가 있다(2025-05, amazinglyabstract.it).
  chart의 machine user Secret으로 부트스트랩하는 경로까지 동일하다.
  저자 스스로 operator 미성숙을 한계로 기록했고, actions는 다루지 않았다.
- flux-iac/tofu-controller가 같은 축의 도구다(terraform HCL을 클러스터가 조정).
  Zitadel에 적용한 공개 사례는 찾지 못했다.
  또한 현 스택은 ArgoCD라 Flux 계열 도입은 별도 비용이다.

### ③ API 호출 Job — 반쪽 선언

ArgoCD PostSync hook Job으로 배포 후 API를 호출하는 일반 패턴은 흔하다.
그러나 **Zitadel target/execution을 이 패턴으로 등록한 공개 사례는 찾지 못했다.**
선례 부재가 불가능을 뜻하지는 않는다 — idempotent 스크립트만 있으면 성립한다.
다만 선례가 없다는 것은, 이 조합을 원한 사람들이 대체로 ①(CRD화)이나 terraform으로 갔다는 방증이기도 하다.

## 옵션 재정리

앞선 논의의 A(수동)·B(Job)에 조사 결과를 얹으면 넷이다.

| | 모양 | 선언성 | 비용 |
|---|---|---|---|
| **R1. 수동 + 절차 기록** | Console/API 1회, 절차는 문서로 | 없음 | 재구축 시 수동 단계 부활. ADR-0034가 명시한 기본 경로 |
| **R2. config Job** | ArgoCD hook Job이 API를 idempotent 호출 | 반쪽(원하는 상태는 git, 수렴은 스크립트 몫) | 기계장치 자작·유지. drift 감지 없음. 선례 미발견 |
| **R3. Crossplane provider-upjet-zitadel** | target/execution이 CRD·매니페스트가 됨 | 완전(drift 조정 포함) | **Crossplane 자체 도입**이 선행. provider v0.1.x |
| **R4. in-cluster IaC 컨트롤러** | tofu-controller류가 terraform HCL을 조정 | 완전 | Flux 계열 컨트롤러 도입. ArgoCD 스택과 이질 |

## ADR-0034에 비춘 관찰

- R3·R4는 ADR-0034의 **방향과는 합치한다** — 클러스터 안 제품의 구성을 클러스터(GitOps)가 소유하는 것이고, terraform(외부 plan)은 여전히 모른다.
- 그러나 0034가 Crossplane류 대안을 버린 이유 — "홈랩 규모에서 컨트롤 플레인 하나를 더 들이는 운영 비용" — 는 R3에 그대로 적용된다.
  0034가 버린 것은 "클러스터가 AWS 리소스를 소유"하는 전면 채택이므로 범위는 다르지만, 비용 논거는 같다.
- **target 1개 + execution 소수를 위해 Crossplane을 들이는 것은 배보다 배꼽이다.**
  단 Zitadel 내부 구성은 이것으로 끝나지 않는다 — OIDC 클라이언트 등록·조직·소셜 IdP 브로커가 같은 성질의 상태다.
  그 총량이 커지면 R3의 고정비가 상각된다.
- R2가 ADR-0034의 "GitOps 매니페스트로 선언"에 해당하는가는 해석의 여지가 있다 — Job은 매니페스트지만 상태 수렴은 스크립트 몫이다.
  0034 accept 심사 때 이 사례를 문안에 비춰볼 가치가 있다.

## 잠정 관찰 (판정 아님)

- 지금 규모(target 1 + execution 수 개)만 보면 R1이 가장 싸고, ADR-0034의 기본 경로와도 합치한다.
- 재구축 재현성을 코드로 갖겠다면, 선례가 수렴한 곳은 R2가 아니라 R3(CRD화)다.
- 판정 축은 결국 **"Zitadel 내부 구성의 최종 총량"** 이다 — 이 축의 값은 클라이언트 등록·브로커 구성이 구체화되는 시점에 정해진다.

## 판정 (2026-08-11 · 사람)

**R2를 우선한다 — 가급적 멱등 구성 Job으로 처리하고, Job에 담기 부적합한 1회성 항목만 수동 + 절차 기록으로 남긴다.**
terraform 경로 배제는 확정이다 — jyoliar-platform-terraform은 이 작업의 수정 대상이 아니다.
잠정 관찰(R1 우선)과 달리 사람은 재구축 재현성 쪽에 무게를 실었다 — 수동 절차의 부활 비용을 코드(Job)로 선지불한다.
R3(Crossplane CRD화)는 현 규모에서 배제하되, Zitadel 내부 구성 총량이 커지면 재평가한다.

파생: 티켓 #55 본문·저장소 절 갱신(target: jyoliar-platform-terraform → jae2274/jyoliar-k8s, terraform 수정 금지 명문화).

## 남긴 것 (0034 심사·후속 지점으로 넘김)

- R2(구성 Job)가 ADR-0034의 "GitOps 매니페스트로 선언"에 해당하는지 — accept 심사 시 문안에 비춰 확인.
- R3 재평가 시점 — OIDC 클라이언트 등록·브로커 구성이 구체화되어 수동/Job 항목 총량이 보이는 때.
