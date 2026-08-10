---
type: discussion
topic: careerhub
subjects:
  - zitadel
  - masterkey
  - ssm-parameter-store
  - external-secrets
status: active
ref-adrs:
  - ADR-0030
related-tickets:
  - "#50"
---

# Zitadel masterkey — 운영 중 변경(회전)은 어떻게 되는가

## 문제

티켓 #50은 masterkey를 terraform(SSM SecureString) → ExternalSecret 경로로 보존한다.
그렇다면 운영 중에 이 masterkey를 **바꾸고 싶어지면** 어떻게 진행하는가.
"시크릿이니 주기적으로 회전한다"는 일반 관례가 masterkey에도 성립하는지가 실질 질문이다.

## 확인된 사실 (2026-08-10 실측)

**① masterkey는 2단 구조의 바깥 키다.**
masterkey(정확히 32바이트)는 DB의 `system.encryption_keys` 테이블에 저장된 **암호화 키들만** AES256으로 감싼다.
실제 secrets(서명 키·TOTP 시드·IdP client secret·SMTP 자격증명 등)는 그 안쪽 키들이 암호화한다.
근거: `internal/crypto/database/database.go` — `ReadKeys()`가 masterkey로 `system.encryption_keys` 전 행을 복호화해 기동한다.

**② 회전 기능이 없다.**
masterkey를 바꾸는 명령·절차가 Zitadel에 존재하지 않는다.
회전 지원은 open feature request다 — [zitadel/zitadel#6768](https://github.com/zitadel/zitadel/issues/6768), milestone v5, 미착수.
제안된 설계(`masterkey` + `masterkey-old` 플래그로 재암호화)는 아직 구현이 아니다.
공식 문서([Secrets 개념](https://zitadel.com/docs/concepts/architecture/secrets))에도 회전 절차가 없다.

**③ `zitadel mirror`는 회전 수단이 아니다.**
mirror는 `system.encryption_keys`를 **암호문 그대로**(COPY as-is) 복사한다 — 목적지 인스턴스도 같은 masterkey를 써야 한다.
"새 masterkey로 새 인스턴스를 세우고 이전"하는 경로는 그래서 성립하지 않는다.

**④ 그냥 SSM 값을 바꾸면 죽는다.**
masterkey를 SSM에서 교체하면 ExternalSecret이 재동기화하고, 다음 pod 재시작 시 `ReadKeys()` 복호화 실패로 기동 불능이 된다.
데이터는 안 잃지만(구 키로 되돌리면 복구) 서비스는 선다.

## 옵션

### A. 회전하지 않는다 — masterkey를 불변 복구 재료로 취급 (현상 유지)

masterkey를 "회전 대상 시크릿"이 아니라 백업 복구의 필수 재료(TLS CA 키 같은 것)로 취급한다.
노출면이 좁다 — SSM SecureString → ExternalSecret → pod env로만 흐르고, 사람이 값을 볼 일이 없다.
비용: masterkey **유출 + DB 덤프 유출이 결합**하면 안쪽 키 전부가 열린다.
그때의 대응 시나리오가 없으면 이 옵션은 "무대응"과 같다 — 유출 시 경로(B 또는 C)를 지금 문서로 정해두는 것이 이 옵션의 완성이다.

### B. 수동 재암호화 — `system.encryption_keys`만 다시 감싼다

구조상(①) 회전의 실작업은 작은 테이블 하나의 재암호화다:
정지 → DB·구 masterkey 백업 → 각 행을 구 키로 복호화·새 키로 암호화해 UPDATE → SSM 값 교체 → ExternalSecret 재동기화 → 재기동.
비용: **비공식**이다 — AES 포맷이 내부 구현(`crypto.EncryptAESString`)에 묶여 있어 버전 의존이고, 실수 시 안쪽 키 전부를 잃는다.
전제: #49의 백업·복구 실측이 close되어 있어야만 감행 가능하다.
정지 시간이 필요하다(수 분 — 우리 규모에서는 무시 가능).

### C. 공식 지원을 기다린다 — #6768 (v5)

그때까지는 회전 불가를 수용한다(사실상 A와 같은 상태로 대기).
비용: milestone만 있고 미착수라 시점을 기약할 수 없다.

### 비교 축

| 축 | A 불변 취급 | B 수동 재암호화 | C 공식 대기 |
|---|---|---|---|
| 지원 여부 | — (회전 안 함) | 비공식·버전 의존 | 공식 (미래) |
| 실패 시 잃는 것 | — | 안쪽 키 전부 = 전체 secrets | — |
| 정지 시간 | 없음 | 있음 (짧음) | 없음 |
| 유출 대응력 | 시나리오 없으면 0 | 즉시 대응 가능 | 지원 전까지 0 |

우리 규모의 감쇠 요인: 사용자 1명, TOTP 미사용, secrets는 사실상 IdP client secret과 서명 키뿐이다.
유출 시 IdP client secret은 콘솔에서 재발급하면 되고 서명 키는 재생성된다 — **최악의 경우에도 "새 masterkey로 재구축 + secrets 재입력"이 감당 가능한 크기**다.
이 감쇠는 사용자·연동이 늘면 사라진다.

## #50에의 함의 (수렴과 무관하게 성립)

- masterkey는 회전 가능한 시크릿이 아니다 — #50의 SSM 파라미터에 **"교체 금지, 교체는 별도 절차" 성격을 명시**할 가치가 있다(④의 사고 방지).
- SSM 파라미터의 이전 버전 보존(SSM은 버전을 자동 보존한다)이 곧 구 masterkey 백업이다 — terraform에서 값 변경이 일어나도 복구 재료가 남는다.
- B를 언젠가 감행하려면 #49(백업·복구 실측)가 전제다 — 의존 방향이 하나 더 확인된 셈이다.

## 관리 — 회전 불가가 확정되면 무게는 유실 방지와 노출면 축소로 옮겨간다

"절대 잃어버리면 안 되고, 누출돼도 바꾸기 어렵다"는 성질은 회전 대상 시크릿이 아니라 **루트 키 재료**(TLS CA 키 같은 것)의 성질이다.
관리 질문을 두 축으로 가른다: ① 유실(잊어버림) 방지 ② 누출 방지·대응.

### 확인된 현행 구조 (jyoliar-platform-terraform 실측)

- terraform state는 **HCP Terraform(TFC)** 에 산다 — `_modules/tfc_remote_state`가 `tfe_outputs`로 워크스페이스 간 참조.
- SecureString 값은 state에 평문으로 남는다 — 즉 시크릿 사본은 **TFC state + SSM(+자동 버전 보존) + 클러스터 Secret** 세 곳에 존재하게 된다.
- 기존 주입 방식은 두 가지다: 사람이 TFC sensitive 변수로 주입(`oauth/` — `var.google_client_secret`) / terraform이 리소스에서 파생(`alert/` — discord webhook).

### 축 ① 유실 방지 — 사본의 지리

**위안이 되는 구조적 사실: masterkey의 생존 범위는 백업의 생존 범위만큼만 넓으면 된다.**
masterkey는 단독으로 가치가 없고 DB 백업(#49 — S3)과 결합해야 의미가 있다.
백업이 AWS에만 사는 한, masterkey가 AWS(SSM)에 살아 있으면 유실 시나리오가 백업 유실 시나리오보다 넓지 않다.

기본 경로(#50 그대로)만으로 사본이 이미 셋이다:

| 사본 | 위치 | 죽는 조건 |
|---|---|---|
| SSM SecureString (+버전 자동 보존) | AWS | 파라미터 삭제(버전까지 함께 죽음) · AWS 계정 상실 |
| TFC state (버전 이력 보존) | HashiCorp SaaS | TFC 워크스페이스 삭제 |
| 클러스터 Secret | 홈랩 | 클러스터 소실 (→ 어차피 SSM에서 재동기화) |

서로 다른 두 SaaS(AWS·HashiCorp)에 독립 사본이 남으므로 단일 사업자 사고로는 안 잃는다.
잔여 유실 경로는 **사람의 삭제 실수**(terraform destroy·파라미터 교체)뿐이고, 이는 코드로 막을 수 있다:

- SSM 파라미터 리소스에 `lifecycle { prevent_destroy = true }`.
- `description`에 "회전 불가 — 교체·삭제 금지, 절차는 discussion 참조"를 명시 — ④(SSM 값 교체 사고)의 방지선.
- 선택지: 오프라인 제3 사본(패스워드 매니저 1부) — 두 SaaS 동시 상실까지 대비하지만, 그 시나리오에서는 S3 백업도 없으므로 실익이 제한적이다.

**정기 검증이 이미 계획에 있다.**
\#50 AC(클러스터 시크릿 삭제 → ExternalSecret 재동기화로 동일 키 복원)와 #49 AC(복구 실측)가 "키를 잃지 않았음"을 실측하는 유일한 리허설이다 — 이 둘이 유실 방지의 실질 가드다.

### 축 ② 누출 — 단독으로는 안 뚫린다

masterkey 누출 단독으로는 아무것도 열리지 않는다 — **DB 덤프(또는 S3 백업 읽기)와 결합해야** 안쪽 키가 열린다.
그런데 그 두 재료(SSM·S3)가 같은 AWS 계정에 산다.
따라서 masterkey 보관을 AWS 계정 보안 수준 이상으로 과잉 설계할 이유가 없다 — 계정이 뚫리면 어차피 둘 다 나간다.

노출면 나열과 현행 방어:

- SSM 읽기(IAM) — external-secrets의 IRSA 최소 권한으로 한정하는 것이 실무 포인트.
- TFC state 읽기 — 워크스페이스 접근자(현재 1인).
- 클러스터 Secret 읽기 — agent ServiceAccount는 클러스터 RBAC가 Secret 값 읽기를 이미 거부한다.
- SSM `GetParameter`는 CloudTrail에 남는다 — 누출 의심 시 감사 경로가 있다.

### 생성·주입 방식 — 옵션

| | 방식 | 장점 | 비용 |
|---|---|---|---|
| ㉮ | terraform `random_password`로 생성 | 사람 눈을 한 번도 안 거친다 · 전 과정 IaC | 오프라인 사본이 자동으로는 안 생김(필요 시 state에서 추출) |
| ㉯ | 사람이 생성 → TFC sensitive 변수 주입 (oauth 패턴) | 패스워드 매니저 원본이 자연히 남는다 | 사람 손을 거치는 노출 창 · 수동 단계 |
| ㉰ | 사람이 SSM에 수동 심기, terraform은 참조만 | state에 안 남는다 | IaC 밖 수동 단계 — 저장소 관례에 역행 · TFC 사본 상실(유실 방지 약화) |

### 잠정 권고

**㉮ + 가드 2종(prevent_destroy · description 경고) + 리허설(#49·#50 AC 그대로)**.
근거: 유실 방지는 SSM 버전 + TFC state 이력으로 이미 이중이고, 누출 방지는 "사람이 값을 안 본다"가 가장 싼 개선이며, ㉰의 state 회피는 유실 방지를 깎아서 얻는 것이라 이 키의 성질(유실이 누출보다 무섭다)과 반대 방향이다.
오프라인 제3 사본은 선택 — 두 SaaS 동시 상실 시나리오에서는 백업 자체가 없어 실익이 제한적임을 근거로 기본 제외.

## 상태

옵션은 벌어져 있고 수렴은 사람의 판정 대기.
잠정 권고 조합: **A(회전 안 함·불변 취급) + 유출 시 경로 B 지정 + 생성 방식 ㉮ + 가드 2종**.
수렴되면 가드 2종·생성 방식은 #50 본문의 Requirements가 아니라 구현 판단으로 흡수 가능하다 — ADR로 승격할 무게는 아니다(되돌리기 쉬움).
