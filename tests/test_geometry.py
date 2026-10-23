from copy import deepcopy
from decimal import localcontext

import pytest

from rcwall.domain.models import GeometryDefinition
from rcwall.geometry.polygons import geometrically_equivalent
from rcwall.validation import validate_definition


def polygon(outer, holes=()):
    def ring(points):
        return [{"x_mm": str(x), "y_mm": str(y)} for x, y in points]

    return {"kind": "POLYGON", "outer": ring(outer), "holes": [ring(h) for h in holes]}


OUTER = [(0, 0), (10, 0), (10, 10), (0, 10)]
HOLE = [(2, 2), (2, 4), (4, 4), (4, 2)]


@pytest.mark.parametrize(
    "shape",
    [
        polygon(OUTER),
        polygon(OUTER, [HOLE]),
        polygon([(0, 0), (8, 0), (8, 2), (2, 2), (2, 8), (0, 8)]),
        polygon(OUTER, [HOLE, [(6, 6), (6, 8), (8, 8), (8, 6)]]),
    ],
)
def test_valid_polygons_and_holes(project_data, shape):
    project_data["geometries"][0]["shape"] = shape
    assert validate_definition(project_data).report.valid


@pytest.mark.parametrize(
    ("shape", "code"),
    [
        (polygon(list(reversed(OUTER))), "invalid_orientation"),
        (polygon(OUTER, [list(reversed(HOLE))]), "invalid_orientation"),
        (polygon(OUTER + [OUTER[0]]), "repeated_closure"),
        (polygon([(0, 0), (10, 0), (10, 10), (0, 0), (0, 10)]), "repeated_vertex"),
        (polygon([(0, 0), (4, 0), (2, 0), (2, 4), (0, 4)]), "overlapping_edges"),
        (polygon([(0, 0), (10, 10), (0, 10), (10, 0)]), "self_intersection"),
        (polygon([(0, 0), (10, 0), (10, 10), (5, 0), (0, 10)]), "self_intersection"),
        (polygon(OUTER, [[(9, 2), (9, 4), (11, 4), (11, 2)]]), "invalid_hole"),
        (polygon(OUTER, [[(12, 2), (12, 4), (14, 4), (14, 2)]]), "invalid_hole"),
        (polygon(OUTER, [[(0, 2), (0, 4), (4, 4), (4, 2)]]), "invalid_hole"),
        (polygon(OUTER, [HOLE, [(3, 3), (3, 5), (5, 5), (5, 3)]]), "overlapping_holes"),
        (polygon(OUTER, [HOLE, [(4, 2), (4, 4), (6, 4), (6, 2)]]), "overlapping_holes"),
        (polygon(OUTER, [[(1, 1), (1, 8), (8, 8), (8, 1)], HOLE]), "overlapping_holes"),
    ],
)
def test_invalid_topology_is_rejected_without_repairs(project_data, shape, code):
    original = deepcopy(shape)
    project_data["geometries"][0]["shape"] = shape
    result = validate_definition(project_data)
    assert result.project is None
    assert any(i.code == code and i.stage == "geometry" for i in result.report.issues)
    assert project_data["geometries"][0]["shape"] == original


@pytest.mark.parametrize("outer", [[(0, 0), (1, 0)], [(0, 0), (1, 0), (2, 0)]])
def test_degenerate_contours(project_data, outer):
    project_data["geometries"][0]["shape"] = polygon(outer)
    assert not validate_definition(project_data).report.valid


def test_region_geometry_is_validated(project_data):
    project_data["regions"] = [
        {
            "region_id": "R1",
            "geometry_id": "G1",
            "role": "WEB",
            "shape": polygon(list(reversed(OUTER))),
        }
    ]
    report = validate_definition(project_data).report
    assert any(i.path == ("regions", 0, "shape", "outer") for i in report.issues)


def test_rectangle_polygon_equivalence_with_cyclic_and_collinear_variants():
    rectangle = GeometryDefinition.model_validate(
        {
            "geometry_id": "RECT",
            "shape": {
                "kind": "RECTANGLE",
                "origin": {"x_mm": "0", "y_mm": "0"},
                "length_mm": "10",
                "thickness_mm": "10",
            },
        }
    )
    points = [(10, 10), (0, 10), (0, 0), (5, 0), (10, 0)]
    contour = GeometryDefinition.model_validate({"geometry_id": "POLY", "shape": polygon(points)})
    before = contour.model_dump(mode="json")
    assert geometrically_equivalent(rectangle, contour)
    assert contour.model_dump(mode="json") == before


def test_hole_order_does_not_change_equivalence():
    second = [(6, 6), (6, 8), (8, 8), (8, 6)]
    left = GeometryDefinition.model_validate(
        {"geometry_id": "G1", "shape": polygon(OUTER, [HOLE, second])}
    )
    right = GeometryDefinition.model_validate(
        {"geometry_id": "G2", "shape": polygon(OUTER[1:] + OUTER[:1], [second, HOLE])}
    )
    assert geometrically_equivalent(left, right)


def test_no_rounding_in_geometry_equivalence_or_tiny_area():
    tiny = "0.000000000000000000000000000000000000000001"
    shape = polygon([(0, 0), (tiny, 0), (tiny, tiny), (0, tiny)])
    left = GeometryDefinition.model_validate({"geometry_id": "G1", "shape": shape})
    right_shape = deepcopy(shape)
    right_shape["outer"][1]["x_mm"] = tiny + "1"
    right_shape["outer"][2]["x_mm"] = tiny + "1"
    right = GeometryDefinition.model_validate({"geometry_id": "G2", "shape": right_shape})
    with localcontext() as context:
        context.prec = 3
        assert geometrically_equivalent(left, left)
        assert not geometrically_equivalent(left, right)


def test_unsupported_shapes_and_transforms_are_rejected(project_data):
    project_data["geometries"][0]["shape"]["rotation_deg"] = "90"
    assert not validate_definition(project_data).report.valid
    project_data["geometries"][0]["shape"] = {"kind": "MULTIPOLYGON", "parts": []}
    assert not validate_definition(project_data).report.valid


def test_invalid_geometry_cannot_be_declared_equivalent():
    geometry = GeometryDefinition.model_validate(
        {"geometry_id": "G1", "shape": polygon(list(reversed(OUTER)))}
    )
    with pytest.raises(ValueError, match="invalid_orientation"):
        geometrically_equivalent(geometry, geometry)
