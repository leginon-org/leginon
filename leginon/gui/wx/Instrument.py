# -*- coding: iso-8859-1 -*-
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/Instrument.py,v $
# $Revision: 1.48 $
# $Name: not supported by cvs2svn $
# $Date: 2006-01-18 21:03:19 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import wx
from leginon.gui.wx.Camera import CameraPanel, EVT_CONFIGURATION_CHANGED
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry, EVT_ENTRY, TypeEntry
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.Events
import leginon.gui.wx.Node
import leginon.gui.wx.ToolBar
import threading

def setControl(control, value):
	testr = '%s value must be of type %s (is type %s)'
	vestr = 'Invalid value %s for instance of %s'
	controlname = control.__class__.__name__
	valuetypename = value.__class__.__name__

	if isinstance(control, wx.StaticText):
		if value is None:
			value = ''
			control.Enable(False)
		else:
			try:
				value = str(value)
			except:
				typename = str.__name__
				raise TypeError(testr % (controlname, typename, valuetypename))
			control.Enable(True)

		control.SetLabel(value)

	elif isinstance(control, (Entry, wx.TextCtrl, wx.CheckBox)):
		if value is None:
			control.Enable(False)
		else:
			control.Enable(True)

		if isinstance(control, TypeEntry):
			pass
		elif isinstance(control, wx.TextCtrl) and type(value) is not str:
			if value is None:
				value = ''
			else:
				typename = str.__name__
				raise TypeError(testr % (controlname, typename, valuetypename))
		elif isinstance(control, wx.CheckBox) and type(value) is not bool:
			if value is None:
				value = False
			else:
				typename = bool.__name__
				raise TypeError(testr % (controlname, typename, valuetypename))

		try:
			control.SetValue(value)
		except ValueError:
			raise ValueError(vestr % (value, controlname))

	elif isinstance(control, wx.Choice):
		if value is None:
			control.Clear()
			control.Enable(False)
		elif isinstance(value, list):
			values = [str(v) for v in value]
			control.Freeze()
			control.Clear()
			control.AppendItems(values)
			control.Thaw()
		else:
			try:
				value = str(value)
			except:
				typename = str.__name__
				raise TypeError(testr % (controlname, typename, valuetypename))

			if control.FindString(value) == wx.NOT_FOUND:
				raise ValueError(vestr % (value, controlname))
			else:
				control.SetStringSelection(value)
			control.Enable(True)

	elif isinstance(control, CameraPanel):
		if value is None:
			control.setSize(None)
		elif isinstance(value, dict):
			keys = value.keys()
			if 'x' in keys and 'y' in keys:
				control.setSize(value)
			else:
				for i in ['dimension', 'offset', 'binning', 'exposure time']:
					if i not in keys:
						raise ValueError
				control._setConfiguration(value)
		else:
			raise ValueError

def getValue(wxobj):
	if isinstance(wxobj, wx.StaticText):
		return wxobj.GetLabel()
	elif isinstance(wxobj, (Entry, wx.TextCtrl, wx.CheckBox)):
		return wxobj.GetValue()
	elif isinstance(wxobj, wx.Choice):
		return wxobj.GetStringSelection()
	elif isinstance(wxobj, wx.Button):
		return True
	elif isinstance(wxobj, wx.Event):
		evtobj = wxobj.GetEventObject()
		if isinstance(evtobj, wx.CheckBox):
			return wxobj.IsChecked()
		elif isinstance(evtobj, (Entry, wx.TextCtrl)):
			return wxobj.GetValue()
		elif isinstance(evtobj, wx.Choice):
			return wxobj.GetString()
		elif isinstance(evtobj, wx.Button):
			return True
	else:
		raise ValueError('Cannot get value for %s' % wxobj.__class__.__name__)

def bindControl(parent, method, control):
	if isinstance(control, wx.CheckBox):
		binder = wx.EVT_CHECKBOX
	elif isinstance(control, Entry):
		binder = EVT_ENTRY
	elif isinstance(control, wx.Choice):
		binder = wx.EVT_CHOICE
	elif isinstance(control, wx.Button):
		binder = wx.EVT_BUTTON
	else:
		raise ValueError('Cannot bind event for %s' % control.__class__.__name__)
	parent.Bind(binder, method, control)

InitParametersEventType = wx.NewEventType()
SetParametersEventType = wx.NewEventType()

EVT_INIT_PARAMETERS = wx.PyEventBinder(InitParametersEventType)
EVT_SET_PARAMETERS = wx.PyEventBinder(SetParametersEventType)

