import os
import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pd = pytest.importorskip("pandas")

from src.main import main
from src.utils import DEFAULT_RESULTAT_SIMU


def test_choix_optim_parameter(tmp_path: Path) -> None:
    output_file = tmp_path / "c.json"
    result = main(
        DEFAULT_RESULTAT_SIMU,
        mode="E",
        output=output_file,
        choix_optim="LLLP",
    )
    assert output_file.exists()
    written = json.loads(output_file.read_text())
    assert result["choix_optim"] == "LLLP"
    assert written["choix_optim"] == "LLLP"