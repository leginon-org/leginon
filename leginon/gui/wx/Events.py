import wx

class FactoryEvent(wx.PyEvent):
	_eventtype = None
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(self._eventtype)

def eventFactory(name):
	toks = name.split()
	basename = ''
	bindername = ''
	for tok in toks:
		basename += tok
		bindername += tok.upper() + '_'
	eventname = basename + 'Event'
	typename = eventname + 'Type'
	bindername = 'EVT_' + bindername[:-1]
	g = globals()
	g[typename] = wx.NewEventType()
	g[bindername] = wx.PyEventBinder(g[typename])
	g[eventname] = type(eventname, (FactoryEvent,), {'_eventtype': g[typename]})

eventFactory('Acquisition Done')
eventFactory('Atlas Calculated')
eventFactory('Atlas Published')
eventFactory('Calibration Done')
eventFactory('Get Instrument Done')
eventFactory('Set Instrument Done')
eventFactory('Measurement Done')

'''
AcquisitionDoneEventType = wx.NewEventType()
AtlasCreatedEventType = wx.NewEventType()
CalibrationDoneEventType = wx.NewEventType()
GetInstrumentDoneEventType = wx.NewEventType()
SetInstrumentDoneEventType = wx.NewEventType()

EVT_ACQUISITION_DONE = wx.PyEventBinder(AcquisitionDoneEventType)
EVT_ATLAS_CREATED = wx.PyEventBinder(AtlasCreatedEventType)
EVT_CALIBRATION_DONE = wx.PyEventBinder(CalibrationDoneEventType)
EVT_GET_INSTRUMENT_DONE = wx.PyEventBinder(GetInstrumentDoneEventType)
EVT_SET_INSTRUMENT_DONE = wx.PyEventBinder(SetInstrumentDoneEventType)

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

class GetInstrumentDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(GetInstrumentDoneEventType)

class SetInstrumentDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetInstrumentDoneEventType)
'''

