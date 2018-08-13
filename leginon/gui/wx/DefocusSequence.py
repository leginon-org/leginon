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
from leginon.gui.wx.Entry import FloatEntry, IntEntry
import leginon.gui.wx.Acquisition
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Acquisition.Panel):
	icon = 'acquisition'
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
		sbsz = self.addDefocusSequenceSettings()
		return sizers + [sbsz]

	def addDefocusSequenceSettings(self):
		sb = wx.StaticBox(self, -1, 'Defocus Squence')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3

		label = wx.StaticText(self, -1, 'Defocus Change per Step (m)')
		sizer.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['step size'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		sizer.Add(self.widgets['step size'], (1,2), (1,2), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)
		label = wx.StaticText(self, -1, 'Total numbers')
		sizer.Add(label, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['nsteps'] = IntEntry(self, -1, min= 1, chars=8, value='1')

		sizer.Add(self.widgets['nsteps'], (2,2), (1,2), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

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

