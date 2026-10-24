import grammar.Grammar;
import file.XMLCodec;
import gui.environment.GrammarEnvironment;
import gui.grammar.GrammarInputPane;
import gui.grammar.parse.BruteParsePane;

import javax.imageio.ImageIO;
import javax.swing.JFrame;
import javax.swing.SwingUtilities;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;

/**
 * Genera una captura PNG del arbol de derivacion de JFLAP 7.1.
 *
 * La gramatica se carga desde `GLC_Lab03.cfg`. El segundo argumento es la
 * cadena codificada (por ejemplo `i=i+i#`); el cuarto, opcional, es el no
 * terminal desde el que se inicia la derivacion (`I` para una instruccion,
 * `M` para el lazo). El quinto argumento es el titulo de la ventana.
 *
 * Uso:
 *   java -cp JFLAP7.1-fixed.jar:herramientas CapturarArbolJFLAP \
 *        gramatica/GLC_Lab03.cfg "i=i+i#" figuras/jflap_arbol_z_xy.png I \
 *        "JFLAP 7.1 - z = x + y #"
 *
 * Requiere una sesion grafica (DISPLAY). En Linux sin escritorio se puede
 * usar Xvfb o el X server disponible. El programa no modifica la gramatica:
 * solo fija el simbolo inicial de la vista para reproducir la derivacion.
 */
public class CapturarArbolJFLAP {

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Uso: CapturarArbolJFLAP <gramatica.cfg> <cadena> <salida.png> [inicio] [titulo]");
            System.exit(2);
        }

        System.setProperty("sun.java2d.uiScale", "1");
        final File archivoGramatica = new File(args[0]);
        final String cadena = args[1];
        final File salida = new File(args[2]);
        final String inicio = args.length > 3 && !args[3].isEmpty() ? args[3] : null;
        final String titulo = args.length > 4 ? args[4] : "JFLAP 7.1 - Arbol de derivacion";

        XMLCodec codec = new XMLCodec();
        Map<String, Object> opciones = new HashMap<String, Object>();
        final Grammar gramatica = (Grammar) codec.decode(archivoGramatica, opciones);
        if (inicio != null) {
            gramatica.setStartVariable(inicio);
        }

        System.out.println("Gramatica      : " + archivoGramatica.getAbsolutePath());
        System.out.println("Simbolo inicial: " + gramatica.getStartVariable());
        System.out.println("No terminales  : " + gramatica.getVariables().length);
        System.out.println("Terminales     : " + gramatica.getTerminals().length);
        System.out.println("Producciones   : " + gramatica.getProductions().length);
        System.out.println("Cadena         : " + cadena);

        final JFrame[] ventana = new JFrame[1];
        final BruteParsePane[] panel = new BruteParsePane[1];
        SwingUtilities.invokeAndWait(() -> {
            GrammarInputPane entrada = new GrammarInputPane(gramatica);
            GrammarEnvironment entorno = new GrammarEnvironment(entrada);
            BruteParsePane parsePane = new BruteParsePane(entorno, gramatica, null);
            JFrame frame = new JFrame(titulo);
            frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
            frame.setContentPane(parsePane);
            frame.setSize(1500, 950);
            frame.setLocation(0, 0);
            frame.setVisible(true);
            frame.validate();
            parsePane.input(cadena);
            ventana[0] = frame;
            panel[0] = parsePane;
        });

        Field campoParser = BruteParsePane.class.getDeclaredField("parser");
        campoParser.setAccessible(true);
        Object parser = null;
        for (int i = 0; i < 1200; i++) {
            Thread.sleep(50);
            parser = campoParser.get(panel[0]);
            if (parser != null) {
                Method terminado = parser.getClass().getMethod("isFinished");
                if ((Boolean) terminado.invoke(parser)) {
                    break;
                }
            }
        }
        if (parser == null) {
            System.err.println("JFLAP no creo el parser.");
            System.exit(1);
        }

        Method obtenerRespuesta = parser.getClass().getMethod("getAnswer");
        Object respuesta = obtenerRespuesta.invoke(parser);
        if (respuesta == null) {
            System.err.println("La cadena fue rechazada por la gramatica.");
            SwingUtilities.invokeAndWait(() -> ventana[0].dispose());
            System.exit(1);
        }

        final int[] pasos = new int[1];
        SwingUtilities.invokeAndWait(() -> {
            int n = 0;
            try {
                while (!panel[0].step() && n < 500) {
                    n++;
                }
            } catch (RuntimeException ex) {
                System.err.println("No se pudo completar la derivacion: " + ex.getMessage());
            }
            pasos[0] = n;
            panel[0].repaint();
        });
        System.out.println("Pasos           : " + pasos[0]);
        Thread.sleep(500);

        SwingUtilities.invokeAndWait(() -> {
            try {
                JFrame frame = ventana[0];
                BufferedImage imagen = new BufferedImage(
                        frame.getWidth(), frame.getHeight(), BufferedImage.TYPE_INT_RGB);
                Graphics2D g2 = imagen.createGraphics();
                frame.paintAll(g2);
                g2.dispose();
                ImageIO.write(imagen, "png", salida);
                System.out.println("Captura         : " + salida.getAbsolutePath()
                        + " (" + imagen.getWidth() + "x" + imagen.getHeight() + ")");
                frame.dispose();
            } catch (Exception ex) {
                ex.printStackTrace();
            }
        });
        System.exit(0);
    }
}
