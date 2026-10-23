# Interfaz Excel V0.1 preliminar

Estado: organización de hojas aprobada; plantilla, generador y lector no implementados.
Excel será una interfaz sobre el modelo canónico. Las columnas y relaciones definitivas
deberán revisarse contra los contratos canónicos antes de su implementación.

## Hojas principales

| Hoja | Propósito previsto | Relaciones por concretar |
| --- | --- | --- |
| Proyecto | Identidad, versión de esquema y unidades del proyecto | Agregado de entrada |
| Geometrias | Definiciones geométricas reutilizables | Secciones, regiones y referencias |
| Regiones | Regiones de borde, alma u otros roles que se aprueben | Geometría propietaria |
| Referencias | Referencias geométricas utilizadas por instrucciones | Geometría e instrucciones de refuerzo |
| Configuraciones | Configuraciones de refuerzo asociadas a geometrías | Geometría, barras y estribos |
| Barras | Instrucciones de distribución longitudinal | Configuración, región y referencia |
| Estribos | Definiciones de conjuntos transversales | Configuración, región y representación geométrica |
| Asignaciones | Uso de configuraciones en muros y niveles | Identidades externas y configuración |
| Dibujo | Especificaciones de representación | Configuración, escala y plantilla |

## Hojas avanzadas

| Hoja | Propósito previsto | Condición de uso |
| --- | --- | --- |
| Vertices | Contornos y huecos asociados a propietarios geométricos | Cuando se requiera representación por vértices |
| Barras_Explicitas | Barras individuales suministradas como entrada | Cuando se utilice distribución explícita |
| Trayectorias | Primitivas que describen recorridos geométricos | Cuando se definan trayectorias |
| Distribucion_Z | Colocación de refuerzo transversal en altura | Cuando se suministre distribución vertical |

Las hojas avanzadas podrán permanecer vacías cuando no sean necesarias. El lector no
deberá confundir una hoja vacía válida con la ausencia de información requerida por
una variante seleccionada.

## Trabajo pendiente de RCWD-001B

La solicitud de RCWD-001 proporciona candidatos de columnas. Al retomarla se comprobará
su correspondencia con los modelos y se documentarán campos obligatorios, opcionales y
condicionales, enumeraciones, claves, relaciones y unidades. No se congela esa propuesta
mediante la estructura vacía de RCWD-000.

El generador programático deberá mantenerse sincronizado con el contrato versionado,
incorporar instrucciones, encabezados con unidades identificables, listas de enumeraciones
y distinción visual entre datos editables e información. Se prevé un ejemplo rectangular
con dos regiones de borde y un alma, sin simular posiciones de acero ni comprobaciones normativas.

La lectura deberá conservar hoja, fila y campo para los errores. No habrá macros,
dependencia de AutoCAD ni fórmulas que sustituyan al motor geométrico Python.
No se establecen todavía números de fila, rangos de edición, tolerancias o conversiones.

Los cambios de nombres de hojas o columnas deberán evaluarse como cambios de la interfaz,
con compatibilidad explícita respecto de las versiones de contrato que soporten.

## Ajuste requerido después de RCWD-001A

El contrato canónico ya distingue GeometryDefinition, ReinforcementConfiguration,
SectionDefinition (con materiales) y WallDefinition. SectionAssignment referencia
section_id, wall_id y level_id. El diseño inicial de nueve hojas no representa todavía
explícitamente todas esas entidades. RCWD-001B deberá definir y documentar su mapeo
sin duplicar configuraciones ni equiparar muro con sección.

Los nombres y columnas preliminares no prevalecen sobre el esquema 0.1.0. Debe revisarse
si conviene añadir hojas para secciones, muros y materiales o una representación equivalente.
Esa decisión no se adopta silenciosamente en RCWD-001A.

El adaptador deberá conservar cadenas decimales con más precisión que la capacidad
numérica nativa de Excel, convertir entradas de forma explícita y traducir las rutas
de ValidationIssue a celdas. La implementación y sus pruebas pertenecen a RCWD-001B.
