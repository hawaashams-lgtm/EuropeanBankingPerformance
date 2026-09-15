#!/usr/bin/env python3
"""Validate the analysis-ready ECB banking dataset using the Python standard library."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "ECBData.csv"
SOURCE_PATH = Path(__file__).resolve().parents[1] / "data" / "ECBSource.csv"
EXPECTED_QUARTERS = 24
EXPECTED_GEOGRAPHIES = {"Germany", "Italy", "SSM"}
EXPECTED_INDICATORS = 9
EXPECTED_ROWS = EXPECTED_QUARTERS * len(EXPECTED_GEOGRAPHIES) * EXPECTED_INDICATORS
EXPECTED_SOURCE_QUARTERS = 44
EXPECTED_SERIES = len(EXPECTED_GEOGRAPHIES) * EXPECTED_INDICATORS


def expected_period(value: date) -> str:
    quarter = (value.month - 1) // 3 + 1
    return f"{value.year}Q{quarter}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate_source(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    assert len(rows) == EXPECTED_SOURCE_QUARTERS, (
        f"Expected {EXPECTED_SOURCE_QUARTERS} source quarters; found {len(rows)}"
    )

    dates = [row["DATE"] for row in rows]
    assert len(dates) == len(set(dates)), "Duplicate dates in ECBSource.csv"

    parsed_dates: list[date] = []
    for row in rows:
        parsed_date = date.fromisoformat(row["DATE"])
        parsed_dates.append(parsed_date)
        assert expected_period(parsed_date) == row["TIME PERIOD"], (
            f"Source date-period mismatch: {row['DATE']} and {row['TIME PERIOD']}"
        )
        assert (parsed_date.month, parsed_date.day) in {
            (3, 31), (6, 30), (9, 30), (12, 31)
        }, f"Source date is not a quarter end: {parsed_date}"

    assert parsed_dates == sorted(parsed_dates), "Source dates are not in chronological order"

    series_columns: dict[str, str] = {}
    for column in rows[0]:
        match = re.search(r"\((SUP\.[^)]+)\)$", column)
        if match:
            series_code = match.group(1)
            assert series_code not in series_columns, f"Duplicate source series code: {series_code}"
            series_columns[series_code] = column

    assert len(series_columns) == EXPECTED_SERIES, (
        f"Expected {EXPECTED_SERIES} source series; found {len(series_columns)}"
    )

    return {row["DATE"]: row for row in rows}, series_columns


def main() -> None:
    rows = read_csv(DATA_PATH)
    source_rows = read_csv(SOURCE_PATH)
    source_by_date, source_columns = validate_source(source_rows)

    assert len(rows) == EXPECTED_ROWS, f"Expected {EXPECTED_ROWS} rows; found {len(rows)}"

    periods = {row["Time Period"] for row in rows}
    geographies = {row["Geography"] for row in rows}
    indicators = {row["Indicator"] for row in rows}

    assert len(periods) == EXPECTED_QUARTERS, f"Expected 24 quarters; found {len(periods)}"
    assert geographies == EXPECTED_GEOGRAPHIES, f"Unexpected geographies: {geographies}"
    assert len(indicators) == EXPECTED_INDICATORS, f"Expected 9 indicators; found {len(indicators)}"

    keys = [(row["Time Period"], row["Geography"], row["Indicator"]) for row in rows]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    assert not duplicates, f"Duplicate analytical keys: {duplicates[:5]}"

    coverage: dict[tuple[str, str], set[str]] = defaultdict(set)
    reconciled = 0
    for row in rows:
        required = ["Date", "Time Period", "Geography", "Indicator", "Value", "Unit", "Series Code"]
        assert all(row[field].strip() for field in required), f"Missing required value: {row}"

        parsed_date = date.fromisoformat(row["Date"])
        assert expected_period(parsed_date) == row["Time Period"], f"Date-period mismatch: {row}"
        assert (parsed_date.month, parsed_date.day) in {
            (3, 31), (6, 30), (9, 30), (12, 31)
        }, f"Date is not a quarter end: {parsed_date}"

        numeric_value = float(row["Value"])
        assert math.isfinite(numeric_value), f"Non-finite value: {row}"

        expected_unit = "EUR billions" if row["Indicator"] == "Total assets" else "Percent"
        assert row["Unit"] == expected_unit, f"Unit mismatch: {row}"
        if expected_unit == "EUR billions":
            assert numeric_value > 0, f"Non-positive total assets: {row}"
        else:
            assert 0 <= numeric_value <= 200, f"Implausible ratio value: {row}"

        source_row = source_by_date.get(row["Date"])
        assert source_row is not None, f"Date missing from ECBSource.csv: {row['Date']}"
        source_column = source_columns.get(row["Series Code"])
        assert source_column is not None, f"Series missing from ECBSource.csv: {row['Series Code']}"
        source_value = source_row[source_column].strip()
        assert source_value, f"Blank source value for analysis row: {row}"
        assert math.isclose(float(source_value), numeric_value, rel_tol=0, abs_tol=1e-9), (
            f"Source mismatch for {row['Date']} and {row['Series Code']}: "
            f"{source_value} != {row['Value']}"
        )
        reconciled += 1

        coverage[(row["Geography"], row["Indicator"])].add(row["Time Period"])

    assert len(coverage) == 27, f"Expected 27 series; found {len(coverage)}"
    incomplete = {key: len(value) for key, value in coverage.items() if len(value) != EXPECTED_QUARTERS}
    assert not incomplete, f"Incomplete series: {incomplete}"

    print("Data validation passed")
    print(f"Rows: {len(rows)}")
    print(f"Quarters: {len(periods)}")
    print(f"Geographies: {len(geographies)}")
    print(f"Indicators: {len(indicators)}")
    print("Missing values: 0")
    print("Duplicate analytical keys: 0")
    print("Coverage: 24/24 quarters for all 27 series")
    print(f"Source reconciliation: {reconciled}/{len(rows)} values matched")


if __name__ == "__main__":
    main()
