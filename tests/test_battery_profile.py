import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mapper import load_battery_profile, map_record, _load_template, DEFAULT_BATTERY_PROFILE


def test_load_battery_profile():
    profile = load_battery_profile(DEFAULT_BATTERY_PROFILE)
    assert isinstance(profile, list)
    assert len(profile) > 0
    assert set(profile[0].keys()) == {"x", "y"}


def test_map_record_sets_profile():
    template = _load_template()
    record = {"newIdVeh": "A", "seqVoy": "1"}
    result = map_record(record, template=template, battery_profile_path=DEFAULT_BATTERY_PROFILE)
    profile = result["vehicules"][0]["profilBatterie"]
    assert isinstance(profile, list)
    assert len(profile) > 0
    assert set(profile[0].keys()) == {"x", "y"}