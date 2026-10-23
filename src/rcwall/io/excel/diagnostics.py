"""Localized Excel diagnostics and traceable canonical paths, outside the domain."""

from dataclasses import dataclass

from rcwall.domain.models import ProjectDefinition, ValidationIssue


@dataclass(frozen=True)
class CellLocation:
    sheet: str
    row: int
    column: str


@dataclass(frozen=True)
class ExcelIssue:
    location: CellLocation
    code: str
    message: str
    canonical_path: tuple[str | int, ...] = ()

    def to_dict(self) -> dict:
        return {
            "Hoja": self.location.sheet,
            "Fila": self.location.row,
            "Columna": self.location.column,
            "Código": self.code,
            "Explicación": self.message,
        }


@dataclass(frozen=True)
class ExcelValidationReport:
    issues: tuple[ExcelIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict:
        return {
            "Válido": self.valid,
            "Alcance": "Validación de datos; no verifica cumplimiento normativo.",
            "Errores": [issue.to_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ExcelImportResult:
    project: ProjectDefinition | None
    report: ExcelValidationReport


class ExcelValidationError(ValueError):
    def __init__(self, report: ExcelValidationReport):
        self.report = report
        super().__init__(
            "\n".join(
                f"Hoja {i.location.sheet}, fila {i.location.row}, "
                f"columna {i.location.column}: {i.message}"
                for i in report.issues
            )
        )


MESSAGES = {
    "missing": "Campo obligatorio vacío para la variante seleccionada.",
    "extra_forbidden": "Dato incompatible con la variante seleccionada; deje la celda vacía.",
    "greater_than": "Se requiere un valor estrictamente positivo.",
    "greater_than_equal": "Se requiere un valor no negativo.",
    "int_type": "Se requiere una cantidad entera positiva.",
    "string_type": "Se requiere texto; no convierta identificadores en números.",
    "string_too_short": "El texto no puede estar vacío.",
    "string_pattern_mismatch": "Texto inválido: revise espacios y caracteres permitidos.",
    "literal_error": "El valor no pertenece a las opciones admitidas.",
    "union_tag_invalid": "Seleccione una de las variantes de la lista desplegable.",
    "union_tag_not_found": "Falta seleccionar la variante en la lista desplegable.",
    "too_short": "Faltan elementos: revise las filas de la hoja avanzada correspondiente.",
    "decimal_input": "Escriba un decimal como texto, con punto decimal y sin separadores de miles.",
    "decimal_parsing": "El texto no representa un número decimal válido.",
    "finite_number": "El número debe ser finito.",
    "finite_number_error": "El número debe ser finito.",
    "duplicate_id": "Identificador repetido dentro del proyecto; no se fusionan registros.",
    "missing_reference": "La referencia no corresponde a una entidad existente y válida.",
    "geometry_mismatch": "Las entidades relacionadas no pertenecen a la misma geometría.",
    "configuration_mismatch": "El estribo y la sección tienen configuraciones distintas.",
    "ambiguous_assignment": "Solo se admite una asignación por muro y nivel.",
    "duplicate_reference": "La lista repite una referencia a la misma barra doblada.",
    "duplicate_property": "El material repite un nombre de propiedad.",
    "invalid_interval": "La cota final Z debe ser mayor que la cota inicial Z.",
    "zero_length_reference": "Los extremos de la línea deben ser distintos.",
    "vertex_count": "El contorno requiere al menos tres vértices.",
    "repeated_closure": "El cierre es implícito; no repita el primer vértice al final.",
    "repeated_vertex": "El contorno contiene vértices repetidos.",
    "overlapping_edges": "El contorno retrocede sobre una arista.",
    "self_intersection": "El contorno se autointerseca o se toca a sí mismo.",
    "zero_area": "El contorno tiene área nula.",
    "invalid_orientation": "Vistos desde arriba: exterior antihorario y huecos horarios.",
    "invalid_hole": "El hueco debe estar estrictamente dentro del exterior, sin tocarlo.",
    "overlapping_holes": "Los huecos no pueden tocarse, solaparse ni anidarse.",
    "nonpositive_area": "El área neta del polígono debe ser positiva.",
}


class SourceMap:
    """Paths refer to reconstructed array indices; cells retain physical row numbers."""

    def __init__(self):
        self.cells: dict[tuple, CellLocation] = {}

    def locate(self, path: tuple) -> CellLocation:
        # Pydantic union error paths insert discriminator values, not data keys.
        clean = tuple(
            p
            for p in path
            if p not in ("RECTANGLE", "POLYGON", "LINEAR_COUNT", "LINEAR_SPACING", "EXPLICIT")
        )
        candidate = clean
        while candidate:
            if candidate in self.cells:
                return self.cells[candidate]
            candidate = candidate[:-1]
        return CellLocation("Proyecto", 7, "ID de proyecto")

    def translate(self, issue: ValidationIssue) -> ExcelIssue:
        message = MESSAGES.get(
            issue.code, "El dato no cumple el contrato canónico; revise el campo indicado."
        )
        if issue.code == "missing" and issue.path[-1:] == ("quantity",):
            message = "La distribución por cantidad requiere un número entero positivo."
        return ExcelIssue(self.locate(issue.path), issue.code, message, issue.path)
