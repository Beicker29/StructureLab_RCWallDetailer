# StructureLab RCWallDetailer

Herramienta de ingeniería en desarrollo para el detallado de secciones de muros de
concreto reforzado. El flujo previsto recibe definiciones desde Excel, utiliza contratos
canónicos versionados y serializables a JSON, resuelve geometría de refuerzo y exporta
detalles editables inicialmente a DXF.

El proyecto es independiente de DCCAD3, AutoCAD y formatos propietarios. Los contratos,
la resolución geométrica, las verificaciones normativas y la representación CAD mantienen
responsabilidades separadas.

## Estado real: RCWD-001A

Implementados los contratos canónicos V0.1 mediante Pydantic, geometrías rectangulares y
poligonales con huecos, validación de tipos/referencias/topología, comparaciones acotadas
de equivalencia y lectura/escritura JSON con valores decimales exactos.

Geometría, configuración, sección reforzada y muro físico son entidades distintas. Una
configuración puede reutilizarse entre secciones; las secciones incluyen materiales y
pueden asignarse a distintos muros y niveles. No se fusionan entidades equivalentes.

Los contratos transversales, de colocación vertical y de dibujo conservan declaraciones
con estado `UNRESOLVED`. `DetailingResult` es una envoltura reservada con estado
`NOT_IMPLEMENTED`. La equivalencia física del refuerzo siempre se informa como indeterminada.

Pendientes: Excel (RCWD-001B), posiciones calculadas de barras, motores de detallado,
transformaciones local/global, verificación normativa y exportación DXF. No existe CLI.
La validación de datos no demuestra cumplimiento de una norma estructural.

## Instalación y desarrollo

Requisitos: Python 3.11 o posterior con pip y venv. No se necesita Excel ni software CAD.
Desde la raíz del repositorio, en Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import rcwall; print(rcwall.__file__)"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

En Linux/macOS, crear el entorno con `python3 -m venv .venv` y utilizar
`.venv/bin/python` con los mismos argumentos. No hace falta activar el entorno.
Para instalar sin herramientas de desarrollo: `python -m pip install .`.

La distribución se llama `structurelab-rcwalldetailer`; el paquete importable es
`rcwall`. Las pruebas requieren instalar primero la distribución y no modifican
PYTHONPATH. Pydantic 2 es la única dependencia directa de ejecución para contratos,
validación local y JSON Schema. Setuptools construye el paquete; pytest y Ruff
pertenecen al extra de desarrollo. No se incorporan dependencias Excel o CAD.

## Uso de los contratos

```python
from rcwall.io.json import read_project, dumps_project, write_project_schema
from rcwall.validation import validate_definition
from rcwall.validation.equivalence import compare_section_definitions

project = read_project("examples/project_v0_1.json")
outcome = validate_definition(project)
print(outcome.report.model_dump(mode="json"))
print(compare_section_definitions(project, "S1", "S2").status)
text = dumps_project(project)
write_project_schema("schemas/project_definition-0.1.0.schema.json")
```

`validate_definition(datos)` devuelve un proyecto aceptado o `project=None`, junto con
un reporte. `read_project`, `loads_project`, `dumps_project` y `write_project` usan
validación completa y lanzan `ProjectValidationError`, con atributo `.report`, si
encuentran errores. Construir un modelo Pydantic solo comprueba sus contratos locales;
para aceptar un proyecto se deben validar además referencias y geometría.

Introducir decimales como texto, Decimal o enteros. La API Python rechaza float.
El JSON canónico escribe decimales como cadenas y cantidades como enteros. El lector
también admite tokens numéricos decimales, procesados directamente como Decimal.
Los anillos se cierran implícitamente y deben venir con orientación correcta, sin repetir
el primer vértice. No se reparan ni se redondean entradas.

Regenerar el esquema y el ejemplo desde el código:

```powershell
.\.venv\Scripts\python.exe scripts/generate_contract_artifacts.py
```

El [ejemplo JSON](examples/project_v0_1.json) contiene entradas ilustrativas declaradas,
no recomendaciones de diseño ni resultados calculados. Conserva dos secciones equivalentes
con identidades distintas. El [JSON Schema](schemas/project_definition-0.1.0.schema.json)
cubre la estructura canónica; la positividad de decimales escritos como texto, las
referencias y la topología requieren además el validador Python.

## Estructura

```text
src/rcwall/
  domain/          Contratos, entidades y relaciones
  geometry/        Predicados topológicos y equivalencia geométrica exacta
  detailing/       Reservado para motores de resolución
  validation/      Tipos, referencias, geometría y equivalencia de definiciones
  io/json.py       Lectura/escritura JSON y generación de esquema
  io/excel/        Reservado para RCWD-001B
  exporters/dxf/   Reservado para exportación
tests/             Instalación, contratos, topología, equivalencia y JSON
docs/              Especificaciones, convenciones y ADR
schemas/           JSON Schema generado para V0.1
examples/          Ejemplo canónico de entrada
scripts/           Regeneración de artefactos de contratos
```

El dominio no conoce libros Excel, rutas de archivos ni bibliotecas CAD.
Los predicados geométricos usan Fraction de la biblioteca estándar sobre los valores
Decimal originales, sin epsilon global.

## Documentación y comprobaciones

- [Arquitectura y dependencias](docs/architecture.md).
- [Requisitos aprobados y pendientes](docs/requirements.md).
- [Contratos implementados y límites](docs/data_contracts.md).
- [Interfaz Excel preliminar](docs/excel_interface.md).
- [Hoja de ruta](docs/development_roadmap.md).
- [Convenciones](docs/conventions.md).
- [ADR-001: independencia del dominio](docs/adr/ADR-001-domain-independence.md).
- [ADR-002: modelo canónico](docs/adr/ADR-002-canonical-data-model.md).
- [ADR-003: distribuciones](docs/adr/ADR-003-reinforcement-layouts.md).
- [ADR-004: identidad y equivalencia](docs/adr/ADR-004-identity-and-equivalence.md).
- [ADR-005: coordenadas y precisión](docs/adr/ADR-005-coordinates-and-precision.md).
- [Instrucciones para agentes](AGENTS.md).

Validación realizada con Python 3.12: 115 pruebas aprobadas, incluidas las diez de
RCWD-000; Ruff check y Ruff format --check sin errores. Esto verifica contratos y
el subconjunto geométrico descrito, no un motor ni una comprobación normativa.

RCWD-001B deberá adaptar las hojas preliminares a los contratos actuales, incluyendo
secciones, materiales y muros físicos. Las políticas de distribución, la geometría
transversal y las transformaciones permanecen delimitadas como trabajo posterior.
