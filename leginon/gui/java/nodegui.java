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


public class nodegui extends JFrame {
    private XmlRpcClient client;
    private String cmd,url;
    private Hashtable hash_name = new Hashtable();
    private NodeDesktop nd = new NodeDesktop();
    private JDesktopPane dtp = nd.getDesktopPane();
    private GuiJIFContainer gc= null;
    private JPanel  controlPanel = new JPanel();
    private Container contentPane;

    
    public nodegui(String url) throws Exception {
		this.url=url;
		addControl();
		display();
		addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent e) {
           			dispose();
            		}
        	});

    }

    private void addControl() throws Exception {
                JButton b = new JButton("Refresh");
                controlPanel.add(b);

                b.addActionListener(new ActionListener() {
                        public void actionPerformed(ActionEvent event) {
				try {
				refresh();
				display();
				} catch (Exception e) {
					System.err.println("Exception Error: "+e);
				}
			}
		});
    }

    private void getSpec() throws Exception {
	client = new XmlRpcClient (url);
	Object result = new Object();
	result = client.execute("spec", new Vector());
	Hashtable spec = (Hashtable)result;
//	System.out.println("Spec"+spec);
	gc = new GuiJIFContainer(client, spec, nd);
	super.setTitle(url+":: Interface to "+gc.getSpectype()+":"+gc.getName());
    }

    private void display() throws Exception {
	setJMenuBar(nd.createMenuBar());
	getSpec();
        contentPane = getContentPane();
        contentPane.setLayout(new BorderLayout());
        contentPane.add(controlPanel, BorderLayout.NORTH);
        contentPane.add(dtp, BorderLayout.CENTER);
    }

    private void refresh() {
	dtp.removeAll();
	dtp.repaint();
    }

    public static void main (String args[]) throws Exception {
	if (args.length < 1) {
        guilaunch gl = new guilaunch();
	gl.setBounds(100,100,800,500);
	gl.show();
	} else {
        nodegui window = new nodegui(args[0]);

	window.setBounds(100,100,800,500);
        window.show();
	}
    }

}
