---
type: discussion
topic: careerhub
subjects: [zitadel, auth-service, careerhub-api-composer, careerhub-web, careerhub-userinfo-service, jyoliar-k8s, jyoliar-platform-terraform, jwt, oidc, postgresql, mongodb]
status: done
ref-adrs: [ADR-0027, ADR-0028, ADR-0029, ADR-0030, ADR-0031]
tickets-issued: "Epic #43 · Feature #44 #45 #46 #47 · 리프 #48~#62"
---

# Zitadel 위임 Epic의 일 쪼갬 — 왜 이렇게 갈랐고, 무엇을 버렸나

발행된 트리 자체는 GitHub(#43)이 자기서술한다. 여기 남기는 것은 **쪼갬의 판단과 버린 대안**이다.

발행 전 정찰: 5개 저장소군(auth-service · api-composer/goutils · userinfo/front/web · jyoliar-k8s/onpremise-k8s/terraform)을 읽고 쪼갰다. 티켓 본문의 사실 주장(Atoi 6~7곳, 인덱스 선언/생성 분리, 백업 부재 등)은 전부 그 정찰의 인용이다.

## 1. Feature 4개 = sub-ADR 4개 — 규모가 아니라 축

Feature는 ADR 계층을 베낀 것이 아니라, **독립적으로 뒤집힐 수 있는 하위 축**마다 세웠다. 우연히 sub-ADR(0030·0029·0031)과 referenced ADR(0027)이 정확히 그 축들이었다. ADR-0028 자체의 직접 귀결 둘(careerhub-web 로그인 재작성 #59 · auth-service 인증 경로 철거 #61)은 어느 하위 축에도 속하지 않아 Epic 직속 리프로 냈다 — Feature를 하나 더 세우면 결정 없는 빈 컨테이너다.

## 2. 버린 쪼갬

- **CNPG 백업(#49)을 Epic 밖 독립 리프로 내는 안.** 백업은 Zitadel 여부와 무관하게 기존 auth 데이터에도 즉시 가치가 있다 — 논리상 독립이다. 그래도 Feature #44 안에 뒀다: 이 계획의 크리티컬 패스 위에 있고(masterkey 복구 전제 — ADR-0030 Consequences), 티켓 컨테이너는 공동무효 단위가 아니라 실행 흐름의 묶음이기 때문. ADR이었다면 갈랐다.
- **careerhub-web 로그인(#59)을 Epic #6(프론트 재작성) 아래 두는 안.** 화면의 지붕은 #6이 맞다. 그러나 이 리프의 근거(ADR-0028 Consequences)와 선행(#55 Zitadel 클라이언트)이 전부 이 Epic에 있고, sub-issue 부모는 하나뿐이다 — 인증 배선의 축을 따라 #43에 뒀다. #6·#8과의 관계는 Epic·리프 Context에 명시했다.
- **masterkey(#50)를 배포(#53)에 접는 안.** 저장소가 갈리고(terraform 선행) 병렬 가능해서 갈랐다. 반면 **CheckHasRole 500→401 정정은 별도 Bug로 내지 않고 #57에 접었다** — 그 미들웨어 자체가 검증 전환으로 재작성되는 코드라, 별도 티켓은 같은 줄을 두 번 파는 일이다.
- **api-composer 검증 전환(#56)을 구현/테스트/spec 3분할하는 안.** 정찰이 항목 10개를 냈지만, alg confusion 차단·iss/aud·테스트 하네스는 전환과 분리 불가능한 한 PR의 면들이다 — Requirements로 접었다.
- **"공용 검증 모듈을 어디 둘까(goutils vs 신규)"를 선행 결정(ADR)으로 세우는 안.** 되돌리기 한 시간 미만 — 임계선(§4②) 미달. ADR-0029가 이미 "공통 모듈로 관리"를 걸었고 거주지는 코드 관할. #56의 구현 판단으로 강등했다.
- **mailer gRPC `GetUserEmails` 무인증을 지금 티켓으로 내는 안.** 실재하는 공백이지만 이 Epic의 축(인증 위임)과 별건이고, 클러스터 내부 한정이라 즉효도 아니다 — Epic Out of Scope에 명시하고 사람 판단으로 넘겼다. Naver 연동해제 콜백도 같다(전환 후의 새 일감 — ADR-0028 Consequences).
- **탈퇴·정지 상태 정합(제품↔앱 전파, ADR-0028 Consequences의 "주기 조정이든 이벤트 수신이든")을 리프로 내는 안.** 방식이 코드 관할로 미뤄져 있고 선행 결정·실측이 없다 — 지금 내면 투기적이다. Epic이 닫히기 전 어딘가에서 다시 올라온다.

## 3. 의존 사슬의 판단

`#49·#50·#51(조사) → #53(배포) → #55(구성) → {#56→#57, #58→#60, #59} → #61(철거) → #62(컷오버)`. #52(클레임 endpoint)만 무의존 — Zitadel 없이 짓고 테스트할 수 있는 유일한 앱 코드다. 컷오버(#62)를 철거(#61) 뒤에 둔 것은 두 배포가 같은 시크릿을 envFrom으로 공유해 원자적으로 못 떼기 때문이다(정찰 확인).

#59에 기존 티켓 **#8을 선행으로 걸었다** — 토큰 접근 단일 모듈 위에 OIDC 배선을 얹는 순서.

## 4. accept 심사(docs-tickets)에 넘기는 관찰

- **ADR-0030 Context의 배치 전제("기존 호스트 아래 경로")가 실측에서 걸린다.** `/auth` PathPrefix는 auth-service가 점유 중이고, Zitadel은 서브패스 서빙 미지원으로 보인다. 다만 Decision은 배치 경로를 코드·설정 관할로 명시적으로 남겼으므로 **결정 자체는 흔들리지 않는다** — Context의 주변 서술이 부정확할 수 있을 뿐. pairwise sub 보존의 진짜 조건(redirect_uri 호스트 vs 제품 호스트)은 #51이 판정한다.
- ADR-0028 Consequences가 지목한 즉효 결함(토큰 원문 로깅)은 실재를 확인하고 Bug #48로 냈다 — proposed 단계에서 이미 이행이 시작된 셈이다.
