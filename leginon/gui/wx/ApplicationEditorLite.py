# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ApplicationEditorLite.py,v $
# $Revision: 1.6 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-23 19:30:28 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import leginon.noderegistry

class ApplicationMenu(wx.Menu):
	def __init__(self, editor):
		self.editor = editor
		wx.Menu.__init__(self)
		self.addlauncherid = wx.NewId()
		self.Bind(wx.EVT_MENU, self.onAddLauncher, id=self.addlauncherid)
		self.Append(self.addlauncherid, 'Add Launcher')

	def onAddLauncher(self, evt):
		item = self.editor.addLauncher()
		self.editor.EnsureVisible(item)
		self.editor.EditLabel(item)

class LauncherMenu(wx.Menu):
	def __init__(self, editor, name):
		self.editor = editor
		self.name = name
		wx.Menu.__init__(self)
		self.addnodeid = wx.NewId()
		self.removeid = wx.NewId()
		self.Bind(wx.EVT_MENU, self.onAddNode, id=self.addnodeid)
		self.Bind(wx.EVT_MENU, self.onRemove, id=self.removeid)
		self.Append(self.addnodeid, 'Add Node...')
		self.Append(self.removeid, 'Remove')

	def onAddNode(self, evt):
		item = self.editor.addNode(None, None, self.name, [])
		self.editor.EnsureVisible(item)
		name = self.editor.GetItemText(item)
		dialog = NodePropertiesDialog(self.editor, name)
		if dialog.ShowModal() == wx.ID_OK:
			classname, newname = dialog.getValues()
			self.editor.setNode(name, classname, newname)
			self.editor.SetItemText(item, newname)
		else:
			item = self.editor.removeNode(name)
		dialog.Destroy()

	def onRemove(self, evt):
		self.editor.removeLauncher(self.name)

class NodeMenu(wx.Menu):
	def __init__(self, editor, name):
		self.editor = editor
		self.name = name
		wx.Menu.__init__(self)
		self.propertiesid = wx.NewId()
		self.bindeventid = wx.NewId()
		self.removeid = wx.NewId()
		self.Bind(wx.EVT_MENU, self.onProperties, id=self.propertiesid)
		self.Bind(wx.EVT_MENU, self.onBindEvent, id=self.bindeventid)
		self.Bind(wx.EVT_MENU, self.onRemove, id=self.removeid)
		self.Append(self.propertiesid, 'Properties...')
		self.Append(self.bindeventid, 'Bind Event...')
		self.Append(self.removeid, 'Remove')

	def onProperties(self, evt):
		classname = self.editor.nodes[self.name]['class name']
		dialog = NodePropertiesDialog(self.editor, self.name, classname)
		if dialog.ShowModal() == wx.ID_OK:
			classname, name = dialog.getValues()
			self.editor.setNode(self.name, classname, name)

		dialog.Destroy()

	def onBindEvent(self, evt):
		item = self.editor.getNodeItem(self.name)
		dialog = EventBindingDialog(self.editor, item)
		if dialog.ShowModal() == wx.ID_OK:
			eventname, tonodename = dialog.getValues()
			item = self.editor.addEventBinding(eventname, self.name, tonodename)
			self.editor.EnsureVisible(item)
		dialog.Destroy()

	def onRemove(self, evt):
		self.editor.removeNode(self.name)

class EventBindingMenu(wx.Menu):
	def __init__(self, editor, fromnodeitem, string):
		self.editor = editor
		self.fromnodeitem = fromnodeitem
		self.string = string
		wx.Menu.__init__(self)
		self.removeid = wx.NewId()
		self.Bind(wx.EVT_MENU, self.onRemove, id=self.removeid)
		self.Append(self.removeid, 'Remove')

	def onRemove(self, evt):
		self.editor.removeEventBinding(self.fromnodeitem, self.string)

