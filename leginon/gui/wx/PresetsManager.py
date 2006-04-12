# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/PresetsManager.py,v $
# $Revision: 1.67 $
# $Name: not supported by cvs2svn $
# $Date: 2006-04-12 17:31:27 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import copy
import data
import instrument
import newdict
import threading
import wx
from gui.wx.Entry import IntEntry, FloatEntry, EVT_ENTRY
import gui.wx.Camera
import gui.wx.Dialog
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Presets
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Dialog
import gui.wx.Instrument
from wx.lib.mixins.listctrl import ColumnSorterMixin

PresetsEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()
SetDoseValueEventType = wx.NewEventType()
SetCalibrationsEventType = wx.NewEventType()
EditPresetEventType = wx.NewEventType()

EVT_PRESETS = wx.PyEventBinder(PresetsEventType)
EVT_SET_DOSE_VALUE = wx.PyEventBinder(SetDoseValueEventType)
EVT_SET_CALIBRATIONS = wx.PyEventBinder(SetCalibrationsEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)
EVT_EDIT_PRESET = wx.PyEventBinder(EditPresetEventType)

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

class EditPresetEvent(wx.PyCommandEvent):
	def __init__(self, source, presetname):
		wx.PyCommandEvent.__init__(self, EditPresetEventType, source.GetId())
		self.SetEventObject(source)
		self.presetname = presetname

class Calibrations(wx.StaticBoxSizer):
	def __init__(self, parent):
		sb = wx.StaticBox(parent, -1, 'Most Recent Calibrations')
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
			except (TypeError, KeyError), e:
				self.sts[name].SetLabel('None')
		self.Layout()

