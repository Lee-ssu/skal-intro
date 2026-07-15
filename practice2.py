# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : JSON 기반 파일 I/O, 예외 처리 및 Pydantic 검증 파이프라인 연습
# 작성일 : 2026년 7월 15일
#
# 제공 JSON에서 7건짜리 연습 CSV를 만들고 Pydantic 모델로 검증한 뒤,
# 정상 데이터와 오류 데이터를 각각 CSV와 JSON 파일로 저장합니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - safe_load_csv()와 파일 예외 처리 작성
# 0.2 : 2026년 7월 15일 - Pydantic v2 SalesRecord 스키마 작성
# 0.3 : 2026년 7월 15일 - valid/errors 검증 파이프라인 작성
# 0.4 : 2026년 7월 15일 - 결과 CSV·JSON 저장 및 재로딩 검증 작성
# 0.5 : 2026년 7월 15일 - 체크포인트 assert와 오류 로그 추가
# 0.6 : 2026년 7월 15일 - 제공 JSON과 month 필드를 기준으로 입력 생성
# -----------------------------------------------------------------------------

"""Practice 2: 파일 I/O, 예외 처리와 Pydantic v2 검증 파이프라인."""

from __future__ import annotations

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
except ImportError:
    print(
        "오류: Pydantic v2가 필요합니다. "
        "먼저 'python3 -m pip install pydantic'를 실행하세요.",
        file=sys.stderr,
    )
    raise SystemExit(1)


BASE_DIR = Path(__file__).resolve().parent
SOURCE_JSON = BASE_DIR / "Python_Practice2_Data.json"
INPUT_CSV = BASE_DIR / "practice2_input.csv"
VALID_CSV = BASE_DIR / "practice2_valid.csv"
ERRORS_JSON = BASE_DIR / "practice2_errors.json"
LOGGER = logging.getLogger("practice2")


