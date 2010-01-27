# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#

import wx

import leginon.gui.wx.ApplicationEditorLite
import leginon.application

class Frame(wx.Frame):
	def __init__(self, parent, manager):
		style = wx.DEFAULT_FRAME_STYLE
		style |= wx.FRAME_NO_TASKBAR
		wx.Frame.__init__(self, parent, -1, 'Application Editor', style=style)

		self.manager = manager
		self.apps = self.manager.getApplications()

		self.menubar = wx.MenuBar()

		menu = wx.Menu()

		load = wx.MenuItem(menu, -1, '&Load...')
		if not self.apps:
			load.Enable(False)
		save = wx.MenuItem(menu, -1, '&Save')
		saveas = wx.MenuItem(menu, -1, 'Save &As...')
		exit = wx.MenuItem(menu, -1, 'E&xit')

		self.Bind(wx.EVT_MENU, self.onLoad, load)
		self.Bind(wx.EVT_MENU, self.onSave, save)
		self.Bind(wx.EVT_MENU, self.onSaveAs, saveas)
		self.Bind(wx.EVT_MENU, self.onExit, exit)
		menu.AppendItem(load)
		menu.AppendSeparator()
		menu.AppendItem(save)
		menu.AppendItem(saveas)
		menu.AppendSeparator()
		menu.AppendItem(exit)

		self.menubar.Append(menu, '&Application')

		self.SetMenuBar(self.menubar)

		#self.editor = leginon.gui.wx.Master.ApplicationEditorCanvas(self, -1)
		self.editor = leginon.gui.wx.ApplicationEditorLite.ApplicationEditorLite(self)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(self.editor, (0, 0), (1, 1), wx.EXPAND)
		#sz.SetItemMinSize(self.editor, (640, 480))
		sz.SetItemMinSize(self.editor, (300, 400))
		sz.AddGrowableRow(0)
		sz.AddGrowableCol(0)
		self.SetSizerAndFit(sz)

	def load(self, app):
		app.load()
		appdata = {'name': app.data['name'], 'nodes': [], 'bindings': []}
		for ns in app.nodespecs:
			appdata['nodes'].append((ns['class string'], ns['alias'],
																ns['launcher alias'], ns['dependencies']))
		for bs in app.bindingspecs:
			appdata['bindings'].append((bs['event class string'],
																	bs['from node alias'], bs['to node alias']))
		#self.editor.application.setApplication(appdata)
		self.editor.set(appdata)

	def onLoad(self, evt):
		dialog = LoadDialog(self, self.apps.keys())
		if dialog.ShowModal() == wx.ID_OK:
			app = self.apps[dialog.getApplicationName()]
			self.load(app)
		dialog.Destroy()

	def save(self, name, appdata):
		app = leginon.application.Application(self.manager)
		app.setName(name)
		for ns in appdata['nodes']:
			app.addNodeSpec(*ns)
		for bs in appdata['bindings']:
			app.addBindingSpec(*bs)
		#self.editor.application.setName(name)
		self.editor.setApplicationName(name)
		self.apps[name] = app
		app.save()

	def onSave(self, evt):
		#appdata = self.editor.application.getApplication()
		appdata = self.editor.get()
		name = appdata['name']
		self.save(name, appdata)

	def onSaveAs(self, evt):
		#name = self.editor.application.getName()
		name = self.editor.getApplicationName()
		dialog = SaveAsDialog(self, name, self.apps.keys())
		if dialog.ShowModal() == wx.ID_OK:
			#appdata = self.editor.application.getApplication()
			appdata = self.editor.get()
			self.save(dialog.getApplicationName(), appdata)
		dialog.Destroy()

	def onExit(self, evt):
		self.Destroy()

class SaveAsDialog(wx.Dialog):
	def __init__(self, parent, name, names):
		self.names = names
		wx.Dialog.__init__(self, parent, -1, 'Save As')

		self.appname = wx.TextCtrl(self, -1, name)

		saveasbutton = wx.Button(self, wx.ID_OK, 'Save')
		saveasbutton.SetDefault()
		cancelbutton = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		buttonsizer = wx.GridBagSizer(0, 3)
		buttonsizer.Add(saveasbutton, (0, 0), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		buttonsizer.Add(cancelbutton, (0, 1), (1, 1), wx.ALIGN_CENTER)
		buttonsizer.AddGrowableCol(0)

		sizer = wx.GridBagSizer(5, 5)
		sizer.Add(wx.StaticText(self, -1, 'Name:'), (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.appname, (0, 1), (1, 1), wx.EXPAND)
		sizer.Add(buttonsizer, (2, 0), (1, 2), wx.EXPAND)
		sizer.AddGrowableCol(1)

		self.dialogsizer = wx.GridBagSizer()
		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

		self.Bind(wx.EVT_BUTTON, self.onSaveAs, saveasbutton)

	def onSaveAs(self, evt):
		name = self.getApplicationName()
		if name in self.names:
			dialog = wx.MessageDialog(
										self,
										'Application \'%s\' already exists, overwrite?' % name,
										'Warning',
										style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
								)
			if dialog.ShowModal() == wx.ID_YES:
				evt.Skip()
			dialog.Destroy()
		else:
			evt.Skip()

	def getApplicationName(self):
		return self.appname.GetValue()

class LoadDialog(wx.Dialog):
	def __init__(self, parent, names):
		self.names = names
		wx.Dialog.__init__(self, parent, -1, 'Load')

		self.appchoice = wx.Choice(self, -1, choices=names)
		self.appchoice.SetSelection(0)

		loadbutton = wx.Button(self, wx.ID_OK, 'Load')
		loadbutton.SetDefault()
		cancelbutton = wx.Button(self, wx.ID_CANCEL, 'Cancel')

		buttonsizer = wx.GridBagSizer(0, 3)
		buttonsizer.Add(loadbutton, (0, 0), (1, 1),
										wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		buttonsizer.Add(cancelbutton, (0, 1), (1, 1), wx.ALIGN_CENTER)
		buttonsizer.AddGrowableCol(0)

		sizer = wx.GridBagSizer(5, 5)
		sizer.Add(wx.StaticText(self, -1, 'Application:'), (0, 0), (1, 1),
							wx.ALIGN_CENTER_VERTICAL)
		sizer.Add(self.appchoice, (0, 1), (1, 1), wx.EXPAND)
		sizer.Add(buttonsizer, (2, 0), (1, 2), wx.EXPAND)
		sizer.AddGrowableCol(1)

		self.dialogsizer = wx.GridBagSizer()
		self.dialogsizer.Add(sizer, (0, 0), (1, 1), wx.EXPAND|wx.ALL, 10)
		self.SetSizerAndFit(self.dialogsizer)

	def getApplicationName(self):
		return self.appchoice.GetStringSelection()

if __name__ == '__main__':
	class App(wx.App):
		def OnInit(self):
			frame = wx.Frame(None, -1, 'Application Editor Test')
			dialog = Frame(frame)
			self.SetTopWindow(frame)
			frame.Show()
			dialog.Show()
			return True

	app = App(0)
	app.MainLoop()

