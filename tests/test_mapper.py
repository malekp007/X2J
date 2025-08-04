import os
import sys
from pathlib import Path
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mapper import map_record, map_records, _load_template, build_chargeurs
from src.utils import (
    load_battery_profile,
    _load_donnees_camions,
    _load_donnees_camions_puissance,
    load_resultat_simu,
    DEFAULT_RESULTAT_SIMU,
)

def test_load_donnees_camions():
    table = _load_donnees_camions()
    assert table[(2, "P")] == 570.0
    assert table[(5, "T")] == 950.0

def test_load_donnees_camions_puissance():
    table = _load_donnees_camions_puissance()
    assert table[(5, "T")] == 1500.0


def test_map_record_battery_capacity():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1", "tVeh": "T"}
    result = map_record(record, template=template, projection=5)
    assert result["vehicules"][0]["capaciteBatterie"] == 950.0

def test_map_record_scales_battery_profile():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1", "tVeh": "T"}
    result = map_record(record, template=template, projection=5)
    profile = result["vehicules"][0]["profilBatterie"]
    reference = load_battery_profile()
    alpha = _load_donnees_camions_puissance()[(5, "T")] / max(p["y"] for p in reference)
    assert profile[0]["y"] == int(alpha * reference[0]["y"])


def test_map_record_libelle_generation():
    template = _load_template()
    record = {
        "newIdVeh": "1",
        "seqVoy": "1",
        "Heure Prochain Service": "2023-06-03T12:00:00",
        "MargeSécurité": 5,
        "tVeh": "P",
    }
    result = map_record(
        record,
        template=template,
        temps_chargement=20,
        marge_securite=10,
        marge_prechauffage=15,
    )
    vehicule = result["vehicules"][0]
    data = json.loads(vehicule["libelle"])
    assert data["debutService"] == "2023-06-03T11:35:00Z"
    assert data["MargeSecurite"] == "00:10"
    assert data["MargePrechauffage"] == "00:15"
    from src.utils import _load_donnees_camions_conso
    expected = _load_donnees_camions_conso()[ (0, "P") ]
    assert data["Conso"] == round(expected, 2)

def test_map_record_type_chargeur():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(record, template=template)
    expected = [{"modeleChargeur": "TypeChargeur_valeur"}]
    assert result["vehicules"][0]["typeChargeur"] == expected

def test_map_record_sets_type_prise():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(record, template=template)
    vehicule = result["vehicules"][0]
    assert vehicule["typePrise"] == 'CCS COMBO2'

def test_map_record_sets_id_prise():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(record, template=template)
    vehicule = result["vehicules"][0]
    assert vehicule["idPrise"] == "TR1_CH_1_P1"

def test_map_record_sets_configuration_values():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(
        record,
        template=template,
        activation_rendement="true",
        diminution_soc=5,
        pas_de_temps=15,
        start_dt="2024-12-15",
        end_dt="2025-12-20",
    )
    config = result["configuration"]
    assert config["activationRendement"] == "true"
    assert config["diminutionSOC"] == 5
    assert config["pasDeTemps"] == 15
    assert config["debutOptim"] == "2024-12-15T00:00:00Z"
    assert config["finOptim"] == "2024-12-22T00:00:00Z"

def test_map_record_custom_axeoptimdegrade():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(record, template=template, axe_optim_degrade=[3, 2, 1])
    config = result["configuration"]
    assert config["axeOptimDegrade"] == [3, 2, 1]



def test_map_record_invalid_debutoptim():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1"}
    result = map_record(
        record,
        template=template,
        start_dt="2024-12-17",
        end_dt="2024-12-20",
    )
    config = result["configuration"]
    assert config["debutOptim"] == "2024-12-17T00:00:00Z"
    assert config["finOptim"] == "2024-12-20T00:00:00Z"


def test_build_chargeurs_generates_unique_items():
    template = _load_template()
    records = load_resultat_simu(DEFAULT_RESULTAT_SIMU, mode="E")[:10]
    chargeurs = build_chargeurs(
        records,
        template=template,
        chargeur_pmax=150,
        prise_pmax=60,
    )
    unique_ids = set(
        r.get("newIdVeh", "").strip() for r in records if r.get("newIdVeh", "").strip()
    )
    assert len(chargeurs) == len(unique_ids)
    first = chargeurs[0]
    assert first["id"].startswith("TR1_")
    assert first["pMax"] == 150
    assert first["mutualisation"]["nombrePrises"] == 1
    assert first["prises"][0]["pMax"] == 60


def test_map_records_aggregate() -> None:
    template = _load_template()
    records = [
        {"newIdVeh": "1", "seqVoy": "1"},
        {"newIdVeh": "2", "seqVoy": "1"},
    ]
    result = map_records(records, template=template)

    assert isinstance(result, dict)
    assert "configuration" in result
    assert "sources" in result
    assert isinstance(result.get("vehicules"), list)
    assert len(result["vehicules"]) == 2

def test_map_record_uses_soc_retour():
    template = _load_template()
    record = {"newIdVeh": "1", "seqVoy": "1", "soc_retour": 42}
    result = map_record(record, template=template)

    vehicule = result["vehicules"][0]
    assert vehicule["soc"] == 42.0

