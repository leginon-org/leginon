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
		nodes = []
		replaceargs = []
		for args in self.manager.app.launchspec:
			nodes.append(('manager', args[3]))
			if args[2] == 'EM' and self.remotelauncher is not None:
				newlauncherid = self.remotelauncher
			else:
				newlauncherid = self.locallauncherid

			if args[0] != newlauncherid: 
				replaceargs.append((args, (newlauncherid,) + args[1:]))

		for i in replaceargs:
			self.manager.app.delLaunchSpec(i[0])
			self.manager.app.addLaunchSpec(i[1])

		self.manager.app.launch()
		self.manager.waitNodes(nodes)

	def startUI(self):
		managerlocation = self.managerLocation()
		self.manageruiclient = interface.Client(managerlocation[0],
																						managerlocation[1])
		self.debug = Debug(self.manageruiclient, self.notebook,
																		self.windowmenu, 'Debug')
		self.imagecorrection = ImageCorrection(self.manager, self.manageruiclient,
																		self.locallauncherid, self.notebook,
																		self.debug, self.windowmenu,
																		'Image Correction')

	def nodeLocations(self):
		try:
			return self.manageruiclient.execute('getNodeLocations')
		except:
			return {}

#	def uiClient(self, nodeid, attempts = 10):
#		nodeidstr = str(nodeid)
#		for i in range(attempts):
#			try:
#				nodelocations = self.nodeLocations()
#				hostname = nodelocations[nodeidstr]['hostname']
#				uiport = nodelocations[nodeidstr]['UI port']
#				return interface.Client(hostname, uiport)
#			except KeyError:
#				time.sleep(0.25)
#		return None

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

class WidgetGroup(Pmw.Group):
	def __init__(self, parent, name):
		Pmw.Group.__init__(self, parent, tag_text=name)
		self.widgets = []
		self.applybutton = None
		self.setcommands = []

	def addWidget(self, widget, setcommand=None):
		nwidgets = len(self.widgets)
		widget.grid(row = nwidgets, column = 0, padx = 10, pady = 5,
																		sticky=Tkinter.W+Tkinter.E)
		if setcommand is not None:
			self.addSetCommand(setcommand)
		if self.applybutton is not None:
			self.applybutton.grid_configure(row=nwidgets+1)
		self.widgets.append(widget)

	def addSetCommand(self, setcommand):
		nwidgets = len(self.widgets)
		if self.applybutton is None:
			self.applybutton = Tkinter.Button(self.interior(), text='Apply',
																													command=self.apply)
			self.applybutton.grid(row = nwidgets+1, column = 0, padx = 10, pady = 5)
		self.setcommands.append(setcommand)

	def apply(self):
		for setcommand in self.setcommands:
			setcommand()

class CustomWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		self.groups = {}
		self.widgets = {}

	def getWidgetInstance(self, id):
		# may need locking
		try:
			return self.widgets[id]
		except KeyError:
			return None

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
					w = nodegui.widgetFromSpec(parent, uiclient, subspec, False, True)
					if subspec['id'] in self.widgets:
						print 'error, widget id %s already exists' % str(subspec['id'])
					self.widgets[subspec['id']] = w
					return w
				else:
					return self.widgetFrom(parent, uiclient, subspec, name[1:])

	# should be kwargs
	def arrangeEntry(self, widget, width = 10, justify = Tkinter.RIGHT, buttons=True):
		widget.entry['width'] = width
		widget.entry['justify'] = justify
		widget.entry.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
		if buttons:
			if widget.getbutton is None:
				widget.setbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
			else:
				widget.getbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
				widget.setbutton.grid(row = 0, column = 3, padx = 5, pady = 5)
		else:
			if widget.setbutton is not None:
				widget.setbutton.grid_forget()
			if widget.getbutton is not None:
				widget.getbutton.grid_forget()

	def arrangeCombobox(self, widget, text=None, buttons=True):
		if text is not None:
			widget.label.configure(text=text)
		widget.combo.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
		if buttons:
			if widget.getbutton is None:
				widget.setbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
			else:
				widget.getbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
				widget.setbutton.grid(row = 0, column = 3, padx = 5, pady = 5)
		else:
			if widget.setbutton is not None:
				widget.setbutton.grid_forget()
			if widget.getbutton is not None:
				widget.getbutton.grid_forget()

	def arrangeTree(self, widget, text=None, buttons=True):
		if text is not None:
			widget.label.configure(text=text)
		widget.label.grid(row = 0, column = 0, sticky='w', padx = 5, pady = 5)
		if buttons:
			if widget.getbutton is None:
				widget.setbutton.grid(row = 0, column = 1, padx = 5, pady = 5)
			else:
				widget.getbutton.grid(row = 0, column = 1, padx = 5, pady = 5)
				widget.setbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
		else:
			if widget.setbutton is not None:
				widget.setbutton.grid_forget()
			if widget.getbutton is not None:
				widget.getbutton.grid_forget()
