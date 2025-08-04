from __future__ import annotations

"""
Utility helpers to clean and organise intervention data.
"""

from typing import Mapping, Tuple

from .utils import _load_donnees_camions

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


def add_next_service_time(
        df: pd.DataFrame,
        vehicule_col: str = "newIdVeh",
        start_col: str = "hDep",
        new_col: str = "Heure Prochain Service",
        sort_inplace: bool = False,
) -> pd.DataFrame:
    """
    Adds the *new_col* column containing, for each vehicle record,
    the start time of the immediately following intervention for that same vehicle.
    """
    target = df if sort_inplace else df.copy()
    target.sort_values([vehicule_col, start_col], inplace=True)
    #Shift by one line for each group
    target[new_col] = (
        target
        .groupby(vehicule_col, sort=False)[start_col]
        .shift(-1)
    )
    return target

def compute_soc(
        df: pd.DataFrame,
        conso_table: Mapping[Tuple[int, str], float],
        soc_cible: float,
        *,
        projection: int = 0,
        capacity_table: Mapping[Tuple[int, str], float] | None = None,
        vehicule_col: str = "newIdVeh",
        model_col: str = "tVeh",
        distance_col: str = "dist",
        start_col: str = "hDep",
        soc_col: str = "soc_retour",
) -> pd.DataFrame:
    """Compute the SOC after each service.

    The dataframe is sorted by vehicle and start time. For every row the SOC is
    computed starting from ``soc_cible`` and subtracting the energy consumed
    during the service. The consumption value from ``conso_table`` (in kWh/km)
    is multiplied by the distance travelled to obtain the energy usage in kWh.
    This value is then divided by the battery capacity from ``capacity_table``
    (in kWh) and multiplied by 100 to convert it to a percentage difference.
    The result for one service does not affect the following ones.s
    """
    target = df.sort_values([vehicule_col, start_col]).copy()
    target[soc_col] = None

    if capacity_table is None:
        capacity_table = _load_donnees_camions()

 
    for idx, row in target.iterrows():
        modele = str(row[model_col]).strip()
        conso = conso_table.get((projection, modele), 0.0)
        capacite = capacity_table.get((projection, modele), 0.0)
        try:
            dist = float(row[distance_col])
        except Exception:
            dist = 0.0
        if capacite:
            delta_soc = (conso * dist) / capacite * 100
        else:
            delta_soc = 0.0
        target.at[idx, soc_col] = max(soc_cible - delta_soc, 0)

    return target
