# ADR-002 — Modelo de datos canónico

Estado: adoptado para RCWD-000. Fecha: 2026-10-23.

## Problema

Excel es una interfaz de ingreso, pero sus filas, formatos y hojas no bastan para definir
identidad, relaciones, tipos y compatibilidad de datos entre lectores, motores y exportadores.
El proyecto necesita un contrato estable, verificable e independiente del archivo de entrada.

## Alternativas consideradas

1. Definir el contrato exclusivamente mediante columnas Excel.
2. Intercambiar diccionarios o JSON sin esquema, dejando cada consumidor interpretarlos.
3. Mantener contratos tipados y versionados, serializables a JSON, con validación explícita.

La primera liga el dominio a una interfaz. La segunda permite interpretaciones divergentes
y dificulta detectar cambios incompatibles. La tercera añade trabajo de definición y evolución
del esquema, a cambio de un significado común.

## Decisión adoptada

Adoptar la tercera alternativa. Conservar separados `ProjectDefinition`, `DetailingResult`
y `ValidationReport`. Los adaptadores operarán contra una versión explícita del contrato.
JSON será el formato canónico de intercambio y se generará un JSON Schema a partir de
los modelos cuando se implemente RCWD-001.

Pydantic es la tecnología prevista por la solicitud de RCWD-001, pero no se instala ni
se implementan modelos estructurales completos en RCWD-000.

## Consecuencias

- La plantilla Excel deberá sincronizarse con los contratos y no convertirse en su única fuente.
- Se distinguen tipos/campos, integridad de referencias, geometría y futuras reglas normativas.
- La versión del paquete y la versión del esquema evolucionan de forma explícita y separada.
- Campos obligatorios, cardinalidades, migraciones y compatibilidad quedan pendientes de
  revisión antes de publicar la primera versión del contrato.
- Un JSON bien formado o un esquema válido no prueban por sí solos coherencia geométrica
  ni cumplimiento normativo.