class NodePropertiesDialog(wx.Dialog):
	def __init__(self, parent, name, classname=None):
		self.name = name
		if classname is None:
			title = 'Add Node'
		else:
			title = 'Node Properties'
		wx.Dialog.__init__(self, parent, -1, title)

		self.sizer = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Name:')
		self.sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		self.tcname = wx.TextCtrl(self, -1, name)
		self.sizer.Add(self.tcname, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'Class:')
		self.sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		choices = leginon.noderegistry.getNodeClassNames()
		choices.sort()
		self.cclass = wx.Choice(self, -1, choices=choices)
		if classname is None:
			self.cclass.SetSelection(0)
		else:
			# ...
			self.cclass.SetStringSelection(classname)
		self.sizer.Add(self.cclass, (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.sizer.AddGrowableCol(1)

		buttonsizer = wx.GridBagSizer(5, 5)
		bok = wx.Button(self, wx.ID_OK, 'OK')
		bok.SetDefault()
		buttonsizer.Add(bok, (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		buttonsizer.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		buttonsizer.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

		sizer = wx.GridBagSizer()
		sizer.Add(self.sizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sizer.Add(buttonsizer, (1, 0), (1, 1),
							wx.EXPAND|wx.RIGHT|wx.LEFT|wx.BOTTOM, 10)
		self.SetSizerAndFit(sizer)

	def onOK(self, evt):
		name = self.tcname.GetValue()
		if name == self.name or self.GetParent().getNodeItem(name) is None:
			evt.Skip()
		else:
			message = 'A node named \'%s\' already exists.' % name
			title = 'Node Properties Error'
			dialog = wx.MessageDialog(self, message, title, wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

	def getValues(self):
		classname = self.cclass.GetStringSelection()
		name = self.tcname.GetValue()
		return classname, name

class EventBindingDialog(wx.Dialog):
	def __init__(self, parent, fromnodeitem):
		self.fromnodeitem = fromnodeitem
		wx.Dialog.__init__(self, parent, -1, 'Add Event Binding')

		self.sizer = wx.GridBagSizer(5, 5)

		label = wx.StaticText(self, -1, 'Event:')
		self.sizer.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		fromnodename = parent.GetItemText(fromnodeitem)
		choices = parent.getEventOutputs(fromnodename)
		choices.sort()
		self.cevents = wx.Choice(self, -1, choices=choices)
		self.cevents.SetSelection(0)
		self.sizer.Add(self.cevents, (0, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		label = wx.StaticText(self, -1, 'To Node:')
		self.sizer.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		choices = parent.getNodeNames()
		choices.sort()
		self.ctonode = wx.Choice(self, -1, choices=choices)
		self.ctonode.SetSelection(0)
		self.sizer.Add(self.ctonode, (1, 1), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

		self.sizer.AddGrowableCol(1)

		buttonsizer = wx.GridBagSizer(5, 5)
		bok = wx.Button(self, wx.ID_OK, 'OK')
		bok.SetDefault()
		buttonsizer.Add(bok, (0, 0), (1, 1),
										wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		bcancel = wx.Button(self, wx.ID_CANCEL, 'Cancel')
		buttonsizer.Add(bcancel, (0, 1), (1, 1), wx.ALIGN_CENTER)
		buttonsizer.AddGrowableCol(0)

		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

		sizer = wx.GridBagSizer()
		sizer.Add(self.sizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		sizer.Add(buttonsizer, (1, 0), (1, 1),
							wx.EXPAND|wx.RIGHT|wx.LEFT|wx.BOTTOM, 10)
		self.SetSizerAndFit(sizer)

	def onOK(self, evt):
		eventname = self.cevents.GetStringSelection()
		tonodename = self.ctonode.GetStringSelection()
		parent = self.GetParent()
		string = parent.eventBindingString(eventname, tonodename)
		if parent.getEventBindingItem(self.fromnodeitem, string) is None:
			evt.Skip()
		else:
			message = 'Binding already exists.'
			title = 'Event Binding Error'
			dialog = wx.MessageDialog(self, message, title, wx.OK|wx.ICON_ERROR)
			dialog.ShowModal()
			dialog.Destroy()

	def getValues(self):
		eventname = self.cevents.GetStringSelection()
		tonodename = self.ctonode.GetStringSelection()
		return eventname, tonodename

class ApplicationEditorLite(wx.TreeCtrl):
	def __init__(self, parent):
		self.nodes = {}
		style = wx.TR_EDIT_LABELS|wx.TR_DEFAULT_STYLE
		wx.TreeCtrl.__init__(self, parent, -1, style=style)

		self.root = self.AddRoot('My Application')

		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onTreeItemRightClick)
		self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onTreeBeginLabelEdit)
		self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onTreeEndLabelEdit)

	def clear(self):
		self.DeleteAllItems()
		self.nodes = {}
		self.root = self.AddRoot('My Application')

	def getApplicationName(self):
		return self.GetItemText(self.root)

	def setApplicationName(self, name):
		self.SetItemText(self.root, name)

	def get(self):
		application = {}
		application['name'] = self.getApplicationName()
		application['nodes'] = []
		application['bindings'] = []
		for nodename in self.getNodeNames():
			classname = self.nodes[nodename]['class name']
			nodeitem = self.getNodeItem(nodename)
			launcheritem = self.GetItemParent(nodeitem)
			launchername = self.GetItemText(launcheritem)
			dependencies = []
			node = (classname, nodename, launchername, dependencies)
			application['nodes'].append(node)
			for eventbinding in self.getEventBindings(nodename):
				string, eventname, tonodename = eventbinding
				binding = (eventname, nodename, tonodename)
				application['bindings'].append(binding)
		return application

	def set(self, application):
		self.clear()
		self.setApplicationName(application['name'])
		for node in application['nodes']:
			classname, nodename, launchername, dependencies = node
			if self.getLauncherItem(launchername) is None:
				self.addLauncher(launchername)
			try:
				self.addNode(classname, nodename, launchername, dependencies)
			except ValueError, e:
				message = 'Add node \'%s\' failed: %s.' % (nodename, e)
				title = 'Application Warning'
				dialog = wx.MessageDialog(self, message, title, wx.OK|wx.ICON_WARNING)
				dialog.ShowModal()
				dialog.Destroy()
		for binding in application['bindings']:
			eventname, fromnode, tonode = binding
			try:
				self.addEventBinding(eventname, fromnode, tonode)
			except ValueError, e:
				# ...
				pass
				print e
		self.expand()

	def expand(self):
		self.Expand(self.root)
		item, cookie = self.GetFirstChild(self.root)
		while item.IsOk():
			self.Expand(item)
			item, cookie = self.GetNextChild(self.root, cookie)

	def eventItemMethod(self, evt, methods):
		item = evt.GetItem()
		i = 0
		while item != self.root:
			if item == self.root:
				break
			item = self.GetItemParent(item)
			i += 1
		try:
			methods[i](evt)
		except IndexError:
			pass

	def onTreeItemRightClick(self, evt):
		methods = [
			self.onApplicationRightClick,
			self.onLauncherRightClick,
			self.onNodeRightClick,
			self.onEventBindingRightClick,
		]
		self.eventItemMethod(evt, methods)

	def onTreeBeginLabelEdit(self, evt):
		methods = [
			self.onApplicationBeginLabelEdit,
			self.onLauncherBeginLabelEdit,
			self.onNodeBeginLabelEdit,
			self.onEventBindingBeginLabelEdit,
		]
		self.eventItemMethod(evt, methods)

	def onTreeEndLabelEdit(self, evt):
		methods = [
			self.onApplicationEndLabelEdit,
			self.onLauncherEndLabelEdit,
			self.onNodeEndLabelEdit,
		]
		self.eventItemMethod(evt, methods)

	def onApplicationRightClick(self, evt):
		applicationmenu = ApplicationMenu(self)
		self.PopupMenu(applicationmenu, evt.GetPoint())

	def onLauncherRightClick(self, evt):
		launchermenu = LauncherMenu(self, self.GetItemText(evt.GetItem()))
		self.PopupMenu(launchermenu, evt.GetPoint())

	def onNodeRightClick(self, evt):
		nodemenu = NodeMenu(self, self.GetItemText(evt.GetItem()))
		self.PopupMenu(nodemenu, evt.GetPoint())

	def onEventBindingRightClick(self, evt):
		item = evt.GetItem()
		fromnodeitem = self.GetItemParent(item)
		string = self.GetItemText(item)
		eventbindingmenu = EventBindingMenu(self, fromnodeitem, string)
		self.PopupMenu(eventbindingmenu, evt.GetPoint())

	def onApplicationBeginLabelEdit(self, evt):
		pass

	def onLauncherBeginLabelEdit(self, evt):
		pass

	def onNodeBeginLabelEdit(self, evt):
		pass

	def onEventBindingBeginLabelEdit(self, evt):
		evt.Veto()

	def onApplicationEndLabelEdit(self, evt):
		if not evt.GetLabel():
			evt.Veto()

	def onLauncherEndLabelEdit(self, evt):
		name = evt.GetLabel()
		if not name or self.getLauncherItem(name) is not None:
			evt.Veto()

	def onNodeEndLabelEdit(self, evt):
		name = evt.GetLabel()
		if not name or self.getNodeItem(name) is not None:
			evt.Veto()
		else:
			self.setNode(self.GetItemText(evt.GetItem()), newname=name)

	def getName(self):
		return self.GetItemText(self.root)

	def setName(self, name):
		self.SetItemText(self.root, name)

	def addLauncher(self, name=None):
		if name is None:
			name = 'My Launcher'
			i = 1
			while self.getLauncherItem(name) is not None:
				name = 'My Launcher (%d)' % i
				i += 1
		elif self.getLauncherItem(name) is not None:
			raise ValueError('launcher named \'%s\' already exists' % name)
		return self.AppendItem(self.root, name)

	def removeLauncher(self, name):
		item = self.getLauncherItem(name)
		if item is None:
			raise ValueError('invalid launcher name \'%s\'' % name)
		nodenames = self.getNodeNames(name)
		for nodename in nodenames:
			del self.nodes[nodename]
		self.Delete(item)
		self.removeEventBindings(nodenames)

	def getLauncherItem(self, name):
		item, cookie = self.GetFirstChild(self.root)
		while item.IsOk():
			if self.GetItemText(item) == name:
				return item
			item, cookie = self.GetNextChild(self.root, cookie)
		return None

	def addNode(self, classname, name, launchername, dependencies):
		launcheritem = self.getLauncherItem(launchername)
		if launcheritem is None:
			raise ValueError('invalid launcher name \'%s\'' % launchername)
		if name is None:
			name = 'My Node'
			i = 1
			while self.getNodeItem(name) is not None:
				name = 'My Node (%d)' % i
				i += 1
		elif self.getNodeItem(name) is not None:
			raise ValueError('node named \'%s\' already exists' % name)
		self.nodes[name] = {}
		self.nodes[name]['class name'] = classname
		self.nodes[name]['dependencies'] = dependencies
		self.nodes[name]['events'] = []
		return self.AppendItem(launcheritem, name)

	def removeNode(self, name):
		item = self.getNodeItem(name)
		if item is None:
			raise ValueError('invalid node name \'%s\'' % name)
		self.Delete(item)
		del self.nodes[name]
		self.removeEventBindings([name])

	def getNodeItem(self, name):
		launcheritem, launchercookie = self.GetFirstChild(self.root)
		while launcheritem.IsOk():
			nodeitem, nodecookie = self.GetFirstChild(launcheritem)
			while nodeitem.IsOk():
				if self.GetItemText(nodeitem) == name:
					return nodeitem
				nextnode = self.GetNextChild(launcheritem, nodecookie)
				nodeitem, nodecookie = nextnode
			nextlauncher = self.GetNextChild(self.root, launchercookie)
			launcheritem, launchercookie = nextlauncher
		return None

	def getNodeNames(self, launchername=None):
		names = []
		if launchername is None:
			launcheritem, launchercookie = self.GetFirstChild(self.root)
			while launcheritem.IsOk():
				nodeitem, nodecookie = self.GetFirstChild(launcheritem)
				while nodeitem.IsOk():
					names.append(self.GetItemText(nodeitem))
					nextnode = self.GetNextChild(launcheritem, nodecookie)
					nodeitem, nodecookie = nextnode
				nextlauncher = self.GetNextChild(self.root, launchercookie)
				launcheritem, launchercookie = nextlauncher
		else:
			launcheritem = self.getLauncherItem(launchername)
			nodeitem, nodecookie = self.GetFirstChild(launcheritem)
			while nodeitem.IsOk():
				names.append(self.GetItemText(nodeitem))
				nextnode = self.GetNextChild(launcheritem, nodecookie)
				nodeitem, nodecookie = nextnode
		return names

	def addEventBinding(self, eventname, fromnodename, tonodename):
		if self.getNodeItem(tonodename) is None:
			raise ValueError('no node named \'%s\' exists' % tonodename)
		fromnodeitem = self.getNodeItem(fromnodename)
		if fromnodeitem is None:
			raise ValueError('no node named \'%s\' exists' % fromnodename)
		string = self.eventBindingString(eventname, tonodename)
		if self.getEventBindingItem(fromnodeitem, string) is not None:
			errorstring = '%s from %s to %s already bound'
			raise ValueError(errorstring % (eventname, fromnodename, tonodename))
		self.nodes[fromnodename]['events'].append((eventname, tonodename))
		return self.AppendItem(fromnodeitem, string)

	def removeEventBinding(self, fromnodeitem, string):
		item = self.getEventBindingItem(fromnodeitem, string)
		if item is None:
			raise ValueError('invalid event binding')
		fromnodename = self.GetItemText(fromnodeitem)
		eventname, tonodename = self.eventBinding(string)
		self.Delete(item)
		self.nodes[fromnodename]['events'].remove((eventname, tonodename))

	def eventBindingString(self, eventname, tonodename):
		return '%s to node %s' % (eventname, tonodename)

	def eventBinding(self, string):
		# ...
		tokens = string.split(' to node ')
		eventname = tokens[0]
		tonodename = tokens[-1]
		return eventname, tonodename

	def getEventBindingItem(self, fromnodeitem, string):
		item, cookie = self.GetFirstChild(fromnodeitem)
		while item.IsOk():
			if self.GetItemText(item) == string:
				return item
			item, cookie = self.GetNextChild(fromnodeitem, cookie)
		return None

	def getEventOutputs(self, nodename):
		classname = self.nodes[nodename]['class name']
		nodeclass = leginon.noderegistry.getNodeClass(classname)
		eventoutputs = nodeclass.eventoutputs
		return [eventoutput.__name__ for eventoutput in eventoutputs]

	def getEventBindings(self, fromnodename):
		eventbindings = []
		fromnodeitem = self.getNodeItem(fromnodename)
		item, cookie = self.GetFirstChild(fromnodeitem)
		while item.IsOk():
			string = self.GetItemText(item)
			eventname, tonodename = self.eventBinding(string)
			eventbindings.append((string, eventname, tonodename))
			item, cookie = self.GetNextChild(fromnodeitem, cookie)
		return eventbindings

	def setEventBinding(self, fromnodename, string,
											eventname=None, tonodename=None):
		fromnodeitem = self.getNodeItem(fromnodename)
		item = self.getEventBindingItem(fromnodeitem, string)
		eventbinding = self.eventBinding(self.GetItemText(item))
		if eventname is None:
			eventname = eventbinding[0]
		if tonodename is None:
			tonodename = eventbinding[1]
		string = self.eventBindingString(eventname, tonodename)
		self.SetItemText(item, string)
		index = self.nodes[fromnodename]['events'].index(eventbinding)
		self.nodes[fromnodename]['events'][index] = (eventname, tonodename)

	def setNode(self, name, classname=None, newname=None):
		if classname is not None:
			self.nodes[name]['class name'] = classname
			eventoutputs = self.getEventOutputs(name)
			for eventbinding in self.getEventBindings(name):
				string, eventname, tonodename = eventbinding
				if eventname not in eventoutputs:
					self.removeEventBinding(item, string)
		if newname is not None and name != newname:
			for nodename in self.getNodeNames():
				for eventbinding in self.getEventBindings(nodename):
					string, eventname, tonodename = eventbinding
					if tonodename == name:
						self.setEventBinding(nodename, string, tonodename=newname)
			item = self.getNodeItem(name)
			self.SetItemText(item, newname)
			self.nodes[newname] = self.nodes[name]
			del self.nodes[name]

	def removeEventBindings(self, tonodenames):
		for fromnodename in self.getNodeNames():
			for eventbinding in self.getEventBindings(fromnodename):
				string, eventname, tonodename = eventbinding
				if tonodename in tonodenames:
					fromnodeitem = self.getNodeItem(fromnodename)
					self.removeEventBinding(fromnodeitem, string)

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Application Lite Editor Test')
			editor = ApplicationEditorLite(frame)
			self.SetTopWindow(frame)
			frame.Show()
			return True

	app = App(0)
	app.MainLoop()

