"""종합실습 2 - 서울시 상권 추정매출 분석과 회귀 Pipeline.

작성자: 이상수

프로그램 설명
------------
1. 서울시 상권분석서비스 CSV의 인코딩과 필수 컬럼을 검사해 로딩한다.
2. 서비스 업종별 당월 매출을 집계하고 내림차순 상위 10개를 저장한다.
3. 10대·20대·30대 매출 합계를 막대그래프로 저장한다.
4. 수치형·범주형 전처리와 회귀 모델을 하나의 Pipeline으로 학습·평가·저장한다.

변경 내역
---------
- 2026-07-16: 종합실습 2 요구사항에 맞춰 최초 작성
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

LOGGER = logging.getLogger("comprehensive_practice2")
SELECTED_COLUMNS = [
    "상권_코드_명",
    "상권_구분_코드_명",
    "서비스_업종_코드",
    "서비스_업종_코드_명",
    "당월_매출_금액",
    "남성_매출_금액",
    "여성_매출_금액",
    "연령대_10_매출_금액",
    "연령대_20_매출_금액",
    "연령대_30_매출_금액",
]
NUMERIC_FEATURES = [
    "연령대_10_매출_금액",
    "연령대_20_매출_금액",
    "연령대_30_매출_금액",
]
CATEGORICAL_FEATURES = ["상권_구분_코드_명"]
TARGET_COLUMN = "당월_매출_금액"
NUMERIC_COLUMNS = [TARGET_COLUMN, "남성_매출_금액", "여성_매출_금액", *NUMERIC_FEATURES]
DEFAULT_CSV_NAME = "서울시 상권분석서비스(추정매출-상권).csv"


class ComprehensivePractice2Error(RuntimeError):
    """입력 데이터나 분석 설정이 실습 요구사항을 만족하지 않을 때 발생한다."""


@dataclass(frozen=True)
class DataQualityReport:
    """CSV 로딩 및 선택 컬럼 품질 점검 결과."""

    encoding: str
    rows: int
    columns: int
    selected_duplicate_rows: int
    missing_values: dict[str, int]
    negative_values: dict[str, int]
    zero_values: dict[str, int]


@dataclass(frozen=True)
class ModelMetrics:
    """회귀 Pipeline의 학습·평가·재로딩 결과."""

    train_rows: int
    test_rows: int
    r2_score: float
    reloaded_r2_score: float
    mae: float
    rmse: float
    reload_prediction_match: bool


def configure_logging() -> None:
    """진행 상황과 오류를 읽기 쉬운 형식으로 출력한다."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


def detect_csv_encoding(csv_path: Path) -> str:
    """서울 열린데이터 CSV에서 흔한 UTF-8·CP949 인코딩을 안전하게 판별한다."""

    errors: list[str] = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            pd.read_csv(csv_path, encoding=encoding, nrows=3)
            return encoding
        except UnicodeDecodeError as error:
            errors.append(f"{encoding}: {error.reason}")
    raise ComprehensivePractice2Error(f"CSV 한글 인코딩을 판별할 수 없습니다: {'; '.join(errors)}")


def validate_columns(columns: pd.Index) -> None:
    """과제에서 지정한 10개 컬럼이 모두 존재하는지 확인한다."""

    missing = sorted(set(SELECTED_COLUMNS).difference(columns))
    if missing:
        raise ComprehensivePractice2Error(f"필수 컬럼이 없습니다: {', '.join(missing)}")


def load_sales_data(csv_path: Path) -> tuple[pd.DataFrame, DataQualityReport]:
    """인코딩을 판별하고 지정 컬럼만 읽은 뒤 자료형과 품질을 검사한다."""

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
    encoding = detect_csv_encoding(csv_path)
    header = pd.read_csv(csv_path, encoding=encoding, nrows=0)
    validate_columns(header.columns)
    frame = pd.read_csv(csv_path, encoding=encoding, usecols=SELECTED_COLUMNS)
    frame = frame[SELECTED_COLUMNS].copy()
    if frame.empty:
        raise ComprehensivePractice2Error("CSV에 분석할 데이터 행이 없습니다.")

    text_columns = [column for column in SELECTED_COLUMNS if column not in NUMERIC_COLUMNS]
    for column in text_columns:
        frame[column] = frame[column].astype("string").str.strip()
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    report = DataQualityReport(
        encoding=encoding,
        rows=len(frame),
        columns=len(frame.columns),
        selected_duplicate_rows=int(frame.duplicated().sum()),
        missing_values={column: int(frame[column].isna().sum()) for column in SELECTED_COLUMNS},
        negative_values={column: int(frame[column].lt(0).sum()) for column in NUMERIC_COLUMNS},
        zero_values={column: int(frame[column].eq(0).sum()) for column in NUMERIC_COLUMNS},
    )
    LOGGER.info("CSV 로딩 완료: encoding=%s, rows=%s", encoding, f"{len(frame):,}")
    return frame, report


