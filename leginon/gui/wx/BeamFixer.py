import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import leginon.gui.wx.Reference
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class BeamFixerPanel(leginon.gui.wx.Reference.ReferencePanel, leginon.gui.wx.Instrument.SelectionMixin):
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Reference.ReferencePanel.__init__(self, *args, **kwargs)
		leginon.gui.wx.Instrument.SelectionMixin.__init__(self)
		self.addImagePanel()
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def onNodeInitialized(self):
		leginon.gui.wx.Reference.ReferencePanel.onNodeInitialized(self)
		leginon.gui.wx.Instrument.SelectionMixin.onNodeInitialized(self)

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onSettingsTool(self, evt):
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Reference.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Reference.ScrolledSettings):
	def initialize(self):
		refsizers = leginon.gui.wx.Reference.ScrolledSettings.initialize(self)
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
		self.widgets['camera settings'].setSize(self.node.instrument.camerasize)

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
