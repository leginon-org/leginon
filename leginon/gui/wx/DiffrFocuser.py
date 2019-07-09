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

from pyami import fftfun

from leginon.gui.wx.Entry import FloatEntry, IntEntry, EVT_ENTRY
import leginon.gui.wx.Focuser

class Panel(leginon.gui.wx.Focuser.Panel):
	icon = 'focuser'
	imagepanelclass = leginon.gui.wx.TargetPanel.TargetImagePanel

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Focuser.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sbsz = self.addFocusSettings()
		sbsz1 = self.addDiffrTiltSettings()
		return sizers + [sbsz,sbsz1]

	def addDiffrTiltSettings(self):
		sb = wx.StaticBox(self, -1, 'Diffraction Tilting')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.szmain = wx.GridBagSizer(5, 5)

		newrow=0
		newrow,newcol = self.createTiltStartEntry((newrow,0))
		newrow,newcol = self.createTiltRangeEntry((newrow,0))
		newrow,newcol = self.createTiltSpeedEntry((newrow,0))

		sbsz.Add(self.szmain, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sbsz

	def createTiltStartEntry(self,start_position):
		self.widgets['tilt start'] = FloatEntry(self, -1, min=-75.0, max=75.0, allownone=False, chars=6, value='-58.0')
		tilt_sizer = wx.GridBagSizer(5, 5)
		tilt_sizer.Add(self.widgets['tilt start'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		tilt_sizer.Add(wx.StaticText(self, -1, 'degrees'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Start alpha angle:')
		#
		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(tilt_sizer, (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createTiltRangeEntry(self,start_position):
		self.widgets['tilt range'] = FloatEntry(self, -1, min=-140.0, max=140.0, allownone=False, chars=6, value='114.0')
		tilt_sizer = wx.GridBagSizer(5, 5)
		tilt_sizer.Add(self.widgets['tilt range'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		tilt_sizer.Add(wx.StaticText(self, -1, 'degrees'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Tilting range:')
		#
		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(tilt_sizer, (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createTiltSpeedEntry(self,start_position):
		self.widgets['tilt speed'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=6, value='10.0')
		tilt_sizer = wx.GridBagSizer(5, 5)
		tilt_sizer.Add(self.widgets['tilt speed'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		tilt_sizer.Add(wx.StaticText(self, -1, 'degs/s'), (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Tilt speed:')
		#
		total_length = (1,2)
		self.szmain.Add(label, start_position, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.Add(tilt_sizer, (start_position[0],start_position[1]+1), (1, 1), wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Focuser Test')
			dialog = leginon.gui.wx.ManualFocus.ManualFocusDialog(frame, None)
#			frame.Fit()
#			self.SetTopWindow(frame)
#			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

