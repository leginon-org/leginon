# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
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
		dialog = ImageRotationCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class EditDialog(wx.Dialog):
	def __init__(self, parent, mag, ps, comment):
		wx.Dialog.__init__(self, parent, -1, 'Edit Image Rotation')
		sb = wx.StaticBox(self, -1, 'Image Rotation')
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

		label = wx.StaticText(self, -1, 'Rotation:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.feps, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degrees')
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
		self.Bind(leginon.gui.wx.Entry.EVT_ENTRY, self.onImageRotationEntry, self.feps)

	def onImageRotationEntry(self, evt):
		if evt.GetValue() is None:
			self.bsave.Enable(False)
		else:
			self.bsave.Enable(True)

	def validate(self, evt):
		self.mag = int(self.stmag.GetLabel())
		self.ps = self.feps.GetValue()
		if None in [self.mag, self.ps]:
			dialog = wx.MessageDialog(self, 'Rotation entry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

class ImageRotationListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, size=wx.Size(200,100),
													style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
		ListCtrlAutoWidthMixin.__init__(self)
		self.InsertColumn(0, 'Magnification', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(1, 'Image Rotation (degrees)', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(2, 'Comment')

	def getBestSize(self):
		count = self.GetColumnCount()
		width = sum(map(lambda i: self.GetColumnWidth(i), range(count)))
		height = self.GetSize().height * 3 
		return width, height

	def addImageRotation(self, mag, ps, comment):
		'''
		This adds image_rotation (mag,ps,comment) to the CtrlList.  It replaces
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

	def getImageRotations(self, state=None):
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

class ImageRotationCalibrationDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Image Rotation Calibration',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
		sb = wx.StaticBox(self, -1, 'Rotation')
		sbszps = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.mag, self.mags = self.node.getMagnification()

		self.lcimage_rotation = ImageRotationListCtrl(self, -1)
		radian_rotations = self.node.getCalibrations()
		degree_rotations = map((lambda x: (x[0],math.degrees(float(x[1])),x[2])),radian_rotations)
		self.setLocalImageRotations(degree_rotations)
		for info in self.image_rotations:
			mag, angle, comment = info
			self.lcimage_rotation.addImageRotation(mag, angle, comment)
		self.lcimage_rotation.SetColumnWidth(0, 100)
		self.lcimage_rotation.SetColumnWidth(2, 120)

		self.bedit = wx.Button(self, -1, 'Edit...')
		if self.image_rotations is None:
			self.bedit.Enable(False)

		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		szps = wx.GridBagSizer(5, 5)
		szps.Add(self.lcimage_rotation, (0, 0), (2, 3),wx.EXPAND )
		szpsopt = wx.GridBagSizer(5, 5)
		szpsopt.Add(self.bedit, (0, 0), (1, 1), wx.ALIGN_LEFT)
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

	def setLocalImageRotations(self, image_rotations):
		self.image_rotations = image_rotations
		self.image_rotations.sort()
		self.image_rotations.reverse()

	def onEditButton(self, evt):
		selected = self.lcimage_rotation.getImageRotations(wx.LIST_STATE_SELECTED)
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
			rotation = dialog.ps
			comment = dialog.tccomment.GetValue()
			radian_rotation = math.radians(rotation)
			self.node._store(mag, radian_rotation, comment)
			self.lcimage_rotation.addImageRotation(mag, rotation, comment)
			# refresh values 
			self.setLocalImageRotations(self.lcimage_rotation.getImageRotations())
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

