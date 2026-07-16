# Python Practice

## Practice 1 — 자료구조 집계·컴프리헨션·제너레이터

`practice1.py`는 제시된 실습의 네 가지 항목과 체크포인트를 구현합니다.

## 실행

`Python_Practice1_Data.json`을 이 폴더에 둔 뒤 실행합니다.

```bash
python3 practice1.py
```

파일명이 다르거나 다른 폴더에 있다면 경로를 인자로 전달할 수 있습니다.

```bash
python3 practice1.py /path/to/data.json
```

지원하는 JSON 구조는 다음 두 가지입니다.

```json
{"Sales": [{"region": "서울", "amount": 1200, "month": "2026-01", "category": "A"}]}
```

또는 거래 객체가 바로 들어 있는 최상위 리스트입니다.

```json
[{"region": "서울", "amount": 1200, "month": "2026-01", "category": "A"}]
```

## 테스트

외부 패키지 없이 표준 라이브러리만 사용합니다.

```bash
python3 -m unittest -v
```

## Practice 2 — 파일 I/O·예외 처리·Pydantic 검증

Practice 2는 Pydantic v2가 필요합니다. 가상환경과 패키지를 한 번만 준비합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

실행하면 `Python_Practice2_Data.json`의 앞 7건을 바탕으로 검증용 CSV를
만듭니다. 교수님 지침에 따라 `date` 대신 `month` 필드를 사용하며, 앞 4건은
정상 데이터로 유지하고 뒤 3건에는 빈 `month`, 빈 `region`, `amount=0`을
각각 적용해 검증합니다. 정상 데이터는 `practice2_valid.csv`, 오류 데이터는
`practice2_errors.json`으로 저장한 뒤 결과 CSV를 다시 읽어 건수를 확인합니다.

```bash
.venv/bin/python practice2.py
```

Practice 2 테스트만 실행하려면 다음 명령을 사용합니다.

```bash
.venv/bin/python -m unittest -v test_practice2.py
```

## 종합실습 1 — 비동기 날씨 수집·CSV·Parquet

Open-Meteo에서 서울, 도쿄, 뉴욕, 런던의 현재 기온을 비동기로 수집합니다.
교수님 보완 안내에 따라 countries.dev 국가 API로 시간대 정보를 확인하고,
도시별 IANA 시간대로 현지시각을 계산합니다. 결과는 `weather.csv`와
`weather.parquet`으로 저장한 뒤 다시 읽어 출력합니다.

의존성을 준비한 뒤 실행합니다.

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python comprehensive_step1_async_api.py
.venv/bin/python comprehensive_step2_pydantic.py
.venv/bin/python comprehensive_step3_csv.py
.venv/bin/python comprehensive_step4_parquet.py
.venv/bin/python 이상수.py
```

pytest와 Ruff 검사는 다음과 같이 실행합니다.

```bash
.venv/bin/python -m pytest -v comprehensive_step5_pytest.py
.venv/bin/ruff check comprehensive_step*.py 이상수.py
```

## Practice 3 — Pandas EDA · Polars Lazy · DuckDB SQL 비교

2026-07-16 실습은 `sales_100k.csv`의 EDA, IQR 이상치 처리, 세 도구의 동일 집계와 성능 비교를 수행합니다.

- 상세 실행 안내: [README_practice3.md](README_practice3.md)
- 실행 결과: [practice3_result.md](practice3_result.md)
- 메인 코드: [practice3.py](practice3.py)
- 자동 테스트: [test_practice3.py](test_practice3.py)

## Practice 4 — 시각화 · 통계 검정 · sklearn Pipeline

Practice 3의 IQR 정제 데이터를 연결해 2×2 EDA, t-test, 카이제곱, Pipeline 학습·저장·재로딩과 Plotly HTML 저장을 수행합니다.

- 상세 실행 안내: [README_practice4.md](README_practice4.md)
- 실행 결과: [practice4_result.md](practice4_result.md)
- 메인 코드: [practice4.py](practice4.py)
- 자동 테스트: [test_practice4.py](test_practice4.py)

## 종합실습 2 — 서울시 상권 추정매출 분석

- 상세 실행 및 CSV 점검 안내: [README_comprehensive_practice2.md](README_comprehensive_practice2.md)
- 실제 실행 결과: [comprehensive_practice2_result.md](comprehensive_practice2_result.md)
- 최종 제출 코드: [Test2_이상수.py](Test2_이상수.py), [git2_이상수.py](git2_이상수.py)
- 이메일 제출 압축 파일: `Test2_이상수.zip`
- 자동 테스트: [test_comprehensive_practice2.py](test_comprehensive_practice2.py)
