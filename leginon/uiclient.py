#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import extendedxmlrpclib
import xmlrpc
import threading
import time
import sys
import wx
import wxImageViewer
import wxDictTree
import wxOrderedListBox
import wxMaster
import wxGridTray
import wxMessageLog
import wxList
from Numeric import arraytype

EVT_ADD_WIDGET = wx.NewEventType()
EVT_SET_WIDGET = wx.NewEventType()
EVT_REMOVE_WIDGET = wx.NewEventType()
EVT_CONFIGURE_WIDGET = wx.NewEventType()
EVT_SET_SERVER = wx.NewEventType()
EVT_COMMAND_SERVER = wx.NewEventType()
EVT_ADD_MESSAGE = wx.NewEventType()
EVT_REMOVE_MESSAGE = wx.NewEventType()

class AddWidgetEvent(wx.PyEvent):
	def __init__(self, dependencies, namelist, typelist, value,	
								configuration, event, children):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_ADD_WIDGET)
		self.namelist = namelist
		self.typelist = typelist
		self.value = value
		self.configuration = configuration
		self.dependencies = dependencies
		self.event = event
		self.children = children

class SetWidgetEvent(wx.PyEvent):
	def __init__(self, namelist, value, event):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_SET_WIDGET)
		self.namelist = namelist
		self.value = value
		self.event = event

class RemoveWidgetEvent(wx.PyEvent):
	def __init__(self, namelist, event, layout):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_REMOVE_WIDGET)
		self.namelist = namelist
		self.event = event
		self.layout = layout

class ConfigureWidgetEvent(wx.PyEvent):
	def __init__(self, namelist, configuration, event):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_CONFIGURE_WIDGET)
		self.namelist = namelist
		self.configuration = configuration
		self.event = event

class SetServerEvent(wx.PyEvent):
	def __init__(self, namelist, value, thread=True):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_SET_SERVER)
		self.namelist = namelist
		self.value = value
		self.thread = thread

class CommandServerEvent(wx.PyEvent):
	def __init__(self, namelist, args=(), thread=True):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_COMMAND_SERVER)
		self.namelist = namelist
		self.args = args
		self.thread = thread

class AddMessageEvent(wx.PyEvent):
	def __init__(self, type, message):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_ADD_MESSAGE)
		self.type = type
		self.message = message

class RemoveMessageEvent(wx.PyEvent):
	def __init__(self, type, message):
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_REMOVE_MESSAGE)
		self.type = type
		self.message = message

def WidgetClassFromTypeList(typelist):
	if typelist:
		if typelist[0] == 'object':
			if len(typelist) > 1:
				if typelist[1] == 'container':
					if len(typelist) > 2:
						if typelist[2] == 'select from list':
							if len(typelist) > 3:
								if typelist[3] == 'single':
									return ListSelectWidget
							return OrderedListBoxWidget
						elif typelist[2] == 'select from struct':
							return TreeSelectWidget
						elif typelist[2] == 'click image':
							return ClickImageWidget
						elif typelist[2] == 'target image':
							return TargetImageWidget
						elif typelist[2] == 'dialog':
							if len(typelist) > 3:
								if typelist[3] == 'message':
									return MessageDialogWidget
								elif typelist[3] == 'file':
									return FileDialogWidget
							return DialogContainerWidget
						elif typelist[2] == 'external':
							return DialogContainerWidget
						elif typelist[2] == 'medium':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return ClientContainerFactory(NotebookContainerWidget)
							return NotebookContainerWidget
						elif typelist[2] == 'large':
							if len(typelist) > 3:
								if typelist[3] == 'client':
									return ClientContainerFactory(TreePanelContainerWidget)
							return TreePanelContainerWidget
						elif typelist[2] == 'message':
							return MessageWidget
						elif typelist[2] == 'message log':
							return MessageLogWidget
						elif typelist[2] == 'history data':
							return HistoryEntryWidget
					return StaticBoxContainerWidget
				elif typelist[1] == 'method':
					return ButtonWidget
				elif typelist[1] == 'data':
					if len(typelist) > 2:
						if typelist[2] == 'integer':
							if len(typelist) > 3:
								if typelist[3] == 'progress':
									return ProgressWidget
							else:
								return entryWidgetClassFactory([int])
						elif typelist[2] == 'boolean':
							return CheckBoxWidget
						elif typelist[2] == 'float':
							return entryWidgetClassFactory([float])
						elif typelist[2] == 'number':
							return entryWidgetClassFactory([int, float])
						elif typelist[2] == 'password':
							return entryWidgetClassFactory([str], True)
						elif typelist[2] == 'struct':
							if len(typelist) > 3:
								if typelist[3] == 'application':
									return ApplicationWidget
							return TreeCtrlWidget
						elif typelist[2] == 'binary':
							if len(typelist) > 3:
								if typelist[3] == 'image':
									return ImageWidget
								elif typelist[3] == 'PIL image':
									return PILImageWidget
						elif typelist[2] == 'array':
							if len(typelist) > 3:
								if typelist[3] == 'sequence':
									return ListWidget
								elif typelist[3] == 'grid tray':
									return GridTrayWidget
							return entryWidgetClassFactory([list, tuple])
					return EntryWidget
	raise ValueError('invalid type for widget')
	
class LocalUIClient(object):
	def __init__(self, uiserver):
		self.uiserver = uiserver

	def addServer(self):
		self.uiserver.addLocalClient(self)

	def setServer(self, namelist, value, thread=False):
		if thread:
			threading.Thread(name='local UI client set server thread',
												target=self.uiserver.setFromClient,
												args=(namelist, value)).start()
		else:
			self.uiserver.setFromClient(namelist, value)

	def commandServer(self, namelist, args, thread=False):
		if thread:
			threading.Thread(name='local UI client command server thread',
												target=self.uiserver.commandFromClient,
												args=(namelist, args)).start()
		else:
			self.uiserver.commandFromClient(namelist, args)

