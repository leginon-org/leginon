import data
import gui.wx.Data
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Node
from gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import wx
import wxImageViewer

class Panel(gui.wx.Node.Panel):
	icon = 'acquisition'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pAcquisition' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.stcount = wx.StaticText(self, -1, '')
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.stcount, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# controls
		self.szcontrols = self._getStaticBoxSizer('Controls', (1, 0), (1, 1),
																								wx.ALIGN_TOP)
		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.tbpause = wx.ToggleButton(self, -1, 'Pause')
		self.tbstop = wx.ToggleButton(self, -1, 'Stop')
		self.szcontrols.Add(self.bsettings, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szcontrols.Add(self.tbpause, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szcontrols.Add(self.tbstop, (2, 0), (1, 1), wx.ALIGN_CENTER)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (1, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = wxImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()
		self.Enable(False)

	def onNodeInitialized(self):
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePause, self.tbpause)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleStop, self.tbstop)

		self.Enable(True)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onTogglePause(self, evt):
		if evt.IsChecked():
			self.node.pause.clear()
		else:
			self.node.pause.set()

	def onToggleStop(self, evt):
		if evt.IsChecked():
			self.node.abort = True
		else:
			self.node.abort = False

class SettingsError(Exception):
	pass

class SettingsDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		title = '%s Settings' % self.node.name
		wx.Dialog.__init__(self, parent, -1, title) 

		self.widgets = {}

		# move type
		movetypes = self.node.calclients.keys()
		self.widgets['move type'] = wx.Choice(self, -1, choices=movetypes)
		szmovetype = wx.GridBagSizer(5, 5)
		szmovetype.Add(wx.StaticText(self, -1, 'Use'),
										(0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(self.widgets['move type'],
										(0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szmovetype.Add(wx.StaticText(self, -1, 'to move to target'),
										(0, 2), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# preset order
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset order'] = EditPresetOrder(self, -1)
		self.widgets['preset order'].setChoices(presets)

		# misc. checkboxes
		self.widgets['correct image'] = wx.CheckBox(self, -1, 'Correct image')
		self.widgets['display image'] = wx.CheckBox(self, -1, 'Display image')
		self.widgets['save image'] = wx.CheckBox(self, -1, 'Save image to database')
		self.widgets['wait for process'] = wx.CheckBox(self, -1,
																				'Wait for a node to process the image')
		self.widgets['wait for rejects'] = wx.CheckBox(self, -1,
																				'Publish and wait for rejected targets')
		# duplicate target
		self.widgets['duplicate targets'] = wx.CheckBox(self, -1,
																				'Duplicate targets with type:')
		self.widgets['duplicate target type'] = wx.Choice(self, -1,
																							choices=self.node.duplicatetypes)

		szduplicate = wx.GridBagSizer(0, 0)
		szduplicate.Add(self.widgets['duplicate targets'], (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)
		szduplicate.Add(self.widgets['duplicate target type'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL)

		# settings sizer
		sz = wx.GridBagSizer(5, 5)
		sz.Add(szmovetype, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpausetime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset order'], (2, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.widgets['correct image'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['display image'], (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['save image'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for process'], (6, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['wait for rejects'], (7, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szduplicate, (8, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		# buttons
		self.bok = wx.Button(self, wx.ID_OK, 'OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.bapply = wx.Button(self, wx.ID_APPLY, 'Apply')
		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(self.bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bapply, (0, 2), (1, 1), wx.ALIGN_CENTER)

		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1),
								wx.ALIGN_CENTER|wx.ALL, 10)
		szmain.Add(szbuttons, (1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		# set values
		self.getNodeSettings()

		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onSet, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onSet, self.bapply)

		modifiedevents = {
			wx.CheckBox: wx.EVT_CHECKBOX,
			wx.Choice: wx.EVT_CHOICE,
			FloatEntry: EVT_ENTRY,
			EditPresetOrder: EVT_PRESET_ORDER_CHANGED,
		}

		for widget in self.widgets.values():
			self.Bind(modifiedevents[widget.__class__], self.onModified)

	def onModified(self, evt):
		if self.getSettings() == self.settings:
			self.bapply.Enable(False)
		else:
			self.bapply.Enable(True)
		evt.Skip()

	def onSet(self, evt):
		try:
			self.setNodeSettings()
			evt.Skip()
		except SettingsError:
			dialog = wx.MessageDialog(self, str(e), 'Settings Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

	def getSettings(self):
		getmethods = {
			wx.CheckBox: 'GetValue',
			wx.Choice: 'GetStringSelection',
			FloatEntry: 'GetValue',
			EditPresetOrder: 'getValues',
		}
		settings = {}
		for key, widget in self.widgets.items():
			settings[key] = getattr(widget, getmethods[widget.__class__])()
		return settings

	def setSettings(self, sd):
		setmethods = {
			wx.CheckBox: 'SetValue',
			wx.Choice: 'SetStringSelection',
			FloatEntry: 'SetValue',
			EditPresetOrder: 'setValues',
		}
		for key, widget in self.widgets.items():
			getattr(widget, setmethods[widget.__class__])(sd[key])

	def setNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return
		settings = self.getSettings()
		if settings != self.settings:
			settingsdata = data.AcquisitionSettingsData(initializer=settings)
			node.setSettings(settingsdata)
			self.settings = settings
			self.bapply.Enable(False)

	def getNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return

		settingsdata = node.getSettings()
		self.setSettings(settingsdata)

		self.settings = self.getSettings()
		self.bapply.Enable(False)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

