# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 종합실습 1-1, 공공 API의 JSON 데이터를 비동기로 수집
# 작성일 : 2026년 7월 15일
# 변경사항 : 0.1 - 최초 작성 및 API 예외 처리 추가
# -----------------------------------------------------------------------------

"""Step 1: collect current temperature and local time asynchronously."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime
from typing import Any, TypedDict
from zoneinfo import ZoneInfo

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
COUNTRIES_URL = "https://countries.dev/alpha/{code}"


class City(TypedDict):
    """API 요청에 필요한 도시 정보."""

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


class DataCollectionError(RuntimeError):
    """API 요청 또는 응답 해석에 실패했을 때 발생한다."""


async def fetch_json(
    client: httpx.AsyncClient,
    url: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """HTTP GET 결과를 JSON 객체로 반환하고 오류를 한 종류로 변환한다."""

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise DataCollectionError(f"API 요청 실패: {url} ({error})") from error

    if not isinstance(payload, dict):
        raise DataCollectionError(f"JSON 객체 응답이 아닙니다: {url}")
    return payload


def extract_temperature(payload: Mapping[str, Any]) -> float | str:
    """Open-Meteo JSON에서 현재 기온을 추출한다."""

    current_weather = payload.get("current_weather")
    if isinstance(current_weather, Mapping) and "temperature" in current_weather:
        return current_weather["temperature"]
    raise DataCollectionError("Open-Meteo 응답에 현재 기온이 없습니다.")


async def fetch_city_data(
    city: City, client: httpx.AsyncClient
) -> dict[str, float | str]:
    """한 도시의 날씨와 국가 정보를 동시에 수집한다."""

    country_code = COUNTRY_CODE_BY_TIMEZONE[city["tz"]]
    weather_request = fetch_json(
        client,
        OPEN_METEO_URL,
        {
            "latitude": city["lat"],
            "longitude": city["lon"],
            "current_weather": "true",
        },
    )
    country_request = fetch_json(
        client,
        COUNTRIES_URL.format(code=country_code),
        {"fields": "name,timezones"},
    )
    weather_payload, country_payload = await asyncio.gather(
        weather_request, country_request
    )
    if not country_payload.get("timezones"):
        raise DataCollectionError(f"{city['name']} 국가 시간대 정보가 없습니다.")

    local_time = datetime.now(ZoneInfo(city["tz"]))
    return {
        "도시": city["name"],
        "기온": extract_temperature(weather_payload),
        "현지시각": local_time.strftime("%m/%d/%Y %H:%M"),
    }


async def collect_city_data(cities: list[City] = CITIES) -> list[dict[str, Any]]:
    """네 도시의 데이터를 병렬로 수집한다."""

    async with httpx.AsyncClient(timeout=20.0) as client:
        return list(
            await asyncio.gather(*(fetch_city_data(city, client) for city in cities))
        )


async def main() -> None:
    """수집된 JSON 기반 도시 데이터를 화면에 출력한다."""

    try:
        for row in await collect_city_data():
            print(row)
    except DataCollectionError as error:
        print(f"데이터 수집 실패: {error}")


if __name__ == "__main__":
    asyncio.run(main())
