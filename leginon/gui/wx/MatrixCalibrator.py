# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx
import numpy
import math

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Camera
import leginon.gui.wx.Calibrator
import leginon.gui.wx.Dialog
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

def capitalize(string):
	if string:
		string = string[0].upper() + string[1:]
	return string

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'matrix'
	def initialize(self):
		leginon.gui.wx.Calibrator.Panel.initialize(self)

		#InsertSeparator(2)
		self.cparameter = wx.Choice(self.toolbar, -1)
		self.cparameter.SetSelection(0)
		self.toolbar.InsertControl(5, self.cparameter)
		self.toolbar.InsertTool(6, leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS,
													'settings',
													shortHelpString='Parameter Settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EDIT, 'edit',
													shortHelpString='Edit current calibration')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CALC_PIXEL, 'calculate',
													shortHelpString='Transform pixel vectors between mags')

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.Bind(leginon.gui.wx.Events.EVT_EDIT_MATRIX, self.onEditMatrix)
		self.cparameter.AppendItems(map(capitalize, self.node.parameters.keys()))
		self.cparameter.SetStringSelection(capitalize(self.node.parameter))
		self.cparameter.SetSize(self.cparameter.GetBestSizeTuple())
		self.cparameter.Bind(wx.EVT_CHOICE, self.onParameterChoice, self.cparameter)
		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEditMatrixTool,
											id=leginon.gui.wx.ToolBar.ID_EDIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onCalcPixel,
											id=leginon.gui.wx.ToolBar.ID_CALC_PIXEL)
		self.toolbar.Realize()

	def onParameterSettingsTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		dialog = MatrixSettingsDialog(self, parameter.lower(), parameter)
		dialog.ShowModal()
		dialog.Destroy()

	def onParameterChoice(self, evt):
		self.node.parameter = evt.GetString().lower()

	def _calibrationEnable(self, enable):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, enable)
		self.cparameter.Enable(enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS, enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ACQUIRE, enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALIBRATE, enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, not enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_EDIT, enable)

	def onCalibrateTool(self, evt):
		self._calibrationEnable(False)
		threading.Thread(target=self.node.uiCalibrate).start()

	def onAbortTool(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)
		threading.Thread(target=self.node.uiAbort).start()

	def onEditMatrixTool(self, evt):
		threading.Thread(target=self.node.editCurrentCalibration).start()

	def onEditMatrix(self, evt):
		matrix = evt.calibrationdata['matrix']
		parameter = evt.calibrationdata['type']
		ht = evt.calibrationdata['high tension']
		mag = evt.calibrationdata['magnification']
		tem = evt.calibrationdata['tem']
		ccdcamera = evt.calibrationdata['ccdcamera']
		dialog = EditMatrixDialog(self, matrix, 'Edit Calibration')
		if dialog.ShowModal() == wx.ID_OK:
			matrix = dialog.getMatrix()
			self.node.saveCalibration(matrix, parameter, ht, mag, tem, ccdcamera)
		dialog.Destroy()

	def editCalibration(self, calibrationdata):
		evt = leginon.gui.wx.Events.EditMatrixEvent(calibrationdata=calibrationdata)
		self.GetEventHandler().AddPendingEvent(evt)

	def onCalcPixel(self, evt):
		dialog = PixelToPixelDialog(self, 'Pixel Vector Calculator')
		dialog.ShowModal()
		dialog.Destroy()

class MatrixSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def __init__(self, parent, parameter, parametername):
		self.parameter = parameter
		self.parametername = parametername
		leginon.gui.wx.Settings.Dialog.__init__(self,parent)
	def initialize(self):
		return MatrixScrolledSettings(self,self.scrsize,False,self.parameter,self.parametername)

class MatrixScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def __init__(self, parent, size=(200,200), scrolling=False, parameter=None, parametername=None):
		self.parameter = parameter
		self.parametername = parametername
		leginon.gui.wx.Settings.ScrolledDialog.__init__(self,parent,size,scrolling)

	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		self.sb = wx.StaticBox(self, -1, '%s calibration' % self.parametername)
		sbsz = wx.StaticBoxSizer(self.sb, wx.VERTICAL)

		self.widgets['%s tolerance' % self.parameter] = FloatEntry(self, -1, chars=9)
		self.widgets['%s shift fraction' % self.parameter] = FloatEntry(self, -1, chars=9)
		self.widgets['%s n average' % self.parameter] = IntEntry(self, -1, min=1, chars=2)
		self.widgets['%s interval' % self.parameter] = FloatEntry(self, -1, chars=9)
		self.widgets['%s current as base' % self.parameter] = wx.CheckBox(self, -1, 'Use current position as starting point')
		self.widgets['%s base' % self.parameter] = {}
		self.widgets['%s base' % self.parameter]['x'] = FloatEntry(self, -1, chars=9)
		self.widgets['%s base' % self.parameter]['y'] = FloatEntry(self, -1, chars=9)

		szbase = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'x')
		szbase.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'y')
		szbase.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Base:')
		szbase.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szbase.Add(self.widgets['%s base' % self.parameter]['x'], (1, 1), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		szbase.Add(self.widgets['%s base' % self.parameter]['y'], (1, 2), (1, 1),
								wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Tolerance:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s tolerance' % self.parameter], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Shift fraction:')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s shift fraction' % self.parameter], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, '%')
		sz.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Average:')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s n average' % self.parameter], (2, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'positions')
		sz.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Interval:')
		sz.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['%s interval' % self.parameter], (3, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['%s current as base' % self.parameter], (4, 0), (1, 3),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szbase, (5, 0), (1, 3), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class EditMatrixDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, matrix, title, subtitle='Calibration Matrix'):
		if matrix is not None and len(matrix.shape) != 2:
			raise ValueError
		self.matrix = matrix
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, subtitle=subtitle,
																	style=wx.DEFAULT_DIALOG_STYLE)

	def onInitialize(self):
		label = wx.StaticText(self, -1, 'Matrix:')
		self.sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.floatentries = []
		if self.matrix is None:
			shape = (2, 2)
		else:
			shape = self.matrix.shape
		for row in range(shape[0]):
			self.floatentries.append([])
			for column in range(shape[1]):
				self.floatentries[row].append([])
				self.floatentries[row][column] = FloatEntry(self, -1, chars=9)
				if self.matrix is not None:
					self.floatentries[row][column].SetValue(self.matrix[row, column])
				self.sz.Add(self.floatentries[row][column], (row, column + 1), (1, 1),
										wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		self.addButton('Save', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)

		self.Bind(wx.EVT_BUTTON, self.onSaveButton, id=wx.ID_OK)

	def onSaveButton(self, evt):
		try:
			self.matrix = self.getMatrix()
		except ValueError:
			dialog = wx.MessageDialog(self, 'Invalid calibration values',
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

	def getMatrix(self):
		if self.matrix is None:
			shape = (2, 2)
		else:
			shape = self.matrix.shape
		matrix = numpy.zeros(shape, numpy.float64)
		for row in range(shape[0]):
			for column in range(shape[1]):
				value = self.floatentries[row][column].GetValue()
				if value is None:
					raise ValueError
				matrix[row, column] = value
		return matrix

class PixelToPixelDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, title):
		self.node = parent.node
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, style=wx.DEFAULT_DIALOG_STYLE)

	def onInitialize(self):
		mag1lab = wx.StaticText(self, -1, 'Mag 1:')
		self.mag1 = IntEntry(self, -1, chars=8)
		mag2lab = wx.StaticText(self, -1, 'Mag 2:')
		self.mag2 = IntEntry(self, -1, chars=8)
		p1lab = wx.StaticText(self, -1, 'Pixel 1:')
		self.p1row = FloatEntry(self, -1, chars=4)
		self.p1col = FloatEntry(self, -1, chars=4)
		p2lab = wx.StaticText(self, -1, 'Pixel 2:')
		self.p2row = FloatEntry(self, -1, chars=4)
		self.p2col = FloatEntry(self, -1, chars=4)

		angle1lab = wx.StaticText(self, -1, 'Angle 1')
		self.angle1 = wx.StaticText(self, -1, '')
		len1lab = wx.StaticText(self, -1, 'Length 1')
		self.len1 = wx.StaticText(self, -1, '')
		angle2lab = wx.StaticText(self, -1, 'Angle 2')
		self.angle2 = wx.StaticText(self, -1, '')
		len2lab = wx.StaticText(self, -1, 'Length 2')
		self.len2 = wx.StaticText(self, -1, '')

		calcp1 = wx.Button(self, -1, 'Calculate')
		self.Bind(wx.EVT_BUTTON, self.calcp1, calcp1)
		calcp2 = wx.Button(self, -1, 'Calculate')
		self.Bind(wx.EVT_BUTTON, self.calcp2, calcp2)
		
		self.sz.Add(mag1lab, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.mag1, (0, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(mag2lab, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.mag2, (0, 4), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(p1lab, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.p1row, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.p1col, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(p2lab, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.p2row, (1, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.p2col, (1, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(angle1lab, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.angle1, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(angle2lab, (2, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.angle2, (2, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(len1lab, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.len1, (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(len2lab, (3, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.len2, (3, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.sz.Add(calcp1, (4, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(calcp2, (4, 3), (1, 3), wx.ALIGN_CENTER_VERTICAL)

	def calcp1(self, evt):
		p2row = self.p2row.GetValue()
		p2col = self.p2col.GetValue()
		mag1 = self.mag1.GetValue()
		mag2 = self.mag2.GetValue() 
		p2 = p2row,p2col
		p1 = self.node.pixelToPixel(mag2, mag1, p2)
		self.p1row.SetValue(p1[0])
		self.p1col.SetValue(p1[1])
		a,n = self.angle_len(p1)
		self.angle1.SetLabel(str(a))
		self.len1.SetLabel(str(n))

	def calcp2(self, evt):
		p1row = self.p1row.GetValue()
		p1col = self.p1col.GetValue()
		mag1 = self.mag1.GetValue()
		mag2 = self.mag2.GetValue() 
		p1 = p1row,p1col
		p2 = self.node.pixelToPixel(mag1, mag2, p1)
		self.p2row.SetValue(p2[0])
		self.p2col.SetValue(p2[1])
		a,n = self.angle_len(p2)
		self.angle2.SetLabel(str(a))
		self.len2.SetLabel(str(n))

	def angle_len(self, vect):
		angle = numpy.arctan2(*tuple(vect))
		angle = math.degrees(angle)
		len = numpy.hypot(*tuple(vect))
		return angle, len

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Matrix Calibration Test')
			#panel = Panel(frame, 'Test')
			matrix = numpy.zeros((2, 2))
			dialog = EditMatrixDialog(frame, matrix, 'Test Edit Dialog')
			dialog.Show()
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

