import icons
import wx
import wx.lib.buttons

def getBitmap(filename):
	iconpath = icons.getPath(filename)
	wximage = wx.Image(iconpath)
	bitmap = wx.BitmapFromImage(wximage)
	return bitmap

PresetOrderChangedEventType = wx.NewEventType()
PresetChoiceEventType = wx.NewEventType()
PresetsChangedEventType = wx.NewEventType()
NewPresetEventType = wx.NewEventType()
PresetSelectedEventType = wx.NewEventType()

EVT_PRESET_ORDER_CHANGED = wx.PyEventBinder(PresetOrderChangedEventType)
EVT_PRESET_CHOICE = wx.PyEventBinder(PresetChoiceEventType)
EVT_PRESETS_CHANGED = wx.PyEventBinder(PresetsChangedEventType)
EVT_NEW_PRESET = wx.PyEventBinder(NewPresetEventType)
EVT_PRESET_SELECTED = wx.PyEventBinder(PresetSelectedEventType)

class PresetOrderChangedEvent(wx.PyCommandEvent):
	def __init__(self, presets, source):
		wx.PyCommandEvent.__init__(self, PresetOrderChangedEventType,
																source.GetId())
		self.SetEventObject(source)
		self.presets = presets

class PresetsChoiceEvent(wx.PyCommandEvent):
	def __init__(self, choice, source):
		wx.PyCommandEvent.__init__(self, PresetChoiceEventType, source.GetId())
		self.SetEventObject(source)
		self.SetString(choice)
		self.choice = choice

class PresetsChangedEvent(wx.PyEvent):
	def __init__(self, presets):
		wx.PyEvent.__init__(self)
		self.SetEventType(PresetsChangedEventType)
		self.presets = presets

class NewPresetEvent(wx.PyEvent):
	def __init__(self):
		wx.PyEvent.__init__(self)
		self.SetEventType(NewPresetEventType)

class PresetSelectedEvent(wx.PyCommandEvent):
	def __init__(self, source, presetname):
		wx.PyCommandEvent.__init__(self, PresetSelectedEventType, source.GetId())
		self.SetEventObject(source)
		self.SetString(presetname)
		self.presetname = presetname

