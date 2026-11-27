"""Integrated dataset analysis helpers for NIL scientific workflows."""
from __future__ import annotations

from itertools import combinations

from nilcenter.datasets import DataTable, DatasetError
from nilcenter.statistics import StatisticsError, correlation, describe, linear_regression

MAX_ANALYSIS_COLUMNS = 10


def analyze(
    table: DataTable,
    columns: tuple[str, ...] | list[str] | None = None,
    *,
    regression_pair: tuple[str, str] | None = None,
) -> dict[str, object]:
    """Summarize selected numeric CSV columns and pairwise correlations.

    Optional regression_pair is (predictor, response). The result is JSON-friendly.
    """
    if not isinstance(table, DataTable):
        raise TypeTypeError("table must be a DataTable")
    selected = tuple(columns) if columns is not None else table.columns
    if not selected or len(selected) > MAX_ANALYSIS_COLUMNS:
        raise DatasetError(f"select between 1 and {MAX_ANALYSIS_COLUMNS} columns")
    if len(set(selected)) != len(selected):
        raise DatasetError("columns must be unique")
    numeric = {name: table.numeric_column(name) for name in selected}
    summaries = {name: describe(values) for name, values in numeric.items()}
    correlations: dict[str, dict[str, float | None]] = {name: {} for name in selected}
    for left, right in combinations(selected, 2):
        try:
            value = correlation(numeric[left], numeric[right])
        except StatisticsError:
            value = None
        correlations[left][right] = value
        correlations[right][left] = value
    regression: dict[str, float] | None = None
    if regression_pair is not None:
        predictor, response = regression_pair
        if predictor not in numeric or response not in numeric:
            raise DatasetError("regression columns must be included in selected columns")
        regression = linear_regression(numeric[predictor], numeric[response])
    return {
        "rows": table.row_count,
        "columns": selected,
        "summaries": summaries,
        "correlations": correlations,
        "regression": regression,
    }
