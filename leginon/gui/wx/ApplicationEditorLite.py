# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/gui/wx/ApplicationEditorLite.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-01 01:25:35 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import application
import wx

class ApplicationEditorLite(wx.TreeCtrl):
	def __init__(self, parent):
		style = wx.TR_EDIT_LABELS|wx.TR_DEFAULT_STYLE
		wx.TreeCtrl.__init__(self, parent, -1, style=style)

		self.root = self.AddRoot('My Application')

	def getName(self):
		return self.GetItemText(self.root)

	def setName(self, name):
		self.SetItemText(self.root, name)

	def addLauncher(self, name):
		if self.getLauncherItem(name) is not None:
			raise ValueError('Launcher named \'%s\' already exists' % name)
		self.AppendItem(self.root, name)

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
			raise ValueError('Invalid launcher name')
		if self.getNodeItem(name) is not None:
			raise ValueError('Node named \'%s\' already exists' % name)
		item = self.AppendItem(launcheritem, name)
		self.AppendItem(item, 'Events')

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
			nextlauncher = self.GetNextChild(self.root, launchercookie)
			launcheritem, launchercookie = nextlauncher
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

