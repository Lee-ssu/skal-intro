# Practice 3 - Pandas EDA · Polars Lazy · DuckDB SQL 비교

> 2026-07-16 학습 및 실습 기록
>
> 작성자: 이상수

`sales_100k.csv`를 이용해 Pandas, Polars, DuckDB의 동일한 집계 결과와 실행 시간을 비교하는 실습입니다. 실제 입력 파일은 약 100만 행입니다.

## 구현 체크리스트

- Pandas `df.info()`, `df.isnull().sum()`, `df.describe()` 출력
- `Q1 - 1.5*IQR`부터 `Q3 + 1.5*IQR`까지의 정상 범위만 유지
- 제거 전·후 행 수와 결측치·이상치 제거 건수 출력
- Pandas named aggregation으로 `total`, `mean`, `count` 계산
- 총매출 내림차순 정렬
- Polars `scan_csv → filter → group_by → agg → sort → collect` Lazy 체인
- DuckDB `GROUP BY` SQL로 동일 집계 수행
- 세 도구의 전체 결과 일치 여부 자동 검증
- 동일한 `number`, `repeat` 값으로 `timeit` 성능 비교
- 파일·데이터 형식·실행 오류 처리

## 환경 구성

```bash
cd /Users/leesangsu/Documents/skala07.16
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
.venv/bin/python practice3.py
```

반복 횟수와 출력 행 수를 바꿀 수도 있습니다.

```bash
.venv/bin/python practice3.py --number 2 --repeat 3 --rows 15
```

## 검사

```bash
.venv/bin/ruff check .
.venv/bin/pytest -v
```

## 결과 파일

실행 후 `output/`에 다음 파일이 생성됩니다.

- `pandas_groupby.csv`
- `polars_groupby.csv`
- `duckdb_groupby.csv`
- `benchmark.csv`

원본 `sales_100k.csv`는 크기가 크고 재생성 가능한 입력 데이터이므로 Git에 포함하지 않습니다.
