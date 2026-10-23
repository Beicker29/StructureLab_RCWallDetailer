"""Type, reference and geometry validation with distinct diagnostic stages."""

from dataclasses import dataclass

from pydantic import ValidationError

from rcwall.domain.models import (
    ExplicitLayout,
    ProjectDefinition,
    ValidationIssue,
    ValidationReport,
)
from rcwall.geometry.polygons import validate_shape

ENTITY_KEYS = {
    "geometries": "geometry_id",
    "regions": "region_id",
    "references": "reference_id",
    "configurations": "config_id",
    "bar_layouts": "layout_id",
    "sections": "section_id",
    "walls": "wall_id",
    "assignments": "assignment_id",
    "bent_bars": "bent_bar_id",
    "transverse_assemblies": "assembly_id",
    "vertical_placements": "placement_id",
    "drawings": "drawing_id",
}


@dataclass(frozen=True)
class ValidationOutcome:
    project: ProjectDefinition | None
    report: ValidationReport


def type_issues(error: ValidationError) -> tuple[ValidationIssue, ...]:
    return tuple(
        ValidationIssue(
            stage="types", path=tuple(item["loc"]), code=item["type"], description=item["msg"]
        )
        for item in error.errors(include_url=False)
    )


def validate_references(project: ProjectDefinition) -> tuple[ValidationIssue, ...]:
    """ID-01 uses one project-wide namespace, including IDs of explicitly declared bars."""
    issues = []
    seen = {project.project_id: ("project_id",)}
    indexes = {}

    def issue(path, code, description):
        issues.append(
            ValidationIssue(stage="references", path=path, code=code, description=description)
        )

    def register(identifier, path):
        if identifier in seen:
            issue(path, "duplicate_id", f"ID {identifier!r} ya declarado en {seen[identifier]}.")
        else:
            seen[identifier] = path

    for collection, field in ENTITY_KEYS.items():
        indexes[collection] = {}
        for i, entity in enumerate(getattr(project, collection)):
            identifier = getattr(entity, field)
            register(identifier, (collection, i, field))
            indexes[collection].setdefault(identifier, entity)
            if collection == "bar_layouts" and isinstance(entity.distribution, ExplicitLayout):
                for j, bar in enumerate(entity.distribution.bars):
                    register(bar.bar_id, (collection, i, "distribution", "bars", j, "bar_id"))

    def lookup(identifier, target, path):
        if identifier is None:
            return None
        entity = indexes[target].get(identifier)
        if entity is None:
            issue(path, "missing_reference", f"No existe {identifier!r} en {target}.")
        return entity

    for collection in ("regions", "references", "configurations"):
        for i, entity in enumerate(getattr(project, collection)):
            lookup(entity.geometry_id, "geometries", (collection, i, "geometry_id"))

    for collection in ("bar_layouts", "transverse_assemblies"):
        for i, entity in enumerate(getattr(project, collection)):
            prefix = (collection, i)
            config = lookup(entity.config_id, "configurations", prefix + ("config_id",))
            region = lookup(entity.region_id, "regions", prefix + ("region_id",))
            if config and region and config.geometry_id != region.geometry_id:
                issue(
                    prefix + ("region_id",),
                    "geometry_mismatch",
                    "Región y configuración pertenecen a geometrías distintas.",
                )
            if collection == "bar_layouts" and not isinstance(entity.distribution, ExplicitLayout):
                path = prefix + ("distribution", "reference_id")
                reference = lookup(entity.distribution.reference_id, "references", path)
                if config and reference and config.geometry_id != reference.geometry_id:
                    issue(
                        path,
                        "geometry_mismatch",
                        "Referencia y configuración pertenecen a geometrías distintas.",
                    )
            if collection == "transverse_assemblies":
                if len(set(entity.bent_bar_ids)) != len(entity.bent_bar_ids):
                    issue(
                        prefix + ("bent_bar_ids",),
                        "duplicate_reference",
                        "Una barra no puede referenciarse dos veces en el mismo conjunto.",
                    )
                for j, bar_id in enumerate(entity.bent_bar_ids):
                    lookup(bar_id, "bent_bars", prefix + ("bent_bar_ids", j))

    for i, section in enumerate(project.sections):
        lookup(section.geometry_id, "geometries", ("sections", i, "geometry_id"))
        config = lookup(section.config_id, "configurations", ("sections", i, "config_id"))
        if config and config.geometry_id != section.geometry_id:
            issue(
                ("sections", i, "config_id"),
                "geometry_mismatch",
                "La configuración debe referenciar la misma geometría que la sección.",
            )

    assignments = set()
    for i, assignment in enumerate(project.assignments):
        lookup(assignment.wall_id, "walls", ("assignments", i, "wall_id"))
        lookup(assignment.section_id, "sections", ("assignments", i, "section_id"))
        key = assignment.wall_id, assignment.level_id
        if key in assignments:
            issue(
                ("assignments", i, "level_id"),
                "ambiguous_assignment",
                "V0.1 admite una sola asignación por muro y nivel; subdivisiones pendientes.",
            )
        assignments.add(key)

    for i, placement in enumerate(project.vertical_placements):
        prefix = ("vertical_placements", i)
        assignment = lookup(placement.assignment_id, "assignments", prefix + ("assignment_id",))
        assembly = lookup(placement.assembly_id, "transverse_assemblies", prefix + ("assembly_id",))
        section = indexes["sections"].get(assignment.section_id) if assignment else None
        if section and assembly and section.config_id != assembly.config_id:
            issue(
                prefix + ("assembly_id",),
                "configuration_mismatch",
                "El conjunto no corresponde a la configuración de la sección asignada.",
            )

    for i, drawing in enumerate(project.drawings):
        lookup(drawing.section_id, "sections", ("drawings", i, "section_id"))
    return tuple(issues)


def validate_geometry(project: ProjectDefinition) -> tuple[ValidationIssue, ...]:
    issues = []
    for collection in ("geometries", "regions"):
        for i, entity in enumerate(getattr(project, collection)):
            issues.extend(validate_shape(entity.shape, (collection, i, "shape")))
    return tuple(issues)


def validate_definition(data: object) -> ValidationOutcome:
    """Full entry point. Invalid data never produces an accepted project.

    Models enforce local field contracts; graph and topology require this pipeline.
    Reconstructing model input also catches unchecked model_copy/model_construct data.
    """
    if isinstance(data, ProjectDefinition):
        data = data.model_dump(mode="python", warnings=False)
    try:
        project = ProjectDefinition.model_validate(data)
    except ValidationError as exc:
        return ValidationOutcome(None, ValidationReport(issues=type_issues(exc)))
    report = ValidationReport(issues=validate_references(project) + validate_geometry(project))
    return ValidationOutcome(project if report.valid else None, report)


def validate_project(project: ProjectDefinition) -> ValidationReport:
    return validate_definition(project).report
