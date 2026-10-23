# Registro histórico — Interfaz Excel V0.1 en español (retirada)

**No vigente desde el paquete 0.2.0.** RCWD-EXCEL-RETIRE-000 retiró el adaptador,
los libros y sus comandos. El contenido siguiente describe RCWD-001B exclusivamente
como registro histórico; sus ejemplos no se ejecutan en la versión actual.
Consulte [ADR-007](adr/ADR-007-retire-excel.md) y la [interfaz web vigente](web_prototype.md).

Estado histórico: implementado en RCWD-001B con openpyxl y posteriormente retirado.
El esquema canónico 0.1.0 permanece intacto.
Hay exactamente 17 hojas visibles: once principales y seis avanzadas. No hay hojas ocultas,
macros, fórmulas calculadas ni hoja Trayectorias.

## Generación y lectura

Desde la raíz, con el paquete instalado mediante `python -m pip install -e ".[dev]"`:

```powershell
.\.venv\Scripts\python.exe scripts/generate_excel_artifacts.py
```

Produce archivos estables versionables:
- `examples/excel/plantilla_v0_1.xlsx`: plantilla vacía, sin valores estructurales.
- `examples/excel/ejemplo_v0_1.xlsx`: exportación fiel de `examples/project_v0_1.json`.

```python
from rcwall.io.excel import (
    create_template,
    export_project,
    read_project,
    validate_workbook,
    inspect_workbook,
)
from rcwall.io.json import read_project as read_json, write_project

create_template("entrada.xlsx", editable_rows=200)
project = read_json("examples/project_v0_1.json")
export_project(project, "proyecto.xlsx")
result = inspect_workbook("proyecto.xlsx")
print(result.report.to_dict())  # Hoja, Fila, Columna, Código, Explicación
if result.project is not None:
    write_project(result.project, "proyecto.json")
# read_project devuelve ProjectDefinition o lanza ExcelValidationError con atributo report.
# validate_workbook devuelve únicamente ExcelValidationReport.
```

También existe `generate_example(json_path, xlsx_path)`. Estas funciones no crean carpetas
padre automáticamente; el script de artefactos sí crea su directorio de salida.
`export_project` valida el proyecto y construye el libro antes de abrir el destino.
No se afirma escritura transaccional frente a fallos de disco o interrupciones.

## Diligenciamiento

Filas 1–5: título, instrucciones y leyenda. Fila 6: encabezados. Datos desde fila 7.
Los encabezados se pueden reordenar conservando nombre exacto y fila. No renombrar hojas.
La plantilla vacía es un XLSX válido; antes de importar debe completarse exactamente una
fila en Proyecto, incluida versión 0.1.0 y unidades Milímetros.

Azul indica campos obligatorios, gris opcionales y violeta condicionales. Los títulos y
encabezados están bloqueados; los datos están desbloqueados. La protección sin contraseña
evita accidentes, no es un mecanismo de seguridad. Hay 200 filas preparadas por defecto;
para ampliar en Excel, desproteger, copiar una fila de entrada con su formato/listas y
extender el filtro. El lector recorre también filas adicionales no formateadas.

Todas las magnitudes decimales deben guardarse como **texto** usando punto decimal, sin
separadores de miles. Las celdas ya tienen formato Texto. Pegar desde otra aplicación puede
reemplazarlo o introducir números nativos: el lector los rechazará. Cambiar a Texto después
de que Excel redondeó un número no recupera el dato; reingrese el valor desde su fuente.
Ejemplo preservado exactamente: `3000.000000000000000000000000001`.

Cantidades y órdenes admiten enteros nativos de hasta 15 dígitos o texto entero. Valores
mayores deben escribirse como texto; nunca se convierten a float. El programa no redondea,
rellena offsets, interpreta políticas ni calcula posiciones de refuerzo.

Una celda vacía equivale a campo omitido: Pydantic exige los obligatorios y conserva None
en los opcionales. No significa cero. Las colecciones sin filas quedan vacías conforme al
contrato. Filas totalmente vacías se omiten; espacios en texto no se recortan ni se traducen.
Los campos libres conservan idioma, espacios y contenido original. Solo las enumeraciones
cerradas tienen traducción. Los códigos de error y rutas canónicas son identificadores técnicos.

## Mapeo de columnas

La tabla de correspondencias está en `src/rcwall/io/excel/mapping.py`; una prueba contrasta
los campos representados con el JSON Schema. Las hojas avanzadas normalizan colecciones
anidadas sin crear nuevas entidades de dominio.

### Proyecto

Colección o proyección: `project`. Diligencie una sola fila. Seleccione versión y unidades. Los identificadores son texto.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de proyecto | `project_id` | Texto | Obligatorio | — |
| Versión del esquema | `schema_version` | Texto | Obligatorio | 0.1.0 → `0.1.0` |
| Unidades | `units` | Texto | Obligatorio | Milímetros → `mm` |

