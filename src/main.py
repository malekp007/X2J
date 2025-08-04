"""High level orchestrator for Excel to JSON conversion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any

import pandas as pd

from . import utils
from .transformer import add_next_service_time, compute_soc
from .mapper import (
    map_record,
    map_records,
    _load_template,
    DEFAULT_BATTERY_PROFILE,
    DATA_DIR as MAPPER_DATA_DIR,
)
from .validator import validate_json

# Supported values for the ``choix_optim`` field
CHOIX_OPTIM_VALUES = [
    "CoutEnergie",
    "LissagePuissance",
    "Supervision",
    "LLLP",
]

def _parse_date(value: str | float | int | None) -> datetime | None:
    """Return a :class:`datetime` from an ISO string or Excel serial number."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return utils.excel_number_to_datetime(float(value))
    try:
        return utils.parse_iso_datetime(str(value))
    except Exception:
        try:
            return utils.excel_number_to_datetime(float(value))
        except Exception:
            return None


def _filter_by_jour_dep(
    records: Iterable[Dict[str, Any]],
    start: datetime | None,
    end: datetime | None,
    *,
    jour_col: str = "jourDep",
) -> List[Dict[str, Any]]:
    """Return records with ``jour_col`` within ``start`` and ``end``."""

    if start is None and end is None:
        return list(records)

    filtered: List[Dict[str, Any]] = []
    for rec in records:
        try:
            jour_dt = utils.excel_number_to_datetime(float(rec.get(jour_col, 0)))
        except Exception:
            continue
        if start and jour_dt < start:
            continue
        if end and jour_dt > end:
            continue
        filtered.append(rec)
    return filtered


def main(
    resultat_path: str | Path = utils.DEFAULT_RESULTAT_SIMU,
    *,
    mode: str | None = "E",
    start: str | float | int | None = None,
    end: str | float | int | None = None,
    output: str | Path | None = "result.json",
    projection: int = 0,
    soc_cible: int = 0,
    battery_profile_path: str | Path = DEFAULT_BATTERY_PROFILE,
    donnees_camions_path: str | Path = MAPPER_DATA_DIR / "donnees_camions.xlsx",
    marge_securite: int = 15,
    marge_prechauffage: int = 30,
    activation_rendement: str | None = None,
    diminution_soc: float | None = None,
    pas_de_temps: int | None = None,
    maximum_exec_temps: int = 10,
    resultat_simu_path: str | Path | None = None,
    infrastructure_path: str | Path | None = None,
    temps_chargement: int | None = None,
    temps_dechargement: int | None = None,
    axe_optim_degrade: List[int] | None = None,
    choix_optim: str | None = None,
    default_debut_service: str | datetime | None = "2024-12-16T23:59:59Z",
) -> Dict[str, Any]:
    """Read Excel files, transform data, map to JSON and validate.

    Parameters
    ----------
    resultat_path:
        Path to ``resultat_simu_1.xlsx``.
    mode:
        Vehicle mode to filter (``"E"`` or ``"T"``). ``None`` keeps all rows.
    start, end:
        ``jourDep`` bounds.  Values can be Excel serial numbers or ISO date
        strings.  When ``None`` the bound is ignored.
    output:
        Optional path where the JSON result will be written. If ``None`` the
        file is not created.
    projection:
        Projection number used for consumption lookup.
    soc_cible:
        Initial SOC used when computing returned SOC values.
    battery_profile_path, donnees_camions_path, marge_securite, marge_prechauffage,
    activation_rendement, diminution_soc, pas_de_temps, maximum_exec_temps,
    resultat_simu_path, temps_chargement, temps_dechargement, choix_optim
        Parameters forwarded to :func:`src.mapper.map_record`.

    Returns
    -------
    dict
        JSON structure produced from the selected rows.
    """

    resultat_path = Path(resultat_path)
    battery_profile_path = Path(battery_profile_path)
    donnees_camions_path = Path(donnees_camions_path)
    map_resultat_path = Path(resultat_simu_path) if resultat_simu_path else resultat_path

    # ------------------------------------------------------------------
    # 1. Read the Excel records
    records = utils.load_resultat_simu(resultat_path, mode=mode)

    # ------------------------------------------------------------------
    # 2. Filter on ``jourDep`` 
    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    records = _filter_by_jour_dep(records, start_dt, end_dt)

    if not records:
        return []

    # ------------------------------------------------------------------
    # 3. Transformations
    df = pd.DataFrame(records)
    df = add_next_service_time(df)
    conso_tbl = utils._load_donnees_camions_conso()
    capacite_tbl = utils._load_donnees_camions()
    df = compute_soc(
        df,
        conso_tbl,
        soc_cible,
        projection=projection,
        capacity_table=capacite_tbl,
    )


    # ------------------------------------------------------------------
    # 4. Mapping and validation
    template = _load_template()
    json_results: List[Dict[str, Any]] = []
    json_output = map_records(
        df.to_dict(orient="records"),
        template=template,
        battery_profile_path=battery_profile_path,
        donnees_camions_path=donnees_camions_path,
        resultat_simu_path=map_resultat_path,
        projection=projection,
        marge_securite=marge_securite,
        marge_prechauffage=marge_prechauffage,
        soc_cible=soc_cible,
        activation_rendement=activation_rendement,
        diminution_soc=diminution_soc,
        pas_de_temps=pas_de_temps,
        maximum_exec_temps=maximum_exec_temps,
        start_dt=start_dt,
        end_dt=end_dt,
        temps_chargement=temps_chargement,
        temps_dechargement=temps_dechargement,
        infrastructure_path=infrastructure_path,
        axe_optim_degrade=axe_optim_degrade,
        choix_optim=choix_optim,
        default_debut_service=default_debut_service,
        )

    # ------------------------------------------------------------------
    # 5. Output
    if output is not None:
        output_path = Path(output)
        if output_path.is_dir():
            output_path = output_path / "result.json"
        output_path.write_text(
            json.dumps(json_output, ensure_ascii=False, indent=2)
        )

    return json_output