def aggregate_top10_services(frame: pd.DataFrame) -> pd.DataFrame:
    """서비스 업종별 당월 매출 합계를 내림차순으로 정렬해 상위 10개를 반환한다."""

    valid = frame.dropna(subset=["서비스_업종_코드_명", TARGET_COLUMN])
    if valid.empty:
        raise ComprehensivePractice2Error("업종별 매출 집계에 사용할 유효 행이 없습니다.")
    return (
        valid.groupby("서비스_업종_코드_명", as_index=False, observed=True)
        .agg(당월_매출_금액_합계=(TARGET_COLUMN, "sum"))
        .sort_values("당월_매출_금액_합계", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )


def configure_korean_font() -> None:
    """macOS에서 그래프 한글과 음수 기호가 깨지지 않게 설정한다."""

    plt.rcParams["font.family"] = ["AppleGothic", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def create_age_sales_chart(frame: pd.DataFrame, output_path: Path) -> pd.Series:
    """10대·20대·30대 매출의 컬럼별 합계를 막대그래프로 저장한다."""

    totals = frame[NUMERIC_FEATURES].sum(min_count=1)
    if totals.isna().any():
        raise ComprehensivePractice2Error("연령대별 매출 합계를 계산할 수 없습니다.")

    configure_korean_font()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels = ["10대", "20대", "30대"]
    fig, axis = plt.subplots(figsize=(10, 6))
    bars = axis.bar(labels, totals.to_numpy(), color=["#4C78A8", "#F58518", "#54A24B"])
    axis.set_title("연령대별 추정 매출 합계")
    axis.set_xlabel("연령대")
    axis.set_ylabel("매출 합계")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1e12:.1f}조"))
    axis.grid(axis="y", alpha=0.25)
    for bar, value in zip(bars, totals.to_numpy(), strict=True):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value / 1e12:.2f}조",
            ha="center",
            va="bottom",
        )
    fig.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    LOGGER.info("연령대별 매출 그래프 저장: %s", output_path)
    return totals


def build_model_pipeline() -> Pipeline:
    """수치형·범주형 전처리와 회귀 모델을 하나의 Pipeline으로 결합한다."""

    numeric_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical_pipeline = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    missing_values=pd.NA,
                    strategy="constant",
                    fill_value="missing",
                ),
            ),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        sparse_threshold=0,
    )
    model = ExtraTreesRegressor(
        n_estimators=50,
        max_depth=18,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def train_evaluate_save_pipeline(
    frame: pd.DataFrame,
    model_path: Path,
    test_size: float = 0.2,
) -> ModelMetrics:
    """Pipeline을 학습·평가하고 joblib 저장 후 재로딩 결과까지 확인한다."""

    if not 0.05 <= test_size <= 0.5:
        raise ComprehensivePractice2Error("test_size는 0.05 이상 0.5 이하여야 합니다.")
    model_frame = frame[[*NUMERIC_FEATURES, *CATEGORICAL_FEATURES, TARGET_COLUMN]].dropna(
        subset=[TARGET_COLUMN]
    )
    if len(model_frame) < 30:
        raise ComprehensivePractice2Error("모델 학습에는 유효한 데이터가 최소 30행 필요합니다.")

    features = model_frame[[*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]]
    target = model_frame[TARGET_COLUMN]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=test_size, random_state=42
    )
    pipeline = build_model_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    score = float(pipeline.score(x_test, y_test))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    reloaded_pipeline = joblib.load(model_path)
    reloaded_predictions = reloaded_pipeline.predict(x_test)
    reloaded_score = float(reloaded_pipeline.score(x_test, y_test))
    return ModelMetrics(
        train_rows=len(x_train),
        test_rows=len(x_test),
        r2_score=score,
        reloaded_r2_score=reloaded_score,
        mae=float(mean_absolute_error(y_test, predictions)),
        rmse=float(np.sqrt(mean_squared_error(y_test, predictions))),
        reload_prediction_match=bool(np.allclose(predictions, reloaded_predictions)),
    )


