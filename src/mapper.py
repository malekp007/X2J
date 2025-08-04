"""
Mapper module with fully populated internal default JSON template.
"""

from __future__ import annotations
import json
from datetime import datetime, timedelta
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any, Mapping

import random 

try:
    import pandas as pd
except Exception:
    pd = None

from src.utils import (
    load_battery_profile,
    _load_donnees_camions,
    _load_donnees_camions_puissance,
    _load_donnees_camions_conso,
    jour_dep_bounds,
    excel_number_to_datetime,
    isoformat_z,
    parse_iso_datetime,
    load_infrastructure,
)

# Default path to the battery profile shared by all vehicles
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_BATTERY_PROFILE = DATA_DIR / "profil_batterie_camion.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# Default template (no external file required)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_TEMPLATE: Dict = {
    'idRun': '01234567891011',
    'choix_optim': '',
    'synthese': [],
    'configuration': {
        'activationRendement': 'false',  # string, not boolean
        'axeOptimDegrade': [],           # list[float]
        'diminutionSOC': 0,
        'pasDeTemps': 0,
        'maximumExecTemps': 0,
        'debutOptim': '2000-01-01T00:00:00',  # ISO‑8601 date‑time
        'finOptim': '2050-01-01T01:00:00',    # ISO‑8601 date‑time              # ISO‑8601 date‑time
    },
    'rapport': {
        'url': 'http://example.com',
        'resultUrl': 'http://example.com/result',
    },
    'sources': [
        {
            'id': '',
            'libelle': '',
            'pMax': [],                   # list[float]
            'tranches': [
                {
                    'id': '',
                    'cout': 0.0,
                    'dateDebut': '',     # YYYY‑MM‑DD
                    'dateFin': '',       # YYYY‑MM‑DD
                    'heureTranche': [
                        {
                            'debut': 0,  # hour 0‑23
                            'fin': 1,
                        }
                    ],
                }
            ],
            'transformateurs': [
                {
                    'id': '',
                    'libelle': '',
                    'etat': '',          # e.g. "online"
                    'rendement': [
                        {
                            "x": 10,
                            "y": 0.9
                        },
                        {
                            "x": 20,
                            "y": 0.9
                        },
                        {
                            "x": 30,
                            "y": 0.9
                        },
                        {
                            "x": 40,
                            "y": 0.9
                        },
                        {
                            "x": 50,
                            "y": 0.9
                        },
                        {
                            "x": 60,
                            "y": 0.9
                        },
                        {
                            "x": 70,
                            "y": 0.9
                        },
                        {
                            "x": 80,
                            "y": 0.9
                        },
                        {
                            "x": 90,
                            "y": 0.9
                        },
                        {
                            "x": 100,
                            "y": 0.9
                        }
                    ],      # list[{x,y}]
                    'facteurPuissance': 0,
                    'pMax': 0,
                    'chargeurs': [
                        {
                            'id': '',
                            'libelle': '',
                            'etat': '',
                            'pMax': 0,
                            'typeChargeur': 'TypeChargeur_valeur',
                            'mutualisation': {
                                'nombrePrises': 0,
                                'configsMutualisation': [
                                    {
                                        'configMutualisation': [100],  # list[int]
                                    }
                                ],
                            },
                            'rendement': [
                                {
                                    "x": 10,
                                    "y": 0.94
                                },
                                {
                                    "x": 20,
                                    "y": 0.94
                                },
                                {
                                    "x": 30,
                                    "y": 0.94
                                },
                                {
                                    "x": 40,
                                    "y": 0.94
                                },
                                {
                                    "x": 50,
                                    "y": 0.94
                                },
                                {
                                    "x": 60,
                                    "y": 0.94
                                },
                                {
                                    "x": 70,
                                    "y": 0.94
                                },
                                {
                                    "x": 80,
                                    "y": 0.94
                                },
                                {
                                    "x": 90,
                                    "y": 0.94
                                },
                                {
                                    "x": 100,
                                    "y": 0.94
                                }
                            ],  # list[{x,y}]
                            'prises': [
                                {
                                    'id': '',
                                    'libelle': '',
                                    'etat': '',
                                    'typePrise': '',
                                    'pMax': 0,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ],
    'vehicules': [
        {
            'id': '',
            'capaciteBatterie': 0.0,
            'idPrise': '',
            'libelle': '',
            'modeBoost': 0,
            'typeChargeur': [
                {'modeleChargeur': 'TypeChargeur_valeur'},
            ],
            'typePrise': 'CCS COMBO2',
            'profilBatterie': [],  # list[{x,y}]
            'soc': 0.0,
            'socCible': 0.0,
            'dureeService': 0,      # minutes
            'finService': '',       # ISO‑8601 date‑time
            'debutService': '',     # ISO‑8601 date‑time
        }
    ],
}


def _load_template(_: Path | None = None) -> Dict:
    """Return a fresh deepcopy of the internal template."""
    return deepcopy(DEFAULT_TEMPLATE)

def build_chargeurs(
    records: Iterable[Dict],
    *,
    template: Dict,
    chargeur_pmax: int | None = None,
    prise_pmax: int | None = None,
) -> List[Dict]:
    """Return a list of charger definitions for all unique vehicles."""
    seen: set[str] = set()
    chargeurs: List[Dict] = []
    ch_template = template.get("sources", [{}])[0].get("transformateurs", [{}])[0].get("chargeurs", [{}])[0]
    prise_template = ch_template.get("prises", [{}])[0]

    for idx, rec in enumerate(records):
        veh = str(rec.get("newIdVeh", "")).strip()
        if not veh or veh in seen:
            continue
        seen.add(veh)
        chargeur = deepcopy(ch_template)
        chargeur.update({
            "id": f"TR1_CH_{idx}",
            "libelle": f"TR1_CH_{idx}",
            "etat": "online",
            "pMax": int(chargeur_pmax or 0),
            "typeChargeur": str("TypeChargeur_valeur"),
            "mutualisation": {"nombrePrises": 1, "configsMutualisation": [{"configMutualisation": [100]}]},
        })
        prise = deepcopy(prise_template)
        prise.update({
            "id": f"PR_{veh or idx}",
            "libelle": f"TR1_CH_{idx}_P1",
            "etat": "online",
            "typePrise": str("Type Prise"),
            "pMax": int(prise_pmax or 0.0),
        })
        chargeur["prises"] = [prise]
        chargeurs.append(chargeur)

    return chargeurs

def map_record(
    record: Dict,
    *,
    template: Dict,
    battery_profile_path: Path = DEFAULT_BATTERY_PROFILE,
    donnees_camions_path: Path = DATA_DIR / "donnees_camions.xlsx",
    resultat_simu_path: Path = DATA_DIR / "resultat_simu_1.xlsx",
    projection: int = 0,
    marge_securite: int = 15,
    marge_prechauffage: int = 30,
    soc_cible: int = 0.0,
    activation_rendement: str | None = "false",
    diminution_soc: int = 5,
    pas_de_temps: int | None = None,
    maximum_exec_temps: int = 10,
    start_dt: str | datetime | None = None,
    end_dt: str | datetime | None = None,
    temps_chargement: int | int | None = 30,
    temps_dechargement: int | int | None = 45,
    infrastructure_path: Path | None = None,
    axe_optim_degrade: List[int] | None = None,
    choix_optim: str | None = "",
    default_debut_service: str | datetime | None = "2050-01-01T23:59:59Z",
) -> Dict:
    """
    Convert a single record row to the target JSON structure.
    """
    data = deepcopy(template)

#---Choix Optim -----------------------------------------------------------------------------------------
    data["choix_optim"] = choix_optim
#---Configuration ---------------------------------------------------------------------------------------
    config_template = template.get("configuration")
    configuration = deepcopy(config_template)

    #configuration.activationRendement
    if activation_rendement is not None:
        configuration["activationRendement"] = str(activation_rendement)
    #configuration.axeOptimDegrade
    if axe_optim_degrade is None:
        configuration["axeOptimDegrade"] = [1, 2, 3]
    else:
        configuration["axeOptimDegrade"] = [int(v) for v in axe_optim_degrade]
    #configuration.diminutionSOC
    if diminution_soc is not None:
        configuration["diminutionSOC"] = int(diminution_soc)
    #configuration.pasDeTemps
    if pas_de_temps is not None:
        configuration["pasDeTemps"] = int(pas_de_temps)
    #configuration.maximumExecTemps
    configuration["maximumExecTemps"] = int(maximum_exec_temps)

    # compute the jourDep bounds once for both start and end date handling
    min_jour, max_jour = jour_dep_bounds(resultat_simu_path)

    # configuration.debutOptim
    if start_dt is not None:
        debut_dt = parse_iso_datetime(start_dt)
        bound = (min_jour - timedelta(days=3)).date()
        if debut_dt.date() < bound:
            debut_dt = datetime.combine(bound, datetime.max.time())
        # Arrondir les microsecondes à la seconde la plus proche
        if debut_dt.microsecond >= 500_000:
            debut_dt = debut_dt + timedelta(seconds=1)
        debut_dt = debut_dt.replace(microsecond=0)
        configuration["debutOptim"] = isoformat_z(debut_dt)

    # configuration.finOptim
    if end_dt is not None:
        fin_dt = parse_iso_datetime(end_dt)
        bound = (max_jour + timedelta(days=3)).date()
        if fin_dt.date() > bound:
            fin_dt = datetime.combine(bound, datetime.min.time())
        configuration["finOptim"] = isoformat_z(fin_dt)



    data["configuration"] = configuration

#---Sources ---------------------------------------------------------------------------------------------
    infra = None
    if infrastructure_path is not None:
        try:
            infra = load_infrastructure(infrastructure_path)
        except Exception:
            infra = None
        
    if infra is not None:
        data["sources"] = infra.get("sources", [])
    else:
        data["sources"] = []

#---Vehicules -------------------------------------------------------------------------------------------
    veh_template = template.get("vehicules", [{}])[0]
    vehicule = deepcopy(veh_template)
    new_id = str(record.get("newIdVeh", "")).strip() or None
    
 #vehicules.vehicule.capaciteBatterie
    capacities = _load_donnees_camions(donnees_camions_path)
    tveh = (record.get("tVeh") or "").strip()
    vehicule["capaciteBatterie"] = int(capacities.get((int(projection), tveh), 0))

    #vehicules.vehicule.idPrise
    vehicule["idPrise"] = ""
    if infra is not None:
        # Flatten all available chargers with at least one plug
        chargers: List[Dict[str, Any]] = []
        for src in infra.get("sources", []):
            for trans in src.get("transformateurs", []):
                for ch in trans.get("chargeurs", []):
                    if ch.get("prises"):
                        chargers.append(ch)

        if chargers:
            charger = random.choice(chargers)
            prise = random.choice(charger.get("prises", []))
            vehicule["idPrise"] = prise.get("id", "")
            # Update charger and plug types from the infrastructure
            modele = charger.get("typeChargeur")
            if modele:
                vehicule["typeChargeur"][0]["modeleChargeur"] = str(modele)
            vehicule["typePrise"] = str(prise.get("typePrise", vehicule["typePrise"]))
    elif new_id is not None:
        vehicule["idPrise"] = f"TR1_CH_{new_id}_P1"
        
    #vehicules.vehicule.modeBoost
    vehicule["modeBoost"] = 0
    
    #vehicules.vehicule.profilBatterie
    profile = load_battery_profile(battery_profile_path)
    powers = _load_donnees_camions_puissance(donnees_camions_path)
    power = powers.get((int(projection), tveh))
    if power is not None and profile:
        max_y = max(p["y"] for p in profile)
        if max_y:
            alpha = power / max_y
            profile = [{"x": int(p["x"]), "y": int(alpha * int(p["y"]))} for p in profile]
    vehicule["profilBatterie"] = profile

    #vehicules.vehicule.soc
    try:
        vehicule["soc"] = int(
            record.get("soc_retour", record.get("soc", 0))
        )
    except Exception:
        vehicule["soc"] = 0
    #vehicules.vehicule.socCible
    try:
        vehicule["socCible"] = int(record.get("socCible", soc_cible))
    except Exception:
        vehicule["socCible"] = int(soc_cible)

    #vehicules.vehicule.dureeService
    def _dt(value):
        if isinstance(value, datetime):
            return value
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value))
        except Exception:
            pass
        try:
            return excel_number_to_datetime(float(value))
        except Exception:
            return None
    h_fin = _dt(record.get("hFin"))
    dist = record.get("dist")
    try:
        dist_val = int(dist)
    except Exception:
        dist_val = None
    if dist_val is not None:
        vehicule["dureeService"] = dist_val

    #vehicules.vehicule.finService
    temp_decharg = temps_dechargement or 0
    if h_fin:
        fin_service = h_fin + timedelta(minutes=float(temp_decharg))
        vehicule["finService"] = isoformat_z(fin_service)
    else:
        vehicule["finService"] = ""
    #vehicules.vehicule.debutService
    next_service = _dt(record.get("Heure Prochain Service"))
    temps_charg = temps_chargement or 0
    marge_sec = record.get("MargeSécurité") or 0
    if next_service:
        debut_service = next_service - timedelta(
            minutes=float(temps_charg) + float(marge_sec)
        )
        vehicule["debutService"] = isoformat_z(debut_service)
    elif default_debut_service is not None:
        default_debut_service = (parse_iso_datetime(configuration["finOptim"]) + timedelta(days=1.5)).isoformat()
        ds_val = default_debut_service
        if isinstance(ds_val, datetime):
            vehicule["debutService"] = isoformat_z(ds_val)
        else:
            try:
                vehicule["debutService"] = isoformat_z(parse_iso_datetime(ds_val))
            except Exception:
                vehicule["debutService"] = str(ds_val)

    # vehicules.vehicule.libelle
    conso_table = _load_donnees_camions_conso(donnees_camions_path)
    conso_value = conso_table.get((int(projection), tveh), 0.0)

    # Convert marge_securite (minutes) to HH:MM format
    hours, minutes = divmod(int(marge_securite), 60)
    marge_securite_hhmm = f"{hours:02d}:{minutes:02d}"

    # Convert marge_prechauffage (minutes) to HH:MM format
    hours, minutes = divmod(int(marge_prechauffage), 60)
    marge_prechauffage_hhmm = f"{hours:02d}:{minutes:02d}"

    #vehicules.vehicule.id
    if new_id is not None:
        vehicule["id"] = new_id

    vehicule["libelle"] = json.dumps(
        {
            "numeroExploitation": f"{new_id}",
            "debutService": vehicule.get("debutService", ""),
            "MargeSecurite": marge_securite_hhmm,
            "MargePrechauffage": marge_prechauffage_hhmm,
            "Conso": round(conso_value, 2)
        },
        ensure_ascii=False,
    )



    data["vehicules"] = [vehicule]

#--------------------------------------------------------------------------------------------------------------------------

    return data

def aggregate_results(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine per-vehicle structures into a single JSON object."""
    results = list(results)
    if not results:
        return {}
    merged = deepcopy(results[0])
    merged["vehicules"] = []
    chargeurs: List[Dict] = []
    seen: set[str] = set()

    for item in results:
        merged["vehicules"].extend(item.get("vehicules", []))
        src = item.get("sources")
        if not src:
            continue
        trans = src[0].get("transformateurs")
        if not trans:
            continue
        ch_list = trans[0].get("chargeurs")
        if not ch_list:
            continue
        for ch in ch_list:
            ch_id = ch.get("id")
            if ch_id and ch_id not in seen:
                chargeurs.append(ch)
                seen.add(ch_id)

    if merged.get("sources"):
        merged["sources"][0]["transformateurs"][0]["chargeurs"] = chargeurs

    return merged


def map_records(
    records: Iterable[Dict[str, Any]],
    *,
    template: Dict,
    aggregate: bool = False,
    infrastructure_path: Path | None = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Map multiple records to JSON structures."""
    
    infra = None
    if infrastructure_path is not None:
        try:
            infra = load_infrastructure(infrastructure_path)
        except Exception:
            infra = None

    results: List[Dict[str, Any]] = []
    for rec in records:
        results.append(
            map_record(
                rec,
                template=template,
                infrastructure_path=infrastructure_path,
                **kwargs,
            )
        )

    merged = aggregate_results(results)
    if infra is not None:
        merged["sources"] = infra.get("sources", [])
    return merged