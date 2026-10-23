# Propuesta inicial de contratos

Estado: catálogo conceptual de RCWD-000. No hay clases estructurales implementadas,
campos obligatorios congelados, JSON Schema publicado ni versión de esquema liberada.
La versión `0.0.1` del paquete no es una versión del contrato de datos.

Los nombres siguientes describen responsabilidades previstas. Su composición exacta,
cardinalidades y correspondencia con las tablas Excel se definirán en RCWD-001.

| Entidad propuesta | Responsabilidad conceptual | Decisiones abiertas |
| --- | --- | --- |
| `ProjectDefinition` | Agrupar la definición original del proyecto y sus referencias | Metadatos, colecciones y alcance de identificación |
| `SectionDefinition` | Definir una sección y referenciar su representación geométrica | Separación entre geometría reutilizable y configuración de refuerzo |
| `RegionDefinition` | Identificar una región de una sección y su función | Roles, representación paramétrica o poligonal y pertenencia |
| `BarLayoutDefinition` | Conservar instrucciones paramétricas o explícitas de barras longitudinales | Patrones, referencias, offsets y parámetros condicionales |
| `LongitudinalBar` | Representar una barra individual en el modelo común | Distinción entre dato explícito de entrada y barra resuelta, coordenadas y trazabilidad |
| `TransverseAssembly` | Agrupar elementos de refuerzo transversal | Composición, identidad, representación original y resuelta |
| `BentBarDefinition` | Describir una barra doblada y su trayectoria | Primitivas, radios, ganchos y reglas admitidas |
| `VerticalPlacement` | Definir la distribución de un conjunto transversal en altura | Referencia vertical, intervalos, espaciamiento y extremos |
| `DetailingResult` | Contener geometría calculada, separada de las instrucciones originales | Representación común de salida, procedencia y resultados parciales |
| `ValidationReport` | Comunicar diagnósticos de datos, relaciones y geometría | Niveles de severidad, códigos estables y localización de origen |
| `DrawingSpecification` | Describir la presentación y el destino del resultado resuelto | Escalas, plantillas, identificación y relación con configuraciones |

## Relaciones previstas

`ProjectDefinition` agrupa definiciones de secciones y refuerzo. Una sección referencia
una geometría y regiones. Las instrucciones longitudinales y transversales se asocian a
una configuración y a regiones compatibles. Las asignaciones relacionarán configuraciones
con muros y niveles; su entidad definitiva y sus catálogos externos están pendientes.

`VerticalPlacement` relaciona una asignación con refuerzo transversal. `DrawingSpecification`
identifica la presentación solicitada para un resultado. `DetailingResult` conservará
trazabilidad hacia las definiciones que lo originaron sin sobrescribirlas.

Las referencias geométricas reutilizables y las configuraciones indicadas en Excel
requieren contratos propios o componentes del agregado. Esta decisión debe tomarse
antes de traducir las hojas en modelos; una fila no equivale necesariamente a una entidad.

## Entrada y resultado

Los patrones `LINEAR_COUNT`, `LINEAR_SPACING` y `EXPLICIT` forman parte del alcance
previsto de RCWD-001. Los valores exactos de sus parámetros y las reglas condicionales
todavía requieren revisión. Una instrucción de cantidad o espaciamiento no es una lista
de coordenadas resueltas. No se producirán barras ficticias para completar una salida.

La representación común de barras resueltas debe permitir a los exportadores trabajar
sin conocer el patrón original. No se decide aquí si la barra explícita de entrada y
`LongitudinalBar` compartirán estructura o tendrán tipos distintos.

## Versionado y validación

El modelo canónico será tipado y serializable a JSON. Su versión será explícita e
independiente de la versión de la aplicación. El JSON Schema se derivará de los modelos
en RCWD-001; la compatibilidad, las migraciones y los lectores admitidos se especificarán
antes de publicar la primera versión.

Se deberán distinguir validación local de tipos/campos, integridad entre entidades y
validez geométrica. La validación normativa futura tendrá norma y alcance explícitos.
`ValidationReport` no equivaldrá a una certificación estructural.

Consultar [requisitos pendientes](requirements.md#decisiones-pendientes) y
[ADR-002](adr/ADR-002-canonical-data-model.md). No incorporar automáticamente los campos
del borrador local de RCWD-001 al contrato definitivo.
