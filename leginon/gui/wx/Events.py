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
eventFactory('Submit Targets')
eventFactory('Targets Submitted')
eventFactory('Manual Updated')

PlayerEventType = wx.NewEventType()
SetImageEventType = wx.NewEventType()
SetTargetsEventType = wx.NewEventType()

EVT_PLAYER = wx.PyEventBinder(PlayerEventType)
EVT_SET_IMAGE = wx.PyEventBinder(SetImageEventType)
EVT_SET_TARGETS = wx.PyEventBinder(SetTargetsEventType)

class PlayerEvent(wx.PyEvent):
	def __init__(self, state):
		wx.PyEvent.__init__(self)
		self.SetEventType(PlayerEventType)
		self.state = state

class SetImageEvent(wx.PyEvent):
	def __init__(self, image, typename=None, stats={}):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetImageEventType)
		self.image = image
		self.typename = typename
		self.stats = stats

class SetTargetsEvent(wx.PyEvent):
	def __init__(self, targets, typename):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetTargetsEventType)
		self.targets = targets
		self.typename = typename

