"""Practice 3 핵심 로직의 자동 검증 테스트."""

from pathlib import Path

import pandas as pd

from practice3 import (
    calculate_iqr_bounds,
    duckdb_sql_aggregation,
    normalize_result,
    pandas_named_aggregation,
    polars_lazy_aggregation,
    polars_to_pandas,
    remove_amount_outliers,
    verify_equal_results,
)


def make_sample_csv(path: Path) -> pd.DataFrame:
    """결측치와 명확한 이상치를 포함한 작은 테스트 CSV를 만든다."""

    frame = pd.DataFrame(
        {
            "region": ["서울", "서울", "부산", "부산"] * 3 + ["서울", None],
            "category": ["식품", "전자", "식품", "전자"] * 3 + ["식품", "전자"],
            "amount": [100, 110, 120, 130, 105, 115, 125, 135, 108, 118, 128, 138, 10_000, None],
        }
    )
    frame.to_csv(path, index=False)
    return frame


def test_iqr_removes_null_and_outlier(tmp_path: Path) -> None:
    """IQR 필터가 결측치와 큰 이상치를 제거하는지 확인한다."""

    frame = make_sample_csv(tmp_path / "sample.csv")
    bounds = calculate_iqr_bounds(frame["amount"])
    cleaned = remove_amount_outliers(frame, bounds)

    assert cleaned["amount"].notna().all()
    assert cleaned["amount"].max() < 10_000
    assert len(cleaned) == 12


def test_three_tools_return_same_aggregation(tmp_path: Path) -> None:
    """Pandas·Polars·DuckDB가 같은 전체 집계 결과를 내는지 확인한다."""

    csv_path = tmp_path / "sample.csv"
    frame = make_sample_csv(csv_path)
    bounds = calculate_iqr_bounds(frame["amount"])
    cleaned = remove_amount_outliers(frame, bounds)

    pandas_result = pandas_named_aggregation(cleaned)
    polars_result = polars_to_pandas(polars_lazy_aggregation(csv_path, bounds))
    duckdb_result = duckdb_sql_aggregation(csv_path, bounds)

    verify_equal_results(pandas_result, polars_result, duckdb_result)
    assert len(normalize_result(pandas_result)) == 4
