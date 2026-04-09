import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import leginon.gui.wx.ReferenceTimer
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class LppAlignTimerPanel(leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel, leginon.gui.wx.Instrument.SelectionMixin):

	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel.__init__(self, *args, **kwargs)

	def onNodeInitialized(self):
		leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel.onNodeInitialized(self)
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)

	def _SettingsDialog(self,parent):
		return SettingsDialog(parent)

class SettingsDialog(leginon.gui.wx.ReferenceTimer.SettingsDialog):
	def _ScrolledSettings(self,parent):
		# This "private call" ensures that the class in this module is loaded
		# instead of the one in module containing the parent class
		return ScrolledSettings(self,self.scrsize,True)


class ScrolledSettings(leginon.gui.wx.ReferenceTimer.ScrolledSettings):
	def initialize(self):
		refsizers = leginon.gui.wx.ReferenceTimer.ScrolledSettings.initialize(self)
		return refsizers

	def createPrefixSizer(self, start_position):
		start_position = self.createXLppCheckBox(start_position)
		start_position = self.createXtOffsetSizer(start_position)
		start_position = self.createDeltaXtThresholdSizer(start_position)
		return start_position

	def createIntervalEntry(self, start_position):
		new_start = self.createIntervalTimeEntry(start_position)
		return new_start

	def createXLppCheckBox(self, start_position):
		self.widgets['xlpp'] = wx.CheckBox(self, -1, 'Crossed laser plase plate used')
		self.sz.Add(self.widgets['xlpp'], (start_position[0],0), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT |wx.EXPAND|wx.BOTTOM, 20)
		return start_position[0]+1,start_position[1]+1

	def createXtOffsetSizer(self,start_position):
		savesizer = wx.GridBagSizer(5, 4)
		bordersize = 3
		label = wx.StaticText(self, -1, 'xtilt offset:')
		savesizer.Add(label, (0, 0), (1, 4), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'x:')
		savesizer.Add(label, (1, 1), (1, 1), wx.ALIGN_RIGHT)
		self.widgets['xt offset x'] = FloatEntry(self, -1, allownone=False, chars=8, value='0.0')
		savesizer.Add(self.widgets['xt offset x'], (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'y:')
		savesizer.Add(label, (1, 3), (1, 1), wx.ALIGN_RIGHT)
		self.widgets['xt offset y'] = FloatEntry(self, -1, allownone=False, chars=8, value='0.0')
		savesizer.Add(self.widgets['xt offset y'], (1, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		# 
		self.sz.Add(savesizer, (start_position[0],0), (2, 4), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT |wx.EXPAND|wx.BOTTOM, 20)
		return start_position[0]+2,start_position[1]

	def createDeltaXtThresholdSizer(self,start_position):
		savesizer = wx.GridBagSizer(5, 3)
		bordersize = 3
		label = wx.StaticText(self, -1, 'make final correction only after x-tilt changes less than:')
		savesizer.Add(label, (0, 0), (1, 3), wx.ALIGN_CENTER_VERTICAL)
		self.widgets['delta xt threshold'] = FloatEntry(self, -1, allownone=False, chars=12, value='0.000015')
		savesizer.Add(self.widgets['delta xt threshold'], (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'rad')
		savesizer.Add(label, (1, 3), (1, 1), wx.ALIGN_RIGHT)
		self.sz.Add(savesizer, (start_position[0],0), (2, 4), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT |wx.EXPAND|wx.BOTTOM, 20)
		return start_position[0]+2,start_position[1]

class LppAlignTimerPanel(leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel):
	icon = 'alignzlp'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel.__init__(self, *args, **kwargs)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()
