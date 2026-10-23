"""Comparisons of supported definitions, never automatic identity changes or merging."""

from fractions import Fraction

from rcwall.domain.models import (
    EquivalenceResult,
    ExplicitLayout,
    LinearCount,
    MaterialSpecification,
    ProjectDefinition,
)
from rcwall.geometry.polygons import point, shape_key
from rcwall.validation.project import validate_project


def _material_key(material: MaterialSpecification) -> tuple:
    return material.specification, tuple(
        sorted((prop.name, Fraction(prop.value), prop.unit) for prop in material.properties)
    )


def _configuration_key(project: ProjectDefinition, config_id: str) -> tuple:
    references = {r.reference_id: r for r in project.references}
    regions = {r.region_id: r for r in project.regions}
    layouts = []
    for layout in project.bar_layouts:
        if layout.config_id != config_id:
            continue
        region = regions.get(layout.region_id)
        region_key = (region.role, shape_key(region.shape)) if region else ()
        distribution = layout.distribution
        if isinstance(distribution, ExplicitLayout):
            parameters = tuple(
                sorted(
                    (point(bar.position), Fraction(bar.diameter_mm)) for bar in distribution.bars
                )
            )
        else:
            reference = references[distribution.reference_id]
            common = (
                point(reference.start),
                point(reference.end),
                Fraction(distribution.diameter_mm),
                Fraction(distribution.start_offset_mm),
                Fraction(distribution.end_offset_mm),
            )
            if isinstance(distribution, LinearCount):
                parameters = common + (distribution.quantity, distribution.alignment or "")
            else:
                parameters = common + (
                    Fraction(distribution.spacing_mm),
                    distribution.spacing_policy,
                    distribution.alignment,
                )
        layouts.append((distribution.pattern, region_key, parameters))
    return tuple(sorted(layouts))


def _transverse_key(project: ProjectDefinition, config_id: str) -> tuple:
    """Only declared membership, region and diameter; never infer an unresolved path."""
    bars = {bar.bent_bar_id: bar for bar in project.bent_bars}
    regions = {region.region_id: region for region in project.regions}
    assemblies = []
    for assembly in project.transverse_assemblies:
        if assembly.config_id != config_id:
            continue
        region = regions.get(assembly.region_id)
        region_key = (region.role, shape_key(region.shape)) if region else ()
        diameters = []
        for identifier in assembly.bent_bar_ids:
            diameter = bars[identifier].diameter_mm
            diameters.append((False,) if diameter is None else (True, Fraction(diameter)))
        assemblies.append((region_key, tuple(sorted(diameters))))
    return tuple(sorted(assemblies))


def compare_section_definitions(
    project: ProjectDefinition, left_section_id: str, right_section_id: str
) -> EquivalenceResult:
    """Compare declared geometry, materials and known reinforcement data within a project.

    IDs/labels and ordering of independent layouts/bars are not structural values.
    Reference direction, policy text and all declared dimensions are significant.
    Transverse definitions remain unresolved and cannot yield EQUIVALENT here.
    """
    report = validate_project(project)
    if not report.valid:
        raise ValueError(f"Proyecto inválido: {report.issues[0].code}")
    sections = {section.section_id: section for section in project.sections}
    try:
        left, right = sections[left_section_id], sections[right_section_id]
    except KeyError as exc:
        raise ValueError(f"Sección inexistente: {exc.args[0]}") from exc
    geometries = {geometry.geometry_id: geometry for geometry in project.geometries}

    def result(status, reason):
        return EquivalenceResult(status=status, scope="DEFINITION", reason=reason)

    if shape_key(geometries[left.geometry_id].shape) != shape_key(
        geometries[right.geometry_id].shape
    ):
        return result("DIFFERENT", "La geometría local declarada es diferente.")
    for material in ("concrete", "reinforcement"):
        if _material_key(getattr(left.materials, material)) != _material_key(
            getattr(right.materials, material)
        ):
            return result("DIFFERENT", "Las especificaciones de materiales son diferentes.")
    if _configuration_key(project, left.config_id) != _configuration_key(project, right.config_id):
        return result("DIFFERENT", "Las instrucciones longitudinales son diferentes.")
    if _transverse_key(project, left.config_id) != _transverse_key(project, right.config_id):
        return result("DIFFERENT", "Los datos transversales declarados son diferentes.")
    if any(a.config_id in (left.config_id, right.config_id) for a in project.transverse_assemblies):
        return result(
            "UNDETERMINED", "La semántica de los conjuntos transversales aún no está resuelta."
        )
    return result(
        "EQUIVALENT", "Coinciden las definiciones soportadas; se conservan ambas identidades."
    )


def compare_section_physical_equivalence(
    project: ProjectDefinition, left_section_id: str, right_section_id: str
) -> EquivalenceResult:
    """Explicitly unavailable until resolved reinforcement geometry exists."""
    if not validate_project(project).valid:
        raise ValueError("El proyecto debe superar la validación de datos.")
    ids = {section.section_id for section in project.sections}
    if left_section_id not in ids or right_section_id not in ids:
        raise ValueError("Sección inexistente.")
    return EquivalenceResult(
        status="UNDETERMINED",
        scope="PHYSICAL",
        reason="No existe geometría de refuerzo resuelta en V0.1.",
    )
