# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Calibrator.py,v $
# $Revision: 1.26 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-28 22:17:52 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import threading
import wx
from gui.wx.Choice import Choice
import gui.wx.Camera
import gui.wx.Events
import gui.wx.ImageViewer
import gui.wx.Node
import gui.wx.Settings
import gui.wx.ToolBar
import gui.wx.Instrument

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.instrumentselection = gui.wx.Instrument.SelectionPanel(self)
		self.GetParent().setInstrumentSelection(self.instrumentselection)

		self.widgets['use camera settings'] = wx.CheckBox(self, -1,
																								'Use camera configuration')
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)
		self.widgets['correlation type'] = Choice(self, -1,
																							choices=self.node.cortypes)

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.instrumentselection, (1, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['use camera settings'], (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (3, 0), (1, 1),
						wx.EXPAND)

		sb = wx.StaticBox(self, -1, 'Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class Panel(gui.wx.Node.Panel, gui.wx.Instrument.SelectionMixin):
	imageclass = gui.wx.ImageViewer.TargetImagePanel
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
		if isinstance(self.imagepanel, gui.wx.ImageViewer.TargetImagePanel):
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
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

