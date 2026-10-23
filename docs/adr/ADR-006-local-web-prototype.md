# ADR-006 — Prototipo web local y separación de la representación

Estado: adoptado para RCWD-UI-000. Fecha: 2026-10-23.
Complementa ADR-001 y ADR-005; no sustituye sus decisiones ni cambia el esquema 0.1.0.

## Problema

Se necesita experimentar con edición y selección gráficas sin implementar motores de
detallado, convertir JavaScript en fuente de precisión ni compartir proyectos entre usuarios.
El núcleo existente no necesita conocer HTTP, sesiones, HTML ni SVG.

## Alternativas

1. Agregar rutas y estado global dentro de `rcwall`: mezcla responsabilidades y facilita
   que distintos usuarios compartan accidentalmente un proyecto.
2. Mantener sesiones y archivos en el servidor: necesita almacenamiento, caducidad,
   autenticación y control de concurrencia que este caso local no requiere.
3. Adaptador hermano `rcwall_web`, servicios sin estado y proyecto canónico textual por pestaña.

## Decisión

Se adopta la tercera opción. `app.py` compone FastAPI, las fronteras locales y archivos
estáticos; `routes.py` define el transporte; `services.py` coordina los contratos y
validadores existentes; `static/` contiene HTML, CSS y JavaScript sin framework gráfico.
`rcwall` nunca importa `rcwall_web`. No se copió código de otro repositorio.

Cada petición de edición/importación/exportación lleva el documento completo como una
cadena JSON opaca. El navegador nunca ejecuta `JSON.parse` sobre el documento canónico:
así conserva también cantidades enteras mayores que 2^53. Longitud, espesor y origen
viajan como cadenas estrictas. Python usa `loads_project`, `validate_definition` y
`dumps_project`; no se modifica el contrato para adaptarlo al formulario.

El servidor no mantiene el proyecto actual, cookies de edición ni archivos de usuario.
Cada pestaña mantiene su documento en memoria; recargar o cerrar pierde ese estado.
La descarga JSON es la única persistencia implementada y la controla el usuario.
Los índices enviados seleccionan entidades dentro del documento de la misma petición;
no son claves para buscar proyectos en un almacén compartido.

La creación produce `ProjectDefinition` con una `GeometryDefinition` rectangular,
identificadores UUID y origen obligatorio introducido por el usuario. No crea una
`SectionDefinition`, materiales, `WallDefinition` ni asignaciones: esos conceptos no son
equivalentes y su creación exigiría entradas adicionales. La UI explica esta limitación.
Los muros físicos y las asignaciones de un proyecto importado permanecen intactos.

La edición cambia únicamente longitud/espesor de la geometría seleccionada. Si varias
secciones reutilizan esa geometría, comparten la modificación; no se duplican identidades.
No se mueven barras ni referencias ni se comprueba contención, recubrimiento o factibilidad.
Cada configuración se visualiza por separado para no superponer alternativas de refuerzo.

La proyección usa diferencias y cocientes racionales (`Fraction`) en Python, relativos
al origen local. Solo el resultado destinado a píxeles se convierte a números binarios.
SVG usa Y descendente; la representación invierte ese eje conservando +Y local hacia arriba.
Esto es una transformación de presentación, no un motor local/global del dominio.
La cámara, selección, zoom y desplazamiento son estado visual del navegador y nunca
se incluyen en las peticiones de edición. Los inspectores usan cadenas canónicas.

La proyección tiene un presupuesto de 10 000 dígitos por magnitud (coeficiente más
valor absoluto del exponente); si se supera, devuelve una advertencia y omite la vista.
El proyecto sigue siendo importable/exportable, sin truncamiento ni redondeo. Este
límite operativo del adaptador evita expandir exponentes enormes en `Fraction`.

El formulario espera 350 ms tras una entrada y valida en Python; cada solicitud tiene
una revisión local para descartar respuestas antiguas. Los borradores inválidos se
conservan en el formulario y mantienen el último dibujo válido. La exportación y el
cambio de geometría se bloquean hasta corregir o descartar explícitamente el borrador.

## Dependencias y seguridad

- Extra `web`: FastAPI para rutas/modelos de transporte y Uvicorn para ejecución ASGI.
- Extra `dev`: HTTPX para pruebas HTTP con TestClient, además de pytest y Ruff.
- Extra `ui-test`: Playwright y Chromium únicamente para pruebas; no llegan al frontend.
- Sin paquetes gráficos, CDN, base de datos, autenticación o despliegue público.
- El comando documentado escucha exclusivamente en `127.0.0.1:8000`.
- Host local y Origin del mismo origen, sin CORS permisivo; cuerpos POST JSON de hasta
  2 MiB. Este es un límite de transporte explícito, no del esquema canónico.
- CSP restringida, `nosniff`, respuestas sin caché. Texto del usuario por `textContent`;
  nodos SVG y atributos numéricos construidos con DOM, nunca concatenación HTML.
- No se ofrecen rutas de escritura de archivos ni se aceptan nombres de destino.

Las pruebas HTTP siguen el patrón de [TestClient documentado por FastAPI](https://fastapi.tiangolo.com/tutorial/testing/).
La aplicación es para datos locales de confianza; no constituye un servicio endurecido
para Internet. El coste de validación de polígonos y magnitudes extremas sigue teniendo
los límites del núcleo descritos en ADR-005.

## Consecuencias

El servidor es fácil de reiniciar y no puede mezclar un estado de edición inexistente.
El coste es transferir y validar el proyecto completo en cada edición; no hay historial,
autosave ni colaboración. Ninguna operación visual demuestra validez estructural.
La persistencia, el trabajo por muro/nivel y los motores futuros requieren casos de uso
y decisiones propias; no se adelantan mediante esta interfaz.
