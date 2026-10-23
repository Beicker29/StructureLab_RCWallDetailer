from copy import deepcopy

import pytest

from rcwall.io.json import dumps_project, loads_project
from rcwall.validation import validate_definition


def with_reserved(data):
    data["bent_bars"] = [
        {"bent_bar_id": "BB1", "diameter_mm": "8.00", "definition_status": "UNRESOLVED"}
    ]
    data["transverse_assemblies"] = [
        {
            "assembly_id": "T1",
            "config_id": "C1",
            "bent_bar_ids": ["BB1"],
            "definition_status": "UNRESOLVED",
        }
    ]
    data["vertical_placements"] = [
        {
            "placement_id": "V1",
            "assignment_id": "A1",
            "assembly_id": "T1",
            "z_start_mm": "-3000",
            "z_end_mm": "0",
            "spacing_mm": "150",
            "spacing_policy": "PENDING-POLICY",
            "definition_status": "UNRESOLVED",
        }
    ]
    data["drawings"] = [
        {
            "drawing_id": "D1",
            "section_id": "S1",
            "template_id": "EXTERNAL-TEMPLATE",
            "drawing_scale": "25",
            "definition_status": "UNRESOLVED",
        }
    ]
    return data


def test_reserved_definitions_roundtrip_without_resolution(project_data):
    result = validate_definition(with_reserved(project_data))
    assert result.report.valid
    restored = loads_project(dumps_project(result.project))
    assert restored == result.project
    assert restored.bent_bars[0].definition_status == "UNRESOLVED"
    assert not hasattr(restored.bent_bars[0], "resolved_path")


@pytest.mark.parametrize(
    ("collection", "field"),
    [
        ("transverse_assemblies", "config_id"),
        ("vertical_placements", "assignment_id"),
        ("vertical_placements", "assembly_id"),
        ("drawings", "section_id"),
    ],
)
def test_reserved_references_are_checked(project_data, collection, field):
    with_reserved(project_data)[collection][0][field] = "MISSING"
    assert any(
        i.code == "missing_reference" and i.path == (collection, 0, field)
        for i in validate_definition(project_data).report.issues
    )


def test_bent_bar_membership_and_vertical_compatibility(project_data):
    with_reserved(project_data)
    project_data["transverse_assemblies"][0]["bent_bar_ids"] = ["MISSING"]
    project_data["configurations"].append({"config_id": "C2", "geometry_id": "G1"})
    project_data["transverse_assemblies"][0]["config_id"] = "C2"
    codes = {i.code for i in validate_definition(project_data).report.issues}
    assert {"missing_reference", "configuration_mismatch"} <= codes


def test_bent_bar_duplicate_membership_is_rejected(project_data):
    with_reserved(project_data)["transverse_assemblies"][0]["bent_bar_ids"] = ["BB1", "BB1"]
    assert "duplicate_reference" in {
        i.code for i in validate_definition(project_data).report.issues
    }


def test_reserved_contract_cannot_claim_resolution_or_arbitrary_geometry(project_data):
    with_reserved(project_data)["bent_bars"][0].update(definition_status="RESOLVED", radius_mm="50")
    codes = {i.code for i in validate_definition(project_data).report.issues}
    assert {"literal_error", "extra_forbidden"} <= codes


def test_invalid_vertical_interval(project_data):
    with_reserved(project_data)["vertical_placements"][0]["z_end_mm"] = "-3000"
    report = validate_definition(project_data).report
    assert any(
        i.code == "invalid_interval" and i.path == ("vertical_placements", 0, "z_end_mm")
        for i in report.issues
    )


@pytest.mark.parametrize("field", ["spacing_mm", "spacing_policy", "alignment"])
def test_spacing_fields_are_required(project_data, field):
    project_data["bar_layouts"][0]["distribution"] = {
        "pattern": "LINEAR_SPACING",
        "reference_id": "REF1",
        "diameter_mm": "12",
        "start_offset_mm": "0",
        "end_offset_mm": "0",
        "spacing_mm": "100",
        "spacing_policy": "USER-POLICY",
        "alignment": "USER-ALIGNMENT",
    }
    project_data["bar_layouts"][0]["distribution"].pop(field)
    assert not validate_definition(project_data).report.valid


def test_explicit_bar_ids_are_globally_unique(project_data):
    bar = {"bar_id": "B1", "position": {"x_mm": "1", "y_mm": "1"}, "diameter_mm": "12"}
    project_data["bar_layouts"][0]["distribution"] = {
        "pattern": "EXPLICIT",
        "bars": [bar, deepcopy(bar)],
    }
    assert any(
        i.code == "duplicate_id" and i.path[-3:] == ("bars", 1, "bar_id")
        for i in validate_definition(project_data).report.issues
    )


def test_zero_length_reference_and_nonfinite_coordinates(project_data):
    project_data["references"][0]["end"] = project_data["references"][0]["start"]
    assert "zero_length_reference" in {
        i.code for i in validate_definition(project_data).report.issues
    }
    project_data["references"][0]["start"]["x_mm"] = "Infinity"
    assert not validate_definition(project_data).report.valid