class XMLRPCUIClient(xmlrpc.Client, xmlrpc.Server):
	def __init__(self, serverhostname, serverport, port=None):
		xmlrpc.Client.__init__(self, serverhostname, serverport, port)
		xmlrpc.Server.__init__(self, port)
		self.xmlrpcserver.register_function(self.addFromServer, 'add')
		self.xmlrpcserver.register_function(self.setFromServer, 'set')
		self.xmlrpcserver.register_function(self.removeFromServer, 'remove')
		self.xmlrpcserver.register_function(self.configureFromServer, 'configure')

	def addServer(self):
		self.execute('add client', (self.hostname, self.port))

	def setServer(self, namelist, value, thread=False):
		if thread:
			threading.Thread(name='XML-RPC UI client set server thread',
												target=self.execute,
												args=('set', (namelist, value))).start()
		else:
			self.execute('set', (namelist, value))

	def commandServer(self, namelist, args, thread=False):
		if thread:
			threading.Thread(name='XML-RPC UI client command server thread',
												target=self.execute,
												args=('command', (namelist, args))).start()
		else:
			self.execute('command', (namelist, args))

class UIClient(object):
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
		wx.PostEvent(self.container.widgethandler, evt)
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
		wx.PostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

	def removeFromServer(self, properties):
		namelist = properties['namelist']
		threadingevent = None
		if 'block' in properties and properties['block']:
			if not isinstance(threading.currentThread(), threading._MainThread):
				threadingevent = threading.Event()
		evt = RemoveWidgetEvent(namelist, threadingevent, True)
		wx.PostEvent(self.container.widgethandler, evt)
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
		wx.PostEvent(self.container.widgethandler, evt)
		if threadingevent is not None:
			threadingevent.wait()
		return ''

class LocalClient(LocalUIClient, UIClient):
	def __init__(self, server, container):
		LocalUIClient.__init__(self, server)
		UIClient.__init__(self, container)
		self.addServer()

class XMLRPCClient(XMLRPCUIClient, UIClient):
	def __init__(self, serverhostname, serverport, container, port=None):
		XMLRPCUIClient.__init__(self, serverhostname, serverport, port)
		UIClient.__init__(self, container)
		threading.Thread(name='XML-RPC UI client add server thread',
											target=self.addServer, args=()).start()

class UIStatusBar(wx.StatusBar):
	def __init__(self, parent):
		wx.StatusBar.__init__(self, parent, -1)
		self.SetFieldsCount(1)
		self.gauge = wx.Gauge(self, -1, 100)
		wx.EVT_SIZE(self, self.OnSize)
		self.update()

	def OnSize(self, evt):
		self.update()

	def update(self):
		r = self.GetFieldRect(0)
		self.gauge.SetPosition(wx.Point(r.x + 3*r.width/4 - 2, r.y+2))
		self.gauge.SetSize(wx.Size(r.width/4, r.height-4))

class UIApp(wx.App):
	def __init__(self, location, title='UI', containername='UI Client'):
		self.location = location
		self.title = title
		self.containername = containername
		self._shown = True
		self._enabled = True
		wx.App.__init__(self, 0)
		self.MainLoop()

	def OnInit(self):
		self.frame = wx.Frame(None, -1, self.title, size=(740, 740))
#		self.statusbar = UIStatusBar(self.frame)
#		self.frame.SetStatusBar(self.statusbar)
		self.panel = wx.ScrolledWindow(self.frame, -1)
		self.panel.SetScrollRate(1, 1)		
		containerclass = ClientContainerFactory(SimpleContainerWidget)
		self.container = containerclass(self.containername, self.panel, self,
																		self.location, {})
		if isinstance(self.container, wx.Sizer):
			self.panel.SetSizer(self.container)
		self.SetTopWindow(self.frame)
		self.panel.Show(True)
		self.panel.Fit()
		self.frame.Show(True)
		return True

	def layout(self):
		self.panel.Refresh()

class Widget(object):
	def __init__(self, name, parent, container, value, configuration):
		self.name = name
		self.parent = parent
		self.container = container
		self.widgethandler = wx.EvtHandler()
		if 'enabled' not in configuration:
			configuration['enabled'] = True
		if 'shown' not in configuration:
			configuration['shown'] = True
		self._configure(configuration)

		self.widgethandler.Connect(-1, -1, EVT_CONFIGURE_WIDGET,
																self.onConfigureWidget)

	def _configure(self, configuration):
		if 'enabled' in configuration:
			self.enable(configuration['enabled'])
		if 'shown' in configuration:
			self.show(configuration['shown'])
		if 'tool tip' in configuration and hasattr(self, 'SetToolTip'):
			self.SetToolTip(wx.ToolTip(configuration['tool tip']))

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
#		if self.container is not None:
#			self.container._showWidget(self, show)

	def show(self, show):
		self.shown = show
		if self.container is not None and not self.container._shown:
			self._show(False)
		else:
			self._show(self.shown)

	def setServer(self, value):
		evt = SetServerEvent([self.name], value)
		wx.PostEvent(self.container.widgethandler, evt)

	def commandServer(self, args=()):
		evt = CommandServerEvent([self.name], args)
		wx.PostEvent(self.container.widgethandler, evt)

