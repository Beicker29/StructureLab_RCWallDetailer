"""Exact planar predicates: no epsilon, snapping, winding reversal or input mutation."""

from fractions import Fraction

from rcwall.domain.models import (
    GeometryDefinition,
    Point2D,
    PolygonDefinition,
    RectangleDefinition,
    ValidationIssue,
)

Point = tuple[Fraction, Fraction]
Ring = tuple[Point, ...]
Shape = RectangleDefinition | PolygonDefinition


def point(value: Point2D) -> Point:
    return Fraction(value.x_mm), Fraction(value.y_mm)


def shape_rings(shape: Shape) -> tuple[Ring, tuple[Ring, ...]]:
    """Derived representation only; Fraction avoids Decimal-context rounding."""
    if isinstance(shape, RectangleDefinition):
        x, y = point(shape.origin)
        length, thickness = Fraction(shape.length_mm), Fraction(shape.thickness_mm)
        return ((x, y), (x + length, y), (x + length, y + thickness), (x, y + thickness)), ()
    return tuple(map(point, shape.outer)), tuple(tuple(map(point, hole)) for hole in shape.holes)


def _cross(a: Point, b: Point, c: Point) -> Fraction:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    return _cross(a, b, p) == 0 and all(min(a[i], b[i]) <= p[i] <= max(a[i], b[i]) for i in (0, 1))


def _intersects(a: Point, b: Point, c: Point, d: Point) -> bool:
    ab_c, ab_d = _cross(a, b, c), _cross(a, b, d)
    cd_a, cd_b = _cross(c, d, a), _cross(c, d, b)
    return (
        (ab_c * ab_d < 0 and cd_a * cd_b < 0)
        or (ab_c == 0 and _on_segment(a, b, c))
        or (ab_d == 0 and _on_segment(a, b, d))
        or (cd_a == 0 and _on_segment(c, d, a))
        or (cd_b == 0 and _on_segment(c, d, b))
    )


def _edges(ring: Ring):
    return zip(ring, ring[1:] + ring[:1], strict=True)


def _signed_area2(ring: Ring) -> Fraction:
    return sum((a[0] * b[1] - b[0] * a[1] for a, b in _edges(ring)), Fraction(0))


def _ring_problem(ring: Ring, *, outer: bool) -> tuple[str, str] | None:
    if len(ring) < 3:
        return "vertex_count", "Se requieren al menos tres vértices."
    if ring[0] == ring[-1]:
        return "repeated_closure", "El cierre es implícito; no repita el primer vértice."
    if len(set(ring)) != len(ring):
        return "repeated_vertex", "El contorno contiene vértices repetidos."
    for i, b in enumerate(ring):
        a, c = ring[i - 1], ring[(i + 1) % len(ring)]
        if _cross(a, b, c) == 0 and (_on_segment(a, b, c) or _on_segment(b, c, a)):
            return "overlapping_edges", "El contorno retrocede sobre una arista."
    edges = tuple(_edges(ring))
    for i, (a, b) in enumerate(edges):
        for j in range(i + 1, len(edges)):
            if j == i + 1 or (i == 0 and j == len(edges) - 1):
                continue
            if _intersects(a, b, *edges[j]):
                return "self_intersection", "El contorno se autointerseca o se toca a sí mismo."
    area = _signed_area2(ring)
    if area == 0:
        return "zero_area", "El contorno tiene área nula."
    if (area > 0) != outer:
        return "invalid_orientation", "Se requiere exterior antihorario y huecos horarios."
    return None


def _rings_touch(a: Ring, b: Ring) -> bool:
    return any(_intersects(p, q, r, s) for p, q in _edges(a) for r, s in _edges(b))


def _inside(p: Point, ring: Ring) -> bool:
    inside = False
    for a, b in _edges(ring):
        if _on_segment(a, b, p):
            return False
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                inside = not inside
    return inside


def validate_shape(shape: Shape, path: tuple[str | int, ...] = ()) -> tuple[ValidationIssue, ...]:
    """Validate one simple connected polygon, optionally with disjoint interior holes."""
    outer, holes = shape_rings(shape)
    issues = []

    def issue(suffix, code, description):
        issues.append(
            ValidationIssue(
                stage="geometry", path=path + suffix, code=code, description=description
            )
        )

    for suffix, ring, is_outer in [(("outer",), outer, True)] + [
        (("holes", i), hole, False) for i, hole in enumerate(holes)
    ]:
        problem = _ring_problem(ring, outer=is_outer)
        if problem:
            issue(suffix, *problem)
    if issues:
        return tuple(issues)
    for i, hole in enumerate(holes):
        if _rings_touch(outer, hole) or not _inside(hole[0], outer):
            issue(
                ("holes", i),
                "invalid_hole",
                "El hueco debe estar estrictamente dentro del contorno exterior, sin tocarlo.",
            )
        for j in range(i):
            other = holes[j]
            if _rings_touch(hole, other) or _inside(hole[0], other) or _inside(other[0], hole):
                issue(
                    ("holes", i),
                    "overlapping_holes",
                    "Los huecos no pueden tocarse, solaparse ni anidarse.",
                )
    if _signed_area2(outer) + sum((_signed_area2(h) for h in holes), Fraction(0)) <= 0:
        issue(("holes",), "nonpositive_area", "El área neta debe ser positiva.")
    return tuple(issues)


def _ring_key(ring: Ring) -> Ring:
    # Redundant collinear points are omitted only in the comparison key, never in input.
    corners = tuple(
        p for i, p in enumerate(ring) if _cross(ring[i - 1], p, ring[(i + 1) % len(ring)]) != 0
    )
    start = min(range(len(corners)), key=corners.__getitem__)
    return corners[start:] + corners[:start]


def shape_key(shape: Shape) -> tuple[Ring, tuple[Ring, ...]]:
    """Representation-independent occupied region in the same local frame, exactly."""
    shape = type(shape).model_validate(shape.model_dump(mode="python"))
    issues = validate_shape(shape)
    if issues:
        raise ValueError(f"Geometría inválida: {issues[0].code}")
    outer, holes = shape_rings(shape)
    return _ring_key(outer), tuple(sorted(_ring_key(hole) for hole in holes))


def geometrically_equivalent(left: GeometryDefinition, right: GeometryDefinition) -> bool:
    """Ignore IDs and representation; reject invalid shapes instead of repairing them."""
    return shape_key(left.shape) == shape_key(right.shape)
