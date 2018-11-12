import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import leginon.gui.wx.ReferenceTimer
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class BeamFixerPanel(leginon.gui.wx.ReferenceTimer.ReferenceTimerPanel, leginon.gui.wx.Instrument.SelectionMixin):
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
		sb = wx.StaticBox(self, -1, 'Beam Fixer')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['shift step'] = FloatEntry(self, -1, min=0.0, chars=6)
		presets = self.node.presets_client.getPresetNames()
		self.widgets['correction presets'] = EditPresetOrder(self, -1)
		self.widgets['correction presets'].setChoices(presets)

		# override preset
		overridebox = wx.StaticBox(self, -1, "Override Preset")
		overridesz = wx.StaticBoxSizer(overridebox, wx.VERTICAL)
		self.widgets['override preset'] = wx.CheckBox(self, -1,
																								'Override Preset')
		self.widgets['instruments'] = leginon.gui.wx.Instrument.SelectionPanel(self, passive=True)
		self.panel.setInstrumentSelection(self.widgets['instruments'])
		self.widgets['camera settings'] = leginon.gui.wx.Camera.CameraPanel(self)
		self.widgets['camera settings'].setGeometryLimits({'size':self.node.instrument.camerasize,'binnings':self.node.instrument.camerabinnings,'binmethod':self.node.instrument.camerabinmethod})

		sz = wx.GridBagSizer(5, 10)
		sz.Add(self.widgets['override preset'], (0, 0), (1, 1),
						wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['instruments'], (1, 0), (1, 1), wx.EXPAND)
		sz.Add(self.widgets['camera settings'], (2, 0), (1, 1), wx.EXPAND)
		overridesz.Add(sz, 0, wx.ALIGN_CENTER|wx.ALL, 5)

		sz = wx.GridBagSizer(5, 5)
		szshift = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Shift Beam by ')
		szshift.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szshift.Add(self.widgets['shift step'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of the image ')
		szshift.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szshift, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['correction presets'], (0, 1), (1, 1), wx.ALIGN_CENTER)
		sbsz.Add(sz)
		sbsz.Add(overridesz)

		return refsizers + [sbsz]
