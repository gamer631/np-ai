"""Tests for the bounded math expression engine."""
import pytest

from nilcenter.math_engine import CalculationError, calculate


@pytest.mark.parametrize(("expression", "expected"), [
    ("2 + 3 * 4", 14.0),
    ("(10 - 2) / 4", 2.0),
    ("sqrt(81)", 9.0),
    ("sin(pi / 2)", 1.0),
    ("log(e)", 1.0),
    ("2 ** 5", 32.0),
    ("abs(-7)", 7.0),
])
def test_calculate(expression, expected):
    assert calculate(expression) == pytest.approx(expected)


@pytest.mark.parametrize("expression", [
    "", "import os", "__import__('os')", "1 / 0", "sqrt(-1)", "2 ** 101",
    "unknown(1)", "1 + float('inf')", "1 + 2; 3",
])
def test_rejects_unsafe_or_invalid_expressions(expression):
    with pytest.raises(CalculationError):
        calculate(expression)


def test_expression_length_and_depth_limits():
    with pytest.raises(CalculationError):
        calculate("1" * 300)
    with pytest.raises(CalculationError):
        calculate("(" * 20 + "1" + ")" * 20)


def test_non_string_rejected():
    with pytest.raises(TypeError):
        calculate(5)
