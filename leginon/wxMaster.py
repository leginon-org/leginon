from wxPython.wx import *
import wxObjectCanvas
import event
import nodeclassreg

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

class BindingConnectionPoint(wxObjectCanvas.wxConnectionPointObject):
	def __init__(self, eventclass, color=wxBLACK):
		self.eventclass = eventclass
		self.drawtext = 0
		wxObjectCanvas.wxConnectionPointObject.__init__(self, color)

	def getEventClass(self):
		return self.eventclass

	def getDrawText(self):
		if self.drawtext > 0:
			return True
		return False

	def setDrawText(self, value):
		if value:
			self.drawtext += 1
		else:
			self.drawtext -= 1

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

	def OnEnter(self, evt):
		self.setDrawText(True)
		self.UpdateDrawing()

	def OnLeave(self, evt):
		self.setDrawText(False)
		self.UpdateDrawing()

class BindingInput(BindingConnectionPoint):
	def __init__(self, eventclass):
		BindingConnectionPoint.__init__(self, eventclass, wxRED)
		self.popupmenu = None

	def Draw(self, dc):
		BindingConnectionPoint.Draw(self, dc)
		if self.getDrawText():
			x, y = self.getCanvasPosition()
			#y = y - self.height
			dc.DrawRotatedText(self.eventclass.__name__, x, y, 90)

class BindingOutput(BindingConnectionPoint):
	def __init__(self, eventclass):
		BindingConnectionPoint.__init__(self, eventclass, wxBLUE)

		self.popupmenu = wxMenu()
		self.popupmenu.Append(101, 'Add Binding...')
		EVT_MENU(self.popupmenu, 101, self.menuAddBinding)

	def menuAddBinding(self, evt):
		binding = Binding(self.eventclass, self, None)
		self.ProcessEvent(wxObjectCanvas.StartConnectionEvent(binding))

	def Draw(self, dc):
		BindingConnectionPoint.Draw(self, dc)
		if self.getDrawText():
			x, y = self.getCanvasPosition()
			x = x + self.width
			y = y + self.height
			dc.DrawRotatedText(self.eventclass.__name__, x, y, -90)

class Node(wxObjectCanvas.wxRectangleObject):
	def __init__(self, alias, nodeclass):
		wxObjectCanvas.wxRectangleObject.__init__(self, 100, 100,wxColor(128,0,128))
		self.alias = alias 
		self.nodeclass = nodeclass

		nc = nodeclassreg.getNodeClass(self.nodeclass)
		for inputclass in nc.eventinputs:
			input = BindingInput(inputclass)
			self.addInputConnectionPoint(input)
		for outputclass in nc.eventoutputs:
			output = BindingOutput(outputclass)
			self.addOutputConnectionPoint(output)

		self.addText(self.alias)
		self.addText(self.nodeclass, 0, 12)

		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getAlias(self):
		return self.alias

	def setAlias(self, alias):
		self.removeText(self.alias)
		self.alias = alias 
		self.addText(self.alias)

	def getClass(self):
		return self.nodeclass

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getAlias())
		if dialog.ShowModal() == wxID_OK:
			self.setAlias(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuDelete(self, evt):
		self.removeConnections()
		self.delete()

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, BindingConnectionPoint):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def addInputConnectionPoint(self, cpo):
		if isinstance(cpo, BindingInput):
			wxObjectCanvas.wxRectangleObject.addInputConnectionPoint(self, cpo)
		else:
			raise TypeError('Invalid object type for input')

	def addOutputConnectionPoint(self, cpo):
		if isinstance(cpo, BindingOutput):
			wxObjectCanvas.wxRectangleObject.addOutputConnectionPoint(self, cpo)
		else:
			raise TypeError('Invalid object type for output')

	def OnMotion(self, evt):
		wxObjectCanvas.wxRectangleObject.OnMotion(self, evt)
		#evt.Skip()

	def OnEnter(self, evt):
		for i in self.inputconnectionpoints + self.outputconnectionpoints:
			i.setDrawText(True)
		self.UpdateDrawing()

	def OnLeave(self, evt):
		wxObjectCanvas.wxRectangleObject.OnLeave(self, evt)
		for i in self.inputconnectionpoints + self.outputconnectionpoints:
			i.setDrawText(False)
		self.UpdateDrawing()

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

