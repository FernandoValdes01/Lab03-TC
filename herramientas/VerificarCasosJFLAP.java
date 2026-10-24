import file.XMLCodec;
import grammar.CNFConverter;
import grammar.Grammar;
import grammar.Production;
import grammar.UnitProductionRemover;
import grammar.UnrestrictedGrammar;
import grammar.parse.CYKParser;
import gui.grammar.GrammarTable;
import gui.grammar.ImmutableGrammarTableModel;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.imageio.ImageIO;
import javax.swing.JPanel;
import javax.swing.SwingUtilities;

/** Lee el XML y valida los casos usando las clases de JFLAP 7.1. */
public class VerificarCasosJFLAP {
    private static Grammar normalizar(Grammar original, String inicio) {
        UnitProductionRemover unidades = new UnitProductionRemover();
        Grammar sinUnidades = unidades.getUnitProductionlessGrammar(
            original, unidades.getVariableDependencyGraph(original));
        // El removedor de JFLAP no conserva el inicio del objeto original.
        sinUnidades.setStartVariable(inicio);
        CNFConverter conversor = new CNFConverter(sinUnidades);
        LinkedList<Production> pendientes = new LinkedList<>(
            Arrays.asList(sinUnidades.getProductions()));
        Set<Production> visitadas = new HashSet<>();
        List<Production> reglas = new ArrayList<>();
        while (!pendientes.isEmpty()) {
            Production regla = pendientes.removeFirst();
            if (!visitadas.add(regla)) continue;
            if (conversor.isChomsky(regla)) reglas.add(regla);
            else pendientes.addAll(Arrays.asList(conversor.replacements(regla)));
        }
        // Los auxiliares de CNFConverter tienen nombres de varios caracteres.
        Grammar cnf = new UnrestrictedGrammar();
        cnf.addProductions(reglas.toArray(new Production[0]));
        cnf.setStartVariable(inicio);
        return cnf;
    }

    private static void capturarTabla(Grammar gramatica, File destino) throws Exception {
        SwingUtilities.invokeAndWait(() -> {
            try {
                GrammarTable tabla = new GrammarTable(new ImmutableGrammarTableModel(gramatica));
                tabla.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 19));
                tabla.setRowHeight(30);
                tabla.getTableHeader().setFont(new Font(Font.SANS_SERIF, Font.BOLD, 18));
                tabla.getTableHeader().setPreferredSize(new java.awt.Dimension(760, 32));
                tabla.getColumnModel().getColumn(0).setPreferredWidth(180);
                tabla.getColumnModel().getColumn(1).setPreferredWidth(65);
                tabla.getColumnModel().getColumn(2).setPreferredWidth(515);
                JPanel panel = new JPanel(new BorderLayout());
                panel.setBackground(Color.WHITE);
                panel.add(tabla.getTableHeader(), BorderLayout.NORTH);
                panel.add(tabla, BorderLayout.CENTER);
                panel.setSize(760, 32 + tabla.getRowCount() * 30);
                panel.doLayout();
                tabla.doLayout();
                BufferedImage imagen = new BufferedImage(760, panel.getHeight(), BufferedImage.TYPE_INT_RGB);
                Graphics2D graficos = imagen.createGraphics();
                panel.printAll(graficos);
                graficos.dispose();
                ImageIO.write(imagen, "png", destino);
            } catch (Exception error) {
                throw new RuntimeException(error);
            }
        });
    }

    private static String sha256(File archivo) throws Exception {
        byte[] bytes = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(archivo.toPath()));
        StringBuilder texto = new StringBuilder();
        for (byte b : bytes) texto.append(String.format("%02x", b & 255));
        return texto.toString();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            throw new IllegalArgumentException("Uso: VerificarCasosJFLAP archivo.cfg casos.tsv captura.png");
        }
        File archivo = new File(args[0]);
        File biblioteca = new File(Grammar.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Grammar g = (Grammar) new XMLCodec().decode(archivo, new HashMap<String, Object>());
        System.out.println("Archivo        : " + archivo.getName());
        System.out.println("Biblioteca     : " + biblioteca.getName());
        System.out.println("SHA-256 JAR    : " + sha256(biblioteca));
        System.out.println("Java           : " + System.getProperty("java.version"));
        System.out.println("Simbolo inicial: " + g.getStartVariable() + " = <programa>");
        System.out.println("No terminales  : " + g.getVariables().length);
        System.out.println("Terminales     : " + g.getTerminals().length);
        System.out.println("Producciones   : " + g.getProductions().length);
        if (!"S".equals(g.getStartVariable()) || g.getVariables().length != 14
                || g.getTerminals().length != 19 || g.getProductions().length != 27) {
            throw new IllegalStateException("La gramatica cargada no coincide con la especificacion.");
        }
        System.out.println("\nProducciones leidas por JFLAP (ver equivalencias_jflap.txt):");
        for (Production p : g.getProductions()) {
            System.out.println("  " + p.getLHS() + " -> " + p.getRHS());
        }
        System.out.println("\nValidacion con UnitProductionRemover, CNFConverter y CYKParser de JFLAP:");
        Map<String, Grammar> normalizadas = new HashMap<>();
        int comprobaciones = 0;
        for (String linea : Files.readAllLines(new File(args[1]).toPath(), StandardCharsets.UTF_8)) {
            if (linea.isEmpty() || linea.startsWith("#")) continue;
            String[] campos = linea.split("\t", -1);
            if (campos.length != 4) throw new IllegalArgumentException("Caso mal formado: " + linea);
            String inicio = campos[1];
            if (!normalizadas.containsKey(inicio)) normalizadas.put(inicio, normalizar(g, inicio));
            boolean aceptada = new CYKParser(normalizadas.get(inicio)).solve(campos[3]);
            String resultado = aceptada ? "ACEPTADA" : "RECHAZADA";
            System.out.printf("  %-20s inicio=%s  %-9s  %s%n", campos[0], inicio, resultado, campos[3]);
            if (!resultado.equals(campos[2])) throw new IllegalStateException("Resultado incorrecto: " + campos[0]);
            comprobaciones++;
        }
        capturarTabla(g, new File(args[2]));
        System.out.println("\nCaptura        : " + new File(args[2]).getName());
        System.out.println("Origen captura : componente GrammarTable de JFLAP, renderizado sin escritorio.");
        System.out.println("RESULTADO: " + comprobaciones + " casos correctos; inicio y alfabetos verificados.");
    }
}
