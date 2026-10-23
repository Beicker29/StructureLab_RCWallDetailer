# RCWD-UI-000 — Prototipo web local

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
pública: no hay autenticación ni soporte de despliegue público.

## Flujo de uso

1. **Nuevo muro**: declare longitud, espesor y origen inferior izquierdo X/Y en mm.
   Los campos empiezan vacíos; el origen no se presupone. Use punto decimal.
   Se crea la definición geométrica; todavía no una sección con materiales ni un muro
   físico asignado a niveles. Las identidades necesarias son automáticas.
2. **Importar JSON**: seleccione un proyecto canónico V0.1. Se valida completo antes
   de reemplazar el proyecto abierto. Un error deja intacto el documento anterior.
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

## Estructura y transporte

```text
src/rcwall_web/
  __main__.py       Comando local, solo loopback
  app.py            Composición, límites HTTP, errores y estáticos
  routes.py         Solicitudes de transporte estrictas
  services.py       Creación, edición y representación del proyecto
  static/           index.html, style.css, app.js
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

## Pruebas reproducibles y evidencia

La base anterior se comprobó antes de modificar archivos: **165 pruebas aprobadas**.
Las nuevas pruebas HTTP cubren creación, precisión, origen, edición, importación,
exportación, errores del dominio, configuraciones alternativas, aislamiento, límites
HTTP y texto no confiable.

Comprobación de cierre (2026-10-23, Python 3.12): **198 pruebas aprobadas**
(165 anteriores + 31 HTTP/aplicación + 2 de navegador), Ruff check y format sin errores,
y `pip check` sin dependencias rotas. Starlette 1.9 emite una advertencia de deprecación
del transporte HTTPX de TestClient; las pruebas pasan y no se oculta la advertencia.

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Para incluir las pruebas reales de navegador y regenerar las capturas:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web,ui-test]"
.\.venv\Scripts\python.exe -m playwright install chromium
$env:RCWALL_BROWSER_TESTS = "1"
.\.venv\Scripts\python.exe -m pytest
Remove-Item Env:RCWALL_BROWSER_TESTS
```

Las pruebas de navegador arrancan y detienen su propio servidor local en un puerto
libre. No necesitan un servidor abierto en 8000. Sin la variable se omiten explícitamente.
Se ejecutaron con Chromium automatizado y se inspeccionaron sus capturas; no se afirma
una comprobación manual en un navegador del usuario. Las capturas generadas incluyen:

- [Contorno seleccionado](../outputs/ui/01-contorno.png).
- [Rechazo de una dimensión inválida](../outputs/ui/02-validacion.png).
- [Zoom y desplazamiento](../outputs/ui/03-zoom-desplazamiento.png).
- [Barra explícita y propiedades exactas](../outputs/ui/04-barra-explicita.png).
- [Vista estrecha y texto importado literal](../outputs/ui/05-vista-estrecha.png).

Puede importar el [ejemplo con barras explícitas](../outputs/ui/ejemplo-barras.json),
generado por la prueba de navegador, para explorar la selección y las propiedades.

La prueba compara la descarga antes/después de zoom y desplazamiento, verifica dos
contextos de navegador independientes y comprueba exportación exacta con cantidades
mayores que 2^53 y decimales extensos. Los datos de barras son ejemplos de prueba,
no recomendaciones estructurales.

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
