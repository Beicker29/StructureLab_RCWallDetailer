# StructureLab RCWallDetailer

Herramienta de ingeniería en desarrollo para el detallado de secciones de muros de
concreto reforzado. El flujo previsto recibe definiciones desde Excel, utiliza contratos
canónicos versionados y serializables a JSON, resuelve geometría de refuerzo y exporta
detalles editables inicialmente a DXF.

El proyecto es independiente de DCCAD3, AutoCAD y formatos propietarios. Los contratos,
la resolución geométrica, las verificaciones normativas y la representación CAD mantienen
responsabilidades separadas.

## Estado real: RCWD-UI-000

Implementados los contratos canónicos V0.1 mediante Pydantic, geometrías rectangulares y
poligonales con huecos, validación de tipos/referencias/topología, comparaciones acotadas
de equivalencia y lectura/escritura JSON con valores decimales exactos.

Geometría, configuración, sección reforzada y muro físico son entidades distintas. Una
configuración puede reutilizarse entre secciones; las secciones incluyen materiales y
pueden asignarse a distintos muros y niveles. No se fusionan entidades equivalentes.

Los contratos transversales, de colocación vertical y de dibujo conservan declaraciones
con estado `UNRESOLVED`. `DetailingResult` es una envoltura reservada con estado
`NOT_IMPLEMENTED`. La equivalencia física del refuerzo siempre se informa como indeterminada.

Implementada la interfaz Excel de 17 hojas visibles en español, con plantilla vacía,
ejemplo diligenciado, exportación/importación y reportes de errores localizados.

Implementado el prototipo web local para crear/importar geometrías rectangulares,
editar dimensiones, visualizar barras explícitas y seleccionar, ampliar y desplazar la
vista SVG, conservando el JSON canónico. El núcleo y el esquema 0.1.0 permanecen intactos.

Pendientes: posiciones calculadas de barras, motores de detallado,
transformaciones local/global, verificación normativa y exportación DXF.
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

### Activar el entorno virtual

Una vez creada la carpeta `.venv`, abra una terminal en la raíz del repositorio.
En Windows PowerShell (incluida la terminal integrada de VS Code):

```powershell
.\.venv\Scripts\Activate.ps1
```

En Linux/macOS con Bash o Zsh:

```bash
source .venv/bin/activate
```

Con el entorno activo aparecerá `(.venv)` al inicio de la terminal y podrá usar
`python` directamente, por ejemplo `python -m pytest` o `python -m rcwall_web`
si instaló el extra `web`. La activación se realiza en cada terminal nueva.
Los comandos anteriores con la ruta completa al intérprete también funcionan sin activarlo.

Para salir del entorno virtual:

```text
deactivate
```

### Abrir el prototipo web

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web]"
.\.venv\Scripts\python.exe -m rcwall_web
```

Abra **http://127.0.0.1:8000**. Consulte la [guía web](docs/web_prototype.md) para uso,
pruebas de navegador, capturas, alcance y limitaciones. El proyecto vive en cada pestaña;
exporte el JSON antes de cerrar o recargar. No se guardan proyectos en el servidor.

Cierre RCWD-UI-000: **198 pruebas aprobadas** al habilitar las pruebas de navegador
(165 previas, 31 web y 2 de navegador). Ruff check y format sin errores.

La distribución se llama `structurelab-rcwalldetailer`; el paquete importable es
`rcwall`. Las pruebas requieren instalar primero la distribución y no modifican
PYTHONPATH. Pydantic 2 implementa contratos, validación local y JSON Schema; openpyxl 3.1
implementa exclusivamente la frontera Excel. Setuptools construye el paquete; pytest y
Ruff pertenecen al extra de desarrollo. No hay dependencias CAD.

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
  io/excel/        Generador/lector español y diagnósticos por celda
  exporters/dxf/   Reservado para exportación
src/rcwall_web/    Adaptador web local, separado del núcleo; FastAPI y SVG
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
- [Interfaz Excel, columnas y uso](docs/excel_interface.md).
- [Decisiones técnicas de Excel](docs/excel_decisions.md).
- [Prototipo web, ejecución y evidencia visual](docs/web_prototype.md).
- [ADR-006: interfaz local y precisión](docs/adr/ADR-006-local-web-prototype.md).
- [Hoja de ruta](docs/development_roadmap.md).
- [Convenciones](docs/conventions.md).
- [ADR-001: independencia del dominio](docs/adr/ADR-001-domain-independence.md).
- [ADR-002: modelo canónico](docs/adr/ADR-002-canonical-data-model.md).
- [ADR-003: distribuciones](docs/adr/ADR-003-reinforcement-layouts.md).
- [ADR-004: identidad y equivalencia](docs/adr/ADR-004-identity-and-equivalence.md).
- [ADR-005: coordenadas y precisión](docs/adr/ADR-005-coordinates-and-precision.md).
- [Instrucciones para agentes](AGENTS.md).

Validación histórica de RCWD-001B con Python 3.12: se conservan las 115 pruebas anteriores y se incorporan
50 pruebas Excel (165 en total). Ruff check y Ruff format --check sin errores. Esto verifica contratos y
el subconjunto geométrico descrito, no un motor ni una comprobación normativa.

El mapeo Excel incluye secciones, materiales y muros físicos sin cambiar el esquema 0.1.0.
Las políticas de distribución, la geometría transversal y las transformaciones permanecen
como trabajo posterior. No se verificó interacción manual en Microsoft Excel instalado.

## Generar, editar y validar Excel

```powershell
.\.venv\Scripts\python.exe scripts/generate_excel_artifacts.py
```

Archivos estables: [plantilla vacía](examples/excel/plantilla_v0_1.xlsx) y
[ejemplo diligenciado](examples/excel/ejemplo_v0_1.xlsx), generado del JSON existente.

```python
from rcwall.io.excel import export_project, inspect_workbook
from rcwall.io.json import read_project, write_project

export_project(read_project("examples/project_v0_1.json"), "entrada.xlsx")
# Editar entrada.xlsx, conservando los decimales como texto.
result = inspect_workbook("entrada.xlsx")
print(result.report.to_dict())
if result.project is not None:
    write_project(result.project, "salida.json")
```

Encabezados en fila 6, datos desde fila 7. Las listas controladas están en español;
los textos libres nunca se traducen. Decimales almacenados como números de Excel se
rechazan para impedir pérdida de precisión. La plantilla vacía requiere diligenciar
Proyecto antes de validarse como entrada. Consulte la documentación para ampliar
las 200 filas inicialmente preparadas y para interpretar campos condicionales.
