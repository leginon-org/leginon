import threading
import wx
import wx.lib.scrolledpanel

NodeInitializedEventType = wx.NewEventType()
SetStatusEventType = wx.NewEventType()
SetImageEventType = wx.NewEventType()
SetCorrelationImageEventType = wx.NewEventType()
EVT_NODE_INITIALIZED = wx.PyEventBinder(NodeInitializedEventType)
EVT_SET_STATUS = wx.PyEventBinder(SetStatusEventType)
EVT_SET_IMAGE = wx.PyEventBinder(SetImageEventType)
EVT_SET_CORRELATION_IMAGE = wx.PyEventBinder(SetImageEventType)

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
	def __init__(self, image, statistics={}):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetImageEventType)
		self.image = image
		self.statistics = statistics

class SetCorrelationImageEvent(wx.PyEvent):
	def __init__(self, image, peak):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetCorrelationImageEventType)
		self.image = image
		self.peak

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, *args, **kwargs):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, *args, **kwargs)
		self.node = None
		self.Bind(EVT_NODE_INITIALIZED, self._onNodeInitialized)
		self.Bind(EVT_SET_STATUS, self.onSetStatus)
		self.Bind(EVT_SET_IMAGE, self.onSetImage)
		self.Bind(EVT_SET_CORRELATION_IMAGE, self.onSetCorrelationImage)

	def _onNodeInitialized(self, evt):
		self.node = evt.node
		self.onNodeInitialized()
		evt.event.set()

	def onNodeInitialized(self):
		pass

	def onSetStatus(self, evt):
		self.ststatus.SetLabel(evt.status)

	def onSetImage(self, evt):
		self.imagepanel.setNumericImage(evt.image)

	def onSetCorrelationImage(self, evt):
		self.ipcorrelation.setNumericImage(evt.image)
		self.ipcorrelation.clearTargets()
		self.ipcorrelation.addTarget('Peak', evt.peak[0], evt.peak[1])

	def _getStaticBoxSizer(self, label, *args):
		sbs = wx.StaticBoxSizer(wx.StaticBox(self, -1, label), wx.VERTICAL)
		gbsz = wx.GridBagSizer(5, 5)
		sbs.Add(gbsz, 1, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbs, *args)
		return gbsz

