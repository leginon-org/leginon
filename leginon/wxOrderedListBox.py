from wxPython.wx import *

class wxOrderedListBox(wxPanel):
	def __init__(self, parent, id, callback=None):
		wxPanel.__init__(self, parent, id)
		self.callback = callback
		self.list = []
		self.selected = []
		self.listmapping = {}
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.SetSizer(self.sizer)
		self.listlistbox = wxListBox(self, -1, style=wxLB_EXTENDED|wxLB_NEEDED_SB)
		self.sizer.Add(self.listlistbox, 0, wxALL, 3) # | wxADJUST_MINSIZE, 3)

		self.selectbutton = wxButton(self, -1, '>', style=wxBU_EXACTFIT)
		self.unselectbutton = wxButton(self, -1, '<', style=wxBU_EXACTFIT)
		EVT_BUTTON(self, self.selectbutton.GetId(), self.onSelect)
		EVT_BUTTON(self, self.unselectbutton.GetId(), self.onUnselect)
		buttonsizer = wxBoxSizer(wxVERTICAL)
		buttonsizer.Add(self.selectbutton, 0,
										wxALIGN_CENTER_VERTICAL | wxALIGN_CENTER | wxALL, 3)
		buttonsizer.Add(self.unselectbutton, 0,
										wxALIGN_CENTER_VERTICAL | wxALIGN_CENTER | wxALL, 3)
		buttonsizer.Layout()
		self.sizer.Add(buttonsizer)

		self.selectedlistbox = wxListBox(self, -1,
																			style=wxLB_EXTENDED|wxLB_NEEDED_SB)
		self.sizer.Add(self.selectedlistbox, 0, wxALL, 3) # | wxADJUST_MINSIZE, 3)
		self.sizer.Layout()
		self.Fit()
		self.Show(true)

	def onSelect(self, evt):
		selection = self.listlistbox.GetSelections()
		for i in selection:
			self.listlistbox.Deselect(i)
			self.selected.append(self.listmapping[i])
		self.update()
		if callable(self.callback):
			self.callback(self.selected)

	def onUnselect(self, evt):
		selection = list(self.selectedlistbox.GetSelections())
		selection.reverse()
		for i in selection:
			self.selectedlistbox.Deselect(i)
			del self.selected[i]
		self.update()
		if callable(self.callback):
			self.callback(self.selected)

	def getList(self):
		return self.list

	def setList(self, value):
		self.list = value
		self._updateSelected()
		self.update()

	def getSelected(self):
		return self.selected

	def setSelected(self, value):
		self.selected = value
		self._updateSelected()
		self.update()

	def _updateSelected(self):
		for i in self.selected:
			if i >= len(self.list):
				self.selected.remove(i)

	def update(self):
		for i in range(len(self.selected)):
			index = self.selected[i]
			valuestring = str(self.list[index])
			if i < self.selectedlistbox.GetCount():
				if valuestring != self.selectedlistbox.GetString(i):
					self.selectedlistbox.SetString(i, valuestring)
		if self.selectedlistbox.GetCount() > len(self.selected):
			for i in range(self.selectedlistbox.GetCount() - 1,
											len(self.selected) - 1, -1):
				self.selectedlistbox.Delete(i)
		elif self.selectedlistbox.GetCount() < len(self.selected):
			for i in range(self.selectedlistbox.GetCount(), len(self.selected)):
				index = self.selected[i]
				valuestring = str(self.list[index])
				self.selectedlistbox.Append(valuestring)

		valuestrings = []
		for i in range(len(self.list)):
			if i not in self.selected:
				valuestrings.append(str(self.list[i]))
				self.listmapping[len(valuestrings) - 1] = i
		for i in range(len(valuestrings)):
			valuestring = valuestrings[i]
			if i < self.listlistbox.GetCount():
				if valuestring != self.listlistbox.GetString(i):
					self.listlistbox.SetString(i, valuestring)
		if self.listlistbox.GetCount() > len(valuestrings):
			for i in range(self.listlistbox.GetCount()-1, len(valuestrings)-1, -1):
				self.listlistbox.Delete(i)
		elif self.listlistbox.GetCount() < len(valuestrings):
			for i in range(self.listlistbox.GetCount(), len(valuestrings)):
				self.listlistbox.Append(valuestrings[i])

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = wxPanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	foo = wxOrderedListBox(app.panel, -1)
	foo.setList(['a', 'b', 'c'])
	foo.setSelected([0, 2, 3])
	foo.setList(['a', 'b'])
	foo.setList(['a', 'b', 'c', 'd', 'e'])
	app.MainLoop()

