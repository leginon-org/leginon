from wxPython.wx import *

class wxListView(wxListBox):
	def __init__(self, parent):
		wxListBox.__init__(self, parent, -1)
		EVT_LISTBOX(self, self.GetId(), self.onSelect)

	def toString(self, value):
		return str(value)

	def setValues(self, values):
		count = self.GetCount()
		n = len(values)
		if count < n:
			nsame = count
		else:
			nsame = n
		for i in range(nsame):
			if self.GetString(i) != self.toString(values[i]):
				self.SetString(i, self.toString(values[i]))
		if count < n:
			self.InsertItems(map(self.toString, values[nsame:]), nsame)
		elif count > n:
			for i in range(count - 1, n - 1, -1):
				self.Delete(i)

	def onSelect(self, evt):
		n = evt.GetSelection()
		if n >= 0:
			self.Deselect(n)

#class wxListViewSelect(wxComboBox):
class wxListViewSelect(wxChoice):
	def __init__(self, parent, selectcallback=None):
		self.selectcallback = selectcallback
#		wxComboBox.__init__(self, parent, -1, style=wxCB_DROPDOWN|wxCB_READONLY)
#		EVT_COMBOBOX(self, self.GetId(), self.onSelect)
		wxChoice.__init__(self, parent, -1)
		EVT_CHOICE(self, self.GetId(), self.onSelect)

	def toString(self, value):
		return str(value)

	def setValues(self, values):
		if not values:
			self.Clear()
			return
		self.Freeze()
		count = self.GetCount()
		n = len(values)
		if count < n:
			nsame = count
		else:
			nsame = n
		for i in range(nsame):
			try:
				if self.GetString(i) != self.toString(values[i]):
					nsame = i
					break
			except ValueError:
				self.Thaw()
				raise
		j = nsame
		for j in range(nsame, min(count, n)):
			self.SetString(j, self.toString(values[j]))
		if count > j:
			for i in range(count - 1, j - 1, -1):
				self.Delete(i)
		if j < n:
			for i in range(j, n):
				self.Append(self.toString(values[i]))
		self.Thaw()

	def select(self, value):
		if value is None:
			n = self.GetSelection()
			if n >= 0:
				self.SetSelection(-1)
		else:
			self.SetSelection(value)

	def onSelect(self, evt):
		if callable(self.selectcallback):
			try:
				self.selectcallback(evt.GetSelection())
			except ValueError:
				raise

class wxListEdit(wxPanel):
	def __init__(self, parent, editcallback=None):
		self.editcallback = editcallback
		wxPanel.__init__(self, parent, -1)
		sizer = wxBoxSizer(wxVERTICAL)
		self.entry = wxTextCtrl(self, -1, style=wxTE_PROCESS_ENTER)
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
		EVT_TEXT_ENTER(self.entry, self.entry.GetId(), self.onInsert)

	def fromString(self, string):
		try:
			return eval(string)
		except:
			raise ValueError('Cannot evaluate string to value')

	def toString(self, value):
		if type(value) is str:
			return '"%s"' % value
		else:
			return str(value)

	def getValues(self):
		values = []
		for i in range(self.listbox.GetCount()):
			try:
				values.append(self.fromString(self.listbox.GetString(i)))
			except ValueError:
				raise
		return values

	def setValues(self, values):
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
				if self.fromString(self.listbox.GetString(i)) != values[i]:
					self.listbox.SetString(i, self.toString(values[i]))
			except ValueError:
				raise
		if count < n:
			self.listbox.InsertItems(map(self.toString, values[nsame:]), nsame)
		elif count > n:
			for i in range(count - 1, n - 1, -1):
				self.listbox.Delete(i)

	def doCallback(self):
		if callable(self.editcallback):
			self.editcallback(self.getValues())

	def fakeInsert(self):
		count = self.listbox.GetCount()
		self.listbox.Append('')
		self.listbox.Delete(count)

	def onInsert(self, evt):
		try:
			value = self.fromString(self.entry.GetValue())
		except ValueError:
			self.fakeInsert()
			return
		string = self.toString(value)
		n = self.listbox.GetSelection()
		if n < 0:
			self.listbox.Append(string)
		else:
			self.listbox.InsertItems([string], n)
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

class wxColumnList(wxListCtrl):
	def __init__(self, parent):
			wxListCtrl.__init__(self, parent, -1, style=wxLC_REPORT)

	def getValues(self):
		value = {}
		value['columns'] = []
		for i in range(self.GetColumnCount()):
			value['columns'].append(self.GetColumn(i).GetText())
		value['items'] = []
		for i in range(self.GetItemCount()):
			item = []
			for j in range(self.GetColumnCount()):
				item.append(eval(self.GetItem(i, j).GetText()))
			value['items'].append(item)
		return value

	def setValues(self, value):
		columns = value['columns']
		items = value['items']
		self.ClearAll()
		for i, value in enumerate(columns):
			self.InsertColumn(i, value)
		for i, item in enumerate(items):
			if len(item) != len(columns):
				self.ClearAll()
				raise ValueError('Invalid item dimension for column list')
			self.InsertStringItem(i, '')
			for j, value in enumerate(item):
				if type(value) is str:
					value = '"%s"' % value
				value = str(value)
				self.SetStringItem(i, j, value)

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'List Edit')
			self.SetTopWindow(frame)
			self.panel = wxPanel(frame, -1)
			self.sizer = wxBoxSizer(wxVERTICAL)

			self.listview = wxListView(self.panel)
			self.sizer.Add(self.listview, 1, wxEXPAND)
			self.listview.setValues(['a', 'b', 'c', 'd'])

			self.listedit = wxListEdit(self.panel, self.callback)
			self.sizer.Add(self.listedit, 1, wxEXPAND)

			self.columnlist = wxColumnList(self.panel)
			self.columnlist.setValues({'columns':
																		['Column 1', 'Column 2', 'Column 3'],
																	'items':
																		[['a', 'b', 'c'],
																			['d', 'e', 'f'],
																			['g', 'h', 'i'],
																			['j', 'k', 'l']]})
			print self.columnlist.getValues()
			self.sizer.Add(self.columnlist, 1, wxEXPAND)

			self.panel.SetSizerAndFit(self.sizer)
			frame.Fit()
			frame.Show(True)
			return True

		def callback(self, values):
			self.listedit.setValues(values)

	app = MyApp(0)
	app.MainLoop()

