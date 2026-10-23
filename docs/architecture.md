# Arquitectura inicial

Estado: arquitectura adoptada en RCWD-000. Los paquetes existen como estructura vacía;
el flujo descrito es el objetivo de implementación, no una capacidad actual.

## Responsabilidades y dependencias

| Módulo | Responsabilidad | Dependencias internas permitidas |
| --- | --- | --- |
| `domain` | Entidades, contratos de entrada y salida, identidad y relaciones | Ningún otro módulo de `rcwall` |
| `geometry` | Primitivas, contornos y operaciones geométricas sin conocimiento del archivo origen | `domain` |
| `detailing` | Interpretar instrucciones de refuerzo y producir resultados resueltos | `domain`, `geometry` |
| `validation` | Validar datos, relaciones y geometría; mantener futuras reglas normativas identificables | `domain`, `geometry` |
| `io/excel` | Generar/leer plantillas, interpretar tipos y conservar ubicación de errores | `domain`, `validation` |
| `exporters/dxf` | Transformar únicamente resultados resueltos y especificaciones de dibujo a DXF | `domain`, `geometry` |

`io` y `exporters` son espacios de nombres para adaptadores. La serialización JSON futura
puede vivir en `io` sin crear una capa adicional. Una función de aplicación futura podrá
coordinar estos módulos cuando exista un flujo ejecutable; no se crea un servicio abstracto
ni una CLI vacía en este hito.

La tabla representa dependencias de código, no orden temporal. `detailing` recibe datos
previamente validados; no importa el adaptador Excel. `validation` no ejecuta el motor de
detallado ni exporta DXF. `exporters/dxf` no decide cantidad, posición ni forma del refuerzo.
No se permiten dependencias circulares.

## Flujo previsto

```text
Excel
  → adaptador io/excel (lectura y localización de celdas)
  → contratos de entrada en domain
  → validation (tipos, relaciones y geometría)
  → geometry + detailing (resolución geométrica)
  → DetailingResult
  → exporters/dxf
```

El contrato canónico también podrá entrar o salir como JSON mediante un adaptador de
serialización. Excel no define el dominio: sus tablas representan una versión explícita
del contrato. Los errores de lectura y validación se comunican mediante `ValidationReport`;
no se convierten en resultados geométricos ficticios.

Las verificaciones normativas futuras serán una etapa diferenciada, con norma, edición,
alcance e información de entrada explícitos. No se presume aprobación normativa por
superar controles de tipos, referencias o topología.

## Fronteras

- El dominio no importa `openpyxl`, `ezdxf`, APIs de AutoCAD ni formatos propietarios.
- Las representaciones geométricas no contienen celdas, capas DXF ni objetos de una
  biblioteca CAD. Los tipos de intercambio pertenecen al dominio; las operaciones a `geometry`.
- La entrada conserva las instrucciones originales. La salida contiene su resolución
  independiente del patrón de origen, con trazabilidad prevista hacia la entrada.
- Unidades internas: milímetros explícitos. La elección de origen, ejes, orientación,
  tolerancias y reglas de transformación permanece pendiente.
- La geometría arbitraria es un objetivo conceptual; cada versión declarará qué
  representaciones acepta y rechazará de forma explícita las no soportadas.
- Las bibliotecas específicas se incorporarán en sus fronteras cuando sean necesarias.
  No hay dependencias de ejecución en este hito.

## Preparación para RCWD-001

Ubicar contratos en `domain`, comprobaciones topológicas reutilizables en `geometry`,
validación de relaciones en `validation`, entrada Excel en `io/excel` y serialización JSON
en `io`. La metadata de hoja/fila pertenece al adaptador y se traduce al reporte; no se
introduce una dependencia inversa del dominio al libro. El generador de plantilla deberá
derivar o verificar su correspondencia con los contratos versionados.

Consultar los [ADR](adr/ADR-001-domain-independence.md) antes de cambiar estas fronteras.
