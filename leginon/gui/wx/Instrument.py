import wx
from gui.wx.Entry import Entry, IntEntry, FloatEntry, EVT_ENTRY
import gui.wx.Node

def setControl(control, value):
	testr = '%s value must be of type %s (is type %s)'
	vestr = 'Invalid value %s for instance of %s'
	controlname = control.__class__.__name__
	valuetypename = value.__class__.__name__

	if isinstance(control, wx.StaticText):

		try:
			value = str(value)
		except:
			typename = str.__name__
			raise TypeError(testr % (controlname, typename, valuetypename))

		control.SetLabel(value)

	if isinstance(control, (Entry, wx.TextCtrl, wx.CheckBox)):

		if isinstance(control, Entry):
			pass
		elif isinstance(control, wx.TextCtrl) and type(value) is not str:
			typename = str.__name__
			raise TypeError(testr % (controlname, typename, valuetypename))
		elif isinstance(control, wx.CheckBox) and type(value) is not bool:
			typename = bool.__name__
			raise TypeError(testr % (controlname, typename, valuetypename))

		try:
			control.SetValue(value)
		except ValueError:
			raise ValueError(vestr % (value, controlname))

	elif isinstance(control, wx.Choice):

		if isinstance(control, wx.TextCtrl) and type(value) is not str:
			typename = str.__name__
			raise TypeError(testr % (controlname, typename, valuetypename))

		if control.FindString(value) == wx.NOT_FOUND:
			raise ValueError(vestr % (value, controlname))
		else:
			control.SetStringSelection(value)

def getValue(wxobj):
	if isinstance(wxobj, wx.StaticText):
		return wxobj.GetLabel()
	elif isinstance(wxobj, (Entry, wx.TextCtrl, wx.CheckBox)):
		return wxobj.GetValue()
	elif isinstance(wxobj, wx.Choice):
		return wxobj.GetStringSelection()
	elif isinstance(wxobj, wx.Event):
		evtobj = wxobj.GetEventObject()
		if isinstance(evtobj, wx.CheckBox):
			return wxobj.IsChecked()
		elif isinstance(evtobj, (Entry, wx.TextCtrl)):
			return wxobj.GetValue()
		elif isinstance(evtobj, wx.Choice):
			return wxobj.GetString()
	else:
		raise ValueError('Cannot get value for %s' % wxobj.__class__.__name__)

def bindControl(parent, method, control):
	if isinstance(wxobj, wx.CheckBox):
		binder = wx.EVT_CHECKBOX
	elif isinstance(wxobj, Entry):
		binder = EVT_ENTRY
	elif isinstance(wxobj, wx.Choice):
		binder = wx.EVT_CHOICE
	else:
		raise ValueError('Cannot bind event for %s' % wxobj.__class__.__name__)
	parent.Bind(binder, method, control)

InitParametersEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()

EVT_INIT_PARAMETERS = wx.PyEventBinder(InitParametersEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)