### Geometrías

Colección o proyección: `geometries`. Rectángulo: declare origen, longitud y espesor. Polígono: deje esas celdas vacías y registre sus contornos en Vértices. No repita el primer vértice al cerrar.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de geometría | `geometry_id` | Texto | Obligatorio | — |
| Tipo de geometría | `shape.kind` | Texto | Obligatorio | Rectángulo → `RECTANGLE`; Polígono → `POLYGON` |
| Origen X (mm) | `shape.origin.x_mm` | Decimal como texto | Según variante | — |
| Origen Y (mm) | `shape.origin.y_mm` | Decimal como texto | Según variante | — |
| Longitud (mm) | `shape.length_mm` | Decimal como texto | Según variante | — |
| Espesor (mm) | `shape.thickness_mm` | Decimal como texto | Según variante | — |
| Descripción | `description` | Texto | Opcional | — |

### Regiones

Colección o proyección: `regions`. Cada región conserva su propia geometría y su relación con la geometría principal. Rectángulo: declare origen, longitud y espesor. Polígono: deje esas celdas vacías y registre sus contornos en Vértices. No repita el primer vértice al cerrar.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de región | `region_id` | Texto | Obligatorio | — |
| ID de geometría | `geometry_id` | Texto | Obligatorio | — |
| Función de la región | `role` | Texto | Obligatorio | Borde → `BOUNDARY`; Alma → `WEB`; Otro → `OTHER` |
| Tipo de geometría | `shape.kind` | Texto | Obligatorio | Rectángulo → `RECTANGLE`; Polígono → `POLYGON` |
| Origen X (mm) | `shape.origin.x_mm` | Decimal como texto | Según variante | — |
| Origen Y (mm) | `shape.origin.y_mm` | Decimal como texto | Según variante | — |
| Longitud (mm) | `shape.length_mm` | Decimal como texto | Según variante | — |
| Espesor (mm) | `shape.thickness_mm` | Decimal como texto | Según variante | — |
| Descripción | `description` | Texto | Opcional | — |

### Referencias

Colección o proyección: `references`. Declare los extremos de una línea en el sistema local; no se recortan ni desplazan.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de referencia | `reference_id` | Texto | Obligatorio | — |
| ID de geometría | `geometry_id` | Texto | Obligatorio | — |
| Tipo de referencia | `kind` | Texto | Obligatorio | Línea → `LINE` |
| Inicio X (mm) | `start.x_mm` | Decimal como texto | Obligatorio | — |
| Inicio Y (mm) | `start.y_mm` | Decimal como texto | Obligatorio | — |
| Final X (mm) | `end.x_mm` | Decimal como texto | Obligatorio | — |
| Final Y (mm) | `end.y_mm` | Decimal como texto | Obligatorio | — |

### Configuraciones

Colección o proyección: `configurations`. Una configuración puede reutilizarse en varias secciones sin duplicar sus datos.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de configuración | `config_id` | Texto | Obligatorio | — |
| ID de geometría | `geometry_id` | Texto | Obligatorio | — |
| Descripción | `description` | Texto | Opcional | — |

### Barras

Colección o proyección: `bar_layouts`. Por cantidad: referencia, cantidad, diámetro y ambos desplazamientos. Por separación: referencia, diámetro, separación, desplazamientos, política y alineación. Explícita: use Barras explícitas; deje vacíos los parámetros lineales.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de distribución | `layout_id` | Texto | Obligatorio | — |
| ID de configuración | `config_id` | Texto | Obligatorio | — |
| ID de región | `region_id` | Texto | Opcional | — |
| Patrón de distribución | `distribution.pattern` | Texto | Obligatorio | Distribución por cantidad → `LINEAR_COUNT`; Distribución por separación → `LINEAR_SPACING`; Distribución explícita → `EXPLICIT` |
| ID de referencia | `distribution.reference_id` | Texto | Según variante | — |
| Cantidad | `distribution.quantity` | Entero | Según variante | — |
| Diámetro (mm) | `distribution.diameter_mm` | Decimal como texto | Según variante | — |
| Separación (mm) | `distribution.spacing_mm` | Decimal como texto | Según variante | — |
| Desplazamiento inicial (mm) | `distribution.start_offset_mm` | Decimal como texto | Según variante | — |
| Desplazamiento final (mm) | `distribution.end_offset_mm` | Decimal como texto | Según variante | — |
| Política de separación | `distribution.spacing_policy` | Texto | Según variante | — |
| Alineación | `distribution.alignment` | Texto | Según variante | — |

### Secciones

