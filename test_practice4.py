"""Practice 4 시각화·통계·Pipeline 핵심 기능 테스트.

작성자: 이상수
"""

from pathlib import Path

import numpy as np
import pandas as pd

from practice4 import (
    build_model_pipeline,
    create_eda_figure,
    create_plotly_chart,
    run_region_category_chi_square,
    run_seoul_busan_t_test,
    train_save_reload_pipeline,
)


def make_sample_frame(rows: int = 120) -> pd.DataFrame:
    """두 지역·카테고리와 모델 입력 컬럼을 가진 재현 가능한 표본을 만든다."""

    rng = np.random.default_rng(42)
    quantity = rng.integers(1, 20, size=rows)
    unit_price = rng.integers(1_000, 100_000, size=rows)
    regions = np.where(np.arange(rows) % 2 == 0, "서울", "부산")
    categories = np.where(np.arange(rows) % 3 == 0, "전자", "식품")
    amount = quantity * unit_price + np.where(regions == "서울", 2_000, 0)
    return pd.DataFrame(
        {
            "order_date": pd.date_range("2025-01-01", periods=rows, freq="D").astype(str),
            "region": regions,
            "category": categories,
            "payment_method": np.where(np.arange(rows) % 2 == 0, "카드", "현금"),
            "customer_gender": np.where(np.arange(rows) % 2 == 0, "M", "F"),
            "quantity": quantity,
            "unit_price": unit_price,
            "customer_age": rng.integers(18, 70, size=rows),
            "amount": amount.astype(float),
        }
    )


def test_statistical_tests_return_interpretation() -> None:
    """t-test와 카이제곱 결과에 통계량·p-value·해석이 포함되는지 확인한다."""

    frame = make_sample_frame()
    t_test = run_seoul_busan_t_test(frame)
    chi_square = run_region_category_chi_square(frame)

    assert t_test.seoul_count == 60
    assert t_test.busan_count == 60
    assert 0 <= t_test.p_value <= 1
    assert "p-value" in t_test.interpretation
    assert chi_square.rows == 2
    assert chi_square.columns == 2
    assert 0 <= chi_square.p_value <= 1
    assert chi_square.interpretation


def test_pipeline_fit_save_reload(tmp_path: Path) -> None:
    """ColumnTransformer Pipeline의 학습·저장·재로딩 결과를 확인한다."""

    frame = make_sample_frame(200)
    pipeline = build_model_pipeline()
    assert "preprocessor" in pipeline.named_steps
    assert "model" in pipeline.named_steps

    model_path = tmp_path / "pipeline.joblib"
    metrics = train_save_reload_pipeline(frame, model_path, test_size=0.2)

    assert model_path.exists()
    assert metrics.train_rows == 160
    assert metrics.test_rows == 40
    assert metrics.reload_prediction_match is True
    assert metrics.r2_score == metrics.reloaded_r2_score


def test_visual_outputs_are_saved(tmp_path: Path) -> None:
    """2×2 PNG와 Plotly HTML 파일이 실제로 저장되는지 확인한다."""

    frame = make_sample_frame()
    png_path = tmp_path / "eda.png"
    html_path = tmp_path / "chart.html"
    grouped = (
        frame.groupby(["region", "category"])
        .agg(total=("amount", "sum"), mean=("amount", "mean"), count=("amount", "count"))
        .reset_index()
    )

    create_eda_figure(frame, png_path, sample_size=120)
    create_plotly_chart(grouped, html_path)

    assert png_path.exists() and png_path.stat().st_size > 10_000
    assert html_path.exists() and "plotly" in html_path.read_text(encoding="utf-8").lower()
