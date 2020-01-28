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
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTypeTool('Tableau', display=True)
		if isinstance(self.imagepanel, leginon.gui.wx.TargetPanel.TargetImagePanel):
			color = wx.Colour(255, 128, 0)
			self.imagepanel.addTargetTool('Peak', color)

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)
		# tools
		choices = ['Defocus', 'Image-Shift Coma', 'Image-Shift Stig', 'Image-Shift Defocus']
		if not hide_stig:
			choices.append('Stigmator')
		self.cparameter = wx.Choice(self.toolbar, -1, choices=choices)
		self.cparameter.SetSelection(0)

		self.toolbar.InsertControl(5, self.cparameter)
		self.toolbar.InsertTool(6, leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS, 'settings', shortHelpString='Parameter Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE, 'ruler', shortHelpString='Measure')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT, 'focusget', shortHelpString='Eucentric Focus From Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT, 'focusset', shortHelpString='Eucentric Focus To Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_GET_BEAMTILT, 'beamtiltget', shortHelpString='Rotation Center From Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SET_BEAMTILT, 'beamtiltset', shortHelpString='Rotation Center To Scope')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ALIGN, 'rotcenter', shortHelpString='Align Rotation Center')
		self.toolbar.AddSeparator()
		#self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE_COMAFREE, 'ruler', shortHelpString='Measure Coma-free beam tilt')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_EDIT, 'edit', shortHelpString='Edit current calibration')

		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_ABORT, False)

		self.Bind(leginon.gui.wx.Events.EVT_GET_INSTRUMENT_DONE, self.onGetInstrumentDone)
		self.Bind(leginon.gui.wx.Events.EVT_SET_INSTRUMENT_DONE, self.onSetInstrumentDone)
		self.Bind(leginon.gui.wx.Events.EVT_MEASUREMENT_DONE, self.onMeasurementDone)
		#self.Bind(leginon.gui.wx.Events.EVT_COMA_MEASUREMENT_DONE, self.onComaMeasurementDone)
		self.Bind(leginon.gui.wx.Events.EVT_READ_AB_FREE_STATE, self.onReadAbFreeState)
		self.Bind(leginon.gui.wx.Events.EVT_READ_STATE_DONE, self.onReadStateDone)

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)

		self.measure_dialog = MeasureDialog(self)
		self.comafree_dialog = MeasureComafreeDialog(self)
		self.align_dialog = AlignRotationCenterDialog(self)
		self.manualcomafree_dialog = leginon.gui.wx.ManualComaFree.ManualComaFreeDialog(self)
		self.manualfocus_dialog = leginon.gui.wx.ManualFocus.SimpleManualFocusDialog(self)
		self.read_aberration_free_dialog = ReadAberrationFreeDialog(self)
		self.dialog_done = threading.Event()

		self.Bind(leginon.gui.wx.Events.EVT_EDIT_MATRIX, self.onEditMatrix)
		self.Bind(leginon.gui.wx.Events.EVT_EDIT_FOCUS_CALIBRATION, self.onEditFocusCalibration)

		self.cparameter.SetStringSelection(capitalize(self.node.parameter))
		self.cparameter.Bind(wx.EVT_CHOICE, self.onParameterChoice, self.cparameter)
		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool, id=leginon.gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool, id=leginon.gui.wx.ToolBar.ID_MEASURE)
		#self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureComafreeTool, id=leginon.gui.wx.ToolBar.ID_MEASURE_COMAFREE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusFromScope, id=leginon.gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusToScope, id=leginon.gui.wx.ToolBar.ID_SET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterFromScope, id=leginon.gui.wx.ToolBar.ID_GET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterToScope, id=leginon.gui.wx.ToolBar.ID_SET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEditFocusCalibrationTool, id=leginon.gui.wx.ToolBar.ID_EDIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter, id=leginon.gui.wx.ToolBar.ID_ALIGN)

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
			if not hide_stig:
				self.measure_dialog.scrsettings.correctstig.Enable(enable)
		self.measure_dialog.scrsettings.resetdefocus.Enable(enable)

		self.comafree_dialog.measure.Enable(enable)
		if self.node.comameasurement:
			self.comafree_dialog.correct.Enable(enable)

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
		for axis, value in evt.stig.items():
			if value is None:
				label = '(Not measured)'
			else:
				label = '%g' % value
			self.measure_dialog.scrsettings.labels['stigmator'][axis].SetLabel(label)
		self.measure_dialog.scrsettings.Layout()
		self.measure_dialog.scrsettings.Fit()

	def onComaMeasurementDone(self, evt):
		self._calibrationEnable(True)
		for axis, value in evt.comatilt.items():
			if value is None:
				label = '(Not measured)'
			else:
				label = '%g' % value
			self.comafree_dialog.labels['comatilt'][axis].SetLabel(label)
		self.comafree_dialog.Layout()
		self.comafree_dialog.Fit()

	def measurementDone(self, defocus, stig):
		evt = leginon.gui.wx.Events.MeasurementDoneEvent()
		evt.defocus = defocus
		evt.stig = stig
		self.GetEventHandler().AddPendingEvent(evt)

	def comaMeasurementDone(self, beamtilt):
		evt = leginon.gui.wx.Events.ComaMeasurementDoneEvent()
		evt.comatilt = beamtilt
		self.GetEventHandler().AddPendingEvent(evt)

	def onReadStateDone(self, evt):
		for key in self.read_aberration_free_dialog.aberrations1d:
			value = evt.state[key]
			if value is None:
				label = '(Not measured)'
			else:
				label = '%g' % value
			self.read_aberration_free_dialog.labels[key].SetLabel(label)
		for key in self.read_aberration_free_dialog.aberrations2d:
			ab = evt.state[key]
			for axis, value in ab.items():
				if value is None:
					label = '(Not measured)'
				else:
					label = '%g' % value
				self.read_aberration_free_dialog.labels[key][axis].SetLabel(label)
		self.read_aberration_free_dialog.Layout()
		self.read_aberration_free_dialog.Fit()

	def readStateDone(self, state):
		evt = leginon.gui.wx.Events.ReadStateDoneEvent()
		evt.state = state
		self.GetEventHandler().AddPendingEvent(evt)

	def readAbFreeState(self,imageshift=None):
		# This is called from a sub thread.  It therefore need to
		# initiate dialog through an event
		evt = leginon.gui.wx.Events.ReadAbFreeStateEvent()
		evt.shift = imageshift
		self.GetEventHandler().AddPendingEvent(evt)

	def onReadAbFreeState(self, evt):
		'''
		Handle ReadAbFreeState event by opening the dialog and then
		respond accordingly after closing.
		'''
		if evt.shift:
			text = 'Image Shift x= %.1f um, y= %.1f um' % (evt.shift['x']*1e6, evt.shift['y']*1e6)
		else:
			text = ''
		self.read_aberration_free_dialog.setSubtitle(text)
		if self.read_aberration_free_dialog.ShowModal() != wx.ID_OK:
			is_ok = False
		else:
			is_ok = True
		threading.Thread(target=self.node.guiReadAbFreeStateDone, args=(is_ok,)).start()

	def setManualComaFreeImage(self, image, typename, stats={}):
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename, stats)
		self.manualcomafree_dialog.GetEventHandler().AddPendingEvent(evt)

	def setManualFocusImage(self, image, typename, stats={}):
		evt = leginon.gui.wx.Events.SetImageEvent(image, typename, stats)
		self.manualfocus_dialog.GetEventHandler().AddPendingEvent(evt)

