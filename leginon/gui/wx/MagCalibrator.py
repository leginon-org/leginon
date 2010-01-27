# -*- coding: iso-8859-1 -*-
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx

from leginon.gui.wx.Entry import IntEntry, FloatEntry, Entry
import leginon.gui.wx.Calibrator
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'dose'

	def onCalibrateTool(self, evt):
		self.dialog = MagCalibrationDialog(self)
		self.dialog.ShowModal()
		self.dialog.Destroy()
		self.dialog = None

class MagCalibrationDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
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

		lab = wx.StaticText(self, -1, 'mag1')
		self.widgets['mag1'] = IntEntry(self, -1)
		sz.Add(lab, (11,0), (1,1))
		sz.Add(self.widgets['mag1'], (11,1), (1,1))

		lab = wx.StaticText(self, -1, 'mag2')
		self.widgets['mag2'] = IntEntry(self, -1)
		sz.Add(lab, (12,0), (1,1))
		sz.Add(self.widgets['mag2'], (12,1), (1,1))

		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.onGo, self.gobut)
		self.Bind(wx.EVT_BUTTON, self.onTest, self.testbut)

		return [sbsz,]

	def onGo(self, evt):
		threading.Thread(target=self.node.uiStart).start()

	def onTest(self, evt):
		threading.Thread(target=self.node.uiTest).start()
