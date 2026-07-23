"""GitHub 호출 공용 모듈. 표준 라이브러리(subprocess)만 쓴다.

**GraphQL은 여기 갇혀 있다.** 프롬프트에 쿼리를 적어 두면 agent가 매 호출마다 변형하다 깨뜨린다.
필요한 쿼리는 함수로만 노출한다.

gh CLI 를 쓰는 이유: 인증(토큰 저장·갱신)을 다시 구현하지 않기 위해서다.
"""
import json
import subprocess

from opsdoc import die


def _run(args):
    try:
        p = subprocess.run(args, capture_output=True, text=True)
    except FileNotFoundError:
        die("거부: gh CLI 가 없다. GitHub 조작은 gh 인증에 얹혀 있다.")
    if p.returncode != 0:
        die("거부: GitHub 호출 실패 (exit %d)" % p.returncode,
            "  $ " + " ".join(args[:3]) + " …",
            (p.stderr or p.stdout).strip())
    return p.stdout


def graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", "query=" + query]
    for k, v in variables.items():
        # 플래그를 **파이썬 타입으로** 가른다.
        #   -F : 값을 형에 맞춰 넘긴다 (숫자·불리언). Int! 변수(이슈 번호)에 필요하다.
        #   -f : 언제나 raw string.
        # 문자열에 -F 를 쓰면 안 된다 — 숫자꼴 문자열이 Integer 로 넘어가 String! 이 거부한다.
        # Project 의 SingleSelect 옵션 id 는 실제로 숫자꼴이 나온다 (Backlog = "53153770").
        args += ["-F" if isinstance(v, (int, bool)) else "-f", "%s=%s" % (k, v)]
    payload = json.loads(_run(args))
    if payload.get("errors"):
        die("거부: GraphQL 오류",
            *["  " + e.get("message", str(e)) for e in payload["errors"]])
    return payload["data"]


def split_repo(repo):
    if "/" not in repo:
        die("거부: --repo 는 owner/name 꼴이다 (받은 값: %s)" % repo)
    owner, _, name = repo.partition("/")
    return owner, name


def create_issue(repo, title, body_file):
    """gh issue create — 본문·제목만. Issue Type 은 여기서 못 정한다(플래그가 없다)."""
    url = _run(["gh", "issue", "create", "--repo", repo,
                "--title", title, "--body-file", body_file]).strip().splitlines()[-1]
    number = url.rstrip("/").rsplit("/", 1)[-1]
    if not number.isdigit():
        die("거부: 이슈 번호를 읽지 못했다 — gh 출력: %r" % url)
    return int(number), url


def issue_view(repo, number):
    """이슈 번호 → (node id, Issue Type 이름, 본문). 타입이 없으면 이름은 None.

    본문까지 읽는 이유: 사후 갱신(set-repos.py)은 기존 본문의 절을 교체해야 한다 —
    본문 없이 덮어쓰면 발행 이후 사람이 고친 산문이 날아간다.
    """
    owner, name = split_repo(repo)
    data = graphql(
        "query($o:String!,$r:String!,$n:Int!)"
        "{repository(owner:$o,name:$r){issue(number:$n){id body issueType{name}}}}",
        o=owner, r=name, n=number)
    issue = (data.get("repository") or {}).get("issue")
    if not issue:
        die("거부: %s#%d 를 찾지 못했다." % (repo, number))
    return issue["id"], (issue.get("issueType") or {}).get("name"), issue.get("body") or ""


def issue_node(repo, number):
    """이슈 번호 → (node id, Issue Type 이름)."""
    issue_id, type_name, _ = issue_view(repo, number)
    return issue_id, type_name


def update_issue_body(issue_id, body):
    """이슈 본문 교체. 호출자가 기존 본문 위에 절만 갈아 끼운 값을 넘긴다 — 통짜 덮어쓰기가 아니다."""
    data = graphql(
        "mutation($i:ID!,$b:String!){updateIssue(input:{id:$i,body:$b}){issue{number}}}",
        i=issue_id, b=body)
    return data["updateIssue"]["issue"]


