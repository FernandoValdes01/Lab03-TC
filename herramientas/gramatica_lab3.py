"""
Especificacion formal de la GLC del lenguaje de programacion simplificado
(Laboratorio 3: Diseno y Validacion de Gramaticas).

Este modulo es la UNICA fuente de verdad de la gramatica: el validador
(`validar_gramatica.py`), el archivo de JFLAP (`gramatica/GLC_Lab03.cfg`) y
el informe LaTeX describen exactamente las mismas producciones.

Notacion (Material Referencial 2, cap. 4):
    G = (V, Sigma, P, S)
    V  : no terminales (alfabeto de variables)
    Sg : terminales (alfabeto de constantes)
    P  : conjunto de reglas X -> alpha
    S  : simbolo inicial

Convencion del curso: los no terminales se escriben entre angulos <...> y los
terminales sin angulos. El archivo .cfg de JFLAP codifica cada simbolo
con un caracter; las equivalencias se documentan junto a la gramatica.
"""

# --------------------------------------------------------------------------
# Terminales (Sigma)
# --------------------------------------------------------------------------

PALABRAS_RESERVADAS = ["Begin", "End", "Programa", "salida"]
EXTENSION_PALABRAS_RESERVADAS = ["mientras", "fin_mientras"]

OPERADORES_ARITMETICOS = ["+", "-", "*", "/", "%"]
OPERADOR_ASIGNACION = "="
OPERADORES_RELACIONALES = ["<", ">", "<=", ">="]
SIMBOLOS_ESPECIALES = ["#"]

# Clases lexicas: se reconocen por forma, no se enumeran valor por valor.
# El guion bajo forma parte de la clase IDENT (no es un terminal por separado).
CLASES_LEXICAS = {
    "IDENT": "identificador: letra (letra | digito | '_')*",
    "NUM": "numero: digito+ ('.' digito+)?",
}

# --------------------------------------------------------------------------
# No terminales (V) y su funcion
# --------------------------------------------------------------------------

NO_TERMINALES = [
    ("programa", "Encabezado y cuerpo completo del programa: 'Begin Programa <id> ... End'."),
    ("lista_instrucciones", "Secuencia de una o mas instrucciones del cuerpo del programa."),
    ("instruccion", "Una instruccion del lenguaje: asignacion, salida o lazo (extension)."),
    ("asignacion", "Encabezamiento de una asignacion: simple o con expresion aritmetica."),
    ("asignacion_simple", "Asignacion de un valor simple: <id> = <valor> #."),
    ("asignacion_expresion", "Asignacion de un resultado aritmetico: <id> = <expresion> #."),
    ("valor", "Valor simple que puede asignarse: un numero o un identificador."),
    ("expresion", "Expresion aritmetica binaria: <operando> <operador> <operando>."),
    ("operando", "Cada uno de los dos operandos de una expresion: identificador o numero."),
    ("operador", "Operador aritmetico binario: + - * / %."),
    ("salida_instr", "Instruccion de salida por pantalla: 'salida <id> #'."),
    ("mientras_instr", "Extension creativa: lazo 'mientras <condicion> ... fin_mientras'."),
    ("condicion", "Extension creativa: comparacion entre dos operandos."),
    ("operador_rel", "Extension creativa: operador relacional < > <= >=."),
]

# --------------------------------------------------------------------------
# Producciones (P)
# Cada produccion es (id, no_terminal, [simbolos_del_lado_derecho]).
# Un simbolo es terminal si esta en TERMINALES; en caso contrario es no terminal.
# --------------------------------------------------------------------------

