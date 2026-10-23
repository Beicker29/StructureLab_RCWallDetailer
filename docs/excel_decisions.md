# Decisiones técnicas de RCWD-001B

Estado: implementado. El contrato canónico 0.1.0 y su JSON Schema no se modifican.

- **Frontera:** openpyxl se incorpora exclusivamente como dependencia del adaptador.
  Modelos, predicados y validación canónica se reutilizan sin introducir reglas estructurales.
- **Idioma:** las 17 hojas, columnas, instrucciones, comentarios, listas y mensajes son
  españoles. Las tablas de mapping.py son explícitas e invertibles. Los identificadores,
  descripciones, políticas, alineaciones y especificaciones aportados por el usuario
  permanecen intactos, incluso si contienen otro idioma o espacios significativos.
- **Precisión:** toda magnitud decimal se escribe como texto. Se rechazan todos los
  decimales almacenados como número nativo: aun un entero aparente no permite recuperar
  la escala o los dígitos que Excel pudo haber descartado antes de guardar. No se intenta
  recuperar precisión con str(float). Las cadenas llegan a los validadores Decimal existentes.
- **Enteros:** hasta 15 dígitos se pueden escribir como enteros nativos. Cantidades mayores
  se escriben como texto y se leen directamente como int. Se rechazan bool, fracciones y
  números nativos fuera del límite conservador de 15 dígitos. Los límites de diseño son
  exclusivamente los establecidos por el contrato.
- **Orden:** las entidades principales siguen el orden físico de filas no vacías.
  Las colecciones anidadas usan índices consecutivos desde 1. El exterior tiene orden 1;
  los huecos tienen su propia secuencia desde 1. No se ordenan geométricamente los puntos,
  ni se invierten contornos. Duplicados, saltos y referencias huérfanas son errores.
- **Vacíos:** una fila totalmente vacía se omite. Una celda vacía no introduce un cero ni
  un valor estructural. Pydantic resuelve los campos opcionales y colecciones vacías según
  los valores ya definidos en el contrato. La plantilla vacía es un XLSX utilizable, pero
  no un proyecto aceptable hasta diligenciar Proyecto. No se introduce un ID ficticio.
- **Condicionales:** los parámetros suministrados no se eliminan para encajar una variante.
  Pydantic rechaza los parámetros incompatibles. Filas avanzadas incompatibles o sin
  propietario se reportan y bloquean la importación, en lugar de descartarse silenciosamente.
- **Diagnósticos:** SourceMap enlaza rutas canónicas con celdas físicas; los índices de las
  uniones Pydantic se traducen a los encabezados originales. Los errores de dominio conservan
  su código y ruta técnica, con explicación española. Si hay errores locales, se reutilizan
  los validadores de referencias/geometría sobre registros independientes válidos, solo
  para diagnóstico. Nunca se devuelve un proyecto parcial aceptado. Referencias a registros
  inválidos pueden generar errores derivados; primero deben corregirse los errores locales.
- **Presentación:** encabezados en fila 6, datos desde fila 7; instrucciones dentro de cada
  hoja para respetar exactamente 17 hojas visibles. Se reservan 200 filas editables por
  defecto, ampliables. Protección sin contraseña contra accidentes, no como seguridad.
- **Integridad de texto:** se fuerza tipo cadena al escribir texto que empieza con '='.
  Los retornos de carro se codifican como referencias de caracteres XML para evitar
  la normalización de saltos de línea del parser; el texto leído conserva su contenido.
  Fórmulas reales y errores Excel se rechazan al leer. Se rechaza texto que supera la
  capacidad de una celda o contiene controles no admitidos, antes de guardar el libro.

## Límites y verificación

No hay motores de distribución, geometría transversal calculada, cumplimiento normativo,
DXF, transformaciones ni integraciones externas. Los estados pendientes se muestran como
«Pendiente de definir». Las políticas libres siguen sin interpretación algorítmica.

Los encabezados pueden cambiar de posición conservando sus nombres exactos y la fila 6.
Faltantes, desconocidos o duplicados se reportan; no se realiza migración de plantillas antiguas.
Las filas de datos se leen más allá del área inicialmente formateada, pero ampliar el estilo,
las listas y los filtros en Excel requiere desproteger y copiar una fila de entrada.

La revisión automatizada verifica estructura OOXML, valores almacenados, protección,
formatos, listas, ausencia de fórmulas generadas e ida/vuelta JSON. Se renderizaron las
17 hojas para revisar presentación. El renderizador auxiliar puede presentar cadenas
numéricas como números; la verificación de precisión se hace sobre el XLSX guardado y
el JSON reconstruido. No se verificó la interacción manual en Microsoft Excel instalado.

Las decisiones de algoritmos, normativa y formatos CAD permanecen pendientes en los hitos
posteriores; la interfaz Excel no las resuelve ni altera los contratos.
