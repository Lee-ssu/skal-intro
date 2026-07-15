# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 비동기 공공 API 수집부터 검증·파일 저장·테스트까지 종합 연습
# 작성일 : 2026년 7월 15일
#
# Open-Meteo에서 네 도시의 현재 기온을 비동기로 수집하고 countries.dev로
# 국가 시간대 정보를 확인합니다. Pydantic으로 검증한 결과를 CSV와 Parquet로
# 저장한 뒤 다시 읽어 데이터가 정상적으로 보존됐는지 확인합니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - 도시 목록과 비동기 API 수집 기능 작성
# 0.2 : 2026년 7월 15일 - Weather Pydantic v2 스키마와 검증 추가
# 0.3 : 2026년 7월 15일 - CSV 저장·재로딩 및 파일 예외 처리 추가
# 0.4 : 2026년 7월 15일 - Parquet 저장·선택 컬럼 재로딩 추가
# 0.5 : 2026년 7월 15일 - pytest용 25도 검증 함수와 Ruff 정리 추가
# -----------------------------------------------------------------------------

"""Final Ruff-clean asynchronous weather data pipeline for submission."""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "weather.csv"
PARQUET_PATH = BASE_DIR / "weather.parquet"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
COUNTRIES_URL = "https://countries.dev/alpha/{code}"
LOGGER = logging.getLogger("comprehensive_practice1")


class City(TypedDict):
    """API 요청에 필요한 도시 이름, 좌표와 IANA 시간대 정보."""

    name: str
    lat: float
    lon: float
    tz: str


