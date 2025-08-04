"""
Testing if we only keep 'E' vehicules in '.\data\resultat_simu_1.xlsx' file
"""
from src.utils import load_resultat_simu, DEFAULT_RESULTAT_SIMU

def test_load_resultat_simu_filters_mode():
    rows = load_resultat_simu(DEFAULT_RESULTAT_SIMU, mode="E")
    assert rows, "should load at least one row"
    assert all(r.get("mode") == "E" for r in rows)