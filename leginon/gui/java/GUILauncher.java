				
import java.awt.Dimension;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import java.net.InetAddress;
import java.net.UnknownHostException;
import org.apache.xmlrpc.*;
import java.util.Hashtable;
import java.util.Vector;
import java.util.Enumeration;

public class GUILauncher extends javax.swing.JPanel {

	public final int DEFAULTPORTNUMBER = 49153;
	public final String DEFAULTHOST = "stratocaster";

	public GUILauncher() throws Exception {
		initcomponents();
	}

	private int portnumber = DEFAULTPORTNUMBER;
	private String host = DEFAULTHOST;

	private XmlRpcClient client;
	private Hashtable nodeLocations;

	private int width = 800;
	private int height = 500;
	private int nw_count=1;


	private void xmlRpcConnect(String host) throws Exception {
		client = new XmlRpcClient (host);
	}

	private void getNodeLocations() throws Exception {
		nodeLocations = (Hashtable)client.execute("getNodeLocations", new java.util.Vector());
		Vector items = new Vector();
		for (Enumeration e = nodeLocations.keys() ; e.hasMoreElements() ;)
         		items.add(e.nextElement());

		javax.swing.DefaultComboBoxModel model = new javax.swing.DefaultComboBoxModel(items);
		comboBoxNodeId.setModel(model);
	}

	private String getLocalhost() throws UnknownHostException {
		InetAddress addr = InetAddress.getLocalHost();
	        String hostname = addr.getHostName();
		return hostname;
	}

	private String getNodeUrl(Object key) {
		Hashtable nodeInfo = (Hashtable)nodeLocations.get(key);
		String url = "http://"+nodeInfo.get("hostname")+":"+nodeInfo.get("UI port");
		return url;
	}

