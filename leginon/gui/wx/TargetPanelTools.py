#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetPanelTools.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-08 19:39:01 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $
#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import wx
import sys
import numpy
import gui.wx.ImagePanelTools
import gui.wx.TargetPanelBitmaps
#import shortpath

TargetingEventType = wx.NewEventType()
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)

ShowNumbersEventType = wx.NewEventType()
EVT_SHOWNUMBERS = wx.PyEventBinder(ShowNumbersEventType)

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

##################################
##
##################################

class TargetTypeTool(gui.wx.ImagePanelTools.TypeTool):
	def __init__(self, parent, name, display=None, settings=None, target=None, shape='+', unique=False, numbers=None, size=16):
		self.color = display
		self.shape = shape 
		self.size = size 
		gui.wx.ImagePanelTools.TypeTool.__init__(self, parent, name, display=display, settings=settings)

		self.targettype = TargetType(self.name, self.color, self.shape, self.size, unique)
		self.numberstype = TargetType(self.name, self.color, 'numbers', self.size, unique)

		self.togglebuttons['display'].SetBitmapDisabled(self.bitmaps['display'])

		if target is not None:
			if numbers is not None:
				togglebutton = self.addToggleButton('numbers', 'Show Numbers')
				self.enableToggleButton('numbers', True)
				togglebutton.Bind(wx.EVT_BUTTON, self.onToggleNumbers)
				self.usenumbers = True

			togglebutton = self.addToggleButton('target', 'Add Targets')
			self.enableToggleButton('target', False)
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleTarget)

	#--------------------
	def getBitmaps(self):
		bitmaps = gui.wx.ImagePanelTools.TypeTool.getBitmaps(self)
		bitmaps['display'] = gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, self.shape)
		bitmaps['numbers'] = gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, 'numbers')
		bitmaps['target'] = gui.wx.ImagePanelTools.getBitmap('arrow.png')
		return bitmaps

	#--------------------
	def onToggleTarget(self, evt):
		if not self.togglebuttons['target'].IsEnabled():
			self.togglebuttons['target'].SetValue(False)
			return
		#if self.togglebuttons['target'].GetValue() is True:
		#	self.togglebuttons['target'].SetBackgroundColour(wx.Color(160,160,160))
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
		print "targets=",targets
		#convert to list of (x,y) tuples
		targetlist = [t.position for t in targets]
		bestorder, bestscore = shortpath.sortPoints(list(targetlist), numiter=3, maxeval=70000)
		print "bestorder=",bestorder
		sortedtargets = []
		for i in bestorder:
			sortedtargets.append(targets[i])
		print "sortedtargets=",sortedtargets
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
		if shape != 'polygon' and shape != 'numbers':
			self.bitmaps = {}
			self.bitmaps['default'], self.bitmaps['selected'] = gui.wx.TargetPanelBitmaps.getTargetBitmaps(color, shape, size)
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
		self.targets = []
		for target in targets:
			if isinstance(target, dict):
				self.targets.append(StatsTarget(target['x'], target['y'], self, target['stats']))
			elif isinstance(target, Target):
				self.targets.append(Target(target.x, target.y, self))
			elif isinstance(target, list) or isinstance(target, numpy.ndarray) or isinstance(target, tuple):
				if len(target) < 2:
					print "bad target list: ",target
				else:
					self.targets.append(Target(target[0], target[1], self))
			else:
				print "unknown target type: ",target,"type:",type(target)

	#--------------------
	def getTargetPositions(self):
		if self.targets is None:
			return []
		return map(lambda t: t.position, self.targets)

	#--------------------
	def changeCursorSize(self, size):
		self.size = size
		if self.shape != 'polygon' and self.shape != 'numbers':
			self.bitmaps['default'], self.bitmaps['selected'] = gui.wx.TargetPanelBitmaps.getTargetBitmaps(self.color, self.shape, size)


