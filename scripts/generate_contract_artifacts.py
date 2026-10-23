"""Regenerate the V0.1 schema and a declared-input example (no calculated reinforcement)."""

from pathlib import Path

from rcwall.domain import ProjectDefinition
from rcwall.io.json import write_project, write_project_schema


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    (root / "schemas").mkdir(exist_ok=True)
    (root / "examples").mkdir(exist_ok=True)
    materials = {
        "concrete": {"specification": "CONCRETE-A: ejemplo de especificación declarada"},
        "reinforcement": {"specification": "STEEL-A: ejemplo de especificación declarada"},
    }
    project = ProjectDefinition.model_validate(
        {
            "project_id": "PROJECT-EXAMPLE",
            "schema_version": "0.1.0",
            "units": "mm",
            "geometries": [
                {
                    "geometry_id": "G1",
                    "shape": {
                        "kind": "RECTANGLE",
                        "origin": {"x_mm": "0", "y_mm": "0"},
                        "length_mm": "3000.000000000000000000000000001",
                        "thickness_mm": "200.00",
                    },
                }
            ],
            "references": [
                {
                    "reference_id": "REF1",
                    "geometry_id": "G1",
                    "kind": "LINE",
                    "start": {"x_mm": "100", "y_mm": "100"},
                    "end": {"x_mm": "2900", "y_mm": "100"},
                }
            ],
            "configurations": [{"config_id": "C1", "geometry_id": "G1"}],
            "bar_layouts": [
                {
                    "layout_id": "LAYOUT1",
                    "config_id": "C1",
                    "distribution": {
                        "pattern": "LINEAR_COUNT",
                        "reference_id": "REF1",
                        "quantity": 6,
                        "diameter_mm": "16",
                        "start_offset_mm": "0",
                        "end_offset_mm": "0",
                    },
                }
            ],
            "sections": [
                {
                    "section_id": "S1",
                    "geometry_id": "G1",
                    "config_id": "C1",
                    "materials": materials,
                },
                {
                    "section_id": "S2",
                    "geometry_id": "G1",
                    "config_id": "C1",
                    "materials": materials,
                },
            ],
            "walls": [{"wall_id": "W1"}, {"wall_id": "W2"}],
            "assignments": [
                {"assignment_id": "A1", "wall_id": "W1", "level_id": "L1", "section_id": "S1"},
                {"assignment_id": "A2", "wall_id": "W1", "level_id": "L2", "section_id": "S2"},
                {"assignment_id": "A3", "wall_id": "W2", "level_id": "L1", "section_id": "S1"},
            ],
        }
    )
    write_project_schema(root / "schemas" / "project_definition-0.1.0.schema.json")
    write_project(project, root / "examples" / "project_v0_1.json")


if __name__ == "__main__":
    main()
