"""Tests for CSV dataset ingestion."""
import pytest

from nilcenter.datasets import DataTable, DatasetError


def test_load_csv_and_numeric_column():
    table = DataTable.from_csv("""year,value
2020,2.5
2021,3.5
""")
    assert table.columns == ("year", "value")
    assert table.row_count == 2
    assert table.numeric_column("value") == (2.5, 3.5)


def test_single_column_csv_is_valid():
    assert DataTable.from_csv("""a
b
""").rows == (("b",),)


def test_trims_cells_and_skips_blank_rows():
    table = DataTable.from_csv(""" a , b
 x , 1

 y , 2
""")
    assert table.rows == (("x", "1"), ("y", "2"))


@pytest.mark.parametrize("csv_text", [
    "", "a,b\n1\n", "a,a\n1,2\n", ",b\n1,2\n", "a,b\n,2\n",
])
def test_invalid_csv(csv_text):
    with pytest.raises(DatasetError):
        DataTable.from_csv(csv_text)


def test_numeric_column_rejects_non_numeric():
    table = DataTable.from_csv("""name,number
abc,1
""")
    with pytest.raises(DatasetError):
        table.numeric_column("name")


def test_numeric_column_rejects_non_finite():
    table = DataTable.from_csv("""name,value
abc,NaN
""")
    with pytest.raises(DatasetError):
        table.numeric_column("value")


def test_unknown_column():
    table = DataTable.from_csv("""a
1
""")
    with pytest.raises(DatasetError):
        table.column("missing")


def test_non_string_input():
    with pytest.raises(TypeError):
        DataTable.from_csv(42)
