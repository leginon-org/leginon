#!/usr/bin/env python
import os
import socket
import sys
import time
import win32api
import Tkinter
import tkSimpleDialog
import Pmw
import event
import interface
import leginonsetup
import nodegui
import acquisition
import EM
import targetfinder

applicationfilename = 'leginon.app'

class mySimpleDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent, title, args=None):
		'''Initialize a dialog.

		Arguments:

			parent -- a parent window (the application window)

			title -- the dialog title
		'''
		Tkinter.Toplevel.__init__(self, parent) 
		self.transient(parent)

		if title:
			self.title(title)

		self.parent = parent

		self.result = None

		body = Tkinter.Frame(self)
		self.initial_focus = self.body(body)
		body.pack(padx=5, pady=5)

		self.buttonbox()

#		self.grab_set()

		if not self.initial_focus:
			self.initial_focus = self

		self.protocol("WM_DELETE_WINDOW", self.cancel)

		if self.parent is not None:
			self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
																parent.winfo_rooty()+50))

		self.initial_focus.focus_set()

		self.wait_window(self)

class AddDialog(mySimpleDialog):
	def __init__(self, parent, name):
		self.name = name
		mySimpleDialog.__init__(self, parent, 'Add')

	def body(self, master):
		self.namelabel = Tkinter.Label(master, text='Name:')
		self.namelabel.grid(row=0, column=0, sticky = Tkinter.W)
		self.nameentry = Tkinter.Entry(master)
		self.nameentry.grid(row=1, column=0)
		self.nameentry.insert(Tkinter.END, self.name)

	def apply(self):
		self.result = self.nameentry.get()

class AddChoicesDialog(AddDialog):
	def __init__(self, parent, name, choices, sources=[]):
		self.sources = sources
		self.sources.sort()
		self.choices = choices
		self.choices.sort()
		for source in self.sources:
			self.choices.remove(source)
		AddDialog.__init__(self, parent, name)

	def body(self, master):
		AddDialog.body(self, master)

		self.sourceslabel = Tkinter.Label(master, text='Sources:')
		self.sourceslabel.grid(row=2, column=0, sticky = Tkinter.W)
		self.sourceslistbox = Tkinter.Listbox(master, bg='white')
		self.sourceslistbox.grid(row=3, column = 0, sticky=Tkinter.N+Tkinter.S,
															rowspan=2)
		scrollbar = Tkinter.Scrollbar(master, orient=Tkinter.VERTICAL,
																	command=self.sourceslistbox.yview)
		scrollbar.grid(row=3, column=1, sticky=Tkinter.N+Tkinter.S, rowspan=2)
		self.sourceslistbox.configure(yscrollcommand=scrollbar.set)

		for source in self.sources:
			self.sourceslistbox.insert(Tkinter.END, source)

		self.addbutton = Tkinter.Button(master, text='< Add  ', command=self.add)
		self.addbutton.grid(row = 3, column = 2,
												padx = 5, pady = 5,
												sticky=Tkinter.W+Tkinter.E)
		self.deletebutton = Tkinter.Button(master, text='  Delete >',
																				command=self.delete)
		self.deletebutton.grid(row = 4, column = 2,
														padx = 5, pady = 5,
														sticky=Tkinter.W+Tkinter.E)
		self.choiceslistbox = Tkinter.Listbox(master, bg='white')
		self.choiceslistbox.grid(row=3, column = 3, sticky=Tkinter.N+Tkinter.S,
															rowspan=2)
		scrollbar = Tkinter.Scrollbar(master, orient=Tkinter.VERTICAL,
																	command=self.choiceslistbox.yview)
		scrollbar.grid(row=3, column=4, sticky=Tkinter.N+Tkinter.S, rowspan=2)
		self.choiceslistbox.configure(yscrollcommand=scrollbar.set)

		for choice in self.choices:
			self.choiceslistbox.insert(Tkinter.END, choice)

	def add(self):
		selections = self.choiceslistbox.curselection()
		if len(selections) < 1:
			return

		for selection in selections:
			self.choiceslistbox.delete(selection)
			self.sourceslistbox.insert(Tkinter.END, self.choices[int(selection)])
			self.sources.append(self.choices[int(selection)])
			self.choices.pop(int(selection))

	def delete(self):
		selections = self.sourceslistbox.curselection()
		if len(selections) < 1:
			return

		for selection in selections:
			self.sourceslistbox.delete(selection)
			self.choiceslistbox.insert(Tkinter.END, self.sources[int(selection)])
			self.choices.append(self.sources[int(selection)])
			self.sources.pop(int(selection))

	def apply(self):
		self.result = (self.nameentry.get(), self.sources)

