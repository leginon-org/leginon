import data
import wx
import wx.lib.intctrl

def getWindowPath(window):
	parent = window
	path = ''
	while parent:
		w = parent
		path += w.GetName() + '.'
		parent = w.GetParent()
	return path[:-1], w

def getWindowDataClass(window):
	try:
		return getattr(data, 'wx' + window.__class__.__name__ + 'Data')
	except AttributeError:
		raise ValueError('No data class for window class')

setmap = {'string selection': 'SetStringSelection',
						'value': 'SetValue'}

def setWindowFromData(window, d):
	for key, value in setmap.items():
		if key in d and d[key] is not None:
			getattr(window, value)(d[key])

eventmap = {wx.RadioBox: wx.EVT_RADIOBOX,
						wx.Choice: wx.EVT_CHOICE,
						wx.CheckBox: wx.EVT_CHECKBOX,
						wx.lib.intctrl.IntCtrl: wx.EVT_TEXT}

def onEvent(evt):
	window = evt.GetEventObject()
	#print window.GetName()
	setDBFromWindow(window)
	evt.Skip()

def setWindowFromDB(window):
	path, root = getWindowPath(window)
	dataclass = getWindowDataClass(window)
	if root.session is None:	
		session = None
	else:
		session = data.SessionData(user=root.session['user'])
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

getmap = {'string selection': 'GetStringSelection',
						'value': 'GetValue'}

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

