# -*- coding: iso-8859-1 -*-
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.ToolBar

class SettingsDialog(gui.wx.Calibrator.SettingsDialog):
	def initialize(self):
		szcal = gui.wx.Calibrator.SettingsDialog.initialize(self)

		self.widgets['measure axis'] = Choice(self, -1, choices=self.node.axes)
		self.widgets['measure points'] = IntEntry(self, -1, min=2, chars=5)
		self.widgets['measure tolerance'] = FloatEntry(self, -1, min=0.0, chars=5)
		self.widgets['measure interval'] = FloatEntry(self, -1, chars=9)

		self.widgets['model axis'] = Choice(self, -1, choices=self.node.axes)
		self.widgets['model magnification'] = FloatEntry(self, -1, chars=9)
		self.widgets['model terms'] = IntEntry(self, -1, chars=2)
		self.widgets['model mag only'] = wx.CheckBox(self, -1,
																									'Model magnification only')

		szmeasure = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Axis:')
		szmeasure.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure axis'], (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Points:')
		szmeasure.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure points'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Tolerance:')
		szmeasure.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure tolerance'], (2, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of pixel size')
		szmeasure.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Interval')
		szmeasure.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure interval'], (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		szmeasure.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Measurement')
		sbszmeasure = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszmeasure.Add(szmeasure, 1, wx.EXPAND|wx.ALL, 5)

		szmodel = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Axis:')
		szmodel.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model axis'], (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Magnification:')
		szmodel.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model magnification'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Terms:')
		szmodel.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model terms'], (2, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		szmodel.Add(self.widgets['model mag only'], (3, 0), (1, 2), wx.ALIGN_CENTER)
		szmodel.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Modeling')
		sbszmodel = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszmodel.Add(szmodel, 1, wx.EXPAND|wx.ALL, 5)

		return szcal + [sbszmeasure, sbszmodel]

class Panel(gui.wx.Calibrator.Panel):
	settingsclass = SettingsDialog
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)
		self.toolbar.Realize()
		ctb = self.toolbar.RemoveTool(gui.wx.ToolBar.ID_CALIBRATE)
		atb = self.toolbar.RemoveTool(gui.wx.ToolBar.ID_ABORT)
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE,
													'ruler',
													shortHelpString='Measure')
		self.toolbar.AddSeparator()
		self.toolbar.AddToolItem(atb)
		self.toolbar.AddToolItem(ctb)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool,
											id=gui.wx.ToolBar.ID_MEASURE)

	def onMeasureTool(self, evt):
		self.node.uiStartLoop()

	def onAbortTool(self, evt):
		self.node.uiStopLoop()

	def onCalibrateTool(self, evt):
		self.node.uiFit()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'GonModeler Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

