"""Practice 2의 파일 예외 처리, Pydantic 검증 및 재로딩 테스트."""

import io
import json
import logging
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from practice2 import (
    INPUT_CSV,
    SalesRecord,
    safe_load_csv,
    save_results,
    validate_records,
)


def make_logger(output: io.StringIO) -> logging.Logger:
    """테스트에서 로그 내용을 확인할 수 있는 독립 logger를 만든다."""

    logger = logging.getLogger(f"practice2-test-{id(output)}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    logger.addHandler(logging.StreamHandler(output))
    return logger


class SafeLoadTests(unittest.TestCase):
    def test_missing_file_returns_none_and_logs_finally(self) -> None:
        output = io.StringIO()
        result = safe_load_csv("존재하지_않는_파일.csv", make_logger(output))
        self.assertIsNone(result)
        self.assertIn("CSV 로딩 실패", output.getvalue())
        self.assertIn("CSV 로딩 종료", output.getvalue())


class ValidationTests(unittest.TestCase):
    def test_schema_rules(self) -> None:
        valid = SalesRecord.model_validate(
            {"date": "2026-07-15", "region": "서울", "amount": "0", "category": ""}
        )
        self.assertIsNone(valid.category)

        with self.assertRaises(ValidationError):
            SalesRecord.model_validate(
                {"date": "2026-07-15", "region": "", "amount": "100", "category": "전자"}
            )
        with self.assertRaises(ValidationError):
            SalesRecord.model_validate(
                {"date": "2026-07-15", "region": "서울", "amount": "-1", "category": "전자"}
            )

    def test_valid_four_errors_three_and_error_log(self) -> None:
        raw_data = safe_load_csv(INPUT_CSV)
        self.assertIsNotNone(raw_data)

        output = io.StringIO()
        valid, errors = validate_records(raw_data or [], make_logger(output))
        self.assertEqual(len(valid), 4)
        self.assertEqual(len(errors), 3)
        self.assertIn("ValidationError", output.getvalue())

    def test_save_and_reload_four_records_with_korean_json(self) -> None:
        raw_data = safe_load_csv(INPUT_CSV) or []
        valid, errors = validate_records(raw_data)

        with tempfile.TemporaryDirectory() as directory:
            valid_path = Path(directory) / "valid.csv"
            errors_path = Path(directory) / "errors.json"
            self.assertTrue(save_results(valid, errors, valid_path, errors_path))

            reloaded = safe_load_csv(valid_path)
            self.assertIsNotNone(reloaded)
            self.assertEqual(len(reloaded or []), 4)

            json_text = errors_path.read_text(encoding="utf-8")
            self.assertIn("의류", json_text)
            self.assertNotIn("\\uc758\\ub958", json_text)
            self.assertEqual(len(json.loads(json_text)), 3)


if __name__ == "__main__":
    unittest.main()
