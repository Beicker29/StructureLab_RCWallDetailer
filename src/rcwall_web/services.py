"""Stateless application use cases; canonical text and disposable graphics stay separate."""

from fractions import Fraction
from uuid import uuid4

from rcwall.domain.models import ExplicitLayout, ProjectDefinition, RectangleDefinition
from rcwall.io.json import ProjectValidationError, dumps_project, loads_project
from rcwall.validation import validate_definition


class WebInputError(ValueError):
    """An unsupported web operation, without changing the supplied project."""


def accepted(data: object) -> ProjectDefinition:
    result = validate_definition(data)
    if result.project is None:
        raise ProjectValidationError(result.report)
    return result.project


def create_rectangle(length: str, thickness: str, x: str, y: str) -> ProjectDefinition:
    return accepted(
        {
            "project_id": f"P-{uuid4().hex}",
            "schema_version": "0.1.0",
            "units": "mm",
            "geometries": [
                {
                    "geometry_id": f"G-{uuid4().hex}",
                    "shape": {
                        "kind": "RECTANGLE",
                        "origin": {"x_mm": x, "y_mm": y},
                        "length_mm": length,
                        "thickness_mm": thickness,
                    },
                }
            ],
        }
    )


def edit_rectangle(document: str, index: int, length: str, thickness: str) -> ProjectDefinition:
    project = loads_project(document)
    if index < 0 or index >= len(project.geometries):
        raise WebInputError("Seleccione una geometría existente.")
    if not isinstance(project.geometries[index].shape, RectangleDefinition):
        raise WebInputError("Este prototipo solo edita geometrías rectangulares.")
    data = project.model_dump(mode="json")
    data["geometries"][index]["shape"].update(length_mm=length, thickness_mm=thickness)
    return accepted(data)


def _graphics(shape, bars):
    """Relative exact arithmetic before float projection avoids cancellation at large origins."""
    values = [shape.origin.x_mm, shape.origin.y_mm, shape.length_mm, shape.thickness_mm]
    values.extend(
        value for b in bars for value in (b.position.x_mm, b.position.y_mm, b.diameter_mm)
    )
    if any(
        len(value.as_tuple().digits) + abs(value.as_tuple().exponent) > 10000 for value in values
    ):
        return {
            "rectangle": None,
            "circles": [],
            "bounds": [0, 0, 1000, 200],
            "warning": "Vista omitida: magnitudes fuera del presupuesto gráfico de 10 000 dígitos. "
            "El documento canónico se conserva y puede exportarse.",
        }
    x0, y0 = Fraction(shape.origin.x_mm), Fraction(shape.origin.y_mm)
    length, thickness = Fraction(shape.length_mm), Fraction(shape.thickness_mm)
    points = [
        (
            Fraction(b.position.x_mm) - x0,
            Fraction(b.position.y_mm) - y0,
            Fraction(b.diameter_mm) / 2,
        )
        for b in bars
    ]
    xmin = min([Fraction(0)] + [x - r for x, y, r in points])
    xmax = max([length] + [x + r for x, y, r in points])
    ymin = min([Fraction(0)] + [y - r for x, y, r in points])
    ymax = max([thickness] + [y + r for x, y, r in points])
    scale = max(xmax - xmin, ymax - ymin)

    def visual(value):
        return float(value / scale * 1000)

    rect = {
        "x": visual(-xmin),
        "y": visual(ymax - thickness),
        "width": visual(length),
        "height": visual(thickness),
    }
    circles = [
        {"cx": visual(x - xmin), "cy": visual(ymax - y), "r": visual(r)} for x, y, r in points
    ]
    tiny = min(rect["width"], rect["height"], *[c["r"] for c in circles]) < 0.001
    return {
        "rectangle": rect,
        "circles": circles,
        "bounds": [0, 0, visual(xmax - xmin), visual(ymax - ymin)],
        "warning": "Algunos detalles son demasiado pequeños para esta escala visual."
        if tiny
        else "",
    }


def present(project: ProjectDefinition) -> dict:
    geometries = []
    for index, geometry in enumerate(project.geometries):
        shape = geometry.shape
        item = {
            "index": index,
            "label": geometry.description or f"Geometría {index + 1}",
            "rectangular": isinstance(shape, RectangleDefinition),
            "configurations": [],
        }
        if isinstance(shape, RectangleDefinition):
            item["dimensions"] = {
                "length": str(shape.length_mm),
                "thickness": str(shape.thickness_mm),
                "x": str(shape.origin.x_mm),
                "y": str(shape.origin.y_mm),
            }
            configs = [c for c in project.configurations if c.geometry_id == geometry.geometry_id]
            for config in configs or [None]:
                layouts = [
                    b for b in project.bar_layouts if config and b.config_id == config.config_id
                ]
                explicit = [
                    b
                    for layout in layouts
                    if isinstance(layout.distribution, ExplicitLayout)
                    for b in layout.distribution.bars
                ]
                item["configurations"].append(
                    {
                        "label": (
                            config.description or f"Configuración {len(item['configurations']) + 1}"
                        )
                        if config
                        else "Sin configuración de refuerzo",
                        "pending": sum(
                            not isinstance(b.distribution, ExplicitLayout) for b in layouts
                        ),
                        "bars": [
                            {
                                "id": b.bar_id,
                                "x": str(b.position.x_mm),
                                "y": str(b.position.y_mm),
                                "diameter": str(b.diameter_mm),
                            }
                            for b in explicit
                        ],
                        "graphics": _graphics(shape, explicit),
                    }
                )
        geometries.append(item)
    return {"document": dumps_project(project), "geometries": geometries}
