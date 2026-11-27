"""Bounded CSV dataset ingestion for NIL scientific workflows."""
from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass

MAX_CSV_BYTES = 2_000_000
MAX_ROWS = 100_000
MAX_COLUMNS = 256


class DatasetError(ValueError):
    """Raised for malformed or over-limit dataset input."""


@dataclass(frozen=True, slots=True)
class DataTable:
    """Validated CSV table with immutable row storage."""

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    @classmethod
    def from_csv(cls, text: str) -> DataTable:
        """Parse a bounded CSV string, requiring a header and rectangular rows."""
        if not isinstance(text, str):
            raise TypeError("CSV input must be text")
        if not text or len(text) > MAX_CSV_BYTES or len(text.encode("utf-8")) > MAX_CSV_BYTES:
            raise DatasetError("CSV is empty or exceeds size limit")
        try:
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            header = next(reader, None)
            if header is None:
                raise DatasetError("CSV must include a header")
            columns = tuple(name.strip() for name in header)
            if not columns or len(columns) > MAX_COLUMNS:
                raise DatasetError("column count is empty or exceeds limit")
            if any(not name for name in columns) or len(set(columns)) != len(columns):
                raise DatasetError("column names must be non-empty and unique")
            rows: list[tuple[str, ...]] = []
            for row in reader:
                if not row or (len(row) == 1 and not row[0].strip()):
                    continue
                if len(rows) >= MAX_ROWS:
                    raise DatasetError("row count exceeds limit")
                if len(row) != len(columns):
                    raise DatasetError("row has a different number of fields than header")
                cleaned = tuple(value.strip() for value in row)
                if any(value == "" for value in cleaned):
                    raise DatasetError("empty cells are not supported")
                rows.append(cleaned)
        except csv.Error as exc:
            raise DatasetError("malformed CSV input") from exc
        if not rows:
            raise DatasetError("CSV must contain at least one data row")
        return cls(columns, tuple(rows))

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.columns)

    def column(self, name: str) -> tuple[str, ...]:
        """Return values for an exact column name."""
        try:
            index = self.columns.index(name)
        except ValueError as exc:
            raise DatasetError(f"unknown column: {name}") from exc
        return tuple(row[index] for row in self.rows)

    def numeric_column(self, name: str) -> tuple[float, ...]:
        """Convert a column to finite floats, failing on non-numeric cells."""
        values = self.column(name)
        result: list[float] = []
        for value in values:
            try:
                number = float(value)
            except ValueError as exc:
                raise DatasetError(f"column {name!r} contains non-numeric data") from exc
            if not math.isfinite(number):
                raise DatasetError(f"column {name!r} contains non-finite data")
            result.append(number)
        return tuple(result)
