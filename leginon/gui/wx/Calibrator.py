# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Calibrator.py,v $
# $Revision: 1.34 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-15 02:59:09 $
# $Author: acheng $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
import gui.wx.Camera
import gui.wx.Events
import gui.wx.TargetPanel
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Instrument

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		scr = ScrolledSettings(self,self.scrsize,False)
		return scr

class ScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['correlation type'] = Choice(self, -1, choices=self.node.cortypes)
		self.widgets['override preset'] = wx.CheckBox(self, -1, 'Override Preset')
		self.widgets['instruments'] = gui.wx.Instrument.SelectionPanel(self)
		self.panel.setInstrumentSelection(self.widgets['instruments'])
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['override preset'], (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['instruments'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (0, 1), (3, 1), wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT)

		sz.AddGrowableRow(2)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)

		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

		return [sbsz]

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	imageclass = gui.wx.TargetPanel.TargetImagePanel
	settingsclass = SettingsDialog
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)
		gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire Image')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_CALIBRATE,
													'play',
													shortHelpString='Calibrate')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ABORT,
													'stop',
													shortHelpString='Abort')
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

		self.initialize()

		self.toolbar.Realize()

		self.Bind(gui.wx.Events.EVT_CALIBRATION_DONE, self.onCalibrationDone)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		if isinstance(self.imagepanel, gui.wx.TargetPanel.TargetImagePanel):
			color = wx.Color(255, 128, 0)
			self.imagepanel.addTargetTool('Peak', color)

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

	def onNodeInitialized(self):
		gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.settingsdialog = self.settingsclass(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalibrateTool,
											id=gui.wx.ToolBar.ID_CALIBRATE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAbortTool,
											id=gui.wx.ToolBar.ID_ABORT)

	def _acquisitionEnable(self, enable):
		self.toolbar.Enable(enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def _calibrationEnable(self, enable):
		self.toolbar.Enable(enable)

	def onCalibrationDone(self, evt):
		self._calibrationEnable(True)

	def calibrationDone(self):
		evt = gui.wx.Events.CalibrationDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage).start()

	def onSettingsTool(self, evt):
		self.settingsdialog.ShowModal()

	def onCalibrateTool(self, evt):
		raise NotImplementedError

	def onAbortTool(self, evt):
		raise NotImplementedError

if __name__ == '__main__':
	class FakeInstrument(object):
		def __init__(self):
			self.camerasize = {'x': 1024, 'y': 1024}

	class FakeNode(object):
		def __init__(self):
			self.cortypes = ['foo', 'bar']
			self.instrument = FakeInstrument()

		def getSettings(self):
			return {}

	class FakePanel(wx.Panel):
		def __init__(self, *args, **kwargs):
			wx.Panel.__init__(self, *args, **kwargs)
			self.node = FakeNode()

		def setInstrumentSelection(self, widget):
			widget.setTEMs(['foo longer name', 'bar'])
			widget.setTEM('foo longer name')
			widget.setCCDCameras(['foo longer name', 'bar'])
			widget.setCCDCamera('bar')

	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Calibration Test')
			panel = FakePanel(frame, -1)
			dialog = SettingsDialog(panel, 'Test')
			self.SetTopWindow(frame)
			frame.Show()
			dialog.ShowModal()
			return True

	app = App(0)
	app.MainLoop()

