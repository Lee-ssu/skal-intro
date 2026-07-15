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
