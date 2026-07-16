#!/usr/bin/env bash

# SKALA 날짜별 작업 폴더를 Lee-ssu/skal-intro 저장소에 연결한다.
# 사용 예: ./setup_daily_repo.sh skala07.17

set -euo pipefail

DATE_FOLDER="${1:?날짜 폴더 이름이 필요합니다. 예: skala07.17}"
TARGET_DIR="${2:-$HOME/Documents/$DATE_FOLDER}"
REMOTE_URL="https://github.com/Lee-ssu/skal-intro.git"
BASE_BRANCH="main"
WORK_BRANCH="codex/$DATE_FOLDER"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

if ! command -v gh >/dev/null 2>&1; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "오류: Homebrew가 없어 GitHub CLI를 자동 설치할 수 없습니다." >&2
        exit 1
    fi
    brew install gh
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "GitHub 로그인이 필요합니다. 브라우저 인증을 시작합니다."
    gh auth login --hostname github.com --git-protocol https --web
fi

if [[ ! -d .git ]]; then
    git init
    git remote add origin "$REMOTE_URL"
    git fetch origin "$BASE_BRANCH"
    git symbolic-ref HEAD "refs/heads/$WORK_BRANCH"
    git update-ref "refs/heads/$WORK_BRANCH" "refs/remotes/origin/$BASE_BRANCH"
    git read-tree "refs/remotes/origin/$BASE_BRANCH"

    # 이전 날짜 파일은 원격 이력에 유지하되 새 날짜 폴더에는 표시하지 않는다.
    git ls-files -z | xargs -0 git update-index --skip-worktree

    # 새 폴더에 같은 이름의 파일이 이미 있으면 오늘 변경 대상으로 되돌린다.
    while IFS= read -r -d '' tracked_file; do
        if [[ -e "$tracked_file" ]]; then
            git update-index --no-skip-worktree "$tracked_file"
        fi
    done < <(git ls-files -z)
fi

if [[ ! -d .venv ]]; then
    PYTHON_BIN="${PYTHON_BIN:-python3}"
    "$PYTHON_BIN" -m venv .venv
fi

if [[ -f requirements.txt ]]; then
    .venv/bin/python -m pip install -r requirements.txt
fi

echo "준비 완료"
echo "폴더: $TARGET_DIR"
echo "원격: $REMOTE_URL"
echo "브랜치: $(git branch --show-current)"
