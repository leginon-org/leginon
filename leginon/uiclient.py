import xmlrpclib
import uiserver
import threading
import time
from wxPython.wx import *
import wxImageViewer
import wxDictTree

class XMLRPCClient(object):
	def __init__(self, serverhostname, serverport, port=None):
		uri = 'http://%s:%s' % (serverhostname, serverport)
		self.proxy = xmlrpclib.ServerProxy(uri)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except xmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except xmlrpclib.Fault:
			# exception during call of the function
			raise

class UIClient(XMLRPCClient, uiserver.XMLRPCServer):
	def __init__(self, serverhostname, serverport, port=None):
		XMLRPCClient.__init__(self, serverhostname, serverport, port)
		uiserver.XMLRPCServer.__init__(self, port)
		self.server.register_function(self.addFromServer, 'ADD')
		self.server.register_function(self.setFromServer, 'SET')
		self.server.register_function(self.deleteFromServer, 'DEL')

	def addServer(self):
		self.execute('ADDSERVER', (self.hostname, self.port))

	def setServer(self, namelist, value):
		self.execute('SET', (namelist, value))

	def commandServer(self, namelist, args):
		self.execute('COMMAND', (namelist, args))

	def addFromServer(self, namelist, typelist, value):
		raise NotImplementedError

	def setFromServer(self, namelist, value):
		raise NotImplementedError

	def deleteFromServer(self, namelist):
		raise NotImplementedError

class wxUIClient(UIClient):
	def __init__(self, serverhostname, serverport, port=None):
		# there are some timing issues to be thought out
		UIClient.__init__(self, serverhostname, serverport, port)
		self.app = UIApp(self)
		threading.Thread(target=self.addServer, args=()).start()
		self.app.MainLoop()

	def addFromServer(self, namelist, typelist, value):
		print 'ADD', namelist, typelist, value
		self.app.container.add((self.app.container.name,) + tuple(namelist),
																													typelist, value)
		return ''

	def setFromServer(self, namelist, value):
		print 'SET', namelist, value
		self.app.container.set((self.app.container.name,) + tuple(namelist), value)
		return ''

	def deleteFromServer(self, namelist):
		print 'DEL', namelist
		self.app.container.delete((self.app.container.name,) + tuple(namelist))
		return ''

class UIApp(wxApp):
	def __init__(self, uiclient):
		self.uiclient = uiclient
		wxApp.__init__(self, 0)

	def OnInit(self):
		self.frame = wxFrame(NULL, -1, 'UI')
		self.panel = wxPanel(self.frame, -1)
		self.panel.SetSize(self.frame.GetClientSize())
		self.container = wxStaticBoxContainerWidget(None, ('UI',),
																								self.frame, self.panel)
		self.panel.SetAutoLayout(true)
		self.panel.SetSizer(self.container.wxwidget)
		self.frame.Connect(-1, -1, wxEVT_ADD_WIDGET, self.addWidget)
		self.frame.Connect(-1, -1, wxEVT_SET_WIDGET, self.setWidget)
		self.frame.Connect(-1, -1, wxEVT_DELETE_WIDGET, self.deleteWidget)
		self.container.wxwidget.Fit(self.frame)
		self.frame.Show(true)
		self.SetTopWindow(self.frame)
		self.panel.Show(true)
		return true

	def addWidget(self, evt):
		uiwidget = evt.widget_type(self.uiclient, evt.namelist,
																			self.frame, evt.parent)
		evt.container.children[evt.namelist] = uiwidget
		if isinstance(uiwidget, DataWidget):
			uiwidget.set(evt.value)
		if hasattr(uiwidget, 'wxwidget'):
			evt.container.wxwidget.Add(uiwidget.wxwidget)
		# needs to callback
		self.Layout()
		evt.container.event.set()
		evt.container.lock.release()

	def setWidget(self, evt):
		evt.widget.set(evt.value)

	def deleteWidget(self, evt):
		evt.widget.Destroy()
		if hasattr(evt.widget, 'wxwidget'):
			evt.container.wxwidget.Remove(evt.widget.wxwidget)
		self.Layout()

	def Layout(self):
		self.container._Layout()
		self.container.wxwidget.Fit(self.frame)

