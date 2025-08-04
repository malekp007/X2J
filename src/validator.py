"""Validation helpers for user provided values."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .utils import jour_dep_bounds, parse_iso_datetime


def validate_optim_dates(
    debut: str | datetime,
    fin: str | datetime,
    *,
    resultat_path: Path | None = None,
) -> None:
    """Validate that ``debut`` and ``fin`` are outside the ``jourDep`` range.

    ``debut`` must be strictly earlier than the minimum ``jourDep`` value and
    ``fin`` strictly later than the maximum.
    Raises :class:`ValueError` if the constraint is not satisfied.
    """

    min_jour, max_jour = jour_dep_bounds(resultat_path) if resultat_path else jour_dep_bounds()

    def _to_dt(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        return parse_iso_datetime(value)

    debut_dt = _to_dt(debut)
    fin_dt = _to_dt(fin)

    if debut_dt >= min_jour:
        raise ValueError("debutOptim must be earlier than first jourDep")
    if fin_dt <= max_jour:
        raise ValueError("finOptim must be later than last jourDep")

#Generic JSON validation
from typing import Any, Callable, Dict, Iterable, List

#Helper validators
def _is_iso_datetime(value: Any) -> bool:
    if value == "":
    # allow empty string for optional fields
        return True
    if not isinstance(value, str):
        return False
    try:
        parse_iso_datetime(value)
        return True
    except Exception:
        return False


def _is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        from datetime import date

        date.fromisoformat(value)
        return True
    except Exception:
        return False

Validator = Callable[[Any], bool]

# JSON schema description --------------------------------------------------
SCHEMA: Dict[str, Any] = {
    "idRun": str,
    "synthese": [str],
    "configuration": {
        "activationRendement": str,
        "axeOptimDegrade": [(int)],
        "diminutionSOC": (int),
        "pasDeTemps": (int),
        "maximumExecTemps": (int),
        "debutOptim": _is_iso_datetime,
        "finOptim": _is_iso_datetime,
    },
    "rapport": {
        "url": str,
        "resultUrl": str,
    },
    "sources": [
        {
            "id": str,
            "libelle": str,
            "pMax": [(int)],
            "tranches": [
                {
                    "id": str,
                    "cout": (int, float),
                    "dateDebut": _is_iso_date,
                    "dateFin": _is_iso_date,
                    "heureTranche": [
                        {"debut": (int), "fin": (int)}
                    ],
                }
            ],
            "transformateurs": [
                {
                    "id": str,
                    "libelle": str,
                    "etat": str,
                    "rendement": [
                        {"x": (int), "y": (int, float)}
                    ],
                    "facteurPuissance": (int, float),
                    "pMax": (int),
                    "chargeurs": [
                        {
                            "id": str,
                            "libelle": str,
                            "etat": str,
                            "pMax": (int),
                            "typeChargeur": str,
                            "mutualisation": {
                                "nombrePrises": (int),
                                "configsMutualisation": [
                                    {"configMutualisation": [(int)]}
                                ],
                            },
                            "rendement": [
                                {"x": (int), "y": (int, float)}
                            ],
                            "prises": [
                                {
                                    "id": str,
                                    "libelle": str,
                                    "etat": str,
                                    "typePrise": str,
                                    "pMax": (int),
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ],
    "vehicules": [
        {
            "id": str,
            "capaciteBatterie": (int),
            "idPrise": str,
            "libelle": str,
            "modeBoost": (int),
            "typeChargeur": [{"modeleChargeur": str}],
            "typePrise": str,
            "profilBatterie": [
                {"x": (int), "y": (int)}
            ],
            "soc": (int),
            "socCible": (int),
            "dureeService": (int),
            "finService": _is_iso_datetime,
            "debutService": _is_iso_datetime,
        }
    ],
}

# Validation engine -------------------------------------------------------

def _validate(value: Any, schema: Any, path: str = "") -> None:
    """Recursively validate value against schema."""
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise TypeError(f"{path or 'value'} must be an object")
        for key, subschema in schema.items():
            if key not in value:
                raise ValueError(f"Missing key {path + key}")
            _validate(value[key], subschema, path + key + ".")
    elif isinstance(schema, list):
        if not isinstance(value, list):
            raise TypeError(f"{path.rstrip('.') or 'value'} must be a list")
        if len(schema) != 1:
            raise ValueError("schema list must contain a single element")
        subschema = schema[0]
        for idx, item in enumerate(value):
            _validate(item, subschema, f"{path}[{idx}].")
    elif isinstance(schema, type):
        if not isinstance(value, schema):
            raise TypeError(f"{path.rstrip('.')} must be of type {schema.__name__}")
    elif isinstance(schema, tuple):
        if not any(isinstance(value, t) for t in schema):
            raise TypeError(f"{path.rstrip('.')} must be of type {schema}")
    elif callable(schema):
        if not schema(value):
            raise ValueError(f"{path.rstrip('.')} has invalid value")
    else:
        raise TypeError("Unsupported schema element")


def validate_json(data: Dict[str, Any]) -> None:
    """Validate data against the built-in JSON schema."""
    _validate(data, SCHEMA, path="")