import gui.wx.Data
import gui.wx.Node
import gui.wx.Presets
import wx
import wx.lib.masked

class Panel(gui.wx.Node.Panel):
	def __init__(self, parent, name):
		gui.wx.Node.Panel.__init__(self, parent, -1,
																name='%s.pMosaicTargetMaker' % name)
		self.node = None

		self.szmain = wx.GridBagSizer(5, 5)

		self.szstatus = self._getStaticBoxSizer('Status', (0, 0), (1, 1),
																						wx.EXPAND|wx.ALL)
		self.ststatus = wx.StaticText(self, -1, '')
		self.szstatus.Add(self.ststatus, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.szsettings = self._getStaticBoxSizer('Settings', (1, 0), (1, 1),
																							wx.ALL)

		label = wx.StaticText(self, -1, 'Preset:')
		self.szsettings.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.presetchoice = gui.wx.Presets.PresetChoice(self, -1, name='pcPreset')
		self.szsettings.Add(self.presetchoice, (0, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Atlas label:')
		self.szsettings.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.tclabel = wx.TextCtrl(self, -1, '', name='tcLabel')
		self.szsettings.Add(self.tclabel, (1, 1), (1, 1),
												wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Atlas radius:')
		self.szsettings.Add(label, (0, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.ncradius = wx.lib.masked.NumCtrl(self, -1, 0.5,
																				integerWidth=1,
																				fractionWidth=2,
																				allowNone=False,
																				allowNegative=False,
																				name='ncRadius')
		self.szsettings.Add(self.ncradius, (0, 4), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'microns')
		self.szsettings.Add(label, (0, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		label = wx.StaticText(self, -1, 'Image overlap:')
		self.szsettings.Add(label, (1, 3), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.ncoverlap = wx.lib.masked.NumCtrl(self, -1, 0.0,
								 													 integerWidth=2,
								 													 fractionWidth=0,
								 													 allowNone=False,
								 													 allowNegative=False,
								 													 name='ncOverlap')
		self.szsettings.Add(self.ncoverlap, (1, 4), (1, 1),
												wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, '%')
		self.szsettings.Add(label, (1, 5), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		self.bcreate = wx.Button(self, -1, 'Create Atlas')
		self.szmain.Add(self.bcreate, (2, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		self.SetSizerAndFit(self.szmain)
		self.SetupScrolling()

		self.Bind(wx.EVT_BUTTON, self.onCreateAtlas, self.bcreate)

		self.Bind(gui.wx.Node.EVT_NODE_INITIALIZED, self.onNodeInitialized)
		self.Bind(gui.wx.Node.EVT_SET_STATUS, self.onSetStatus)

	def initializeValues(self):
		self.onNewPreset()
		# TODO: handle preset validation
		gui.wx.Data.setWindowFromDB(self.presetchoice)
		gui.wx.Data.setWindowFromDB(self.tclabel)
		gui.wx.Data.setWindowFromDB(self.ncradius)
		gui.wx.Data.setWindowFromDB(self.ncoverlap)

		gui.wx.Data.bindWindowToDB(self.presetchoice)
		gui.wx.Data.bindWindowToDB(self.tclabel)
		gui.wx.Data.bindWindowToDB(self.ncradius)
		gui.wx.Data.bindWindowToDB(self.ncoverlap)

		self.node.preset = self.presetchoice.GetStringSelection()
		self.node.label = self.tclabel.GetValue()
		self.node.radius = self.ncradius.GetValue()
		self.node.overlap = self.ncoverlap.GetValue()

		self.Bind(gui.wx.Presets.EVT_PRESET_CHOICE, self.onPresetChoice)
		self.Bind(wx.EVT_TEXT, self.onLabel, self.tclabel)
		self.Bind(wx.lib.masked.EVT_NUM, self.onRadius, self.ncradius)
		self.Bind(wx.lib.masked.EVT_NUM, self.onOverlap, self.ncoverlap)

	def onNodeInitialized(self, evt):
		self.node = evt.node
		self.initializeValues()
		evt.event.set()

	def onSetStatus(self, evt):
		self.ststatus.SetLabel(evt.status)

	def onCreateAtlas(self, evt):
		self.node.makeMosaicTargetList()

	def onNewPreset(self, evt=None):
		presets = self.node.presetsclient.getPresetNames()
		if presets:
			evt = gui.wx.Presets.PresetsChangedEvent(presets)
			self.presetchoice.GetEventHandler().AddPendingEvent(evt)

	def onPresetChoice(self, evt):
		self.node.preset = evt.choice

	def onLabel(self, evt):
		self.node.label = evt.GetString()

	def onRadius(self, evt):
		self.node.radius = evt.GetValue()

	def onOverlap(self, evt):
		self.node.overlap = evt.GetValue()

