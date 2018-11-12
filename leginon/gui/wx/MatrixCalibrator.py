# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
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
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SCALE_MATRIX, 'calculate',
													shortHelpString='Scale current matrix to all higher mags')

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
		self.toolbar.Bind(wx.EVT_TOOL, self.onScaleMatrix,
											id=leginon.gui.wx.ToolBar.ID_SCALE_MATRIX)

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

	def onScaleMatrix(self, evt):
		threading.Thread(target=self.node.scaleMatrix).start()

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