PRODUCCIONES = [
    # --- Estructura del programa -----------------------------------------
    ("P01", "programa", ["Begin", "Programa", "IDENT", "lista_instrucciones", "End"]),
    ("P02", "lista_instrucciones", ["instruccion"]),
    ("P03", "lista_instrucciones", ["instruccion", "lista_instrucciones"]),
    ("P04", "instruccion", ["asignacion"]),
    ("P05", "instruccion", ["salida_instr"]),
    ("P06", "instruccion", ["mientras_instr"]),          # extension creativa
    # --- Asignacion simple ------------------------------------------------
    ("P07", "asignacion", ["asignacion_simple"]),
    ("P08", "asignacion", ["asignacion_expresion"]),
    ("P09", "asignacion_simple", ["IDENT", "=", "valor", "#"]),
    ("P10", "asignacion_expresion", ["IDENT", "=", "expresion", "#"]),
    ("P11", "valor", ["NUM"]),
    ("P12", "valor", ["IDENT"]),
    # --- Expresion aritmetica ---------------------------------------------
    ("P13", "expresion", ["operando", "operador", "operando"]),
    ("P14", "operando", ["IDENT"]),
    ("P15", "operando", ["NUM"]),
    ("P16", "operador", ["+"]),
    ("P17", "operador", ["-"]),
    ("P18", "operador", ["*"]),
    ("P19", "operador", ["/"]),
    ("P20", "operador", ["%"]),
    # --- Salida ------------------------------------------------------------
    ("P21", "salida_instr", ["salida", "IDENT", "#"]),
    # --- Extension creativa: repeticion (opcion B) -------------------------
    ("P22", "mientras_instr", ["mientras", "condicion", "lista_instrucciones", "fin_mientras"]),
    ("P23", "condicion", ["operando", "operador_rel", "operando"]),
    ("P24", "operador_rel", ["<"]),
    ("P25", "operador_rel", [">"]),
    ("P26", "operador_rel", ["<="]),
    ("P27", "operador_rel", [">="]),
]

SIMBOLO_INICIAL = "programa"

# --------------------------------------------------------------------------
# Terminales efectivos (Sigma) y no terminales (V) derivados de las reglas
# --------------------------------------------------------------------------

TERMINALES = (
    PALABRAS_RESERVADAS
    + OPERADORES_ARITMETICOS
    + [OPERADOR_ASIGNACION]
    + SIMBOLOS_ESPECIALES
    + list(CLASES_LEXICAS.keys())
    + EXTENSION_PALABRAS_RESERVADAS
    + OPERADORES_RELACIONALES
)

NO_TERMINALES_EFECTIVOS = sorted({p[1] for p in PRODUCCIONES} | {SIMBOLO_INICIAL})

# --------------------------------------------------------------------------
# Codificacion isomorfa para JFLAP 7.1
# --------------------------------------------------------------------------
# El analizador de JFLAP recorre el lado derecho de cada produccion caracter
# por caracter: toda letra mayuscula es una variable y cualquier otro caracter
# es un terminal. Por eso el archivo .cfg no puede usar nombres de varios
# caracteres. La codificacion siguiente asigna exactamente un caracter a cada
# simbolo de la gramatica; no cambia el lenguaje, solo la ortografia interna
# que lee JFLAP. El informe conserva los nombres legibles.

JFLAP_VARIABLES = {
    "programa": "S",
    "lista_instrucciones": "L",
    "instruccion": "I",
    "asignacion": "A",
    "asignacion_simple": "B",
    "asignacion_expresion": "E",
    "valor": "V",
    "expresion": "X",
    "operando": "O",
    "operador": "R",
    "salida_instr": "Q",
    "mientras_instr": "M",
    "condicion": "C",
    "operador_rel": "T",
}

JFLAP_TERMINALES = {
    "Begin": "b",
    "End": "e",
    "Programa": "p",
    "salida": "s",
    "mientras": "m",
    "fin_mientras": "f",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "%": "%",
    "=": "=",
    "#": "#",
    "<": "<",
    ">": ">",
    "<=": "l",
    ">=": "g",
    "IDENT": "i",
    "NUM": "n",
}

JFLAP_SIMBOLO_INICIAL = JFLAP_VARIABLES[SIMBOLO_INICIAL]

if set(JFLAP_VARIABLES) != set(NO_TERMINALES_EFECTIVOS):
    raise ValueError("La codificacion JFLAP no cubre exactamente los no terminales")
if set(JFLAP_TERMINALES) != set(TERMINALES):
    raise ValueError("La codificacion JFLAP no cubre exactamente los terminales")
if len(set(JFLAP_VARIABLES.values())) != len(JFLAP_VARIABLES):
    raise ValueError("Hay codigos JFLAP repetidos entre los no terminales")
if len(set(JFLAP_TERMINALES.values())) != len(JFLAP_TERMINALES):
    raise ValueError("Hay codigos JFLAP repetidos entre los terminales")
if set(JFLAP_VARIABLES.values()) & set(JFLAP_TERMINALES.values()):
    raise ValueError("Un codigo JFLAP no puede ser variable y terminal a la vez")


def codificar_jflap(simbolo):
    """Devuelve el caracter con el que JFLAP representa el simbolo dado."""
    if simbolo in JFLAP_VARIABLES:
        return JFLAP_VARIABLES[simbolo]
    return JFLAP_TERMINALES[simbolo]


