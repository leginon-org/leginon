import icons
import wx
import wx.lib.buttons
from wx.lib.masked import NumCtrl, EVT_NUM
import gui.wx.Camera
import gui.wx.Node
import wxImageViewer

def getBitmap(filename):
	iconpath = icons.getPath(filename)
	wximage = wx.Image(iconpath)
	bitmap = wx.BitmapFromImage(wximage)
	bitmap.SetMask(wx.Mask(bitmap, wx.WHITE))
	return bitmap

PresetOrderChangedEventType = wx.NewEventType()
PresetChoiceEventType = wx.NewEventType()
PresetsChangedEventType = wx.NewEventType()
NewPresetEventType = wx.NewEventType()
SetDoseValueEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()
SetCalibrationsEventType = wx.NewEventType()

EVT_PRESET_ORDER_CHANGED = wx.PyEventBinder(PresetOrderChangedEventType)
EVT_PRESET_CHOICE = wx.PyEventBinder(PresetChoiceEventType)
EVT_PRESETS_CHANGED = wx.PyEventBinder(PresetsChangedEventType)
EVT_NEW_PRESET = wx.PyEventBinder(NewPresetEventType)
EVT_SET_DOSE_VALUE = wx.PyEventBinder(SetDoseValueEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)
EVT_SET_CALIBRATIONS = wx.PyEventBinder(SetCalibrationsEventType)

class PresetOrderChangedEvent(wx.PyCommandEvent):
	def __init__(self, presets, source):
		wx.PyCommandEvent.__init__(self, PresetOrderChangedEventType,
																source.GetId())
		self.SetEventObject(source)
		self.presets = presets

class PresetsChoiceEvent(wx.PyCommandEvent):
	def __init__(self, choice, source):
		wx.PyCommandEvent.__init__(self, PresetChoiceEventType, source.GetId())
		self.SetEventObject(source)
		self.SetString(choice)
		self.choice = choice

class PresetsChangedEvent(wx.PyEvent):
	def __init__(self, presets):
		wx.PyEvent.__init__(self)
		self.SetEventType(PresetsChangedEventType)
		self.presets = presets

class NewPresetEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(NewPresetEventType)

class SetDoseValueEvent(wx.PyEvent):
	def __init__(self, dosestring):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetDoseValueEventType)
		self.dosestring = dosestring

