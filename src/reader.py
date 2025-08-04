"""
Flexible data reader utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Dict

import pandas as pd

def read_excel(
    path: str | Path,
    *,
    sheet_name: int | str | Iterable[int | str] = 0,
    as_dict: bool = False,
    add_sheet_column: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | List[Dict[str, Any]]:
    """"
    Read one or several sheets from path and return either a pandas.DataFrame
    or a list of dictionnaries.
    """
    path = Path(path)

    if isinstance(sheet_name, (list, tuple, set)):
        dfs = []
        for sh in sheet_name:
            df = pd.read_excel(path, sheet_name=sh, **kwargs)
            if add_sheet_column:
                df["__sheet__"] = sh
            dfs.append(df)
        df = pd.concat(dfs, ignore_index=True)
    else: 
        df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
        if add_sheet_column:
            df["__sheet__"] = sheet_name
    
    return df.to_dict(orient="records") if as_dict else df

def read_file(
    path: str | Path,
    *,
    as_dict: bool = False,
    sheet_name: int | str | Iterable[int | str] = 0,
    add_sheet_column: bool = False,
    **kwargs: Any,
) -> pd.DataFrame | List[Dict[str, Any]]:
    """
    Universal reader that chooses the appropriate backend based on the file
    extension ( .xlsx , .xls , .csv )

    Unsupported extensions raise :class:VelueError.
    """
    path = Path(path)
    ext = path.suffix.lower()

    if ext in {".xlsx", ".xls", ".xlsm"}:
        return read_excel(
            path,
            sheet_name=sheet_name,
            as_dict=as_dict,
            add_sheet_column=add_sheet_column,
            **kwargs,
        )
    if ext == ".csv":
        df = pd.read_csv(path, **kwargs)
        return df.to_dict(orient="records") if as_dict else df
    
    raise ValueError(f"Unsupported file extension: {ext}")