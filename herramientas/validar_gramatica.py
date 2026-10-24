#!/usr/bin/env python3
"""
Validador de la GLC del lenguaje de programacion simplificado (Laboratorio 3).

Herramienta de apoyo reproducible para el informe: tokeniza el codigo fuente,
lo reconoce con la GLC del modulo `gramatica_lab3.py` y responde preguntas de
la rubrica:

    validacion   de las 8 cadenas de la Pregunta 4 y de los casos extra;
    derivacion   por la izquierda de una cadena;
    arbol        arbol sintactico de una cadena (SVG, se convierte a PNG);
    programa     valida y deriva el programa de referencia del enunciado.

El parser es descendente recursivo con retroceso: para cada no terminal
prueba sus producciones en orden y devuelve el primer analisis que consume
todos los tokens. En las cadenas de prueba el analisis resulto unico; el
conteo de ejemplos no demuestra ausencia de ambiguedad para todo el lenguaje.

Uso:
    python3 validar_gramatica.py validacion
    python3 validar_gramatica.py derivacion "z = x + y #"
    python3 validar_gramatica.py arbol "z = x + y #" ../figuras/arbol.svg
    python3 validar_gramatica.py programa
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gramatica_lab3 as G  # noqa: E402


# ==========================================================================
# Analisis lexico
# ==========================================================================

RESERVADAS = set(G.PALABRAS_RESERVADAS + G.EXTENSION_PALABRAS_RESERVADAS)
SIMPLES = set("+-*/%=#_<>")
DOBLES = ("<=", ">=")


class Token(object):
    """Un lexema: clase (IDENT/NUM/LIT/ERROR) y texto."""

    def __init__(self, clase, texto, posicion):
        self.clase = clase
        self.texto = texto
        self.posicion = posicion

    def __repr__(self):
        return "Token(%s, %r)" % (self.clase, self.texto)


def es_letra_ascii(c):
    """Letra A-Z o a-z. Excluye letras Unicode como la enie."""
    return ("A" <= c <= "Z") or ("a" <= c <= "z")


def es_digito_ascii(c):
    """Digito 0-9. Excluye digitos Unicode de otros alfabetos."""
    return "0" <= c <= "9"


def es_blanco_ascii(c):
    """Espacio, tabulador, salto de linea y controles blancos clasicos."""
    return c in " \t\r\n\f\v"


def tokenizar(codigo):
    """Convierte el codigo en una lista de tokens. Devuelve (tokens, errores).

    Los comentarios `/* ... */` y `// ...` se ignoran: son elementos lexicos
    que no forman parte del lenguaje y aparecen en el programa de referencia.
    """
    tokens = []
    errores = []
    i = 0
    n = len(codigo)
    while i < n:
        c = codigo[i]
        if es_blanco_ascii(c):
            i += 1
            continue
        if codigo.startswith("/*", i):
            fin = codigo.find("*/", i + 2)
            if fin < 0:
                errores.append("comentario sin cerrar en la posicion %d" % i)
                break
            i = fin + 2
            continue
        if codigo.startswith("//", i):
            fin = codigo.find("\n", i)
            i = n if fin < 0 else fin + 1
            continue
        if es_digito_ascii(c):
            j = i
            while j < n and es_digito_ascii(codigo[j]):
                j += 1
            if j < n and codigo[j] == "." and j + 1 < n and es_digito_ascii(codigo[j + 1]):
                j += 1
                while j < n and es_digito_ascii(codigo[j]):
                    j += 1
            tokens.append(Token("NUM", codigo[i:j], i))
            i = j
            continue
        if es_letra_ascii(c) or c == "_":
            j = i
            while j < n and (es_letra_ascii(codigo[j]) or es_digito_ascii(codigo[j])
                             or codigo[j] == "_"):
                j += 1
            palabra = codigo[i:j]
            if palabra in RESERVADAS:
                tokens.append(Token("LIT", palabra, i))
            elif palabra[0] == "_":
                errores.append("identificador invalido '%s' en la posicion %d" % (palabra, i))
                tokens.append(Token("ERROR", palabra, i))
            else:
                tokens.append(Token("IDENT", palabra, i))
            i = j
            continue
        if codigo.startswith(DOBLES, i):
            tokens.append(Token("LIT", codigo[i:i + 2], i))
            i += 2
            continue
        if c in SIMPLES:
            tokens.append(Token("LIT", c, i))
            i += 1
            continue
        errores.append("simbolo inesperado '%s' en la posicion %d" % (c, i))
        tokens.append(Token("ERROR", c, i))
        i += 1
    return tokens, errores


def empareja_terminal(terminal, token):
    """True si el terminal de la gramatica casa con el token leido."""
    if terminal == "IDENT":
        return token.clase == "IDENT"
    if terminal == "NUM":
        return token.clase == "NUM"
    return token.clase == "LIT" and token.texto == terminal


# ==========================================================================
# Arbol sintactico
# ==========================================================================

class Nodo(object):
    """Nodo del arbol: no terminal (con produccion) o terminal (hoja).

    El atributo `plan` enlaza el nodo con su equivalente en el arbol de
    analisis; sirve para reconstruir la derivacion por la izquierda.
    """

    def __init__(self, simbolo, es_no_terminal, produccion=None, hijos=None, plan=None,
                 texto=None):
        self.simbolo = simbolo
        self.es_no_terminal = es_no_terminal
        self.produccion = produccion      # identificador de la regla usada
        self.hijos = hijos if hijos is not None else []
        self.plan = plan
        self.texto = texto                # lexema del terminal

    def etiqueta(self):
        if self.es_no_terminal:
            return "<%s>" % self.simbolo
        return self.texto or self.simbolo

    def __repr__(self):
        return "Nodo(%s)" % self.etiqueta()


def produccion_por_id(pid):
    for p in G.PRODUCCIONES:
        if p[0] == pid:
            return p
    raise KeyError(pid)


def analizar(tokens, inicio=None):
    """Analiza la lista de tokens. Devuelve (raiz, error) con raiz None si falla.

    El analisis es descendente recursivo con retroceso completo: cada no
    terminal devuelve todos sus posibles analisis y el llamador elige el
    primero que consume la cadena completa. La gramatica propuesta es no
    ambigua, de modo que ese analisis es unico.
    """
    if inicio is None:
        inicio = G.SIMBOLO_INICIAL
    memo = {}

    def casar_rhs(rhs, pos):
        """Todas las formas de casar rhs a partir de pos. [(fin, hijos), ...]"""
        combos = [(pos, [])]
        for simbolo in rhs:
            nuevos = []
            for fin, hijos in combos:
                if G.es_terminal(simbolo):
                    if fin < len(tokens) and empareja_terminal(simbolo, tokens[fin]):
                        hoja = Nodo(simbolo, False, texto=tokens[fin].texto)
                        nuevos.append((fin + 1, hijos + [hoja]))
                else:
                    for fin2, sub in parsear(simbolo, fin):
                        nuevos.append((fin2, hijos + [sub]))
            combos = nuevos
            if not combos:
                break
        return combos

    def parsear(no_terminal, pos):
        clave = (no_terminal, pos)
        if clave in memo:
            return memo[clave]
        resultados = []
        for pid, _nt, rhs in G.producciones_de(no_terminal):
            for fin, hijos in casar_rhs(rhs, pos):
                resultados.append((fin, Nodo(no_terminal, True, pid, hijos)))
        memo[clave] = resultados
        return resultados

    raiz = parsear(inicio, 0)
    completo = [r for r in raiz if r[0] == len(tokens)]
    if not completo:
        if not raiz:
            return None, "no se pudo derivar la cadena con la gramatica propuesta"
        return None, "sobran %d token(s) sin analizar al final de la cadena" % (
            len(tokens) - max(r[0] for r in raiz))
    return completo[0][1], None


def numero_de_analisis(codigo, inicio=None):
    """Cuenta cuantos analisis completos admite la cadena.

    Un valor 1 demuestra que la gramatica es no ambigua para esa cadena:
    el arbol sintactico es unico.
    """
    tokens, errores = tokenizar(codigo)
    if errores:
        return 0
    if inicio is None:
        inicio = G.SIMBOLO_INICIAL
    memo = {}

    def casar_rhs(rhs, pos):
        combos = [(pos, 1)]
        for simbolo in rhs:
            nuevos = []
            for fin, peso in combos:
                if G.es_terminal(simbolo):
                    if fin < len(tokens) and empareja_terminal(simbolo, tokens[fin]):
                        nuevos.append((fin + 1, peso))
                else:
                    for fin2, sub in parsear(simbolo, fin):
                        nuevos.append((fin2, peso * sub))
            combos = nuevos
            if not combos:
                break
        return combos

    def parsear(no_terminal, pos):
        clave = (no_terminal, pos)
        if clave in memo:
            return memo[clave]
        resultados = []
        for _pid, _nt, rhs in G.producciones_de(no_terminal):
            for fin, peso in casar_rhs(rhs, pos):
                resultados.append((fin, peso))
        memo[clave] = resultados
        return resultados

    completos = [peso for fin, peso in parsear(inicio, 0) if fin == len(tokens)]
    return sum(completos)


def analizar_codigo(codigo, inicio=None):
    """Analiza codigo fuente. Devuelve (raiz, tokens, errores, mensaje_error)."""
    tokens, errores_lexicos = tokenizar(codigo)
    if errores_lexicos:
        return None, tokens, errores_lexicos, "error lexico: " + "; ".join(errores_lexicos)
    raiz, mensaje = analizar(tokens, inicio)
    return raiz, tokens, errores_lexicos, mensaje


# Niveles de reconocimiento: un fragmento puede ser un programa completo, una
# lista de instrucciones o una sola instruccion.
NIVELES = ["programa", "lista_instrucciones", "instruccion"]


def reconocer(codigo):
    """Reconoce el codigo en el nivel mas general posible.

    Devuelve (raiz, tokens, errores_lexicos, mensaje, nivel). Si ninguna
    nivel funciona, raiz es None y nivel es None.
    """
    tokens, errores_lexicos = tokenizar(codigo)
    if errores_lexicos:
        return None, tokens, errores_lexicos, "error lexico: " + "; ".join(errores_lexicos), None
    for nivel in NIVELES:
        raiz, mensaje = analizar(tokens, nivel)
        if raiz is not None:
            return raiz, tokens, errores_lexicos, None, nivel
    return None, tokens, errores_lexicos, "no se pudo derivar la cadena con la gramatica propuesta", None



# ==========================================================================
# Derivacion por la izquierda
# ==========================================================================

def copiar_sin_expandir(nodo):
    """Copia un nodo del analisis dejandolo sin expandir (solo con su regla)."""
    if not nodo.es_no_terminal:
        return Nodo(nodo.simbolo, False, texto=nodo.texto)
    return Nodo(nodo.simbolo, True, nodo.produccion, [], nodo)


def expandir(nodo):
    """Aplica la regla registrada en el nodo: reemplaza el no terminal por
    el lado derecho de su produccion."""
    pid, _nt, rhs = produccion_por_id(nodo.produccion)
    hijos = []
    for j, simbolo in enumerate(rhs):
        if G.es_terminal(simbolo):
            plan = nodo.plan.hijos[j] if nodo.plan is not None else None
            hijos.append(Nodo(simbolo, False, texto=plan.texto if plan is not None else None))
        else:
            plan = nodo.plan.hijos[j] if nodo.plan is not None else None
            hijos.append(copiar_sin_expandir(plan) if plan is not None
                         else Nodo(simbolo, True, None, []))
    nodo.hijos = hijos
    return pid


def forma_frontera(nodo):
    """Forma sentencial: lista de simbolos que aun quedan por expandir."""
    if not nodo.es_no_terminal:
        return [nodo.texto or nodo.simbolo]
    if not nodo.hijos:
        return ["<%s>" % nodo.simbolo]
    forma = []
    for hijo in nodo.hijos:
        forma.extend(forma_frontera(hijo))
    return forma


def primer_no_terminal_pendiente(nodo):
    """Primer no terminal sin expandir de izquierda a derecha."""
    if not nodo.es_no_terminal:
        return None
    if not nodo.hijos:
        return nodo
    for hijo in nodo.hijos:
        encontrado = primer_no_terminal_pendiente(hijo)
        if encontrado is not None:
            return encontrado
    return None


def derivacion_izquierda(raiz):
    """Devuelve la lista de pasos de la derivacion por la izquierda.

    Cada paso es una tupla (forma_anterior, forma_nueva, regla_aplicada).
    En cada paso se expande el no terminal mas a la izquierda de la forma
    sentencial, que es justamente lo que define una derivacion por la
    izquierda.
    """
    arbol = copiar_sin_expandir(raiz)
    pasos = [(" ".join(forma_frontera(arbol)), None, None)]
    while True:
        nodo = primer_no_terminal_pendiente(arbol)
        if nodo is None:
            break
        pid = expandir(nodo)
        pasos.append((pasos[-1][0], " ".join(forma_frontera(arbol)), pid))
    return pasos


def texto_derivacion(raiz):
    """Derivacion por la izquierda en notacion S => ... => w."""
    pasos = derivacion_izquierda(raiz)
    lineas = ["<%s>" % raiz.simbolo]
    for anterior, nuevo, pid in pasos[1:]:
        lineas.append("=> %s   [%s]" % (nuevo, pid))
    return "\n".join(lineas)


# ==========================================================================
# Arbol en SVG
# ==========================================================================

def dibujar_arbol(raiz, titulo=None):
    """Construye el SVG del arbol sintactico.

    Diseno horizontal tipo "arbol，处于 ajustado": cada hoja ocupa una banda
    de ancho suficiente para su etiqueta y cada nodo interno se ubica en el
    punto medio de sus hijos, de modo que las ramas nunca se cruzan.
    """
    ancho_etiqueta = 7.4        # ancho aproximado por caracter
    relleno = 22
    separacion = 42
    alto_nivel = 54
    margen_x = 26
    margen_y = 34

    def etiqueta(nodo):
        return nodo.etiqueta()

    def ancho_texto(texto):
        return len(texto) * ancho_etiqueta + relleno

    def medir(nodo):
        """Ancho del subarbol (post-orden)."""
        if not nodo.es_no_terminal:
            nodo.ancho = ancho_texto(etiqueta(nodo))
            return
        for hijo in nodo.hijos:
            medir(hijo)
        total = sum(h.ancho for h in nodo.hijos) + separacion * (len(nodo.hijos) - 1)
        nodo.ancho = max(total, ancho_texto(etiqueta(nodo)))

    def asignar(nodo, x0):
        """Ubica el subarbol dentro de la misma coordenada horizontal."""
        if not nodo.es_no_terminal:
            nodo.x = x0 + nodo.ancho / 2.0
            return
        cursor = x0
        for hijo in nodo.hijos:
            asignar(hijo, cursor)
            cursor += hijo.ancho + separacion
        nodo.x = (nodo.hijos[0].x + nodo.hijos[-1].x) / 2.0

    def nivel(nodo, prof):
        nodo.profundidad = prof
        if nodo.es_no_terminal:
            for hijo in nodo.hijos:
                nivel(hijo, prof + 1)

    nivel(raiz, 0)
    medir(raiz)
    asignar(raiz, 0.0)

    def extentos(nodo):
        """Extremo izquierdo y derecho ocupados por el subarbol."""
        medio = ancho_texto(etiqueta(nodo)) / 2.0
        if not nodo.es_no_terminal:
            return nodo.x - medio, nodo.x + medio
        izq = der = None
        for hijo in nodo.hijos:
            a, b = extentos(hijo)
            izq = a if izq is None else min(izq, a)
            der = b if der is None else max(der, b)
        return min(izq, nodo.x - medio), max(der, nodo.x + medio)

    izq, der = extentos(raiz)
    ancho = int(der - izq + 2 * margen_x)
    profundidad_max = 0
    pila = [(raiz, 0)]
    while pila:
        nodo, prof = pila.pop()
        profundidad_max = max(profundidad_max, prof)
        if nodo.es_no_terminal:
            for hijo in nodo.hijos:
                pila.append((hijo, prof + 1))
    alto = int(profundidad_max * alto_nivel + 2 * margen_y + (26 if titulo else 0))

    def px(nodo):
        return margen_x + (nodo.x - izq)

    def py(nodo):
        return margen_y + (26 if titulo else 0) + nodo.profundidad * alto_nivel

    partes = []
    partes.append("<?xml version='1.0' encoding='UTF-8'?>")
    partes.append(
        "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d' "
        "viewBox='0 0 %d %d' font-family='DejaVu Sans, sans-serif'>" % (ancho, alto, ancho, alto))
    partes.append("<rect width='100%' height='100%' fill='#ffffff'/>")
    if titulo:
        partes.append(
            "<text x='%d' y='24' text-anchor='middle' font-size='16' font-weight='bold' "
            "fill='#1f3864'>%s</text>" % (ancho // 2, escapar(titulo))
        )

    def recorrer(nodo):
        for hijo in nodo.hijos:
            partes.append(
                "<line x1='%.1f' y1='%.1f' x2='%.1f' y2='%.1f' stroke='#5b6b7c' "
                "stroke-width='1.2'/>" % (px(nodo), py(nodo), px(hijo), py(hijo))
            )
            recorrer(hijo)

    def dibujar_nodo(nodo):
        x = px(nodo)
        y = py(nodo)
        texto = etiqueta(nodo)
        if nodo.es_no_terminal:
            rx = ancho_texto(texto) / 2.0
            partes.append(
                "<ellipse cx='%.1f' cy='%.1f' rx='%.1f' ry='15' fill='#dceaf7' "
                "stroke='#2b5f9e' stroke-width='1.4'/>" % (x, y, rx)
            )
            partes.append(
                "<text x='%.1f' y='%.1f' text-anchor='middle' font-size='13' "
                "fill='#1f3864'>%s</text>" % (x, y + 4, escapar(texto))
            )
        else:
            rx = ancho_texto(texto) / 2.0
            partes.append(
                "<ellipse cx='%.1f' cy='%.1f' rx='%.1f' ry='15' fill='#f3f5f6' "
                "stroke='#7b8794' stroke-width='1.2'/>" % (x, y, rx)
            )
            partes.append(
                "<text x='%.1f' y='%.1f' text-anchor='middle' font-size='13' "
                "fill='#24303f'>%s</text>" % (x, y + 4, escapar(texto))
            )
        for hijo in nodo.hijos:
            dibujar_nodo(hijo)

    recorrer(raiz)
    dibujar_nodo(raiz)
    partes.append("</svg>")
    return "\n".join(partes)


def escapar(texto):
    return (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def arbol_como_texto(nodo, nivel=0):
    """Arbol en forma indentada (util para revisar en consola)."""
    if not nodo.es_no_terminal:
        return "  " * nivel + (nodo.texto or nodo.simbolo)
    lineas = ["  " * nivel + "<%s>" % nodo.simbolo]
    for hijo in nodo.hijos:
        lineas.append(arbol_como_texto(hijo, nivel + 1))
    return "\n".join(lineas)


# ==========================================================================
# Diagnostico deErrores
# ==========================================================================

DIAGNOSTICOS = {
    4: "Falta el operador de asignacion '=' entre el identificador y el valor.",
    5: "El operador '+' aparece sin operando a la izquierda: la expresion aritmetica "
       "exige <operando> <operador> <operando>.",
    6: "La instruccion 'salida' exige un identificador como argumento.",
    7: "Falta el terminador de instruccion '#'.",
}


def diagnosticar(codigo, numero_caso=None):
    """Explica por que una cadena es invalida, cuando se puede precisar."""
    if numero_caso in DIAGNOSTICOS:
        return DIAGNOSTICOS[numero_caso]
    raiz, tokens, errores_lexicos, mensaje, _nivel = reconocer(codigo)
    if raiz is not None:
        return "La cadena es valida."
    if errores_lexicos:
        return "Error lexico: " + "; ".join(errores_lexicos)
    if "sobran" in (mensaje or ""):
        return "Sobran simbolos al final de la cadena: el programa debe terminar con 'End'."
    return "La cadena no es derivable con la gramatica propuesta."


# ==========================================================================
# Comandos
# ==========================================================================

def _veredicto(codigo, numero_caso=None):
    """(veredicto, nivel, diagnostico) para una cadena cualquiera."""
    raiz, _tokens, _err, _msg, nivel = reconocer(codigo)
    if raiz is None:
        return "RECHAZADA", None, diagnosticar(codigo, numero_caso)
    return "ACEPTADA", nivel, ""


def comando_validacion():
    lineas = []
    lineas.append("VALIDACION DE CADENAS CON LA GLC PROPUESTA")
    lineas.append("=" * 78)
    lineas.append("")
    lineas.append("Pregunta 4 - casos del enunciado")
    lineas.append("-" * 78)
    for numero, cadena, _comentario in G.CASOS_P4:
        veredicto, nivel, diagnostico = _veredicto(cadena, numero)
        lineas.append("")
        lineas.append("Caso %d" % numero)
        lineas.append("  Cadena    : %s" % cadena.replace("\n", " / "))
        lineas.append("  Veredicto : %s" % veredicto)
        if nivel:
            lineas.append("  Nivel     : <%s>" % nivel)
        lineas.append("  Analisis  : %s" % (diagnostico if veredicto == "RECHAZADA"
                                           else "La cadena es valida."))
    lineas.append("")
    lineas.append("Pregunta 3.14 - cadenas cuya generacion se debe determinar")
    lineas.append("-" * 78)
    for cadena, _desc in G.CASOS_P3_14:
        veredicto, nivel, _d = _veredicto(cadena)
        lineas.append("  %-24s -> %-10s (nivel <%s>)" % (cadena, veredicto, nivel))
    lineas.append("")
    lineas.append("Extension creativa (opcion B: repeticion)")
    lineas.append("-" * 78)
    for titulo, cadena in (
        ("valida", G.EXTENSION_CADENA_VALIDA),
        ("invalida", G.EXTENSION_CADENA_INVALIDA),
    ):
        veredicto, nivel, diagnostico = _veredicto(cadena)
        lineas.append("  cadena %-9s -> %s" % (titulo, veredicto))
        lineas.append("    %s" % cadena.replace("\n", " / "))
        if veredicto == "RECHAZADA":
            lineas.append("    Motivo: %s" % diagnostico)
    lineas.append("")
    lineas.append("Programa de referencia del enunciado")
    lineas.append("-" * 78)
    raiz, tokens, errores_lexicos, mensaje, nivel = reconocer(G.PROGRAMA_REFERENCIA)
    lineas.append("  Tokens reconocidos : %d" % len(tokens))
    lineas.append("  Veredicto          : %s" % ("ACEPTADO" if raiz is not None else "RECHAZADO"))
    lineas.append("  Nivel              : <%s>" % nivel)
    if raiz is None:
        lineas.append("  Motivo             : %s" % mensaje)
    lineas.append("")
    lineas.append("Cadenas de control adicionales")
    lineas.append("-" * 78)
    extra = [
        "x = 1.345 #",
        "m = k % 10 #",
        "t = k/z#",
        "temporal = x #",
        "y = temporal #",
        "salida z2 #",
        "z = x + y #",
        "z=x-y#",
        "z = x / y #",
        "z = x * y #",
        "z = x + y * z #",
        "Begin Programa p x = 1 # End",
        "Begin Programa p End",
        "x = 20 # y = 30 #",
        "x == 20 #",
        "x = y #",
        "9x = 20 #",
        "x = 20 # #",
        "salida 20 #",
        "SALIDA x #",
        "begin Programa p x = 1 # End",
        "ñ = 1 #",
        "x = ١ #",
        "x = １２ #",
    ]
    for cadena in extra:
        veredicto, nivel, _d = _veredicto(cadena)
        lineas.append("  %-28s -> %s" % (cadena, veredicto))
    return "\n".join(lineas)


def comando_derivacion(cadena, inicio=None):
    if inicio:
        raiz, tokens, errores_lexicos, mensaje = analizar_codigo(cadena, inicio)
        nivel = inicio
    else:
        raiz, tokens, errores_lexicos, mensaje, nivel = reconocer(cadena)
    if raiz is None:
        return "La cadena NO es derivable: %s\n%s" % (mensaje, "; ".join(errores_lexicos))
    partes = []
    partes.append("Tokens: %s" % " ".join(t.texto for t in tokens))
    partes.append("Nivel de reconocimiento: <%s>" % nivel)
    partes.append("")
    partes.append("Derivacion por la izquierda:")
    partes.append(texto_derivacion(raiz))
    partes.append("")
    partes.append("Arbol sintactico:")
    partes.append(arbol_como_texto(raiz))
    return "\n".join(partes)


def comando_arbol(cadena, destino, titulo=None, inicio=None):
    if inicio:
        raiz, _tokens, _err, mensaje = analizar_codigo(cadena, inicio)
    else:
        raiz, _tokens, _err, mensaje, _nivel = reconocer(cadena)
    if raiz is None:
        return "La cadena NO es derivable: %s" % mensaje
    svg = dibujar_arbol(raiz, titulo=titulo or cadena.replace("\n", " "))
    with open(destino, "w", encoding="utf-8") as archivo:
        archivo.write(svg)
    return "Arbol escrito en %s" % destino


def comando_programa():
    raiz, tokens, _err, mensaje, nivel = reconocer(G.PROGRAMA_REFERENCIA)
    if raiz is None:
        return "Programa NO derivable: %s" % mensaje
    partes = []
    partes.append("Programa de referencia: RECONOCIDO (%d tokens, nivel <%s>)" % (len(tokens), nivel))
    partes.append("")
    partes.append("Derivacion por la izquierda:")
    pasos = derivacion_izquierda(raiz)
    for i, (anterior, nuevo, pid) in enumerate(pasos):
        if nuevo is None:
            continue
        partes.append("%2d) %s%s" % (i + 1, nuevo, ("   [%s]" % pid) if pid else ""))
    return "\n".join(partes)


def comando_evidencias(destino):
    """Escribe el registro completo de evidencias del laboratorio."""
    partes = []
    partes.append("EVIDENCIAS DEL LABORATORIO 3 - DISENO Y VALIDACION DE GRAMATICAS")
    partes.append("Generado por herramientas/validar_gramatica.py")
    partes.append("=" * 78)
    partes.append("")
    partes.append("1. GRAMATICA PROPUESTA (producciones P01..P27)")
    partes.append("-" * 78)
    for pid, nt, rhs in G.PRODUCCIONES:
        lado = " ".join(rhs) if rhs else "epsilon"
        partes.append("%s)  <%s> -> %s" % (pid, nt, lado))
    partes.append("")
    partes.append("Simbolo inicial: <%s>" % G.SIMBOLO_INICIAL)
    partes.append("No terminales (%d): %s" % (len(G.NO_TERMINALES_EFECTIVOS),
                  ", ".join("<%s>" % n for n in G.NO_TERMINALES_EFECTIVOS)))
    partes.append("Terminales (%d): %s" % (len(G.TERMINALES), ", ".join(G.TERMINALES)))
    partes.append("")
    partes.append("2. VALIDACION DE LAS 8 CADENAS DE LA PREGUNTA 4")
    partes.append("-" * 78)
    for numero, cadena, _comentario in G.CASOS_P4:
        veredicto, nivel, diagnostico = _veredicto(cadena)
        partes.append("Caso %d" % numero)
        partes.append("  Cadena    : %s" % cadena.replace("\n", " / "))
        partes.append("  Veredicto : %s" % veredicto)
        if nivel:
            partes.append("  Nivel     : <%s>" % nivel)
        if veredicto == "RECHAZADA":
            partes.append("  Analisis  : %s" % diagnostico)
        partes.append("")
    partes.append("2.b NUMERO DE ARBOLES SINTACTICOS DE LOS CASOS PROBADOS")
    partes.append("-" * 78)
    for numero, cadena, _comentario in G.CASOS_P4:
        cuenta = numero_de_analisis(cadena, "instruccion")
        if cuenta == 0:
            cuenta = numero_de_analisis(cadena, "lista_instrucciones")
        if cuenta == 0:
            cuenta = numero_de_analisis(cadena, "programa")
        veredicto = "sin analisis" if cuenta == 0 else (
            "1 (analisis unico para esta cadena)" if cuenta == 1
            else "%d (gramatica ambigua)" % cuenta)
        partes.append("  Caso %d: %-30s -> %s" % (numero, cadena.replace("\n", " / ")[:30], veredicto))
    partes.append("")
    partes.append("3. PREGUNTA 3.14: OTRAS CADENAS A DETERMINAR")
    partes.append("-" * 78)
    for cadena, descripcion in G.CASOS_P3_14:
        veredicto, nivel, _d = _veredicto(cadena)
        partes.append("  %-24s -> %-10s  %s" % (cadena, veredicto, descripcion))
    partes.append("")
    partes.append("4. DERIVACIONES POR LA IZQUIERDA")
    partes.append("-" * 78)
    for cadena, inicio, titulo in (
        ("z = x + y #", "instruccion", "Pregunta 3.10: asignacion con expresion"),
        ("salida z #", "instruccion", "Pregunta 3.11: instruccion de salida"),
        ("mientras x < 10 x = x + 1 # fin_mientras", "instruccion",
         "Extension creativa: lazo"),
    ):
        raiz, tokens, _e, mensaje = analizar_codigo(cadena, inicio)
        partes.append("")
        partes.append("%s" % titulo)
        partes.append("  Cadena: %s" % cadena)
        if raiz is None:
            partes.append("  No derivable: %s" % mensaje)
            continue
        partes.append("  Tokens: %s" % " ".join(t.texto for t in tokens))
        for linea in texto_derivacion(raiz).split("\n"):
            partes.append("  " + linea)
        partes.append("  Arbol sintactico:")
        for linea in arbol_como_texto(raiz).split("\n"):
            partes.append("  " + linea)
    partes.append("")
    partes.append("5. PROGRAMA DE REFERENCIA DEL ENUNCIADO")
    partes.append("-" * 78)
    raiz, tokens, _e, mensaje, nivel = reconocer(G.PROGRAMA_REFERENCIA)
    partes.append("  Codigo:")
    for linea in G.PROGRAMA_REFERENCIA.split("\n"):
        partes.append("    " + linea)
    partes.append("")
    if raiz is None:
        partes.append("  NO derivable: %s" % mensaje)
    else:
        partes.append("  Derivado correctamente. Tokens: %d, nivel <%s>" % (len(tokens), nivel))
        partes.append("  Derivacion por la izquierda (formas sentenciales):")
        for i, (anterior, nuevo, pid) in enumerate(derivacion_izquierda(raiz)):
            if nuevo is None:
                continue
            partes.append("   %2d) %s   [%s]" % (i, nuevo, pid))
    partes.append("")
    partes.append("6. EXTENSION CREATIVA: CADENA VALIDA E INVALIDA")
    partes.append("-" * 78)
    for titulo, cadena in (("valida", G.EXTENSION_CADENA_VALIDA),
                           ("invalida", G.EXTENSION_CADENA_INVALIDA)):
        veredicto, nivel, diagnostico = _veredicto(cadena)
        partes.append("  Cadena %s (%s, nivel <%s>):" % (titulo, veredicto, nivel))
        for linea in cadena.split("\n"):
            partes.append("    " + linea)
        if veredicto == "RECHAZADA":
            partes.append("    Motivo: %s" % diagnostico)
        partes.append("")
    partes.append("7. CADENAS DE CONTROL")
    partes.append("-" * 78)
    extra = [
        "x = 1.345 #", "m = k % 10 #", "t = k/z#", "temporal = x #", "y = temporal #",
        "salida z2 #", "z = x + y #", "z=x-y#", "z = x / y #", "z = x * y #",
        "z = x + y * z #", "Begin Programa p x = 1 # End", "Begin Programa p End",
        "x = 20 # y = 30 #", "x == 20 #", "x = y #", "9x = 20 #", "x = 20 # #",
        "salida 20 #", "SALIDA x #", "begin Programa p x = 1 # End",
        "ñ = 1 #", "x = ١ #", "x = １２ #",
    ]
    for cadena in extra:
        veredicto, _nivel, _d = _veredicto(cadena)
        partes.append("  %-30s -> %s" % (cadena, veredicto))
    texto = "\n".join(partes) + "\n"
    with open(destino, "w", encoding="utf-8") as archivo:
        archivo.write(texto)
    return "Evidencias escritas en %s (%d lineas)" % (destino, len(partes))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    comando = sys.argv[1]
    if comando == "validacion":
        print(comando_validacion())
    elif comando == "derivacion":
        if len(sys.argv) < 3:
            print("Falta la cadena a derivar.")
            return 1
        inicio = sys.argv[3] if len(sys.argv) > 3 else None
        print(comando_derivacion(sys.argv[2], inicio))
    elif comando == "arbol":
        if len(sys.argv) < 4:
            print("Uso: validar_gramatica.py arbol <cadena> <archivo.svg> [simbolo_inicial]")
            return 1
        inicio = sys.argv[4] if len(sys.argv) > 4 else None
        print(comando_arbol(sys.argv[2], sys.argv[3], inicio=inicio))
    elif comando == "programa":
        print(comando_programa())
    elif comando == "evidencias":
        destino = sys.argv[2] if len(sys.argv) > 2 else "evidencias.txt"
        print(comando_evidencias(destino))
    else:
        print("Comando desconocido: %s" % comando)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
