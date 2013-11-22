# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Conditioner
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import IntEntry,FloatEntry

class Panel(leginon.gui.wx.Conditioner.Panel):
	icon = 'targetfilter'
	def addTools(self):
		super(Panel,self).addTools()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		
	def onStopTool(self, evt):
		self.node.player.stop()
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool, id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		print 'this one'
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'AutoFiller')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Conditioner')
		sz = wx.GridBagSizer(7, 4)
		sz_time = wx.GridBagSizer(1, 4)
		sz.Add(self.widgets['bypass'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label1 = wx.StaticText(self, -1, 'Wait for at least')
		self.widgets['repeat time'] = IntEntry(self, -1, chars=6, min = 0)
		label2 = wx.StaticText(self, -1, 'seconds before fixing condition')
		sz_time.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_time.Add(self.widgets['repeat time'], (0, 1), (1, 1), wx.EXPAND)
		sz_time.Add(label2, (0, 2), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(sz_time, (1, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
	
		# column fill start
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

		# column fill end
		self.widgets['column fill end'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='80.0')
		szcolend = wx.GridBagSizer(5, 5)
		szcolend.Add(wx.StaticText(self, -1, 'Colomn Fill done when level is above'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szcolend.Add(self.widgets['column fill end'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szcolend.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# autoloader fill start
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

		# loader fill end
		self.widgets['loader fill end'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='80.0')
		szloaderend = wx.GridBagSizer(5, 5)
		szloaderend.Add(wx.StaticText(self, -1, 'Grid Loader Fill done when level is above'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szloaderend.Add(self.widgets['column fill end'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szloaderend.Add(wx.StaticText(self, -1, '%'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		sz.Add(szcolstart, (2, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		sz.Add(szcolend, (3, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		sz.Add(szloaderstart, (4, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		sz.Add(szloaderend, (5, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		

		return [sbsz]

