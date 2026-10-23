"""Generate the stable Spanish empty template and filled canonical example."""

from pathlib import Path

from rcwall.io.excel import create_template, generate_example


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    destination = root / "examples" / "excel"
    destination.mkdir(parents=True, exist_ok=True)
    create_template(destination / "plantilla_v0_1.xlsx")
    generate_example(root / "examples" / "project_v0_1.json", destination / "ejemplo_v0_1.xlsx")


if __name__ == "__main__":
    main()
