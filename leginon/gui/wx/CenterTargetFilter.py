# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx

import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetFilter
from leginon.gui.wx.Entry import IntEntry

class Panel(leginon.gui.wx.TargetFilter.Panel):
	icon = 'targetfilter'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.TargetFilter.Panel.__init__(self, *args, **kwargs)
		self.SettingsDialog = SettingsDialog
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)

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
		sb = wx.StaticBox(self, -1, 'Target Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		targettypes = ['acquisition','focus','preview']
		self.widgets['bypass'] = wx.CheckBox(self, -1,'Bypass Filter')
		self.widgets['target type'] = wx.Choice(self, -1, choices=targettypes)
		self.widgets['user check'] = wx.CheckBox(self, -1,'Verify filter before submitting')
		self.widgets['limit'] = IntEntry(self, -1, min=0, chars=6)

		sz = wx.GridBagSizer(5, 10)
		## filter
		sz.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Filtering Target Type')
		sz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['target type'], (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['user check'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		label = wx.StaticText(self, -1, 'Limit Targets to the center-most')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['limit'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]
