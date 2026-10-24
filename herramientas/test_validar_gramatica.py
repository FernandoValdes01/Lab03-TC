"""Regresiones del reconocimiento léxico y de los casos del enunciado."""

import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

import gramatica_lab3 as G
import validar_gramatica as V


class ValidacionTest(unittest.TestCase):
    def test_comentario_sin_cerrar_se_rechaza_en_todas_las_entradas(self):
        codigo = "x = 20 # /* sin cierre"
        self.assertIsNone(V.reconocer(codigo)[0])
        self.assertIsNone(V.analizar_codigo(codigo, "instruccion")[0])
        self.assertEqual(V.numero_de_analisis(codigo, "instruccion"), 0)
        self.assertEqual(V._veredicto(codigo)[0], "RECHAZADA")

    def test_clases_lexicas_respetan_las_expresiones_regulares(self):
        for codigo in ("x = ² #", "x = ١٠ #", "ñ = 1 #", "xñ = 1 #", "_x = 1 #"):
            with self.subTest(codigo=codigo):
                self.assertIsNone(V.reconocer(codigo)[0])

    def test_comentario_cerrado_y_clases_validas(self):
        for codigo in ("x = 20 # /* cerrado */", "z2 = 1.345 #", "temporal_01 = 0 #"):
            with self.subTest(codigo=codigo):
                self.assertIsNotNone(V.reconocer(codigo)[0])

    def test_casos_del_enunciado(self):
        for numero, codigo, _ in G.CASOS_P4:
            with self.subTest(caso=numero):
                self.assertEqual(V.reconocer(codigo)[0] is not None, numero in (1, 2, 3, 8))
        self.assertIsNotNone(V.analizar_codigo(G.PROGRAMA_REFERENCIA)[0])
        self.assertIsNotNone(V.analizar_codigo(G.EXTENSION_CADENA_VALIDA)[0])
        self.assertIsNone(V.analizar_codigo(G.EXTENSION_CADENA_INVALIDA)[0])

    def test_lazos_anidados_y_operadores_relacionales(self):
        codigo = ("Begin Programa p mientras x < 10 mientras y >= 0 "
                  "salida y # fin_mientras x = x + 1 # fin_mientras End")
        self.assertIsNotNone(V.analizar_codigo(codigo)[0])
        self.assertIsNone(V.analizar_codigo(codigo.replace("fin_mientras", "", 1))[0])

    def test_xml_conserva_la_gramatica_bajo_una_biyeccion(self):
        codigos = G.CODIGOS_JFLAP
        self.assertEqual(len(set(codigos.values())), 33)
        self.assertTrue(all(len(c) == 1 for c in codigos.values()))
        self.assertTrue(all(codigos[n].isupper() for n in G.NO_TERMINALES_EFECTIVOS))
        self.assertTrue(all(not codigos[t].isupper() for t in G.TERMINALES))
        inversa = {codigo: simbolo for simbolo, codigo in codigos.items()}
        archivo = Path(__file__).resolve().parents[1] / "gramatica" / "GLC_Lab03.cfg"
        xml = ET.parse(archivo).getroot()
        reglas = [(inversa[p.findtext("left")], [inversa[c] for c in p.findtext("right")])
                  for p in xml.findall("production")]
        self.assertEqual(reglas, [(nt, rhs) for _, nt, rhs in G.PRODUCCIONES])
        self.assertEqual(codigos[G.SIMBOLO_INICIAL], "S")


if __name__ == "__main__":
    unittest.main()
