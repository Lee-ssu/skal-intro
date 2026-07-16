# Practice 4 실행 결과

- 작성자: 이상수
- 실행일: 2026-07-16
- 입력 데이터: `sales_100k.csv` 1,000,000행
- IQR 정제 후 데이터: 973,806행

## 1. EDA 시각화 4종

`fig, axes = plt.subplots(2, 2)`를 사용해 하나의 figure에 다음 차트를 구성했다.

1. 매출 히스토그램 + KDE
2. 지역별 매출 박스플롯
3. 월별 총매출 라인 차트
4. 수치형 변수 상관 히트맵

결과 파일: `output/practice4_eda_2x2.png`

## 2. 통계 검정

### 서울 vs 부산 평균 매출 Welch t-test

- 서울: 241,071건, 평균 2,476,501.17
- 부산: 116,295건, 평균 2,471,075.70
- t 통계량: 0.726904
- p-value: 0.46728565
- 해석: p-value가 0.05 이상이므로 서울과 부산의 평균 매출 차이는 통계적으로 유의하지 않다.

### 지역 × 카테고리 카이제곱 독립성 검정

- 분할표: 8 × 8
- 카이제곱 통계량: 74.991852
- 자유도: 49
- p-value: 0.00985361
- 최소 기대빈도: 8,365.12
- 해석: p-value가 0.05 미만이므로 지역과 카테고리는 서로 독립적이지 않다.

## 3. sklearn Pipeline

- 전처리: `ColumnTransformer`
  - 수치형: 중앙값 대치 + 표준화
  - 범주형: 최빈값 대치 + One-Hot Encoding
- 모델: Ridge 회귀
- 학습 행 수: 779,044
- 평가 행 수: 194,762
- R² score: 0.841137
- MAE: 600,996.07
- RMSE: 833,087.00
- 재로딩 R² score: 0.841137
- 저장 전·후 예측값 일치: True
- 모델 파일: `output/practice4_pipeline.joblib`

## 4. Plotly 인터랙티브 차트

- 지역·카테고리별 총매출 막대 차트 작성
- HTML 저장: `output/practice4_region_category.html`

## 품질 검사

- Ruff lint: 통과
- Ruff format: 통과
- pytest: 3개 테스트 통과
- 100만 행 전체 실행: 성공
- PNG 레이아웃 및 한글 표시: 확인 완료
- Pipeline 저장·재로딩: 확인 완료