class Widget(object):
	def __init__(self, uiclient, namelist):
		self.uiclient = uiclient
		self.namelist = namelist
		self.name = namelist[-1]

class ContainerWidget(Widget):
	def __init__(self, uiclient, namelist):
		Widget.__init__(self, uiclient, namelist)
		self.children = {}

	def addWidget(self, namelist, typelist, value):
		raise NotImplementedError

	def add(self, namelist, typelist, value):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if len(namelist) - len(self.namelist) == 1:
				self.addWidget(namelist, typelist, value)
			elif childnamelist in self.children and isinstance(
																self.children[childnamelist], ContainerWidget):
				self.children[childnamelist].add(namelist, typelist, value)
			else:
				raise ValueError
		else:
			raise ValueError

	def setWidget(self, namelist, value):
		raise NotImplementedError

	def set(self, namelist, value):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if childnamelist in self.children:
				if namelist in self.children:
					self.setWidget(namelist, value)
				else:
					self.children[childnamelist].set(namelist, value)
			else:
				raise ValueError
		else:
			raise ValueError

	def deleteWidget(self, namelist):
		raise NotImplementedError

	def delete(self, namelist):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if len(namelist) - len(self.namelist) == 1:
				self.deleteWidget(namelist)
			elif childnamelist in self.children and isinstance(
																self.children[childnamelist], ContainerWidget):
				self.children[childnamelist].delete(namelist)
			else:
				raise ValueError
		else:
			raise ValueError

def WidgetClassFromTypeList(typelist):
	if typelist:
		if typelist[0] == 'object':
			if len(typelist) > 1:
				if typelist[1] == 'container':
					if len(typelist) > 2:
						if typelist[2] == 'select from list':
							return wxComboBoxWidget
						elif typelist[2] == 'select from struct':
							return wxTreeSelectWidget
						elif typelist[2] == 'target image':
							return wxTargetImageWidget
						elif typelist[2] == 'dialog':
							return wxDialogWidget
					return wxStaticBoxContainerWidget
				elif typelist[1] == 'method':
					return wxButtonWidget
				elif typelist[1] == 'data':
					if len(typelist) > 2:
						if typelist[2] == 'boolean':
							return wxCheckBoxWidget
						elif typelist[2] == 'struct':
							return wxTreeCtrlWidget
						elif typelist[2] == 'binary':
							if len(typelist) > 3:
								if typelist[3] == 'image':
									return wxImageWidget
					return wxEntryWidget
	raise ValueError('invalid type for widget')
	
wxEVT_ADD_WIDGET = wxNewEventType()

class AddWidgetEvent(wxPyEvent):
	def __init__(self, namelist, container, typelist, parent, value):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_WIDGET)
		self.widget_type = WidgetClassFromTypeList(typelist)
		self.namelist = namelist
		self.container = container
		self.parent = parent
		self.value = value

wxEVT_SET_WIDGET = wxNewEventType()

class SetWidgetEvent(wxPyEvent):
	def __init__(self, widget, value):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_WIDGET)
		self.widget = widget
		self.value = value

wxEVT_DELETE_WIDGET = wxNewEventType()

class DeleteWidgetEvent(wxPyEvent):
	def __init__(self, container, widget):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_DELETE_WIDGET)
		self.container = container
		self.widget = widget

