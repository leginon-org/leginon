/*
 * Applet version of NodeGUI.
 */

import java.awt.*;
import javax.swing.*;

public class nodeapplet extends JApplet {
    private Container contentPane;

    public void start() {
	try {
		display();
	} catch (Exception e) {
		System.err.println("Exception Error: "+e);
	}
    }

    private void display() throws Exception {
        contentPane = getContentPane();
        contentPane.setLayout(new BorderLayout());
        contentPane.add(new GUILauncher());
    }

}