class Leginon(Tkinter.Frame):
	def __init__(self, parent):
		self.manageruiclient = None
		self.wrappers = {}
		self.gridatlases = {}
		self.targets = {}
		self.manager = None
		self.remotelauncher = None

		self.parent = parent
		self.parent.protocol('WM_DELETE_WINDOW', self.exit)
		Tkinter.Frame.__init__(self, parent)

		self.notebook = Pmw.NoteBook(self)
		self.notebook.component('hull')['width'] = 800
		self.notebook.component('hull')['height'] = 600
		self.notebook.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

		self.menu = Tkinter.Menu(parent, tearoff=0)
		parent.config(menu = self.menu)

		self.filemenu = Tkinter.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label='File', menu=self.filemenu)
		self.filemenu.add_command(label='New...', command=self.new)
		self.filemenu.add_separator()
		self.filemenu.add_command(label='Exit', command=self.exit)

		self.editmenu = Tkinter.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label='Edit', menu=self.editmenu)
		self.editmenu.add_command(label='Add Grid Atlas...',
															command=self.menuAddGridAtlas)
		self.editmenu.add_command(label='Add Target...', command=self.menuAddTarget)
		self.menu.entryconfigure(1, state=Tkinter.DISABLED)

		self.windowmenu = Tkinter.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label='Window', menu=self.windowmenu)
