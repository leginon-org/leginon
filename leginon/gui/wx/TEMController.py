# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import threading
import wx
import time

from leginon.gui.wx.Entry import IntEntry, FloatEntry, Entry, EVT_ENTRY
import leginon.gui.wx.Camera
from leginon.gui.wx.Choice import Choice
import leginon.gui.wx.Node
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
import leginon.gui.wx.Instrument

class Panel(leginon.gui.wx.Node.Panel, leginon.gui.wx.Instrument.SelectionMixin):
	icon = 'remote'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Node.Panel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_SETTINGS,
													'settings',
													shortHelp='Settings')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
													'refresh',
													shortHelp='Refresh')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_LIGHT_ON,
													'light_on',
													shortHelp='Open Column Valves')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_LIGHT_OFF,
													'light_off',
													shortHelp='Close Column Valves')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PLAY, 'play', shortHelp='Continue Last')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_PAUSE, 'pause', shortHelp='Pause All')
		self.toolbar.AddSeparator()
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_XY, 'xy',
													shortHelp='Reset stage X,Y to 0,0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_Z, 'z',
													shortHelp='Reset stage Z to 0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_ALPHA, 'alpha',
													shortHelp='Reset stage alpha tilt to 0')

		self.pressure_order = ['column','projection','buffer tank']
		self.sz_pressure = TEMParameters(self,'Gauge Pressure', self.pressure_order)
		self.szmain.Add(self.sz_pressure, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.current_mechanism = 'objective'
		self.current_aperture = ''
		self.sz_aperture = TEMParameters(self,'Aperture State', [])
		self.szmain.Add(self.sz_aperture, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# set sz_gridloader key order later
		self.sz_gridloader = TEMParameters(self,'Grid Loader', [])
		self.szmain.Add(self.sz_gridloader, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)
		self.szmain.AddGrowableCol(1)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		# Base Class function call
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)
		# These need to be here because self.node is not defined in __init__
		self.insertApertureSelector(3)
		self.insertMechanismSelector(3)
		self.insertGridSlotSelector(3)
		self.insertPresetSelector(3)
		# ToolBar Events
		self.toolbar.Bind(wx.EVT_TOOL, self.onGetPresetTool,
											id=leginon.gui.wx.ToolBar.ID_GET_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSendPresetTool,
											id=leginon.gui.wx.ToolBar.ID_SEND_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onUnloadGridTool,
											id=leginon.gui.wx.ToolBar.ID_EXTRACT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onLoadGridTool,
											id=leginon.gui.wx.ToolBar.ID_INSERT)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSetApertureTool,
											id=leginon.gui.wx.ToolBar.ID_CALIBRATE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onRefreshTool,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)
		self.toolbar.Bind(wx.EVT_TOOL, self.onLightOnTool,
											id=leginon.gui.wx.ToolBar.ID_LIGHT_ON)
		self.toolbar.Bind(wx.EVT_TOOL, self.onLightOffTool,
											id=leginon.gui.wx.ToolBar.ID_LIGHT_OFF)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetXY,
											id=leginon.gui.wx.ToolBar.ID_RESET_XY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPlay,
											id=leginon.gui.wx.ToolBar.ID_PLAY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onPause,
											id=leginon.gui.wx.ToolBar.ID_PAUSE)
		self.Bind(leginon.gui.wx.Events.EVT_PLAYER, self.onPlayer)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetZ,
											id=leginon.gui.wx.ToolBar.ID_RESET_Z)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetAlpha,
											id=leginon.gui.wx.ToolBar.ID_RESET_ALPHA)
		# Contoller Events
		self.Bind(leginon.gui.wx.Events.EVT_GET_DISPLAY_PRESSURE, self.onDisplayPressure)
		self.Bind(leginon.gui.wx.Events.EVT_GET_DISPLAY_GRID_LOADER_SLOT_STATES, self.onDisplayGridLoaderSlotStates)
		self.Bind(leginon.gui.wx.Events.EVT_GET_DISPLAY_APERTURE_STATES, self.onDisplayApertureStates)
		self.Bind(leginon.gui.wx.Events.EVT_UPDATE_GRID_SLOT_SELECTOR, self.onUpdateGridSlotSelector)
		self.Bind(leginon.gui.wx.Events.EVT_UPDATE_MECHANISM_SELECTOR, self.onUpdateMechanismSelector)
		self.Bind(leginon.gui.wx.Events.EVT_UPDATE_APERTURE_SELECTOR, self.onUpdateApertureSelector)
		self.mechanism_choices.Bind(wx.EVT_CHOICE, self.onSetMechanismTool,self.mechanism_choices)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onShow(self):
		self.setPresetChoice()
		self.setGridSlotChoice()

	def setTEMParamDone(self):
		'''
		called from node. Event creater for contoller.
		'''
		self.refreshDisplay()

	def onRefreshTool(self, evt):
		self.refreshDisplay()

	def refreshDisplay(self):
		self.addDisplayPressureEvent()
		self.addDisplayGridLoaderSlotStatesEvent()
		self.addUpdateGridSlotSelectorEvent()
		self.addDisplayApertureStatesEvent()
		self.addUpdateMechanismSelectorEvent()
		self.addUpdateApertureSelectorEvent()

	#=============Preset Selector and Set  ========================
	def insertPresetSelector(self, position):
		'''
		Select preset to send.
		'''
		# This needs to be done after self.node is set.
		self.presetnames = self.node.presetsclient.getPresetNames()

		self.preset_choices = Choice(self.toolbar, -1, choices=self.presetnames)
		#self.toolbar.InsertTool(position+3,leginon.gui.wx.ToolBar.ID_GET_PRESET,
		#											'instrumentget',
		#										shortHelp='Get preset from scope')
		self.toolbar.InsertSeparator(position)
		self.toolbar.InsertTool(position, leginon.gui.wx.ToolBar.ID_SEND_PRESET,
													'instrumentset',
													shortHelp='Send preset to scope')
		self.toolbar.InsertControl(position, self.preset_choices)
		return

	def setPresetChoice(self):
		current_choice = self.preset_choices.GetStringSelection()
		self.presetnames = self.node.presetsclient.getPresetNames()
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.preset_choices.Clear()
		for name in self.presetnames:
			self.preset_choices.Append(name)
		if current_choice in self.presetnames:
			self.preset_choices.SetStringSelection(current_choice)

	def onGetPresetTool(self,evt):
		# MCV controller  makes model to do things
		presetname = self.preset_choices.GetStringSelection()
		args = (presetname,)
		threading.Thread(target=self.node.uiGetPreset,args=args).start()

	def onSendPresetTool(self,evt):
		# MCV controller  makes model to do things
		presetname = self.preset_choices.GetStringSelection()
		args = (presetname,)
		self._lightonEnable(False)
		threading.Thread(target=self.node.uiSendPreset,args=args).start()

	def sendPresetDone(self):
		# MCV controller handle model changed event
		# Enable both tools for now since we are not refreshing it when the
		# node is selected.
		self.enableAll(True)

	#=============COLUMN VALVE CONTROL========================
	def enableAll(self, state):
		self._lightonEnable(state)
		self._lightoffEnable(state)

	def _lightonEnable(self, enable):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_LIGHT_ON, enable)

	def _lightoffEnable(self, enable):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_LIGHT_OFF, enable)

	def setIsLightOn(self,status):
		self._lightonEnable(not status)
		self._lightoffEnable(status)

	def onLightOnTool(self, evt):
		self._lightonEnable(False)
		self._lightoffEnable(True)
		threading.Thread(target=self.node.uiOpenColumnValve).start()

	def onLightOffTool(self, evt):
		self._lightonEnable(True)
		self._lightoffEnable(False)
		threading.Thread(target=self.node.uiCloseColumnValve).start()

	#=========GRID SLOT SELECTOR============================
	def getGridSelectionNames(self):
		# This needs to be done after self.node is set.
		self.grid_slot_names = self.node.getGridSlotNames()
		# Use a different list to include default before knowing which grid is loaded.
		self.grid_selection_names = list(self.grid_slot_names)
		if self.grid_selection_names:
			self.grid_selection_names.insert(0,'?')

	def insertGridSlotSelector(self,position):
		'''
		Create Choice Sizer
		'''
		self.getGridSelectionNames()
		self.grid_slot_choices = Choice(self.toolbar, -1, choices=self.grid_selection_names)
		# Insert in reverse order
		self.toolbar.InsertSeparator(position)
		self.toolbar.InsertTool(position, leginon.gui.wx.ToolBar.ID_EXTRACT,
													'cleargrid',
												shortHelp='Remove grid from column')
		self.toolbar.InsertTool(position, leginon.gui.wx.ToolBar.ID_INSERT,
													'extractgrid',
													shortHelp='Insert grid from gridloader slot')
		self.toolbar.InsertControl(position,self.grid_slot_choices)
		return

	def addUpdateGridSlotSelectorEvent(self):
		# MCV model create event to publish
		self.getGridSelectionNames()
		if not self.grid_selection_names:
			# Do nothing is no grids
			return
		evt = leginon.gui.wx.Events.UpdateGridSlotSelectorEvent()
		evt.values = self.grid_selection_names
		self.GetEventHandler().AddPendingEvent(evt)

	def onUpdateGridSlotSelector(self, evt):
		names = evt.values
		self.setGridSlotChoices(names)
		self.setGridSlotChoice()

	def setGridSlotChoices(self,names):
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.grid_slot_choices.Clear()
		for name in names:
			self.grid_slot_choices.Append(name)

	def setGridSlotChoice(self):
		if not self.grid_slot_names:
			return
		current_choice = self.grid_slot_choices.GetStringSelection()
		if current_choice in self.grid_selection_names:
			self.grid_slot_choices.SetStringSelection(current_choice)

	def onUnloadGridTool(self,evt):
		current_slot_name = self.grid_slot_choices.GetStringSelection()
		threading.Thread(target=self.node.unloadGrid).start()

	def onLoadGridTool(self,evt):
		current_slot_name = self.grid_slot_choices.GetStringSelection()
		args = (current_slot_name,)
		threading.Thread(target=self.node.loadGrid,args=args).start()

	def onLoadGridDone(self):
		self.displayGridLoaderSlotStates()
		self.enableAll(True)

	def onUnLoadGridDone(self):
		self.displayGridLoaderSlotStates()
		self.enableAll(True)

	#===========WORKFLOW CONTROL===================
	def onPlay(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
		threading.Thread(target=self.node.uiContinue).start()

	def onPause(self, evt):
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)
		threading.Thread(target=self.node.uiPause).start()

	def onPlayer(self, evt):
		if evt.state == 'play':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, False)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, True)
		elif evt.state == 'pause':
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PLAY, True)
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_PAUSE, False)

	#===========STAGE CONTROL===================
	def onResetXY(self, evt):
		self.node.onResetXY()

	def onResetZ(self, evt):
		self.node.onResetZ()

	def onResetAlpha(self, evt):
		self.node.onResetAlpha()

	#=========APERTURE MECHANISM SELECTOR============================
	def getApertureMechanisms(self):
		self.mechanism_names = self.node.getApertureMechanisms()

	def insertMechanismSelector(self,position):
		'''
		Create Choice Sizer
		'''
		self.getApertureMechanisms()
		self.mechanism_choices = Choice(self.toolbar, -1, choices=self.mechanism_names)
		# Insert in reverse order
		self.toolbar.InsertControl(position,self.mechanism_choices)
		if not self.mechanism_names:
			# this tool is created first by ApertureSelector
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALIBRATE, False)
		return

	def addUpdateMechanismSelectorEvent(self):
		# MCV model create event to publish
		self.getApertureMechanisms()
		if not self.mechanism_names:
			# Do nothing
			return
		evt = leginon.gui.wx.Events.UpdateMechanismSelectorEvent()
		evt.values = self.mechanism_names
		evt.current = self.current_mechanism
		self.GetEventHandler().AddPendingEvent(evt)

	def onUpdateMechanismSelector(self, evt):
		names = evt.values
		current = evt.current
		self.setMechanismChoices(names)
		self.setMechanismChoice(current)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALIBRATE, bool(names))

	def setMechanismChoices(self,names):
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.mechanism_choices.Clear()
		for name in names:
			self.mechanism_choices.Append(name)

	def setMechanismChoice(self,current_choice):
		if not self.mechanism_names:
			return
		if current_choice in self.mechanism_names:
			self.mechanism_choices.SetStringSelection(current_choice)

	def onSetMechanismTool(self,evt):
		self.current_mechanism = evt.GetString().lower()
		self.addUpdateApertureSelectorEvent()

	#=========APERTURE SELECTOR============================
	def getApertureSelectionNames(self):
		# This needs to be done after self.node is set.
		self.aperture_names = self.node.getApertureNames(self.current_mechanism)
		# Use a different list to include default before knowing which state it is in.
		self.aperture_selection_names = list(self.aperture_names)

	def insertApertureSelector(self,position):
		'''
		Create Choice Sizer
		'''
		self.getApertureSelectionNames()
		self.aperture_choices = Choice(self.toolbar, -1, choices=self.aperture_selection_names)
		# Insert in reverse order
		self.toolbar.InsertSeparator(position)
		self.toolbar.InsertTool(position, leginon.gui.wx.ToolBar.ID_CALIBRATE,
													'instrumentset',
												shortHelp='Send objective aperture selection to scope')
		self.toolbar.InsertControl(position,self.aperture_choices)
		if not self.aperture_selection_names:
			self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALIBRATE, False)
		return

	def addUpdateApertureSelectorEvent(self):
		# MCV model create event to publish
		self.getApertureSelectionNames()
		if not self.aperture_selection_names:
			# Do nothing is no grids
			return
		evt = leginon.gui.wx.Events.UpdateApertureSelectorEvent()
		evt.values = self.aperture_selection_names
		evt.current = self.current_aperture
		self.GetEventHandler().AddPendingEvent(evt)

	def onUpdateApertureSelector(self, evt):
		names = evt.values
		current = evt.current
		self.setApertureChoices(names)
		self.setApertureChoice(current)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_CALIBRATE, bool(names))

	def setApertureChoices(self,names):
		# This part is needed for wxpython 2.8.  It can be replaced by Set function in 3.0
		self.aperture_choices.Clear()
		for name in names:
			self.aperture_choices.Append(name)

	def setApertureChoice(self,current_choice):
		if not self.aperture_selection_names:
			return
		if current_choice in self.aperture_selection_names:
			self.aperture_choices.SetStringSelection(current_choice)

	def onSetApertureTool(self,evt):
		self.current_mechanism = self.mechanism_choices.GetStringSelection()
		self.current_aperture = self.aperture_choices.GetStringSelection()
		args = (self.current_mechanism, self.current_aperture,)
		threading.Thread(target=self.node.selectAperture,args=args).start()

	#=============PRESSURE DISPLAY=====================
	def addDisplayPressureEvent(self):
		# MCV model create event to publish
		evt = leginon.gui.wx.Events.GetDisplayPressureEvent()
		evt.unit = 'Pascal'
		evt.values = self.node.getPressuresToDisplay(evt.unit)
		self.GetEventHandler().AddPendingEvent(evt)

	def onDisplayPressure(self, evt):
		# MCV controller handle event and set change to view
		self.sz_pressure.setUnit(evt.unit)
		self.sz_pressure.setFloat(evt.values)
		self.szmain.Layout()


	#==========GRID LOADER SLOT STATE DISPLAY=======
	def addDisplayGridLoaderSlotStatesEvent(self):
		# MCV model create event to publish
		states = self.node.getGridSlotStatesToDisplay()
		if not states:
			# Do nothing is no grid loader or having trouble in getting the states
			return
		evt = leginon.gui.wx.Events.GetDisplayGridLoaderSlotStatesEvent()
		evt.unit = ''
		evt.values = states
		self.GetEventHandler().AddPendingEvent(evt)

	def onDisplayGridLoaderSlotStates(self, evt):
		# Reload it in case it is different such as instrument not ready
		self.grid_slot_names = self.node.getGridSlotNames()
		self.sz_gridloader.setOrder(self.grid_slot_names)
		self.sz_gridloader.setUnit(evt.unit)
		self.sz_gridloader.setString(evt.values)
		self.szmain.Layout()

	#=============Aperture DISPLAY=====================
	def addDisplayApertureStatesEvent(self):
		# MCV model create event to publish
		evt = leginon.gui.wx.Events.GetDisplayApertureStatesEvent()
		evt.values = self.node.getApertureStatesToDisplay()
		self.GetEventHandler().AddPendingEvent(evt)

	def onDisplayApertureStates(self, evt):
		# MCV controller handle event and set change to view
		mech_names= self.node.getApertureMechanisms()
		self.sz_aperture.setOrder(mech_names)
		self.sz_aperture.setUnit('um')
		self.sz_aperture.setString(evt.values)
		self.szmain.Layout()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'TEM Controller')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = self.addSettings()
		sbsz.Add(sz, 0, wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addSettings(self):
		sz = wx.GridBagSizer(5, 10)
		pos = self.createRetractObjApOnGridChangingCheckBox(sz, (0,0))
		sz.Add(wx.StaticLine(self,-1),pos,(1,2), wx.EXPAND|wx.TOP|wx.BOTTOM)
		but = wx.Button(self, -1, 'Reconnect Remote')
		sz.Add(but, (pos[0]+1,pos[1]), (1, 2), wx.ALIGN_LEFT)
		self.Bind(wx.EVT_BUTTON, self.onReconnect, but)
		return sz

	def createRetractObjApOnGridChangingCheckBox(self, sz, start_position):
		self.widgets['retract obj ap on grid changing'] = wx.CheckBox(self, -1,
			'Retract objective aperture during grid exchange')
		# sz is changed in-place
		sz.Add(self.widgets['retract obj ap on grid changing'], (start_position[0],0), (1,2))
		return (1,0)

	def onReconnect(self, evt):
		self.node.uiClickReconnectRemote()

class TEMParameters(wx.StaticBoxSizer):
	def __init__(self, parent,title,order=[]):
		sb = wx.StaticBox(parent, -1, title)
		wx.StaticBoxSizer.__init__(self, sb, wx.VERTICAL)

		self.parent = parent
		self.sts = {}
		self.sz = wx.GridBagSizer(0, 5)
		self.unit = ''
		self.order = []
		self.setOrder(order)
		self.sz.AddGrowableCol(0)
		self.Add(self.sz, 1, wx.EXPAND|wx.ALL, 3)

	def setOrder(self, name_order):
		'''
		set the inmutable item keys and unit and insert static text sizer
		in oder.
		'''
		if self.order:
			# set Only once
			return
		# order is a list of name of parameters to be displayed
		self.order = name_order
		for i, name in enumerate(self.order):
			stname = wx.StaticText(self.parent, -1, name)
			label = 'Unknown'
			unitkey = '%s unit' % name
			this_unit = self.getUnitFromLabel(label)
			self.sts[unitkey] = wx.StaticText(self.parent, -1, this_unit)
			self.sts[name] = wx.StaticText(self.parent, -1, label)
			self.sz.Add(stname, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.sts[name], (i, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			self.sz.Add(self.sts[unitkey], (i, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

	def setUnit(self, value):
		self.unit = value

	def getUnitFromLabel(self,label):
		try:
			float(label)
			this_unit = self.unit
		except ValueError:
			this_unit = ''
		return this_unit

	def setString(self, values):
		for name in self.order:
			try:
				label = '%s' % (values[name])
				self.sts[name].SetLabel(label)
				this_unit = self.getUnitFromLabel(label)
				unitkey = '%s unit' % name
				self.sts[unitkey].SetLabel(this_unit)
			except (TypeError, KeyError) as e:
				self.sts[name].SetLabel('None')
		self.Layout()

	def setFloat(self, values):
		for name in self.order:
			try:
				label = '%6.4e' % (values[name])
				self.sts[name].SetLabel(label)
				this_unit = self.getUnitFromLabel(label)
				unitkey = '%s unit' % name
				self.sts[unitkey].SetLabel(this_unit)
			except (TypeError, KeyError) as e:
				self.sts[name].SetLabel('None')
			except:
				raise
		self.Layout()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'TEM Controller Test')
			panel = Panel(frame)
			dialog = SettingsDialog(frame, node)
			frame.Fit()
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

