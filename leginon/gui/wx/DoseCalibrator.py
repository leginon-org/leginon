# -*- coding: iso-8859-1 -*-
import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.Settings
import gui.wx.ToolBar

class Panel(gui.wx.Calibrator.Panel):
	icon = 'dose'
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)
		self.toolbar.Realize()
		self.toolbar.DeleteTool(gui.wx.ToolBar.ID_ABORT)

	def onCalibrateTool(self, evt):
		dialog = DoseCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class DoseCalibrationDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.bscreenup = wx.Button(self, -1, 'Up')
		self.bscreendown = wx.Button(self, -1, 'Down')

		szscreen = wx.GridBagSizer(5, 5)
		szscreen.Add(self.bscreenup, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szscreen.Add(self.bscreendown, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szscreen.AddGrowableCol(0)
		szscreen.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Main Screen')
		sbszscreen = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszscreen.Add(szscreen, 0, wx.EXPAND|wx.ALL, 5)

		self.stbeamcurrent = wx.StaticText(self, -1, '')
		self.stscreenmag = wx.StaticText(self, -1, '')
		self.stdoserate = wx.StaticText(self, -1, '')
		self.widgets['beam diameter'] = FloatEntry(self, -1, chars=6)
		self.widgets['scale factor'] = FloatEntry(self, -1, chars=6)
		self.bmeasuredose = wx.Button(self, -1, 'Measure Dose')

		sz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Beam current:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.stbeamcurrent, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'amps')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Screen magnification:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.stscreenmag, (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Dose rate:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.stdoserate, (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		#label = wx.StaticText(self, -1, 'e/m²/s')
		label = wx.StaticText(self, -1, 'e/m^2/s')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Beam diameter:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['beam diameter'], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'meters')
		sz.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Screen to beam current scale factor:')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['scale factor'], (4, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sz.Add(self.bmeasuredose, (5, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

		sz.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Dose Measurement')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)

		self.szdose = sz

		self.stsensitivity = wx.StaticText(self, -1, '')
		self.bcalibratesensitivity = wx.Button(self, -1, 'Calibrate')

		szcam = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Sensitivity:')
		szcam.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szcam.Add(self.stsensitivity, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'counts/e')
		szcam.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		szcam.Add(self.bcalibratesensitivity, (1, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)
		szcam.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Camera Sensitivity')
		sbszcam = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszcam.Add(szcam, 1, wx.EXPAND|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.onScreenUpButton, self.bscreenup)
		self.Bind(wx.EVT_BUTTON, self.onScreenDownButton, self.bscreendown)
		self.Bind(wx.EVT_BUTTON, self.onMeasureDoseButton, self.bmeasuredose)
		self.Bind(wx.EVT_BUTTON, self.onCalibrateSensitivityButton,
							self.bcalibratesensitivity)

		return [sbszscreen, sbsz, sbszcam]

	def onScreenUpButton(self, evt):
		self.node.screenUp()

	def onScreenDownButton(self, evt):
		self.node.screenDown()

	def _setDoseResults(self, results):
		try:
			self.stbeamcurrent.SetLabel(str(results['beam current']))
			self.stscreenmag.SetLabel(str(results['screen magnification']))
			self.stdoserate.SetLabel(str(results['dose rate']))
		except KeyError:
			self.stbeamcurrent.SetLabel('')
			self.stscreenmag.SetLabel('')
			self.stdoserate.SetLabel('')
		self.szmain.Layout()
		self.Fit()

	def onMeasureDoseButton(self, evt):
		self.node.uiMeasureDoseRate()
		self._setDoseResults(self.node.results)

	def _setSensitivityResults(self, results):
		if results is None:
			self.stsensitivity.SetLabel('')
		else:
			self.stsensitivity.SetLabel(str(results))
		self.szmain.Layout()
		self.Fit()

	def onCalibrateSensitivityButton(self, evt):
		self.node.uiCalibrateCamera()
		self._setSensitivityResults(self.node.sens)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Dose Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

