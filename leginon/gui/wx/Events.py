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

PlayerEventType = wx.NewEventType()

EVT_PLAYER = wx.PyEventBinder(PlayerEventType)

class PlayerEvent(wx.PyEvent):
	def __init__(self, state):
		wx.PyEvent.__init__(self)
		self.SetEventType(PlayerEventType)
		self.state = state

