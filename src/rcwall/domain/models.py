"""Canonical V0.1 input contracts; no I/O, geometry operations or detailing engines."""

import re
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    ValidationError,
    WithJsonSchema,
    computed_field,
    model_validator,
)
from pydantic_core import PydanticCustomError

SCHEMA_VERSION = "0.1.0"
DECIMAL_PATTERN = r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$"


def _decimal(value: object) -> Decimal:
    """Reject binary floats and retain all declared decimal digits and exponent."""
    if isinstance(value, bool) or not isinstance(value, (Decimal, str, int)):
        raise PydanticCustomError("decimal_input", "Use Decimal, texto decimal o entero; no float.")
    if isinstance(value, str) and not re.fullmatch(DECIMAL_PATTERN, value):
        raise PydanticCustomError("decimal_input", "Texto decimal inválido.")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise PydanticCustomError("decimal_input", "Valor decimal inválido.") from exc
    if not number.is_finite():
        raise PydanticCustomError("finite_number", "El número debe ser finito.")
    return number


DecimalValue = Annotated[
    Decimal,
    BeforeValidator(_decimal),
    PlainSerializer(str, return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "pattern": DECIMAL_PATTERN}, mode="serialization"),
]
PositiveDecimal = Annotated[DecimalValue, Field(gt=0)]
NonnegativeDecimal = Annotated[DecimalValue, Field(ge=0)]
Identifier = Annotated[str, Field(strict=True, min_length=1, pattern=r"^\S+$")]
Text = Annotated[str, Field(strict=True, min_length=1, pattern=r"\S")]
PositiveInteger = Annotated[int, Field(strict=True, gt=0)]


