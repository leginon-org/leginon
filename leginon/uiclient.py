#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import extendedxmlrpclib
import uiserver
import threading
import time
import sys
from wxPython.wx import *
from wxPython.wxc import wxPyAssertionError
import wxImageViewer
import wxDictTree
import wxOrderedListBox
import wxMaster
import wxGridTray
import wxMessageLog
from Numeric import arraytype

wxEVT_ADD_WIDGET = wxNewEventType()
wxEVT_SET_WIDGET = wxNewEventType()
wxEVT_REMOVE_WIDGET = wxNewEventType()
wxEVT_CONFIGURE_WIDGET = wxNewEventType()
wxEVT_SET_SERVER = wxNewEventType()
wxEVT_COMMAND_SERVER = wxNewEventType()
wxEVT_ADD_MESSAGE = wxNewEventType()
wxEVT_REMOVE_MESSAGE = wxNewEventType()

class AddWidgetEvent(wxPyEvent):
	def __init__(self, dependencies, namelist, typelist, value,	
								configuration, event, children):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_WIDGET)
		self.namelist = namelist
		self.typelist = typelist
		self.value = value
		self.configuration = configuration
		self.dependencies = dependencies
		self.event = event
		self.children = children

class SetWidgetEvent(wxPyEvent):
	def __init__(self, namelist, value, event):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_WIDGET)
		self.namelist = namelist
		self.value = value
		self.event = event

class RemoveWidgetEvent(wxPyEvent):
	def __init__(self, namelist, event):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_REMOVE_WIDGET)
		self.namelist = namelist
		self.event = event

class ConfigureWidgetEvent(wxPyEvent):
	def __init__(self, namelist, configuration, event):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_CONFIGURE_WIDGET)
		self.namelist = namelist
		self.configuration = configuration
		self.event = event

class SetServerEvent(wxPyEvent):
	def __init__(self, namelist, value, thread=True):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_SET_SERVER)
		self.namelist = namelist
		self.value = value
		self.thread = thread

class CommandServerEvent(wxPyEvent):
	def __init__(self, namelist, args=(), thread=True):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_COMMAND_SERVER)
		self.namelist = namelist
		self.args = args
		self.thread = thread

class AddMessageEvent(wxPyEvent):
	def __init__(self, type, message):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_MESSAGE)
		self.type = type
		self.message = message

class RemoveMessageEvent(wxPyEvent):
	def __init__(self, type, message):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_REMOVE_MESSAGE)
		self.type = type
		self.message = message

def WidgetClassFromTypeList(typelist):
	if typelist:
		if typelist[0] == 'object':
			if len(typelist) > 1:
				if typelist[1] == 'container':
					if len(typelist) > 2:
						if typelist[2] == 'single select from list':
							return wxComboBoxWidget
						elif typelist[2] == 'select from list':
							return wxOrderedListBoxWidget
						elif typelist[2] == 'select from struct':
							return wxTreeSelectWidget
						elif typelist[2] == 'click image':
							return wxClickImageWidget
						elif typelist[2] == 'target image':
							return wxTargetImageWidget
						elif typelist[2] == 'dialog':
							if len(typelist) > 3:
								if typelist[3] == 'message':
									return wxMessageDialogWidget
								elif typelist[3] == 'file':
									return wxFileDialogWidget
							return wxDialogContainerWidget
						elif typelist[2] == 'external':
							return wxDialogContainerWidget
						elif typelist[2] == 'medium':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return wxClientContainerFactory(wxNotebookContainerWidget)
							return wxNotebookContainerWidget
						elif typelist[2] == 'large':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return wxClientContainerFactory(wxTreePanelContainerWidget)
							return wxTreePanelContainerWidget
						elif typelist[2] == 'message':
							return wxMessageWidget
						elif typelist[2] == 'message log':
							return wxMessageLogWidget
					return wxStaticBoxContainerWidget
				elif typelist[1] == 'method':
					return wxButtonWidget
				elif typelist[1] == 'data':
					if len(typelist) > 2:
						if typelist[2] == 'integer':
							if len(typelist) > 3:
								if typelist[3] == 'progress':
									return wxProgressWidget
							else:
								return entryWidgetClass([int])
						elif typelist[2] == 'boolean':
							return wxCheckBoxWidget
						elif typelist[2] == 'float':
							return entryWidgetClass([float])
						elif typelist[2] == 'number':
							return entryWidgetClass([int, float])
						elif typelist[2] == 'struct':
							if len(typelist) > 3:
								if typelist[3] == 'application':
									return wxApplicationWidget
							return wxTreeCtrlWidget
						elif typelist[2] == 'binary':
							if len(typelist) > 3:
								if typelist[3] == 'image':
									return wxImageWidget
								elif typelist[3] == 'PIL image':
									return wxPILImageWidget
						elif typelist[2] == 'array':
							if len(typelist) > 3:
								if typelist[3] == 'sequence':
									return wxListBoxWidget
								elif typelist[3] == 'grid tray':
									return wxGridTrayWidget
							return entryWidgetClass([list, tuple])
					return wxEntryWidget
	raise ValueError('invalid type for widget')
	
class XMLRPCClient(object):
	def __init__(self, serverhostname, serverport, port=None):
		uri = 'http://%s:%s' % (serverhostname, serverport)
		self.proxy = extendedxmlrpclib.ServerProxy(uri, allow_none=1)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except extendedxmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except extendedxmlrpclib.Fault:
			# exception during call of the function
			raise

class LocalUIClient(object):
	def __init__(self, uiserver):
		self.uiserver = uiserver

	def addServer(self):
		self.uiserver.addLocalClient(self)

	def setServer(self, namelist, value, thread=False):
		self.uiserver.setFromClient(namelist, value)

	def commandServer(self, namelist, args, thread=False):
		if thread:
			threading.Thread(target=self.uiserver.commandFromClient,
												args=(namelist, args)).start()
		else:
			self.uiserver.commandFromClient(namelist, args)

