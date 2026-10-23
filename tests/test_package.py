"""Smoke checks against the installed distribution, without modifying sys.path."""

from importlib import import_module, metadata

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
        "rcwall.io.excel",
        "rcwall.exporters",
        "rcwall.exporters.dxf",
    ],
)
def test_public_packages_are_importable(module_name):
    assert import_module(module_name).__name__ == module_name
