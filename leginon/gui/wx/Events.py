# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Events.py,v $
# $Revision: 1.27 $
# $Name: not supported by cvs2svn $
# $Date: 2006-04-11 05:25:48 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx

class FactoryEvent(wx.PyEvent):
	_eventtype = None
	def __init__(self, **kwargs):
		wx.PyEvent.__init__(self)
		self.SetEventType(self._eventtype)
		for name in self._attributes:
			if name in kwargs:
				value = kwargs[name]
			else:
				value = None
			setattr(self, name, value)

class FactoryCommandEvent(wx.PyCommandEvent):
	_eventtype = None
	def __init__(self, source, **kwargs):
		wx.PyCommandEvent.__init__(self, self._eventtype, source.GetId())
		self.SetEventObject(source)
		for name in self._attributes:
			if name in kwargs:
				value = kwargs[name]
			else:
				value = None
			setattr(self, name, value)

def eventFactory(name, attributes=[], command=False):
	toks = name.split()
	basename = ''
	bindername = ''
	for tok in toks:
		basename += tok
		bindername += tok.upper() + '_'
	eventname = basename + 'Event'
	if command:
		bases = (FactoryCommandEvent,)
	else:
		bases = (FactoryEvent,)
	typename = eventname + 'Type'
	bindername = 'EVT_' + bindername[:-1]
	g = globals()
	g[typename] = wx.NewEventType()
	g[bindername] = wx.PyEventBinder(g[typename])
	g[eventname] = type(eventname, bases, {'_eventtype': g[typename],
																					'_attributes': attributes})

eventFactory('Acquisition Done')
eventFactory('Atlas Calculated')
eventFactory('Atlas Published')
eventFactory('Calibration Done')
eventFactory('Get Instrument Done')
eventFactory('Set Instrument Done')
eventFactory('Get BeamTilt Done')
eventFactory('Set BeamTilt Done')
eventFactory('Measurement Done')
eventFactory('Coma Measurement Done')
eventFactory('Submit Targets')
eventFactory('Targets Submitted')
eventFactory('Enable Play Button')
eventFactory('Manual Updated')
eventFactory('Update Drawing')
eventFactory('Found Targets')
eventFactory('Get Atlases Done')
eventFactory('Set Atlas Done')
eventFactory('Get Magnifications Done')
eventFactory('Refresh Done')
eventFactory('Grid Queue Empty')
eventFactory('Clear Grid')
eventFactory('Grid Inserted')
eventFactory('Extracting Grid')
eventFactory('Edit Matrix', attributes=['calibrationdata'])
eventFactory('Edit Focus Calibration', attributes=[
	'tem',
	'ccd_camera',
	'high_tension',
	'magnification',
	'parameter',
	'matrix',
	'rotation_center',
	'eucentric_focus',
])
eventFactory('Add TEM', attributes=['name'], command=True)
eventFactory('Remove TEM', attributes=['name'], command=True)
eventFactory('Set TEM', attributes=['name'], command=True)
eventFactory('Set TEMs', attributes=['names'], command=True)
eventFactory('TEM Change', attributes=['name'], command=True)
eventFactory('Add CCDCamera', attributes=['name'], command=True)
eventFactory('Remove CCDCamera', attributes=['name'], command=True)
eventFactory('Set CCDCamera', attributes=['name'], command=True)
eventFactory('Set CCDCameras', attributes=['names'], command=True)
eventFactory('CCDCamera Change', attributes=['name'], command=True)

PlayerEventType = wx.NewEventType()
SetImageEventType = wx.NewEventType()
SetTargetsEventType = wx.NewEventType()
StatusUpdatedEventType = wx.NewEventType()

EVT_PLAYER = wx.PyEventBinder(PlayerEventType)
EVT_SET_IMAGE = wx.PyEventBinder(SetImageEventType)
EVT_SET_TARGETS = wx.PyEventBinder(SetTargetsEventType)
EVT_STATUS_UPDATED = wx.PyEventBinder(StatusUpdatedEventType)

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

class StatusUpdatedEvent(wx.PyCommandEvent):
	def __init__(self, source, level, status=None):
		wx.PyCommandEvent.__init__(self, StatusUpdatedEventType, source.GetId())
		self.SetEventObject(source)
		self.level = level
		self.status = status

