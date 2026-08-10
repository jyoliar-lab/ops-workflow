---
id: ADR-0034
type: adr
topic: homelab
subjects: [jyoliar-platform-terraform, jyoliar-k8s, argocd]
status: proposed
accepted_at:
references:
superseded_by:
---

# ADR-0034 — terraform은 GitOps가 생성한 인프라에 의존하지 않는다

## Context

홈랩 인프라의 desired는 두 플레인이 나눠 갖는다.
terraform(jyoliar-platform-terraform)은 AWS 측 기반 재료 — IAM·SSM 파라미터·S3·네트워크 — 를 소유한다.
GitOps(jyoliar-k8s · ArgoCD)는 클러스터와 그 위의 워크로드를 소유한다.
지금까지 둘의 관계는 암묵이었다: 클러스터가 ExternalSecret·IRSA로 terraform 산출물을 당겨 쓰는 방향만 실재했다.

외부 IdP 제품(Zitadel) 도입을 검토하며 이 암묵이 처음 시험대에 올랐다.
제품의 내부 구성(클라이언트·브로커 등)을 terraform provider로 관리하는 선택지는, terraform이 클러스터 안에서 GitOps가 띄운 제품의 API에 접속해야 plan이 성립하는 구조다.
방향을 규정하지 않으면 같은 질문이 반복된다 — 클러스터 서비스의 DNS record를 terraform이 들고 있는 기존 사례도 같은 축의 질문이다.

## Decision

**의존은 단방향이다: GitOps(클러스터)가 terraform 산출물을 소비하고, terraform은 GitOps가 생성한 인프라를 알지 못한다.**

terraform의 역할은 seed까지다 — 클러스터가 서기 전에, 또는 클러스터 밖에서 존재해야 하는 재료(자격증명·시크릿 원본·IAM·스토리지)를 만들어 두는 것.
클러스터 내부에서 동작하는 것의 상태 — 워크로드 자체든, 그 워크로드가 노출하는 관리 API 뒤의 구성이든 — 는 terraform의 관할이 아니다.
그것은 GitOps 매니페스트로 선언되거나, 선언할 수단이 없으면 절차 기록과 함께 사람이 수행한다.

terraform plan·apply는 클러스터의 가용성과 무관하게 언제나 성립해야 한다.

## Alternatives

- **방향을 규정하지 않고 사례별로 판단한다.**
  가장 강한 반론: 도구가 지원하면 쓰는 게 실용적이고, 원칙은 유연성을 죽인다.
  버린 이유: 실제로는 사례마다 같은 논쟁이 재연되고, 판단이 사람·시점에 따라 갈려 리소스 배치의 일관성이 무너진다.
  이번 검토에서 제품 provider 옵션이 자연스럽게 후보로 올라온 것 자체가, 규정 없는 상태에서 경계가 침식되는 증거다.

- **제품별 terraform provider로 클러스터 내부 구성까지 terraform이 소유한다.**
  가장 강한 반론: 구성이 코드로 남고, 재현·리뷰가 가능해진다 — 수동 구성보다 우월해 보인다.
  버린 이유: plan이 GitOps 산출물(클러스터 안 제품)의 가용성에 의존하게 되어 부트스트랩 순환이 생긴다 — 클러스터 재구축 시 terraform이 클러스터를 기다리고, 제품 교체 시 terraform이 먼저 깨진다.
  또한 한 제품의 desired가 두 저장소(존재는 GitOps, 내부 상태는 terraform)로 갈라져 어느 쪽도 전체를 말하지 못한다.
  "코드로 남긴다"는 가치는 GitOps 매니페스트나 절차 기록으로도 달성된다.

- **역방향으로 통일한다 — 클러스터가 AWS 리소스까지 소유한다(Crossplane류).**
  버린 이유: 부트스트랩 재료(클러스터 자체가 서기 위해 필요한 것)는 정의상 클러스터가 소유할 수 없어 결국 이중 체계가 남는다.
  홈랩 규모에서 컨트롤 플레인 하나를 더 들이는 운영 비용도 정당화되지 않는다.

## Consequences

- **클러스터 내부 제품의 초기 구성은 terraform 밖이다.**
  선언 수단이 없는 제품(관리 API로만 구성되는 것)은 수동 구성 + 절차 기록으로 남는다 — 재현성이 코드보다 약한 것을 대가로 받아들인다.

- **terraform에 이미 있는 클러스터 종속 리소스는 이관 대상으로 식별된다.**
  클러스터 서비스의 DNS record가 그 예다 — 클러스터의 상태(어떤 서비스가 어디 사는가)를 terraform이 복제하고 있으므로, 클러스터 측 선언(external-dns 등)으로 옮기는 방향이 이 결정의 파생이다.

- **경계 재료는 SSM 파라미터 형태의 접점으로 수렴한다.**
  terraform이 심고 ExternalSecret이 당기는 기존 패턴이 두 플레인의 유일한 공식 접점이 된다 — 접점의 형태가 늘어나는 것은 이 결정에 비추어 심사할 일이 된다.

## 무효화 조건

- 클러스터가 AWS 리소스를 소유하는 컨트롤 플레인(Crossplane류)을 채택하는 경우 — 의존 방향 자체가 재정의되므로 이 결정은 통째로 무효다.
- terraform 없이 부트스트랩이 성립하는 구조(예: AWS 이탈)로 전환하는 경우 — 한쪽 플레인이 소멸하면 방향 규정도 의미를 잃는다.
