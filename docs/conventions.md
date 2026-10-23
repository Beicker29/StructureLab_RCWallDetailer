# Convenciones de contratos y desarrollo

## Organización y nombres

Distribución: `structurelab-rcwalldetailer`. Paquete: `rcwall` bajo src.
Módulos, funciones y variables en snake_case; clases en PascalCase; constantes en
UPPER_SNAKE_CASE. Identificadores de código en inglés, documentación de uso en español.

Los modelos y funciones públicas declaran tipos y alcance. Las dependencias siguen
architecture.md: el dominio no importa geometría, validación, Excel, archivos ni CAD.
Las salidas regenerables de trabajo van en outputs/ o generated/. Los esquemas y
ejemplos de contratos se versionan en schemas/ y examples/ para revisión y pruebas.
No ignorar globalmente archivos JSON/XLSX/DXF. No importar borradores de .work/.

## Identidad y relaciones

- ID-01: un espacio global de IDs en cada ProjectDefinition, incluido el proyecto,
  entidades anidadas de barras explícitas y colecciones principales.
- ID-02: los IDs no dependen de filas Excel, orden de colecciones ni handles CAD.
- Texto no vacío sin espacios, sensible a mayúsculas. No se recorta, normaliza,
  renumera ni genera automáticamente. La estabilidad es responsabilidad del autor
  entre revisiones; los modelos inmutables evitan cambios accidentales en memoria.
- level_id y template_id son referencias externas declaradas, no entidades de catálogos
  existentes en V0.1. Una cadena no demuestra que ese nivel/plantilla exista fuera del proyecto.
- Una sección es geometría + configuración compatible + materiales. Un muro físico
  tiene identidad propia y se relaciona con secciones mediante asignaciones.
- Una única asignación por muro/nivel; las subdivisiones sin representación se rechazan.

## Coordenadas

GEO-01/02: mano derecha, sección horizontal xy, z vertical positivo.
GEO-03: contorno exterior antihorario y huecos horarios, vistos desde +z.
RECTANGLE exige origen local explícito en su esquina inferior izquierda; longitud en
+x y espesor en +y. No se asigna automáticamente el origen (0,0).

POLYGON admite un exterior simple y huecos interiores disjuntos. Cierre implícito,
sin duplicar el primer punto. No se invierten, recortan, desplazan ni reparan contornos.
GEO-04 queda aplazado: sin transformación local/global, ejes globales o cotas deducidas.
Multipolígonos, curvas e islas dentro de huecos quedan explícitamente fuera de V0.1.

## Unidades y precisión

Longitudes internas en milímetros con sufijo _mm. units debe declarar mm. No hay
conversiones de unidades ni inferencias por magnitud. Las propiedades materiales
opcionales conservan su unidad textual explícita, sin interpretación automática.

NUM-01: Decimal para valores declarados; entrada Python mediante Decimal, string o int.
Se rechazan float y bool en esos campos. La lectura JSON usa Decimal directamente para
tokens no enteros. La escritura canónica utiliza cadenas decimales; las cantidades
mantienen tipo entero. El valor y escala Decimal se conservan; el formato fuente no.

NUM-02/03: ninguna tolerancia permite aceptar incumplimientos. No existe epsilon global.
Los predicados de orientación/intersección/área operan con Fraction exacta a partir
de Decimal, evitando incluso redondeos del contexto aritmético Decimal.

NUM-04: ningún ajuste geométrico silencioso. La clave temporal de comparación puede
omitir puntos collineales redundantes para probar equivalencia, pero nunca altera
la entrada ni sustituye su representación. No se fusionan objetos equivalentes.

Cero y ausencia son distintos. Diámetros, dimensiones, cantidades y offsets no tienen
valores estructurales predeterminados. Una colección omitida es vacía; un campo opcional
omitido es None, sin activar reglas de resolución implícitas.

## Versionado

La versión del paquete reside en pyproject.toml. schema_version del proyecto es
independiente y solo acepta 0.1.0. El paquete 0.2.0 retira la API Excel, manteniendo
el mismo esquema 0.1.0; ambas versiones no están vinculadas.

Cambios incompatibles del contrato requieren nueva versión de esquema y decisión
explícita sobre consumidores y migraciones. Los cambios incompatibles de una API de
adaptador se reflejan en la versión del paquete y su documentación, sin migrar un
contrato intacto. No se deduce la versión desde un nombre de archivo.
No existen versiones anteriores publicadas ni migraciones implementadas.
Las variantes usan discriminadores kind/pattern y rechazan claves desconocidas.

## Pruebas y calidad

Instalar .[dev] y ejecutar pytest, ruff check . y ruff format --check .
pytest usa importlib sin alterar sys.path; se conservan las diez pruebas de RCWD-000.
Las pruebas nuevas cubren tipos, variantes, referencias, topología, equivalencia,
precisión y JSON. tmp_path aísla archivos temporales; no se prueba cumplimiento normativo.

Ruff aplica E/F/I/UP/B y ancho de 100 caracteres. Las pruebas se separan por
responsabilidad; nuevas carpetas por módulo se introducirán cuando el volumen lo requiera.
No modificar reglas para ocultar fallos específicos.

La generación reproducible de artefactos se ejecuta con
`python scripts/generate_contract_artifacts.py`; una prueba comprueba que el esquema
versionado coincide con los modelos actuales. JSON Schema complementa, pero no reemplaza,
los controles de referencias, topología y límites numéricos del validador Python.

## Decisiones

Documentación UTF-8 en docs; ADR en docs/adr con problema, alternativas, decisión,
consecuencias y estado. Conservar ADR previos e identificar qué decisiones nuevas
resuelven sus pendientes. Separar aprobación conceptual, implementación y validación.
