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
ID_ACQUISITION_TYPE = 1010
ID_MEASURE_DRIFT = 1011
ID_DECLARE_DRIFT = 1012
ID_CHECK_DRIFT = 1013
ID_REFRESH = 1014
ID_PAUSES = 1015
ID_AUTO_FOCUS = 1016
ID_MANUAL_FOCUS = 1017
ID_MODEL = 1018

class ToolBar(wx.ToolBar):
	def __init__(self, parent):
		wx.ToolBar.__init__(self, parent, -1)
		self.spacer = wx.StaticText(self, -1, '')
		self.AddControl(self.spacer)

		self.panel = None

		tools = [
			('settings', ID_SETTINGS, 'settings.png', 'Settings', 'onSettingsTool'),
			('acquisition type', ID_ACQUISITION_TYPE, wx.Choice,
				'Acquisition type', 'onAcqTypeChoice'),
			('acquire', ID_ACQUIRE, 'acquire.png', 'Acquire', 'onAcquireTool',),
			('calibrate', ID_CALIBRATE, 'play.png', 'Calibrate',
				'onCalibrateTool',),
			('abort', ID_ABORT, 'stop.png', 'Abort', 'onAbortTool',),
			('play', ID_PLAY, 'play.png', 'Play', 'onPlayTool',),
			('pause', ID_PAUSE, 'pause.png', 'Pause', 'onPauseTool',),
			('stop', ID_STOP, 'stop.png', 'Stop', 'onStopTool',),
			('check drift', ID_CHECK_DRIFT, 'check.png',
				'Check drift', 'onCheckDriftTool', self.AddCheckTool),
			('measure drift', ID_MEASURE_DRIFT, 'ruler.png', 'Measure drift',
				'onMeasureDriftTool',),
			('declare drift', ID_DECLARE_DRIFT, 'declare.png', 'Declare drift',
				'onDeclareDriftTool',),
			('measure', ID_MEASURE, 'ruler.png', 'Measure', 'onMeasureTool',),
			('submit', ID_SUBMIT, 'play.png', 'Submit', 'onSubmitTool',),
			('refresh', ID_REFRESH, 'refresh.png', 'Refresh', 'onRefreshTool',),
			('pauses', ID_PAUSES, 'clock.png', 'Do pauses', 'onPausesTool',
				self.AddCheckTool),
			('auto focus', ID_AUTO_FOCUS, 'autofocus.png', 'Autofocus',
				'onAutoFocusTool', self.AddCheckTool),
			('manual focus', ID_MANUAL_FOCUS, 'manualfocus.png', 'Manual focus',
				'onManualFocusTool'),
			('model', ID_MODEL, 'play.png', 'Model', 'onModelTool',),
		]

		self.order = []
		self.ids = {}
		self.methods = {}
		self.tools = {}
		self.names = {}
		for tool in tools:
			self.order.append(tool[0])
			self.ids[tool[0]] = tool[1]
			self.names[tool[1]] = tool[0]
			self.methods[tool[1]] = tool[4]
			tooltip = tool[3]
			if isinstance(tool[2], type) and issubclass(tool[2], wx.Control):
				control = tool[2](self, tool[1])
				control.SetToolTip(wx.ToolTip(tooltip))
				self.tools[tool[0]] = control
				self.AddControl(control)
			else:
				if tool[2]:
					bitmap = wx.BitmapFromImage(wx.Image(icons.getPath(tool[2])))
				else:
					bitmap = wx.EmptyBitmap(16, 16)
				try:
					self.tools[tool[0]] = tool[5](tool[1], bitmap, shortHelp=tooltip)
				except IndexError:
					self.tools[tool[0]] = self.AddSimpleTool(tool[1], bitmap, tooltip)

		self.Realize()

		for tool in self.order:
			toolid = self.ids[tool]
			if not isinstance(self.tools[tool], wx.ToolBarToolBase):
				self.tools[tool].Show(False)
			self.RemoveTool(toolid)

		self.settings = {}

		self.Bind(wx.EVT_TOOL, self.onEvent)
		self.Bind(wx.EVT_CHOICE, self.onEvent)

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
					if isinstance(self.tools[tool], wx.ToolBarToolBase):
						self.AddToolItem(self.tools[tool])
					else:
						self.AddControl(self.tools[tool])
						self.tools[tool].Show(True)
			else:
				if tool not in tools:
					if not isinstance(self.tools[tool], wx.ToolBarToolBase):
						self.tools[tool].Show(False)
					self.RemoveTool(toolid)
		if tools:
			self._setStates(self.panel)
		self.Realize()
		self.Enable(True)

	def onEvent(self, evt):
		if self.panel is None:
			return


		try:
			name = self.names[evt.GetId()]
		except KeyError:
			raise RuntimeError
		if hasattr(evt, 'IsChecked'):
			self.settings[self.panel][name]['toggled'] = evt.IsChecked()
		if isinstance(evt.GetEventObject(), wx.Choice):
			self.settings[self.panel][name]['selection'] = evt.GetInt()

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
		if panel in self.settings:
			return
		self.settings[panel] = {}
		for tool in panel.tools:
			self.settings[panel][tool] = {}
			self.settings[panel][tool]['enabled'] = True
			if isinstance(self.tools[tool], wx.ToolBarToolBase):
				self.settings[panel][tool]['toggled'] = False
			elif isinstance(self.tools[tool], wx.Choice):
				self.settings[panel][tool]['choices'] = []
				self.settings[panel][tool]['selection'] = -1

	def _setStates(self, panel):
		self._initializeStates(panel)
		for tool in panel.tools:
			toolid = self.ids[tool]
			if isinstance(self.tools[tool], wx.ToolBarToolBase):
				self.EnableTool(toolid, self.settings[panel][tool]['enabled'])
				self.ToggleTool(toolid, self.settings[panel][tool]['toggled'])
			elif isinstance(self.tools[tool], wx.Choice):
				self.tools[tool].Enable(self.settings[panel][tool]['enabled'])
				self.tools[tool].Clear()
				choices = self.settings[panel][tool]['choices']
				if choices:
					self.tools[tool].AppendItems(choices)
				selection = self.settings[panel][tool]['selection']
				if choices and selection >= 0:
					self.tools[tool].SetSelection(selection)

	def getState(self, panel, tool):
		self._initializeStates(panel)
		return self.settings[panel][tool]

	def toggle(self, panel, tool, value):
		self._initializeStates(panel)
		self.settings[panel][tool]['toggled'] = value
		if self.panel is panel:
			toolid = self.ids[tool]
			self.ToggleTool(toolid, value)

	def enable(self, panel, tool, value):
		self._initializeStates(panel)
		self.settings[panel][tool]['enabled'] = value
		if self.panel is panel:
			toolid = self.ids[tool]
			self.EnableTool(toolid, value)

	def setChoices(self, panel, tool, choices):
		self._initializeStates(panel)
		self.settings[panel][tool]['choices'] = choices
		if self.panel is panel:
			self.tools[tool].Clear()
			if choices:
				self.tools[tool].AppendItems(choices)

	def setSelection(self, panel, tool, selection):
		self._initializeStates(panel)
		self.settings[panel][tool]['selection'] = selection
		if self.panel is panel:
			count = self.tools[tool].GetCount()
			if count > 0 and selection >= 0:
				self.tools[tool].SetSelection(selection)

