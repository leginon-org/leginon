/*
 * Swing version of NodeGUI.
 */

import org.apache.xmlrpc.*;
import java.util.Hashtable;
import java.util.Vector;
import java.awt.*;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.awt.event.ItemListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import javax.swing.*;


public class guilaunch extends JFrame {
    private XmlRpcClient client;
    private String cmd,url;
    private Hashtable hash_name = new Hashtable();
    private JDesktopPane dtp = new JDesktopPane();
    private GuiJIFContainer gc= null;
    private JPanel  controlPanel = new JPanel();
    private Container contentPane;


    public guilaunch() throws Exception {
		display();
		addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent e) {
				dispose();
            		}
        	});

    }

    private void display() throws Exception {
        contentPane = getContentPane();
	GUILauncher l = new GUILauncher();
        contentPane.setLayout(new BorderLayout());
        contentPane.add(l);
    }
}
