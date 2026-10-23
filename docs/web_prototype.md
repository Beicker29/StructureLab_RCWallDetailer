# RCWD-UI-000R — Prototipo web local consolidado

Implementado sobre el contrato `ProjectDefinition` 0.1.0, sin modificar dominio,
validadores, motores existentes ni esquema. Interfaz en español con FastAPI, HTML,
CSS, JavaScript y SVG. No usa código trasladado del repositorio de vigas.

## Ejecutar

Desde la raíz, con Python 3.11 o posterior y el entorno virtual creado:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web]"
.\.venv\Scripts\python.exe -m rcwall_web
```

Abra **http://127.0.0.1:8000**. Detenga con Ctrl+C en la terminal.
No hace falta Node, Excel, CAD ni compilar archivos estáticos. Linux/macOS:
use `.venv/bin/python` con los mismos argumentos. No cambie la escucha a una interfaz
pública: no hay autenticación ni soporte de despliegue público. Render continúa fuera
de alcance; no se incorporan servicios ni archivos de despliegue.

## Flujo de uso

1. **Nuevo muro**: declare longitud, espesor y origen inferior izquierdo X/Y en mm.
   Los campos empiezan vacíos; el origen no se presupone. Use punto decimal.
   Se crea la definición geométrica; todavía no una sección con materiales ni un muro
   físico asignado a niveles. Las identidades necesarias son automáticas.
   Si ya hay un proyecto, **Crear geometría** solicita confirmación antes de reemplazarlo.
   Rechazar la confirmación, pulsar **Cancelar** o Escape conserva el proyecto y sus
   entradas pendientes. Abrir el diálogo pausa la validación pendiente; al cancelarlo
   puede continuar escribiendo, validar expresamente o descartar ese borrador.
2. **Importar JSON**: seleccione un proyecto canónico V0.1. Se valida completo antes
   de reemplazar el proyecto abierto, con confirmación previa. Cancelar o importar
   un archivo inválido conserva el documento y los textos pendientes del formulario.
3. Elija una **geometría** y una **configuración** usando los selectores. No necesita
   escribir identificadores ni manejar las hojas Excel. Solo los rectángulos se dibujan
   y editan; otras entidades se conservan en el JSON.
4. Cambie longitud o espesor. La validación automática ocurre después de una pausa de
   350 ms; también puede pulsar **Validar cambios**. Ante un error se conserva el último
   dibujo válido y se bloquea la exportación. **Descartar cambios** recupera los valores
   aceptados explícitamente. El origen importado es de consulta en esta versión.
5. Pulse el contorno o una barra explícita para consultar sus valores declarados. Use
   la rueda o +/− para zoom, arrastre el fondo para desplazar y **Ajustar vista** para
   encuadrar. Los elementos también admiten selección con Tab y Enter/Espacio.
6. **Exportar JSON** descarga el documento validado completo. Guárdelo antes de cerrar
   o recargar: el estado de cada pestaña es temporal y no se guarda en el servidor.

Una geometría reutilizada se edita para todas las secciones que la referencian. Las
barras y referencias mantienen sus coordenadas declaradas aunque se reduzca el muro;
esta versión no evalúa contención o recubrimientos ni reacomoda refuerzo.
La advertencia aparece sobre el editor cuando la geometría tiene declaraciones de
refuerzo longitudinal o transversal, incluso en configuraciones alternativas. Permanece
visible durante la edición y aclara que validar datos no aprueba el detallado estructural.

### Cambios pendientes y cierre

La interfaz diferencia un borrador pendiente de validar de una versión canónica sin
exportar. Un proyecto nuevo queda pendiente de exportación; una importación válida se
considera recuperable del archivo original. Una descarga iniciada marca únicamente la
versión enviada a descargar. Un fallo de exportación o la descarga de una versión
anterior no marca como guardada una edición más reciente ni un proyecto que la reemplazó.

`beforeunload` se registra cuando hay cambios sin exportar o entradas pendientes, y se
retira cuando se recupera la versión respaldada. Selección, zoom y desplazamiento no
marcan el proyecto como modificado. La aplicación puede detectar que inició la descarga,
pero no confirmar que el usuario la guardó en disco: compruebe el archivo descargado.
El navegador decide cuándo mostrar el aviso de cierre y su texto; requiere interacción
previa y puede omitirlo en algunos escenarios móviles. No reemplaza la exportación ni
implementa guardado automático. Véase [beforeunload en MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event).

## Estructura y transporte

```text
src/rcwall_web/
  __main__.py       Comando local, solo loopback
  app.py            Composición, límites HTTP, errores y estáticos
  routes.py         Solicitudes de transporte estrictas
  services.py       Creación, edición y representación del proyecto
  static/
    index.html      Estructura y textos de la interfaz
    style.css       Estilos legibles, sin framework
    app.js          Formularios, propiedades y coordinación
    api.js          HTTP, errores y descarga del documento textual
    state.js        Estado por pestaña, revisiones y versión respaldada
    svg.js          Representación, selección y cámara SVG
