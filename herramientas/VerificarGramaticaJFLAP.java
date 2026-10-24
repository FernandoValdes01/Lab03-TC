import grammar.Grammar;
import grammar.Production;
import file.XMLCodec;

import java.io.File;
import java.util.HashMap;
import java.util.Map;

/**
 * Verificador del archivo de gramatica de JFLAP 7.1.
 *
 * Carga `GLC_Lab03.cfg` con el propio codificador XML de JFLAP 7.1 y
 * comprueba que la herramienta lo lea con la codificacion isomorfa de la
 * gramatica: 14 variables, 19 terminales, 27 producciones, simbolo inicial
 * `S` y todos los simbolos de un solo caracter.
 *
 * Uso:
 *   java -cp JFLAP7.1-fixed.jar:. VerificarGramaticaJFLAP gramatica/GLC_Lab03.cfg
 */
public class VerificarGramaticaJFLAP {

    public static void main(String[] args) throws Exception {
        File archivo = new File(args.length > 0 ? args[0] : "gramatica/GLC_Lab03.cfg");
        System.out.println("Archivo        : " + archivo.getPath());
        System.out.println("Java           : " + System.getProperty("java.version"));

        XMLCodec codec = new XMLCodec();
        Map<String, Object> opciones = new HashMap<String, Object>();
        Grammar g = (Grammar) codec.decode(archivo, opciones);

        String[] variables = g.getVariables();
        String[] terminales = g.getTerminals();
        Production[] producciones = g.getProductions();

        System.out.println("Tipo de objeto : " + g.getClass().getName());
        System.out.println("Simbolo inicial: " + g.getStartVariable());
        System.out.println("No terminales  : " + variables.length);
        System.out.println("Terminales     : " + terminales.length);
        System.out.println("Producciones   : " + producciones.length);
        System.out.println("");
        System.out.println("Producciones leidas por JFLAP:");
        for (Production p : producciones) {
            System.out.println("  " + p.getLHS() + " -> " + p.getRHS());
        }

        boolean ok = g.getStartVariable().equals("S")
                && variables.length == 14
                && terminales.length == 19
                && producciones.length == 27;
        for (String v : variables) {
            ok = ok && v.length() == 1;
        }
        for (String t : terminales) {
            ok = ok && t.length() == 1;
        }
        for (Production p : producciones) {
            ok = ok && p.getLHS().length() == 1 && p.getRHS().length() > 0;
        }

        System.out.println("");
        if (ok) {
            System.out.println("RESULTADO: el archivo fue aceptado por JFLAP 7.1 y cumple");
            System.out.println("           14 variables, 19 terminales, 27 producciones,");
            System.out.println("           simbolo inicial S y simbolos de un caracter.");
        } else {
            System.out.println("RESULTADO: el archivo fue leido, pero NO cumple la codificacion");
            System.out.println("           esperada (14/19/27, inicio S, simbolos de un caracter).");
            System.exit(1);
        }
    }
}
