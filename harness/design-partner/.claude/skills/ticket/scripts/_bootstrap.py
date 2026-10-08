"""공유 라이브러리(_lib) 경로 부트스트랩 — 이 디렉터리의 스크립트가 `import _bootstrap` 한 줄로 쓴다.

_lib 는 git 루트의 .claude/skills/_lib 에 하나다. 하네스 전용 스킬은 harness/<역할>/.claude/skills/ 밑에
살아 상대경로(../../_lib)로는 닿지 않으므로, 이 파일의 위치에서 .git 을 찾아 올라가 루트를 역산한다.
_lib 를 찾기 전에는 _lib 를 import 할 수 없으니 이 파일만은 _lib 밖, 스크립트 옆에 산다.
파이썬은 실행된 스크립트의 디렉터리를 sys.path[0] 에 넣으므로 별도 설정 없이 import 된다.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(_d, ".git")) and _d != os.path.dirname(_d):
    _d = os.path.dirname(_d)
_lib = os.path.join(_d, ".claude", "skills", "_lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)
