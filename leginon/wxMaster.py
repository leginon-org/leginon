from wxPython.wx import *
import wxObjectCanvas

class RenameDialog(wxDialog):
	def __init__(self, parent, id, title='Rename', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'New Name:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.name_entry = wxTextCtrl(self, -1, '')
		box.Add(self.name_entry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'OK')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.name_entry.GetValue()

	def SetValue(self, name):
		self.name_entry.SetValue(name)

class AddBindingDialog(wxDialog):
	def __init__(self, parent, id, title='Add Binding', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Class:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.classentry = wxTextCtrl(self, -1, '')
		box.Add(self.classentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'Add')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.classentry.GetValue()

	def SetValue(self, eventclass):
		self.classentry.SetValue(eventclass)

class Node(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 60, 60)
		self.addText(self.name)

		self.popupmenu = wxMenu()
		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Binding...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddBinding)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddBinding(self, evt):
		if self.parent is not None:
			dialog = AddBindingDialog(None, -1)
			if dialog.ShowModal() == wxID_OK:
				eventclass = dialog.GetValue()
				self.parent.startAddBinding(eventclass, self)
			dialog.Destroy()

	def menuDelete(self, evt):
		if self.parent is not None:
			self.parent.removeConnectionObjects(self)
			self.parent.removeShapeObject(self)

	def addShapeObject(self, so, x=0, y=0):
		raise TypeError('Invalid object type to add')

class Binding(wxObjectCanvas.wxConnectionObject):
	def __init__(self, name, fromnode=None, tonode=None):
		self.name = name
		wxObjectCanvas.wxConnectionObject.__init__(self, fromnode, tonode)
		self.setText(self.name)

class AddNodeDialog(wxDialog):
	def __init__(self, parent, id, title='Add Node', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Alias:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.aliasentry = wxTextCtrl(self, -1, '')
		box.Add(self.aliasentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Class:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.classentry = wxTextCtrl(self, -1, '')
		box.Add(self.classentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'Add')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.aliasentry.GetValue(), self.classentry.GetValue()

	def SetValue(self, alias, nodeclass):
		self.aliasentry.SetValue(alias)
		self.classentry.SetValue(nodeclass)

class Launcher(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 150, 150)
		self.addText(self.name)

		self.popupmenu = wxMenu()
		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Node...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddNode)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddNode(self, evt):
		dialog = AddNodeDialog(None, -1)
		if dialog.ShowModal() == wxID_OK:
			alias, nodeclass = dialog.GetValue()
			self.addShapeObject(Node(alias))
		dialog.Destroy()

	def menuDelete(self, evt):
		for so in self.shapeobjects:
			self.removeConnectionObjects(so)
		if self.parent is not None:
			self.parent.removeShapeObject(self)

	def startAddBinding(self, eventclass, fromnode):
		if self.parent is not None:
			self.parent.startAddBinding(eventclass, fromnode)

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Node):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

class AddLauncherDialog(wxDialog):
	def __init__(self, parent, id, title='Add Launcher', pos=wxDefaultPosition,
								size=wxDefaultSize, style=wxDEFAULT_DIALOG_STYLE):

		wxDialog.__init__(self, parent, id, title, pos, size, style)
		sizer = wxBoxSizer(wxVERTICAL)

		box = wxBoxSizer(wxHORIZONTAL)
		label = wxStaticText(self, -1, 'Alias:')
		box.Add(label, 0, wxALIGN_CENTER|wxALL, 3)
		self.aliasentry = wxTextCtrl(self, -1, '')
		box.Add(self.aliasentry, 1, wxALIGN_CENTER|wxALL, 3)
		sizer.AddSizer(box)

		box = wxBoxSizer(wxHORIZONTAL)
		button = wxButton(self, wxID_OK, 'Add')
		button.SetDefault()
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		button = wxButton(self, wxID_CANCEL, 'Cancel')
		box.Add(button, 0, wxALIGN_CENTER|wxALL, 5)
		sizer.AddSizer(box)

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

	def GetValue(self):
		return self.aliasentry.GetValue()

	def SetValue(self, alias):
		self.aliasentry.SetValue(alias)

class Application(wxObjectCanvas.wxRectangleObject):
	def __init__(self, name):
		self.name = name
		wxObjectCanvas.wxRectangleObject.__init__(self, 700, 700)
		self.addText(self.name)

		self.startedbinding = None

		self.popupmenu = wxMenu()
		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Launcher...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddLauncher)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getName(self):
		return self.name

	def setName(self, name):
		self.removeText(self.name)
		self.name = name
		self.addText(self.name)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getName())
		if dialog.ShowModal() == wxID_OK:
			self.setName(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddLauncher(self, evt):
		dialog = AddLauncherDialog(None, -1)
		if dialog.ShowModal() == wxID_OK:
			alias = dialog.GetValue()
			self.addShapeObject(Launcher(alias))
		dialog.Destroy()

	def menuDelete(self, evt):
		if self.parent is not None:
			self.parent.removeShapeObject(self)

	def startAddBinding(self, eventclass, fromnode):
		self.startedbinding = Binding(eventclass, fromnode, None)
		self.startedbinding.setParent(self)
		wxObjectCanvas.EVT_LEFT_CLICK(self, self.finishAddBinding)
		wxObjectCanvas.EVT_RIGHT_CLICK(self, self.cancelAddBinding)

	def finishAddBinding(self, evt):
		tonode = evt.shapeobject
		if self.startedbinding is not None and isinstance(tonode, Node):
			binding = self.startedbinding
			self.startedbinding = None
			binding.setToShapeObject(tonode)
			self.addConnectionObject(binding)
		wxObjectCanvas.EVT_LEFT_CLICK(self, self.OnLeftClick)
		wxObjectCanvas.EVT_RIGHT_CLICK(self, self.OnRightClick)

	def cancelAddBinding(self, evt):
		self.startedbinding = None
		wxObjectCanvas.EVT_LEFT_CLICK(self, self.OnLeftClick)
		wxObjectCanvas.EVT_RIGHT_CLICK(self, self.OnRightClick)

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Launcher):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

