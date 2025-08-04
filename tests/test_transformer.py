"Tests for the transformer utilities"

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pd = pytest.importorskip("pandas")

from src.transformer import (
    add_next_service_time,
    compute_soc,
)

def test_add_next_service_time_basic():
    df = pd.DataFrame(
        {
            "newIdVeh": ["A", "A", "B"],
            "hDep": [
                pd.Timestamp("2023-06-03 08:00"),
                pd.Timestamp("2023-06-03 12:00"),
                pd.Timestamp("2023-06-03 09:00"),
            ],
        }
    )

    result = add_next_service_time(df)

    next_col = "Heure Prochain Service"
    assert next_col in result.columns
    # Rows should be sorted by vehicle and start time
    assert result.iloc[0][next_col] == pd.Timestamp("2023-06-03 12:00")
    assert pd.isna(result.iloc[1][next_col])
    assert pd.isna(result.iloc[2][next_col])

def test_compute_soc_basic():
    df = pd.DataFrame(
        {
            "newIdVeh": ["A", "A", "B"],
            "tVeh": ["P", "P", "T"],
            "dist": [10, 20, 5],
            "hDep": [1, 2, 1],
        }
    )

    conso = {(0, "P"): 1.0, (0, "T"): 2.0}
    capacities = {(0, "P"): 1000.0, (0, "T"): 1000.0}

    result = compute_soc(df, conso, 100, projection=0)
    result = compute_soc(df, conso, 100, projection=0, capacity_table=capacities)
    assert result.loc[0, "soc_retour"] == 99
    assert result.loc[1, "soc_retour"] == 98
    assert result.loc[2, "soc_retour"] == 99