class BindingLabel(wxObjectCanvas.wxRectangleObject):
	def __init__(self, text, color=wxBLACK):
		wxObjectCanvas.wxRectangleObject.__init__(self, 0, 0)
		self.addText(text)

		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def menuDelete(self, evt):
		self.parent.delete()
		self.delete()

	def OnLeftDragStart(self, evt):
		pass

	def OnMotion(self, evt):
		pass

	def Draw(self, dc):
		width, height = 0, 0
		for text in self.text:
			x, y = self.text[text]
			w, h = dc.GetTextExtent(text)
			if w + x > width:
				width = w + x
			if h + y > height:
				height = h + y
		self.width = width + 3
		self.height = height + 3
		wxObjectCanvas.wxRectangleObject.Draw(self, dc)

class Binding(wxObjectCanvas.wxConnectionObject):
	def __init__(self, eventclass, bindingoutput=None, bindinginput=None):
		self.eventclass = eventclass
		wxObjectCanvas.wxConnectionObject.__init__(self, bindingoutput,
																											bindinginput)
		self.label = BindingLabel(self.eventclass.__name__)
		self.addShapeObject(self.label)

	def getEventClass(self):
		return self.eventclass

	def _crookedLine(self, dc, so1, x, y):
		x1, y1 = wxObjectCanvas.wxConnectionObject._crookedLine(self, dc, so1, x, y)
		self.setLabelPosition(x1, y1, x, y)

	def crookedLine(self, dc, so1, so2):
		x1, y1, x2, y2 = wxObjectCanvas.wxConnectionObject.crookedLine(self, dc,
																																		so1, so2)
		self.setLabelPosition(x1, y1, x2, y2)

	def setLabelPosition(self, x1, y1, x2, y2):
		xoffset, yoffset = self.getCanvasPosition()
		lx = (x2 - x1)/2 + x1 - xoffset - self.label.width/2
		ly = (y2 - y1)/2 + y1 - yoffset - self.label.height/2
		self.label.setPosition(lx, ly)

	def getFromNode(self):
		connectionpoint = self.getFromShapeObject()
		if connectionpoint is not None:
			return connectionpoint.getParent()
		return None

	def getToNode(self):
		connectionpoint = self.getToShapeObject()
		if connectionpoint is not None:
			return connectionpoint.getParent()
		return None

	def getLineType(self):
		fromshapobject = self.getFromShapeObject()
		toshapeobject = self.getToShapeObject()

		if fromshapeobject is None or toshapeobject is None:
			return

		fromx, fromy = fromshapeobject.getCanvasPosition()
		tox, toy = toshapeobject.getCanvasPosition()

		fromwidth, fromheight = fromshapeobject.getSize()
		towidth, toheight = toshapeobject.getSize()

		fromnode = self.getFromNode()
		tonode = self.getToNode()

		if fromnode is None or tonode is None:
			return

		fromnodex, fromnodey = fromnode.getCanvasPosition()
		tonodex, tonodey = tonode.getCanvasPosition()

		fromnodewidth, fromnodeheight = fromnode.getSize()
		tonodewidth, tonodeheight = tonode.getSize()

		# if from's bottom is higher than to's top
		if toheight > fromheight + fromwidth:
			# direct
			pass
		else:
			# indirect
			if fromnodex > tonodex + tonodewidth:
				# go in between
				pass
			elif tonodex > fromnodex + fromnodewidth:
				# go in between
				pass
			else:
				# go around
				pass

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
		classnames = nodeclassreg.getNodeClassNames()
		classnames.sort()
		self.classcombo = wxComboBox(self, -1, choices=classnames,
																	style=wxCB_DROPDOWN|wxCB_READONLY)
		self.classcombo.SetSelection(0)
		box.Add(self.classcombo, 1, wxALIGN_CENTER|wxALL, 3)
#		self.classentry = wxTextCtrl(self, -1, '')
#		box.Add(self.classentry, 1, wxALIGN_CENTER|wxALL, 3)
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
		return self.aliasentry.GetValue(), self.classcombo.GetStringSelection()
		#return self.aliasentry.GetValue(), self.classentry.GetValue()

	def SetValue(self, alias, nodeclass):
		self.aliasentry.SetValue(alias)
		self.classcombo.SetStringSelection(nodeclass)
		#self.classentry.SetValue(nodeclass)

