/*
 * Swing version of NodeGUI.
 */

import org.apache.xmlrpc.*;
import java.util.*;
import java.net.URL;
import java.io.*;
import java.awt.*;
import java.awt.event.*;
import java.awt.event.ItemListener;
import javax.swing.*;
import javax.swing.event.*;
import javax.swing.tree.*;


public class nodegui extends JFrame {
    XmlRpcClient client;
    String cmd,url;
    Hashtable hash_name = new Hashtable();
    JDesktopPane dtp = new JDesktopPane();
    GuiJIFContainer gc= null;
    JPanel  controlPanel = new JPanel();
    Container contentPane;


    public nodegui(String url) throws Exception {
		this.url=url;
		addControl();
		display();
		addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent e) {
           			System.exit(0);
            		}
        	});

    }

    public void addControl() throws Exception {
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

    public void getSpec() throws Exception {
	client = new XmlRpcClient (url);
	Object result = new Object();
	result = send("spec", new Vector());
	Hashtable spec = (Hashtable)result;
	gc = new GuiJIFContainer(client, spec, dtp);
	super.setTitle("Interface to "+gc.getSpectype()+":"+gc.getName());
    }

    public void display() throws Exception {
	getSpec();
        contentPane = getContentPane();
        contentPane.setLayout(new BorderLayout());
        contentPane.add(controlPanel, BorderLayout.NORTH);
        contentPane.add(dtp, BorderLayout.CENTER);
    }

    public void refresh() {
	dtp.removeAll();
	dtp.repaint();
    }

    private Object send(String cmd, Vector v) throws Exception {
	Object ret_obj=new Object();
	ret_obj = client.execute (cmd, new Vector());
	return ret_obj;
    }

    public static void main (String args[]) throws Exception {
	if (args.length < 1) {
	    System.err.println ("Usage: java Client URL");
	} else {
        nodegui window = new nodegui(args[0]);

	window.setBounds(100,100,400,500);
        window.show();
	}
    }

}
class GuiJIFContainer {
	XmlRpcClient xmlrpcclient;
	Hashtable spec;
	Vector content;
	Container c;
	String name, spectype;
	int width=300, height=200;

	public GuiJIFContainer(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.c=c;
		build();
	}

	public String getName() {
		return name;
	}

	public String getSpectype() {
		return spectype;
	}

	public void build() throws Exception {
		
		spectype = (String)spec.get("spectype");
		name = (String)spec.get("name");
		content = (Vector)spec.get("content");
		int jif_count=0;
		
		if (content instanceof Vector)
		for (Enumeration e = content.elements() ; e.hasMoreElements() ;) {

			Hashtable o = (Hashtable)e.nextElement();
			String s = (String)o.get("spectype");
			String n = (String)o.get("name");
			JPanel framePanel = new JPanel();
    			JScrollPane scrollPane = new JScrollPane(framePanel);
                	scrollPane.setPreferredSize(new Dimension(width,height));

			JInternalFrame jif = new JInternalFrame();
			jif.setTitle(n);
			jif.setContentPane(scrollPane); 
			jif.setIconifiable(true);
			jif.setResizable(true);
			jif.setMaximizable(true);
			jif.setClosable(false);
			jif.setBounds(20*(jif_count%10), 20*(jif_count%10), width, height);
			jif.setVisible(true);
			jif.pack();

			if (s.equals("container")) {
				new GuiContainer(xmlrpcclient, (Hashtable)o, framePanel);
			} else if (s.equals("method")) {
				new GuiMethod(xmlrpcclient, (Hashtable)o, framePanel);
			} else if (s.equals("data")) {
				new GuiData(xmlrpcclient, (Hashtable)o, framePanel);
			} 
			c.add(jif,2);
			jif.setIcon(true);
			jif_count++;
		}

	}
}

class GuiContainer {
	XmlRpcClient xmlrpcclient;
	Hashtable spec;
	Vector content;
	Container c;
	int type;
	public String name;

	public GuiContainer(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.c=c;
		build();
	}
	public void build() throws Exception {
		JPanel mainPanel =new JPanel();	
		name = (String)spec.get("name");
                mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		content = (Vector)spec.get("content");

		for (Enumeration e = content.elements() ; e.hasMoreElements() ;) {
			Hashtable o = (Hashtable)e.nextElement();
			String s = (String)o.get("spectype");

			if (s.equals("container")) 
				new GuiContainer(xmlrpcclient, (Hashtable)o, mainPanel);
			else if (s.equals("method"))
				new GuiMethod(xmlrpcclient, (Hashtable)o, mainPanel);
			else if (s.equals("data"))
				new GuiData(xmlrpcclient, (Hashtable)o, mainPanel);

		}
		c.add(mainPanel);
	}
}

