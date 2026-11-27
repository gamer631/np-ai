"""Dependency-free bounded statistical analysis primitives for NIL research."""
from __future__ import annotations

import math
from collections.abc import Iterable

MAX_SAMPLES = 100_000
MAX_BINS = 512


class StatisticsError(ValueError):
    """Raised for invalid or bounded-out statistical input."""


def _values(data: Iterable[float]) -> list[float]:
    values = list(data)
    if not values:
        raise StatisticsError("at least one value is required")
    if len(values) > MAX_SAMPLES:
        raise StatisticsError("sample count exceeds limit")
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise StatisticsError("samples must be numeric")
        if not math.isfinite(value):
            raise StatisticsError("samples must be finite")
    return [float(v) for v in values]


def _paired(x: Iterable[float], y: Iterable[float]) -> tuple[list[float], list[float]]:
    left, right = _values(x), _values(y)
    if len(left) != len(right):
        raise StatisticsError("paired data must have equal lengths")
    if len(left) < 2:
        raise StatisticsError("at least two paired samples are required")
    return left, right


def describe(data: Iterable[float]) -> dict[str, float]:
    """Return count, mean, median, population/sample variance and std dev, min/max."""
    values = _values(data)
    ordered = sorted(values)
    n = len(ordered)
    mean = math.fsum(ordered) / n
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    sum_sq = math.fsum((v - mean) ** 2 for v in ordered)
    return {
        "count": float(n),
        "mean": mean,
        "median": median,
        "min": ordered[0],
        "max": ordered[-1],
        "population_variance": sum_sq / n,
        "population_std_dev": math.sqrt(sum_sq / n),
        "sample_variance": sum_sq / (n - 1) if n > 1 else 0.0,
        "sample_std_dev": math.sqrt(sum_sq / (n - 1)) if n > 1 else 0.0,
    }


def correlation(x: Iterable[float], y: Iterable[float]) -> float:
    """Compute Pearson correlation; reject constant-valued series."""
    left, right = _paired(x, y)
    mean_x, mean_y = math.fsum(left) / len(left), math.fsum(right) / len(right)
    dx, dy = [v - mean_x for v in left], [v - mean_y for v in right]
    sum_x, sum_y = math.fsum(v * v for v in dx), math.fsum(v * v for v in dy)
    if sum_x == 0 or sum_y == 0:
        raise StatisticsError("correlation is undefined for constant data")
    return math.fsum(a * b for a, b in zip(dx, dy)) / math.sqrt(sum_x * sum_y)


def linear_regression(x: Iterable[float], y: Iterable[float]) -> dict[str, float]:
    """Fit y = slope*x + intercept and return slope, intercept, r and r_squared."""
    left, right = _paired(x, y)
    mean_x, mean_y = math.fsum(left) / len(left), math.fsum(right) / len(right)
    dx = [v - mean_x for v in left]
    denominator = math.fsum(v * v for v in dx)
    if denominator == 0:
        raise StatisticsError("regression is undefined for constant x")
    slope = math.fsum(a * (b - mean_y) for a, b in zip(dx, right)) / denominator
    intercept = mean_y - slope * mean_x
    r = correlation(left, right)
    return {"slope": slope, "intercept": intercept, "r": r, "r_squared": r * r}


def histogram(data: Iterable[float], bins: int = 10) -> dict[str, list[float]]:
    """Return simple equal-width bins with counts and edges."""
    values = _values(data)
    if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= MAX_BINS:
        raise StatisticsError(f"bins must be an integer from 1 to {MAX_BINS}")
    low, high = min(values), max(values)
    if low == high:
        return {"edges": [low, high], "counts": [float(len(values))]}
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        index = min(int((value - low) / width), bins - 1)
        counts[index] += 1
    edges = [low + i * width for i in range(bins)] + [high]
    return {"edges": edges, "counts": [float(c) for c in counts]}
