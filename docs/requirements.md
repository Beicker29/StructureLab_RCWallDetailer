# Requisitos y estado

RCWD-000 estableció la arquitectura. RCWD-001A implementa el contrato canónico y
su subconjunto de validación. RCWD-001B implementa la interfaz Excel de 17 hojas en español; los motores posteriores
no están implementados. La aprobación de un requisito no equivale a su ejecución completa.

## Requisitos funcionales aprobados

| ID | Requisito | Estado |
| --- | --- | --- |
| RF-01 | Ingreso inicial por Excel | Implementado RCWD-001B con openpyxl |
| RF-02 | Contratos tipados, versionados y serializables a JSON | Implementado V0.1 |
| RF-03 | Separar entrada y resultados | Entradas implementadas; resultado reservado NOT_IMPLEMENTED |
| RF-04 | Geometrías arbitrarias mediante implementación progresiva | Rectángulos y polígonos simples con huecos; curvas/múltiples exteriores pendientes |
| RF-05 | Refuerzo paramétrico y explícito | Tres patrones de entrada validados; sin resolución |
| RF-06 | Representación geométrica común del refuerzo resuelto | Pendiente |
| RF-07 | DXF editable y futuras integraciones | Pendiente |
| RF-08 | Diagnósticos de tipos, referencias y geometría | Implementados con stage/path/code/description; ubicación Excel implementada |
| RF-09 | Once hojas principales y seis avanzadas, todas en español | Implementadas según aprobación RCWD-001B |
| RF-10 | Configuraciones reutilizables, secciones con materiales y muros independientes | Implementado |
| RF-11 | Asignación de secciones a múltiples muros/niveles | Implementado; un par muro/nivel no admite asignaciones ambiguas |

## Decisiones aprobadas en RCWD-001A

| Decisión | Aplicación y límite |
| --- | --- |
| ID-01, ID-02 | IDs únicos globalmente en el proyecto, explícitos, sin dependencia Excel/CAD |
| EQ-01 | Equivalencia exacta rectángulo/polígono en el mismo marco local, sin transformar coordenadas |
| EQ-02, EQ-03 | Diferencias de instrucciones longitudinales, datos transversales conocidos o materiales producen definiciones distintas |
| EQ-04 | Comparación de definiciones separada de equivalencia física; esta última UNDETERMINED |
| EQ-05, EQ-06 | Sin fusiones automáticas ni redondeos para declarar equivalencia |
| GEO-01, GEO-02 | Mano derecha; xy horizontal, +z vertical |
| GEO-03 | Exteriores antihorarios y huecos horarios; orientación incorrecta se rechaza |
| GEO-05 | Polígonos por vértices con huecos; subconjunto simple/conectado explícito |
| NUM-01 | Decimal y cadenas JSON; se preservan valores sin redondeo |
| NUM-02, NUM-03 | Sin tolerancias de diseño ni epsilon global; predicados racionales exactos |
| NUM-04 | Sin modificaciones geométricas silenciosas |

GEO-04 se aplaza expresamente: no existen transformaciones locales/globales.
La equivalencia transversal permanece indeterminada mientras sus contratos sean UNRESOLVED.

## No funcionales y restricciones

- Python 3.11+, paquete instalable src/rcwall; arquitectura y dirección de dependencias
  de RCWD-000 conservadas.
- Dominio independiente de Excel, bibliotecas CAD y geometría operativa.
- Pydantic y openpyxl son dependencias directas de ejecución. Se justificó para contratos,
  condiciones locales y esquema; openpyxl para el adaptador Excel. Predicados con biblioteca estándar.
- Pruebas automatizadas, Ruff y artefactos de esquema sincronizados con modelos.
- Esquema versionado independientemente del paquete; rechazo de versiones no admitidas.
- No usar DCCAD3 como referencia técnica, algoritmo, formato o convención.
- Sin Excel, dibujo, distribución calculada ni comprobaciones normativas en RCWD-001A.
- No inferir recubrimientos, resistencias, radios, ganchos o valores geométricos.
- El constructor Pydantic no sustituye la validación completa de referencias y topología.
- La validación de datos no constituye cumplimiento estructural.

## Decisiones pendientes o delimitadas

| ID | Estado y siguiente decisión |
| --- | --- |
| DP-01 | Contratos V0.1 definidos para el subconjunto documentado; ampliaciones requieren evolución explícita |
| DP-02 | Mano, ejes y orientación resueltos; origen global y transformaciones siguen aplazados |
| DP-03 | V0.1 solo admite mm; conversiones externas pendientes |
| DP-04 | Predicados exactos sin tolerancia; tolerancias para futuros cálculos aproximados pendientes |
| DP-05 | Unicidad global definida; level_id externo sin catálogo. No hay versiones previas que migrar |
| DP-06 | Políticas/alineación conservadas como texto; catálogo y algoritmos pendientes. No se verifica factibilidad de offsets |
| DP-07 | Polígonos simples y huecos soportados; curvas, trayectorias y múltiples exteriores pendientes |
| DP-08 | Recubrimientos, radios, ganchos, anclajes, contención y conflictos de refuerzo pendientes |
| DP-09 | Norma, jurisdicción, edición, alcance y verificación normativa pendientes |
| DP-10 | Dibujo UNRESOLVED; capas, bloques, catálogo de plantillas y exportación pendientes |
| DP-11 | Alcances detallados RCWD-002 a RCWD-006 requieren aprobación |
| DP-12 | Resuelto: 17 hojas, secciones/materiales/muros independientes; ver excel_interface.md |
| DP-13 | Catálogos de niveles, subdivisión de muro/nivel y materiales diferenciados por grupo pendientes |

Los límites no se completan con supuestos: estados UNRESOLVED, errores explícitos o
comparaciones UNDETERMINED indican cuándo falta semántica para continuar.
