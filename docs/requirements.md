# Requisitos y estado

La aprobación de un requisito no implica su implementación. RCWD-000 aprueba la base
arquitectónica; RCWD-001 es trabajo posterior. Los detalles de RCWD-002 a RCWD-006
en la hoja de ruta son una propuesta, pendiente de precisar antes de ejecutar cada hito.

## Funcionales aprobados

| ID | Requisito | Estado de implementación |
| --- | --- | --- |
| RF-01 | Ingreso inicial mediante Excel | Pendiente, RCWD-001 |
| RF-02 | Contratos canónicos tipados, validados, versionados y serializables a JSON | Pendiente, RCWD-001 |
| RF-03 | Mantener definiciones de entrada separadas del resultado calculado | Frontera documentada; contratos pendientes |
| RF-04 | Admitir conceptualmente geometrías arbitrarias mediante implementación progresiva | Documentado; sin motor |
| RF-05 | Admitir instrucciones paramétricas y refuerzo explícito | Documentado; sin resolución |
| RF-06 | Producir resultados geométricos comunes para exportadores | Documentado; sin resultado ejecutable |
| RF-07 | Exportar inicialmente DXF editable, permitiendo futuras integraciones | Adaptador reservado; exportación pendiente |
| RF-08 | Validar datos, referencias y geometría con diagnósticos localizables | Pendiente, RCWD-001 |
| RF-09 | Interfaz Excel con nueve hojas principales y cuatro avanzadas | Diseño preliminar documentado |

## No funcionales aprobados

| ID | Requisito | Evidencia o criterio |
| --- | --- | --- |
| RNF-01 | Python como lenguaje principal y paquete instalable bajo `src/` | `pyproject.toml`, `src/rcwall/` |
| RNF-02 | Dominio independiente de Excel y CAD | Dependencias permitidas y ADR-001 |
| RNF-03 | Algoritmos, validación normativa y representación desacoplados | Módulos separados |
| RNF-04 | Pruebas automatizadas para comportamientos implementados | `pytest`, pruebas de instalación/importación |
| RNF-05 | Estilo y controles estáticos consistentes | Configuración `ruff` |
| RNF-06 | Dependencias mínimas y justificadas | Sin dependencias de ejecución en RCWD-000 |
| RNF-07 | Evolución explícita y compatible de contratos versionados | ADR-002; política operativa por definir en RCWD-001 |
| RNF-08 | Unidades internas explícitas, inicialmente milímetros | Convenciones; sin conversiones implementadas |

## Restricciones aprobadas

- No usar DCCAD3 como origen de formatos, convenciones, algoritmos ni arquitectura.
- No requerir AutoCAD ni formatos propietarios en el dominio o en la geometría.
- No implementar algoritmos de detallado, contratos completos ni generador Excel en RCWD-000.
- No crear abstracciones sin una necesidad concreta.
- No asumir valores geométricos ni normativos sin registrarlos y definirlos.
- No equiparar validez de datos con cumplimiento estructural.

## Decisiones pendientes

| ID | Tema por resolver | Antes de |
| --- | --- | --- |
| DP-01 | Campos definitivos, obligatoriedad condicional, enumeraciones y cardinalidades | Congelar contratos RCWD-001 |
| DP-02 | Origen local, sentidos de ejes, orientación de contornos y significado de Z | Interpretar geometría RCWD-001/002 |
| DP-03 | Conversión de unidades externas y tratamiento de unidades no admitidas | Lectura RCWD-001 |
| DP-04 | Precisión, tolerancias topológicas y tratamiento de geometría degenerada | Validación geométrica RCWD-001/002 |
| DP-05 | Alcance de unicidad de IDs, referencias externas a muros/niveles y migraciones | Contratos RCWD-001 |
| DP-06 | Políticas de espaciamiento, alineación, extremos, offsets y conflictos | Contratos RCWD-001 y motores RCWD-003 |
| DP-07 | Huecos, múltiples contornos, primitivas de trayectorias y curvas admitidas | Contratos RCWD-001/002 |
| DP-08 | Recubrimientos, radios de doblado, ganchos, anclajes y reglas normativas | Resolución RCWD-003/004 |
| DP-09 | Norma, jurisdicción, edición, alcance y validación de verificaciones | Cualquier comprobación normativa |
| DP-10 | Capas DXF, bloques, textos, escalas y plantillas de dibujo | RCWD-005 |
| DP-11 | Alcance detallado y aprobación de RCWD-002 a RCWD-006 | Inicio de cada hito |

RCWD-001 deberá documentar su subconjunto implementado y rechazar opciones no soportadas
de manera explícita. Esta lista no autoriza a completar vacíos con reglas estructurales inventadas.
