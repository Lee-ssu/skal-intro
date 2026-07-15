# Practice 1 — 자료구조 집계·컴프리헨션·제너레이터

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
