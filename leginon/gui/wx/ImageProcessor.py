# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx

from leginon.gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.ImagePanel

class Panel(leginon.gui.wx.Node.Panel):
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	icon = 'fftmaker'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.Realize()

		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)

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
		sb = wx.StaticBox(self, -1, 'Image Processor')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['process'] = wx.CheckBox(self, -1,
																			'Process images when event received')

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['process'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

