//
// COPYRIGHT:
//       The Leginon software is Copyright 2003
//       The Scripps Research Institute, La Jolla, CA
//       For terms of the license agreement
//       see  http://ami.scripps.edu/software/leginon-license
//
import java.awt.*;
import java.util.*;
import java.awt.event.*;
import javax.swing.*;

public class NodeDesktop {
	private CustomDesktopPane desktopPane = new CustomDesktopPane();
	private JMenu displayMenu = new JMenu();
	private	Vector vframe = new Vector();
	private Vector vmenu = new Vector();
	private Vector vtogglebutton = new Vector();
	private Vector vgui = new Vector();
	private	JMenuItem	menuFrame;
	private	JToolBar toolbar = new JToolBar();
	
	private final int	ITEM_PLAIN	=	0;	// Item types
	private final int	ITEM_CHECK	=	1;
	private final int	ITEM_RADIO	=	2;

	public JDesktopPane getDesktopPane() {
		return desktopPane;
	}

	public void clear() {
		desktopPane.removeAll();
		desktopPane.repaint();
		toolbar.removeAll();
		vframe.clear();
		vmenu.clear();
		vgui.clear();
		vtogglebutton.clear();
	}

	public JMenuBar createMenuBar() {
		JMenuBar menubar = new JMenuBar();
		displayMenu = new JMenu("Display");
		displayMenu.setMnemonic(68);

		displayMenu.add(new OpenAllAction());
		displayMenu.add(new CloseAllAction());
		displayMenu.add(new TileAllAction());
		displayMenu.add(new CascadeAction());
		displayMenu.addSeparator();

		menubar.add(displayMenu);
		return menubar;
	}

	public JToolBar addButtons() {
		return toolbar;
	}

	public void addJIF(Object gui, JScrollPane scrollPane, int nb, String name) throws Exception {
			Dimension d = scrollPane.getPreferredSize();
			JInternalFrame jif = createInternalFrame(name);
			jif.setBounds(20*(nb%10), 20*(nb%10), (int)d.getWidth(),(int)d.getHeight());
			jif.setContentPane(scrollPane); 
			jif.setVisible(true);
			vframe.add(jif);
			vgui.add(gui);

			JMenuItem jmi =	createMenuItem( displayMenu, ITEM_CHECK, name, null, nb+47, name);
			vmenu.add(jmi);

			JToggleButton jtb = createToggleButton(name);
			toolbar.add(jtb);
			vtogglebutton.add(jtb);
			desktopPane.add(jif);
			jif.setIcon(true);
			
	}

