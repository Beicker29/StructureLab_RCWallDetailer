# RCWD-EXCEL-RETIRE-000 — Informe de retiro

Fecha: 2026-10-23. Paquete: **0.2.0**. Contrato canónico: **0.1.0, sin cambios**.
Decisión: [ADR-007](adr/ADR-007-retire-excel.md).

## Auditoría y preservación

Se revisaron AGENTS, arquitectura, ADR, requisitos, hoja de ruta, importaciones y
dependencias. Git estaba limpio antes de intervenir. La línea base fue de **212
pruebas aprobadas**, incluidas 10 pruebas Chromium, con una advertencia de Starlette.

Los nueve archivos retirados estaban bajo control de versiones y coincidían con
`HEAD` antes de eliminarlos. Se presentó el inventario antes de modificar archivos.
El usuario cerró los libros y confirmó «Cerrados, sin cambios pendientes»; después
se verificó la ausencia del bloqueo Office y la igualdad binaria de ambos libros.
El estado anterior puede recuperarse en Git desde
`9b329f6af98cd8423904da72b0196bf385ec4074`.

## Archivos retirados

| Ruta | Motivo |
| --- | --- |
| `src/rcwall/io/excel/__init__.py` | API pública Excel |
| `src/rcwall/io/excel/diagnostics.py` | Diagnósticos por hoja/fila/celda |
| `src/rcwall/io/excel/mapping.py` | Correspondencia entre hojas y contratos |
| `src/rcwall/io/excel/reader.py` | Lectura de libros |
| `src/rcwall/io/excel/writer.py` | Escritura de libros |
| `scripts/generate_excel_artifacts.py` | Generador de plantilla y ejemplo |
| `tests/test_excel.py` | 50 pruebas exclusivas de la funcionalidad retirada |
| `examples/excel/ejemplo_v0_1.xlsx` | Ejemplo de entrada Excel |
| `examples/excel/plantilla_v0_1.xlsx` | Plantilla de entrada Excel |

Se retiraron también los directorios vacíos y la caché compilada del adaptador.
`openpyxl` dejó de ser dependencia: no tenía consumidores de producto ajenos a
ese adaptador. La prueba de importación Excel se sustituyó por una comprobación de
ausencia del módulo y de la dependencia. La prueba de arquitectura impide importar
el adaptador retirado desde el núcleo.

Una carpeta generada `build/`, no versionada, conservaba copias antiguas del adaptador.
Se trasladó íntegra a `.qa/retire-build-before/`, ignorada por Git y fuera de las
rutas de compilación, para preservar su contenido. No es código activo ni parte
de la distribución. Las compilaciones posteriores usan las fuentes actuales.

## Archivos y capacidades conservados

Se comprobaron hashes SHA-256 de **26 archivos**, todos idénticos a la auditoría:
los archivos Python restantes de `rcwall`, el esquema JSON, el ejemplo canónico y
todos los archivos de `rcwall_web`. Esto incluye `ProjectDefinition`, los modelos
Pydantic, validadores, predicados, equivalencia y serialización decimal exacta.
No cambiaron identidades, relaciones, reglas geométricas ni contratos estructurales.

Se conservan `docs/excel_interface.md`, `docs/excel_decisions.md`, los ADR previos y
los cierres históricos de la hoja de ruta, con avisos de retiro. El historial de los
libros permanece en Git. Las capturas seleccionadas y el JSON de `outputs/ui/`
permanecen intactos. Las capturas de esta ejecución se guardan aparte, en
`outputs/ui-runs/excel-retire/` (artefactos locales ignorados).

Se actualizaron README, AGENTS, arquitectura, requisitos, hoja de ruta, convenciones,
documentación de contratos y guía web. No se agregaron pantallas, motores ni formatos.

## Compatibilidad

La eliminación de `rcwall.io.excel` es incompatible para sus consumidores. Por ello
el paquete pasa de 0.1.0 a **0.2.0**; no se publica como parche ni conserva funciones
vacías. La lista de funciones retiradas y la transición a web/JSON están en ADR-007.
**El esquema y contrato canónico V0.1 no cambiaron y no requieren migración.**

Un entorno antiguo puede conservar openpyxl como dependencia huérfana; no se desinstaló
de otros entornos del usuario. La instalación nueva no lo incluye. No se implementa
un convertidor XLSX ni un formato tabular sustituto.

## Verificación final

Se construyó un wheel desde una copia limpia de las fuentes y se instaló, sin modo
editable, en `.qa/retire-clean-env/` con los extras `dev,web,ui-test`. Se comprobó que
`rcwall` y `rcwall_web` se importaban desde ese entorno, sin utilizar las fuentes
editables del repositorio. El wheel contiene los estáticos web y no contiene módulos
Excel ni declara openpyxl en sus dependencias.

También se compiló desde la raíz con `python -m pip wheel --no-deps --wheel-dir
outputs/packages .`, después de apartar el build antiguo. Se inspeccionó ese wheel:
sin Excel, y con código y estáticos idénticos byte por byte al paquete probado.

| Comprobación | Resultado |
| --- | --- |
| pytest con `RCWALL_BROWSER_TESTS=1` | **162 aprobadas**, 10 de navegador, 36,32 s |
| Ruff check | Aprobado |
| Ruff format --check | Aprobado; 46 archivos |
| pip check del entorno limpio | Sin dependencias rotas |
| `find_spec('openpyxl')` y `find_spec('rcwall.io.excel')` | Ambos ausentes |
| Creación, validación de dimensiones, importación/exportación JSON | Pruebas HTTP y navegador aprobadas |
| Selección, zoom, desplazamiento y aislamiento entre sesiones | Pruebas Chromium aprobadas |
| Precisión decimal, datos gráficos y texto no confiable | Regresiones aprobadas |
| Integridad de núcleo, esquema, ejemplo JSON y web | 26 hashes idénticos |

Se revisaron visualmente las capturas locales de
[selección, zoom y desplazamiento](../outputs/ui-runs/excel-retire/test_browser_creation_editing_selection_zoom_pan_and_sessions/03-zoom-desplazamiento.png)
y [barra seleccionada con propiedades exactas](../outputs/ui-runs/excel-retire/test_browser_import_bars_untrusted_text_and_exact_export/04-barra-explicita.png).
Estos enlaces apuntan a artefactos de la ejecución local, no versionados; pueden
regenerarse con las pruebas de navegador.

La reducción de 212 a 162 pruebas corresponde al retiro de 50 pruebas Excel,
la eliminación de un caso de importación y la adición de una prueba de ausencia.
No se eliminaron pruebas de capacidades que permanecen en el producto.

Comandos de la verificación sobre la distribución instalada (PowerShell):

```powershell
$env:RCWALL_BROWSER_TESTS = '1'
$env:RCWALL_UI_OUTPUT = 'outputs/ui-runs/excel-retire'
.\.qa\retire-clean-env\Scripts\python.exe -m pytest
.\.qa\retire-clean-env\Scripts\python.exe -m ruff check .
.\.qa\retire-clean-env\Scripts\python.exe -m ruff format --check .
.\.qa\retire-clean-env\Scripts\python.exe -m pip check
```

Permanece una advertencia de deprecación HTTPX del TestClient de Starlette, ya presente
en la línea base. No hubo fallos de prueba. La verificación fue local en Windows con
Python 3.12.14; no se afirma ejecución hospedada de CI ni despliegue público.