class Contract(BaseModel):
    """Immutable records with immutable collections and no ignored unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")

    def reject(self, field: str, code: str, message: str) -> None:
        raise ValidationError.from_exception_data(
            type(self).__name__,
            [
                {
                    "type": PydanticCustomError(code, message),
                    "loc": (field,),
                    "input": getattr(self, field),
                }
            ],
        )


class Point2D(Contract):
    x_mm: DecimalValue
    y_mm: DecimalValue


class RectangleDefinition(Contract):
    """Axis-aligned rectangle with explicit lower-left origin in the local xy plane."""

    kind: Literal["RECTANGLE"]
    origin: Point2D
    length_mm: PositiveDecimal
    thickness_mm: PositiveDecimal


Ring = Annotated[tuple[Point2D, ...], Field(min_length=3)]


class PolygonDefinition(Contract):
    """Implicitly closed rings. Topology and winding are checked in geometry/validation."""

    kind: Literal["POLYGON"]
    outer: Ring
    holes: tuple[Ring, ...] = ()


ShapeDefinition = Annotated[RectangleDefinition | PolygonDefinition, Field(discriminator="kind")]


class GeometryDefinition(Contract):
    geometry_id: Identifier
    shape: ShapeDefinition
    description: Text | None = None


class RegionDefinition(Contract):
    region_id: Identifier
    geometry_id: Identifier
    role: Literal["BOUNDARY", "WEB", "OTHER"]
    shape: ShapeDefinition
    description: Text | None = None


class GeometricReference(Contract):
    reference_id: Identifier
    geometry_id: Identifier
    kind: Literal["LINE"]
    start: Point2D
    end: Point2D

    @model_validator(mode="after")
    def distinct_ends(self) -> Self:
        if self.start == self.end:
            self.reject("end", "zero_length_reference", "Los extremos deben ser distintos.")
        return self


class ReinforcementConfiguration(Contract):
    config_id: Identifier
    geometry_id: Identifier
    description: Text | None = None


class LinearCount(Contract):
    pattern: Literal["LINEAR_COUNT"]
    reference_id: Identifier
    quantity: PositiveInteger
    diameter_mm: PositiveDecimal
    start_offset_mm: NonnegativeDecimal
    end_offset_mm: NonnegativeDecimal
    alignment: Text | None = None


class LinearSpacing(Contract):
    pattern: Literal["LINEAR_SPACING"]
    reference_id: Identifier
    diameter_mm: PositiveDecimal
    spacing_mm: PositiveDecimal
    start_offset_mm: NonnegativeDecimal
    end_offset_mm: NonnegativeDecimal
    spacing_policy: Text
    alignment: Text


class ExplicitBar(Contract):
    bar_id: Identifier
    position: Point2D
    diameter_mm: PositiveDecimal


class ExplicitLayout(Contract):
    pattern: Literal["EXPLICIT"]
    bars: Annotated[tuple[ExplicitBar, ...], Field(min_length=1)]


DistributionDefinition = Annotated[
    LinearCount | LinearSpacing | ExplicitLayout, Field(discriminator="pattern")
]


class BarLayoutDefinition(Contract):
    layout_id: Identifier
    config_id: Identifier
    distribution: DistributionDefinition
    region_id: Identifier | None = None


class MaterialProperty(Contract):
    """User-declared property; its name/unit do not trigger any normative interpretation."""

    name: Identifier
    value: DecimalValue
    unit: Text


class MaterialSpecification(Contract):
    specification: Text
    properties: tuple[MaterialProperty, ...] = ()

    @model_validator(mode="after")
    def unique_properties(self) -> Self:
        names = [prop.name for prop in self.properties]
        if len(names) != len(set(names)):
            self.reject("properties", "duplicate_property", "Nombre de propiedad repetido.")
        return self


class SectionMaterials(Contract):
    concrete: MaterialSpecification
    reinforcement: MaterialSpecification


class SectionDefinition(Contract):
    section_id: Identifier
    geometry_id: Identifier
    config_id: Identifier
    materials: SectionMaterials
    description: Text | None = None


class WallDefinition(Contract):
    wall_id: Identifier
    description: Text | None = None


class SectionAssignment(Contract):
    assignment_id: Identifier
    wall_id: Identifier
    level_id: Identifier
    section_id: Identifier


class BentBarDefinition(Contract):
    """Unresolved declaration: no inferred path, bend radius or hook."""

    bent_bar_id: Identifier
    definition_status: Literal["UNRESOLVED"]
    diameter_mm: PositiveDecimal | None = None
    description: Text | None = None


class TransverseAssembly(Contract):
    assembly_id: Identifier
    config_id: Identifier
    definition_status: Literal["UNRESOLVED"]
    region_id: Identifier | None = None
    bent_bar_ids: tuple[Identifier, ...] = ()
    description: Text | None = None


class VerticalPlacement(Contract):
    placement_id: Identifier
    assignment_id: Identifier
    assembly_id: Identifier
    definition_status: Literal["UNRESOLVED"]
    z_start_mm: DecimalValue
    z_end_mm: DecimalValue
    spacing_mm: PositiveDecimal | None = None
    spacing_policy: Text | None = None

    @model_validator(mode="after")
    def ordered_interval(self) -> Self:
        if self.z_end_mm <= self.z_start_mm:
            self.reject("z_end_mm", "invalid_interval", "z_end_mm debe ser mayor que z_start_mm.")
        return self


class DrawingSpecification(Contract):
    drawing_id: Identifier
    section_id: Identifier
    definition_status: Literal["UNRESOLVED"]
    template_id: Identifier | None = None
    drawing_scale: PositiveDecimal | None = None


class ProjectDefinition(Contract):
    project_id: Identifier
    schema_version: Literal["0.1.0"]
    units: Literal["mm"]
    geometries: tuple[GeometryDefinition, ...] = ()
    regions: tuple[RegionDefinition, ...] = ()
    references: tuple[GeometricReference, ...] = ()
    configurations: tuple[ReinforcementConfiguration, ...] = ()
    bar_layouts: tuple[BarLayoutDefinition, ...] = ()
    sections: tuple[SectionDefinition, ...] = ()
    walls: tuple[WallDefinition, ...] = ()
    assignments: tuple[SectionAssignment, ...] = ()
    bent_bars: tuple[BentBarDefinition, ...] = ()
    transverse_assemblies: tuple[TransverseAssembly, ...] = ()
    vertical_placements: tuple[VerticalPlacement, ...] = ()
    drawings: tuple[DrawingSpecification, ...] = ()


class ValidationIssue(Contract):
    stage: Literal["types", "references", "geometry", "json"]
    path: tuple[str | int, ...]
    code: str
    description: str


class ValidationReport(Contract):
    issues: tuple[ValidationIssue, ...] = ()
    scope: Literal["DATA_ONLY_NOT_STRUCTURAL_COMPLIANCE"] = "DATA_ONLY_NOT_STRUCTURAL_COMPLIANCE"

    @computed_field
    @property
    def valid(self) -> bool:
        return not self.issues


class DetailingResult(Contract):
    """Reserved result envelope; cannot claim any resolved reinforcement geometry."""

    project_id: Identifier
    schema_version: Literal["0.1.0"]
    status: Literal["NOT_IMPLEMENTED"]


class EquivalenceResult(Contract):
    status: Literal["EQUIVALENT", "DIFFERENT", "UNDETERMINED"]
    scope: Literal["GEOMETRY", "DEFINITION", "PHYSICAL"]
    reason: str
