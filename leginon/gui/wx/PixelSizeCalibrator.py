# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/PixelSizeCalibrator.py,v $
# $Revision: 1.12 $
# $Name: not supported by cvs2svn $
# $Date: 2004-11-03 21:22:51 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.ImageViewer
import gui.wx.ToolBar

class Panel(gui.wx.Calibrator.Panel):
	icon = 'pixelsize'
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)

		self.toolbar.Realize()
		self.toolbar.DeleteTool(gui.wx.ToolBar.ID_ABORT)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)
		self.measurement = None
		self.Bind(gui.wx.ImageViewer.EVT_MEASUREMENT, self.onMeasurement)

	def onMeasurement(self, evt):
		self.measurement = evt.measurement

	def onCalibrateTool(self, evt):
		dialog = PixelSizeCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class ExtrapolateDialog(wx.Dialog):
	def __init__(self, parent, frommags, mags):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Extrapolate Pixel Size')

		self.mags = frommags
		strmags = str(frommags)[1:-1]
		self.stmags = wx.StaticText(self, -1, strmags)
		self.cmag = wx.Choice(self, -1, choices=map(str, mags))
		self.cmag.SetSelection(0)
		self.stps = wx.StaticText(self, -1, '')
		self.tccomment = wx.TextCtrl(self, -1, 'Extrapolated from %s' % (strmags,),
																	style=wx.TE_MULTILINE)

		szedit = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'From:')
		szedit.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stmags, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Magnification:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.cmag, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Pixel size:')
		szedit.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stps, (2, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm/pixel')
		szedit.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szedit.Add(label, (3, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.tccomment, (4, 0), (1, 3), wx.EXPAND)

		szedit.AddGrowableRow(3)
		szedit.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Extrapolate')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(szedit, 1, wx.EXPAND|wx.ALL, 5)

		self.bextrapolate = wx.Button(self, -1, 'Extrapolate')
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
		self.SetSizerAndFit(self.sz)

		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)

	def onExtrapolateButton(self, evt):
		mag = float(self.cmag.GetStringSelection())
		if mag is None:
			dialog = wx.MessageDialog(self, 'No magnification entered',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.mag = mag
		self.ps = self.node.extrapolate(self.mags, mag)
		self.stps.SetLabel(str(self.ps))
		self.sz.Layout()

		self.bsave.Enable(True)

class EditDialog(wx.Dialog):
	def __init__(self, parent, mag, ps, comment):
		wx.Dialog.__init__(self, parent, -1, 'Edit Pixel Size')

		#self.cmag = wx.Choice(self, -1, choices=map(str, mags))
		#self.cmag.SetSelection(0)
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
		#szedit.Add(self.cmag, (0, 1), (1, 1),
		#						wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szedit.Add(self.stmag, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Pixel size:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.feps, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'm/pixel')
		szedit.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szedit.Add(label, (2, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.tccomment, (3, 0), (1, 3), wx.EXPAND)

		szedit.AddGrowableRow(3)
		szedit.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Pixel Size')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
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
		self.Bind(gui.wx.Entry.EVT_ENTRY, self.onPixelSizeEntry, self.feps)

	def onPixelSizeEntry(self, evt):
		if evt.GetValue() is None:
			self.bsave.Enable(False)
		else:
			self.bsave.Enable(True)

	def validate(self, evt):
		#self.mag = float(self.cmag.GetStringSelection())
		self.mag = float(self.stmag.GetLabel())
		self.ps = self.feps.GetValue()
		if None in [self.mag, self.ps]:
			dialog = wx.MessageDialog(self, 'Pixel size entry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

class MeasureDialog(wx.Dialog):
	def __init__(self, parent, mag, bin):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Measure Pixel Size')

		self.pixeldistance = parent.measurement['magnitude']

		self.stmag = wx.StaticText(self, -1, str(mag))
		self.stpd = wx.StaticText(self, -1, str(self.pixeldistance))
		self.stbinning = wx.StaticText(self, -1, str(bin))
		self.stps = wx.StaticText(self, -1, '')
		self.fedistance = FloatEntry(self, -1, chars=6)
		self.tccomment = wx.TextCtrl(self, -1, 'Measured',
																	style=wx.TE_MULTILINE)

		szedit = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Magnification:')
		szedit.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stmag, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Measured distance:')
		szedit.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stpd, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'pixels')
		szedit.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Binning:')
		szedit.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stbinning, (2, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Distance:')
		szedit.Add(label, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.fedistance, (3, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm')
		szedit.Add(label, (3, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Pixel size:')
		szedit.Add(label, (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.stps, (4, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm/pixel')
		szedit.Add(label, (4, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szedit.Add(label, (5, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szedit.Add(self.tccomment, (6, 0), (1, 3), wx.EXPAND)

		szedit.AddGrowableRow(3)
		szedit.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Measure')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(szedit, 1, wx.EXPAND|wx.ALL, 5)

		self.bmeasure = wx.Button(self, -1, 'Calculate')
		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bsave.Enable(False)
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bmeasure, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.Add(self.bsave, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(self.bcancel, (0, 2), (1, 1), wx.ALIGN_CENTER)
		szbutton.AddGrowableCol(0)

		self.sz = wx.GridBagSizer(5, 5)
		self.sz.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.SetSizerAndFit(self.sz)

		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.bmeasure)

	def onMeasureButton(self, evt):
		distance = self.fedistance.GetValue()
		if distance is None:
			dialog = wx.MessageDialog(self, 'No distance entered',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return
		else:
			evt.Skip()

		self.ps = self.node.calculateMeasured(self.pixeldistance, distance)
		self.stps.SetLabel(str(self.ps))
		self.sz.Layout()

		self.bsave.Enable(True)

class PixelSizeListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id,
													style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES)
		ListCtrlAutoWidthMixin.__init__(self)
		self.InsertColumn(0, 'Magnification', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(1, 'Pixel size', wx.LIST_FORMAT_RIGHT)
		self.InsertColumn(2, 'Comment')

	def addPixelSize(self, mag, ps, comment):
		mag = float(mag)
		if ps is None:
			psstr = ''
		else:
			psstr = '%g' % ps
		commentstr = str(comment)
		index = 0
		for i in range(self.GetItemCount()):
			item = self.GetItem(i)
			imag = float(item.GetText())
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

	def getSelected(self):
		selected = []
		for i in range(self.GetItemCount()):
			if self.GetItemState(i, wx.LIST_STATE_SELECTED):
				mag = float(self.GetItem(i, 0).GetText())
				text = self.GetItem(i, 1).GetText()
				try:
					ps = float(text)
				except ValueError:
					ps = None
				comment = self.GetItem(i, 2).GetText()
				selected.append((mag, ps, comment))
		return selected

class PixelSizeCalibrationDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Pixel Size Calibration',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		self.measurement = parent.measurement
		self.mag, self.mags = self.node.getMagnification()

		self.lcpixelsize = PixelSizeListCtrl(self, -1)
		cals = self.node.getCalibrations()
		cals.sort()
		cals.reverse()
		for ps in cals:
			mag, ps, comment = ps
			self.lcpixelsize.addPixelSize(mag, ps, comment)

		self.bedit = wx.Button(self, -1, 'Edit...')
		self.bextrapolate = wx.Button(self, -1, 'Extrapolate...')
		if self.mags is None:
			self.bedit.Enable(False)
			self.bextrapolate.Enable(False)

		self.bmeasure = wx.Button(self, -1, 'Measure...')
		if None in [self.node.mag, self.node.bin, self.measurement]:
			self.bmeasure.Enable(False)

		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		szps = wx.GridBagSizer(5, 5)
		szps.Add(self.lcpixelsize, (0, 0), (1, 3), wx.EXPAND)

		count = self.lcpixelsize.GetColumnCount()
		width = sum(map(lambda i: self.lcpixelsize.GetColumnWidth(i), range(count)))
		height = self.lcpixelsize.GetSize().height * 3
		szps.SetItemMinSize(self.lcpixelsize, (width, height))

		szps.Add(self.bedit, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szps.Add(self.bextrapolate, (1, 1), (1, 1), wx.ALIGN_CENTER)
		szps.Add(self.bmeasure, (1, 2), (1, 1), wx.ALIGN_CENTER)
		szps.AddGrowableRow(0)
		szps.AddGrowableCol(0)
		szps.AddGrowableCol(1)
		szps.AddGrowableCol(2)

		sb = wx.StaticBox(self, -1, 'Pixel Size')
		sbszps = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszps.Add(szps, 1, wx.EXPAND|wx.ALL, 5)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.bdone, (0, 0), (1, 1),
									wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		szbutton.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbszps, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onEditButton, self.bedit)
		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.bmeasure)

	def onEditButton(self, evt):
		selected = self.lcpixelsize.getSelected()
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
			self.lcpixelsize.addPixelSize(mag, ps, comment)
		dialog.Destroy()

	def onExtrapolateButton(self, evt):
		selected = self.lcpixelsize.getSelected()
		if not selected:
			dialog = wx.MessageDialog(self, 'No magnifications selected',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		mags = map(lambda (m, p, c): m, selected)
		dialog = ExtrapolateDialog(self, mags, self.mags)
		if dialog.ShowModal() == wx.ID_OK:
			mag = dialog.mag
			ps = dialog.ps
			comment = dialog.tccomment.GetValue()
			self.node._store(mag, ps, comment)
			self.lcpixelsize.addPixelSize(mag, ps, comment)
		dialog.Destroy()

	def onMeasureButton(self, evt):
		mag = self.node.mag
		bin = self.node.bin
		dialog = MeasureDialog(self, mag, bin)
		if dialog.ShowModal() == wx.ID_OK:
			ps = dialog.ps
			comment = dialog.tccomment.GetValue()
			self.node._store(mag, ps, comment)
			self.lcpixelsize.addPixelSize(mag, ps, comment)
		dialog.Destroy()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Pixel Size Calibration Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

