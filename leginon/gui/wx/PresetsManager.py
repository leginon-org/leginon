# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/PresetsManager.py,v $
# $Revision: 1.26 $
# $Name: not supported by cvs2svn $
# $Date: 2004-11-11 19:43:17 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import data
import newdict
import threading
import wx
from gui.wx.Entry import FloatEntry, EVT_ENTRY
import gui.wx.Camera
import gui.wx.Dialog
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Presets
import gui.wx.Settings
import gui.wx.ToolBar

PresetsEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()
SetDoseValueEventType = wx.NewEventType()
SetCalibrationsEventType = wx.NewEventType()

EVT_PRESETS = wx.PyEventBinder(PresetsEventType)
EVT_SET_DOSE_VALUE = wx.PyEventBinder(SetDoseValueEventType)
EVT_SET_CALIBRATIONS = wx.PyEventBinder(SetCalibrationsEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)

class PresetsEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, PresetsEventType, source.GetId())
		self.SetEventObject(source)

class SetParametersEvent(wx.PyCommandEvent):
	def __init__(self, parameters, source):
		wx.PyCommandEvent.__init__(self, SetParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters

class SetDoseValueEvent(wx.PyEvent):
	def __init__(self, dose):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetDoseValueEventType)
		self.dose = dose

class SetCalibrationsEvent(wx.PyCommandEvent):
	def __init__(self, times, source):
		wx.PyCommandEvent.__init__(self, SetCalibrationsEventType, source.GetId())
		self.SetEventObject(source)
		self.times = times