if __name__ == "__main__":  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Convert Excel interventions to JSON")
    parser.add_argument(
        "--start",
        help="first jourDep to include (ISO date or Excel serial)",
    )
    parser.add_argument(
        "--end",
        help="last jourDep to include (ISO date or Excel serial)",
    )
    parser.add_argument(
        "--mode",
        default="E",
        help="vehicle mode to keep",
    )
    parser.add_argument(
        "--output",
        default="result.json",
        help="where to write the resulting JSON",
    )
    parser.add_argument(
        "--resultat",
        default=str(utils.DEFAULT_RESULTAT_SIMU),
        help="path to resultat_simu_1.xlsx",
    )
    parser.add_argument("--projection", type=int, default=0, help="projection number")
    parser.add_argument("--soc-cible", type=float, default=0.0, help="initial SOC")

    parser.add_argument(
        "--infrastructure",
        help="path to infrastructure JSON/YAML",
    )
    parser.add_argument("--temps-chargement", type=int)
    parser.add_argument("--temps-dechargement", type=int)
    parser.add_argument("--maximum-exec-temps", type=int, default=10, help="maximum execution time")
    parser.add_argument("--marge-securite", default="00:15", help="marge de sécurité")
    parser.add_argument("--marge-prechauffage", default="00:30", help="marge de préchauffage")
    parser.add_argument("--diminution-soc", type=float, help="diminution de SOC")
    parser.add_argument(
        "--axe-optim-degrade",
        default="1,2,3",
        help="comma separated values for configuration.axeOptimDegrade",
    )
    parser.add_argument(
        "--choix-optim",
        default=CHOIX_OPTIM_VALUES[0],
        choices=CHOIX_OPTIM_VALUES,
        help="value for the choix_optim field",
    )
    parser.add_argument(
        "--default-debut-service",
        help="value used when Heure Prochain Service is missing",
    )
    args = parser.parse_args()
    main(
        args.resultat,
        mode=args.mode if args.mode != "None" else None,
        start=args.start,
        end=args.end,
        output=args.output,
        projection=args.projection,
        soc_cible=args.soc_cible,
        temps_chargement=args.temps_chargement,
        temps_dechargement=args.temps_dechargement,
        maximum_exec_temps=args.maximum_exec_temps,
        marge_securite=args.marge_securite,
        marge_prechauffage=args.marge_prechauffage,
        diminution_soc=args.diminution_soc,
        axe_optim_degrade=[int(x) for x in args.axe_optim_degrade.split(',') if x],
        choix_optim=args.choix_optim,
        infrastructure_path=args.infrastructure,

    
    )