class Master(wxObjectCanvas.wxRectangleObject):
	def __init__(self):
		wxObjectCanvas.wxRectangleObject.__init__(self, 800, 800)
		self.addText('Master')

if __name__ == '__main__':
	import time

	class MasterApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Master Application')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.master = Master()
			self.objectcanvas = wxObjectCanvas.wxObjectCanvas(self.panel, -1,
																												self.master)
			self.objectcanvas.SetSize((800, 800))
			self.panel.Fit()
			self.panel.Show(true)
			self.frame.Fit()
			self.frame.Show(true)
			return true

	class ApplicationApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Master Application')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.master = Application('New Application')
			self.objectcanvas = wxObjectCanvas.wxObjectCanvas(self.panel, -1,
																												self.master)
			self.objectcanvas.SetSize((800, 800))
			self.panel.Fit()
			self.panel.Show(true)
			self.frame.Fit()
			self.frame.Show(true)
			return true

	#app = MasterApp(0)
	app = ApplicationApp(0)
	app.frame.Fit()

	l0 = Launcher('Launcher 0')
	l1 = Launcher('Launcher 1')
	l2 = Launcher('Launcher 2')
	n0 = Node('Node 0')
	n1 = Node('Node 1')
	n2 = Node('Node 2')
	n3 = Node('Node 3')
	n4 = Node('Node 4')

	app.master.addShapeObject(l1)
	app.master.addShapeObject(l0)
	app.master.addShapeObject(l2)
	l0.addShapeObject(n1)
	l2.addShapeObject(n2)
	l0.addShapeObject(n0)
	l1.addShapeObject(n3)
	l2.addShapeObject(n4)
	b0 = Binding('Binding 0', n0, n1)
	b1 = Binding('Binding 1', n3, n2)
	b2 = Binding('Binding 2', n3, n1)
	app.master.addConnectionObject(b0)
	app.master.addConnectionObject(b1)
	app.master.addConnectionObject(b2)

	app.MainLoop()

