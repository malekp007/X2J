import os
import sys
import pytest


import json
from pathlib import Path

from src.validator import validate_optim_dates, validate_json
from src.mapper import _load_template, map_record


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.validator import validate_optim_dates


def test_validate_optim_dates_accepts_valid_range():
    # should not raise
    validate_optim_dates("2024-12-15", "2024-12-20")


def test_validate_optim_dates_rejects_invalid_range():
    with pytest.raises(ValueError):
        validate_optim_dates("2024-12-17", "2024-12-18")

def test_validate_json_accepts_template(tmp_path: Path):
    record = {
        "newIdVeh": "1",
        "seqVoy": "1",
        "tVeh": "T",
        "hDep": "2023-06-03T08:00:00",
        "hFin": "2023-06-03T10:00:00",
        "Heure Prochain Service": "2023-06-03T12:00:00",
        "Temps Chargement": 20,
        "MargeSécurité": 5,
        "Temps Déchargement": 10,
    }
    infra = {
        "sources": [
            {
                "transformateurs": [
                    {
                        "chargeurs": [
                            {
                                "typeChargeur": "type",
                                "prises": [
                                    {"id": "P1", "typePrise": "T"}
                                ],
                            }
                        ],
                    }
                ]
            }
        ]
    }
    infra_path = tmp_path / "infra.json"
    infra_path.write_text(json.dumps(infra))
    
    data = map_record(
        record, 
        template=_load_template(),
        temps_chargement=20,
        temps_dechargement=10,
        infrastructure_path=infra_path,
    )
    # fill in missing values so that validation passes
    src = _load_template()["sources"][0]
    data["sources"] = [src]
    src["id"] = "SRC"
    src["libelle"] = "SRC"
    src["pMax"] = [1]
    src["tranches"][0]["id"] = "T"
    src["tranches"][0]["dateDebut"] = "2023-01-01"
    src["tranches"][0]["dateFin"] = "2023-01-01"
    src["transformateurs"][0].update({
        "id": "TR1",
        "libelle": "TR1",
        "etat": "online",
        "rendement": [{"x": 1, "y": 1}],
    })
    ch = src["transformateurs"][0]["chargeurs"][0]
    ch.update({
        "id": "C1",
        "libelle": "C1",
        "etat": "online",
        "pMax": 1,
        "typeChargeur": "type",
    })
    ch["mutualisation"]["nombrePrises"] = 1
    ch["mutualisation"]["configsMutualisation"][0]["configMutualisation"] = [1]
    ch["rendement"] = [{"x": 1, "y": 1}]
    prise = ch["prises"][0]
    prise.update({"id": "P1", "libelle": "P1", "etat": "online", "typePrise": "T", "pMax": 1})
    veh = data["vehicules"][0]
    veh.update({
        "id": "V1",
        "idPrise": "P1",
        "libelle": "V1",
        "typePrise": "T",
        "profilBatterie": [{"x": 1, "y": 1}],
        "finService": "2023-06-03T10:10:00",
        "debutService": "2023-06-03T11:40:00",
    })
    validate_json(data)


def test_validate_json_rejects_invalid_type():
    data = _load_template()
    data["configuration"]["pasDeTemps"] = "oops"
    with pytest.raises(TypeError):
        validate_json(data)