import logging
import launcher
import threading
import wx
import wx.lib.scrolledpanel
import wxLogging

CreateNodeEventType = wx.NewEventType()
DestroyNodeEventType = wx.NewEventType()
CreateNodePanelEventType = wx.NewEventType()
EVT_CREATE_NODE = wx.PyEventBinder(CreateNodeEventType)
EVT_DESTROY_NODE = wx.PyEventBinder(DestroyNodeEventType)
EVT_CREATE_NODE_PANEL = wx.PyEventBinder(CreateNodePanelEventType)

class CreateNodeEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(CreateNodeEventType)
		self.node = node

class DestroyNodeEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(DestroyNodeEventType)
		self.node = node

class CreateNodePanelEvent(wx.PyEvent):
	def __init__(self, panelclass, name):
		wx.PyEvent.__init__(self)
		self.SetEventType(CreateNodePanelEventType)
		self.panelclass = panelclass
		self.name = name
		self.event = threading.Event()
		self.panel = None

class App(wx.App):
	def __init__(self, name, **kwargs):
		self.name = name
		self.kwargs = kwargs
		wx.App.__init__(self, 0)

	def OnInit(self):
		# seperate thread
		self.launcher = launcher.Launcher(self.name, **self.kwargs)
		frame = Frame(self.launcher)
		launcher.panel = frame.panel
		self.launcher.start()
		self.SetTopWindow(frame)
		frame.Show(True)
		return True

	def OnExit(self):
		self.launcher.exit()

class StatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent, -1)

class Frame(wx.Frame):
	def __init__(self, launcher):
		self.launcher = launcher
		wx.Frame.__init__(self, None, -1, 'Leginon', size=(750, 750),
											name='fLeginon')

		# menu
		self.menubar = wx.MenuBar()

		# file menu
		filemenu = wx.Menu()
		exit = wx.MenuItem(filemenu, -1, 'E&xit')
		self.Bind(wx.EVT_MENU, self.onExit, exit)
		filemenu.AppendItem(exit)
		self.menubar.Append(filemenu, '&File')

		# settings menu
		self.settingsmenu = wx.Menu()
		self.loggingmenuitem = wx.MenuItem(self.settingsmenu, -1, '&Logging')
		self.Bind(wx.EVT_MENU, self.onMenuLogging, self.loggingmenuitem)
		self.settingsmenu.AppendItem(self.loggingmenuitem)
		self.menubar.Append(self.settingsmenu, '&Settings')

		self.SetMenuBar(self.menubar)

		# status bar
		self.statusbar = StatusBar(self)
		self.SetStatusBar(self.statusbar)

		self.panel = Panel(self, launcher)

	def onExit(self, evt):
		self.launcher.exit()
		self.Close()

	def onMenuLogging(self, evt):
		dialog = wxLogging.LoggingConfigurationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class ListCtrlPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sashwindow = wx.SashLayoutWindow(self, -1, style=wx.NO_BORDER)
		self.sashwindow.SetDefaultSize((100, -1))
		self.sashwindow.SetOrientation(wx.LAYOUT_VERTICAL)
		self.sashwindow.SetAlignment(wx.LAYOUT_LEFT)
		self.sashwindow.SetSashVisible(wx.SASH_RIGHT, True)
		self.sashwindow.SetExtraBorderSize(5)

		self.listctrl = wx.ListCtrl(self.sashwindow, -1,
																style=wx.LC_REPORT|wx.LC_NO_HEADER)
		self.listctrl.InsertColumn(0, 'Panels')

		self.defaultpanel = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
		self.panel = self.defaultpanel
		self.panelmap = {}

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.listctrl)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemDeselected, self.listctrl)
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_SASH_DRAGGED, self.onSashDragged, self.sashwindow)

	def addPanel(self, panel, label, imageindex=0):
		panel.Show(False)
		self.panelmap[label] = panel
		index = self.listctrl.GetItemCount()
		self.listctrl.InsertImageStringItem(index, label, imageindex)

	def removePanel(self, panel):
		for text, p in self.panelmap.items():
			if p is panel:
				break
		itemid = self.listctrl.FindItem(0, text, False)
		item = self.listctrl.GetItem(itemid)
		state = item.GetState()
		if state & wx.LIST_STATE_SELECTED:
			state &= not wx.LIST_STATE_SELECTED
			item.SetState(state)
			self._setPanel(self.defaultpanel)
		self.listctrl.DeleteItem(itemid)
		del self.panelmap[text]
		panel.Destroy()

	def _setPanel(self, panel):
		self.Freeze()

		self.panel.Show(False)

		self.panel = panel
		self.panel.Show(True)

		wx.LayoutAlgorithm().LayoutWindow(self, self.panel)

		self.Thaw()

	def onItemSelected(self, evt):
		self._setPanel(self.panelmap[evt.GetItem().GetText()])

	def onItemDeselected(self, evt):
		self._setPanel(self.defaultpanel)

	def onSashDragged(self, evt):
		if evt.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
			return
		self.sashwindow.SetDefaultSize((evt.GetDragRect().width, -1))
		wx.LayoutAlgorithm().LayoutWindow(self, self.panel)

	def onSize(self, evt):
		wx.LayoutAlgorithm().LayoutWindow(self, self.panel)

import os, sys
import node, acquisition, targetfinder

iconmap = [('acquisition', acquisition.Acquisition),
						('targetfinder', targetfinder.TargetFinder),
						('node', node.Node)]

class Panel(ListCtrlPanel):
	def __init__(self, parent, launcher):
		self.launcher = launcher
		ListCtrlPanel.__init__(self, parent, -1, style=wx.NO_BORDER,
														name='pLauncher')

		self.initializeImageList()

		self.Bind(EVT_CREATE_NODE, self.onCreateNode)
		self.Bind(EVT_DESTROY_NODE, self.onDestroyNode)
		self.Bind(EVT_CREATE_NODE_PANEL, self.onCreateNodePanel)

	def initializeImageList(self):
		imagelist = wx.ImageList(16, 16)
		for filename, nodeclass in iconmap:
			iconpath = os.path.join(sys.path[0], 'icons', filename + '.png')
			image = wx.Image(iconpath)
			bitmap = wx.BitmapFromImage(image)
			imagelist.Add(bitmap)
		self.listctrl.AssignImageList(imagelist, wx.IMAGE_LIST_SMALL)

	def addNode(self, n):
		if not hasattr(n, 'panel'):
			return
		panel = n.panel
		label = n.name
		for i, icon in enumerate(iconmap):
			if isinstance(n, icon[1]):
				break
		self.addPanel(panel, label, i)

	def removeNode(self, n):
		if not hasattr(n, 'panel'):
			return
		self.removePanel(n.panel)

	def onCreateNode(self, evt):
		self.addNode(evt.node)

	def onDestroyNode(self, evt):
		self.removeNode(evt.node)

	def onCreateNodePanel(self, evt):
		self.Freeze()
		evt.panel = evt.panelclass(self, evt.name)
		evt.panel.Show(False)
		self.Thaw()
		evt.event.set()

