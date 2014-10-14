# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import threading
import wx
import time

from leginon.gui.wx.Entry import IntEntry, FloatEntry, Entry, EVT_ENTRY
import leginon.gui.wx.Camera
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.ImagePanelTools
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.ImagePanel
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Instrument

LocationsEventType = wx.NewEventType()
EVT_LOCATIONS = wx.PyEventBinder(LocationsEventType)
TestEventType = wx.NewEventType()
EVT_TEST = wx.PyEventBinder(TestEventType)

class LocationsEvent(wx.PyCommandEvent):
	def __init__(self, source, locations):
		wx.PyCommandEvent.__init__(self, LocationsEventType, source.GetId())
		self.SetEventObject(source)
		self.locations = locations

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	icon = 'navigator'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelpString='Settings')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_ACQUIRE,
													'acquire',
													shortHelpString='Acquire')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_STAGE_LOCATIONS,
													'stagelocations',
													shortHelpString='Stage Locations')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_MEASURE,
													'ruler',
													shortHelpString='Test stage reproducibility')

		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_XY, 'xy',
													shortHelpString='Reset stage X,Y to 0,0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_Z, 'z',
													shortHelpString='Reset stage Z to 0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_ALPHA, 'alpha',
													shortHelpString='Reset stage alpha tilt to 0')

		# image
		self.imagepanel = leginon.gui.wx.TargetPanel.ClickAndTargetImagePanel(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.imagepanel.addTypeTool('Correlation', display=True)
		self.imagepanel.addTargetTool('Peak', wx.Colour(255,0,0))

		self.szmain.Add(self.imagepanel, (0, 0), (1, 1), wx.EXPAND)

		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

		self.Bind(EVT_LOCATIONS, self.onLocations)

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		self.locationsdialog = StageLocationsDialog(self, self.node)

		movetypes = self.node.calclients.keys()
		self.cmovetype = Choice(self.toolbar, -1, choices=movetypes)
		self.cmovetype.SetStringSelection(self.node.settings['move type'])
		## make sure node setting is a value that is in the choice list
		self.node.settings['move type'] = self.cmovetype.GetStringSelection()
		self.cmovetype.SetToolTip(wx.ToolTip('Navigion Parameter'))
		self.toolbar.InsertControl(4, self.cmovetype)

		self.insertPresetSelector(2)
		self.toolbar.Bind(wx.EVT_TOOL, self.onGetPresetTool,
											id=leginon.gui.wx.ToolBar.ID_GET_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSendPresetTool,
											id=leginon.gui.wx.ToolBar.ID_SEND_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=leginon.gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onStageLocationsTool,
											id=leginon.gui.wx.ToolBar.ID_STAGE_LOCATIONS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onReproTest,
											id=leginon.gui.wx.ToolBar.ID_MEASURE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetXY,
											id=leginon.gui.wx.ToolBar.ID_RESET_XY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetZ,
											id=leginon.gui.wx.ToolBar.ID_RESET_Z)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetAlpha,
											id=leginon.gui.wx.ToolBar.ID_RESET_ALPHA)
		self.cmovetype.Bind(wx.EVT_CHOICE, self.onMoveTypeChoice)
		self.Bind(leginon.gui.wx.ImagePanelTools.EVT_IMAGE_CLICKED, self.onImageClicked,
							self.imagepanel)
		self.test_dialog = ReproTestDialog(self)
		self.Bind(EVT_TEST, self.onReproTest, self)

	def insertPresetSelector(self,position):
		'''
		Select preset to send/get.
		'''
		# This needs to be done after self.node is set.
		self.presetnames = self.node.presetsclient.getPresetNames()

		self.preset_choices = Choice(self.toolbar, -1, choices=self.presetnames)
		#self.toolbar.InsertTool(position+3,leginon.gui.wx.ToolBar.ID_GET_PRESET,
		#											'instrumentget',
		#										shortHelpString='Get preset from scope')
		self.toolbar.InsertTool(position,leginon.gui.wx.ToolBar.ID_SEND_PRESET,
													'instrumentset',
													shortHelpString='Send preset to scope')
		self.toolbar.InsertControl(position,self.preset_choices)
		return

	def onShow(self):
		current_choice = self.preset_choices.GetStringSelection()
		self.presetnames = self.node.presetsclient.getPresetNames()
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.preset_choices.Clear()
		for name in self.presetnames:
			self.preset_choices.Append(name)
		if current_choice in self.presetnames:
			self.preset_choices.SetStringSelection(current_choice)

	def onGetPresetTool(self,evt):
		presetname = self.preset_choices.GetStringSelection()
		args = (presetname,)
		threading.Thread(target=self.node.uiGetPreset,args=args).start()

	def onSendPresetTool(self,evt):
		presetname = self.preset_choices.GetStringSelection()
		print 'sending %s' % presetname
		self._acquisitionEnable(False)
		args = (presetname,)
		threading.Thread(target=self.node.uiSendPreset,args=args).start()

	def onSendPresetDone(self):
		self._acquisitionEnable(True)

	def onResetXY(self, evt):
		self.node.onResetXY()

	def onResetZ(self, evt):
		self.node.onResetZ()

	def onResetAlpha(self, evt):
		self.node.onResetAlpha()

	def onReproTest(self, evt):
		self.test_dialog.Show()

	def onMoveTypeChoice(self, evt):
		self.node.settings['move type'] = evt.GetString()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def _acquisitionEnable(self, enable):
		self.toolbar.Enable(enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.uiAcquireImage).start()

	def onStageLocationsTool(self, evt):
		self.locationsdialog.ShowModal()

	def onImageClicked(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.navigate, args=(evt.xy,)).start()

	def navigateDone(self):
		evt = leginon.gui.wx.ImagePanel.ImageClickDoneEvent(self.imagepanel)
		self.imagepanel.GetEventHandler().AddPendingEvent(evt)
		self.acquisitionDone()

	def onLocations(self, evt):
		self.locationsdialog.setLocations(evt.locations)

	def locationsEvent(self, locations):
		evt = LocationsEvent(self, locations)
		self.GetEventHandler().AddPendingEvent(evt)

