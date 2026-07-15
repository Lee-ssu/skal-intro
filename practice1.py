# -----------------------------------------------------------------------------
# 작성자 : 이상수
# 작성목적 : 컴프리헨션과 제너레이터의 이해를 돕기 위한 연습문제
# 작성일 : 2026년 7월 15일
#
# 컴프리헨션과 제너레이터의 이해를 돕기 위한 연습문제입니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - 최초 작성
# 0.2 : 2026년 7월 15일 - Counter(지역별 거래 건수),
#       defaultdict(카테고리별 amount 리스트) 추가
# 0.3 : 2026년 7월 15일 - amount > 1000 제너레이터와 메모리 비교 추가
# 0.4 : 2026년 7월 15일 - month·category 기준 총매출 집계 추가
# 0.5 : 2026년 7월 15일 - 체크포인트 검증과 amount 기준 top3 정렬 추가
# 0.6 : 2026년 7월 15일 - 파일 읽기, JSON 파싱 및 데이터 예외 처리 추가
# -----------------------------------------------------------------------------

"""Practice 1: sales data aggregation with Python data structures.

변경 내역
----------
* 리스트/딕셔너리 컴프리헨션으로 고액 거래 및 지역별 총매출 계산
* Counter와 defaultdict를 이용한 거래 건수/카테고리별 금액 집계
* 제너레이터와 리스트의 메모리 크기 비교
* 월별·카테고리별 총매출과 금액 기준 top 3 계산

기본 입력 파일은 이 스크립트와 같은 폴더의
``Python_Practice1_Data.json``이다. JSON 최상위가 거래 리스트이거나,
``{"Sales": [...]}`` 형태인 경우를 모두 지원한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import GeneratorType
from typing import Any, Iterable, Iterator, Mapping, Sequence


DEFAULT_DATA_PATH = Path(__file__).with_name("Python_Practice1_Data.json")
REQUIRED_FIELDS = ("region", "amount", "month", "category")


class SalesDataError(ValueError):
    """입력 JSON의 구조나 값이 실습에서 요구하는 형식과 다를 때 발생한다."""


def load_sales(path: str | Path) -> list[dict[str, Any]]:
    """JSON 파일을 읽고 검증된 sales 리스트를 반환한다.

    파일 읽기/JSON 파싱 오류는 호출자가 상황에 맞는 메시지로 처리하도록
    그대로 전달하고, 데이터 구조 오류는 ``SalesDataError``로 통일한다.
    """

    data_path = Path(path)
    with data_path.open(encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict):
        # 자료에 표기된 "Sales"를 우선 사용하되 소문자 키도 허용한다.
        if "Sales" in payload:
            sales = payload["Sales"]
        elif "sales" in payload:
            sales = payload["sales"]
        else:
            raise SalesDataError("최상위 객체에 'Sales' 리스트가 없습니다.")
    else:
        sales = payload

    if not isinstance(sales, list):
        raise SalesDataError("Sales 값은 리스트여야 합니다.")

    validated: list[dict[str, Any]] = []
    for index, sale in enumerate(sales):
        if not isinstance(sale, dict):
            raise SalesDataError(f"Sales[{index}]는 객체여야 합니다.")

        missing = [field for field in REQUIRED_FIELDS if field not in sale]
        if missing:
            raise SalesDataError(
                f"Sales[{index}]에 필수 키가 없습니다: {', '.join(missing)}"
            )

        amount = sale["amount"]
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise SalesDataError(f"Sales[{index}].amount는 숫자여야 합니다.")
        if amount < 0:
            raise SalesDataError(f"Sales[{index}].amount는 음수일 수 없습니다.")

        for field in ("region", "month", "category"):
            if not isinstance(sale[field], str) or not sale[field].strip():
                raise SalesDataError(
                    f"Sales[{index}].{field}는 비어 있지 않은 문자열이어야 합니다."
                )

        validated.append(sale.copy())

    return validated


def high_value_sales(
    sales: Iterable[Mapping[str, Any]], threshold: float = 1000
) -> list[Mapping[str, Any]]:
    """amount가 threshold 이상인 거래를 리스트 컴프리헨션으로 반환한다."""

    return [sale for sale in sales if sale["amount"] >= threshold]


def region_sales_totals(
    sales: Sequence[Mapping[str, Any]], threshold: float = 1000
) -> dict[str, float]:
    """고액 거래만 대상으로 지역별 총매출을 딕셔너리로 계산한다."""

    filtered = high_value_sales(sales, threshold)
    regions = {sale["region"] for sale in filtered}
    return {
        region: sum(sale["amount"] for sale in filtered if sale["region"] == region)
        for region in sorted(regions)
    }


def region_transaction_counts(
    sales: Iterable[Mapping[str, Any]],
) -> Counter[str]:
    """Counter로 전체 거래의 지역별 건수를 센다."""

    return Counter(sale["region"] for sale in sales)


def amounts_by_category(
    sales: Iterable[Mapping[str, Any]],
) -> dict[str, list[float]]:
    """defaultdict를 사용해 카테고리별 amount 리스트를 만든다."""

    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for sale in sales:
        grouped[sale["category"]].append(sale["amount"])
    return dict(grouped)


def sales_over(
    sales: Iterable[Mapping[str, Any]], threshold: float = 1000
) -> Iterator[Mapping[str, Any]]:
    """amount가 threshold보다 큰 행만 지연 평가하는 제너레이터다."""

    for sale in sales:
        if sale["amount"] > threshold:
            yield sale


def compare_memory(
    sales: Sequence[Mapping[str, Any]], threshold: float = 1000
) -> dict[str, int]:
    """동일 조건의 리스트와 제너레이터 컨테이너 크기를 비교한다.

    ``sys.getsizeof``는 거래 객체가 참조하는 하위 객체 전체가 아니라 각
    컨테이너 자체의 얕은 크기를 측정한다는 점에 유의한다.
    """

    list_version = [sale for sale in sales if sale["amount"] > threshold]
    generator_version = sales_over(sales, threshold)
    return {
        "list_bytes": sys.getsizeof(list_version),
        "generator_bytes": sys.getsizeof(generator_version),
    }


def monthly_category_totals(
    sales: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """월과 카테고리를 기준으로 그룹핑한 총매출 중첩 딕셔너리를 만든다."""

    totals: defaultdict[str, defaultdict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for sale in sales:
        totals[sale["month"]][sale["category"]] += sale["amount"]

    # 결과를 일반 dict로 변환하고 컴프리헨션으로 키 순서를 안정화한다.
    return {
        month: {
            category: totals[month][category]
            for category in sorted(totals[month])
        }
        for month in sorted(totals)
    }


def top_sales(
    sales: Iterable[Mapping[str, Any]], limit: int = 3
) -> list[Mapping[str, Any]]:
    """amount를 기준으로 내림차순 정렬한 상위 limit개 거래를 반환한다."""

    if limit < 0:
        raise ValueError("limit은 0 이상이어야 합니다.")
    return sorted(sales, key=lambda sale: sale["amount"], reverse=True)[:limit]


def analyze_sales(sales: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """모든 실습 결과를 계산하고 핵심 체크포인트를 assert로 검증한다."""

    filtered = high_value_sales(sales)
    region_total = region_sales_totals(sales)
    region_count = region_transaction_counts(sales)
    category_amounts = amounts_by_category(sales)
    memory = compare_memory(sales)
    month_category_total = monthly_category_totals(sales)
    top3 = top_sales(sales)

    # 독립적인 기준식으로 결과를 확인해 계산 실수를 즉시 발견한다.
    assert sum(region_total.values()) == sum(sale["amount"] for sale in filtered)
    assert sum(region_count.values()) == len(sales)
    assert all(
        top3[index]["amount"] >= top3[index + 1]["amount"]
        for index in range(len(top3) - 1)
    )
    # 작은 입력에서는 제너레이터의 고정 오버헤드가 리스트보다 클 수 있다.
    # 따라서 크기는 위의 memory 결과로 직접 비교하고, 여기서는 실제로
    # 지연 평가되는 iterator인지 검증한다.
    assert isinstance(sales_over(sales), GeneratorType)

    return {
        "filtered_sales": filtered,
        "region_total": region_total,
        "region_count": region_count,
        "region_count_top": region_count.most_common(),
        "category_amounts": category_amounts,
        "memory": memory,
        "month_category_total": month_category_total,
        "top3": top3,
    }


def print_results(results: Mapping[str, Any]) -> None:
    """분석 결과를 한글 레이블과 함께 읽기 쉬운 JSON 형태로 출력한다."""

    labels = (
        ("filtered_sales", "1. amount >= 1000 거래"),
        ("region_total", "1. 지역별 고액 거래 총매출"),
        ("region_count", "2. 지역별 거래 건수"),
        ("region_count_top", "2. 지역별 거래 건수 순위"),
        ("category_amounts", "2. 카테고리별 amount 리스트"),
        ("memory", "3. 메모리 비교 (bytes)"),
        ("month_category_total", "4. 월별·카테고리별 총매출"),
        ("top3", "Checkpoint. 금액 상위 3건"),
    )
    for key, label in labels:
        print(f"\n[{label}]")
        print(json.dumps(results[key], ensure_ascii=False, indent=2))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """명령행 인자를 파싱한다."""

    parser = argparse.ArgumentParser(description="Practice 1 판매 데이터 집계")
    parser.add_argument(
        "data_file",
        nargs="?",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="분석할 JSON 파일 경로 (기본: Python_Practice1_Data.json)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """데이터를 분석해 출력하며 예상 가능한 오류는 친절하게 안내한다."""

    args = parse_args(argv)
    try:
        sales = load_sales(args.data_file)
        results = analyze_sales(sales)
    except FileNotFoundError:
        print(f"오류: 데이터 파일을 찾을 수 없습니다: {args.data_file}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"오류: 데이터 파일을 읽을 권한이 없습니다: {args.data_file}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(
            f"오류: 올바른 JSON이 아닙니다 "
            f"(줄 {error.lineno}, 열 {error.colno}): {error.msg}",
            file=sys.stderr,
        )
        return 1
    except (SalesDataError, OSError) as error:
        print(f"오류: {error}", file=sys.stderr)
        return 1

    print_results(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
