# Convenciones iniciales

Estas convenciones organizan el repositorio. Las decisiones que cambien el significado
estructural de un dato permanecen pendientes hasta su definición explícita.

## Nombres y módulos

- Distribución: `structurelab-rcwalldetailer`. Paquete importable: `rcwall`.
- Código Python: módulos, funciones y variables en `snake_case`; clases en `PascalCase`;
  constantes en `UPPER_SNAKE_CASE`.
- Identificadores de código y contratos en inglés; documentación de uso en español.
- Modelos y operaciones públicas nuevos deberán declarar tipos y documentar su alcance.
- Usar `src/rcwall/` y las fronteras de `architecture.md`. Evitar módulos genéricos
  `utils`, capas de repositorio o bases abstractas sin un caso concreto.

## Unidades y coordenadas

- Unidad interna inicial de longitud: milímetro. En futuros campos escalares expuestos,
  expresar la unidad, por ejemplo con el sufijo `_mm`, cuando corresponda.
- No mezclar valores de unidades distintas ni inferir conversiones a partir de su magnitud.
- Un cero numérico y un valor ausente no son equivalentes. Los valores predeterminados
  con significado geométrico requieren una decisión explícita.
- El origen local, los ejes de sección, el signo de Z, las orientaciones de contorno,
  las tolerancias y la representación angular siguen pendientes. No se establece un
  origen implícito ni se ajustan coordenadas automáticamente.
- Los formatos de número de Excel no definen las unidades ni la precisión geométrica.

## Identificadores y referencias

Los identificadores del dominio deberán ser independientes de las filas de Excel y de
los handles CAD. No renumerarlos al ordenar un libro. La identidad de una entidad y su
etiqueta de presentación son conceptos diferentes.

Quedan pendientes el alcance de unicidad, la sensibilidad a mayúsculas, caracteres
permitidos, generación automática, referencias a catálogos externos y política de
duplicados. Esas reglas se fijarán junto con los contratos, no mediante normalizaciones
silenciosas del lector.

## Versionado

La versión del paquete reside en `pyproject.toml`; RCWD-000 comienza en `0.0.1`.
Se emplearán versiones de paquete `MAJOR.MINOR.PATCH`. El esquema canónico tendrá una
versión explícita separada: no existe un esquema publicado en este hito.

Una modificación incompatible debe identificar consumidores afectados, nueva versión
de esquema y tratamiento de entradas anteriores. Antes de publicar RCWD-001 se decidirá
la compatibilidad soportada y si las migraciones son automáticas o explícitas. No se
deduce una versión del contrato a partir del nombre del archivo Excel.

## Pruebas y calidad

Ejecutar las pruebas con `pytest` después de instalar `.[dev]`. El modo de importación
es `importlib`; no añadir `src` manualmente a `sys.path`. Las comprobaciones iniciales
verifican metadata de la distribución y la importación de los módulos reservados.

Para comportamientos futuros, organizar pruebas según responsabilidad bajo `tests/`
(`domain`, `geometry`, `validation`, `io/excel`, `detailing`, `exporters/dxf`) cuando
existan casos reales. Usar nombres `test_*.py`, datos pequeños explícitos y casos válidos,
inválidos y de frontera. Usar `tmp_path` para archivos temporales. Las pruebas de datos
no se deben presentar como verificación normativa.

`ruff` aplica reglas de errores, nombres/importaciones, modernización y errores comunes
(`E`, `F`, `I`, `UP`, `B`) y formato con ancho de 100 caracteres. No desactivar reglas
globalmente para ocultar un fallo puntual.

## Archivos y decisiones

Documentación UTF-8 en `docs/`. ADR en `docs/adr/ADR-NNN-descripcion.md`, con problema,
alternativas, decisión, consecuencias y estado. Referenciar el ADR desde la documentación
afectada. Distinguir aprobación conceptual y ejecución comprobada.

Salidas regenerables en `outputs/` o `generated/`, ignoradas por Git. Ejemplos y fixtures
que deban conservarse se ubicarán en rutas explícitas versionadas al implementarse su
hito. No ignorar globalmente `.xlsx`, `.json` ni `.dxf`: pueden ser entregables legítimos.
`.work/` almacena material local no activo y no debe importarse desde el paquete.
