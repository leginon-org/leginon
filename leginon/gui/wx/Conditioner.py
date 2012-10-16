# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import IntEntry

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Test')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		self.node.onTest()

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
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Condition Fixer')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass Conditioner')
		sz = wx.GridBagSizer(2, 4)
		sz_time = wx.GridBagSizer(1, 4)
		sz.Add(self.widgets['bypass'], (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label1 = wx.StaticText(self, -1, 'Wait for at least')
		self.widgets['repeat time'] = IntEntry(self, -1, chars=6, min = 0)
		label2 = wx.StaticText(self, -1, 'seconds before fixing condition')
		sz_time.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz_time.Add(self.widgets['repeat time'], (0, 1), (1, 1), wx.EXPAND)
		sz_time.Add(label2, (0, 2), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(sz_time, (1, 0), (1, 2), wx.ALIGN_LEFT|wx.ALL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		

		return [sbsz]

