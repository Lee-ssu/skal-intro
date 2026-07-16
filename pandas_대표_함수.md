# pandas 2.x 대표 함수와 메서드

pandas는 표 형태의 데이터를 불러오고, 확인하고, 가공하고, 분석하고, 저장할 때 사용한다.

## 1. 데이터 만들기와 불러오기

```python
import pandas as pd

df = pd.DataFrame({
    "이름": ["철수", "영희", "민수"],
    "점수": [90, 85, None],
    "반": ["A", "A", "B"],
})

csv_df = pd.read_csv("students.csv")
```

- `pd.DataFrame()`: 딕셔너리나 리스트로 표를 만든다.
- `pd.read_csv()`: CSV 파일을 DataFrame으로 읽는다.
- `pd.read_excel()`: Excel 파일을 DataFrame으로 읽는다.

## 2. 데이터 확인하기

```python
df.head()       # 앞의 5행
df.tail()       # 뒤의 5행
df.info()       # 열, 자료형, 결측치 등 구조
df.describe()   # 숫자 데이터의 통계 요약
```

- `head(n)`, `tail(n)`: 데이터의 앞이나 뒤를 빠르게 확인한다.
- `info()`: 행 수, 열 이름, 자료형, 결측 여부를 확인한다.
- `describe()`: 개수, 평균, 표준편차, 최솟값, 최댓값 등을 계산한다.

## 3. 행과 열 선택하기

```python
df["이름"]
df[["이름", "점수"]]
df.loc[df["점수"] >= 90, ["이름", "점수"]]
df.iloc[0:2, 0:2]
```

- `df["열 이름"]`: 열 하나를 선택한다.
- `loc[]`: 행·열의 이름이나 조건으로 선택한다.
- `iloc[]`: 행·열의 정수 위치로 선택한다.

## 4. 정렬하고 빈도 확인하기

```python
df.sort_values("점수", ascending=False)
df["반"].value_counts()
df["이름"].unique()
```

- `sort_values()`: 지정한 열을 기준으로 정렬한다.
- `value_counts()`: 각 값이 몇 번 나왔는지 센다.
- `unique()`: 중복을 제거한 고유값을 반환한다.

## 5. 결측치 처리하기

```python
df.isna()
df.dropna()
df.fillna({"점수": 0})
```

- `isna()`: 값이 비어 있는지 확인한다.
- `dropna()`: 결측치가 있는 행이나 열을 제거한다.
- `fillna()`: 결측치를 지정한 값으로 채운다.

## 6. 열 수정하기

```python
df.rename(columns={"점수": "시험점수"})
df.drop(columns=["반"])
df["점수"] = df["점수"].astype("Float64")
```

- `rename()`: 행이나 열의 이름을 바꾼다.
- `drop()`: 필요 없는 행이나 열을 제거한다.
- `astype()`: 열의 자료형을 변환한다.

## 7. 그룹별 집계하기

```python
df.groupby("반")["점수"].mean()
df.groupby("반").agg(
    평균점수=("점수", "mean"),
    학생수=("이름", "count"),
)
```

- `groupby()`: 같은 값을 가진 행끼리 그룹을 만든다.
- `agg()`: 평균, 합계, 개수 등 여러 통계를 계산한다.

## 8. 표 합치기

```python
pd.merge(left_df, right_df, on="학생번호", how="left")
pd.concat([df1, df2], ignore_index=True)
```

- `pd.merge()`: 공통 열을 기준으로 두 표를 연결한다. SQL의 JOIN과 비슷하다.
- `pd.concat()`: 여러 표를 위아래 또는 좌우로 이어 붙인다.

## 9. 파일로 저장하기

```python
df.to_csv("result.csv", index=False)
df.to_excel("result.xlsx", index=False)
```

- `to_csv()`: DataFrame을 CSV 파일로 저장한다.
- `to_excel()`: DataFrame을 Excel 파일로 저장한다.
- `index=False`: pandas가 만든 행 번호를 파일에 저장하지 않는다.

## 기억할 기본 흐름

```text
read_csv → head/info → loc/iloc → 결측치 처리
         → sort_values/groupby → merge → to_csv
```

## pandas 2.x Copy-on-Write 주의

pandas 2.x에서 Copy-on-Write는 사용할 수 있지만 기본 활성화는 아니다.

```python
pd.options.mode.copy_on_write = True
```

pandas 3.0부터 Copy-on-Write가 기본이자 유일한 동작이다. 버전에 관계없이 체인 할당을 피하고 `.loc`, `.copy()`, `.assign()`을 사용하는 습관이 안전하다.
