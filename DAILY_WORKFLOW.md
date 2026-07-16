# SKALA 날짜별 GitHub 작업 방식

앞으로 날짜 폴더만 바꿔 같은 GitHub 저장소를 사용한다.

## 기본 규칙

- 로컬 폴더: `~/Documents/skalaMM.DD`
- GitHub 저장소: `Lee-ssu/skal-intro`
- 기본 브랜치: `main`
- 날짜별 작업 브랜치: `codex/skalaMM.DD`
- `.venv`, 원본 대용량 데이터, 캐시는 커밋하지 않음
- 코드, README, 테스트, 작은 실행 결과만 명시적으로 커밋
- 작업 완료 후 Ruff·pytest·실제 실행을 확인하고 push 및 Draft PR 생성

## 다음 날짜 폴더 준비

이전 날짜 폴더에서 다음과 같이 실행한다.

```bash
./setup_daily_repo.sh skala07.17
```

필요하면 대상 경로도 직접 지정할 수 있다.

```bash
./setup_daily_repo.sh skala07.17 /Users/leesangsu/Documents/skala07.17
```

스크립트가 자동으로 처리하는 내용:

1. 날짜 폴더 생성
2. `gh`가 없으면 Homebrew로 설치
3. GitHub 인증 확인과 필요 시 브라우저 로그인
4. `Lee-ssu/skal-intro` 원격 연결
5. `origin/main`에서 날짜별 `codex/` 브랜치 생성
6. 독립 가상환경 생성
7. `requirements.txt`가 있으면 패키지 설치

커밋과 push는 그날 작업과 검증이 끝난 뒤 수행한다.
