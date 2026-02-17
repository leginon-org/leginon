# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx
import numpy

import leginon.gui.wx.Calibrator
import leginon.gui.wx.ManualComaFree
import leginon.gui.wx.ManualFocus
import leginon.gui.wx.MatrixCalibrator
import leginon.gui.wx.Dialog
from leginon.gui.wx.Entry import FloatEntry, IntEntry
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

hide_stig = True
hide_incomplete = False

class SettingsDialog(leginon.gui.wx.Calibrator.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Calibrator.ScrolledSettings):
	def initialize(self):
		sizers = leginon.gui.wx.Calibrator.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Beam Tilt')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

#		self.widgets['measure beam tilt'] = FloatEntry(self, -1, chars=7)
		self.widgets['correct tilt'] = wx.CheckBox(self, -1, 'Correct image for tilt')
		self.widgets['settling time'] = FloatEntry(self, -1, chars=4)

		sizer = wx.GridBagSizer(5, 20)
#		label = wx.StaticText(self, -1, 'Measure beam tilt (+/-)')
#		sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
#		sizer.Add(self.widgets['measure beam tilt'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sizer.Add(self.widgets['correct tilt'], (0, 2), (1, 3), wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, 'Settling time')
		sizer.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.widgets['settling time'], (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		sizer.Add(label, (1, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		sizer.AddGrowableRow(0)
		sizer.AddGrowableRow(1)
		sizer.AddGrowableCol(0)
		sizer.AddGrowableCol(2)

		sbsz.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)

		return sizers + [sbsz]

def capitalize(string):
	if string:
		string = string[0].upper() + string[1:]
	return string

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'beamtilt'
	settingsdialogclass = SettingsDialog
	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Tableau', display=True)
		if isinstance(self.imagepanel, leginon.gui.wx.TargetPanel.TargetImagePanel):
			color = wx.Colour(255, 128, 0)
			self.imagepanel.addTargetTool('Peak', color)

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)
		# tools
		choices = ['Objective',]
		self.cparameter = wx.Choice(self.toolbar, -1, choices=choices)
		self.cparameter.SetSelection(0)

		self.toolbar.InsertControl(5, self.cparameter)
		self.toolbar.InsertTool(6, leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS, 'settings', shortHelp='Parameter Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE, 'ruler', shortHelp='Measure')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT, 'focusget', shortHelp='Eucentric Focus From Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT, 'focusset', shortHelp='Eucentric Focus To Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_BEAMTILT, 'beamtiltget', shortHelp='Stigmator Center From Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_BEAMTILT, 'beamtiltset', shortHelp='Stigmator Center To Scope')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EDIT, 'edit', shortHelp='Edit current calibration')

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

		self.Bind(leginon.gui.wx.Events.EVT_GET_INSTRUMENT_DONE, self.onGetInstrumentDone)
		self.Bind(leginon.gui.wx.Events.EVT_SET_INSTRUMENT_DONE, self.onSetInstrumentDone)
		self.Bind(leginon.gui.wx.Events.EVT_MEASUREMENT_DONE, self.onMeasurementDone)

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)

		self.measure_dialog = MeasureDialog(self)
		self.manualfocus_dialog = leginon.gui.wx.ManualFocus.SimpleManualFocusDialog(self)
		self.dialog_done = threading.Event()

		self.Bind(leginon.gui.wx.Events.EVT_EDIT_CALIBRATION, self.onEditStigCalibration)

		self.cparameter.SetStringSelection(capitalize(self.node.parameter))
		self.cparameter.Bind(wx.EVT_CHOICE, self.onParameterChoice, self.cparameter)
		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool, id=leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool, id=leginon.gui.wx.ToolBar.ID_MEASURE)
		#self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureComafreeTool, id=leginon.gui.wx.ToolBar.ID_MEASURE_COMAFREE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusFromScope, id=leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusToScope, id=leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStigmatorCenterFromScope, id=leginon.gui.wx.ToolBar.ID_GET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStigmatorCenterToScope, id=leginon.gui.wx.ToolBar.ID_SET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEditFocusCalibrationTool, id=leginon.gui.wx.ToolBar.ID_EDIT)

	def instrumentEnable(self, enable):
		tools = [
			leginon.gui.wx.ToolBar.ID_ACQUIRE,
			leginon.gui.wx.ToolBar.ID_CALIBRATE,
			#leginon.gui.wx.ToolBar.ID_MEASURE,
			leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT,
			leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT,
			leginon.gui.wx.ToolBar.ID_GET_BEAMTILT,
			leginon.gui.wx.ToolBar.ID_SET_BEAMTILT,
		]
		for tool in tools:
			self.toolbar.EnableTool(tool, enable)

		self.measure_dialog.scrsettings.measure.Enable(enable)
		if self.node.measurement:
			self.measure_dialog.scrsettings.correctdefocus.Enable(enable)
			self.measure_dialog.scrsettings.correctstig.Enable(enable)
		self.measure_dialog.scrsettings.resetdefocus.Enable(enable)

	def _acquisitionEnable(self, enable):
		self.instrumentEnable(enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_SETTINGS, enable)

	def _calibrationEnable(self, enable):
		self._acquisitionEnable(enable)
		self.cparameter.Enable(enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS, enable)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, not enable)

	def onGetInstrumentDone(self, evt):
		self.instrumentEnable(True)

	def onSetInstrumentDone(self, evt):
		self.instrumentEnable(True)

	def onMeasurementDone(self, evt):
		self._calibrationEnable(True)
		if evt.defocus is None:
			label = '(Not measured)'
		else:
			label = '%g' % evt.defocus
		self.measure_dialog.scrsettings.labels['defocus'].SetLabel(label)
		for axis, value in list(evt.stig.items()):
			if value is None:
				label = '(Not measured)'
			else:
				label = '%g' % value
			self.measure_dialog.scrsettings.labels['stigmator'][axis].SetLabel(label)
		self.measure_dialog.scrsettings.Layout()
		self.measure_dialog.scrsettings.Fit()

	def measurementDone(self, defocus, stig):
		evt = leginon.gui.wx.Events.MeasurementDoneEvent()
		evt.defocus = defocus
		evt.stig = stig
		self.GetEventHandler().AddPendingEvent(evt)

