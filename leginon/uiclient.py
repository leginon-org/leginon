#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import xmlrpclib
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
from Numeric import arraytype

wxEVT_ADD_WIDGET = wxNewEventType()
wxEVT_SET_WIDGET = wxNewEventType()
wxEVT_REMOVE_WIDGET = wxNewEventType()
wxEVT_CONFIGURE_WIDGET = wxNewEventType()
wxEVT_SET_SERVER = wxNewEventType()
wxEVT_COMMAND_SERVER = wxNewEventType()

class AddWidgetEvent(wxPyEvent):
	def __init__(self, dependencies, namelist, typelist, value,	
								configuration, event):
		wxPyEvent.__init__(self)
		self.SetEventType(wxEVT_ADD_WIDGET)
		self.namelist = namelist
		self.typelist = typelist
		self.value = value
		self.configuration = configuration
		self.dependencies = dependencies
		self.event = event

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
						elif typelist[2] == 'message dialog':
							return wxMessageDialogWidget
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
		self.proxy = xmlrpclib.ServerProxy(uri, allow_none=1)

	def execute(self, function_name, args=()):
		try:
			return getattr(self.proxy, function_name)(*args)
		except xmlrpclib.ProtocolError:
			# usually return value not correct type
			raise
		except xmlrpclib.Fault:
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

		#UIClient.__init__(self, serverhostname, serverport, port)
		#threading.Thread(target=self.addServer, args=()).start()

	def addFromServer(self, properties):
		dependencies = properties['dependencies']
		namelist = properties['namelist']
		typelist = properties['typelist']
		try:
			value = properties['value']
		except KeyError:
			value = ''
		configuration = properties['configuration']

		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()

		evt = AddWidgetEvent(dependencies, namelist, typelist, value,	
													configuration, threadingevent)
		wxPostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

	def setFromServer(self, properties):
		namelist = properties['namelist']
		#namelist = list(namelist)
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

class UIApp(wxApp):
	def __init__(self, clientclass, clientclassargs, title='UI',
								containername='UI Client'):
		self.clientclass = clientclass
		self.clientclassargs = clientclassargs
		self.title = title
		self.containername = containername
		wxApp.__init__(self, 0)
		self.MainLoop()

	def OnInit(self):
		self.frame = wxFrame(NULL, -1, self.title)
		self.panel = wxScrolledWindow(self.frame, -1, size=(600, 700))
		self.panel.SetScrollRate(1, 1)		
		containerclass = wxClientContainerFactory(wxSimpleContainerWidget)
		self.container = containerclass(self.containername, self.panel, self,
																		self.clientclass, self.clientclassargs)
		if self.container.sizer is not None:
			self.panel.SetSizer(self.container.sizer)
		self.SetTopWindow(self.frame)
		self.panel.Show(true)
		self.panel.Fit()
		#self.frame.Fit()
		self.frame.Show(true)
		return true

	def layout(self):
		self.panel.Refresh()

