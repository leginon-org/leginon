#!/usr/bin/env python
import Tkinter
import socket
import leginonsetup
import EM
import Pmw
import interface
import nodegui
import threading

applicationfilename = 'leginon.app'

class Leginon(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		self.uiclients = {}
		self.notebook = Pmw.NoteBook(self)
		self.notebook.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

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

		locallauncherid = self.localLauncherID()
		replaceargs = {}
		for args in self.manager.app.launchspec:
			if args[2] == 'EM' and self.remotelauncher is not None:
				newlauncherid = self.remotelauncher
			else:
				newlauncherid = locallauncherid

			if args[0] != newlauncherid: 
				replaceargs[args] = (newlauncherid,) + args[1:]

		for args in replaceargs:
			self.manager.app.delLaunchSpec(args)
			self.manager.app.addLaunchSpec(replaceargs[args])

		self.manager.app.launch()

	def startGUI(self):
		managerlocation = self.managerLocation()
		self.uiclients['manager'] = interface.Client(managerlocation[0],
																									managerlocation[1])
#		nodelocations = self.nodeLocations()
#		for node in nodelocations:
#			page = self.notebook.add(eval(node)[-1])
#			gui = nodegui.NodeGUI(page, nodelocations[node]['hostname'],
#																	nodelocations[node]['UI port'], None, True)
#			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
		gridatlaspage = self.notebook.add('Grid Atlas')
		gridatlaswidget = GridAtlasWidget(gridatlaspage,
														self.nodeLocation('Grid Atlas Grid Preview'),
														self.nodeLocation('Grid Atlas State Image Mosaic'),
														self.nodeLocation('Grid Atlas Mosaic Navigator'),
														self.nodeLocation('Grid Atlas Image Viewer'))
		gridatlaswidget.pack()
		self.notebook.setnaturalsize()

	def nodeLocations(self):
		try:
			return self.uiclients['manager'].execute('getNodeLocations')
		except:
			return {}

	def nodeLocation(self, name):
		nodelocations = self.nodeLocations()
		# not kosher
		try:
			return nodelocations[str(('manager', name))]
		except KeyError:
			return None

	def managerLocation(self):
		managerlocation = self.manager.location()
		return (managerlocation['hostname'], managerlocation['UI port'])

	def localLauncherID(self):
		return (socket.gethostname(),)

class CustomWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		self.uiclients = {}
		self.groups = {}

	def uiClient(self, uiclientname, uiclientlocation):
		self.uiclients[uiclientname] = interface.Client(
										uiclientlocation['hostname'], uiclientlocation['UI port'])

	def widgetFromName(self, parent, uiclientname, name):
		widget = None
		spec = self.uiclients[uiclientname].getSpec()
		return self.widgetFrom(parent, uiclientname, spec, name)

	def widgetFrom(self, parent, uiclientname, spec, name):
		content = spec['content']
		for subspec in content:
			if subspec['name'] == name[0]:
				if len(name) == 1:
					return nodegui.widgetFromSpec(parent, self.uiclients[uiclientname],
																															subspec, False)
				else:
					return self.widgetFrom(parent, uiclientname, subspec, name[1:])

	def arrangeEntry(self, widget, width = 10):
		widget.entry['width'] = width
		widget.entry['justify'] = Tkinter.RIGHT
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
	def __init__(self, parent, gridpreview, stateimagemosaic, mosaicnavigator,
																																	imageviewer):
		CustomWidget.__init__(self, parent)

		self.uiClient('Grid Preview', gridpreview)
		self.uiClient('State Image Mosaic', stateimagemosaic)
#		self.uiClient('MN', mosaicnavigator)
#		self.uiClient('IV', imageviewer)

		widget = self.addWidget('Settings', 'Grid Preview',
														('Preferences', 'Magnification'))
		self.arrangeEntry(widget, 9)
		widget = self.addWidget('Settings', 'State Image Mosaic',
																			('Scale', 'Auto Scale'))
		self.arrangeEntry(widget, 4)

		self.addWidget('Control', 'Grid Preview', ('Controls', 'Run'))
		self.addWidget('Control', 'Grid Preview', ('Controls', 'Stop'))
		self.addWidget('Control', 'Grid Preview', ('Controls', 'Reset'))
#		self.addWidget('Control', 'State Image Mosaic', ('Image', 'Publish Image'))

		self.addWidget('Image', 'State Image Mosaic', ('Mosaic Image',))

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

