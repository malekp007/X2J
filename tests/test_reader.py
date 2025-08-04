"""Tests for the reader utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pd = pytest.importorskip("pandas")

from src.reader import read_excel, read_file


def _create_excel(tmp_path: Path):
    df1 = pd.DataFrame({"A": [1, 2], "B": ["a", "b"]})
    df2 = pd.DataFrame({"A": [3, 4], "B": ["c", "d"]})
    file_path = tmp_path / "test.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        df1.to_excel(writer, index=False, sheet_name="Sheet1")
        df2.to_excel(writer, index=False, sheet_name="Sheet2")
    return file_path, df1, df2


def _create_csv(tmp_path: Path):
    df = pd.DataFrame({"A": [1, 2], "B": ["a", "b"]})
    file_path = tmp_path / "test.csv"
    df.to_csv(file_path, index=False)
    return file_path, df


def test_read_excel_single_sheet_df(tmp_path):
    excel_file, df1, _ = _create_excel(tmp_path)
    result = read_excel(excel_file, sheet_name="Sheet1")
    pd.testing.assert_frame_equal(result.reset_index(drop=True), df1)


def test_read_excel_multi_sheet_add_sheet_column(tmp_path):
    excel_file, df1, df2 = _create_excel(tmp_path)
    result = read_excel(
        excel_file,
        sheet_name=["Sheet1", "Sheet2"],
        add_sheet_column=True,
    )
    expected = pd.concat(
        [
            df1.assign(__sheet__="Sheet1"),
            df2.assign(__sheet__="Sheet2"),
        ],
        ignore_index=True,
    )
    pd.testing.assert_frame_equal(result, expected)


def test_read_excel_as_dict(tmp_path):
    excel_file, df1, _ = _create_excel(tmp_path)
    result = read_excel(excel_file, sheet_name="Sheet1", as_dict=True)
    assert result == df1.to_dict(orient="records")


def test_read_file_csv(tmp_path):
    csv_file, df = _create_csv(tmp_path)
    result = read_file(csv_file)
    pd.testing.assert_frame_equal(result, df)


def test_read_file_excel(tmp_path):
    excel_file, _, df2 = _create_excel(tmp_path)
    result = read_file(excel_file, sheet_name="Sheet2")
    pd.testing.assert_frame_equal(result.reset_index(drop=True), df2)


def test_read_file_invalid_extension(tmp_path):
    bad_file = tmp_path / "data.txt"
    bad_file.write_text("dummy")
    with pytest.raises(ValueError):
        read_file(bad_file)