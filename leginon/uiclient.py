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

	def setServer(self, namelist, value, thread=True):
		if thread:
			threading.Thread(target=self.execute,
												args=('SET', (namelist, value))).start()
		else:
			self.execute('SET', (namelist, value))

	def commandServer(self, namelist, args, thread=True):
		if thread:
			threading.Thread(target=self.execute,
												args=('COMMAND', (namelist, args))).start()
		else:
			self.execute('COMMAND', (namelist, args))

	def addFromServer(self, namelist, typelist, value, read, write):
		raise NotImplementedError

	def setFromServer(self, namelist, value):
		raise NotImplementedError

	def deleteFromServer(self, namelist):
		raise NotImplementedError

class wxUIClient(UIClient):
	def __init__(self, container, serverhostname, serverport, port=None):
		# there are some timing issues to be thought out
		UIClient.__init__(self, serverhostname, serverport, port)
		self.container = container
		threading.Thread(target=self.addServer, args=()).start()

	def addFromServer(self, namelist, typelist, value, read, write):
		# h4X0r
		while(not hasattr(self.container, 'name')):
			time.sleep(0.01)
		self.container.add((self.container.name,) + tuple(namelist),
																									typelist, value, read, write)
		return ''

	def setFromServer(self, namelist, value):
		self.container.set((self.container.name,) + tuple(namelist), value)
		return ''

	def deleteFromServer(self, namelist):
		print 'DEL', namelist
		self.container.delete((self.container.name,) + tuple(namelist))
		return ''

class UIApp(wxApp):
	def __init__(self, serverhostname, serverport, port=None):
		self.serverhostname = serverhostname
		self.serverport = serverport
		self.port = port
		wxApp.__init__(self, 0)
		self.MainLoop()

	def OnInit(self):
		self.frame = wxFrame(NULL, -1, 'UI')
#		self.panel = wxPanel(self.frame, -1)
		self.panel = wxScrolledWindow(self.frame, -1, size=(600, 700))
		self.panel.SetScrollRate(1, 1)		
#		self.panel.SetSize(self.frame.GetClientSize())
		containerclass = wxClientContainerFactory(wxStaticBoxContainerWidget)
		self.container = containerclass((self.serverhostname, self.serverport),
																		('UI',), self.panel, self, self.port)
		self.panel.SetAutoLayout(true)
		self.panel.SetSizer(self.container.wxwidget)
#		self.container.wxwidget.Fit(self.frame)
		size = self.panel.GetSize()
#		self.container.wxwidget.SetDimension(0, 0, size.GetWidth(), size.GetHeight())
		self.SetTopWindow(self.frame)
		self.panel.Show(true)
		self.frame.Fit()
		self.frame.Show(true)
		return true

	def Fit(self):
		pass

class Widget(object):
	def __init__(self, uiclient, namelist):
		self.uiclient = uiclient
		self.namelist = namelist
		self.name = namelist[-1]

class ContainerWidget(Widget):
	def __init__(self, uiclient, namelist):
		Widget.__init__(self, uiclient, namelist)
		self.children = {}

	def addWidget(self, namelist, typelist, value, read, write):
		raise NotImplementedError

	def add(self, namelist, typelist, value, read, write):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if len(namelist) - len(self.namelist) == 1:
				self.addWidget(namelist, typelist, value, read, write)
			elif childnamelist in self.children and isinstance(
																self.children[childnamelist], ContainerWidget):
				self.children[childnamelist].add(namelist, typelist, value, read, write)
			else:
				raise ValueError
		else:
			raise ValueError

	def setWidget(self, widget, value):
		raise NotImplementedError

	def set(self, namelist, value):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if childnamelist in self.children:
				if namelist in self.children:
					widget = self.children[namelist]
					self.setWidget(widget, value)
				else:
					self.children[childnamelist].set(namelist, value)
			else:
				raise ValueError
		else:
			raise ValueError

	def deleteWidget(self, widget):
		raise NotImplementedError

	def delete(self, namelist):
		childnamelist = namelist[:len(self.namelist) + 1]
		if namelist[:len(self.namelist)] == self.namelist:
			if len(namelist) - len(self.namelist) == 1:
				widget = self.children[namelist]
				del self.children[namelist]
				self.deleteWidget(widget)
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
						elif typelist[2] == 'click image':
							return wxClickImageWidget
						elif typelist[2] == 'target image':
							return wxTargetImageWidget
						elif typelist[2] == 'dialog':
							return wxDialogWidget
						elif typelist[2] == 'medium':
							return wxNotebookContainerWidget
						elif typelist[2] == 'large':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return wxClientContainerFactory(wxNotebookContainerWidget)
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
	def __init__(self, namelist, container, typelist, parent, value, read, write):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_WIDGET)
		self.widget_type = WidgetClassFromTypeList(typelist)
		self.namelist = namelist
		self.container = container
		self.parent = parent
		self.value = value
		self.read = read
		self.write = write

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