Colección o proyección: `sections`. La sección reúne geometría, configuración y materiales declarados. Las propiedades adicionales se registran en Propiedades de materiales. No se asignan resistencias predeterminadas.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de sección | `section_id` | Texto | Obligatorio | — |
| ID de geometría | `geometry_id` | Texto | Obligatorio | — |
| ID de configuración | `config_id` | Texto | Obligatorio | — |
| Especificación del concreto | `materials.concrete.specification` | Texto | Obligatorio | — |
| Especificación del acero | `materials.reinforcement.specification` | Texto | Obligatorio | — |
| Descripción | `description` | Texto | Opcional | — |

### Muros

Colección o proyección: `walls`. El muro es el elemento físico. Su identidad es independiente de la sección reforzada.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de muro | `wall_id` | Texto | Obligatorio | — |
| Descripción | `description` | Texto | Opcional | — |

### Asignaciones

Colección o proyección: `assignments`. Asigne una sección a cada par muro y nivel. El nivel es una referencia externa declarada.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de asignación | `assignment_id` | Texto | Obligatorio | — |
| ID de muro | `wall_id` | Texto | Obligatorio | — |
| ID de nivel | `level_id` | Texto | Obligatorio | — |
| ID de sección | `section_id` | Texto | Obligatorio | — |

### Estribos

Colección o proyección: `transverse_assemblies`. Conjuntos pendientes de definir. Declare sus componentes en Estribos-barras. No se calculan formas ni ganchos.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de estribo | `assembly_id` | Texto | Obligatorio | — |
| ID de configuración | `config_id` | Texto | Obligatorio | — |
| ID de región | `region_id` | Texto | Opcional | — |
| Estado de definición | `definition_status` | Texto | Obligatorio | Pendiente de definir → `UNRESOLVED` |
| Descripción | `description` | Texto | Opcional | — |

### Dibujo

Colección o proyección: `drawings`. Especificaciones pendientes de definir. La escala es una magnitud decimal textual. No se genera dibujo.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de dibujo | `drawing_id` | Texto | Obligatorio | — |
| ID de sección | `section_id` | Texto | Obligatorio | — |
| Estado de definición | `definition_status` | Texto | Obligatorio | Pendiente de definir → `UNRESOLVED` |
| ID de plantilla | `template_id` | Texto | Opcional | — |
| Escala de dibujo (adimensional) | `drawing_scale` | Decimal como texto | Opcional | — |

### Vértices (avanzada)

Colección o proyección: `vertices`. Contorno exterior antihorario y huecos horarios. Numere vértices desde 1 en cada contorno. Conserve el orden; el cierre es implícito. Solo propietarios poligonales.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| Tipo de propietario | `owner_type` | Texto | Obligatorio | Geometría → `geometries`; Región → `regions` |
| ID de propietario | `owner_id` | Texto | Obligatorio | — |
| Tipo de contorno | `loop_role` | Texto | Obligatorio | Exterior → `outer`; Hueco → `holes` |
| Orden de contorno | `loop_order` | Entero | Obligatorio | — |
| Orden de vértice | `order` | Entero | Obligatorio | — |
| Coordenada X (mm) | `x_mm` | Decimal como texto | Obligatorio | — |
| Coordenada Y (mm) | `y_mm` | Decimal como texto | Obligatorio | — |

### Barras explícitas (avanzada)

Colección o proyección: `explicit_bars`. Solo para distribución explícita. Numere las barras desde 1 por distribución; no se calculan posiciones.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de distribución | `layout_id` | Texto | Obligatorio | — |
| Orden de barra | `order` | Entero | Obligatorio | — |
| ID de barra | `bar_id` | Texto | Obligatorio | — |
| Posición X (mm) | `position.x_mm` | Decimal como texto | Obligatorio | — |
| Posición Y (mm) | `position.y_mm` | Decimal como texto | Obligatorio | — |
| Diámetro (mm) | `diameter_mm` | Decimal como texto | Obligatorio | — |

### Propiedades de materiales (avanzada)

Colección o proyección: `material_properties`. Numere propiedades desde 1 por sección y material. Nombre, valor y unidad se conservan exactamente.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de sección | `section_id` | Texto | Obligatorio | — |
| Material | `material_role` | Texto | Obligatorio | Concreto → `concrete`; Acero → `reinforcement` |
| Orden de propiedad | `order` | Entero | Obligatorio | — |
| Nombre de propiedad | `name` | Texto | Obligatorio | — |
| Valor (unidad declarada) | `value` | Decimal como texto | Obligatorio | — |
| Unidad de la propiedad | `unit` | Texto | Obligatorio | — |

### Barras dobladas (avanzada)

