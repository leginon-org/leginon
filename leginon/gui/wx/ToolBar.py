import icons
import wx

ID_SETTINGS = 1
ID_ACQUIRE = 2
ID_PLAY = 4
ID_PAUSE = 8
ID_STOP = 16

class ToolBar(wx.ToolBar):
	def __init__(self, parent):
		wx.ToolBar.__init__(self, parent, -1)
		self.spacer = wx.StaticText(self, -1, '')
		self.AddControl(self.spacer)

		self.panel = None

		self.order = [
			'settings',
			'acquire',
			'play',
			'pause',
			'stop',
		]

		self.ids = {
			'settings': ID_SETTINGS,
			'acquire': ID_ACQUIRE,
			'play': ID_PLAY,
			'pause': ID_PAUSE,
			'stop': ID_STOP,
		}

		self.bitmaps = {
			'settings': wx.BitmapFromImage(wx.Image(icons.getPath('settings.png')))
		}

		self.tooltips = {
			'settings': 'Settings',
			'acquire': 'Acquire',
			'play': 'Play',
			'pause': 'Pause',
			'stop': 'Stop',
		}

		self.methods = {
			ID_SETTINGS: 'onSettingsTool',
			ID_ACQUIRE: 'onAcquireTool',
			ID_PLAY: 'onPlayTool',
			ID_PAUSE: 'onPauseTool',
			ID_STOP: 'onStopTool',
		}

		self.tools = {}

		for tool in self.order:
			toolid = self.ids[tool]
			try:
				bitmap = self.bitmaps[tool]
			except KeyError:
				bitmap = wx.EmptyBitmap(16, 16)
			tooltip = self.tooltips[tool]
			self.AddSimpleTool(toolid, bitmap, tooltip)

		self.Realize()

		for tool in self.order:
			toolid = self.ids[tool]
			self.tools[tool] = self.RemoveTool(toolid)

		self.states = {}

		self.Bind(wx.EVT_TOOL, self.onTool)

	def setSpacerWidth(self, width):
		self.spacer.SetSize((width, -1))
		self.Realize()

	def setPanel(self, panel):
		self.panel = panel
		if not hasattr(panel, 'tools') or panel.tools is None:
			self.setTools([])
		else:
			self.setTools(panel.tools)

	def setTools(self, tools):
		self.Enable(False)
		for tool in self.order:
			toolid = self.ids[tool]
			if self.FindById(toolid) is None:
				if tool in tools:
					self.AddToolItem(self.tools[tool])
			else:
				if tool not in tools:
					self.RemoveTool(toolid)
		if tools:
			self._setStates(self.panel)
		self.Realize()
		self.Enable(True)

	def onTool(self, evt):
		if self.panel is None:
			return
		try:
			name = self.methods[evt.GetId()]
		except KeyError:
			raise RuntimeError
		try:
			method = getattr(self.panel, name)
		except AttributeError:
			raise RuntimeError
		method(evt)

	def _initializeStates(self, panel):
		if panel in self.states:
			return
		self.states[panel] = {}
		for tool in panel.tools:
			self.states[panel][tool] = {'enabled': True, 'toggled': False}

	def _setStates(self, panel):
		self._initializeStates(panel)
		for tool, toolid in self.ids.items():
			if self.FindById(toolid) is not None:
				self.ToggleTool(toolid, self.states[panel][tool]['toggled'])
				self.EnableTool(toolid, self.states[panel][tool]['enabled'])

	def toggle(self, panel, tool, value):
		self._initializeStates(panel)
		self.states[panel][tool]['toggled'] = value
		if self.panel is panel:
			toolid = self.ids[tool]
			self.ToggleTool(toolid, value)

	def enabled(self, panel, tool, value):
		self._initializeStates(panel)
		self.states[panel][tool]['enabled'] = value
		if self.panel is panel:
			toolid = self.ids[tool]
			self.EnableTool(toolid, value)

