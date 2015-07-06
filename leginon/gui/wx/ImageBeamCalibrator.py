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
	icon = 'matrix'
	def initialize(self):
		leginon.gui.wx.Calibrator.Panel.initialize(self)
		self.dialog = None
		self.toolbar.DeleteTool(leginon.gui.wx.ToolBar.ID_ABORT)

	def onCalibrateTool(self, evt):
		dialog = leginon.gui.wx.Dialog.ConfirmationDialog(self,'Image Beam Calibration' , 'Step 1: Center Beam')
		if dialog.ShowModal() == wx.ID_OK:
			self._calibrationEnable(False)
			threading.Thread(target=self.node.uiCalibrate).start()
		else:
			self.node.uiAbort()

	def moveBeam(self,axis = 'x'):
		# pop up dialog to wait
		dialog = leginon.gui.wx.Dialog.ConfirmationDialog(self,'Image Beam Calibration' , 'Image Shift applied in %s axis \n Step 2: Move Beam to Center' % axis)
		if dialog.ShowModal() == wx.ID_OK:
			return self.node.uiMoveBeamDone()
		else:
			self.node.uiAbort()

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

