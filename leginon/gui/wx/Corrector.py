# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/Corrector.py,v $
# $Revision: 1.56 $
# $Name: not supported by cvs2svn $
# $Date: 2008-02-22 22:47:06 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $

import threading
import wx

from leginon.gui.wx.Entry import IntEntry, FloatEntry
import leginon.gui.wx.Node
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.Stats
import leginon.gui.wx.Events
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Instrument
from leginon.gui.wx.Choice import Choice

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
		if not s:
			continue
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

def iscoord(x):
	if not isinstance(x, tuple):
		return False
	if len(x) != 2:
		return False
	for i in x:
		if type(i) is not int:
			return False
	return True

def str2pixels(string):
	pixels = []
	try:
		p = eval(string)
	except:
		return pixels

	# if only one pixel...
	if len(p) == 2 and type(p[0]) is int:
		pixels.append(p)
	else:
		for a in p:
			if iscoord(a):
				pixels.append(a)
	pixels.sort()
	return pixels

def pixels2str(pixels):
	return 'There are %d bad pixels' % len(pixels)

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	icon = 'corrector'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		choices = [
			'Dark',
			'Bright',
			'Bright-Dark',
			'Norm',
			'Raw',
			'Corrected'
		]
		self.cacqtype = wx.Choice(self.toolbar, -1, choices=choices)
		self.cacqtype.SetSelection(0)
		self.toolbar.AddControl(self.cacqtype)

		choices = [
			'Both Channels',
			'Channel 0',
			'Channel 1',
		]
		self.cchannel = wx.Choice(self.toolbar, -1, choices=choices)
		self.cchannel.SetSelection(0)
		self.toolbar.AddControl(self.cchannel)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire')
		self.toolbar.AddSeparator()

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLUS,'plus',shortHelpString='Add Region To Bad Pixel List')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STAGE_LOCATIONS,'stagelocations',shortHelpString='Add Extreme Points To Bad Pixel List')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,'display',shortHelpString='Display Specified Image')

		# settings
		self.szplan = self._getStaticBoxSizer('Plan', (0, 0), (1, 1), wx.ALIGN_TOP)

		self.stbadrowscount = wx.StaticText(self, -1)
		self.stbadcolumnscount = wx.StaticText(self, -1)
		self.stbadpixelscount = wx.StaticText(self, -1)
		self.stdespike = wx.StaticText(self, -1)
		self.beditplan = wx.Button(self, -1, 'Edit...')
		self.bgrabpixels = wx.Button(self, -1, 'Grab From Image')
		self.bclearpixels = wx.Button(self, -1, 'Clear Bad Pixels')

		self.szplan.Add(self.beditplan, (0, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		self.szplan.Add(self.stbadrowscount, (2, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.szplan.Add(self.stbadcolumnscount, (3, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.szplan.Add(self.stbadpixelscount, (4, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.szplan.Add(self.stdespike, (5, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.szplan.Add(self.bclearpixels, (6, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
		self.szplan.Add(self.bgrabpixels, (7, 0), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)

		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.TargetImagePanel(self, -1)
		self.imagepanel.addTargetTool('Bad_Pixels', wx.Colour(255, 0, 0), target=True, shape='.')
		self.imagepanel.selectiontool.setDisplayed('Bad_Pixels', True)
		self.imagepanel.setTargets('Bad_Pixels', [])
		self.imagepanel.addTargetTool('Bad_Region', wx.Colour(0, 255, 255), target=True, shape='polygon', display=True)
		self.imagepanel.selectiontool.setDisplayed('Bad_Region', True)
		self.imagepanel.setTargets('Bad_Region', [])

		self.szmain.Add(self.imagepanel, (0, 1), (2, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=leginon.gui.wx.ToolBar.ID_ACQUIRE)

		self.toolbar.Bind(wx.EVT_TOOL, self.onAddTool,
											id=leginon.gui.wx.ToolBar.ID_PLUS)

		self.toolbar.Bind(wx.EVT_TOOL, self.onPlayTool,
											id=leginon.gui.wx.ToolBar.ID_STAGE_LOCATIONS)

		self.toolbar.Bind(wx.EVT_TOOL, self.onDisplayTool,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)

		self.settingsdialog = SettingsDialog(self)

		plan = self.node.retrieveCorrectorPlanFromSettings()
		self.setPlan(plan)

		self.Bind(wx.EVT_BUTTON, self.onEditPlan, self.beditplan)
		self.Bind(wx.EVT_BUTTON, self.onGrabPixels, self.bgrabpixels)
		self.Bind(wx.EVT_BUTTON, self.onClearPixels, self.bclearpixels)

	def onSetImage(self, evt):
		leginon.gui.wx.Node.Panel.onSetImage(self, evt)

	def resetInstruments(self):
		'''
		Use gui value to set proxy instrument.  This is called before
		settings dialog is opened since
		gui initialization may come before instruments are available.
		It causes mismatch of gui and the instrument in proxy
		'''
		dialogvalues = self.settingsdialog.widgets['instruments'].GetValue()
		for instrument in dialogvalues.keys():
			if dialogvalues[instrument] == 'None':
				dialogvalues[instrument] = None
		self.node.instrument.setTEM(dialogvalues['tem'])
		self.node.instrument.setCCDCamera(dialogvalues['ccdcamera'])

	def onSettingsTool(self, evt):
		self.resetInstruments()
		self.settingsdialog.ShowModal()
		plan = self.node.retrieveCorrectorPlanFromSettings()
		self.setPlan(plan)

	def _acquisitionEnable(self, enable):
		self.beditplan.Enable(enable)
		self.toolbar.Enable(enable)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		acqtype = self.cacqtype.GetStringSelection()
		channel = self.cchannel.GetStringSelection()
		if channel == 'Channel 0':
			channels = [0]
		elif channel == 'Channel 1':
			channels = [1]
		elif channel == 'Both Channels':
			channels = [0,1]
		if acqtype == 'Dark':
			method = self.node.acquireDark
			kwargs = {'channels': channels}
		elif acqtype == 'Bright':
			method = self.node.acquireBright
			kwargs = {'channels': channels}
		elif acqtype == 'Raw':
			method = self.node.acquireRaw
			kwargs = {}
		elif acqtype == 'Corrected':
			method = self.node.acquireCorrected
			kwargs = {'channels': channels}
		else:
			self._acquisitionEnable(True)
			return
		threading.Thread(target=method, kwargs=kwargs).start()	

	def onDisplayTool(self, evt):
		acqtype = self.cacqtype.GetStringSelection()
		if acqtype == 'Dark':
			reftype = 'dark'
		elif acqtype == 'Bright':
			reftype = 'bright'
		elif acqtype == 'Norm':
			reftype = 'norm'
		elif acqtype == 'Bright-Dark':
			reftype = 'dark-subtracted'
		else:
			return
		chanstr = self.cchannel.GetStringSelection()
		if chanstr  == 'Channel 0':
			channel = 0
		elif chanstr == 'Channel 1':
			channel = 1
		else:
			return
		self.node.displayRef(reftype, channel)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

        def onAddTool(self, evt):
                self.node.onAddRegion()

        def onPlayTool(self, evt):
                self.node.onAddPoints()

	def validatePlan(self, plan):
		camsettings = self.node.getCameraSettings()
		dimx = camsettings['dimension']['x']
		dimy = camsettings['dimension']['y']

		if 'pixels' in plan and plan['pixels']:
			ok_pixels = []
			not_ok_pixels = []
			for x,y in plan['pixels']:
				if (0 <= x < dimx) and (0 <= y < dimy):
					ok_pixels.append((x,y))
				else:
					not_ok_pixels.append((x,y))
			n_bad = len(not_ok_pixels)
			if n_bad:
				self.node.logger.warning("%d bad pixels out of bounds: %s" % (n_bad, not_ok_pixels))
			plan['pixels'] = ok_pixels

		if 'rows' in plan and plan['rows']:
			ok_rows = []
			not_ok_rows = []
			for row in plan['rows']:
				if 0 <= row < dimy:
					ok_rows.append(row)
				else:
					not_ok_rows.append(row)
			n_bad = len(not_ok_rows)
			if n_bad:
				self.node.logger.warning("%d bad rows out of bounds: %s" % (n_bad, not_ok_rows))
			plan['rows'] = ok_rows

		if 'columns' in plan and plan['columns']:
			ok_columns = []
			not_ok_columns = []
			for col in plan['columns']:
				if 0 <= col < dimx:
					ok_columns.append(col)
				else:
					not_ok_columns.append(col)
			n_bad = len(not_ok_columns)
			if n_bad:
				self.node.logger.warning("%d bad columns out of bounds: %s" % (n_bad, not_ok_columns))
			plan['columns'] = ok_columns

	def setPlan(self, plan):
		if not hasattr(self, 'plan'):
			self.plan = {}
		if plan is None or plan is {}:
			self.imagepanel.setTargets('Bad_Pixels', [])
			self.stbadrowscount.SetLabel('0')
			self.stbadcolumnscount.SetLabel('0')
			self.stbadpixelscount.SetLabel('0')
			self.stdespike.SetLabel('Despike: Off')
		else:
			self.validatePlan(plan)
			self.plan.update(plan)
			self.imagepanel.setTargets('Bad_Pixels', self.plan['pixels'])
			self.stbadrowscount.SetLabel(str(len(self.plan['rows']))+' Bad rows')
			self.stbadcolumnscount.SetLabel(str(len(self.plan['columns']))+' Bad columns')
			self.stbadpixelscount.SetLabel(str(len(self.plan['pixels']))+' Bad pixels')
			if self.plan['despike']:
				self.stdespike.SetLabel('Despike: On')
			else:
				self.stdespike.SetLabel('Despike: Off')

	def onEditPlan(self, evt):
		dialog = EditPlanDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			self.setPlan(dialog.plan)
			# ...
			threading.Thread(target=self.node.storeCorrectorPlan, args=(self.plan,)).start()
		dialog.Destroy()

	def onGrabPixels(self, evt):
		pixels = self.imagepanel.getTargetPositions('Bad_Pixels')
		self.setPlan({'pixels':pixels})
		threading.Thread(target=self.node.storeCorrectorPlan, args=(self.plan,)).start()

	def onClearPixels(self, evt):
		self.setPlan({'pixels':[]})
		threading.Thread(target=self.node.storeCorrectorPlan, args=(self.plan,)).start()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Image Correction')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		#sb = wx.StaticBox(self, -1, 'Clipping')
		#sbszclip = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sb = wx.StaticBox(self, -1, 'Reference Creation')
		sbszref = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['instruments'] = leginon.gui.wx.Instrument.SelectionPanel(self)
		self.panel.setInstrumentSelection(self.widgets['instruments'])

		self.widgets['n average'] = IntEntry(self, -1, min=1, max=99, chars=2)
		self.widgets['combine'] = Choice(self, -1, choices=['median', 'average'])
		self.widgets['store series'] = wx.CheckBox(self, -1, 'Save all images')

		self.widgets['camera settings'] = leginon.gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setGeometryLimits({'size':self.node.instrument.camerasize,'binnings':self.node.instrument.camerabinnings,'binmethod':self.node.instrument.camerabinmethod})
		#self.widgets['clip min'] = FloatEntry(self, -1, chars=6)
		#self.widgets['clip max'] = FloatEntry(self, -1, chars=6)

		'''
		szclip = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Clip min:')
		szclip.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szclip.Add(self.widgets['clip min'], (0, 1), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Clip max:')
		szclip.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szclip.Add(self.widgets['clip max'], (1, 1), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szclip.AddGrowableCol(1)
		sbszclip.Add(szclip, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)
		'''

		szref = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Images to combine:')
		szref.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szref.Add(self.widgets['n average'], (0, 1), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		label = wx.StaticText(self, -1, 'Combine method:')
		szref.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szref.Add(self.widgets['combine'], (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		szref.Add(self.widgets['store series'], (2,0), (1,2))

		sbszref.Add(szref, 1, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 3)

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['instruments'], (0, 0), (1, 1), wx.ALIGN_CENTER)
		sz.Add(self.widgets['camera settings'], (1, 0), (2, 1), wx.ALIGN_CENTER|wx.EXPAND)
		sz.Add(sbszref, (0, 1), (1, 1), wx.EXPAND)
		#sz.Add(sbszclip, (1, 1), (1, 1), wx.EXPAND)

		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		return [sbsz]

class EditPlanDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent.GetParent(), -1, 'Edit Plan')
		self.parent = parent
		self.plan = parent.plan
		
		strows = wx.StaticText(self, -1, 'Bad rows:')
		stcolumns = wx.StaticText(self, -1, 'Bad columns:')
		stpixels = wx.StaticText(self, -1, 'Bad Pixel (x,y):')

		pixels = ', '.join(map(str,self.plan['pixels']))
		rows = ', '.join(map(str,self.plan['rows']))
		columns = ', '.join(map(str,self.plan['columns']))

		self.tcrows = wx.TextCtrl(self, -1, rows)
		self.tccolumns = wx.TextCtrl(self, -1, columns)
		self.tcpixels = wx.TextCtrl(self, -1, pixels)

		self.cdespike = wx.CheckBox(self, -1, 'Despike images')
		self.cdespike_size = IntEntry(self, -1, min=1, chars=4)
		self.cdespike_threshold = FloatEntry(self, -1, min=0, chars=4)
		self.cdespike.SetValue(self.plan['despike'])
		self.cdespike_size.SetValue(self.plan['despike size'])
		self.cdespike_threshold.SetValue(self.plan['despike threshold'])

		szdespike = wx.GridBagSizer(5, 5)
		szdespike.Add(self.cdespike, (0, 0), (1, 2),
									wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'Neighborhood size:')
		szdespike.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdespike.Add(self.cdespike_size, (1, 1), (1, 1),
									wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Threshold:')
		szdespike.Add(label, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szdespike.Add(self.cdespike_threshold, (2, 1), (1, 1),
									wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szdespike.AddGrowableCol(1)

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
		szplan.Add(stpixels, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szplan.Add(self.tcpixels, (2, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szplan.Add(szdespike, (3, 0), (1, 2), wx.EXPAND)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(szplan, (0, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)
		sz.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(sz)

		self.Bind(wx.EVT_BUTTON, self.onSave, bsave)

	def onSave(self, evt):
		try:
			rows = str2plan(self.tcrows.GetValue())
			columns = str2plan(self.tccolumns.GetValue())
			pixels = str2pixels(self.tcpixels.GetValue())
		except ValueError:
			dialog = wx.MessageDialog(self, 'Invalid plan', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.plan = {'rows': rows, 'columns': columns, 'pixels': pixels,
				'despike':self.cdespike.GetValue(),
				'despike size': self.cdespike_size.GetValue(),
				'despike threshold': self.cdespike_threshold.GetValue()
			}
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

