# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 종합실습 1-3, Weather 객체의 CSV 저장 및 재로딩
# 작성일 : 2026년 7월 15일
# 변경사항 : 0.1 - CSV 저장·읽기와 파일 없음 예외 처리 추가
# -----------------------------------------------------------------------------

"""Step 3: save Weather records to CSV and load them again."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from comprehensive_step1_async_api import collect_city_data
from comprehensive_step2_pydantic import Weather, validate_weather

CSV_PATH = Path(__file__).with_name("weather.csv")


def to_dataframe(records: list[Weather]) -> pd.DataFrame:
    """Weather 객체를 한글 컬럼 DataFrame으로 변환한다."""

    rows = [record.model_dump(by_alias=True) for record in records]
    data = pd.DataFrame(rows, columns=["도시", "기온", "현지시각"])
    numeric_temperature = pd.to_numeric(data["기온"], errors="coerce")
    if numeric_temperature.notna().all():
        data["기온"] = numeric_temperature
    else:
        data["기온"] = data["기온"].astype(str)
    return data


async def collect_weather_dataframe() -> pd.DataFrame:
    """API 수집과 Pydantic 검증을 거쳐 DataFrame을 반환한다."""

    return to_dataframe(validate_weather(await collect_city_data()))


def save_csv(data: pd.DataFrame, path: str | Path = CSV_PATH) -> bool:
    """Weather DataFrame을 CSV 파일로 저장한다."""

    try:
        data.to_csv(path, index=False, encoding="utf-8-sig")
    except (OSError, ValueError) as error:
        print(f"CSV 저장 실패: {error}")
        return False
    return True


def load_csv(path: str | Path = CSV_PATH) -> pd.DataFrame | None:
    """CSV가 없거나 손상됐으면 예외 메시지와 함께 None을 반환한다."""

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except (FileNotFoundError, EmptyDataError, ParserError, OSError) as error:
        print(f"CSV 읽기 실패: {error}")
        return None


async def main() -> None:
    """Weather 객체를 CSV로 저장하고 다시 읽어 출력한다."""

    data = await collect_weather_dataframe()
    if save_csv(data):
        reloaded = load_csv()
        if reloaded is not None:
            print(reloaded)


if __name__ == "__main__":
    asyncio.run(main())
