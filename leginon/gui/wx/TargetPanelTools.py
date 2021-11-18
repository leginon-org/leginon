#!/usr/bin/python -O
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/TargetPanelTools.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-08 19:39:01 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $
#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import wx
import sys
import numpy
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.TargetPanelBitmaps
#import shortpath

TargetingEventType = wx.NewEventType()
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)

ShowNumbersEventType = wx.NewEventType()
EVT_SHOWNUMBERS = wx.PyEventBinder(ShowNumbersEventType)

ShowAreaEventType = wx.NewEventType()
EVT_SHOWAREA = wx.PyEventBinder(ShowAreaEventType)

ShowExposureEventType = wx.NewEventType()
EVT_SHOWEXPOSURE = wx.PyEventBinder(ShowExposureEventType)

##################################
##
##################################

class TargetingEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, TargetingEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

class ShowNumbersEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, ShowNumbersEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

class ShowAreaEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, ShowAreaEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

class ShowExposureEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, ShowExposureEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value
##################################
##
##################################

class TargetTypeTool(leginon.gui.wx.ImagePanelTools.TypeTool):
	def __init__(self, parent, name, display=None, settings=None, target=None, shape='+', unique=False, numbers=None, area=None, exp=None, size=16):
		self.color = display
		self.shape = shape 
		self.size = size 
		leginon.gui.wx.ImagePanelTools.TypeTool.__init__(self, parent, name, display=display, settings=settings)

		self.targettype = TargetType(self.name, self.color, self.shape, self.size, unique)
		self.numberstype = TargetType(self.name, self.color, 'numbers', self.size, unique)
		self.areatype = TargetType(self.name, self.color, 'area', self.size, unique)
		self.exptype = TargetType(self.name, self.color, 'exp', self.size, unique)

		self.togglebuttons['display'].SetBitmapDisabled(self.bitmaps['display'])

		# display numbers does not require target is selectable.
		if numbers is not None:
			togglebutton = self.addToggleButton('numbers', 'Show Numbers')
			self.enableToggleButton('numbers', True)
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleNumbers)
			self.usenumbers = True
		if target is not None:
			# target is selectable
			if area is not None:
				togglebutton = self.addToggleButton('area', 'Show Image Area')
				self.enableToggleButton('area', True)
				togglebutton.Bind(wx.EVT_BUTTON, self.onToggleArea)
				self.usearea = True

			if exp is not None:
				togglebutton = self.addToggleButton('exp', 'Show Exposure Area')
				self.enableToggleButton('exp', True)
				togglebutton.Bind(wx.EVT_BUTTON, self.onToggleExposure)
				self.usearea = True
				self.useexp = True
	
			togglebutton = self.addToggleButton('target', 'Add Targets')
			self.enableToggleButton('target', False)
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleTarget)

	#--------------------
	def getBitmaps(self):
		bitmaps = leginon.gui.wx.ImagePanelTools.TypeTool.getBitmaps(self)
		bitmaps['display'] = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, self.shape)
		bitmaps['numbers'] = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, 'numbers')
		bitmaps['area'] = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, 'area')
		bitmaps['exp'] = leginon.gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, 'exp')
		bitmaps['target'] = leginon.gui.wx.ImagePanelTools.getBitmap('arrow.png')
		return bitmaps

	#--------------------
	def onToggleTarget(self, evt):
		if not self.togglebuttons['target'].IsEnabled():
			self.togglebuttons['target'].SetValue(False)
			return
		#if self.togglebuttons['target'].GetValue() is True:
		#	self.togglebuttons['target'].SetBackgroundColour(wx.Colour(160,160,160))
		#else:
		#	self.togglebuttons['target'].SetBackgroundColour(wx.WHITE)
		evt = TargetingEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['target'].GetEventHandler().AddPendingEvent(evt)

	#--------------------
	def sortTargets(self, targets):
		"""
		input: list of targets where target.position is a tuple
		output: sorted list of targets where target.position is a tuple
		"""
		#convert to list of (x,y) tuples
		targetlist = [t.position for t in targets]
		bestorder, bestscore = shortpath.sortPoints(list(targetlist), numiter=3, maxeval=70000)
		sortedtargets = []
		for i in bestorder:
			sortedtargets.append(targets[i])
		return sortedtargets

	#--------------------
	def onToggleNumbers(self, evt):
		if not self.togglebuttons['numbers'].IsEnabled():
			self.togglebuttons['numbers'].SetValue(False)
			return
		#if self.togglebuttons['numbers'].GetValue() is True:
		#	self.targettype.setTargets(self.sortTargets(self.targettype.getTargets()))
		self.numberstype.setTargets(self.targettype.getTargets())
		evt = ShowNumbersEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['numbers'].GetEventHandler().AddPendingEvent(evt)

	def onToggleArea(self, evt):
		if not self.togglebuttons['area'].IsEnabled():
			self.togglebuttons['area'].SetValue(False)
			return
		self.areatype.setTargets(self.targettype.getTargets())
		evt = ShowAreaEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['area'].GetEventHandler().AddPendingEvent(evt)

	def onToggleExposure(self, evt):
		if not self.togglebuttons['exp'].IsEnabled():
			self.togglebuttons['exp'].SetValue(False)
			return
		# get new image vector and beam size
		self.parent.parent.parent.node.uiRefreshTargetImageVectors()
		self.parent.parent.imagevectors = self.parent.parent.parent.node.getTargetImageVectors()
		self.parent.parent.beamradius = self.parent.parent.parent.node.getTargetBeamRadius()
		# Below if used by TomoTargetImagePanel
		if hasattr(self.parent.parent,'trackimagevectors'):
			self.parent.parent.trackimagevectors = self.parent.parent.parent.node.getTrackImageVectors()
		if hasattr(self.parent.parent,'trackbeamradius'):
			self.parent.parent.trackbeamradius = self.parent.parent.parent.node.getTrackBeamRadius()
		if hasattr(self.parent.parent,'focusimagevectors'):
			self.parent.parent.focusimagevectors = self.parent.parent.parent.node.getFocusImageVectors()
		if hasattr(self.parent.parent,'focusbeamradius'):
			self.parent.parent.focusbeamradius = self.parent.parent.parent.node.getFocusBeamRadius()
		
		# set and show targets
		self.exptype.setTargets(self.targettype.getTargets())
		evt = ShowExposureEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['exp'].GetEventHandler().AddPendingEvent(evt)
