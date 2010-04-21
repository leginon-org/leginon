# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
from leginon.gui.wx.Presets import EditPresetOrder
from leginon.gui.wx.Presets import PresetChoice
import leginon.gui.wx.Acquisition
import leginon.gui.wx.Dialog
import leginon.gui.wx.Events
import leginon.gui.wx.Icons
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar
import leginon.gui.wx.FocusSequence

class Panel(leginon.gui.wx.Acquisition.Panel):
	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Stig Options')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3

		label = wx.StaticText(self, -1, 'Stig0 X')
		sizer.Add(label, (0,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stig0x'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['stig0x'], (0,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Stig0 Y')
		sizer.Add(label, (1,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stig0y'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['stig0y'], (1,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Stig1 X')
		sizer.Add(label, (2,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stig1x'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['stig1x'], (2,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Stig1 Y')
		sizer.Add(label, (3,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stig1y'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['stig1y'], (3,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Stig Count')
		sizer.Add(label, (4,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stigcount'] = IntEntry(self, -1, chars=6)
		sizer.Add(self.widgets['stigcount'], (4,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 2)

		return sizers + [sbsz]
