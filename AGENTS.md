# Instrucciones del repositorio

## Alcance y estado

Este proyecto desarrolla una herramienta independiente de detallado de secciones de muros
de concreto reforzado. La base activa incluye RCWD-000, los contratos RCWD-001A,
la interfaz Excel RCWD-001B y el prototipo web local RCWD-UI-000.
Leer `README.md` y
`docs/development_roadmap.md` antes de ampliar funcionalidades. Los directorios reservados
no implican que sus motores estén implementados.

## Reglas de trabajo

- Respetar las responsabilidades y dependencias de `docs/architecture.md`.
- Mantener `src/rcwall/domain` independiente de Excel, `openpyxl`, `ezdxf` y software CAD.
- No inventar reglas de detallado estructural, capacidades resistentes ni cumplimiento normativo.
- No asumir valores geométricos o normativos silenciosamente. Registrar las ambigüedades
  en la documentación; solicitar definición antes de implementar comportamiento que dependa de ellas.
- Explicitar unidades internas, inicialmente milímetros. No interpretar otras unidades ni
  convertirlas sin un contrato aprobado.
- Separar las definiciones originales de entrada y los resultados geométricos calculados.
- Escribir pruebas automatizadas para cada comportamiento implementado. Ubicarlas bajo
  `tests/` y ejecutarlas con `python -m pytest` tras instalar el paquete.
- Ejecutar `python -m ruff check .` y `python -m ruff format --check .` para cambios Python.
- No introducir dependencias sin necesidad concreta; documentar su módulo consumidor y propósito.
- Documentar cambios de contratos o arquitectura. Crear o sustituir un ADR cuando cambie
  una decisión adoptada, conservando el historial de la decisión previa.
- Preservar compatibilidad de contratos versionados. Un cambio incompatible requiere
  versión de esquema y estrategia de migración explícitas.
- No utilizar DCCAD3 como referencia técnica, arquitectónica o de convenciones.
- Diferenciar siempre requisitos aprobados, propuestas, decisiones pendientes y funciones implementadas.
- No declarar implementada o validada una función que todavía no lo esté. Una validación
  de datos nunca demuestra por sí misma cumplimiento estructural.
- Inspeccionar archivos existentes y preservar trabajo ajeno antes de modificarlo. No rescatar
  automáticamente borradores locales de `.work/` como implementación aprobada.

## Organización

Usar el paquete `rcwall` bajo `src/`, pruebas en `tests/`, documentación en `docs/` y
decisiones en `docs/adr/`. Las salidas generadas van en `outputs/` o `generated/`.
La interfaz web vive en `src/rcwall_web/`; el núcleo `rcwall` no importa este adaptador.
No agregar servicios, repositorios abstractos, interfaces CAD ni capas de orquestación
hasta que un caso de uso implementado las necesite.
