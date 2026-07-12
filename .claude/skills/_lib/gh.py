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
        args += ["-F", "%s=%s" % (k, v)]        # -F 는 숫자·불리언을 형에 맞춰 넘긴다
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


def issue_node(repo, number):
    """이슈 번호 → (node id, Issue Type 이름). 타입이 없으면 이름은 None."""
    owner, name = split_repo(repo)
    data = graphql(
        "query($o:String!,$r:String!,$n:Int!)"
        "{repository(owner:$o,name:$r){issue(number:$n){id issueType{name}}}}",
        o=owner, r=name, n=number)
    issue = (data.get("repository") or {}).get("issue")
    if not issue:
        die("거부: %s#%d 를 찾지 못했다." % (repo, number))
    return issue["id"], (issue.get("issueType") or {}).get("name")


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


# close 하는 함수가 없다 (CLAUDE.md §5).
# 빠뜨린 것이 아니다 — PR 머지 ≠ 티켓 종료. 그 사이에 사용자 검수가 산다.
# "닫지 마세요"라는 프롬프트보다 **닫는 함수가 없는 것**이 강하다.