	private void initcomponents() throws Exception  {

		tabbedPaneLauncher = new javax.swing.JTabbedPane();
		panelConnect = new javax.swing.JPanel();
		panelConnectHost = new javax.swing.JPanel();
		panelConnectStatus = new javax.swing.JPanel();
		labelHost = new javax.swing.JLabel();
		comboBoxHost = new javax.swing.JComboBox();
		labelPort = new javax.swing.JLabel();
		textFieldConnectPort = new javax.swing.JTextField();
		labelStatus = new javax.swing.JLabel();
		labelState = new javax.swing.JLabel();
		panelAuto = new javax.swing.JPanel();
		labelNodeId = new javax.swing.JLabel();
		comboBoxNodeId = new javax.swing.JComboBox();
		buttonConnect = new javax.swing.JButton();
		buttonLaunch = new javax.swing.JButton();
		buttonLaunchGui = new javax.swing.JButton();
		buttonRefresh = new javax.swing.JButton();
		panelManual = new javax.swing.JPanel();
		labelManualHost = new javax.swing.JLabel();
		comboBoxManualHost = new javax.swing.JComboBox();
		labelManualPort = new javax.swing.JLabel();
		textFieldManualPort = new javax.swing.JTextField();

		/**
		*	Connect Tab
		*/


		panelConnect.setLayout(new java.awt.BorderLayout());
		panelConnect.setBorder(new javax.swing.border.TitledBorder(null, "Manager UI Server Host", javax.swing.border.TitledBorder.DEFAULT_JUSTIFICATION, javax.swing.border.TitledBorder.DEFAULT_POSITION, new java.awt.Font("Dialog", 1, 12)));

		panelConnectHost.setLayout(new java.awt.FlowLayout(java.awt.FlowLayout.LEFT));
		panelConnectStatus.setLayout(new java.awt.FlowLayout(java.awt.FlowLayout.LEFT));


		labelHost.setText("Host");
		panelConnectHost.add(labelHost);

		comboBoxHost.setEditable(true);
		try {
			host = getLocalhost();
		} catch (UnknownHostException e) { }
		comboBoxHost.addItem(host);

		panelConnectHost.add(comboBoxHost);

		labelPort.setText("Port");
		panelConnectHost.add(labelPort);

		addPortCounter(panelConnectHost, textFieldConnectPort);

		buttonConnect.setText("Connect");
		buttonConnect.setPreferredSize(new Dimension(100,24));
		buttonConnect.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {	
					portnumber = Integer.parseInt(textFieldConnectPort.getText());
					host = (String)comboBoxHost.getSelectedItem();
					if(!isComboBoxItem(comboBoxHost, host))
						comboBoxHost.addItem(host);
					xmlRpcConnect("http://"+host+":"+portnumber);
					labelState.setText("Connected");
					getNodeLocations();
				} catch (Exception ex) {
					labelState.setText("Not Connected");
					System.out.println("Not Connected: "+ex);
				}
			}
		});

		panelConnectHost.add(buttonConnect);
		panelConnect.add(panelConnectHost, java.awt.BorderLayout.NORTH);

		labelStatus.setText("Status:");
		panelConnectStatus.add(labelStatus);

		labelState.setText("Not Connected");
		panelConnectStatus.add(labelState);
		panelConnect.add(panelConnectStatus, java.awt.BorderLayout.CENTER);


		tabbedPaneLauncher.addTab("Connect", panelConnect);

		/**
		*	Automatic Tab
		*/

		panelAuto.setLayout(new java.awt.FlowLayout(java.awt.FlowLayout.LEFT));
		panelAuto.setBorder(new javax.swing.border.TitledBorder(null, "Node UI", javax.swing.border.TitledBorder.DEFAULT_JUSTIFICATION, javax.swing.border.TitledBorder.DEFAULT_POSITION, new java.awt.Font("Dialog", 1, 12)));
		labelNodeId.setText("Node ID");
		panelAuto.add(labelNodeId);

		panelAuto.add(comboBoxNodeId);

		buttonLaunch.setText("Launch");
		buttonLaunch.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {	
					Object key = comboBoxNodeId.getSelectedItem();
        				nodegui newWindow = new nodegui(getNodeUrl(key));
					newWindow.setBounds(20*(nw_count%10), 20*(nw_count%10), width, height);
					newWindow.setVisible(true);
					nw_count++;
				} catch (Exception ex) {
					System.out.println("Launch Exception: "+ex);
				}
			}
		});

		panelAuto.add(buttonLaunch);

		buttonRefresh.setText("Refresh");
		buttonRefresh.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {	
				} catch (Exception ex) {
					labelState.setText("Not Connected");
					System.out.println("Not Connected: "+ex);
				}
			}
		});

		panelAuto.add(buttonRefresh);

		tabbedPaneLauncher.addTab("Automatic", panelAuto);

		/**
		*	Manual Tab
		*/

		panelManual.setBorder(new javax.swing.border.TitledBorder(null, "Manual UI selection", javax.swing.border.TitledBorder.DEFAULT_JUSTIFICATION, javax.swing.border.TitledBorder.DEFAULT_POSITION, new java.awt.Font("Dialog", 1, 12)));
		labelManualHost.setText("Host");
		panelManual.add(labelManualHost);

		comboBoxManualHost.setEditable(true);
		try {
			host = getLocalhost();
		} catch (UnknownHostException e) { }
		comboBoxManualHost.addItem(host);

		panelManual.add(comboBoxManualHost);

		labelManualPort.setText("Port");
		panelManual.add(labelManualPort);

		addPortCounter(panelManual, textFieldManualPort);

		buttonLaunchGui.setText("Launch GUI");
		buttonLaunchGui.setPreferredSize(new Dimension(120,24));
		buttonLaunchGui.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {	
					portnumber = Integer.parseInt(textFieldManualPort.getText());
					host = (String)comboBoxManualHost.getSelectedItem();
					if(!isComboBoxItem(comboBoxManualHost, host))
						comboBoxManualHost.addItem(host);
					
        				nodegui newWindow = new nodegui("http://"+host+":"+portnumber);
					newWindow.setBounds(20*(nw_count%10), 20*(nw_count%10), width, height);
					newWindow.setVisible(true);
					nw_count++;
				} catch (Exception ex) {}
			}
		});

		panelManual.add(buttonLaunchGui);

		tabbedPaneLauncher.addTab("Manual", panelManual);

		add(tabbedPaneLauncher);
        }

	private boolean isComboBoxItem(javax.swing.JComboBox cb, String item) {
		boolean state=false;
		for (int i=0; i<cb.getItemCount(); i++)
			if(item.equals(cb.getItemAt(i)))
				state=true;
		return state;
	}

	private void addPortCounter(javax.swing.JPanel panel, final javax.swing.JTextField textFieldPort) {
	        javax.swing.JButton button = null;
		textFieldPort.setColumns(6);
		textFieldPort.setText(""+portnumber);
		textFieldPort.setPreferredSize(new Dimension(60,24));
		panel.add(textFieldPort);

		button = new javax.swing.JButton("-");
                button.setMargin(new java.awt.Insets(2, 2, 2, 2));
		button.setPreferredSize(new Dimension(24,24));
		button.setToolTipText("Decrease port number");
		button.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
			  dec(textFieldPort);
			}
	        });
	        panel.add(button);

		button = new javax.swing.JButton("+");
                button.setMargin(new java.awt.Insets(2, 2, 2, 2));
		button.setPreferredSize(new Dimension(24,24));
	        button.setToolTipText("Increase port number");
	        button.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
			  inc(textFieldPort);
			}
		});
	        panel.add(button);
	}

	private void inc(javax.swing.JTextField controller) {
		portnumber = Integer.parseInt(controller.getText());
		portnumber++;
		controller.setText(""+portnumber);
	}

	private void dec(javax.swing.JTextField controller) {
		portnumber = Integer.parseInt(controller.getText());
		portnumber--;
		controller.setText(""+portnumber);
	}

	private javax.swing.JTabbedPane tabbedPaneLauncher;
	private javax.swing.JPanel panelConnect;
	private javax.swing.JPanel panelConnectHost;
	private javax.swing.JPanel panelConnectStatus;
	private javax.swing.JPanel panelAuto;
	private javax.swing.JPanel panelManual;
	private javax.swing.JLabel labelStatus;
	private javax.swing.JLabel labelState;
	private javax.swing.JLabel labelHost;
	private javax.swing.JLabel labelManualPort;
	private javax.swing.JLabel labelManualHost;
	private javax.swing.JLabel labelPort;
	private javax.swing.JLabel labelNodeId;
	private javax.swing.JComboBox comboBoxNodeId;
	private javax.swing.JComboBox comboBoxHost;
	private javax.swing.JComboBox comboBoxManualHost;
	private javax.swing.JTextField textFieldConnectPort;
	private javax.swing.JTextField textFieldManualPort;
	private javax.swing.JButton buttonConnect;
	private javax.swing.JButton buttonLaunch;
	private javax.swing.JButton buttonLaunchGui;
	private javax.swing.JButton buttonRefresh;
}