	private JToggleButton createToggleButton(String name) {
		JToggleButton jtb = new JToggleButton(name, false);

		jtb.addMouseListener(new java.awt.event.MouseAdapter() {
			public void mouseExited(java.awt.event.MouseEvent evt) {
				jtbMouseExited(evt);
			}
			public void mouseEntered(java.awt.event.MouseEvent evt) {
				jtbMouseEntered(evt);
			}
        	});

		jtb.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(java.awt.event.ActionEvent evt) {
				jtbActionPerformed(evt);
			}
		});

		return jtb;
	}
	private void jtbMouseEntered(java.awt.event.MouseEvent evt) {
		JToggleButton jtb = (JToggleButton)evt.getSource();
	        jtb.setBackground(new java.awt.Color(204, 204, 255));
	}

	private void setToggleButton(JToggleButton jtb, boolean state) {
		if (state) {
			jtb.setForeground(new java.awt.Color(204, 204, 235));
			jtb.setSelected(true);
		} else {
			jtb.setForeground(new java.awt.Color(0, 0, 0));
			jtb.setSelected(false);
		}	
	}

	private void setInternalFrame(JInternalFrame jif, boolean state) throws Exception {
		if (state) {
			jif.setIcon(false);
			jif.setSelected(true);
		} else {
			jif.setIcon(true);
			jif.setSelected(false);
		}
	}

	private void jtbActionPerformed(java.awt.event.ActionEvent evt) {
		JToggleButton jtb = (JToggleButton)evt.getSource();
		int index = vtogglebutton.indexOf(jtb);
		JInternalFrame sjif = (JInternalFrame)vframe.elementAt(index);
		JCheckBoxMenuItem cb = (JCheckBoxMenuItem)vmenu.elementAt(index);
		try {
			if (jtb.isSelected()) {
				setToggleButton(jtb,true);
				cb.setState(true);
				setInternalFrame(sjif,true);
			} else {
				setToggleButton(jtb,false);
				cb.setState(false);
				setInternalFrame(sjif,false);
			}	
		} catch (Exception e) {}
	}

	private void jtbMouseExited(java.awt.event.MouseEvent evt) {
		JToggleButton jtb = (JToggleButton)evt.getSource();
		jtb.setBackground(new java.awt.Color(204, 204, 204));
	}

	private JInternalFrame createInternalFrame(String name) {
		JInternalFrame jif = new JInternalFrame(
				  	name, // title
				  	true,  // resizable
				  	false,  // closable
				  	true,  // maximizable
				  	true); // iconifiable

		jif.addInternalFrameListener(new javax.swing.event.InternalFrameListener() {
			public void internalFrameOpened(javax.swing.event.InternalFrameEvent evt) {}
			public void internalFrameClosing(javax.swing.event.InternalFrameEvent evt) {}
			public void internalFrameClosed(javax.swing.event.InternalFrameEvent evt) {}
			public void internalFrameIconified(javax.swing.event.InternalFrameEvent evt) {}
			public void internalFrameDeiconified(javax.swing.event.InternalFrameEvent evt) {}
			public void internalFrameActivated(javax.swing.event.InternalFrameEvent evt) {
				jifInternalFrameActivated(evt);
			}
			public void internalFrameDeactivated(javax.swing.event.InternalFrameEvent evt) {
				jifInternalFrameDeactivated(evt);
			}
		});
		return jif;
	}

	private void jifInternalFrameDeactivated(javax.swing.event.InternalFrameEvent evt) {
		JInternalFrame sjif = (JInternalFrame)evt.getSource();
		int index = vframe.indexOf(sjif);
		if (index > -1 ) {
			JCheckBoxMenuItem cb = (JCheckBoxMenuItem)vmenu.elementAt(index);
			JToggleButton jt = (JToggleButton)vtogglebutton.elementAt(index);
			try {
				cb.setState(false);
				setToggleButton(jt,false);
			} catch (Exception e) {}
		}
	}

	private void jifInternalFrameActivated(javax.swing.event.InternalFrameEvent evt) {
		JInternalFrame sjif = (JInternalFrame)evt.getSource();
		int index = vframe.indexOf(sjif);
		JCheckBoxMenuItem cb = (JCheckBoxMenuItem)vmenu.elementAt(index);
		JToggleButton jt = (JToggleButton)vtogglebutton.elementAt(index);
		try {
			cb.setState(true);
			setToggleButton(jt,true);

			Object o = vgui.elementAt(index);
			if (o instanceof GuiContainer) {
				GuiContainer gui = (GuiContainer)o;
				gui.refresh();
			} else if (o instanceof GuiMethod) {
				GuiMethod gui = (GuiMethod)o;
				gui.refresh();
			} else if (o instanceof GuiData) {
				GuiData gui = (GuiData)o;
				gui.refresh();
			}
		} catch (Exception e) {}
		
		
	}

	private JMenuItem createMenuItem( JMenu menu, int iType, String sText,
								ImageIcon image, int acceleratorKey,
								String sToolTip ) {
		// Create the item
		JMenuItem menuItem;

		switch( iType ) {
			case ITEM_RADIO:
				menuItem = new JRadioButtonMenuItem();
				break;
			case ITEM_CHECK:
				menuItem = new JCheckBoxMenuItem();
				break;
			default:
				menuItem = new JMenuItem();
				break;
		}

		// Add the item test
		menuItem.setText( sText );

		// Add the optional icon
		if( image != null )
			menuItem.setIcon( image );

		// Add the accelerator key
		if( acceleratorKey > 0 )
			menuItem.setMnemonic( acceleratorKey );

		// Add the optional tool tip text
		if( sToolTip != null )
			menuItem.setToolTipText( sToolTip );

		// Add an action handler TO THIS menu item
		menuItem.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(java.awt.event.ActionEvent evt) {
				JCheckBoxMenuItem cb = (JCheckBoxMenuItem)evt.getSource();
				int index = vmenu.indexOf(cb);
				JInternalFrame sjif = (JInternalFrame)vframe.elementAt(index);
				JToggleButton jt = (JToggleButton)vtogglebutton.elementAt(index);
				try {
				if (cb.getState()) {
					setInternalFrame(sjif,true);
					setToggleButton(jt,true);
				} else {
					cb.setState(false);
					setInternalFrame(sjif,false);
					setToggleButton(jt,false);
				}
				} catch (Exception e) {}
		
			}
		});

		menu.add( menuItem );

		return menuItem;
	}

	class TileAllAction extends AbstractAction {
		public TileAllAction() {
			super("tile");
		}
		public void actionPerformed(ActionEvent e) {
			desktopPane.tile();
		}
	}
	class OpenAllAction extends AbstractAction {
		public OpenAllAction() {
			super("open all");
		}
		public void actionPerformed(ActionEvent e) {
			desktopPane.openAll();
		}
	}
	class CloseAllAction extends AbstractAction {
		public CloseAllAction() {
			super("iconify all");
		}
		public void actionPerformed(ActionEvent e) {
			desktopPane.closeAll();
		}
	}
	class CascadeAction extends AbstractAction {
		public CascadeAction() {
			super("cascade");
		}
		public void actionPerformed(ActionEvent e) {
			desktopPane.cascade();
		}
	}
}

