from copy import deepcopy

import pytest

from rcwall.domain.models import ProjectDefinition
from rcwall.validation.equivalence import (
    compare_section_definitions,
    compare_section_physical_equivalence,
)


def compare(data):
    return compare_section_definitions(ProjectDefinition.model_validate(data), "S1", "S2")


def separate_configuration(data):
    data["configurations"].append({"config_id": "C2", "geometry_id": "G1"})
    second = deepcopy(data["bar_layouts"][0])
    second.update(layout_id="LAYOUT2", config_id="C2")
    data["bar_layouts"].append(second)
    data["sections"][1]["config_id"] = "C2"
    return second["distribution"]


def test_equivalent_sections_keep_both_identities(project_data):
    before = deepcopy(project_data)
    assert compare(project_data).status == "EQUIVALENT"
    assert project_data == before
    assert len(project_data["sections"]) == 2


def test_configuration_identity_does_not_define_equivalence(project_data):
    separate_configuration(project_data)
    assert compare(project_data).status == "EQUIVALENT"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", 7),
        ("diameter_mm", "16.00000000000000000000000001"),
        ("start_offset_mm", "0.00000000000000000000000001"),
        ("alignment", "DECLARED-END"),
    ],
)
def test_different_reinforcement_produces_different_definition(project_data, field, value):
    distribution = separate_configuration(project_data)
    distribution[field] = value
    assert compare(project_data).status == "DIFFERENT"


@pytest.mark.parametrize("material", ["concrete", "reinforcement"])
def test_different_material_specifications(project_data, material):
    project_data["sections"][1]["materials"][material]["specification"] = "OTHER-DECLARED-SPEC"
    assert compare(project_data).status == "DIFFERENT"


def test_material_property_difference_and_order(project_data):
    props = [
        {"name": "p1", "value": "1.000", "unit": "declared-unit"},
        {"name": "p2", "value": "2", "unit": "declared-unit"},
    ]
    project_data["sections"][0]["materials"]["concrete"]["properties"] = props
    project_data["sections"][1]["materials"]["concrete"]["properties"] = list(
        reversed(deepcopy(props))
    )
    assert compare(project_data).status == "EQUIVALENT"
    project_data["sections"][1]["materials"]["concrete"]["properties"][0]["value"] = (
        "2.0000000000000000001"
    )
    assert compare(project_data).status == "DIFFERENT"


def test_same_dimensions_at_different_local_positions_differ(project_data):
    geometry = deepcopy(project_data["geometries"][0])
    geometry["geometry_id"] = "G2"
    geometry["shape"]["origin"]["x_mm"] = "1"
    project_data["geometries"].append(geometry)
    project_data["configurations"].append({"config_id": "C2", "geometry_id": "G2"})
    project_data["sections"][1].update(geometry_id="G2", config_id="C2")
    assert compare(project_data).status == "DIFFERENT"


def test_physical_equivalence_is_not_claimed(project_data):
    project = ProjectDefinition.model_validate(project_data)
    result = compare_section_physical_equivalence(project, "S1", "S1")
    assert result.status == "UNDETERMINED"
    assert result.scope == "PHYSICAL"


def test_unresolved_transverse_semantics_prevent_equivalence_claim(project_data):
    project_data["transverse_assemblies"] = [
        {"assembly_id": "T1", "config_id": "C1", "definition_status": "UNRESOLVED"}
    ]
    assert compare(project_data).status == "UNDETERMINED"


def test_equivalence_rejects_invalid_project(project_data):
    project_data["sections"][0]["config_id"] = "MISSING"
    with pytest.raises(ValueError, match="Proyecto inválido"):
        compare(project_data)


def test_different_declared_transverse_diameters_are_known_differences(project_data):
    separate_configuration(project_data)
    project_data["bent_bars"] = [
        {"bent_bar_id": "BB1", "diameter_mm": "8", "definition_status": "UNRESOLVED"},
        {"bent_bar_id": "BB2", "diameter_mm": "10", "definition_status": "UNRESOLVED"},
    ]
    project_data["transverse_assemblies"] = [
        {
            "assembly_id": "T1",
            "config_id": "C1",
            "bent_bar_ids": ["BB1"],
            "definition_status": "UNRESOLVED",
        },
        {
            "assembly_id": "T2",
            "config_id": "C2",
            "bent_bar_ids": ["BB2"],
            "definition_status": "UNRESOLVED",
        },
    ]
    assert compare(project_data).status == "DIFFERENT"


def test_adding_transverse_declaration_changes_definition(project_data):
    separate_configuration(project_data)
    project_data["transverse_assemblies"] = [
        {"assembly_id": "T1", "config_id": "C1", "definition_status": "UNRESOLVED"}
    ]
    assert compare(project_data).status == "DIFFERENT"
