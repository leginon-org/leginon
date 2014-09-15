# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import threading

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import IntEntry

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.addTools()
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addTools(self):
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Test')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		self.node.player.play()
		# onTest takes longer. Therefore start another thread
		t = threading.Thread(target=self.node.onTest)
		t.start()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool, id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return self._initializeScrolledSettings(False)

	def _initializeScrolledSettings(self,show_scrollbar=False):
		# This "private call" ensures that a sub class defined in a 
		# separate module loads its own function defined there
		# instead of the one in this module containing the parent class
		return ScrolledSettings(self,self.scrsize,show_scrollbar)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def getTitle(self):
		return 'Condition Fixer'

	def addSettings(self):
		self.createBypassCheckBox((0,0))
		self.createRepeatTimeEntry((1,0))

	def addBindings(self):
		self.Bind(wx.EVT_CHECKBOX, self.onBypassChange, self.widgets['bypass'])

	def createBypassCheckBox(self,start_position):
		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Conditioner')
		self.sz.Add(self.widgets['bypass'], start_position, (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)

	def createRepeatTimeEntry(self,start_position):
		sz_time = wx.GridBagSizer(1, 4)
		label1 = wx.StaticText(self, -1, 'Wait for at least')
		self.widgets['repeat time'] = IntEntry(self, -1, chars=6, min = 0)
		label2 = wx.StaticText(self, -1, 'seconds before fixing condition')
		sz_time.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_time.Add(self.widgets['repeat time'], (0, 1), (1, 1), wx.EXPAND)
		sz_time.Add(label2, (0, 2), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.sz.Add(sz_time, start_position, (1, 2), wx.ALIGN_LEFT|wx.ALL)

	def onBypassChange(self,event):
		settings = self.node.getSettings()
		settings['bypass'] = self.widgets['bypass'].IsChecked()
		self.node.setSettings(settings)
		self.node.makeConditioningRequests()
