import wx
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Camera
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Presets
import gui.wx.Settings
import gui.wx.ToolBar

SetParametersEventType = wx.NewEventType()
SetDoseValueEventType = wx.NewEventType()
SetCalibrationsEventType = wx.NewEventType()

EVT_SET_DOSE_VALUE = wx.PyEventBinder(SetDoseValueEventType)
EVT_SET_CALIBRATIONS = wx.PyEventBinder(SetCalibrationsEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)

class SetParametersEvent(wx.PyCommandEvent):
	def __init__(self, parameters, source):
		wx.PyCommandEvent.__init__(self, SetParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters

class SetDoseValueEvent(wx.PyEvent):
	def __init__(self, dosestring):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetDoseValueEventType)
		self.dosestring = dosestring

class SetCalibrationsEvent(wx.PyCommandEvent):
	def __init__(self, times, source):
		wx.PyCommandEvent.__init__(self, SetCalibrationsEventType, source.GetId())
		self.SetEventObject(source)
		self.times = times

class Panel(gui.wx.Node.Panel):
	icon = 'presets'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		# presets

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
		szcalibrations.AddGrowableCol(0)

		sb = wx.StaticBox(self, -1, 'Calibrations')
		self.sbszcalibrations = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.sbszcalibrations.Add(szcalibrations, 1,
															wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		stmagnification = wx.StaticText(self, -1, 'Magnification')
		self.femagnification = FloatEntry(self, -1, chars=9)
		stdefocus = wx.StaticText(self, -1, 'Defocus')
		self.fedefocus = FloatEntry(self, -1, chars=9)
		stspotsize = wx.StaticText(self, -1, 'Spot size')
		self.fespotsize = FloatEntry(self, -1, chars=2)
		stintensity = wx.StaticText(self, -1, 'Intensity')
		self.feintensity = FloatEntry(self, -1, chars=9)
		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stimageshift = wx.StaticText(self, -1, 'Image shift')
		self.feimageshiftx = FloatEntry(self, -1, chars=9)
		self.feimageshifty = FloatEntry(self, -1, chars=9)

		stbeamshift = wx.StaticText(self, -1, 'Beam shift')
		self.febeamshiftx = FloatEntry(self, -1, chars=9)
		self.febeamshifty = FloatEntry(self, -1, chars=9)

		self.cbfilm = wx.CheckBox(self, -1, 'Film')
		stdose = wx.StaticText(self, -1, 'Dose:')
		self.stdose = wx.StaticText(self, -1, '')

		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		szparameters = wx.GridBagSizer(5, 5)
		szparameters.Add(stmagnification, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.femagnification, (0, 1), (1, 2),
											wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szparameters.Add(stdefocus, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.fedefocus, (1, 1), (1, 2),
											wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szparameters.Add(stspotsize, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.fespotsize, (2, 1), (1, 2),
											wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szparameters.Add(stintensity, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.feintensity, (3, 1), (1, 2),
											wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		szparameters.Add(stx, (4, 1), (1, 1), wx.ALIGN_CENTER)
		szparameters.Add(sty, (4, 2), (1, 1), wx.ALIGN_CENTER)
		szparameters.Add(stimageshift, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.feimageshiftx, (5, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szparameters.Add(self.feimageshifty, (5, 2), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szparameters.Add(stbeamshift, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.febeamshiftx, (6, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szparameters.Add(self.febeamshifty, (6, 2), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		szparameters.Add(self.cbfilm, (7, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(stdose, (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.stdose, (8, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		szparameters.Add(self.cpcamconfig, (9, 0), (1, 3), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Parameters')
		sbszparameters = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszparameters.Add(szparameters, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		self.cycleorder = gui.wx.Presets.PresetOrder(self, -1)
		self.btoscope = wx.Button(self, -1, 'To Scope')
		self.bfromscope = wx.Button(self, -1, 'From Scope')
		self.bremove = wx.Button(self, -1, 'Remove')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.cycleorder, (0, 0), (1, 1), wx.ALIGN_CENTER)
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

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(self.sbszcalibrations, (0, 0), (1, 2), wx.EXPAND|wx.ALL)
		self.sz.Add(sbszparameters, (1, 1), (2, 1), wx.EXPAND|wx.ALL)
		self.sz.Add(sz, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add(sbszcreate, (2, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(self.sz, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 5)

		# dose image
		self.szdoseimage = self._getStaticBoxSizer('Dose Image', (1, 1), (3, 1),
																								wx.EXPAND|wx.ALL)
		stimagedose = wx.StaticText(self, -1, 'Dose:')
		self.stimagedose = wx.StaticText(self, -1, '')

		self.bacquire = wx.Button(self, -1, 'Acquire')

		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)

		self.szdoseimage.Add(stimagedose, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.stimagedose, (0, 1), (1, 1),
													wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.bacquire, (0, 2), (1, 1),
													wx.ALIGN_CENTER_VERTICAL)
		self.szdoseimage.Add(self.imagepanel, (1, 0), (1, 3), wx.ALIGN_CENTER)
		self.szdoseimage.AddGrowableCol(2)

		self.szmain.AddGrowableCol(1)
		self.szmain.AddGrowableRow(3)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(gui.wx.Presets.EVT_PRESET_ORDER_CHANGED, self.onCycleOrderChanged,
							self.cycleorder)
		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(EVT_SET_CALIBRATIONS, self.onSetCalibrations)
		self.Bind(EVT_SET_DOSE_VALUE, self.onSetDoseValue)

	def onNodeInitialized(self):
		self.cpcamconfig.setSize(self.node.session)

		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

		self.Bind(wx.EVT_BUTTON, self.onAcquireDoseImage, self.bacquire)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.femagnification)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.fedefocus)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.fespotsize)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.feintensity)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.feimageshiftx)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.feimageshifty)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.febeamshiftx)
		self.Bind(EVT_ENTRY, self.onUpdateParameters, self.febeamshifty)
		self.Bind(wx.EVT_CHECKBOX, self.onUpdateParameters, self.cbfilm)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, self.onUpdateParameters,
							self.cpcamconfig)
		self.Bind(gui.wx.Presets.EVT_PRESET_SELECTED, self.onPresetSelected,
							self.cycleorder)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)
		self.Bind(wx.EVT_BUTTON, self.onImport, self.bimport)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onCycleOrderChanged(self, evt):
		self.node.setCycleOrder(evt.presets)

	def onSetOrder(self, presets, setorder=True):
		if setorder:
			evt = gui.wx.Presets.PresetsChangedEvent(presets)
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
		parameters['magnification'] = int(self.femagnification.GetValue())
		parameters['defocus'] = float(self.fedefocus.GetValue())
		parameters['spot size'] = int(self.fespotsize.GetValue())
		parameters['intensity'] = float(self.feintensity.GetValue())
		parameters['image shift'] = {}
		parameters['image shift']['x'] = float(self.feimageshiftx.GetValue())
		parameters['image shift']['y'] = float(self.feimageshifty.GetValue())
		parameters['beam shift'] = {}
		parameters['beam shift']['x'] = float(self.febeamshiftx.GetValue())
		parameters['beam shift']['y'] = float(self.febeamshifty.GetValue())
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
		if self.cycleorder.getSelectedPreset() is not None:
			self.node.updateParams(self._getParameters())

	def _setParameters(self, parameters):
		self.femagnification.SetValue(parameters['magnification'])
		self.fedefocus.SetValue(parameters['defocus'])
		self.fespotsize.SetValue(parameters['spot size'])
		self.feintensity.SetValue(parameters['intensity'])
		self.feimageshiftx.SetValue(parameters['image shift']['x'])
		self.feimageshifty.SetValue(parameters['image shift']['y'])
		self.febeamshiftx.SetValue(parameters['beam shift']['x'])
		self.febeamshifty.SetValue(parameters['beam shift']['y'])
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
			except (TypeError, KeyError):
				value.SetLabel('None')
		self.sbszcalibrations.Layout()

	def onSetCalibrations(self, evt):
		self._setCalibrations(evt.times)

	def setCalibrations(self, times):
		evt = SetCalibrationsEvent(times, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetSelected(self, evt):
		self.node.selectPreset(evt.GetString())

	def onToScope(self, evt):
		self.node.cycleToScope(self.cycleorder.getSelectedPreset())

	def onFromScope(self, evt):
		self.node.fromScope(self.cycleorder.getSelectedPreset())

	def onRemove(self, evt):
		self.node.removePreset(self.cycleorder.getSelectedPreset())

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['xy only'] = wx.CheckBox(self, -1,
																					'Move stage x and y axes only')
		self.widgets['stage always'] = wx.CheckBox(self, -1,
																		'Always move stage regardless of move type')
		self.widgets['cycle'] = wx.CheckBox(self, -1, 'Cycle presets')
		self.widgets['optimize cycle'] = wx.CheckBox(self, -1,
																									'Optimize preset cycle')
		self.widgets['mag only'] = wx.CheckBox(self, -1, 'Cycle magnification only')

		szpausetime = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Pause')
		szpausetime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds between preset changes')
		szpausetime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(szpausetime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['xy only'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stage always'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['cycle'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['optimize cycle'], (4, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mag only'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Preset Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

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

