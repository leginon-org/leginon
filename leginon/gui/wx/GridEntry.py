# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Robot.py,v $
# $Revision: 1.16 $
# $Name: not supported by cvs2svn $
# $Date: 2007-06-15 02:30:31 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

from gui.wx.Entry import Entry, FloatEntry
import gui.wx.Events
import gui.wx.Icons
import gui.wx.Node
import gui.wx.ToolBar
import gui.wx.Settings
import threading
import wx
import unique

class Panel(gui.wx.Node.Panel):
	#icon = 'robot'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_PLAY,
													'play', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Grid List')
		self.toolbar.Realize()

		self.cgrid = wx.Choice(self, -1)
		self.cgrid.Enable(False)
		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Grids in the project')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgrid, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'New Grid Name:')
		szgrid.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.newgrid = Entry(self, -1)
		szgrid.Add(self.newgrid, (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.savenewgrid = wx.Button(self, wx.ID_APPLY)
		szgrid.Add(self.savenewgrid, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.szmain.Add(szgrid, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool, id=gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshGridsButton,
											id=gui.wx.ToolBar.ID_REFRESH)

		self.Bind(wx.EVT_CHOICE, self.onGridChoice, self.cgrid)
		self.Bind(wx.EVT_BUTTON, self.onSaveNewGrid, self.savenewgrid)
		self.refreshGrids()

	def onSaveNewGrid(self,evt=None):
		choices = self.node.getGridNames()
		newgrid = self.newgrid.Update()
		newgrid = self.newgrid.GetValue()
		if newgrid is None or newgrid == '':
			self.node.onBadEMGridName('No Grid Name')
			return
		elif newgrid in choices:
			self.node.onBadEMGridName('Grid Name Exists')
			return
		else:
			self.node.publishNewEMGrid(newgrid)
		self.refreshGrids()

	def onGridChoice(self, evt=None):
		if evt is None:
			gridlabel = self.cgrid.GetStringSelection()
		else:
			gridlabel = evt.GetString()
		settings = self.node.getSettings()
		settings['grid name'] = gridlabel
		self.node.setSettings(settings)
		if gridlabel != '--New Grid as Below--':
			self.newgrid.Enable(False)
		else:
			self.newgrid.Enable(True)

	def setGridSelection(self,choices):
		if choices:
			self.cgrid.Clear()
			self.cgrid.AppendItems(choices)
			if self.node.settings['grid name']:
				n = self.cgrid.FindString(self.node.settings['grid name'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.cgrid.SetSelection(0)
			else:
				self.cgrid.SetSelection(n)
			self.cgrid.Enable(True)
			self.onGridChoice()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onPlayTool(self, evt):
		gridlabel = self.cgrid.GetStringSelection()
		if gridlabel == '--New Grid as Below--':
			choices = self.node.getGridNames()
			newgrid = self.newgrid.Update()
			newgrid = self.newgrid.GetValue()
			if newgrid is None or newgrid == '':
				self.node.onBadEMGridName('No Grid Name')
				return
			elif newgrid in choices:
				self.node.onBadEMGridName('Grid Name Exists')
				return
			else:
				self.node.publishNewEMGrid(newgrid)
		self.refreshGrids()
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)
		self.node.submitGrid()

	def onRefreshGridsButton(self, evt):
		self.refreshGrids

	def refreshGrids(self):
		choices = self.node.getGridNames()
		choices.insert(0,'--New Grid as Below--')
		self.setGridSelection(choices)		

	def onGridDone(self):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, True)

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Grid Entry')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'No Settings')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

