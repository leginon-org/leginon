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

		self.szsettings = wx.GridBagSizer(5, 5)
		newrow,newcol = self.createAdjustMethodSelector((0,0))
		newrow,newcol = self.createRequiredDoseEntry((newrow,0))
		newrow,newcol = self.createMaxExposureTimeEntry((newrow,0))
		newrow,newcol = self.createMaxBeamDiameterEntry((newrow,0))
		newrow,newcol = self.createCorrectionPresetsEditor((0,newcol))

		sbsz.Add(self.szsettings)

		return refsizers + [sbsz]

	def createAdjustMethodSelector(self,start_position):
		# define widget
		regtypes = self.node.getAdjustMethods()
		self.widgets['adjust method'] = Choice(self, -1, choices=regtypes)
		# make sizer
		sz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Adjust exposure dose by changing')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['adjust method'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szsettings.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createRequiredDoseEntry(self,start_position):
		# define widget
		self.widgets['required dose'] = FloatEntry(self, -1, min=0.0, chars=6)
		# make sizer
		sz = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Match the exposure of the first preset choice to ')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['required dose'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'e / A^2 ')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szsettings.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]


	def createMaxExposureTimeEntry(self,start_position):
		# define widget
		self.widgets['max exposure time'] = IntEntry(self, -1, min=0, chars=6)
		# make sizer
		sz = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Maximal exposure time')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max exposure time'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'ms')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szsettings.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createMaxBeamDiameterEntry(self,start_position):
		# define widget
		self.widgets['max beam diameter'] = FloatEntry(self, -1, min=0.0, chars=6)
		# make sizer
		sz = wx.GridBagSizer(5,5)
		label = wx.StaticText(self, -1, 'Maximal beam diameter')
		sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.widgets['max beam diameter'], (0, 1), (1, 1),
		wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'um')
		sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		# add to main
		total_length = (1,1)
		self.szsettings.Add(sz, start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]

	def createCorrectionPresetsEditor(self,start_position):
		# define widget
		presets = self.node.presets_client.getPresetNames()
		self.widgets['correction presets'] = EditPresetOrder(self, -1)
		self.widgets['correction presets'].setChoices(presets)
		# add to main
		total_length = (4,1)
		self.szsettings.Add(self.widgets['correction presets'], start_position, total_length,
				  wx.ALIGN_CENTER)
		return start_position[0]+total_length[0],start_position[1]+total_length[1]
