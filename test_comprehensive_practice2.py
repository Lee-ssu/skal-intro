"""종합실습 2 집계·그래프·Pipeline 핵심 기능 테스트.

작성자: 이상수
"""

from pathlib import Path

import numpy as np
import pandas as pd

from comprehensive_practice2 import (
    NUMERIC_FEATURES,
    aggregate_top10_services,
    build_model_pipeline,
    create_age_sales_chart,
    load_sales_data,
    train_evaluate_save_pipeline,
)


def make_sample_frame(rows: int = 120) -> pd.DataFrame:
    """과제에서 지정한 한글 컬럼을 가진 재현 가능한 표본을 만든다."""

    rng = np.random.default_rng(42)
    age10 = rng.integers(0, 100_000, size=rows).astype(float)
    age20 = rng.integers(10_000, 300_000, size=rows).astype(float)
    age30 = rng.integers(20_000, 500_000, size=rows).astype(float)
    district_type = np.where(np.arange(rows) % 2 == 0, "골목상권", "발달상권")
    target = age10 + age20 + age30 + rng.integers(0, 50_000, size=rows)
    return pd.DataFrame(
        {
            "상권_코드_명": [f"상권-{index % 10}" for index in range(rows)],
            "상권_구분_코드_명": district_type,
            "서비스_업종_코드": [f"CS{index % 12:06d}" for index in range(rows)],
            "서비스_업종_코드_명": [f"업종-{index % 12}" for index in range(rows)],
            "당월_매출_금액": target,
            "남성_매출_금액": target * 0.52,
            "여성_매출_금액": target * 0.48,
            "연령대_10_매출_금액": age10,
            "연령대_20_매출_금액": age20,
            "연령대_30_매출_금액": age30,
        }
    )


def test_cp949_csv_loading_and_quality_report(tmp_path: Path) -> None:
    """CP949 CSV를 자동 판별하고 지정 10개 컬럼만 읽는지 확인한다."""

    source = make_sample_frame(40)
    csv_path = tmp_path / "sales.csv"
    source.to_csv(csv_path, index=False, encoding="cp949")
    loaded, report = load_sales_data(csv_path)
    assert loaded.shape == (40, 10)
    assert report.encoding == "cp949"
    assert sum(report.missing_values.values()) == 0


def test_top10_aggregation_is_descending() -> None:
    """업종별 합계가 상위 10개로 제한되고 내림차순인지 확인한다."""

    top10 = aggregate_top10_services(make_sample_frame())
    assert len(top10) == 10
    assert top10["당월_매출_금액_합계"].is_monotonic_decreasing


def test_age_chart_is_saved(tmp_path: Path) -> None:
    """세 연령대 합계가 계산되고 막대그래프 PNG가 저장되는지 확인한다."""

    output_path = tmp_path / "age_sales.png"
    totals = create_age_sales_chart(make_sample_frame(), output_path)
    assert list(totals.index) == NUMERIC_FEATURES
    assert output_path.exists() and output_path.stat().st_size > 10_000


def test_pipeline_fit_save_reload(tmp_path: Path) -> None:
    """두 전처리 Pipeline과 최종 모델의 저장·재로딩 결과를 확인한다."""

    frame = make_sample_frame(240)
    frame.loc[0, "연령대_10_매출_금액"] = np.nan
    frame.loc[1, "상권_구분_코드_명"] = pd.NA
    pipeline = build_model_pipeline()
    assert "preprocessor" in pipeline.named_steps
    assert "model" in pipeline.named_steps

    model_path = tmp_path / "pipeline.joblib"
    metrics = train_evaluate_save_pipeline(frame, model_path, test_size=0.2)
    assert model_path.exists()
    assert metrics.train_rows == 192
    assert metrics.test_rows == 48
    assert metrics.reload_prediction_match is True
