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
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_XY, 'xy',
													shortHelpString='Reset stage X,Y to 0,0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_Z, 'z',
													shortHelpString='Reset stage Z to 0')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_RESET_ALPHA, 'alpha',
													shortHelpString='Reset stage alpha tilt to 0')

		self.orders = ['column','projection','buffer tank']
		self.sz_pressure = TEMParameters(self,'Gauge Pressure', self.orders)
		self.szmain.Add(self.sz_pressure, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.szmain.AddGrowableRow(0)
		self.szmain.AddGrowableCol(0)

		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)

		self.insertPresetSelector(2)
		self.toolbar.Bind(wx.EVT_TOOL, self.onGetPresetTool,
											id=leginon.gui.wx.ToolBar.ID_GET_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSendPresetTool,
											id=leginon.gui.wx.ToolBar.ID_SEND_PRESET)
		self.toolbar.Bind(wx.EVT_TOOL, self.onSettingsTool,
											id=leginon.gui.wx.ToolBar.ID_SETTINGS)
		self.toolbar.Bind(wx.EVT_TOOL, self.onAcquireTool,
											id=leginon.gui.wx.ToolBar.ID_ACQUIRE)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetXY,
											id=leginon.gui.wx.ToolBar.ID_RESET_XY)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetZ,
											id=leginon.gui.wx.ToolBar.ID_RESET_Z)
		self.toolbar.Bind(wx.EVT_TOOL, self.onResetAlpha,
											id=leginon.gui.wx.ToolBar.ID_RESET_ALPHA)

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
		args = (presetname,)
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.uiSendPreset,args=args).start()

	def onSendPresetDone(self):
		self._acquisitionEnable(True)

	def onSetTEMParamDone(self):
		self.displayPressures()
		self._acquisitionEnable(True)

	def onRefreshDisplay(self,evt):
		self.displayPressures()

	def displayPressures(self):
		unit = 'Pascal'
		pressures = self.node.getPressuresToDisplay(unit)
		self.sz_pressure.setUnit(unit)
		self.sz_pressure.set(pressures)
		self.szmain.Layout()

	def _acquisitionEnable(self, enable):
		self.toolbar.Enable(enable)

	def onAcquisitionDone(self, evt):
		self._acquisitionEnable(True)

	def onResetXY(self, evt):
		self.node.onResetXY()

	def onResetZ(self, evt):
		self.node.onResetZ()

	def onResetAlpha(self, evt):
		self.node.onResetAlpha()

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self,show_basic=True)
		dialog.ShowModal()
		dialog.Destroy()

	def onAcquireTool(self, evt):
		self._acquisitionEnable(False)
		threading.Thread(target=self.node.onOpenColumnValve).start()

class SettingsDialog(leginon.gui.wx.Settings.Dialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Settings.ScrolledDialog):
	def initialize(self):
		leginon.gui.wx.Settings.ScrolledDialog.initialize(self)
		sb = wx.StaticBox(self, -1, 'TEM Controller')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		sz = self.addSettings()
		sbsz.Add(sz, 0, wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, 5)
		return [sbsz]

	def addSettings(self):
		sz = wx.GridBagSizer(5, 10)
		return sz

class TEMParameters(wx.StaticBoxSizer):
	def __init__(self, parent,title,order=[]):
		sb = wx.StaticBox(parent, -1, title)
		wx.StaticBoxSizer.__init__(self, sb, wx.VERTICAL)

		# order is a list of name of parameters to be displayed
		self.order = order

		self.sts = {}
		sz = wx.GridBagSizer(0, 5)
		self.unit = ''
		for i, name in enumerate(self.order):
			stname = wx.StaticText(parent, -1, name)
			label = 'Unknown'
			unitkey = '%s unit' % name
			self.sts[unitkey] = wx.StaticText(parent, -1, self.unit)
			self.sts[name] = wx.StaticText(parent, -1, label)
			sz.Add(stname, (i, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			sz.Add(self.sts[name], (i, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
			sz.Add(self.sts[unitkey], (i, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.AddGrowableCol(0)
		self.Add(sz, 1, wx.EXPAND|wx.ALL, 3)

	def setUnit(self, value):
		self.unit = value

	def set(self, values):
		for name in self.order:
			try:
				label = '%5.4f' % (values[name])
				self.sts[name].SetLabel(label)
				unitkey = '%s unit' % name
				self.sts[unitkey].SetLabel(self.unit)
			except (TypeError, KeyError), e:
				self.sts[name].SetLabel('None')
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