class wxContainerWidget(ContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		ContainerWidget.__init__(self, uiclient, namelist)
		self.window = window
		self.parent = parent
		self.lock = threading.Lock()
		self.event = threading.Event()

	def addWidget(self, namelist, typelist, value):
		self.lock.acquire()
		self.event.clear()
		evt = AddWidgetEvent(namelist, self, typelist, self.parent, value)
		wxPostEvent(self.window, evt)
		self.event.wait()

	def setWidget(self, namelist, value):
		self.lock.acquire()
		widget = self.children[namelist]
		evt = SetWidgetEvent(widget, value)
		wxPostEvent(self.window, evt)
		self.lock.release()

	def deleteWidget(self, namelist):
		self.lock.acquire()
		widget = self.children[namelist]
		del self.children[namelist]
		evt = DeleteWidgetEvent(self, widget)
		wxPostEvent(self.window, evt)
		self.lock.release()

class wxStaticBoxContainerWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxContainerWidget.__init__(self, uiclient, namelist, window, parent)
		self.staticbox = wxStaticBox(self.parent, -1, self.name)
		self.wxwidget = wxStaticBoxSizer(self.staticbox, wxVERTICAL)

	# thread unsafe
	def _Layout(self):
		for child in self.children.values():
			if isinstance(child, self.__class__):
				child._Layout()
		self.wxwidget.Layout()

	def Destroy(self):
		for child in self.children.values():
			child.Destroy()
			self.wxwidget.Remove(child.wxwidget)
		self.staticbox.Destroy()

class MethodWidget(Widget):
	def __init__(self, uiclient, namelist):
		Widget.__init__(self, uiclient, namelist)

	def commandServer(self, args=()):
		self.uiclient.commandServer(self.namelist, args)

	def command(self, evt):
		self.commandServer()

class wxMethodWidget(MethodWidget):
	def __init__(self, uiclient, namelist, window, parent):
		MethodWidget.__init__(self, uiclient, namelist)
		self.window = window
		self.parent = parent

	def Destroy(self):
		pass

class wxButtonWidget(wxMethodWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxMethodWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.button = wxButton(self.parent, -1, self.name)
		EVT_BUTTON(self.window, self.button.GetId(), self.command)
		self.wxwidget.Add(self.button, 0, wxALIGN_CENTER | wxALL, 5)

class DataWidget(Widget):
	def __init__(self, uiclient, namelist):
		Widget.__init__(self, uiclient, namelist)

	def setServer(self, value):
		self.uiclient.setServer(self.namelist, value)

	def set(self, value):
		if isinstance(value, xmlrpclib.Binary):
			self.value = value.data
		else:
			self.value = value

class wxDataWidget(DataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		DataWidget.__init__(self, uiclient, namelist)
		self.window = window
		self.parent = parent

	def Destroy(self):
		pass

class wxEntryWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxDataWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.applybutton = wxButton(self.parent, -1, 'Apply')
		self.applybutton.Enable(false)
		EVT_BUTTON(self.window, self.applybutton.GetId(), self.apply)
		self.entry = wxTextCtrl(self.parent, -1)
		EVT_TEXT(self.window, self.entry.GetId(), self.onEdit)
		EVT_TEXT_ENTER(self.window, self.entry.GetId(), self.onEnter)
		self.wxwidget.Add(self.label, 0, wxALIGN_CENTER | wxALL, 5)
		self.wxwidget.Add(self.entry, 0, wxALIGN_CENTER | wxALL, 5)
		self.wxwidget.Add(self.applybutton, 0, wxALIGN_CENTER | wxALL, 5)

	def Destroy(self):
		self.applybutton.Destroy()
		self.entry.Destroy()
		self.label.Destroy()

	def onEdit(self, evt):
		self.applybutton.Enable(true)

	def onEnter(self, evt):
		if self.applybutton.IsEnabled():
			self.apply(evt)

	def apply(self, evt):
		value = self.entry.GetValue()
		if type(self.value) is not str:
			try:
				value = eval(value)
			except:
				return
		if type(self.value) != type(value):
			return
		self.value = value
		self.applybutton.Enable(false)
		self.setServer(self.value)

	def set(self, value):
		DataWidget.set(self, value)
		self.entry.SetValue(str(self.value))
		self.applybutton.Enable(false)

class wxCheckBoxWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxDataWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.checkbox = wxCheckBox(self.parent, -1, self.name)
		EVT_CHECKBOX(self.window, self.checkbox.GetId(), self.apply)
		self.wxwidget.Add(self.checkbox, 0, wxALIGN_CENTER | wxALL, 5)

	def apply(self, evt):
		value = self.checkbox.GetValue()
		if value:
			self.value = 1
		else:
			self.value = 0
		self.setServer(self.value)

	def set(self, value):
		DataWidget.set(self, value)
		self.checkbox.SetValue(self.value)

	def Destroy(self):
		self.checkbox.Destroy()

class wxTreeCtrlWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxDataWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1,
																							self.name, self.apply)
		self.wxwidget.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)

	def apply(self):
		self.setServer(self.value)

	def set(self, value):
		DataWidget.set(self, value)
		self.tree.set(self.value)

	def Destroy(self):
		self.tree.Destroy()

class MessageDialog(wxDialog):
	def __init__(self, parent, id, title, callback):
		wxDialog.__init__(self, parent, id, title)
		self.callback = callback
		panel = wxPanel(self, -1)
		panel.SetAutoLayout(true)
		self.sizer = wxBoxSizer(wxVERTICAL)
		panel.SetSizer(self.sizer)
		self.message = wxStaticText(panel, -1, '')
		self.sizer.Add(self.message, 0, wxALIGN_CENTER | wxALL, 10)
		self.okbutton = wxButton(panel, -1, 'OK')
		EVT_BUTTON(self, self.okbutton.GetId(), self.OnOK)
		self.sizer.Add(self.okbutton, 0, wxALIGN_CENTER | wxALL, 10)
		self.sizer.Layout()
		self.sizer.Fit(self)
		EVT_CLOSE(self, self.OnClose)

	def OnOK(self, evt):
		self.callback()

	def OnClose(self, evt):
		self.callback()

class wxDialogWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxContainerWidget.__init__(self, uiclient, namelist, window, parent)
		self.dialog = MessageDialog(self.parent, -1, self.name, self.callback)
		self.messageflag = False
		self.okflag = False

	def add(self, namelist, typelist, value):
		self.setWidget(namelist, value)

	def Destroy(self):
		self.dialog.Destroy()

	def Show(self):
		self.dialog.sizer.SetItemMinSize(self.dialog.message,
																	self.dialog.message.GetSize().GetWidth(),
																	self.dialog.message.GetSize().GetHeight())
		self.dialog.sizer.Layout()
		self.dialog.sizer.Fit(self.dialog)
		self.dialog.Show(true)

	def _set(self, value):
		self.dialog.message.SetLabel(value)
		self.messageflag = True
		if self.messageflag and self.okflag:
			self.Show()

	def setWidget(self, namelist, value):
		self.lock.acquire()
		if namelist == self.namelist + ('Message',):
			evt = SetWidgetEvent(self, value)
			wxPostEvent(self.window, evt)
		elif namelist == self.namelist + ('OK',):
			self.okflag = True
		self.lock.release()
		if self.messageflag and self.okflag:
			self.Show()

	def set(self, namelist, value=None):
		if value is None:
			self._set(namelist)
		else:
			self.setWidget(namelist, value)

	def delete(self, namelist):
		pass

	def callback(self):
		self.uiclient.commandServer(self.namelist + ('OK',), ())

class wxComboBoxWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.combobox = wxComboBox(self.parent, -1)
		self.combobox.Enable(false)
		EVT_COMBOBOX(self.window, self.combobox.GetId(), self.apply)
		self.wxwidget.Add(self.combobox, 0, wxALIGN_CENTER | wxALL, 5)
		self.value = {'List': [], 'Selected': None}

	def apply(self, evt):
		value = [evt.GetSelection()]
		self.uiclient.setServer(self.namelist + ('Selected',), value)

	def Destroy(self):
		self.combobox.Destroy()

	def add(self, namelist, typelist, value):
		self.setWidget(namelist, value)

	def _set(self, value):
		if 'List' in value:
			self.combobox.Clear()
			for i in range(len(value['List'])):
				self.combobox.Append(str(value['List'][i]))
		if 'Selected' in value:
			i = value['Selected'][0]
			self.combobox.SetValue(str(value['List'][i]))
		self.combobox.Enable(true)

	def setWidget(self, namelist, value):
		self.lock.acquire()
		if namelist == self.namelist + ('List',):
			self.value['List'] = value
		elif namelist == self.namelist + ('Selected',):
			self.value['Selected'] = value
		else:
			self.lock.release()
			return
		if self.value['List'] and self.value['Selected'] is not None:
			evt = SetWidgetEvent(self, self.value)
			wxPostEvent(self.window, evt)
		self.lock.release()

	# container set, should only be called within the container (setWidget)
	def set(self, namelist, value=None):
		if value is None:
			self._set(namelist)
		else:
			self.setWidget(namelist, value)
		
	def delete(self, namelist):
		pass

class wxTreeSelectWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name,
																											None, self.select)
		self.tree.Enable(false)
		self.wxwidget.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.value = {'Struct': {}, 'Selected': []}

	def select(self, itemlist):
		value = [itemlist]
		self.uiclient.setServer(self.namelist + ('Selected',), value)

	def Destroy(self):
		self.combobox.Destroy()

	def add(self, namelist, typelist, value):
		self.setWidget(namelist, value)

	def _set(self, value):
		if 'Struct' in value:
			self.tree.set(value['Struct'])
		if 'Selected' in value and value['Selected']:
			self.tree.select(value['Selected'][0])
		if self.value['Struct'] and 'Selected' in value:
			self.tree.Enable(true)

	def setWidget(self, namelist, value):
		self.lock.acquire()
		setvalue = {}
		if namelist == self.namelist + ('Struct',):
			setvalue[namelist[-1]] = value
			if not self.value['Struct']:
				setvalue['Selected'] = self.value['Selected']
			self.value['Struct'] = value
		elif namelist == self.namelist + ('Selected',):
			self.value['Selected'] = value
			if self.value['Struct']:
				setvalue[namelist[-1]] = value
		else:
			self.lock.release()
			return
		if setvalue:
			evt = SetWidgetEvent(self, setvalue)
			wxPostEvent(self.window, evt)
		self.lock.release()

	# container set, should only be called within the container (setWidget)
	def set(self, namelist, value=None):
		if value is None:
			self._set(namelist)
		else:
			self.setWidget(namelist, value)
		
	def delete(self, namelist):
		pass

class wxImageWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxDataWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.imageviewer = wxImageViewer.ImagePanel(self.parent, -1)
		#self.imageviewer.SetSize(wxSize(512, 512))
		self.wxwidget.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)

	def set(self, value):
		# not keeping track of image for now
		#DataWidget.set(self, value)
		self.imageviewer.setImage(value.data)
		self.wxwidget.SetItemMinSize(self.imageviewer,
																	self.imageviewer.GetSize().GetWidth(),
																	self.imageviewer.GetSize().GetHeight())

	def Destroy(self):
		self.imageviewer.Destroy()

class wxTargetImageWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, window, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.targetimage = wxImageViewer.TargetImagePanel(self.parent, -1, self.callback)
		self.wxwidget.Add(self.targetimage, 0, wxALIGN_CENTER | wxALL, 5)

	def apply(self, evt):
		value = self.targetimage.targets
		self.uiclient.setServer(self.namelist + ('Targets',), value)

	def Destroy(self):
		self.targetimage.Destroy()

	def add(self, namelist, typelist, value):
		self.setWidget(namelist, value)

	def callback(self):
		self.uiclient.setServer(self.namelist + ('Targets',), self.targetimage.targets)

	def _set(self, value):
		if 'Image' in value:
			self.targetimage.setImage(value['Image'])
			self.wxwidget.SetItemMinSize(self.targetimage,
																		self.targetimage.GetSize().GetWidth(),
																		self.targetimage.GetSize().GetHeight())
		if 'Targets' in value:
			self.targetimage.clearTargets()
			for target in value['Targets']:
				x = target[0]
				y = target[1]
				self.targetimage.addTarget(x, y)
		else:
			return

	def setWidget(self, namelist, value):
		self.lock.acquire()
		newvalue = {}
		if namelist == self.namelist + ('Image',):
			newvalue['Image'] = value.data
		elif namelist == self.namelist + ('Targets',):
			newvalue['Targets'] = value
		else:
			self.lock.release()
			return
		evt = SetWidgetEvent(self, newvalue)
		wxPostEvent(self.window, evt)
		self.lock.release()

	def set(self, namelist, value=None):
		if value is None:
			self._set(namelist)
		else:
			self.setWidget(namelist, value)
		
	def delete(self, namelist):
		pass

if __name__ == '__main__':
	import sys
	client = wxUIClient(sys.argv[1], int(sys.argv[2]))

