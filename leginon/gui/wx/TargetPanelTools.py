#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/TargetPanelTools.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-06 00:51:41 $
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
import gui.wx.ImagePanelTools
import gui.wx.TargetPanelBitmaps

TargetingEventType = wx.NewEventType()
EVT_TARGETING = wx.PyEventBinder(TargetingEventType)

##################################
##
##################################

class TargetingEvent(wx.PyCommandEvent):
	def __init__(self, source, name, value):
		wx.PyCommandEvent.__init__(self, TargetingEventType, source.GetId())
		self.SetEventObject(source)
		self.name = name
		self.value = value

##################################
##
##################################

class TargetTypeTool(gui.wx.ImagePanelTools.TypeTool):
	def __init__(self, parent, name, display=None, settings=None, target=None, shape='+', unique=False):
		self.color = display
		self.shape = shape 
		gui.wx.ImagePanelTools.TypeTool.__init__(self, parent, name, display=display, settings=settings)

		self.targettype = TargetType(self.name, self.color, self.shape, unique)

		self.togglebuttons['display'].SetBitmapDisabled(self.bitmaps['display'])

		if target is not None:
			togglebutton = self.addToggleButton('target', 'Add Targets')
			self.enableToggleButton('target', False)
			togglebutton.Bind(wx.EVT_BUTTON, self.onToggleTarget)

	#--------------------
	def getBitmaps(self):
		bitmaps = gui.wx.ImagePanelTools.TypeTool.getBitmaps(self)
		bitmaps['display'] = gui.wx.TargetPanelBitmaps.getTargetIconBitmap(self.color, self.shape)
		bitmaps['target'] = gui.wx.ImagePanelTools.getBitmap('arrow.png')
		return bitmaps

	#--------------------
	def onToggleTarget(self, evt):
		if not self.togglebuttons['target'].IsEnabled():
			self.togglebuttons['target'].SetValue(False)
			return
		evt = TargetingEvent(evt.GetEventObject(), self.name, evt.GetIsDown())
		self.togglebuttons['target'].GetEventHandler().AddPendingEvent(evt)

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
	def __init__(self, name, color, shape='+', unique=False):
		self.name = name
		self.unique = unique
		self.shape = shape
		self.color = color
		if shape != 'polygon' and shape != 'numbers':
			self.bitmaps = {}
			self.bitmaps['default'], self.bitmaps['selected'] = gui.wx.TargetPanelBitmaps.getTargetBitmaps(color, shape)
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
			else:
				self.targets.append(Target(target[0], target[1], self))

	#--------------------
	def getTargetPositions(self):
		if self.targets is None:
			return []
		return map(lambda t: t.position, self.targets)


