# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/RCTAcquisition.py,v $
# $Revision: 1.11 $
# $Name: not supported by cvs2svn $
# $Date: 2007-12-11 20:41:36 $
# $Author: vossman $
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
	icon = 'focuser'
	imagepanelclass = gui.wx.TargetPanel.TargetImagePanel
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
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		sizers = gui.wx.Acquisition.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'RCT Options')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		sizer = wx.GridBagSizer(5, 4)
		bordersize = 3

		label = wx.StaticText(self, -1, 'List of Tilts to Collect (in degrees)')
		sizer.Add(label, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['tilts'] = Entry(self, -1, chars=15, style=wx.ALIGN_RIGHT)
		sizer.Add(self.widgets['tilts'], (0,2), (1,2), wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Maximum Tilt Stepsize (in degrees)')
		sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['stepsize'] = IntEntry(self, -1, chars=2, value='15')
		sizer.Add(self.widgets['stepsize'], (1,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Pause Between Steps')
		sizer.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['pause'] = FloatEntry(self, -1, chars=2, value='1')
		sizer.Add(self.widgets['pause'], (1,3), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Min Feature Size')
		sizer.Add(label, (2,0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['minsize'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['minsize'], (2,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Max Feature Size')
		sizer.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['maxsize'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['maxsize'], (2,3), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Median Filter (pixels)')
		sizer.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['medfilt'] = IntEntry(self, -1, chars=2, value='0')
		sizer.Add(self.widgets['medfilt'], (3,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'LowPass Filter (pixels)')
		sizer.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['lowfilt'] = FloatEntry(self, -1, chars=2, value='0.0')
		sizer.Add(self.widgets['lowfilt'], (3,3), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Drift threshold')
		sizer.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['drift threshold'] = FloatEntry(self, -1, chars=6, value='0.0')
		sizer.Add(self.widgets['drift threshold'], (4,1), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		label = wx.StaticText(self, -1, 'Drift preset')
		sizer.Add(label, (4, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		presets = self.node.presetsclient.getPresetNames()
		self.widgets['drift preset'] = PresetChoice(self, -1)
		self.widgets['drift preset'].setChoices(presets)
		sizer.Add(self.widgets['drift preset'], (4,3), (1,1), wx.ALL|wx.ALIGN_CENTER_VERTICAL, bordersize)

		sbsz.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 2)

		return sizers + [sbsz]
