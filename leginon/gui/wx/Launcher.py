import icons
import logging
import launcher
import threading
import wx
import wx.lib.scrolledpanel
import gui.wx.Logging
import gui.wx.MessageLog
import gui.wx.ToolBar

CreateNodeEventType = wx.NewEventType()
DestroyNodeEventType = wx.NewEventType()
CreateNodePanelEventType = wx.NewEventType()
SetOrderEventType = wx.NewEventType()

EVT_CREATE_NODE = wx.PyEventBinder(CreateNodeEventType)
EVT_DESTROY_NODE = wx.PyEventBinder(DestroyNodeEventType)
EVT_CREATE_NODE_PANEL = wx.PyEventBinder(CreateNodePanelEventType)
EVT_SET_ORDER = wx.PyEventBinder(SetOrderEventType)

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

class SetOrderEvent(wx.PyCommandEvent):
	def __init__(self, source, order):
		wx.PyCommandEvent.__init__(self, SetOrderEventType, source.GetId())
		self.SetEventObject(source)
		self.order = order

class App(wx.App):
	def __init__(self, name, **kwargs):
		self.name = name
		self.kwargs = kwargs
		wx.App.__init__(self, 0)

	def OnInit(self):
		self.launcher = launcher.Launcher(self.name, **self.kwargs)
		frame = Frame(self.launcher)
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
		wx.Frame.__init__(self, None, -1, 'Leginon', size=(750, 750))

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

		self.toolbar = gui.wx.ToolBar.ToolBar(self)
		self.toolbar.Show(True)
		self.SetToolBar(self.toolbar)

		# status bar
		self.statusbar = StatusBar(self)
		self.SetStatusBar(self.statusbar)

		self.panel = Panel(self, launcher)

		self.Bind(wx.EVT_SIZE, self.onSize)

	def onSize(self, evt):
		self.panel.SetSize(self.GetClientSize())
		self.panel.Layout()
		evt.Skip()

	def onExit(self, evt):
		self.launcher.exit()
		self.Close()

	def onMenuLogging(self, evt):
		dialog = gui.wx.Logging.LoggingConfigurationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class ListCtrlPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.swselect = wx.SashLayoutWindow(self, -1, style=wx.NO_BORDER)
		self.swselect.SetDefaultSize((100, -1))
		self.swselect.SetOrientation(wx.LAYOUT_VERTICAL)
		self.swselect.SetAlignment(wx.LAYOUT_LEFT)
		self.swselect.SetSashVisible(wx.SASH_RIGHT, True)
		self.swselect.SetExtraBorderSize(5)

		self.swmessage = wx.SashLayoutWindow(self, -1, style=wx.NO_BORDER)
		self.swmessage.SetDefaultSize((-1, 100))
		self.swmessage.SetOrientation(wx.LAYOUT_HORIZONTAL)
		self.swmessage.SetAlignment(wx.LAYOUT_TOP)
		self.swmessage.SetSashVisible(wx.SASH_BOTTOM, True)
		#self.swmessage.SetExtraBorderSize(5)

		self.data = 0
		self.datatextmap = {}
		self.listctrl = wx.ListCtrl(self.swselect, -1,
																style=wx.LC_REPORT|wx.LC_NO_HEADER)
		self.listctrl.InsertColumn(0, 'Panels')

		self.defaultpanel = wx.lib.scrolledpanel.ScrolledPanel(self, -1)
		self.panel = self.defaultpanel
		self.panelmap = {}

		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected, self.listctrl)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemDeselected, self.listctrl)
		self.Bind(wx.EVT_SASH_DRAGGED, self.onSashDragged)

	def addPanel(self, panel, label, imageindex=0):
		panel.Show(False)
		self.panelmap[label] = panel
		index = self.listctrl.GetItemCount()
		index = self.listctrl.InsertImageStringItem(index, label, imageindex)
		self.listctrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.listctrl.SetItemData(index, self.data)
		self.datatextmap[self.data] = label
		self.data += 1

	def removePanel(self, panel):
		for text, p in self.panelmap.items():
			if p is panel:
				break
		index = self.listctrl.FindItem(0, text, False)
		item = self.listctrl.GetItem(index)
		state = item.GetState()
		if self.listctrl.GetItemState(index, wx.LIST_STATE_SELECTED):
			self.listctrl.SetItemState(index, wx.LIST_STATE_SELECTED, 0)
			self._setPanel(self.defaultpanel)
		self.listctrl.DeleteItem(index)
		del self.panelmap[text]
		if hasattr(panel, 'toolbar'):
			panel.toolbar.Destroy()
		if hasattr(panel, 'messagelog'):
			panel.messagelog.Destroy()
		panel.Destroy()

	def _onSetPanel(self, panel):
		pass

	def _setPanel(self, panel):
		self.Freeze()
		self.panel.Show(False)
		self._onSetPanel(panel)
		self.panel = panel
		self.panel.Show(True)
		self.Layout()
		if hasattr(panel, 'messagelog'):
			panel.messagelog.Layout()
		self.Thaw()

	def onItemSelected(self, evt):
		self._setPanel(self.panelmap[evt.GetItem().GetText()])

	def onItemDeselected(self, evt):
		self._setPanel(self.defaultpanel)

	def onSashDragged(self, evt):
		if evt.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
			return
		if evt.GetEventObject() is self.swselect:
			self.swselect.SetDefaultSize((evt.GetDragRect().width, -1))
		if evt.GetEventObject() is self.swmessage:
			self.swmessage.SetDefaultSize((-1, evt.GetDragRect().height))
		self.Layout()

#	def onSize(self, evt):
#		self.Layout()
#		evt.Skip()

	def Layout(self):
		wx.LayoutAlgorithm().LayoutWindow(self, self.panel)