#		self.menu.entryconfigure(2, state=Tkinter.DISABLED)

	def start(self):
		self.new()

	def menuAddTarget(self):
		name = 'Target #%s' % str(len(self.targets) + 1)
		add_dialog = AddChoicesDialog(self, name,
											 self.targets.keys() + self.gridatlases.keys(), [])
		if add_dialog.result is not None:
			sourceids = []
			for source in add_dialog.result[1]:
				if source in self.targets:
					sourceids.append(self.targets[source].targetid)
				elif source in self.gridatlases:
					sourceids.append(self.gridatlases[source].targetid)
			self.addTarget(add_dialog.result[0], sourceids)

	def menuAddGridAtlas(self):
		name = 'Grid Atlas #%s' % str(len(self.gridatlases) + 1)
		add_dialog = AddDialog(self, name)
		if add_dialog.result is not None:
			self.addGridAtlas(add_dialog.result)

	def exit(self):
		self.kill()
		self.parent.destroy()

	def kill(self):
		if self.manager is None:
			self.remotelauncher = None
			return

		nodeids = self.manager.clients.keys()
		if self.remotelauncher is not None:
			nodeids.remove(self.remotelauncher)
			self.remotelauncher = None
		nodeids.remove(self.locallauncherid)
		for nodeid in nodeids:
			try:
				self.manager.killNode(nodeid)
			except Exception, e:
				print 'failed to kill', nodeid, e

		while len(self.manager.clients) > 2:
			time.sleep(0.25)

		self.manager.killNode(self.locallauncherid)

		while len(self.manager.clients) > 1:
			time.sleep(0.25)

		self.manager.exit()
		self.manager = None
		for page in self.notebook.pagenames():
			self.notebook.delete(page)
		self.manageruiclient = None
		self.windowmenu.delete(0, Tkinter.END)
		self.wrappers = {}
		self.gridatlases = {}
		self.targets = {}

	# needs to check what got started, the whole lot needs error handling
	def new(self):
		self.filemenu.entryconfigure(0, state=Tkinter.DISABLED)
		self.kill()
		setupwizard = leginonsetup.SetupWizard(self)
		self.manager = setupwizard.manager
		self.remotelauncher = setupwizard.remotelauncher
		if self.manager is None:
			self.filemenu.entryconfigure(0, state=Tkinter.NORMAL)
			return
		self.menu.entryconfigure(1, state=Tkinter.NORMAL)
		self.startApplication()
		self.startUI()
		self.filemenu.entryconfigure(0, state=Tkinter.NORMAL)

	def startApplication(self):
		self.manager.app.load(applicationfilename)

		self.locallauncherid = self.localLauncherID()
		replaceargs = {}
		for args in self.manager.app.launchspec:
			if args[2] == 'EM' and self.remotelauncher is not None:
				newlauncherid = self.remotelauncher
			else:
				newlauncherid = self.locallauncherid

			if args[0] != newlauncherid: 
				replaceargs[args] = (newlauncherid,) + args[1:]

		for args in replaceargs:
			self.manager.app.delLaunchSpec(args)
			self.manager.app.addLaunchSpec(replaceargs[args])

		self.manager.app.launch()

	def startUI(self):
		managerlocation = self.managerLocation()
		self.manageruiclient = interface.Client(managerlocation[0],
																										managerlocation[1])
		self.debug = Debug(self.manageruiclient, self.notebook,
																		self.windowmenu, 'Debug')

	def nodeLocations(self):
		try:
			return self.manageruiclient.execute('getNodeLocations')
		except:
			return {}

	def uiClient(self, nodeid, attempts = 10):
		nodeidstr = str(nodeid)
		for i in range(attempts):
			try:
				nodelocations = self.nodeLocations()
				hostname = nodelocations[nodeidstr]['hostname']
				uiport = nodelocations[nodeidstr]['UI port']
				return interface.Client(hostname, uiport)
			except KeyError:
				time.sleep(0.25)
		return None

	def managerLocation(self):
		managerlocation = self.manager.location()
		return (managerlocation['hostname'], managerlocation['UI port'])

	def localLauncherID(self):
		return (socket.gethostname(),)

	def addGridAtlas(self, name):
		self.gridatlases[name] = GridAtlas(self.manager, self.manageruiclient,
																		self.locallauncherid, self.notebook,
																		self.debug, self.windowmenu, name)

	def addTarget(self, name, sourceids=[]):
		self.targets[name] = Target(self.manager, self.manageruiclient,
																self.locallauncherid, self.notebook,
																self.debug, self.windowmenu, name,
																sourceids)

class CustomWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
#		self.uiclients = {}
		self.groups = {}

	def widgetFromName(self, parent, uiclient, name, attempts=10):
		for i in range(attempts):
			spec = uiclient.getSpec()
			if spec is not None:
				break
			time.sleep(0.25)
		return self.widgetFrom(parent, uiclient, spec, name)

	def widgetFrom(self, parent, uiclient, spec, name):
		content = spec['content']
		for subspec in content:
			if subspec['name'] == name[0]:
				if len(name) == 1:
					return nodegui.widgetFromSpec(parent, uiclient, subspec, False)
				else:
					return self.widgetFrom(parent, uiclient, subspec, name[1:])

	# should be kwargs
	def arrangeEntry(self, widget, width = 10, justify = Tkinter.RIGHT):
		widget.entry['width'] = width
		widget.entry['justify'] = justify
		widget.entry.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
		widget.getbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
		widget.setbutton.grid(row = 0, column = 3, padx = 5, pady = 5)

	def arrangeCombobox(self, widget, text=None):
		if text is not None:
			widget.label.configure(text=text)
		widget.combo.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
		widget.getbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
		widget.setbutton.grid(row = 0, column = 3, padx = 5, pady = 5)

	# addGroup and addWidget might be able to be done purely with Pmw.Group
	def addGroup(self, name):
		group = Pmw.Group(self, tag_text = name)
		group.grid(row = len(self.groups), column = 0, padx=10, pady=10)
		# whatever
		if name == 'Image':
			group.grid(row = 0, column = 1, rowspan = len(self.groups))
		self.groups[name] = {}
		self.groups[name]['group'] = group
		self.groups[name]['widgets'] = []

	def addWidget(self, groupname, uiclient, name):
		if groupname not in self.groups:
			self.addGroup(groupname)
		nwidgets = len(self.groups[groupname]['widgets'])
		interior = self.groups[groupname]['group'].interior()
		widget = self.widgetFromName(interior, uiclient, name)
		widget.grid(row = nwidgets, column = 0, padx = 10, pady = 10,
																		sticky=Tkinter.W+Tkinter.E)
		self.groups[groupname]['widgets'].append(widget)
		return widget

