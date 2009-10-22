# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/BeamTiltCalibrator.py,v $
# $Revision: 1.24 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-21 23:50:44 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx
import numpy
import gui.wx.Calibrator
import gui.wx.MatrixCalibrator
import gui.wx.Dialog
from gui.wx.Entry import FloatEntry
import gui.wx.Settings
import gui.wx.ToolBar

class SettingsDialog(gui.wx.Calibrator.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(gui.wx.Calibrator.ScrolledSettings):
	def initialize(self):
		sizers = gui.wx.Calibrator.ScrolledSettings.initialize(self)
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

class Panel(gui.wx.Calibrator.Panel):
	icon = 'beamtilt'
	settingsclass = SettingsDialog
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)

		choices = ['Defocus', 'Stigmator', 'Coma-free']
		self.parameter = wx.Choice(self.toolbar, -1, choices=choices)
		self.parameter.SetSelection(0)

		self.toolbar.InsertControl(5, self.parameter)
		self.toolbar.InsertTool(6, gui.wx.ToolBar.ID_PARAMETER_SETTINGS, 'settings', shortHelpString='Parameter Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE, 'ruler', shortHelpString='Measure')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GET_INSTRUMENT, 'focusget', shortHelpString='Eucentric Focus From Scope')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SET_INSTRUMENT, 'focusset', shortHelpString='Eucentric Focus To Scope')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_GET_BEAMTILT, 'beamtiltget', shortHelpString='Rotation Center From Scope')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_SET_BEAMTILT, 'beamtiltset', shortHelpString='Rotation Center To Scope')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ALIGN, 'rotcenter', shortHelpString='Align Rotation Center')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(gui.wx.ToolBar.ID_EDIT, 'edit', shortHelpString='Edit current calibration')
		self.toolbar.AddTool(gui.wx.ToolBar.ID_MEASURE_COMAFREE, 'ruler', shortHelpString='Measure Coma-free')

		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, False)

		self.Bind(gui.wx.Events.EVT_GET_INSTRUMENT_DONE, self.onGetInstrumentDone)
		self.Bind(gui.wx.Events.EVT_SET_INSTRUMENT_DONE, self.onSetInstrumentDone)
		self.Bind(gui.wx.Events.EVT_MEASUREMENT_DONE, self.onMeasurementDone)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)

		self.measure_dialog = MeasureDialog(self)
		self.comafree_dialog = MeasureComafreeDialog(self)
		self.align_dialog = AlignRotationCenterDialog(self)

		self.Bind(gui.wx.Events.EVT_EDIT_FOCUS_CALIBRATION, self.onEditFocusCalibration)

		self.toolbar.Bind(wx.EVT_TOOL, self.onParameterSettingsTool, id=gui.wx.ToolBar.ID_PARAMETER_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool, id=gui.wx.ToolBar.ID_MEASURE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureComafreeTool, id=gui.wx.ToolBar.ID_MEASURE_COMAFREE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusFromScope, id=gui.wx.ToolBar.ID_GET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEucentricFocusToScope, id=gui.wx.ToolBar.ID_SET_INSTRUMENT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterFromScope, id=gui.wx.ToolBar.ID_GET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRotationCenterToScope, id=gui.wx.ToolBar.ID_SET_BEAMTILT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onEditFocusCalibrationTool, id=gui.wx.ToolBar.ID_EDIT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAlignRotationCenter, id=gui.wx.ToolBar.ID_ALIGN)

	def instrumentEnable(self, enable):
		tools = [
			gui.wx.ToolBar.ID_ACQUIRE,
			gui.wx.ToolBar.ID_CALIBRATE,
			#gui.wx.ToolBar.ID_MEASURE,
			gui.wx.ToolBar.ID_GET_INSTRUMENT,
			gui.wx.ToolBar.ID_SET_INSTRUMENT,
			gui.wx.ToolBar.ID_GET_BEAMTILT,
			gui.wx.ToolBar.ID_SET_BEAMTILT,
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
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_SETTINGS, enable)

	def _calibrationEnable(self, enable):
		self._acquisitionEnable(enable)
		self.parameter.Enable(enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_PARAMETER_SETTINGS, enable)
		self.toolbar.EnableTool(gui.wx.ToolBar.ID_ABORT, not enable)

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

	def measurementDone(self, defocus, stig):
		evt = gui.wx.Events.MeasurementDoneEvent()
		evt.defocus = defocus
		evt.stig = stig
		self.GetEventHandler().AddPendingEvent(evt)

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
		self.align_dialog.Show()

	def onMeasureTool(self, evt):
		self.measure_dialog.ShowModal()

	def onMeasureComafreeTool(self, evt):
		self.comafree_dialog.Show()

	def onParameterSettingsTool(self, evt):
		parameter = self.parameter.GetStringSelection()
		if parameter == 'Defocus':
			dialog = DefocusSettingsDialog(self)
		elif parameter == 'Stigmator':
			dialog = StigmatorSettingsDialog(self)
		elif parameter == 'Coma-free':
			dialog = ComafreeSettingsDialog(self)
		else:
			raise RuntimeError
		dialog.ShowModal()
		dialog.Destroy()

	def onCalibrateTool(self, evt):
		self._calibrationEnable(False)
		parameter = self.parameter.GetStringSelection()
		if parameter == 'Defocus':
			threading.Thread(target=self.node.calibrateDefocus).start()
		elif parameter == 'Stigmator':
			threading.Thread(target=self.node.calibrateStigmator).start()
		elif parameter == 'Coma-free':
			threading.Thread(target=self.node.calibrateComaFree).start()
		else:
			raise RuntimeError

	def onAbortTool(self, evt):
		self.node.abortCalibration()

	def onEditFocusCalibrationTool(self, evt):
		threading.Thread(target=self.node.editCurrentCalibration).start()

	def onEditFocusCalibration(self, evt):
		dialog = EditFocusCalibrationDialog(self, evt.matrix, evt.rotation_center, evt.eucentric_focus, 'Edit Calibration')
		if dialog.ShowModal() == wx.ID_OK:
			calibration = dialog.getFocusCalibration()
			self.node.saveCalibration(calibration, evt.parameter, evt.high_tension, evt.magnification, evt.tem, evt.ccd_camera)
		dialog.Destroy()

	def editCalibration(self, **kwargs):
		evt = gui.wx.Events.EditFocusCalibrationEvent(**kwargs)
		self.GetEventHandler().AddPendingEvent(evt)

class DefocusSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return DefocusScrolledSettings(self,self.scrsize,False)

class DefocusScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
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

class StigmatorSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return StigmatorScrolledSettings(self,self.scrsize,False)

class StigmatorScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
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

class ComafreeSettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return ComafreeScrolledSettings(self,self.scrsize,False)

class ComafreeScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		gui.wx.Settings.ScrolledDialog.initialize(self)
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

class MeasureComafreeDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Measure Coma-free Alignment')

		self.measure = wx.Button(self, -1, 'Measure')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		tiltlabel = wx.StaticText(self, -1, 'Tilt (radian):')
		self.tiltvalue = FloatEntry(self, -1, allownone=False, chars=5, value='0.005')
		sbsz.Add(tiltlabel, (0,0), (1,1))
		sbsz.Add(self.tiltvalue, (0,1), (1,1))

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		btilt = self.tiltvalue.GetValue()
		threading.Thread(target=self.node.measureComaFree, args=(btilt,)).start()

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


class MeasureDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		return MeasureScrolledSettings(self,self.scrsize,False)

class MeasureScrolledSettings(gui.wx.Settings.ScrolledDialog):
	def initialize(self):

		gui.wx.Settings.ScrolledDialog.initialize(self)
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

class EditFocusCalibrationDialog(gui.wx.MatrixCalibrator.EditMatrixDialog):
	def __init__(self, parent, matrix, rotation_center, eucentric_focus, title, subtitle='Focus Calibration'):
		self.rotation_center = rotation_center
		self.eucentric_focus = eucentric_focus
		gui.wx.MatrixCalibrator.EditMatrixDialog.__init__(self, parent, matrix, title, subtitle='Focus Calibration')

	def onInitialize(self):
		matrix = gui.wx.MatrixCalibrator.EditMatrixDialog.onInitialize(self)
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
		matrix = gui.wx.MatrixCalibrator.EditMatrixDialog.getMatrix(self)
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
	app = wx.PySimpleApp()
	app.frame = wx.Frame(None, -1, 'Matrix Calibration Test')
	matrix = numpy.zeros((2, 2))
	rotation_center = {'x': 0, 'y': 0}
	eucentric_focus = 0
	app.dialog = EditFocusCalibrationDialog(app.frame, matrix, rotation_center, eucentric_focus, 'Test Edit Dialog')
	app.dialog.Show()
	app.MainLoop()

