from copy import deepcopy
from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from rcwall.domain.models import ProjectDefinition
from rcwall.validation import validate_definition


def test_rectangle_and_reuse(project_data):
    outcome = validate_definition(project_data)
    assert outcome.report.valid
    project = outcome.project
    assert len(project.configurations) == 1
    assert project.sections[0].config_id == project.sections[1].config_id
    assert project.assignments[0].section_id == project.assignments[2].section_id
    assert project.assignments[0].wall_id == project.assignments[1].wall_id
    assert project.assignments[0].section_id != project.assignments[1].section_id


@pytest.mark.parametrize("invalid", ["0", "-0.01", "NaN", "Infinity", " 1 ", True, 1.1])
def test_invalid_dimensions_are_type_errors(project_data, invalid):
    project_data["geometries"][0]["shape"]["length_mm"] = invalid
    outcome = validate_definition(project_data)
    assert outcome.project is None
    assert any(i.stage == "types" and i.path[-1] == "length_mm" for i in outcome.report.issues)


def test_global_id_namespace(project_data):
    project_data["walls"][0]["wall_id"] = "G1"
    report = validate_definition(project_data).report
    issue = next(i for i in report.issues if i.code == "duplicate_id")
    assert issue.path == ("walls", 0, "wall_id")


def test_duplicate_entity_is_not_merged(project_data):
    project_data["configurations"].append(deepcopy(project_data["configurations"][0]))
    outcome = validate_definition(project_data)
    assert outcome.project is None
    assert "duplicate_id" in {i.code for i in outcome.report.issues}


@pytest.mark.parametrize(
    ("collection", "field"),
    [
        ("references", "geometry_id"),
        ("configurations", "geometry_id"),
        ("bar_layouts", "config_id"),
        ("sections", "geometry_id"),
        ("sections", "config_id"),
        ("assignments", "wall_id"),
        ("assignments", "section_id"),
    ],
)
def test_missing_reference_localization(project_data, collection, field):
    project_data[collection][0][field] = "MISSING"
    outcome = validate_definition(project_data)
    assert any(
        i.code == "missing_reference" and i.path == (collection, 0, field)
        for i in outcome.report.issues
    )


def test_incompatible_section_configuration(project_data):
    other = deepcopy(project_data["geometries"][0])
    other["geometry_id"] = "G2"
    project_data["geometries"].append(other)
    project_data["sections"][1]["geometry_id"] = "G2"
    outcome = validate_definition(project_data)
    assert any(
        i.code == "geometry_mismatch" and i.path == ("sections", 1, "config_id")
        for i in outcome.report.issues
    )


def test_incompatible_layout_region_and_reference(project_data):
    other = deepcopy(project_data["geometries"][0])
    other["geometry_id"] = "G2"
    project_data["geometries"].append(other)
    project_data["regions"] = [
        {"region_id": "R2", "geometry_id": "G2", "role": "WEB", "shape": other["shape"]}
    ]
    project_data["bar_layouts"][0]["region_id"] = "R2"
    project_data["references"][0]["geometry_id"] = "G2"
    report = validate_definition(project_data).report
    assert sum(i.code == "geometry_mismatch" for i in report.issues) == 2


def test_ambiguous_wall_level_is_rejected(project_data):
    project_data["assignments"][1]["level_id"] = "L1"
    assert "ambiguous_assignment" in {
        i.code for i in validate_definition(project_data).report.issues
    }


@pytest.mark.parametrize("pattern", ["LINEAR_COUNT", "LINEAR_SPACING", "EXPLICIT"])
def test_distribution_variants(project_data, pattern):
    distribution = project_data["bar_layouts"][0]["distribution"]
    if pattern == "LINEAR_SPACING":
        distribution.pop("quantity")
        distribution.update(
            pattern=pattern,
            spacing_mm="150.25",
            spacing_policy="DECLARED-EXACT",
            alignment="DECLARED-START",
        )
    elif pattern == "EXPLICIT":
        project_data["bar_layouts"][0]["distribution"] = {
            "pattern": pattern,
            "bars": [
                {"bar_id": "B1", "position": {"x_mm": "10", "y_mm": "20"}, "diameter_mm": "12.5"}
            ],
        }
    result = validate_definition(project_data)
    assert result.report.valid
    assert result.project.bar_layouts[0].distribution.pattern == pattern


@pytest.mark.parametrize(
    "field", ["quantity", "reference_id", "diameter_mm", "start_offset_mm", "end_offset_mm"]
)
def test_linear_count_requires_known_parameters(project_data, field):
    project_data["bar_layouts"][0]["distribution"].pop(field)
    assert not validate_definition(project_data).report.valid


@pytest.mark.parametrize("quantity", [0, -1, 2.5, True, "6"])
def test_quantity_requires_positive_integer(project_data, quantity):
    project_data["bar_layouts"][0]["distribution"]["quantity"] = quantity
    assert not validate_definition(project_data).report.valid


def test_contradictory_pattern_parameters(project_data):
    project_data["bar_layouts"][0]["distribution"]["spacing_mm"] = "100"
    assert any(i.code == "extra_forbidden" for i in validate_definition(project_data).report.issues)


def test_explicit_requires_bars_and_rejects_linear_parameters(project_data):
    project_data["bar_layouts"][0]["distribution"] = {
        "pattern": "EXPLICIT",
        "bars": [],
        "quantity": 3,
    }
    codes = {i.code for i in validate_definition(project_data).report.issues}
    assert {"too_short", "extra_forbidden"} <= codes


def test_decimal_digits_are_not_limited_by_context(project_data):
    value = "3000.12345678901234567890123456789012345678900"
    project_data["geometries"][0]["shape"]["length_mm"] = value
    with localcontext() as context:
        context.prec = 6
        result = validate_definition(project_data)
        assert result.report.valid
        actual = result.project.geometries[0].shape.length_mm
        assert actual.as_tuple() == Decimal(value).as_tuple()


def test_immutable_models_and_collections(project_data):
    project = ProjectDefinition.model_validate(project_data)
    assert isinstance(project.geometries, tuple)
    with pytest.raises(ValidationError):
        project.units = "m"
    bad = project.model_copy(update={"units": "m"})
    assert not validate_definition(bad).report.valid


def test_duplicate_material_properties_rejected(project_data):
    prop = {"name": "declared_strength", "value": "30", "unit": "MPa"}
    project_data["sections"][0]["materials"]["concrete"]["properties"] = [prop, prop]
    assert "duplicate_property" in {i.code for i in validate_definition(project_data).report.issues}


def test_structured_report_exposes_scope_and_validity(project_data):
    project_data["units"] = "cm"
    payload = validate_definition(project_data).report.model_dump(mode="json")
    assert payload["valid"] is False
    assert payload["scope"] == "DATA_ONLY_NOT_STRUCTURAL_COMPLIANCE"
    assert {"stage", "path", "code", "description"} <= payload["issues"][0].keys()
