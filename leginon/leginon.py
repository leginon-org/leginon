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
		nodelocations = self.nodeLocations()
		for node in nodelocations:
			page = self.notebook.add(eval(node)[-1])
			gui = nodegui.NodeGUI(page, nodelocations[node]['hostname'],
																	nodelocations[node]['UI port'], None, True)
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
		gridatlaspage = self.notebook.add('Grid Atlas')
		gridatlaswidget = GridAtlasWidget(gridatlaspage,
														self.nodeLocation('Grid Atlas Grid Preview'),
														self.nodeLocation('Grid Atlas State Image Mosaic'),
														self.nodeLocation('Grid Atlas Mosaic Navigator'),
														self.nodeLocation('Grid Atlas Image Viewer'))
		gridatlaswidget.pack()

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

# maybe the widgets themselves could launch the necessary nodes
class GridAtlasWidget(CustomWidget):
	def __init__(self, parent, gridpreview, stateimagemosaic, mosaicnavigator,
																																	imageviewer):
		CustomWidget.__init__(self, parent)

		self.uiClient('GP', gridpreview)
		self.uiClient('SIM', stateimagemosaic)
		self.uiClient('MN', mosaicnavigator)
		self.uiClient('IV', imageviewer)

		# Grid Preview
		frame = Pmw.LabeledWidget(self, labelpos = 'nw',
															label_text = 'Grid Preview')

		# settings
		settingsframe = Pmw.LabeledWidget(frame.interior(), labelpos = 'nw',
															label_text = 'Settings')
		settingsframe.component('hull')['bd'] = 1
		settingsframe.component('hull')['relief'] = Tkinter.SOLID
		settingsframe.grid(row = 0, column = 0, padx = 10, pady = 10)

		# control
		controlframe = Pmw.LabeledWidget(frame.interior(), labelpos = 'nw',
															label_text = 'Control')
		controlframe.component('hull')['bd'] = 1
		controlframe.component('hull')['relief'] = Tkinter.SOLID
		widget = self.widgetFromName(controlframe.interior(), 'GP', ('Controls', 'Run'))
		widget.grid(row = 0, column = 0, padx = 5, pady = 5)
		widget = self.widgetFromName(controlframe.interior(), 'GP', ('Controls', 'Stop'))
		widget.grid(row = 0, column = 1, padx = 5, pady = 5)
		widget = self.widgetFromName(controlframe.interior(), 'GP', ('Controls', 'Reset'))
		widget.grid(row = 0, column = 2, padx = 5, pady = 5)
		controlframe.grid(row = 1, column = 0, padx = 10, pady = 10)

		frame.grid(row = 0, column = 0, padx = 10, pady = 10)

		# State Mosaic Image
		frame = Pmw.LabeledWidget(self, labelpos = 'nw',
															label_text = 'State Image Mosaic')
		# settings
		settingsframe = Pmw.LabeledWidget(frame.interior(), labelpos = 'nw',
															label_text = 'Settings')
		settingsframe.component('hull')['bd'] = 1
		settingsframe.component('hull')['relief'] = Tkinter.SOLID
		widget = self.widgetFromName(settingsframe.interior(), 'SIM',
																	('Scale', 'Auto Scale'))
		widget.entry['width'] = 4
		widget.entry['justify'] = Tkinter.RIGHT
		widget.entry.grid(row = 0, column = 1, padx = 5, pady = 5, columnspan = 1)
		widget.getbutton.grid(row = 0, column = 2, padx = 5, pady = 5)
		widget.setbutton.grid(row = 0, column = 3, padx = 5, pady = 5)
		widget.grid(row = 0, column = 0, padx = 5, pady = 5)

		settingsframe.grid(row = 0, column = 0, padx = 10, pady = 10)

		# control
		controlframe = Pmw.LabeledWidget(frame.interior(), labelpos = 'nw',
															label_text = 'Control')
		controlframe.component('hull')['bd'] = 1
		controlframe.component('hull')['relief'] = Tkinter.SOLID
		widget = self.widgetFromName(controlframe.interior(), 'SIM',
																	('Image', 'Publish Image'))
		widget.grid(row = 0, column = 0, padx = 5, pady = 5)
		controlframe.grid(row = 1, column = 0, padx = 10, pady = 10)

		frame.grid(row = 1, column = 0, padx = 10, pady = 10)

		# data (Mosaic Image)
		frame = Tkinter.Frame(self, bd=1, relief=Tkinter.SOLID)
		widget = self.widgetFromName(frame, 'SIM', ['Mosaic Image'])
		widget.pack()
		frame.grid(row = 0, column = 1, rowspan = 2, padx = 10, pady = 10)

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

