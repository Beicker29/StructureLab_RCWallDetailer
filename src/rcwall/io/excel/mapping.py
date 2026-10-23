"""Explicit Spanish presentation map. Canonical fields and enumerations are unchanged."""

from dataclasses import dataclass
from typing import Literal

from rcwall.domain import models as m

HEADER_ROW = 6
FIRST_DATA_ROW = 7
MAX_NATIVE_INTEGER = 999_999_999_999_999

SHAPES = {"RECTANGLE": "Rectángulo", "POLYGON": "Polígono"}
ROLES = {"BOUNDARY": "Borde", "WEB": "Alma", "OTHER": "Otro"}
PATTERNS = {
    "LINEAR_COUNT": "Distribución por cantidad",
    "LINEAR_SPACING": "Distribución por separación",
    "EXPLICIT": "Distribución explícita",
}
STATUS = {"UNRESOLVED": "Pendiente de definir"}
OWNERS = {"geometries": "Geometría", "regions": "Región"}
LOOPS = {"outer": "Exterior", "holes": "Hueco"}
MATERIALS = {"concrete": "Concreto", "reinforcement": "Acero"}


@dataclass(frozen=True)
class Column:
    field: str
    header: str
    kind: Literal["text", "decimal", "integer"] = "text"
    requirement: Literal["required", "optional", "conditional"] = "required"
    choices: dict[str, str] | None = None
    help: str = ""

    @property
    def path(self) -> tuple[str, ...]:
        return tuple(self.field.split("."))


@dataclass(frozen=True)
class Sheet:
    name: str
    collection: str
    model: type[m.Contract] | None
    columns: tuple[Column, ...]
    instructions: str
    advanced: bool = False


def c(field, header, kind="text", requirement="required", choices=None, help=""):
    return Column(field, header, kind, requirement, choices, help)


DESCRIPTION = c("description", "Descripción", requirement="optional")
STATE = c(
    "definition_status",
    "Estado de definición",
    choices=STATUS,
    help="Conserve «Pendiente de definir». No hay geometría calculada.",
)
SHAPE_COLUMNS = (
    c("shape.kind", "Tipo de geometría", choices=SHAPES),
    c("shape.origin.x_mm", "Origen X (mm)", "decimal", "conditional"),
    c("shape.origin.y_mm", "Origen Y (mm)", "decimal", "conditional"),
    c("shape.length_mm", "Longitud (mm)", "decimal", "conditional"),
    c("shape.thickness_mm", "Espesor (mm)", "decimal", "conditional"),
)
SHAPE_HELP = (
    "Rectángulo: declare origen, longitud y espesor. Polígono: deje esas celdas vacías "
    "y registre sus contornos en Vértices. No repita el primer vértice al cerrar."
)

