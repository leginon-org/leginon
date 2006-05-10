# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/RCTAcquisition.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2006-05-10 22:55:26 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import Entry, FloatEntry, EVT_ENTRY
from gui.wx.Presets import EditPresetOrder
import gui.wx.Acquisition
import gui.wx.Dialog
import gui.wx.Events
import gui.wx.Icons
import gui.wx.ImageViewer
import gui.wx.ToolBar
import gui.wx.FocusSequence

class Panel(gui.wx.Acquisition.Panel):
	icon = 'focuser'
	imagepanelclass = gui.wx.ImageViewer.TargetImagePanel
	def __init__(self, parent, name):
		gui.wx.Acquisition.Panel.__init__(self, parent, name)

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE, 'acquire', shortHelpString='Acquire')

		# correlation image
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255, 128, 0))
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool, id=gui.wx.ToolBar.ID_ACQUIRE)

		self.szmain.Layout()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAcquireTool(self, evt):
		threading.Thread(target=self.node.testAcquire).start()

class SettingsDialog(gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		sizers = gui.wx.Acquisition.SettingsDialog.initialize(self)

		sizer = wx.GridBagSizer(5, 5)

		print 'TILTS'
		label = wx.StaticText(self, -1, 'Tilts (deg)')
		sizer.Add(label, (0, 0), (1, 1))
		self.widgets['tilts'] = Entry(self, -1)
		sizer.Add(self.widgets['tilts'], (0,1), (1,1))

		print 'STEPSIZE'
		label = wx.StaticText(self, -1, 'Step Size (deg)')
		sizer.Add(label, (1, 0), (1, 1))
		self.widgets['stepsize'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['stepsize'], (1,1), (1,1))

		label = wx.StaticText(self, -1, 'Sigma')
		sizer.Add(label, (2, 0), (1, 1))
		self.widgets['sigma'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['sigma'], (2,1), (1,1))

		label = wx.StaticText(self, -1, 'Min Size')
		sizer.Add(label, (3, 0), (1, 1))
		self.widgets['minsize'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['minsize'], (3,1), (1,1))

		label = wx.StaticText(self, -1, 'Max Size')
		sizer.Add(label, (4, 0), (1, 1))
		self.widgets['maxsize'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['maxsize'], (4,1), (1,1))

		label = wx.StaticText(self, -1, 'Min Period')
		sizer.Add(label, (5, 0), (1, 1))
		self.widgets['minperiod'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['minperiod'], (5,1), (1,1))

		label = wx.StaticText(self, -1, 'Min Stable')
		sizer.Add(label, (6, 0), (1, 1))
		self.widgets['minstable'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['minstable'], (6,1), (1,1))

		sb = wx.StaticBox(self, -1, 'RCT Options')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return sizers + [sbsz]
