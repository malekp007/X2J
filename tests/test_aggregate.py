import os
import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pd = pytest.importorskip("pandas")

from src.main import main
from src.utils import load_resultat_simu, DEFAULT_RESULTAT_SIMU


def test_main_aggregate(tmp_path: Path) -> None:
    rows = load_resultat_simu(DEFAULT_RESULTAT_SIMU, mode="E")
    output_file = tmp_path / "agg.json"

    result = main(
        DEFAULT_RESULTAT_SIMU,
        mode="E",
        output=output_file,
    )

    assert output_file.exists()
    written = json.loads(output_file.read_text())

    assert isinstance(result, dict)
    assert result == written
    assert "configuration" in result
    assert "sources" in result
    assert isinstance(result.get("vehicules"), list)
    assert len(result["vehicules"]) == len(rows)