class SalesRecord(BaseModel):
    """판매 행의 필수 값과 허용 범위를 검증하는 Pydantic v2 모델."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    region: str
    amount: float = Field(gt=0)
    category: str | None = None

    @field_validator("month", mode="before")
    @classmethod
    def month_must_not_be_empty(cls, value: Any) -> Any:
        """month가 비어 있으면 형식 검사 전에 명확한 오류를 발생시킨다."""

        if value is None or not str(value).strip():
            raise ValueError("month는 비어 있을 수 없습니다.")
        return value

    @field_validator("region")
    @classmethod
    def region_must_not_be_empty(cls, value: str) -> str:
        """공백만 있는 region을 허용하지 않는다."""

        if not value:
            raise ValueError("region은 비어 있을 수 없습니다.")
        return value

    @field_validator("category", mode="before")
    @classmethod
    def empty_category_to_none(cls, value: Any) -> Any:
        """선택 항목인 category가 빈 문자열이면 None으로 변환한다."""

        return None if value is None or not str(value).strip() else value


def prepare_practice_csv(
    source_path: str | Path = SOURCE_JSON,
    output_path: str | Path = INPUT_CSV,
    logger: logging.Logger = LOGGER,
) -> bool:
    """제공 JSON을 바탕으로 정상 4건과 오류 3건의 연습 CSV를 만든다.

    앞 4건은 그대로 사용하고, 다음 3건에는 각 검증 규칙을 확인하도록
    빈 month, 빈 region, 0원 amount를 한 가지씩 적용한다.
    """

    try:
        with Path(source_path).open("r", encoding="utf-8") as file:
            source_data = json.load(file)

        if not isinstance(source_data, list) or len(source_data) < 7:
            raise ValueError("제공 JSON에는 최소 7개의 판매 레코드가 필요합니다.")

        raw_data = [dict(row) for row in source_data[:7]]
        raw_data[4]["month"] = ""
        raw_data[5]["region"] = ""
        raw_data[6]["amount"] = 0

        with Path(output_path).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(
                file, fieldnames=["month", "region", "amount", "category"]
            )
            writer.writeheader()
            writer.writerows(raw_data)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        logger.error("연습 CSV 생성 실패 (%s): %s", type(error).__name__, error)
        return False

    logger.info("제공 JSON 기반 연습 CSV 생성: %s", output_path)
    return True


def safe_load_csv(
    file_path: str | Path, logger: logging.Logger = LOGGER
) -> list[dict[str, str]] | None:
    """CSV를 안전하게 읽고, 실패하면 로그를 남긴 뒤 None을 반환한다.

    성공 여부와 관계없이 ``finally``에서 로딩 종료 로그가 출력된다.
    """

    path = Path(file_path)
    logger.info("CSV 로딩 시작: %s", path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise csv.Error("CSV 헤더가 없습니다.")
            rows = list(reader)
            logger.info("CSV 로딩 성공: %d건", len(rows))
            return rows
    except (OSError, UnicodeError, csv.Error) as error:
        logger.error("CSV 로딩 실패 (%s): %s", type(error).__name__, error)
        return None
    finally:
        logger.info("CSV 로딩 종료: %s", path)


def validate_records(
    raw_data: Iterable[Mapping[str, Any]], logger: logging.Logger = LOGGER
) -> tuple[list[SalesRecord], list[dict[str, Any]]]:
    """각 행을 SalesRecord로 변환하고 성공/실패 결과를 분리한다."""

    valid: list[SalesRecord] = []
    errors: list[dict[str, Any]] = []

    for line_number, row in enumerate(raw_data, start=2):
        try:
            valid.append(SalesRecord.model_validate(row))
        except ValidationError as error:
            details = error.errors(include_url=False, include_context=False)
            logger.error(
                "ValidationError - CSV %d행: %s",
                line_number,
                json.dumps(details, ensure_ascii=False),
            )
            errors.append({"row": dict(row), "error": details})

    return valid, errors


def save_results(
    valid: Iterable[SalesRecord],
    errors: list[dict[str, Any]],
    valid_path: str | Path = VALID_CSV,
    errors_path: str | Path = ERRORS_JSON,
    logger: logging.Logger = LOGGER,
) -> bool:
    """검증 성공 레코드는 CSV로, 오류 레코드는 한글 보존 JSON으로 저장한다."""

    try:
        with Path(valid_path).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(SalesRecord.model_fields))
            writer.writeheader()
            for record in valid:
                # 직접 dict를 만들지 않고 Pydantic v2의 model_dump()를 사용한다.
                writer.writerow(record.model_dump(mode="json"))

        with Path(errors_path).open("w", encoding="utf-8") as file:
            json.dump(errors, file, ensure_ascii=False, indent=2)
    except OSError as error:
        logger.error("결과 파일 저장 실패 (%s): %s", type(error).__name__, error)
        return False

    logger.info("정상 데이터 저장: %s", valid_path)
    logger.info("오류 데이터 저장: %s", errors_path)
    return True


def run_pipeline() -> tuple[list[SalesRecord], list[dict[str, Any]]] | None:
    """읽기 → 검증 → 저장 → 재로딩의 전체 파이프라인을 수행한다."""

    if not prepare_practice_csv():
        return None

    raw_data = safe_load_csv(INPUT_CSV)
    assert raw_data is not None, "입력 CSV 로딩에 실패했습니다."

    valid, errors = validate_records(raw_data)
    assert len(valid) == 4, f"valid는 4건이어야 합니다: {len(valid)}건"
    assert len(errors) == 3, f"errors는 3건이어야 합니다: {len(errors)}건"

    if not save_results(valid, errors):
        return None

    reloaded = safe_load_csv(VALID_CSV)
    assert reloaded is not None, "결과 CSV 재로딩에 실패했습니다."
    assert len(reloaded) == 4, f"재로딩 결과는 4건이어야 합니다: {len(reloaded)}건"

    return valid, errors


def main() -> int:
    """로그를 설정하고 실행 결과 건수를 출력한다."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    try:
        result = run_pipeline()
    except AssertionError as error:
        LOGGER.error("체크포인트 실패: %s", error)
        return 1

    if result is None:
        return 1

    valid, errors = result
    print(f"\n검증 완료: valid {len(valid)}건 / errors {len(errors)}건")
    print(f"재로딩 확인: {VALID_CSV.name} 4건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
