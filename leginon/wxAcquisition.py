import wx

'''
CreateNodeEventType = wx.NewEventType()
EVT_CREATE_NODE = wx.PyEventBinder(CreateNodeEventType)

class CreateNodeEvent(wx.PyEvent):
	def __init__(self, node):
		wx.PyEvent.__init__(self)
		self.SetEventType(CreateNodeEventType)
		self.node = node
'''

class Panel(wx.Panel):
	def __init__(self, parent, node):
		self.node = node
		wx.Panel.__init__(self, parent, -1)

		self.SetBackgroundColour(wx.RED)

		'''
		self.sizer = wx.GridBagSizer(0, 0)

		self.sizer.Add(wx.StaticBox(self, -1, 'Status'), (0, 0), (1, 2))
		self.sizer.Add(wx.StaticBox(self, -1, 'Controls'), (1, 0), (1, 1))
		self.sizer.Add(wx.StaticBox(self, -1, 'Settings'), (2, 0), (1, 1))
		self.sizer.Add(wx.StaticBox(self, -1, 'Image'), (1, 1), (2, 1))

		self.SetSizerAndFit(self.sizer)
		'''

