"""Practice 4 - 시각화, 통계 검정, sklearn Pipeline.

작성자: 이상수

프로그램 설명
------------
Practice 3에서 사용한 sales_100k.csv와 IQR 정제 결과를 연결해 다음을 수행한다.
1. 2×2 서브플롯에 EDA 시각화 4종 저장
2. 서울·부산 평균 매출 t-test와 지역·카테고리 카이제곱 검정
3. ColumnTransformer + Pipeline 학습·평가·저장·재로딩
4. 지역·카테고리별 총매출 Plotly 인터랙티브 HTML 저장

변경 내역
---------
- 2026-07-16: Practice 4 요구사항에 맞춰 최초 작성
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from practice3 import (
    Practice3Error,
    calculate_iqr_bounds,
    load_pandas,
    pandas_named_aggregation,
    remove_amount_outliers,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LOGGER = logging.getLogger("practice4")
SIGNIFICANCE_LEVEL = 0.05
NUMERIC_FEATURES = ["quantity", "unit_price", "customer_age"]
CATEGORICAL_FEATURES = ["region", "category", "payment_method", "customer_gender"]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET_COLUMN = "amount"
PRACTICE4_COLUMNS = {
    "order_date",
    "region",
    "category",
    "payment_method",
    "customer_gender",
    "quantity",
    "unit_price",
    "customer_age",
    "amount",
}


class Practice4Error(RuntimeError):
    """Practice 4 입력이나 분석 단계가 요구사항을 만족하지 않을 때 발생한다."""


@dataclass(frozen=True)
class TTestResult:
    """서울·부산 독립표본 t-test 결과."""

    seoul_count: int
    busan_count: int
    seoul_mean: float
    busan_mean: float
    t_statistic: float
    p_value: float
    significant: bool
    interpretation: str


@dataclass(frozen=True)
class ChiSquareResult:
    """지역·카테고리 독립성 카이제곱 검정 결과."""

    rows: int
    columns: int
    chi2_statistic: float
    p_value: float
    degrees_of_freedom: int
    min_expected_frequency: float
    significant: bool
    interpretation: str


@dataclass(frozen=True)
class ModelMetrics:
    """Pipeline 학습·저장·재로딩 평가 지표."""

    train_rows: int
    test_rows: int
    r2_score: float
    reloaded_r2_score: float
    mae: float
    rmse: float
    reload_prediction_match: bool


def configure_logging() -> None:
    """분석 진행 상황과 오류를 보기 쉬운 형식으로 출력한다."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def validate_practice4_columns(frame: pd.DataFrame) -> None:
    """시각화·통계·모델링에 필요한 컬럼을 검사한다."""

    missing = PRACTICE4_COLUMNS.difference(frame.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise Practice4Error(f"Practice 4 필수 컬럼이 없습니다: {names}")


def prepare_clean_data(csv_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Practice 3과 같은 Pandas 로딩 및 IQR 이상치 제거를 수행한다."""

    raw_frame = load_pandas(csv_path)
    validate_practice4_columns(raw_frame)
    bounds = calculate_iqr_bounds(raw_frame[TARGET_COLUMN])
    clean_frame = remove_amount_outliers(raw_frame, bounds)
    if clean_frame.empty:
        raise Practice4Error("IQR 처리 후 데이터가 남아 있지 않습니다.")
    return raw_frame, clean_frame


def configure_korean_font() -> None:
    """macOS 한글 표시와 음수 기호 깨짐을 방지한다."""

    plt.rcParams["font.family"] = ["AppleGothic", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def create_eda_figure(
    clean_frame: pd.DataFrame,
    output_path: Path,
    sample_size: int = 50_000,
) -> None:
    """히스토그램·박스플롯·월별 라인·상관 히트맵을 2×2 한 figure에 저장한다."""

    if sample_size < 100:
        raise Practice4Error("시각화 표본 크기는 100 이상이어야 합니다.")

    configure_korean_font()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample_count = min(sample_size, len(clean_frame))
    plot_sample = clean_frame.sample(n=sample_count, random_state=42)

    date_amount = clean_frame[["order_date", "amount"]].copy()
    date_amount["order_date"] = pd.to_datetime(date_amount["order_date"], errors="coerce")
    date_amount = date_amount.dropna(subset=["order_date", "amount"])
    monthly = (
        date_amount.assign(month=date_amount["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["amount"]
        .sum()
    )

    correlation_columns = ["quantity", "unit_price", "customer_age", "amount"]
    correlation = clean_frame[correlation_columns].corr()

    fig, axes = plt.subplots(2, 2, figsize=(17, 12))

    sns.histplot(plot_sample["amount"], bins=50, kde=True, ax=axes[0, 0], color="steelblue")
    axes[0, 0].set_title("매출 분포: 히스토그램 + KDE")
    axes[0, 0].set_xlabel("매출액")
    axes[0, 0].set_ylabel("건수")

    sns.boxplot(data=plot_sample, x="region", y="amount", ax=axes[0, 1], color="lightgreen")
    axes[0, 1].set_title("지역별 매출 박스플롯")
    axes[0, 1].set_xlabel("지역")
    axes[0, 1].set_ylabel("매출액")
    axes[0, 1].tick_params(axis="x", rotation=30)

    sns.lineplot(data=monthly, x="month", y="amount", marker="o", ax=axes[1, 0])
    axes[1, 0].set_title("월별 총매출 추이")
    axes[1, 0].set_xlabel("월")
    axes[1, 0].set_ylabel("총매출")
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].grid(alpha=0.3)

    sns.heatmap(
        correlation,
        annot=True,
        cmap="coolwarm",
        center=0,
        fmt=".2f",
        square=True,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("수치형 변수 상관 히트맵")

    fig.suptitle("Practice 4 - EDA 시각화 4종", fontsize=18, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    LOGGER.info("2×2 EDA 시각화를 저장했습니다: %s", output_path)


def run_seoul_busan_t_test(clean_frame: pd.DataFrame) -> TTestResult:
    """서울과 부산의 평균 amount 차이를 Welch 독립표본 t-test로 검정한다."""

    seoul = clean_frame.loc[clean_frame["region"] == "서울", "amount"].dropna()
    busan = clean_frame.loc[clean_frame["region"] == "부산", "amount"].dropna()
    if len(seoul) < 2 or len(busan) < 2:
        raise Practice4Error("서울·부산 t-test에는 각 그룹에 2개 이상의 값이 필요합니다.")

    t_statistic, p_value = stats.ttest_ind(seoul, busan, equal_var=False, nan_policy="omit")
    significant = bool(p_value < SIGNIFICANCE_LEVEL)
    interpretation = (
        "p-value < 0.05이므로 서울과 부산의 평균 매출은 통계적으로 유의한 차이가 있다."
        if significant
        else "p-value >= 0.05이므로 서울과 부산의 평균 매출 차이는 통계적으로 유의하지 않다."
    )
    return TTestResult(
        seoul_count=len(seoul),
        busan_count=len(busan),
        seoul_mean=float(seoul.mean()),
        busan_mean=float(busan.mean()),
        t_statistic=float(t_statistic),
        p_value=float(p_value),
        significant=significant,
        interpretation=interpretation,
    )


def run_region_category_chi_square(clean_frame: pd.DataFrame) -> ChiSquareResult:
    """지역과 카테고리의 독립성을 분할표와 카이제곱 검정으로 확인한다."""

    contingency = pd.crosstab(clean_frame["region"], clean_frame["category"])
    if contingency.shape[0] < 2 or contingency.shape[1] < 2:
        raise Practice4Error("카이제곱 검정에는 각 변수가 2개 이상의 범주를 가져야 합니다.")

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    significant = bool(p_value < SIGNIFICANCE_LEVEL)
    interpretation = (
        "p-value < 0.05이므로 지역과 카테고리는 서로 독립적이지 않다."
        if significant
        else "p-value >= 0.05이므로 지역과 카테고리가 독립이라는 귀무가설을 기각할 수 없다."
    )
    return ChiSquareResult(
        rows=contingency.shape[0],
        columns=contingency.shape[1],
        chi2_statistic=float(chi2),
        p_value=float(p_value),
        degrees_of_freedom=int(dof),
        min_expected_frequency=float(expected.min()),
        significant=significant,
        interpretation=interpretation,
    )


def print_statistical_results(t_test: TTestResult, chi_square: ChiSquareResult) -> None:
    """통계량, p-value와 유의미 여부 해석을 한 줄 이상 명확히 출력한다."""

    print("\n" + "=" * 76)
    print("2) 통계 검정 - t-test + 카이제곱")
    print("=" * 76)
    print("[서울 vs 부산 평균 매출 Welch t-test]")
    print(f"서울: n={t_test.seoul_count:,}, 평균={t_test.seoul_mean:,.2f}")
    print(f"부산: n={t_test.busan_count:,}, 평균={t_test.busan_mean:,.2f}")
    print(f"t 통계량={t_test.t_statistic:.6f}, p-value={t_test.p_value:.8f}")
    print(f"해석: {t_test.interpretation}")

    print("\n[지역 × 카테고리 카이제곱 독립성 검정]")
    print(f"분할표 크기: {chi_square.rows} × {chi_square.columns}")
    print(
        f"카이제곱={chi_square.chi2_statistic:.6f}, "
        f"자유도={chi_square.degrees_of_freedom}, p-value={chi_square.p_value:.8f}"
    )
    print(f"최소 기대빈도={chi_square.min_expected_frequency:,.2f}")
    print(f"해석: {chi_square.interpretation}")


def build_model_pipeline() -> Pipeline:
    """전처리와 Ridge 회귀 모델을 하나의 sklearn Pipeline으로 구성한다."""

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", Ridge(alpha=1.0, solver="lsqr")),
        ]
    )


def train_save_reload_pipeline(
    clean_frame: pd.DataFrame,
    model_path: Path,
    test_size: float = 0.2,
) -> ModelMetrics:
    """Pipeline을 fit·predict·score한 뒤 joblib 저장과 재로딩까지 검증한다."""

    if not 0.05 <= test_size <= 0.5:
        raise Practice4Error("test_size는 0.05 이상 0.5 이하여야 합니다.")

    model_frame = clean_frame[MODEL_FEATURES + [TARGET_COLUMN]].copy()
    model_frame[TARGET_COLUMN] = pd.to_numeric(model_frame[TARGET_COLUMN], errors="coerce")
    model_frame = model_frame.dropna(subset=[TARGET_COLUMN])
    if len(model_frame) < 20:
        raise Practice4Error("Pipeline 학습에는 최소 20행이 필요합니다.")

    features = model_frame[MODEL_FEATURES]
    target = model_frame[TARGET_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=42,
    )

    pipeline = build_model_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    score = float(pipeline.score(x_test, y_test))
    mae = float(mean_absolute_error(y_test, predictions))
    rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    reloaded_pipeline = joblib.load(model_path)
    reloaded_predictions = reloaded_pipeline.predict(x_test)
    reloaded_score = float(reloaded_pipeline.score(x_test, y_test))
    prediction_match = bool(np.allclose(predictions, reloaded_predictions, rtol=1e-10))
    if not prediction_match:
        raise Practice4Error("저장 전과 재로딩 후 예측값이 일치하지 않습니다.")

    return ModelMetrics(
        train_rows=len(x_train),
        test_rows=len(x_test),
        r2_score=score,
        reloaded_r2_score=reloaded_score,
        mae=mae,
        rmse=rmse,
        reload_prediction_match=prediction_match,
    )


def print_model_metrics(metrics: ModelMetrics, model_path: Path) -> None:
    """Pipeline 학습·평가·저장·재로딩 결과를 출력한다."""

    print("\n" + "=" * 76)
    print("3) sklearn ColumnTransformer + Pipeline")
    print("=" * 76)
    print(f"학습 행 수: {metrics.train_rows:,}")
    print(f"평가 행 수: {metrics.test_rows:,}")
    print(f"R² score: {metrics.r2_score:.6f}")
    print(f"MAE: {metrics.mae:,.2f}")
    print(f"RMSE: {metrics.rmse:,.2f}")
    print(f"재로딩 R² score: {metrics.reloaded_r2_score:.6f}")
    print(f"저장 전·후 예측 일치: {metrics.reload_prediction_match}")
    print(f"모델 저장: {model_path}")


def create_plotly_chart(grouped: pd.DataFrame, output_path: Path) -> None:
    """지역·카테고리별 총매출 막대 차트를 인터랙티브 HTML로 저장한다."""

    plot_frame = grouped.dropna(subset=["region", "category"]).copy()
    if plot_frame.empty:
        raise Practice4Error("Plotly 차트에 사용할 지역·카테고리 집계가 없습니다.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure = px.bar(
        plot_frame,
        x="region",
        y="total",
        color="category",
        barmode="group",
        hover_data={"mean": ":,.2f", "count": ":,", "total": ":,.2f"},
        title="지역·카테고리별 총매출",
        labels={
            "region": "지역",
            "total": "총매출",
            "category": "카테고리",
            "mean": "평균 매출",
            "count": "거래 건수",
        },
    )
    figure.update_layout(template="plotly_white", legend_title_text="카테고리")
    figure.write_html(output_path, include_plotlyjs="cdn", full_html=True)
    LOGGER.info("Plotly 인터랙티브 차트를 저장했습니다: %s", output_path)


def save_numeric_results(
    output_dir: Path,
    t_test: TTestResult,
    chi_square: ChiSquareResult,
    model_metrics: ModelMetrics,
) -> None:
    """통계 검정 결과는 JSON, 모델 평가지표는 CSV로 저장한다."""

    output_dir.mkdir(parents=True, exist_ok=True)
    statistics_payload = {
        "author": "이상수",
        "significance_level": SIGNIFICANCE_LEVEL,
        "t_test": asdict(t_test),
        "chi_square": asdict(chi_square),
    }
    (output_dir / "practice4_statistics.json").write_text(
        json.dumps(statistics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame([asdict(model_metrics)]).to_csv(
        output_dir / "practice4_model_metrics.csv",
        index=False,
    )


def parse_args() -> argparse.Namespace:
    """입력 데이터, 출력 폴더, 시각화 표본과 테스트 비율을 받는다."""

    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=base_dir / "sales_100k.csv",
        help="분석할 sales CSV 경로",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "output",
        help="차트·모델·통계 결과 저장 폴더",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50_000,
        help="히스토그램·박스플롯에 사용할 재현 가능한 표본 크기",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="모델 평가 데이터 비율")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    """Practice 3 연계부터 Practice 4 전체 산출물 저장까지 순서대로 실행한다."""

    csv_path = args.csv_path.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {csv_path}")

    LOGGER.info("Practice 3 IQR 정제 데이터를 준비합니다: %s", csv_path)
    raw_frame, clean_frame = prepare_clean_data(csv_path)
    print("\n" + "=" * 76)
    print("1) Practice 3 → 4 연계 및 2×2 EDA")
    print("=" * 76)
    print(f"원본 행 수: {len(raw_frame):,}")
    print(f"IQR 정제 후 행 수: {len(clean_frame):,}")

    eda_path = output_dir / "practice4_eda_2x2.png"
    create_eda_figure(clean_frame, eda_path, sample_size=args.sample_size)

    t_test_result = run_seoul_busan_t_test(clean_frame)
    chi_square_result = run_region_category_chi_square(clean_frame)
    print_statistical_results(t_test_result, chi_square_result)

    model_path = output_dir / "practice4_pipeline.joblib"
    model_metrics = train_save_reload_pipeline(
        clean_frame,
        model_path,
        test_size=args.test_size,
    )
    print_model_metrics(model_metrics, model_path)

    grouped = pandas_named_aggregation(clean_frame)
    plotly_path = output_dir / "practice4_region_category.html"
    create_plotly_chart(grouped, plotly_path)
    save_numeric_results(output_dir, t_test_result, chi_square_result, model_metrics)

    print("\n" + "=" * 76)
    print("4) 산출물 저장 완료")
    print("=" * 76)
    print(f"EDA 2×2 PNG: {eda_path}")
    print(f"Plotly HTML: {plotly_path}")
    print(f"Pipeline 모델: {model_path}")
    print(f"통계 JSON: {output_dir / 'practice4_statistics.json'}")
    print(f"모델 지표 CSV: {output_dir / 'practice4_model_metrics.csv'}")


def main() -> int:
    """예상 가능한 파일·데이터·분석 오류를 사용자 친화적으로 처리한다."""

    configure_logging()
    try:
        run(parse_args())
    except (FileNotFoundError, PermissionError, OSError, Practice3Error, Practice4Error) as error:
        LOGGER.error("Practice 4 실행 실패: %s", error)
        return 1
    except KeyboardInterrupt:
        LOGGER.warning("사용자가 실행을 중단했습니다.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
