import wx

AcquisitionDoneEventType = wx.NewEventType()
AtlasCreatedEventType = wx.NewEventType()
CalibrationDoneEventType = wx.NewEventType()

EVT_ACQUISITION_DONE = wx.PyEventBinder(AcquisitionDoneEventType)
EVT_ATLAS_CREATED = wx.PyEventBinder(AtlasCreatedEventType)
EVT_CALIBRATION_DONE = wx.PyEventBinder(CalibrationDoneEventType)

class AcquisitionDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AcquisitionDoneEventType)

class AtlasCreatedEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AtlasCreatedEventType)

class CalibrationDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(CalibrationDoneEventType)