class ContainerWidget(Widget):
	def __init__(self, name, parent, container, value, configuration):
		self.children = {}
		self.pending = []
		self.notebook = None
		self.treecontainer = None

		self.nosizerclasses = (NotebookContainerWidget, DialogContainerWidget,
														TreePanelContainerWidget, MessageDialogWidget,
														FileDialogWidget)
		self.expandclasses = (MessageWidget, MessageLogWidget)
		Widget.__init__(self, name, parent, container, value, configuration)
		self.childparent = self.parent

		self.widgethandler.Connect(-1, -1, EVT_ADD_WIDGET, self.onAddWidget)
		self.widgethandler.Connect(-1, -1, EVT_SET_WIDGET, self.onSetWidget)
		self.widgethandler.Connect(-1, -1, EVT_REMOVE_WIDGET, self.onRemoveWidget)
		self.widgethandler.Connect(-1, -1, EVT_SET_SERVER, self.onSetServer)
		self.widgethandler.Connect(-1, -1, EVT_COMMAND_SERVER,
																self.onCommandServer)
		self.widgethandler.Connect(-1, -1, EVT_ADD_MESSAGE, self.onAddMessage)
		self.widgethandler.Connect(-1, -1, EVT_REMOVE_MESSAGE,
																self.onRemoveMessage)

	def childEvent(self, evt):
		for name, child in self.children.items():
			if name == evt.namelist[0]:
				evt.namelist = evt.namelist[1:]
				wx.PostEvent(child.widgethandler, evt)
				return
		self.pending.append(evt)
		#raise ValueError('No such child to enable widget')

	def _enable(self, enable):
		Widget._enable(self, enable)
		for child in self.children.values():
			child.enable(child.enabled)

	def _show(self, show):
		Widget._show(self, show)
		self.showNotebook(show)
		self.showTreeContainer(show)
		for child in self.children.values():
			child.show(child.shown)

	def onConfigureWidget(self, evt):
		if len(evt.namelist) == 0:
			Widget.onConfigureWidget(self, evt)
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
			wx.PostEvent(self.widgethandler, evt)

	def _addWidgetSizer(self, child, show=True):
		if self.sizer is not None and not isinstance(child, self.nosizerclasses):
			if isinstance(child, self.expandclasses):
				self.sizer.Add(child, 0, wx.ALL|wx.EXPAND, 3)
			else:
				self.sizer.Add(child, 0, wx.ALL, 3)

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

	def _removeWidget(self, name, widget, layout):
		del self.children[name]
		widget.destroy()
		if self.sizer is not None and not isinstance(widget, self.nosizerclasses):
			self.sizer.Remove(widget)
		if layout:
			self.layout()

	def removeChildren(self):
		for name, child in self.children.items():
			self._removeWidget(name, child, False)

	def onRemoveWidget(self, evt):
		if len(evt.namelist) == 1:
			for name, child in self.children.items():
				if name == evt.namelist[0]:
					self._removeWidget(name, child, evt.layout)
					if evt.event is not None:
						evt.event.set()
			#raise ValueError('No such child to remove widget')
		else:
			self.childEvent(evt)

	def onSetServer(self, evt):
		evt.namelist.insert(0, self.name)
		wx.PostEvent(self.container.widgethandler, evt)

	def onCommandServer(self, evt):
		evt.namelist.insert(0, self.name)
		wx.PostEvent(self.container.widgethandler, evt)

	def onAddMessage(self, evt):
		wx.PostEvent(self.container.widgethandler, evt)

	def onRemoveMessage(self, evt):
		wx.PostEvent(self.container.widgethandler, evt)

	def showNotebook(self, show):
		if self.notebook is not None:
			self.notebook.Show(show)

	def getNotebook(self):
		if self.notebook is None:
			self.notebook = wx.Notebook(self.childparent, -1)
			self.notebooksizer = wx.NotebookSizer(self.notebook)
			if self.sizer is not None:
				self.sizer.Add(self.notebooksizer, 0,
												wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
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
			self.treecontainer = TreePanel(self.childparent)
			if self.sizer is not None:
				self.sizer.Add(self.treecontainer, 1,
												wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
			self.layout()
		return self.treecontainer

	def showTreeContainer(self, show):
		if self.treecontainer is not None:	
			self.treecontainer.show(show)

	def layout(self):
		if self.sizer is not None:
			self.sizer.Layout()
		if isinstance(self.childparent, wx.ScrolledWindow):
			self.childparent.FitInside()
		else:
			self.childparent.Fit()
		self.container.layout()

	def destroy(self):
		self.removeChildren()
		self.removeNotebook()

class SimpleContainerWidget(wx.BoxSizer, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.sizer = self
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def destroy(self):
		ContainerWidget.destroy(self)

	def _addWidget(self, name, typelist, value, configuration, children):
		ContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

class StaticBoxContainerWidget(wx.StaticBoxSizer, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.staticbox = wx.StaticBox(parent, -1, name)
		wx.StaticBoxSizer.__init__(self, self.staticbox, wx.VERTICAL)
		self.sizer = self
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _show(self, show):
		self.staticbox.Show(show)
		ContainerWidget._show(self, show)

	def destroy(self):
		self.staticbox.Destroy()
		ContainerWidget.destroy(self)

	def _addWidget(self, name, typelist, value, configuration, children):
		ContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

class NotebookContainerWidget(wx.Panel, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.parentnotebook = container.getNotebook()
		wx.Panel.__init__(self, self.parentnotebook, -1)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self)
		self.Show(True)
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)
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
		ContainerWidget._addWidget(self, name, typelist, value,
																	configuration, children)
		self.layout()

	def destroy(self):
		ContainerWidget.destroy(self)
		self.parentnotebook.DeletePage(self.getPageNumber())

	def getPageNumber(self):
		for i in range(self.parentnotebook.GetPageCount()):
			if self.parentnotebook.GetPage(i) == self.panel:
				return i

# this had/has a self.sizer, but now is subclass of wx.Dialog
class DialogContainerWidget(wx.Dialog, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.Dialog.__init__(self, parent, -1, name,
							style=wx.CAPTION|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
		self.panel = wx.ScrolledWindow(self, -1)
		self.panel.SetScrollRate(1, 1)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.panel.SetSizer(self.sizer)
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)
		self.childparent = self.panel
		self.layout()

	def _show(self, show):
		self.panel.Show(show)
		self.CenterOnParent()
		self.Show(show)
		ContainerWidget._show(self, show)

	def destroy(self):
		self.Destroy()
		ContainerWidget.destroy(self)

	def layout(self):
		self.sizer.Layout()
		self.sizer.Fit(self.panel)
		self.Fit()

class ClientContainerWidget(object):
	pass

def ClientContainerFactory(wxcontainerwidget):
	class ClientContainer(ClientContainerWidget, wxcontainerwidget):
		def __init__(self, name, parent, container, value, configuration):
			wxcontainerwidget.__init__(self, name, parent, container, value,
																	configuration)
			if 'instance' in value and value['instance'] is not None:
				clientclass = LocalClient
				args = (value['instance'],)
			elif 'hostname' in value and value['hostname'] is not None \
						and 'XML-RPC port' in value and value['XML-RPC port'] is not None:
				clientclass = XMLRPCClient
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

	return ClientContainer

class MethodWidget(Widget):
	def __init__(self, name, parent, container, value, configuration):
		Widget.__init__(self, name, parent, container, value, configuration)

	def commandFromWidget(self, evt=None):
		Widget.commandServer(self)

	def layout(self):
		self.container.layout()

	def destroy(self):
		pass

class ButtonWidget(wx.Button, MethodWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.Button.__init__(self, parent, -1, name)
		MethodWidget.__init__(self, name, parent, container, value, configuration)
		wx.EVT_BUTTON(self.parent, self.GetId(), self.commandFromWidget)
		self.layout()

	def _enable(self, enable):
		self.Enable(enable)
		MethodWidget._enable(self, enable)

	def _show(self, show):
		self.Show(show)
		MethodWidget._show(self, show)

class DataWidget(Widget):
	def __init__(self, name, parent, container, value, configuration):
		if 'read' in configuration and configuration['read']:
			self.read = True
		else:
			self.read = False

		if 'write' in configuration and configuration['write']:
			self.write = True
		else:
			self.write = False

		Widget.__init__(self, name, parent, container, value, configuration)
		self.widgethandler.Connect(-1, -1, EVT_SET_WIDGET, self.onSetWidget)

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
		self.container.layout()

	def destroy(self):
		pass

class ProgressWidget(wx.BoxSizer, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.BoxSizer.__init__(self, wx.HORIZONTAL)
		DataWidget.__init__(self, name, parent, container, value, configuration)
		self.label = wx.StaticText(self.parent, -1, self.name)
		self.gauge = wx.Gauge(self.parent, -1, 100, style=wx.GA_HORIZONTAL)
		size = self.gauge.GetSizeTuple()
		self.gauge.SetSize((size[0]*4, size[1]))

		self.set(value)

		self.Add(self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.Add(self.gauge, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.layout()

	def layout(self):
		self.Layout()
		DataWidget.layout(self)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.gauge.Enable(enable)
		DataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.gauge.Show(show)
		DataWidget._show(self, show)

	def setWidget(self, value):
		self.gauge.SetValue(value)

	def destroy(self):
		self.label.Destroy()
		self.gauge.Destroy()

class GridTrayWidget(wxGridTray.GridTrayPanel, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wxGridTray.GridTrayPanel.__init__(self, parent, self.setServer)
		DataWidget.__init__(self, name, parent, container, value, configuration)
		self.set(value)

	def setWidget(self, value):
		self.setQueue(value)

class EntryWidget(wx.BoxSizer, DataWidget):
	types = [str]
	password = False
	def __init__(self, name, parent, container, value, configuration):
		self.dirty = False
		self.error = False
		wx.BoxSizer.__init__(self, wx.HORIZONTAL)
		self.label = wx.StaticText(parent, -1, name + ':')

		if 'write' in configuration and configuration['write']:
			if str in self.types:
				size = (150, -1)
			else:
				size = (-1, -1)
			style=wx.TE_PROCESS_ENTER
			if self.password:
				style |= wx.TE_PASSWORD
			self.entry = wx.TextCtrl(parent, -1, size=size, style=style)
		else:
			self.entry = wx.StaticText(parent, -1, '')

		DataWidget.__init__(self, name, parent, container, value, configuration)

		if self.write:
			image = wx.BitmapFromImage(wx.Image('%s/%s.bmp'
																					% (wxMessageLog.iconsdir, 'error')))
			self.errorbitmap = wx.StaticBitmap(parent, -1, image,
																					(image.GetWidth(), image.GetHeight()))
																						
			wx.EVT_KILL_FOCUS(self.entry, self.onKillFocus)
			wx.EVT_TEXT_ENTER(self.entry, self.entry.GetId(), self.onEnter)
			wx.EVT_CHAR(self.entry, self.onChar)

		self.Add(self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.Add(self.entry, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		if self.write:
			self.Add(self.errorbitmap, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
			self.Show(self.errorbitmap, False)
		self.set(value)
		self.layout()

#	def SetToolTip(self, tooltip):
#		self.label.SetToolTip(tooltip)
#		self.entry.SetToolTip(tooltip)

	def setDirty(self, dirty):
		if self.dirty != dirty:
			if self.error:
				self.setError(False)
			self.dirty = dirty

	def setError(self, error):
		if self.error != error:
			self.Show(self.errorbitmap, error)
			self.Layout()
			self.error = error

	def onChar(self, evt):
		self.setDirty(True)
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.setWidget(self.value)
		evt.Skip()

	def onKillFocus(self, evt):
		if self.dirty:
			self.setFromWidget()
		evt.Skip()

	def destroy(self):
		self.entry.Destroy()
		self.label.Destroy()
		if self.write:
			self.errorbitmap.Destroy()

	def onEnter(self, evt):
		self.setFromWidget(evt)

	def setFromWidget(self, evt=None):
		value = self.entry.GetValue()
		if self.types != [str]:
			try:
				value = eval(value)
			except:
				if str not in self.types:
					self.setError(True)
					return
		if type(value) not in self.types:
			self.setError(True)
			return
		self.setDirty(False)
		self.value = value
		self.setServer(self.value)

	def setWidget(self, value):
		if isinstance(self.entry, wx.StaticText):
			if value is None:
				self.entry.SetLabel('')
			else:
				self.entry.SetLabel(str(self.value))
			entrysize = self.entry.GetSize()
			self.SetItemMinSize(self.entry, entrysize.GetWidth(),
																			entrysize.GetHeight())
			minwidth, minheight = self.GetMinSize()
			width, height = self.GetSize()
			set = False
			if minwidth > width:
				width = minwidth
				set = True
			if minheight > height:
				height = minheight
				set = True
			if set:
				self.SetMinSize((width, height))
				self.layout()
		else:
			if value is None:
				self.entry.SetValue('')
			else:
				self.entry.SetValue(str(self.value))
			self.setDirty(False)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.entry.Enable(enable)
		DataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.entry.Show(show)
		if self.error:
			self.errorbitmap.Show(show)
		DataWidget._show(self, show)

def entryWidgetClassFactory(itypes, ispassword=False):
	class EntryWidgetClass(EntryWidget):
		types = itypes
		password = ispassword
	return EntryWidgetClass

class CheckBoxWidget(wx.CheckBox, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.CheckBox.__init__(self, parent, -1, name)
		DataWidget.__init__(self, name, parent, container, value, configuration)
		self.set(value)
		wx.EVT_CHECKBOX(self.parent, self.GetId(), self.setFromWidget)

	def _enable(self, enable):
		if self.write:
			self.Enable(enable)
		else:
			self.Enable(False)
		DataWidget._enable(self, enable)

	def _show(self, show):
		self.Show(show)
		DataWidget._show(self, show)

	def setFromWidget(self, evt):
		value = self.GetValue()
		if value:
			self.value = 1
		else:
			self.value = 0
		self.setServer(self.value)

	def setWidget(self, value):
		self.SetValue(self.value)

class TreeCtrlWidget(wxDictTree.DictTreeCtrlPanel, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		if 'write' in configuration and configuration['write']:
			wxDictTree.DictTreeCtrlPanel.__init__(self, parent, -1, name,
																						self.setFromWidget)
		else:
			wxDictTree.DictTreeCtrlPanel.__init__(self, parent, -1, name)
		DataWidget.__init__(self, name, parent, container, value, configuration)

		self.set(value)

	def _enable(self, enable):
		DataWidget._enable(self, enable)

	def _show(self, show):
		DataWidget._show(self, show)

	def setFromWidget(self):
		self.setServer(self.value)

	def setWidget(self, value):
		self._set(self.value)

class ApplicationWidget(wx.BoxSizer, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.applicationeditor = wxMaster.ApplicationEditorCanvas(parent, -1)
		self.applybutton = wx.Button(parent, -1, 'Apply')
		DataWidget.__init__(self, name, parent, container, value, configuration)

		wx.EVT_BUTTON(self.applybutton, self.applybutton.GetId(), self.apply)
		self.Add(self.applicationeditor, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		self.Add(self.applybutton, 0, wx.ALIGN_CENTER | wx.ALL, 5)
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

class ImageMixIn(object):
	def setImage(self, value):
		if isinstance(value, arraytype):
			self.image.setNumericImage(value)
		elif isinstance(value, extendedxmlrpclib.Binary):
			self.image.setImageFromMrcString(value.data)
		else:
			self.image.clearImage()
			return
		width, height = self.image.GetSizeTuple()
		self.SetItemMinSize(self.image, width, height)

class ImageWidget(wx.BoxSizer, DataWidget, ImageMixIn):
	def __init__(self, name, parent, container, value, configuration):
		ImageMixIn.__init__(self)
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.label = wx.StaticText(parent, -1, name)
		self.image = wxImageViewer.ImagePanel(parent, -1)
		DataWidget.__init__(self, name, parent, container, value, configuration)
		self.set(value)
		self.Add(self.label, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		self.Add(self.image, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		self.layout()

	def setValue(self, value):
		# no...more...pie
		pass

	def setWidget(self, value):
		ImageMixIn.setImage(self, value)

	def destroy(self):
		self.label.Destroy()
		self.image.Destroy()

class PILImageWidget(ImageWidget):
	def setWidget(self, value):
		if value.data:
			self.image.setImageFromPILString(value.data)
			width, height = self.image.GetSizeTuple()
			self.SetItemMinSize(self.image, width, height)
		else:
			self.image.clearImage()

class MessageDialog(wx.Dialog):
	def __init__(self, parent, id, title, callback):
		wx.Dialog.__init__(self, parent, id, title)
		self.callback = callback
		panel = wx.Panel(self, -1)
		panel.SetAutoLayout(True)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(self.sizer)
		self.message = wx.StaticText(panel, -1, '')
		self.sizer.Add(self.message, 0, wx.ALIGN_CENTER | wx.ALL, 10)
		self.okbutton = wx.Button(panel, -1, 'OK')
		wx.EVT_BUTTON(self, self.okbutton.GetId(), self.OnOK)
		self.sizer.Add(self.okbutton, 0, wx.ALIGN_CENTER | wx.ALL, 10)
		self.sizer.Layout()
		self.sizer.Fit(self)
		wx.EVT_CLOSE(self, self.OnClose)

	def OnOK(self, evt):
		self.callback()

	def OnClose(self, evt):
		self.callback()

class DefinedContainerWidget(ContainerWidget):
	def setServer(self, name, value, thread=True):
		evt = SetServerEvent([self.name, name], value, thread)
		wx.PostEvent(self.container.widgethandler, evt)

	def commandServer(self, name, args=(), thread=True):
		evt = CommandServerEvent([self.name, name], args, thread)
		wx.PostEvent(self.container.widgethandler, evt)

	def setFromMapping(self, name, value):
		if name in self.namemapping:
			mapname = name
		elif None in self.namemapping:
			mapname = None
		else:
			raise RuntimeError('Unhandled set widget, %s not in mapping' % name)
		if self.namemapping[mapname] is None:
			return
		elif callable(self.namemapping[mapname]):
			if mapname is None:
				self.namemapping[mapname](name, value)
			else:
				self.namemapping[mapname](value)
		else:
			raise RuntimeError('%s maps to uncallable and non-None value' % name)

	def _addWidget(self, name, typelist, value, configuration, children):
		self.setFromMapping(name, value)

	def onAddWidget(self, evt):
		self._addWidget(evt.namelist[0], None, evt.value, None, None)
		if evt.event is not None:
			evt.event.set()

	def onSetWidget(self, evt):
		self.setFromMapping(evt.namelist[-1], evt.value)
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.container.layout()

class MessageDialogWidget(MessageDialog, DefinedContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		MessageDialog.__init__(parent, -1, name, self.onDialogOK)
		self.namemapping = {'Message': self.setMessage,
												'OK': None}
		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)

	def setMessage(self, value):
		self.message.SetLabel(value)

	def _show(show):
		self.Show(show)
		DefinedContainerWidget._show(self, show)

	def onDialogOK(self):
		self.commandServer('OK')

	def layout(self):
		width, height = self.message.GetSizeTuple()
		self.sizer.SetItemMinSize(self.message, width, height)
		self.sizer.Layout()
		self.sizer.Fit(self)

class ListWidget(wx.BoxSizer, DataWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.label = wx.StaticText(parent, -1, name)
		if 'write' in configuration and configuration['write']:
			self.list = wxList.wxListEdit(parent, self.onSetFromWidget)
		else:
			self.list = wxList.wxListView(parent)
		self.Add(self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.Add(self.list, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		DataWidget.__init__(self, name, parent, container, value, configuration)
		self.set(value)

#	def SetToolTip(self, tooltip):
#		self.list.SetToolTip(tooltip)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.list.Enable(enable)
		DataWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.list.Show(show)
		DataWidget._show(self, show)

	def setFromWidget(self):
		self.setServer(self.value)

	def onSetFromWidget(self, values):
		self.value = values
		self.setFromWidget()

	def setWidget(self, value):
		self.list.setValues(value)

	def destroy(self):
		self.label.Destroy()
		#self.list.Destroy()

class ListSelectWidget(wx.BoxSizer, DefinedContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		wx.BoxSizer.__init__(self, wx.HORIZONTAL)
		self.label = wx.StaticText(parent, -1, name + ':')
		self.listselect = wxList.wxListViewSelect(parent, self.onSelect)
		self.value = {'List': None, 'Selected': None}
		self.namemapping = {'List': self.setList,
												'Selected': self.setSelected}
		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)
		self.Add(self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.Add(self.listselect, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.layout()

#	def SetToolTip(self, tooltip):
#		self.label.SetToolTip(tooltip)
#		self.listselect.SetToolTip(tooltip)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.listselect.Enable(enable)
		ContainerWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.listselect.Show(show)
		ContainerWidget._show(self, show)

	def layout(self):
		self.Layout()
		DefinedContainerWidget.layout(self)

	def destroy(self):
		self.label.Destroy()
		self.listselect.Destroy()

	def onSelect(self, value):
		self.setServer('Selected', value)

	def setList(self, value):
		self.value['List'] = value
		self.listselect.setValues(value)
		self.listselect.SetSize(self.listselect.GetBestSize())
		width, height = self.listselect.GetSize()
		self.SetItemMinSize(self.listselect, width, height)
		self.layout()

	def setSelected(self, value):
		self.value['Selected'] = value
		self.listselect.select(value)

class OrderedListBoxWidget(wxOrderedListBox.wxOrderedListBox,
														DefinedContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.value = {'List': None, 'Selected': None}
		self.namemapping = {'List': self.setList,
												'Selected': self.setSelected}
		wxOrderedListBox.wxOrderedListBox.__init__(self, parent, -1, self.onSelect)
		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)
		self.layout()

	def onSelect(self, value):
		self.setServer('Selected', value)

	def setList(self, value):
		self.value['List'] = value
		self._setList(value)

	def setSelected(self, value):
		self.value['Selected'] = value
		self._setSelected(value)

	def layout(self):
		self.Layout()
		DefinedContainerWidget.layout(self)

class TreeSelectWidget(wxDictTree.DictTreeCtrlPanel, DefinedContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.value = {'Struct': {}, 'Selected': []}
		self.namemapping = {'Struct': self.setStruct(value),
												'Selected': self.setSelected(value)}
		wxDictTree.DictTreeCtrlPanel.__init__(self, parent, -1, name, None,
																						self.onSelect)
		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)
		self.layout()

	def _enable(self, enable):
		self.Enable(enable)
		ContainerWidget._enable(self, enable)

	def _show(self, show):
		self.Show(show)
		ContainerWidget._show(self, enable)

	def onSelect(self, value):
		self.setServer('Selected', [value])

	def setStruct(self, value):
		self.value['Struct'] = value
		self._set(value)
		if self.value['Selected'] is not None:
			self.Enable(True)

	def setSelected(self, value):
		self.value['Selected'] = value
		if self.value['Struct'] and self.value['Selected']:
			self.select(value[0])
			self.Enable(True)

class ClickImageWidget(wx.BoxSizer, DefinedContainerWidget, ImageMixIn):
	def __init__(self, name, parent, container, value, configuration):
		ImageMixIn.__init__(self)
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.label = wx.StaticText(parent, -1, name)
		self.image = wxImageViewer.ClickImagePanel(parent, -1, self.onClick)
		self.namemapping = {'Image': self.setImage,
												'Coordinates': None,
												'Click': None}

		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)

		self.Add(self.label, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		self.Add(self.image, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		self.layout()

	def onClick(self, coordinate):
		self.setServer('Coordinates', coordinate, False)
		self.commandServer('Click')

	def layout(self):
		self.Layout()
		DefinedContainerWidget.layout(self)

	def destroy(self):
		self.label.Destroy()
		self.image.Destroy()

class TargetImageWidget(wx.BoxSizer, DefinedContainerWidget, ImageMixIn):
	def __init__(self, name, parent, container, value, configuration):
		self.targetcolors = {}
		ImageMixIn.__init__(self)
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		self.label = wx.StaticText(parent, -1, name)
		self.image = wxImageViewer.TargetImagePanel(parent, -1, self.onTarget)
		self.namemapping = {'Image': self.setImage,
												None: self.setTarget}
		DefinedContainerWidget.__init__(self, name, parent, container, value,
																		configuration)
		self.Add(self.label, 0, wx.ALIGN_LEFT | wx.ALL, 5)
		self.Add(self.image, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		self.layout()

	def onTarget(self, name, value):
		self.setServer(name, value)

	def setTargets(self, name, value):
		color = self.targetcolors[name]
		self.image.setTargetTypeValue(name, value, color)

	def setTargetColor(self, name, value):
		try:
			self.targetcolors[name] = tuple(value)
		except:
			self.targetcolors[name] = None

	def setTarget(self, name, value):
		if name[:5] == 'color':
			self.setTargetColor(name[5:], value)
		else:
			self.setTargets(name, value)

	def layout(self):
		self.Layout()
		DefinedContainerWidget.layout(self)

	def destroy(self):
		self.label.Destroy()
		self.image.Destroy()

class BitmapTreeCtrl(wx.TreeCtrl):
	def __init__(self, parent, style):
		wx.TreeCtrl.__init__(self, parent, -1, style=style)
		self.bitmaps = {}
		wx.EVT_PAINT(self, self.OnPaint)

	def setItemBitmap(self, id, bitmap):
		for b in self.bitmaps:
			if id in self.bitmaps[b]:
				self.bitmaps[b].remove(id)
				width = b.GetWidth()
				height = b.GetHeight()
		if bitmap is not None:
			try:
				self.bitmaps[bitmap].append(id)
			except KeyError:
				self.bitmaps[bitmap] = [id]
			self.drawBitmaps(wx.ClientDC(self))
		else:
			if self.IsVisible(id):
				rect = self.GetBoundingRect(id, True)
				dc = wx.ClientDC(self)
				dc.BeginDrawing()
				dc.SetPen(wx.Pen(self.GetBackgroundColour()))
				dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
				dc.DrawRectangle((rect[0] + rect[2], rect[1]), (width, height))
				dc.EndDrawing()

	def OnPaint(self, evt):
		dc = wx.PaintDC(self)
		try:
			wx.TreeCtrl.OnPaint(self, evt)
		except AttributeError:
			pass
		self.drawBitmaps(dc)
		evt.Skip()

	def drawBitmaps(self, dc):
		dc.BeginDrawing()
		for bitmap in self.bitmaps:
			for id in self.bitmaps[bitmap]:
				if self.IsVisible(id):
					rect = self.GetBoundingRect(id, True)
					dc.DrawBitmap(bitmap, (rect[0] + rect[2], rect[1]))
		dc.EndDrawing()

class TreePanel(wx.Panel):
	def __init__(self, parent):
		self.bitmaps = {}
		for type in wxMessageLog.types:
			self.bitmaps[type] = wx.BitmapFromImage(wx.Image('%s/%s.bmp' %
																								(wxMessageLog.iconsdir, type)))
			self.bitmapsize = (self.bitmaps[type].GetWidth(),
													self.bitmaps[type].GetHeight())

		wx.Panel.__init__(self, parent, -1)

		self.containers = {}

		self.sashwindow = wx.SashLayoutWindow(self, -1, style=wx.NO_BORDER)
		self.sashwindow.SetDefaultSize(wx.Size(128, -1))
		self.sashwindow.SetOrientation(wx.LAYOUT_VERTICAL)
		self.sashwindow.SetAlignment(wx.LAYOUT_LEFT)
		self.sashwindow.SetSashVisible(wx.SASH_RIGHT, True)
		self.sashwindow.SetExtraBorderSize(5)

		self.tree = BitmapTreeCtrl(self.sashwindow,
																	wx.TR_HIDE_ROOT)#|wx.TR_NO_BUTTONS)

		self.root = self.tree.AddRoot('Containers')

		self.childpanel = wx.ScrolledWindow(self, -1, size=(512, 512),
																				style=wx.SUNKEN_BORDER)
		self.childpanel.SetScrollRate(10, 10)
		self.childsizer = wx.BoxSizer(wx.VERTICAL)
		self.childpanel.SetSizer(self.childsizer)

		wx.EVT_SIZE(self, self.OnSize)
		wx.EVT_SASH_DRAGGED(self, self.sashwindow.GetId(), self.OnSashDrag)
		wx.EVT_TREE_SEL_CHANGED(self.tree, self.tree.GetId(), self.OnTreeSelected)

	def updateMessage(self, container, type):
		try:
			image = self.bitmaps[type]
		except KeyError:
			image = None
		try:
			self.tree.setItemBitmap(self.containers[container], image)
		except KeyError:
			pass

	def OnSashDrag(self, evt):
		if evt.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
			return

		self.sashwindow.SetDefaultSize(wx.Size(evt.GetDragRect().width, -1))
		wx.LayoutAlgorithm().LayoutWindow(self, self.childpanel)
		self.childpanel.Refresh()

	def OnSize(self, evt):
		wx.LayoutAlgorithm().LayoutWindow(self, self.childpanel)

	def show(self, show):
		self.tree.Show(show)
		self.childpanel.Show(show)

	def addContainer(self, container):
		if isinstance(container.container, TreePanelContainerWidget):
			parentid = self.containers[container.container]
		else:
			parentid = self.root
		self.childsizer.Add(container, 1, wx.EXPAND)
		id = self.tree.AppendItem(parentid, container.name)
		if parentid != self.root:
			self.tree.Expand(parentid)
		self.containers[container] = id
		self.tree.SetPyData(id, container)
		container.show(False)
		#self.tree.SelectItem(id)

	def deleteContainer(self, container):
		id = self.containers[container]
		self.tree.Delete(id)
		self.childsizer.Remove(container)
		del self.containers[container]

	def OnTreeSelected(self, evt):
		for container in self.containers:
			container.show(False)
		selectedcontainer = self.tree.GetPyData(self.tree.GetSelection())
		if selectedcontainer is not None:
			selectedcontainer.show(True)
			selectedcontainer.layout()

class TreePanelContainerWidget(wx.Panel, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.treepanel = container.getTreeContainer()
		wx.Panel.__init__(self, self.treepanel.childpanel, -1)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(self.sizer)
		self.message = None
		self.messages = {}
		ContainerWidget.__init__(self, name, self, container, value,
																configuration)
		self.treepanel.addContainer(self)

	def getTreeContainer(self):
		return self.treepanel

	def _show(self, show):
		ContainerWidget._show(self, show)
		self.Show(show)
		self.treepanel.childsizer.Show(self, show)

	def show(self, show):
		#self.treepanel.tree.SelectItem(self.treepanel.containers[self])
		ContainerWidget.show(self, show)
		if not self._shown and isinstance(self.container,
																			TreePanelContainerWidget):
			self._show(self.shown)

	def _addWidget(self, namelist, typelist, value, configuration, children):
		ContainerWidget._addWidget(self, namelist, typelist, value,
																	configuration, children)
		self.layout()

	def layout(self):
		#ContainerWidget.layout(self)
		self.sizer.Layout()
		self.Fit()
		if self._shown:
			self.treepanel.childsizer.SetMinSize(self.GetSize())
			self.treepanel.childpanel.FitInside()

	def destroy(self):
		ContainerWidget.destroy(self)
		self.treepanel.deleteContainer(self)

	def updateMessage(self):
		messagetype = None
		for type in wxMessageLog.types:
			if type in self.messages:
				messagetype = type
		self.treepanel.updateMessage(self, messagetype)

	def onAddMessage(self, evt):
		try:
			self.messages[evt.type] += 1
		except KeyError:
			self.messages[evt.type] = 1
			self.updateMessage()
		ContainerWidget.onAddMessage(self, evt)

	def onRemoveMessage(self, evt):
		try:
			self.messages[evt.type] -= 1
			if self.messages[evt.type] == 0:
				del self.messages[evt.type]
				self.updateMessage()
		except KeyError:
			pass
		ContainerWidget.onRemoveMessage(self, evt)

class FileDialogWidget(ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.cancelflag = False
		self.filenameflag = False
		self.labelname = None
		self.dialog = None
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _enable(self, enable):
		if self.dialog is not None:
			self.dialog.Enable(enable)
		ContainerWidget._enable(self, enable)

	def _show(self, show):
		if self.dialog is not None:
			if self.dialog.ShowModal() == wx.ID_OK:
				setvalue = self.dialog.GetPath()
				commandnamelist = [self.name, self.labelname]
			else:
				setvalue = None
				commandnamelist = [self.name, 'Cancel']
			setevent = SetServerEvent([self.name, 'Filename'], setvalue, thread=False)
			wx.PostEvent(self.container.widgethandler, setevent)
			commandevent = CommandServerEvent(commandnamelist, (), thread=False)
			wx.PostEvent(self.container.widgethandler, commandevent)

		ContainerWidget._show(self, show)

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Cancel':
			self.cancelflag = True
		elif name == 'Filename':
			self.filenameflag = True
		else:
			self.labelname = name
		if self.cancelflag and self.filenameflag and self.labelname is not None:
			if self.labelname == 'Save':
				style = wx.SAVE
			else:
				style = wx.OPEN
			self.dialog = wx.FileDialog(self.parent, self.name, style=style)

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
		wx.PostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		self.dialog.Destroy()

class MessageWidget(wx.BoxSizer, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.messagewidget = None
		self.type = None
		self.message = None
		self.clearflag = False
		wx.BoxSizer.__init__(self, wx.VERTICAL)
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def display(self):
		self.messagewidget = wxMessageLog.wxMessage(self.parent, self.type,
																							self.message, self.onClear)
		self.Add(self.messagewidget, 0, wx.EXPAND)
		self.Layout()
		evt = AddMessageEvent(self.type, self.message)
		wx.PostEvent(self.container.widgethandler, evt)

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
		wx.PostEvent(self.container.widgethandler, evt)

	def layout(self):
		pass

	def destroy(self):
		if self.messagewidget is not None:
			self.messagewidget.Destroy()
		evt = RemoveMessageEvent(self.type, self.message)
		wx.PostEvent(self.container.widgethandler, evt)

	def _show(self, show):
		if self.messagewidget is not None:
			self.messagewidget.Show(show)
		ContainerWidget._show(self, show)

	#def _enable(self, enable):

class MessageLogWidget(wxMessageLog.wxMessageLog, ContainerWidget):
	def __init__(self, name, parent, container, value, configuration):
		self.messages = {}
		wxMessageLog.wxMessageLog.__init__(self, parent)
		ContainerWidget.__init__(self, name, parent, container, value,
																configuration)

	def _addWidget(self, name, typelist, value, configuration, children):
		for child in children:
			if child['namelist'][-1] == 'Type':
				type = child['value']
			elif child['namelist'][-1] == 'Message':
				message = child['value']
			elif child['namelist'][-1] == 'Clear':
				pass
		self.messages[name] = self.addMessage(type, message, self.onClear)
		self.layout()
		evt = AddMessageEvent(type, message)
		wx.PostEvent(self.container.widgethandler, evt)

	def onClear(self, messagewidget):
		for name, widget in self.messages.items():
			if widget == messagewidget:
				evt = CommandServerEvent([self.name, name, 'Clear'], ())
				wx.PostEvent(self.container.widgethandler, evt)
				break

	def onSetWidget(self, evt):
		if evt.event is not None:
			evt.event.set()

	def onRemoveWidget(self, evt):
		name = evt.namelist[0]
		wx.PostEvent(self.container.widgethandler,
			RemoveMessageEvent(self.messages[name].type, self.messages[name].message))
		try:
			self.removeMessage(self.messages[name])
			del self.messages[name]
			self.layout()
		except KeyError:
			pass
		if evt.event is not None:
			evt.event.set()

	def layout(self):
		self.Layout()
		self.container.layout()

	def _show(self, show):
		self.Show(show)
		ContainerWidget._show(self, show)

class HistoryEntryWidget(wx.BoxSizer, DefinedContainerWidget):
	typemap = {'integer': [int], 'float': [float],
							'number': [int, float], 'string': [str]}
	types = [str]
	def __init__(self, name, parent, container, value, configuration):
		self.dirty = False
		wx.BoxSizer.__init__(self, wx.HORIZONTAL)
		self.label = wx.StaticText(parent, -1, name + ':')
		self.combobox = wx.ComboBox(parent, -1, style=wx.CB_DROPDOWN)

		self.namemapping = {'Value': self.setValue,
												'History': self.setHistory}

		DefinedContainerWidget.__init__(self, name, parent, container, value,
																configuration)

		wx.EVT_KILL_FOCUS(self.combobox, self.onKillFocus)
		wx.EVT_TEXT_ENTER(self.combobox, self.combobox.GetId(), self.onEnter)
		wx.EVT_COMBOBOX(self.combobox, self.combobox.GetId(), self.onComboBox)
		wx.EVT_CHAR(self.combobox, self.onChar)

		self.Add(self.label, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.Add(self.combobox, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 3)
		self.layout()

	def setDirty(self, dirty):
		self.dirty = dirty

	def onChar(self, evt):
		self.setDirty(True)
		if evt.GetKeyCode() == wx.WXK_ESCAPE:
			self.setWidget(self.value)
		evt.Skip()

	def onKillFocus(self, evt):
		if self.dirty:
			self.setFromWidget()
		evt.Skip()

	def _addWidget(self, name, typelist, value, configuration, children):
		if name == 'Value':
			try:
				self.types = self.typemap[typelist[-1]]
			except KeyError:
				pass
		DefinedContainerWidget._addWidget(self, name, typelist, value,
																			configuration, children)

	def destroy(self):
		self.combobox.Destroy()
		self.label.Destroy()

	def onEnter(self, evt):
		self.setFromWidget(evt)

	def onComboBox(self, evt):
		self.setFromWidget(evt)

	def setFromWidget(self, evt=None):
		if evt is None:
			value = self.combobox.GetValue()
		else:
			value = evt.GetString()
		if self.types != [str]:
			try:
				value = eval(value)
			except:
				if str not in self.types:
					return
		if type(value) not in self.types:
			return
		self.setDirty(False)
		evt = SetServerEvent([self.name, 'Value'], value)
		wx.PostEvent(self.container.widgethandler, evt)

	def setValue(self, value):
		if value is None:
			self.combobox.SetValue('')
		else:
			self.combobox.SetValue(str(value))
		self.setDirty(False)

	def setHistory(self, history):
		value = self.combobox.GetValue()
		if history is None:
			self.combobox.Clear()
		else:
			self.combobox.Clear()
			for item in history:
				self.combobox.Append(str(item))
		self.combobox.SetValue(value)

	def _enable(self, enable):
		self.label.Enable(enable)
		self.combobox.Enable(enable)
		ContainerWidget._enable(self, enable)

	def _show(self, show):
		self.label.Show(show)
		self.combobox.Show(show)
		ContainerWidget._show(self, show)

	def layout(self):
		self.Layout()
		DefinedContainerWidget.layout(self)

if __name__ == '__main__':
	import sys
	client = UIApp({'hostname': sys.argv[1], 'XML-RPC port': int(sys.argv[2])})

