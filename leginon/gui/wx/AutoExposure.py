#!/usr/bin/env python

import wx
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Acquisition
from leginon.gui.wx.Entry import FloatEntry

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)

		sb = wx.StaticBox(self, label='Auto Exposure')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, label='Target Mean Intensity: ')
		self.widgets['mean intensity'] = FloatEntry(self, -1)
		sz.Add(label)
		sz.Add(self.widgets['mean intensity'])
		sbsz.Add(sz)

		sz = wx.BoxSizer(wx.HORIZONTAL)
		label1 = wx.StaticText(self, label='Tolerance: ')
		self.widgets['mean intensity tolerance'] = FloatEntry(self, -1)
		label2 = wx.StaticText(self, label='%')
		sz.Add(label1)
		sz.Add(self.widgets['mean intensity tolerance'])
		sz.Add(label2)
		sbsz.Add(sz)

		return sizers + [sbsz]

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'autoexposure'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