class PresetChoice(wx.Choice):
	def __init__(self, *args, **kwargs):
		wx.Choice.__init__(self, *args, **kwargs)
		self.Enable(False)

		self.Bind(wx.EVT_CHOICE, self.onChoice)
		self.Bind(EVT_PRESETS_CHANGED, self.onPresetsChanged)

	def onChoice(self, evt):
		evt = PresetsChoiceEvent(evt.GetString(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onPresetsChanged(self, evt):
		self.setChoices(evt.presets)

	def setChoices(self, choices):
		selection = self.GetStringSelection()
		self.Freeze()
		self.Clear()
		for c in choices:
			if c:
				self.Append(c)
		if choices:
			n = self.FindString(selection)
			if n == wx.NOT_FOUND:
				self.SetSelection(0)
			else:
				self.SetSelection(n)
		self.Enable(choices)
		self.Thaw()

	def SetStringSelection(self, string):
		if string is not None and self.GetCount() > 0:
			n = self.FindString(string)
			if n == wx.NOT_FOUND:
				self.SetSelection(0)
			else:
				self.SetSelection(n)

class PresetOrder(wx.Panel):
	def __init__(self, parent, id, **kwargs):
		wx.Panel.__init__(self, parent, id, **kwargs)
		self._widgets()
		self._sizer()
		self._bind()

	def _widgets(self, label='Presets Order'):
		if label:
			self.storder = wx.StaticText(self, -1, label)
		self.listbox = wx.ListBox(self, -1)
		self.upbutton = self._bitmapButton('up', 'Move preset up in cycle')
		self.downbutton = self._bitmapButton('down', 'Move preset down in cycle')

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.listbox, (1, 0), (2, 1), wx.EXPAND|wx.ALL)
		sizer.Add(self.upbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.downbutton, (2, 1), (1, 1),
							wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
		sizer.AddGrowableRow(2)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		self.Bind(wx.EVT_BUTTON, self.onUp, self.upbutton)
		self.Bind(wx.EVT_BUTTON, self.onDown, self.downbutton)
		self.Bind(wx.EVT_LISTBOX, self.onSelect, self.listbox)
		self.Bind(EVT_PRESETS_CHANGED, self.onPresetsChanged)

	def _bitmapButton(self, name, tooltip=None):
		bitmap = getBitmap('%s.png' % name)
		button = wx.lib.buttons.GenBitmapButton(self, -1, bitmap, size=(20, 20))
		button.SetBezelWidth(1)
		button.Enable(False)
		if tooltip is not None:
			button.SetToolTip(wx.ToolTip(tooltip))
		return button

	def onUp(self, evt):
		n = self.listbox.GetSelection()
		if n > 0:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n - 1)
			self.listbox.SetSelection(n - 1)
		self.updateButtons(n - 1)
		self.presetsEditEvent()

	def onDown(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0 and n < self.listbox.GetCount() - 1:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n + 1)
			self.listbox.SetSelection(n + 1)
		self.updateButtons(n + 1)
		self.presetsEditEvent()

	def getSelectedPreset(self):
		presetname = self.listbox.GetStringSelection()
		if not presetname:
			presetname = None
		return presetname

	def setSelectedPreset(self):
		n = self.listbox.FindString(presetname)
		if n == wx.NOT_FOUND:
			return False
		self.listbox.SetSelection(n)
		return True

	def onPresetsChanged(self, evt):
		self.setChoices(evt.presets)

	def setChoices(self, choices):
		self.setValues(choices)

	def getValues(self):
		values = []
		for i in range(self.listbox.GetCount()):
			try:
				values.append(self.listbox.GetString(i))
			except ValueError:
				raise
		return values

	def setValues(self, values):
		filtered = []
		for v in values:
			if v:
				filtered.append(v)
		values = filtered
		count = self.listbox.GetCount()
		if values is None:
			values = []
		n = len(values)
		if count < n:
			nsame = count
		else:
			nsame = n
		for i in range(nsame):
			try:
				if self.listbox.GetString(i) != values[i]:
					self.listbox.SetString(i, values[i])
			except ValueError:
				raise
		if count < n:
			self.listbox.InsertItems(values[nsame:], nsame)
		elif count > n:
			for i in range(count - 1, n - 1, -1):
				self.listbox.Delete(i)

	def presetsEditEvent(self):
		evt = PresetOrderChangedEvent(self.getValues(), self)
		self.GetEventHandler().AddPendingEvent(evt)

	def onSelect(self, evt):
		self.updateButtons(evt.GetInt())
		evt = PresetSelectedEvent(self, evt.GetString())
		self.GetEventHandler().AddPendingEvent(evt)

	def updateButtons(self, n):
		if n > 0:
			self.upbutton.Enable(True)
		else:
			self.upbutton.Enable(False)
		if n < self.listbox.GetCount() - 1:
			self.downbutton.Enable(True)
		else:
			self.downbutton.Enable(False)

class EditPresetOrder(PresetOrder):
	def _widgets(self):
		PresetOrder._widgets(self)
		self.choice = wx.Choice(self, -1)
		self.choice.Enable(False)
		self.insertbutton = self._bitmapButton('plus', 'Insert preset into cycle')
		self.deletebutton = self._bitmapButton('minus', 'Remove preset from cycle')

	def _sizer(self):
		sizer = wx.GridBagSizer(3, 3)
		sizer.Add(self.storder, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALL)
		sizer.Add(self.choice, (1, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL)
		sizer.Add(self.insertbutton, (1, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.listbox, (2, 0), (3, 1), wx.EXPAND|wx.ALL)
		sizer.Add(self.deletebutton, (2, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.upbutton, (3, 1), (1, 1), wx.ALIGN_CENTER|wx.ALL)
		sizer.Add(self.downbutton, (4, 1), (1, 1),
							wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP|wx.ALL)
		sizer.AddGrowableRow(4)
		self.SetSizerAndFit(sizer)

	def _bind(self):
		PresetOrder._bind(self)
		self.Bind(wx.EVT_BUTTON, self.onInsert, self.insertbutton)
		self.Bind(wx.EVT_BUTTON, self.onDelete, self.deletebutton)

	def setChoices(self, choices):
		self.Freeze()
		self.choice.Clear()
		self.choice.AppendItems(choices)
		if choices:
			self.choice.SetSelection(0)
		self.choice.Enable(choices)
		self.insertbutton.Enable(choices)
		self.Thaw()

	def onInsert(self, evt):
		try:
			string = self.choice.GetStringSelection()
		except ValueError:
			return
		n = self.listbox.GetSelection()
		if n < 0:
			self.listbox.Append(string)
		else:
			self.listbox.InsertItems([string], n)
			self.updateButtons(n + 1)
		self.presetsEditEvent()

	def onDelete(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0:
			self.listbox.Delete(n)
		count = self.listbox.GetCount()
		if n < count:
			self.listbox.SetSelection(n)
			self.updateButtons(n)
		elif count > 0:
			self.listbox.SetSelection(n - 1)
			self.updateButtons(n - 1)
		else:
			self.deletebutton.Enable(False)
		self.presetsEditEvent()

	def onSelect(self, evt):
		PresetOrder.onSelect(self, evt)
		self.deletebutton.Enable(True)

