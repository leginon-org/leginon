#!/usr/bin/env python -O
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
		if n == 0:
			self.sz.AddGrowableCol(1)
		if 'display' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['display'], (n, 2), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['display'].Bind(leginon.gui.wx.ImagePanelTools.EVT_DISPLAY, self.onDisplay)
		if 'numbers' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['numbers'], (n, 3), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['numbers'].Bind(leginon.gui.wx.TargetPanelTools.EVT_SHOWNUMBERS, self.onNumber)
		else:
			#add spacer
			self.sz.Add((1,1), (n, 3), (1, 1), wx.ALIGN_CENTER)
		if 'area' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['area'], (n, 4), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['area'].Bind(leginon.gui.wx.TargetPanelTools.EVT_SHOWAREA, self.onImageArea)
			typetool.togglebuttons['area'].SetValue(True)
		elif 'exp' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['exp'], (n, 4), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['exp'].Bind(leginon.gui.wx.TargetPanelTools.EVT_SHOWEXPOSURE, self.onImageExposure)
			typetool.togglebuttons['exp'].SetValue(True)
		else:
			#add spacer
			self.sz.Add((1,1), (n, 4), (1, 1), wx.ALIGN_CENTER)
		if 'target' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['target'], (n, 5), (1, 1), wx.ALIGN_CENTER)
			typetool.togglebuttons['target'].Bind(leginon.gui.wx.TargetPanelTools.EVT_TARGETING, self.onTargeting)
		if 'settings' in typetool.togglebuttons:
			self.sz.Add(typetool.togglebuttons['settings'], (n, 6), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add((1,1), (n, 7), (1, 1), wx.ALIGN_CENTER)

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
	def isDisplayed(self, name, typename='display',default=True):
		tool = self._getTypeTool(name)
		try:
			return tool.togglebuttons[typename].GetValue()
		except KeyError:
			return default

	#--------------------
	def setDisplayed(self, name, value, typename='display'):
		tool = self._getTypeTool(name)
		if typename != 'display' and value == []:
			value = tool.togglebuttons[typename].GetValue()
		try:
			tool.togglebuttons[typename].SetValue(value)
		except KeyError:
			raise AttributeError
		self._setDisplayed(name, value, typename)

	#--------------------
	def _setDisplayed(self, name, value, typename='display'):
		tool = self._getTypeTool(name)
		if isinstance(tool, leginon.gui.wx.TargetPanelTools.TargetTypeTool):
			if value:
				targets = self.getTargets(name)
			else:
				targets = None
			if typename == 'display':
				typetool = tool.targettype
			else:
				if typename == 'area':
					typetool = tool.areatype
				elif typename == 'numbers':
					typetool = tool.numberstype
				elif typename == 'exp':
					typetool = tool.exptype
				typetool.setTargets(tool.targettype.getTargets())
			self.parent.setDisplayedTargets(typetool, targets)
			if not value and typename == 'display' and self.isTargeting(name):
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
	def setEnableSettings(self,name,value=True):
		tool = self._getTypeTool(name)
		tool.enableToggleButton('settings',value)

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
	def setDependantTypeTools(self, name, targets):
		for typename in ('numbers','area','exp'):
			if self.isDisplayed(name,typename,False):
				self.setDisplayed(name, targets, typename)

	#--------------------
	def addTarget(self, name, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.addTarget(x, y)
		targets = tool.targettype.getTargets()
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, targets)
		self.setDependantTypeTools(name, targets)

	#--------------------
	def insertTarget(self, name, pos, x, y):
		tool = self._getTypeTool(name)
		tool.targettype.insertTarget(pos, x, y)
		targets = tool.targettype.getTargets()
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, targets)
		self.setDependantTypeTools(name, targets)

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
		targets = tool.targettype.getTargets()
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, targets)
		self.setDependantTypeTools(name, targets)

	#--------------------
	def setTargets(self, name, targets):
		try:
			tool = self._getTypeTool(name)
		except ValueError:
			return
		tool.targettype.setTargets(targets)
		if self.isDisplayed(name):
			self.parent.setDisplayedTargets(tool.targettype, tool.targettype.targets)
		self.setDependantTypeTools(name, targets)
		if targets is None:
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

	#--------------------
	def onNumber(self, evt):
		self._setDisplayed(evt.name, evt.value, 'numbers')

	def onImageArea(self, evt):
		self._setDisplayed(evt.name, evt.value, 'area')

	def onImageExposure(self, evt):
		self._setDisplayed(evt.name, evt.value, 'exp')

