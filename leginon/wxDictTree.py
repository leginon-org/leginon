from wxPython.wx import *

class DictTreeCtrl(wxTreeCtrl):
	def __init__(self, parent, id, pos, size, style):
		wxTreeCtrl.__init__(self, parent, id, pos, size, style)

class DictTreeCtrlPanel(wxPanel):
	def __init__(self, parent, id, label, editcallback=None, selectcallback=None):
		wxPanel.__init__(self, parent, id)
		self.editcallback = editcallback
		self.selectcallback = selectcallback
		style = wxTR_HAS_BUTTONS
		if callable(self.editcallback):
			style |=wxTR_EDIT_LABELS
		self.tree = DictTreeCtrl(self, -1, wxDefaultPosition,
																	wxSize(180, 200), style)
		self.root = self.tree.AddRoot(label)
		EVT_TREE_BEGIN_LABEL_EDIT(self, self.tree.GetId(), self.OnBeginEdit)
		EVT_TREE_END_LABEL_EDIT(self, self.tree.GetId(), self.OnEndEdit)
		EVT_TREE_SEL_CHANGING(self, self.tree.GetId(), self.OnBeginSelect)
		EVT_TREE_SEL_CHANGED(self, self.tree.GetId(), self.OnSelect)
		self.SetSize(self.tree.GetSize())

	def set(self, dictvalue):
		self.tree.DeleteChildren(self.root)
		self.dict = dictvalue
		self.tree.SetPyData(self.root, self.dict)
		self.setDict(self.root, self.dict)
		self.tree.Expand(self.root)

	def get(self):
		return self.dict

	def setDict(self, parent, dictvalue):
		for item in dictvalue:
			child = self.tree.AppendItem(parent, str(item))
			if type(dictvalue[item]) is dict:
				self.setDict(child, dictvalue[item])
				self.tree.SetPyData(child, dictvalue[item])
			else:
				self.tree.SetPyData(child, item)
				child = self.tree.AppendItem(child, str(dictvalue[item]))
				self.tree.SetPyData(child, dictvalue[item])

	def OnBeginEdit(self, evt):
		if self.tree.ItemHasChildren(evt.GetItem()):
			evt.Veto()

	def OnBeginSelect(self, evt):
		if self.tree.ItemHasChildren(evt.GetItem()):
			evt.Veto()

	def OnSelect(self, evt):
		if not callable(self.selectcallback):
			return
		item = evt.GetItem()
		itemlist = []
		while item != self.root:
			value = self.tree.GetPyData(item)
			if type(value) is dict:
				value = self.tree.GetItemText(item)
			itemlist.insert(0, value)
			item = self.tree.GetItemParent(item)
		self.selectcallback(itemlist)

	def select(self, namelist):
		#self.tree.UnselectAll()
		selectcallback = self.selectcallback
		self.selectcallback = None
		result = self.selectItem(self.root, namelist)
		self.selectcallback = selectcallback
		return result

	def selectItem(self, item, namelist):
		# needs error checking
		if not namelist:
			return False
		value = self.tree.GetPyData(item)
		cookie = 0
		if type(value) is dict and namelist[0] in value:
			(child, cookie) = self.tree.GetFirstChild(item, cookie)
			while child.IsOk():
				if self.selectItem(child, namelist[1:]):
					return True
				(child, cookie) = self.tree.GetNextChild(item, cookie)
		if type(value) is not dict:
			(child, cookie) = self.tree.GetFirstChild(item, cookie)
			if self.tree.GetPyData(child) == namelist[0]:
				# two events?
				self.tree.SelectItem(child)
				return True
		return False

	def nothing(self):
		pass

	def OnEndEdit(self, evt):
		if not callable(self.editcallback) or evt.IsEditCancelled():
			return
		newvalue = evt.GetLabel()
		# apparently under Gtk if you hit enter to set the value two events fire
		# one of the event value is '', a quick way around is to not let the user
		# (or anyone) set to ''
		if not newvalue:
			return
		item = evt.GetItem()
		parentitem = self.tree.GetItemParent(item)
		parentdata = self.tree.GetPyData(parentitem)
		grandparentdata = self.tree.GetPyData(self.tree.GetItemParent(parentitem))
		oldvalue = grandparentdata[parentdata]
		if type(oldvalue) is not str:
			try:
				newvalue = eval(newvalue)
			except:
				evt.Veto()
				return
			if type(newvalue) != type(oldvalue):
				evt.Veto()
				return
		self.tree.SetPyData(item, newvalue)
		grandparentdata[parentdata] = newvalue
		self.editcallback()
		evt.Skip()

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Tree Control')
			frame.Show(true)
			self.SetTopWindow(frame)
			panel = DictTreeCtrlPanel(frame, -1, 'Label Value', True)
			return true

	app = MyApp(0)
	app.MainLoop()