Colección o proyección: `bent_bars`. Declaraciones pendientes de definir; no hay trayectorias, radios, ganchos ni geometría calculada.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de barra doblada | `bent_bar_id` | Texto | Obligatorio | — |
| Estado de definición | `definition_status` | Texto | Obligatorio | Pendiente de definir → `UNRESOLVED` |
| Diámetro (mm) | `diameter_mm` | Decimal como texto | Opcional | — |
| Descripción | `description` | Texto | Opcional | — |

### Estribos-barras (avanzada)

Colección o proyección: `assembly_bars`. Relacione estribos con barras dobladas existentes. Numere componentes desde 1 por estribo.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de estribo | `assembly_id` | Texto | Obligatorio | — |
| Orden de componente | `order` | Entero | Obligatorio | — |
| ID de barra doblada | `bent_bar_id` | Texto | Obligatorio | — |

### Distribución vertical (avanzada)

Colección o proyección: `vertical_placements`. Coordenadas Z declaradas, positivas hacia arriba. La cota final supera la inicial. No se infieren elevaciones ni se calculan ubicaciones.

| Encabezado visible | Campo interno | Entrada | Condición | Opciones cerradas |
| --- | --- | --- | --- | --- |
| ID de colocación | `placement_id` | Texto | Obligatorio | — |
| ID de asignación | `assignment_id` | Texto | Obligatorio | — |
| ID de estribo | `assembly_id` | Texto | Obligatorio | — |
| Estado de definición | `definition_status` | Texto | Obligatorio | Pendiente de definir → `UNRESOLVED` |
| Cota inicial Z (mm) | `z_start_mm` | Decimal como texto | Obligatorio | — |
| Cota final Z (mm) | `z_end_mm` | Decimal como texto | Obligatorio | — |
| Separación (mm) | `spacing_mm` | Decimal como texto | Opcional | — |
| Política de separación | `spacing_policy` | Texto | Opcional | — |

## Condiciones y orden de colecciones

- Rectángulo: origen X/Y, longitud y espesor obligatorios. Polígono: esas columnas vacías;
  sus coordenadas pertenecen a Vértices. Exteriores antihorarios, huecos horarios.
- Vértices: propietario Geometría o Región y su ID. Exterior con orden de contorno 1;
  huecos con orden independiente 1, 2, 3…; vértices desde 1 por contorno.
  No repita el punto inicial al final. Se conserva el orden, incluso el de los huecos.
- Distribución por cantidad: referencia, cantidad, diámetro y ambos desplazamientos
  obligatorios; alineación opcional; separación/política vacías.
- Distribución por separación: referencia, diámetro, separación, ambos desplazamientos,
  política y alineación obligatorios; cantidad vacía.
- Distribución explícita: parámetros lineales vacíos; una o más filas en Barras explícitas,
  con identificador único por barra y orden consecutivo por distribución.
- Propiedades: orden consecutivo por sección/material. No existe catálogo ficticio de
  materiales; las especificaciones se declaran en Secciones.
- Estribos-barras: orden consecutivo por estribo, referencia a una barra doblada existente.
- Órdenes duplicados, saltos, filas huérfanas o incompatibles son errores, no datos ignorados.
- Las filas principales conservan su orden físico. Las avanzadas usan el orden explícito,
  independientemente de su posición física. Ordenarlas por otras columnas no modifica la
  secuencia canónica si se mantienen los números de orden.
- Los contratos pendientes exigen «Pendiente de definir». Los campos opcionales se conservan
  sin completarlos con geometrías, estados o políticas inventadas.

## Diagnósticos y límites

Cada error tiene hoja, fila física, encabezado o columna, código y explicación española.
Los errores canónicos incluyen además su ruta original accesible desde Python.
El adaptador distingue hojas/encabezados ausentes o desconocidos, duplicados, celdas vacías,
tipos, enumeraciones, referencias, IDs, topología y parámetros incompatibles.

Se recopilan errores independientes. Cuando una entidad no supera tipos, se ejecuta
validación canónica sobre las otras entidades válidas únicamente para diagnóstico;
pueden aparecer referencias derivadas a entidades inválidas. No se devuelve un proyecto
parcial ni se corrigen datos. Primero corrija errores de tipos y después vuelva a validar.

Fórmulas reales, celdas de error, magnitudes decimales numéricas y enteros nativos demasiado
grandes se rechazan. Texto libre que comienza por '=' se exporta como cadena literal.
El límite de longitud por celda de Excel se verifica antes de escribir, sin truncar.
Las filas informativas no forman parte de los datos importados.

Los reportes validan datos del contrato, no cumplimiento normativo, recubrimientos,
factibilidad del armado, estribos, posiciones calculadas o dibujo. No se implementan
transformaciones local/global, DXF ni integración con programas externos.

Consulte [decisiones y verificación](excel_decisions.md) para límites de precisión,
protección, interacción nativa y trazabilidad. Las 115 pruebas previas se conservan;
las pruebas Excel están en `tests/test_excel.py`.
