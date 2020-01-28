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
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry, TupleSequenceEntry
import leginon.gui.wx.Acquisition
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
		sbsz = self.addMoveSettings()
		return sizers + [sbsz]

	def addMoveSettings(self):
		sb = wx.StaticBox(self, -1, 'Tilting')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3

		acquire_during_move_sz = self.createAcquireDuringMoveSizer()
		tilt_and_move_time_sz = self.createTiltAndMoveTimeSizer()
		imaging_delay_sz = self.createImagingDelaySizer()

		sizer.Add(acquire_during_move_sz, (0,0), (1,4), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)
		sizer.Add(tilt_and_move_time_sz, (1,0), (1,4), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)
		sizer.Add(imaging_delay_sz, (3,0), (1,4), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)

		return sbsz

	def createAcquireDuringMoveSizer(self):
		self.widgets['acquire during move'] = \
				wx.CheckBox(self, -1, 'Acquire each target while moving')
		return self.widgets['acquire during move']

	def createTiltAndMoveTimeSizer(self):
		self.widgets['move to'] = TupleSequenceEntry(self, -1,
																		allownone=False,
																		chars=20,
																		value='10,40')
		self.widgets['total move time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=6,
																		value='0.0')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(wx.StaticText(self, -1, 'Tilt to'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['move to'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'degrees during'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['total move time'],
								(0, 3), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'seconds'),
								(0, 4), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		return sz

	def createImagingDelaySizer(self):
		self.widgets['imaging delay'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(wx.StaticText(self, -1, 'Delay camera exposure by'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['imaging delay'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(wx.StaticText(self, -1, 'seconds after moving starts'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		return sz

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

