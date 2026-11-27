"""Tests for NIL descriptive statistics."""
import pytest

from nilcenter.statistics import StatisticsError, correlation, describe, histogram, linear_regression


def test_describe_values():
    result = describe([1, 2, 3, 4])
    assert result["mean"] == 2.5
    assert result["median"] == 2.5
    assert result["population_variance"] == 1.25
    assert result["sample_variance"] == pytest.approx(5 / 3)
    assert result["min"] == 1 and result["max"] == 4


def test_correlation_positive_and_negative():
    assert correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1)
    assert correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)


def test_regression():
    result = linear_regression([1, 2, 3], [3, 5, 7])
    assert result["slope"] == pytest.approx(2)
    assert result["intercept"] == pytest.approx(1)
    assert result["r_squared"] == pytest.approx(1)


def test_histogram():
    result = histogram([0, 1, 2, 3], bins=3)
    assert result["edges"] == pytest.approx([0, 1, 2, 3])
    assert result["counts"] == [1, 1, 2]


def test_constant_histogram():
    assert histogram([4, 4, 4]) == {"edges": [4.0, 4.0], "counts": [3.0]}


@pytest.mark.parametrize("bad", [[], [float("nan")], [float("inf")], [True], ["x"]])
def test_invalid_data(bad):
    with pytest.raises(StatisticsError):
        describe(bad)


def test_constant_correlation_rejected():
    with pytest.raises(StatisticsError):
        correlation([1, 1], [2, 3])


def test_regression_constant_x_rejected():
    with pytest.raises(StatisticsError):
        linear_regression([1, 1], [2, 3])


def test_histogram_bin_limit():
    with pytest.raises(StatisticsError):
        histogram([1, 2], bins=1000)
