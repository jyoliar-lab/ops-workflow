---
type: discussion
topic: careerhub
subjects: [keycloak, zitadel, auth-service]
status: rejected
ref-adrs: [ADR-0030]
---

# Keycloak operator·plugin으로 클레임 훅 타겟의 GitOps 주입이 가능한가

## 문제

Zitadel의 Actions v2 target/execution은 k8s 리소스가 아니라 순수 GitOps 매니페스트로 선언할 수 없다는 것이 직전 조사(260811_2031)의 결론이었다.
Keycloak에는 공식 operator가 있다 — 그렇다면 operator의 CRD나 plugin으로, 클레임 훅의 타겟(발급 시 auth-service를 호출해 클레임을 싣는 접합)을 GitOps 방식으로 외부 주입할 수 있는가.
Keycloak은 ADR-0030에서 기각됐고 기각 축의 하나가 "발급 훅이 Java SPI 인프로세스 배치(jar 빌드)"였다 — operator가 그 축을 우회한다면 재고의 사유가 되는지가 이 조사의 물음이다.

## 조사 결과

질문은 두 층으로 갈라진다 — **능력**(외부 호출형 클레임 훅이 존재하는가)과 **구성**(그 설정을 선언적으로 주입할 수 있는가).
결론부터: **operator는 구성 층의 일부만 다루고, 병목인 능력 층은 건드리지 못한다.**

### ① 능력 층 — 외부 호출형 클레임 훅이 제품에 없다

- Keycloak에는 Zitadel Actions v2 같은 **내장 외부-HTTP 클레임 훅이 없다.**
  토큰 내용 변경의 공식 확장점은 protocol mapper SPI — Java로 빌드해 제품 프로세스 안에 배치하는 JAR이다.
  ADR-0030 ③이 기록한 실행 모델 그대로이며, 이는 operator 유무와 무관한 제품 설계다.
- 정확히 원하는 것을 하는 커뮤니티 확장은 존재한다: [zloom/keycloak-external-claim-mapper](https://github.com/zloom/keycloak-external-claim-mapper) — 원격 HTTP JSON을 fetch해 JWT에 싣는 protocol mapper.
  그러나 실측: **그것도 결국 SPI JAR이고**, star 15 · 최신 릴리스 0.0.3(2025-06) · 개인 유지다.
  채택 시 "우리 Go 코드가 앱에 산다"가 아니라 "남의 Java 코드가 IdP 프로세스 안에 산다"가 되고, Keycloak 분기별 릴리스 추적 의무(ADR-0030 ⑥)가 이 서드파티 JAR의 호환 검증으로 확장된다.
- script mapper(JavaScript)는 preview 기능인 데다 스크립트 배포 자체가 JAR 패키징을 요구하고, 외부 HTTP 호출용 설계가 아니다 — 우회로가 못 된다.

### ② 구성 층 — operator CRD의 선언 범위는 생각보다 좁다

- 공식 operator의 CRD는 둘뿐이다: `Keycloak`(서버 배포)과 `KeycloakRealmImport`.
  **`KeycloakRealmImport`는 create-only다** — 기존 realm의 update·삭제를 지원하지 않고, 제품 쪽 변경을 되읽는 reconcile도 없다([공식 문서](https://www.keycloak.org/operator/realm-import)).
  즉 mapper 설정의 지속적 선언 수단이 아니라 최초 1회 시딩 도구다.
- 확장(JAR) 배치의 공식 방법은 **커스텀 이미지 빌드**다([customizing-keycloak](https://www.keycloak.org/operator/customizing-keycloak)).
  기각 사유였던 "jar 빌드·제품 업그레이드마다 재빌드"가 operator 경로에서 이미지 빌드 파이프라인으로 이름만 바꿔 그대로 남는다.
- 성숙한 선언 수단은 operator 밖에 있다: [adorsys/keycloak-config-cli](https://github.com/adorsys/keycloak-config-cli)(star 1.1k, 2026-07 활동 — 구성 Job 패턴의 기성품)와 [crossplane-contrib/provider-keycloak](https://github.com/crossplane-contrib/provider-keycloak)(star 71, 2026-08 활동).
  이 도구들로 mapper의 **설정**은 선언할 수 있으나, 설정이 가리키는 mapper **구현체**는 여전히 이미지 안 JAR이어야 한다 — 구성 층이 아무리 성숙해도 능력 층의 공백을 메우지 못한다.

## 비교 관찰 — 역설적 대칭

| | Zitadel | Keycloak |
|---|---|---|
| 훅 능력 | **제품 내장** (Actions v2, 외부 HTTP 호출) | 없음 — 서드파티 SPI JAR + 커스텀 이미지 |
| 구성 선언 생태 | 미성숙 (crossplane provider v0.1.x) | **성숙** (config-cli 1.1k★ · crossplane 71★ 활발) |

두 제품은 정확히 반대편이 약하다.
그리고 우리 요구(ADR-0028의 접합: 발급 시 제품→앱 호출)의 병목은 **능력 층**이다 — 구성은 Job으로든 수동으로든 어떻게든 되지만, 능력은 제품이 주지 않으면 인프로세스 코드로 벌충해야 한다.

## 판정 (2026-08-11 · 사람 확인)

- **operator·CRD·plugin은 ADR-0030의 기각 축 ③을 해소하지 못한다.**
  operator가 선언화하는 것은 배포·최초 시딩이지 훅 실행 모델이 아니고, plugin(커뮤니티 mapper)은 기각 사유였던 인프로세스 JAR 그 자체다.
- ADR-0030의 무효화 조건(외부 호출형 훅의 제거·유료화 / 유지보수 상실)에 해당하는 사실 변화도 없다.
- 따라서 **재고·supersede의 사유가 되지 않는다** — 사람이 확인했고, 이 문서는 rejected(재고 안 함)로 닫는다.
- 부수 수확: Keycloak 생태의 keycloak-config-cli는 "IdP 내부 구성을 멱등 Job으로 선언"하는 패턴의 성숙한 선례다 — Zitadel용 구성 Job(260811_2031의 R2)을 설계할 때 참조 모델로 쓸 수 있다.

## 미결

없음 — 부수 수확(keycloak-config-cli 참조 모델)은 티켓 #55 코멘트로 전달됐다.
