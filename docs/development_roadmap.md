# Hoja de ruta

RCWD-000 establece la base aprobada. RCWD-001 se divide en contratos canónicos
(RCWD-001A, implementado) e interfaz Excel (RCWD-001B, implementado). La división RCWD-002
a RCWD-006 es una propuesta de planificación: requiere aprobación de alcance y criterios
detallados antes de implementar cada hito.

| Hito | Objetivo | Dependencias | Criterios generales de aceptación | Estado |
| --- | --- | --- | --- | --- |
| RCWD-000 | Inicialización, arquitectura y entorno técnico | Ninguna | Paquete instalable e importable; documentación y ADR; pruebas y revisión estática iniciales | Base implementada |
| RCWD-001A | Contratos canónicos V0.1 | RCWD-000 | Tipos y relaciones; sección/muro/materiales; patrones de entrada; polígonos; precisión; JSON, esquema y pruebas | Implementado: 115 pruebas pasan, incluidas diez originales; Ruff sin errores |
| RCWD-001B | Plantilla e interfaz Excel V0.1 | RCWD-001A | Generación/lectura sincronizada con modelos; mapeo de secciones y muros; reportes hoja/fila/campo; ida/vuelta preservando unidades y decimales | Implementado: 17 hojas españolas, 50 pruebas Excel |
| RCWD-002 | Representaciones y operaciones geométricas reutilizables | RCWD-001, decisiones de coordenadas y tolerancias | Casos geométricos admitidos documentados; operaciones deterministas probadas; rechazo de casos no soportados; independencia de Excel/CAD | Propuesto |
| RCWD-003 | Resolución de refuerzo longitudinal | RCWD-001 y RCWD-002, políticas de distribución aprobadas | Patrones acordados producen una representación común; instrucciones preservadas; trazabilidad y pruebas de extremos/conflictos | Propuesto |
| RCWD-004 | Resolución transversal y distribución vertical | RCWD-001 y RCWD-002; integración con RCWD-003 cuando aplique | Trayectorias y colocación Z verificables; parámetros explícitos de doblado/anclaje; ninguna geometría inferida sin regla aprobada | Propuesto |
| RCWD-005 | Exportación DXF editable | Resultados estables de RCWD-003/004 y especificación de dibujo aprobada | DXF legible en herramientas acordadas; entidades editables, escala y unidades verificadas; exportador sin reglas de detallado | Propuesto |
| RCWD-006 | Integración y preparación de una versión utilizable | RCWD-001 a RCWD-005 | Flujo completo con ejemplos de referencia, errores reproducibles, pruebas de integración/regresión y documentación de límites | Propuesto |

## Puertas de avance

Cada hito debe declarar qué está implementado y probado, qué casos rechaza y qué
decisiones siguen abiertas. Los criterios se comprueban con datos de referencia revisados,
sin inventar resultados normativos. Los cambios del contrato requieren una decisión de
versionado antes de ajustar lectores, motores o exportadores.

RCWD-001 incluye la validación geométrica necesaria para sus datos de entrada; esto no
equivale al conjunto de operaciones de resolución de RCWD-002. Las operaciones de
topología reutilizables se ubicarán desde el inicio en `geometry`.

Las verificaciones normativas no quedan autorizadas por esta numeración. Antes de
programarlas se requiere definir norma, edición, jurisdicción, entradas y alcance, y
asignarles un hito o alcance aprobado independiente. Tampoco se incluyen una interfaz
gráfica, integración con AutoCAD ni formatos CAD adicionales.

## Cierre de RCWD-000

La estructura debe permitir comenzar RCWD-001 en `domain`, `validation`, `geometry`
e `io/excel` sin renombrar el paquete ni mover responsabilidades entre adaptadores y
dominio. Los borradores de una implementación interrumpida no constituyen aceptación
de RCWD-001 y deben revisarse antes de cualquier reutilización.

## Cierre de RCWD-001A

Se conservó la arquitectura y se incorporó Pydantic como única dependencia directa de
ejecución. Contratos inmutables, JSON y validación completa están implementados; el
dominio no importa adaptadores ni operaciones geométricas. La equivalencia geométrica
cubre el mismo marco local; la equivalencia física del refuerzo no está implementada.

Para RCWD-001B, el diseño preliminar de hojas debe resolver el mapeo de SectionDefinition,
WallDefinition y materiales. No se debe volver a usar config_id como sustituto de la
identidad de sección ni wall_id como identidad de sección. Las políticas textuales y
los contratos UNRESOLVED deben conservar su estado explícito, sin valores por defecto
de Excel que alteren el significado estructural.

## Cierre de RCWD-001B

Interfaz de 17 hojas aprobadas implementada exclusivamente en io/excel. Generador, lector,
validación y diagnósticos reutilizan contratos 0.1.0 sin modificarlos. Secciones, muros,
materiales y asignaciones tienen su mapeo explícito. Los decimales se almacenan como texto
y el ciclo canónico sin modificaciones conserva exactamente su serialización.

La revisión incluye 165 pruebas (115 previas + 50 Excel), Ruff y vistas de las hojas.
La interacción nativa de Microsoft Excel no se ejecutó. Las políticas libres y los estados
pendientes siguen sin resolución algorítmica; RCWD-002 y posteriores conservan sus puertas
de aprobación y definición de alcance.
