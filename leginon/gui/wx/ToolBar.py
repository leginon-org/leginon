import icons
import wx

ID_SETTINGS = 1001
ID_ACQUIRE = 1002
ID_PLAY = 1003
ID_PAUSE = 1004
ID_STOP = 1005
ID_CALIBRATE = 1006
ID_MEASURE = 1007
ID_ABORT = 1008
ID_SUBMIT = 1009

class ToolBar(wx.ToolBar):
	def __init__(self, parent):
		wx.ToolBar.__init__(self, parent, -1)
		self.spacer = wx.StaticText(self, -1, '')
		self.AddControl(self.spacer)

		self.panel = None

		tools = [
			('settings', ID_SETTINGS, 'settings.png', 'Settings', 'onSettingsTool'),
			('acquire', ID_ACQUIRE, 'acquire.png', 'Acquire', 'onAcquireTool',),
			('calibrate', ID_CALIBRATE, 'play.png', 'Calibrate',
				'onCalibrateTool',),
			('abort', ID_ABORT, 'stop.png', 'Abort', 'onAbortTool',),
			('play', ID_PLAY, 'play.png', 'Play', 'onPlayTool',),
			('pause', ID_PAUSE, 'pause.png', 'Pause', 'onPauseTool',),
			('stop', ID_STOP, 'stop.png', 'Stop', 'onStopTool',),
			('measure', ID_MEASURE, 'ruler.png', 'Measure', 'onMeasureTool',),
			('submit', ID_SUBMIT, 'play.png', 'Submit', 'onSubmitTool',),
		]

		self.order = []
		self.ids = {}
		self.methods = {}
		self.tools = {}
		for tool in tools:
			self.order.append(tool[0])
			self.ids[tool[0]] = tool[1]
			self.methods[tool[1]] = tool[4]
			if tool[2]:
				bitmap = wx.BitmapFromImage(wx.Image(icons.getPath(tool[2])))
			else:
				bitmap = wx.EmptyBitmap(16, 16)
			tooltip = tool[3]
			self.AddSimpleTool(tool[1], bitmap, tooltip)

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