class GridAtlasWidget(CustomWidget):
	def __init__(self, parent, gridpreview, stateimagemosaic):
		CustomWidget.__init__(self, parent)

		widget = self.addWidget('Settings', gridpreview,
														('Preferences', 'Magnification'))
		self.arrangeEntry(widget, 9)
		widget = self.addWidget('Settings', stateimagemosaic,
																			('Scale', 'Auto Scale'))
		self.arrangeEntry(widget, 4)

		self.addWidget('Control', gridpreview, ('Controls', 'Run'))
		self.addWidget('Control', gridpreview, ('Controls', 'Stop'))
		self.addWidget('Control', gridpreview, ('Controls', 'Reset'))

		widget = self.addWidget('Image', stateimagemosaic, ('Mosaic Image',))
		widget.iv.canvas.resize(0, 0, 512, 512)

class TargetWidget(CustomWidget):
	def __init__(self, parent, acquisition, clicktargetfinder):
		CustomWidget.__init__(self, parent)

		widget = self.addWidget('Settings', acquisition,
															('Presets', 'Preset Names'))
		self.arrangeEntry(widget, 20, Tkinter.LEFT)
		widget = self.addWidget('Settings', acquisition,
															('Preferences', 'TEM Parameter'))
		self.arrangeCombobox(widget, 'Positioning Method')
		widget = self.addWidget('Settings', acquisition,
															('Preferences', 'Acquisition Type'))
		self.arrangeCombobox(widget)

		widget = self.addWidget('Image', clicktargetfinder, ('Clickable Image',))
		widget.iv.canvas.resize(0, 0, 512, 512)

class WidgetWrapper(object):
	def __init__(self, manager, manageruiclient, launcherid, notebook,
																			debug, windowmenu, name):
		self.nodeinfo = {}
		self.manager = manager
		self.manageruiclient = manageruiclient
		self.launcherid = launcherid
		self.notebook = notebook
		self.debug = debug
		self.windowmenu = windowmenu
		self.name = name

	def addNodeInfo(self, key, name, classname):
		self.nodeinfo[key] = {}
		self.nodeinfo[key]['name'] = name
		self.nodeinfo[key]['class name'] = classname

	def initialize(self):
		for node in self.nodeinfo:
			self.nodeinfo[node]['ID'] = self.manager.launchNode(self.launcherid, 0,
																						self.nodeinfo[node]['class name'],
																						self.nodeinfo[node]['name'])

		self.initializeBindings()

		for node in self.nodeinfo:
			self.nodeinfo[node]['UI info'] = self.uiClient(self.nodeinfo[node]['ID'])
		self.page = self.notebook.add(self.name)

		self.initializeWidget()

		self.menuvariable = Tkinter.IntVar()
		self.menuvariable.set(1)
		self.windowmenu.add_checkbutton(label=self.name,
																		variable=self.menuvariable,
																		command=self.menuCallback)
		self.widget.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
		self.notebook.setnaturalsize()
		self.notebook.selectpage(self.name)

		for node in self.nodeinfo:
			self.debug.addDebugTab(self.nodeinfo[node]['name'],
															self.nodeinfo[node]['UI info'])

	def initializeBindings(self):
		pass

	def initializeWidget(self):
		pass

	def menuCallback(self):
		if self.menuvariable.get() == 1:
			self.show()
		else:
			self.hide()

	# better way in Pmw.NoteBook that delete?
	def hide(self):
		self.widget.destroy()
		self.notebook.delete(self.name)
		self.page = None
		self.widget = None

	def show(self):
		self.page = self.notebook.add(self.name)
		self.initializeWidget()
		self.widget.pack()
		self.notebook.selectpage(self.name)

	def nodeLocations(self):
		try:
			return self.manageruiclient.execute('getNodeLocations')
		except:
			return {}

	def uiClient(self, nodeid, attempts = 10):
		nodeidstr = str(nodeid)
		for i in range(attempts):
			try:
				nodelocations = self.nodeLocations()
				hostname = nodelocations[nodeidstr]['hostname']
				uiport = nodelocations[nodeidstr]['UI port']
				uiclient = interface.Client(hostname, uiport)
				return {'client': uiclient, 'hostname': hostname, 'UI port': uiport}
			except KeyError:
				time.sleep(0.25)
		return None

