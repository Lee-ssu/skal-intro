# Practice 4 - 시각화 4종 · 통계 검정 · sklearn Pipeline

> 2026-07-16 학습 및 실습 기록
>
> 작성자: 이상수

Practice 3의 `sales_100k.csv`와 IQR 이상치 제거 결과를 연결해 시각화, 통계 검정, 머신러닝 Pipeline을 수행합니다.

## 체크포인트

- `fig, axes = plt.subplots(2, 2)` 한 figure에 시각화 4종 구성
  - 히스토그램+KDE
  - 지역별 박스플롯
  - 월별 총매출 라인 차트
  - 수치형 변수 상관 히트맵
- 서울·부산 평균 매출에 `scipy.stats.ttest_ind` 적용
- 지역×카테고리 분할표에 `chi2_contingency` 적용
- 두 검정의 통계량, p-value와 `p < 0.05` 해석 출력
- `ColumnTransformer + Pipeline`으로 전처리와 Ridge 회귀 결합
- `fit`, `predict`, `score`, `joblib.dump`, `joblib.load` 순서 실행
- 지역·카테고리별 총매출 Plotly 막대 차트를 `.html`로 저장
- 파일·입력 컬럼·표본 크기·모델 설정 오류 처리

## 실행

```bash
cd /Users/leesangsu/Documents/skala07.16
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python practice4.py
```

실행이 끝난 뒤 그래프를 화면에서 바로 열려면 다음 옵션을 사용한다.

```bash
.venv/bin/python practice4.py --open-results
```

VS Code의 `Practice 4 실행` 구성은 이 옵션을 자동으로 사용한다.

## 검사

```bash
.venv/bin/ruff check practice4.py test_practice4.py
.venv/bin/pytest -v test_practice4.py
```

## 생성 파일

- `output/practice4_eda_2x2.png`
- `output/practice4_region_category.html`
- `output/practice4_pipeline.joblib`
- `output/practice4_statistics.json`
- `output/practice4_model_metrics.csv`

실제 실행 수치와 해석은 [practice4_result.md](practice4_result.md)에 정리되어 있습니다.