def issue_type_id(repo, type_name):
    owner, name = split_repo(repo)
    data = graphql(
        "query($o:String!,$r:String!){repository(owner:$o,name:$r)"
        "{issueTypes(first:20){nodes{id name}}}}",
        o=owner, r=name)
    nodes = ((data.get("repository") or {}).get("issueTypes") or {}).get("nodes") or []
    for node in nodes:
        if node["name"] == type_name:
            return node["id"]
    die("거부: '%s' Issue Type 이 %s 에 없다." % (type_name, repo),
        "  있는 타입: " + (", ".join(n["name"] for n in nodes) or "(없음)"),
        "  org 설정에서 Issue Types 4종(Epic·Feature·Task·Bug)을 확인한다.")


def set_issue_type(issue_id, type_id):
    """gh issue create 에 --type 플래그가 없다 → 타입 지정은 GraphQL로만 된다."""
    data = graphql(
        "mutation($i:ID!,$t:ID!){updateIssueIssueType(input:{issueId:$i,issueTypeId:$t})"
        "{issue{number issueType{name}}}}",
        i=issue_id, t=type_id)
    return data["updateIssueIssueType"]["issue"]


def add_sub_issue(parent_id, child_id):
    data = graphql(
        "mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c})"
        "{issue{number} subIssue{number}}}",
        p=parent_id, c=child_id)
    return data["addSubIssue"]


# ── Projects ─────────────────────────────────────────────────────────────
# 근거 ADR 은 **Project 필드**에 담는다 (CLAUDE.md §5).
# 이슈 자체에는 임의 필드를 붙일 수 없고(스키마 고정), 라벨은 다중·평면이라 단일 값 속성을 담기엔 헐겁다.
# Project 필드는 단일 값 속성이라 성격이 맞는다 — 그리고 보드는 어차피 컨트롤 플레인의 뷰다.


def project(org, number):
    """org Project → {id, fields: {name: {id, dataType, options}}}"""
    data = graphql(
        "query($o:String!,$n:Int!){organization(login:$o){projectV2(number:$n){id "
        "fields(first:30){nodes{"
        "... on ProjectV2Field{id name dataType} "
        "... on ProjectV2SingleSelectField{id name dataType options{id name}}}}}}}",
        o=org, n=number)
    p = (data.get("organization") or {}).get("projectV2")
    if not p:
        die("거부: %s 의 Project #%d 를 찾지 못했다." % (org, number))
    fields = {}
    for f in p["fields"]["nodes"]:
        if f:
            fields[f["name"]] = f
    return {"id": p["id"], "fields": fields}


def project_item(issue_id, project_id):
    """이슈의 **기존** Project item id. 미등록이면 None — 등록하지 않는다.

    등록(+초기 Status)은 발행(create.py)의 일이다. 조회 함수가 슬쩍 등록하면
    Status 없는 항목이 생기고, 그 항목은 보드에서 유령이 된다.
    """
    data = graphql(
        "query($i:ID!){node(id:$i){... on Issue{"
        "projectItems(first:20){nodes{id project{id}}}}}}",
        i=issue_id)
    nodes = ((data.get("node") or {}).get("projectItems") or {}).get("nodes") or []
    for n in nodes:
        if n and (n.get("project") or {}).get("id") == project_id:
            return n["id"]
    return None


def add_to_project(project_id, issue_id):
    data = graphql(
        "mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c})"
        "{item{id}}}",
        p=project_id, c=issue_id)
    return data["addProjectV2ItemById"]["item"]["id"]


def set_text_field(project_id, item_id, field_id, value):
    graphql(
        "mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){updateProjectV2ItemFieldValue("
        "input:{projectId:$p,itemId:$i,fieldId:$f,value:{text:$v}}){projectV2Item{id}}}",
        p=project_id, i=item_id, f=field_id, v=value)


def set_select_field(project_id, item_id, field_id, option_id):
    graphql(
        "mutation($p:ID!,$i:ID!,$f:ID!,$v:String!){updateProjectV2ItemFieldValue("
        "input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$v}})"
        "{projectV2Item{id}}}",
        p=project_id, i=item_id, f=field_id, v=option_id)


def option_id(field, name):
    for o in field.get("options") or []:
        if o["name"] == name:
            return o["id"]
    die("거부: '%s' 필드에 '%s' 옵션이 없다." % (field["name"], name),
        "  있는 옵션: " + ", ".join(o["name"] for o in field.get("options") or []))


# close 하는 함수가 없다 (CLAUDE.md §5).
# 빠뜨린 것이 아니다 — PR 머지 ≠ 티켓 종료. 그 사이에 사용자 검수가 산다.
# "닫지 마세요"라는 프롬프트보다 **닫는 함수가 없는 것**이 강하다.
