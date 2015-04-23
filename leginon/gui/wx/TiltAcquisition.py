#!/usr/bin/env python

# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
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

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sbsz = self.addTiltSettings()
		return sizers + [sbsz]

	def addTiltSettings(self):
		sb = wx.StaticBox(self, -1, 'Tilting')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3
		self.widgets['use tilts'] = \
				wx.CheckBox(self, -1, 'Acquire each target at different tilt in the list')
		sizer.Add(self.widgets['use tilts'], (0,0), (1,4), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'List of Tilts to Collect (in degrees)')
		sizer.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['tilts'] = Entry(self, -1, chars=15, style=wx.ALIGN_RIGHT)
		sizer.Add(self.widgets['tilts'], (1,2), (1,2), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

		self.widgets['reset per targetlist'] = \
				wx.CheckBox(self, -1, 'Reset to the first of the tilts for targets from new image')
		sizer.Add(self.widgets['reset per targetlist'], (2,1), (1,3), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

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

