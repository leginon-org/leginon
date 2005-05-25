import wx

UpdatePluginRegionEventType = wx.NewEventType()
SetNumarrayEventType = wx.NewEventType()
ScaleSizeEventType = wx.NewEventType()
ScaleValuesEventType = wx.NewEventType()
FitToPageEventType = wx.NewEventType()
DisplayCrosshairsEventType = wx.NewEventType()

EVT_UPDATE_PLUGIN_REGION = wx.PyEventBinder(UpdatePluginRegionEventType)
EVT_SET_NUMARRAY = wx.PyEventBinder(SetNumarrayEventType)
EVT_SCALE_SIZE = wx.PyEventBinder(ScaleSizeEventType)
EVT_SCALE_VALUES = wx.PyEventBinder(ScaleValuesEventType)
EVT_FIT_TO_PAGE = wx.PyEventBinder(FitToPageEventType)
EVT_DISPLAY_CROSSHAIRS = wx.PyEventBinder(DisplayCrosshairsEventType)

class UpdatePluginRegionEvent(wx.PyCommandEvent):
	def __init__(self, source, oldregion, copyregion=None):
		sourceid = source.GetId()
		wx.PyCommandEvent.__init__(self, UpdatePluginRegionEventType, sourceid)
		self.SetEventObject(source)
		self.plugin = source
		self.oldregion = oldregion
		self.copyregion = copyregion

class SetNumarrayEvent(wx.PyCommandEvent):
	def __init__(self, source, array):
		wx.PyCommandEvent.__init__(self, SetNumarrayEventType, source.GetId())
		self.SetEventObject(source)
		self.array = array

	def GetNumarray(self):
		return self.array

class ScaleSizeEvent(wx.PyCommandEvent):
	def __init__(self, source, scale):
		wx.PyCommandEvent.__init__(self, ScaleSizeEventType, source.GetId())
		self.SetEventObject(source)
		self.scale = scale

	def GetScale(self):
		return self.scale

class ScaleValuesEvent(wx.PyCommandEvent):
	def __init__(self, source, valuerange):
		wx.PyCommandEvent.__init__(self, ScaleValuesEventType, source.GetId())
		self.SetEventObject(source)
		self.valuerange = valuerange

	def GetValueRange(self):
		return self.valuerange

class FitToPageEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, FitToPageEventType, source.GetId())
		self.SetEventObject(source)

class DisplayCrosshairsEvent(wx.PyCommandEvent):
	def __init__(self, source, display):
		wx.PyCommandEvent.__init__(self, DisplayCrosshairsEventType, source.GetId())
		self.SetEventObject(source)
		self.display = display