wxEVT_NOTEBOOK_SELECT_PAGE = wxNewEventType()

class NotebookSelectPageEvent(wxPyEvent):
	def __init__(self, notebook, pagenumber):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_NOTEBOOK_SELECT_PAGE)
		self.notebook = notebook
		self.pagenumber = pagenumber

class wxContainerWidget(ContainerWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent):
		ContainerWidget.__init__(self, uiclient, namelist)
		self.widgethandler = widgethandler
		self.parent = parent
		self.lock = threading.Lock()
		self.event = threading.Event()
		self.notebook = None
		self.widgetplace = self.parent

	def addWidget(self, namelist, typelist, value, read, write):
		self.lock.acquire()
		self.event.clear()
		evt = AddWidgetEvent(namelist, self, typelist, self.widgetplace, value,
													read, write)
		wxPostEvent(self.widgethandler, evt)
		self.event.wait()

	def setWidget(self, widget, value):
		self.lock.acquire()
		evt = SetWidgetEvent(widget, value)
		wxPostEvent(self.widgethandler, evt)
		self.lock.release()

	def deleteWidget(self, widget):
		self.lock.acquire()
		evt = DeleteWidgetEvent(self, widget)
		wxPostEvent(self.widgethandler, evt)
		self.lock.release()

	def getWxNotebook(self):
		if self.notebook is None:
			self.notebook = wxNotebook(self.widgetplace, -1)
			self.notebooksizer = wxNotebookSizer(self.notebook)
			if hasattr(self, 'wxwidget'):
				#self.wxwidget.Add(self.notebooksizer, 0, wxCENTER | wxALL, 5)
				#self.wxwidget.Add(self.notebooksizer, 0, wxALL, 5)
				self.wxwidget.Add(self.notebooksizer, 1, wxEXPAND | wxALL, 5)
		return self.notebook

#	def _Layout(self):
#		for child in self.children.values():
#			if hasattr(child, '_Layout'):
#				child._Layout()
#		if hasattr(self, 'wxwidget'):
#			self.wxwidget.Layout()
#		if self.notebook is not None:
#			self.notebook.Refresh()

	def Destroy(self):
		for key in self.children.keys():
			child = self.children[key]
			del self.children[key]
			child.Destroy()
			try:
				self.wxwidget.Remove(child.wxwidget)
			except:
				pass
		if self.notebook is not None:
			self.notebook.Destroy()

class wxStaticBoxContainerWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent, container):
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.staticbox = wxStaticBox(self.parent, -1, self.name)
		self.wxwidget = wxStaticBoxSizer(self.staticbox, wxVERTICAL)
		self.container = container

	def Fit(self):
		if isinstance(self.parent, wxScrolledWindow):
			self.wxwidget.FitInside(self.parent)
		else:
			self.wxwidget.Fit(self.parent)
		if self.container is not None:
			self.container.Fit()

	def Destroy(self):
		wxContainerWidget.Destroy(self)
		self.staticbox.Destroy()

class wxNotebookContainerWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent, container, notebook):
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.parentnotebook = notebook
		self.panel = wxPanel(notebook, -1)
		notebook.AddPage(self.panel, self.name)
		self.wxwidget = wxBoxSizer(wxVERTICAL)
		self.panel.SetAutoLayout(true)
		self.panel.SetSizer(self.wxwidget)
		self.panel.Show(true)
		self.widgetplace = self.panel
		self.container = container

	def Fit(self):
		if self.container is not None:
			self.container.Fit()

	def addWidget(self, namelist, typelist, value, read, write):
		# needs locking to insure page number, etc.
		evt = NotebookSelectPageEvent(self.parentnotebook, self.getPageNumber())
		wxPostEvent(self.widgethandler, evt)
		wxContainerWidget.addWidget(self, namelist, typelist, value, read, write)

	def Destroy(self):
		wxContainerWidget.Destroy(self)
		self.parentnotebook.DeletePage(self.getPageNumber())

	def getPageNumber(self):
		for i in range(self.parentnotebook.GetPageCount()):
			if self.parentnotebook.GetPage(i) == self.panel:
				return i

class wxClientContainerWidget(object):
	pass

def wxClientContainerFactory(wxcontainerwidget):
	class wxClientContainer(wxClientContainerWidget, wxcontainerwidget):
		def __init__(self, serverhostnameport, namelist, parent, container,
									port=None, **kwargs):
			uiclient = wxUIClient(self, serverhostnameport[0],
																	serverhostnameport[1], port)
			namelist = (namelist[-1],)
			self.widgethandler = wxEvtHandler()
			self.widgethandler.Connect(-1, -1, wxEVT_ADD_WIDGET,
																	self.addWidgetHandler)
			self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET,
																	self.setWidgetHandler)
			self.widgethandler.Connect(-1, -1, wxEVT_DELETE_WIDGET,
																	self.deleteWidgetHandler)
			self.widgethandler.Connect(-1, -1, wxEVT_NOTEBOOK_SELECT_PAGE,
																	self.notebookPageSelectHandler)

			wxcontainerwidget.__init__(self, uiclient, namelist, self.widgethandler,
																	parent, container, **kwargs)

		def addWidgetHandler(self, evt):
			if issubclass(evt.widget_type, DataWidget):
				uiwidget = evt.widget_type(self.uiclient, evt.namelist,
																		self.widgethandler, evt.parent, evt.read,
																		evt.write)
			elif issubclass(evt.widget_type, wxStaticBoxContainerWidget):
				uiwidget = evt.widget_type(self.uiclient, evt.namelist,
																		self.widgethandler, evt.parent,
																		evt.container)
			elif issubclass(evt.widget_type, wxNotebookContainerWidget):
				notebook = evt.container.getWxNotebook()
				if issubclass(evt.widget_type, wxClientContainerWidget):
					uiwidget = evt.widget_type(evt.value, evt.namelist, evt.parent,
																			evt.container, notebook=notebook)
				else:
					uiwidget = evt.widget_type(self.uiclient, evt.namelist,
																		self.widgethandler, evt.parent,
																		evt.container, notebook)
			elif issubclass(evt.widget_type, wxClientContainerWidget):
				uiwidget = evt.widget_type(evt.value, evt.namelist, evt.parent)
			else:
				uiwidget = evt.widget_type(self.uiclient, evt.namelist,
																		self.widgethandler, evt.parent)
			evt.container.children[evt.namelist] = uiwidget
			if isinstance(uiwidget, DataWidget):
				uiwidget.set(evt.value)
			if hasattr(uiwidget, 'wxwidget'):
				if not isinstance(uiwidget, wxNotebookContainerWidget):
					#evt.container.wxwidget.Add(uiwidget.wxwidget, 0, wxCENTER | wxALL, 5)
					#evt.container.wxwidget.Add(uiwidget.wxwidget, 0, wxALL, 5)
					evt.container.wxwidget.Add(uiwidget.wxwidget, 0, wxEXPAND | wxALL, 5)
