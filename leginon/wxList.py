from wxPython.wx import *

class wxListView(wxListBox):
	def __init__(self, parent):
		wxListBox.__init__(self, parent, -1)
		EVT_LISTBOX(self, self.GetId(), self.onSelect)

	def getValues(self):
		values = []
		for i in range(self.GetCount()):
			values.append(self.GetString(i))
		return values

	def setValues(self, values):
		if values != self.getValues():
			self.Clear()
			for value in values:
				self.Append(value)

	def onSelect(self, evt):
		n = evt.GetSelection()
		if n >= 0:
			self.Deselect(n)

class wxListEdit(wxPanel):
	def __init__(self, parent, callback=None):
		self.callback = callback
		wxPanel.__init__(self, parent, -1)
		sizer = wxBoxSizer(wxVERTICAL)
		self.entry = wxTextCtrl(self, -1)
		insertbutton = wxButton(self, -1, 'Insert')
		insertsizer = wxBoxSizer(wxHORIZONTAL)
		insertsizer.Add(self.entry, 1, wxALIGN_CENTER|wxALL)
		insertsizer.Add(insertbutton, 0, wxALIGN_CENTER|wxALL, 3)
		sizer.Add(insertsizer, 0, wxEXPAND)
		self.listbox = wxListBox(self, -1)
		sizer.Add(self.listbox, 1, wxEXPAND)
		self.deletebutton = wxButton(self, -1, 'Delete')
		self.deletebutton.Enable(False)
		self.upbutton = wxButton(self, -1, 'Up')
		self.upbutton.Enable(False)
		self.downbutton = wxButton(self, -1, 'Down')
		self.downbutton.Enable(False)
		buttonsizer = wxBoxSizer(wxHORIZONTAL)
		buttonsizer.Add(self.deletebutton, 0, wxALIGN_CENTER|wxALL, 3)
		buttonsizer.Add(self.upbutton, 0, wxALIGN_CENTER|wxALL, 3)
		buttonsizer.Add(self.downbutton, 0, wxALIGN_CENTER|wxALL, 3)
		sizer.Add(buttonsizer, 0, wxALIGN_CENTER|wxALL)
		self.SetSizerAndFit(sizer)

		EVT_BUTTON(insertbutton, insertbutton.GetId(), self.onInsert)
		EVT_BUTTON(self.deletebutton, self.deletebutton.GetId(), self.onDelete)
		EVT_BUTTON(self.upbutton, self.upbutton.GetId(), self.onUp)
		EVT_BUTTON(self.downbutton, self.downbutton.GetId(), self.onDown)
		EVT_LISTBOX(self.listbox, self.listbox.GetId(), self.onSelect)

	def getValues(self):
		values = []
		for i in range(self.listbox.GetCount()):
			try:
				values.append(eval(self.listbox.GetString(i)))
			except:
				print 'Error evaluating list values'
		return values

	def setValues(self, values):
		if values != self.getValues():
			self.listbox.Clear()
			for value in values:
				if type(value) is str:
					value = '"%s"' % value
				self.listbox.Append(str(value))

	def doCallback(self):
		if callable(self.callback):
			self.callback(self.getValues())

	def onInsert(self, evt):
		value = self.entry.GetValue()
		try:
			eval(value)
		except:
			print 'Error evaluating value'
			return
		n = self.listbox.GetSelection()
		if n < 0:
			self.listbox.Append(value)
		else:
			self.listbox.InsertItems([value], n)
			self.updateButtons(n + 1)
		self.doCallback()

	def onDelete(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0:
			self.listbox.Delete(n)
		count = self.listbox.GetCount()
		if n < count:
			self.listbox.Select(n)
			self.updateButtons(n)
		elif count > 0:
			self.listbox.Select(n - 1)
			self.updateButtons(n - 1)
		else:
			self.deletebutton.Enable(False)
		self.doCallback()

	def onUp(self, evt):
		n = self.listbox.GetSelection()
		if n > 0:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n - 1)
			self.listbox.Select(n - 1)
		self.updateButtons(n - 1)
		self.doCallback()

	def onDown(self, evt):
		n = self.listbox.GetSelection()
		if n >= 0 and n < self.listbox.GetCount() - 1:
			string = self.listbox.GetString(n)
			self.listbox.Delete(n)
			self.listbox.InsertItems([string], n + 1)
			self.listbox.Select(n + 1)
		self.updateButtons(n + 1)
		self.doCallback()

	def onSelect(self, evt):
		self.deletebutton.Enable(True)
		self.updateButtons(evt.GetSelection())

	def updateButtons(self, n):
		if n > 0:
			self.upbutton.Enable(True)
		else:
			self.upbutton.Enable(False)
		if n < self.listbox.GetCount() - 1:
			self.downbutton.Enable(True)
		else:
			self.downbutton.Enable(False)

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'List Edit')
			self.SetTopWindow(frame)
			self.panel = wxPanel(frame, -1)
			self.sizer = wxBoxSizer(wxVERTICAL)
			self.listedit = wxListEdit(self.panel, self.callback)
			self.sizer.Add(self.listedit, 1, wxEXPAND)
			self.panel.SetSizerAndFit(self.sizer)
			frame.Fit()
			frame.Show(True)
			return True

		def callback(self, values):
			self.listedit.setValues(values)

	app = MyApp(0)
	app.MainLoop()