# initialize/refresh needs to be optimized
class Debug(WidgetWrapper):
	def __init__(self, manageruiclient, notebook, windowmenu, name):
		WidgetWrapper.__init__(self, None, manageruiclient, None, notebook, None,
																														windowmenu, name)
		self.initialize()

	def initializeWidget(self):
		self.widget = Pmw.NoteBook(self.page)
		nodelocations = self.nodeLocations()
		for node in nodelocations:
			page = self.widget.add(eval(node)[-1])
			gui = nodegui.NodeGUI(page, nodelocations[node]['hostname'],
																	nodelocations[node]['UI port'], None, True)
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
		self.widget.setnaturalsize()

	def addDebugTab(self, name, ui_info):
		if self.widget is not None:
			page = self.widget.add(name)
			gui = nodegui.NodeGUI(page, ui_info['hostname'],
																	ui_info['UI port'], None, True)
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

class GridAtlas(WidgetWrapper):
	def __init__(self, manager, manageruiclient, launcherid, notebook,
																			debug, windowmenu, name):
		WidgetWrapper.__init__(self, manager, manageruiclient, launcherid,
														notebook, debug, windowmenu, name)

		self.addNodeInfo('gridpreview', self.name + ' Grid Preview', 'GridPreview')
		self.addNodeInfo('stateimagemosaic', self.name + ' State Image Mosaic',
																												'StateImageMosaic')

		self.initialize()
		self.targetid = self.nodeinfo['stateimagemosaic']['ID']

	def initializeBindings(self):
		self.manager.addEventDistmap(event.TileImagePublishEvent,
																				self.nodeinfo['gridpreview']['ID'],
																				self.nodeinfo['stateimagemosaic']['ID'])

	def initializeWidget(self):
		self.widget = GridAtlasWidget(self.page,
												self.nodeinfo['gridpreview']['UI info']['client'],
												self.nodeinfo['stateimagemosaic']['UI info']['client'])

class Target(WidgetWrapper):
	def __init__(self, manager, manageruiclient, launcherid, notebook,
											debug, windowmenu, name, targetsourceids):
		WidgetWrapper.__init__(self, manager, manageruiclient, launcherid,
														notebook, debug, windowmenu, name)

		self.targetsourceids = targetsourceids

		self.addNodeInfo('acquire', self.name + ' Acquisition', 'Acquisition')
		self.addNodeInfo('target', self.name + ' Click Target Finder',
																							'ClickTargetFinder')

		self.initialize()

		self.targetid = self.nodeinfo['target']['ID']

	def initializeBindings(self):
		self.manager.addEventDistmap(event.CameraImagePublishEvent,
																				self.nodeinfo['acquire']['ID'],
																				self.nodeinfo['target']['ID'])
		for nodeid in self.targetsourceids:
			self.manager.addEventDistmap(event.ImageTargetListPublishEvent,
																				nodeid, self.nodeinfo['acquire']['ID'])


	def initializeWidget(self):
		self.widget = TargetWidget(self.page,
																self.nodeinfo['acquire']['UI info']['client'],
																self.nodeinfo['target']['UI info']['client'])

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

