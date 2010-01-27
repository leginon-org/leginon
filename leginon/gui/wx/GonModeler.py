# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import Entry, IntEntry, FloatEntry
import leginon.gui.wx.Calibrator
import leginon.gui.wx.ToolBar

class SettingsDialog(leginon.gui.wx.Calibrator.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Calibrator.ScrolledSettings):
	def initialize(self):
		szcal = leginon.gui.wx.Calibrator.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Measurement')
		sbszmeasure = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Modeling')
		sbszmodel = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['measure axis'] = Choice(self, -1, choices=self.node.axes)
		self.widgets['measure points'] = IntEntry(self, -1, min=2, chars=5)
		self.widgets['measure tolerance'] = FloatEntry(self, -1, min=0.0, chars=5)
		self.widgets['measure interval'] = FloatEntry(self, -1, chars=9)
		self.widgets['measure label'] = Entry(self, -1, chars=12)
		self.widgets['model label'] = Entry(self, -1, chars=12)

		self.widgets['model axis'] = Choice(self, -1, choices=self.node.axes)
		self.widgets['model magnification'] = FloatEntry(self, -1, chars=9)
		self.widgets['model terms'] = IntEntry(self, -1, chars=2)
		self.widgets['model mag only'] = wx.CheckBox(self, -1,
																									'Scale and Rotation Adjustment Only')

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
		label = wx.StaticText(self, -1, '%')
		szmeasure.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Interval')
		szmeasure.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure interval'], (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Label')
		szmeasure.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmeasure.Add(self.widgets['measure label'], (4, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		szmeasure.AddGrowableCol(1)

		sbszmeasure.Add(szmeasure, 1, wx.EXPAND|wx.ALL, 5)

		szmodel = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Label:')
		szmodel.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model label'], (0, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Axis:')
		szmodel.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model axis'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Magnification:')
		szmodel.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model magnification'], (2, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Terms:')
		szmodel.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szmodel.Add(self.widgets['model terms'], (3, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		szmodel.Add(self.widgets['model mag only'], (4, 0), (1, 2), wx.ALIGN_CENTER)
		szmodel.AddGrowableCol(1)

		sbszmodel.Add(szmodel, 1, wx.EXPAND|wx.ALL, 5)

		return szcal + [sbszmeasure, sbszmodel]

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'sine'
	settingsclass = SettingsDialog
	def initialize(self):
		leginon.gui.wx.Calibrator.Panel.initialize(self)
		self.toolbar.Realize()
		ctb = self.toolbar.RemoveTool(leginon.gui.wx.ToolBar.ID_CALIBRATE)
		atb = self.toolbar.RemoveTool(leginon.gui.wx.ToolBar.ID_ABORT)
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE,
													'cam_ruler',
													shortHelpString='Measure')
		self.toolbar.AddToolItem(atb)
		self.toolbar.AddSeparator()
		self.toolbar.AddToolItem(ctb)

		self.Bind(leginon.gui.wx.Events.EVT_MEASUREMENT_DONE, self.onMeasurementDone)

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool,
											id=leginon.gui.wx.ToolBar.ID_MEASURE)
		self.node.settings['measure label'] =  self.node.session['name']
		self.node.setSettings(self.node.settings)

	def onMeasurementDone(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_MEASURE, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

	def measurementDone(self):
		evt = leginon.gui.wx.Events.MeasurementDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def onMeasureTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, True)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_MEASURE, False)
		threading.Thread(target=self.node.uiStartLoop).start()

	def onAbortTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		threading.Thread(target=self.node.uiStopLoop).start()

	def onCalibrateTool(self, evt):
		threading.Thread(target=self.node.uiFit).start()

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

