import xmlrpclib
import uiserver
import threading
import time
from wxPython.wx import *
import wxImageViewer

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
		self.app = UIApp(0)
		UIClient.__init__(self, serverhostname, serverport, port)
		# quick
		self.app.uiclient = self
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
		evt.container.wxwidget.Add(uiwidget.wxwidget)
		# needs to callback
		self.Layout()
		evt.container.event.set()
		evt.container.lock.release()

	def setWidget(self, evt):
		evt.widget.set(evt.value)

	def deleteWidget(self, evt):
		evt.widget.Destroy()
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
	if typelist and typelist[0] == 'object':
		if len(typelist) > 1 and typelist[1] == 'container':
			return wxStaticBoxContainerWidget
		elif len(typelist) > 1 and typelist[1] == 'data':
			if len(typelist) > 2 and typelist[2] == 'binary':
				if len(typelist) > 3 and typelist[3] == 'image':
					return wxImageWidget
				else:
					return wxEntryWidget
			else:
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

class wxImageWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, window, parent):
		wxDataWidget.__init__(self, uiclient, namelist, window, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.imageviewer = wxImageViewer.ImagePanel(self.parent, -1)
		#self.imageviewer.SetSize(wxSize(512, 512))
		self.wxwidget.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)

	def set(self, value):
		DataWidget.set(self, value)
		self.imageviewer.setImage(self.value)
		self.wxwidget.SetItemMinSize(self.imageviewer,
																	self.imageviewer.GetSize().GetWidth(),
																	self.imageviewer.GetSize().GetHeight())

