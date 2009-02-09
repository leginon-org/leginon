# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/StigAcquisition.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-12 20:37:54 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, FloatEntry, IntEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder
from gui.wx.Presets import PresetChoice
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.TargetPanel
import gui.wx.ToolBar
import gui.wx.FocusSequence

class Panel(gui.wx.Acquisition.Panel):
	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = gui.wx.Acquisition.ScrolledSettings.initialize(self)
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
