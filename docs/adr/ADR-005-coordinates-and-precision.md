# ADR-005 — Coordenadas y precisión decimal

Estado: adoptado e implementado para RCWD-001A. Fecha: 2026-10-23.
Resuelve las convenciones locales y de precisión que RCWD-000 dejó pendientes.
GEO-04 y tolerancias de futuros cálculos aproximados siguen aplazados.

## Problema

La representación canónica debe conservar valores declarados y orientar contornos de
forma inequívoca. Redondear entradas, usar un epsilon de diseño o reparar polígonos
puede cambiar el significado de una sección sin que el usuario lo haya solicitado.
Además, operaciones Decimal dependen de un contexto de precisión, mientras que los
predicados de topología de segmentos rectos pueden evaluarse exactamente.

## Alternativas consideradas

1. float binario y epsilon global: sencillo, pero pierde dígitos decimales y mezcla
   tolerancia computacional con aceptación geométrica o de diseño.
2. Decimal para entrada y todas las operaciones: conserva la declaración, pero sumas y
   productos pueden redondearse si exceden el contexto de precisión activo.
3. Decimal para contratos, JSON decimal textual y Fraction para predicados exactos,
   con geometría inválida rechazada y sin reparaciones.

## Decisión adoptada

Adoptar la tercera alternativa:

- GEO-01/02: marco local de mano derecha, xy horizontal y +z vertical.
- GEO-03: exteriores antihorarios y huecos horarios vistos desde +z. El lector no invierte
  anillos. Un cierre explícito repetido se rechaza; los anillos tienen cierre implícito.
- GEO-05: rectángulos alineados con ejes y polígonos simples por vértices con un exterior
  y huecos interiores disjuntos. El origen inferior izquierdo del rectángulo es obligatorio;
  no se presupone (0,0). Sus dimensiones recorren +x y +y.
- GEO-04: sin transformaciones local/global, inferencia de origen global ni elevaciones
  a partir de identificadores de nivel.
- NUM-01: Decimal conserva valor y escala declarados. La API acepta Decimal, string o
  int y rechaza bool/float. El JSON canónico emite strings decimales, enteros para cantidades.
  La lectura de tokens decimales JSON se realiza directamente con parse_float=Decimal.
- NUM-02/03: no hay tolerancias de aceptación ni epsilon global. Las orientaciones,
  intersecciones, áreas y comparaciones geométricas usan Fraction a partir de Decimal,
  sin depender del contexto aritmético Decimal.
- NUM-04: no se cierran con puntos adicionales, invierten, redondean, desplazan ni reparan
  entradas. Solo las claves derivadas de comparación omiten puntos collineales redundantes;
  las definiciones originales permanecen intactas.

Se rechazan explícitamente autointersecciones, vértices repetidos, retrocesos, área nula,
orientación incorrecta y huecos que tocan/cruzan el exterior o se tocan/solapan/anidan.
No se soportan multipolígonos, curvas o islas dentro de huecos. No se implementa una
operación geométrica adicional para reparar o aproximar estos casos.

## Consecuencias

La serialización canónica es reproducible, aunque no conserva espacios, orden de claves
o grafías equivalentes como signo + y ceros iniciales del archivo fuente. Sí conserva
los datos estructurales sin convertirlos en float ni redondearlos.

JSON Schema describe los campos decimales canónicos como strings; la positividad y las
relaciones/topología requieren además el validador Python. El esquema no se presenta
como sustituto de controles semánticos.

El coste de los predicados crece con el número de segmentos y la cantidad de dígitos;
las comprobaciones de intersecciones son cuadráticas. No se promete rendimiento para
contornos masivos ni se imponen límites de precisión que alteren silenciosamente valores.
Un futuro motor con cálculos aproximados deberá justificar sus tolerancias computacionales.

Excel requerirá una política explícita para conservar decimales que excedan su precisión
numérica nativa. Esa adaptación pertenece a RCWD-001B, sin modificar este contrato.