class StageLocationsDialog(wx.Dialog):
	def __init__(self, parent, node):
		self.node = node
		wx.Dialog.__init__(self, parent, -1, 'Stage Locations',
												style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)

		self.sz = wx.GridBagSizer(5, 5)

		stposition = {}
		self.stposition = {}
		axes = ['x', 'y', 'z', 'a', 'b']
		for i, a in enumerate(axes):
			stposition[a] = wx.StaticText(self, -1, a)
			self.stposition[a] = wx.StaticText(self, -1, '-')
			self.sz.Add(stposition[a], (0, i + 1), (1, 1), wx.ALIGN_CENTER)
			self.sz.Add(self.stposition[a], (1, i + 1), (1, 1), wx.ALIGN_CENTER)
			self.sz.AddGrowableCol(i + 1)

		label0 = wx.StaticText(self, -1, 'Position:')
		label1 = wx.StaticText(self, -1, 'Comment:')
		self.stcomment = wx.StaticText(self, -1, '(No location selected)')
		label2 = wx.StaticText(self, -1, 'Locations')
		choices = self.node.getLocationNames()
		self.lblocations = wx.ListBox(self, -1, style=wx.LB_SINGLE)
		self.bnew = wx.Button(self, -1, 'New...')
		self.btoscope = wx.Button(self, -1, 'To scope')
		self.bfromscope = wx.Button(self, -1, 'From scope')
		self.bremove = wx.Button(self, -1, 'Remove')
		self.btoscope.Enable(False)
		self.bfromscope.Enable(False)
		self.bremove.Enable(False)

		self.sz.Add(label0, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(label1, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.stcomment, (2, 1), (1, 5),
													wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(label2, (3, 1), (1, 5), wx.ALIGN_CENTER_VERTICAL)
		self.sz.Add(self.lblocations, (4, 1), (1, 5), wx.EXPAND|wx.FIXED_MINSIZE|wx.ALL, 5)
		self.lblocations.AppendItems(choices)

		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(self.bnew, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.btoscope, (1, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bfromscope, (2, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bremove, (3, 0), (1, 1), wx.ALIGN_CENTER)
		self.sz.Add(szbuttons, (4, 0), (1, 1),
								wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP)

		self.sz.AddGrowableRow(4)

		szdialog = wx.GridBagSizer(5, 5)
		szdialog.Add(self.sz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		szdialog.AddGrowableCol(0)

		self.SetSizerAndFit(szdialog)

		self.Bind(wx.EVT_BUTTON, self.onNew, self.bnew)
		self.Bind(wx.EVT_BUTTON, self.onToScope, self.btoscope)
		self.Bind(wx.EVT_BUTTON, self.onFromScope, self.bfromscope)
		self.Bind(wx.EVT_BUTTON, self.onRemove, self.bremove)
		self.Bind(wx.EVT_LISTBOX, self.onLocationSelected, self.lblocations)

	def onNew(self, evt):
		dialog = NewLocationDialog(self, self.node)
		if dialog.ShowModal() == wx.ID_OK:
			self.node.fromScope(dialog.name, dialog.comment, dialog.xyonly)
		dialog.Destroy()

	def onToScope(self, evt):
		name = self.lblocations.GetStringSelection()
		self.node.toScope(name)

	def onFromScope(self, evt):
		name = self.lblocations.GetStringSelection()
		self.node.fromScope(name)

	def onRemove(self, evt):
		n = self.lblocations.GetSelection()
		if n < 0:
			return
		name = self.lblocations.GetString(n)
		self.lblocations.Delete(n)
		self.node.removeLocation(name)

	def _setLocation(self, l):
		for a in ['x', 'y', 'z', 'a', 'b']:
			if l is None:
				self.stposition[a].SetLabel('-')
			else:
				try:
					if l[a] is None:
						self.stposition[a].SetLabel('-')
					else:
						self.stposition[a].SetLabel('%g' % l[a])
				except KeyError:
					self.stposition[a].SetLabel('-')

		if l is None:
			comment = '(No location selected)'
		elif l['comment'] is None:
			comment = ''
		else:
			comment = l['comment']
		self.stcomment.SetLabel(comment)

		if l is None:
			enable = False
		else:
			enable = True
		self.btoscope.Enable(enable)
		self.bfromscope.Enable(enable)
		self.bremove.Enable(enable)

		self.Fit()

	def onLocationSelected(self, evt):
		if evt.IsSelection():
			location = self.node.getLocation(evt.GetString())
		else:
			location = None
		self._setLocation(location)

	def setLocations(self, locations):
		string = self.lblocations.GetStringSelection()
		self.lblocations.Clear()
		self.lblocations.AppendItems(locations)
		if self.lblocations.FindString(string) == wx.NOT_FOUND:
			self._setLocation(None)
		else:
			location = self._setLocation(self.node.getLocation(string))
			self.lblocations.SetStringSelection(string)

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'Navigation')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		if self.show_basic:
			sz = self.addBasicSettings()
		else:
			sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addBasicSettings(self):
		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		# error checking and correction
		self.widgets['check calibration'] = wx.CheckBox(self, -1,
																										'Measure move error')
		sz = wx.GridBagSizer(5, 10)
		sz.Add(szpausetime, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['check calibration'], (1, 0), (1, 1))
		return sz

	def addSettings(self):
		overridebox = wx.StaticBox(self, -1, "Override Preset during Testing")
		overridesz = wx.StaticBoxSizer(overridebox, wx.VERTICAL)
		errbox = wx.StaticBox(self, -1, "Error Checking and Correction during Testing")
		errsz = wx.StaticBoxSizer(errbox, wx.VERTICAL)

		# pause time
		self.widgets['pause time'] = FloatEntry(self, -1,
																		min=0.0,
																		allownone=False,
																		chars=4,
																		value='0.0')
		szpausetime = wx.GridBagSizer(5, 5)
		szpausetime.Add(wx.StaticText(self, -1, 'Wait'),
								(0, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)
		szpausetime.Add(self.widgets['pause time'],
								(0, 1), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		szpausetime.Add(wx.StaticText(self, -1, 'seconds before acquiring image'),
								(0, 2), (1, 1),
								wx.ALIGN_CENTER_VERTICAL)

		# override preset
		self.widgets['override preset'] = wx.CheckBox(self, -1,
																								'Override Preset')
		self.widgets['instruments'] = leginon.gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.panel.setInstrumentSelection(self.widgets['instruments'])
		self.widgets['camera settings'] = leginon.gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setGeometryLimits({'size':self.node.instrument.camerasize,'binnings':self.node.instrument.camerabinnings,'binmethod':self.node.instrument.camerabinmethod})

		self.widgets['background readout'] = wx.CheckBox(self, -1, 'Background Readout')

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['override preset'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['instruments'], (1, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['background readout'], (3, 0), (1, 1), wx.EXPAND)
		overridesz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		# error checking and correction
		self.widgets['check calibration'] = wx.CheckBox(self, -1,
																										'Measure move error')
		precsz = wx.GridBagSizer(5, 5)
		label1 = wx.StaticText(self, -1, 'Move to within')
		self.widgets['precision'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=6, value='0.0')
		label2 = wx.StaticText(self, -1, 'm of clicked position')
		precsz.Add(label1, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		precsz.Add(self.widgets['precision'], (0, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		precsz.Add(label2, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label1 = wx.StaticText(self, -1, 'Acceptable distance:') 
		self.widgets['accept precision'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=6, value='1e-3')
		label2 = wx.StaticText(self, -1, '(m) if move error get worse')
		precsz.Add(label1, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		precsz.Add(self.widgets['accept precision'], (1, 1), (1, 1),
						wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		precsz.Add(label2, (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.widgets['final image shift'] = wx.CheckBox(self, -1, 'Final Image Shift')
		precsz.Add(self.widgets['final image shift'], (2,0),(1,2))

		#maxerrsz = wx.GridBagSizer(5, 5)
		#label = wx.StaticText(self, -1, 'Local Correlation Size (pixels)')
		#self.widgets['max error'] = FloatEntry(self, -1, min=0.0, allownone=False, chars=6, value='0.0')
		#maxerrsz.Add(label, (0, 0), (1, 1))
		#maxerrsz.Add(self.widgets['max error'], (0, 1), (1, 1),
		#				wx.ALIGN_CENTER_VERTICAL)

		hysfixsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, '')
		self.widgets['cycle after'] = wx.CheckBox(self, -1, 'Preset cycle after final move')
		self.widgets['cycle each'] = wx.CheckBox(self, -1, 'Preset cycle after each move')
		self.widgets['preexpose'] = wx.CheckBox(self, -1, 'Perform pre-exposure from preset')
		hysfixsz.Add(self.widgets['cycle after'], (0, 0), (1, 1))
		hysfixsz.Add(self.widgets['cycle each'], (1, 0), (1, 1))
		hysfixsz.Add(self.widgets['preexpose'], (2, 0), (1, 1))

		## 
		ccsz = wx.GridBagSizer(5,5)
		ccsz.Add(self.widgets['check calibration'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		#sz.Add(maxerrsz, (1, 0), (1, 1),
		#				wx.ALIGN_CENTER_VERTICAL)
		ccsz.Add(precsz, (2, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		ccsz.Add(hysfixsz, (3, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		errsz.Add(ccsz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		# settings sizer
		sz = wx.GridBagSizer(5, 10)
		sz.Add(overridesz, (0, 0), (6, 1))
		sz.Add(szpausetime, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(errsz, (3,1), (1,1))
		#sz.AddGrowableRow(2)
		return sz

class NewLocationDialog(wx.Dialog):
	def __init__(self, parent, node):
		self.node = node
		wx.Dialog.__init__(self, parent, -1, 'New Location')

		stname = wx.StaticText(self, -1, 'Name:')
		stcomment = wx.StaticText(self, -1, 'Comment:')
		self.tcname = wx.TextCtrl(self, -1, '')
		self.tccomment = wx.TextCtrl(self, -1, '')
		self.cbxyonly = wx.CheckBox(self, -1, 'Save x and y only')
		self.cbxyonly.SetValue(True)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(stname, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.tcname, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(stcomment, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.tccomment, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		sz.Add(self.cbxyonly, (2, 0), (1, 2), wx.ALIGN_CENTER)
		sz.AddGrowableCol(1)

		bsave = wx.Button(self, wx.ID_OK, 'Save')
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(bsave, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbutton.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)

		szmain = wx.GridBagSizer(5, 5)
		szmain.Add(sz, (0, 0), (1, 1), wx.ALIGN_CENTER|wx.ALL, border=5)
		szmain.Add(szbutton, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, border=5)

		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onSave, bsave)

	def onSave(self, evt):
		name = self.tcname.GetValue()
		if not name or name in self.node.getLocationNames():
			dialog = wx.MessageDialog(self, 'Invalid location name', 'Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()
		else:
			self.name = name
			self.comment = self.tccomment.GetValue()
			self.xyonly = self.cbxyonly.GetValue()
			evt.Skip()

class ReproTestDialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		wx.Dialog.__init__(self, parent, -1, 'Test Reproducibiltiy')

		self.measure = wx.Button(self, -1, 'Run')
		self.Bind(wx.EVT_BUTTON, self.onMeasureButton, self.measure)

		szbutton = wx.GridBagSizer(5, 5)
		szbutton.Add(self.measure, (0, 0), (1, 1), wx.EXPAND)

		sbsz = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Label:')
		self.labvalue = Entry(self, -1, chars=20, value='test1')
		sbsz.Add(label, (0,0), (1,1))
		sbsz.Add(self.labvalue, (0,1), (1,1))

		label = wx.StaticText(self, -1, 'Moves:')
		self.movesvalue = IntEntry(self, -1, allownone=False, chars=5, value='10')
		sbsz.Add(label, (1,0), (1,1))
		sbsz.Add(self.movesvalue, (1,1), (1,1))

		label = wx.StaticText(self, -1, 'Distance:')
		self.distvalue = FloatEntry(self, -1, allownone=False, chars=5, value='1e-5')
		sbsz.Add(label, (2,0), (1,1))
		sbsz.Add(self.distvalue, (2,1), (1,1))

		label = wx.StaticText(self, -1, 'Angle:')
		self.angvalue = FloatEntry(self, -1, allownone=True, chars=5, value='')
		sbsz.Add(label, (3,0), (1,1))
		sbsz.Add(self.angvalue, (3,1), (1,1))

		self.sizer = wx.GridBagSizer(5, 5)
		self.sizer.Add(sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.sizer.Add(self.measure, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		self.SetSizerAndFit(self.sizer)

	def onMeasureButton(self, evt):
		self.Close()
		label = self.labvalue.GetValue()
		moves = self.movesvalue.GetValue()
		distance = self.distvalue.GetValue()
		angle = self.angvalue.GetValue()
		threading.Thread(target=self.node.move_away_move_back, args=(label,moves,distance,angle)).start()


if __name__ == '__main__':
	class Node(object):
		def getLocationNames(self):
			return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']

		def getLocation(self, name):
			value = 1.23456789e-6
			keys = ['x', 'y', 'z', 'a', 'b']
			location = {}
			for key in keys:
				location[key] = value
			location['comment'] = 'This is a fake stage position for testing'
			return location

	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Navigator Test')
			#panel = Panel(frame)
			node = Node()
			dialog = StageLocationsDialog(frame, node)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