class XMLRPCUIClient(XMLRPCClient, uiserver.XMLRPCServer):
	def __init__(self, serverhostname, serverport, port=None):
		XMLRPCClient.__init__(self, serverhostname, serverport, port)
		uiserver.XMLRPCServer.__init__(self, port)
		self.xmlrpcserver.register_function(self.addFromServer, 'add')
		self.xmlrpcserver.register_function(self.setFromServer, 'set')
		self.xmlrpcserver.register_function(self.removeFromServer, 'remove')
		self.xmlrpcserver.register_function(self.configureFromServer, 'configure')

	def addServer(self):
		self.execute('add client', (self.hostname, self.port))

	def setServer(self, namelist, value, thread=False):
		if thread:
			threading.Thread(target=self.execute,
												args=('set', (namelist, value))).start()
		else:
			self.execute('set', (namelist, value))

	def commandServer(self, namelist, args, thread=False):
		if thread:
			threading.Thread(target=self.execute,
												args=('command', (namelist, args))).start()
		else:
			self.execute('command', (namelist, args))

class wxUIClient(object):
	def __init__(self, container):
		# there are some timing issues to be thought out
		self.container = container

	def addFromServer(self, properties):
		dependencies = properties['dependencies']
		namelist = properties['namelist']
		typelist = properties['typelist']
		value = properties['value']
		configuration = properties['configuration']

		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()

		if 'children' in properties:
			children = properties['children']
		else:
			children = []
		evt = AddWidgetEvent(dependencies, namelist, typelist, value,	
													configuration, threadingevent, children)
		wxPostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

	def setFromServer(self, properties):
		namelist = properties['namelist']
		value = properties['value']
		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()
		evt = SetWidgetEvent(namelist, value, threadingevent)
		wxPostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

	def removeFromServer(self, properties):
		namelist = properties['namelist']
		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()
		evt = RemoveWidgetEvent(namelist, threadingevent)
		wxPostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

	def configureFromServer(self, properties):
		namelist = properties['namelist']
		configuration = properties['configuration']
		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()
		evt = ConfigureWidgetEvent(namelist, configuration, threadingevent)
		wxPostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

class wxLocalClient(LocalUIClient, wxUIClient):
	def __init__(self, server, container):
		LocalUIClient.__init__(self, server)
		wxUIClient.__init__(self, container)
		self.addServer()

class wxXMLRPCClient(XMLRPCUIClient, wxUIClient):
	def __init__(self, serverhostname, serverport, container, port=None):
		XMLRPCUIClient.__init__(self, serverhostname, serverport, port)
		wxUIClient.__init__(self, container)
		threading.Thread(target=self.addServer, args=()).start()

class UIStatusBar(wxStatusBar):
	def __init__(self, parent):
		wxStatusBar.__init__(self, parent, -1)
		self.SetFieldsCount(1)
		self.gauge = wxGauge(self, -1, 100)
		EVT_SIZE(self, self.OnSize)
		self.update()

	def OnSize(self, evt):
		self.update()

	def update(self):
		r = self.GetFieldRect(0)
		self.gauge.SetPosition(wxPoint(r.x + 3*r.width/4 - 2, r.y+2))
		self.gauge.SetSize(wxSize(r.width/4, r.height-4))

class UIApp(wxApp):
	def __init__(self, location, title='UI', containername='UI Client'):
		self.location = location
		self.title = title
		self.containername = containername
		self._shown = True
		self._enabled = True
		wxApp.__init__(self, 0)
		self.MainLoop()

	def OnInit(self):
		self.frame = wxFrame(NULL, -1, self.title, size=(740, 740))
#		self.statusbar = UIStatusBar(self.frame)
#		self.frame.SetStatusBar(self.statusbar)
		self.panel = wxScrolledWindow(self.frame, -1)
		self.panel.SetScrollRate(1, 1)		
		containerclass = wxClientContainerFactory(wxSimpleContainerWidget)
		self.container = containerclass(self.containername, self.panel, self,
																		self.location, {})
		if self.container.sizer is not None:
			self.panel.SetSizer(self.container.sizer)
		self.SetTopWindow(self.frame)
		self.panel.Show(true)
		self.panel.Fit()
		self.frame.Show(true)
		return true

	def _showWidget(self, child, show=True):
		pass

	def layout(self):
		self.panel.Refresh()

