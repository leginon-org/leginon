#!/usr/bin/env python
import Tkinter
import socket
import leginonsetup
import EM
import Pmw
import interface
import nodegui

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
		self.startApplication()
		self.startGUI()

	def startApplication(self):
		if self.manager is None:
			return

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
			page = self.notebook.add(node)
			gui = nodegui.NodeGUI(page, nodelocations[node]['hostname'],
																	nodelocations[node]['UI port'])
			gui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)

	def nodeLocations(self):
		try:
			return self.uiclients['manager'].execute('getNodeLocations')
		except:
			return {}

	def managerLocation(self):
		managerlocation = self.manager.location()
		return (managerlocation['hostname'], managerlocation['UI port'])

	def localLauncherID(self):
		return (socket.gethostname(),)

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	ui.start()
	root.mainloop()

