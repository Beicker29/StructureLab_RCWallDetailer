# ADR-007 — Retiro de Excel y web como interfaz principal

Estado: adoptado e implementado para RCWD-EXCEL-RETIRE-000. Fecha: 2026-10-23.
Sustituye únicamente las decisiones de mantener Excel como interfaz operativa de
ADR-001/002 y los compromisos Excel de ADR-004/005. Conserva sus decisiones de dominio,
identidad y precisión, y la arquitectura web de ADR-006.

## Problema y alternativas

Mantener libros, mapeos y validaciones de transporte Excel duplica una frontera de
entrada que ya no forma parte del producto solicitado. Las modificaciones históricas
de los libros tampoco deben tratarse como cambios del modelo canónico.

Se consideró mantener el adaptador como extra opcional o archivarlo como código ejecutable.
Ambas alternativas conservarían una API que habría que mantener y probar. Se adopta
su eliminación del producto activo; Git y la documentación histórica conservan la evidencia.

## Decisión

- La interfaz principal es la web local FastAPI de `rcwall_web`; JSON es el formato de
  intercambio. Se mantienen HTML/CSS/JavaScript/SVG, estado por pestaña y servidor sin
  almacenamiento compartido, restringido por el comando local a `127.0.0.1`.
- Se eliminan `src/rcwall/io/excel/` (cinco módulos), el generador
  `scripts/generate_excel_artifacts.py`, `tests/test_excel.py` y los dos libros bajo
  `examples/excel/`. No se sustituye Excel por otro formato tabular.
- Se retira `openpyxl` de las dependencias: sus únicos consumidores de producto eran
  `reader.py` y `writer.py` del adaptador; las pruebas Excel eran su otro consumidor.
- Se conservan `docs/excel_interface.md` y `docs/excel_decisions.md` con avisos explícitos
  de retiro, las entradas históricas de la hoja de ruta y los ADR previos. Las notas de
  actualización de esos ADR delimitan lo sustituido sin borrar la decisión original.
- Modelos Pydantic, predicados, validación, equivalencia, JSON, esquema y web permanecen
  intactos. Ningún modelo se elimina por haber sido consumido desde Excel.

## Compatibilidad y versiones

Se incrementa el paquete de **0.1.0 a 0.2.0**, como cambio incompatible durante desarrollo
pre-1.0. No se publica como parche: desaparece el paquete importable `rcwall.io.excel`
y sus símbolos públicos `create_template`, `generate_example`, `export_project`,
`inspect_workbook`, `read_project`, `validate_workbook`, `ExcelValidationError` y
`ExcelValidationReport`. No se mantienen alias ni adaptadores vacíos de compatibilidad.

Los consumidores deben dejar de invocar esa API y usar la web o `rcwall.io.json` con
documentos JSON canónicos. `read_project` de JSON conserva su comportamiento y no acepta
XLSX. Los proyectos que ya existen como JSON no requieren conversión. No se implementa
un convertidor automático de libros; el código anterior puede consultarse en Git para
recuperar un flujo histórico separado, no como capacidad de la versión activa.

**El contrato canónico sigue en 0.1.0.** El retiro de un transporte no cambia datos,
identidades, relaciones ni reglas; no requiere ni introduce una migración de esquema.

## Auditoría y preservación

La línea base fue de 212 pruebas aprobadas, con 10 pruebas Chromium ejecutadas.
El estado de Git estaba limpio; los nueve archivos retirados estaban versionados y
coincidían con `HEAD` tanto en la auditoría inicial como justo antes de eliminarlos.
Punto de recuperación anterior al retiro: `9b329f6af98cd8423904da72b0196bf385ec4074`.

Se detectó un archivo de bloqueo Office y se pospuso la eliminación de los libros hasta
que el usuario confirmó: «Cerrados, sin cambios pendientes». El archivo de bloqueo ya
no existía en la segunda inspección. Las ediciones previas de los libros están preservadas
en Git; no se revirtieron ni se regeneraron como parte del retiro.

## Consecuencias y límites

La distribución y una instalación limpia no deben contener módulos Excel ni requerir
openpyxl. Se retiran sus 50 pruebas específicas y el caso de importación del paquete
Excel; se agrega una comprobación de ausencia del adaptador/dependencia y se conserva
la cobertura de todas las capacidades restantes. La reducción del recuento no implica
suprimir pruebas del núcleo ni de la web.

Los entornos antiguos pueden conservar openpyxl porque pip no desinstala automáticamente
dependencias huérfanas. No es una dependencia del paquete 0.2.0; un entorno nuevo permite
verificarlo sin modificar otros consumidores locales del usuario.

La web mantiene su alcance actual: no se agregan pantallas, resolución de distribuciones,
estribos, reglas estructurales, DXF ni despliegue público en Render. Retirar Excel no
convierte las declaraciones existentes en resultados calculados.