class wxWidget(object):
	def __init__(self, name, parent, container):
		self.name = name
		self.parent = parent
		self.container = container
		self.widgethandler = wxEvtHandler()
		self.sizer = None
		self.shown = True

		self.widgethandler.Connect(-1, -1, wxEVT_CONFIGURE_WIDGET,
																self.onConfigureWidget)

	def onConfigureWidget(self, evt):
		if 'enabled' in evt.configuration:
			self.enable(evt.configuration['enabled'])
		if evt.event is not None:
			evt.event.set()

	def enable(self, enabled):
		pass

	def show(self, show):
		self.shown = show

	def getParent(self):
		return self.parent

	def getName(self):
		return self.name

	def getContainer(self):
		return self.container

	def setServer(self, value):
		evt = SetServerEvent([self.name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def commandServer(self, args=()):
		evt = CommandServerEvent([self.name], args)
		wxPostEvent(self.container.widgethandler, evt)

class wxContainerWidget(wxWidget):
	def __init__(self, name, parent, container):
		wxWidget.__init__(self, name, parent, container)
		self.children = {}
		self.childparent = self.parent
		self.pending = []

		self.notebook = None
		self.treecontainer = None

		self.widgethandler.Connect(-1, -1, wxEVT_ADD_WIDGET, self.onAddWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_REMOVE_WIDGET, self.onRemoveWidget)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_SERVER, self.onSetServer)
		self.widgethandler.Connect(-1, -1, wxEVT_COMMAND_SERVER,
																self.onCommandServer)

	def show(self, show):
		wxWidget.show(self, show)
		if self.notebook is not None:
			self.notebook.Show(show)
		if self.treecontainer is not None:	
			self.treecontainer.show(show)
		for child in self.children.values():
			if self.sizer is not None:
				if isinstance(child, wxNotebookContainerWidget):
					childsizer = None
				elif isinstance(child, wxDialogContainerWidget):
					childsizer = None
				elif isinstance(child, wxTreePanelContainerWidget):
					childsizer = None
				else:
					childsizer = child.sizer
				if childsizer is not None:
					self.sizer.Show(childsizer, show)
			child.show(show)

	def _addWidget(self, name, typelist, value, configuration):
		childclass = WidgetClassFromTypeList(typelist)
		if issubclass(childclass, wxClientContainerWidget):
			if isinstance(value, uiserver.Server):
				clientclass = wxLocalClient
				value = (value,)
			else:
				clientclass = wxXMLRPCClient
			child = childclass(name, self.childparent, self, clientclass, value)
		elif issubclass(childclass, wxDataWidget):
			child = childclass(name, self.childparent, self, value, configuration)
		else:
			child = childclass(name, self.childparent, self)
		self.children[name] = child
		if isinstance(child, wxNotebookContainerWidget):
			childsizer = None
		elif isinstance(child, wxDialogContainerWidget):
			childsizer = None
		elif isinstance(child, wxTreePanelContainerWidget):
			childsizer = None
		else:
			childsizer = child.sizer
		if self.sizer is not None and childsizer is not None:
			self.sizer.Add(childsizer, 0, wxALL, 3)
			self.sizer.Show(childsizer, self.shown)
		child.show(self.shown)

#		if isinstance(child, wxClientContainerWidget):
#			child.uiclient.start()

		# hmm...
		for evt in list(self.pending):
			self.pending.remove(evt)
			wxPostEvent(self.widgethandler, evt)

	def getPendingCount(self):
		pendingcount = 0
		for i in self.children.values():
			if hasattr(i, 'getPendingCount'):
				pendingcount += i.getPendingCount()
		pendingcount += len(self.pending)
		return pendingcount

	def _addWidgetToChild(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wxPostEvent(child.widgethandler, evt)
				return
		self.pending.append(evt)

	def onAddWidget(self, evt):
		if len(evt.namelist) == 1:
			for name in self.children:
				for i in evt.dependencies:
					if i == name:
						evt.dependencies.remove(i)
			if evt.dependencies:
				self.pending.append(evt)
			else:
				childname = evt.namelist[0]
				self._addWidget(childname, evt.typelist, evt.value, evt.configuration)
				if evt.event is not None:
					evt.event.set()
		else:
			self._addWidgetToChild(evt)

	def onSetWidget(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wxPostEvent(child.widgethandler, evt)
				return
		self.pending.append(evt)
		#raise ValueError('No such child to set widget')

	def onRemoveWidget(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				if len(evt.namelist) == 1:
					del self.children[name]
					child.destroy()
					if isinstance(child, wxNotebookContainerWidget):
						childsizer = None
					elif isinstance(child, wxDialogContainerWidget):
						childsizer = None
					elif isinstance(child, wxTreePanelContainerWidget):
						childsizer = None
					else:
						childsizer = child.sizer
					if self.sizer is not None and childsizer is not None:
						self.sizer.Remove(childsizer)
					if evt.event is not None:
						evt.event.set()
					return
				else:
					evt.namelist = evt.namelist[1:]
					wxPostEvent(child.widgethandler, evt)
					return
		self.pending.append(evt)
		#raise ValueError('No such child to remove widget')

	def onConfigureWidget(self, evt):
		if len(evt.namelist) == 0:
			self.configuration(evt.configuration)
			if evt.event is not None:
				evt.event.set()
		else:
			for name, child in self.children.items():
				if name == evt.namelist[0]:
					evt.namelist = evt.namelist[1:]
					wxPostEvent(child.widgethandler, evt)
					return
			self.pending.append(evt)
			#raise ValueError('No such child to enable widget')

	def configuration(self, configuration):
		if 'enabled' in configuration:
			wxWidget.enable(self, configuration['enabled'])
		for name, child in self.children.items():
			evt = ConfigureWidgetEvent([], configuration)
			wxPostEvent(child.widgethandler, evt)

	def onSetServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def onCommandServer(self, evt):
		evt.namelist.insert(0, self.name)
		wxPostEvent(self.container.widgethandler, evt)

	def getNotebook(self):
		if self.notebook is None:
			self.notebook = wxNotebook(self.childparent, -1)#, style=wxCLIP_CHILDREN)
			self.notebooksizer = wxNotebookSizer(self.notebook)
			if self.sizer is not None:
				self.sizer.Add(self.notebooksizer, 0,
												wxEXPAND|wxALIGN_CENTER_HORIZONTAL|wxALL, 5)
			self.layout()
		return self.notebook

	def getTreePanel(self):
		if self.treecontainer is None:
			self.treecontainer = wxTreePanel(self.childparent)
			if self.sizer is not None:
				self.sizer.Add(self.treecontainer, 1,
												wxEXPAND|wxALIGN_CENTER_HORIZONTAL|wxALL, 5)
			self.layout()
		return self.treecontainer

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		if isinstance(self.childparent, wxScrolledWindow):
			self.childparent.FitInside()
		else:
			self.childparent.Fit()
		self.container.layout()

	def destroy(self):
		for name, child in self.children.items():
			del self.children[name]
			child.destroy()
			if isinstance(child, wxNotebookContainerWidget):
				childsizer = None
			elif isinstance(child, wxDialogContainerWidget):
				childsizer = None
			elif isinstance(child, wxTreePanelContainerWidget):
				childsizer = None
			else:
				childsizer = self.sizer
			if self.sizer is not None and childsizer is not None:
				self.sizer.Remove(childsizer)
		if self.notebook is not None:
			self.notebook.Destroy()
			self.notebook = None
			self.sizer.Remove(self.notebooksizer)
			self.notebooksizer = None

class wxSimpleContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxVERTICAL)

	def destroy(self):
		wxContainerWidget.destroy(self)

	def _addWidget(self, namelist, typelist, value, configuration):
		wxContainerWidget._addWidget(self, namelist, typelist, value, configuration)
		self.layout()

class wxStaticBoxContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.staticbox = wxStaticBox(self.parent, -1, self.name)
		self.sizer = wxStaticBoxSizer(self.staticbox, wxVERTICAL)

	def show(self, show):
		self.staticbox.Show(show)
		wxContainerWidget.show(self, show)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.staticbox.Destroy()

	def _addWidget(self, namelist, typelist, value, configuration):
		wxContainerWidget._addWidget(self, namelist, typelist, value, configuration)
		self.layout()

class wxNotebookContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
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

	def _addWidget(self, namelist, typelist, value, configuration):
		wxContainerWidget._addWidget(self, namelist, typelist, value, configuration)
		self.layout()

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.parentnotebook.DeletePage(self.getPageNumber())

	def getPageNumber(self):
		for i in range(self.parentnotebook.GetPageCount()):
			if self.parentnotebook.GetPage(i) == self.panel:
				return i

class wxDialogContainerWidget(wxContainerWidget):
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.dialog = wxDialog(self.parent, -1, name,
														style=wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX
																	|wxRESIZE_BORDER)
		self.panel = wxScrolledWindow(self.dialog, -1)
		self.panel.SetScrollRate(1, 1)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.panel.SetSizer(self.sizer)
		self.childparent = self.panel
		self.panel.Show(true)
		self.dialog.Show(true)

	def show(self, show):
		self.panel.Show(show)
		self.dialog.Show(show)
		wxContainerWidget.show(self, show)
		self.layout()

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
		def __init__(self, name, parent, container, clientclass, clientclassargs):
			wxcontainerwidget.__init__(self, name, parent, container)
			self.uiclient = apply(clientclass, clientclassargs + (self,))

		def onSetServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.setServer(evt.namelist, evt.value, evt.thread)

		def onCommandServer(self, evt):
			evt.namelist.insert(0, self.name)
			self.uiclient.commandServer(evt.namelist, evt.args, evt.thread)

	return wxClientContainer

class wxMethodWidget(wxWidget):
	def __init__(self, name, parent, container):
		wxWidget.__init__(self, name, parent, container)

	def commandFromWidget(self, evt=None):
		wxWidget.commandServer(self)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		self.container.layout()

	def destroy(self):
		pass

class wxButtonWidget(wxMethodWidget):
	def __init__(self, name, parent, container):
		wxMethodWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.button = wxButton(self.parent, -1, self.name)
		EVT_BUTTON(self.parent, self.button.GetId(), self.commandFromWidget)
		self.sizer.Add(self.button, 0, wxALIGN_CENTER | wxALL, 0)
		self.layout()

	def enable(self, enabled):
		self.button.Enable(enabled)

class wxDataWidget(wxWidget):
	def __init__(self, name, parent, container, value, configuration):
		try:
			if configuration['read']:
				self.read = True
			else:
				self.read = False
		except KeyError:
			self.read = False

		try:
			if configuration['write']:
				self.write = True
			else:
				self.write = False
		except KeyError:
			self.write = False

		wxWidget.__init__(self, name, parent, container)
		self.widgethandler.Connect(-1, -1, wxEVT_SET_WIDGET, self.onSetWidget)

	def onSetWidget(self, evt):
		self.set(evt.value)
		if evt.event is not None:
			evt.event.set()

	def setWidget(self, value):
		pass

	def setValue(self, value):
		if isinstance(value, xmlrpclib.Binary):
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
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		if self.write:
			self.applybutton = wxButton(self.parent, -1, 'Apply')
			self.applybutton.Enable(false)
			EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.setFromWidget)
			self.entry = wxTextCtrl(self.parent, -1, style=wxTE_PROCESS_ENTER)
			EVT_TEXT(self.entry, self.entry.GetId(), self.onEdit)
			EVT_TEXT_ENTER(self.entry, self.entry.GetId(), self.onEnter)
		else:
			self.entry = wxStaticText(self.parent, -1, '')

		self.set(value)

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
			self.entry.SetValue(str(self.value))
		if hasattr(self, 'applybutton'):
			self.dirty = False
			self.applybutton.Enable(false)

	def enable(self, enabled):
		self.label.Enable(enabled)
		self.entry.Enable(enabled)
		if hasattr(self, 'applybutton'):
			if enabled and self.dirty:
				self.applybutton.Enable(True)
			else:
				self.applybutton.Enable(False)

def entryWidgetClass(itypes):
	class EWC(wxEntryWidget):
		types = itypes
	return EWC

class wxCheckBoxWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.checkbox = wxCheckBox(self.parent, -1, self.name)
		if not self.write:
			self.checkbox.Enable(false)
		else:
			EVT_CHECKBOX(self.parent, self.checkbox.GetId(), self.setFromWidget)

		self.set(value)

		self.sizer.Add(self.checkbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

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
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.listbox = wxListBox(self.parent, -1)

		EVT_LISTBOX(self.listbox, self.listbox.GetId(), self.OnListBox)

		self.set(value)

		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.listbox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.layout()

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
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		if self.write:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1,
																								self.name, self.setFromWidget)
		else:
			self.tree = wxDictTree.DictTreeCtrlPanel(self.parent, -1, self.name)

		self.set(value)

		self.sizer.Add(self.tree, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def setFromWidget(self):
		self.setServer(self.value)

	def setWidget(self, value):
		self.tree.set(self.value)

	def destroy(self):
		self.tree.Destroy()

class wxApplicationWidget(wxDataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxVERTICAL)
		# maybe have callback
		self.applicationeditor = wxMaster.ApplicationEditorCanvas(self.parent, -1)

		self.sizer.Add(self.applicationeditor, 0, wxALIGN_CENTER | wxALL, 5)
		self.applybutton = wxButton(self.parent, -1, 'Apply')
		EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.apply)
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
		wxDataWidget.__init__(self, name, parent, container, value, configuration)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.imageviewer = wxImageViewer.ImagePanel(self.parent, -1)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.set(value)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.imageviewer, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def setValue(self, value):
		# not keeping track of image for now
		pass

	def setWidget(self, value):
		if isinstance(value, xmlrpclib.Binary):
			if value.data:
				self.imageviewer.setImageFromMrcString(value.data)
				width, height = self.imageviewer.GetSizeTuple()
				self.sizer.SetItemMinSize(self.imageviewer, width, height)
			else:
				self.imageviewer.clearImage()
		else:
			if isinstance(value, arraytype):
				self.imageviewer.setNumericImage(value)
				width, height = self.imageviewer.GetSizeTuple()
				self.sizer.SetItemMinSize(self.imageviewer, width, height)
			else:
				self.imageviewer.clearImage()

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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
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

	def onAddWidget(self, evt):
		name = evt.namelist[0]
		value = evt.value
		if name == 'Message':
			self.setMessage(value)
			self.messageflag = True
		elif name == 'OK':
			self.okflag = True
		if self.messageflag and self.okflag:
			self.display()
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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.combobox = wxComboBox(self.parent, -1,
																style=wxCB_DROPDOWN | wxCB_READONLY)
		self.combobox.Enable(false)
		EVT_COMBOBOX(self.parent, self.combobox.GetId(), self.onSelect)
		self.label = wxStaticText(self.parent, -1, self.name + ':')
		self.sizer.Add(self.label, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.sizer.Add(self.combobox, 0, wxALIGN_CENTER | wxLEFT | wxRIGHT, 3)
		self.value = {'List': None, 'Selected': None}
		self.layout()

	def onSelect(self, evt):
		value = evt.GetSelection()
		evt = SetServerEvent([self.name, 'Selected'], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setList(self, value):
		self.value['List'] = value
		self.combobox.Clear()
		if value:
			for i in value:
				self.combobox.Append(str(i))
			self.combobox.Enable(true)
		else:
			self.combobox.Enable(false)

		self.combobox.SetSize(self.combobox.GetBestSize())
		width, height = self.combobox.GetSize()
		self.sizer.SetItemMinSize(self.combobox, width, height)
		self.layout()

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['List']:
			self.combobox.SetSelection(value)

	def onAddWidget(self, evt):
		name = evt.namelist[0]
		value = evt.value
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)
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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxHORIZONTAL)
		self.orderedlistbox = wxOrderedListBox.wxOrderedListBox(self.parent, -1,
																														self.onSelect)
		self.sizer.Add(self.orderedlistbox, 0, wxALIGN_CENTER)
		self.sizer.Layout()
		self.value = {'List': None, 'Selected': None}
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

	def onAddWidget(self, evt):
		name = evt.namelist[0]
		value = evt.value
		if name == 'List':
			self.setList(value)
		elif name == 'Selected':
			self.setSelected(value)
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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
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

	def onAddWidget(self, evt):
		name = evt.namelist[0]
		value = evt.value
		if name == 'Struct':
			self.setStruct(value)
		elif name == 'Selected':
			self.setSelected(value)
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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.condition = threading.Condition()
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.clickimage = wxImageViewer.ClickImagePanel(self.parent, -1,
																											self.foo)
		self.label = wxStaticText(self.parent, -1, self.name)
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
		if value:
			self.clickimage.setImageFromMrcString(value.data, True)
			width, height = self.clickimage.GetSizeTuple()
			self.sizer.SetItemMinSize(self.clickimage, width, height)
		else:
			self.clickimage.clearImage()

	def onAddWidget(self, evt):
		# should disable until all available
		name = evt.namelist[0]
		value = evt.value
		if name == 'Image':
			self.setImage(value)
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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.targetimage = wxImageViewer.TargetImagePanel(self.parent, -1,
																											self.targetCallback)
		self.label = wxStaticText(self.parent, -1, self.name)
		self.sizer.Add(self.label, 0, wxALIGN_LEFT | wxALL, 5)
		self.sizer.Add(self.targetimage, 0, wxALIGN_CENTER | wxALL, 5)
		self.layout()

	def targetCallback(self, name, value):
		evt = SetServerEvent([self.name, name], value)
		wxPostEvent(self.container.widgethandler, evt)

	def setImage(self, value):
		if value:
			self.targetimage.setImageFromMrcString(value.data, True)
			width, height = self.targetimage.GetSizeTuple()
			self.sizer.SetItemMinSize(self.targetimage, width, height)
		else:
			self.targetimage.clearImage()

	def setTargets(self, name, value):
		self.targetimage.setTargetTypeValue(name, value)

	def onAddWidget(self, evt):
		# should disable until all available
		name = evt.namelist[0]
		value = evt.value
		if name == 'Image':
			self.setImage(value)
		else:
			self.setTargets(name, value)
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

		self.tree = wxTreeCtrl(self.sashwindow, -1,
														style=wxTR_HIDE_ROOT|wxTR_NO_BUTTONS)
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
		parentcontainer = container.getContainer()
		if isinstance(parentcontainer, wxTreePanelContainerWidget):
			parentid = self.containers[parentcontainer]
		else:
			parentid = self.root
		containername = container.getName()
		if containername is None:
			raise ValueError('no name for container to add to Tree Container')
		self.childsizer.Add(container.sizer, 0) #, wxEXPAND)
		id = self.tree.AppendItem(parentid, containername)
		if parentid != self.root:
			self.tree.Expand(parentid)
		self.containers[container] = id
		self.tree.SetPyData(id, container)
		self.tree.SelectItem(id)

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
	def __init__(self, name, parent, container):
		wxContainerWidget.__init__(self, name, parent, container)
		self.treepanel = self.container.getTreePanel()
		self.childparent = self.treepanel.childpanel
		self.sizer = wxBoxSizer(wxVERTICAL)
		self.treepanel.addContainer(self)

	def getTreePanel(self):
		return self.treepanel

	def show(self, show):
		self.treepanel.childsizer.Show(self.sizer, show)
		wxContainerWidget.show(self, show)

	def _addWidget(self, name, typelist, value, configuration):
		wxContainerWidget._addWidget(self, name, typelist, value, configuration)
		self.layout()

	def layout(self):
		wxContainerWidget.layout(self)
		self.treepanel.childsizer.FitInside(self.childparent)

	def destroy(self):
		wxContainerWidget.destroy(self)
		self.treepanel.deleteContainer(self)

if __name__ == '__main__':
	import sys
	client = UIApp(sys.argv[1], int(sys.argv[2]))

