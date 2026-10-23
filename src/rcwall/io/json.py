"""Versioned JSON boundary with exact decimals, duplicate-key rejection and full validation."""

import json
from decimal import Decimal
from pathlib import Path

from rcwall.domain.models import (
    SCHEMA_VERSION,
    ProjectDefinition,
    ValidationIssue,
    ValidationReport,
)
from rcwall.validation.project import ValidationOutcome, validate_definition


class ProjectValidationError(ValueError):
    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__("; ".join(f"{i.code} en {i.path}: {i.description}" for i in report.issues))


class _DuplicateKey(ValueError):
    pass


def _object_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateKey(f"Clave JSON repetida: {key!r}.")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError(f"Constante JSON no finita: {value}.")


def validate_json(text: str) -> ValidationOutcome:
    try:
        data = json.loads(
            text,
            parse_float=Decimal,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_pairs,
        )
    except (ValueError, TypeError) as exc:
        code = "duplicate_json_key" if isinstance(exc, _DuplicateKey) else "invalid_json"
        issue = ValidationIssue(stage="json", path=(), code=code, description=str(exc))
        return ValidationOutcome(None, ValidationReport(issues=(issue,)))
    return validate_definition(data)


def loads_project(text: str) -> ProjectDefinition:
    outcome = validate_json(text)
    if outcome.project is None:
        raise ProjectValidationError(outcome.report)
    return outcome.project


def dumps_project(project: ProjectDefinition) -> str:
    outcome = validate_definition(project)
    if outcome.project is None:
        raise ProjectValidationError(outcome.report)
    return (
        json.dumps(
            outcome.project.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def read_project(path: str | Path) -> ProjectDefinition:
    return loads_project(Path(path).read_text(encoding="utf-8"))


def write_project(project: ProjectDefinition, path: str | Path) -> None:
    # Validate/serialize before opening the destination, so invalid data cannot truncate it.
    text = dumps_project(project)
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def project_json_schema() -> dict:
    schema = ProjectDefinition.model_json_schema(mode="serialization")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:rcwall:project-definition:{SCHEMA_VERSION}"
    schema["$comment"] = (
        "Canonical decimals are strings. Numeric bounds, references and topology additionally "
        "require rcwall.validation.validate_definition; schema validation is not design compliance."
    )
    return schema


def write_project_schema(path: str | Path) -> None:
    text = json.dumps(project_json_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    Path(path).write_text(text, encoding="utf-8", newline="\n")
