from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any
from datetime import datetime, timedelta
import json
import zipfile
import xml.etree.ElementTree as ET

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_BATTERY_PROFILE = DATA_DIR / "profil_batterie_camion.xlsx"
DEFAULT_DONNEES_CAMIONS = DATA_DIR / "donnees_camions.xlsx"

try:
    import pandas as pd
except Exception:  
    pd = None
    
try:  
    import yaml
except Exception:
    yaml = None


def load_infrastructure(path: Path | str) -> Dict[str, Any]:
    """Load infrastructure description from JSON or YAML file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    ext = path.suffix.lower()
    if ext in {".yaml", ".yml"}:
        if yaml is None:
            raise ImportError("PyYAML is required to load YAML files")
        return yaml.safe_load(text) or {}
    return json.loads(text)

def load_battery_profile(path: Path = DEFAULT_BATTERY_PROFILE) -> List[Dict[str, float]]:
    """Return the battery profile as a list of ``{"x": float, "y": float}``."""
    if pd is not None:
        df = pd.read_excel(path)
        rows = df.to_numpy().tolist()
    else:
        with zipfile.ZipFile(path) as z:
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            strings_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            strings = [
                "".join(t.text or "" for t in si.findall(".//m:t", ns))
                for si in strings_root.findall("m:si", ns)
            ]
            sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
            rows = []
            for row in sheet.findall("m:sheetData/m:row", ns):
                vals = []
                for c in row.findall("m:c", ns):
                    v = c.find("m:v", ns)
                    if v is None:
                        vals.append("")
                    elif c.get("t") == "s":
                        vals.append(strings[int(v.text)])
                    else:
                        vals.append(v.text)
                rows.append(vals)
            rows = rows[1:]
    result = []
    for r in rows:
        if len(r) < 2:
            continue
        x, y = r[0], r[1]
        if pd is not None:
            try:
                import math
                if x is None or y is None or (isinstance(x, float) and math.isnan(x)) or (isinstance(y, float) and math.isnan(y)):
                    continue
            except Exception:
                pass
        if x in ("", None) or y in ("", None):
            continue
        try:
            result.append({"x": int(x), "y": int(y)})
        except Exception:
            continue
    return result


def _load_donnees_camions(path: Path = DEFAULT_DONNEES_CAMIONS) -> Dict[Tuple[int, str], float]:
    """Return a mapping ``(projection, modele) -> capacite`` from the Excel file."""
    path = Path(path)
    mapping: Dict[Tuple[int, str], float] = {}
    with zipfile.ZipFile(path) as z:
        strings_xml = z.read("xl/sharedStrings.xml")
        root = ET.fromstring(strings_xml)
        strings = [
            "".join(t.text or "" for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si")
        ]

        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        sheet = ET.fromstring(sheet_xml)

        rows = []
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for row in sheet.findall("m:sheetData/m:row", ns):
            vals = []
            for c in row.findall("m:c", ns):
                v = c.find("m:v", ns)
                if v is None:
                    vals.append("")
                elif c.get("t") == "s":
                    vals.append(strings[int(v.text)])
                else:
                    vals.append(v.text)
            rows.append(vals)

    header = rows[0]
    proj_idx = header.index("Projection")
    model_idx = header.index("Modèle")
    cap_idx = header.index("Capacité max de la batterie (kWh)")

    for r in rows[1:]:
        if len(r) <= cap_idx:
            continue
        try:
            proj = int(r[proj_idx])
        except Exception:
            continue
        modele = r[model_idx].strip()
        if not modele:
            continue
        try:
            cap = float(r[cap_idx])
        except Exception:
            continue
        mapping[(proj, modele)] = cap

    return mapping

def _load_donnees_camions_conso(
    path: Path = DEFAULT_DONNEES_CAMIONS,
) -> Dict[Tuple[int, str], float]:
    """Return a mapping ``(projection, modele) -> consumption`` from the Excel file."""
    path = Path(path)
    mapping: Dict[Tuple[int, str], float] = {}
    with zipfile.ZipFile(path) as z:
        strings_xml = z.read("xl/sharedStrings.xml")
        root = ET.fromstring(strings_xml)
        strings = [
            "".join(t.text or "" for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si")
        ]

        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        sheet = ET.fromstring(sheet_xml)

        rows = []
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for row in sheet.findall("m:sheetData/m:row", ns):
            vals = []
            for c in row.findall("m:c", ns):
                v = c.find("m:v", ns)
                if v is None:
                    vals.append("")
                elif c.get("t") == "s":
                    vals.append(strings[int(v.text)])
                else:
                    vals.append(v.text)
            rows.append(vals)

    header = rows[0]
    proj_idx = header.index("Projection")
    model_idx = header.index("Modèle")
    conso_idx = header.index("Conso estimée réelle (kWh/km)")

    for r in rows[1:]:
        if len(r) <= conso_idx:
            continue
        try:
            proj = int(r[proj_idx])
        except Exception:
            continue
        modele = r[model_idx].strip()
        if not modele:
            continue
        try:
            conso = float(r[conso_idx])
        except Exception:
            continue
        mapping[(proj, modele)] = conso

    return mapping

DEFAULT_RESULTAT_SIMU = DATA_DIR / "resultat_simu_1.xlsx"


def load_resultat_simu(
    path: Path = DEFAULT_RESULTAT_SIMU, *, mode: str | None = "E"
) -> List[Dict[str, str]]:
    """
    Return the rows of the Excel file filtered by vehicle mode : 'E' or 'T'. 
    """
    path = Path(path)
    records: List[Dict[str, str]] = []
    with zipfile.ZipFile(path) as z:
        strings_xml = z.read("xl/sharedStrings.xml")
        root = ET.fromstring(strings_xml)
        strings = [
            "".join(t.text or "" for t in si.findall(
                ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
            ))
            for si in root.findall(
                "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"
            )
        ]

        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        sheet = ET.fromstring(sheet_xml)

        rows = []
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for row in sheet.findall("m:sheetData/m:row", ns):
            vals = []
            for c in row.findall("m:c", ns):
                v = c.find("m:v", ns)
                if v is None:
                    vals.append("")
                elif c.get("t") == "s":
                    vals.append(strings[int(v.text)])
                else:
                    vals.append(v.text)
            rows.append(vals)

    header = rows[0]
    mode_idx = header.index("mode")

    for r in rows[1:]:
        if len(r) <= mode_idx:
            continue
        if mode is not None and str(r[mode_idx]).strip() != mode:
            continue
        record = {
            header[i]: (r[i] if i < len(r) else "") for i in range(len(header))
        }
        records.append(record)

    return records

EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_number_to_datetime(value: float) -> datetime:
    """Convert an Excel serial date number to :class:`datetime`."""
    return EXCEL_EPOCH + timedelta(days=float(value))


def jour_dep_bounds(
    path: Path = DEFAULT_RESULTAT_SIMU,
    *,
    mode: str | None = None,
) -> tuple[datetime, datetime]:
    """Return the minimum and maximum ``jourDep`` values as datetimes."""
    rows = load_resultat_simu(path, mode=mode)
    jour_vals: List[float] = []
    for r in rows:
        try:
            jour_vals.append(float(r.get("jourDep", 0)))
        except Exception:
            continue
    if not jour_vals:
        return EXCEL_EPOCH, EXCEL_EPOCH
    return excel_number_to_datetime(min(jour_vals)), excel_number_to_datetime(
        max(jour_vals)
    )

def _load_donnees_camions_puissance(
    path: Path = DEFAULT_DONNEES_CAMIONS,
) -> Dict[Tuple[int, str], float]:
    """Return a mapping ``(projection, modele) -> puissance`` from the Excel file."""
    path = Path(path)
    mapping: Dict[Tuple[int, str], float] = {}
    with zipfile.ZipFile(path) as z:
        strings_xml = z.read("xl/sharedStrings.xml")
        root = ET.fromstring(strings_xml)
        strings = [
            "".join(t.text or "" for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"))
            for si in root.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si")
        ]

        sheet_xml = z.read("xl/worksheets/sheet1.xml")
        sheet = ET.fromstring(sheet_xml)

        rows = []
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for row in sheet.findall("m:sheetData/m:row", ns):
            vals = []
            for c in row.findall("m:c", ns):
                v = c.find("m:v", ns)
                if v is None:
                    vals.append("")
                elif c.get("t") == "s":
                    vals.append(strings[int(v.text)])
                else:
                    vals.append(v.text)
            rows.append(vals)

    header = rows[0]
    proj_idx = header.index("Projection")
    model_idx = header.index("Modèle")
    power_idx = header.index("Puissance de recharge max (kW)")

    for r in rows[1:]:
        if len(r) <= power_idx:
            continue
        try:
            proj = int(r[proj_idx])
        except Exception:
            continue
        modele = r[model_idx].strip()
        if not modele:
            continue
        try:
            power = float(r[power_idx])
        except Exception:
            continue
        mapping[(proj, modele)] = power

    return mapping

def parse_iso_datetime(value: str | datetime) -> datetime:
    """Parse an ISO 8601 date-time string, accepting a trailing ``'Z'``."""

    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).rstrip("Z"))


def isoformat_z(dt: datetime, *, timespec: str = "seconds") -> str:
    """Return an ISO 8601 date-time string with a trailing ``'Z'``.
    """

    return dt.replace(microsecond=0).isoformat(timespec=timespec) + "Z"