class CustomJInternalFrame extends JInternalFrame {
	private Container c;

	public void refresh() {

	}

}

class CustomDesktopPane extends JDesktopPane { 
	private int xoffset = 20, yoffset = 20, w = 350, h = 300;

	public void closeAll() {
		JInternalFrame[] frames = getAllFrames();

		for(int i=0; i < frames.length; ++i) {
			if(!frames[i].isIcon()) {
				try {
					frames[i].setIcon(true);
				}
				catch(java.beans.PropertyVetoException ex) {
					System.out.println("iconification vetoed!");
				}
			}
		}
	}
	public void openAll() {
		JInternalFrame[] frames = getAllFrames();

		for(int i=0; i < frames.length; ++i) {
			if(frames[i].isIcon()) {
				try {
					frames[i].setIcon(false);
				}
				catch(java.beans.PropertyVetoException ex) {
					System.out.println("restoration vetoed!");
				}
			}
		}
	}
	public void cascade() {
		JInternalFrame[] frames = getAllFrames();
		int x = 0, y = 0;

		for(int i=0; i < frames.length; ++i) {
			if( ! frames[i].isIcon()) {
				frames[i].setBounds(x,y,w,h);
				x += xoffset;
				y += yoffset;
			}
		}
	}

	public void tile() {
            Rectangle viewP = new Rectangle(new Dimension(super.getWidth(), super.getHeight()-30));

            int totalNonIconFrames=0;

            JInternalFrame[] frames = getAllFrames();

            for (int i=0; i < frames.length; i++) {
                 if (!frames[i].isIcon()) {    // don't include iconified frames...
                        totalNonIconFrames++;
                 }
            }

            int curCol = 0;
            int curRow = 0;
            int i=0;

            if (totalNonIconFrames > 0) {

                  // compute number of columns and rows then tile the frames
                  int numCols = (int)Math.sqrt(totalNonIconFrames);

                  int frameWidth = viewP.width/numCols;

                  for (curCol=0; curCol < numCols; curCol++) {

                        int numRows = totalNonIconFrames / numCols;
                        int remainder = totalNonIconFrames % numCols;

                        if ((numCols-curCol) <= remainder) {
                              numRows++; // add an extra row for this guy
                        }

                        int frameHeight = viewP.height/numRows;

                        for (curRow=0; curRow < numRows; curRow++) {
                              while (frames[i].isIcon()) { // find the next visible frame
                                    i++;
                              }

                              frames[i].setBounds(curCol*frameWidth,curRow*frameHeight,
                                    frameWidth,frameHeight);

                              i++;
                        }

                  }

            }

      }
}