class Panel(ListCtrlPanel):
	def __init__(self, parent, launcher=None):
		ListCtrlPanel.__init__(self, parent, -1, style=wx.NO_BORDER)

		self.order = []

		if launcher is not None:
			self.setLauncher(launcher)

		self.defaultcolor = (self.listctrl.GetForegroundColour(),
													self.listctrl.GetBackgroundColour())
		self.statuscolors = {
			'INFO': (wx.BLUE, self.defaultcolor[1]),
			'WARNING': (wx.Color(225, 180, 0), self.defaultcolor[1]),
			'ERROR': (wx.RED, self.defaultcolor[1]),
			'PROCESSING': (wx.GREEN, self.defaultcolor[1]),
		}
		self.initializeImageList()

		self.Bind(gui.wx.MessageLog.EVT_STATUS_UPDATED, self.onStatusUpdated)
		self.Bind(EVT_SET_ORDER, self.onSetOrder)
		self.swmessage.Bind(wx.EVT_SIZE, self.onSize)

	def onSize(self, evt=None):
		if hasattr(self.panel, 'messagelog'):
			size = self.swmessage.GetClientSize()
			self.panel.messagelog.SetSize(size - (10, 10))

	def _onSetPanel(self, panel):
		ListCtrlPanel._onSetPanel(self, panel)
		tb = self.GetParent().GetToolBar()
		tb.Show(False)
		if hasattr(panel, 'toolbar'):
			tb = panel.toolbar
		else:
			tb = self.GetParent().toolbar
		self.GetParent().SetToolBar(tb)
		tb.Show(True)
		tb.SetSize((self.GetParent().GetClientSize().width, -1))
		if hasattr(self.panel, 'messagelog'):
			self.panel.messagelog.Show(False)
		if hasattr(panel, 'messagelog'):
			panel.messagelog.Show(True)
			size = self.swmessage.GetClientSize()
			panel.messagelog.SetPosition((5, 5))
			panel.messagelog.SetSize(size - (10, 10))

	def onStatusUpdated(self, evt):
		evtobj = evt.GetEventObject()
		for name, panel in self.panelmap.items():
			if panel is evtobj:
				item = self.listctrl.FindItem(-1, name, False)
				try:
					color = self.statuscolors[evt.level]
				except KeyError:
					color = self.defaultcolor
				self.listctrl.SetItemBackgroundColour(item, color[1])
				self.listctrl.SetItemTextColour(item, color[0])
				return

	def sortOrder(self, x, y):
		x = self.datatextmap[x]
		y = self.datatextmap[y]
		try:
			i = self.order.index(x)
		except ValueError:
			i = None
		try:
			j = self.order.index(y)
		except ValueError:
			j = None
		if i == j:
			return 0
		if i is None:
			return -1
		if j is None:
			return 1
		if i > j:
			return 1
		else:
			return -1

	def onSetOrder(self, evt):
		self.order = evt.order
		self.listctrl.SortItems(self.sortOrder)

	def setOrder(self, order):
		evt = SetOrderEvent(self, order)
		self.GetEventHandler().AddPendingEvent(evt)

	def setLauncher(self, launcher):
		self.launcher = launcher
		self.Bind(EVT_CREATE_NODE, self.onCreateNode)
		self.Bind(EVT_DESTROY_NODE, self.onDestroyNode)
		self.Bind(EVT_CREATE_NODE_PANEL, self.onCreateNodePanel)
		launcher.panel = self

	def addIcon(self, filename):
		iconpath = icons.getPath(filename + '.png')
		image = wx.Image(iconpath)
		bitmap = wx.BitmapFromImage(image)
		self.iconmap[filename] = self.imagelist.Add(bitmap)

	def initializeImageList(self):
		self.iconmap = {}
		self.imagelist = wx.ImageList(16, 16)
		self.listctrl.AssignImageList(self.imagelist, wx.IMAGE_LIST_SMALL)

	def addNode(self, n):
		panel = n.panel
		if panel is None:
			return
		label = n.name

		if hasattr(panel, 'icon'):
			icon = panel.icon
		else:
			icon = 'node'

		if icon not in self.iconmap:
			self.addIcon(icon)
		i = self.iconmap[icon]

		self.addPanel(panel, label, i)
		self.listctrl.SortItems(self.sortOrder)

	def removeNode(self, n):
		if not hasattr(n, 'panel') or n.panel is None:
			return
		self.removePanel(n.panel)

	def onCreateNode(self, evt):
		self.addNode(evt.node)

	def onDestroyNode(self, evt):
		if evt.node is not None:
			self.removeNode(evt.node)

	def onCreateNodePanel(self, evt):
		self.Freeze()
		evt.panel = evt.panelclass(self, evt.name)
		evt.panel.Show(False)
		self.Thaw()
		evt.event.set()

	def Layout(self):
		ListCtrlPanel.Layout(self)
		tb = self.GetParent().GetToolBar()
		if hasattr(tb, 'spacer'):
			tb.spacer.SetSize((self.swselect.GetSize().width, -1))
			tb.Realize()
	
	def getToolBar(self):
		parent = self.GetParent()
		parent.Freeze()
		toolbar = gui.wx.ToolBar.ToolBar(parent)
		toolbar.Show(False)
		parent.Thaw()
		return toolbar

def getStatusIcon(image, color):
	bitmap = wx.BitmapFromImage(image)
	dc = wx.MemoryDC()
	dc.SelectObject(bitmap)
	dc.BeginDrawing()
	dc.SetPen(wx.BLACK_PEN)
	dc.SetBrush(wx.Brush(color))
	dc.DrawRectangle(0, 0, 5, 5)
	dc.EndDrawing()
	return bitmap

