"""Practice 3 - Pandas EDA, Polars Lazy, DuckDB SQL 성능 비교.

프로그램 설명
------------
sales_100k.csv를 세 가지 분석 도구로 처리하고 결과와 실행 시간을 비교한다.
모든 도구는 Pandas에서 계산한 동일한 IQR 정상 범위를 사용하며,
region·category별 amount 합계·평균·건수를 같은 조건으로 집계한다.

변경 내역
---------
- 2026-07-16: Practice 3 요구사항에 맞춰 최초 작성
"""

from __future__ import annotations

import argparse
import logging
import sys
import timeit
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
import polars as pl

LOGGER = logging.getLogger("practice3")
REQUIRED_COLUMNS = {"region", "category", "amount"}
RESULT_COLUMNS = ["region", "category", "total", "mean", "count"]


class Practice3Error(RuntimeError):
    """입력 데이터나 분석 단계가 요구사항을 만족하지 않을 때 발생한다."""


@dataclass(frozen=True)
class IQRBounds:
    """IQR 방식으로 계산한 amount 정상 범위와 기초 통계."""

    q1: float
    q3: float
    iqr: float
    lower: float
    upper: float


def configure_logging() -> None:
    """분석 진행 상황과 오류를 보기 쉬운 형식으로 출력한다."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )


def validate_csv_path(csv_path: Path) -> None:
    """입력 파일의 존재 여부와 CSV 확장자를 검사한다."""

    if not csv_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {csv_path}")
    if not csv_path.is_file():
        raise Practice3Error(f"입력 경로가 파일이 아닙니다: {csv_path}")
    if csv_path.suffix.lower() != ".csv":
        raise Practice3Error(f"CSV 파일만 사용할 수 있습니다: {csv_path}")


def validate_columns(columns: list[str]) -> None:
    """집계에 필요한 region, category, amount 컬럼을 확인한다."""

    missing = REQUIRED_COLUMNS.difference(columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise Practice3Error(f"필수 컬럼이 없습니다: {names}")


def load_pandas(csv_path: Path) -> pd.DataFrame:
    """CSV를 Pandas DataFrame으로 읽고 필수 컬럼과 amount 타입을 검증한다."""

    try:
        frame = pd.read_csv(csv_path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError as error:
        raise Practice3Error("CSV 파일이 비어 있습니다.") from error
    except pd.errors.ParserError as error:
        raise Practice3Error(f"CSV 형식을 해석할 수 없습니다: {error}") from error

    validate_columns(frame.columns.tolist())
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    return frame


def print_basic_eda(frame: pd.DataFrame) -> None:
    """과제 체크포인트인 df.info()와 컬럼별 결측치 수를 출력한다."""

    print("\n" + "=" * 72)
    print("1) Pandas 기본 EDA")
    print("=" * 72)
    print(f"shape: {frame.shape}")
    print("\n[df.info()]")
    frame.info()
    print("\n[df.isnull().sum()]")
    print(frame.isnull().sum().to_string())
    print("\n[df.describe() - 숫자형]")
    print(frame.describe().round(2).to_string())


def calculate_iqr_bounds(amount: pd.Series) -> IQRBounds:
    """Q1 - 1.5*IQR부터 Q3 + 1.5*IQR까지의 정상 범위를 계산한다."""

    valid_amount = pd.to_numeric(amount, errors="coerce").dropna()
    if valid_amount.empty:
        raise Practice3Error("amount 컬럼에 분석 가능한 숫자가 없습니다.")

    q1 = float(valid_amount.quantile(0.25))
    q3 = float(valid_amount.quantile(0.75))
    iqr = q3 - q1
    if iqr <= 0:
        raise Practice3Error("amount의 IQR이 0 이하이므로 이상치 범위를 계산할 수 없습니다.")

    return IQRBounds(
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower=q1 - 1.5 * iqr,
        upper=q3 + 1.5 * iqr,
    )


def remove_amount_outliers(
    frame: pd.DataFrame,
    bounds: IQRBounds,
) -> pd.DataFrame:
    """IQR 정상 범위에 포함된 행만 남기고 제거 전·후 건수를 출력한다."""

    normal_mask = frame["amount"].between(bounds.lower, bounds.upper, inclusive="both")
    cleaned = frame.loc[normal_mask].copy()

    null_count = int(frame["amount"].isna().sum())
    outlier_count = int((frame["amount"].notna() & ~normal_mask).sum())

    print("\n[IQR 이상치 처리]")
    print(f"Q1: {bounds.q1:,.2f}")
    print(f"Q3: {bounds.q3:,.2f}")
    print(f"IQR: {bounds.iqr:,.2f}")
    print(f"정상 범위: {bounds.lower:,.2f} <= amount <= {bounds.upper:,.2f}")
    print(f"제거 전 행 수: {len(frame):,}")
    print(f"amount 결측치 제거: {null_count:,}")
    print(f"IQR 이상치 제거: {outlier_count:,}")
    print(f"제거 후 행 수: {len(cleaned):,}")
    return cleaned


def pandas_named_aggregation(frame: pd.DataFrame) -> pd.DataFrame:
    """Pandas named aggregation으로 지역·카테고리별 집계를 계산한다."""

    result = (
        frame.groupby(["region", "category"], dropna=False)
        .agg(
            total=("amount", "sum"),
            mean=("amount", "mean"),
            count=("amount", "count"),
        )
        .reset_index()
        .sort_values(
            ["total", "region", "category"],
            ascending=[False, True, True],
            na_position="last",
        )
        .reset_index(drop=True)
    )
    return result[RESULT_COLUMNS]


def pandas_pipeline(csv_path: Path, bounds: IQRBounds) -> pd.DataFrame:
    """성능 비교용 Pandas 읽기 → 필터 → named aggregation 파이프라인."""

    frame = load_pandas(csv_path)
    mask = frame["amount"].between(bounds.lower, bounds.upper, inclusive="both")
    return pandas_named_aggregation(frame.loc[mask])


def polars_lazy_aggregation(csv_path: Path, bounds: IQRBounds) -> pl.DataFrame:
    """Polars scan_csv → filter → group_by → agg → sort → collect 체인."""

    lazy_result = (
        pl.scan_csv(csv_path, encoding="utf8-lossy")
        .filter(pl.col("amount").is_between(bounds.lower, bounds.upper, closed="both"))
        .group_by(["region", "category"])
        .agg(
            pl.col("amount").sum().alias("total"),
            pl.col("amount").mean().alias("mean"),
            pl.col("amount").count().alias("count"),
        )
        .sort(
            ["total", "region", "category"],
            descending=[True, False, False],
            nulls_last=True,
        )
    )
    return lazy_result.collect()


def duckdb_sql_aggregation(csv_path: Path, bounds: IQRBounds) -> pd.DataFrame:
    """DuckDB SQL GROUP BY로 동일한 필터와 집계를 수행한다."""

    escaped_path = str(csv_path.resolve()).replace("'", "''")
    query = f"""
        SELECT
            region,
            category,
            SUM(amount)::DOUBLE AS total,
            AVG(amount)::DOUBLE AS mean,
            COUNT(amount)::BIGINT AS count
        FROM read_csv_auto('{escaped_path}', header = true)
        WHERE amount BETWEEN ? AND ?
        GROUP BY region, category
        ORDER BY total DESC, region ASC NULLS LAST, category ASC NULLS LAST
    """

    try:
        with duckdb.connect() as connection:
            result = connection.execute(query, [bounds.lower, bounds.upper]).fetchdf()
    except duckdb.Error as error:
        raise Practice3Error(f"DuckDB SQL 실행 실패: {error}") from error
    return result[RESULT_COLUMNS]


def polars_to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """PyArrow 추가 의존성 없이 Polars 결과를 Pandas로 변환한다."""

    return pd.DataFrame(frame.to_dict(as_series=False))[RESULT_COLUMNS]


def normalize_result(frame: pd.DataFrame) -> pd.DataFrame:
    """세 도구의 결과 타입과 정렬을 통일해 정확히 비교할 수 있게 한다."""

    normalized = frame.copy()
    normalized["region"] = normalized["region"].astype("string")
    normalized["category"] = normalized["category"].astype("string")
    normalized["total"] = pd.to_numeric(normalized["total"])
    normalized["mean"] = pd.to_numeric(normalized["mean"])
    normalized["count"] = pd.to_numeric(normalized["count"]).astype("int64")
    return normalized.sort_values(
        ["total", "region", "category"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)


def verify_equal_results(
    pandas_result: pd.DataFrame,
    polars_result: pd.DataFrame,
    duckdb_result: pd.DataFrame,
) -> None:
    """세 도구의 전체 집계 결과가 허용 오차 안에서 같은지 검증한다."""

    expected = normalize_result(pandas_result)
    for tool_name, actual in {
        "Polars": polars_result,
        "DuckDB": duckdb_result,
    }.items():
        try:
            pd.testing.assert_frame_equal(
                expected,
                normalize_result(actual),
                check_dtype=False,
                check_exact=False,
                rtol=1e-9,
                atol=1e-6,
            )
        except AssertionError as error:
            raise Practice3Error(f"Pandas와 {tool_name}의 집계 결과가 다릅니다.") from error
    LOGGER.info("Pandas, Polars, DuckDB 전체 집계 결과가 일치합니다.")


def benchmark_tools(
    csv_path: Path,
    bounds: IQRBounds,
    number: int,
    repeat: int,
) -> pd.DataFrame:
    """세 도구를 같은 number·repeat 값으로 timeit 측정한다."""

    if number < 1 or repeat < 1:
        raise Practice3Error("timeit의 number와 repeat는 1 이상이어야 합니다.")

    tasks: dict[str, Callable[[], object]] = {
        "Pandas": lambda: pandas_pipeline(csv_path, bounds),
        "Polars Lazy": lambda: polars_lazy_aggregation(csv_path, bounds),
        "DuckDB SQL": lambda: duckdb_sql_aggregation(csv_path, bounds),
    }
    records: list[dict[str, float | int | str]] = []

    for tool_name, task in tasks.items():
        LOGGER.info("%s 성능을 측정합니다.", tool_name)
        measurements = timeit.repeat(stmt=task, repeat=repeat, number=number)
        per_run = [elapsed / number for elapsed in measurements]
        records.append(
            {
                "tool": tool_name,
                "number": number,
                "repeat": repeat,
                "best_seconds": min(per_run),
                "average_seconds": sum(per_run) / len(per_run),
            }
        )

    return pd.DataFrame(records).sort_values("best_seconds").reset_index(drop=True)


def print_result(title: str, frame: pd.DataFrame, rows: int) -> None:
    """전체 결과 크기와 상위 결과를 콘솔에 출력한다."""

    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    print(f"전체 그룹 수: {len(frame):,}")
    print(frame.head(rows).round({"total": 2, "mean": 2}).to_string(index=False))


def save_outputs(
    output_dir: Path,
    pandas_result: pd.DataFrame,
    polars_result: pd.DataFrame,
    duckdb_result: pd.DataFrame,
    benchmark_result: pd.DataFrame,
) -> None:
    """전체 집계 결과와 성능 비교 결과를 CSV로 저장한다."""

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_options = {"index": False, "float_format": "%.2f"}
    normalize_result(pandas_result).to_csv(output_dir / "pandas_groupby.csv", **csv_options)
    normalize_result(polars_result).to_csv(output_dir / "polars_groupby.csv", **csv_options)
    normalize_result(duckdb_result).to_csv(output_dir / "duckdb_groupby.csv", **csv_options)
    benchmark_result.to_csv(output_dir / "benchmark.csv", index=False)
    LOGGER.info("전체 결과를 저장했습니다: %s", output_dir.resolve())


def parse_args() -> argparse.Namespace:
    """입력 파일, 출력 위치, 출력 행 수와 timeit 반복 횟수를 받는다."""

    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=base_dir / "sales_100k.csv",
        help="분석할 CSV 파일 경로",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "output",
        help="결과 CSV를 저장할 폴더",
    )
    parser.add_argument("--rows", type=int, default=15, help="화면에 출력할 상위 그룹 수")
    parser.add_argument("--number", type=int, default=2, help="timeit 한 세트의 실행 횟수")
    parser.add_argument("--repeat", type=int, default=3, help="timeit 측정 세트 반복 횟수")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    """EDA부터 결과 검증·성능 측정·파일 저장까지 전체 실습을 실행한다."""

    csv_path = args.csv_path.expanduser().resolve()
    validate_csv_path(csv_path)
    if args.rows < 1:
        raise Practice3Error("--rows는 1 이상이어야 합니다.")

    LOGGER.info("데이터를 읽습니다: %s", csv_path)
    raw_frame = load_pandas(csv_path)
    print_basic_eda(raw_frame)

    bounds = calculate_iqr_bounds(raw_frame["amount"])
    clean_frame = remove_amount_outliers(raw_frame, bounds)

    pandas_result = pandas_named_aggregation(clean_frame)
    polars_frame = polars_lazy_aggregation(csv_path, bounds)
    polars_result = polars_to_pandas(polars_frame)
    duckdb_result = duckdb_sql_aggregation(csv_path, bounds)

    print_result("2) Pandas groupby named aggregation", pandas_result, args.rows)
    print_result("3) Polars Lazy API 집계 결과", polars_result, args.rows)
    print_result("4) DuckDB SQL 집계 결과", duckdb_result, args.rows)
    verify_equal_results(pandas_result, polars_result, duckdb_result)

    benchmark_result = benchmark_tools(
        csv_path,
        bounds,
        number=args.number,
        repeat=args.repeat,
    )
    print("\n" + "=" * 72)
    print("5) timeit 성능 비교 - 동일 number/repeat 적용")
    print("=" * 72)
    print(benchmark_result.round(4).to_string(index=False))

    save_outputs(
        args.output_dir,
        pandas_result,
        polars_result,
        duckdb_result,
        benchmark_result,
    )


def main() -> int:
    """예상 가능한 오류를 사용자 친화적인 메시지로 처리한다."""

    configure_logging()
    try:
        run(parse_args())
    except (FileNotFoundError, PermissionError, Practice3Error) as error:
        LOGGER.error("실습 실행 실패: %s", error)
        return 1
    except KeyboardInterrupt:
        LOGGER.warning("사용자가 실행을 중단했습니다.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