def save_results(
    output_dir: Path,
    top10: pd.DataFrame,
    quality: DataQualityReport,
    metrics: ModelMetrics,
) -> None:
    """집계·데이터 품질·모델 성능 결과를 재사용 가능한 파일로 저장한다."""

    output_dir.mkdir(parents=True, exist_ok=True)
    top10.to_csv(
        output_dir / "comprehensive_practice2_top10.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame([asdict(metrics)]).to_csv(
        output_dir / "comprehensive_practice2_metrics.csv", index=False
    )
    (output_dir / "comprehensive_practice2_data_quality.json").write_text(
        json.dumps(asdict(quality), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def print_results(
    frame: pd.DataFrame,
    quality: DataQualityReport,
    top10: pd.DataFrame,
    age_totals: pd.Series,
    metrics: ModelMetrics,
) -> None:
    """데이터 점검, 상위 업종, 연령대 합계와 모델 성능을 터미널에 출력한다."""

    print("\n[1) CSV 및 선택 컬럼 점검]")
    print(f"인코딩: {quality.encoding}")
    print(f"데이터 크기: {len(frame):,}행 × {len(frame.columns)}열")
    print(f"선택 컬럼 기준 중복 행: {quality.selected_duplicate_rows:,}")
    print(f"전체 결측치: {sum(quality.missing_values.values()):,}")
    print(f"전체 음수값: {sum(quality.negative_values.values()):,}")
    print("\n[2) 서비스 업종별 당월 매출 합계 TOP 10]")
    print(top10.to_string(index=False, formatters={"당월_매출_금액_합계": "{:,.0f}".format}))
    print("\n[3) 연령대별 매출 합계]")
    for column, total in age_totals.items():
        print(f"{column}: {total:,.0f}")
    print("\n[4) 최종 모델 Pipeline 성능]")
    print(f"학습 행 수: {metrics.train_rows:,}")
    print(f"평가 행 수: {metrics.test_rows:,}")
    print(f"R² score: {metrics.r2_score:.6f}")
    print(f"MAE: {metrics.mae:,.2f}")
    print(f"RMSE: {metrics.rmse:,.2f}")
    print(f"재로딩 R² score: {metrics.reloaded_r2_score:.6f}")
    print(f"저장 전·후 예측 일치: {metrics.reload_prediction_match}")


def parse_args() -> argparse.Namespace:
    """CSV 경로, 출력 폴더, 평가 비율과 결과 자동 열기 옵션을 받는다."""

    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", type=Path, default=base_dir / DEFAULT_CSV_NAME)
    parser.add_argument("--output-dir", type=Path, default=base_dir / "output")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--open-results", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    """CSV 점검부터 집계·그래프·Pipeline 학습·저장까지 순서대로 실행한다."""

    csv_path = args.csv_path.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    frame, quality = load_sales_data(csv_path)
    top10 = aggregate_top10_services(frame)
    chart_path = output_dir / "comprehensive_practice2_age_sales.png"
    age_totals = create_age_sales_chart(frame, chart_path)
    model_path = output_dir / "comprehensive_practice2_pipeline.joblib"
    metrics = train_evaluate_save_pipeline(frame, model_path, test_size=args.test_size)
    save_results(output_dir, top10, quality, metrics)
    print_results(frame, quality, top10, age_totals, metrics)
    print("\n[5) 산출물 저장 완료]")
    print(f"상위 10개 업종 CSV: {output_dir / 'comprehensive_practice2_top10.csv'}")
    print(f"연령대 매출 그래프: {chart_path}")
    print(f"최종 Pipeline 모델: {model_path}")
    print(f"모델 성능 CSV: {output_dir / 'comprehensive_practice2_metrics.csv'}")
    print(f"데이터 품질 JSON: {output_dir / 'comprehensive_practice2_data_quality.json'}")
    if args.open_results:
        try:
            webbrowser.open(chart_path.resolve().as_uri(), new=2)
        except webbrowser.Error as error:
            LOGGER.warning("그래프를 자동으로 열지 못했습니다: %s", error)


def main() -> int:
    """파일·인코딩·데이터·모델 오류를 사용자 친화적으로 처리한다."""

    configure_logging()
    try:
        run(parse_args())
    except (
        FileNotFoundError,
        PermissionError,
        OSError,
        pd.errors.ParserError,
        ComprehensivePractice2Error,
    ) as error:
        LOGGER.error("종합실습 2 실행 실패: %s", error)
        return 1
    except KeyboardInterrupt:
        LOGGER.warning("사용자가 실행을 중단했습니다.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
