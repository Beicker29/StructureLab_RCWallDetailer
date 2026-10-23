import json
from decimal import Decimal
from pathlib import Path

import pytest

from rcwall.domain.models import ProjectDefinition
from rcwall.io.json import (
    ProjectValidationError,
    dumps_project,
    loads_project,
    project_json_schema,
    read_project,
    validate_json,
    write_project,
)


def test_reproducible_json_roundtrip(project_data):
    project = ProjectDefinition.model_validate(project_data)
    serialized = dumps_project(project)
    reconstructed = loads_project(serialized)
    assert reconstructed == project
    assert dumps_project(reconstructed) == serialized
    assert (
        reconstructed.geometries[0].shape.length_mm.as_tuple()
        == project.geometries[0].shape.length_mm.as_tuple()
    )


def test_json_numeric_tokens_are_parsed_without_binary_float(project_data):
    value = "3000.12345678901234567890123456789000"
    project_data["geometries"][0]["shape"]["length_mm"] = value
    text = json.dumps(project_data).replace('"' + value + '"', value)
    project = loads_project(text)
    assert project.geometries[0].shape.length_mm.as_tuple() == Decimal(value).as_tuple()
    assert json.loads(dumps_project(project))["geometries"][0]["shape"]["length_mm"] == value


def test_invalid_data_cannot_truncate_destination(project_data, tmp_path):
    path = tmp_path / "project.json"
    project = ProjectDefinition.model_validate(project_data)
    write_project(project, path)
    before = path.read_bytes()
    bad = project.model_copy(update={"schema_version": "9.0.0"})
    with pytest.raises(ProjectValidationError):
        write_project(bad, path)
    assert path.read_bytes() == before
    assert read_project(path) == project


@pytest.mark.parametrize(
    "text", ['{"project_id": "A", "project_id": "B"}', '{"x": NaN}', "{", "[]"]
)
def test_bad_json_is_diagnosed(text):
    outcome = validate_json(text)
    assert outcome.project is None
    assert not outcome.report.valid


def test_duplicate_nested_json_keys_are_rejected():
    result = validate_json('{"nested": {"x": 1, "x": 2}}')
    assert result.report.issues[0].code == "duplicate_json_key"


def test_unknown_version_has_no_hypothetical_migration(project_data):
    project_data["schema_version"] = "0.0.1"
    with pytest.raises(ProjectValidationError) as error:
        loads_project(json.dumps(project_data))
    assert error.value.report.issues[0].path == ("schema_version",)


def test_generated_schema_is_synchronized_and_uses_decimal_strings():
    path = Path(__file__).resolve().parents[1] / "schemas" / "project_definition-0.1.0.schema.json"
    schema = project_json_schema()
    assert json.loads(path.read_text(encoding="utf-8")) == schema
    assert schema["$defs"]["RectangleDefinition"]["properties"]["length_mm"]["type"] == "string"
    assert (
        schema["$defs"]["BarLayoutDefinition"]["properties"]["distribution"]["discriminator"][
            "propertyName"
        ]
        == "pattern"
    )
    assert schema["additionalProperties"] is False


def test_example_is_valid_canonical_json():
    path = Path(__file__).resolve().parents[1] / "examples" / "project_v0_1.json"
    assert dumps_project(read_project(path)) == path.read_text(encoding="utf-8")