class EditPresetDialog(gui.wx.Dialog.Dialog):
	def __init__(self, parent, parameters, tems, ccd_cameras, node):
		self.parameters = parameters
		self.tems = tems
		self.ccd_cameras = ccd_cameras
		self.node = node

		try:
			title =  'Edit Preset %s' % parameters['name']
		except KeyError:
			raise ValueError
		gui.wx.Dialog.Dialog.__init__(self, parent, title, 'Preset Parameters')

	def getMagChoices(self):
		try:
			mags = self.tems[self.parameters['tem']['name']]
		except:
			mags = []
		return [str(int(m)) for m in mags]

	def getTEMChoices(self):
		choices = self.tems.keys()
		choices.sort()
		return [self.nonestring] + choices

	def getCCDCameraChoices(self):
		choices = self.ccd_cameras.keys()
		choices.sort()
		return [self.nonestring] + choices

	def onInitialize(self):
		parameters = self.parameters
		self.nonestring = '(None)'

		tems = self.getTEMChoices()
		magnifications = self.getMagChoices()
		ccdcameras = self.getCCDCameraChoices()
		self.choices = {
			'tem': wx.Choice(self, -1, choices=tems),
			'magnification': wx.Choice(self, -1, choices=magnifications),
			'ccdcamera': wx.Choice(self, -1, choices=ccdcameras),
		}

		self.floats = {
			'defocus': FloatEntry(self, -1, chars=9),
			'spot size': FloatEntry(self, -1, chars=2),
			'intensity': FloatEntry(self, -1, chars=9),
			'image shift': {
				'x': FloatEntry(self, -1, chars=9),
				'y': FloatEntry(self, -1, chars=9),
			},
			'beam shift': {
				'x': FloatEntry(self, -1, chars=9),
				'y': FloatEntry(self, -1, chars=9),
			},
			'energy filter width': FloatEntry(self, -1, chars=6),
			'pre exposure': FloatEntry(self, -1, chars=6),
		}

		self.bools = {
			'film': wx.CheckBox(self, -1, 'Use film'),
			'skip': wx.CheckBox(self, -1, 'Skip when cycling'),
			'energy filter': wx.CheckBox(self, -1, 'Energy filtered'),
		}

		self.dicts = {
			'camera parameters': gui.wx.Camera.CameraPanel(self),
		}

		buttons = {
			'tem': (
				'magnification', 
				'defocus',
				'spot size',
				'intensity',
				'image shift',
				'beam shift',
			),
			'ccdcamera': (
				'energy filter',
				'energy filter width',
				'camera parameters',
			),
		}
		self._buttons = {}
		for key in ['tem', 'ccdcamera']:
			self._buttons[key] = {}
			for name in buttons[key]:
				button =  bitmapButton(self, 'instrumentget', 'Set this value from the instrument value')
				self._buttons[key][name] = button
				self.Bind(wx.EVT_BUTTON, self.onButton, button)

			if key in parameters and parameters[key] is not None:
				value = parameters[key]
				if self.choices[key].FindString(value['name']) == wx.NOT_FOUND:
					self.choices[key].Append(value['name'])
				self.choices[key].SetStringSelection(value['name'])
				enable_buttons = True
			else:
				self.choices[key].SetStringSelection(self.nonestring)
				enable_buttons = False

			for value in self._buttons[key].values():
				value.Enable(enable_buttons)

		self.setParameters(parameters)

		labels = (
    		('tem', 'TEM'),
    		('magnification', 'Magnification'),
    		('defocus', 'Defocus'),
    		('spot size', 'Spot size'),
    		('intensity', 'Intensity'),
    		('image shift', 'Image shift'),
    		('beam shift', 'Beam shift'),
    		('ccdcamera', 'CCD Camera'),
    		('energy filter width', 'Energy filter width'),
    		('pre exposure', 'Pre-exposure'),
		)

		self.labels = {}
		for key, text in labels:
			self.labels[key] = wx.StaticText(self, -1, text)

		sizer = wx.GridBagSizer(5, 5)
		sizer.Add(self.labels['tem'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['tem'], (0, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sizer.Add(self.labels['magnification'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['magnification'], (1, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sizer.Add(self._buttons['tem']['magnification'], (1, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['defocus'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['defocus'], (2, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['defocus'], (2, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['spot size'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['spot size'], (3, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['spot size'], (3, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['intensity'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['intensity'], (4, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['intensity'], (4, 3), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'x')
		sizer.Add(label, (5, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		sizer.Add(label, (5, 2), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['image shift'], (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['image shift']['x'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self.floats['image shift']['y'], (6, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['image shift'], (6, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['beam shift'], (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['beam shift']['x'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self.floats['beam shift']['y'], (7, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['beam shift'], (7, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bools['skip'], (9, 0), (1, 8), wx.ALIGN_CENTER)

		sizer.Add(self.labels['ccdcamera'], (0, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['ccdcamera'], (0, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.EXPAND)
		sizer.Add(self.bools['film'], (1, 5), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.bools['energy filter'], (2, 5), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(self._buttons['ccdcamera']['energy filter'], (2, 7), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.labels['energy filter width'], (3, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['energy filter width'], (3, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['ccdcamera']['energy filter width'], (3, 7), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.labels['pre exposure'], (4, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['pre exposure'], (4, 6), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)

		sizer.Add(self.dicts['camera parameters'], (5, 5), (4, 2), wx.ALIGN_CENTER)
		sizer.Add(self._buttons['ccdcamera']['camera parameters'], (5, 7), (4, 1), wx.ALIGN_CENTER)

		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(4)
		sizer.AddGrowableCol(5)
		for i in range(10):
			sizer.AddGrowableRow(i)

		self.sz.Add(sizer, (0, 0), (1, 1), wx.ALL|wx.EXPAND)
		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)

		self.addButton('Save', id=wx.ID_OK)
		self.addButton('Cancel', id=wx.ID_CANCEL)

		self.Bind(wx.EVT_CHOICE, self.onTEMChoice, self.choices['tem'])
		self.Bind(wx.EVT_CHOICE, self.onCCDCameraChoice, self.choices['ccdcamera'])

	def onButton(self, evt):
		event_button = evt.GetEventObject()
		for instrument_type in self._buttons:
			for name, button in self._buttons[instrument_type].items():
				if button is event_button:
					instrument_name = self.choices[instrument_type].GetStringSelection()
					try:
						target = self.node.getValue
						event = threading.Event()
						args = (instrument_type, instrument_name, name, event)
						threading.Thread(target=target, args=args).start()
						event.wait()
						value = self.node.last_value
						if name != 'camera parameters':
							value = {name: value} 
						self.setParameters(value)
					except:
						pass
					break

	def onTEMChoice(self, evt):
		mag = self.choices['magnification'].GetStringSelection()
		tem = evt.GetString()
		if tem == self.nonestring:
			choices = []
		else:
			try:
				mags = self.tems[tem]
				choices = [str(int(m)) for m in mags]
			except KeyError:
				choices = []
		for value in self._buttons['tem'].values():
			value.Enable(bool(choices))
    	#'energy filter',
		#'camera parameters',
		self.choices['magnification'].Freeze()
		self.choices['magnification'].Clear()
		self.choices['magnification'].AppendItems(choices)
		if self.choices['magnification'].FindString(mag) == wx.NOT_FOUND:
			if choices:
				self.choices['magnification'].SetSelection(0)
		else:
			self.choices['magnification'].SetStringSelection(mag)
		if self.choices['magnification'].IsEnabled():
			if not choices:
				self.choices['magnification'].Enable(False)
		else:
			if choices:
				self.choices['magnification'].Enable(True)
		self.choices['magnification'].Thaw()

	def onCCDCameraChoice(self, evt):
		ccdcamera = evt.GetString()
		try:
			camerasize = self.ccd_cameras[ccdcamera]
		except KeyError:
			camerasize = None
		self.dicts['camera parameters'].setSize(camerasize)
		for value in self._buttons['ccdcamera'].values():
			value.Enable(camerasize is not None)

	def setParameters(self, parameters):
		try:
			if parameters['magnification'] is not None:
				magnification = str(int(parameters['magnification']))
				if self.choices['magnification'].FindString(magnification) == wx.NOT_FOUND:
					self.choices['magnification'].Append(magnification)
				self.choices['magnification'].SetStringSelection(magnification)
		except KeyError:
			pass

		keys = (
			'defocus',
			'spot size',
			'intensity',
			'energy filter width',
			'pre exposure',
		)
		for key in keys:
			try:
				self.floats[key].SetValue(parameters[key])
			except KeyError:
				pass

		for key in ['image shift', 'beam shift']:
			for axis in ['x', 'y']:
				try:
					self.floats[key][axis].SetValue(parameters[key][axis])
				except KeyError:
					pass

		for key in ['skip', 'film', 'energy filter']:
			try:
				self.bools[key].SetValue(bool(parameters[key]))
			except KeyError:
				pass

		try:
			size = self.ccd_cameras[parameters['ccdcamera']['name']]
			self.dicts['camera parameters'].setSize(size)
		except:
			pass

		try:
			self.dicts['camera parameters'].setConfiguration(parameters)
		except KeyError:
			pass

	def getParameters(self):
		parameters = {}
		tem = self.choices['tem'].GetStringSelection()
		if tem == self.nonestring:
			tem = None
		parameters['tem'] = tem
		n = self.choices['magnification'].GetSelection()
		if n < 0:
			magnification = None
		else:
			magnification = int(self.choices['magnification'].GetString(n))
		parameters['magnification'] = magnification
		keys = [
			'defocus',
			'spot size',
			'intensity',
			'energy filter width',
			'pre exposure',
		]
		for key in keys:
			value = self.floats[key].GetValue()
			if value is not None:
				value = float(value)
			parameters[key] = value

		for key in ['image shift', 'beam shift']:
			parameters[key] = {}
			for axis in ['x', 'y']:
				value = self.floats[key][axis].GetValue()
				if value is not None:
					value = float(value)
				parameters[key][axis] = value

		for key in ['skip', 'film', 'energy filter']:
			parameters[key] = bool(self.bools[key].GetValue())

		ccdcamera = self.choices['ccdcamera'].GetStringSelection()
		if ccdcamera == self.nonestring:
			ccdcamera = None
		parameters['ccdcamera'] = ccdcamera
		parameters.update(self.dicts['camera parameters'].getConfiguration())

		return parameters

class EditPresets(gui.wx.Presets.PresetOrder):
	def _widgets(self):
		gui.wx.Presets.PresetOrder._widgets(self, 'Presets (Cycle Order)')
		self.btoscope = self._bitmapButton('instrumentset', 'To Scope')
		self.bedit = self._bitmapButton('edit', 'Edit the selected preset parameters')
		self.bacquire = self._bitmapButton('acquire', 'Acquire dose image for the selected preset')
		self.bfromscope = self._bitmapButton('instrumentget', 'From Scope')
		self.bremove = self._bitmapButton('minus', 'Remove the selected preset')

		self.bnewfromscope = self._bitmapButton('instrumentgetnew', 'Create a new preset from the current instrument state')
		self.bnewfromscope.Enable(True)
		self.bimport = self._bitmapButton('import', 'Import presets from another session')
		self.bimport.Enable(True)

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.listbox, (1, 0), (12, 1), wx.EXPAND)
		sizer.Add(self.upbutton, (1, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.downbutton, (2, 1), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.btoscope, (4, 1), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.bedit, (6, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bacquire, (7, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bfromscope, (8, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bremove, (9, 1), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.bnewfromscope, (11, 1), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bimport, (12, 1), (1, 1), wx.ALIGN_CENTER)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		gui.wx.Presets.PresetOrder._bind(self)
		self.Bind(wx.EVT_BUTTON, self.onEdit, self.bedit)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)

	def onEdit(self, evt):
		n = self.listbox.GetSelection()
		if n < 0:
			return
		presetname = self.listbox.GetString(n)
		evt = EditPresetEvent(self, presetname)
		self.GetEventHandler().AddPendingEvent(evt)

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
			self.bedit.Enable(True)
			self.bacquire.Enable(True)
			self.bfromscope.Enable(True)
			self.bremove.Enable(True)
		else:
			self.btoscope.Enable(False)
			self.bedit.Enable(False)
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
			dosestr = '%.2f' % (dose/1e20)
		dosestr = 'Use the measured dose %s e/A^2 for this preset?' % dosestr
		self.doselabel.SetLabel(dosestr)

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	icon = 'presets'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		# presets

		self.calibrations = Calibrations(self)
		self.calibrations.set({})
		self.parameters = Parameters(self)
		self.presets = EditPresets(self, -1)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(self.presets, (0, 0), (2, 1), wx.ALIGN_CENTER)
		self.sz.Add(self.calibrations, (0, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.sz.Add(self.parameters, (1, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.Add(self.sz, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 5)
		self.sz.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(EVT_SET_CALIBRATIONS, self.onSetCalibrations)
		self.Bind(EVT_SET_DOSE_VALUE, self.onSetDoseValue)
		self.Bind(EVT_EDIT_PRESET, self.onEditPreset)

	def onNodeInitialized(self):
		gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)

		#self.parameters.instrumentselection.setProxy(self.node.instrument)
		#self.parameters.bind(self.onUpdateParameters)

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
			args = (dialog.name, dialog.temname, dialog.camname)
			threading.Thread(target=target, args=args).start()
		dialog.Destroy()

	#def onUpdateParameters(self, evt=None):
	#	self.node.updateParams(self.parameters.get())

	def onSetParameters(self, evt):
		self.parameters.set(evt.parameters)
		self.sz.Layout()

	def setParameters(self, parameters):
		if isinstance(parameters, data.Data):
			parameters = parameters.toDict(dereference=True)
		evt = SetParametersEvent(parameters, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetCalibrations(self, evt):
		self.calibrations.set(evt.times)
		self.sz.Layout()

	def setCalibrations(self, times):
		evt = SetCalibrationsEvent(times, self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetSelected(self, evt):
		selection = evt.GetString()
		if selection:
			threading.Thread(target=self.node.selectPreset, args=(selection,)).start()
		else:
			self.calibrations.set({})
			self.parameters.set(None)
			try:
				self.parameters.Enable(False)
			except AttributeError:
				pass

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

	def onEditPreset(self, evt):
		preset = self.node.presetByName(evt.presetname)
		if preset is None:
			return
		if isinstance(preset, data.Data):
			preset = preset.toDict(dereference=True)

		tems = {}
		for tem_name in self.node.instrument.getTEMNames():
			try:
				tem = self.node.instrument.getTEM(tem_name)
				tems[tem_name] = tem.Magnifications
			except instrument.NotAvailableError:
				continue
		if not tems:
			return

		ccd_cameras = {}
		for ccd_camera_name in self.node.instrument.getCCDCameraNames():
			try:
				ccd_camera = self.node.instrument.getCCDCamera(ccd_camera_name)
				ccd_cameras[ccd_camera_name] = ccd_camera.CameraSize
			except instrument.NotAvailableError:
				continue
		if not ccd_cameras:
			return

		dialog = EditPresetDialog(self, preset, tems, ccd_cameras, self.node)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.updatePreset(evt.presetname, dialog.getParameters())
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['xy only'] = wx.CheckBox(self, -1,
#																					'Move stage x and y axes only')
#		self.widgets['stage always'] = wx.CheckBox(self, -1,
#																		'Always move stage regardless of move type')
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
#		sz.Add(self.widgets['stage always'], (1, 0), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['cycle'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['optimize cycle'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mag only'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Preset Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class NewDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Create New Preset')
		self.node = node

		self.instrumentselection = gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.GetParent().initInstrumentSelection(self.instrumentselection)
		stname = wx.StaticText(self, -1, 'Preset name:')
		self.tcname = wx.TextCtrl(self, -1, '')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.instrumentselection, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
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
		temname = self.instrumentselection.getTEM()
		camname = self.instrumentselection.getCCDCamera()
		if not name or name in self.node.presets:
			dialog = wx.MessageDialog(self, 'Invalid preset name', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.name = name
			self.temname = temname
			self.camname = camname
			evt.Skip()

class SessionListCtrl(wx.ListCtrl, ColumnSorterMixin):
	def __init__(self, parent):
		wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
		self.InsertColumn(0, 'Session')
		self.InsertColumn(1, 'Time')
		self.InsertColumn(2, 'User')
		self.InsertColumn(3, 'Description')

		self.itemDataMap = {}
		ColumnSorterMixin.__init__(self, 4)

	def GetListCtrl(self):
		return self

	def setSessions(self, sessions):
		self.DeleteAllItems()
		self.itemDataMap = {}
		sessions.reverse()
		for i, session in enumerate(sessions):
			name = session['name']
			time = session.timestamp
			user = session['user']['full name']
			comment = session['comment']
			index = self.InsertStringItem(0, name)
			self.SetStringItem(index, 1, str(time))
			self.SetStringItem(index, 2, user)
			self.SetStringItem(index, 3, comment)
			self.SetItemData(index, i)
			self.itemDataMap[i] = (name, time, user, comment)
		sessions.reverse()
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(2, wx.LIST_AUTOSIZE)

class ImportDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Import Presets',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.node = node
		self.presets = None

		self.instrumentselection = gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.GetParent().initInstrumentSelection(self.instrumentselection)

		self.session = SessionListCtrl(self)

		agelab1 = wx.StaticText(self, -1, 'Limit sessions to last')
		self.ageentry = IntEntry(self, -1, chars=4)
		self.ageentry.SetValue(20)
		agelab2 = wx.StaticText(self, -1, 'days')
		self.findpresets = wx.Button(self, -1, 'Find')
		self.Bind(wx.EVT_BUTTON, self.onFindPresets, self.findpresets)

		self.parameters = Parameters(self)

		self.lbpresets = wx.ListBox(self, -1, style=wx.LB_EXTENDED)

		sz = wx.GridBagSizer(5, 0)
		sz.Add(self.instrumentselection, (0, 0), (1, 4), wx.EXPAND)

		sz.Add(self.session, (1, 0), (1, 4), wx.EXPAND)

		sz.Add(agelab1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.ageentry, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz.Add(agelab2, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		sz.Add(self.findpresets, (2, 3), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.parameters, (3, 0), (1, 4), wx.EXPAND)
		label = wx.StaticText(self, -1, 'Presets')
		sz.Add(label, (4, 0), (1, 4), wx.ALIGN_CENTER)
		sz.Add(self.lbpresets, (5, 0), (1, 4), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz.AddGrowableCol(3)

		self.bimport = wx.Button(self, -1, 'Import')
		self.bimport.Enable(False)
		bdone = wx.Button(self, wx.ID_OK, 'Done')
		bdone.SetDefault()

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bimport, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bdone, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain = wx.GridBagSizer(5, 5)
		self.szmain.Add(sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szmain.Add(szbutton, (1, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

		self.SetSizerAndFit(self.szmain)
		self.SetAutoLayout(True)

		#self.Bind(wx.EVT_CHOICE, self.onSessionChoice, self.csession)
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSessionSelected, self.session)
		self.Bind(wx.EVT_LISTBOX, self.onPresetsListBox, self.lbpresets)
		self.Bind(wx.EVT_BUTTON, self.onImport, self.bimport)

	def onFindPresets(self, evt=None):
		temname = self.instrumentselection.getTEM()
		camname = self.instrumentselection.getCCDCamera()
		msg = 'Please select both a TEM and a CCD camera'
		if None in (temname, camname):
			dialog = wx.MessageDialog(self, msg, 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		try:
			tem = self.node.instrument.getTEMData(temname)
			ccd = self.node.instrument.getCCDCameraData(camname)
		except RuntimeError:
			dialog = wx.MessageDialog(self, msg, 'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		days = self.ageentry.GetValue()
		agestr = '-%d 0:0:0' % (days,)
		pquery = data.PresetData(tem=tem, ccdcamera=ccd)
		presets = self.node.research(pquery, timelimit=agestr)
		sessions = newdict.OrderedDict()
		for p in presets:
			sname = p['session']['name']
			if sname:
				sessions[sname] = p['session']
		self.session.setSessions(sessions.values())

	def onSessionSelected(self, evt):
		name = evt.GetText()
		self.presets = self.node.getSessionPresets(name)
		presetnames = self.presets.keys()
		self.bimport.Enable(False)
		self.lbpresets.Clear()
		if presetnames:
			self.lbpresets.AppendItems(presetnames)
			self.lbpresets.Enable(True)
		else:
			self.lbpresets.Enable(False)

	def onPresetsListBox(self, evt):
		selections = self.lbpresets.GetSelections()
		if selections:
			self.bimport.Enable(True)
		else:
			self.bimport.Enable(False)

		if len(selections) == 1:
			name = self.lbpresets.GetString(selections[0])
			preset = self.presets[name]
		else:
			preset = None
		self.parameters.set(preset)
		self.szmain.Layout()
		self.szmain.SetMinSize(self.szmain.GetSize())
		self.Fit()

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

class Parameters(wx.StaticBoxSizer):
	labelclass = wx.StaticText
	def __init__(self, parent):
		sb = wx.StaticBox(parent, -1, 'Preset Parameters')
		wx.StaticBoxSizer.__init__(self, sb, wx.VERTICAL)

		labels = (
			('tem', 'TEM:'),
			('ccdcamera', 'CCD Camera:'),
			('magnification', 'Magnification:'),
			('defocus', 'Defocus:'),
			('spot size', 'Spot size:'),
			('intensity', 'Intensity:'),
			('image shift', 'Image shift:'),
			('beam shift', 'Beam shift:'),
			('film', 'Use film:'),
			('energy filter', 'Energy filtered:'),
			('energy filter width', 'Energy filter width:'),
			('dimension', 'Dimension:'),
			('offset', 'Offset:'),
			('binning', 'Binning:'),
			('exposure time', 'Exposure time (ms):'),
			('dose', 'Dose (e/A^2):'),
			('pre exposure', 'Pre-Exposure (s):'),
			('skip', 'Skip when cycling:'),
		)
			
		self.labels = {}
		self.values = {}
		for key, value in labels:
			self.labels[key] = self.labelclass(parent, -1, value)
			self.values[key] = wx.StaticText(parent, -1, '')

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.labels['tem'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['tem'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['magnification'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['magnification'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['defocus'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['defocus'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['spot size'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['spot size'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['intensity'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['intensity'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['image shift'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['image shift'], (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['beam shift'], (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['beam shift'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['skip'], (9, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['skip'], (9, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		sz.Add(self.labels['ccdcamera'], (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['ccdcamera'], (0, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['film'], (1, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['film'], (1, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['energy filter'], (2, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['energy filter'], (2, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['energy filter width'], (3, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['energy filter width'], (3, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['dimension'], (4, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['dimension'], (4, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['offset'], (5, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['offset'], (5, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['binning'], (6, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['binning'], (6, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['exposure time'], (7, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['exposure time'], (7, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['pre exposure'], (8, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['pre exposure'], (8, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['dose'], (9, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['dose'], (9, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		sz.AddGrowableCol(1)
		sz.AddGrowableCol(5)

		self.Add(sz, 1, wx.EXPAND|wx.ALL, 3)

	def set(self, parameters):
		if parameters is None:
			for value in self.values.values():
				value.SetLabel('')
		else:
			for key in ['tem', 'ccdcamera']:
				if parameters[key] is None:
					self.values[key].SetLabel('None')
				else:
					self.values[key].SetLabel(parameters[key]['name'])

			keys = [
				'magnification',
				'defocus',
				'spot size',
				'intensity',
				'energy filter width',
				'exposure time',
				'pre exposure',
			]
			for key in keys:
				self.values[key].SetLabel(str(parameters[key]))

			for key in ['image shift', 'beam shift']:
				s = '(%g, %g)' % (parameters[key]['x'], parameters[key]['y'])
				self.values[key].SetLabel(s)

			for key in ['film', 'energy filter', 'skip']:
				if parameters[key]:
					s = 'Yes'
				else:
					s = 'No'
				self.values[key].SetLabel(s)

			for key in ['dimension', 'binning']:
				s = '%d x %d' % (parameters[key]['x'], parameters[key]['y'])
				self.values[key].SetLabel(s)

			for key in ['offset']:
				s = '(%d, %d)' % (parameters[key]['x'], parameters[key]['y'])
				self.values[key].SetLabel(s)

			for key in ['dose']:
				if parameters[key] is None:
					s = 'N/A'
				else:
					s = '%.2f' % (parameters[key]/1e20,)
				self.values[key].SetLabel(s)

			self.Layout()

class SelectParameters(Parameters):
	labelclass = wx.CheckBox
	def __init__(self, parent):
		Parameters.__init__(self, parent)
		self.setSelected()

	def getSelected(self):
		selected = {}
		selected['magnification'] = self.lblmag.GetValue()
		selected['defocus'] = self.lbldefocus.GetValue()
		selected['spot size'] = self.lblspotsize.GetValue()
		selected['intesity'] = self.lblintensity.GetValue()
		selected['image shift'] = self.lblimageshift.GetValue()
		selected['beam shift'] = self.lblbeamshift.GetValue()
		selected['use film'] = self.lblfilm.GetValue()
		selected['energy filter'] = self.lblenergyfilter.GetValue()
		selected['energy filter width'] = self.lblenergyfilterwidth.GetValue()
		selected['dimension'] = self.lbldimension.GetValue()
		selected['offset'] = self.lbloffset.GetValue()
		selected['binning'] = self.lblbinning.GetValue()
		selected['exposure time'] = self.lblexposuretime.GetValue()
		selected['pre exposure'] = self.lblpreexp.GetValue()
		selected['dose'] = self.lbldose.GetValue()
		return selected

	def setSelected(self, parameters=None):
		self.lblmag.SetValue(parameters is None or 'magnification' in parameters)
		self.lbldefocus.SetValue(parameters is None or 'defocus' in parameters)
		self.lblspotsize.SetValue(parameters is None or 'spot size' in parameters)
		self.lblintensity.SetValue(parameters is None or 'intensity' in parameters)
		self.lblimageshift.SetValue(
															parameters is None or 'image shift' in parameters)
		self.lblbeamshift.SetValue(parameters is None or 'beam shift' in parameters)
		self.lblfilm.SetValue(parameters is None or 'use film' in parameters)
		self.lblenergyfilter.SetValue(parameters is None or 'energy filter' in parameters)
		self.lblenergyfilterwidth.SetValue(parameters is None or 'energy filter width' in parameters)
		self.lbldimension.SetValue(parameters is None or 'dimension' in parameters)
		self.lbloffset.SetValue(parameters is None or 'offset' in parameters)
		self.lblbinning.SetValue(parameters is None or 'binning' in parameters)
		self.lblexposuretime.SetValue(
														parameters is None or 'exposure time' in parameters)
		self.lblpreexp.SetValue(parameters is None or 'pre exposure' in parameters)
		self.lbldose.SetValue(parameters is None or 'dose' in parameters)

class FromScopeDialog(wx.Dialog):
	def __init__(self, parent):
		self.preset = {}
		wx.Dialog.__init__(self, parent, -1, 'Overwrite Preset',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.parameters = SelectParameters(self)

		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.bcancel.SetDefault()

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bsave, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(self.parameters, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sz.Add(szbutton, (1, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)

		self.SetSizerAndFit(self.sz)
		self.SetAutoLayout(True)

		self.bsave.Enable(False)
		self.bcancel.Enable(False)

	def setPreset(self, preset):
		self.preset = preset
		self.parameters.set(preset)
		self.sz.Layout()
		# ...
		self.bsave.Enable(True)
		self.bcancel.Enable(True)

	def getPreset(self):
		# ...
		selected = self.parameters.getSelected()
		for key in self.preset:
			if key in selected and not selected[key]:
				self.preset[key] = None
		return self.preset

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Presets Test')
			preset = {
				'name': 'Test Preset',
				'magnification': 100.0,
				'defocus': 0.0,
				'spot size': 1,
				'intensity': 0.0,
				'image shift': {'x': 0.0, 'y': 0.0},
				'beam shift': {'x': 0.0, 'y': 0.0},
				'film': False,
				'dimension': {'x': 1024, 'y': 1024},
				'offset': {'x': 0, 'y': 0},
				'binning': {'x': 1, 'y': 1},
				'exposure time': 1000,
				'pre exposure': 0.0,
				'energy filter': True,
				'energy filter width': 0.0,
			}
			#dialog = EditPresetDialog(frame, preset, {}, {})
			#dialog.Show()
			panel = wx.Panel(frame, -1)
			sz = Parameters(panel)
			panel.SetSizer(sz)
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

def bitmapButton(parent, name, tooltip=None):
	bitmap = gui.wx.Icons.icon(name)
	button = wx.lib.buttons.GenBitmapButton(parent, -1, bitmap, size=(20, 20))
	button.SetBezelWidth(1)
	button.Enable(False)
	if tooltip is not None:
		button.SetToolTip(wx.ToolTip(tooltip))
	return button

