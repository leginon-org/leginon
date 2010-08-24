# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Node.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS, 'settings', shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelpString='Submit')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)

		self.toolbar.Realize()

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onPlayTool(self, evt):
		self.node.onContinue()

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
		sb = wx.StaticBox(self, -1, 'Target Repeater')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.BoxSizer(wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1, 'Bypass')
		sz.Add(self.widgets['bypass'])
		sz.AddSpacer((20,20))
		
		resetsb = wx.StaticBox(self, -1, 'When done....')
		resetsbsz = wx.StaticBoxSizer(resetsb, wx.VERTICAL)
		resetsz = wx.BoxSizer(wx.VERTICAL)
		self.widgets['reset a'] = wx.CheckBox(self, -1, 'Reset Alpha Tilt')
		resetsz.Add(self.widgets['reset a'])
		self.widgets['reset z'] = wx.CheckBox(self, -1, 'Reset Z')
		resetsz.Add(self.widgets['reset z'])
		self.widgets['reset xy'] = wx.CheckBox(self, -1, 'Reset X,Y')
		resetsz.Add(self.widgets['reset xy'])
		resetsbsz.Add(resetsz, wx.ALIGN_CENTER|wx.ALL)

		sz.Add(resetsbsz)

		sbsz.Add(sz, wx.ALIGN_CENTER|wx.ALL)

		return [sbsz]