class Launcher(wxObjectCanvas.wxRectangleObject):
	def __init__(self, alias):
		self.alias = alias
		wxObjectCanvas.wxRectangleObject.__init__(self, 400, 400, wxColor(0,128,0))
		self.addText(self.alias)

		self.popupmenu.Append(101, 'Rename...')
		self.popupmenu.Append(102, 'Add Node...')
		self.popupmenu.Append(103, 'Delete')
		EVT_MENU(self.popupmenu, 101, self.menuRename)
		EVT_MENU(self.popupmenu, 102, self.menuAddNode)
		EVT_MENU(self.popupmenu, 103, self.menuDelete)

	def getAlias(self):
		return self.alias

	def setAlias(self, alias):
		self.removeText(self.alias)
		self.alias = alias
		self.addText(self.alias)

	def menuRename(self, evt):
		dialog = RenameDialog(None, -1)
		dialog.SetValue(self.getAlias())
		if dialog.ShowModal() == wxID_OK:
			self.setAlias(dialog.GetValue())
			self.UpdateDrawing()
		dialog.Destroy()

	def menuAddNode(self, evt):
		dialog = AddNodeDialog(None, -1)
		if dialog.ShowModal() == wxID_OK:
			alias, nodeclass = dialog.GetValue()
			self.addShapeObject(Node(alias, nodeclass))
		dialog.Destroy()

	def menuDelete(self, evt):
		for node in self.getNodes():
			node.removeConnections()
		self.delete()

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Node):
			for node in self.getNodes():
				if node.getAlias() == so.getAlias():
					raise ValueError('Node with same alias already exists')
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def getNodes(self):
		nodes = []
		for node in self.shapeobjects:
			if isinstance(node, Node):
				nodes.append(node)
		return nodes

	def OnStartConnection(self, evt):
		evt.Skip()

	def OnEndConnection(self, evt):
		evt.Skip()

	def OnCancelConnection(self, evt):
		evt.Skip()

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
		wxObjectCanvas.wxRectangleObject.__init__(self, 700, 700, wxColor(128,0,0))
		self.addText(self.name)

		self.startedbinding = None

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
		self.delete()

	def getLaunchers(self):
		return self.getShapeObjectsOfType(Launcher)

	def getBindings(self):
		return self.getShapeObjectsOfType(Binding)

	def getShapeObjectsOfType(self, shapeobjecttype):
		shapeobjects = []
		for shapeobject in self.shapeobjects:
			if isinstance(shapeobject, shapeobjecttype):
				shapeobjects.append(shapeobject)
		return shapeobjects

	def getNodes(self):
		nodes = []
		for launcher in self.getLaunchers():
			nodes += launcher.getNodes()
		return nodes

	def OnMotion(self, evt):
		wxObjectCanvas.wxRectangleObject.OnMotion(self, evt)
		evt.Skip(False)

	def addShapeObject(self, so, x=0, y=0):
		if isinstance(so, Launcher):
			for launcher in self.getLaunchers():
				if launcher.getAlias() == so.getAlias():
					raise ValueError('Launcher with same alias already exists')
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		elif isinstance(so, BindingLabel):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		elif isinstance(so, Binding):
			wxObjectCanvas.wxRectangleObject.addShapeObject(self, so, x, y)
		else:
			raise TypeError('Invalid object type to add')

	def OnStartConnection(self, evt):
		wxObjectCanvas.wxRectangleObject.OnStartConnection(self, evt)
		for node in self.getNodes():
			for input in node.inputconnectionpoints:
				if issubclass(self.connection.eventclass, input.eventclass):
					input.setDrawText(True)

	def OnEndConnection(self, evt):
		if self.connection is not None:
			if issubclass(self.connection.eventclass, evt.toso.eventclass):
				for node in self.getNodes():
					for input in node.inputconnectionpoints:
						if issubclass(self.connection.eventclass, input.eventclass):
							input.setDrawText(False)
				wxObjectCanvas.wxRectangleObject.OnEndConnection(self, evt)

	def cancelConnection(self):
		for node in self.getNodes():
			for input in node.inputconnectionpoints:
				if issubclass(self.connection.eventclass, input.eventclass):
					input.setDrawText(False)
		wxObjectCanvas.wxRectangleObject.cancelConnection(self)

	def getApplication(self):
		application = {'name': self.getName(), 'nodes': [], 'bindings': []}
		for launcher in self.getLaunchers():
			for node in launcher.getNodes():
				nodetuple = (node.getClass(), node.getAlias(),
											launcher.getAlias(), (), 0, [])
				application['nodes'].append(nodetuple)
		bindings = {}
		for binding in self.getBindings():
			fromnode = binding.getFromNode()
			tonode = binding.getToNode()
			if fromnode is not None and tonode is not None:
				fromalias = fromnode.getAlias()
				toalias = tonode.getAlias()
				bindingtuple = (binding.getEventClass().__name__, fromalias, toalias)
				application['bindings'].append(bindingtuple)
		return application

	def setApplication(self, application):
		if application['name'] != self.getName():
			self.setName(application['name'])

		nodes = []
		nodespecs = []
		for node in self.getNodes():
			for nodespec in application['nodes']:
				if node.getClass() == nodespec[0]:
					if node.getAlias() == nodespec[1]:
						parent = node.getParent()
						if parent is not None and parent.getAlias() == nodespec[2]:
							nodes.append(node)
							nodespecs.append(nodespec)

		for node in self.getNodes():
			if node not in nodes:
				node.delete()

		for nodespec in application['nodes']:
			if nodespec not in nodespecs:
				launcher = None
				for l in self.getLaunchers():
					if l.getAlias() == nodespec[2]:
						launcher = l
						break
					else:
						launcher = None

				if launcher is None:
					launcher = Launcher(nodespec[2])
					self.addShapeObject(launcher)
			
				launcher.addShapeObject(Node(nodespec[1], nodespec[0]))

		bindings = []
		bindspecs = []
		for binding in self.getBindings():
			for bindspec in application['bindings']:
				if binding.getEventClass().__name__ == bindspec[0]:
					fromso = binding.getFromShapeObject()
					toso = binding.getToShapeObject()
					if fromso is not None and toso is not None:
						fromnode = fromso.getParent()
						tonode = toso.getParent()
						if fromnode is not None and fromnode.getAlias() == bindspec[1]:
							if tonode is not None and tonode.getAlias() == bindspec[2]:
								bindings.append(binding)
								bindspecs.append(bindspec)

		for binding in self.getBindings():
			if binding not in bindings:
				binding.delete()

		for bindspec in application['bindings']:
			if bindspec not in bindspecs:
				fromcp = None
				tocp = None
				for node in self.getNodes():
					if node.getAlias() == bindspec[1]:
						for output in node.outputconnectionpoints:
							if output.getEventClass().__name__ == bindspec[0]:
								fromcp = output
					if node.getAlias() == bindspec[2]:
						for input in node.inputconnectionpoints:
							if input.getEventClass().__name__ == bindspec[0]:
								tocp = input
				if fromcp is not None and tocp is not None:
					binding = Binding(eval('event.' + bindspec[0]), fromcp, tocp)
					self.addShapeObject(binding)

class Master(wxObjectCanvas.wxRectangleObject):
	def __init__(self):
		wxObjectCanvas.wxRectangleObject.__init__(self, 800, 800)
		self.addText('Master')

class ApplicationEditorCanvas(wxObjectCanvas.wxObjectCanvas):
	def __init__(self, parent, id):
		self.application = Application('New Application')
		wxObjectCanvas.wxObjectCanvas.__init__(self, parent, id, self.application)

if __name__ == '__main__':
	import time

	class ApplicationApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Master Application')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.master = Application('New Application')
			self.objectcanvas = wxObjectCanvas.wxObjectCanvas(self.panel, -1,
																												self.master)
			self.panel.SetSize(self.objectcanvas.GetSize())
			self.panel.Show(true)
			self.frame.SetClientSize(self.panel.GetSize())
			self.frame.Show(true)
			return true

	app = ApplicationApp(0)
	app.MainLoop()

