import org.apache.xmlrpc.*;
import java.util.Hashtable;
import java.util.Enumeration;
import java.util.Vector;
import java.awt.*;
import java.awt.event.ItemListener;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;
import javax.swing.*;
import javax.swing.event.TreeModelEvent;
import javax.swing.event.TreeModelListener;
import javax.swing.event.TreeSelectionEvent;
import javax.swing.event.TreeSelectionListener;
import javax.swing.tree.TreePath;

public class GuiContainer {
	private XmlRpcClient xmlrpcclient;
	private Hashtable spec;
	private Vector content;
	private Container c;
	private String name;

	public GuiContainer(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.c=c;
		build();
	}

	public void refresh() {}

	private void build() throws Exception {
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

	private XmlRpcClient xmlrpcclient;
	private Hashtable spec;
	private Container c;
	private Vector argspec;
	private Vector widgets;
	private String name;

	public GuiMethod(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec= specWidget;
		this.c=c;
		build();
	}

	public void refresh() throws Exception {
		if (widgets instanceof Vector)
			for (Enumeration e = widgets.elements() ; e.hasMoreElements() ;) {
				Object widget = e.nextElement();
				if (widget instanceof TreeData) {
					TreeData td = (TreeData)widget;
					td.update();
				} else if (widget instanceof AddComboBox) {
					AddComboBox acb = (AddComboBox)widget;
					acb.update();
				}
			}
	}

	private void build() throws Exception {
		JPanel mainPanel =new JPanel();	
		String Mname = (String)spec.get("name");
		String Mid = (String)spec.get("id");
		mainPanel.setBorder(new javax.swing.border.TitledBorder(Mname));
                mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		argspec = (Vector)spec.get("argspec");
		Vector args = new Vector();
		widgets = new Vector();
		
		if (argspec instanceof Vector)
		for (Enumeration e = argspec.elements() ; e.hasMoreElements() ;) {
			Hashtable o = (Hashtable)e.nextElement();
			String type  = (String)o.get("spectype");
			String name = (String)o.get("name");
			String xmlrpctype  = (String)o.get("xmlrpctype");
			String id = (String)o.get("id");

			Object defaultval = null;
			if (spec.containsKey("default")) {
				defaultval = spec.get("default");
			}

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
    				new AddTextField(name, 20, defaultval, widgets, mainPanel);

			if (xmlrpctype.equals("boolean"))
				new AddCheckBox(name, widgets, mainPanel);

			if (xmlrpctype.equals("struct")) {
				new TreeData(name, xmlrpcclient, id, (Hashtable)defaultval, widgets, mainPanel);
			}
	
		}

		new AddButton (Mname, xmlrpcclient, Mid, widgets, mainPanel);
		c.add(mainPanel);
	}
}

class GuiData {
	private XmlRpcClient xmlrpcclient;
	private Hashtable spec;
	private Container c;
	private Vector argspec;
	private Vector widgets;
	private String name;
	private String xmlrpctype;

	public GuiData(XmlRpcClient xmlrpcclient, Hashtable specWidget, Container c) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.c=c;
		build();
	}

	public void refresh() throws Exception {
		if (widgets instanceof Vector)
			for (Enumeration e = widgets.elements() ; e.hasMoreElements() ;) {
				Object widget = e.nextElement();
				if (widget instanceof TreeData) {
					TreeData td = (TreeData)widget;
					td.update();
				} else if (widget instanceof AddComboBox) {
					AddComboBox acb = (AddComboBox)widget;
					acb.update();
				} 
			}
	}

	private void build() throws Exception {
		name = (String)spec.get("name");
		xmlrpctype  = (String)spec.get("xmlrpctype");
		String id = (String)spec.get("id");
		widgets = new Vector();

		JPanel mainPanel =new JPanel();	
		mainPanel.setBorder(new javax.swing.border.TitledBorder(name));
                mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));

		if (spec.containsKey("permissions")) {
			JPanel permPanel =new JPanel();	
                	permPanel.setLayout(new BoxLayout(permPanel, BoxLayout.X_AXIS));
			String permissions = (String)spec.get("permissions");
			if (permissions.matches("^[a-zA-Z]*[rR][a-zA-Z]*"))
				new AddButton ("Get", xmlrpcclient, "GET", id, widgets, permPanel);
			if (permissions.matches("^[a-zA-Z]*[wW][a-zA-Z]*"))
				new AddButton ("Set", xmlrpcclient, "SET", id, widgets, permPanel);
			mainPanel.add(permPanel);
		}

		Object defaultval = null;
		if (spec.containsKey("default")) {
			defaultval = spec.get("default");
		} 

		if (spec.containsKey("choices")) {
				Hashtable choices = (Hashtable)spec.get("choices");
				String choices_type = (String)choices.get("type");
				String choices_id = (String)choices.get("id");
				if (choices_type.equals("array"))
					new AddComboBox(name, xmlrpcclient, choices_id, widgets, mainPanel, true);
				if (choices_type.equals("struct"))
					new TreeData(name, xmlrpcclient, choices_id, widgets, mainPanel);
		} else
		if (xmlrpctype.matches("string|integer|float|array")) {
			new AddTextField(20, defaultval, widgets, mainPanel);
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
	private String text;
	private Vector widgets;
	private Container c;
	private JCheckBox checkbox;

	public AddCheckBox(String text, Vector widgets, Container c) {
		this.text=text;
		this.widgets=widgets;
		this.c = c;
		build();
	}
	
	public Boolean getValue() {
		Boolean b = Boolean.FALSE;
		return b.valueOf(checkbox.isSelected());	
	}

	private void build() {
		checkbox = new JCheckBox(text,false);
        	checkbox.setAlignmentX(Component.LEFT_ALIGNMENT);
        	c.add(checkbox);
		widgets.add(this);
	}
}

