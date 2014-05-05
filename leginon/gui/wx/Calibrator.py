# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
import leginon.gui.wx.Camera
import leginon.gui.wx.Events
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Instrument

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		if self.show_basic:
			sz = self.addBasicSettings()
		else:
			sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addBasicSettings(self):
		self.widgets['override preset'] = wx.CheckBox(self, -1, 'Override Preset')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.widgets['override preset'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		return sz

	def addSettings(self):
		self.widgets['correlation type'] = Choice(self, -1, choices=self.node.cortypes)
		self.widgets['override preset'] = wx.CheckBox(self, -1, 'Override Preset')
		self.widgets['instruments'] = leginon.gui.wx.Instrument.SelectionPanel(self)
		self.panel.setInstrumentSelection(self.widgets['instruments'])
		self.widgets['camera settings'] = leginon.gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setGeometryLimits({'size':self.node.instrument.camerasize,'binnings':self.node.instrument.camerabinnings,'binmethod':self.node.instrument.camerabinmethod})

		szcor = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Use')
		szcor.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcor.Add(self.widgets['correlation type'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'correlation')
		szcor.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szlpf = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'phase correlation low pass filter')
		szlpf.Add(label, (0, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'sigma:')
		szlpf.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['phase corr lpf sigma'] = FloatEntry(self, -1,
																												min=0.0, chars=4)
		szlpf.Add(self.widgets['phase corr lpf sigma'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'pixels')
		szlpf.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szcor, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szlpf, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['override preset'], (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['instruments'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['camera settings'], (0, 1), (4, 1), wx.ALIGN_CENTER|wx.EXPAND)

		sz.AddGrowableRow(3)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		return sz

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	imageclass = leginon.gui.wx.TargetPanel.TargetImagePanel
	settingsdialogclass = SettingsDialog
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire Image')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CALIBRATE,
													'play',
													shortHelpString='Calibrate')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ABORT,
													'stop',
													shortHelpString='Abort')
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

		self.initialize()

		self.Bind(leginon.gui.wx.Events.EVT_CALIBRATION_DONE, self.onCalibrationDone)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		if isinstance(self.imagepanel, leginon.gui.wx.TargetPanel.TargetImagePanel):
			color = wx.Colour(255, 128, 0)
			self.imagepanel.addTargetTool('Peak', color)

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=leginon.gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalibrateTool,
											id=leginon.gui.wx.ToolBar.ID_CALIBRATE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAbortTool,
											id=leginon.gui.wx.ToolBar.ID_ABORT)

	def _acquisitionEnable(self, enable):
		self.toolbar.Enable(enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def _calibrationEnable(self, enable):
		self.toolbar.Enable(enable)

	def onCalibrationDone(self, evt):
		self._calibrationEnable(True)

	def calibrationDone(self):
		evt = leginon.gui.wx.Events.CalibrationDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.acquireImage).start()

	def onSettingsTool(self, evt):
		dialog = self.settingsdialogclass(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

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

