# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 종합실습 1-5, 서울 현재기온 25도 조건과 파일 I/O를 pytest로 검사
# 작성일 : 2026년 7월 15일
# 변경사항 : 0.1 - 모의 API, Fail 메시지, CSV·Parquet 테스트 추가
# -----------------------------------------------------------------------------

"""Step 5: pytest checks for API conversion and file round trips."""

import asyncio

import httpx
import pandas as pd
import pytest

from comprehensive_step1_async_api import fetch_city_data
from comprehensive_step2_pydantic import Weather
from comprehensive_step3_csv import load_csv, save_csv, to_dataframe
from comprehensive_step4_parquet import load_parquet_summary, save_parquet

SEOUL = {
    "name": "서울",
    "lat": 37.5665,
    "lon": 126.9780,
    "tz": "Asia/Seoul",
}


def mock_api_response(request: httpx.Request) -> httpx.Response:
    """서울 좌표에 대한 두 공공 API의 모의 응답을 만든다."""

    if request.url.host == "api.open-meteo.com":
        assert float(request.url.params["latitude"]) == SEOUL["lat"]
        assert float(request.url.params["longitude"]) == SEOUL["lon"]
        return httpx.Response(200, json={"current_weather": {"temperature": 25.0}})
    if request.url.host == "countries.dev":
        assert request.url.path.endswith("/KR")
        return httpx.Response(
            200,
            json={"name": "Korea (Republic of)", "timezones": ["UTC+09:00"]},
        )
    return httpx.Response(404, json={"error": "unknown host"})


def test_seoul_temperature_from_coordinates_is_25() -> None:
    """서울의 모의 현재기온이 정확히 25도인지 확인한다."""

    async def run_test() -> Weather:
        transport = httpx.MockTransport(mock_api_response)
        async with httpx.AsyncClient(transport=transport) as client:
            raw_data = await fetch_city_data(SEOUL, client)
            return Weather.model_validate(raw_data)

    weather = asyncio.run(run_test())
    assert float(weather.temperature) == 25.0, "Fail: 현재 기온이 25도가 아닙니다."


def test_non_25_temperature_has_fail_message() -> None:
    """25도가 아니면 Fail 메시지를 가진 AssertionError가 발생한다."""

    weather = Weather(city="서울", temperature=24.9, local_time="07/15/2026 16:00")
    with pytest.raises(AssertionError, match="Fail"):
        assert float(weather.temperature) == 25.0, "Fail: 현재 기온이 25도가 아닙니다."


def test_csv_and_parquet_round_trip(tmp_path) -> None:
    """CSV와 Parquet 파일의 저장·재로딩 결과를 확인한다."""

    records = [
        Weather(city="서울", temperature=25.0, local_time="07/15/2026 16:00"),
        Weather(city="도쿄", temperature=28.1, local_time="07/15/2026 16:00"),
    ]
    data = to_dataframe(records)
    csv_path = tmp_path / "weather.csv"
    parquet_path = tmp_path / "weather.parquet"

    assert save_csv(data, csv_path)
    reloaded_csv = load_csv(csv_path)
    assert reloaded_csv is not None
    pd.testing.assert_frame_equal(reloaded_csv, data, check_dtype=False)

    assert save_parquet(data, parquet_path)
    reloaded_parquet = load_parquet_summary(parquet_path)
    assert reloaded_parquet is not None
    assert list(reloaded_parquet.columns) == ["도시", "기온"]


def test_missing_files_return_none(tmp_path) -> None:
    """없는 CSV와 Parquet를 읽으면 None이 반환되는지 확인한다."""

    assert load_csv(tmp_path / "missing.csv") is None
    assert load_parquet_summary(tmp_path / "missing.parquet") is None
