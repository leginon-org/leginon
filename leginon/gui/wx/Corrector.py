import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Data
import gui.wx.Node
import gui.wx.ImageViewer
import gui.wx.Settings
import threading

AcquisitionDoneEventType = wx.NewEventType()
EVT_ACQUISITION_DONE = wx.PyEventBinder(AcquisitionDoneEventType)
class AcquisitionDoneEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(AcquisitionDoneEventType)

class Panel(gui.wx.Node.Panel):
	icon = 'corrector'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1, name='%s.pCorrector' % name)

		self.szmain = wx.GridBagSizer(5, 5)

		# status
		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 2),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		# statistics
		self.szstats = self._getStaticBoxSizer('Statistics', (1, 0), (1, 1),
																						wx.EXPAND|wx.ALL)
		stlmean = wx.StaticText(self, -1, 'Mean:')
		stlmin = wx.StaticText(self, -1, 'Minimum:')
		stlmax = wx.StaticText(self, -1, 'Maximum:')
		stlsigma = wx.StaticText(self, -1, 'Std. Dev.:')

		self.stvmean = wx.StaticText(self, -1, '')
		self.stvmin = wx.StaticText(self, -1, '')
		self.stvmax = wx.StaticText(self, -1, '')
		self.stvsigma = wx.StaticText(self, -1, '')

		self.szstats.Add(stlmean, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstats.Add(self.stvmean, (0, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szstats.Add(stlmin, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstats.Add(self.stvmin, (1, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szstats.Add(stlmax, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstats.Add(self.stvmax, (2, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szstats.Add(stlsigma, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szstats.Add(self.stvsigma, (3, 1), (1, 1),
											wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		self.szstats.AddGrowableCol(1)

		# settings
		self.szplan = self._getStaticBoxSizer('Plan', (2, 0), (1, 1),
																							wx.EXPAND|wx.ALL)

		label = wx.StaticText(self, -1, 'Bad rows:')
		self.szplan.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.stbadrows = wx.StaticText(self, -1)
		self.szplan.Add(self.stbadrows, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Bad columns:')
		self.szplan.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.stbadcolumns = wx.StaticText(self, -1)
		self.szplan.Add(self.stbadcolumns, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.szplan.AddGrowableCol(1)

		self.beditplan = wx.Button(self, -1, 'Edit...')
		self.szplan.Add(self.beditplan, (2, 1), (1, 2),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.bsettings = wx.Button(self, -1, 'Settings...')
		self.szbuttons = wx.GridBagSizer(5, 5)
		self.szbuttons.Add(self.bsettings, (0, 0), (1, 1), wx.ALIGN_CENTER)
		self.szmain.Add(self.szbuttons, (3, 0), (1, 1), wx.ALIGN_CENTER)

		# controls
		self.szcontrols = self._getStaticBoxSizer('Controls', (4, 0), (1, 1),
																wx.EXPAND|wx.ALL)
		szrb = wx.GridBagSizer(0, 0)
		self.rbdark = wx.RadioButton(self, -1, 'Dark reference', style=wx.RB_GROUP)
		self.rbbright = wx.RadioButton(self, -1, 'Bright reference')
		self.rbraw = wx.RadioButton(self, -1, 'Raw image')
		self.rbcorrected = wx.RadioButton(self, -1, 'Corrected image')
		szrb.Add(self.rbdark, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szrb.Add(self.rbbright, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szrb.Add(self.rbraw, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szrb.Add(self.rbcorrected, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szcontrols.Add(szrb, (0, 0), (1, 1), wx.ALIGN_CENTER)

		self.bacquire = wx.Button(self, -1, 'Acquire')
		self.szcontrols.Add(self.bacquire, (1, 0), (1, 1), wx.ALIGN_CENTER)
		self.szcontrols.AddGrowableRow(0)
		self.szcontrols.AddGrowableRow(1)
		self.szcontrols.AddGrowableCol(0)

		# image
		self.szimage = self._getStaticBoxSizer('Image', (1, 1), (5, 1),
																						wx.EXPAND|wx.ALL)
		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
		self.szimage.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND|wx.ALL)
		self.szimage.AddGrowableRow(0)
		self.szimage.AddGrowableCol(0)

		self.szmain.AddGrowableRow(4)
		self.szmain.AddGrowableCol(1)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.node.getPlan()
		self.setPlan(self.node.plan)
		self.Bind(EVT_ACQUISITION_DONE, self.onAcquisitionDone)
		self.Bind(wx.EVT_BUTTON, self.onSettingsButton, self.bsettings)
		self.Bind(wx.EVT_BUTTON, self.onEditPlan, self.beditplan)
		self.Bind(wx.EVT_BUTTON, self.onAcquire, self.bacquire)

	def onSetImage(self, evt):
		gui.wx.Node.Panel.onSetImage(self, evt)
		if 'mean' in evt.statistics:
			self.stvmean.SetLabel(str(evt.statistics['mean']))
		if 'min' in evt.statistics:
			self.stvmin.SetLabel(str(evt.statistics['min']))
		if 'max' in evt.statistics:
			self.stvmax.SetLabel(str(evt.statistics['max']))
		if 'stdev' in evt.statistics:
			self.stvsigma.SetLabel(str(evt.statistics['stdev']))
		#if self.IsShown():
		#	self.szmain.Layout()
		#	self.GetParent().Layout()

	def onSettingsButton(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()
		self.node.getPlan()
		self.setPlan(self.node.plan)

	def onAcquire(self, evt):
		self.Enable(False)
		if self.rbdark.GetValue():
			method = self.node.acquireDark
		elif self.rbbright.GetValue():
			method = self.node.acquireBright
		elif self.rbraw.GetValue():
			method = self.node.acquireRaw
		elif self.rbcorrected.GetValue():
			method = self.node.acquireCorrected
		threading.Thread(target=method).start()	

	def onAcquisitionDone(self, evt):
		self.Enable(True)

	def acquisitionDone(self):
		evt = AcquisitionDoneEvent()
		self.GetEventHandler().AddPendingEvent(evt)

	def setPlan(self, plan):
		self.stbadrows.SetLabel(self.plan2str(plan['rows']))
		self.stbadcolumns.SetLabel(self.plan2str(plan['columns']))
		self.plan = plan

	def onEditPlan(self, evt):
		dialog = EditPlanDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.setPlan(dialog.plan)
			self.node.plan = self.plan
			self.node.setPlan()
		dialog.Destroy()

	def plan2str(self, plan):
		splan = []
		for i in plan:
			if i not in splan:
				splan.append(i)
		splan.sort()
		return str(splan)[1:-1]

	def str2plan(self, string):
		strings = string.split(',')
		plan = []
		for s in strings:
			try:
				s = s.strip()
				if not s:
					continue
				i = int(s)
				if i not in plan:
					plan.append(i)
			except ValueError:
				raise ValueError
		plan.sort()
		return plan

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['n average'] = IntEntry(self, -1, min=1, max=99, chars=2)
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.session)
		self.widgets['despike'] = wx.CheckBox(self, -1, 'Despike images')
		self.widgets['despike size'] = IntEntry(self, -1, min=1, chars=4)
		self.widgets['despike threshold'] = FloatEntry(self, -1, min=1, chars=9)

		szdespike = wx.GridBagSizer(5, 5)
		szdespike.Add(self.widgets['despike'], (0, 0), (1, 2),
									wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Neighborhood size:')
		szdespike.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdespike.Add(self.widgets['despike size'], (1, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Threshold:')
		szdespike.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdespike.Add(self.widgets['despike threshold'], (2, 1), (1, 1),
									wx.ALIGN_CENTER_VERTICAL)
		sb = wx.StaticBox(self, -1, 'Despike')
		sbszdespike = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbszdespike.Add(szdespike, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		sz = wx.GridBagSizer(5, 10)
		label = wx.StaticText(self, -1, 'Images to average:')
		sz.Add(self.widgets['camera settings'], (0, 0), (2, 1), wx.ALIGN_CENTER)
		sz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['n average'], (0, 2), (1, 1),
						wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		sz.Add(sbszdespike, (1, 1), (1, 2), wx.ALIGN_CENTER|wx.EXPAND|wx.ALL)

		sb = wx.StaticBox(self, -1, 'Image Correction')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return sbsz

class EditPlanDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, 'Edit Plan')

		strows = wx.StaticText(self, -1, 'Bad rows:')
		stcolumns = wx.StaticText(self, -1, 'Bad columns:')
		self.tcrows = wx.TextCtrl(self, -1, parent.stbadrows.GetLabel())
		self.tccolumns = wx.TextCtrl(self, -1, parent.stbadcolumns.GetLabel())

		bsave = wx.Button(self, wx.ID_OK, 'Save')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bsave, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		szplan = wx.GridBagSizer(5, 5)
		szplan.Add(strows, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szplan.Add(self.tcrows, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szplan.Add(stcolumns, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szplan.Add(self.tccolumns, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szplan, (0, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)
		sz.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onSave, bsave)

	def onSave(self, evt):
		try:
			rows = self.GetParent().str2plan(self.tcrows.GetValue())
			columns = self.GetParent().str2plan(self.tccolumns.GetValue())
		except ValueError:
			dialog = wx.MessageDialog(self, 'Invalid plan', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.plan = {'rows': rows, 'columns': columns}
			evt.Skip()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Corrector Test')
			panel = Panel(frame, 'Test')
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