class AddComboBox {
	private String text, id;
	private XmlRpcClient xmlrpcclient;
	private Container c;
	private Vector items = new Vector();
	private Vector widgets;
	private JComboBox cb;
	boolean editable;

	public AddComboBox(String text, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c, boolean editable) throws Exception  {
		this.text=text;
		this.xmlrpcclient=xmlrpcclient;
		this.widgets=widgets;
		this.id=id;
		this.c = c;
		this.editable=editable;
		build();
	}

	public AddComboBox(String text, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this(text, xmlrpcclient, id, widgets, c, false);
	}

	public AddComboBox(XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this(null, xmlrpcclient, id, widgets, c, false);
	}

	public String getValue() {
		return (String)cb.getSelectedItem();
	}	

	public void setValue(String value) {
		cb.setSelectedItem(value);
	}	

	public void update() throws Exception {
		getData(id);
		DefaultComboBoxModel model = new DefaultComboBoxModel(items);
        	cb.setModel(model);
		cb.revalidate();
	}

	private void build() throws Exception {
		JPanel aPanel = new JPanel();
		aPanel.setLayout(new BoxLayout(aPanel, BoxLayout.Y_AXIS));

		getData(id);
		cb = new JComboBox(items);
		cb.setEditable(editable);
		JLabel lbl = new JLabel(text);
		aPanel.add(lbl);
		aPanel.add(cb);
		aPanel.setAlignmentX(Component.LEFT_ALIGNMENT);
		aPanel.setAlignmentY(Component.TOP_ALIGNMENT);
		c.add(aPanel);
		widgets.add(this);
	}

	private void getData(String id) throws Exception {
			Vector param = new Vector(1);
			param.add(id);
			Object data = xmlrpcclient.execute("GET", param);

			if (data instanceof Vector)
				items=(Vector)data;

	}
}

class AddTextField {
	private String text;
	private Object defaultval;
	private int size;
	private Vector widgets;
	private Container c;
	private JTextField textField;

	public AddTextField(String text, int size, Object defaultval, Vector widgets, Container c) {
		this.text=text;
		this.size=size;
		this.defaultval=defaultval;
		this.widgets=widgets;
		this.c = c;
		build();
	}

	public AddTextField(int size, Object defaultval, Vector widgets, Container c) {
		this(null, size, defaultval, widgets, c);
	}
	
	public String getValue() {
		return textField.getText();
	}

	public void update(String text) {
		textField.setText(text);
	}

	private void build() {
		JPanel aPanel = new JPanel();
		aPanel.setLayout(new BoxLayout(aPanel, BoxLayout.Y_AXIS));
		if (defaultval==null)
			defaultval="";
		textField = new JTextField(""+defaultval, size);
		JLabel lbl = new JLabel(text);
        	aPanel.add(lbl);
        	aPanel.add(textField);
        	aPanel.setAlignmentX(Component.CENTER_ALIGNMENT);
		c.add(aPanel);
		widgets.add(this);

	}
}

class AddButton {
	private String name, id, cmd, cmdxmlrpc;
	private XmlRpcClient xmlrpcclient;
	private Vector args, widgets;
	private Container c;

	public AddButton (String name, XmlRpcClient xmlrpcclient, String cmd, String id, Vector widgets, Container c) throws Exception  {
		this.name=name;
		this.xmlrpcclient=xmlrpcclient;
		this.cmd=cmd;
		this.id=id;
		this.widgets=widgets;
		this.c = c;
		build();
	}

