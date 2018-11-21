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

import math

class Panel(leginon.gui.wx.Calibrator.Panel):
	icon = 'pixelsize'
	def initialize(self):
		# image
		self.imagepanel = self.imageclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

	def onNodeInitialized(self):
		leginon.gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.oldmag = None
		self.toolbar.DeleteTool(leginon.gui.wx.ToolBar.ID_ABORT)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onCalibrateTool(self, evt):
		dialog = ScaleRotationCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class EditDialog(wx.Dialog):
	def __init__(self, parent, mag, v1, v2, comment):
		wx.Dialog.__init__(self, parent, -1, 'Edit Scale Rotation')
		sb = wx.StaticBox(self, -1, 'Scale Rotation')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.stmag = wx.StaticText(self, -1)
		self.stmag.SetLabel(str(mag))
		self.fev1 = FloatEntry(self, -1, min=-100.0, max=100.0, chars=5)
		self.fev1.SetValue(v1)
		self.fev2 = FloatEntry(self, -1, min=-360.0, max=360.0, chars=9)
		self.fev2.SetValue(v2)
		self.tccomment = wx.TextCtrl(self, -1, 'Manual entry',
																	style=wx.TE_MULTILINE)
		self.tccomment.SetValue(comment)

		szedit = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Magnification:')
		szedit.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stmag, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Scale Addition:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.fev1, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '%')
		szedit.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Rotation:')
		szedit.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.fev2, (2, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degrees')
		szedit.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szedit.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.tccomment, (3, 1), (1, 3), wx.EXPAND)

		szedit.AddGrowableRow(3)
		szedit.AddGrowableRow(0)
		szedit.AddGrowableCol(0)
		szedit.AddGrowableCol(1)
		szedit.AddGrowableCol(2)
		szedit.AddGrowableCol(3)

		sbsz.Add(szedit, 1, wx.EXPAND|wx.ALL, 5)

		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		if v1 is None:
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
		self.Bind(leginon.gui.wx.Entry.EVT_ENTRY, self.onScaleRotationEntry, self.fev1, self.fev2)

	def onScaleRotationEntry(self, evt):
		if evt.GetValue() is None:
			self.bsave.Enable(False)
		else:
			self.bsave.Enable(True)

	def validate(self, evt):
		self.mag = int(self.stmag.GetLabel())
		self.v1 = self.fev1.GetValue()
		self.v2 = self.fev2.GetValue()
		msg = None
		if None in [self.mag, self.v1, self.v2]:
			msg = 'Must have value'
		if msg:
			dialog = wx.MessageDialog(self, 'Scale Rotation entry',
																msg, wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

class ScaleRotationListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, size=wx.Size(200,100),
													style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
		ListCtrlAutoWidthMixin.__init__(self)
		self.InsertColumn(0, 'Magnification', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(1, 'Scale Addition (%)', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(2, 'Image Rotation (degrees)', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(3, 'Comment')

	def getBestSize(self):
		count = self.GetColumnCount()
		width = sum(map(lambda i: self.GetColumnWidth(i), range(count)))
		height = self.GetSize().height * 3 
		return width, height

	def addScaleRotation(self, mag, v1, v2, comment):
		'''
		This adds image_rotation (mag,v1, v2, comment) to the CtrlList.  It replaces
		existing values if mag value coincides with existing one.
		'''
		mag = int(mag)
		if v1 is None:
			v1str = ''
		else:
			v1str = '%g' % v1
		if v2 is None:
			v2str = ''
		else:
			v2str = '%g' % v2
		commentstr = str(comment)
		index = 0
		for i in range(self.GetItemCount()):
			item = self.GetItem(i)
			imag = int(item.GetText())
			if mag < imag:
				index = i
				break
			elif mag == imag:
				self.SetStringItem(i, 1, v1str)
				self.SetStringItem(i, 2, v2str)
				self.SetStringItem(i, 3, commentstr)
				return
		self.InsertStringItem(index, str(mag))
		self.SetStringItem(index, 1, v1str)
		self.SetStringItem(index, 2, v2str)
		self.SetStringItem(index, 3, commentstr)
		self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(2, wx.LIST_AUTOSIZE)
		self.SetColumnWidth(3, wx.LIST_AUTOSIZE)

	def getScaleRotations(self, state=None):
		selected = []
		for i in range(self.GetItemCount()):
			if state is not None and not self.GetItemState(i, state):
				continue
			mag = int(self.GetItem(i, 0).GetText())
			v1text = self.GetItem(i, 1).GetText()
			v2text = self.GetItem(i, 2).GetText()
			try:
				v1 = float(v1text) # roation
			except ValueError:
				v1 = None
			try:
				v2 = float(v2text) # scale addition
			except ValueError:
				v2 = None
			comment = self.GetItem(i, 3).GetText()
			selected.append((mag, v1, v2, comment))
		return selected

class ScaleRotationCalibrationDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Image Rotation Calibration',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		sb = wx.StaticBox(self, -1, 'Rotation')
		sbszv1 = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.mag, self.mags = self.node.getMagnification()

		self.lcimage = ScaleRotationListCtrl(self, -1)
		scale_rotations = self.node.getCalibrations()
		gui_scale_rotations = map((lambda x: (x[0],float(x[1])*100.0,math.degrees(float(x[2])),x[3])),scale_rotations)
		self.setLocalScaleRotations(gui_scale_rotations)
		for info in self.scale_rotations:
			mag, percent_scale_addition, angle, comment = info
			# These are added as is.  Need to be in percent and degrees
			self.lcimage.addScaleRotation(mag, percent_scale_addition, angle, comment)
		self.lcimage.SetColumnWidth(0, 100)
		self.lcimage.SetColumnWidth(1, 100)
		self.lcimage.SetColumnWidth(2, 100)
		self.lcimage.SetColumnWidth(3, 120)

		self.bedit = wx.Button(self, -1, 'Edit...')
		if self.scale_rotations is None:
			self.bedit.Enable(False)

		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		szv1 = wx.GridBagSizer(5, 5)
		szv1.Add(self.lcimage, (0, 0), (2, 3),wx.EXPAND )
		szv1opt = wx.GridBagSizer(5, 5)
		szv1opt.Add(self.bedit, (0, 0), (1, 1), wx.ALIGN_LEFT)
		szv1.Add(szv1opt, (2, 0), (1, 1), wx.EXPAND)
		szv1.AddGrowableRow(0)
		szv1.AddGrowableCol(0)

		sbszv1.Add(szv1, 1, wx.EXPAND|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszv1, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(self.bdone, (1, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onEditButton, self.bedit)

	def setLocalScaleRotations(self, scale_rotations):
		self.scale_rotations = scale_rotations
		self.scale_rotations.sort()
		self.scale_rotations.reverse()

	def onEditButton(self, evt):
		selected = self.lcimage.getScaleRotations(wx.LIST_STATE_SELECTED)
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
			# store rotation
			scale_addition_percent = dialog.v1
			rotation_degrees = dialog.v2
			comment = dialog.tccomment.GetValue()
			rotation_radians = math.radians(rotation_degrees)
			scale_addition = scale_addition_percent / 100.0
			self.node.store(mag, scale_addition, rotation_radians, comment)
			# These are added as is.  Need to be in percent and degrees
			self.lcimage.addScaleRotation(mag, scale_addition_percent, rotation_degrees, comment)
			# refresh values 
			self.setLocalScaleRotations(self.lcimage.getScaleRotations())
		dialog.Destroy()


if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Image Rotation Calibration Test')
			panel = wx.Panel(frame, -1)
			frame.node = None
			dialog = EditDialog(frame, 'test')
			frame.Fit()
			self.SetTopWindow(frame)
			dialog.Show(True)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

