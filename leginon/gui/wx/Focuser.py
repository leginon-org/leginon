import gui.wx.Acquisition
from gui.wx.Choice import Choice
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import wx
import wxImageViewer

UpdateImagesEventType = wx.NewEventType()
ManualCheckEventType = wx.NewEventType()
ManualCheckDoneEventType = wx.NewEventType()

EVT_UPDATE_IMAGES = wx.PyEventBinder(UpdateImagesEventType)
EVT_MANUAL_CHECK = wx.PyEventBinder(ManualCheckEventType)
EVT_MANUAL_CHECK_DONE = wx.PyEventBinder(ManualCheckDoneEventType)

class UpdateImagesEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, UpdateImagesEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckEventType, source.GetId())
		self.SetEventObject(source)

class ManualCheckDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, ManualCheckDoneEventType, source.GetId())
		self.SetEventObject(source)

class Panel(gui.wx.Acquisition.Panel):
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)
		self.SetName('%s.pFocuser' % name)

		self.tbauto = wx.ToggleButton(self, -1, 'Autofocus')
		self.bmanual = wx.Button(self, -1, 'Manual Focus')
		self.szcontrols.Add(self.tbauto, (3, 0), (1, 1), wx.EXPAND)
		self.szcontrols.Add(self.bmanual, (4, 0), (1, 1), wx.EXPAND)

		# correlation image
		szimage = self._getStaticBoxSizer('Correlation Image', (2, 1), (1, 1),
																						wx.EXPAND|wx.ALL)
		self.ipcorrelation = wxImageViewer.TargetImagePanel(self, -1, tool=False)
		self.ipcorrelation.addTargetType('Peak')
		szimage.Add(self.ipcorrelation, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.AddGrowableRow(2)

		self.szmain.Layout()

	def onNodeInitialized(self):
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onToggleAuto, self.tbauto)
		self.Bind(wx.EVT_BUTTON, self.onManualButton, self.bmanual)

		self.manualdialog = ManualFocusDialog(self)
		self.Bind(wx.EVT_BUTTON, self.onManualButton, self.bmanual)
		self.Bind(EVT_MANUAL_CHECK, self.onManualCheck, self)
		self.Bind(EVT_MANUAL_CHECK_DONE, self.onManualCheckDone, self)

		gui.wx.Acquisition.Panel.onNodeInitialized(self)

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onToggleAuto(self, evt):
		self.node.autofocus = evt.IsChecked()

	def onManualButton(self, evt):
		self.node.manualNow()

	def onManualCheck(self, evt):
		self.manualdialog.ShowModal()
		self.node.manualDone()

	def onManualCheckDone(self, evt):
		self.manualdialog.Show(False)

	def updateManualImages(self):
		evt = UpdateImagesEvent()
		self.manualdialog.AddPendingEvent(evt)

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		asz = gui.wx.Acquisition.SettingsDialog.initialize(self)

		focustypes = self.node.focus_methods.keys()
		self.widgets['correction type'] = Choice(self, -1, choices=focustypes)

		presets = self.node.presetsclient.getPresetNames()
		self.widgets['preset'] = Choice(self, -1, choices=presets)

		self.widgets['melt time'] = FloatEntry(self, -1,
																						min=0.0,
																						allownone=False,
																						chars=4,
																						value='0.0')
		szmelt = wx.GridBagSizer(5, 5)
		szmelt.Add(self.widgets['melt time'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szmelt.Add(wx.StaticText(self, -1, 'seconds'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		self.widgets['beam tilt'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['fit limit'] = FloatEntry(self, -1,
																						allownone=False,
																						chars=9,
																						value='0.0')

		self.widgets['check drift'] = wx.CheckBox(self, -1,
																								'Check for drift greater than')
		self.widgets['drift threshold'] = FloatEntry(self, -1,
																									min=0.0,
																									allownone=False,
																									chars=4,
																									value='0.0')
		szdrift = wx.GridBagSizer(5, 5)
		szdrift.Add(self.widgets['check drift'], (0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szdrift.Add(self.widgets['drift threshold'], (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szdrift.Add(wx.StaticText(self, -1, 'pixels'), (0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		self.widgets['check before'] = wx.CheckBox(self, -1,
																			'Manual focus check before autofocus')
		self.widgets['check after'] = wx.CheckBox(self, -1,
																			'Manual focus check after autofocus')

		self.widgets['stig correction'] = wx.CheckBox(self, -1, 'Correct')
		self.widgets['stig defocus min'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		self.widgets['stig defocus max'] = FloatEntry(self, -1,
																									allownone=False,
																									chars=9,
																									value='0.0')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['stig correction'], (0, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Min.'), (1, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Max.'), (1, 2), (1, 1), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Defocus:'), (2, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig defocus min'], (2, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(self.widgets['stig defocus max'], (2, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szstig = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Stigmator'), wx.VERTICAL)
		szstig.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.widgets['acquire final'] = wx.CheckBox(self, -1, 'Acquire final image')

		# settings sizer
		sz = wx.GridBagSizer(10, 5)
		sz.Add(wx.StaticText(self, -1, 'Correction type'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['correction type'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Preset'), (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['preset'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Melt time:'), (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szmelt, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(wx.StaticText(self, -1, 'Beam tilt:'), (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['beam tilt'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'Fit limit:'), (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['fit limit'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(szdrift, (5, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sz.Add(self.widgets['check before'], (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['check after'], (1, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['acquire final'], (2, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szstig, (3, 2), (4, 1), wx.ALIGN_CENTER)
		sz.AddGrowableRow(6)

		sb = wx.StaticBox(self, -1, 'Autofocus')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(asz, (0, 0), (1, 1), wx.EXPAND)
		sz.Add(sbsz, (1, 0), (1, 1), wx.EXPAND)

		return sz

class ManualFocusDialog(wx.Dialog):
	def __init__(self, parent, title='Manual Focus'):
		wx.Dialog.__init__(self, parent, -1, title)
		self.node = parent.node

		self.tbpause = wx.ToggleButton(self, -1, 'Pause')
		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		self.beftoscope = wx.Button(self, -1, 'To Scope')
		self.beffromscope = wx.Button(self, -1, 'From Scope')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.beftoscope, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.beffromscope, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szef = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Eucentric Focus'),
															wx.VERTICAL)
		szef.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.cparameter = wx.Choice(self, -1, choices=['Defocus', 'Stage Z'])
		self.cparameter.SetSelection(0)
		self.feincrement = FloatEntry(self, -1, min=0.0,
																						allownone=False,
																						chars=6,
																						value='5e-7')
		self.bup = wx.Button(self, -1, 'Up')
		self.bdown = wx.Button(self, -1, 'Down')
		self.bzero = wx.Button(self, -1, 'Zero')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.cparameter, (0, 0), (1, 3), wx.ALIGN_CENTER)
		sz.Add(wx.StaticText(self, -1, 'Increment:'), (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.feincrement, (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'm'), (1, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.bup, (2, 0), (1, 3), wx.ALIGN_CENTER)
		sz.Add(self.bdown, (3, 0), (1, 3), wx.ALIGN_CENTER)
		sz.Add(self.bzero, (4, 0), (1, 3), wx.ALIGN_CENTER)
		szadjust = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Adjust'), wx.VERTICAL)
		szadjust.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.breset = wx.Button(self, -1, 'Reset')
		szreset = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Instrument Defocus'),
															wx.VERTICAL)
		szreset.Add(self.breset, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.femaskradius = FloatEntry(self, -1, allownone=False,
																							chars=6,
																							value='0.01')
		szmaskradius = wx.GridBagSizer(5, 5)
		szmaskradius.Add(wx.StaticText(self, -1, 'Mask radius:'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		szmaskradius.Add(self.femaskradius, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szmaskradius.Add(wx.StaticText(self, -1, '% of image'), (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)

		self.rbimage = wx.RadioBox(self, -1, 'Display',
																					choices=['Image', 'Power Spectrum'],
																					style=wx.RA_VERTICAL)

		szimage = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Image'), wx.VERTICAL)
		szimage.Add(szmaskradius, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		szimage.Add(self.rbimage, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.ipimage = wxImageViewer.ImagePanel(self, -1)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szef, (0, 0), (1, 2), wx.EXPAND)
		sz.Add(szadjust, (1, 0), (1, 2), wx.EXPAND)
		sz.Add(szreset, (2, 0), (1, 2), wx.EXPAND)
		sz.Add(szimage, (3, 0), (1, 2), wx.EXPAND)
		sz.Add(self.tbpause, (4, 0), (1, 1), wx.ALIGN_CENTER|wx.TOP, 10)
		sz.Add(self.bdone, (4, 1), (1, 1), wx.ALIGN_CENTER|wx.TOP, 10)
		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_TOP|wx.ALL, 10)
		szmain.Add(self.ipimage, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onEFToScopeButton, self.beftoscope)
		self.Bind(wx.EVT_BUTTON, self.onEFFromScopeButton, self.beffromscope)
		self.Bind(wx.EVT_BUTTON, self.onZeroButton, self.bzero)
		self.Bind(wx.EVT_BUTTON, self.onUpButton, self.bup)
		self.Bind(wx.EVT_BUTTON, self.onDownButton, self.bdown)
		self.Bind(wx.EVT_BUTTON, self.onResetButton, self.breset)
		self.Bind(wx.EVT_TOGGLEBUTTON, self.onTogglePause, self.tbpause)
		self.Bind(EVT_ENTRY, self.onMaskRadiusEntry, self.femaskradius)
		self.Bind(EVT_ENTRY, self.onIncrementEntry, self.feincrement)
		self.Bind(wx.EVT_CHOICE, self.onParameterChoice, self.cparameter)
		self.Bind(EVT_UPDATE_IMAGES, self.onUpdateImages, parent)
		self.Bind(wx.EVT_RADIOBOX, self.onUpdateImages, self.rbimage)

		self.onParameterChoice()
		self.onMaskRadiusEntry()
		self.onIncrementEntry()

	def onTogglePause(self, evt):
		if evt.IsChecked():
			self.node.manualPause()
		else:
			self.node.manualContinue()

	def onEFToScopeButton(self, evt):
		self.node.uiChangeToEucentric()

	def onEFFromScopeButton(self, evt):
		self.node.uiEucentricFromScope()

	def onZeroButton(self, evt):
		self.node.uiChangeToZero()

	def onUpButton(self, evt):
		self.node.uiFocusUp()

	def onDownButton(self, evt):
		self.node.uiFocusDown()

	def onResetButton(self, evt):
		self.node.uiResetDefocus()

	def onMaskRadiusEntry(self, evt=None):
		if evt is None:
			value = self.femaskradius.GetValue()
		else:
			value = evt.GetValue()
		self.node.maskradius = value

	def onIncrementEntry(self, evt=None):
		if evt is None:
			value = self.feincrement.GetValue()
		else:
			value = evt.GetValue()
		self.node.increment = value

	def onParameterChoice(self, evt=None):
		if evt is None:
			parameter = self.cparameter.GetStringSelection()
		else:
			parameter = evt.GetString()
		self.node.parameter = parameter

	def onUpdateImages(self, evt):
		string = self.rbimage.GetStringSelection()
		if string == 'Image':
			self.ipimage.setNumericImage(self.node.man_image)
		elif string == 'Power Spectrum':
			self.ipimage.setNumericImage(self.node.man_power)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			panel = Panel(frame, 'Test')
			frame.node = object() 
			dialog = ManualFocusDialog(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