	public AddButton (String name, XmlRpcClient xmlrpcclient, String id, Vector widgets, Container c) throws Exception  {
		this(name,xmlrpcclient,null,id,widgets,c);
	}
	private void build() throws Exception {
        	JButton button = new JButton(name);
		c.add(button);
                button.addActionListener(new ActionListener() {
                        public void actionPerformed(ActionEvent event) {
				try {


				if (cmd==null) {	
					cmdxmlrpc=id;
					args = getArgs(widgets);
				} else {
					cmdxmlrpc=cmd;
					args = getData(widgets);
				}
					// Display xmlRPC command
					// System.out.println("xmlrpcclient.execute("+cmdxmlrpc+", "+args+");");
					Object result = xmlrpcclient.execute(cmdxmlrpc, args);
					
					refresh(widgets, result);


				} catch (Exception e) {
					System.err.println("Exception: "+e);
				}
			}
		});
	}
	
	private void refresh(Vector widgets, Object result) throws Exception {
		for (Enumeration enumwidget = widgets.elements() ; enumwidget.hasMoreElements() ;) {
			Object o = enumwidget.nextElement();
			if (o instanceof TreeData) {
				TreeData td = (TreeData)o;
				td.update();
			} else if (o instanceof AddComboBox) {
				AddComboBox c = (AddComboBox)o;
				c.update();
				c.setValue((String)result);
			} else if (o instanceof AddTextField) {
				AddTextField t = (AddTextField)o;
				if (result!=null)
				t.update(""+result);
			}
		}
	}

	private Vector getData(Vector widgets) throws Exception {
		Vector args = new Vector();
		args.add(id);
		if (cmd.equals("SET"))
		for (Enumeration enumwidget = widgets.elements() ; enumwidget.hasMoreElements() ;) {
			Object o = enumwidget.nextElement();
			if (o instanceof AddTextField) {
				AddTextField t = (AddTextField)o;
				args.add(t.getValue());
			} else if (o instanceof TreeData) {
				TreeData td = (TreeData)o;
				args.add(td.getHashTree());
			} else if (o instanceof AddComboBox) {
				AddComboBox acb = (AddComboBox)o;
				args.add(acb.getValue());
			}
		}
		return args;
	}

	private Vector getArgs(Vector widgets) throws Exception {
		Vector args = new Vector();
		for (Enumeration enumwidget = widgets.elements() ; enumwidget.hasMoreElements() ;) {
			Object o = enumwidget.nextElement();
			if (o instanceof AddTextField) {
				AddTextField t = (AddTextField)o;
				args.add(t.getValue());
			} else if (o instanceof AddCheckBox) {
				AddCheckBox ckb = (AddCheckBox)o; 
				args.add(ckb.getValue());
			} else if (o instanceof TreeData) {
				TreeData td = (TreeData)o;
				args.add(td.getValue());
			} else if (o instanceof AddComboBox) {
				AddComboBox c = (AddComboBox)o;
				args.add(c.getValue());
			}
		}
		return args;
	}

}

class TreeData {
	private String name, id;
	private XmlRpcClient xmlrpcclient;
	private Container c;
	private Vector widgets;
	private JTree tree;
	private TreeTableModel model;
	private JTreeTable treeTable;
	private JScrollPane hashPane;
	private Hashtable hashtree = new Hashtable();
	private Vector path = new Vector();

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

	public Vector getValue() {
		return path;
	}

	public Hashtable getHashTree() {
		return hashtree;
	}
	public void update() throws Exception {
		getData(id);
		model = new HashtableNodesModel(new HashtableNodes(hashtree,name).getRoot());
		tree.setModel(model);
		treeTable.revalidate();
	}


	private void build() throws Exception {

		if (hashtree==null || hashtree.isEmpty())
			getData(id);

		model = new HashtableNodesModel(new HashtableNodes(hashtree,name).getRoot());
		treeTable = new JTreeTable(model);
                hashPane = new JScrollPane(treeTable);
        	hashPane.getViewport().setBackground(Color.white);

		treeTable.setBackground(new Color(255, 255, 255));
                hashPane.setPreferredSize(new Dimension(300,300));
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
					if (value!=null && !(value.equals("")))
						path.add(value);

					// to remove the root of the tree...
					path.remove(0);
				}
        
			}
		});
		model.addTreeModelListener( new TreeModelListener() {
			public void treeNodesChanged(TreeModelEvent e) {
				Object key = e.getChildren()[0];
				Object value = model.getValueAt(key,1);
				TreePath tp = e.getTreePath().pathByAddingChild(key);
				Object [] keys = tp.getPath();

				// update the hashtable
				new HashtableNodes.UpdateHashTree(hashtree, keys, value);
			}
			public void treeNodesInserted(TreeModelEvent e) {}
			public void treeNodesRemoved(TreeModelEvent e) {}
			public void treeStructureChanged(TreeModelEvent e) {}
	});

		widgets.add(this);

	}

	private void getData(String id) throws Exception {
			Vector param = new Vector(1);
			param.add(id);
			Object data = xmlrpcclient.execute("GET", param);

			if (data instanceof Hashtable)
				hashtree=(Hashtable)data;
	}
}
