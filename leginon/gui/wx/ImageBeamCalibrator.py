# -*- coding: iso-8859-1 -*-
# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
import threading
import wx

from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Calibrator
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Dialog

class SettingsDialog(leginon.gui.wx.Calibrator.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Calibrator.ScrolledSettings):
	def initialize(self):
		szcal = leginon.gui.wx.Calibrator.ScrolledSettings.initialize(self)
		sbszs = self.addImageBeamSettings()
		return szcal + sbszs

	def addImageBeamSettings(self,start_position=(0,0)):
		sb = wx.StaticBox(self, -1, 'Image Shift Applied in Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		label1 = wx.StaticText(self, -1, 'Move')
		self.widgets['image shift delta'] = FloatEntry(self, -1, chars=9)
		label2 = wx.StaticText(self, -1, 'meters in each axis')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['image shift delta'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(label2, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		sz.AddGrowableCol(2)
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		return [sbsz,]

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'matrix'
	settingsdialogclass = SettingsDialog
	def initialize(self):
		leginon.gui.wx.Calibrator.Panel.initialize(self)
		self.dialog = None
		self.toolbar.DeleteTool(leginon.gui.wx.ToolBar.ID_ABORT)

	def onCalibrateTool(self, evt):
		self.node.uiCalibrate()
		if self.node.instrument_status == 'good':
			dialog = CalibrateDialog(self,'Image Beam Calibration' , '')
			if dialog.ShowModal() != wx.ID_OK:
				self.node.uiAbort()
			self._calibrationEnable(True)

class CalibrateDialog(leginon.gui.wx.Dialog.ConfirmationDialog):
	def addDescriptionSizers(self):
		end_position = self.addStep1Sizer((0,0))
		end_position = self.addStep2Sizer((end_position[0],0))
		end_position = self.addStep3Sizer((end_position[0],0))
		self.b_step2.Enable(False)
		self.b_step3.Enable(False)
		self.bok.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onStep1Done, self.b_step1)
		self.Bind(wx.EVT_BUTTON, self.onStep2Done, self.b_step2)
		self.Bind(wx.EVT_BUTTON, self.onStep3Done, self.b_step3)

	def addStep1Sizer(self,start_position):
		sb = wx.StaticBox(self, -1, 'Step 1: Center Beam')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		label1 = wx.StaticText(self, -1, 'Click')
		self.b_step1 = wx.Button(self, -1, 'Done')
		label2 = wx.StaticText(self, -1, 'After centering beam on Main Screen')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.b_step1, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(label2, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		sz.AddGrowableCol(2)
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		self.mainsz.Add(sbsz, start_position, (1,1), wx.EXPAND|wx.ALL, 5)
		return (start_position[0]+1,start_position[1]+1)

	def addStep2Sizer(self,start_position):
		sb = wx.StaticBox(self, -1, 'Step 2: Image Shifted in X:')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		label1 = wx.StaticText(self, -1, 'Click')
		self.b_step2 = wx.Button(self, -1, 'Done')
		label2 = wx.StaticText(self, -1, 'After recentering beam on Main Screen')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.b_step2, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(label2, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		sz.AddGrowableCol(2)
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		self.mainsz.Add(sbsz, start_position, (1,1), wx.EXPAND|wx.ALL, 5)
		return (start_position[0]+1,start_position[1]+1)

	def addStep3Sizer(self,start_position):
		sb = wx.StaticBox(self, -1, 'Step 3: Image Shifted in Y:')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		label1 = wx.StaticText(self, -1, 'Click')
		self.b_step3 = wx.Button(self, -1, 'Done')
		label2 = wx.StaticText(self, -1, 'After recentering beam on Main Screen')
		sz = wx.GridBagSizer(5, 5)
		sz.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.b_step3, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(label2, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		sz.AddGrowableCol(2)
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		self.mainsz.Add(sbsz, start_position, (1,1), wx.EXPAND|wx.ALL, 5)
		return (start_position[0]+1,start_position[1]+1)

	def onStep1Done(self,evt):
		t = threading.Thread(target=self.parent.node.prepareStep2)
		t.start()
		self.b_step1.Enable(False)
		self.b_step2.Enable(True)
		t.join()

	def onStep2Done(self,evt):
		threading.Thread(target=self.parent.node.prepareStep3).start()
		self.b_step2.Enable(False)
		self.b_step3.Enable(True)

	def onStep3Done(self,evt):
		threading.Thread(target=self.parent.node.finish).start()
		self.b_step3.Enable(False)
		self.bok.Enable(True)

	def onOK(self,evt):
		threading.Thread(target=self.parent.node.saveCalibration).start()
		super(CalibrateDialog,self).onOK(evt)

	def onCancel(self,evt):
		self.parent.node.uiAbort()
		super(CalibrateDialog,self).onCancel(evt)

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

