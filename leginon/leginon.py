#!/usr/bin/env python
import Tkinter
import leginonsetup

class Leginon(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		setupwizard = leginonsetup.SetupWizard(self)
		self.manager = setupwizard.manager

if __name__ == '__main__':

	root = Tkinter.Tk()
	root.wm_title('Leginon')
	ui = Leginon(root)
	ui.pack()
	root.mainloop()