class SetParametersEvent(wx.PyCommandEvent):
	def __init__(self, parameters, source):
		wx.PyCommandEvent.__init__(self, SetParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters

class SetCalibrationsEvent(wx.PyCommandEvent):
	def __init__(self, times, source):
		wx.PyCommandEvent.__init__(self, SetCalibrationsEventType, source.GetId())
		self.SetEventObject(source)
		self.times = times

class PresetChoice(wx.Choice):
	def __init__(self, *args, **kwargs):
		wx.Choice.__init__(self, *args, **kwargs)
		self.Enable(False)

		self.Bind(wx.EVT_CHOICE, self.onChoice)
		self.Bind(EVT_PRESETS_CHANGED, self.onPresetsChanged)

	def onChoice(self, evt):
		evt = PresetsChoiceEvent(evt.GetString(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetsChanged(self, evt):
		self.setChoices(evt.presets)

	def setChoices(self, choices):
		selection = self.GetStringSelection()
		self.Freeze()
		self.Clear()
		self.AppendItems(choices)
		if choices:
			n = self.FindString(selection)
			if n == wx.NOT_FOUND:
				self.SetSelection(0)
			else:
				self.SetSelection(n)
		self.Enable(choices)
		self.Thaw()

class PresetOrder(wx.Panel):
	def __init__(self, parent, id, **kwargs):
		wx.Panel.__init__(self, parent, id, **kwargs)
		self._widgets()
		self._sizer()
		self._bind()

	def _widgets(self):
		self.storder = wx.StaticText(self, -1, 'Presets Order')
		self.listbox = wx.ListBox(self, -1)
		self.upbutton = self._bitmapButton('up')
		self.downbutton = self._bitmapButton('down')

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.listbox, (1, 0), (2, 1), wx.EXPAND|wx.ALL)
		sizer.Add(self.upbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.downbutton, (2, 1), (1, 1),
							wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
		sizer.AddGrowableRow(2)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		self.Bind(wx.EVT_BUTTON, self.onUp, self.upbutton)
		self.Bind(wx.EVT_BUTTON, self.onDown, self.downbutton)
		self.Bind(wx.EVT_LISTBOX, self.onSelect, self.listbox)
		self.Bind(EVT_PRESETS_CHANGED, self.onPresetsChanged)

	def _bitmapButton(self, name):
		bitmap = getBitmap('%s.png' % name)
		button = wx.lib.buttons.GenBitmapButton(self, -1, bitmap, size=(20, 20))
		button.SetBezelWidth(1)
		button.Enable(False)
		return button

	def onUp(self, evt):
		n = self.listbox.GetSelection()
		if n > 0:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n - 1)
			self.listbox.Select(n - 1)
		self.updateButtons(n - 1)
		self.presetsEditEvent()

	def onDown(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0 and n < self.listbox.GetCount() - 1:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n + 1)
			self.listbox.Select(n + 1)
		self.updateButtons(n + 1)
		self.presetsEditEvent()

	def onPresetsChanged(self, evt):
		self.setChoices(evt.presets)

	def setChoices(self, choices):
		self.setValues(choices)

	def getValues(self):
		values = []
		for i in range(self.listbox.GetCount()):
			try:
				values.append(self.listbox.GetString(i))
			except ValueError:
				raise
		return values

	def setValues(self, values):
		count = self.listbox.GetCount()
		if values is None:
			values = []
		n = len(values)
		if count < n:
			nsame = count
		else:
			nsame = n
		for i in range(nsame):
			try:
				if self.listbox.GetString(i) != values[i]:
					self.listbox.SetString(i, values[i])
			except ValueError:
				raise
		if count < n:
			self.listbox.InsertItems(values[nsame:], nsame)
		elif count > n:
			for i in range(count - 1, n - 1, -1):
				self.listbox.Delete(i)

	def presetsEditEvent(self):
		evt = PresetOrderChangedEvent(self.getValues(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSelect(self, evt):
		self.updateButtons(evt.GetSelection())

	def updateButtons(self, n):
		if n > 0:
			self.upbutton.Enable(True)
		else:
			self.upbutton.Enable(False)
		if n < self.listbox.GetCount() - 1:
			self.downbutton.Enable(True)
		else:
			self.downbutton.Enable(False)

class EditPresetOrder(PresetOrder):
	def _widgets(self):
		PresetOrder._widgets(self)
		self.choice = wx.Choice(self, -1)
		self.choice.Enable(False)
		self.insertbutton = self._bitmapButton('plus')
		self.deletebutton = self._bitmapButton('minus')

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.choice, (1, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		sizer.Add(self.insertbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.listbox, (2, 0), (3, 1), wx.EXPAND|wx.ALL)
		sizer.Add(self.deletebutton, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.upbutton, (3, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.downbutton, (4, 1), (1, 1),
							wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
		sizer.AddGrowableRow(4)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		PresetOrder._bind(self)
		self.Bind(wx.EVT_BUTTON, self.onInsert, self.insertbutton)
		self.Bind(wx.EVT_BUTTON, self.onDelete, self.deletebutton)

	def setChoices(self, choices):
		self.Freeze()
		self.choice.Clear()
		self.choice.AppendItems(choices)
		if choices:
			self.choice.SetSelection(0)
		self.choice.Enable(choices)
		self.insertbutton.Enable(choices)
		self.Thaw()

	def onInsert(self, evt):
		try:
			string = self.choice.GetStringSelection()
		except ValueError:
			return
		n = self.listbox.GetSelection()
		if n < 0:
			self.listbox.Append(string)
		else:
			self.listbox.InsertItems([string], n)
			self.updateButtons(n + 1)
		self.presetsEditEvent()

	def onDelete(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0:
			self.listbox.Delete(n)
		count = self.listbox.GetCount()
		if n < count:
			self.listbox.Select(n)
			self.updateButtons(n)
		elif count > 0:
			self.listbox.Select(n - 1)
			self.updateButtons(n - 1)
		else:
			self.deletebutton.Enable(False)
		self.presetsEditEvent()

	def onSelect(self, evt):
		PresetOrder.onSelect(self, evt)
		self.deletebutton.Enable(True)

class Panel(gui.wx.Node.Panel):
	icon = 'presets'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pPresets' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# settings
		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.EXPAND|wx.ALL)
		stpause = wx.StaticText(self, -1, 'Pause')
		self.ncpause = NumCtrl(self, -1, 1.0, integerWidth=2,
																					fractionWidth=1,
																					allowNone=False,
																					allowNegative=False,
																					name='ncPause')
		stseconds = wx.StaticText(self, -1, 'seconds between preset changes')

		self.cbxyonly = wx.CheckBox(self, -1, 'Move stage x and y only',
																name='cbXYOnly')
		self.cbstagealways = wx.CheckBox(self, -1,
																'Move stage even when move type is image shift',
																name='cbStageAlways')

		self.cbcycleon = wx.CheckBox(self, -1, 'Cycle on', name='cbCycleOn')
		self.cbcycleoptimize = wx.CheckBox(self, -1, 'Optimize cycle',
																				name='cbCycleOptimize')
		self.cbcyclemagonly = wx.CheckBox(self, -1, 'Change magnification only',
																			name='cbCycleMagOnly')

		self.cycleorder = PresetOrder(self, -1, name='poPresetOrder')

		szcycle = wx.GridBagSizer(5, 5)
		szcycle.Add(self.cbcycleon, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcycle.Add(self.cbcycleoptimize, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcycle.Add(self.cbcyclemagonly, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcycle.Add(self.cycleorder, (3, 0), (1, 1), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Presets Cycle')
		sbszcycle = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszcycle.Add(szcycle, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stpause, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.ncpause, (0, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(stseconds, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		
		self.szsettings.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbxyonly, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(self.cbstagealways, (2, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		self.szsettings.Add(sbszcycle, (3, 0), (1, 1), wx.ALIGN_CENTER)

		# presets
		self.szpresets = self._getStaticBoxSizer('Presets', (2, 0), (1, 1),
																							wx.EXPAND|wx.ALL)

		stpixelsize = wx.StaticText(self, -1, 'Pixel size:')
		stimageshift = wx.StaticText(self, -1, 'Image shift:')
		ststage = wx.StaticText(self, -1, 'Stage:')
		stbeamshift = wx.StaticText(self, -1, 'Beam shift:')
		stmodeled = wx.StaticText(self, -1, 'Modeled stage:')
		stmodeledmagonly = wx.StaticText(self, -1, 'Modeled stage (mag. only):')
		self.stpixelsize = wx.StaticText(self, -1, '')
		self.stimageshift = wx.StaticText(self, -1, '')
		self.ststage = wx.StaticText(self, -1, '')
		self.stbeamshift = wx.StaticText(self, -1, '')
		self.stmodeled = wx.StaticText(self, -1, '')
		self.stmodeledmagonly = wx.StaticText(self, -1, '')

		szcalibrations = wx.GridBagSizer(0, 5)

		szcalibrations.Add(stpixelsize, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.stpixelsize, (0, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(stimageshift, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.stimageshift, (1, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(ststage, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.ststage, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(stbeamshift, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.stbeamshift, (3, 1), (1, 1), 
												wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(stmodeled, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.stmodeled, (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(stmodeledmagonly, (5, 0), (1, 1), 
												wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.Add(self.stmodeledmagonly, (5, 1), (1, 1), 
												wx.ALIGN_CENTER_VERTICAL)
		szcalibrations.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Calibrations')
		sbszcalibrations = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszcalibrations.Add(szcalibrations, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		stmagnification = wx.StaticText(self, -1, 'Magnification')
		self.ncmagnification = NumCtrl(self, -1, 0.0, integerWidth=9,
																									fractionWidth=1,
																									allowNone=False,
																									allowNegative=False,
																									groupDigits=False)
		stdefocus = wx.StaticText(self, -1, 'Defocus')
		self.ncdefocus = NumCtrl(self, -1, 0.0, integerWidth=6,
																							fractionWidth=3,
																							allowNone=False,
																							allowNegative=True,
																							signedForegroundColour='Black',
																							groupDigits=False)
		stspotsize = wx.StaticText(self, -1, 'Spot size')
		self.ncspotsize = NumCtrl(self, -1, 1, integerWidth=11,
																									fractionWidth=0,
																									allowNone=False,
																									allowNegative=False,
																									groupDigits=False,
																									min=1, max=11,
																									invalidBackgroundColour='Red')
		stintensity = wx.StaticText(self, -1, 'Intensity')
		self.ncintensity = NumCtrl(self, -1, 0.0, integerWidth=7,
																									fractionWidth=3,
																									allowNone=False,
																									allowNegative=False,
																									groupDigits=False,
																									min=0.0, max=2.0,
																									invalidBackgroundColour='Red')

		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stimageshift = wx.StaticText(self, -1, 'Image shift')
		self.ncimageshiftx = NumCtrl(self, -1, 0.0, integerWidth=1,
																									fractionWidth=9,
																									allowNone=False,
																									allowNegative=True,
																								signedForegroundColour='Black',
																									groupDigits=False,
																									min=-1.0, max=1.0,
																									invalidBackgroundColour='Red')
		self.ncimageshifty = NumCtrl(self, -1, 0.0, integerWidth=1,
																									fractionWidth=9,
																									allowNone=False,
																									allowNegative=True,
																								signedForegroundColour='Black',
																									groupDigits=False,
																									min=-1.0, max=1.0,
																									invalidBackgroundColour='Red')

		stbeamshift = wx.StaticText(self, -1, 'Beam shift')
		self.ncbeamshiftx = NumCtrl(self, -1, 0.0, integerWidth=1,
																									fractionWidth=9,
																									allowNone=False,
																									allowNegative=True,
																								signedForegroundColour='Black',
																									groupDigits=False,
																									min=-1.0, max=1.0,
																									invalidBackgroundColour='Red')
		self.ncbeamshifty = NumCtrl(self, -1, 0.0, integerWidth=1,
																								fractionWidth=9,
																								allowNone=False,
																								allowNegative=True,
																								signedForegroundColour='Black',
																								groupDigits=False,
																								min=-1.0, max=1.0,
																								invalidBackgroundColour='Red')

		self.cbfilm = wx.CheckBox(self, -1, 'Film')
		stdose = wx.StaticText(self, -1, 'Dose:')
		self.stdose = wx.StaticText(self, -1, '')

		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		szparameters = wx.GridBagSizer(5, 5)
		szparameters.Add(stmagnification, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncmagnification, (0, 1), (1, 2), wx.ALIGN_CENTER)
		szparameters.Add(stdefocus, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncdefocus, (1, 1), (1, 2), wx.ALIGN_CENTER)
		szparameters.Add(stspotsize, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncspotsize, (2, 1), (1, 2), wx.ALIGN_CENTER)
		szparameters.Add(stintensity, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncintensity, (3, 1), (1, 2), wx.ALIGN_CENTER)

		szparameters.Add(stx, (4, 1), (1, 1), wx.ALIGN_CENTER)
		szparameters.Add(sty, (4, 2), (1, 1), wx.ALIGN_CENTER)
		szparameters.Add(stimageshift, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncimageshiftx, (5, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncimageshifty, (5, 2), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(stbeamshift, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncbeamshiftx, (6, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.ncbeamshifty, (6, 2), (1, 1),
											wx.ALIGN_CENTER_VERTICAL)

		szparameters.Add(self.cbfilm, (7, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(stdose, (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.stdose, (8, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.cpcamconfig, (9, 0), (1, 3), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Parameters')
		sbszparameters = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszparameters.Add(szparameters, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		self.cpreset = PresetChoice(self, -1)
		self.btoscope = wx.Button(self, -1, 'To scope')
		self.bfromscope = wx.Button(self, -1, 'From scope')
		self.bremove = wx.Button(self, -1, 'Remove')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.cpreset, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.btoscope, (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.bfromscope, (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.bremove, (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		szcreate = wx.GridBagSizer(5, 5)

		self.bimport = wx.Button(self, -1, 'Import...')
		self.bnew = wx.Button(self, -1, 'New...')

		sb = wx.StaticBox(self, -1, 'Create')
		sbszcreate = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszcreate.Add(szcreate, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)

		szcreate.Add(self.bimport, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szcreate.Add(self.bnew, (1, 0), (1, 1), wx.ALIGN_CENTER)

		self.szpresets.Add(sbszcalibrations, (0, 0), (1, 2), wx.EXPAND|wx.ALL)
		self.szpresets.Add(sbszparameters, (1, 0), (2, 1), wx.EXPAND|wx.ALL)
		self.szpresets.Add(sz, (1, 1), (1, 1), wx.ALIGN_CENTER)
		self.szpresets.Add(sbszcreate, (2, 1), (1, 1), wx.ALIGN_CENTER)

		# dose image
		self.szdoseimage = self._getStaticBoxSizer('Dose Image', (1, 1), (2, 1),
																								wx.EXPAND|wx.ALL)
		stimagedose = wx.StaticText(self, -1, 'Dose:')
		self.stimagedose = wx.StaticText(self, -1, '')

		self.bacquire = wx.Button(self, -1, 'Acquire')

		self.imagepanel = wxImageViewer.ImagePanel(self, -1)

		self.szdoseimage.Add(stimagedose, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.stimagedose, (0, 1), (1, 1),
													wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.bacquire, (0, 2), (1, 1),
													wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.imagepanel, (1, 0), (1, 3), wx.ALIGN_CENTER)
		self.szdoseimage.AddGrowableCol(2)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

		self.Bind(wx.EVT_BUTTON, self.onImport, self.bimport)
		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(EVT_PRESET_ORDER_CHANGED, self.onCycleOrderChanged,
							self.cycleorder)
		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(EVT_SET_CALIBRATIONS, self.onSetCalibrations)

	def onNodeInitialized(self):
		gui.wx.Data.setWindowFromDB(self.ncpause)
		gui.wx.Data.setWindowFromDB(self.cbxyonly)
		gui.wx.Data.setWindowFromDB(self.cbstagealways)
		gui.wx.Data.setWindowFromDB(self.cbcycleon)
		gui.wx.Data.setWindowFromDB(self.cbcycleoptimize)
		gui.wx.Data.setWindowFromDB(self.cbcyclemagonly)

		self.cpcamconfig.setSize(self.node.session)

		self.node.pause = self.ncpause.GetValue()
		self.node.xyonly = self.cbxyonly.GetValue()
		self.node.stagealways = self.cbstagealways.GetValue()
		self.node.cycleon = self.cbcycleon
		self.node.cycleoptimize = self.cbcycleoptimize
		self.node.cyclemagonly = self.cbcyclemagonly

		self.Bind(EVT_NUM, self.onPauseNum, self.ncpause)
		self.Bind(wx.EVT_CHECKBOX, self.onXYOnlyCheck, self.cbxyonly)
		self.Bind(wx.EVT_CHECKBOX, self.onStageAlwaysCheck, self.cbstagealways)
		self.Bind(wx.EVT_CHECKBOX, self.onCycleCheck, self.cbcycleon)
		self.Bind(wx.EVT_CHECKBOX, self.onOptimizeCheck, self.cbcycleoptimize)
		self.Bind(wx.EVT_CHECKBOX, self.onMagOnlyCheck, self.cbcyclemagonly)
		self.Bind(wx.EVT_BUTTON, self.onAcquireDoseImage, self.bacquire)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncmagnification)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncdefocus)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncspotsize)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncintensity)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncimageshiftx)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncimageshifty)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncbeamshiftx)
		self.Bind(EVT_NUM, self.onUpdateParameters, self.ncbeamshifty)
		self.Bind(wx.EVT_CHECKBOX, self.onUpdateParameters, self.cbfilm)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, self.onUpdateParameters,
							self.cpcamconfig)
		self.Bind(EVT_PRESET_CHOICE, self.onPresetChoice, self.cpreset)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)

		gui.wx.Data.bindWindowToDB(self.ncpause)
		gui.wx.Data.bindWindowToDB(self.cbxyonly)
		gui.wx.Data.bindWindowToDB(self.cbstagealways)
		gui.wx.Data.bindWindowToDB(self.cbcycleon)
		gui.wx.Data.bindWindowToDB(self.cbcycleoptimize)
		gui.wx.Data.bindWindowToDB(self.cbcyclemagonly)

	def onPauseNum(self, evt):
		self.node.pause = evt.GetValue()

	def onXYOnlyCheck(self, evt):
		self.node.xyonly = evt.IsChecked()

	def onStageAlwaysCheck(self, evt):
		self.node.stagealways = evt.IsChecked()

	def onCycleCheck(self, evt):
		self.node.cycleon = evt.IsChecked()

	def onOptimizeCheck(self, evt):
		self.node.cycleoptimize = evt.IsChecked()

	def onMagOnlyCheck(self, evt):
		self.node.cyclemagonly = evt.IsChecked()

	def onCycleOrderChanged(self, evt):
		self.node.setCycleOrder(evt.presets)

	def onSetOrder(self, presets, setorder=True):
		evt = PresetsChangedEvent(presets)
		self.cpreset.GetEventHandler().AddPendingEvent(evt)
		if setorder:
			evt = PresetsChangedEvent(presets)
			self.cycleorder.GetEventHandler().AddPendingEvent(evt)

	def setDoseValue(self, dosestring):
		evt = SetDoseValueEvent(dosestring)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetDoseValue(self, evt):
		self.stimagedose.SetLabel(evt.dosestring)

	def onAcquireDoseImage(self, evt):
		self.node.acquireDoseImage()

	def onImport(self, evt):
		dialog = ImportDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onNew(self, evt):
		dialog = NewDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.newFromScope(dialog.name)
		dialog.Destroy()

	def _getParameters(self):
		parameters = {}
		parameters['magnification'] = int(self.ncmagnification.GetValue())
		parameters['defocus'] = float(self.ncdefocus.GetValue())
		parameters['spot size'] = int(self.ncspotsize.GetValue())
		parameters['intensity'] = float(self.ncintensity.GetValue())
		parameters['image shift'] = {}
		parameters['image shift']['x'] = float(self.ncimageshiftx.GetValue())
		parameters['image shift']['y'] = float(self.ncimageshifty.GetValue())
		parameters['beam shift'] = {}
		parameters['beam shift']['x'] = float(self.ncbeamshiftx.GetValue())
		parameters['beam shift']['y'] = float(self.ncbeamshifty.GetValue())
		parameters['film'] = self.cbfilm.GetValue()
		dose = self.stdose.GetLabel()
		if not dose or dose == 'N/A':
			dose = None
		else:
			# oops
			dose = float(dose)*1e20
		parameters.update(self.cpcamconfig.getConfiguration())
		return parameters

	def onUpdateParameters(self, evt=None):
		if self.cpreset.GetSelection() >= 0:
			self.node.updateParams(self._getParameters())

	def _setParameters(self, parameters):
		self.ncmagnification.SetValue(parameters['magnification'])
		self.ncdefocus.SetValue(parameters['defocus'])
		self.ncspotsize.SetValue(parameters['spot size'])
		self.ncintensity.SetValue(parameters['intensity'])
		self.ncimageshiftx.SetValue(parameters['image shift']['x'])
		self.ncimageshifty.SetValue(parameters['image shift']['y'])
		self.ncbeamshiftx.SetValue(parameters['beam shift']['x'])
		self.ncbeamshifty.SetValue(parameters['beam shift']['y'])
		self.cbfilm.SetValue(parameters['film'])
		if parameters['dose'] is None:
			dose = 'N/A'
		else:
			dose = '%.4f' % (parameters['dose']/1e20,)
		self.stdose.SetLabel(dose)
		self.cpcamconfig.setConfiguration(parameters)

	def onSetParameters(self, evt):
		self._setParameters(evt.parameters)

	def setParameters(self, parameters):
		evt = SetParametersEvent(parameters.toDict(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def _setCalibrations(self, times):
		items = {
			'pixel size': self.stpixelsize,
			'image shift': self.stimageshift,
			'stage': self.ststage,
			'beam': self.stbeamshift,
			'modeled stage': self.stmodeled,
			'modeled stage mag only': self.stmodeledmagonly,
		}
		for key, value in items.items():
			try:
				value.SetLabel(times[key])
			except KeyError:
				pass

	def onSetCalibrations(self, evt):
		self._setCalibrations(evt.times)

	def setCalibrations(self, times):
		evt = SetCalibrationsEvent(times, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetChoice(self, evt):
		self.node.selectPreset(evt.GetString())

	def onToScope(self, evt):
		self.node.cycleToScope(self.cpreset.GetStringSelection())

	def onFromScope(self, evt):
		self.node.fromScope(self.cpreset.GetStringSelection())

	def onRemove(self, evt):
		self.node.removePreset(self.cpreset.GetStringSelection())

class NewDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Create New Preset')

		stdesc = wx.StaticText(self, -1,
														'Create a new preset from the current scope state')
		stname = wx.StaticText(self, -1, 'Preset name:')
		self.tcname = wx.TextCtrl(self, -1, '')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stdesc, (0, 0), (1, 2), wx.ALIGN_CENTER)
		sz.Add(stname, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.tcname, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		bcreate = wx.Button(self, wx.ID_OK, 'Create')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bcreate, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		szmain.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onCreate, bcreate)

	def onCreate(self, evt):
		name = self.tcname.GetValue()
		if not name or name in self.GetParent().node.presets:
			dialog = wx.MessageDialog(self, 'Invalid preset name', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.name = name
			evt.Skip()

class ImportDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Import Presets')
		self.presets = None

		stdesc = wx.StaticText(self, -1,
														'Select a session to import presets from.')
		self.stpresets = wx.StaticText(self, -1, '(No session selected.)')
		stsession = wx.StaticText(self, -1, 'Session:')
		self.csession = wx.Choice(self, -1, choices=self._getSessionNames())

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stdesc, (0, 0), (1, 2), wx.ALIGN_CENTER)
		sz.Add(self.stpresets, (1, 0), (1, 2), wx.ALIGN_CENTER)
		sz.Add(stsession, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.csession, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		bimport = wx.Button(self, wx.ID_OK, 'Import')
		bdone = wx.Button(self, wx.ID_CANCEL, 'Done')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bimport, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bdone, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain = wx.GridBagSizer(5, 5)
		self.szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		self.szmain.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(self.szmain)

		self.Bind(wx.EVT_BUTTON, self.onImport, bimport)
		self.Bind(wx.EVT_CHOICE, self.onSessionChoice, self.csession)

	def _getSessionNames(self):
		return self.GetParent().node.sessiondict.keys()

	def onSessionChoice(self, evt=None):
		if evt is None:
			name = self.csession.GetStringSelection()
		else:
			name = evt.GetString()
		self.presets = self.GetParent().node.getSessionPresets(name)
		presetnames = self.presets.keys()
		if presetnames:
			label = ', '.join(presetnames)
		else:
			label = 'No presets in selected session.'
		self.stpresets.SetLabel(label)
		self.szmain.Layout()

	def onImport(self, evt):
		if self.presets:
			self.GetParent().node.importPresets(self.presets)
		else:
			dialog = wx.MessageDialog(self, 'No presets to import', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Presets Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

