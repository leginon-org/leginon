#!/usr/bin/env python
import socket
import time
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
		self.sourceslistbox = Tkinter.Listbox(master)
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
		self.choiceslistbox = Tkinter.Listbox(master)
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
		Tkinter.Frame.__init__(self, parent)
		self.uiclients = {}
		self.acquireandtargets = {}
		self.notebook = Pmw.NoteBook(self)
		self.notebook.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

		self.menu = Tkinter.Menu(parent, tearoff=0)
		parent.config(menu = self.menu)

		self.editmenu = Tkinter.Menu(self.menu, tearoff=0)
		self.menu.add_cascade(label='Edit', menu=self.editmenu)
		self.editmenu.add_command(label='Add...', command=self.add)

	def add(self):
		# Grid Atlas in there for now
		name = 'Acquire and Target #%s' % str(len(self.acquireandtargets))
		add_dialog = AddChoicesDialog(self, name, self.acquireandtargets.keys(), [])
		if add_dialog.result is not None:
			sourceids = []
			for source in add_dialog.result[1]:
				sourceids.append(self.acquireandtargets[source].targetid)
			print sourceids
			self.addAcquireAndTarget(add_dialog.result[0], sourceids)

	# needs to check what got started, the whole lot needs error handling
	def start(self):
		setupwizard = leginonsetup.SetupWizard(self)
		self.manager = setupwizard.manager
		self.remotelauncher = setupwizard.remotelauncher
		if self.manager is None:
			return
		self.startApplication()
		self.startGUI()

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

	def startGUI(self):
		managerlocation = self.managerLocation()
		self.uiclients[('manager',)] = interface.Client(managerlocation[0],
																										managerlocation[1])
#		nodelocations = self.nodeLocations()
#		for node in nodelocations:
#			page = self.notebook.add(eval(node)[-1])
#			gui = nodegui.NodeGUI(page, nodelocations[node]['hostname'],
#																	nodelocations[node]['UI port'], None, True)
#			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

		gridatlaspage = self.notebook.add('Grid Atlas')
		gridatlaswidget = GridAtlasWidget(gridatlaspage,
										self.uiClient(('manager', 'Grid Atlas Grid Preview')),
										self.uiClient(('manager', 'Grid Atlas State Image Mosaic')),
										('manager', 'Grid Atlas State Image Mosaic'))
		gridatlaswidget.pack()

		self.acquireandtargets['Grid Atlas'] = gridatlaswidget
		self.notebook.setnaturalsize()

	def nodeLocations(self):
		try:
			return self.uiclients[('manager',)].execute('getNodeLocations')
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

	def addAcquireAndTarget(self, name, sourceids=[]):
		acquirename = name + ' Acquisition'
		targetname = name + ' Click Target Finder'
		acquireid = self.manager.launchNode(self.locallauncherid, 0,
																				'Acquisition', acquirename)
		targetid = self.manager.launchNode(self.locallauncherid, 0,
																				'ClickTargetFinder', targetname)
		self.manager.addEventDistmap(event.CameraImagePublishEvent,
																						acquireid, targetid)
		for nodeid in sourceids:
			self.manager.addEventDistmap(event.ImageTargetListPublishEvent,
																										nodeid, acquireid)
		page = self.notebook.add(name)
		self.acquireandtargets[name] = AcquireAndTargetWidget(page,
																									self.uiClient(acquireid),
																									self.uiClient(targetid),
																									targetid)
		self.acquireandtargets[name].pack()
		self.notebook.setnaturalsize()

class CustomWidget(Tkinter.Frame):
	def __init__(self, parent, ):
		Tkinter.Frame.__init__(self, parent)
		self.uiclients = {}
		self.groups = {}


	def widgetFromName(self, parent, uiclient, name):
		widget = None
		spec = uiclient.getSpec()
		return self.widgetFrom(parent, uiclient, spec, name)

	def widgetFrom(self, parent, uiclient, spec, name):
		content = spec['content']
		for subspec in content:
			if subspec['name'] == name[0]:
				if len(name) == 1:
					return nodegui.widgetFromSpec(parent, uiclient, subspec, False)
				else:
					return self.widgetFrom(parent, uiclient, subspec, name[1:])

	# kwargs
	def arrangeEntry(self, widget, width = 10, justify = Tkinter.RIGHT):
		widget.entry['width'] = width
		widget.entry['justify'] = justify
		widget.entry.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
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

# maybe the widgets themselves could launch the necessary nodes
class GridAtlasWidget(CustomWidget):
	def __init__(self, parent, gridpreview, stateimagemosaic, targetid):
		CustomWidget.__init__(self, parent)

		self.targetid = targetid

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

class AcquireAndTargetWidget(CustomWidget):
	def __init__(self, parent, acquisition, clicktargetfinder, targetid):
		CustomWidget.__init__(self, parent)

		self.targetid = targetid

		widget = self.addWidget('Settings', acquisition,
															('Preferences', 'Preset Names'))
		self.arrangeEntry(widget, 20, Tkinter.LEFT)
		self.addWidget('Image', clicktargetfinder, ('Clickable Image',))

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

