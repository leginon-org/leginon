import wx
from gui.wx.Entry import Entry, IntEntry, FloatEntry, EVT_ENTRY
import gui.wx.Node

SetParametersEventType = wx.NewEventType()
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)
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
		self.addXY('Condensor', 'Stigmator')

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

		parameters = {
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
			self.sz.Add(parameters[key], (row, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
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

		st = wx.StaticText(self.parent, -1, 'Position:')
		self.sz.Add(st, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		for i, a in enumerate(['x', 'y', 'z']):
			st = wx.StaticText(self.parent, -1, a)
			self.sz.Add(st, (2, i+1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.parameters[a], (3, i+1), (1, 1),
									wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		for i, a in enumerate(['a', 'b']):
			st = wx.StaticText(self.parent, -1, a)
			self.sz.Add(st, (4, i+1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.parameters[a], (5, i+1), (1, 1),
									wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

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

		parameters = {
			'Status': wx.StaticText(self.parent, -1, ''),
			'Type': wx.Choice(self.parent, -1),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)

		self.sz.AddGrowableCol(1)

class ScreenSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Screen'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(0, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameters = {
			'Current': wx.StaticText(self.parent, -1, ''),
			'Main': wx.Choice(self.parent, -1),
			'Small': wx.StaticText(self.parent, -1, ''),
		}

		p = 'Current'
		st = wx.StaticText(self.parent, -1, p + ':')
		self.sz.Add(st, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(parameters[p], (0, 1), (1, 2), wx.ALIGN_CENTER)

		st = wx.StaticText(self.parent, -1, 'Position:')
		self.sz.Add(st, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		for i, p in enumerate(['Main', 'Small']):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i+1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i+1, 2), (1, 1), wx.ALIGN_CENTER)
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
		parameters = {
			'Status': wx.StaticText(self.parent, -1, ''),
			'Column pressure': wx.StaticText(self.parent, -1, ''),
			'Column valves': wx.Choice(self.parent, -1),
			'Turbo pump': wx.StaticText(self.parent, -1, ''),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)
			self.sz.AddGrowableRow(i)

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
		parameters = {
			'Status': wx.Choice(self.parent, -1),
			'Mode': wx.Choice(self.parent, -1),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)

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
		parameters = {
			'Focus': FloatEntry(self.parent, -1, chars=9),
			'Defocus': FloatEntry(self.parent, -1, chars=9),
			'Reset Defocus': wx.Button(self.parent, -1, 'Reset Defocus'),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)

		self.sz.Add(parameters['Reset Defocus'], (i+1, 1), (1, 1), wx.ALIGN_CENTER)

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
		parameters = {
			'High tension': wx.StaticText(self.parent, -1, ''),
			'Magnification': FloatEntry(self.parent, -1, chars=7),
			'Intensity': FloatEntry(self.parent, -1, chars=7),
			'Spot size': IntEntry(self.parent, -1, chars=2),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(parameters[p], (i, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
			self.sz.AddGrowableRow(i)

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
			'stage status': self.szstage.parameters['Status'],
			'corrected stage position': self.szstage.parameters['Correction'],
			'stage position': {
				'x': self.szstage.parameters['x'],
				'y': self.szstage.parameters['y'],
				'z': self.szstage.parameters['z'],
				'a': self.szstage.parameters['a'],
				'b': self.szstage.parameters['b'],
			},
		}

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()
		self.Enable(False)

		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)

	def _setParameter(self, parameter, value):
		if isinstance(parameter, dict):
			self._setParameters(value, parameter)
		elif isinstance(parameter, wx.StaticText):
			parameter.SetLabel(value)
		elif isinstance(parameter, (Entry, wx.TextCtrl, wx.CheckBox)):
			parameter.SetValue(value)

	def _setParameters(self, parameters, parametermap=None):
		if parametermap is None:
			parametermap = self.parametermap
		for key, value in parameters.items():
			try:
				self._setParameter(parametermap[key], value)
			except KeyError:
				pass

	def onSetParameters(self, evt):
		self._setParameters(evt.parameters, self.parametermap)

	def setParameters(self, parameters):
		evt = SetParametersEvent(parameters)
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

