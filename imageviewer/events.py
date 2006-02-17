import wx

DisplayCrosshairsEventType = wx.NewEventType()
DisplayMagnifierEventType = wx.NewEventType()
FitToPageEventType = wx.NewEventType()
SetNumarrayEventType = wx.NewEventType()
ScaleSizeEventType = wx.NewEventType()
ScaleValuesEventType = wx.NewEventType()

EVT_DISPLAY_CROSSHAIRS = wx.PyEventBinder(DisplayCrosshairsEventType)
EVT_DISPLAY_MAGNIFIER = wx.PyEventBinder(DisplayMagnifierEventType)
EVT_FIT_TO_PAGE = wx.PyEventBinder(FitToPageEventType)
EVT_SET_NUMARRAY = wx.PyEventBinder(SetNumarrayEventType)
EVT_SCALE_SIZE = wx.PyEventBinder(ScaleSizeEventType)
EVT_SCALE_VALUES = wx.PyEventBinder(ScaleValuesEventType)

class DisplayCrosshairsEvent(wx.PyCommandEvent):
    def __init__(self, source, display):
        wx.PyCommandEvent.__init__(self, DisplayCrosshairsEventType,
                                    source.GetId())
        self.SetEventObject(source)
        self.display = display

class DisplayMagnifierEvent(wx.PyCommandEvent):
    def __init__(self, source, display):
        wx.PyCommandEvent.__init__(self, DisplayMagnifierEventType,
                                    source.GetId())
        self.SetEventObject(source)
        self.display = display

class FitToPageEvent(wx.PyCommandEvent):
    def __init__(self, source):
        wx.PyCommandEvent.__init__(self, FitToPageEventType, source.GetId())
        self.SetEventObject(source)

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