CITIES: list[City] = [
    {"name": "서울", "lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul"},
    {"name": "도쿄", "lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo"},
    {"name": "뉴욕", "lat": 40.7128, "lon": -74.0060, "tz": "America/New_York"},
    {"name": "런던", "lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
]

COUNTRY_CODE_BY_TIMEZONE = {
    "Asia/Seoul": "KR",
    "Asia/Tokyo": "JP",
    "America/New_York": "US",
    "Europe/London": "GB",
}


class Weather(BaseModel):
    """도시, 현재 기온, 현지시각을 검증하는 Pydantic v2 모델."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    city: str = Field(alias="도시", min_length=1)
    temperature: float | str = Field(alias="기온")
    local_time: str = Field(alias="현지시각", min_length=1)

    @field_validator("temperature")
    @classmethod
    def temperature_must_not_be_blank(cls, value: float | str) -> float | str:
        """문자열 기온을 허용하되 빈 문자열은 거부한다."""

        if isinstance(value, str) and not value.strip():
            raise ValueError("기온은 비어 있을 수 없습니다.")
        return value


class DataCollectionError(RuntimeError):
    """공공 API 응답을 가져오거나 해석할 수 없을 때 발생한다."""


async def fetch_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """HTTP GET으로 JSON 객체를 가져오고 네트워크·상태 오류를 변환한다."""

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise DataCollectionError(f"API 요청 실패: {url} ({error})") from error

    if not isinstance(payload, dict):
        raise DataCollectionError(f"API 응답이 JSON 객체가 아닙니다: {url}")
    return payload


def extract_temperature(payload: Mapping[str, Any]) -> float | str:
    """Open-Meteo의 기존/현재 응답 형식에서 현재 기온을 추출한다."""

    current_weather = payload.get("current_weather")
    if isinstance(current_weather, Mapping) and "temperature" in current_weather:
        return current_weather["temperature"]

    current = payload.get("current")
    if isinstance(current, Mapping) and "temperature_2m" in current:
        return current["temperature_2m"]

    raise DataCollectionError("Open-Meteo 응답에 현재 기온이 없습니다.")


def utc_offset_label(local_time: datetime) -> str:
    """도시 시각의 UTC 오프셋을 countries.dev 형식으로 변환한다."""

    offset = local_time.utcoffset()
    if offset is None:
        raise DataCollectionError("도시의 UTC 오프셋을 계산할 수 없습니다.")

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


async def fetch_city_weather(city: City, client: httpx.AsyncClient) -> Weather:
    """한 도시의 기온과 국가 정보를 동시에 받고 Weather로 검증한다."""

    country_code = COUNTRY_CODE_BY_TIMEZONE.get(city["tz"])
    if country_code is None:
        raise DataCollectionError(f"국가 코드가 없는 시간대입니다: {city['tz']}")

    weather_request = fetch_json(
        client,
        OPEN_METEO_URL,
        params={
            "latitude": city["lat"],
            "longitude": city["lon"],
            "current_weather": "true",
        },
    )
    country_request = fetch_json(
        client,
        COUNTRIES_URL.format(code=country_code),
        params={"fields": "name,timezones"},
    )
    weather_payload, country_payload = await asyncio.gather(
        weather_request, country_request
    )

    try:
        local_time = datetime.now(ZoneInfo(city["tz"]))
    except ZoneInfoNotFoundError as error:
        raise DataCollectionError(f"시간대를 찾을 수 없습니다: {city['tz']}") from error

    country_timezones = country_payload.get("timezones", [])
    city_offset = utc_offset_label(local_time)
    if not isinstance(country_timezones, list) or city_offset not in country_timezones:
        LOGGER.warning(
            "%s의 도시 오프셋 %s를 국가 API 목록에서 확인하지 못했습니다.",
            city["name"],
            city_offset,
        )

    return Weather(
        city=city["name"],
        temperature=extract_temperature(weather_payload),
        local_time=local_time.strftime("%m/%d/%Y %H:%M"),
    )


async def collect_weather(cities: list[City] = CITIES) -> list[Weather]:
    """모든 도시 요청을 비동기로 동시에 실행한다."""

    timeout = httpx.Timeout(20.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return list(
            await asyncio.gather(*(fetch_city_weather(city, client) for city in cities))
        )


def to_dataframe(records: list[Weather]) -> pd.DataFrame:
    """Weather 객체를 한글 컬럼의 DataFrame으로 변환한다."""

    rows = [record.model_dump(by_alias=True) for record in records]
    data = pd.DataFrame(rows, columns=["도시", "기온", "현지시각"])
    numeric_temperature = pd.to_numeric(data["기온"], errors="coerce")
    if numeric_temperature.notna().all():
        data["기온"] = numeric_temperature
    else:
        # Parquet은 한 컬럼의 타입이 일정해야 하므로 숫자 변환이 불가능한
        # 값이 하나라도 있으면 전체 기온 컬럼을 문자열로 통일한다.
        data["기온"] = data["기온"].astype(str)
    return data


def save_csv(data: pd.DataFrame, path: str | Path = CSV_PATH) -> bool:
    """DataFrame을 CSV로 저장하고 파일 오류를 로그로 처리한다."""

    try:
        data.to_csv(path, index=False, encoding="utf-8-sig")
    except (OSError, ValueError) as error:
        LOGGER.error("CSV 저장 실패: %s", error)
        return False
    return True


def load_csv(path: str | Path = CSV_PATH) -> pd.DataFrame | None:
    """CSV를 읽고 파일 없음·빈 파일·파싱 오류가 발생하면 None을 반환한다."""

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except (FileNotFoundError, EmptyDataError, ParserError, OSError) as error:
        LOGGER.error("CSV 읽기 실패: %s", error)
        return None


def save_parquet(data: pd.DataFrame, path: str | Path = PARQUET_PATH) -> bool:
    """DataFrame을 압축된 Parquet 파일로 저장한다."""

    try:
        data.to_parquet(path, index=False)
    except (ImportError, OSError, ValueError) as error:
        LOGGER.error("Parquet 저장 실패: %s", error)
        return False
    return True


def load_parquet_summary(
    path: str | Path = PARQUET_PATH,
) -> pd.DataFrame | None:
    """Parquet에서 과제 조건인 도시와 기온 컬럼만 읽는다."""

    try:
        return pd.read_parquet(path, columns=["도시", "기온"])
    except (FileNotFoundError, ImportError, OSError, ValueError) as error:
        LOGGER.error("Parquet 읽기 실패: %s", error)
        return None


def assert_temperature_is_25(weather: Weather) -> None:
    """pytest에서 서울 기온이 25도가 아닐 때 Fail 메시지를 보여준다."""

    try:
        temperature = float(weather.temperature)
    except (TypeError, ValueError) as error:
        raise AssertionError("Fail: 현재 기온을 숫자로 변환할 수 없습니다.") from error
    assert temperature == 25.0, f"Fail: 현재 기온은 {temperature}도입니다."


async def run_pipeline() -> int:
    """수집, 검증, CSV·Parquet 저장과 재로딩을 순서대로 수행한다."""

    records = await collect_weather()
    data = to_dataframe(records)

    if not save_csv(data):
        return 1
    reloaded_csv = load_csv()
    if reloaded_csv is None:
        return 1
    print("\n[CSV 재로딩 결과]")
    print(reloaded_csv)

    if not save_parquet(data):
        return 1
    reloaded_parquet = load_parquet_summary()
    if reloaded_parquet is None:
        return 1
    print("\n[Parquet 재로딩 결과 - 도시, 기온]")
    print(reloaded_parquet)
    return 0


def main() -> int:
    """로그를 준비하고 비동기 종합 파이프라인을 실행한다."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    try:
        return asyncio.run(run_pipeline())
    except (DataCollectionError, ValidationError) as error:
        LOGGER.error("종합실습 실행 실패: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
