import threading
import wx
import wx.lib.scrolledpanel

NodeInitializedEventType = wx.NewEventType()
SetStatusEventType = wx.NewEventType()
SetImageEventType = wx.NewEventType()
EVT_NODE_INITIALIZED = wx.PyEventBinder(NodeInitializedEventType)
EVT_SET_STATUS = wx.PyEventBinder(SetStatusEventType)
EVT_SET_IMAGE = wx.PyEventBinder(SetImageEventType)

class NodeInitializedEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(NodeInitializedEventType)
		self.node = node
		self.event = threading.Event()

class SetStatusEvent(wx.PyEvent):
	def __init__(self, status):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetStatusEventType)
		self.status = status

class SetImageEvent(wx.PyEvent):
	def __init__(self, image):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetImageEventType)
		self.image = image

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def _getStaticBoxSizer(self, label, *args):
		sbs = wx.StaticBoxSizer(wx.StaticBox(self, -1, label), wx.VERTICAL)
		gbsz = wx.GridBagSizer(5, 5)
		sbs.Add(gbsz, 1, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbs, *args)
		return gbsz

