# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/DriftManager.py,v $
# $Revision: 1.26 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-08 01:10:03 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import FloatEntry, IntEntry
import gui.wx.Camera
import gui.wx.TargetPanel
import gui.wx.Node
import gui.wx.Settings
import gui.wx.Instrument

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	icon = 'driftmanager'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		gui.wx.Instrument.SelectionMixin.__init__(self)

		# settings
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE_DRIFT,
													'ruler',
													shortHelpString='Measure Drift')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_DECLARE_DRIFT,
													'declare',
													shortHelpString='Declare Drift')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_CHECK_DRIFT,
													'play',
													shortHelpString='Check Drift')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ABORT_DRIFT,
													'stop',
													shortHelpString='Abort Drift Check')
		self.toolbar.Realize()

		# image
		self.imagepanel = gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Color(255,0,0))

		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCheckDriftTool,
											id=gui.wx.ToolBar.ID_CHECK_DRIFT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAbortDriftTool,
											id=gui.wx.ToolBar.ID_ABORT_DRIFT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureDriftTool,
											id=gui.wx.ToolBar.ID_MEASURE_DRIFT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onDeclareDriftTool,
											id=gui.wx.ToolBar.ID_DECLARE_DRIFT)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onCheckDriftTool(self, evt):
		self.node.uiMonitorDrift()

	def onAbortDriftTool(self, evt):
		self.node.abort()

	def onMeasureDriftTool(self, evt):
		self.node.uiMeasureDrift()

	def onDeclareDriftTool(self, evt):
		self.node.uiDeclareDrift()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Transform Management')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['threshold'] = FloatEntry(self, -1, min=0.0, chars=9)
		self.widgets['pause time'] = FloatEntry(self, -1, min=0.0, chars=4)
		self.widgets['min mag'] = IntEntry(self, -1, min=1, chars=9)
		self.instrumentselection = gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.panel.setInstrumentSelection(self.instrumentselection)
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)

		szthreshold = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait for drift to be less than')
		szthreshold.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szthreshold.Add(self.widgets['threshold'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'meters')
		szthreshold.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szpause = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Wait at least')
		szpause.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szpause.Add(self.widgets['pause time'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds between images')
		szpause.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szminmag = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Minimum Magnification')
		szminmag.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szminmag.Add(self.widgets['min mag'], (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(szthreshold, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szpause, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szminmag, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.instrumentselection, (3, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['camera settings'], (4, 0), (1, 1), wx.EXPAND)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Drift Manager Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

