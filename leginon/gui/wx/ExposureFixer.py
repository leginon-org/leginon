import wx

from leginon.gui.wx.Choice import Choice
from leginon.gui.wx.Entry import FloatEntry, IntEntry
from leginon.gui.wx.Presets import EditPresetOrder, EVT_PRESET_ORDER_CHANGED
import leginon.gui.wx.Reference
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar

class ExposureFixerPanel(leginon.gui.wx.Reference.ReferencePanel, leginon.gui.wx.Instrument.SelectionMixin):
	imagepanelclass = leginon.gui.wx.ImagePanel.ImagePanel
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Reference.ReferencePanel.__init__(self, *args, **kwargs)
		self.addImagePanel()
		self.szmain.AddGrowableRow(1)
		self.szmain.AddGrowableCol(0)
		self.SetSizer(self.szmain)
		self.SetAutoLayout(True)
		self.SetupScrolling()

	def addImagePanel(self):
		# image
		self.imagepanel = self.imagepanelclass(self, -1)
		self.imagepanel.addTypeTool('Image', display=True)
		self.imagepanel.selectiontool.setDisplayed('Image', True)
		self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND|wx.ALL, 3)

	def onSettingsTool(self, evt):
		# can not inherit for some reason
		dialog = SettingsDialog(self)
		dialog.ShowModal()
		dialog.Destroy()

class SettingsDialog(leginon.gui.wx.Reference.SettingsDialog):
	def initialize(self):
		return ScrolledSettings(self,self.scrsize,False)

class ScrolledSettings(leginon.gui.wx.Reference.ScrolledSettings):
	def initialize(self):
		refsizers = leginon.gui.wx.Reference.ScrolledSettings.initialize(self)
		sb = wx.StaticBox(self, -1, 'Exposure Fixer')
		sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)

		self.widgets['required dose'] = FloatEntry(self, -1, min=0.0, chars=6)
		self.widgets['max exposure time'] = IntEntry(self, -1, min=0, chars=6)
		presets = self.node.presets_client.getPresetNames()
		self.widgets['correction presets'] = EditPresetOrder(self, -1)
		self.widgets['correction presets'].setChoices(presets)
		'''
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
		'''
		sz = wx.GridBagSizer(5, 5)
		szshift = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Match the exposure of the first preset choice to ')
		szshift.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		szshift.Add(self.widgets['required dose'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'e / A^2 ')
		szshift.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztime = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Maximal exposure time')
		sztime.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sztime.Add(self.widgets['max exposure time'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'ms')
		sztime.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(szshift, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(sztime, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['correction presets'], (0, 1), (2, 1), wx.ALIGN_CENTER)
		sbsz.Add(sz)
		#sbsz.Add(overridesz)

		return refsizers + [sbsz]
