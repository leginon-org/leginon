# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/Corrector.py,v $
# $Revision: 1.33 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-25 19:03:49 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
from gui.wx.Entry import IntEntry, FloatEntry
import gui.wx.Node
import gui.wx.ImageViewer
import gui.wx.Settings
import threading
import gui.wx.Stats
import gui.wx.Events
import gui.wx.ToolBar

def plan2str(plan):
	if not plan:
		return ''
	splan = []
	for i in plan:
		if i not in splan:
			splan.append(i)
	splan.sort()
	j = 0
	start = stop = -1
	ranges = []
	string = ''
	i = -1
	for i in range(len(splan) - 1):
		if splan[i] + 1 == splan[i + 1]:
			if j == 0:
				start = splan[i]
			else:
				stop = splan[i + 1]
			j += 1
		else:
			if j > 1:
				string += '%d-%d, ' % (start, stop)
				ranges.append((start, stop))
			elif j > 0:
				string += '%d, %d, ' % (splan[i-1], splan[i])
			else:
				string += '%d, ' % (splan[i],)
			j = 0
	if j > 1:
		string += '%d-%d, ' % (start, stop)
	elif j > 0:
		string += '%d, %d, ' % (splan[i], splan[i+1])
	else:
		string += '%d, ' % (splan[i+1],)

	return string[:-2]

def str2plan(string):
	strings = string.split(',')
	plan = []
	for s in strings:
		try:
			toks = map(lambda s: int(s.strip()), s.split('-'))
			if len(toks) > 2:
				continue
			elif len(toks) == 2:
				toks = range(toks[0], toks[1] + 1)
			for t in toks:
				if t not in plan:
					plan.append(t)
		except ValueError:
			raise ValueError
	plan.sort()
	return plan

class Panel(gui.wx.Node.Panel):
	icon = 'corrector'
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1)

		self.toolbar.AddTool(gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		choices = [
			'Dark reference',
			'Bright reference',
			'Raw image',
			'Corrected image'
		]
		self.cacqtype = wx.Choice(self.toolbar, -1, choices=choices)
		self.cacqtype.SetSelection(0)
		self.toolbar.AddControl(self.cacqtype)
		self.toolbar.AddTool(gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire')
		self.toolbar.Realize()

		# settings
		self.szplan = self._getStaticBoxSizer('Plan', (0, 0), (1, 1), wx.ALIGN_TOP)

		self.stbadrows = wx.StaticText(self, -1)
		self.stbadcolumns = wx.StaticText(self, -1)
		self.beditplan = wx.Button(self, -1, 'Edit...')

		label = wx.StaticText(self, -1, 'Bad rows:')
		self.szplan.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szplan.Add(self.stbadrows, (0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		label = wx.StaticText(self, -1, 'Bad columns:')
		self.szplan.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szplan.Add(self.stbadcolumns, (1, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.szplan.AddGrowableCol(1)
		self.szplan.Add(self.beditplan, (2, 1), (1, 2),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		# image
		self.imagepanel = gui.wx.ImageViewer.ImagePanel(self, -1)
		self.szmain.Add(self.imagepanel, (0, 1), (2, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=gui.wx.ToolBar.ID_ACQUIRE)

		self.dialog = SettingsDialog(self)

		self.node.getPlan()
		self.setPlan(self.node.plan)

		self.Bind(wx.EVT_BUTTON, self.onEditPlan, self.beditplan)

	def onSetImage(self, evt):
		gui.wx.Node.Panel.onSetImage(self, evt)

	def onSettingsTool(self, evt):
		self.dialog.ShowModal()
		self.node.getPlan()
		self.setPlan(self.node.plan)

	def _acquisitionEnable(self, enable):
		self.beditplan.Enable(enable)
		self.toolbar.Enable(enable)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		acqtype = self.cacqtype.GetStringSelection()
		if acqtype == 'Dark reference':
			method = self.node.acquireDark
		elif acqtype == 'Bright reference':
			method = self.node.acquireBright
		elif acqtype == 'Raw image':
			method = self.node.acquireRaw
		elif acqtype == 'Corrected image':
			method = self.node.acquireCorrected
		threading.Thread(target=method).start()	

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def setPlan(self, plan):
		if plan is None:
			self.stbadrows.SetLabel('')
			self.stbadcolumns.SetLabel('')
		else:
			self.stbadrows.SetLabel(plan2str(plan['rows']))
			self.stbadcolumns.SetLabel(plan2str(plan['columns']))
		self.plan = plan

	def onEditPlan(self, evt):
		dialog = EditPlanDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.setPlan(dialog.plan)
			self.node.plan = self.plan
			self.node.setPlan()
		dialog.Destroy()

class SettingsDialog(gui.wx.Settings.Dialog):
	def initialize(self):
		gui.wx.Settings.Dialog.initialize(self)

		self.widgets['n average'] = IntEntry(self, -1, min=1, max=99, chars=2)
		self.widgets['camera settings'] = gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)
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

		return [sbsz]

class EditPlanDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent.GetParent(), -1, 'Edit Plan')
		self.parent = parent

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
			rows = str2plan(self.tcrows.GetValue())
			columns = str2plan(self.tccolumns.GetValue())
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

