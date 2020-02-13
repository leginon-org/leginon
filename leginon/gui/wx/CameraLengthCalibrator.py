# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Calibrator
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.ToolBar

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'pixelsize'
	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.toolbar.InsertTool(4, leginon.gui.wx.ToolBar.ID_MEASURE, 'ruler', shortHelpString='Measure')
		self.measurement = None
		self.oldmag = None
		self.measuredialog = MeasureSettingsDialog(self)
		#self.Bind(leginon.gui.wx.ImagePanelTools.EVT_MEASUREMENT, self.onMeasurement)
		self.toolbar.Bind(wx.EVT_TOOL, self.onMeasureTool, id=leginon.gui.wx.ToolBar.ID_MEASURE)
		self.toolbar.DeleteTool(leginon.gui.wx.ToolBar.ID_ABORT)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)
		if self.node.mag != self.oldmag:
			self.measuredialog.scrsettings.measurements.setMeasurements([])
		if self.node.image_camera_length is not None:
			cam_length_label = 'x was '+str(self.node.image_camera_length)+' m'
		else:
			cam_length_label = 'x does not exist'
		label = 'camera length at '+str(self.node.mag)+cam_length_label
		self.measuredialog.scrsettings.currentimage_camera_length.SetLabel(label)
		self.oldmag = self.node.mag

	#def onMeasurement(self, evt):
	#	self.measurement = evt.measurement

	def onMeasureTool(self, evt):
#		self.measurement = evt.measurement
		self.measuredialog.Show(True)

	def onCalibrateTool(self, evt):
		dialog = CameraLengthCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class MeasureSettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return MeasureScrolledSettings(self,self.scrsize,False)

class MeasureScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Camera Length Measurement')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbl = wx.StaticBox(self, -1, 'Known D-Spacing')
		sblsz = wx.StaticBoxSizer(sbl, wx.VERTICAL)
		sbm = wx.StaticBox(self, -1, 'Distance Measured Between reflections')
		sbmsz = wx.StaticBoxSizer(sbm, wx.VERTICAL)
		sbp = wx.StaticBox(self, -1, 'Camera Length Results')
		sbpsz = wx.StaticBoxSizer(sbp, wx.VERTICAL)

		self.calculate = wx.Button(self, -1, 'Calculate Camera Length')
		self.measurements = MeasurementListCtrl(self, -1)
		self.save = wx.Button(self, -1, 'Save Averaged Camera Length From Selected')


		self.widgets['d spacing'] = FloatEntry(self, -1, chars=9)
		self.widgets['distance'] = FloatEntry(self, -1, chars=9)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'd spacing:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		sz.Add(self.widgets['d spacing'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'Angstrum')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)

		sblsz.Add(sz, 0, wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Measured Powder Ring Diameter on Diffraction Image:')
		sz.Add(label, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(self.widgets['distance'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_CENTER)
		label = wx.StaticText(self, -1, '(pixels)')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.calculate, (2, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE|wx.ALIGN_CENTER)
		sbmsz.Add(sz, 0, wx.ALIGN_CENTER)

		label = ' need image to find saved camera lengths'
		self.currentimage_camera_length = wx.StaticText(self, -1, label)
		sbpsz.Add(self.currentimage_camera_length, 0, wx.ALIGN_CENTER|wx.EXPAND)
		sbpsz.SetItemMinSize(self.measurements, self.measurements.getBestSize())
		sbpsz.Add(self.measurements, 1, wx.EXPAND)
		sbpsz.Add(self.save, 0, wx.ALIGN_CENTER)

		sbsz.Add(sblsz, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sbsz.Add(sbmsz, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sbsz.Add(sbpsz, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.Bind(wx.EVT_BUTTON, self.onCalculateButton, self.calculate)
		self.Bind(wx.EVT_BUTTON, self.onSaveButton, self.save)

		return [sbsz]

	def onCalculateButton(self, evt):
		self.dialog.setNodeSettings()
		camera_length = self.node.calculateCameraLength()
		if camera_length is not None:
			self.measurements.addMeasurement(camera_length)

	def onSaveButton(self, evt):
		measurements = self.measurements.getMeasurements(wx.LIST_STATE_SELECTED)
		average = self.node.averageCameraLengths(measurements)
		if average is not None:
			cam_length_label = 'x is now '+str(self.node.image_camera_length)+' m'
			label = 'camera length at '+str(self.node.mag)+cam_length_label
		else:
			label = 'Select at least one measurement for Averaging'
		self.currentimage_camera_length.SetLabel(label)

class ExtrapolateDialog(wx.Dialog):
	def __init__(self, parent, fromps, tops):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Extrapolate Camera Length',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		sb = wx.StaticBox(self, -1, 'Select Magnifications to Calculate')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.fromps = fromps
		self.pslc = CameraLengthListCtrl(self, -1)
		for camera_length in tops:
			self.pslc.addCameraLength(*camera_length)
		self.pslc.SetColumnWidth(0, 100)
		self.pslc.SetColumnWidth(2, 120)
		self.stps = wx.StaticText(self, -1, '')
		self.tccomment = wx.TextCtrl(self, -1, '(Extrapolated)',
																	style=wx.TE_MULTILINE)

		sz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Camera Length:')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.SetItemMinSize(self.pslc, self.pslc.getBestSize())
		sz.Add(self.pslc, (1, 0), (3, 1), wx.EXPAND)

		label = wx.StaticText(self, -1, 'Comment:')
		sz.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.tccomment, (5, 0), (2, 1), wx.EXPAND)

		sz.AddGrowableRow(0)
		sz.AddGrowableRow(1)
		sz.AddGrowableCol(0)

		sbsz.Add(sz, 1, wx.EXPAND|wx.ALL, 5)

		self.bextrapolate = wx.Button(self, -1, 'Calculate Selected')
		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bsave.Enable(False)
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bextrapolate, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bsave, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcancel, (0, 2), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sz.AddGrowableRow(0)
		self.sz.AddGrowableCol(0)
		self.SetSizerAndFit(self.sz)

		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)

	def onExtrapolateButton(self, evt):
		selected = self.pslc.getCameraLengths(wx.LIST_STATE_SELECTED)
		if not selected:
			dialog = wx.MessageDialog(self,
										'Please select one or more camera lengths for extrapolation',
										'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		comment = self.tccomment.GetValue()
		camera_lengths = self.node.extrapolate(self.fromps, selected)
		for m, p, c in camera_lengths:
			self.pslc.addCameraLength(m, p, comment)

		self.bsave.Enable(True)

class EditDialog(wx.Dialog):
	def __init__(self, parent, mag, ps, comment):
		wx.Dialog.__init__(self, parent, -1, 'Edit Camera Length')
		sb = wx.StaticBox(self, -1, 'Camer Length')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.stmag = wx.StaticText(self, -1)
		self.stmag.SetLabel(str(mag))
		self.feps = FloatEntry(self, -1, min=0.0, chars=9)
		self.feps.SetValue(ps)
		self.tccomment = wx.TextCtrl(self, -1, 'Manual entry',
																	style=wx.TE_MULTILINE)
		self.tccomment.SetValue(comment)

		szedit = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Magnification:')
		szedit.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stmag, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Camera length:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.feps, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'm')
		szedit.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szedit.Add(label, (2, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.tccomment, (3, 0), (1, 3), wx.EXPAND)

		szedit.AddGrowableRow(3)
		szedit.AddGrowableRow(0)
		szedit.AddGrowableCol(0)
		szedit.AddGrowableCol(1)
		szedit.AddGrowableCol(2)

		sbsz.Add(szedit, 1, wx.EXPAND|wx.ALL, 5)

		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		if ps is None:
			self.bsave.Enable(False)
		else:
			self.bsave.Enable(True)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bsave, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.validate, self.bsave)
		self.Bind(leginon.gui.wx.Entry.EVT_ENTRY, self.onCameraLengthEntry, self.feps)

	def onCameraLengthEntry(self, evt):
		if evt.GetValue() is None:
			self.bsave.Enable(False)
		else:
			self.bsave.Enable(True)

	def validate(self, evt):
		self.mag = int(self.stmag.GetLabel())
		self.ps = self.feps.GetValue()
		if None in [self.mag, self.ps]:
			dialog = wx.MessageDialog(self, 'Camera length entry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

class CameraLengthListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, size=wx.Size(200,100),
													style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
		ListCtrlAutoWidthMixin.__init__(self)
		self.InsertColumn(0, 'Magnification', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(1, 'Camera length', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(2, 'Comment')

	def getBestSize(self):
		count = self.GetColumnCount()
		width = sum(map(lambda i: self.GetColumnWidth(i), range(count)))
		height = self.GetSize().height * 3 
		return width, height

	def addCameraLength(self, mag, ps, comment):
		'''
		This adds camera_length (mag,ps,comment) to the CtrlList.  It replaces
		existing values if mag value coincides with existing one.
		'''
		mag = int(mag)
		if ps is None:
			psstr = ''
		else:
			psstr = '%g' % ps
		commentstr = str(comment)
		index = 0
		for i in range(self.GetItemCount()):
			item = self.GetItem(i)
			imag = int(item.GetText())
			if mag < imag:
				index = i
				break
			elif mag == imag:
				self.SetStringItem(i, 1, psstr)
				self.SetStringItem(i, 2, commentstr)
				return
		self.InsertStringItem(index, str(mag))
		self.SetStringItem(index, 1, psstr)
		self.SetStringItem(index, 2, commentstr)
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(1, wx.LIST_AUTOSIZE)

	def getCameraLengths(self, state=None):
		selected = []
		for i in range(self.GetItemCount()):
			if state is not None and not self.GetItemState(i, state):
				continue
			mag = int(self.GetItem(i, 0).GetText())
			text = self.GetItem(i, 1).GetText()
			try:
				ps = float(text)
			except ValueError:
				ps = None
			comment = self.GetItem(i, 2).GetText()
			selected.append((mag, ps, comment))
		return selected

class CameraLengthCalibrationDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Camera Length Calibration',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		sb = wx.StaticBox(self, -1, 'Camera Length')
		sbszps = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.measurement = parent.measurement
		self.mag, self.mags = self.node.getMagnification()

		self.lccamera_length = CameraLengthListCtrl(self, -1)
		self.setLocalCameraLengths(self.node.getCalibrations())
		for ps in self.camera_lengths:
			mag, ps, comment = ps
			self.lccamera_length.addCameraLength(mag, ps, comment)
		self.lccamera_length.SetColumnWidth(0, 100)
		self.lccamera_length.SetColumnWidth(2, 120)

		self.bedit = wx.Button(self, -1, 'Edit...')
		self.bextrapolate = wx.Button(self, -1, 'Extrapolate From Selected...')
		if self.camera_lengths is None:
			self.bedit.Enable(False)
			self.bextrapolate.Enable(False)

		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		szps = wx.GridBagSizer(5, 5)
		szps.Add(self.lccamera_length, (0, 0), (2, 3),wx.EXPAND )
		szpsopt = wx.GridBagSizer(5, 5)
		szpsopt.Add(self.bedit, (0, 0), (1, 1), wx.ALIGN_LEFT)
		szpsopt.Add(self.bextrapolate, (0, 1), (1, 2), wx.ALIGN_CENTER)
		szps.Add(szpsopt, (2, 0), (1, 1), wx.EXPAND)
		szps.AddGrowableRow(0)
		szps.AddGrowableCol(0)

		sbszps.Add(szps, 1, wx.EXPAND|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszps, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(self.bdone, (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onEditButton, self.bedit)
		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)

	def setLocalCameraLengths(self, camera_lengths):
		self.camera_lengths = camera_lengths
		self.camera_lengths.sort()
		self.camera_lengths.reverse()

	def onEditButton(self, evt):
		selected = self.lccamera_length.getCameraLengths(wx.LIST_STATE_SELECTED)
		if len(selected) > 1:
			dialog = wx.MessageDialog(self, 'Please select one magnification to edit',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		elif len(selected) < 1:
			dialog = wx.MessageDialog(self, 'No magnifications selected',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		args = selected[0]

		dialog = EditDialog(self, *args)
		if dialog.ShowModal() == wx.ID_OK:
			mag = dialog.mag
			ps = dialog.ps
			comment = dialog.tccomment.GetValue()
			self.node._store(mag, ps, comment)
			self.lccamera_length.addCameraLength(mag, ps, comment)
			# refresh values read by the ExtrapolateDialog
			self.setLocalCameraLengths(self.lccamera_length.getCameraLengths())
		dialog.Destroy()

	def onExtrapolateButton(self, evt):
		selected = self.lccamera_length.getCameraLengths(wx.LIST_STATE_SELECTED)
		if not selected:
			dialog = wx.MessageDialog(self, 'No magnifications selected',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		dialog = ExtrapolateDialog(self, selected, self.camera_lengths)
		if dialog.ShowModal() == wx.ID_OK:
			extrapolated = dialog.pslc.getCameraLengths()
			mags = map(lambda (m, p, c): m, self.camera_lengths)
			for camera_length in dialog.pslc.getCameraLengths():
				# refresh values in CameraLengthCalibrationDialog
				self.lccamera_length.addCameraLength(*camera_length)
				if camera_length not in self.camera_lengths:
					self.node._store(*camera_length)
			# refresh values read by the gui
			self.setLocalCameraLengths(extrapolated)
		dialog.Destroy()

class MeasurementListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT)
		self.InsertColumn(0, 'Camera Length (m)')

		self.itemDataMap = {}
		ListCtrlAutoWidthMixin.__init__(self)

	def getBestSize(self):
		count = self.GetColumnCount()
		width = sum(map(lambda i: self.GetColumnWidth(i), range(count)))
		height = self.GetSize().height * 3
		return width, height

	def addMeasurement(self, camera_length):
		index = self.GetItemCount()
		self.InsertStringItem(index, '%e' % camera_length) 
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

	def getMeasurements(self, state=None):
		selected = []
		for i in range(self.GetItemCount()):
			if state is not None and not self.GetItemState(i, state):
				continue
			camera_length = float(self.GetItem(i, 0).GetText())
			selected.append(camera_length)
		return selected

	def GetListCtrl(self):
		return self

	def setMeasurements(self, measurements):
		self.DeleteAllItems()
		self.itemDataMap = {}
		measurements.reverse()
		for i, measurement in enumerate(measurements):
			camera_length = measurement['camera_length']
			index = self.InsertStringItem(0, camera_length)
			self.SetItemData(index, i)
			self.itemDataMap[i] = (camera_length)
		measurements.reverse()
		if len(measurements) == 0:
			self.SetColumnWidth(0, wx.FIXED_MINSIZE)
		else:
			self.SetColumnWidth(0, wx.LIST_AUTOSIZE)


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Camera Length Calibration Test')
			panel = wx.Panel(frame, -1)
			frame.node = None
			dialog = MeasureSettingsDialog(frame, 'test')
			frame.Fit()
			self.SetTopWindow(frame)
			dialog.Show(True)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

