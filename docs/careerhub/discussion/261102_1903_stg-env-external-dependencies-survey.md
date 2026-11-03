---
type: discussion
kind: survey
goal: careerhub-env-separation
topic: careerhub
subjects: [zitadel, google-oauth, jyoliar-platform-terraform, mongodb]
status: done
related:
  - docs/careerhub/discussion/261102_1903_renewal-stg-environment-namespace-data-env-axis.md
---

# stg 환경의 외부 의존 — Google OAuth 클라이언트 관리·MongoDB 복사 도구 조사 (2026-11-02)

## 질문

논의 문서의 두 축이 외부 사실을 요구했다.
4-3(stg Zitadel의 로그인 수단)은 Google OAuth 클라이언트를 코드로 만들 수 있는가, 하나의 클라이언트가 여러 환경의 redirect URI를 받을 수 있는가, Zitadel이 브로커 없이 로컬 로그인을 허용하는가를 묻는다.
4-2(수집 데이터 복사 방법)는 mongodump·mongorestore를 클러스터 안 Job으로 돌릴 때 쓸 도구 이미지가 있는가를 묻는다.

## 조사

### 1. Google OAuth 2.0 클라이언트는 API·terraform으로 만들 수 없다

웹 애플리케이션용 OAuth 클라이언트와 동의 화면의 세부(scope·테스트 사용자·redirect URI)는 공개 API가 없고 콘솔에서만 설정된다.
Google Cloud 커뮤니티 스레드(조사일 2026-11-02)는 terraform·gcloud로 만든 동의 화면이 Internal로 고정되고 redirect URI를 코드로 넣을 수 없다고 보고하며, 답변은 provider 저장소에 기능 요청을 내라는 것뿐이다.
> "the consent screen defaults to Internal when created via Terraform or gcloud, and … scopes, test users, and redirect URIs can't be set that way"
> — https://discuss.google.dev/t/oauth-consent-screen-and-oauth-client-automation-limitations/134485

Boost 웹사이트의 OpenTofu 모듈은 같은 한계를 terraform-provider-google#16452·Google 이슈 116182848로 가리키고, 가능한 자동화를 다 한 결과가 "프로젝트 생성·API 활성화까지"라고 적었다.
> "as far as this could be automated given limitations on both Google Cloud Platform and Github's APIs for creating oauth clients/apps"
> — https://gitmirror.hak8or.com/boost/website-v2/src/commit/58b791eee2a9126571609aa44a16466e486c8cdd/development-tofu/modules/google_oauth_client/main.tf

terraform에 있는 유일한 클라이언트 리소스 `google_iap_client`는 IAP 전용이고, brand가 Internal일 때만 동작한다.
Google 문서는 API로 만든 brand가 자동으로 Internal이 되고, Public으로 바꾸면 `identityAwareProxyClients.create()`가 더 이상 동작하지 않는다고 적는다.
> "brands created using an API are automatically configured as internal, and must be manually set to public … identityAwareProxyClients.create() API stops working"
> — https://docs.cloud.google.com/iap/docs/oauth-client-creation

Pulumi 레지스트리(같은 API를 미러)는 IAP OAuth Admin API 폐기로 2026-01-19 이후 `gcp.iap.Client`가 의도대로 동작하지 않는다고 경고한다.
> "after Jan 19, 2026 the gcp.iap.Client Terraform resource will no longer function as intended due to the deprecation of the IAP OAuth Admin APIs"
> — https://www.pulumi.com/registry/packages/gcp/api-docs/iap/client/

### 2. 클라이언트 하나가 여러 redirect URI를 받지만, Google의 권고는 환경별 클라이언트다

Google은 redirect URI를 요청마다 등록 목록과 정확히 대조하고, 와일드카드를 허용하지 않으며, localhost 외에는 HTTPS를 요구한다.
한 클라이언트의 redirect URI 개수 상한은 공식 문서에 없고, 서드파티가 100개라고 적는다(미확인).
> "Google checks the redirect_uri in each request against the registered list … Wildcards are not allowed"
> — https://workos.com/blog/google-oauths-strict-redirect-uri-matching
> — https://discuss.google.dev/t/max-number-of-authorized-redirect-uris/168503

Google 지원 문서는 운영 전환 시 운영 프로젝트에 새 클라이언트를 만들라고 권고한다.
> "create a new OAuth 2.0 client ID for your production app in a production project"
> — https://support.google.com/cloud/answer/6158849

### 3. Zitadel 로그인 정책에는 username/password 허용 스위치가 있다

Zitadel의 LoginPolicy에는 `allowUsernamePassword`·`allowExternalIdp`·`allowRegister` 필드가 있고, 기본 정책 조회 API의 예시 응답이 그 키를 보여준다.
기본값이 true인지, 조직 정책으로 덮는지는 이 조사에서 확인하지 못했다 — 실측(stg Zitadel 기동 뒤 `GetDefaultLoginPolicy`)으로 닫을 일이다.
> — https://zitadel.com/docs/reference/api/management/zitadel.management.v1.ManagementService.GetDefaultLoginPolicy
> — https://hexdocs.pm/zitadel_api/1.0.0-rc.8/Zitadel.Policy.V1.LoginPolicy.html

### 4. mongodump·mongorestore 도구 이미지

MongoDB 피드백 포럼의 사용자 보고는 `mongodb/mongodb-community-server` 이미지가 mongodump·mongorestore·mongosh를 포함한다고 적는다 — 공식 매니페스트가 아니다.
> "the community image ships with mongodump and mongorestore, alongside mongoexport, mongoimport, mongofiles, mongosh"
> — https://feedback.mongodb.com/forums/930808-atlas-cli/suggestions/48857015-include-mongodb-shell-mongosh-and-mongodb-tools

별도 도구 이미지로 `alpine/mongosh`(mongodump·mongorestore 포함으로 문서화)와 `wicos/mongodb-tools`가 있다.
> — https://hub.docker.com/r/alpine/mongosh
> — https://hub.docker.com/r/wicos/mongodb-tools

prod의 `careerhub-mongodb-0` 안에서 `which mongodump`를 치면 즉시 닫힌다 — 이 세션은 pod exec 권한이 없어 실측하지 못했다.

## 논의 문서로 가져가는 것

- Google OAuth 클라이언트 생성은 어떤 길로도 코드가 되지 않는다. 환경별 클라이언트는 환경마다 콘솔 수동 1회를 뜻한다.
- 한 클라이언트에 여러 redirect URI를 둘 수는 있다. Google의 권고는 환경별 클라이언트다.
- Zitadel 로컬 로그인(username/password)은 정책 스위치가 존재한다. 기본 상태는 실측.
- mongodump 도구는 운영 Mongo 이미지에 들어 있을 가능성이 높다(미확인). 없으면 `alpine/mongosh`가 대안이다.
