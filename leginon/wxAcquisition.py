import wx
import wx.lib.scrolledpanel

'''
CreateNodeEventType = wx.NewEventType()
EVT_CREATE_NODE = wx.PyEventBinder(CreateNodeEventType)

class CreateNodeEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(CreateNodeEventType)
		self.node = node
'''

class Panel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1)

		self.sizer = wx.GridBagSizer(5, 5)

		self.sizer.Add(wx.StaticBox(self, -1, 'Status'), (0, 0), (1, 2),
										wx.EXPAND)
		self.sizer.Add(wx.StaticBox(self, -1, 'Controls'), (1, 0), (1, 1),
										wx.EXPAND)
		self.sizer.Add(wx.StaticBox(self, -1, 'Settings'), (2, 0), (1, 1),
										wx.EXPAND)
		self.sizer.Add(wx.StaticBox(self, -1, 'Image'), (1, 1), (2, 1),
										wx.EXPAND)

		self.SetSizerAndFit(self.sizer)

