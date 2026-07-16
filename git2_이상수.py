"""종합실습 2 GitHub 제출용 실행 진입점.

작성자: 이상수

기능 설명
---------
교수님이 지정한 git2_이상수.py 파일명으로 실행할 수 있도록
Test2_이상수.py의 검증된 main 함수를 호출한다.

변경 내역
---------
- 2026-07-16: GitHub 제출용 실행 파일 최초 작성
"""

from __future__ import annotations

import sys

from Test2_이상수 import main

if __name__ == "__main__":
    sys.exit(main())
