#!/usr/bin/env python3
"""
Genera el archivo de gramatica para JFLAP 7.1 (`gramatica/GLC_Lab03.cfg`).

JFLAP guarda las gramaticas en XML. Cada produccion es un elemento
<production> con el lado izquierdo en <left> y el lado derecho en <right>.
Su analizador recorre el lado derecho caracter por caracter: las letras
mayusculas son variables y cualquier otro caracter es un terminal. Por eso
cada simbolo de la gramatica se codifica con exactamente un caracter
(seccion "Codificacion isomorfa para JFLAP 7.1" de `gramatica_lab3.py`).
El mapeo no cambia el lenguaje: solo adapta la ortografia que JFLAP puede
leer. El informe conserva los nombres legibles y explica la equivalencia.

La salida se genera desde `gramatica_lab3.py`, de modo que el archivo de
JFLAP y el informe describen exactamente la misma gramatica.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gramatica_lab3 as G  # noqa: E402


def escapar(texto):
    return (texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def generar_cfg():
    lineas = []
    lineas.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    lineas.append("<!-- Generated for JFLAP 7.1 from gramatica_lab3.py. -->")
    lineas.append("<structure>")
    lineas.append("  <type>grammar</type>")
    lineas.append("  <!-- The list of productions. -->")
    for pid, nt, rhs in G.PRODUCCIONES:
        lineas.append("  <production>")
        lineas.append("    <left>%s</left>" % escapar(G.codificar_jflap(nt)))
        lineas.append("    <right>%s</right>" % escapar(G.codificar_rhs_jflap(rhs)))
        lineas.append("  </production>")
    lineas.append("</structure>")
    return "\n".join(lineas) + "\n"


def generar_txt():
    """Definicion formal legible de G = (V, Sigma, P, S)."""
    lineas = []
    lineas.append("GRAMATICA LIBRE DE CONTEXTO DEL LENGUAJE DE PROGRAMACION SIMPLIFICADO")
    lineas.append("Laboratorio 3 - Diseno y Validacion de Gramaticas")
    lineas.append("=" * 78)
    lineas.append("")
    lineas.append("G = (V, Sigma, P, S)")
    lineas.append("")
    lineas.append("SIMBOLO INICIAL")
    lineas.append("  S = <%s>   (codigo JFLAP: %s)" % (
        G.SIMBOLO_INICIAL, G.JFLAP_SIMBOLO_INICIAL))
    lineas.append("")
    lineas.append("NO TERMINALES (V), |V| = %d" % len(G.NO_TERMINALES_EFECTIVOS))
    for nombre, funcion in G.NO_TERMINALES:
        lineas.append("  <%s>" % nombre)
        lineas.append("      %s" % funcion)
    lineas.append("")
    lineas.append("TERMINALES (Sigma), |Sigma| = %d" % len(G.TERMINALES))
    lineas.append("  Palabras reservadas      : %s" % ", ".join(G.PALABRAS_RESERVADAS))
    lineas.append("  Extension (reservadas)   : %s" % ", ".join(G.EXTENSION_PALABRAS_RESERVADAS))
    lineas.append("  Operadores aritmeticos   : %s" % " ".join(G.OPERADORES_ARITMETICOS))
    lineas.append("  Operador de asignacion   : %s" % G.OPERADOR_ASIGNACION)
    lineas.append("  Operadores relacionales  : %s" % " ".join(G.OPERADORES_RELACIONALES))
    lineas.append("  Simbolos especiales      : %s" % " ".join(G.SIMBOLOS_ESPECIALES))
    lineas.append("  Clases lexicas           : %s" % ", ".join(sorted(G.CLASES_LEXICAS)))
    for clase, forma in G.CLASES_LEXICAS.items():
        lineas.append("      %-6s : %s" % (clase, forma))
    lineas.append("  Identificadores (ER)      : %s" % G.IDENTIFICADORES_RE)
    lineas.append("  Numeros (ER)              : %s" % G.NUMEROS_RE)
    lineas.append("")
    lineas.append("CODIFICACION ISOMORFA PARA JFLAP 7.1")
    lineas.append("-" * 78)
    lineas.append("  JFLAP lee cada caracter del lado derecho: mayusculas = variables,")
    lineas.append("  cualquier otro caracter = terminal. Para que el .cfg represente")
    lineas.append("  esta misma gramatica, cada simbolo se codifica con un caracter.")
    lineas.append("")
    lineas.append("  No terminales (14):")
    for nombre in G.NO_TERMINALES_EFECTIVOS:
        lineas.append("    %-24s -> %s" % ("<%s>" % nombre, G.JFLAP_VARIABLES[nombre]))
    lineas.append("")
    lineas.append("  Terminales (19):")
    for terminal in G.TERMINALES:
        lineas.append("    %-24s -> %s" % (terminal, G.JFLAP_TERMINALES[terminal]))
    lineas.append("")
    lineas.append("  Cadenas de evidencia para las capturas:")
    for nombre, inicio, cadena, legible in G.JFLAP_EJEMPLOS:
        lineas.append("    %-18s inicio <%s>  %-18s  %s" % (
            nombre, inicio, cadena, legible))
    lineas.append("")
    lineas.append("PRODUCCIONES (P), |P| = %d" % len(G.PRODUCCIONES))
    for pid, nt, rhs in G.PRODUCCIONES:
        lado = " ".join(rhs) if rhs else "epsilon"
        lineas.append("  %s)  <%s> -> %s" % (pid, nt, lado))
    lineas.append("")
    lineas.append("Nota: GLC_Lab03.cfg usa la codificacion de un caracter por simbolo")
    lineas.append("descrita arriba. Al cargarlo, JFLAP 7.1 reporta 14 variables, 19")
    lineas.append("terminales, 27 producciones y S como simbolo inicial. El lenguaje")
    lineas.append("generado es el mismo; solo cambia la ortografia interna de JFLAP.")
    return "\n".join(lineas) + "\n"


def generar_equivalencias():
    lineas = ["CODIFICACION BIYECTIVA PARA JFLAP 7.1", "=" * 78,
              "Cada caracter representa un simbolo completo. No se escriben espacios.",
              "IDENT y NUM representan clases lexicas, no lexemas concretos.", "",
              "NO TERMINALES"]
    for nombre, _ in G.NO_TERMINALES:
        lineas.append("  %s = <%s>" % (G.CODIGOS_JFLAP[nombre], nombre))
    lineas.append("\nTERMINALES")
    for simbolo in G.TERMINALES:
        lineas.append("  %s = %s" % (G.CODIGOS_JFLAP[simbolo], simbolo))
    lineas.append("\nPRODUCCIONES (misma numeracion del informe)")
    for pid, nt, rhs in G.PRODUCCIONES:
        lineas.append("  %s) %s -> %s" % (pid, G.CODIGOS_JFLAP[nt],
                      "".join(G.CODIGOS_JFLAP[s] for s in rhs)))
    lineas.append("\nEjemplos: z = x + y # -> i=i+i#; salida z # -> si#.")
    lineas.append("Para instrucciones sueltas seleccionar I como inicio; para programas, S.")
    return "\n".join(lineas) + "\n"


def generar_casos():
    from validar_gramatica import tokenizar

    casos = [("P4-%d" % n, "S" if n == 8 else "I", n in (1, 2, 3, 8), codigo)
             for n, codigo, _ in G.CASOS_P4]
    casos += [("P3-%d" % n, "I", True, codigo)
              for n, (codigo, _) in enumerate(G.CASOS_P3_14, 1)]
    casos += [("extension-valida", "S", True, G.EXTENSION_CADENA_VALIDA),
              ("extension-invalida", "S", False, G.EXTENSION_CADENA_INVALIDA),
              ("referencia", "S", True, G.PROGRAMA_REFERENCIA)]
    lineas = ["# caso\tinicio\tesperado\tcadena_codificada"]
    for nombre, inicio, valido, codigo in casos:
        tokens, errores = tokenizar(codigo)
        if errores:
            raise ValueError(errores)
        cadena = "".join(G.CODIGOS_JFLAP[t.clase if t.clase in G.CLASES_LEXICAS else t.texto]
                         for t in tokens)
        lineas.append("\t".join((nombre, inicio, "ACEPTADA" if valido else "RECHAZADA", cadena)))
    return "\n".join(lineas) + "\n"



def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "gramatica")
    destino_cfg = os.path.join(base, "GLC_Lab03.cfg")
    destino_txt = os.path.join(base, "GLC_Lab03.txt")
    with open(destino_cfg, "w", encoding="utf-8") as archivo:
        archivo.write(generar_cfg())
    with open(destino_txt, "w", encoding="utf-8") as archivo:
        archivo.write(generar_txt())
    print("Archivo de JFLAP escrito en %s (%d producciones, %d variables, %d terminales)" % (
        destino_cfg, len(G.PRODUCCIONES), len(G.JFLAP_VARIABLES), len(G.JFLAP_TERMINALES)))
    for nombre, contenido in (("equivalencias_jflap.txt", generar_equivalencias()), ("casos_jflap.tsv", generar_casos())):
        with open(os.path.join(base, nombre), "w", encoding="utf-8") as archivo:
            archivo.write(contenido)
    print("Definicion formal escrita en %s" % destino_txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
