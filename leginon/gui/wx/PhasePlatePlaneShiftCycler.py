#!/usr/bin/env python

# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/Focuser.py,v $
# $Revision: 1.60 $
# $Name: not supported by cvs2svn $
# $Date: 2007-10-31 02:37:06 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import threading
import sys
import math
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry
import leginon.gui.wx.Acquisition
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)

	def onNodeInitialized(self):
		leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()
		self.node.resetCycle()

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sbsz = self.addCycleSettings()
		return sizers + [sbsz]

	def addCycleSettings(self):
		sb = wx.StaticBox(self, -1, 'LPP Plane Shift')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3
		self.widgets['use cycler'] = \
				wx.CheckBox(self, -1, 'Cycle through the sequence of shifts on LPP plane below')
		sizer.Add(self.widgets['use cycler'], (0,0), (1,4), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'List of Values to Collect')
		sizer.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['shifts on plane'] = Entry(self, -1, chars=15, style=wx.ALIGN_RIGHT)
		sizer.Add(self.widgets['shifts on plane'], (1,2), (1,2), wx.EXPAND|wx.ALL, bordersize)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sbsz

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Acquisition Test')
			dialog = SettingsDialog(frame, None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