class Calibrations(wx.StaticBoxSizer):
	def __init__(self, parent):
		sb = wx.StaticBox(parent, -1, 'Calibrations')
		wx.StaticBoxSizer.__init__(self, sb, wx.VERTICAL)

		self.order = [
			('pixel size', 'Pixel size'),
			('image shift', 'Image shift'),
			('stage', 'Stage'),
			('beam', 'Beam shift'),
			('modeled stage', 'Modeled stage'),
			('modeled stage mag only', 'Modeled stage (mag. only)'),
		]

		self.sts = {}
		sz = wx.GridBagSizer(0, 5)
		for i, (name, label) in enumerate(self.order):
			stlabel = wx.StaticText(parent, -1, label)
			self.sts[name] = wx.StaticText(parent, -1, '')
			sz.Add(stlabel, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			sz.Add(self.sts[name], (i, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		self.Add(sz, 1, wx.EXPAND|wx.ALL, 3)

	def set(self, times):
		for name, label in self.order:
			try:
				self.sts[name].SetLabel(times[name])
			except (TypeError, KeyError):
				self.sts[name].SetLabel('None')
		self.Layout()

class Parameters(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1)

		stmag = wx.StaticText(self, -1, 'Magnification')
		stdefocus = wx.StaticText(self, -1, 'Defocus')
		stspotsize = wx.StaticText(self, -1, 'Spot size')
		stintensity = wx.StaticText(self, -1, 'Intensity')
		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stimageshift = wx.StaticText(self, -1, 'Image shift')
		stbeamshift = wx.StaticText(self, -1, 'Beam shift')
		stdose = wx.StaticText(self, -1, 'Dose:')

		self.femag = FloatEntry(self, -1, chars=9)
		self.fedefocus = FloatEntry(self, -1, chars=9)
		self.fespotsize = FloatEntry(self, -1, chars=2)
		self.feintensity = FloatEntry(self, -1, chars=9)
		self.feimageshiftx = FloatEntry(self, -1, chars=9)
		self.feimageshifty = FloatEntry(self, -1, chars=9)
		self.febeamshiftx = FloatEntry(self, -1, chars=9)
		self.febeamshifty = FloatEntry(self, -1, chars=9)
		self.cbfilm = wx.CheckBox(self, -1, 'Film')
		self.stdose = wx.StaticText(self, -1, '')
		self.cpcamconfig = gui.wx.Camera.CameraPanel(self)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stmag, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.femag, (0, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(stdefocus, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.fedefocus, (1, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(stspotsize, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.fespotsize, (2, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(stintensity, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.feintensity, (3, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(stx, (4, 1), (1, 1), wx.ALIGN_CENTER)
		sz.Add(sty, (4, 2), (1, 1), wx.ALIGN_CENTER)
		sz.Add(stimageshift, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.feimageshiftx, (5, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(self.feimageshifty, (5, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(stbeamshift, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.febeamshiftx, (6, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(self.febeamshifty, (6, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(self.cbfilm, (0, 3), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(stdose, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.stdose, (1, 4), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.cpcamconfig, (2, 3), (5, 2), wx.ALIGN_CENTER)

		sb = wx.StaticBox(self, -1, 'Parameters')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 3)

		self.SetSizerAndFit(sbsz)

	def get(self):
		parameters = {}
		parameters['magnification'] = int(self.femag.GetValue())
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
			dose = float(dose)
		parameters.update(self.cpcamconfig.getConfiguration())
		return parameters

	def set(self, parameters):
		if parameters is None:
			self.femag.SetValue(None)
			self.fedefocus.SetValue(None)
			self.fespotsize.SetValue(None)
			self.feintensity.SetValue(None)
			self.feimageshiftx.SetValue(None)
			self.feimageshifty.SetValue(None)
			self.febeamshiftx.SetValue(None)
			self.febeamshifty.SetValue(None)
			self.cbfilm.SetValue(False)
			self.stdose.SetLabel('')
			self.cpcamconfig.clear()
		else:
			self.femag.SetValue(parameters['magnification'])
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
				dose = '%e' % (parameters['dose'],)
			self.stdose.SetLabel(dose)

			try:
				self.cpcamconfig.setConfiguration(parameters)
			except ValueError:
				# cam config bad, do something...
				pass

	def bind(self, method):
		self.Bind(EVT_ENTRY, method, self.femag)
		self.Bind(EVT_ENTRY, method, self.fedefocus)
		self.Bind(EVT_ENTRY, method, self.fespotsize)
		self.Bind(EVT_ENTRY, method, self.feintensity)
		self.Bind(EVT_ENTRY, method, self.feimageshiftx)
		self.Bind(EVT_ENTRY, method, self.feimageshifty)
		self.Bind(EVT_ENTRY, method, self.febeamshiftx)
		self.Bind(EVT_ENTRY, method, self.febeamshifty)
		self.Bind(wx.EVT_CHECKBOX, method, self.cbfilm)
		self.Bind(gui.wx.Camera.EVT_CONFIGURATION_CHANGED, method, self.cpcamconfig)

class EditPresets(gui.wx.Presets.PresetOrder):
	def _widgets(self):
		gui.wx.Presets.PresetOrder._widgets(self, 'Presets (Cycle Order)')
		self.btoscope = self._bitmapButton('instrumentset',
																				'Go to the selected preset')
		self.bacquire = self._bitmapButton('acquire',
																	'Acquire dose image for the selected preset')
		self.bfromscope = self._bitmapButton('instrumentget',
							'Overwrite the selected preset with the current instrument state')
		self.bremove = self._bitmapButton('minus', 'Remove the selected preset')

		self.bnewfromscope = self._bitmapButton('instrumentgetnew',
												'Create a new preset from the current instrument state')
		self.bnewfromscope.Enable(True)
		self.bimport = self._bitmapButton('import',
																			'Import presets from another session')
		self.bimport.Enable(True)

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.listbox, (1, 0), (11, 1), wx.EXPAND)
		sizer.Add(self.upbutton, (1, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.downbutton, (2, 1), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.btoscope, (4, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bacquire, (6, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bfromscope, (7, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bremove, (8, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bnewfromscope, (10, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bimport, (11, 1), (1, 1), wx.ALIGN_CENTER)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		gui.wx.Presets.PresetOrder._bind(self)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)

	def onRemove(self, evt):
		n = self.listbox.GetSelection()
		if n < 0:
			return
		presetname = self.listbox.GetString(n)
		self.listbox.Delete(n)
		self.presetRemoved(presetname)

		count = self.listbox.GetCount()
		if n < count:
			self.listbox.Select(n)
		elif count > 0:
			self.listbox.Select(n - 1)
		n = self.listbox.GetSelection()
		self.updateButtons(n)
		if n < 0:
			presetname = ''
		else:
			presetname = self.listbox.GetString(n)
		self.presetSelected(presetname)
		self.presetOrderChanged()

	def setChoices(self, choices):
		gui.wx.Presets.PresetOrder.setChoices(self, choices)

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
		self.presetOrderChanged()

	def updateButtons(self, n):
		gui.wx.Presets.PresetOrder.updateButtons(self, n)
		if n >= 0:
			self.btoscope.Enable(True)
			self.bacquire.Enable(True)
			self.bfromscope.Enable(True)
			self.bremove.Enable(True)
		else:
			self.btoscope.Enable(False)
			self.bacquire.Enable(False)
			self.bfromscope.Enable(False)
			self.bremove.Enable(False)

class DoseDialog(gui.wx.Dialog.Dialog):
	def __init__(self, parent):
		gui.wx.Dialog.Dialog.__init__(self, parent, 'Dose Image', 'Dose Image')
		self.dose = None

	def onInitialize(self):
		gui.wx.Dialog.Dialog.onInitialize(self)

		self.image = gui.wx.ImageViewer.ImagePanel(self, -1)

		self.doselabel = wx.StaticText(self, -1, '')

		self.sz.Add(self.image, (0, 0), (1, 1), wx.EXPAND)
		self.sz.Add(self.doselabel, (1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)

		self.addButton('Yes', wx.ID_OK)
		self.addButton('No', wx.ID_CANCEL)

	def setDose(self, dose):
		self.dose = dose
		if dose is None:
			dosestr = 'N/A'
		else:
			dosestr = '%e' % (dose/1e20)
		dosestr = 'Use the measured dose %s for this preset?' % dosestr
		self.doselabel.SetLabel(dosestr)

class Panel(gui.wx.Node.Panel):
	icon = 'presets'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		# presets

		self.calibrations = Calibrations(self)
		self.calibrations.set({})
		self.parameters = Parameters(self)
		self.parameters.Enable(False)
		self.presets = EditPresets(self, -1)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(self.calibrations, (0, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.sz.Add(self.parameters, (1, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.sz.Add(self.presets, (0, 0), (2, 1), wx.ALIGN_CENTER)
		self.szmain.Add(self.sz, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 5)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(EVT_SET_CALIBRATIONS, self.onSetCalibrations)
		self.Bind(EVT_SET_DOSE_VALUE, self.onSetDoseValue)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

		self.parameters.cpcamconfig.setSize(self.node.session)
		self.parameters.cpcamconfig.clear()
		self.parameters.bind(self.onUpdateParameters)

		self.Bind(gui.wx.Presets.EVT_PRESET_SELECTED,
							self.onPresetSelected, self.presets)
		self.Bind(gui.wx.Presets.EVT_PRESET_ORDER_CHANGED,
							self.onCycleOrderChanged, self.presets)
		self.Bind(gui.wx.Presets.EVT_PRESET_REMOVED,
							self.onRemove, self.presets)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.presets.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.presets.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onNewFromScope, self.presets.bnewfromscope)

		self.importdialog = ImportDialog(self, self.node)
		self.Bind(wx.EVT_BUTTON, self.onImport, self.presets.bimport)

		self.dosedialog = DoseDialog(self)
		self.Bind(wx.EVT_BUTTON, self.onAcquireDoseImage, self.presets.bacquire)

		self.Bind(EVT_PRESETS, self.onPresets)

	def _presetsEnable(self, enable):
		self.toolbar.Enable(enable)
		self.parameters.Enable(enable)
		self.presets.Enable(enable)
		self.importdialog.Enable(enable)

	def onPresets(self, evt):
		self._presetsEnable(True)

	def presetsEvent(self):
		evt = PresetsEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onCycleOrderChanged(self, evt):
		self._presetsEnable(False)
		target = self.node.setCycleOrder
		args = (evt.presets,)
		threading.Thread(target=target, args=args).start()

	def setOrder(self, presets, setorder=True):
		if setorder:
			evt = gui.wx.Presets.PresetsChangedEvent(presets)
			self.presets.GetEventHandler().AddPendingEvent(evt)

	def setDoseValue(self, dose):
		evt = SetDoseValueEvent(dose)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetImage(self, evt):
		self.dosedialog.image.setImage(evt.image)
		if not self.dosedialog.IsShown():
			if self.dosedialog.ShowModal() == wx.ID_OK:
				self.node.saveDose(self.dosedialog.dose,
														self.presets.getSelectedPreset())
			self.dosedialog.image.setImage(None)

	def onSetDoseValue(self, evt):
		self.dosedialog.setDose(evt.dose)

	def onAcquireDoseImage(self, evt):
		presetname = self.presets.getSelectedPreset()
		self._presetsEnable(False)
		target = self.node.acquireDoseImage
		args = (presetname,)
		threading.Thread(target=target, args=args).start()

	def onImport(self, evt):
		self.importdialog.ShowModal()

	def onFromScope(self, evt):
		name = self.presets.getSelectedPreset()
		self._presetsEnable(False)
		target = self.node.fromScope
		args = (name,)
		threading.Thread(target=target, args=args).start()

	def onNewFromScope(self, evt):
		dialog = NewDialog(self, self.node)
		if dialog.ShowModal() == wx.ID_OK:
			self._presetsEnable(False)
			target = self.node.fromScope
			args = (dialog.name,)
			threading.Thread(target=target, args=args).start()
		dialog.Destroy()

	def onUpdateParameters(self, evt=None):
		self.node.updateParams(self.parameters.get())

	def onSetParameters(self, evt):
		self.parameters.set(evt.parameters)

	def setParameters(self, parameters):
		if isinstance(parameters, data.Data):
			parameters = parameters.toDict()
		evt = SetParametersEvent(parameters, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetCalibrations(self, evt):
		self.calibrations.set(evt.times)

	def setCalibrations(self, times):
		evt = SetCalibrationsEvent(times, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetSelected(self, evt):
		selection = evt.GetString()
		if selection:
			self.node.selectPreset(selection)
			self.parameters.Enable(True)
		else:
			self.calibrations.set({})
			self.parameters.set(None)
			self.parameters.Enable(False)

	def onToScope(self, evt):
		self._presetsEnable(False)
		target = self.node.cycleToScope
		pname = self.node.currentselection['name']
		args = (pname,)
		threading.Thread(target=target, args=args).start()

	def onRemove(self, evt):
		self._presetsEnable(False)
		target = self.node.removePreset
		args = (evt.presetname,)
		threading.Thread(target=target, args=args).start()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['xy only'] = wx.CheckBox(self, -1,
#																					'Move stage x and y axes only')
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
#		sz.Add(self.widgets['xy only'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stage always'], (1, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['cycle'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['optimize cycle'], (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mag only'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Preset Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class NewDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Create New Preset')
		self.node = node

		stname = wx.StaticText(self, -1, 'Preset name:')
		self.tcname = wx.TextCtrl(self, -1, '')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stname, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.tcname, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

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
		if not name or name in self.node.presets:
			dialog = wx.MessageDialog(self, 'Invalid preset name', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.name = name
			evt.Skip()

class ImportDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Import Presets')
		self.node = node
		self.presets = None

		sessionnames = self.node.getSessions()
		self.csession = wx.Choice(self, -1, choices=sessionnames)
		self.lbpresets = wx.ListBox(self, -1, style=wx.LB_EXTENDED)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Session:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.csession, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Presets:')
		sz.Add(label, (1, 0), (1, 1))
		sz.Add(self.lbpresets, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		self.bimport = wx.Button(self, -1, 'Import')
		self.bimport.Enable(False)
		bdone = wx.Button(self, wx.ID_OK, 'Done')
		bdone.SetDefault()

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bimport, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bdone, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain = wx.GridBagSizer(5, 5)
		self.szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 10)
		self.szmain.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, 5)

		self.SetSizerAndFit(self.szmain)

		self.Bind(wx.EVT_CHOICE, self.onSessionChoice, self.csession)
		self.Bind(wx.EVT_LISTBOX, self.onPresetsListBox, self.lbpresets)
		self.Bind(wx.EVT_BUTTON, self.onImport, self.bimport)

	def onSessionChoice(self, evt=None):
		if evt is None:
			name = self.csession.GetStringSelection()
		else:
			name = evt.GetString()
		self.presets = self.node.getSessionPresets(name)
		presetnames = self.presets.keys()
		self.lbpresets.Clear()
		if presetnames:
			self.lbpresets.AppendItems(presetnames)
			self.lbpresets.Enable(True)
		else:
			self.lbpresets.Enable(False)

	def onPresetsListBox(self, evt):
		if self.lbpresets.GetSelections():
			self.bimport.Enable(True)
		else:
			self.bimport.Enable(False)

	def onImport(self, evt):
		self.bimport.Enable(False)
		presets = newdict.OrderedDict()
		selections = self.lbpresets.GetSelections()
		for i in selections:
			name = self.lbpresets.GetString(i)
			presets[name] = self.presets[name]
			self.lbpresets.Deselect(i)
		target = self.node.importPresets
		args = (presets,)
		threading.Thread(target=target, args=args).start()

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

