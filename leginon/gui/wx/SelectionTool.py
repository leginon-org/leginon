#!/usr/bin/python -O
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/SelectionTool.py,v $
# $Revision: 1.4 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 21:35:30 $
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
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.TargetPanelTools

##################################
##
##################################

class SelectionTool(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent, -1, style=wx.SIMPLE_BORDER)
		self.SetBackgroundColour(wx.Colour(255, 255, 220))

		self.parent = parent

		self.sz = wx.GridBagSizer(3, 6)
		self.sz.AddGrowableCol(1)
		self.sz.SetEmptyCellSize((0, 24))

		self.order = []
		self.tools = {}
		self.images = {}
		self.targets = {}

		self.SetSizerAndFit(self.sz)

	#--------------------
	def _addTypeTool(self, typetool):
		n = len(self.tools)
		self.sz.Add(typetool.bitmap, (n, 0), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add(typetool.label, (n, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
		if 'display' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['display'], (n, 2), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['display'].Bind(leginon.gui.wx.ImagePanelTools.EVT_DISPLAY, self.onDisplay)
		if 'numbers' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['numbers'], (n, 3), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['numbers'].Bind(leginon.gui.wx.TargetPanelTools.EVT_SHOWNUMBERS, self.onNumber)
		else:
			#add spacer
			self.sz.Add((1,1), (n, 3), (1, 1), wx.ALIGN_CENTER)
		if 'target' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['target'], (n, 4), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['target'].Bind(leginon.gui.wx.TargetPanelTools.EVT_TARGETING, self.onTargeting)
		if 'settings' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['settings'], (n, 5), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add((1,1), (n, 6), (1, 1), wx.ALIGN_CENTER)

		if isinstance(typetool, leginon.gui.wx.TargetPanelTools.TargetTypeTool):
			self.targets[typetool.name] = None
		else:
			self.images[typetool.name] = None

	#--------------------
	def addTypeTool(self, name, toolclass=leginon.gui.wx.ImagePanelTools.TypeTool, **kwargs):
		if name in self.tools:
			raise ValueError('Type \'%s\' already exists' % name)
		typetool = toolclass(self, name, **kwargs)
		self._addTypeTool(typetool)
		self.order.append(name)
		self.tools[name] = typetool
		self.sz.Layout()
		self.Fit()

	#--------------------
	def hasType(self, name):
		if name in self.tools:
			return True
		else:
			return False

	#--------------------
	def _getTypeTool(self, name):
		try:
			return self.tools[name]
		except KeyError:
			raise ValueError('No type \'%s\' added' % name)

	#--------------------
	def isDisplayed(self, name):
		tool = self._getTypeTool(name)
		try:
			return tool.togglebuttons['display'].GetValue()
		except KeyError:
			return True

	#--------------------
	def setDisplayed(self, name, value):
		tool = self._getTypeTool(name)
		try:
			tool.togglebuttons['display'].SetValue(value)
		except KeyError:
			raise AttributeError
		self._setDisplayed(name, value)

	#--------------------
	def _setDisplayed(self, name, value):
		tool = self._getTypeTool(name)
		if isinstance(tool, leginon.gui.wx.TargetPanelTools.TargetTypeTool):
			if value:
				targets = self.getTargets(name)
			else:
				targets = None
			self.parent.setDisplayedTargets(tool.targettype, targets)
			if not value and self.isTargeting(name):
				self.setTargeting(name, False)
		else:
			for n in self.images:
				if n == name:
					continue
				tool = self._getTypeTool(n)
				try:
					tool.togglebuttons['display'].SetValue(False)
				except KeyError:
					pass
			if value:
				image = self.images[name]
				self.parent.setImage(image)
			else:
				self.parent.setImage(None)

	#--------------------
	def onDisplay(self, evt):
		self._setDisplayed(evt.name, evt.value)

	#--------------------
	def setImage(self, name, image):
		tool = self._getTypeTool(name)
		if image is None:
			tool.SetBitmap('red')
		else:
			tool.SetBitmap('green')
		self.images[name] = image
		if self.isDisplayed(name):
			self.parent.setImage(image)

	##########################################################
	##########################################################
	##########################################################

	#--------------------
	def getTargets(self, name):
		return self._getTypeTool(name).targettype.getTargets()

	#--------------------
	def addTarget(self, name, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.addTarget(x, y)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	#--------------------
	def insertTarget(self, name, pos, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.insertTarget(pos, x, y)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	#--------------------
	def clearAllTargetTypes(self):
		for name in self.tools:
			tool = self._getTypeTool(name)
			if hasattr(tool,'targettype'):
				self.setTargets(name,[])

	#--------------------
	def clearTargetType(self, targettype):
		name = targettype.name
		self.setTargets(name,[])

	#--------------------
	def deleteTarget(self, target):
		name = target.type.name
		tool = self._getTypeTool(name)
		tool.targettype.deleteTarget(target)
		if self.isDisplayed(name):
			# ...
			targets = tool.targettype.getTargets()
			self.parent.setDisplayedTargets(tool.targettype, targets)

	#--------------------
	def setTargets(self, name, targets):
		try:
			tool = self._getTypeTool(name)
		except ValueError:
			return
		tool.targettype.setTargets(targets)
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, tool.targettype.targets)
		if targets is None:
			#if self.isTargeting(name):
			#	self.setTargeting(name, False)
			if 'target' in tool.togglebuttons:
				tool.enableToggleButton('target', False)
			tool.SetBitmap('red')
		else:
			if 'target' in tool.togglebuttons:
				tool.enableToggleButton('target', True)
			tool.SetBitmap('green')
		if 'target' in tool.togglebuttons:
			tool.togglebuttons['target'].Refresh()

	#--------------------
	def changeCursorSize(self, name, size):
		try:
			tool = self._getTypeTool(name)
		except ValueError:
			return
		tool.targettype.changeCursorSize(size)
		if 'target' in tool.togglebuttons:
			tool.togglebuttons['target'].Refresh()

	#--------------------
	def getTargetPositions(self, name):
		return self._getTypeTool(name).targettype.getTargetPositions()

	#--------------------
	def isTargeting(self, name):
		tool = self._getTypeTool(name)
		try:
			return tool.togglebuttons['target'].GetValue()
		except KeyError:
			return False

	#--------------------
	def _setTargeting(self, name, value):
		tool = self._getTypeTool(name)

		if value and tool.targettype.getTargets() is None:
			raise ValueError('Cannot set targetting when targets is None')

		for n in self.targets:
			if n == name:
				continue
			t = self._getTypeTool(n)
			try:
				t.togglebuttons['target'].SetValue(False)
			except KeyError:
				pass

		if value and not self.isDisplayed(name):
			self.setDisplayed(name, True)

		if value:
			self.parent.selectedtype = tool.targettype
		else:
			self.parent.selectedtype = None

		if value:
			self.parent.UntoggleTools(None)

	#--------------------
	def onTargeting(self, evt):
		self._setTargeting(evt.name, evt.value)

	#--------------------
	def setTargeting(self, name, value):
		tool = self._getTypeTool(name)
		try:
			tool.togglebuttons['target'].SetValue(value)
		except KeyError:
			pass
		self._setTargeting(name, value)

	##########################################################
	##########################################################
	##########################################################

	#--------------------
	def isNumbered(self, name):
		tool = self._getTypeTool(name)
		try:
			return tool.togglebuttons['numbers'].GetValue()
		except KeyError:
			return True

	#--------------------
	def setNumbered(self, name, value):
		tool = self._getTypeTool(name)
		try:
			tool.togglebuttons['numbers'].SetValue(value)
		except KeyError:
			raise AttributeError
		self._setNumbered(name, value)

	#--------------------
	def _setNumbered(self, name, value):
		tool = self._getTypeTool(name)
		if isinstance(tool, leginon.gui.wx.TargetPanelTools.TargetTypeTool):
			if value:
				targets = self.getTargets(name)
			else:
				targets = None
			tool.numberstype.setTargets(tool.targettype.getTargets())
			self.parent.setDisplayedNumbers(tool.numberstype, targets)
		else:
			for n in self.images:
				if n == name:
					continue
				tool = self._getTypeTool(n)
				try:
					tool.togglebuttons['numbers'].SetValue(False)
				except KeyError:
					pass
			if value:
				image = self.images[name]
				self.parent.setImage(image)
			else:
				self.parent.setImage(None)

	#--------------------
	def onNumber(self, evt):
		self._setNumbered(evt.name, evt.value)


