import wx

SetNumarrayEventType = wx.NewEventType()
ScaleSizeEventType = wx.NewEventType()
ScaleValuesEventType = wx.NewEventType()
FitToPageEventType = wx.NewEventType()

EVT_SET_NUMARRAY = wx.PyEventBinder(SetNumarrayEventType)
EVT_SCALE_SIZE = wx.PyEventBinder(ScaleSizeEventType)
EVT_SCALE_VALUES = wx.PyEventBinder(ScaleValuesEventType)
EVT_FIT_TO_PAGE = wx.PyEventBinder(FitToPageEventType)

class SetNumarrayEvent(wx.PyCommandEvent):
	def __init__(self, source, array):
		wx.PyCommandEvent.__init__(self, SetNumarrayEventType, source.GetId())
		self.SetEventObject(source)
		self.array = array

	def GetNumarray(self):
		return self.array

class ScaleSizeEvent(wx.PyCommandEvent):
	def __init__(self, source, width, height):
		wx.PyCommandEvent.__init__(self, ScaleSizeEventType, source.GetId())
		self.SetEventObject(source)
		self.width = width
		self.height = height

	def GetWidth(self):
		return self.width

	def GetHeight(self):
		return self.height

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
