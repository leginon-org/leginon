# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

from leginon.gui.wx.Entry import Entry, FloatEntry
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.Node
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Settings

import threading
import wx

class GridSelectionPanel(leginon.gui.wx.Node.Panel):
	#icon = 'robot'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY,
													'play', shortHelpString='Start')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelpString='Refresh Grid List')

		self.setDefaultGridSelection()
		self.createGridSelector((0,0))
		self.addNew()

		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def setDefaultGridSelection(self):
		self.default_gridlabel = None

	def addNew(self):
		'''
		placeholder for subclass new gui
		the sizer is added to self.szmain
		'''
		pass

	def enableNew(self,gridlabel):
		'''
		placeholder to enable subclass new gui to upon
		grid Choice selection
		'''
		pass

	def runNew(self):
		'''
		placeholder for subclass new gui to be run upon
		default grid Choice selection
		'''
		pass


	def createGridSelector(self,start_position):
		sb = wx.StaticBox(self, -1, 'EM Grid for Imaging')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.cgrid = wx.Choice(self, -1)
		self.cgrid.Enable(False)
		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Grids in the database')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.Add(self.cgrid, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szgrid.AddGrowableCol(1)
		sbsz.Add(szgrid, 0, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbsz, start_position, (1, 1), wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool, id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshGridsButton,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)

		self.Bind(wx.EVT_CHOICE, self.onGridChoice, self.cgrid)
		self.refreshGrids()

	def onGridChoice(self, evt=None):
		if evt is None:
			gridlabel = self.cgrid.GetStringSelection()
		else:
			gridlabel = evt.GetString()
		settings = self.node.getSettings()
		settings['grid name'] = gridlabel
		self.node.setSettings(settings)
		self.enableNew(gridlabel)

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
		if self.default_gridlabel and gridlabel == self.default_gridlabel:
			self.runNew()
		#self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.node.submitGrid()

	def onRefreshGridsButton(self, evt):
		self.refreshGrids

	def refreshGrids(self):
		choices = self.node.getGridNames()
		if self.default_gridlabel:
			choices.insert(0,self.default_gridlabel)
		self.setGridSelection(choices)		

	def onGridDone(self):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

class Panel(GridSelectionPanel):
	def setDefaultGridSelection(self):
		self.default_gridlabel = '--New Grid as Below--'

	def addNew(self):
		self.createNewGridEntry((1,0))

	def enableNew(self,gridlabel):
		# enable entry of new grid
		if gridlabel != self.default_gridlabel:
			self.newgrid.Enable(False)
		else:
			self.newgrid.Enable(True)

	def runNew(self):
		self.onSaveNewGrid(None)

	def createNewGridEntry(self,start_position):
		sb = wx.StaticBox(self, -1, 'New Grid')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		szgrid = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'New Grid Name:')
		szgrid.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.newgrid = Entry(self, -1)
		szgrid.Add(self.newgrid, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.savenewgrid = wx.Button(self, wx.ID_APPLY)

		szgrid.Add(self.savenewgrid, (2, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)

		szgrid.AddGrowableCol(1)
		sbsz.Add(szgrid, 0, wx.EXPAND|wx.ALL, 5)
		self.szmain.Add(sbsz, start_position, (1, 1), wx.EXPAND|wx.ALL|wx.ALIGN_CENTER_VERTICAL)
	
	def onNodeInitialized(self):
		super(Panel,self).onNodeInitialized()
		self.Bind(wx.EVT_BUTTON, self.onSaveNewGrid, self.savenewgrid)

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

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Grid Entry')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'No Settings')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