#-----------
	def onEucentricFocusToScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.eucentricFocusToScope).start()

	def onEucentricFocusFromScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.eucentricFocusFromScope).start()

	def onStigmatorCenterToScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.stigmatorCenterToScope).start()

	def onStigmatorCenterFromScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.stigmatorCenterFromScope).start()

	def onMeasureTool(self, evt):
		self.measure_dialog.ShowModal()

	def onParameterChoice(self, evt):
		self.node.parameter = evt.GetString().lower()

	def onParameterSettingsTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		if parameter == 'Stigmator':
			dialog = StigmatorSettingsDialog(self)
		else:
			# Do nothing, just enable other tools
			self.node.logger.warning('Please use Beam-Tilt Coma selection to calibrate this')
			self._calibrationEnable(True)
			return
		dialog.ShowModal()
		dialog.Destroy()

	def onCalibrateTool(self, evt):
		self._calibrationEnable(False)
		parameter = self.cparameter.GetStringSelection()
		if parameter == 'Defocus':
			threading.Thread(target=self.node.calibrateDefocus).start()
		elif parameter == 'Stigmator':
			threading.Thread(target=self.node.calibrateStigmator).start()
		elif parameter == 'Beam-Tilt Coma':
			threading.Thread(target=self.node.calibrateComaFree).start()
		elif parameter == 'Image-Shift Coma':
			threading.Thread(target=self.node.calibrateImageShiftComa).start()
		else:
			self.node.logger.warning('Please use Beam-Tilt Coma selection to calibrate this')
			# Do nothing, just enable other tools
			self._calibrationEnable(True)
			return

	def onAbortTool(self, evt):
		self.node.abortCalibration()

	def onEditFocusCalibrationTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		if parameter != 'Defocus':
			threading.Thread(target=self.node.editCurrentCalibration).start()
		else:
			threading.Thread(target=self.node.editCurrentFocusCalibration).start()

	def onEditStigCalibration(self, evt):
		'''
		Edit and save upon closing dialog.
		Includes probe but not magnification.
		'''
		parameter = evt.calibrationdata['type']
		tem = evt.calibrationdata['tem']
		ccdcamera = evt.calibrationdata['ccdcamera']
		rotation = evt.calibrationdata['rotation angle']
		coeff = evt.calibrationdata['coeff']
		print(coeff)
		dialog = EditStigDialog(self, rotation, coeff , parameter, 'Edit Calibration')
		if dialog.ShowModal() == wx.ID_OK:
			rotation, coeff = dialog.getStigCalibration()
			self.node.saveCalibration(rotation, coeff, parameter)
		dialog.Destroy()

	def editCalibration(self, calibrationdata):
		evt = leginon.gui.wx.Events.EditCalibrationEvent(calibrationdata=calibrationdata)
		self.GetEventHandler().AddPendingEvent(evt)

	def onEditFocusCalibration(self, evt):
		dialog = EditFocusCalibrationDialog(self, evt.matrix, evt.rotation_center, evt.eucentric_focus, 'Edit Calibration')
		if dialog.ShowModal() == wx.ID_OK:
			calibration = dialog.getFocusCalibration()
			self.node.saveFocusCalibration(calibration, evt.parameter, evt.high_tension, evt.magnification, evt.tem, evt.ccd_camera, evt.probe)
		dialog.Destroy()

	def editFocusCalibration(self, **kwargs):
		evt = leginon.gui.wx.Events.EditFocusCalibrationEvent(**kwargs)
		self.GetEventHandler().AddPendingEvent(evt)

class StigmatorSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return StigmatorScrolledSettings(self,self.scrsize,False)

class StigmatorScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Stigmator Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['stig beam tilt'] = FloatEntry(self, -1, chars=9)
		self.widgets['stig delta'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Beam tilt (+/-)')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig beam tilt'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Delta stig')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['stig delta'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]


class MeasureDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return MeasureScrolledSettings(self,self.scrsize,False)

class MeasureScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):

		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Parameters')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['measure defocus'] = FloatEntry(self, -1, chars=8)

		self.labels = {}
		self.labels['defocus'] = wx.StaticText(self, -1, '(Not measured)')
		self.labels['stigmator'] = {}
		for axis in ('x', 'y'):
			self.labels['stigmator'][axis] = wx.StaticText(self, -1, '(Not measured)')

		szresult = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Measured with defocus (m)')
		szresult.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.widgets['measure defocus'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Defocus')
		szresult.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.labels['defocus'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stig. x')
		szresult.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.labels['stigmator']['x'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Stig. y')
		szresult.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.labels['stigmator']['y'], (3, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.AddGrowableRow(0)
		szresult.AddGrowableRow(1)
		szresult.AddGrowableRow(2)
		szresult.AddGrowableRow(3)
		szresult.AddGrowableCol(0)

		self.measure = wx.Button(self, -1, 'Measure')
		self.correctdefocus = wx.Button(self, -1, 'Correct Defocus')
		self.correctstig = wx.Button(self, -1, 'Correct Stig.')
		self.resetdefocus = wx.Button(self, -1, 'Reset Defocus')
		self.correctdefocus.Enable(False)
		self.correctstig.Enable(False)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.correctdefocus, (1, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.correctstig, (2, 0), (1, 1), wx.EXPAND)
		szbutton.Add(self.resetdefocus, (3, 0), (1, 1), wx.EXPAND)

		sz = wx.GridBagSizer(5, 20)
		sz.Add(szresult, (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(szbutton, (0, 1), (1, 1), wx.ALIGN_CENTER)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)
		self.Bind(wx.EVT_BUTTON, self.onCorrectDefocusButton, self.correctdefocus)
		self.Bind(wx.EVT_BUTTON, self.onCorrectStigButton, self.correctstig)
		self.Bind(wx.EVT_BUTTON, self.onResetDefocusButton, self.resetdefocus)

		return [sbsz]

	def onMeasureButton(self, evt):
		self.dialog.setNodeSettings()
		self.panel._calibrationEnable(False)
		threading.Thread(target=self.node.measure).start()

	def onCorrectDefocusButton(self, evt):
		self.panel.instrumentEnable(False)
		threading.Thread(target=self.node.correctDefocus).start()

	def onCorrectStigButton(self, evt):
		self.panel.instrumentEnable(False)
		threading.Thread(target=self.node.correctStigmator).start()

	def onResetDefocusButton(self, evt):
		self.panel.instrumentEnable(False)
		threading.Thread(target=self.node.resetDefocus).start()

class EditStigDialog(leginon.gui.wx.Dialog.Dialog):
	def __init__(self, parent, rotation_angle, coeff, title, subtitle='Stig Calibration'):
		if coeff is not None and len(coeff.keys()) != 2:
			raise ValueError
		self.rotation = rotation_angle
		self.coeff = coeff
		leginon.gui.wx.Dialog.Dialog.__init__(self, parent, title, subtitle=subtitle,
																	style=wx.DEFAULT_DIALOG_STYLE)

	def onInitialize(self):
		row = 0
		label = wx.StaticText(self, -1, 'Coefficient:')
		self.sz.Add(label, (row + 2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.coeff_entries = {}
		for i, axis in enumerate(('x', 'y')):
			label = wx.StaticText(self, -1, axis)
			self.sz.Add(label, (row + 1, i + 1), (1, 1), wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_BOTTOM)
			entry = FloatEntry(self, -1, chars=9)
			if self.coeff is not None:
				try:
					entry.SetValue(self.coeff[axis])
				except KeyError:
					pass
			self.coeff_entries[axis] = entry
			self.sz.Add(entry, (row + 2, i + 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Stigmator Rotation (degrees):')
		self.sz.Add(label, (row + 3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.rotation_entry = FloatEntry(self, -1, chars=9)
		self.sz.Add(self.rotation_entry, (row + 3, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.rotation_entry.SetValue(self.rotation)

		self.addButton('Save', wx.ID_OK)
		self.addButton('Cancel', wx.ID_CANCEL)

		self.Bind(wx.EVT_BUTTON, self.onSaveButton, id=wx.ID_OK)

	def onSaveButton(self, evt):
		try:
			self.rotation, self.coeff = self.getStigCalibration()
		except ValueError:
			dialog = wx.MessageDialog(self, 'Invalid calibration values',
				'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

	def getStigCalibration(self):
		coeff = {}
		for axis, entry in list(self.coeff_entries.items()):
			value = entry.GetValue()
			if value is None:
				raise ValueError
			coeff[axis] = value

		rotation = self.rotation_entry.GetValue()
		if value is None:
			raise ValueError

		return rotation, coeff

class EditFocusCalibrationDialog(leginon.gui.wx.MatrixCalibrator.EditMatrixDialog):
	def __init__(self, parent, matrix, rotation_center, eucentric_focus, title, subtitle='Focus Calibration'):
		self.rotation_center = rotation_center
		self.eucentric_focus = eucentric_focus
		leginon.gui.wx.MatrixCalibrator.EditMatrixDialog.__init__(self, parent, matrix, title, subtitle='Focus Calibration')

	def onInitialize(self):
		matrix = leginon.gui.wx.MatrixCalibrator.EditMatrixDialog.onInitialize(self)
		row = 1

		label = wx.StaticText(self, -1, 'Rotation Center:')
		self.sz.Add(label, (row + 2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.rotation_center_entries = {}
		for i, axis in enumerate(('x', 'y')):
			label = wx.StaticText(self, -1, axis)
			self.sz.Add(label, (row + 1, i + 1), (1, 1), wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_BOTTOM)
			entry = FloatEntry(self, -1, chars=9)
			if self.rotation_center is not None:
				try:
					entry.SetValue(self.rotation_center[axis])
				except KeyError:
					pass
			self.rotation_center_entries[axis] = entry
			self.sz.Add(entry, (row + 2, i + 1), (1, 1), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Eucentric Focus:')
		self.sz.Add(label, (row + 3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.eucentric_focus_entry = FloatEntry(self, -1, chars=9)
		self.sz.Add(self.eucentric_focus_entry, (row + 3, 1), (1, 2), wx.ALIGN_CENTER|wx.FIXED_MINSIZE)
		self.eucentric_focus_entry.SetValue(self.eucentric_focus)

	def getFocusCalibration(self):
		matrix = leginon.gui.wx.MatrixCalibrator.EditMatrixDialog.getMatrix(self)
		rotation_center = {}
		for axis, entry in list(self.rotation_center_entries.items()):
			value = entry.GetValue()
			if value is None:
				raise ValueError
			rotation_center[axis] = value

		eucentric_focus = self.eucentric_focus_entry.GetValue()
		if value is None:
			raise ValueError

		return matrix, rotation_center, eucentric_focus

if __name__ == '__main__':
	class Node(object):
		def __init__(self):
			app = wx.PySimpleApp()
			app.frame = wx.Frame(None, -1, 'Matrix Calibration Test')
			app.frame.node = Node()
			matrix = numpy.zeros((2, 2))
			rotation_center = {'x': 0, 'y': 0}
			eucentric_focus = 0
			app.dialog = MeasureDialog(app.frame)
			app.dialog.Show()
			app.MainLoop()

