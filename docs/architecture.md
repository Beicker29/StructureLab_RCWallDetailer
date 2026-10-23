# Arquitectura vigente

Estado: RCWD-EXCEL-RETIRE-000. Se conservan los contratos, validación, predicados
geométricos exactos y JSON; la web local es la interfaz principal. Excel fue retirado
por ADR-007, conservando RCWD-001B como historial.
Detallado y CAD permanecen reservados; el flujo completo sigue siendo un objetivo.

## Responsabilidades y dependencias

| Módulo | Responsabilidad | Dependencias internas permitidas |
| --- | --- | --- |
| `domain` | Entidades, contratos de entrada y salida, identidad y relaciones | Ningún otro módulo de `rcwall` |
| `geometry` | Primitivas, contornos y operaciones geométricas sin conocimiento del archivo origen | `domain` |
| `detailing` | Interpretar instrucciones de refuerzo y producir resultados resueltos | `domain`, `geometry` |
| `validation` | Validar datos, relaciones y geometría; mantener futuras reglas normativas identificables | `domain`, `geometry` |
| `io/json` | Lectura/escritura canónica con precisión decimal y validación | `domain`, `validation` |
| `exporters/dxf` | Transformar únicamente resultados resueltos y especificaciones de dibujo a DXF | `domain`, `geometry` |

`io` y `exporters` son espacios de nombres para adaptadores. `io/json.py` implementa
serialización y depende de `domain` y `validation`. Los servicios web coordinan el flujo
implementado en el paquete hermano `rcwall_web`. No existe un adaptador operativo Excel
ni una capa de persistencia compartida.

La tabla representa dependencias de código, no orden temporal. `detailing` recibe datos
previamente validados; no importa adaptadores. `validation` no ejecuta el motor de
detallado ni exporta DXF. `exporters/dxf` no decide cantidad, posición ni forma del refuerzo.
No se permiten dependencias circulares.

## Flujo implementado y evolución pendiente

```text
Web local / documento JSON
  → rcwall_web (rutas y servicios) / io.json
  → contratos de entrada en domain
  → validation (tipos, relaciones y geometría)
  → JSON canónico + representación SVG desechable
```

`geometry + detailing → DetailingResult → exporters/dxf` es un flujo futuro, no una
funcionalidad implementada. La representación SVG de entradas explícitas no constituye
un resultado de detallado. Los errores se comunican mediante `ValidationReport`.

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
- Pydantic es la dependencia para contratos; openpyxl ya no es dependencia. Los predicados usan
  Fraction de la biblioteca estándar a partir de los valores Decimal originales.

## Módulos implementados

Los contratos viven en `domain/models.py`, los predicados en `geometry/polygons.py`,
la validación en `validation/project.py`, la equivalencia de secciones en
`validation/equivalence.py` y JSON en `io/json.py`. Los módulos del núcleo permanecen
sin cambios. `io/excel` dejó de existir; su historial está en Git y los registros de RCWD-001B.

Consultar los [ADR](adr/ADR-001-domain-independence.md) antes de cambiar estas fronteras.

## Adaptador web RCWD-UI-000

El caso de uso web aprobado introduce `src/rcwall_web/` como paquete hermano del núcleo.
`app.py` compone FastAPI y estáticos; `routes.py` contiene rutas/modelos HTTP;
`services.py` coordina `rcwall.domain`, `rcwall.validation` y `rcwall.io.json`;
`static/` representa la vista en HTML/CSS/JavaScript/SVG. Ningún módulo de `rcwall`
depende de este adaptador. FastAPI y Uvicorn son dependencias opcionales del extra `web`;
HTTPX y Playwright pertenecen a pruebas, no al dominio ni al frontend.

No hay estado de proyecto en el servidor ni persistencia compartida. El navegador conserva
el JSON como texto opaco por pestaña; Python valida cada operación completa. La proyección
visual y la cámara no forman parte del contrato ni de los resultados de detallado.
Las diferencias exactas se calculan en Python y solo la representación de pantalla usa float.
Se documenta en [ADR-006](adr/ADR-006-local-web-prototype.md), que complementa las decisiones
previas, y en la [guía del prototipo](web_prototype.md).

RCWD-UI-000R consolida el frontend en módulos ES nativos: `api.js` para transporte,
`state.js` para edición/revisiones y versión respaldada, `svg.js` para representación
y cámara, y `app.js` para formularios y coordinación. No añade dependencias ni capas
del backend. Se conservan las decisiones de ADR-006 y el esquema 0.1.0.

El retiro y el cambio incompatible de API del paquete 0.2.0 se registran en
[ADR-007](adr/ADR-007-retire-excel.md). El esquema sigue en 0.1.0.
