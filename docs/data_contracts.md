# Contratos canónicos V0.1

Estado: implementados en RCWD-001A. Versión del esquema: `0.1.0`, independiente de
la versión de paquete. Los modelos viven en `rcwall.domain.models`; el esquema
se genera desde ellos, nunca desde Excel. No se reutilizó el borrador archivado.

## Entidades y relaciones

| Contrato | Contenido y relaciones implementadas |
| --- | --- |
| ProjectDefinition | project_id, schema_version, units y colecciones de entidades; units solo admite mm |
| GeometryDefinition | geometry_id y shape discriminada entre RECTANGLE/POLYGON; descripción opcional |
| RegionDefinition | region_id, geometry_id, role (BOUNDARY/WEB/OTHER) y shape explícita |
| GeometricReference | reference_id, geometry_id, kind=LINE y extremos distintos start/end |
| ReinforcementConfiguration | config_id, geometry_id y descripción opcional; no duplica geometría |
| BarLayoutDefinition | layout_id, config_id, distribution y region_id opcional |
| SectionDefinition | section_id, geometry_id, config_id y materials; la configuración referencia exactamente la misma geometry_id |
| WallDefinition | wall_id identifica el muro físico; descripción opcional |
| SectionAssignment | assignment_id, wall_id, level_id y section_id |
| ValidationReport | issues, scope=DATA_ONLY_NOT_STRUCTURAL_COMPLIANCE y valid calculado desde issues |

Las colecciones de ProjectDefinition son `geometries`, `regions`, `references`,
`configurations`, `bar_layouts`, `sections`, `walls`, `assignments`, `bent_bars`,
`transverse_assemblies`, `vertical_placements` y `drawings`. Se admiten colecciones
vacías: un catálogo parcial sin referencias rotas es una definición válida de datos,
no una sección detallada ni un proyecto listo para diseño.

Los IDs de todas las entidades, incluido project_id y las barras explícitas, son únicos
en un único espacio de nombres del proyecto. Las referencias pueden repetirse.
Una geometría admite varias configuraciones; una configuración puede referenciarse desde
varias secciones. Cada sección incorpora sus propias especificaciones de materiales.

Una sección puede asignarse a varios muros/niveles y un muro puede cambiar de sección
entre niveles. V0.1 admite como máximo una asignación por par wall_id/level_id:
subdivisiones del mismo muro en un nivel aún no están representadas y se rechazan.
level_id es una etiqueta externa estable; no existe catálogo de niveles ni elevaciones
en V0.1. No se afirma haber validado su existencia en un modelo de edificio.

## Materiales

`SectionMaterials` exige `concrete` y `reinforcement`, cada uno un
`MaterialSpecification` con texto no vacío `specification`. Puede incorporar
`properties`: declaraciones `name`, `value` decimal y `unit` explícita.
No puede repetirse un nombre de propiedad dentro de una especificación.

No se inventan resistencias, módulos, grados de acero ni unidades de propiedades.
El texto y las propiedades se conservan y comparan literalmente/numericamente según su
tipo; no se interpretan como cumplimiento de una norma. Distinta especificación declarada
produce distinta definición de sección, aunque una equivalencia material física
pudiera demostrarse en otro contexto. Materiales por barra o por conjunto siguen pendientes.

## Geometría y coordenadas

El sistema local es de mano derecha: xy horizontal y z vertical positivo.
RECTANGLE requiere origin explícito (esquina inferior izquierda), length_mm en +x
y thickness_mm en +y, ambos positivos. Es un rectángulo alineado con esos ejes;
una figura rotada puede declararse como polígono, sin aplicar una transformación automática.

POLYGON requiere outer, una secuencia de al menos tres Point2D (x_mm, y_mm), y admite
holes como secuencias adicionales. Un único contorno exterior simple, conectado,
antihorario; huecos horarios, estrictamente interiores y disjuntos. El cierre es implícito.
Repetir el primer punto al final es un error explícito, no un caso que el lector corrija.

