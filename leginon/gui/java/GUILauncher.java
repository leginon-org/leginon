				
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import java.net.*;

public class GUILauncher extends JPanel {

	public final int DEFAULTPORTNUMBER = 49153;
	public final String DEFAULTHOST = "stratocaster";

	public GUILauncher() throws Exception {
		initcomponents();
	}

	public JButton bt_cmd;

	private int portnumber = DEFAULTPORTNUMBER;
	private String host = DEFAULTHOST;

	private int width = 800;
	private int height = 500;
	private int nw_count=1;

	private JComboBox comboBox = new JComboBox();
	private ComboBoxEditor editor = comboBox.getEditor();
	private JTextField jText;


	private String getLocalhost() throws UnknownHostException {
		InetAddress addr = InetAddress.getLocalHost();
	        // Get IP Address
	        byte[] ipAddr = addr.getAddress();
    
	        // Get hostname
	        String hostname = addr.getHostName();
		return hostname;
	}


	private void initcomponents() throws Exception  {
		JPanel panel = new JPanel();
		jText = new JTextField(""+portnumber, 6);
		jText.setPreferredSize(new Dimension(60,24));
        	bt_cmd  = new JButton("Launch GUI");
		bt_cmd.setPreferredSize(new Dimension(120,24));
		bt_cmd.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {	
					portnumber = Integer.parseInt(jText.getText());
					host = (String)comboBox.getSelectedItem();
					comboBox.addItem(host);
					System.out.println("http://"+host+":"+portnumber);
        				nodegui newWindow = new nodegui("http://"+host+":"+portnumber);
					newWindow.setBounds(20*(nw_count%10), 20*(nw_count%10), width, height);
					newWindow.setVisible(true);
					nw_count++;
				} catch (Exception ex) {}
			}
		});

		comboBox.setEditable(true);
		try {
			host = getLocalhost();
		} catch (UnknownHostException e) { }

		comboBox.addItem(host);

        	panel.add(bt_cmd);
		panel.add(comboBox);
        	panel.add(jText);
		addPortButton(panel);
		add(panel);

		editor.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				host = (String)editor.getItem();
				comboBox.addItem(host);
				comboBox.setSelectedItem(host);
				
			}
		});
        }

	private void addPortButton(JPanel panel) {
	        JButton button = null;

		button = new JButton("-");
                button.setMargin(new java.awt.Insets(2, 2, 2, 2));
		button.setPreferredSize(new Dimension(24,24));
		button.setToolTipText("Decrease port number");
		button.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				dec();
			}
	        });
	        panel.add(button);

		button = new JButton("+");
                button.setMargin(new java.awt.Insets(2, 2, 2, 2));
		button.setPreferredSize(new Dimension(24,24));
	        button.setToolTipText("Increase port number");
	        button.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
	                  inc();
			}
		});
	        panel.add(button);
	}

	private void inc() {
		portnumber = Integer.parseInt(jText.getText());
		portnumber++;
		jText.setText(""+portnumber);
	}

	private void dec() {
		portnumber = Integer.parseInt(jText.getText());
		portnumber--;
		jText.setText(""+portnumber);
	}
}
