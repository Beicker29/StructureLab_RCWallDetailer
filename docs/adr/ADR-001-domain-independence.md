# ADR-001 — Independencia del dominio

Estado: adoptado para RCWD-000. Fecha: 2026-10-23.

## Problema

El proyecto debe interpretar secciones y refuerzo sin convertir las limitaciones de una
interfaz de entrada o de una aplicación CAD en reglas del dominio. Acoplar geometría a
celdas o entidades CAD impediría probar motores de forma independiente y agregar otros
adaptadores sin modificar el significado de los datos.

## Alternativas consideradas

1. Usar filas/celdas Excel como representación interna de toda la aplicación.
2. Usar entidades DXF o de AutoCAD como representación geométrica central.
3. Separar contratos, geometría, detallado, validación y adaptadores de entrada/salida.

Las dos primeras reducen inicialmente traducciones, pero trasladan convenciones de
herramientas externas al motor. La tercera requiere adaptadores explícitos y permite
pruebas y evolución independientes.

## Decisión adoptada

Adoptar módulos separados bajo `src/rcwall/`. `domain` no depende de otros módulos del
proyecto ni de Excel/CAD. `geometry` contiene operaciones independientes del formato.
`detailing` resuelve instrucciones; `validation` mantiene controles diferenciados.
`io/excel` y `exporters/dxf` traducen desde/hacia sus formatos en las fronteras.

DXF es el destino CAD inicial. No se toma DCCAD3 como referencia técnica o arquitectónica.

## Consecuencias

- Se pueden probar contratos y motores sin instalar Excel ni software CAD.
- Los adaptadores deben traducir y conservar trazabilidad sin filtrar objetos de sus
  bibliotecas hacia el dominio.
- Un exportador no completa geometría ni reglas de refuerzo ausentes.
- Las dependencias permitidas se mantienen en `docs/architecture.md`; nuevos casos no
  justifican introducir dependencias circulares.
- Esta decisión establece límites, no implementa motores ni garantiza validez estructural.