def codificar_rhs_jflap(rhs):
    """Codifica un lado derecho completo sin separadores (JFLAP lo lee asi)."""
    return "".join(codificar_jflap(simbolo) for simbolo in rhs)


# Cadenas de evidencia para las capturas de JFLAP. Cada tupla es
# (nombre, no terminal inicial, cadena codificada, cadena legible).
JFLAP_EJEMPLOS = [
    ("arbol_z_xy", "I", "i=i+i#", "z = x + y #"),
    ("arbol_salida_z", "I", "si#", "salida z #"),
    ("arbol_extension", "M", "mi<ni=i+n#f",
     "mientras x < 10 x = x + 1 # fin_mientras"),
]

# Clases lexicas: identificadores y numeros se describen con expresiones
# regulares, no enumerando valores (Pregunta 1.5).
IDENTIFICADORES_RE = r"[A-Za-z][A-Za-z0-9_]*"
NUMEROS_RE = r"[0-9]+(\.[0-9]+)?"

# --------------------------------------------------------------------------
# Programas y cadenas de referencia
# --------------------------------------------------------------------------

PROGRAMA_REFERENCIA = """Begin
Programa operativo_01_02

x = 1.345 #
y = 20 #

/* operaciones y salidas */

z=x+y#
z2 = x + y #
h=z-x#
h2 = z - x #
k=h*y#
t=k/z#
m = k % 10 #

salida z #
salida h #
salida k #

salida t #
salida m #

temporal = 0 #
temporal = x #
x=y#
y = temporal #

salida x #
salida y #

End"""

# Cadena del caso 8 de la Pregunta 4 (el enunciado la escribe con "/" como
# separador de lineas).
PROGRAMA_CASO_8 = """Begin
Programa prueba
x = 5 #
salida x #
End"""

# Casos de la Pregunta 4: (numero, cadena, comentario_del_docente)
CASOS_P4 = [
    (1, "x = 10 #", "Asignacion simple con valor numerico."),
    (2, "z=x+y#", "Asignacion con expresion aritmetica."),
    (3, "salida z #", "Instruccion de salida."),
    (4, "x 10 #", "Falta el operador de asignacion."),
    (5, "z=+xy#", "El operador '+' no tiene operando a la izquierda."),
    (6, "salida #", "Falta el argumento de la instruccion salida."),
    (7, "x = 20", "Falta el terminador de instruccion."),
    (8, PROGRAMA_CASO_8, "Programa completo con encabezado y cuerpo."),
]

# Pregunta 3.14: cadenas cuya generacion debe determinarse.
CASOS_P3_14 = [
    ("x = 20 #", "Asignacion simple con un numero entero."),
    ("z = x * y #", "Asignacion con expresion aritmetica."),
    ("salida temporal #", "Salida de un identificador."),
]

# Extension creativa (opcion B): cadena valida e invalida.
EXTENSION_CADENA_VALIDA = """Begin
Programa lazo
mientras x < 10
x = x + 1 #
fin_mientras
salida x #
End"""

EXTENSION_CADENA_INVALIDA = """Begin
Programa lazo
mientras x < 10
x = x + 1 #
salida x #
End"""

# --------------------------------------------------------------------------
# Funciones de apoyo
# --------------------------------------------------------------------------

def es_terminal(simbolo):
    """True si el simbolo pertenece a Sigma."""
    return simbolo in TERMINALES


def es_no_terminal(simbolo):
    """True si el simbolo pertenece a V."""
    return simbolo in NO_TERMINALES_EFECTIVOS


def producciones_de(no_terminal):
    """Producciones que tienen como lado izquierdo el no terminal dado."""
    return [(pid, nt, rhs) for (pid, nt, rhs) in PRODUCCIONES if nt == no_terminal]


def gramatica_como_texto():
    """Presentacion de la gramatica en notacion X -> alpha (para el informe)."""
    lineas = []
    for pid, nt, rhs in PRODUCCIONES:
        lado = " ".join(rhs) if rhs else "epsilon"
        lineas.append("%s)  <%s> -> %s" % (pid, nt, lado))
    return "\n".join(lineas)

# Alias compartido con las pruebas y utilidades de validación.
CODIGOS_JFLAP = {**JFLAP_VARIABLES, **JFLAP_TERMINALES}
