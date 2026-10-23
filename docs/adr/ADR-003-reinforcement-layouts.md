# ADR-003 — Distribución paramétrica de refuerzo

Estado: adoptado conceptualmente para RCWD-000; reglas de resolución pendientes.
Fecha: 2026-10-23.

## Problema

Una distribución de refuerzo puede expresarse mediante instrucciones de cantidad o
espaciamiento, o mediante barras suministradas individualmente. El sistema debe preservar
la intención de entrada y permitir una representación común para los exportadores,
sin confundir instrucciones con geometría ya calculada.

## Alternativas consideradas

1. Admitir exclusivamente coordenadas explícitas de todas las barras.
2. Admitir exclusivamente patrones paramétricos y descartar la entrada tras resolverlos.
3. Admitir ambos modos, preservar las instrucciones y producir resultados geométricos comunes.

La primera obliga al usuario a resolver todo antes de ingresar datos. La segunda pierde
trazabilidad y limita configuraciones que no encajan en patrones. La tercera requiere
reglas claras por variante y un modelo de resultado independiente.

## Decisión adoptada

Admitir conceptualmente patrones paramétricos y explícitos. Mantener sus definiciones
originales separadas de `DetailingResult`. La geometría resuelta tendrá un contrato común
que permita exportarla sin que el exportador interprete patrones.

RCWD-001 prevé `LINEAR_COUNT`, `LINEAR_SPACING` y `EXPLICIT`. La extensibilidad deberá
permitir futuras variantes sin cambiar la separación fundamental entre instrucciones y
resultados. No se prescribe todavía una jerarquía de clases o un registro de plugins.

## Consecuencias

- Los contratos validarán parámetros obligatorios e incompatibles de cada variante.
- Los motores conservarán trazabilidad hacia la instrucción original.
- Espaciamiento, alineación, offsets, extremos, recubrimientos, radios y ganchos requieren
  decisiones explícitas antes de implementarse; no se derivan de este ADR.
- Las coordenadas explícitas son entradas, no resultados simulados de un motor inexistente.
- No se implementa resolución ni se certifica cumplimiento estructural en RCWD-000.