class GuiMethod {
	XmlRpcClient xmlrpcclient;
	Hashtable spec;
	Container c;
	Vector argspec;
	public String name;
	public GuiMethod(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec= specWidget;
		this.c=c;
		build();
	}
	public void build() throws Exception {
		JPanel mainPanel =new JPanel();	
		String Mname = (String)spec.get("name");
		String Mid = (String)spec.get("id");
		mainPanel.setBorder(new javax.swing.border.TitledBorder(Mname));
                mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		argspec = (Vector)spec.get("argspec");
		Vector args = new Vector();
		Vector widgets = new Vector();
		
		if (argspec instanceof Vector)
		for (Enumeration e = argspec.elements() ; e.hasMoreElements() ;) {
			Hashtable o = (Hashtable)e.nextElement();
			String type  = (String)o.get("spectype");
			String name = (String)o.get("name");
			String xmlrpctype  = (String)o.get("xmlrpctype");
			String id = (String)o.get("id");

			if (o.containsKey("choices")) {
				Hashtable choices = (Hashtable)o.get("choices");
				String choices_type = (String)choices.get("type");
				String choices_id = (String)choices.get("id");
				if (choices_type.equals("array"))
					new AddComboBox(name, xmlrpcclient, choices_id, widgets, mainPanel);
				if (choices_type.equals("struct"))
					new TreeData(name, xmlrpcclient, choices_id, widgets, mainPanel);
			} else

			if (xmlrpctype.equals("string"))
    				new AddTextField(name, 20, widgets, mainPanel);

			if (xmlrpctype.equals("boolean"))
				new AddCheckBox(name, widgets, mainPanel);

			Object defaultval = null;
			if (spec.containsKey("default")) {
				defaultval = spec.get("default");
			}
			if (xmlrpctype.equals("struct")) {
				new TreeData(name, xmlrpcclient, id, (Hashtable)defaultval, widgets, mainPanel);
			}
	
		}

		new AddButton (Mname, xmlrpcclient, Mid, widgets, mainPanel);
		c.add(mainPanel);
	}
}

class GuiData {
	XmlRpcClient xmlrpcclient;
	Hashtable spec;
	Container c;
	Vector argspec;
	String name;
	String xmlrpctype;
	int type;

	public GuiData(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.c=c;
		build();
	}
	public void build() throws Exception {
		name = (String)spec.get("name");
		xmlrpctype  = (String)spec.get("xmlrpctype");
		String id = (String)spec.get("id");
		Vector widgets = new Vector();
		Vector args = new Vector();
		args.add(id);

		JPanel mainPanel =new JPanel();	
		mainPanel.setBorder(new javax.swing.border.TitledBorder(name));
                mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));

		if (spec.containsKey("permissions")) {
			type=1;	
			String permissions = (String)spec.get("permissions");
			if (permissions.equals("r"))
				new AddButton ("Get", xmlrpcclient, "GET", args, mainPanel);
			if (permissions.equals("w")) 
				new AddButton ("Set", xmlrpcclient, "SET", args, mainPanel);
			if (permissions.equals("rw")) {

				new AddButton ("Get", xmlrpcclient, "GET", args, mainPanel);
				new AddButton ("Set", xmlrpcclient, "SET", args, mainPanel);
			}
		}

		Object defaultval = null;
		if (spec.containsKey("default")) {
			type=1;	
			defaultval = spec.get("default");
			System.out.println("def: "+defaultval +" class: "+defaultval.getClass());
		} 

		System.out.println("NAME: "+name+" SPEC: "+spec);
		if (spec.containsKey("choices")) {
				Hashtable choices = (Hashtable)spec.get("choices");
				String choices_type = (String)choices.get("type");
				String choices_id = (String)choices.get("id");
				if (choices_type.equals("array"))
					new AddComboBox(name, xmlrpcclient, choices_id, widgets, mainPanel);
				if (choices_type.equals("struct"))
					new TreeData(name, xmlrpcclient, choices_id, widgets, mainPanel);
		} else
		if (xmlrpctype.equals("string")) {
    			new AddTextField(20, widgets, mainPanel);
		} else
		if (xmlrpctype.equals("boolean")) {
			new AddCheckBox(name, widgets, mainPanel);
		} else
		if (xmlrpctype.equals("struct")) {
			new TreeData(name, xmlrpcclient, id, (Hashtable)defaultval, widgets, mainPanel);
		}
		c.add(mainPanel,name);
	}
}

class AddCheckBox {
	String text;
	Vector widgets;
	Container c;
	public AddCheckBox(String text, Vector widgets, Container c) {
		this.text=text;
		this.widgets=widgets;
		this.c = c;
		build();
	}
	private void build() {
		JCheckBox checkbox = new JCheckBox(text);
		widgets.add(checkbox);
        	checkbox.setAlignmentX(Component.LEFT_ALIGNMENT);
        	c.add(checkbox);
	}
}

class AddComboBox {
	String text, id;
	XmlRpcClient xmlrpcclient;
	Container c;
	Vector items;
	Vector widgets;

	public AddComboBox(String text, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this.text=text;
		this.xmlrpcclient=xmlrpcclient;
		this.widgets=widgets;
		this.id=id;
		this.c = c;
		build();
	}

	public AddComboBox(XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this(null, xmlrpcclient, id, widgets, c);
	}
	
