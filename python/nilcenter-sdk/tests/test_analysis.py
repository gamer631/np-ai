"""Tests for integrated dataset analysis."""
import pytest

from nilcenter.analysis import analyze
from nilcenter.datasets import DataTable, DatasetError


def test_analysis_integration():
    table = DataTable.from_csv("x,y\n1,3\n2,5\n3,7\n")
    result = analyze(table, regression_pair=("x", "y"))
    assert result["rows"] == 3
    assert result["summaries"]["x"]["mean"] == pytest.approx(2)
    assert result["correlations"]["x"]["y"] == pytest.approx(1)
    assert result["regression"]["slope"] == pytest.approx(2)
    assert result["regression"]["intercept"] == pytest.approx(1)


def test_constant_column_correlation_is_null():
    table = DataTable.from_csv("x,y\n1,2\n1,3\n")
    result = analyze(table)
    assert result["correlations"]["x"]["y"] is None


def test_analysis_column_limits_and_duplicates():
    table = DataTable.from_csv("a,b\n1,2\n3,4\n")
    with pytest.raises(DatasetError):
        analyze(table, columns=("a", "a"))
    with pytest.raises(DatasetError):
        analyze(table, columns=())


def test_regression_pair_requires_selected_columns():
    table = DataTable.from_csv("a,b\n1,2\n3,4\n")
    with pytest.raises(DatasetError):
        analyze(table, columns=("a",), regression_pair=("a", "b"))
