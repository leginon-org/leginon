# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.TargetFilter
from gui.wx.Entry import IntEntry

class Panel(gui.wx.TargetFilter.Panel):
	icon = 'targetfilter'
	def __init__(self, parent, name):
		gui.wx.TargetFilter.Panel.__init__(self, parent, -1)
		self.SettingsDialog = SettingsDialog
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PLAY, False)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Target Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['bypass'] = wx.CheckBox(self, -1,'Bypass Filter')
		self.widgets['limit'] = IntEntry(self, -1, min=0, chars=6)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Limit Targets to the center-most')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['limit'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]
