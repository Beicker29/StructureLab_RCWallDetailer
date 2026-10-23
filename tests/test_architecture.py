import ast
from pathlib import Path

import rcwall.domain


def test_core_never_imports_web_adapter_or_http_frameworks():
    root = Path(rcwall.domain.__file__).parent.parent
    forbidden = {"rcwall_web", "fastapi", "starlette", "uvicorn", "openpyxl"}
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert not {alias.name.split(".")[0] for alias in node.names} & forbidden
                assert not any(alias.name.startswith("rcwall.io.excel") for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden
                assert not node.module.startswith("rcwall.io.excel")


def test_domain_imports_only_its_own_contracts_and_declared_libraries():
    directory = Path(rcwall.domain.__file__).parent
    allowed = {"re", "decimal", "typing", "pydantic", "pydantic_core"}
    for path in directory.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] in allowed, (path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1, (path, node.module)
                else:
                    assert node.module.split(".")[0] in allowed, (path, node.module)
