import json
from pathlib import Path

from src.mapper import map_records, map_record, _load_template
from src.utils import load_infrastructure


def test_map_records_with_infrastructure(tmp_path: Path) -> None:
    infra = {
        "sources": [
            {
                "id": "SRC",
                "transformateurs": [
                    {
                        "id": "T1",
                        "chargeurs": [
                            {
                                "id": "C1",
                                "typeChargeur": "TypeChargeur_valeur",
                                "prises": [
                                    {"id": "P1", "typePrise": "CCS COMBO2"}
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    path = tmp_path / "infra.json"
    path.write_text(json.dumps(infra))

    records = [
        {"newIdVeh": "1", "seqVoy": "1"},
        {"newIdVeh": "2", "seqVoy": "1"},
    ]

    template = _load_template()
    result = map_records(records, template=template, infrastructure_path=path)

    assert result["sources"] == infra["sources"]
    ids = {v["idPrise"] for v in result["vehicules"]}
    assert ids == {"P1"}
    assert load_infrastructure(path) == infra


def test_map_record_with_infrastructure(tmp_path: Path) -> None:
    infra = {
        "sources": [
            {
                "id": "SRC",
                "transformateurs": [
                    {
                        "id": "T1",
                        "chargeurs": [
                            {
                                "id": "C1",
                                "typeChargeur": "TypeChargeur_valeur",
                                "prises": [
                                    {"id": "P1", "typePrise": "CCS COMBO2"},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    path = tmp_path / "infra.json"
    path.write_text(json.dumps(infra))

    rec = {"newIdVeh": "1", "seqVoy": "1"}
    template = _load_template()
    result = map_record(rec, template=template, infrastructure_path=path)

    assert result["sources"] == infra["sources"]
    veh = result["vehicules"][0]
    assert veh["idPrise"] == "P1"