"""practice1.py의 핵심 계산과 예외 처리를 검증하는 표준 라이브러리 테스트."""

import json
import tempfile
import unittest
from pathlib import Path

from practice1 import (
    SalesDataError,
    amounts_by_category,
    compare_memory,
    high_value_sales,
    load_sales,
    monthly_category_totals,
    region_sales_totals,
    region_transaction_counts,
    sales_over,
    top_sales,
)


SALES = [
    {"region": "서울", "amount": 1000, "month": "2026-01", "category": "A"},
    {"region": "부산", "amount": 1500, "month": "2026-01", "category": "B"},
    {"region": "서울", "amount": 2500, "month": "2026-02", "category": "A"},
    {"region": "부산", "amount": 500, "month": "2026-02", "category": "A"},
]


class AggregationTests(unittest.TestCase):
    def test_comprehension_and_region_total(self) -> None:
        self.assertEqual([sale["amount"] for sale in high_value_sales(SALES)], [1000, 1500, 2500])
        self.assertEqual(region_sales_totals(SALES), {"부산": 1500, "서울": 3500})

    def test_counter_and_defaultdict_results(self) -> None:
        counts = region_transaction_counts(SALES)
        self.assertEqual(counts.most_common(), [("서울", 2), ("부산", 2)])
        self.assertEqual(amounts_by_category(SALES), {"A": [1000, 2500, 500], "B": [1500]})

    def test_generator_is_smaller_and_uses_strict_comparison(self) -> None:
        generator = sales_over(SALES)
        self.assertEqual([sale["amount"] for sale in generator], [1500, 2500])

        # 제너레이터는 고정 크기이므로 충분한 거래가 있을 때 리스트보다 작다.
        memory = compare_memory(SALES * 100)
        self.assertLess(memory["generator_bytes"], memory["list_bytes"])

    def test_month_category_total_and_top3(self) -> None:
        self.assertEqual(
            monthly_category_totals(SALES),
            {
                "2026-01": {"A": 1000.0, "B": 1500.0},
                "2026-02": {"A": 3000.0},
            },
        )
        self.assertEqual([sale["amount"] for sale in top_sales(SALES)], [2500, 1500, 1000])


class LoadingTests(unittest.TestCase):
    def test_loads_sales_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps({"Sales": SALES}, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(load_sales(path), SALES)

    def test_rejects_missing_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            path.write_text(json.dumps({"Sales": [{"region": "서울"}]}), encoding="utf-8")
            with self.assertRaises(SalesDataError):
                load_sales(path)


if __name__ == "__main__":
    unittest.main()
