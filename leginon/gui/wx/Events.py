import wx

AcquisitionDoneEventType = wx.NewEventType()
AtlasCreatedEventType = wx.NewEventType()

EVT_ACQUISITION_DONE = wx.PyEventBinder(AcquisitionDoneEventType)
EVT_ATLAS_CREATED = wx.PyEventBinder(AtlasCreatedEventType)

class AcquisitionDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AcquisitionDoneEventType)

class AtlasCreatedEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AtlasCreatedEventType)

