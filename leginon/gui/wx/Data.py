# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Data.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2004-10-21 22:27:06 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import leginondata
import wx
import wx.lib.intctrl
import wx.lib.masked
import gui.wx.Presets
import gui.wx.Camera

getmap = {
	'string selection': 'GetStringSelection',
	'value': 'GetValue',
	'preset order': 'getValues',
	'dimension': '_getDimension',
	'offset': '_getOffset',
	'binning': '_getBinning',
	'exposure time': '_getExposureTime',
}

setmap = {
	'string selection': 'SetStringSelection',
	'value': 'SetValue',
	'preset order': 'setValues',
	'dimension': '_setDimension',
	'offset': '_setOffset',
	'binning': '_setBinning',
	'exposure time': '_setExposureTime',
}

eventmap = {
	wx.RadioBox: wx.EVT_RADIOBOX,
	wx.Choice: wx.EVT_CHOICE,
	wx.CheckBox: wx.EVT_CHECKBOX,
	wx.TextCtrl: wx.EVT_TEXT,
	wx.lib.intctrl.IntCtrl: wx.EVT_TEXT,
	wx.lib.masked.NumCtrl: wx.lib.masked.EVT_NUM,
	gui.wx.Presets.PresetOrder: gui.wx.Presets.EVT_PRESET_ORDER_CHANGED,
	gui.wx.Presets.EditPresetOrder: gui.wx.Presets.EVT_PRESET_ORDER_CHANGED,
	gui.wx.Presets.PresetChoice: gui.wx.Presets.EVT_PRESET_CHOICE,
	gui.wx.Camera.CameraPanel: gui.wx.Camera.EVT_CONFIGURATION_CHANGED,
	gui.wx.Entry.Entry: gui.wx.Entry.EVT_ENTRY,
	gui.wx.Entry.IntEntry: gui.wx.Entry.EVT_ENTRY,
	gui.wx.Entry.FloatEntry: gui.wx.Entry.EVT_ENTRY,
}

def getWindowPath(window):
	parent = window
	path = ''
	while parent:
		w = parent
		name = w.GetName()
		if name:
			path += name + '.'
		if name == 'fLeginon':
			break
		parent = w.GetParent()
	return path[:-1], w

def getWindowDataClass(window):
	try:
		return getattr(data, 'wx' + window.__class__.__name__ + 'Data')
	except AttributeError:
		raise ValueError('No data class for window class %s'
											% window.__class__.__name__)

def setWindowFromData(window, d):
	for key, value in setmap.items():
		if key in d and d[key] is not None:
			getattr(window, value)(d[key])

def onEvent(evt):
	window = evt.GetEventObject()
	setDBFromWindow(window)
	evt.Skip()

def setWindowFromDB(window):
	path, root = getWindowPath(window)
	dataclass = getWindowDataClass(window)
	if root.session is None:	
		session = None
	else:
		session = leginondata.SessionData(user=root.session['user'])
	initializer = {'path': path, 'session': session}
	instance = dataclass(initializer=initializer)
	try:
		d = root.research(instance, results=1)[0]
	except IndexError:
		return False
	setWindowFromData(window, d)
	return True

def bindWindowToDB(window):
	window.Bind(eventmap[window.__class__], onEvent, window)

def setDataFromWindow(window, d):
	for key, value in getmap.items():
		if key in d:
			d[key] = getattr(window, value)()

def setDBFromWindow(window):
	path, root = getWindowPath(window)
	dataclass = getWindowDataClass(window)
	initializer = {'path': path, 'session': root.session}
	instance = dataclass(initializer=initializer)
	setDataFromWindow(window, instance)
	root.publish(instance, database=True, dbforce=True)