class InitParametersEvent(wx.PyCommandEvent):
	def __init__(self, source, parameters, session):
		wx.PyCommandEvent.__init__(self, InitParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.parameters = parameters
		self.session = session

class SetParametersEvent(wx.PyCommandEvent):
	def __init__(self, source, name, parameters):
		wx.PyCommandEvent.__init__(self, SetParametersEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.parameters = parameters

'''
class Magnification(wx.Choice):
	attribute = 'Magnification'
	choicesattribute = 'Magnifications'
	def __init__(self, *args, **kwargs):
		self.value = None
		self.choices = []
		wx.Choice.__init__(self, *args, **kwargs)
		self.Enable(False)
		self.Bind(wx.EVT_CHOICE, self.onChoice, self)

	def onChoice(self, evt):
		n = self.GetSelection()
		self.value = self.choices[n]
		evt.Skip()

	def get(self):
		return self.value

	def set(self, value):
		if value == self.value:
			return
		if value not in self.choices:
			raise ValueError('value not in choices')
		n = self.choices.index(value)
		self.SetSelection(n)
		self.value = value

	def getChoices(self):
		return list(self.choices)

	def setChoices(self, choices):
		if choices == self.choices:
			return
		self.choices = list(choices)
		self.Freeze()
		self.Clear()
		self.AppendItems([str(i) for i in choices])
		try:
			n = self.choices.index(self.value)
		except ValueError:
			self.value = None
			self.Enable(False)
		else:
			self.SetSelection(n)
		self.Thaw()
'''

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
		self.sz.AddGrowableCol(1)
		self.sz.AddGrowableCol(2)
		self.sz.AddGrowableCol(3)

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
			self.xy[group][name][a] = FloatEntry(self.parent, -1, chars=9, allownone=True)
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
			'Exposure number': IntEntry(self.parent, -1, chars=5, allownone=True),
			'Exposure type': wx.Choice(self.parent, -1),
			'Automatic exposure time': wx.StaticText(self.parent, -1, ''),
			'Manual exposure time': FloatEntry(self.parent, -1, chars=5, allownone=True),
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
			style = wx.ALIGN_CENTER
			if isinstance(self.parameters[key], Entry):
				style |= wx.FIXED_MINSIZE
			self.sz.Add(self.parameters[key], (row, 1), (1, 1), style)
			self.parameters[key].Enable(False)
			self.parameters[key].Enable(False)
			row += 1
		self.sz.AddGrowableCol(1)

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
			'x': FloatEntry(self.parent, -1, chars=9, allownone=True),
			'y': FloatEntry(self.parent, -1, chars=9, allownone=True),
			'z': FloatEntry(self.parent, -1, chars=9, allownone=True),
			'a': FloatEntry(self.parent, -1, chars=4, allownone=True),
			'b': FloatEntry(self.parent, -1, chars=4, allownone=True),
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
			self.sz.AddGrowableCol(i+1)

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
		self.sz.AddGrowableCol(1)

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
			'Focus': FloatEntry(self.parent, -1, chars=9, allownone=True),
			'Defocus': FloatEntry(self.parent, -1, chars=9, allownone=True),
		}
		resetdefoc = wx.Button(self.parent, -1, 'Reset Defocus')
		resetdefoc.Bind(wx.EVT_BUTTON, self.onResetDefocus)

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p)
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), wx.ALIGN_CENTER)

		self.sz.Add(resetdefoc, (i+1, 1), (1, 1),
								wx.ALIGN_CENTER)

		for p in self.parameters.values():
			p.Enable(False)

		self.sz.AddGrowableCol(1)

	def onResetDefocus(self, evt):
		name = self.parent.GetParent().choice.GetStringSelection()
		node = self.parent.GetParent().node
		node.resetDefocus(name)

		args = (name, ['Defocus'])
		threading.Thread(target=node.refresh, args=args).start()

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
			'Magnification': wx.Choice(self.parent, -1),
			'Intensity': FloatEntry(self.parent, -1, chars=7, allownone=True),
			'Spot size': IntEntry(self.parent, -1, chars=2, allownone=True),
		}

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			style = wx.ALIGN_CENTER
			if isinstance(self.parameters[p], Entry):
				style |= wx.FIXED_MINSIZE
			self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i, 1), (1, 1), style)
			self.sz.AddGrowableRow(i)
			self.parameters[p].Enable(False)

		self.sz.AddGrowableCol(1)

class CamInfoSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Information'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Name',
			'Chip',
			'Serial number',
			'Maximum value',
			'Live mode',
			'Simulation image path',
			'Temperature',
			'Hardware gain index',
			'Hardware speed index',
			'Retractable',
			'Axis',
		]
		self.parameters = {}

		szsize = wx.GridBagSizer(0, 0)
		st = wx.StaticText(self.parent, -1, 'Size:')
		self.parameters['Size'] = {}
		self.parameters['Size']['x'] = wx.StaticText(self.parent, -1, '')
		#stx = wx.StaticText(self.parent, -1, ' × ')
		stx = wx.StaticText(self.parent, -1, ' x ')
		self.parameters['Size']['y'] = wx.StaticText(self.parent, -1, '')
		szsize.Add(st, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsize.Add(self.parameters['Size']['x'], (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szsize.Add(stx, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szsize.Add(self.parameters['Size']['y'], (0, 3), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szsize.AddGrowableCol(1)

		szpsize = wx.GridBagSizer(0, 0)
		st = wx.StaticText(self.parent, -1, 'Pixel size:')
		self.parameters['Pixel size'] = {}
		self.parameters['Pixel size']['x'] = wx.StaticText(self.parent, -1, '')
		#stx = wx.StaticText(self.parent, -1, ' × ')
		stx = wx.StaticText(self.parent, -1, ' x ')
		self.parameters['Pixel size']['y'] = wx.StaticText(self.parent, -1, '')
		szpsize.Add(st, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpsize.Add(self.parameters['Pixel size']['x'], (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szpsize.Add(stx, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpsize.Add(self.parameters['Pixel size']['y'], (0, 3), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpsize.AddGrowableCol(1)

		self.sz.Add(szsize, (0, 0), (1, 2), wx.EXPAND)
		self.sz.AddGrowableRow(0)
		self.sz.Add(szpsize, (1, 0), (1, 2), wx.EXPAND)
		self.sz.AddGrowableRow(1)

		for i, p in enumerate(parameterorder):
			st = wx.StaticText(self.parent, -1, p + ':')
			self.parameters[p] = wx.StaticText(self.parent, -1, '')
			self.sz.Add(st, (i+2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.parameters[p], (i+2, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
			self.sz.AddGrowableRow(i+2)

		self.sz.AddGrowableCol(1)

		self.parametermap = {
			'CameraName': 'Name',
			'ChipName': 'Chip',
			'SerialNumber': 'Serial number',
			'MaximumPixelValue': 'Maximum value',
			'LiveModeAvailable': 'Live mode',
			'SimulationImagePath': 'Simulation image path',
			'Temperature': 'Temperature',
			'HardwareGainIndex': 'Hardware gain index',
			'HardwareSpeedIndex': 'Hardware speed index',
			'Retractable': 'Retractable',
			'CameraAxis': 'Axis',
		}

		for k, v in self.parametermap.items():
			self.parametermap[k] = self.parameters[v]

		self.parametermap['camera size'] = {'x': self.parameters['Size']['x'],
																				'y': self.parameters['Size']['y']}
		self.parametermap['pixel size'] = {'x': self.parameters['Pixel size']['x'],
																				'y': self.parameters['Pixel size']['y']}


class CamConfigSizer(wx.StaticBoxSizer):
	def __init__(self, parent, title='Settings'):
		self.parent = parent
		wx.StaticBoxSizer.__init__(self, wx.StaticBox(self.parent, -1, title),
																			wx.VERTICAL)
		self.sz = wx.GridBagSizer(5, 5)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 5)

		parameterorder = [
			'Camera configuration',
			'Exposure type',
			'Inserted',
			'Gain index',
			'Speed index',
			'Mirror',
			'Rotation',
			'Shutter open delay',
			'Shutter close delay',
			'Preamp delay',
			'Parallel mode',
		]

		self.parameters = {
			'Exposure type': wx.Choice(self.parent, -1),
			'Inserted': wx.CheckBox(self.parent, -1, 'Inserted'),
			'Gain index': IntEntry(self.parent, -1, chars=2, allownone=True),
			'Speed index': IntEntry(self.parent, -1, chars=2, allownone=True),
			'Mirror': wx.Choice(self.parent, -1),
			'Rotation': wx.Choice(self.parent, -1),
			'Shutter open delay': IntEntry(self.parent, -1, chars=5, allownone=True),
			'Shutter close delay': IntEntry(self.parent, -1, chars=5, allownone=True),
			'Preamp delay': IntEntry(self.parent, -1, chars=5, allownone=True),
			'Parallel mode': wx.CheckBox(self.parent, -1, 'Parallel mode'),
			'Camera configuration': CameraPanel(self.parent),
		}

		for i, p in enumerate(parameterorder):
			if isinstance(self.parameters[p], wx.CheckBox):
				self.sz.Add(self.parameters[p], (i, 0), (1, 2), wx.ALIGN_CENTER)
			elif isinstance(self.parameters[p], CameraPanel):
				self.sz.Add(self.parameters[p], (i, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
			else:
				st = wx.StaticText(self.parent, -1, p + ':')
				self.sz.Add(st, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
				style = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
				if isinstance(self.parameters[p], Entry):
					style |= wx.FIXED_MINSIZE
				self.sz.Add(self.parameters[p], (i, 1), (1, 1), style)
			self.parameters[p].Enable(False)
			self.sz.AddGrowableRow(i)

		self.parametermap = {
			'ExposureType': 'Exposure type',
			'ExposureTypes': 'Exposure type',
			'Inserted': 'Inserted',
			'GainIndex': 'Gain index',
			'SpeedIndex': 'Speed index',
			'ShutterOpenDelay': 'Shutter open delay',
			'ShutterCloseDelay': 'Shutter close delay',
			'PreampDelay': 'Preamp delay',
			'ParallelMode': 'Parallel mode',
			'Mirror': 'Mirror',
			'MirrorStates': 'Mirror',
			'Rotation': 'Rotation',
			'Rotations': 'Rotation',
			'CameraSize': 'Camera configuration',
			'Configuration': 'Camera configuration',
		}

		for k, v in self.parametermap.items():
			self.parametermap[k] = self.parameters[v]

		self.sz.AddGrowableCol(1)

class ParameterMixin(object):
	def setParameters(self, parameters, parametermap=None):
		if parametermap is None:
			parametermap = self.parametermap
		keys = ['Magnifications', 'LowDoseStates', 'LowDoseModes',
						'ShutterPositions', 'ExternalShutterStates', 'MainScreenPositions',
						'HolderTypes', 'ColumnValvePositions', 'FilmExposureTypes',
						'FilmDateTypes', 'ExposureTypes', 'MirrorStates', 'Rotations',
						'CameraSize']
		for key in keys:
			try:
				setControl(parametermap[key], parameters[key])
			except KeyError:
				pass
		for key, value in parameters.items():
			if key in keys:
				continue
			try:
				if isinstance(parametermap[key], dict):
					self.setParameters(value, parametermap[key])
				else:
					setControl(parametermap[key], value)
			except KeyError:
				pass

	def clearParameters(self, parametermap=None):
		if parametermap is None:
			parametermap = self.parametermap
		for key, value in parametermap.items():
			try:
				if isinstance(value, dict):
					self.clearParameters(value)
				else:
					setControl(value, None)
			except KeyError:
				pass

	def makeDict(self, keypath, value):
		if len(keypath) == 0:
			return value
		else:
			return {keypath[0]: self.makeDict(keypath[1:], value)}

	def reverseMap(self, map, reversemap={}, keypath=[]):
		keys = ['Magnifications', 'LowDoseStates', 'LowDoseModes',
						'ShutterPositions', 'ExternalShutterStates', 'MainScreenPositions',
						'HolderTypes', 'ColumnValvePositions', 'FilmExposureTypes',
						'FilmDateTypes', 'ExposureTypes', 'MirrorStates', 'Rotations',
						'CameraSize']
		for key, value in map.items():
			if key in keys:
				continue
			if isinstance(value, dict):
				self.reverseMap(value, reversemap, keypath + [key])
			else:
				reversemap[value] = keypath + [key]
		return reversemap

	def onControl(self, evt):
		control = evt.GetEventObject()
		control.Enable(False)
		keypath = self.controlmap[control]
		value = getValue(evt)
		name = self.GetParent().choice.GetStringSelection()
		if not name:
			return
		attributes = self.makeDict(keypath, value)
		args = (name, attributes)
		threading.Thread(target=self.GetParent().node.refresh, args=args).start()

class TEMPanel(wx.Panel, ParameterMixin):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sz = wx.GridBagSizer(5, 5)

		self.szlenses = LensesSizer(self)
		self.szfilm = FilmSizer(self)
		self.szstage = StageSizer(self)
		self.szholder = HolderSizer(self)
		self.szscreen = ScreenSizer(self)
		self.szvacuum = VacuumSizer(self)
		self.szlowdose = LowDoseSizer(self)
		self.szfocus = FocusSizer(self)
		self.szpmain = MainSizer(self)

		self.sz.Add(self.szpmain, (0, 0), (1, 1), wx.EXPAND)
		self.sz.Add(self.szstage, (0, 1), (1, 1), wx.EXPAND)

		self.sz.Add(self.szlenses, (1, 0), (1, 1), wx.EXPAND)
		self.sz.Add(self.szfilm, (1, 1), (1, 1), wx.EXPAND)

		self.sz.Add(self.szfocus, (2, 0), (1, 1), wx.EXPAND)
		self.sz.Add(self.szscreen, (2, 1), (1, 1), wx.EXPAND)

		self.sz.Add(self.szvacuum, (3, 0), (2, 1), wx.EXPAND)

		self.sz.Add(self.szholder, (3, 1), (1, 1), wx.EXPAND)
		self.sz.Add(self.szlowdose, (4, 1), (1, 1), wx.EXPAND)

		self.sz.AddGrowableCol(0)
		self.sz.AddGrowableCol(1)

		self.SetSizer(self.sz)

		self.parametermap = {
			'HighTension': self.szpmain.parameters['High tension'],
			'Magnifications': self.szpmain.parameters['Magnification'],
			'Magnification': self.szpmain.parameters['Magnification'],
			'Intensity': self.szpmain.parameters['Intensity'],
			'SpotSize': self.szpmain.parameters['Spot size'],
			'StageStatus': self.szstage.parameters['Status'],
			'CorrectedStagePosition': self.szstage.parameters['Correction'],
			'StagePosition': {
				'x': self.szstage.parameters['x'],
				'y': self.szstage.parameters['y'],
				'z': self.szstage.parameters['z'],
				'a': self.szstage.parameters['a'],
				'b': self.szstage.parameters['b'],
			},
			'ImageShift': {
				'x': self.szlenses.xy['Image']['Shift']['x'],
				'y': self.szlenses.xy['Image']['Shift']['y'],
			},
			'RawImageShift': {
				'x': self.szlenses.xy['Image']['Shift (raw)']['x'],
				'y': self.szlenses.xy['Image']['Shift (raw)']['y'],
			},
			'BeamShift': {
				'x': self.szlenses.xy['Beam']['Shift']['x'],
				'y': self.szlenses.xy['Beam']['Shift']['y'],
			},
			'BeamTilt': {
				'x': self.szlenses.xy['Beam']['Tilt']['x'],
				'y': self.szlenses.xy['Beam']['Tilt']['y'],
			},
			'Stigmator': {
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
			'FilmStock': self.szfilm.parameters['Stock'],
			'FilmExposureNumber': self.szfilm.parameters['Exposure number'],
			'FilmExposureTypes': self.szfilm.parameters['Exposure type'],
			'FilmExposureType': self.szfilm.parameters['Exposure type'],
			'FilmAutomaticExposureTime':
				self.szfilm.parameters['Automatic exposure time'],
			'FilmManualExposureTime':
				self.szfilm.parameters['Manual exposure time'],
			'FilmUserCode': self.szfilm.parameters['User code'],
			'FilmDateTypes': self.szfilm.parameters['Date Type'],
			'FilmDateType': self.szfilm.parameters['Date Type'],
			'FilmText': self.szfilm.parameters['Text'],
			'ShutterPositions': self.szfilm.parameters['Shutter'],
			'Shutter': self.szfilm.parameters['Shutter'],
			'ExternalShutterStates': self.szfilm.parameters['External shutter'],
			'ExternalShutter': self.szfilm.parameters['External shutter'],
			'Focus': self.szfocus.parameters['Focus'],
			'Defocus': self.szfocus.parameters['Defocus'],
			'ScreenCurrent': self.szscreen.parameters['Current'],
			'MainScreenPositions': self.szscreen.parameters['Main'],
			'MainScreenPosition': self.szscreen.parameters['Main'],
			'SmallScreenPosition': self.szscreen.parameters['Small'],
			'VacuumStatus': self.szvacuum.parameters['Status'],
			'ColumnPressure': self.szvacuum.parameters['Column pressure'],
			'ColumnValvePositions': self.szvacuum.parameters['Column valves'],
			'ColumnValvePosition': self.szvacuum.parameters['Column valves'],
			'TurboPump': self.szvacuum.parameters['Turbo pump'],
			'HolderStatus': self.szholder.parameters['Status'],
			'HolderTypes': self.szholder.parameters['Type'],
			'HolderType': self.szholder.parameters['Type'],
			'LowDoseStates': self.szlowdose.parameters['Status'],
			'LowDose': self.szlowdose.parameters['Status'],
			'LowDoseModes': self.szlowdose.parameters['Mode'],
			'LowDoseMode': self.szlowdose.parameters['Mode'],
		}

		self.controlmap = self.reverseMap(self.parametermap)
		for control in self.controlmap:
			try:
				bindControl(self, self.onControl, control)
			except ValueError:
				pass

	def setParameters(self, parameters, parametermap=None):
		ParameterMixin.setParameters(self, parameters, parametermap)

	def clearParameters(self, parametermap=None):
		ParameterMixin.clearParameters(self, parametermap)

class CCDCameraPanel(wx.Panel, ParameterMixin):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)

		self.sz = wx.GridBagSizer(5, 5)

		self.szcaminfo = CamInfoSizer(self)
		self.szcamconfig = CamConfigSizer(self)

		self.sz.Add(self.szcamconfig, (0, 0), (1, 1), wx.EXPAND)
		self.sz.Add(self.szcaminfo, (0, 1), (1, 1), wx.EXPAND)

		self.sz.AddGrowableCol(0)
		self.sz.AddGrowableCol(1)

		self.SetSizer(self.sz)

		self.parametermap = {}
		self.parametermap.update(self.szcaminfo.parametermap)
		self.parametermap.update(self.szcamconfig.parametermap)

		self.controlmap = self.reverseMap(self.parametermap)
		for control in self.controlmap:
			try:
				bindControl(self, self.onControl, control)
			except ValueError:
				pass
		self.Bind(EVT_CONFIGURATION_CHANGED, self.onCamConfig,
							self.szcamconfig.parameters['Camera configuration'])

	def onCamConfig(self, evt):
		name = self.GetParent().choice.GetStringSelection()
		if not name:
			return
		attributes = {'Configuration': evt.configuration}
		args = (name, attributes)
		threading.Thread(target=self.GetParent().node.refresh, args=args).start()

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'instrument'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CALCULATE,
													'calculate',
													shortHelpString='Get Magnifications')
		self.toolbar.Realize()

		self.tems = {}
		self.ccdcameras = {}

		self.choice = wx.Choice(self, -1)
		self.choice.Enable(False)
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Instrument')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.choice, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER)

		self.tempanel = TEMPanel(self, -1)
		self.tempanel.Show(False)

		self.ccdcamerapanel = CCDCameraPanel(self, -1)
		self.ccdcamerapanel.Show(False)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.Enable(False)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(leginon.gui.wx.Events.EVT_ADD_TEM, self.onAddTEM)
		self.Bind(leginon.gui.wx.Events.EVT_REMOVE_TEM, self.onRemoveTEM)
		self.Bind(leginon.gui.wx.Events.EVT_ADD_CCDCAMERA, self.onAddCCDCamera)
		self.Bind(leginon.gui.wx.Events.EVT_REMOVE_CCDCAMERA, self.onRemoveCCDCamera)
		self.Bind(wx.EVT_CHOICE, self.onChoice, self.choice)
		self.Bind(EVT_SET_PARAMETERS, self.onSetParameters)
		self.Bind(leginon.gui.wx.Events.EVT_GET_MAGNIFICATIONS_DONE,
							self.onGetMagnificationsDone)

	def setParameters(self, name, parameters):
		evt = SetParametersEvent(self, name, parameters)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSetParameters(self, evt):
		if evt.name in self.tems:
			self.tems[evt.name].update(evt.parameters)
			if self.choice.GetStringSelection() == evt.name:
				self.tempanel.setParameters(evt.parameters)
		elif evt.name in self.ccdcameras:
			self.ccdcameras[evt.name].update(evt.parameters)
			if self.choice.GetStringSelection() == evt.name:
				self.ccdcamerapanel.setParameters(evt.parameters)
		self.szmain.Layout()

	def onRefreshTool(self, evt):
		name = self.choice.GetStringSelection()
		if name in self.tems:
			attributes = self.tempanel.parametermap.keys()
		elif name in self.ccdcameras:
			attributes = self.ccdcamerapanel.parametermap.keys()
		else:
			return
		if name:
			args = (name, attributes)
			threading.Thread(target=self.node.refresh, args=args).start()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalculateTool,
											id=leginon.gui.wx.ToolBar.ID_CALCULATE)
		self.Enable(True)
		self.onChoice()

	def onCalculateTool(self, evt):
		string = self.choice.GetStringSelection()
		if not string:
			return
		args = (string,)
		self.choice.Enable(False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALCULATE, False)
		threading.Thread(target=self.node.getMagnifications, args=args).start()

	def onGetMagnificationsDone(self):
		self.choice.Enable(True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALCULATE, True)

	def getMagnificationsDone(self):
		evt = leginon.gui.wx.Events.GetMagnificationsDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onChoice(self, evt=None):
		if evt is None:
			string = self.choice.GetStringSelection()
		else:
			string = evt.GetString()
		try:
			if self.node is not None and self.node.hasMagnifications(string):
				self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALCULATE, True)
			else:
				self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALCULATE, False)
		except ValueError:
			pass
		if string in self.tems :
			if self.szmain.FindItem(self.tempanel):
				self.tempanel.clearParameters()
				self.tempanel.setParameters(self.tems[string])
			else:
				if self.szmain.FindItem(self.ccdcamerapanel):
					self.szmain.Detach(self.ccdcamerapanel)
					self.ccdcamerapanel.Show(False)
					self.ccdcamerapanel.clearParameters()
				self.tempanel.setParameters(self.tems[string])
				self.szmain.Add(self.tempanel, (1, 0), (1, 1), wx.ALIGN_CENTER)
				self.tempanel.Show(True)
		elif string in self.ccdcameras:
			if self.szmain.FindItem(self.ccdcamerapanel):
				self.ccdcamerapanel.clearParameters()
				self.ccdcamerapanel.setParameters(self.ccdcameras[string])
			else:
				if self.szmain.FindItem(self.tempanel):
					self.szmain.Detach(self.tempanel)
					self.tempanel.Show(False)
					self.tempanel.clearParameters()
				self.ccdcamerapanel.setParameters(self.ccdcameras[string])
				self.szmain.Add(self.ccdcamerapanel, (1, 0), (1, 1), wx.ALIGN_CENTER)
				self.ccdcamerapanel.Show(True)
		self.szmain.Layout()

	def onAddTEM(self, evt):
		self.tems[evt.name] = {}
		self.onAdd(evt)

	def onAddCCDCamera(self, evt):
		self.ccdcameras[evt.name] = {}
		self.onAdd(evt)

	def onRemoveTEM(self, evt):
		try:
			del self.tems[evt.name]
		except KeyError:
			pass
		self.onRemove(evt)

	def onRemoveCCDCamera(self, evt):
		try:
			del self.ccdcameras[evt.name]
		except KeyError:
			pass
		self.onRemove(evt)

	def onAdd(self, evt):
		empty = self.choice.IsEmpty()
		self.choice.Append(evt.name)
		if empty:
			self.choice.Enable(True)
			self.choice.SetSelection(0)
			self.onChoice()

	def onRemove(self, evt):
		n = self.choice.FindString(evt.name)
		if n == wx.NOT_FOUND:
			return
		self.choice.Delete(n)
		if self.choice.IsEmpty():
			self.choice.Enable(False)

	def onSetCCDCameras(self, evt):
		self.choice.AppendItems(evt.names)

	def addTEM(self, name):
		evt = leginon.gui.wx.Events.AddTEMEvent(self, name=name)
		self.GetEventHandler().AddPendingEvent(evt)

	def removeTEM(self, name):
		evt = leginon.gui.wx.Events.RemoveTEMEvent(self, name=name)
		self.GetEventHandler().AddPendingEvent(evt)

	def addCCDCamera(self, name):
		evt = leginon.gui.wx.Events.AddCCDCameraEvent(self, name=name)
		self.GetEventHandler().AddPendingEvent(evt)

	def removeCCDCamera(self, name):
		evt = leginon.gui.wx.Events.RemoveCCDCameraEvent(self, name=name)
		self.GetEventHandler().AddPendingEvent(evt)

class SelectionPanel(wx.Panel):
	def __init__(self, parent, passive=False):
		'''
		passive means that selecting an instrument does not actually set the 
		parent node's instrument.  You still must get the selection and set
		your instrument yourself.  Also, if the node's instrument changes,
		this gui will not reflect that change.  Useful if you want an 
		instrument selection that is used conditionally.
		'''
		wx.Panel.__init__(self, parent, -1)
		sb = wx.StaticBox(self, -1, 'Instrument')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.nonestring = 'None'
		self.passive = passive

		self.ctem = Choice(self, -1, choices=[self.nonestring])
		self.cccdcamera = Choice(self, -1, choices=[self.nonestring])

		sz = wx.GridBagSizer(3, 3)
		label = wx.StaticText(self, -1, 'TEM')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.ctem, (0, 1), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)
		label = wx.StaticText(self, -1, 'CCD Camera')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.cccdcamera, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)

		sz.AddGrowableCol(1)

		self.sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

		self.SetSizer(self.sbsz)
		self.SetAutoLayout(True)

		self.Bind(leginon.gui.wx.Events.EVT_SET_TEMS, self.onSetTEMs)
		self.Bind(leginon.gui.wx.Events.EVT_SET_CCDCAMERAS, self.onSetCCDCameras)
		if not passive:
			self.Bind(wx.EVT_CHOICE, self.onTEMChoice, self.ctem)
			self.Bind(wx.EVT_CHOICE, self.onCCDCameraChoice, self.cccdcamera)
			self.Bind(leginon.gui.wx.Events.EVT_SET_TEM, self.onSetTEM)
			self.Bind(leginon.gui.wx.Events.EVT_SET_CCDCAMERA, self.onSetCCDCamera)

	def setProxy(self, proxy):
		self.proxy = proxy
		if self.proxy is None:
			tem = None
			ccdcamera = None
			tems = []
			ccdcameras = []
		else:
			tem = self.proxy.getTEMName()
			tems = self.proxy.getTEMNames()
			ccdcamera = self.proxy.getCCDCameraName()
			ccdcameras = self.proxy.getCCDCameraNames()
		self.setTEMs(tems)
		self.setTEM(tem)
		self.setCCDCameras(ccdcameras)
		self.setCCDCamera(ccdcamera)

	def GetValue(self):
		value = {}
		value['tem'] = str(self.getTEM())
		value['ccdcamera'] = str(self.getCCDCamera())
		return value

	def SetValue(self, value):
		tem = value['tem']
		ccdcamera = value['ccdcamera']
		if tem == 'None':
			tem = None
		if ccdcamera == 'None':
			ccdcamera = None
		self.setTEM(tem)
		self.setCCDCamera(ccdcamera)

	def getTEM(self):
		tem = self.ctem.GetStringSelection()
		if tem == self.nonestring:
			tem = None
		return tem

	def setTEM(self, tem):
		if tem is None:
			tem = self.nonestring
		elif self.ctem.FindString(tem) == wx.NOT_FOUND:
			tem = self.nonestring
		self.ctem.SetStringSelection(tem)
		if not self.ctem.IsEnabled():
			self.ctem.Enable(True)

	def onSetTEM(self, evt):
		self.setTEM(evt.name)

	def setTEMs(self, tems):
		string = self.ctem.GetStringSelection()
		self.ctem.Freeze()
		self.ctem.Clear()
		self.ctem.AppendItems([self.nonestring] + tems)
		if self.ctem.FindString(string) == wx.NOT_FOUND:
			string = self.nonestring
		self.ctem.SetStringSelection(string)
		self.ctem.Thaw()
		self.sbsz.Layout()

	def onSetTEMs(self, evt):
		self.setTEMs(evt.names)

	def getCCDCamera(self):
		ccdcamera = self.cccdcamera.GetStringSelection()
		if ccdcamera == self.nonestring:
			ccdcamera = None
		return ccdcamera

	def setCCDCamera(self, ccdcamera):
		if ccdcamera is None:
			ccdcamera = self.nonestring
		elif self.cccdcamera.FindString(ccdcamera) == wx.NOT_FOUND:
			ccdcamera = self.nonestring
		self.cccdcamera.SetStringSelection(ccdcamera)
		if not self.cccdcamera.IsEnabled():
			self.cccdcamera.Enable(True)

	def onSetCCDCamera(self, evt):
		self.setCCDCamera(evt.name)

	def setCCDCameras(self, ccdcameras):
		string = self.cccdcamera.GetStringSelection()
		self.cccdcamera.Freeze()
		self.cccdcamera.Clear()
		self.cccdcamera.AppendItems([self.nonestring] + ccdcameras)
		if self.cccdcamera.FindString(string) == wx.NOT_FOUND:
			string = self.nonestring
		self.cccdcamera.SetStringSelection(string)
		self.cccdcamera.Thaw()
		self.sbsz.Layout()

	def onSetCCDCameras(self, evt):
		self.setCCDCameras(evt.names)

	def onTEMChoice(self, evt):
		string = evt.GetString()
		if string == self.nonestring:
			tem = None
		else:
			tem = string
		evt = leginon.gui.wx.Events.TEMChangeEvent(self, name=tem)
		if not self.passive:
			self.GetEventHandler().AddPendingEvent(evt)

	def onCCDCameraChoice(self, evt):
		string = evt.GetString()
		if string == self.nonestring:
			ccdcamera = None
		else:
			ccdcamera = string
		if not self.passive:
			evt = leginon.gui.wx.Events.CCDCameraChangeEvent(self, name=ccdcamera)
			self.GetEventHandler().AddPendingEvent(evt)

class SelectionMixin(object):
	def __init__(self):
		self.instrumentselections = []
		self.Bind(leginon.gui.wx.Events.EVT_SET_TEMS, self.onSetTEMs)
		self.Bind(leginon.gui.wx.Events.EVT_SET_CCDCAMERAS, self.onSetCCDCameras)

	def onNodeInitialized(self):
		self.proxy = self.node.instrument
		self.Bind(leginon.gui.wx.Events.EVT_TEM_CHANGE, self.onTEMChange)
		self.Bind(leginon.gui.wx.Events.EVT_CCDCAMERA_CHANGE, self.onCCDCameraChange)

	def initInstrumentSelection(self, instrumentselection):
		self.instrumentselections.append(instrumentselection)
		tem = self.proxy.getTEMName()
		tems = self.proxy.getTEMNames()
		ccdcamera = self.proxy.getCCDCameraName()
		ccdcameras = self.proxy.getCCDCameraNames()
		instrumentselection.setTEMs(tems)
		instrumentselection.setTEM(tem)
		instrumentselection.setCCDCameras(ccdcameras)
		instrumentselection.setCCDCamera(ccdcamera)

	def setInstrumentSelection(self, instrumentselection):
		self.initInstrumentSelection(instrumentselection)

		if instrumentselection.passive:
			return

		self.Bind(leginon.gui.wx.Events.EVT_SET_TEM, self.onSetTEM)
		self.Bind(leginon.gui.wx.Events.EVT_SET_CCDCAMERA, self.onSetCCDCamera)

	def onTEMChange(self, evt):
		threading.Thread(target=self.proxy.setTEM, args=(evt.name,)).start()

	def onCCDCameraChange(self, evt):
		threading.Thread(target=self.proxy.setCCDCamera, args=(evt.name,)).start()

	def instrumentSelectionEvent(self, evt, passive):
		if not self.instrumentselections:
			return
		still_exist = []
		for i in self.instrumentselections:
			## handle if SelectionPanel was destroyed already
			try:
				selector_is_passive = i.passive
			except:
				continue
			still_exist.append(i)
			if i.passive and not passive:
				continue
			evthandler = i.GetEventHandler()
			evthandler.AddPendingEvent(evt)
		## new list of selection panels that still exist
		self.instrumentselections = still_exist

	def setCameraSize(self):
		try:
			camerasize = self.proxy.camerasize
			self.settingsdialog.widgets['camera settings'].setSize(camerasize)
		except AttributeError:
			pass

	def onSetTEM(self, evt):
		self.instrumentSelectionEvent(evt, passive=False)

	def onSetTEMs(self, evt):
		self.instrumentSelectionEvent(evt, passive=True)

	def onSetCCDCamera(self, evt):
		self.instrumentSelectionEvent(evt, passive=False)
		self.setCameraSize()

	def onSetCCDCameras(self, evt):
		self.instrumentSelectionEvent(evt, passive=True)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Instrument Test')
			#panel = Panel(frame, 'Test')
			panel = SelectionPanel(frame, None, ['Tecnai'], None, ['Tietz', 'Tietz Fastscan'])
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

