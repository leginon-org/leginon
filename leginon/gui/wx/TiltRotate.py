# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetRepeater
from leginon.gui.wx.Entry import Entry

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Submit')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT, 'stop', shortHelpString='Abort')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onPlayTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		self.node.onContinue()

	def onStopTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
		self.node.player.stop()

	def onNodeInitialized(self):
		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool, id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStopTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		if evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
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

class ScrolledSettings(leginon.gui.wx.TargetRepeater.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.TargetRepeater.ScrolledSettings.initialize(self)

		sb = wx.StaticBox(self, -1, 'Tilts')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['tilts'] = Entry(self, -1, chars=15, style=wx.ALIGN_RIGHT)
		sbsz.Add(self.widgets['tilts'], wx.EXPAND)

		return sizers + [sbsz]

