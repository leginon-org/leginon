# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import wx
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.TargetFilter
from gui.wx.Entry import IntEntry, FloatEntry
from gui.wx.Presets import PresetChoice
from gui.wx.Choice import Choice

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

		sz = wx.GridBagSizer(5, 10)

		self.widgets['bypass'] = wx.CheckBox(self, -1,'Bypass Filter')
		targettypes = ['acquisition','preview']
		self.widgets['target type'] = wx.Choice(self, -1, choices=targettypes)

		self.widgets['raster spacing'] = FloatEntry(self, -1, min=0, chars=6)
		self.widgets['raster angle'] = FloatEntry(self, -1, chars=8)
		self.widgets['raster width'] = FloatEntry(self, -1, min=0, chars=6)

		movetypes = self.node.calclients.keys()
		self.widgets['raster movetype'] = Choice(self, -1, choices=movetypes)
		## auto raster
		self.autobut = wx.Button(self, -1, 'Calculate spacing and angle using the following parameters:')
		self.Bind(wx.EVT_BUTTON, self.onAutoButton, self.autobut)
		self.widgets['raster preset'] = PresetChoice(self, -1)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['raster preset'].setChoices(presets)
		self.widgets['raster overlap'] = FloatEntry(self, -1, chars=8)

		sztype = wx.GridBagSizer(0,5)
		sztype.Add(self.widgets['bypass'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Convoluting Target Type')
		sztype.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztype.Add(self.widgets['target type'], (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztype.AddGrowableCol(0)
		sz.Add(sztype, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sz.Add(self.autobut, (1, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Raster Preset')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster preset'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Overlap percent')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster overlap'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Move Type')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster movetype'], (4, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Spacing')
		sz.Add(label, (5, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster spacing'], (5, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Angle')
		sz.Add(label, (6, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster angle'], (6, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Width')
		sz.Add(label, (7, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['raster width'], (7, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sb = wx.StaticBox(self, -1, 'Target Filter')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

	def onAutoButton(self, evt):
		self.setNodeSettings()
		s,a = self.node.autoSpacingAngle()
		self.widgets['raster spacing'].SetValue(s)
		self.widgets['raster angle'].SetValue(a)
