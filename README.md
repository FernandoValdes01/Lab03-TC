# Lab03-TC · Gramáticas libres de contexto

Laboratorio 3 de Teoría de la Computación, INFO1148.

**Integrantes:** Juan Muñoz Veloso y Fernando Valdés Gómez.

El trabajo define una gramática para un lenguaje de programación simplificado,
con asignaciones, operaciones aritméticas, instrucciones de salida y una extensión
de repetición `mientras ... fin_mientras`.

## Archivos

| Ruta | Contenido |
|---|---|
| `Lab03_Juan_Munoz_Veloso.pdf` | Informe del laboratorio. |
| `Lab03_Juan_Munoz_Veloso.tex` | Fuente del informe. |
| `gramatica/GLC_Lab03.cfg` | Gramática compatible con JFLAP 7.1. |
| `gramatica/GLC_Lab03.txt` | Definición formal y codificación de símbolos. |
| `gramatica/equivalencias_jflap.txt` | Correspondencia entre símbolos legibles y códigos de JFLAP. |
| `gramatica/casos_jflap.tsv` | Casos de prueba codificados y resultados esperados. |
| `herramientas/` | Analizador Python, pruebas y utilidades Java para JFLAP. |
| `evidencias/` | Resultados de validación y derivaciones. |
| `figuras/` | Árboles legibles y capturas de componentes de JFLAP. |
| `fonts/` | Fuente del informe y su licencia. |

## Requisitos

- Python 3, sin paquetes externos, para el analizador y sus pruebas.
- JDK 21 o posterior y el archivo JAR de JFLAP 7.1 para las comprobaciones Java.
- Sesión gráfica para reproducir las capturas de árboles de JFLAP.
- XeLaTeX y latexmk para compilar el informe.
- `rsvg-convert`, opcional, para convertir los árboles SVG a PNG o PDF.

Los comandos siguientes se ejecutan desde la raíz del repositorio. El JAR de
JFLAP es una dependencia externa y no se distribuye en este repositorio.

## Validar el lenguaje

```sh
python3 -m unittest discover -s herramientas -p 'test_*.py'
python3 herramientas/validar_gramatica.py validacion
python3 herramientas/validar_gramatica.py derivacion 'z = x + y #' instruccion
python3 herramientas/validar_gramatica.py programa
```

El analizador distingue el programa completo de los fragmentos de instrucciones.
`IDENT` representa `[A-Za-z][A-Za-z0-9_]*` y `NUM` representa
`[0-9]+(\.[0-9]+)?`. La gramática permite una operación binaria por expresión;
no incluye precedencia, signos unarios ni comprobaciones de tipos.

## Abrir la gramática en JFLAP

```sh
export LAB03_JFLAP_JAR='/ruta/al/JFLAP7.1-fixed.jar'
java -jar "$LAB03_JFLAP_JAR" gramatica/GLC_Lab03.cfg
```

JFLAP procesa símbolos de un carácter. El archivo `.cfg` usa una correspondencia
biyectiva para representar los 14 no terminales y los 19 terminales del informe,
con 27 producciones. `S` corresponde a `<programa>`. Los códigos `i` y `n`
representan clases léxicas; no almacenan los nombres o valores concretos.

Para un programa completo se usa `S` como inicio. Para analizar una instrucción
suelta se selecciona `I`; para el cuerpo de un lazo, `M`. Ejemplos:

| Instrucción | Entrada codificada | Inicio |
|---|---|---|
| `z = x + y #` | `i=i+i#` | `I` |
| `salida z #` | `si#` | `I` |
| `mientras x < 10 x = x + 1 # fin_mientras` | `mi<ni=i+n#f` | `M` |

## Verificar con la biblioteca de JFLAP

```sh
mkdir -p build/java
javac -cp "$LAB03_JFLAP_JAR" -d build/java herramientas/*.java
java -Djava.awt.headless=true -cp "$LAB03_JFLAP_JAR:build/java" \
  VerificarGramaticaJFLAP gramatica/GLC_Lab03.cfg
java -Djava.awt.headless=true -cp "$LAB03_JFLAP_JAR:build/java" \
  VerificarCasosJFLAP gramatica/GLC_Lab03.cfg gramatica/casos_jflap.tsv \
  figuras/captura_jflap.png
```

`VerificarGramaticaJFLAP` comprueba la lectura y los tamaños de los alfabetos.
`VerificarCasosJFLAP` contrasta 14 casos con los resultados esperados usando las
clases de transformación y análisis CYK de JFLAP. Las pruebas Python comprueban
que cada producción del XML corresponde a la especificación por tokens.

## Reproducir las capturas de árboles

Con una sesión gráfica y las clases Java compiladas:

```sh
java -cp "$LAB03_JFLAP_JAR:build/java" CapturarArbolJFLAP \
  gramatica/GLC_Lab03.cfg 'i=i+i#' figuras/jflap_arbol_z_xy.png I \
  'JFLAP 7.1 - z = x + y #'
java -cp "$LAB03_JFLAP_JAR:build/java" CapturarArbolJFLAP \
  gramatica/GLC_Lab03.cfg 'si#' figuras/jflap_arbol_salida_z.png I \
  'JFLAP 7.1 - salida z #'
java -cp "$LAB03_JFLAP_JAR:build/java" CapturarArbolJFLAP \
  gramatica/GLC_Lab03.cfg 'mi<ni=i+n#f' figuras/jflap_arbol_extension.png M \
  'JFLAP 7.1 - mientras x < 10 x = x + 1 # fin_mientras'
```

Las imágenes `jflap_arbol_*.png` son capturas de componentes de la interfaz de
JFLAP renderizados por la utilidad Java incluida. `captura_jflap.png` muestra su
tabla de producciones. Los archivos `arbol_*.svg`, `.png` y `.pdf` son esquemas
generados por el analizador Python, identificados por separado en el informe.

## Regenerar archivos y evidencias

Estos comandos actualizan los archivos generados:

```sh
python3 herramientas/generar_cfg_jflap.py
python3 herramientas/validar_gramatica.py evidencias evidencias/evidencias_lab03.txt
java -Djava.awt.headless=true -cp "$LAB03_JFLAP_JAR:build/java" \
  VerificarGramaticaJFLAP gramatica/GLC_Lab03.cfg > evidencias/verificacion_jflap.txt
java -Djava.awt.headless=true -cp "$LAB03_JFLAP_JAR:build/java" \
  VerificarCasosJFLAP gramatica/GLC_Lab03.cfg gramatica/casos_jflap.tsv \
  figuras/captura_jflap.png > evidencias/validacion_casos_jflap.txt
```

## Compilar el informe

```sh
latexmk -pdf Lab03_Juan_Munoz_Veloso.tex
latexmk -c Lab03_Juan_Munoz_Veloso.tex
```

`.latexmkrc` selecciona XeLaTeX. El informe usa las fuentes locales de `fonts/`.
Para actualizar una figura vectorial a partir de su SVG:

```sh
rsvg-convert -f pdf1.4 figuras/arbol_z_xy.svg -o figuras/arbol_z_xy.pdf
```

## Acceso

Repositorio privado: https://github.com/FernandoValdes01/Lab03-TC

Archivo de JFLAP:
https://github.com/FernandoValdes01/Lab03-TC/blob/main/gramatica/GLC_Lab03.cfg

Los enlaces a archivos estarán disponibles después del primer commit y push.
Para que el docente pueda abrirlos, su cuenta debe tener acceso al repositorio privado.