#-----------
	def onEucentricFocusToScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.eucentricFocusToScope).start()

	def onEucentricFocusFromScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.eucentricFocusFromScope).start()

	def onRotationCenterToScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.rotationCenterToScope).start()

	def onRotationCenterFromScope(self, evt):
		self.instrumentEnable(False)
		threading.Thread(target=self.node.rotationCenterFromScope).start()

	def onAlignRotationCenter(self, evt):
		self.align_dialog.ShowModal()

	def onMeasureTool(self, evt):
		self.measure_dialog.ShowModal()

	def onMeasureComafreeTool(self, evt):
		self.comafree_dialog.ShowModal()

	def onParameterChoice(self, evt):
		self.node.parameter = evt.GetString().lower()

	def onParameterSettingsTool(self, evt):
		parameter = self.cparameter.GetStringSelection()
		if parameter == 'Defocus':
			dialog = DefocusSettingsDialog(self)
		elif parameter == 'Stigmator':
			dialog = StigmatorSettingsDialog(self)
		elif parameter == 'Beam-Tilt Coma':
			dialog = ComafreeSettingsDialog(self)
		elif parameter == 'Image-Shift Coma':
			dialog = ImageShiftComaSettingsDialog(self)
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

	def onEditMatrix(self, evt):
		'''
		Edit and save upon closing dialog.
		Includes probe but not magnification.
		'''
		matrix = evt.calibrationdata['matrix']
		parameter = evt.calibrationdata['type']
		ht = evt.calibrationdata['high tension']
		probe = evt.calibrationdata['probe']
		tem = evt.calibrationdata['tem']
		ccdcamera = evt.calibrationdata['ccdcamera']
		dialog = EditMatrixDialog(self, matrix, 'Edit Calibration')
		if dialog.ShowModal() == wx.ID_OK:
			matrix = dialog.getMatrix()
			self.node.saveCalibration(matrix, parameter, ht, None, tem, ccdcamera, probe)
		dialog.Destroy()

	def editCalibration(self, calibrationdata):
		evt = leginon.gui.wx.Events.EditMatrixEvent(calibrationdata=calibrationdata)
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

class DefocusSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return DefocusScrolledSettings(self,self.scrsize,False)

class DefocusScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Defocus Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['defocus beam tilt'] = FloatEntry(self, -1, chars=9)
		self.widgets['first defocus'] = FloatEntry(self, -1, chars=9)
		self.widgets['second defocus'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Beam tilt (+/-)')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['defocus beam tilt'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'First defocus')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['first defocus'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Second defocus')
		sz.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['second defocus'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

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

class ComafreeSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ComafreeScrolledSettings(self,self.scrsize,False)

class ComafreeScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Coma-free Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['comafree beam tilt'] = FloatEntry(self, -1, chars=9)
		self.widgets['comafree misalign'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Beam tilt (+/-)')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['comafree beam tilt'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Misalignment (+/-)')
		sz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['comafree misalign'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class ImageShiftComaSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ImageShiftComaScrolledSettings(self,self.scrsize,False)

class ImageShiftComaScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Image-Shift Coma Calibration')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)


		self.sz = wx.GridBagSizer(5, 5)
		position = (0,0)
		#position = self.addImageshiftComaTiltSizer(position)
		position = self.addImageshiftComaNumberSizer(position)
		position = self.addImageshiftComaStepSizer(position)
		#position = self.addImageshiftComaRepeatSizer(position)
		sbsz.Add(self.sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)
		return [sbsz]

	def addImageshiftComaTiltSizer(self, p=(0,0)):
		self.widgets['imageshift coma tilt'] = FloatEntry(self, -1, chars=9)
		label = wx.StaticText(self, -1, 'Coma measurement beam tilt (+/-)')
		self.sz.Add(label, p, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.widgets['imageshift coma tilt'], (p[0],p[1]+1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'radians')
		self.sz.Add(label, (p[0],p[1]+2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return (p[0]+1,p[1])

	def addImageshiftComaNumberSizer(self, p=(0,0)):
		self.widgets['imageshift coma number'] = IntEntry(self, -1, min=1, chars=2)
		label = wx.StaticText(self, -1, 'Measure coma at')
		self.sz.Add(label, p, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.widgets['imageshift coma number'], (p[0],p[1]+1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'positions per image shift direction')
		self.sz.Add(label, (p[0],p[1]+2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return (p[0]+1,p[1])

	def addImageshiftComaStepSizer(self, p=(0,0)):
		self.widgets['imageshift coma step'] = FloatEntry(self, -1, chars=9)
		label = wx.StaticText(self, -1, 'Add additional')
		self.sz.Add(label, p, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.widgets['imageshift coma step'], (p[0], p[1]+1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm image shift at each position')
		self.sz.Add(label, (p[0], p[1]+2), (1, 1), wx.ALIGN_LEFT)
		return (p[0]+1,p[1])

	def addImageshiftComaRepeatSizer(self, p=(0,0)):
		self.widgets['imageshift coma repeat'] = IntEntry(self, -1, min=1, chars=2)
		label = wx.StaticText(self, -1, 'Repeat coma measurement')
		self.sz.Add(label, p, (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.widgets['imageshift coma repeat'], (p[0], p[1]+1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'times')
		self.sz.Add(label, (p[0], p[1]+2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		return (p[0]+1,p[1])

class ReadAberrationFreeDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node
		self.panel = parent
		self.aberrations1d = ('defocus',)
		self.aberrations2d = ('stig','beam tilt')

		wx.Dialog.__init__(self, parent, -1, 'Aberration Free State')

		self.subtitle = wx.StaticText(self, -1, '')
		self.align = wx.Button(self, -1, 'Align ComaFree Manually')
		self.livefft = wx.Button(self, -1, 'View Live FFT')
		self.read = wx.Button(self, -1, 'Read Values')
		self.reset = wx.Button(self, -1, 'Reset Values')
		self.bok = wx.Button(self, wx.ID_OK, '&OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, '&Cancel')
		self.manualcomafree_dialog = self.panel.manualcomafree_dialog
		self.manualfocus_dialog = self.panel.manualfocus_dialog

		self.livefft.Enable(True)
		self.align.Enable(True)
		self.read.Enable(True)
		self.reset.Enable(True)
		self.Bind(wx.EVT_BUTTON, self.onManualFocusButton, self.livefft)
		self.Bind(wx.EVT_BUTTON, self.onAlignButton, self.align)
		self.Bind(wx.EVT_BUTTON, self.onReadButton, self.read)
		self.Bind(wx.EVT_BUTTON, self.onResetButton, self.reset)
		self.Bind(wx.EVT_BUTTON, self.onOKButton, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onSet, self.bcancel)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.livefft, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		szbutton.Add(self.align, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		szbutton.Add(self.read, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		szbutton.Add(self.reset, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		self.labels = {}
		for key in self.aberrations1d:
				self.labels[key] = wx.StaticText(self, -1, '(Not measured)')
		for key in self.aberrations2d:
			self.labels[key] = {}
			for axis in ('x', 'y'):
				self.labels[key][axis] = wx.StaticText(self, -1, '(Not measured)')

		self.szresult = wx.GridBagSizer(5, 5)

		startrow = 0
		for key in self.aberrations1d+self.aberrations2d:
			startrow = self.addResultSizer(startrow,key)
		self.szresult.AddGrowableCol(1)

		# BoxSizer
		sb = wx.StaticBox(self, -1, '')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.subtitle = wx.StaticText(self, -1, '')
		self.sbsz.Add(self.subtitle, 1, wx.EXPAND|wx.ALL, 5)
		sz = wx.GridBagSizer(5, 5)
		sz.Add(szbutton, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 10)
		sz.Add(self.szresult, (0, 1), (2, 2), wx.EXPAND|wx.ALL, 10)

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(self.sbsz, (0, 0), (1, 3), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(sz, (1, 0), (2, 3), wx.EXPAND|wx.ALL, 10)

		csizer = wx.GridBagSizer(5, 5)

		csizer.Add(self.bok, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 5)
		csizer.Add(self.bcancel, (0, 1), (1, 1), wx.EXPAND|wx.ALL, 5)
		self.sizer.Add(csizer, (3, 0), (1, 3), wx.ALIGN_RIGHT|wx.ALL, 10)

		self.sizer.AddGrowableRow(1)
		self.sizer.AddGrowableRow(2)
		self.sizer.AddGrowableRow(3)
		self.sizer.AddGrowableCol(0)
		self.sizer.AddGrowableCol(1)
		self.sizer.AddGrowableCol(2)

		self.SetSizerAndFit(self.sizer)

	def setSubtitle(self, text):
		self.subtitle.SetLabel(text)

	def addResultSizer(self, row, key):
		nextrow = row + 0
		label = wx.StaticText(self, -1, key)
		self.szresult.Add(label, (nextrow, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		if key in self.aberrations2d:
			label = wx.StaticText(self, -1, 'x')
			self.szresult.Add(label, (nextrow+1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.szresult.Add(self.labels[key]['x'], (nextrow+1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			label = wx.StaticText(self, -1, 'y')
			self.szresult.Add(label, (nextrow+2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.szresult.Add(self.labels[key]['y'], (nextrow+2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			nextrow +=3
		else:
			self.szresult.Add(self.labels[key], (nextrow+1, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
			nextrow +=2
		for r in range(row,nextrow-1):
			self.szresult.AddGrowableRow(r)
		return nextrow

	def onOKButton(self, evt):
		self.panel.dialog_done.set()
		evt.Skip()

	def onSet(self, evt):
		evt.Skip()

	def onAlignButton(self, evt):
		threading.Thread(target=self.node.acquireTableauImages).start()
		if self.manualcomafree_dialog.ShowModal() !=wx.ID_OK:
			self.onResetButton(evt=None)
		else:
			self.onReadButton(evt=None)

	def onManualFocusButton(self, evt):
		threading.Thread(target=self.node.manualFocusLoop).start()
		state = self.manualfocus_dialog.ShowModal()
		self.node.manualplayer.stop()
		if state != wx.ID_OK:
			self.onResetButton(evt=None)
		else:
			self.onReadButton(evt=None)

	def onReadButton(self, evt):
		self.panel._calibrationEnable(False)
		threading.Thread(target=self.node.readState).start()

	def onResetButton(self, evt):
		self.panel._calibrationEnable(False)
		threading.Thread(target=self.node.resetState).start()


class MeasureComafreeDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node
		self.panel = parent

		wx.Dialog.__init__(self, parent, -1, 'Measure Coma-free Beam Tilt')

		self.measure = wx.Button(self, -1, 'Measure')
		self.correctshift = wx.CheckBox(self, -1, 'Correct image-shift-induced beam tilt')
		self.correct = wx.Button(self, -1, 'Correct Beam Tilt')
		self.correct.Enable(False)
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)
		self.Bind(wx.EVT_BUTTON, self.onCorrectButton, self.correct)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.correctshift, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		szbutton.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		szbutton.Add(self.correct, (2, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		tiltlabel = wx.StaticText(self, -1, 'Tilt (radian):')
		self.tiltvalue = FloatEntry(self, -1, allownone=False, chars=5, value='0.005')
		sbsz.Add(tiltlabel, (0,0), (1,1))
		sbsz.Add(self.tiltvalue, (0,1), (1,1))

		self.labels = {}
		self.labels['comatilt'] = {}
		for axis in ('x', 'y'):
			self.labels['comatilt'][axis] = wx.StaticText(self, -1, '(Not measured)')

		szresult = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Beam Tilt Adjustment')
		szresult.Add(label, (0, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'x')
		szresult.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.labels['comatilt']['x'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'y')
		szresult.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.labels['comatilt']['y'], (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.AddGrowableRow(0)
		szresult.AddGrowableRow(1)
		szresult.AddGrowableRow(2)
		szresult.AddGrowableCol(1)

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 2), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(szresult, (1, 0), (2, 2), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(szbutton, (3, 0), (2, 2), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		btilt = self.tiltvalue.GetValue()
		correctshift = self.correctshift.GetValue()
		self.panel._calibrationEnable(False)
		threading.Thread(target=self.node.measureComaFree, args=(btilt,correctshift)).start()

	def onCorrectButton(self, evt):
		self.panel.instrumentEnable(False)
		threading.Thread(target=self.node.correctComaTilt).start()

class AlignRotationCenterDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Align Rotation Center')

		self.measure = wx.Button(self, -1, 'Align')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Defocus 1:')
		self.d1value = FloatEntry(self, -1, allownone=False, chars=5, value='-2e-6')
		sbsz.Add(label, (0,0), (1,1))
		sbsz.Add(self.d1value, (0,1), (1,1))
		label = wx.StaticText(self, -1, 'Defocus 2:')
		self.d2value = FloatEntry(self, -1, allownone=False, chars=5, value='-4e-6')
		sbsz.Add(label, (1,0), (1,1))
		sbsz.Add(self.d2value, (1,1), (1,1))

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		self.Close()
		d1 = self.d1value.GetValue()
		d2 = self.d2value.GetValue()
		threading.Thread(target=self.node.alignRotationCenter, args=(d1,d2,)).start()



class MeasureDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return MeasureScrolledSettings(self,self.scrsize,False)

class MeasureScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):

		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Parameters')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['measure beam tilt'] = FloatEntry(self, -1, chars=7)

		self.labels = {}
		self.labels['defocus'] = wx.StaticText(self, -1, '(Not measured)')
		self.labels['stigmator'] = {}
		for axis in ('x', 'y'):
			self.labels['stigmator'][axis] = wx.StaticText(self, -1, '(Not measured)')

		szresult = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'beam tilt (+/-)')
		szresult.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szresult.Add(self.widgets['measure beam tilt'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

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

class EditMatrixDialog(leginon.gui.wx.MatrixCalibrator.EditMatrixDialog):
	pass

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
			self.sz.Add(label, (row + 1, i + 1), (1, 1), wx.ALIGN_CENTER|wx.ALIGN_BOTTOM)
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
		for axis, entry in self.rotation_center_entries.items():
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
			app.dialog = ReadAberrationFreeDialog(app.frame)
			app.dialog.Show()
			app.MainLoop()

