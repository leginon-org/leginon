import org.apache.xmlrpc.*;
import java.util.Hashtable;
import java.util.Enumeration;
import java.util.Vector;
import java.awt.*;
import javax.swing.*;

public class GuiJIFContainer {
	private XmlRpcClient xmlrpcclient;
	private Hashtable spec;
	private Vector content;
	private NodeDesktop dtp;
	private String name, spectype;
	int width=350, height=300;

	public GuiJIFContainer(XmlRpcClient xmlrpcclient, Hashtable specWidget, NodeDesktop dtp) throws Exception {
		this.xmlrpcclient=xmlrpcclient;
		this.spec=specWidget;
		this.dtp=dtp;
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

			dtp.addJIF(scrollPane, jif_count, n);

			if (s.equals("container")) {
				new GuiContainer(xmlrpcclient, (Hashtable)o, framePanel);
			} else if (s.equals("method")) {
				new GuiMethod(xmlrpcclient, (Hashtable)o, framePanel);
			} else if (s.equals("data")) {
				new GuiData(xmlrpcclient, (Hashtable)o, framePanel);
			} 
			jif_count++;
		}

	}
}
