import wx
from gui.wx.Choice import Choice
import gui.wx.Camera
import gui.wx.Entry
import gui.wx.Presets

class SettingsError(Exception):
	pass

attributes = {
	wx.CheckBox: ('GetValue', 'SetValue', wx.EVT_CHECKBOX),
	wx.Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	Choice: ('GetStringSelection', 'SetStringSelection', wx.EVT_CHOICE),
	gui.wx.Entry.Entry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Entry.IntEntry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Entry.FloatEntry: ('GetValue', 'SetValue', gui.wx.Entry.EVT_ENTRY),
	gui.wx.Presets.PresetChoice:
		('GetStringSelection', 'SetStringSelection',
			gui.wx.Presets.EVT_PRESET_CHOICE),
	gui.wx.Presets.PresetOrder:
		('getValues', 'setValues', gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	gui.wx.Presets.EditPresetOrder:
		('getValues', 'setValues', gui.wx.Presets.EVT_PRESET_ORDER_CHANGED),
	gui.wx.Camera.CameraPanel:
		('getData', 'setData',
			gui.wx.Camera.EVT_CONFIGURATION_CHANGED),
}

class Dialog(wx.Dialog):
	def __init__(self, parent):
		self.node = parent.node

		title = '%s Settings' % self.node.name
		wx.Dialog.__init__(self, parent, -1, title) 

		self.widgets = {}

		sz = self.initialize()

		# buttons
		self.bok = wx.Button(self, wx.ID_OK, 'OK')
		self.bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		self.bapply = wx.Button(self, wx.ID_APPLY, 'Apply')
		szbuttons = wx.GridBagSizer(5, 5)
		szbuttons.Add(self.bok, (0, 0), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		szbuttons.Add(self.bapply, (0, 2), (1, 1), wx.ALIGN_CENTER)

		szmain = wx.GridBagSizer(5, 5)
		for i, s in enumerate(sz):
			szmain.Add(s, (i, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		szmain.Add(szbuttons, (i+1, 0), (1, 1),
								wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 10)

		# set values
		self.getNodeSettings()

		self.SetSizerAndFit(szmain)

		self.Bind(wx.EVT_BUTTON, self.onSet, self.bok)
		self.Bind(wx.EVT_BUTTON, self.onSet, self.bapply)

		for widget in self.widgets.values():
			self.Bind(attributes[widget.__class__][2], self.onModified)

	def initialize(self):
		return []

	def onModified(self, evt):
		if self.getSettings() == self.settings:
			self.bapply.Enable(False)
		else:
			self.bapply.Enable(True)
		evt.Skip()

	def onSet(self, evt):
		try:
			self.setNodeSettings()
			evt.Skip()
		except SettingsError:
			dialog = wx.MessageDialog(self, str(e), 'Settings Error',
																wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

	def getSettings(self):
		settings = {}
		for key, widget in self.widgets.items():
			settings[key] = getattr(widget, attributes[widget.__class__][0])()
		return settings

	def setSettings(self, sd):
		for key, widget in self.widgets.items():
			try:
				getattr(widget, attributes[widget.__class__][1])(sd[key])
			except ValueError:
				raise ValueError('Invalid value %s for widget "%s"' % (sd[key], key))

	def setNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return
		settings = self.getSettings()
		if settings != self.settings:
			settingsdata = node.settingsclass(initializer=settings)
			node.setSettings(settingsdata)
			self.settings = settings
			self.bapply.Enable(False)

	def getNodeSettings(self):
		node = self.GetParent().node
		if node is None:
			return

		settingsdata = node.getSettings()
		self.setSettings(settingsdata)

		self.settings = self.getSettings()
		self.bapply.Enable(False)