##################################
##
##################################

class Target(object):
	def __init__(self, x, y, type):
		self.position = (x, y)
		self.x = x
		self.y = y
		self.type = type

##################################
##
##################################

class StatsTarget(Target):
	def __init__(self, x, y, type, stats):
		Target.__init__(self, x, y, type)
		self.stats = stats

##################################
##
##################################

class TargetType(object):
	def __init__(self, name, color, shape='+', size=16, unique=False):
		self.name = name
		self.unique = unique
		self.shape = shape
		self.color = color
		self.size = size
		if shape != 'polygon' and shape !='spline' and shape != 'numbers':
			self.bitmaps = {}
			self.bitmaps['default'], self.bitmaps['selected'] = leginon.gui.wx.TargetPanelBitmaps.getTargetBitmaps(color, shape, size)
		self.targets = None

	#--------------------
	def getTargets(self):
		if self.targets is None:
			return None
		return list(self.targets)

	#--------------------
	def addTarget(self, x, y):
		target = Target(x, y, self)
		if self.unique:
			self.targets = [target]
		else:
			self.targets.append(target)

	#--------------------
	def insertTarget(self, pos, x, y):
		target = Target(x, y, self)
		if self.unique:
			self.targets = [target]
		else:
			self.targets.insert(pos, target)

	#--------------------
	def deleteTarget(self, target):
		try:
			self.targets.remove(target)
		except ValueError:
			pass

	#--------------------
	def setTargets(self, targets):
		if self.unique and len(targets) > 1:
			raise ValueError
		if targets is None:
			self.targets = []
			return
		self.targets = []
		for target in targets:
			if isinstance(target, dict):
				# targets from remote or manual selections do not have stats.
				if 'stats' not in target.keys():
					target['stats'] = None
				self.targets.append(StatsTarget(target['x'], target['y'], self, target['stats']))
			elif isinstance(target, Target):
				self.targets.append(Target(target.x, target.y, self))
			elif isinstance(target, list) or isinstance(target, numpy.ndarray) or isinstance(target, tuple):
				if len(target) < 2:
					print "bad target list: ",target
				else:
					self.targets.append(Target(target[0], target[1], self))
			else:
				print "unknown target type for ",self.name,": ",target,"type:",type(target)

	#--------------------
	def getTargetPositions(self):
		if self.targets is None:
			return []
		return map(lambda t: t.position, self.targets)

	#--------------------
	def changeCursorSize(self, newsize):
		self.size = newsize
		if self.shape != 'polygon' and self.shape != 'spline' and self.shape != 'numbers':
			self.bitmaps['default'], self.bitmaps['selected'] = leginon.gui.wx.TargetPanelBitmaps.getTargetBitmaps(self.color, self.shape, newsize)


