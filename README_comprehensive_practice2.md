# 종합실습 2 — 서울시 상권 추정매출 분석

> 작성자: 이상수<br>
> 최종 제출 코드: `Test2_이상수.py`, `git2_이상수.py`<br>
> 제출 압축 파일: `Test2_이상수.zip`

## 구현 내용

- 서울시 상권분석서비스 CSV의 UTF-8·CP949 인코딩 자동 판별
- 과제에서 지정한 10개 컬럼 선택 및 데이터 품질 검사
- `서비스_업종_코드_명`별 `당월_매출_금액` 합계 TOP 10 산출
- 10대·20대·30대 매출 컬럼 합계 막대그래프 저장
- 수치형 Pipeline: 중앙값 결측치 처리 + 표준화
- 범주형 Pipeline: `missing` 결측치 처리 + 원-핫 인코딩
- `ColumnTransformer + ExtraTreesRegressor` 최종 Pipeline 학습
- `fit`, `predict`, `score`, `joblib.dump`, `joblib.load` 실행 및 검증

## CSV 점검 결과

- 인코딩: CP949 — 파일은 정상이지만 `pd.read_csv()`에서 인코딩 지정이 필요함
- 원본 크기: 106,920행 × 55열
- 선택 데이터: 106,920행 × 10열
- 필수 컬럼 누락: 없음
- 선택 컬럼 결측치: 없음
- 음수 매출: 없음
- 원본 전체 컬럼 기준 완전 중복: 없음
- 선택 컬럼 기준 중복 118행은 분기 컬럼을 제외하면서 같아 보이는 관측치이므로 삭제하지 않음

## 실행

```bash
cd /Users/leesangsu/Documents/skala07.16
.venv/bin/python comprehensive_practice2.py
```

실행 후 그래프까지 자동으로 열기:

```bash
.venv/bin/python comprehensive_practice2.py --open-results
```

VS Code에서는 `Fn + F5`를 누르고 `종합실습 2 실행`을 선택한다.

## 이메일 제출 파일

- `Test2_이상수.py`: 종합실습 2 전체 코드
- `git2_이상수.py`: GitHub 제출용 실행 진입점
- 위 두 파일을 담은 `Test2_이상수.zip`

## 생성 파일

- `output/comprehensive_practice2_top10.csv`
- `output/comprehensive_practice2_age_sales.png`
- `output/comprehensive_practice2_pipeline.joblib`
- `output/comprehensive_practice2_metrics.csv`
- `output/comprehensive_practice2_data_quality.json`