Se rechazan vértices repetidos, retrocesos sobre aristas, autointersecciones, área nula,
orientación incorrecta, huecos exteriores, tangentes, superpuestos o anidados.
Se permiten puntos intermedios collineales sin retroceso. No se soportan multipolígonos,
arcos, islas dentro de huecos ni transformaciones local/global (GEO-04).
Los casos no representables se rechazan por tipo/estructura; no se reparan.

Regiones y geometrías se validan individualmente. No se implementan todavía cobertura
o partición del muro por regiones, contención de barras/regiones en el hormigón,
recubrimientos, choques ni separación mínima de acero. Una referencia geométrica no
se recorta automáticamente a una región.

## Patrones longitudinales

La unión discriminada `distribution` permite ampliar variantes en versiones posteriores.

| pattern | Campos requeridos | Campos opcionales |
| --- | --- | --- |
| LINEAR_COUNT | reference_id, quantity entera positiva, diameter_mm positivo, start_offset_mm y end_offset_mm no negativos | alignment |
| LINEAR_SPACING | reference_id, diameter_mm y spacing_mm positivos, offsets no negativos, spacing_policy, alignment | Ninguno |
| EXPLICIT | bars no vacía; cada barra declara bar_id, position y diameter_mm positivo | Ninguno |

Los offsets deben declararse incluso si son cero. No se combinan quantity y spacing_mm.
EXPLICIT rechaza parámetros lineales y no necesita referencia lineal. Todas las variantes
rechazan campos desconocidos. La geometría de referencia y la región, si se indica,
deben pertenecer a la misma geometry_id que la configuración.

spacing_policy y alignment son instrucciones textuales no vacías, preservadas sin
normalización ni interpretación. No hay catálogo normativo ni algoritmo aprobado para
ellas; aceptar el contrato no significa poder resolver esas instrucciones. En COUNT,
alignment ausente queda ausente y no implica centrar o alinear al inicio.
region_id ausente no genera ni asigna una región ficticia.

No se calculan posiciones, cantidad a partir de separación, espaciado a partir de
cantidad, ajustes de extremos ni factibilidad de los offsets. Esas comprobaciones
dependen de políticas de distribución pendientes. Las barras EXPLICIT son datos
individuales aportados por el usuario, no resultados de un motor.

## Contratos preparados, todavía no resueltos

| Contrato | Campos conocidos | Límite explícito |
| --- | --- | --- |
| BentBarDefinition | bent_bar_id, definition_status, diameter_mm y description opcionales | definition_status exige UNRESOLVED; sin trayectoria, radios ni ganchos |
| TransverseAssembly | assembly_id, config_id, definition_status; region_id y description opcionales; bent_bar_ids | UNRESOLVED; relaciones validadas, sin geometría calculada |
| VerticalPlacement | placement_id, assignment_id, assembly_id, definition_status, z_start_mm, z_end_mm; spacing_mm y spacing_policy opcionales | UNRESOLVED; z_end > z_start y compatibilidad de configuración, sin ubicaciones calculadas |
| DrawingSpecification | drawing_id, section_id, definition_status; template_id y drawing_scale opcionales | UNRESOLVED; escala positiva si existe, sin dibujo ni catálogo de plantillas |
| DetailingResult | project_id, schema_version y status=NOT_IMPLEMENTED | No admite geometría resuelta ni afirmaciones normativas |

Un conjunto no repite una misma bent_bar_id. Las barras dobladas pueden referenciarse
sin duplicar su declaración. Las colocaciones verticales deben apuntar a conjuntos
de la configuración correspondiente a la sección asignada. Los valores Z se conservan
como coordenadas declaradas; no se infieren elevaciones desde level_id.
Campos futuros requieren evolución explícita del contrato; no se admiten diccionarios
de extensiones arbitrarios que el validador no comprenda.

## Validación completa y diagnósticos

