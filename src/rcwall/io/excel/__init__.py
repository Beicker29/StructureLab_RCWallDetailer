"""Spanish Excel interface over canonical V0.1 contracts."""

from .diagnostics import ExcelValidationError, ExcelValidationReport
from .reader import inspect_workbook, read_project, validate_workbook
from .writer import create_template, export_project, generate_example

__all__ = [
    "ExcelValidationError",
    "ExcelValidationReport",
    "create_template",
    "export_project",
    "generate_example",
    "inspect_workbook",
    "read_project",
    "validate_workbook",
]