class wxWidget(object):
	def __init__(self, name, parent, container, value, configuration):
		self.name = name
		self.parent = parent
		self.container = container
		self.widgethandler = wxEvtHandler()
		if 'enabled' not in configuration:
			configuration['enabled'] = True
		if 'shown' not in configuration:
			configuration['shown'] = True
		self._configure(configuration)

		self.widgethandler.Connect(-1, -1, wxEVT_CONFIGURE_WIDGET,
																self.onConfigureWidget)

	def _configure(self, configuration):
		if 'enabled' in configuration:
			self.enable(configuration['enabled'])
		if 'shown' in configuration:
			self.show(configuration['shown'])

	def onConfigureWidget(self, evt):
		self._configure(evt.configuration)
		if evt.event is not None:
			evt.event.set()

	def _enable(self, enable):
		self._enabled = enable

	def enable(self, enable):
		self.enabled = enable
		if self.container is not None and not self.container._enabled:
			self._enable(False)
		else:
			self._enable(self.enabled)

	def _show(self, show):
		self._shown = show
		if self.container is not None:
			self.container._showWidget(self, show)

	def show(self, show):
		self.shown = show
		if self.container is not None and not self.container._shown:
			self._show(False)
		else:
			self._show(self.shown)

	def setServer(self, value):
		evt = SetServerEvent([self.name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def commandServer(self, args=()):
		evt = CommandServerEvent([self.name], args)
		wxPostEvent(self.container.widgethandler, evt)

class wxContainerWidget(wxWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.children = {}
		self.pending = []
		self.notebook = None
		self.treecontainer = None

		self.nosizerclasses = (wxNotebookContainerWidget, wxDialogContainerWidget,
														wxTreePanelContainerWidget, wxMessageDialogWidget,
														wxFileDialogWidget)
		self.expandclasses = (wxMessageWidget, wxMessageLogWidget)
		wxWidget.__init__(self, name, parent, container, value, configuration)
		self.childparent = self.parent

		self.widgethandler.Connect(-1, -1, wxEVT_ADD_WIDGET, self.onAddWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_REMOVE_WIDGET, self.onRemoveWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_SERVER, self.onSetServer)
		self.widgethandler.Connect(-1, -1, wxEVT_COMMAND_SERVER,
																self.onCommandServer)
		self.widgethandler.Connect(-1, -1, wxEVT_ADD_MESSAGE, self.onAddMessage)
		self.widgethandler.Connect(-1, -1, wxEVT_REMOVE_MESSAGE,
																self.onRemoveMessage)

	def childEvent(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wxPostEvent(child.widgethandler, evt)
				return
		self.pending.append(evt)
		#raise ValueError('No such child to enable widget')

	def _enable(self, enable):
		wxWidget._enable(self, enable)
		for child in self.children.values():
			child.enable(child.enabled)

	def _showWidget(self, child, show):
		if self.sizer is not None and not isinstance(child, self.nosizerclasses):
			self.sizer.Show(child.sizer, show)

	def _show(self, show):
		wxWidget._show(self, show)
		self.showNotebook(show)
		self.showTreeContainer(show)
		for child in self.children.values():
			child.show(child.shown)

	def onConfigureWidget(self, evt):
		if len(evt.namelist) == 0:
			wxWidget.onConfigureWidget(self, evt)
		else:
			self.childEvent(evt)

	def handleDependencies(self, evt):
		for name in self.children:
			for i in evt.dependencies:
				if i == name:
					evt.dependencies.remove(i)
		if evt.dependencies:
			self.pending.append(evt)
			return False
		return True

	def handlePendingEvents(self):
		for evt in list(self.pending):
			self.pending.remove(evt)
			wxPostEvent(self.widgethandler, evt)

	def _addWidgetSizer(self, child, show=True):
		if self.sizer is not None and not isinstance(child, self.nosizerclasses):
			if isinstance(child, self.expandclasses):
				self.sizer.Add(child.sizer, 0, wxALL|wxEXPAND, 3)
			else:
				self.sizer.Add(child.sizer, 0, wxALL, 3)

	def _addWidget(self, name, typelist, value, configuration, children):
		if self._shown:
			show = True
			self._show(False)
		else:
			show = False
		childclass = WidgetClassFromTypeList(typelist)
		child = childclass(name, self.childparent, self, value, configuration)
		self.children[name] = child
		for childproperties in children:
			childname = childproperties['namelist'][-1]
			childtypelist = childproperties['typelist']
			childvalue = childproperties['value']
			childconfiguration = childproperties['configuration']
			try:
				childchildren = childproperties['children']
			except KeyError:
				childchildren = []
			child._addWidget(childname, childtypelist, childvalue,
												childconfiguration, childchildren)

		self._addWidgetSizer(child)
		child.layout()

		self.handlePendingEvents()
		if show:
			self._show(True)

	def onAddWidget(self, evt):
		if len(evt.namelist) == 1:
			if self.handleDependencies(evt):
				self._addWidget(evt.namelist[0], evt.typelist, evt.value,
												evt.configuration, evt.children)
				if evt.event is not None:
					evt.event.set()
		else:
			self.childEvent(evt)

	def onSetWidget(self, evt):
		self.childEvent(evt)

	def _removeWidget(self, name, widget):
		del self.children[name]
		widget.destroy()
		if self.sizer is not None and not isinstance(widget, self.nosizerclasses):
			self.sizer.Remove(widget.sizer)

	def removeChildren(self):
		for name, child in self.children.items():
			self._removeWidget(name, child)

	def onRemoveWidget(self, evt):
		if len(evt.namelist) == 1:
			for name, child in self.children.items():
				if name == evt.namelist[0]:
					self._removeWidget(name, child)
					if evt.event is not None:
						evt.event.set()
			self.pending.append(evt)
			#raise ValueError('No such child to remove widget')
		else:
			self.childEvent(evt)

	def onSetServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def onCommandServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def onAddMessage(self, evt):
		wxPostEvent(self.container.widgethandler, evt)

	def onRemoveMessage(self, evt):
		wxPostEvent(self.container.widgethandler, evt)

	def showNotebook(self, show):
		if self.notebook is not None:
			self.notebook.Show(show)

	def getNotebook(self):
		if self.notebook is None:
			self.notebook = wxNotebook(self.childparent, -1)#, style=wxCLIP_CHILDREN)
			self.notebooksizer = wxNotebookSizer(self.notebook)
			if self.sizer is not None:
				self.sizer.Add(self.notebooksizer, 0,
												wxEXPAND|wxALIGN_CENTER_HORIZONTAL|wxALL, 5)
			self.layout()
		return self.notebook

	def removeNotebook(self):
		if self.notebook is not None:
			self.notebook.Destroy()
			self.notebook = None
			self.sizer.Remove(self.notebooksizer)
			self.notebooksizer = None

	def getTreeContainer(self):
		if self.treecontainer is None:
			self.treecontainer = wxTreePanel(self.childparent)
			if self.sizer is not None:
				self.sizer.Add(self.treecontainer, 1,
												wxEXPAND|wxALIGN_CENTER_HORIZONTAL|wxALL, 5)
			self.layout()
		return self.treecontainer

	def showTreeContainer(self, show):
		if self.treecontainer is not None:	
			self.treecontainer.show(show)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		if isinstance(self.childparent, wxScrolledWindow):
			self.childparent.FitInside()
		else:
			self.childparent.Fit()
		self.container.layout()

	def destroy(self):
		self.removeChildren()
		self.removeNotebook()

class wxSimpleContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxVERTICAL)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def destroy(self):
		wxContainerWidget.destroy(self)

	def _addWidget(self, name, typelist, value, configuration, children):
		wxContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

class wxStaticBoxContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.staticbox = wxStaticBox(parent, -1, name)
		self.sizer = wxStaticBoxSizer(self.staticbox, wxVERTICAL)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _show(self, show):
		self.staticbox.Show(show)
		wxContainerWidget._show(self, show)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.staticbox.Destroy()

	def _addWidget(self, name, typelist, value, configuration, children):
		wxContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

class wxNotebookContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.parentnotebook = self.container.getNotebook()
		self.panel = wxPanel(self.parentnotebook, -1)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.panel.SetSizer(self.sizer)
		self.panel.Show(true)
		self.childparent = self.panel
		self.parentnotebook.AddPage(self.panel, self.name)
		self.layout()

	def layout(self):
		self.sizer.Layout()
		self.childparent.Fit()
		self.container.notebooksizer.Layout()
		self.container.notebooksizer.Fit(self.parentnotebook)
		self.container.layout()

	def _addWidget(self, name, typelist, value, configuration, children):
		wxContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.parentnotebook.DeletePage(self.getPageNumber())

	def getPageNumber(self):
		for i in range(self.parentnotebook.GetPageCount()):
			if self.parentnotebook.GetPage(i) == self.panel:
				return i

class wxDialogContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.dialog = wxDialog(parent, -1, name,
									style=wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX|wxRESIZE_BORDER)
		self.panel = wxScrolledWindow(self.dialog, -1)
		self.panel.SetScrollRate(1, 1)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.panel.SetSizer(self.sizer)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.childparent = self.panel
		self.layout()


	def getParentCenter(self):
		parent = self.parent
		position = wxPoint()
		while parent is not None:
			position += parent.GetPosition()
			parent = parent.GetParent()
		parentsize = self.parent.GetSize()
		dialogsize = self.dialog.GetSize()
		position.x += (parentsize.x - dialogsize.x)/2
		position.y += (parentsize.y - dialogsize.y)/2
		return position

	def _show(self, show):
		self.panel.Show(show)
		self.dialog.SetPosition(self.getParentCenter())
		self.dialog.Show(show)
		wxContainerWidget._show(self, show)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.dialog.Destroy()

	def layout(self):
		self.sizer.Layout()
		self.sizer.Fit(self.panel)
		self.dialog.Fit()

class wxClientContainerWidget(object):
	pass

def wxClientContainerFactory(wxcontainerwidget):
	class wxClientContainer(wxClientContainerWidget, wxcontainerwidget):
		def __init__(self, name, parent, container, value, configuration):
			wxcontainerwidget.__init__(self, name, parent, container, value,
																	configuration)
			if 'instance' in value and value['instance'] is not None:
				clientclass = wxLocalClient
				args = (value['instance'],)
			elif 'hostname' in value and value['hostname'] is not None \
						and 'XML-RPC port' in value and value['XML-RPC port'] is not None:
				clientclass = wxXMLRPCClient
				args = (value['hostname'], value['XML-RPC port'])
			else:
				raise ValueError('No location information to create client container')
			self.uiclient = apply(clientclass, args + (self,))

		def onSetServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.setServer(evt.namelist, evt.value, evt.thread)

		def onCommandServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.commandServer(evt.namelist, evt.args, evt.thread)

		def onAddMessage(self, evt):
			pass

		def onRemoveMessage(self, evt):
			pass

	return wxClientContainer

class wxMethodWidget(wxWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxWidget.__init__(self, name, parent, container, value, configuration)

	def commandFromWidget(self, evt=None):
		wxWidget.commandServer(self)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		pass

class wxButtonWidget(wxMethodWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.button = wxButton(parent, -1, name)
		wxMethodWidget.__init__(self, name, parent, container, value, configuration)
		EVT_BUTTON(self.parent, self.button.GetId(), self.commandFromWidget)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER | wxALL, 0)
		self.layout()

	def _enable(self, enable):
		self.button.Enable(enable)
		wxMethodWidget._enable(self, enable)

	def _show(self, show):
		self.button.Show(show)
		wxMethodWidget._show(self, show)

class wxDataWidget(wxWidget):
	def __init__(self, name, parent, container, value, configuration):
		if 'read' in configuration and configuration['read']:
			self.read = True
		else:
			self.read = False

		if 'write' in configuration and configuration['write']:
			self.write = True
		else:
			self.write = False

		wxWidget.__init__(self, name, parent, container, value, configuration)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)

	def onSetWidget(self, evt):
		self.set(evt.value)
		if evt.event is not None:
			evt.event.set()

	def setWidget(self, value):
		pass

	def setValue(self, value):
		if isinstance(value, extendedxmlrpclib.Binary):
			self.value = value.data
		else:
			self.value = value

	def set(self, value):
		self.setValue(value)
		self.setWidget(value)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		pass

class wxProgressWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.gauge = wxGauge(self.parent, -1, 100, style=wxGA_HORIZONTAL)
		size = self.gauge.GetSizeTuple()
		self.gauge.SetSize((size[0]*4, size[1]))

		self.set(value)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.gauge, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def _enable(self, enable):
		self.label.Enable(enable)
		self.gauge.Enable(enable)
		wxDataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.gauge.Show(show)
		wxDataWidget._show(self, show)

	def setWidget(self, value):
		self.gauge.SetValue(value)

	def destroy(self):
		self.label.Destroy()
		self.gauge.Destroy()

class wxGridTrayWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.gridtray = wxGridTray.GridTrayPanel(parent, self.setServer)

		self.set(value)

		self.sizer.Add(self.gridtray)
		self.sizer.SetItemMinSize(self.gridtray,
															self.gridtray.gridtraybitmap.GetSize())
		self.layout()

	def setWidget(self, value):
		self.gridtray.set(value)

	def destroy(self):
		self.gridtray.Destroy()

class wxEntryWidget(wxDataWidget):
	types = [str]
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(parent, -1, name + ':')

		if 'write' in configuration and configuration['write']:
			self.applybutton = wxButton(parent, -1, 'Apply')
			self.applybutton.Enable(false)
			self.entry = wxTextCtrl(parent, -1, style=wxTE_PROCESS_ENTER)
			self.dirty = False
		else:
			self.entry = wxStaticText(parent, -1, '')

		wxDataWidget.__init__(self, name, parent, container, value, configuration)

		self.set(value)

		if self.write:
			EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.setFromWidget)
			EVT_TEXT(self.entry, self.entry.GetId(), self.onEdit)
			EVT_TEXT_ENTER(self.entry, self.entry.GetId(), self.onEnter)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.entry, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		if hasattr(self, 'applybutton'):
			self.sizer.Add(self.applybutton, 0, wxALIGN_CENTER|wxLEFT|wxRIGHT, 3)
			self.dirty = self.applybutton.IsEnabled()
		self.layout()

	def destroy(self):
		if hasattr(self, 'applybutton'):
			self.applybutton.Destroy()
		self.entry.Destroy()
		self.label.Destroy()

	def onEdit(self, evt):
		self.dirty = True
		self.applybutton.Enable(true)

	def onEnter(self, evt):
		if self.applybutton.IsEnabled():
			self.setFromWidget(evt)

	def setFromWidget(self, evt):
		value = self.entry.GetValue()
		if self.types != [str]:
			try:
				value = eval(value)
			except:
				excinfo = sys.exc_info()
				sys.excepthook(*excinfo)
				if str not in self.types:
					return
		if type(value) not in self.types:
			return
		self.value = value
		self.dirty = False
		self.applybutton.Enable(false)
		self.setServer(self.value)

	def setWidget(self, value):
		if isinstance(self.entry, wxStaticText):
			if value is None:
				self.entry.SetLabel('')
			else:
				self.entry.SetLabel(str(self.value))
			entrysize = self.entry.GetSize()
			self.sizer.SetItemMinSize(self.entry, entrysize.GetWidth(),
																						entrysize.GetHeight())
			minwidth, minheight = self.sizer.GetMinSize()
			width, height = self.sizer.GetSize()
			set = False
			if minwidth > width:
				width = minwidth
				set = True
			if minheight > height:
				height = minheight
				set = True
			if set:
				self.sizer.SetMinSize((width, height))
				self.layout()
		else:
			if value is None:
				self.entry.SetValue('')
			else:
				self.entry.SetValue(str(self.value))
		if hasattr(self, 'applybutton'):
			self.dirty = False
			self.applybutton.Enable(false)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.entry.Enable(enable)
		if hasattr(self, 'applybutton'):
			if enable and self.dirty:
				self.applybutton.Enable(True)
			else:
				self.applybutton.Enable(False)
		wxDataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.entry.Show(show)
		if hasattr(self, 'applybutton'):
			self.applybutton.Show(show)
		wxDataWidget._show(self, show)

def entryWidgetClass(itypes):
	class EWC(wxEntryWidget):
		types = itypes
	return EWC

class wxCheckBoxWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.checkbox = wxCheckBox(parent, -1, name)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		wxDataWidget.__init__(self, name, parent, container, value, configuration)

		self.set(value)

		EVT_CHECKBOX(self.parent, self.checkbox.GetId(), self.setFromWidget)

		self.sizer.Add(self.checkbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def _enable(self, enable):
		if self.write:
			self.checkbox.Enable(enable)
		else:
			self.checkbox.Enable(False)
		wxDataWidget._enable(self, enable)

	def _show(self, show):
		self.checkbox.Show(show)
		wxDataWidget._show(self, show)

	def setFromWidget(self, evt):
		value = self.checkbox.GetValue()
		if value:
			self.value = 1
		else:
			self.value = 0
		self.setServer(self.value)

	def setWidget(self, value):
		self.checkbox.SetValue(self.value)

	def destroy(self):
		self.checkbox.Destroy()

class wxListBoxWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.label = wxStaticText(parent, -1, name)
		self.listbox = wxListBox(parent, -1)
		wxDataWidget.__init__(self, name, parent, container, value, configuration)

		self.set(value)

		EVT_LISTBOX(self.listbox, self.listbox.GetId(), self.OnListBox)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.listbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def _enable(self, enable):
		self.label.Enable(enable)
		self.listbox.Enable(enable)
		wxDataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.listbox.Show(show)
		wxDataWidget._show(self, show)

	def OnListBox(self, evt):
		selection = evt.GetSelection()
		if selection >= 0:
			self.listbox.Deselect(selection)

	def setWidget(self, value):
		self.listbox.Clear()
		for i in value:
			self.listbox.Append(str(i))

	def destroy(self):
		self.label.Destroy()
		self.listbox.Destroy()

class wxTreeCtrlWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		if self.write:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1,
																								self.name, self.setFromWidget)
		else:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name)

		self.set(value)

		self.sizer.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def _enable(self, enable):
		#self.tree.Enable(enable)
		wxDataWidget._enable(self, enable)

	def _show(self, show):
		#self.tree.Show(show)
		wxDataWidget._show(self, show)

	def setFromWidget(self):
		self.setServer(self.value)

	def setWidget(self, value):
		self.tree.set(self.value)

	def destroy(self):
		self.tree.Destroy()

class wxApplicationWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.applicationeditor = wxMaster.ApplicationEditorCanvas(parent, -1)
		self.applybutton = wxButton(parent, -1, 'Apply')
		wxDataWidget.__init__(self, name, parent, container, value, configuration)

		EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.apply)
		self.sizer.Add(self.applicationeditor, 0, wxALIGN_CENTER | wxALL, 5)
		self.sizer.Add(self.applybutton, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

		self.set(value)

	def apply(self, evt):
		self.value = self.applicationeditor.application.getApplication()
		self.setFromWidget()

	def setFromWidget(self):
		self.setServer(self.value)

	def setWidget(self, value):
		self.applicationeditor.application.setApplication(self.value)

	def destroy(self):
		self.applicationeditor.Destroy()

class wxImageWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.label = wxStaticText(parent, -1, name)
		self.imageviewer = wxImageViewer.ImagePanel(parent, -1)
		self.sizer = wxBoxSizer(wxVERTICAL)
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.set(value)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def setValue(self, value):
		# not keeping track of image for now
		pass

	def setWidget(self, value):
		if isinstance(value, arraytype):
			self.imageviewer.setNumericImage(value)
		elif isinstance(value, extendedxmlrpclib.Binary):
			self.imageviewer.setImageFromMrcString(value.data)
		else:
			self.imageviewer.clearImage()
			return
		width, height = self.imageviewer.GetSizeTuple()
		self.sizer.SetItemMinSize(self.imageviewer, width, height)

	def destroy(self):
		self.label.Destroy()
		self.imageviewer.Destroy()

class wxPILImageWidget(wxImageWidget):
	def setWidget(self, value):
		if value.data:
			self.imageviewer.setImageFromPILString(value.data)
			width, height = self.imageviewer.GetSizeTuple()
			self.sizer.SetItemMinSize(self.imageviewer, width, height)
		else:
			self.imageviewer.clearImage()

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

class wxMessageDialogWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.dialog = MessageDialog(self.parent, -1, self.name,
																self.dialogCallback)
		self.messageflag = False
		self.okflag = False

	def setMessage(self, value):
		self.dialog.message.SetLabel(value)

	def display(self):
		width, height = self.dialog.message.GetSizeTuple()
		self.dialog.sizer.SetItemMinSize(self.dialog.message, width, height)
		self.dialog.sizer.Layout()
		self.dialog.sizer.Fit(self.dialog)
		self.dialog.Show(true)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Message':
			self.setMessage(value)
			self.messageflag = True
		elif name == 'OK':
			self.okflag = True
		if self.messageflag and self.okflag:
			self.display()

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['Message']:
			self.setMessage(evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def dialogCallback(self):
		evt = CommandServerEvent([self.name, 'OK'], ())
		wxPostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		self.dialog.Destroy()

class wxComboBoxWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.combobox = wxComboBox(parent, -1, style=wxCB_DROPDOWN | wxCB_READONLY)
		self.label = wxStaticText(parent, -1, name + ':')
		self.value = {'List': None, 'Selected': None}
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		EVT_COMBOBOX(self.parent, self.combobox.GetId(), self.onSelect)
		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.combobox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

	def onSelect(self, evt):
		value = evt.GetSelection()
		evt = SetServerEvent([self.name, 'Selected'], value)
		wxPostEvent(self.container.widgethandler, evt)

	def _enable(self, enable):
		if self.value['List'] or not enable:
			self.combobox.Enable(enable)
		wxContainerWidget._enable(self, enable)

	def setList(self, value):
		self.value['List'] = value
		self.combobox.Clear()
		if value:
			for i in value:
				self.combobox.Append(str(i))
			if self.enabled:
				self.combobox.Enable(True)
		else:
			self.combobox.Enable(False)

		self.combobox.SetSize(self.combobox.GetBestSize())
		width, height = self.combobox.GetSize()
		self.sizer.SetItemMinSize(self.combobox, width, height)
		self.layout()

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['List']:
			self.combobox.SetSelection(value)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['List']:
			self.setList(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.combobox.Destroy()

class wxOrderedListBoxWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.value = {'List': None, 'Selected': None}
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.orderedlistbox = wxOrderedListBox.wxOrderedListBox(self.parent, -1,
																														self.onSelect)
		self.sizer.Add(self.orderedlistbox, 0, wxALIGN_CENTER)
		self.sizer.Layout()
		self.layout()

	def onSelect(self, value):
		evt = SetServerEvent([self.name, 'Selected'], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setList(self, value):
		self.value['List'] = value
		self.orderedlistbox.setList(value)

	def setSelected(self, value):
		self.value['Selected'] = value
		self.orderedlistbox.setSelected(value)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['List']:
			self.setList(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.orderedlistbox.sizer.Layout()
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.orderedlistbox.Destroy()

class wxTreeSelectWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name,
																											None, self.onSelect)
		self.tree.Enable(false)
		self.sizer.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.value = {'Struct': {}, 'Selected': []}
		self.layout()

	def onSelect(self, value):
		evt = SetServerEvent([self.name, 'Selected'], [value])
		wxPostEvent(self.container.widgethandler, evt)

	def setStruct(self, value):
		self.value['Struct'] = value
		self.tree.set(value)
		if self.value['Selected'] is not None:
			self.tree.Enable(true)

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['Struct'] and self.value['Selected']:
			self.tree.select(value[0])
			self.tree.Enable(true)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Struct':
			self.setStruct(value)
		elif name == 'Selected':
			self.setSelected(value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['Struct']:
			self.setStruct(evt.value)
		if evt.namelist == ['Selected']:
			self.setSelected(evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.combobox.Destroy()

class wxClickImageWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.condition = threading.Condition()
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.label = wxStaticText(parent, -1, name)
		self.clickimage = wxImageViewer.ClickImagePanel(parent, -1, self.foo)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.clickimage, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def foo(self, coordinate):
		threading.Thread(target=self.clickCallback, args=(coordinate,)).start()

	def clickCallback(self, coordinate):
		self.condition.acquire()
		evt = SetServerEvent([self.name, 'Coordinates'], coordinate)
		wxPostEvent(self.container.widgethandler, evt)
		self.condition.wait()
		self.condition.release()
		evt = CommandServerEvent([self.name, 'Click'], ())
		wxPostEvent(self.container.widgethandler, evt)

	def setImage(self, value):
		if isinstance(value, arraytype):
			self.clickimage.setNumericImage(value, True)
		elif isinstance(value, extendedxmlrpclib.Binary):
			self.clickimage.setImageFromMrcString(value.data, True)
		else:
			self.clickimage.clearImage()
			return
		width, height = self.clickimage.GetSizeTuple()
		self.sizer.SetItemMinSize(self.clickimage, width, height)

	def _addWidget(self, name, typelist, value, configuration, children):
		# should disable until all available
		if name == 'Image':
			self.setImage(value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['Image']:
			self.setImage(evt.value)
		else:
			self.condition.acquire()
			self.condition.notify()
			self.condition.release()
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.clickimage.Destroy()

class wxTargetImageWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.label = wxStaticText(parent, -1, name)
		self.targetimage = wxImageViewer.TargetImagePanel(parent, -1,
																											self.targetCallback)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.targetimage, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def targetCallback(self, name, value):
		evt = SetServerEvent([self.name, name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setImage(self, value):
		if isinstance(value, arraytype):
			self.targetimage.setNumericImage(value, True)
		elif isinstance(value, extendedxmlrpclib.Binary):
			self.targetimage.setImageFromMrcString(value.data, True)
		else:
			self.targetimage.clearImage()
			return
		width, height = self.targetimage.GetSizeTuple()
		self.sizer.SetItemMinSize(self.targetimage, width, height)

	def setTargets(self, name, value):
		self.targetimage.setTargetTypeValue(name, value)

	def _addWidget(self, name, typelist, value, configuration, children):
		# should disable until all available
		if name == 'Image':
			self.setImage(value)
		else:
			self.setTargets(name, value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.namelist == ['Image']:
			self.setImage(evt.value)
		else:
			self.setTargets(evt.namelist[0], evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		self.label.Destroy()
		self.targetimage.Destroy()

class wxTreePanel(wxPanel):
	def __init__(self, parent):
		wxPanel.__init__(self, parent, -1)

		self.containers = {}

		self.sashwindow = wxSashLayoutWindow(self, -1, style=wxNO_BORDER)
		self.sashwindow.SetDefaultSize(wxSize(128, -1))
		self.sashwindow.SetOrientation(wxLAYOUT_VERTICAL)
		self.sashwindow.SetAlignment(wxLAYOUT_LEFT)
		self.sashwindow.SetSashVisible(wxSASH_RIGHT, True)
		self.sashwindow.SetExtraBorderSize(5)

		bitmaps = {}
		height = None
		width = None
		for type in wxMessageLog.types:
			bitmap = wxBitmapFromImage(wxImage('%s/%s.bmp' % 
																					(wxMessageLog.iconsdir, type)))
			if width is None:
				width = bitmap.GetWidth()
			elif width != bitmap.GetWidth():
				raise ValueError('Invalid tree bitmap width')
			if height is None:
				height = bitmap.GetHeight()
			elif height != bitmap.GetHeight():
				raise ValueError('Invalid tree bitmap height')
			bitmaps[type] = bitmap

		self.imagelist = wxImageList(width, height)
		self.bitmaps = {}
		self.bitmaps[None] = self.imagelist.AddWithColourMask(wxEmptyBitmap(width, height), wxBLACK)
		for type in bitmaps:
			self.bitmaps[type] = self.imagelist.Add(bitmaps[type])

		self.tree = wxTreeCtrl(self.sashwindow, -1,
														style=wxTR_HIDE_ROOT|wxTR_NO_BUTTONS)

		self.tree.AssignImageList(self.imagelist)
		self.root = self.tree.AddRoot('Containers')

		self.childpanel = wxScrolledWindow(self, -1, size=(512, 512),
																				style=wxSUNKEN_BORDER)
		self.childpanel.SetScrollRate(10, 10)
		self.childsizer = wxBoxSizer(wxVERTICAL)
		self.childpanel.SetSizer(self.childsizer)

		EVT_SIZE(self, self.OnSize)
		EVT_SASH_DRAGGED(self, self.sashwindow.GetId(), self.OnSashDrag)
		EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.OnTreeSelected)

	def OnSashDrag(self, evt):
		if evt.GetDragStatus() == wxSASH_STATUS_OUT_OF_RANGE:
			return

		self.sashwindow.SetDefaultSize(wxSize(evt.GetDragRect().width, -1))
		wxLayoutAlgorithm().LayoutWindow(self, self.childpanel)
		self.childpanel.Refresh()

	def OnSize(self, evt):
		wxLayoutAlgorithm().LayoutWindow(self, self.childpanel)

	def show(self, show):
		self.tree.Show(show)
		self.childpanel.Show(show)

	def addContainer(self, container):
		if isinstance(container.container, wxTreePanelContainerWidget):
			parentid = self.containers[container.container]
		else:
			parentid = self.root
		self.childsizer.Add(container.sizer, 1, wxEXPAND)
		id = self.tree.AppendItem(parentid, container.name)
		if parentid != self.root:
			self.tree.Expand(parentid)
		self.containers[container] = id
		self.tree.SetPyData(id, container)
		self.setImage(None, id)
		#self.tree.SelectItem(id)

	def setContainerImage(self, type, container):
		id = self.containers[container]
		self.setImage(type, id)

	def setImage(self, type, id):
		if not self.tree.ItemHasChildren(id):
			childid = self.tree.AppendItem(id, 'Refreshing...')
		else:
			childid = None
		self.tree.Expand(id)
		for state in [wxTreeItemIcon_Normal, wxTreeItemIcon_Selected,
									wxTreeItemIcon_Expanded, wxTreeItemIcon_SelectedExpanded]:
			self.tree.SetItemImage(id, self.bitmaps[type], state)
		if childid is not None:
			self.tree.Delete(childid)

	def deleteContainer(self, container):
		id = self.containers[container]
		self.tree.Delete(id)
		try:
			self.childsizer.Remove(container.sizer)
			del self.containers[container]
		except KeyError:
			pass

	def OnTreeSelected(self, evt):
		for container in self.containers:
			container.show(False)
		selectedcontainer = self.tree.GetPyData(self.tree.GetSelection())
		selectedcontainer.show(True)
		self.childsizer.Layout()
		self.childsizer.FitInside(self.childpanel)

class wxTreePanelContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.treepanel = container.getTreeContainer()
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.messages = {}
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.childparent = self.treepanel.childpanel
		self.treepanel.addContainer(self)

	def getTreeContainer(self):
		return self.treepanel

	def _show(self, show):
		wxContainerWidget._show(self, show)
		self.treepanel.childsizer.Show(self.sizer, show)

	def show(self, show):
		#self.treepanel.tree.SelectItem(self.treepanel.containers[self])
		wxContainerWidget.show(self, show)
		if not self._shown and isinstance(self.container,
																			wxTreePanelContainerWidget):
			self._show(self.shown)

	def _addWidget(self, namelist, typelist, value, configuration, children):
		wxContainerWidget._addWidget(self, namelist, typelist, value,
																	configuration, children)
		self.layout()

	def layout(self):
		wxContainerWidget.layout(self)
		self.treepanel.childsizer.FitInside(self.childparent)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.treepanel.deleteContainer(self)

	def updateMessages(self):
		for type in wxMessageLog.types:
			if type in self.messages:
				self.treepanel.setContainerImage(type, self)
				return
		self.treepanel.setContainerImage(None, self)

	def onAddMessage(self, evt):
		try:
			self.messages[evt.type] += 1
		except KeyError:
			self.messages[evt.type] = 1
			self.updateMessages()
		wxContainerWidget.onAddMessage(self, evt)

	def onRemoveMessage(self, evt):
		try:
			self.messages[evt.type] -= 1
			if self.messages[evt.type] == 0:
				del self.messages[evt.type]
				self.updateMessages()
		except KeyError:
			pass
		wxContainerWidget.onRemoveMessage(self, evt)

class wxFileDialogWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.cancelflag = False
		self.filenameflag = False
		self.labelname = None
		self.dialog = None
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _enable(self, enable):
		if self.dialog is not None:
			self.dialog.Enable(enable)
		wxContainerWidget._enable(self, enable)

	def _show(self, show):
		if self.dialog is not None:
			if self.dialog.ShowModal() == wxID_OK:
				setvalue = self.dialog.GetPath()
				commandnamelist = [self.name, self.labelname]
			else:
				setvalue = None
				commandnamelist = [self.name, 'Cancel']
			setevent = SetServerEvent([self.name, 'Filename'], setvalue, thread=False)
			wxPostEvent(self.container.widgethandler, setevent)
			commandevent = CommandServerEvent(commandnamelist, (), thread=False)
			wxPostEvent(self.container.widgethandler, commandevent)

		wxContainerWidget._show(self, show)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Cancel':
			self.cancelflag = True
		elif name == 'Filename':
			self.filenameflag = True
		else:
			self.labelname = name
		if self.cancelflag and self.filenameflag and self.labelname is not None:
			if self.labelname == 'Save':
				style = wxSAVE
			else:
				style = wxOPEN
			self.dialog = wxFileDialog(self.parent, self.name, style=style)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def dialogCallback(self):
		evt = CommandServerEvent([self.name, self.labelname], ())
		wxPostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		self.dialog.Destroy()

class wxMessageWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.messagewidget = None
		self.type = None
		self.message = None
		self.clearflag = False
		self.sizer = wxBoxSizer(wxVERTICAL)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def display(self):
		self.messagewidget = wxMessageLog.wxMessage(self.parent, self.type,
																							self.message, self.onClear)
		self.sizer.Add(self.messagewidget, 0, wxEXPAND)
		self.sizer.Layout()
		evt = AddMessageEvent(self.type, self.message)
		wxPostEvent(self.container.widgethandler, evt)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Type':
			self.type = value
		if name == 'Message':
			self.message = value
		elif name == 'Clear':
			self.clearflag = True
		if self.type is not None and self.message is not None and self.clearflag:
			self.display()

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def onClear(self, messagewidget):
		evt = CommandServerEvent([self.name, 'Clear'], ())
		wxPostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		if self.messagewidget is not None:
			self.messagewidget.Destroy()
		evt = RemoveMessageEvent(self.type, self.message)
		wxPostEvent(self.container.widgethandler, evt)

	def _show(self, show):
		if self.messagewidget is not None:
			self.messagewidget.Show(show)
		wxContainerWidget._show(self, show)

	#def _enable(self, enable):

class wxMessageLogWidget(wxContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.messages = {}
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.messagelog = wxMessageLog.wxMessageLog(parent)
		self.sizer.Add(self.messagelog, 0, wxEXPAND)
		wxContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _addWidget(self, name, typelist, value, configuration, children):
		for child in children:
			if child['namelist'][-1] == 'Type':
				type = child['value']
			elif child['namelist'][-1] == 'Message':
				message = child['value']
			elif child['namelist'][-1] == 'Clear':
				pass
		self.messages[name] = self.messagelog.addMessage(type, message,
																											self.onClear)
		evt = AddMessageEvent(type, message)
		wxPostEvent(self.container.widgethandler, evt)

	def onClear(self, messagewidget):
		for name, widget in self.messages.items():
			if widget == messagewidget:
				evt = CommandServerEvent([self.name, name, 'Clear'], ())
				wxPostEvent(self.container.widgethandler, evt)
				break

	def onSetWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		name = evt.namelist[0]
		wxPostEvent(self.container.widgethandler,
			RemoveMessageEvent(self.messages[name].type, self.messages[name].message))
		try:
			self.messagelog.removeMessage(self.messages[name])
			del self.messages[name]
			self.layout()
		except KeyError:
			pass
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.messagelog.Layout()

if __name__ == '__main__':
	import sys
	client = UIApp({'hostname': sys.argv[1], 'XML-RPC port': int(sys.argv[2])})

