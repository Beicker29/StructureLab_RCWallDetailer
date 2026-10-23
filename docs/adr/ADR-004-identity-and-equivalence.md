# ADR-004 — Identidad y equivalencia

Estado: adoptado e implementado en el subconjunto RCWD-001A. Fecha: 2026-10-23.
Resuelve identidad y comparaciones pendientes de ADR-002/003; no sustituye su separación
entre definiciones y resultados.

Evolución: [ADR-007](ADR-007-retire-excel.md) retira el adaptador Excel.
Sus compromisos de mapeo son históricos; las decisiones de identidad y equivalencia
de este ADR permanecen vigentes sin cambios de contrato.

## Problema

La identidad del muro físico no puede confundirse con la de una sección reforzada.
Tampoco se debe duplicar geometría o configuración para asignarla a otro nivel. Dos
representaciones geométricas distintas pueden describir el mismo contorno; dos secciones
con igual contorno pueden diferir por refuerzo o materiales. Detectar equivalencia no
autoriza a cambiar identidades o fusionar entidades.

## Alternativas consideradas

1. Identificar secciones mediante fila Excel, muro o geometría solamente. Impide distinguir
   variaciones de materiales/refuerzo y hace inestable la identidad al reordenar datos.
2. Usar hashes de coordenadas redondeadas y fusionar coincidencias. Mezcla identidad con
   comparación y puede eliminar diferencias pequeñas pero reales.
3. Usar IDs explícitos y relaciones; comparar propiedades mediante operaciones separadas,
   con un alcance declarado y resultado indeterminado donde falta semántica.

## Decisión adoptada

Adoptar la tercera alternativa, implementando ID-01/02 y EQ-01 a EQ-06:

- Todos los IDs de entidades pertenecen a un único espacio de nombres del proyecto.
  Son cadenas explícitas no vacías, sin espacios y sensibles a mayúsculas; no se generan,
  normalizan ni vinculan a filas Excel o handles CAD. Se incluyen IDs de barras explícitas.
- GeometryDefinition se referencia desde ReinforcementConfiguration. SectionDefinition
  asocia geometría, configuración compatible y materiales. WallDefinition tiene identidad
  independiente; SectionAssignment referencia muro, nivel y sección.
- Una configuración puede reutilizarse en varias secciones. La compatibilidad referencial
  exige la misma geometry_id, incluso si otra geometría pudiera compararse como equivalente:
  la equivalencia nunca reescribe referencias.
- En V0.1 se admite una asignación por muro/nivel. Se rechazan asignaciones ambiguas porque
  todavía no hay un contrato para representar subdivisiones en ese par.
- level_id y template_id son referencias externas declaradas. No se simulan sus catálogos.
- EQ-01: se compara el contorno ocupado exacto en el mismo marco local, independientemente
  de RECTANGLE/POLYGON, punto inicial, orden de huecos y puntos collineales redundantes.
  La clave de comparación no modifica el original. No se aplica traslación ni rotación.
- EQ-02/03: las definiciones de sección comparan geometría, materiales e instrucciones
  longitudinales y los datos transversales conocidos (membresía, región y diámetro).
  Cualquier diferencia conocida de esos valores produce DIFFERENT.
  Se excluyen IDs, descripciones y orden de elementos independientes, conservando multiplicidad.
- EQ-04: equivalencia de definición y equivalencia física son operaciones diferentes.
  Las definiciones transversales incompletas impiden afirmar equivalencia completa;
  la equivalencia física siempre es UNDETERMINED hasta disponer de refuerzo resuelto.
- EQ-05/06: ninguna comparación fusiona, renombra o reasigna entidades, ni usa redondeo.

La configuración se conserva una sola vez por ID. Una sección con otro refuerzo o material
debe declararse con otra identidad si se requiere conservar ambas variantes. El programa
valida unicidad dentro de una instantánea; no implementa seguimiento histórico entre archivos.

## Consecuencias

Los exportadores futuros trabajarán con resultados, sin decidir equivalencia física a
partir del patrón de entrada. Las aplicaciones deben consultar el alcance de cada
comparación y no interpretar UNDETERMINED como verdadero o falso.

La coincidencia numérica 1.0/1.00 permite equivalencia de valor sin perder su escala
declarada en el JSON original. Diferencias de especificación material se comparan como
declaraciones, sin inferir equivalencia normativa de nombres o unidades.

Los IDs no son huellas del contenido. Los modelos son inmutables, pero el autor debe
mantener la estabilidad entre revisiones. No existen fusiones ni migraciones automáticas.
Los campos de Excel deberán revisarse para representar sección y muro por separado.
