# -*- coding: iso-8859-1 -*-
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/MagCalibrator.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2008-01-16 21:01:34 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Entry import IntEntry, FloatEntry, Entry
import gui.wx.Calibrator
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Calibrator.Panel):
	icon = 'dose'

	def onCalibrateTool(self, evt):
		self.dialog = MagCalibrationDialog(self)
		self.dialog.ShowModal()
		self.dialog.Destroy()
		self.dialog = None

class MagCalibrationDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Stuff')
		sbsz= wx.StaticBoxSizer(sb, wx.VERTICAL)

		sz = wx.GridBagSizer(5, 5)

		self.gobut = wx.Button(self, -1, 'Go')
		sz.Add(self.gobut, (0, 0), (1, 1), wx.ALIGN_CENTER)

		self.testbut = wx.Button(self, -1, 'Test')
		sz.Add(self.testbut, (0, 1), (1, 1), wx.ALIGN_CENTER)

		lab = wx.StaticText(self, -1, 'minsize')
		self.widgets['minsize'] = FloatEntry(self, -1)
		sz.Add(lab, (1,0), (1,1))
		sz.Add(self.widgets['minsize'], (1,1), (1,1))

		lab = wx.StaticText(self, -1, 'maxsize')
		self.widgets['maxsize'] = FloatEntry(self, -1)
		sz.Add(lab, (2,0), (1,1))
		sz.Add(self.widgets['maxsize'], (2,1), (1,1))

		lab = wx.StaticText(self, -1, 'pause')
		self.widgets['pause'] = FloatEntry(self, -1)
		sz.Add(lab, (3,0), (1,1))
		sz.Add(self.widgets['pause'], (3,1), (1,1))

		lab = wx.StaticText(self, -1, 'label')
		self.widgets['label'] = Entry(self, -1)
		sz.Add(lab, (4,0), (1,1))
		sz.Add(self.widgets['label'], (4,1), (1,1))

		lab = wx.StaticText(self, -1, 'threshold')
		self.widgets['threshold'] = FloatEntry(self, -1)
		sz.Add(lab, (5,0), (1,1))
		sz.Add(self.widgets['threshold'], (5,1), (1,1))

		lab = wx.StaticText(self, -1, 'maxcount')
		self.widgets['maxcount'] = IntEntry(self, -1)
		sz.Add(lab, (6,0), (1,1))
		sz.Add(self.widgets['maxcount'], (6,1), (1,1))

		lab = wx.StaticText(self, -1, 'minbright')
		self.widgets['minbright'] = FloatEntry(self, -1)
		sz.Add(lab, (7,0), (1,1))
		sz.Add(self.widgets['minbright'], (7,1), (1,1))

		lab = wx.StaticText(self, -1, 'maxbright')
		self.widgets['maxbright'] = FloatEntry(self, -1)
		sz.Add(lab, (8,0), (1,1))
		sz.Add(self.widgets['maxbright'], (8,1), (1,1))

		lab = wx.StaticText(self, -1, 'cutoffpercent')
		self.widgets['cutoffpercent'] = FloatEntry(self, -1)
		sz.Add(lab, (9,0), (1,1))
		sz.Add(self.widgets['cutoffpercent'], (9,1), (1,1))

		lab = wx.StaticText(self, -1, 'magsteps')
		self.widgets['magsteps'] = IntEntry(self, -1)
		sz.Add(lab, (10,0), (1,1))
		sz.Add(self.widgets['magsteps'], (10,1), (1,1))

		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.onGo, self.gobut)
		self.Bind(wx.EVT_BUTTON, self.onTest, self.testbut)

		return [sbsz,]

	def onGo(self, evt):
		threading.Thread(target=self.node.uiStart).start()

	def onTest(self, evt):
		threading.Thread(target=self.node.uiTest).start()
