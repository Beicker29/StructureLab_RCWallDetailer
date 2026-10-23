# Arquitectura inicial

Estado: arquitectura adoptada en RCWD-000 y conservada en RCWD-001A. Están implementados
contratos, validación, predicados geométricos exactos y JSON. Excel, detallado y CAD
permanecen reservados; el flujo completo descrito sigue siendo un objetivo.

## Responsabilidades y dependencias

| Módulo | Responsabilidad | Dependencias internas permitidas |
| --- | --- | --- |
| `domain` | Entidades, contratos de entrada y salida, identidad y relaciones | Ningún otro módulo de `rcwall` |
| `geometry` | Primitivas, contornos y operaciones geométricas sin conocimiento del archivo origen | `domain` |
| `detailing` | Interpretar instrucciones de refuerzo y producir resultados resueltos | `domain`, `geometry` |
| `validation` | Validar datos, relaciones y geometría; mantener futuras reglas normativas identificables | `domain`, `geometry` |
| `io/excel` | Generar/leer plantillas, interpretar tipos y conservar ubicación de errores | `domain`, `validation` |
| `exporters/dxf` | Transformar únicamente resultados resueltos y especificaciones de dibujo a DXF | `domain`, `geometry` |

`io` y `exporters` son espacios de nombres para adaptadores. `io/json.py` implementa
serialización y depende de `domain` y `validation`, como la futura frontera Excel. Una función de aplicación futura podrá
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
- Unidades internas: milímetros, mano derecha, xy horizontal y z vertical positivo.
  Exteriores antihorarios y huecos horarios. Origen del rectángulo explícito.
  Transformaciones local/global aplazadas; no hay epsilon global.
- La geometría arbitraria es un objetivo conceptual; cada versión declarará qué
  representaciones acepta y rechazará de forma explícita las no soportadas.
- Pydantic es la dependencia directa para contratos. Los predicados geométricos usan
  Fraction de la biblioteca estándar a partir de los valores Decimal originales.

## Implementación RCWD-001A y preparación para RCWD-001B

Los contratos viven en `domain/models.py`, los predicados en `geometry/polygons.py`,
la validación en `validation/project.py`, la equivalencia de secciones en
`validation/equivalence.py` y JSON en `io/json.py`. Excel seguirá en `io/excel`. La metadata de hoja/fila pertenece al adaptador y se traduce al reporte; no se
introduce una dependencia inversa del dominio al libro. El generador de plantilla deberá
derivar o verificar su correspondencia con los contratos versionados.

Consultar los [ADR](adr/ADR-001-domain-independence.md) antes de cambiar estas fronteras.
