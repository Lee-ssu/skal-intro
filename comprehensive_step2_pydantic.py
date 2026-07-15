# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 종합실습 1-2, Weather Pydantic v2 스키마 정의 및 검증
# 작성일 : 2026년 7월 15일
# 변경사항 : 0.1 - Weather 모델과 검증 오류 처리 추가
# -----------------------------------------------------------------------------

"""Step 2: validate city, temperature and local time with Pydantic v2."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from comprehensive_step1_async_api import DataCollectionError, collect_city_data


class Weather(BaseModel):
    """도시, 기온(float 또는 str), 현지시각을 검증한다."""

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


def validate_weather(raw_data: list[dict[str, Any]]) -> list[Weather]:
    """API 수집 결과를 Weather 객체 목록으로 변환한다."""

    return [Weather.model_validate(row) for row in raw_data]


async def main() -> None:
    """실제 API 데이터를 수집해 Weather 검증 결과를 출력한다."""

    try:
        records = validate_weather(await collect_city_data())
    except (DataCollectionError, ValidationError) as error:
        print(f"Weather 검증 실패: {error}")
        return

    for record in records:
        print(record.model_dump(by_alias=True))


if __name__ == "__main__":
    asyncio.run(main())
