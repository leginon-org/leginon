# -*- coding: iso-8859-1 -*-
import wx
from gui.wx.Choice import Choice
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator

class Panel(gui.wx.Calibrator.Panel):
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)
		self.bcalibrate.SetLabel('Measure')

		self.bmodel = wx.Button(self, -1, 'Model')
		self.szbuttons.Add(self.bmodel, (4, 0), (1, 1), wx.EXPAND)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.Bind(wx.EVT_BUTTON, self.onModelButton, self.bmodel)

	def onCalibrateButton(self, evt):
		self.node.uiStartLoop()

	def onAbortButton(self, evt):
		self.node.uiStopLoop()

	def onModelButton(self, evt):
		self.node.uiFit()

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

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

