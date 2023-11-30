# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import sys
import wx

import leginon.gui.wx.Settings
from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.ToolBar

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sbsz = self.createShutterDelaySizer()
		return sizers + [sbsz]

	def createShutterDelaySizer(self):
		sb = wx.StaticBox(self, -1, 'Batch acquisition parallelization')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 5)
		self.widgets['shutter delay'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=6, value='0.0')
		sd_sizer = wx.GridBagSizer(5, 5)
		sd_sizer.Add(wx.StaticText(self, -1, 'add extra'), (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sd_sizer.Add(self.widgets['shutter delay'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sd_sizer.Add(wx.StaticText(self, -1, 'sec delay before next target move'), (0, 2), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(sd_sizer, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
		return sbsz

	def createMoverChoiceSizer(self):
		szmover = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Mover:')
		self.widgets['mover'] = Choice(self, -1, choices=['presets manager',])
		szmover.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmover.Add(self.widgets['mover'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		return szmover

	def createMovePrecisionSizer(self):
		szmoveprec = wx.GridBagSizer(5, 5)
		label0 = wx.StaticText(self, -1, '')
		szmoveprec.Add(label0, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label1 = wx.StaticText(self, -1, '')
		szmoveprec.Add(label1, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label2 = wx.StaticText(self, -1, '')
		szmoveprec.Add(label2, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return szmoveprec

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'acquisition'
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	settingsdialogclass = SettingsDialog

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			panel = Panel(frame)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()