SHEETS = (
    Sheet(
        "Proyecto",
        "project",
        None,
        (
            c("project_id", "ID de proyecto"),
            c(
                "schema_version",
                "Versión del esquema",
                choices={m.SCHEMA_VERSION: m.SCHEMA_VERSION},
            ),
            c("units", "Unidades", choices={"mm": "Milímetros"}),
        ),
        "Diligencie una sola fila. Seleccione versión y unidades. Los identificadores son texto.",
    ),
    Sheet(
        "Geometrías",
        "geometries",
        m.GeometryDefinition,
        (
            c("geometry_id", "ID de geometría"),
            *SHAPE_COLUMNS,
            DESCRIPTION,
        ),
        SHAPE_HELP,
    ),
    Sheet(
        "Regiones",
        "regions",
        m.RegionDefinition,
        (
            c("region_id", "ID de región"),
            c("geometry_id", "ID de geometría"),
            c("role", "Función de la región", choices=ROLES),
            *SHAPE_COLUMNS,
            DESCRIPTION,
        ),
        "Cada región conserva su propia geometría y su relación con la geometría principal. "
        + SHAPE_HELP,
    ),
    Sheet(
        "Referencias",
        "references",
        m.GeometricReference,
        (
            c("reference_id", "ID de referencia"),
            c("geometry_id", "ID de geometría"),
            c("kind", "Tipo de referencia", choices={"LINE": "Línea"}),
            c("start.x_mm", "Inicio X (mm)", "decimal"),
            c("start.y_mm", "Inicio Y (mm)", "decimal"),
            c("end.x_mm", "Final X (mm)", "decimal"),
            c("end.y_mm", "Final Y (mm)", "decimal"),
        ),
        "Declare los extremos de una línea en el sistema local; no se recortan ni desplazan.",
    ),
    Sheet(
        "Configuraciones",
        "configurations",
        m.ReinforcementConfiguration,
        (
            c("config_id", "ID de configuración"),
            c("geometry_id", "ID de geometría"),
            DESCRIPTION,
        ),
        "Una configuración puede reutilizarse en varias secciones sin duplicar sus datos.",
    ),
    Sheet(
        "Barras",
        "bar_layouts",
        m.BarLayoutDefinition,
        (
            c("layout_id", "ID de distribución"),
            c("config_id", "ID de configuración"),
            c("region_id", "ID de región", requirement="optional"),
            c("distribution.pattern", "Patrón de distribución", choices=PATTERNS),
            c("distribution.reference_id", "ID de referencia", requirement="conditional"),
            c("distribution.quantity", "Cantidad", "integer", "conditional"),
            c("distribution.diameter_mm", "Diámetro (mm)", "decimal", "conditional"),
            c("distribution.spacing_mm", "Separación (mm)", "decimal", "conditional"),
            c(
                "distribution.start_offset_mm",
                "Desplazamiento inicial (mm)",
                "decimal",
                "conditional",
            ),
            c("distribution.end_offset_mm", "Desplazamiento final (mm)", "decimal", "conditional"),
            c(
                "distribution.spacing_policy",
                "Política de separación",
                requirement="conditional",
                help="Texto libre obligatorio por separación. No se interpreta ni traduce.",
            ),
            c(
                "distribution.alignment",
                "Alineación",
                requirement="conditional",
                help="Texto: requerido por separación, opcional por cantidad; vacío en explícita.",
            ),
        ),
        "Por cantidad: referencia, cantidad, diámetro y ambos desplazamientos. "
        "Por separación: referencia, diámetro, separación, desplazamientos, política y alineación. "
        "Explícita: use Barras explícitas; "
        "deje vacíos los parámetros lineales.",
    ),
    Sheet(
        "Secciones",
        "sections",
        m.SectionDefinition,
        (
            c("section_id", "ID de sección"),
            c("geometry_id", "ID de geometría"),
            c("config_id", "ID de configuración"),
            c("materials.concrete.specification", "Especificación del concreto"),
            c("materials.reinforcement.specification", "Especificación del acero"),
            DESCRIPTION,
        ),
        "La sección reúne geometría, configuración y materiales declarados. "
        "Las propiedades adicionales "
        "se registran en Propiedades de materiales. No se asignan resistencias predeterminadas.",
    ),
    Sheet(
        "Muros",
        "walls",
        m.WallDefinition,
        (c("wall_id", "ID de muro"), DESCRIPTION),
        "El muro es el elemento físico. Su identidad es independiente de la sección reforzada.",
    ),
    Sheet(
        "Asignaciones",
        "assignments",
        m.SectionAssignment,
        (
            c("assignment_id", "ID de asignación"),
            c("wall_id", "ID de muro"),
            c("level_id", "ID de nivel"),
            c("section_id", "ID de sección"),
        ),
        "Asigne una sección a cada par muro y nivel. El nivel es una referencia externa declarada.",
    ),
    Sheet(
        "Estribos",
        "transverse_assemblies",
        m.TransverseAssembly,
        (
            c("assembly_id", "ID de estribo"),
            c("config_id", "ID de configuración"),
            c("region_id", "ID de región", requirement="optional"),
            STATE,
            DESCRIPTION,
        ),
        "Conjuntos pendientes de definir. Declare sus componentes en Estribos-barras. "
        "No se calculan formas ni ganchos.",
    ),
    Sheet(
        "Dibujo",
        "drawings",
        m.DrawingSpecification,
        (
            c("drawing_id", "ID de dibujo"),
            c("section_id", "ID de sección"),
            STATE,
            c("template_id", "ID de plantilla", requirement="optional"),
            c("drawing_scale", "Escala de dibujo (adimensional)", "decimal", "optional"),
        ),
        "Especificaciones pendientes de definir. La escala es una magnitud decimal textual. "
        "No se genera dibujo.",
    ),
    Sheet(
        "Vértices",
        "vertices",
        None,
        (
            c("owner_type", "Tipo de propietario", choices=OWNERS),
            c("owner_id", "ID de propietario"),
            c("loop_role", "Tipo de contorno", choices=LOOPS),
            c(
                "loop_order",
                "Orden de contorno",
                "integer",
                help="Exterior: 1. Huecos: 1, 2, 3… en el orden original, sin saltos.",
            ),
            c("order", "Orden de vértice", "integer"),
            c("x_mm", "Coordenada X (mm)", "decimal"),
            c("y_mm", "Coordenada Y (mm)", "decimal"),
        ),
        "Contorno exterior antihorario y huecos horarios. "
        "Numere vértices desde 1 en cada contorno. "
        "Conserve el orden; el cierre es implícito. Solo propietarios poligonales.",
        True,
    ),
    Sheet(
        "Barras explícitas",
        "explicit_bars",
        None,
        (
            c("layout_id", "ID de distribución"),
            c("order", "Orden de barra", "integer"),
            c("bar_id", "ID de barra"),
            c("position.x_mm", "Posición X (mm)", "decimal"),
            c("position.y_mm", "Posición Y (mm)", "decimal"),
            c("diameter_mm", "Diámetro (mm)", "decimal"),
        ),
        "Solo para distribución explícita. Numere las barras desde 1 por distribución; "
        "no se calculan posiciones.",
        True,
    ),
    Sheet(
        "Propiedades de materiales",
        "material_properties",
        None,
        (
            c("section_id", "ID de sección"),
            c("material_role", "Material", choices=MATERIALS),
            c("order", "Orden de propiedad", "integer"),
            c("name", "Nombre de propiedad"),
            c("value", "Valor (unidad declarada)", "decimal"),
            c("unit", "Unidad de la propiedad"),
        ),
        "Numere propiedades desde 1 por sección y material. "
        "Nombre, valor y unidad se conservan exactamente.",
        True,
    ),
    Sheet(
        "Barras dobladas",
        "bent_bars",
        m.BentBarDefinition,
        (
            c("bent_bar_id", "ID de barra doblada"),
            STATE,
            c("diameter_mm", "Diámetro (mm)", "decimal", "optional"),
            DESCRIPTION,
        ),
        "Declaraciones pendientes de definir; "
        "no hay trayectorias, radios, ganchos ni geometría calculada.",
        True,
    ),
    Sheet(
        "Estribos-barras",
        "assembly_bars",
        None,
        (
            c("assembly_id", "ID de estribo"),
            c("order", "Orden de componente", "integer"),
            c("bent_bar_id", "ID de barra doblada"),
        ),
        "Relacione estribos con barras dobladas existentes. "
        "Numere componentes desde 1 por estribo.",
        True,
    ),
    Sheet(
        "Distribución vertical",
        "vertical_placements",
        m.VerticalPlacement,
        (
            c("placement_id", "ID de colocación"),
            c("assignment_id", "ID de asignación"),
            c("assembly_id", "ID de estribo"),
            STATE,
            c("z_start_mm", "Cota inicial Z (mm)", "decimal"),
            c("z_end_mm", "Cota final Z (mm)", "decimal"),
            c("spacing_mm", "Separación (mm)", "decimal", "optional"),
            c("spacing_policy", "Política de separación", requirement="optional"),
        ),
        "Coordenadas Z declaradas, positivas hacia arriba. La cota final supera la inicial. "
        "No se infieren elevaciones ni se calculan ubicaciones.",
        True,
    ),
)
BY_COLLECTION = {s.collection: s for s in SHEETS}
BY_NAME = {s.name: s for s in SHEETS}


def get_path(data: dict, path: tuple[str, ...]):
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def set_path(data: dict, path: tuple[str, ...], value: object) -> None:
    for key in path[:-1]:
        data = data.setdefault(key, {})
    data[path[-1]] = value