```

| Operación POST | Entrada JSON de transporte | Resultado |
| --- | --- | --- |
| `/api/create` | `length`, `thickness`, `x`, `y`: cadenas | Documento canónico y datos visuales |
| `/api/import` | `document`: texto JSON completo | Proyecto validado y datos visuales |
| `/api/edit` | `document`, `index` entero, `length` y `thickness` cadenas | Documento modificado y validado |
| `/api/export` | `document`: texto JSON completo | Descarga del JSON canónico |

El envoltorio HTTP no es una nueva versión del contrato. `document` permanece como
texto opaco en JavaScript, evitando pérdida tanto de decimales como de enteros grandes.
Los datos visuales normalizados son desechables y nunca se envían como sustituto de
la definición. Las etiquetas libres se muestran como texto literal. Límite de cuerpo
HTTP: 2 MiB, incluido el envoltorio y el escape del documento.
Los módulos son ES nativos servidos por FastAPI: no necesitan Node.js, bundler ni
dependencias nuevas. La CSP no cambia. `has_reinforcement` es metadata de presentación
del adaptador para la advertencia; no se agrega a `ProjectDefinition` ni al JSON exportado.

## Pruebas reproducibles y evidencia

La base de RCWD-UI-000 se comprobó antes de modificar archivos: **198 pruebas aprobadas**,
incluidas las dos pruebas de navegador originales.
Las nuevas pruebas HTTP cubren creación, precisión, origen, edición, importación,
exportación, errores del dominio, configuraciones alternativas, aislamiento, límites
HTTP y texto no confiable.

Comprobación histórica de RCWD-UI-000 (2026-10-23, Python 3.12): **198 pruebas aprobadas**
(165 anteriores + 31 HTTP/aplicación + 2 de navegador), Ruff check y format sin errores,
y `pip check` sin dependencias rotas. Starlette 1.9 emite una advertencia de deprecación
del transporte HTTPX de TestClient; las pruebas pasan y no se oculta la advertencia.

Cierre local de RCWD-UI-000R: **212 pruebas aprobadas** (202 de Python/API y 10 de
navegador Chromium), con Ruff check, Ruff format --check y pip check aprobados.
La advertencia de deprecación HTTPX de Starlette sigue presente. Las pruebas nuevas
cubren confirmación de reemplazo, cancelación por botón/Escape, conservación de
borradores y proyectos ante errores, respuestas tardías, descarga de versiones antiguas,
avisos de recarga, refuerzo asociado e independencia del núcleo. Se comprobó además
aislamiento entre pestañas del mismo contexto y entre contextos de navegador.

Las huellas de todos los archivos Python del núcleo, el esquema y ambos libros Excel
coinciden con las de la inspección inicial. ADR-006 y las cinco capturas históricas
permanecen intactos. No fue necesario adoptar una nueva decisión arquitectónica.

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Para incluir las pruebas reales de navegador y conservar las capturas de la ejecución:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web,ui-test]"
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RCWALL_BROWSER_TESTS = "1"
$env:RCWALL_UI_OUTPUT = "outputs/ui-runs"
.\.venv\Scripts\python.exe -m pytest
Remove-Item Env:RCWALL_BROWSER_TESTS
Remove-Item Env:RCWALL_UI_OUTPUT
```

Las pruebas de navegador arrancan y detienen su propio servidor local en un puerto
libre. No necesitan un servidor abierto en 8000. Sin `RCWALL_BROWSER_TESTS` se omiten
explícitamente. Sin `RCWALL_UI_OUTPUT`, las capturas quedan en el directorio temporal de
pytest. El destino `outputs/ui-runs/` está ignorado por Git; las pruebas rechazan escribir
en `outputs/ui/`, que contiene únicamente evidencia seleccionada para documentación.
Se ejecutaron con Chromium automatizado y se inspeccionaron sus capturas; no se afirma
una comprobación manual en un navegador del usuario. Se conservan estas capturas históricas
de RCWD-UI-000 porque ilustran comportamientos distintos, sin regenerarlas automáticamente:

- [Contorno seleccionado](../outputs/ui/01-contorno.png).
- [Rechazo de una dimensión inválida](../outputs/ui/02-validacion.png).
- [Zoom y desplazamiento](../outputs/ui/03-zoom-desplazamiento.png).
- [Barra explícita y propiedades exactas](../outputs/ui/04-barra-explicita.png).
- [Vista estrecha y texto importado literal](../outputs/ui/05-vista-estrecha.png).

Evidencia seleccionada de RCWD-UI-000R:
[advertencia geométrica con coordenadas de barras conservadas](../outputs/ui/06-advertencia-geometrica.png).

