#!/usr/bin/env python
import Tkinter
import socket
import leginonsetup
import EM

applicationfilename = 'leginon.app'

class Leginon(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		setupwizard = leginonsetup.SetupWizard(self)
		self.manager = setupwizard.manager
		self.remotelauncher = setupwizard.remotelauncher
		self.runApplication()
		print 'done.'

	def runApplication(self):
		if self.manager is None:
			return

		self.manager.app.load(applicationfilename)

		locallauncherid = self.localLauncherID()
		replaceargs = {}
		for args in self.manager.app.launchspec:
			if args[2] == EM.EM and self.remotelauncher is not None:
				newlauncherid = self.remotelauncher
			else:
				newlauncherid = locallauncherid

			if args[0] != newlauncherid: 
				replaceargs[args] = (newlauncherid,) + args[1:]

		for args in replaceargs:
			print args
			self.manager.app.delLaunchSpec(args)
			print replaceargs[args]
			self.manager.app.addLaunchSpec(replaceargs[args])

		self.manager.app.launch()

	def localLauncherID(self):
		return (socket.gethostname(),)

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack()
	root.mainloop()