1. `ProjectDefinition.model_validate` comprueba tipos, variantes, finitud, dimensiones,
   obligatoriedad y condiciones locales.
2. `validate_references` comprueba unicidad global, existencia y compatibilidad.
3. `validate_geometry` comprueba la topología y orientación mediante predicados exactos.

La entrada pública `rcwall.validation.validate_definition` coordina las tres etapas.
Si hay errores de tipos, no ejecuta las etapas que necesitan modelos válidos. Si los
tipos son válidos, agrega errores de referencias y geometría. Devuelve ValidationOutcome
con project aceptado solo cuando report.valid es verdadero. `validate_project`
devuelve únicamente el reporte para un modelo existente, reconstruyéndolo para detectar
datos introducidos por mecanismos Pydantic que omiten validación.

Cada ValidationIssue contiene stage (types/references/geometry/json), path como tupla
de campos e índices desde cero, code y description. Ejemplo:
`("assignments", 0, "section_id")`, código `missing_reference`.
Los discriminadores pueden aparecer en rutas de errores Pydantic. Los códigos locales
de Pydantic pueden variar entre versiones de esa biblioteca; los códigos de referencias
y geometría pertenecen a RCWall. El adaptador Excel deberá traducir rutas a hoja/fila/campo.

El modelo es inmutable y usa tuplas para colecciones. No puede aceptarse un modelo
solo porque su constructor pasó: las relaciones y topología requieren la entrada completa.

## JSON, precisión y esquema

`rcwall.io.json` ofrece loads_project/dumps_project, read_project/write_project,
validate_json, project_json_schema y write_project_schema. La escritura y lectura
ejecutan la validación completa. Un error no trunca el archivo de destino antes de
validar los datos. La escritura no constituye una transacción ante fallos del sistema de archivos.

Los decimales usan Decimal y se escriben como cadenas; las cantidades son enteros JSON.
Se conservan valor, dígitos decimales y escala de Decimal, sin redondeo. No se promete
preservar la grafía original (por ejemplo signo + o ceros iniciales), espacios JSON u
orden de claves del archivo fuente. dumps/loads/dumps produce el mismo JSON canónico:
claves ordenadas, UTF-8, indentación fija, colecciones en su orden original y salto final.

El lector admite además números JSON decimales mediante parse_float=Decimal; no pasa
por float binario. Rechaza claves duplicadas, NaN/Infinity, unidades distintas a mm y
versiones distintas a 0.1.0. No hay migraciones hipotéticas.

El esquema generado usa Draft 2020-12 y describe la serialización canónica con decimales
como strings. La positividad de esos strings, relaciones entre entidades y topología
requieren la validación Python adicional. Cambios incompatibles requieren nueva versión
de esquema. Es la primera versión publicada, sin esquemas previos que migrar.

## Equivalencia

`geometry.polygons.geometrically_equivalent` compara regiones geométricas exactas en
el mismo marco local: rectángulo/polígono, índice inicial del contorno, orden de huecos
y puntos collineales intermedios no cambian el resultado. La representación fuente queda
intacta. No se comparan objetos bajo traslación/rotación o transformaciones globales.

`validation.equivalence.compare_section_definitions` compara geometría, materiales
e instrucciones longitudinales; también detecta diferencias en membresía, región y
diámetros transversales declarados. Excluye IDs/descripciones y orden de elementos
independientes, conservando multiplicidades, dirección de referencias y parámetros.
Una diferencia conocida produce DIFFERENT; si hay conjuntos transversales sin semántica
resuelta y ninguna diferencia conocida, devuelve UNDETERMINED; EQUIVALENT se limita al
subconjunto de definiciones soportadas. No fusiona, renombra ni reasigna entidades.

`compare_section_physical_equivalence` devuelve siempre UNDETERMINED para secciones
existentes de un proyecto válido. No se deduce equivalencia física entre patrones
distintos ni a partir de coincidencias parciales. Ver ADR-004 y ADR-005.