Puede importar el [ejemplo con barras explícitas](../outputs/ui/ejemplo-barras.json),
conservado como ejemplo estable, para explorar la selección y las propiedades. Las pruebas
generan sus propias copias temporales y no sobrescriben este archivo.

La prueba compara la descarga antes/después de zoom y desplazamiento, verifica dos
contextos de navegador independientes y comprueba exportación exacta con cantidades
mayores que 2^53 y decimales extensos. Los datos de barras son ejemplos de prueba,
no recomendaciones estructurales.

### Integración continua

No había un workflow del proyecto. Se incorporan dos configuraciones mínimas:

- `.github/workflows/ci.yml`: push, pull request o ejecución manual; instala `.[dev,web]`,
  ejecuta pytest, Ruff check y Ruff format. El módulo Playwright se omite explícitamente.
- `.github/workflows/browser.yml`: ejecución manual independiente; instala `.[dev,web,ui-test]`
  y Chromium, habilita las pruebas de navegador y adjunta las capturas como artefactos
  temporales de GitHub Actions. No publica la aplicación.

Se ejecutaron las pruebas localmente; la ejecución hospedada de estos workflows queda
pendiente de subir los cambios a GitHub. Configuración basada en la
[guía de pruebas Python de GitHub](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

### Limpieza y preservación de los Excel (histórico de RCWD-UI-000R)

Este registro describe el estado previo al retiro. RCWD-EXCEL-RETIRE-000 eliminó los
libros y el adaptador tras comprobar su respaldo en Git y confirmar que no había
ediciones pendientes. La divergencia descrita abajo se cerró por retiro, sin cambiar
el lector. Véase [ADR-007](adr/ADR-007-retire-excel.md).

`~$plantilla_v0_1.xlsx` es un archivo de bloqueo de Office, y el `.whl` bajo
`outputs/packages/` es una compilación. Se retiraron del índice conservando las copias
locales; `.gitignore` excluye estos archivos y los resultados automáticos de navegador.
La copia temporal de Excel estaba bloqueada por la aplicación y no se eliminó.

Se compararon ambos libros con `8977403` (RCWD-001B). Sus modificaciones llegaron en
`55f2a5d`, antes del prototipo web: tienen 17 hojas pero `Barras` fue renombrada como
`BarrasVerticales`; se observaron 441 diferencias de valor/tipo en el ejemplo y 437 en
la plantilla, además de cambios de formato. La plantilla contiene ahora datos del
proyecto `EJ-MURO-CR-001`. No son cambios binarios accidentales demostrados: ambos libros
se conservaron byte por byte, sin regenerar ni guardar con openpyxl.

El lector Excel entonces vigente requería la hoja `Barras`, por lo que esos libros
modificados no correspondían a su plantilla aprobada. La divergencia quedó pendiente
en RCWD-UI-000R, que no revirtió el trabajo del usuario ni amplió el lector.

## Límites y recomendaciones para RCWD-UI-001

Implementado: geometría rectangular, barras explícitas de configuraciones importadas,
selección, cámara y ciclo JSON completo. Los polígonos se preservan pero no se dibujan.
Distribuciones por cantidad/separación se informan como pendientes; estribos y sus
trayectorias no se generan. La visualización puede perder detalles bajo la escala de
pantalla; los valores originales permanecen disponibles y se advierte esa situación.
Si una magnitud supera el presupuesto visual de 10 000 dígitos (dígitos de coeficiente
más valor absoluto del exponente), se omite explícitamente la vista y se conserva la
importación/exportación canónica. Ese límite protege la proyección racional, no restringe
el contrato ni redondea datos. No es un límite de recursos del validador de polígonos.

No hay edición de barras/materiales/asignaciones, historial, guardado automático,
colaboración, DXF, transformaciones local/global ni cálculos normativos. La validación
es de datos, no cumplimiento estructural. El tamaño y coste de proyectos extensos no
se han caracterizado como garantía de rendimiento.

Propuestas para RCWD-UI-001, pendientes de aprobación de alcance:

1. Definir el flujo muro → nivel → sección, entradas de materiales y creación de
   asignaciones, sin equiparar geometría con muro físico.
2. Añadir historial y recuperación local con política explícita de privacidad.
3. Mejorar selección de barras pequeñas, superpuestas y navegación por teclado;
   ampliar pruebas a Firefox/WebKit y dispositivos táctiles.
4. Definir antes de implementar cualquier edición de refuerzo, política de contención,
   distribución, recubrimientos o comportamiento al cambiar dimensiones.
5. Evaluar rendimiento y límites operativos con proyectos representativos antes de
   decidir almacenamiento o validación incremental.

Decisión arquitectónica completa: [ADR-006](adr/ADR-006-local-web-prototype.md).

Desde el paquete 0.2.0, la web es la interfaz principal y JSON es el formato de
intercambio. El retiro de Excel no modifica esta implementación, sus límites ni el
contrato 0.1.0. Véase [verificación del retiro](excel_retirement.md).
