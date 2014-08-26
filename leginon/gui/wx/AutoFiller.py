# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Conditioner
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Events
from leginon.gui.wx.Entry import IntEntry,FloatEntry

class Panel(leginon.gui.wx.Conditioner.Panel):
	icon = 'targetfilter'
	def addTools(self):
		super(Panel,self).addTools()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		
	def onStopTool(self, evt):
		self.node.player.stop()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool, id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)
		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		elif evt.state == 'stop':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Conditioner.ScrolledSettings):
	def getTitle(self):
		return 'N2 Autofiller'

	def addSettings(self):
		super(ScrolledSettings,self).addSettings()
		self.createAutofillerModeSelector((2,0))	
		self.createColumnFillStartEntry((3,0))
		self.createColumnFillEndEntry((4,0))
		self.createGridLoaderFillStartEntry((5,0))
		self.createGridLoaderFillEndEntry((6,0))

	def addBindings(self):
		super(ScrolledSettings,self).addBindings()
		self.Bind(wx.EVT_CHOICE, self.onAutofillerModeChoice, self.mode)
		choices = self.node.getFillerModes()
		self.setAutofillerModeSelection(choices)

	def createAutofillerModeSelector(self,start_position):	
		szmode = wx.GridBagSizer(5, 5)
		# plate format
		label = wx.StaticText(self, -1, 'Filler Mode:')
		szmode.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.mode = wx.Choice(self, -1)
		self.mode.Enable(False)
		szmode.Add(self.mode, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szmode, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)

	def createColumnFillStartEntry(self,start_position):
		self.widgets['column fill start'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='15.0')
		szcolstart = wx.GridBagSizer(5, 5)
		szcolstart.Add(wx.StaticText(self, -1, 'Colomn Fill when level is below'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szcolstart.Add(self.widgets['column fill start'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szcolstart.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szcolstart, start_position, (1, 2), wx.ALIGN_LEFT|wx.ALL)

	def createColumnFillEndEntry(self,start_position):
		self.widgets['column fill end'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='85.0')
		szcolstart = wx.GridBagSizer(5, 5)
		szcolstart.Add(wx.StaticText(self, -1, 'Colomn Fill done when level is above'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szcolstart.Add(self.widgets['column fill end'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szcolstart.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szcolstart, start_position, (1, 2), wx.ALIGN_LEFT|wx.ALL)

	def createGridLoaderFillStartEntry(self,start_position):
		self.widgets['loader fill start'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='15.0')
		szloaderstart = wx.GridBagSizer(5, 5)
		szloaderstart.Add(wx.StaticText(self, -1, 'Grid Loader Fill when level is below'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szloaderstart.Add(self.widgets['loader fill start'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szloaderstart.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(szloaderstart, start_position, (1, 2), wx.ALIGN_LEFT|wx.ALL)

	def createGridLoaderFillEndEntry(self,start_position):
		self.widgets['loader fill end'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='80.0')
		szloaderend = wx.GridBagSizer(5, 5)
		szloaderend.Add(wx.StaticText(self, -1, 'Grid Loader Fill done when level is above'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szloaderend.Add(self.widgets['loader fill end'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szloaderend.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(szloaderend, start_position, (1, 2), wx.ALIGN_LEFT|wx.ALL)
		
	def onAutofillerModeChoice(self, evt=None):
		if evt is None:
			modelabel = self.mode.GetStringSelection()
		else:
			modelabel = evt.GetString()
		settings = self.node.getSettings()
		settings['autofiller mode'] = modelabel
		self.node.setSettings(settings)
		self.mode.Enable(True)

	def setAutofillerModeSelection(self,choices):
		if choices:
			self.mode.Clear()
			self.mode.AppendItems(choices)
			if self.node.settings['autofiller mode']:
				n = self.mode.FindString(self.node.settings['autofiller mode'])
			else:
				n = wx.NOT_FOUND
			if n == wx.NOT_FOUND:
				self.mode.SetSelection(0)
			else:
				self.mode.SetSelection(n)
			self.mode.Enable(True)
			self.onAutofillerModeChoice()

