/*
 * Applet version of NodeGUI.
 */

//
// COPYRIGHT:
//       The Leginon software is Copyright 2003
//       The Scripps Research Institute, La Jolla, CA
//       For terms of the license agreement
//       see  http://ami.scripps.edu/software/leginon-license
//
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