#			self._Layout()
			if hasattr(evt.container, 'wxwidget'):
				evt.parent.Layout()
				evt.container.wxwidget.Layout()
				minsize = evt.container.wxwidget.GetMinSize()
				size = evt.parent.GetSize()
				if minsize[0] > size[0] or minsize[1] > size[1]:
					evt.parent.Fit()
					evt.container.Fit()
			evt.container.event.set()
			evt.container.lock.release()

		def setWidgetHandler(self, evt):
			evt.widget.set(evt.value)

		def deleteWidgetHandler(self, evt):
			evt.widget.Destroy()
			if hasattr(evt.widget, 'wxwidget'):
				try:
					evt.container.wxwidget.Remove(evt.widget.wxwidget)
				except:
					pass
#			self._Layout()
			evt.container.Fit()

		def notebookPageSelectHandler(self, evt):
			evt.notebook.SetSelection(evt.pagenumber)

	return wxClientContainer

class MethodWidget(Widget):
	def __init__(self, uiclient, namelist):
		Widget.__init__(self, uiclient, namelist)

	def commandServer(self, args=()):
		self.uiclient.commandServer(self.namelist, args)

	def command(self, evt):
		self.commandServer()

class wxMethodWidget(MethodWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent):
		MethodWidget.__init__(self, uiclient, namelist)
		self.widgethandler = widgethandler
		self.parent = parent

	def Destroy(self):
		pass

class wxButtonWidget(wxMethodWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent):
		wxMethodWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.button = wxButton(self.parent, -1, self.name)
		EVT_BUTTON(self.parent, self.button.GetId(), self.command)
		self.wxwidget.Add(self.button, 0, wxALIGN_CENTER | wxALL, 0)

class DataWidget(Widget):
	def __init__(self, uiclient, namelist, read, write):
		if read:
			self.read = True
		else:
			self.read = False
		if write:
			self.write = True
		else:
			self.write = False
		Widget.__init__(self, uiclient, namelist)

	def setServer(self, value):
		self.uiclient.setServer(self.namelist, value)

	def set(self, value):
		if isinstance(value, xmlrpclib.Binary):
			self.value = value.data
		else:
			self.value = value

class wxDataWidget(DataWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent, read, write):
		DataWidget.__init__(self, uiclient, namelist, read, write)
		self.widgethandler = widgethandler
		self.parent = parent

	def Destroy(self):
		pass

class wxEntryWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent, read, write):
		wxDataWidget.__init__(self, uiclient, namelist, widgethandler, parent, read, write)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		if self.write:
			self.applybutton = wxButton(self.parent, -1, 'Apply')
			self.applybutton.Enable(false)
			EVT_BUTTON(self.parent, self.applybutton.GetId(), self.apply)
			self.entry = wxTextCtrl(self.parent, -1, style=wxTE_PROCESS_ENTER)
			EVT_TEXT(self.parent, self.entry.GetId(), self.onEdit)
			EVT_TEXT_ENTER(self.parent, self.entry.GetId(), self.onEnter)
		else:
			self.entry = wxStaticText(self.parent, -1, '')
		#self.wxwidget.Add(self.label, 0, wxALIGN_RIGHT | wxALL, 5)
		self.wxwidget.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		#self.wxwidget.Add(self.entry, 0, wxALIGN_LEFT | wxALL, 5)
		self.wxwidget.Add(self.entry, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		if hasattr(self, 'applybutton'):
			#self.wxwidget.Add(self.applybutton, 0, wxALIGN_CENTER | wxALL, 5)
			self.wxwidget.Add(self.applybutton, 0, wxALIGN_CENTER|wxLEFT|wxRIGHT, 3)

	def Destroy(self):
		if hasattr(self, 'applybutton'):
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
		if isinstance(self.entry, wxStaticText):
			self.entry.SetLabel(str(self.value))
			entrysize = self.entry.GetSize()
			self.wxwidget.SetItemMinSize(self.entry, entrysize.GetWidth(),
																								entrysize.GetHeight())
		else:
			self.entry.SetValue(str(self.value))
		if hasattr(self, 'applybutton'):
			self.applybutton.Enable(false)

class wxCheckBoxWidget(wxDataWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent, read, write):
		wxDataWidget.__init__(self, uiclient, namelist, widgethandler, parent, read, write)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.checkbox = wxCheckBox(self.parent, -1, self.name)
		if not self.write:
			self.checkbox.Enable(false)
		else:
			EVT_CHECKBOX(self.parent, self.checkbox.GetId(), self.apply)
		#self.wxwidget.Add(self.checkbox, 0, wxALIGN_CENTER | wxALL, 5)
		self.wxwidget.Add(self.checkbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)

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
	def __init__(self, uiclient, namelist, widgethandler, parent, read, write):
		wxDataWidget.__init__(self, uiclient, namelist, widgethandler, parent, read, write)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		if self.write:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1,
																								self.name, self.apply)
		else:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name)
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
	def __init__(self, uiclient, namelist, widgethandler, parent):
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.dialog = MessageDialog(self.parent, -1, self.name, self.callback)
		self.messageflag = False
		self.okflag = False

	def add(self, namelist, typelist, value, read, write):
		self.setWidget(namelist, value)

	def Destroy(self):
		self.dialog.Destroy()

	# not thread safe
	def Show(self):
		messagesize = self.dialog.message.GetSize()
		self.dialog.sizer.SetItemMinSize(self.dialog.message,
																messagesize.GetWidth(), messagesize.GetHeight())
		self.dialog.sizer.Layout()
		self.dialog.sizer.Fit(self.dialog)
		self.dialog.Show(true)

	def _set(self, value):
		if value is not None:
			self.dialog.message.SetLabel(value)
		if self.messageflag and self.okflag:
			self.Show()

	def setWidget(self, namelist, value):
		self.lock.acquire()
		if namelist == self.namelist + ('Message',):
			self.messageflag = True
			evt = SetWidgetEvent(self, value)
			wxPostEvent(self.widgethandler, evt)
		elif namelist == self.namelist + ('OK',):
			self.okflag = True
			evt = SetWidgetEvent(self, None)
			wxPostEvent(self.widgethandler, evt)
		self.lock.release()

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
	def __init__(self, uiclient, namelist, widgethandler, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.wxwidget = wxBoxSizer(wxHORIZONTAL)
		self.combobox = wxComboBox(self.parent, -1,
																style=wxCB_DROPDOWN | wxCB_READONLY)
		self.combobox.Enable(false)
		EVT_COMBOBOX(self.parent, self.combobox.GetId(), self.apply)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		#self.wxwidget.Add(self.label, 0, wxALIGN_CENTER | wxALL, 5)
		self.wxwidget.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		#self.wxwidget.Add(self.combobox, 0, wxALIGN_CENTER | wxALL, 5)
		self.wxwidget.Add(self.combobox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.value = {'List': None, 'Selected': None}

	def apply(self, evt):
		value = [evt.GetSelection()]
		self.uiclient.setServer(self.namelist + ('Selected',), value)

	def Destroy(self):
		self.label.Destroy()
		self.combobox.Destroy()

	def add(self, namelist, typelist, value, read, write):
		self.setWidget(namelist, value)

	def _set(self, value):
		if 'List' in value:
			self.combobox.Clear()
			for i in range(len(value['List'])):
				self.combobox.Append(str(value['List'][i]))
			if value['List']:
				self.combobox.Enable(true)
			else:
				self.combobox.Enable(false)
		if 'Selected' in value and value['Selected'] and self.value['List']:
			i = value['Selected'][0]
			self.combobox.SetValue(str(value['List'][i]))

	def setWidget(self, namelist, value):
		self.lock.acquire()
		if namelist == self.namelist + ('List',):
			self.value['List'] = value
		elif namelist == self.namelist + ('Selected',):
			self.value['Selected'] = value
		else:
			self.lock.release()
			return
		if self.value['List'] is not None and self.value['Selected'] is not None:
			evt = SetWidgetEvent(self, self.value)
			wxPostEvent(self.widgethandler, evt)
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
	def __init__(self, uiclient, namelist, widgethandler, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
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

	def add(self, namelist, typelist, value, read, write):
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
			wxPostEvent(self.widgethandler, evt)
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
	def __init__(self, uiclient, namelist, widgethandler, parent, read, write):
		wxDataWidget.__init__(self, uiclient, namelist, widgethandler, parent, read, write)
		self.wxwidget = wxBoxSizer(wxVERTICAL)
		self.imageviewer = wxImageViewer.ImagePanel(self.parent, -1)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.wxwidget.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.wxwidget.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)

	def set(self, value):
		# not keeping track of image for now
		#DataWidget.set(self, value)
		if value.data:
			self.imageviewer.setImageFromMrcString(value.data)
			imageviewersize = self.imageviewer.GetSize()
			self.wxwidget.SetItemMinSize(self.imageviewer,
												imageviewersize.GetWidth(), imageviewersize.GetHeight())
			#self.parent.Layout()
		else:
			self.imageviewer.clearImage()

	def Destroy(self):
		self.label.Destroy()
		self.imageviewer.Destroy()

class wxClickImageWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent):
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.wxwidget = wxBoxSizer(wxVERTICAL)
		self.clickimage = wxImageViewer.ClickImagePanel(self.parent, -1,
																											self.callback)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.wxwidget.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.wxwidget.Add(self.clickimage, 0, wxALIGN_CENTER | wxALL, 5)

	def Destroy(self):
		self.label.Destroy()
		self.targetimage.Destroy()

	def add(self, namelist, typelist, value, read, write):
		self.setWidget(namelist, value)

	def callback(self, xy):
		self.uiclient.setServer(self.namelist + ('Coordinates',), xy, False)
		self.uiclient.commandServer(self.namelist + ('Click',), (), True)

	def _set(self, value):
		if value:
			self.clickimage.setImageFromMrcString(value)
			width, height = self.targetimage.GetSizeTuple()
			self.wxwidget.SetItemMinSize(self.clickimage, width, height)
		else:
			self.clickimage.clearImage()

	def setWidget(self, namelist, value):
		if namelist == self.namelist + ('Image',):
			evt = SetWidgetEvent(self, value.data)
			wxPostEvent(self.widgethandler, evt)

	def set(self, namelist, value=None):
		if value is None:
			self._set(namelist)
		else:
			self.setWidget(namelist, value)
		
	def delete(self, namelist):
		pass

class wxTargetImageWidget(wxContainerWidget):
	def __init__(self, uiclient, namelist, widgethandler, parent):
		self.lock = threading.Lock()
		wxContainerWidget.__init__(self, uiclient, namelist, widgethandler, parent)
		self.wxwidget = wxBoxSizer(wxVERTICAL)
		self.targetimage = wxImageViewer.TargetImagePanel(self.parent, -1, self.callback)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.wxwidget.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.wxwidget.Add(self.targetimage, 0, wxALIGN_CENTER | wxALL, 5)

	def Destroy(self):
		self.label.Destroy()
		self.clickimage.Destroy()

	def add(self, namelist, typelist, value, read, write):
		self.setWidget(namelist, value)

	def callback(self, name, value):
		self.uiclient.setServer(self.namelist + (name,), value)

	def _set(self, value):
		for key in value:
			if key == 'Image':
				if value['Image']:
					self.targetimage.setImageFromMrcString(value['Image'])
					targetimagesize = self.targetimage.GetSize()
					self.wxwidget.SetItemMinSize(self.targetimage,
											targetimagesize.GetWidth(), targetimagesize.GetHeight())
					#self.parent.Layout()
				else:
					self.targetimage.clearImage()
			else:
				self.targetimage.setTargetType(key, value[key])

	def setWidget(self, namelist, value):
		self.lock.acquire()
		newvalue = {}
		if namelist == self.namelist + ('Image',):
			newvalue['Image'] = value.data
		elif namelist[:-1] == self.namelist:
			newvalue[namelist[-1]] = value
		else:
			self.lock.release()
			return
		evt = SetWidgetEvent(self, newvalue)
		wxPostEvent(self.widgethandler, evt)
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
	client = UIApp(sys.argv[1], int(sys.argv[2]))

