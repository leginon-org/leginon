import threading
import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Calibrator.Panel):
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)

		self.toolbar.InsertSeparator(2)
		self.cparameter = wx.Choice(self.toolbar, -1,
																choices=['Defocus', 'Stigmators'])
		self.cparameter.SetSelection(0)
		self.toolbar.InsertControl(3, self.cparameter)
		self.toolbar.InsertTool(4, gui.wx.ToolBar.ID_PARAMETER_SETTINGS,
													'settings',
													shortHelpString='Parameter Settings')

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE,
													'ruler',
													shortHelpString='Measure')

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GET_INSTRUMENT,
													'instrumentget',
													shortHelpString='Eucentric Focus From Scope')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SET_INSTRUMENT,
													'instrumentset',
													shortHelpString='Eucentric Focus To Scope')

		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

		self.Bind(gui.wx.Events.EVT_GET_INSTRUMENT_DONE, self.onGetInstrumentDone)
		self.Bind(gui.wx.Events.EVT_SET_INSTRUMENT_DONE, self.onSetInstrumentDone)
		self.Bind(gui.wx.Events.EVT_MEASUREMENT_DONE, self.onMeasurementDone)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)

		self.measuredialog = MeasureDialog(self)

		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool,
											id=gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool,
											id=gui.wx.ToolBar.ID_MEASURE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucFromScope,
											id=gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucToScope,
											id=gui.wx.ToolBar.ID_SET_INSTRUMENT)

	def _instrumentEnable(self, enable):
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ACQUIRE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_CALIBRATE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_MEASURE, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_GET_INSTRUMENT, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SET_INSTRUMENT, enable)
		self.measuredialog.bmeasure.Enable(enable)
		if self.node.resultvalue:
			self.measuredialog.bcorrectdefocus.Enable(enable)
			self.measuredialog.bcorrectstig.Enable(enable)
		self.measuredialog.bresetdefocus.Enable(enable)

	def _acquisitionEnable(self, enable):
		self._instrumentEnable(enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, enable)

	def _calibrationEnable(self, enable):
		self._acquisitionEnable(enable)
		self.cparameter.Enable(enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PARAMETER_SETTINGS, enable)
		# not implemented
		#self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, not enable)

	def onGetInstrumentDone(self, evt):
		self._instrumentEnable(True)

	def onSetInstrumentDone(self, evt):
		self._instrumentEnable(True)

	def onMeasurementDone(self, evt):
		self._calibrationEnable(True)
		result = self.node.resultvalue
		for key, value in self.measuredialog.sts.items():
			try:
				value.SetLabel(str(result[key]))
			except:
				value.SetLabel('Not measured')
		self.measuredialog.szmain.Layout()
		self.measuredialog.Fit()

	def measurementDone(self):
		evt = gui.wx.Events.MeasurementDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onEucToScope(self, evt):
		self._instrumentEnable(False)
		threading.Thread(target=self.node.eucToScope).start()

	def onEucFromScope(self, evt):
		self._instrumentEnable(False)
		threading.Thread(target=self.node.eucFromScope).start()

	def onMeasureTool(self, evt):
		self.measuredialog.ShowModal()

	def onParameterSettingsTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		if parameter == 'Defocus':
			dialog = DefocusSettingsDialog(self)
		elif parameter == 'Stigmators':
			dialog = StigmatorsSettingsDialog(self)
		else:
			raise RuntimeError
		dialog.ShowModal()
		dialog.Destroy()

	def onCalibrateTool(self, evt):
		self._calibrationEnable(False)
		parameter = self.cparameter.GetStringSelection()
		if parameter == 'Defocus':
			threading.Thread(target=self.node.uiCalibrateDefocus).start()
		elif parameter == 'Stigmators':
			threading.Thread(target=self.node.uiCalibrateStigmators).start()
		else:
			raise RuntimeError

	def onAbortTool(self, evt):
		self.node.abortCalibration()

class DefocusSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['defocus beam tilt'] = FloatEntry(self, -1, chars=9)
		self.widgets['first defocus'] = FloatEntry(self, -1, chars=9)
		self.widgets['second defocus'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Beam tilt:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['defocus beam tilt'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'First defocus:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['first defocus'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Second defocus:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['second defocus'], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		self.sb = wx.StaticBox(self, -1, 'Defocus Calibration')
		sbsz = wx.StaticBoxSizer(self.sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class StigmatorsSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['stig beam tilt'] = FloatEntry(self, -1, chars=9)
		self.widgets['stig delta'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Beam tilt:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig beam tilt'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Delta stig:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig delta'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		self.sb = wx.StaticBox(self, -1, 'Stigmator Calibration')
		sbsz = wx.StaticBoxSizer(self.sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class MeasureDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Measure')

		self.febeamtilt = FloatEntry(self, -1, chars=9)
		self.febeamtilt.SetValue(self.node.defaultmeasurebeamtilt)

		self.sts = {}
		self.sts['defocus'] = wx.StaticText(self, -1, 'Not measured')
		self.sts['stigx'] = wx.StaticText(self, -1, 'Not measured')
		self.sts['stigy'] = wx.StaticText(self, -1, 'Not measured')

		szresult = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Defocus:')
		szresult.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.sts['defocus'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stigmator x:')
		szresult.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.sts['stigx'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stigmator y:')
		szresult.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.sts['stigy'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.bmeasure = wx.Button(self, -1, 'Measure')
		self.bcorrectdefocus = wx.Button(self, -1, 'Correct Defocus')
		self.bcorrectstig = wx.Button(self, -1, 'Correct Stigmator')
		self.bresetdefocus = wx.Button(self, -1, 'Reset Defocus')
		self.bcorrectdefocus.Enable(False)
		self.bcorrectstig.Enable(False)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bmeasure, (0, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.bcorrectdefocus, (1, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.bcorrectstig, (2, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.bresetdefocus, (3, 0), (1, 1), wx.EXPAND)

		sz = wx.GridBagSizer(5, 20)
		label = wx.StaticText(self, -1, 'Beam tilt:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.febeamtilt, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(szresult, (1, 0), (1, 2), wx.ALIGN_CENTER)
		sz.Add(szbutton, (0, 2), (2, 1), wx.ALIGN_CENTER)

		self.sb = wx.StaticBox(self, -1, 'Measure')
		sbsz = wx.StaticBoxSizer(self.sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.bdone = wx.Button(self, wx.ID_OK, 'Close')

		self.szmain = wx.GridBagSizer(5, 5)
		self.szmain.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.szmain.Add(self.bdone, (1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.szmain)

		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.bmeasure)
		self.Bind(wx.EVT_BUTTON, self.onCorrectDefocusButton, self.bcorrectdefocus)
		self.Bind(wx.EVT_BUTTON, self.onCorrectStigButton, self.bcorrectstig)
		self.Bind(wx.EVT_BUTTON, self.onResetDefocusButton, self.bresetdefocus)

	def onMeasureButton(self, evt):
		self.GetParent()._calibrationEnable(False)
		threading.Thread(target=self.node.uiMeasureDefocusStig,
											args=(self.febeamtilt.GetValue(),)).start()

	def onCorrectDefocusButton(self, evt):
		self.GetParent()._instrumentEnable(False)
		threading.Thread(target=self.node.uiCorrectDefocus).start()

	def onCorrectStigButton(self, evt):
		self.GetParent()._instrumentEnable(False)
		threading.Thread(target=self.node.uiCorrectStigmator).start()

	def onResetDefocusButton(self, evt):
		self.GetParent()._instrumentEnable(False)
		threading.Thread(target=self.node.uiResetDefocus).start()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Beam Tilt Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

