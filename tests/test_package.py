"""Smoke checks against the installed distribution, without modifying sys.path."""

from importlib import import_module, metadata, util

import pytest


def test_installed_distribution():
    distribution = metadata.distribution("structurelab-rcwalldetailer")
    assert distribution.version
    assert distribution.metadata["Requires-Python"] == ">=3.11"


@pytest.mark.parametrize(
    "module_name",
    [
        "rcwall",
        "rcwall.domain",
        "rcwall.geometry",
        "rcwall.detailing",
        "rcwall.validation",
        "rcwall.io",
        "rcwall.exporters",
        "rcwall.exporters.dxf",
    ],
)
def test_public_packages_are_importable(module_name):
    assert import_module(module_name).__name__ == module_name


def test_excel_adapter_is_not_distributed_or_required():
    assert util.find_spec("rcwall.io.excel") is None
    requirements = metadata.requires("structurelab-rcwalldetailer") or []
    assert not any("openpyxl" in requirement.lower() for requirement in requirements)