class InitParametersEvent(wx.PyCommandEvent):
	def __init__(self, source, parameters):
		wx.PyCommandEvent.__init__(self, InitParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters

class SetParametersEvent(wx.PyCommandEvent):
	def __init__(self, source, parameters):
		wx.PyCommandEvent.__init__(self, SetParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters

class LensesSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Lenses'):
		self.parent = parent
		self.xy = {}
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameters = {}

		p = 'Objective excitation'
		st = wx.StaticText(self.parent, -1, p + ':')
		parameters[p] = wx.StaticText(self.parent, -1, '')
		self.sz.Add(st, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(parameters[p], (0, 2), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		for i, a in enumerate(['x', 'y']):
			st = wx.StaticText(self.parent, -1, a)
			self.sz.Add(st, (1, i+2), (1, 1), wx.ALIGN_CENTER)
		self.row = 2

		self.addXY('Shift', 'Image')
		self.addXY('Shift (raw)', 'Image')
		self.addXY('Shift', 'Beam')
		self.addXY('Tilt', 'Beam')
		self.addXY('Objective', 'Stigmator')
		self.addXY('Diffraction', 'Stigmator')
		self.addXY('Condenser', 'Stigmator')

		self.sz.AddGrowableCol(0)

	def addXY(self, name, group):
		row = self.row
		if group not in self.xy:
			self.xy[group] = {}
			label = wx.StaticText(self.parent, -1, group + ':')
			self.sz.Add(label, (row, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.xy[group][name] = {}
		self.xy[group][name]['label'] = wx.StaticText(self.parent, -1, name)
		self.sz.Add(self.xy[group][name]['label'], (row, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		for i, a in enumerate(['x', 'y']):
			self.xy[group][name][a] = FloatEntry(self.parent, -1, chars=9)
			self.sz.Add(self.xy[group][name][a], (row, i+2), (1, 1),
									wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
			self.xy[group][name][a].Enable(False)
		self.row += 1

class FilmSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Film'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Stock',
			'Exposure number',
			'Exposure type',
			'Automatic exposure time',
			'Manual exposure time',
			'User code',
			'Date Type',
			'Text',
			'Shutter',
			'External shutter',
		]

		self.parameters = {
			'Stock': wx.StaticText(self.parent, -1, ''),
			'Exposure number': IntEntry(self.parent, -1, chars=5),
			'Exposure type': wx.Choice(self.parent, -1),
			'Automatic exposure time': wx.StaticText(self.parent, -1, ''),
			'Manual exposure time': FloatEntry(self.parent, -1, chars=5),
			'User code': Entry(self.parent, -1, chars=3),
			'Date Type': wx.Choice(self.parent, -1),
			'Text': Entry(self.parent, -1, chars=20),
			'Shutter': wx.Choice(self.parent, -1),
			'External shutter': wx.Choice(self.parent, -1),
		}

		row = 0
		for key in parameterorder:
			st = wx.StaticText(self.parent, -1, key + ':')
			self.sz.Add(st, (row, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			style = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
			if isinstance(self.parameters[key], Entry):
				style |= wx.FIXED_MINSIZE
			self.sz.Add(self.parameters[key], (row, 1), (1, 1), style)
			self.parameters[key].Enable(False)
			row += 1

class StageSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Stage'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(0, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		self.parameters = {
			'Status': wx.StaticText(self.parent, -1, ''),
			'Correction': wx.CheckBox(self.parent, -1, 'Correct stage movement'),
			'x': FloatEntry(self.parent, -1, chars=9),
			'y': FloatEntry(self.parent, -1, chars=9),
			'z': FloatEntry(self.parent, -1, chars=9),
			'a': FloatEntry(self.parent, -1, chars=4),
			'b': FloatEntry(self.parent, -1, chars=4),
		}

		st = wx.StaticText(self.parent, -1, 'Status:')
		self.sz.Add(st, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.parameters['Status'], (0, 1), (1, 3),
								wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(self.parameters['Correction'], (1, 0), (1, 4), wx.ALIGN_CENTER)
		self.parameters['Correction'].Enable(False)

		st = wx.StaticText(self.parent, -1, 'Position:')
		self.sz.Add(st, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		for i, a in enumerate(['x', 'y', 'z']):
			st = wx.StaticText(self.parent, -1, a)
			self.sz.Add(st, (2, i+1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.parameters[a], (3, i+1), (1, 1),
									wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
			self.parameters[a].Enable(False)

		for i, a in enumerate(['a', 'b']):
			st = wx.StaticText(self.parent, -1, a)
			self.sz.Add(st, (4, i+1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.parameters[a], (5, i+1), (1, 1),
									wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
			self.parameters[a].Enable(False)

		st = wx.StaticText(self.parent, -1, 'Angle:')
		self.sz.Add(st, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

class HolderSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Holder'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(0, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = ['Status', 'Type']

		self.parameters = {
			'Status': wx.StaticText(self.parent, -1, ''),
			'Type': wx.Choice(self.parent, -1),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)
			self.parameters[p].Enable(False)

		self.sz.AddGrowableCol(1)

class ScreenSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Screen'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(0, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		self.parameters = {
			'Current': wx.StaticText(self.parent, -1, ''),
			'Main': wx.Choice(self.parent, -1),
			'Small': wx.StaticText(self.parent, -1, ''),
		}

		p = 'Current'
		st = wx.StaticText(self.parent, -1, p + ':')
		self.sz.Add(st, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.parameters[p], (0, 1), (1, 2), wx.ALIGN_CENTER)

		st = wx.StaticText(self.parent, -1, 'Position:')
		self.sz.Add(st, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		for i, p in enumerate(['Main', 'Small']):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i+1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i+1, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
			self.parameters[p].Enable(False)
		self.sz.AddGrowableCol(0)
		self.sz.AddGrowableCol(1)
		self.sz.AddGrowableCol(2)

class VacuumSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Vacuum'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(0, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Status',
			'Column pressure',
			'Column valves',
			'Turbo pump'
		]
		self.parameters = {
			'Status': wx.StaticText(self.parent, -1, ''),
			'Column pressure': wx.StaticText(self.parent, -1, ''),
			'Column valves': wx.Choice(self.parent, -1),
			'Turbo pump': wx.StaticText(self.parent, -1, ''),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)
			self.sz.AddGrowableRow(i)
			self.parameters[p].Enable(False)

class LowDoseSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Low Dose'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Status',
			'Mode'
		]
		self.parameters = {
			'Status': wx.Choice(self.parent, -1),
			'Mode': wx.Choice(self.parent, -1),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)
			self.parameters[p].Enable(False)

		self.sz.AddGrowableCol(1)

class FocusSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Focus'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Focus',
			'Defocus',
		]
		self.parameters = {
			'Focus': FloatEntry(self.parent, -1, chars=9),
			'Defocus': FloatEntry(self.parent, -1, chars=9),
			'Reset Defocus': wx.Button(self.parent, -1, 'Reset Defocus'),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)

		self.sz.Add(self.parameters['Reset Defocus'], (i+1, 1), (1, 1),
								wx.ALIGN_CENTER)

		for p in self.parameters.values():
			p.Enable(False)

		self.sz.AddGrowableCol(1)

class MainSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Main'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'High tension',
			'Magnification',
			'Intensity',
			'Spot size',
		]
		self.parameters = {
			'High tension': wx.StaticText(self.parent, -1, ''),
			'Magnification': FloatEntry(self.parent, -1, chars=7),
			'Intensity': FloatEntry(self.parent, -1, chars=7),
			'Spot size': IntEntry(self.parent, -1, chars=2),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			style = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
			if isinstance(self.parameters[p], Entry):
				style |= wx.FIXED_MINSIZE
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), style)
			self.sz.AddGrowableRow(i)
			self.parameters[p].Enable(False)

		self.sz.AddGrowableCol(1)

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pInstrument' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.szparameters = self._getStaticBoxSizer('Microscope', (1, 0), (1, 2),
																								wx.EXPAND|wx.ALL)
		self.szlenses = LensesSizer(self)
		self.szfilm = FilmSizer(self)
		self.szstage = StageSizer(self)
		self.szholder = HolderSizer(self)
		self.szscreen = ScreenSizer(self)
		self.szvacuum = VacuumSizer(self)
		self.szlowdose = LowDoseSizer(self)
		self.szfocus = FocusSizer(self)
		self.szpmain = MainSizer(self)

		self.szparameters.Add(self.szpmain, (0, 0), (1, 1), wx.EXPAND)
		self.szparameters.Add(self.szstage, (0, 1), (1, 1), wx.EXPAND)

		self.szparameters.Add(self.szlenses, (1, 0), (1, 1), wx.EXPAND)
		self.szparameters.Add(self.szfilm, (1, 1), (1, 1), wx.EXPAND)

		self.szparameters.Add(self.szfocus, (2, 0), (1, 1), wx.EXPAND)
		self.szparameters.Add(self.szscreen, (2, 1), (1, 1), wx.EXPAND)

		self.szparameters.Add(self.szvacuum, (3, 0), (2, 1), wx.EXPAND)

		self.szparameters.Add(self.szholder, (3, 1), (1, 1), wx.EXPAND)
		self.szparameters.Add(self.szlowdose, (4, 1), (1, 1), wx.EXPAND)

		self.parametermap = {
			'high tension': self.szpmain.parameters['High tension'],
			'magnification': self.szpmain.parameters['Magnification'],
			'intensity': self.szpmain.parameters['Intensity'],
			'spot size': self.szpmain.parameters['Spot size'],
			'stage status': self.szstage.parameters['Status'],
			'corrected stage position': self.szstage.parameters['Correction'],
			'stage position': {
				'x': self.szstage.parameters['x'],
				'y': self.szstage.parameters['y'],
				'z': self.szstage.parameters['z'],
				'a': self.szstage.parameters['a'],
				'b': self.szstage.parameters['b'],
			},
			'image shift': {
				'x': self.szlenses.xy['Image']['Shift']['x'],
				'y': self.szlenses.xy['Image']['Shift']['y'],
			},
			'raw image shift': {
				'x': self.szlenses.xy['Image']['Shift (raw)']['x'],
				'y': self.szlenses.xy['Image']['Shift (raw)']['y'],
			},
			'beam shift': {
				'x': self.szlenses.xy['Beam']['Shift']['x'],
				'y': self.szlenses.xy['Beam']['Shift']['y'],
			},
			'beam tilt': {
				'x': self.szlenses.xy['Beam']['Tilt']['x'],
				'y': self.szlenses.xy['Beam']['Tilt']['y'],
			},
			'stigmator': {
				'objective': {
					'x': self.szlenses.xy['Stigmator']['Objective']['x'],
					'y': self.szlenses.xy['Stigmator']['Objective']['y'],
				},
				'diffraction': {
					'x': self.szlenses.xy['Stigmator']['Diffraction']['x'],
					'y': self.szlenses.xy['Stigmator']['Diffraction']['y'],
				},
				'condenser': {
					'x': self.szlenses.xy['Stigmator']['Condenser']['x'],
					'y': self.szlenses.xy['Stigmator']['Condenser']['y'],
				},
			},
			'film stock': self.szfilm.parameters['Stock'],
			'film exposure number': self.szfilm.parameters['Exposure number'],
			'film exposure type': self.szfilm.parameters['Exposure type'],
			'film automatic exposure time':
				self.szfilm.parameters['Automatic exposure time'],
			'film manual exposure time':
				self.szfilm.parameters['Manual exposure time'],
			'film user code': self.szfilm.parameters['User code'],
			'film date type': self.szfilm.parameters['Date Type'],
			'film text': self.szfilm.parameters['Text'],
			'shutter': self.szfilm.parameters['Shutter'],
			'external shutter': self.szfilm.parameters['External shutter'],
			'focus': self.szfocus.parameters['Focus'],
			'defocus': self.szfocus.parameters['Defocus'],
			'reset defocus': self.szfocus.parameters['Reset Defocus'],
			'screen current': self.szscreen.parameters['Current'],
			'main screen position': self.szscreen.parameters['Main'],
			'small screen position': self.szscreen.parameters['Small'],
			'vacuum status': self.szvacuum.parameters['Status'],
			'column pressure': self.szvacuum.parameters['Column pressure'],
			'column valves': self.szvacuum.parameters['Column valves'],
			'turbo pump': self.szvacuum.parameters['Turbo pump'],
			'holder status': self.szholder.parameters['Status'],
			'holder type': self.szholder.parameters['Type'],
			'low dose': self.szlowdose.parameters['Status'],
			'low dose mode': self.szlowdose.parameters['Mode'],
		}

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()
		self.Enable(False)

		self.Bind(EVT_INIT_PARAMETERS, self.onInitParameters)
		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)

	def _initParameter(self, parameter, value):
		if isinstance(parameter, wx.Choice):
			parameter.Clear()
			parameter.AppendItems(value['values'])

	def _setParameter(self, parameter, value):
		if isinstance(parameter, dict):
			self._setParameters(value, parameter)
		else:
			try:
				setControl(parameter, value)
				parameter.Enable(True)
			except (TypeError, ValueError), e:
				pass

	def _initParameters(self, parameters, parametermap=None):
		self.Enable(False)
		self.Freeze()
		if parametermap is None:
			parametermap = self.parametermap
		for key, value in parameters.items():
			try:
				self._initParameter(parametermap[key], value)
			except KeyError:
				pass
		self.Thaw()
		self.Enable(True)

	def _setParameters(self, parameters, parametermap=None):
		self.Enable(False)
		self.Freeze()
		if parametermap is None:
			parametermap = self.parametermap
		for key, value in parameters.items():
			try:
				self._setParameter(parametermap[key], value)
			except KeyError:
				pass
		self.Thaw()
		self.Enable(True)

	def onInitParameters(self, evt):
		self._initParameters(evt.parameters, self.parametermap)

	def initParameters(self, parameters):
		evt = InitParametersEvent(self, parameters)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetParameters(self, evt):
		self._setParameters(evt.parameters, self.parametermap)

	def setParameters(self, parameters):
		evt = SetParametersEvent(self, parameters)
		self.GetEventHandler().AddPendingEvent(evt)

	def onNodeInitialized(self):
		self.Enable(True)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Instrument Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

