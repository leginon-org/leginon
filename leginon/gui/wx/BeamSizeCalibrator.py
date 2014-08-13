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

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'dose'
	def initialize(self):
		leginon.gui.wx.Calibrator.Panel.initialize(self)
		self.dialog = None
		self.toolbar.DeleteTool(leginon.gui.wx.ToolBar.ID_ABORT)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE, 'ruler', shortHelpString='Measure current beam size')
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool, id=leginon.gui.wx.ToolBar.ID_MEASURE)

	def onCalibrateTool(self, evt):
		if not self.node.getC2Size():
			self.c2dialog = C2SizeDialog(self,'C2 Aperture Size')
			self.c2dialog.ShowModal()
			self.c2dialog.Destroy()
		self.dialog = BeamSizeCalibrationDialog(self)
		self.dialog.ShowModal()
		self.dialog.Destroy()
		self.dialog = None

	def onMeasureTool(self, evt):
		threading.Thread(target=self.node.uiMeasureBeamDiameter).start()

class C2SizeDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, title):
		self.node = parent.node
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, style=wx.DEFAULT_DIALOG_STYLE)

	def onInitialize(self):
		c2sizer = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'C2 size: ')
		c2sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_LEFT)
		self.c2sizectrl = IntEntry(self, -1, chars=6)
		c2sizer.Add(self.c2sizectrl, (0, 1), (1, 1), wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'um')
		c2sizer.Add(label, (0, 2), (1, 1), wx.ALIGN_LEFT)

		self.sz.Add(c2sizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL,10)
		savebtn = wx.Button(self, -1, 'Save')
		self.sz.Add(savebtn, (1, 0), (1, 1), wx.EXPAND|wx.ALL,5)
		self.sz.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onSave, savebtn)

	def onSave(self,evt):
		args = (self.c2sizectrl.GetValue(),)
		threading.Thread(target=self.node.uiSetC2Size,args=args).start()

class BeamSizeCalibrationDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return BeamSizeScrolledSettings(self,self.scrsize,False)

class BeamSizeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def getTitle(self):
		return 'Beam Size Calibration'

	def addSettings(self):
		newrow = 0
		newrow,newcol = self.createScreenPositionSetter((newrow,0))
		newrow,newcol = self.createScreenBeamDiameterEntry((newrow,0))
		newrow,newcol = self.createSaveFocusedIntensityButton((newrow,0))

	def addBindings(self):
		self.Bind(wx.EVT_BUTTON, self.onScreenUpButton, self.bscreenup)
		self.Bind(wx.EVT_BUTTON, self.onScreenDownButton, self.bscreendown)
		self.Bind(wx.EVT_BUTTON, self.onSaveScreenDiameterButton, self.save_screen_diameter)
		self.Bind(wx.EVT_BUTTON, self.onSaveFocusedBeamButton, self.save_focused_beam)

	def createScreenPositionSetter(self,start_position):
		sb = wx.StaticBox(self, -1, 'Set Main Screen Position')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = wx.GridBagSizer(5, 5)
		self.bscreenup = wx.Button(self, -1, 'Up')
		self.bscreendown = wx.Button(self, -1, 'Down')

		szscreen = wx.GridBagSizer(5, 5)
		szscreen.Add(self.bscreenup, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szscreen.Add(self.bscreendown, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szscreen.AddGrowableCol(0)
		szscreen.AddGrowableCol(1)

		sbsz.Add(szscreen, 0, wx.EXPAND|wx.ALL, 5)
		# add to main
		total_length = (1,2)
		self.sz.Add(sbsz, start_position, total_length,
				  wx.ALIGN_LEFT|wx.ALL)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createScreenBeamDiameterEntry(self,start_position):
		sb = wx.StaticBox(self, -1, 'Diameter on Screen')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.widgets['beam diameter'] = FloatEntry(self, -1, chars=6)
		self.save_screen_diameter = wx.Button(self, -1, 'Save')
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Set Beam diameter on main screen to')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['beam diameter'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'meters and then:')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.save_screen_diameter, (1, 3), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5)

		sz.AddGrowableCol(1)

		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		# add to main
		total_length = (1,3)
		self.sz.Add(sbsz, start_position, total_length,
				  wx.ALIGN_LEFT|wx.ALL)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createSaveFocusedIntensityButton(self,start_position):
		sb = wx.StaticBox(self, -1, 'Record Focused Beam')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.save_focused_beam = wx.Button(self, -1, 'Save Focused Beam')
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Focus the Beam and click:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.save_focused_beam, (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.AddGrowableCol(1)

		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		# add to main
		total_length = (1,2)
		self.sz.Add(sbsz, start_position, total_length,
				  wx.ALIGN_LEFT|wx.ALL)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def onScreenUpButton(self, evt):
		threading.Thread(target=self.node.screenUp).start()
		#self.node.screenUp()

	def onScreenDownButton(self, evt):
		threading.Thread(target=self.node.screenDown).start()
		#self.node.screenDown()

	def onSaveFocusedBeamButton(self, evt):
		threading.Thread(target=self.node.uiMeasureFocusedIntensityDialValue).start()

	def onSaveScreenDiameterButton(self, evt):
		self.widgets['beam diameter'].GetValue()
		threading.Thread(target=self.node.uiMeasureIntensityDialValue).start()

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

