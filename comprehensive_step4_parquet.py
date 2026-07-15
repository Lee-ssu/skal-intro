# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 종합실습 1-4, Weather 객체의 Parquet 저장 및 선택 컬럼 재로딩
# 작성일 : 2026년 7월 15일
# 변경사항 : 0.1 - Parquet 저장·읽기와 파일 없음 예외 처리 추가
# -----------------------------------------------------------------------------

"""Step 4: save Weather records to Parquet and load selected columns."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd

from comprehensive_step3_csv import collect_weather_dataframe

PARQUET_PATH = Path(__file__).with_name("weather.parquet")


def save_parquet(data: pd.DataFrame, path: str | Path = PARQUET_PATH) -> bool:
    """Weather DataFrame을 Parquet 파일로 저장한다."""

    try:
        data.to_parquet(path, index=False)
    except (ImportError, OSError, ValueError) as error:
        print(f"Parquet 저장 실패: {error}")
        return False
    return True


def load_parquet_summary(
    path: str | Path = PARQUET_PATH,
) -> pd.DataFrame | None:
    """Parquet에서 도시와 기온 컬럼만 읽어온다."""

    try:
        return pd.read_parquet(path, columns=["도시", "기온"])
    except (FileNotFoundError, ImportError, OSError, ValueError) as error:
        print(f"Parquet 읽기 실패: {error}")
        return None


async def main() -> None:
    """Weather 데이터를 Parquet로 저장하고 도시·기온만 출력한다."""

    data = await collect_weather_dataframe()
    if save_parquet(data):
        reloaded = load_parquet_summary()
        if reloaded is not None:
            print(reloaded)


if __name__ == "__main__":
    asyncio.run(main())
