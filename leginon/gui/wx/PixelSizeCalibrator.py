# -*- coding: iso-8859-1 -*-
import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Calibrator
import gui.wx.Settings

class Panel(gui.wx.Calibrator.Panel):
	def initialize(self):
		gui.wx.Calibrator.Panel.initialize(self)
		# for testing
		self.Bind(wx.EVT_BUTTON, self.onCalibrateButton, self.bcalibrate)

	def onNodeInitialized(self):
		gui.wx.Calibrator.Panel.onNodeInitialized(self)

	def onCalibrateButton(self, evt):
		dialog = PixelSizeCalibrationDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onAbortButton(self, evt):
		raise NotImplementedError

class ExtrapolateDialog(wx.Dialog):
	def __init__(self, parent, mags):
		wx.Dialog.__init__(self, parent, -1, 'Extrapolate Pixel Size')

		self.stmags = wx.StaticText(self, -1, str(mags)[1:-1])
		self.femag = FloatEntry(self, -1, chars=6)
		self.stps = wx.StaticText(self, -1, '')
		self.tccomment = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)

		szenter = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'From:')
		szenter.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.stmags, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		label = wx.StaticText(self, -1, 'Magnification:')
		szenter.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.femag, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Pixel size:')
		szenter.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.stps, (2, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		label = wx.StaticText(self, -1, 'm/pixel')
		szenter.Add(label, (2, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szenter.Add(label, (3, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.tccomment, (4, 0), (1, 3), wx.EXPAND)

		szenter.AddGrowableRow(3)
		szenter.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Entry')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(szenter, 1, wx.EXPAND|wx.ALL, 5)

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

		sz = wx.GridBagSizer(5, 5)
		sz.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sz.Add(szbutton, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)

	def onExtrapolateButton(self, evt):
		mag = self.femag.GetValue()
		if mag is None:
			dialog = wx.MessageDialog(self, 'No magnification entered',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
			return

		self.bsave.Enable(True)

class EnterDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Enter Pixel Size')

		self.femag = FloatEntry(self, -1, chars=6)
		self.feps = FloatEntry(self, -1, chars=6)
		self.tccomment = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)

		szenter = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Magnification:')
		szenter.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.femag, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Pixel size:')
		szenter.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.feps, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'm/pixel')
		szenter.Add(label, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Comment:')
		szenter.Add(label, (2, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		szenter.Add(self.tccomment, (3, 0), (1, 3), wx.EXPAND)

		szenter.AddGrowableRow(3)
		szenter.AddGrowableCol(1)

		sb = wx.StaticBox(self, -1, 'Entry')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(szenter, 1, wx.EXPAND|wx.ALL, 5)

		self.bsave = wx.Button(self, wx.ID_OK, 'Save')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

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

	def validate(self, evt):
		mag = self.femag.GetValue()
		ps = self.feps.GetValue()
		if None in [mag, ps]:
			dialog = wx.MessageDialog(self, 'Pixel size entry',
																'Error', wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			evt.Skip()

class MeasureDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Measure Pixel Size')

class PixelSizeListCtrl(wx.ListCtrl):
	def __init__(self, parent, id):
		wx.ListCtrl.__init__(self, parent, id, style=wx.LC_REPORT)
		self.InsertColumn(0, 'Magnification')
		self.InsertColumn(1, 'Pixel size')
		self.InsertColumn(2, 'Comment')

	def addPixelSize(self, mag, ps, comment):
		index = 0
		for i in range(self.GetItemCount()):
			item = self.GetItem(i)
			imag = float(item.GetText())
			if mag < imag:
				index = i
				break
			elif mag == imag:
				self.SetStringItem(i, 1, str(ps))
				self.SetStringItem(i, 2, str(comment))
				return
		self.InsertStringItem(index, str(mag))
		self.SetStringItem(index, 1, str(ps))
		self.SetStringItem(index, 2, str(comment))

class PixelSizeCalibrationDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Pixel Size Calibration')

		self.lcpixelsize = PixelSizeListCtrl(self, -1)

		self.benter = wx.Button(self, -1, 'Enter...')
		self.bextrapolate = wx.Button(self, -1, 'Extrapolate...')
		self.bmeasure = wx.Button(self, -1, 'Measure...')

		self.bdone = wx.Button(self, wx.ID_OK, 'Done')

		szps = wx.GridBagSizer(5, 5)
		szps.Add(self.lcpixelsize, (0, 0), (1, 3), wx.EXPAND)
		szps.Add(self.benter, (1, 0), (1, 1), wx.ALIGN_CENTER)
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

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onEnterButton, self.benter)
		self.Bind(wx.EVT_BUTTON, self.onExtrapolateButton, self.bextrapolate)
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.bmeasure)

	def onEnterButton(self, evt):
		dialog = EnterDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

	def onExtrapolateButton(self, evt):
		#dialog = ExtrapolateDialog(self, mags)
		dialog = ExtrapolateDialog(self, [1.0, 100.0])
		dialog.ShowModal()
		dialog.Destroy()

	def onMeasureButton(self, evt):
		dialog = MeasureDialog(self)
		dialog.ShowModal()
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

