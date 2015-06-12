# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/PresetsManager.py,v $
# $Revision: 1.94 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-15 02:58:40 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import copy
import threading
import time
import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin

from pyami.ordereddict import OrderedDict
import leginon.leginondata
import leginon.instrument
from leginon.gui.wx.Entry import IntEntry, FloatEntry, EVT_ENTRY
import leginon.gui.wx.Camera
import leginon.gui.wx.Dialog
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.Node
import leginon.gui.wx.Presets
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Dialog
import leginon.gui.wx.Instrument

PresetsEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()
SetDoseValueEventType = wx.NewEventType()
SetCalibrationsEventType = wx.NewEventType()
EditPresetEventType = wx.NewEventType()
UpdatePresetLabelsEventType = wx.NewEventType()
AcquireAlignDoneEventType = wx.NewEventType()

EVT_PRESETS = wx.PyEventBinder(PresetsEventType)
EVT_SET_DOSE_VALUE = wx.PyEventBinder(SetDoseValueEventType)
EVT_SET_CALIBRATIONS = wx.PyEventBinder(SetCalibrationsEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)
EVT_EDIT_PRESET = wx.PyEventBinder(EditPresetEventType)
EVT_UPDATE_PRESET_LABELS = wx.PyEventBinder(UpdatePresetLabelsEventType)
EVT_ACQUIRE_ALIGN_DONE = wx.PyEventBinder(AcquireAlignDoneEventType)

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
	def __init__(self, doses):
		wx.PyEvent.__init__(self)
		self.SetEventType(SetDoseValueEventType)
		self.doses = doses

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

class UpdatePresetLabelsEvent(wx.PyCommandEvent):
	def __init__(self, source, leftpreset, rightpreset):
		wx.PyCommandEvent.__init__(self, UpdatePresetLabelsEventType, source.GetId())
		self.SetEventObject(source)
		self.leftpreset  = leftpreset
		self.rightpreset = rightpreset

class AcquireAlignDoneEvent(wx.PyCommandEvent):
	def __init__(self, source):
		wx.PyCommandEvent.__init__(self, AcquireAlignDoneEventType, source.GetId())
		self.SetEventObject(source)

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
			('defocus', 'Beam tilt - Defocus'),
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

class EditPresetDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, parameters, tems, ccd_cameras, node):
		self.parameters = parameters
		self.tems = tems
		self.ccd_cameras = ccd_cameras
		self.node = node

		self.aperture_sizer = None

		try:
			title =  'Edit Preset %s' % parameters['name']
		except KeyError:
			raise ValueError
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, 'Preset Parameters')

	def getMagChoices(self):
		try:
			mags = self.tems[self.parameters['tem']['name']]['magnifications']
		except:
			mags = []
		return [str(int(m)) for m in mags]

	def getProbeModeChoices(self):
		try:
			probes = self.tems[self.parameters['tem']['name']]['probe modes']
		except:
			probes = []
		return probes

	def getTEMChoices(self):
		choices = self.tems.keys()
		choices.sort()
		return [self.nonestring] + choices

	def getCCDCameraChoices(self):
		choices = self.ccd_cameras.keys()
		choices.sort()
		return [self.nonestring] + choices

	def getApertureSizeChoices(self, tem=None):
		try:
			if tem is None:
				tem = self.parameters['tem']['name']
			apertures = list(self.tems[tem]['apertures'])
			aperture_sizes = dict(self.tems[tem]['aperture sizes'])
		except (KeyError, TypeError):
			apertures = []
			aperture_sizes = {}

		sizes = {}
		for aperture in aperture_sizes:
			sizes[aperture] = []
			for a in aperture_sizes[aperture]:
				if a == 0:
					sizes[aperture].append("open")
				else:
					sizes[aperture].append(str(a))
		return apertures, sizes

	def onInitialize(self):
		parameters = self.parameters
		self.nonestring = '(None)'

		tems = self.getTEMChoices()
		magnifications = self.getMagChoices()
		ccdcameras = self.getCCDCameraChoices()
		probes = self.getProbeModeChoices()
		self.choices = {
			'tem': wx.Choice(self, -1, choices=tems),
			'magnification': wx.Choice(self, -1, choices=magnifications),
			'ccdcamera': wx.Choice(self, -1, choices=ccdcameras),
			'probe mode': wx.Choice(self, -1, choices=probes),
		}

		self.floats = {
			'defocus': FloatEntry(self, -1, chars=9),
			'defocus range min': FloatEntry(self, -1, chars=9),
			'defocus range max': FloatEntry(self, -1, chars=9),
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
			'tem energy filter width': FloatEntry(self, -1, chars=6),
			'energy filter width': FloatEntry(self, -1, chars=6),
			'pre exposure': FloatEntry(self, -1, chars=6),
		}

		self.bools = {
			'film': wx.CheckBox(self, -1, 'Use film'),
			'tem energy filter': wx.CheckBox(self, -1, 'Energy filtered'),
			'energy filter': wx.CheckBox(self, -1, 'Energy filtered'),
			'skip': wx.CheckBox(self, -1, 'Skip when cycling'),
			'alt channel': wx.CheckBox(self, -1, 'Use Channel 1 correction in normal acquisition'),
		}

		self.dicts = {
			'camera parameters': leginon.gui.wx.Camera.CameraPanel(self),
		}

		buttons = {
			'tem': (
				'magnification', 
				'defocus',
				'spot size',
				'intensity',
				'image shift',
				'beam shift',
				'energy filter',
				'energy filter width',
				'probe mode',
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

		labels = (
    		('tem', 'TEM'),
    		('magnification', 'Magnification'),
    		('defocus', 'Defocus'),
    		('defocus range', 'Random Defocus Range'),
    		('spot size', 'Spot size'),
    		('intensity', 'Intensity'),
    		('image shift', 'Image shift'),
    		('beam shift', 'Beam shift'),
    		('tem energy filter width', 'Energy filter width'),
				('probe mode', 'Probe Mode'),
    		('ccdcamera', 'Digital Camera'),
    		('energy filter width', 'Energy filter width'),
    		('pre exposure', 'Pre-exposure'),
		)

		self.labels = {}
		for key, text in labels:
			self.labels[key] = wx.StaticText(self, -1, text)

		sizer = wx.GridBagSizer(5, 5)
		self._sz = sizer

		sizer.Add(self.labels['tem'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['tem'], (0, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sizer.Add(self.labels['magnification'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['magnification'], (1, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sizer.Add(self._buttons['tem']['magnification'], (1, 3), (1, 1), wx.ALIGN_CENTER)





		sizer.Add(self.labels['defocus'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['defocus'], (2, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['defocus'], (2, 3), (1, 1), wx.ALIGN_CENTER)



		sizer.Add(self.labels['defocus range'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['defocus range min'], (3, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self.floats['defocus range max'], (3, 2), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)


		sizer.Add(self.labels['spot size'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['spot size'], (4, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['spot size'], (4, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['intensity'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['intensity'], (5, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['intensity'], (5, 3), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'x')
		sizer.Add(label, (6, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		sizer.Add(label, (6, 2), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['image shift'], (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['image shift']['x'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self.floats['image shift']['y'], (7, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['image shift'], (7, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['beam shift'], (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['beam shift']['x'], (8, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self.floats['beam shift']['y'], (8, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['beam shift'], (8, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.labels['probe mode'], (9, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.choices['probe mode'], (9, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sizer.Add(self._buttons['tem']['probe mode'], (9, 3), (1, 1), wx.ALIGN_CENTER)
		sizer.Add(self.bools['tem energy filter'], (10, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		sizer.Add(self._buttons['tem']['energy filter'], (10, 3), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(self.labels['tem energy filter width'], (11, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.floats['tem energy filter width'], (11, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sizer.Add(self._buttons['tem']['energy filter width'], (11, 3), (1, 1), wx.ALIGN_CENTER)

		self.initializeApertureSelection()

		sizer.Add(self.bools['skip'], (13, 0), (1, 4), wx.ALIGN_LEFT)
		sizer.Add(self.bools['alt channel'], (14, 0), (1, 4), wx.ALIGN_LEFT)

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

		sizer.Add(self.dicts['camera parameters'], (5, 5), (15, 2), wx.ALIGN_CENTER|wx.EXPAND)
		sizer.Add(self._buttons['ccdcamera']['camera parameters'], (5, 7), (15, 1), wx.ALIGN_CENTER)


		self.setParameters(parameters)


		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(4)
		sizer.AddGrowableCol(5)
		for i in range(12):
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

	def initializeApertureSelection(self, evt=None):
		apertures, aperture_sizes = self.getApertureSizeChoices()
		if self.aperture_sizer is not None:
			for aperture in apertures:
				try:
					self.aperture_sizer.Remove(self.labels[aperture])
					self.labels[aperture].Destroy()
					del self.labels[aperture]
					self.aperture_sizer.Remove(self.choices[aperture])
					self.choices[aperture].Destroy()
					del self.choices[aperture]
				except KeyError:
					pass

			self.aperture_sbsizer.Remove(self.aperture_sizer)
			self._sz.Remove(self.aperture_sbsizer)
			self._sz.Remove(self._buttons['tem']['aperture sizes'])
			self._buttons['tem']['aperture sizes'].Destroy()
			del self._buttons['tem']['aperture sizes']
			self.aperture_sizer = None
			self.aperture_sbsizer = None
			self.aperture_sb = None
			self._sz.Layout()

		if evt is not None:
			tem = evt.GetString()
			apertures, aperture_sizes = self.getApertureSizeChoices(tem)
		if aperture_sizes:
			self.aperture_sb = wx.StaticBox(self, -1, 'Apertures')
			self.aperture_sbsizer = wx.StaticBoxSizer(self.aperture_sb, wx.VERTICAL)
			self.aperture_sizer = wx.GridBagSizer(5,5)
			i = 0
			for aperture in apertures:
				self.labels[aperture] = wx.StaticText(self, -1, aperture)
				self.choices[aperture] = wx.Choice(self, -1, choices=aperture_sizes[aperture])
				self.aperture_sizer.Add(self.labels[aperture], (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
				self.aperture_sizer.Add(self.choices[aperture], (i, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
				i += 1
			self.aperture_sizer.AddGrowableCol(1)
			self.aperture_sbsizer.Add(self.aperture_sizer, 0, wx.EXPAND|wx.ALL, 5)
			self._sz.Add(self.aperture_sbsizer, (12, 0), (1, 3), wx.ALIGN_CENTER|wx.EXPAND|wx.HORIZONTAL)
			button =  bitmapButton(self, 'instrumentget', 'Set this value from the instrument value')
			self._buttons['tem']['aperture sizes'] = button
			self.Bind(wx.EVT_BUTTON, self.onButton, button)
			self._sz.Add(self._buttons['tem']['aperture sizes'], (12, 3), (1, 1), wx.ALIGN_CENTER)
			self._sz.Layout()

	def setTEMItemChoices(self,tem,itemgroupname,itemname,func=str):
		current_choice = self.choices[itemname].GetStringSelection()
		if tem == self.nonestring:
			new_choices = []
		else:
			try:
				items = self.tems[tem][itemgroupname]
				new_choices = [str(func(m)) for m in items]
			except KeyError:
				new_choices = []
		self.choices[itemname].Freeze()
		self.choices[itemname].Clear()
		self.choices[itemname].AppendItems(new_choices)
		if self.choices[itemname].FindString(current_choice) == wx.NOT_FOUND:
			if new_choices:
				self.choices[itemname].SetSelection(0)
		else:
			self.choices[itemname].SetStringSelection(current_choice)
		if self.choices[itemname].IsEnabled():
			if not new_choices:
				self.choices[itemname].Enable(False)
		else:
			if new_choices:
				self.choices[itemname].Enable(True)
		self.choices[itemname].Thaw()
		return new_choices

	def onTEMChoice(self, evt):
		tem = evt.GetString()
		new_choices = self.setTEMItemChoices(tem,'probe modes','probe mode',str)
		new_choices = self.setTEMItemChoices(tem,'magnifications','magnification',int)

		for value in self._buttons['tem'].values():
			# empty new_choices means TEM is not valid
			value.Enable(bool(new_choices))
    	#'energy filter',
		#'camera parameters',

		self.initializeApertureSelection(evt)

	def onCCDCameraChoice(self, evt):
		ccdcamera = evt.GetString()
		try:
			camera_geom_limits = self.ccd_cameras[ccdcamera]
		except KeyError:
			camera_geom_limits = None
		self.dicts['camera parameters'].setGeometryLimits(camera_geom_limits)
		for value in self._buttons['ccdcamera'].values():
			value.Enable(camera_geom_limits is not None)

	def setChoice(self,parameters, itemname, func):
			if itemname not in parameters.keys():
				return
			if parameters[itemname] is not None:
				value = str(func(parameters[itemname]))
				if self.choices[itemname].FindString(value) == wx.NOT_FOUND:
					self.choices[itemname].Append(value)
				self.choices[itemname].SetStringSelection(value)

	def setParameters(self, parameters):
		self.setChoice(parameters,'magnification',int)
		self.setChoice(parameters,'probe mode',str)

		if 'aperture size' in parameters and parameters['aperture size'] is not None:
			for aperture, aperture_size in parameters['aperture size'].items():
				if aperture not in self.choices:
					continue
				if aperture_size == 0:
					size_str = 'open'
				else:
					size_str = str(aperture_size)
				if self.choices[aperture].FindString(size_str) == wx.NOT_FOUND:
					continue
				self.choices[aperture].SetStringSelection(size_str)

		keys = (
			'defocus',
			'defocus range min',
			'defocus range max',
			'spot size',
			'intensity',
			'tem energy filter width',
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

		for key in ['skip', 'alt channel', 'film', 'tem energy filter', 'energy filter']:
			try:
				self.bools[key].SetValue(bool(parameters[key]))
			except KeyError:
				pass

		try:
			geom_limits = self.ccd_cameras[parameters['ccdcamera']['name']]
			self.dicts['camera parameters'].setGeometryLimits(geom_limits)
		except:
			pass

		try:
			self.dicts['camera parameters'].setConfiguration(parameters)
		except KeyError:
			pass

	def getChoice(self,itemname,func):
		n = self.choices[itemname].GetSelection()
		if n < 0:
			value = None
		else:
			value = func(self.choices[itemname].GetString(n))
		return value

	def getParameters(self):
		parameters = {}
		tem = self.choices['tem'].GetStringSelection()
		if tem == self.nonestring:
			tem = None
		parameters['tem'] = tem

		parameters['magnification'] = self.getChoice('magnification',int)
		parameters['probe mode'] = self.getChoice('probe mode',str)

		apertures, aperture_sizes = self.getApertureSizeChoices()
		if apertures:
			parameters['aperture size'] = {}
			for aperture in apertures:
				n = self.choices[aperture].GetSelection()
				if n < 0:
					continue
				aperture_size_str = self.choices[aperture].GetString(n)
				if aperture_size_str == 'open':
					aperture_size = 0
				else:
					aperture_size = float(aperture_size_str)

				parameters['aperture size'][aperture] = aperture_size

		keys = [
			'defocus',
			'defocus range min',
			'defocus range max',
			'spot size',
			'intensity',
			'tem energy filter width',
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

		for key in ['skip', 'alt channel', 'film', 'tem energy filter', 'energy filter']:
			parameters[key] = bool(self.bools[key].GetValue())

		ccdcamera = self.choices['ccdcamera'].GetStringSelection()
		if ccdcamera == self.nonestring:
			ccdcamera = None
		parameters['ccdcamera'] = ccdcamera
		parameters.update(self.dicts['camera parameters'].getConfiguration())

		return parameters

class EditPresets(leginon.gui.wx.Presets.PresetOrder):
	def _widgets(self):
		leginon.gui.wx.Presets.PresetOrder._widgets(self, 'Presets (Cycle Order)')
		self.btoscope = self._bitmapButton('instrumentset', 'To Scope')
		self.bedit = self._bitmapButton('edit', 'Edit the selected preset parameters')
		self.bacquire = self._bitmapButton('acquire', 'Acquire dose image for the selected preset')
		self.bfromscope = self._bitmapButton('instrumentget', 'From Scope')
		self.bremove = self._bitmapButton('minus', 'Remove the selected preset')

		self.bnewfromscope = self._bitmapButton('instrumentgetnew', 'Create a new preset from the current instrument state')
		self.bnewfromscope.Enable(True)
		self.bimport = self._bitmapButton('import', 'Import presets from another session')
		self.bimport.Enable(True)
		self.balign = self._bitmapButton('alignpresets', 'Align presets to each other')
		self.balign.Enable(True)
		self.bbeam = self._bitmapButton('presetsbeam', 'Shift beam for a preset')
		self.bbeam.Enable(True)

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.listbox, (1, 0), (1, 1), wx.EXPAND)

		optionsizer = wx.GridBagSizer(3,3)
		optionsizer.Add(self.upbutton, (0, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.downbutton, (1, 0), (1, 1), wx.ALIGN_CENTER)

		optionsizer.Add(self.btoscope, (3, 0), (1, 1), wx.ALIGN_CENTER)

		optionsizer.Add(self.bedit, (5, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bacquire, (6, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bfromscope, (7, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bremove, (8, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.balign, (9, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bbeam, (10, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bnewfromscope, (11, 0), (1, 1), wx.ALIGN_CENTER)
		optionsizer.Add(self.bimport, (12, 0), (1, 1), wx.ALIGN_CENTER)

		sizer.Add(optionsizer, (1, 1), (1,1), wx.EXPAND)
		sizer.AddGrowableRow(1)
		sizer.AddGrowableCol(0)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		leginon.gui.wx.Presets.PresetOrder._bind(self)
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
		leginon.gui.wx.Presets.PresetOrder.setChoices(self, choices)

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
		leginon.gui.wx.Presets.PresetOrder.updateButtons(self, n)
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

class DoseDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent):
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Dose Image', 'Dose Image')
		self.doses = [None,None]
		self.parent = parent

	def onInitialize(self):
		leginon.gui.wx.Dialog.Dialog.onInitialize(self)

		self.image = leginon.gui.wx.ImagePanel.ImagePanel(self, -1,imagesize=(360,360))

		self.doselabel = wx.StaticText(self, -1, '')
		self.pixelframedoselabel = wx.StaticText(self, -1, '')
		self.pixeldoseratelabel = wx.StaticText(self, -1, '')

		self.sz.Add(self.image, (0, 0), (1, 1), wx.EXPAND)

		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)

		szmatch = wx.GridBagSizer(5, 5)
		self.bmatch = wx.Button(self, -1, 'Match')
		self.bmatch.Enable(True)
		szmatch.Add(self.bmatch,(0,0),(1,1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'to')
		szmatch.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL )
		self.dose_to_match = FloatEntry(self, -1, min=0,value='10', chars=5)
		szmatch.Add(self.dose_to_match, (0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'e/A^2')
		szmatch.Add(label, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL )
		self.sz.Add(szmatch, (1,0),(1,1), wx.ALIGN_RIGHT)

		self.szbuttons.Add(self.doselabel, (0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		bsave = wx.Button(self, wx.ID_OK, 'YES')
		bsave.Enable(True)
		self.szbuttons.Add(bsave,(0,1),(1,1), wx.ALIGN_CENTER_VERTICAL)
		bcancel = wx.Button(self, wx.ID_CANCEL, 'NO')
		bcancel.Enable(True)
		self.szbuttons.Add(bcancel,(0,2),(1,1), wx.ALIGN_CENTER_VERTICAL)
		self.szbuttons.AddGrowableRow(0)
		self.szbuttons.Add(self.pixeldoseratelabel, (1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szbuttons.Add(self.pixelframedoselabel, (2, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.Bind(wx.EVT_BUTTON, self.onMatchDose, self.bmatch)
		self.Bind(wx.EVT_BUTTON, self.onCancel, bcancel)
		self.Bind(wx.EVT_CLOSE, self.onCancel)

	def setDose(self, doses):
		self.doses = doses
		dose = doses[0]
		if dose is None:
			dosestr = 'N/A'
		else:
			dosestr = '%.2f' % (dose/1e20)
		dosestr = 'Use the measured dose %s e/A^2 for this preset?' % dosestr
		# per frame dose
		if doses[1] is not None:
			if doses[1][0]:
				framestr = 'per frame'
			else:
				framestr = ''
			pixelframedosestr = '( Dose on camera pixel %s: %.1f electrons )' % (framestr,doses[1][1])
			self.pixelframedoselabel.SetLabel(pixelframedosestr)
		# dose rate.  This is more useful on K2 or Falcon with fixed base
		# frame rate but variable saved frame rate
		if doses[2] is not None:
			pixeldoseratestr = '( Dose rate on camera pixel: %.1f electrons/second )' % (doses[2])
			self.pixeldoseratelabel.SetLabel(pixeldoseratestr)

		self.doselabel.SetLabel(dosestr)

	def onMatchDose(self,evt):
		dose_to_match = self.dose_to_match.GetValue()
		self.parent.onMatchDose(dose_to_match * 1e20,self.doses[0])

	def onCancel(self,evt):
		self.parent.onCancelDoseMeasure()
		self.EndModal(0)
		
		

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	icon = 'presets'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		# presets

		self.calibrations = Calibrations(self)
		self.calibrations.set({})
		self.parameters = Parameters(self)
		self.presets = EditPresets(self, -1)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(self.presets, (0, 0), (2, 1), wx.ALIGN_CENTER|wx.EXPAND)
		self.sz.Add(self.calibrations, (0, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.sz.Add(self.parameters, (1, 1), (1, 1), wx.EXPAND|wx.ALL)
		self.szmain.Add(self.sz, (1, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, 5)
		self.sz.AddGrowableCol(0)
		self.sz.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(EVT_SET_CALIBRATIONS, self.onSetCalibrations)
		self.Bind(EVT_SET_DOSE_VALUE, self.onSetDoseValue)
		self.Bind(EVT_EDIT_PRESET, self.onEditPreset)
		self.Bind(EVT_UPDATE_PRESET_LABELS, self.onUpdatePresetLabels)
		self.Bind(EVT_ACQUIRE_ALIGN_DONE, self.onAcquireAlignDone)

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)

		#self.parameters.instrumentselection.setProxy(self.node.instrument)
		#self.parameters.bind(self.onUpdateParameters)

		self.Bind(leginon.gui.wx.Presets.EVT_PRESET_SELECTED,
							self.onPresetSelected, self.presets)
		self.Bind(leginon.gui.wx.Presets.EVT_PRESET_ORDER_CHANGED,
							self.onCycleOrderChanged, self.presets)
		self.Bind(leginon.gui.wx.Presets.EVT_PRESET_REMOVED,
							self.onRemove, self.presets)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.presets.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.presets.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onNewFromScope, self.presets.bnewfromscope)

		self.importdialog = ImportDialog(self, self.node)
		self.Bind(wx.EVT_BUTTON, self.onImport, self.presets.bimport)

		self.Bind(wx.EVT_BUTTON, self.onAlign, self.presets.balign)

		self.beamdialog = BeamDialog(self, self.node)
		self.Bind(wx.EVT_BUTTON, self.onBeam, self.presets.bbeam)

		self.dosedialog = DoseDialog(self)
		self.Bind(wx.EVT_BUTTON, self.onAcquireDoseImage, self.presets.bacquire)

		self.Bind(EVT_PRESETS, self.onPresets)

		self.alignacquiremode = None

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
			evt = leginon.gui.wx.Presets.PresetsChangedEvent(presets)
			self.presets.GetEventHandler().AddPendingEvent(evt)

	def setDoseValue(self, doses):
		evt = SetDoseValueEvent(doses)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetImage(self, evt):
		self.dosedialog.image.setImage(evt.image)
		if not self.dosedialog.IsShown():
			if self.dosedialog.ShowModal() == wx.ID_OK:
				self.node.saveDose(self.dosedialog.doses[0],
														self.presets.getSelectedPreset())
			self.dosedialog.image.setImage(None)

	def onSetDoseValue(self, evt):
		self.dosedialog.setDose(evt.doses)

	def onAcquireDoseImage(self, evt):
		presetname = self.presets.getSelectedPreset()
		self._presetsEnable(False)
		target = self.node.acquireDoseImage
		args = (presetname,)
		threading.Thread(target=target, args=args).start()

	def onMatchDose(self, dose_to_match, dose):
		presetname = self.presets.getSelectedPreset()
		self.node.matchDose(presetname, dose_to_match, dose)	

	def onCancelDoseMeasure(self):
		presetname = self.presets.getSelectedPreset()
		self.node.cancelDoseMeasure(presetname)

	def onImport(self, evt):
		self.importdialog.ShowModal()

	def updatePresetLabels(self, leftpreset, rightpreset):
		evt = UpdatePresetLabelsEvent(self, leftpreset, rightpreset)
		self.GetEventHandler().AddPendingEvent(evt)

	def acquireAlignDone(self):
		evt = AcquireAlignDoneEvent(self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onAcquireAlignDone(self, evt):
		self.aligndialog.enableContinue()

	def onUpdatePresetLabels(self, evt):
		refpreset = self.node.refpreset
		if self.customalign == True:
			self.aligndialog.labref.SetLabel('Custom Alignment Mode ')
			self.aligndialog.presetlabelref.SetLabel('no same mag automatic adjustment')
		else:
			self.aligndialog.labref.SetLabel('Overall Reference Preset: ')
			self.aligndialog.presetlabelref.SetLabel(refpreset)
		self.aligndialog.choiceleft.SetStringSelection(evt.leftpreset)
		self.aligndialog.choiceright.SetStringSelection(evt.rightpreset)
		self.alignacquiremode = self.aligndialog.choiceacquiremode.GetStringSelection()

	def onAlign(self, evt):
		self.aligndialog = AlignDialog(self, self.node)
		preset_names = self.node.presets.keys()
		self.aligndialog.choiceleft.setChoices(preset_names)
		self.aligndialog.choiceright.setChoices(preset_names)
		refpreset = self.presets.getSelectedPreset()
		self.customalign = False
		self.aligndialog.imright.setImage(None)
		self.aligndialog.imleft.setImage(None)
		threading.Thread(target=self.node.initAlignPresets, args=(refpreset,)).start()
		self.aligndialog.ShowModal()

	def onBeam(self, evt):
		selectedpreset = self.presets.getSelectedPreset()
		self.beamdialog.setPreset(selectedpreset)
		self.beamdialog.im.setImage(None)
		self.beamdialog.bautocenter.Disable()
		self.beamdialog.bcommit.Disable()
		self.beamdialog.ShowModal()
		self.node.new_beamshift = None

	def onDoneLastAlign(self):
		self.aligndialog.enableDone()

	def onDoneAllAlign(self):
		# Destroy used instead of EndModal so that Leginon can close properly.  Don't know why
		self.aligndialog.Destroy()

	def setAlignImage(self, image, typename, stats={}):
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename, stats)
		self.aligndialog.GetEventHandler().AddPendingEvent(evt)

	def setBeamImage(self, image, stats={}):
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename=None)
		self.beamdialog.GetEventHandler().AddPendingEvent(evt)

	def disableBeamAdjust(self, magnification):
		self.beamdialog.bautocenter.Enable(False)
		self.beamdialog.bcommit.Enable(False)
		self.beamdialog.bacquire.Enable(False)
		self.beamdialog.magnification.SetLabel('Preset magnification: %d' % (magnification))
		self.beamdialog.beamshift.SetLabel('No valid Beam Shift Calibration Available')
	def enableBeamAdjust(self, magnification,beamshift):
		self.beamdialog.bautocenter.Enable(False)
		self.beamdialog.bcommit.Enable(False)
		self.beamdialog.bacquire.Enable(True)
		self.beamdialog.magnification.SetLabel('Acquiring magnification: %d' % (magnification))
		self.displayBeamShift(beamshift)

	def displayBeamShift(self,beamshift):
		self.beamdialog.beamshift.SetLabel('current beam shift:  x: %.4e,  y: %.4e' % (beamshift['x'], beamshift['y']))

	def onFromScope(self, evt):
		name = self.presets.getSelectedPreset()
		self._presetsEnable(False)
		target = self.node.fromScope
		# The True in the last argument copies beam shift to all presets at the same mag
		args = (name,None,None,False)
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
		if isinstance(parameters, leginon.leginondata.Data):
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
		if isinstance(preset, leginon.leginondata.Data):
			preset = preset.toDict(dereference=True)

		tems = {}
		for tem_name in self.node.instrument.getTEMNames():
			try:
				tem = self.node.instrument.getTEM(tem_name)
				tems[tem_name] = {}
				tems[tem_name]['magnifications'] = tem.Magnifications
				tems[tem_name]['probe modes'] = tem.ProbeModes
				try:
					tems[tem_name]['apertures'] = tem.Apertures
					tems[tem_name]['aperture sizes'] = tem.ApertureSizes
				except AttributeError:
					pass
			except leginon.instrument.NotAvailableError:
				continue
		if not tems:
			return

		ccd_cameras = {}
		for ccd_camera_name in self.node.instrument.getCCDCameraNames():
			try:
				ccd_camera = self.node.instrument.getCCDCamera(ccd_camera_name)
				ccd_cameras[ccd_camera_name] = {}
				ccd_cameras[ccd_camera_name]['size'] = ccd_camera.CameraSize
				ccd_cameras[ccd_camera_name]['binnings'] = ccd_camera.CameraBinnings
				ccd_cameras[ccd_camera_name]['binmethod'] = ccd_camera.CameraBinMethod
			except leginon.instrument.NotAvailableError:
				continue
		if not ccd_cameras[ccd_camera_name]['size']:
			return

		dialog = EditPresetDialog(self, preset, tems, ccd_cameras, self.node)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.updatePreset(evt.presetname, dialog.getParameters())
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Preset Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
#		self.widgets['xy only'] = wx.CheckBox(self, -1,
#																					'Move stage x and y axes only')
#		self.widgets['stage always'] = wx.CheckBox(self, -1,
#																		'Always move stage regardless of move type')
		self.widgets['cycle'] = wx.CheckBox(self, -1, 'Cycle presets')
		self.widgets['optimize cycle'] = wx.CheckBox(self, -1,
																									'Optimize preset cycle')
		self.widgets['mag only'] = wx.CheckBox(self, -1, 'Cycle magnification only')
		self.widgets['apply offset'] = wx.CheckBox(self, -1, 'Apply stage tilt axis offset to all image shifts')

		self.widgets['blank'] = wx.CheckBox(self, -1, 'Beam blank during preset change')
		szsmallsize = wx.BoxSizer(wx.HORIZONTAL)
		smallsizelab = wx.StaticText(self, -1, 'Small image size (for dose image, etc.)')
		self.widgets['smallsize'] = IntEntry(self, -1, chars=6)
		szsmallsize.Add(smallsizelab)
		szsmallsize.Add(self.widgets['smallsize'])

		szpausetime = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Pause')
		szpausetime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds between preset changes')
		szpausetime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

#		sz.Add(self.widgets['xy only'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		sz.Add(self.widgets['stage always'], (1, 0), (1, 1),
#						wx.ALIGN_CENTER_VERTICAL)
		sz = wx.GridBagSizer(5, 10)
		sz.Add(szpausetime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['cycle'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['optimize cycle'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['mag only'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['apply offset'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['blank'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szsmallsize, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class NewDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Create New Preset')
		self.node = node

		self.instrumentselection = leginon.gui.wx.Instrument.SelectionPanel(self, passive=True)
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
			usernamelist = []
			name = session['name']
			try:
				time = session.timestamp
			except:
				time = None
			try:
				usernamelist.append(session['user']['firstname'])
				usernamelist.append(session['user']['lastname'])
				user = ' '.join(usernamelist)
			except:
				continue
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


class AlignDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, node):
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, 'Align Presets')
		imsize = 384
		self.node = node
		self.parent = parent

		
		refname = self.parent.presets.getSelectedPreset()
		boxref = wx.StaticBox(self, -1)
		szref = wx.StaticBoxSizer(boxref, wx.HORIZONTAL)
		sz = wx.BoxSizer(wx.HORIZONTAL)
		self.labref = wx.StaticText(self, -1, 'Overall Reference Preset: ')
		self.presetlabelref = wx.StaticText(self, -1)
		sz.Add(self.labref, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		sz.AddSpacer((10,10))
		sz.Add(self.presetlabelref, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#		szref = wx.BoxSizer(wx.HORIZONTAL)
		szref.Add(sz, 1, wx.ALIGN_CENTER|wx.ALL, 5)
		szmode = wx.BoxSizer(wx.HORIZONTAL)
		szmode.Add(szref, 1)
		self.choiceacquiremode = wx.Choice(self, -1, choices=(['Full Camera','Similar look across mags']))	
		szmode.Add(self.choiceacquiremode, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

		preset_names = self.node.presets.keys()
		lableft = wx.StaticText(self, -1, 'Current Reference Preset ')
		self.choiceleft = leginon.gui.wx.Presets.PresetChoice(self,-1)
		self.choiceleft.setChoices(preset_names)

		self.imleft = leginon.gui.wx.ImagePanel.ClickImagePanel(self, -1,mode='vertical',imagesize=(imsize,imsize))
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onLeftImageClicked, self.imleft)
		szleft = wx.BoxSizer(wx.VERTICAL)
		szpreset = wx.GridBagSizer(2, 2)
		szpreset.Add(lableft, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szpreset.Add(self.choiceleft, (0, 1), (1, 1))
		szleft.Add(szpreset, 0, wx.EXPAND)
		szleft.Add(self.imleft, 1, wx.EXPAND)

		labright = wx.StaticText(self, -1, 'Current Preset To Adjust ')
		self.choiceright = leginon.gui.wx.Presets.PresetChoice(self,-1)
		self.choiceright.setChoices(preset_names)

		self.imright = leginon.gui.wx.ImagePanel.ClickImagePanel(self, -1,mode='vertical',imagesize=(imsize,imsize))
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onRightImageClicked, self.imright)
		szright = wx.BoxSizer(wx.VERTICAL)
		szpreset = wx.GridBagSizer(2, 2)
		szpreset.Add(labright, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szpreset.Add(self.choiceright, (0, 1), (1, 1))
		szright.Add(szpreset, 0, wx.EXPAND)
		szright.Add(self.imright, 1, wx.EXPAND)

		self.bstart = wx.Button(self, -1, 'Start')
		self.bstart.Enable(True)
		self.bcontinue = wx.Button(self, -1, 'Continue')
		self.bdone = wx.Button(self, -1, 'Done')


		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bstart, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcontinue, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bdone, (0, 2), (1, 1), wx.ALIGN_CENTER)
		
		
		szimages = wx.BoxSizer(wx.HORIZONTAL)
		szimages.Add(szleft, 1, wx.EXPAND)
		szimages.Add(szright, 1, wx.EXPAND)
		szmain = wx.GridBagSizer(5,5)
		szmain.Add(szmode, (0,0),(1,1),wx.ALL|wx.EXPAND, border=5)
		szmain.Add(szimages, (1, 0), (1, 1), wx.EXPAND)
		szmain.Add(szbutton, (2, 0), (1, 1), wx.ALL, border=5)

		szmain.AddGrowableRow(1)
		szmain.AddGrowableCol(0)

		self.SetSizerAndFit(szmain)
		self.SetAutoLayout(True)

		self.Bind(wx.EVT_CHOICE, self.onAcquireModeChoice, self.choiceacquiremode)
		self.Bind(wx.EVT_BUTTON, self.onNext, self.bcontinue)
		self.Bind(wx.EVT_BUTTON, self.onStart, self.bstart)
		self.Bind(leginon.gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)
		self.Bind(wx.EVT_BUTTON, self.onClose, self.bdone)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.enableStart()

	def onLeftImageClicked(self, evt):
		self.node.onAlignImageClicked('left', evt.xy)

	def onRightImageClicked(self, evt):
		self.node.onAlignImageClicked('right', evt.xy)

	def onAcquireModeChoice(self, evt):
		if not self.bstart.IsEnabled() or self.parent.customalign == True:
			self.parent.alignacquiremode = self.choiceacquiremode.GetStringSelection()
			self.node.acquireAlignImages(self)

	def onNext(self, evt):
		self.parent.alignacquiremode = self.choiceacquiremode.GetStringSelection()
		self.bstart.Disable()
		self.node.onAlignNext()

	def onStart(self, evt):
		currentpresetleft = self.choiceleft.GetStringSelection()
		currentpresetright = self.choiceright.GetStringSelection()
		self.parent.alignacquiremode = self.choiceacquiremode.GetStringSelection()

		refname = self.node.refpreset
		if currentpresetleft == refname and currentpresetright == self.node.firstrightpreset and self.parent.customalign == False:
			self.enableContinue()
			threading.Thread(target=self.node.loopAlignPresets, args=(refname,)).start()
		else:
			self.enableStartDone()
			if self.parent.customalign == True:
				self.labref.SetLabel('Custom Alignment Mode: ')
				self.presetlabelref.SetLabel('no same mag automatic adjustment')
			else:
				self.labref.SetLabel('Custom Alignment Mode: ')
				self.presetlabelref.SetLabel('no same mag automatic adjustment')
				self.parent.customalign = True
			self.node.acquireAlignImages(currentpresetleft, currentpresetright)

	def onSetImage(self, evt):
		if evt.typename == 'left':
			self.imleft.setImage(evt.image)
		else:
			self.imright.setImage(evt.image)

	def enableStart(self):
		self.choiceleft.Enable(True)
		self.choiceright.Enable(True)
		self.bstart.Enable(True)
		self.bcontinue.Disable()
		self.bdone.Disable()

	def enableContinue(self):
		self.choiceleft.Disable()
		self.choiceright.Disable()
		self.bstart.Disable()
		self.bcontinue.Enable(True)
		self.bdone.Disable()

	def enableStartDone(self):
		self.enableStart()
		self.bdone.Enable(True)

	def enableDone(self):
		self.bstart.Disable()
		self.bcontinue.Disable()
		self.bdone.Enable(True)

	def onClose(self, evt):
		self.enableStart()
		self.node.doneAllAlignPresets()
		self.EndModal(0)

class BeamDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Adjust Beam', style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		imsize = 512
		self.node = node
		self.parent = parent

		### create imageviewer
		self.im = leginon.gui.wx.ImagePanel.ClickImagePanel(self, -1, imagesize=(imsize,imsize))
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked, self.im)
		self.im.statstypesizer.SetEmptyCellSize((110, 100))
	
		### create buttons
		self.bacquire = wx.Button(self, -1, 'Acquire')
		self.bacquire.Enable(True)
		self.bautocenter = wx.Button(self, -1, 'Auto Center')
		self.bautocenter.Enable(False)
		self.bcommit = wx.Button(self, -1, 'Commit')
		self.bcommit.Enable(False)
		self.bcycle = wx.CheckBox(self, -1, 'Cycle for each adjustment')
		self.bcycle.SetValue(True)
		self.beamshift = wx.StaticText(self, -1, 'current beam shift:')
		self.magnification = wx.StaticText(self, -1, 'Acquiring magnification:')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bacquire, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bautocenter, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcommit, (0, 2), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcycle, (0, 3), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.magnification, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.beamshift, (1, 1), (1, 4), wx.ALIGN_CENTER)

		### merge buttons and imageviewer
		szmain = wx.GridBagSizer(5,5)
		szmain.Add(self.im, (0, 0), (1, 1), wx.EXPAND)
		szmain.Add(szbutton, (1, 0), (1, 1))
		szmain.AddGrowableRow(0)
		szmain.AddGrowableCol(0)

		self.SetSizerAndFit(szmain)
		self.SetAutoLayout(True)

		#self.Bind(wx.EVT_CHOICE, self.onSessionChoice, self.csession)
		self.Bind(wx.EVT_BUTTON, self.onAcquire, self.bacquire)
		self.Bind(wx.EVT_BUTTON, self.onAutoCenter, self.bautocenter)
		self.Bind(wx.EVT_BUTTON, self.onCommit, self.bcommit)
		self.Bind(leginon.gui.wx.Events.EVT_SET_IMAGE, self.onSetImage)

	def onImageClicked(self, evt):
		cycle = self.bcycle.GetValue()
		self.node.onBeamImageClicked(evt.xy, cycle=cycle)

	def onAcquire(self, evt):
		threading.Thread(target=self.node.acquireBeamImage).start()
		self.bautocenter.Enable(True)
		self.bcommit.Enable(True)

	def onAutoCenter(self, evt):
		cycle = self.bcycle.GetValue()
		threading.Thread(target=self.node.autoBeamCenter, kwargs={'cycle':cycle}).start()

	def onCommit(self, evt):
		threading.Thread(target=self.node.commitBeamAdjustment).start()
		self.EndModal(0)

	def setPreset(self, preset):
		self.node.initBeamAdjust(preset)

	def onSetImage(self, evt):
		self.im.setImage(evt.image)

class ImportDialog(wx.Dialog):
	def __init__(self, parent, node):
		wx.Dialog.__init__(self, parent, -1, 'Import Presets',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		self.node = node
		self.presets = None

		self.instrumentselection = leginon.gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.GetParent().initInstrumentSelection(self.instrumentselection)

		self.session = SessionListCtrl(self)
		self.session.SetMinSize((40, 150))

		agelab1 = wx.StaticText(self, -1, 'Limit sessions to last')
		self.ageentry = IntEntry(self, -1, chars=4)
		self.ageentry.SetValue(20)
		agelab2 = wx.StaticText(self, -1, 'days')
		self.findpresets = wx.Button(self, -1, 'Find')
		self.Bind(wx.EVT_BUTTON, self.onFindPresets, self.findpresets)

		self.parameters = Parameters(self)

		self.lbpresets = wx.ListBox(self, -1, style=wx.LB_EXTENDED,size=(80,60))
		self.lbpresets.SetMinSize((40, 100))

		### left side of import window
		sz0 = wx.GridBagSizer(5, 0)
		sz0.Add(self.instrumentselection, (0, 0), (1, 4), wx.EXPAND)
		sz0.Add(self.session, (1, 0), (1, 4), wx.EXPAND)
		sz0.Add(agelab1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz0.Add(self.ageentry, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		sz0.Add(agelab2, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		sz0.Add(self.findpresets, (2, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		### when window is stretched, stretch session list
		sz0.AddGrowableCol(0)
		sz0.AddGrowableRow(1)

		### right side of import window
		sz1 = wx.GridBagSizer(5, 0)
		sz1.Add(self.parameters, (0, 0), (1, 4), wx.EXPAND)
		label = wx.StaticText(self, -1, 'Presets')
		sz1.Add(label, (1, 0), (1, 4), wx.ALIGN_CENTER)
		sz1.Add(self.lbpresets, (2, 0), (1, 4), wx.EXPAND)
		### when window is stretched vertically, stretch preset list
		sz1.AddGrowableRow(2)

		### buttons at bottom of window
		self.bimport = wx.Button(self, -1, 'Import')
		self.bimport.Enable(False)
		bdone = wx.Button(self, wx.ID_OK, 'Done')
		bdone.SetDefault()
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bimport, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bdone, (0, 1), (1, 1), wx.ALIGN_CENTER)

		### merge windows and buttons
		self.szmain = wx.GridBagSizer(5, 5)
		self.szmain.Add(sz0, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szmain.Add(sz1, (0, 1), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szmain.Add(szbutton, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)
		### when window is stretched, stretch left window horiz., and both panes vert.
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
		pquery = leginon.leginondata.PresetData(tem=tem, ccdcamera=ccd)
		presets = self.node.research(pquery, timelimit=agestr)
		self.sessiondict = OrderedDict()
		badsessions = []
		for p in presets:
			if p['session'] is None:
				continue
			sname = p['session']['name']
			# reduce sessions to check for multiple TEM used in most recent preset
			if sname not in self.sessiondict.keys() and sname not in badsessions:
				if self.onlyOneTEMinSessionPresets(p['session']):
					self.sessiondict[sname] = p['session']
				else:
					badsessions.append(sname)
		self.session.setSessions(self.sessiondict.values())

	def onlyOneTEMinSessionPresets(self,sessiondata):
		'''
		This function make sure all current presets are on the same tem host.
		SetupWizard can not prevent users from switching instrument hosts in
		the same session in order to allow camera switch.  As a result, it
		could make a session to have presets from different
		TEM.  This prevents that mistake to be imported to a new session.
		'''
		tems = []
		presets = self.node.getSessionPresets(sessiondata)
		for presetname in presets.keys():
			q = leginon.leginondata.PresetData(session=sessiondata,name=presetname)
			newestpreset = q.query(results=1)[0]
			if newestpreset['tem'].dbid not in tems:
				if len(tems) < 1:
					tems.append(newestpreset['tem'].dbid)
				else:
					return False
		return True

	def onSessionSelected(self, evt):
		name = evt.GetText()
		sessiondata = self.sessiondict[name]
		self.presets = self.node.getSessionPresets(sessiondata)
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
		presets = OrderedDict()
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
			('ccdcamera', 'Digital Camera:'),
			('magnification', 'Magnification:'),
			('defocus', 'Defocus:'),
			('defocus range', 'Random Defocus Range:'),
			('spot size', 'Spot size:'),
			('intensity', 'Intensity:'),
			('image shift', 'Image shift:'),
			('beam shift', 'Beam shift:'),
			('film', 'Use film:'),
			('tem energy filter', 'Energy filtered:'),
			('tem energy filter width', 'Energy filter width:'),
			('energy filter', 'Energy filtered:'),
			('energy filter width', 'Energy filter width:'),
			('dimension', 'Dimension:'),
			('offset', 'Offset:'),
			('binning', 'Binning:'),
			('exposure time', 'Exposure time (ms):'),
			('save frames', 'Save raw frames:'),
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
		sz.Add(self.labels['defocus range'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['defocus range'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['spot size'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['spot size'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['intensity'], (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['intensity'], (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['image shift'], (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['image shift'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['beam shift'], (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['beam shift'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['tem energy filter'], (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['tem energy filter'], (8, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['tem energy filter width'], (9, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['tem energy filter width'], (9, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.labels['skip'], (10, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['skip'], (10, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

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
		sz.Add(self.labels['save frames'], (10, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.values['save frames'], (10, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		sz.AddGrowableCol(1)
		sz.AddGrowableCol(5)

		self.Add(sz, 1, wx.EXPAND|wx.ALL, 3)

		self._sz = sz
		self.parent = parent

		self.aperture_sizer = None
		self.labels['aperture size'] = {}
		self.values['aperture size'] = {}

	def set(self, parameters):
		if parameters is None:
			for value in self.values.values():
				try:
					value.SetLabel('')
				except AttributeError:
					pass
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
				'tem energy filter width',
				'energy filter width',
				'exposure time',
				'pre exposure',
			]
			for key in keys:
				if key == 'exposure time':
					self.values[key].SetLabel('%.1f' % (float(parameters[key])))
				else:
					self.values[key].SetLabel(str(parameters[key]))

			r = []
			for key in ('defocus range min','defocus range max'):
				if parameters[key] is None:
					r = None
					break
				r.append('%.3g' % (parameters[key],))
			if r is None:
				s = 'None'
			else:
				s = '(%s, %s)' % tuple(r)
			self.values['defocus range'].SetLabel(s)

			for key in ['image shift', 'beam shift']:
				try:
					s = '(%g, %g)' % (parameters[key]['x'], parameters[key]['y'])
				except TypeError:
					s = '(None, None)'
				self.values[key].SetLabel(s)

			for key in ['film', 'tem energy filter', 'energy filter', 'skip', 'save frames']:
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

			if self.aperture_sizer is not None:
				for aperture in self.labels['aperture size'].keys():
						self.aperture_sizer.Remove(self.labels['aperture size'][aperture])
						self.labels['aperture size'][aperture].Destroy()
						del self.labels['aperture size'][aperture]

				for aperture in self.values['aperture size'].keys():
						self.aperture_sizer.Remove(self.values['aperture size'][aperture])
						self.values['aperture size'][aperture].Destroy()
						del self.values['aperture size'][aperture]
	
				self.aperture_sbsizer.Remove(self.aperture_sizer)
				self._sz.Remove(self.aperture_sbsizer)
				self.aperture_sizer = None
				self.aperture_sbsizer = None
				self.aperture_sb = None

			if parameters['aperture size']:
				if 'apertures' in parameters:
					apertures = parameters['apertures']
				else:
					apertures = parameters['aperture size'].keys()
					apertures.sort()

				i = 0
				self.aperture_sizer = wx.GridBagSizer(5, 5)
				for aperture in apertures:
					aperture_size = parameters['aperture size'][aperture]
					if aperture_size is None:
						continue
					if aperture_size == 0:
						aperture_size_str = 'open'
					else:
						aperture_size_str = str(aperture_size)
					self.labels['aperture size'][aperture] = self.labelclass(self.parent, -1, aperture)
					self.aperture_sizer.Add(self.labels['aperture size'][aperture], (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
					self.values['aperture size'][aperture] = wx.StaticText(self.parent, -1, aperture_size_str)
					self.aperture_sizer.Add(self.values['aperture size'][aperture], (i, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
					i += 1

				if self.labels['aperture size'] or self.values['aperture size']:
					self.aperture_sb = wx.StaticBox(self.parent, -1, 'Apertures')
					self.aperture_sbsizer = wx.StaticBoxSizer(self.aperture_sb, wx.VERTICAL)
					self.aperture_sizer.AddGrowableCol(1)
					self.aperture_sbsizer.Add(self.aperture_sizer, 0, wx.EXPAND|wx.ALL, 5)
					self._sz.Add(self.aperture_sbsizer, (11, 0), (1, 2), wx.EXPAND)
				else:
					self.aperture_sizer.Destroy()
					self.aperture_sizer = None

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
		selected['tem energy filter'] = self.lbltemenergyfilter.GetValue()
		selected['tem energy filter width'] = self.lbltemenergyfilterwidth.GetValue()
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
		self.lbltemenergyfilter.SetValue(parameters is None or 'tem energy filter' in parameters)
		self.lbltemenergyfilterwidth.SetValue(parameters is None or 'tem energy filter width' in parameters)
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

def bitmapButton(parent, name, tooltip=None):
	bitmap = leginon.gui.wx.Icons.icon(name)
	button = wx.lib.buttons.GenBitmapButton(parent, -1, bitmap, size=(20, 20))
	button.SetBezelWidth(1)
	button.Enable(False)
	if tooltip is not None:
		button.SetToolTip(wx.ToolTip(tooltip))
	return button

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Presets Test')
			preset = {
				'name': 'Test Preset',
				'tem': {'name': 'TEM1'},
				'ccdcamera': None,
				'magnification': 1000.0,
				'defocus': 0.0,
				'defocus range min': 0.0,
				'defocus range max': 0.0,
				'skip': True,
				'save frames': False,
				'frame time': 200.0,
				'dose': 0,
				'spot size': 1,
				'intensity': 0.0,
				'image shift': {'x': 0.0, 'y': 0.0},
				'beam shift': {'x': 0.0, 'y': 0.0},
				'film': False,
				'dimension': {'x': 1024, 'y': 1024},
				'offset': {'x': 0, 'y': 0},
				'binning': {'x': 1, 'y': 1},
				'exposure time': 1000.0,
				'pre exposure': 0.0,
				'tem energy filter': True,
				'tem energy filter width': 0.0,
				'energy filter': True,
				'energy filter width': 0.0,
				'aperture size': {
					'condenser': 100e-6,
					'objective': 20e-6,
				}
			}
			tems = {
				'TEM1': {
					'magnifications': [100, 1000, 10000, 100000],
					'apertures': ['condenser', 'objective'],
					'aperture sizes': {
						'condenser': [0, 100e-6, 10e-6, 1e-6],
						'objective': [0, 200e-6, 20e-6, 2e-6],
					}
				},
				'TEM2': {
					'magnifications': [200, 2000, 20000, 200000],
					'apertures': ['condenser', 'objective'],
					'aperture sizes': {
						'condenser': [0, 150e-6, 15e-6, 1e-6],
						'objective': [0, 250e-6, 25e-6, 2e-6],
					}
				}
			}
			dialog = EditPresetDialog(frame, preset, tems, {}, None)
			dialog.Show()
			panel = wx.Panel(frame, -1)
			sz = Parameters(panel)
			sz.set(preset)
			sz.set(preset)
			panel.SetSizer(sz)
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

