# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ApplicationEditorLite.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-01 20:11:35 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import wx
import application
import event
import nodeclassreg

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
		name = self.editor.GetItemText(item)
		dialog = NodePropertiesDialog(self.editor, name)
		if dialog.ShowModal() == wx.ID_OK:
			classname, name = dialog.getValues()
			self.editor.SetItemText(item, name)
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
		dialog = NodePropertiesDialog(self.editor, self.name)
		if dialog.ShowModal() == wx.ID_OK:
			classname, name = dialog.getValues()
			item = self.editor.getNodeItem(self.name)
			self.editor.SetItemText(item, name)
		dialog.Destroy()

	def onBindEvent(self, evt):
		item = self.editor.getNodeItem(self.name)
		dialog = EventBindingDialog(self.editor, item)
		if dialog.ShowModal() == wx.ID_OK:
			eventname, tonodename = dialog.getValues()
			self.editor.addEventBinding(eventname, self.name, tonodename)
		dialog.Destroy()

	def onRemove(self, evt):
		self.editor.removeNode(self.name)

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
		choices = nodeclassreg.getNodeClassNames()
		choices.sort()
		self.cclass = wx.Choice(self, -1, choices=choices)
		if classname is None:
			self.cclass.SetSelection(0)
		else:
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
		choices = event.eventClasses().keys()
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
		style = wx.TR_EDIT_LABELS|wx.TR_DEFAULT_STYLE
		wx.TreeCtrl.__init__(self, parent, -1, style=style)

		self.root = self.AddRoot('My Application')

		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onTreeItemRightClick)
		self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onTreeBeginLabelEdit)
		self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onTreeEndLabelEdit)

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
			raise ValueError('Launcher named \'%s\' already exists' % name)
		return self.AppendItem(self.root, name)

	def removeLauncher(self, name):
		item = self.getLauncherItem(name)
		if item is None:
			raise ValueError('Invalid launcher name \'%s\'' % name)
		self.Delete(item)

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
			raise ValueError('Invalid launcher name \'%s\'' % launchername)
		if name is None:
			name = 'My Node'
			i = 1
			while self.getNodeItem(name) is not None:
				name = 'My Node (%d)' % i
				i += 1
		elif self.getNodeItem(name) is not None:
			raise ValueError('Node named \'%s\' already exists' % name)
		return self.AppendItem(launcheritem, name)

	def removeNode(self, name):
		item = self.getNodeItem(name)
		if item is None:
			raise ValueError('Invalid node name \'%s\'' % name)
		self.Delete(item)

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

	def getNodeNames(self):
		names = []
		launcheritem, launchercookie = self.GetFirstChild(self.root)
		while launcheritem.IsOk():
			nodeitem, nodecookie = self.GetFirstChild(launcheritem)
			while nodeitem.IsOk():
				names.append(self.GetItemText(nodeitem))
				nextnode = self.GetNextChild(launcheritem, nodecookie)
				nodeitem, nodecookie = nextnode
			nextlauncher = self.GetNextChild(self.root, launchercookie)
			launcheritem, launchercookie = nextlauncher
		return names

	def addEventBinding(self, eventname, fromnodename, tonodename):
		if self.getNodeItem(tonodename) is None:
			raise ValueError('No node named \'%s\' exists' % tonodename)
		fromnodeitem = self.getNodeItem(fromnodename)
		if fromnodeitem is None:
			raise ValueError('No node named \'%s\' exists' % fromnodename)
		string = self.eventBindingString(eventname, tonodename)
		if self.getEventBindingItem(fromnodeitem, string) is not None:
			errorstring = '%s from %s to %s already bound'
			raise ValueError(errorstring % (eventname, fromnodename, tonodename))
		return self.AppendItem(fromnodeitem, string)

	def removeEventBinding(self, fromnodeitem, string):
		item = self.getEventBindingItem(fromnodeitem, string)
		if item is None:
			raise ValueError('Invalid event binding')
		self.Delete(item)

	def eventBindingString(self, eventname, tonodename):
		return '%s to node %s' % (eventname, tonodename)

	def getEventBindingItem(self, fromnodeitem, string):
		item, cookie = self.GetFirstChild(fromnodeitem)
		while item.IsOk():
			if self.GetItemText(item) == string:
				return item
			item, cookie = self.GetNextChild(fromnodeitem, cookie)
		return None

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Application Lite Editor Test')
			editor = ApplicationEditorLite(frame)
			self.SetTopWindow(frame)
			frame.Show()
			editor.addLauncher('Instrument')
			editor.addNode(None, 'EM', 'Instrument', None)
			return True

	app = App(0)
	app.MainLoop()

