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
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)

	def onNodeInitialized(self):
		leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel.onNodeInitialized(self)
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.ReferenceTimer.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,True)

class ScrolledSettings(leginon.gui.wx.ReferenceTimer.ScrolledSettings):
	def initialize(self):
		refsizers = leginon.gui.wx.ReferenceTimer.ScrolledSettings.initialize(self)
		return refsizers

class LppAlignTimerPanel(leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel):
	icon = 'alignzlp'
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel.__init__(self, *args, **kwargs)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()
