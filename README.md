# StructureLab RCWallDetailer

Herramienta de ingeniería en desarrollo para el detallado automatizado de secciones de
muros de concreto reforzado. El flujo previsto recibe definiciones desde Excel, utiliza
contratos canónicos versionados y serializables a JSON, resuelve geometría de refuerzo y
exporta detalles editables inicialmente a DXF.

El proyecto es independiente de DCCAD3, AutoCAD y formatos propietarios. La validación
de datos, la resolución geométrica, las verificaciones normativas y la representación CAD
tendrán responsabilidades separadas.

## Estado real: RCWD-000

Implementado: estructura instalable `src/rcwall/`, configuración de desarrollo, pruebas de
instalación/importación y documentación de arquitectura y decisiones.

Los módulos contienen únicamente documentación de su responsabilidad. Todavía no hay
contratos estructurales ejecutables, lector/generador Excel, serializador de proyectos,
motor geométrico, distribución de acero, verificación normativa ni exportador DXF.
No existe un comando CLI funcional. RCWD-001 es el siguiente hito.

La solicitud RCWD-000 reemplazó una implementación parcial iniciada para RCWD-001.
Esos borradores se conservaron localmente en `.work/rcwd-001-draft/`, excluidos del
paquete, de las pruebas y del control de versiones. No son una API ni un esquema aprobado.

## Instalación y desarrollo

Requisitos: Python 3.11 o posterior con `pip` y `venv`. No se necesita Excel, AutoCAD ni
licencia CAD para instalar o ejecutar las comprobaciones iniciales. Los comandos siguientes
se ejecutan desde la raíz del repositorio.

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import rcwall; print(rcwall.__file__)"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

En Linux/macOS, usar los mismos argumentos con `.venv/bin/python` después de crear
el entorno con `python3 -m venv .venv`. No es necesario activar el entorno.

Para una instalación de uso sin herramientas de desarrollo: `python -m pip install .`.
El paquete importable se llama `rcwall`; la distribución se llama
`structurelab-rcwalldetailer`. Las pruebas requieren instalar primero la distribución;
no modifican `PYTHONPATH` para simular una instalación.

No hay dependencias de ejecución en RCWD-000. `setuptools` construye el paquete;
`pytest` ejecuta pruebas y `ruff` revisa y formatea Python, ambos en el extra `dev`.
Pydantic, openpyxl y una biblioteca DXF se incorporarán cuando se implementen los
hitos que los requieran, con sus decisiones registradas.

## Estructura

```text
src/rcwall/
  domain/          Contratos, entidades y relaciones
  geometry/        Representaciones y operaciones geométricas
  detailing/       Resolución del refuerzo longitudinal y transversal
  validation/      Datos, geometría y futuras reglas normativas separadas
  io/excel/        Interfaz Excel y ubicación de errores en celdas
  exporters/dxf/   Exportación del resultado resuelto
tests/             Pruebas iniciales de instalación e importación
docs/              Especificaciones, convenciones y ADR
```

La dirección de dependencias parte de los adaptadores hacia el dominio. El dominio
no conoce libros Excel, bibliotecas CAD ni rutas de archivos. El flujo completo y los
límites de cada módulo están en [Arquitectura](docs/architecture.md).

## Documentación

- [Requisitos aprobados y decisiones pendientes](docs/requirements.md).
- [Propuesta de contratos de datos](docs/data_contracts.md).
- [Interfaz Excel V0.1 preliminar](docs/excel_interface.md).
- [Hoja de ruta RCWD-000 a RCWD-006](docs/development_roadmap.md).
- [Convenciones de desarrollo](docs/conventions.md).
- [ADR-001: independencia del dominio](docs/adr/ADR-001-domain-independence.md).
- [ADR-002: modelo canónico](docs/adr/ADR-002-canonical-data-model.md).
- [ADR-003: distribución paramétrica y explícita](docs/adr/ADR-003-reinforcement-layouts.md).
- [Instrucciones para agentes](AGENTS.md).

Antes de RCWD-001 deben resolverse o delimitarse explícitamente los campos condicionales,
enumeraciones, referencias, coordenadas y políticas de compatibilidad del esquema. La
estructura permite implementar ese hito sin cambiar la raíz del paquete ni sus límites.
