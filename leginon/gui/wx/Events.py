import wx

AcquisitionDoneEventType = wx.NewEventType()

EVT_ACQUISITION_DONE = wx.PyEventBinder(AcquisitionDoneEventType)

class AcquisitionDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AcquisitionDoneEventType)

