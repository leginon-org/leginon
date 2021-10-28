# -*- coding: iso-8859-1 -*-
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org

import copy
import wx
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry, EVT_ENTRY
import numpy
import re
from pyami import primefactor

ConfigurationChangedEventType = wx.NewEventType()
SetConfigurationEventType = wx.NewEventType()

EVT_CONFIGURATION_CHANGED = wx.PyEventBinder(ConfigurationChangedEventType)
EVT_SET_CONFIGURATION = wx.PyEventBinder(SetConfigurationEventType)

class ConfigurationChangedEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, ConfigurationChangedEventType,
																source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class SetConfigurationEvent(wx.PyCommandEvent):
	def __init__(self, configuration, source):
		wx.PyCommandEvent.__init__(self, SetConfigurationEventType, source.GetId())
		self.SetEventObject(source)
		self.configuration = configuration

class CameraPanel(wx.Panel):
	def __init__(self, parent, hide_frames=False):
		wx.Panel.__init__(self, parent, -1)
		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.hide_frames = hide_frames
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.size = None
		self.binmethod = 'exact'
		self.geometry = None
		self.binnings = {'x': [1,2,3,4,6,8], 'y': [1,2,3,4,6,8]}
		self.defaultexptime = 1000.0
		self.defaultsaveframes = False
		self.defaultframetime = 200
		self.defaultusecds = False
		self.defaultfastsave = False
		self.defaultalignframes = False
		self.defaultalignfilter = 'None'
		#self.defaultuseframes = ''
		self.defaultreadoutdelay= 0
		self.defaultrequestnframes = 1
		self.common = {}
		self.setfuncs = {
			'exposure time': self._setExposureTime,
			'save frames': self._setSaveFrames,
			'frame time': self._setFrameTime,
			'align frames': self._setAlignFrames,
			'align filter': self._setAlignFilter,
			#'use frames': self._setUseFrames,
			'readout delay': self._setReadoutDelay,
			'fast save': self._setFastSave,
			'use cds': self._setUseCds,
			'request nframes': self._setRequestNFrames,
		}
		self.getfuncs = {
			'exposure time': self._getExposureTime,
			'save frames': self._getSaveFrames,
			'frame time': self._getFrameTime,
			'align frames': self._getAlignFrames,
			'align filter': self._getAlignFilter,
			#'use frames': self._getUseFrames,
			'readout delay': self._getReadoutDelay,
			'fast save': self._getFastSave,
			'use cds': self._getUseCds,
			'request nframes': self._getRequestNFrames,
		}

		self.framewidges = []

		# geometry
		self.ccommon = wx.Choice(self, -1, choices = ['(None)'])
		self.ccommon.SetSelection(0)
		bcustom = wx.Button(self, -1, 'Custom...')

		std = wx.StaticText(self, -1, 'Dimension:')
		self.stdimension = wx.StaticText(self, -1, '')

		sto = wx.StaticText(self, -1, 'Offset:')
		self.stoffset = wx.StaticText(self, -1, '')

		stb = wx.StaticText(self, -1, 'Binning:')
		self.stbinning = wx.StaticText(self, -1, '')

		self.szmain = wx.GridBagSizer(3, 3)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.ccommon, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(bcustom, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		self.szmain.Add(sz, (0, 0), (1, 2), wx.EXPAND)

		self.szmain.Add(std, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stdimension, (1, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(sto, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stoffset, (2, 1), (1, 1), wx.ALIGN_CENTER)

		self.szmain.Add(stb, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(self.stbinning, (3, 1), (1, 1), wx.ALIGN_CENTER)

		# exposure time
		stet = wx.StaticText(self, -1, 'Exposure time:')
		self.feexposuretime = FloatEntry(self, -1, min=0.0, chars=7)
		stms = wx.StaticText(self, -1, 'ms')

		self.szmain.Add(stet, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz = wx.GridBagSizer(0, 3)
		sz.Add(self.feexposuretime, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(stms, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(sz, (4, 1), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		sz = self.createFrameCameraSizer()
		self.szmain.Add(sz, (7, 0), (1, 3), wx.ALIGN_CENTER|wx.EXPAND)
		if self.hide_frames:
			self.disableFrameWidges()

		self.szmain.AddGrowableCol(1)
		self.szmain.AddGrowableCol(2)

		self.sbsz.Add(self.szmain, 0, wx.EXPAND|wx.ALL, 2)

		self.SetSizerAndFit(self.sbsz)

		self.Bind(wx.EVT_CHOICE, self.onCommonChoice, self.ccommon)
		self.Bind(wx.EVT_BUTTON, self.onCustomButton, bcustom)
		self.Bind(EVT_ENTRY, self.onExposureTime, self.feexposuretime)
		self.Bind(EVT_SET_CONFIGURATION, self.onSetConfiguration)
		#self.Enable(False)

	def disableFrameWidges(self):
		self.saveframes.Disable()
		self.alignframes.Disable()
		self.alignfilter.Disable()
		#self.useframes.Disable()
		self.usecds.Disable()
		self.fastsave.Disable()

	def createFrameCameraSizer(self):
		sb = wx.StaticBox(self, -1, 'Camera with Movie Mode')
		ddsb = wx.StaticBoxSizer(sb, wx.VERTICAL)
		ddsz = wx.GridBagSizer(5, 5)
		# save frames
		self.saveframes = wx.CheckBox(self, -1, 'Save frames')
		self.framewidges.append(self.saveframes)
		ddsz.Add(self.saveframes, (0, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# frame time
		stet = wx.StaticText(self, -1, 'Exposure time per Frame:')
		self.frametime = FloatEntry(self, -1, min=0.01, chars=7)
		self.framewidges.append(self.frametime)
		stms = wx.StaticText(self, -1, 'ms')

		ddsz.Add(stet, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		ftsz = wx.GridBagSizer(0, 3)
		ftsz.Add(self.frametime, (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		ftsz.Add(stms, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		ddsz.Add(ftsz, (1, 1), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# DE64c Request Total Movie Frames
		label = wx.StaticText(self, -1, 'DEc Request Total Movie Frames:')
		self.requestnframes = IntEntry(self, -1)
		self.framewidges.append(self.requestnframes)
		ddsz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		ddsz.Add(self.requestnframes, (2, 1), (1, 1), wx.ALIGN_CENTER | wx.EXPAND)

		# use raw frames
		label = wx.StaticText(self, -1, 'Frames to use:')
		self.useframes = Entry(self, -1)
		self.framewidges.append(self.useframes)
		ddsz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		ddsz.Add(self.useframes, (3, 1), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)

		# readout delay
		strd = wx.StaticText(self, -1, 'Readout delay:')
		self.readoutdelay = IntEntry(self, -1, chars=7)
		self.framewidges.append(self.readoutdelay)
		stms = wx.StaticText(self, -1, 'ms')
		sz = wx.BoxSizer(wx.HORIZONTAL)
		sz.Add(strd)
		sz.Add(self.readoutdelay)
		sz.Add(stms)
		ddsz.Add(sz, (4, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# save 8x8 fake image so it is fast to save and transfer
		self.fastsave = wx.CheckBox(self, -1, 'Save 8x8 stats image to speed up')
		self.framewidges.append(self.fastsave)
		ddsz.Add(self.fastsave, (5, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# use cds for K3
		self.usecds = wx.CheckBox(self, -1, 'Use CDS (Gatan K3)')
		self.framewidges.append(self.usecds)
		ddsz.Add(self.usecds, (6, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# align frames box
		sb = wx.StaticBox(self, -1, 'Frame-Aligning Camera Only')
		afsb = wx.StaticBoxSizer(sb, wx.VERTICAL)
		afsz = wx.GridBagSizer(3, 3)
		# align frames
		self.alignframes = wx.CheckBox(self, -1, 'Align frames')
		self.framewidges.append(self.alignframes)
		afsz.Add(self.alignframes, (0, 0), (1, 2), wx.ALIGN_CENTER|wx.EXPAND)

		# align frame filter
		label = wx.StaticText(self, -1, 'c-correlation filter:')
		self.alignfilter = wx.Choice(self, -1, choices=self.getAlignFilters())
		self.alignfilter.SetSelection(0)
		self.framewidges.append(self.alignfilter)
		afsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		afsz.Add(self.alignfilter, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.EXPAND)
		afsb.Add(afsz, 0, wx.EXPAND|wx.ALL, 2)

		ddsz.Add(afsb, (7, 0), (3, 2), wx.ALIGN_CENTER|wx.EXPAND)

		ddsb.Add(ddsz, 0, wx.EXPAND|wx.ALL, 2)
		ddsz.AddGrowableCol(1)
		return ddsb

	def bindFrameCameraEvents(self):
		self.Bind(wx.EVT_CHECKBOX, self.onSaveFrames, self.saveframes)
		self.Bind(EVT_ENTRY, self.onFrameTime, self.frametime)
		#self.Bind(EVT_ENTRY, self.onUseFrames, self.useframes)
		self.Bind(EVT_ENTRY, self.onReadoutDelay, self.readoutdelay)

	def setGeometryLimits(self,limitdict):
		if limitdict is None:
			self.setSize(None)
		if 'binnings' in limitdict.keys():
			self.binnings['x'] = limitdict['binnings']
			self.binnings['y'] = limitdict['binnings']
		if 'binmethod' in limitdict.keys():
			self.binmethod = limitdict['binmethod']
		if 'size' in limitdict.keys():
			self.setSize(limitdict['size'])
		else:
			self.setSize(None)

	def setSize(self, size):
		if size is None:
			self.size = None
			self.Freeze()
			self.choices, self.common = None, None
			self.ccommon.Clear()
			self.ccommon.Append('(None)')
			self.szmain.Layout()
			#self.Enable(False)
			self.Thaw()
		else:
			self.size = dict(size)
			self.Freeze()
			self.choices, self.common = self.getCenteredGeometries()
			self.ccommon.Clear()
			self.ccommon.AppendItems(self.choices)
			if self.geometry is None or not self.validateGeometry():
				self.ccommon.SetSelection(len(self.choices) - 1)
				self.setGeometry(self.common[self.ccommon.GetStringSelection()])
			else:
				self.setCommonChoice()
			if self.feexposuretime.GetValue() is None:
				self.feexposuretime.SetValue(self.defaultexptime)
			#self.Enable(True)
			self.szmain.Layout()
			self.Thaw()

	def clear(self):
		if self.size is None:
			return
		self.Freeze()
		self.ccommon.SetSelection(len(self.choices) - 1)
		self.setGeometry(self.common[self.ccommon.GetStringSelection()])
		self.feexposuretime.SetValue(self.defaultexptime)
		self.saveframes.SetValue(self.defaultsaveframes)
		self.frametime.SetValue(self.defaultframetime)
		self.alignframes.SetValue(self.defaultalignframes)
		self.alignfilter.SetValue(self.defaultalignfilter)
		#self.useframes.SetValue(self.defaultuseframes)
		self.readoutdelay.SetValue(self.defaultreadoutdelay)
		self.fastsave.SetValue(self.defaultfastsave)
		self.usecds.SetValue(self.defaultusecds)
		self.requestnframes.SetValue(self.requestnframes)
		#self.Enable(False)
		self.Thaw()

	def onConfigurationChanged(self):
		evt = ConfigurationChangedEvent(self.getConfiguration(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onExposureTime(self, evt):
		self.onConfigurationChanged()

	def onSaveFrames(self, evt):
		self.onConfigurationChanged()

	def onFrameTime(self, evt):
		self.onConfigurationChanged()

	def onUseFrames(self, evt):
		self.onConfigurationChanged()

	def onReadoutDelay(self, evt):
		self.onConfigurationChanged()

	def onRequestNFrames(self, evt):
		self.onConfigurationchanged()

	def setCommonChoice(self):
		for key, geometry in self.common.items():
			flag = True
			for i in ['dimension', 'offset', 'binning']:
				if self.geometry[i] != geometry[i]:
					flag = False
					break
			if flag:
				self.ccommon.SetStringSelection(key)
				return
		if self.ccommon.FindString('(Custom)') is wx.NOT_FOUND:
			self.ccommon.Insert('(Custom)', 0)
			self.ccommon.SetSelection(0)

	def _getDimension(self):
		return self.geometry['dimension']

	def _setDimension(self, value):
		self.geometry['dimension'] = value
		self.setCommonChoice()

	def _getOffset(self):
		return self.geometry['offset']

	def _setOffset(self, value):
		self.geometry['offset'] = value
		self.setCommonChoice()

	def _getBinning(self):
		return self.geometry['binning']

	def _setBinning(self, value):
		self.geometry['binning'] = value
		self.setCommonChoice()

	def _getExposureTime(self):
		return self.feexposuretime.GetValue()

	def _setExposureTime(self, value):
		self.feexposuretime.SetValue(value)

	def _getSaveFrames(self):
		return self.saveframes.GetValue()

	def _setSaveFrames(self, value):
		value = bool(value)
		self.saveframes.SetValue(value)

	def _getFrameTime(self):
		return self.frametime.GetValue()

	def _setFrameTime(self, value):
		self.frametime.SetValue(value)

	def _getUseCds(self):
		return self.usecds.GetValue()

	def _setUseCds(self, value):
		value = bool(value)
		self.usecds.SetValue(value)

	def _getFastSave(self):
		return self.fastsave.GetValue()

	def _setFastSave(self, value):
		value = bool(value)
		self.fastsave.SetValue(value)
	def _getRequestNFrames(self):
		return self.requestnframes.GetValue()

	def _setRequestNFrames(self, value):
		self.requestnframes.SetValue(value)

	def _getAlignFrames(self):
		return self.alignframes.GetValue()

	def _setAlignFrames(self, value):
		value = bool(value)
		self.alignframes.SetValue(value)

	def getAlignFilters(self):
		return ['None','Hanning Window (default)','Bandpass Filter (default)','Sobel Filter (default)','Combined Filter (default)']

	def _getAlignFilter(self):
		return self.alignfilter.GetStringSelection()

	def _setAlignFilter(self, value):
		if value:
			value = str(value)
		else:
			value = 'None'
		self.alignfilter.SetStringSelection(value)

	def _getUseFrames(self):
		frames_str = self.useframes.GetValue()
		numbers = re.split('\D+', frames_str)
		numbers = filter(None, numbers)
		if numbers:
			numbers = map(int, numbers)
			numbers = tuple(numbers)
		else:
			numbers = ()
		return numbers

	def _setUseFrames(self, value):
		if value:
			value = str(value)
		else:
			value = ''
		self.useframes.SetValue(value)

	def _getReadoutDelay(self):
		return self.readoutdelay.GetValue()

	def _setReadoutDelay(self, value):
		return self.readoutdelay.SetValue(value)

	def onCommonChoice(self, evt):
		key = evt.GetString()
		if key == '(Custom)' or key.startswith('-'):
			return
		if self.setGeometry(self.common[key]):
			self.onConfigurationChanged()
		n = self.ccommon.FindString('(Custom)')
		if n is not wx.NOT_FOUND:
			self.ccommon.Delete(n)

	def onCustomButton(self, evt):
		dialog = CustomDialog(self, self.getGeometry())
		if dialog.ShowModal() == wx.ID_OK:
			if self.setGeometry(dialog.getGeometry()):
				self.onConfigurationChanged()
			self.setCommonChoice()
		dialog.Destroy()

	def getCenteredGeometry(self, dimension, binning):
		offset ={}
		for axis in ['x','y']:
			offset[axis] = int((self.size[axis]/binning - dimension)/2)

		geometry = {'dimension': {'x': dimension, 'y': dimension},
								'offset': {'x': offset['x'], 'y': offset['y']},
								'binning': {'x': binning, 'y': binning}}
		return geometry

	def getFullGeometry(self,binning):
		if self.binmethod == 'exact' and ((self.size['x'] % binning) or (self.size['y'] % binning)):
			return None
		dimx = self.size['x'] / binning
		dimy = self.size['y'] / binning
		geometry = {'dimension': {'x': dimx, 'y': dimy},
								'offset': {'x': 0, 'y': 0},
								'binning': {'x': binning, 'y': binning}}
		return geometry

	def getCenteredGeometries(self):
		geometries = {}
		keys = []
		show_sections = False
		if self.size['x'] != self.size['y']:
			show_sections = True
			keys.append('--- Full ---')
			for binning in self.binnings['x']:
				dimx = self.size['x'] / binning
				dimy = self.size['y'] / binning
				key = '%d x %d bin %d' % (dimx,dimy,binning)
				geo = self.getFullGeometry(binning)
				if geo is not None:
					geometries[key] = geo
					keys.append(key)
		if self.binnings['x'] != self.binnings['y']:
			return geometries
		self.minsize = min(self.size['x'],self.size['y'])
		dimensions = [int(self.minsize/float(b)) for b in self.binnings['x']]
		def good(dim):
			return not bool(numpy.modf(dim)[1]-dim)
		def filtergood(input, mask):
			result = []
			for i,inval in enumerate(input):
				if mask[i]:
					result.append(inval)
			return result
		if self.binmethod == 'exact':
			mask = [good(dim) for dim in dimensions]
		else:
			mask = [True for dim in dimensions]
		dimensions = filtergood(dimensions, mask)
		def minsize(size):
			return size >= self.minsize / max(self.binnings['x'])
		dimensions = filter(minsize, dimensions)
		dimensions = map((lambda x: primefactor.getAllEvenPrimes(x)[-1]),dimensions)
		binnings = filtergood(self.binnings['x'], mask)
		dimensions.reverse()
		if show_sections:
			keys.append('--- Center ---')
		for d in dimensions:
			for b in self.binnings['x']:
				if d*b <= self.minsize:
					key = '%d x %d bin %d' % (d, d, b)
					geometries[key] = self.getCenteredGeometry(d, b)
					keys.append(key)
				else:
					break
		return keys, geometries

	def validateGeometry(self, geometry=None):
		if geometry is None:
			geometry = self.geometry
		for a in ['x', 'y']:
			try:
				if geometry['dimension'][a] < 1 or geometry['offset'][a] < 0:
					return False
				if geometry['binning'][a] not in self.binnings[a]:
					return False
				size = geometry['dimension'][a] + geometry['offset'][a]
				size *= geometry['binning'][a]
				if size > self.size[a]:
					return False
			except:
				return False
		return True

	def cmpGeometry(self, geometry):
		if self.geometry == geometry:
			return True
		for g in ['dimension', 'offset', 'binning']:
			try:
				for a in ['x', 'y']:
					if self.geometry[g][a] != geometry[g][a]:
						return False
			except (KeyError, TypeError):
				return False
		return True

	def setGeometry(self, geometry):
		if self.cmpGeometry(geometry):
			return False

		if self.size is not None and not self.validateGeometry(geometry):
			raise ValueError

		self._setGeometry(geometry)

		return True

	def getGeometry(self):
		return self.geometry

	def getConfiguration(self):
		g = self.getGeometry()
		if g is None:
			return None
		c = copy.deepcopy(g)
		for key,func in self.getfuncs.items():
			c[key] = func()
		return c

	def _setGeometry(self, geometry):
		if self.geometry is None:
			self.geometry = {}
		else:
			self.geometry = copy.deepcopy(self.geometry)
		self.Freeze()
		for g in ['dimension', 'offset', 'binning']:
			if g not in self.geometry:
				self.geometry[g] = {}
			try:
				self.geometry[g].update(dict(geometry[g]))
				if g == 'offset':
					label = '(%d, %d)'
				else:
					label = '%d x %d'
				label = label % (self.geometry[g]['x'], self.geometry[g]['y'])
				getattr(self, 'st' + g).SetLabel(label)
			except:
				pass
		self.szmain.Layout()
		self.Thaw()
		return True

	def _setConfiguration(self, value):
		for key, func in self.setfuncs.items():
			if key in value:
				func(value[key])
		self._setGeometry(value)
		self.setCommonChoice()

	def setConfiguration(self, value):
		for key, func in self.setfuncs.items():
			if key in value:
				func(value[key])
		self.setGeometry(value)
		if self.size is not None:
			self.setCommonChoice()
		#if not self.IsEnabled():
		#	self.Enable(True)

	def onSetConfiguration(self, evt):
		self.setConfiguration(evt.configuration)

class CustomDialog(wx.Dialog):
	def __init__(self, parent, geometry):
		wx.Dialog.__init__(self, parent, -1, 'Custom')
		sb = wx.StaticBox(self, -1, 'Camera Configuration')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		stx = wx.StaticText(self, -1, 'x')
		sty = wx.StaticText(self, -1, 'y')
		stdimension = wx.StaticText(self, -1, 'Dimension:')
		self.iexdimension = IntEntry(self, -1, min=1, max=parent.size['x'],
																	chars=len(str(parent.size['x'])))
		self.ieydimension = IntEntry(self, -1, min=1, max=parent.size['y'],
																	chars=len(str(parent.size['y'])))
		stbinning = wx.StaticText(self, -1, 'Binning:')
		self.cxbinning = wx.Choice(self, -1, choices=map(str,parent.binnings['x']))
		self.cybinning = wx.Choice(self, -1, choices=map(str,parent.binnings['y']))
		stoffset = wx.StaticText(self, -1, 'Offset:')
		self.iexoffset = IntEntry(self, -1, min=0, max=parent.size['x'],
																	chars=len(str(parent.size['x'])))
		self.ieyoffset = IntEntry(self, -1, min=0, max=parent.size['y'],
																	chars=len(str(parent.size['y'])))
		self.szxy = wx.GridBagSizer(5, 5)
		self.szxy.Add(stx, (0, 1), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(sty, (0, 2), (1, 1), wx.ALIGN_CENTER)
		self.szxy.Add(stdimension, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.iexdimension, (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(self.ieydimension, (1, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(stbinning, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.cxbinning, (2, 1), (1, 1),
									wx.ALIGN_CENTER|wx.ALL)
		self.szxy.Add(self.cybinning, (2, 2), (1, 1),
									wx.ALIGN_CENTER|wx.ALL)
		self.szxy.Add(stoffset, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szxy.Add(self.iexoffset, (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)
		self.szxy.Add(self.ieyoffset, (3, 2), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALL)

		bok = wx.Button(self, wx.ID_OK, 'OK')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		self.sbsz.Add(self.szxy, 0, wx.ALIGN_CENTER)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.sbsz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		sz.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		if geometry is not None:
			self.iexdimension.SetValue(int(geometry['dimension']['x']))
			self.ieydimension.SetValue(int(geometry['dimension']['y']))
			self.cxbinning.SetStringSelection(str(geometry['binning']['x']))
			self.cybinning.SetStringSelection(str(geometry['binning']['y']))
			self.iexoffset.SetValue(int(geometry['offset']['x']))
			self.ieyoffset.SetValue(int(geometry['offset']['y']))

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onOK, bok)

	def getGeometry(self):
		geometry = {'dimension': {}, 'binning': {}, 'offset': {}}
		geometry['dimension']['x'] = self.iexdimension.GetValue()
		geometry['dimension']['y'] = self.ieydimension.GetValue()
		geometry['binning']['x'] = int(self.cxbinning.GetStringSelection())
		geometry['binning']['y'] = int(self.cybinning.GetStringSelection())
		geometry['offset']['x'] = self.iexoffset.GetValue()
		geometry['offset']['y'] = self.ieyoffset.GetValue()
		return geometry

	def onOK(self, evt):
		geometry = self.getGeometry()
		if geometry is not None and self.GetParent().validateGeometry(geometry):
			evt.Skip()
		else:
			dialog = wx.MessageDialog(self, 'Invalid camera geometry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Camera Test')
			panel = CameraPanel(frame)
			panel.setGeometry({'dimension': {'x': 1024, 'y': 1024},
													'offset': {'x': 0, 'y': 0},
													'binning': {'x': 1, 'y': 1}})
			panel.setSize({'x': 512, 'y': 512})
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()