#		widget.sc.frame.grid(row = 1, column = 0, padx = 5, pady = 5,
#																											columnspan = 2)
#		widget.sc.frame.configure(bd=1, relief=Tkinter.SUNKEN)
		widget.tree.edit_tree.configure(bd=1, relief=Tkinter.SUNKEN)

	def addGroup(self, name):
		group = WidgetGroup(self, name)
		self.groups[name] = group
		group.grid(row = len(self.groups), column = 0, padx=10, pady=10)
		# whatever
		if name == 'Image':
			group.grid(row = 0, column = 1, rowspan = len(self.groups))

	def addWidget(self, groupname, info, name, groupset=False):
		info['server'].nodegui = self
		uiclient = info['client']
		if groupname not in self.groups:
			self.addGroup(groupname)
		interior = self.groups[groupname].interior()
		widget = self.widgetFromName(interior, uiclient, name)
		if groupset:
			self.groups[groupname].addWidget(widget, widget.setbutton.invoke)
		else:
			self.groups[groupname].addWidget(widget)
		return widget

class ImageCorrectionWidget(CustomWidget):
	def __init__(self, parent, corrector):
		CustomWidget.__init__(self, parent)

		widget = self.addWidget('Settings', corrector,
														('Preferences', 'Frames to Average'), True)
		self.arrangeEntry(widget, 2, Tkinter.RIGHT, False)
		widget = self.addWidget('Settings', corrector,
														('Preferences', 'Camera Configuration'), True)
		self.arrangeTree(widget, None, False)

		self.addWidget('Control', corrector, ('Acquire', 'Acquire Dark'))
		self.addWidget('Control', corrector, ('Acquire', 'Acquire Bright'))
		self.addWidget('Control', corrector, ('Acquire', 'Acquire Corrected'))

		widget = self.addWidget('Image', corrector, ('Acquire', 'Image'))
		widget.iv.canvas.resize(0, 0, 512, 512)

class GridAtlasWidget(CustomWidget):
	def __init__(self, parent, gridpreview, stateimagemosaic):
		CustomWidget.__init__(self, parent)

		widget = self.addWidget('Settings', gridpreview,
														('Preferences', 'Magnification'), True)
		self.arrangeEntry(widget, 9, Tkinter.RIGHT, False)
		widget = self.addWidget('Settings', stateimagemosaic,
																			('Scale', 'Auto Scale'), True)
		self.arrangeEntry(widget, 4, Tkinter.RIGHT, False)
		widget = self.addWidget('Settings', stateimagemosaic,
																			('Calibration Method',), True)
		self.arrangeCombobox(widget, 'Positioning Method', False)

		self.addWidget('Control', gridpreview, ('Controls', 'Run'))
		self.addWidget('Control', gridpreview, ('Controls', 'Stop'))
		self.addWidget('Control', gridpreview, ('Controls', 'Reset'))

		widget = self.addWidget('Image', stateimagemosaic, ('Mosaic Image',))
		widget.iv.canvas.resize(0, 0, 512, 512)

class TargetWidget(CustomWidget):
	def __init__(self, parent, acquisition, clicktargetfinder):
		CustomWidget.__init__(self, parent)

		widget = self.addWidget('Settings', acquisition,
															('Presets', 'Preset Names'), True)
		self.arrangeEntry(widget, 20, Tkinter.LEFT, False)
		widget = self.addWidget('Settings', acquisition,
															('Preferences', 'TEM Parameter'), True)
		self.arrangeCombobox(widget, 'Positioning Method', False)
		widget = self.addWidget('Settings', acquisition,
															('Preferences', 'Acquisition Type'), True)
		self.arrangeCombobox(widget, None, False)

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

	def addNodeInfo(self, key, name, classname, dependencies=[]):
		self.nodeinfo[key] = {}
		self.nodeinfo[key]['name'] = name
		self.nodeinfo[key]['class name'] = classname
		self.nodeinfo[key]['dependencies'] = dependencies

	def initialize(self):
		ids = []
		for node in self.nodeinfo:
			self.nodeinfo[node]['ID'] = self.manager.launchNode(self.launcherid, 0,
																						self.nodeinfo[node]['class name'],
																						self.nodeinfo[node]['name'],
																						(),
																						self.nodeinfo[node]['dependencies'])
			ids.append(self.nodeinfo[node]['ID'])

		if ids:
			self.manager.waitNodes(ids)

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
				server = nodegui.Server(('Custom Widget Server',), None)
				uiclient = interface.Client(hostname, uiport, server)
				return {'client': uiclient, 'hostname': hostname,
								'UI port': uiport, 'server': server}
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
																	nodelocations[node]['UI port'],
																	None, True, True)
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
		self.widget.setnaturalsize()

	def addDebugTab(self, name, ui_info):
		if self.widget is not None:
			page = self.widget.add(name)
			gui = nodegui.NodeGUI(page, ui_info['hostname'],
																	ui_info['UI port'], None, True, True)
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

class ImageCorrection(WidgetWrapper):
	def __init__(self, manager, manageruiclient, launcherid, notebook,
																			debug, windowmenu, name):
		WidgetWrapper.__init__(self, manager, manageruiclient, launcherid,
														notebook, debug, windowmenu, name)
		self.addNodeInfo('corrector', self.name + ' Corrector', 'Corrector')
		self.initialize()

	def initializeWidget(self):
		self.widget = ImageCorrectionWidget(self.page,
															self.nodeinfo['corrector']['UI info'])

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
												self.nodeinfo['gridpreview']['UI info'],
												self.nodeinfo['stateimagemosaic']['UI info'])

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
		self.widget = TargetWidget(self.page, self.nodeinfo['acquire']['UI info'],
																					self.nodeinfo['target']['UI info'])

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

