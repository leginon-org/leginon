import icons
import threading
import wx
import wx.lib.scrolledpanel
import gui.wx.MessageLog
import gui.wx.ToolBar

NodeInitializedEventType = wx.NewEventType()
SetImageEventType = wx.NewEventType()
SetTargetsEventType = wx.NewEventType()

EVT_NODE_INITIALIZED = wx.PyEventBinder(NodeInitializedEventType)
EVT_SET_IMAGE = wx.PyEventBinder(SetImageEventType)
EVT_SET_TARGETS = wx.PyEventBinder(SetTargetsEventType)

class NodeInitializedEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(NodeInitializedEventType)
		self.node = node
		self.event = threading.Event()

class SetImageEvent(wx.PyEvent):
	def __init__(self, image, typename=None, statistics={}):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetImageEventType)
		self.image = image
		self.typename = typename
		self.statistics = statistics

class SetTargetsEvent(wx.PyEvent):
	def __init__(self, targets, typename):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetTargetsEventType)
		self.targets = targets
		self.typename = typename

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent, id, tools=None, **kwargs):

		self.node = None
		if 'style' in kwargs:
			kwargs['style'] |= wx.SIMPLE_BORDER
		else:
			kwargs['style'] = wx.SIMPLE_BORDER
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id, **kwargs)

		self.toolbar = parent.getToolBar()
		self.toolbar.Show(False)

		self.szmain = wx.GridBagSizer(5, 5)

		self.messagelog = gui.wx.MessageLog.MessageLog(self)
		self.szmain.Add(self.messagelog, (0, 0), (1, 2), wx.EXPAND|wx.ALL, 3)

		self.Bind(EVT_NODE_INITIALIZED, self._onNodeInitialized)
		self.Bind(EVT_SET_IMAGE, self.onSetImage)
		self.Bind(EVT_SET_TARGETS, self.onSetTargets)
		self.Bind(gui.wx.MessageLog.EVT_ADD_MESSAGE, self.onAddMessage)

	def onAddMessage(self, evt):
		self.messagelog.addMessage(evt.level, evt.message)

	def _onNodeInitialized(self, evt):
		self.node = evt.node
		self.onNodeInitialized()
		evt.event.set()

	def onNodeInitialized(self):
		pass

	def onSetImage(self, evt):
		if evt.typename is None:
			self.imagepanel.setImage(evt.image)
		else:
			self.imagepanel.setImageType(evt.image, evt.typename)

	def onSetTargets(self, evt):
		self.imagepanel.setTargets(evt.typname, evt.targets)

	def _getStaticBoxSizer(self, label, *args):
		sbs = wx.StaticBoxSizer(wx.StaticBox(self, -1, label), wx.VERTICAL)
		gbsz = wx.GridBagSizer(5, 5)
		sbs.Add(gbsz, 1, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbs, *args)
		return gbsz