	private void build() throws Exception {
		Vector param = new Vector(1);
		param.add(id);
		Object items_obj = xmlrpcclient.execute("GET", param);
		JPanel aPanel = new JPanel();
		aPanel.setLayout(new BoxLayout(aPanel, BoxLayout.Y_AXIS));

		if (items_obj instanceof Vector)
			items=(Vector)items_obj;
		else
			items=new Vector();

		JComboBox cb = new JComboBox(items);
		widgets.add(cb);
		JLabel lbl = new JLabel(text);
		aPanel.add(lbl);
		aPanel.add(cb);
		aPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
		aPanel.setAlignmentY(Component.TOP_ALIGNMENT);
		c.add(aPanel);
	}
}

class AddTextField {
	String text;
	int size;
	Vector widgets;
	Container c;

	public AddTextField(String text, int size, Vector widgets, Container c) {
		this.text=text;
		this.size=size;
		this.widgets=widgets;
		this.c = c;
		build();
	}

	public AddTextField(int size, Vector widgets, Container c) {
		this(null, size, widgets, c);
	}

	private void build() {
		JPanel aPanel = new JPanel();
		aPanel.setLayout(new BoxLayout(aPanel, BoxLayout.Y_AXIS));
		JTextField textField = new JTextField(size);
		widgets.add(textField);
		JLabel lbl = new JLabel(text);
        	aPanel.add(lbl);
        	aPanel.add(textField);
        	aPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
		c.add(aPanel);

	}
}

class AddButton {
	String name, id;
	XmlRpcClient xmlrpcclient;
	Vector args, widgets=new Vector();
	Container c;
	public AddButton (String name, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this.name=name;
		this.xmlrpcclient=xmlrpcclient;
		this.id=id;
		this.widgets=widgets;
		this.c = c;
		build();
	}
	private void build() throws Exception {
        	JButton button = new JButton(name);
		c.add(button);
                button.addActionListener(new ActionListener() {
                        public void actionPerformed(ActionEvent event) {
				args = getArgs(widgets);
				System.out.println("("+widgets+");");
				System.out.println("xmlrpcclient.execute("+id+", "+args+");");
				try {
					xmlrpcclient.execute(id, args);
				} catch (Exception e) {
					System.err.println("Exception: "+e);
				}
			}
		});
	}

	private Vector getArgs(Vector widgets) {
		Vector args = new Vector();
		for (Enumeration enumwidget = widgets.elements() ; enumwidget.hasMoreElements() ;) {
			Object o = enumwidget.nextElement();
			if (o instanceof JTextField) {
				JTextField jtf = (JTextField)o;
				args.add(jtf.getText());
			} else if (o instanceof JCheckBox) {
				JCheckBox jckb = (JCheckBox)o;
				Boolean b = Boolean.FALSE;
				args.add(b.valueOf(jckb.isSelected()));	
			} else if (o instanceof Vector) {
				Vector v = (Vector)o;
				args.add(v);
			} else if (o instanceof JComboBox) {
				JComboBox jcb = (JComboBox)o;
				args.add(jcb.getSelectedItem());
			} else if (o instanceof String) {
				args.add(o.toString());
			}
				
		}
		return args;
	}
}

class TreeData {
	String name, id;
	XmlRpcClient xmlrpcclient;
	Container c;
	Hashtable hashtree;
	Vector widgets = new Vector();
	JTree tree;
	TreeTableModel model;
	Vector path = new Vector();

	public TreeData(String name, XmlRpcClient xmlrpcclient, String id, Hashtable defaultval, Vector widgets, Container c) throws Exception  {
		this.name=name;
		this.xmlrpcclient=xmlrpcclient;
		this.id=id;
		this.hashtree=defaultval;
		this.widgets=widgets;
		this.c = c;
		build();
	}
	public TreeData(String name, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this(name,xmlrpcclient,id,null,widgets,c);
	}

	private void build() throws Exception {
		if (hashtree ==null) {
			Vector param = new Vector(1);
			param.add(id);
			Object data = xmlrpcclient.execute("GET", param);

			if (data instanceof Hashtable) {
				hashtree=(Hashtable)data;
			} else hashtree = new Hashtable();
		} 

		System.out.println("HASHTREE: "+hashtree);
		model = new HashtableNodesModel(new HashtableNodes(hashtree,name).getRoot());
		JTreeTable treeTable = new JTreeTable(model);
                JScrollPane hashPane = new JScrollPane(treeTable);
                hashPane.setPreferredSize(new Dimension(200,200));
		c.add(hashPane);

		tree = treeTable.getTree();
		tree.addTreeSelectionListener(new TreeSelectionListener() {
			public void valueChanged(TreeSelectionEvent e) {
				Object key = tree.getLastSelectedPathComponent();
				Object value = model.getValueAt(key,1);
				TreePath tp = tree.getSelectionPath();
				if (tp!=null){
					path.clear();
					Object[] keys = tp.getPath();
					for (int i=0; i<keys.length; i++){
                                		Object k = keys[i].toString();
                                		path.add(k);
                        		}
						path.add(value);
						path.remove(0);
				}
        
			}
		});
		widgets.add(path);

	}
}
