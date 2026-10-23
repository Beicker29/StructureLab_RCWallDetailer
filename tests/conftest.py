"""Shared declared-input fixtures, independent of any detailing algorithm."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_data():
    path = Path(__file__).resolve().parents[1] / "examples" / "project_v0_1.json"
    return json.loads(path.read_text(encoding="utf-8"))
