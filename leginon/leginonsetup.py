#!/usr/bin/env python
import Tkinter
import sys
import os
import manager
import launcher
import time
import socket

wraplength = 300
defaultlauncherport = 55555

class Wizard(Tkinter.Toplevel):
	def __init__(self, parent, title=None):
		Tkinter.Toplevel.__init__(self, parent)
		self.transient(parent)
		if title is not None:
			self.title(title)

		buttonframe = Tkinter.Frame(self)

		self.backbutton = Tkinter.Button(buttonframe, text='< Back')
		self.backbutton.grid(row=0, column=0, padx=5, pady=5)
		self.backbutton['state'] = Tkinter.DISABLED

		self.nextbutton = Tkinter.Button(buttonframe, text='Next >')
		self.nextbutton.grid(row=0, column=1, padx=5, pady=5)
		self.backbutton['state'] = Tkinter.DISABLED

		self.cancelbutton = Tkinter.Button(buttonframe, text='Cancel')
		self.cancelbutton.grid(row=0, column=2, padx=5, pady=5)
		self.backbutton['state'] = Tkinter.DISABLED

		buttonframe.grid(row=1, column=0, sticky=Tkinter.E)

		self.widget = None

		if parent is not None:
			self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
																parent.winfo_rooty()+50))
		self.focus_set()

	def setWidget(self, widget, back=None, next=None, cancel=None):
		self.unsetWidget()

		self.widget = widget

		if back is not None:
			self.backbutton['state'] = Tkinter.NORMAL
		else:
			self.backbutton['state'] = Tkinter.DISABLED
		self.backbutton['command'] = back

		if next is not None:
			self.nextbutton['state'] = Tkinter.NORMAL
		else:
			self.nextbutton['state'] = Tkinter.DISABLED
		self.nextbutton['command'] = next

		if cancel is not None:
			self.cancelbutton['state'] = Tkinter.NORMAL
		else:
			self.cancelbutton['state'] = Tkinter.DISABLED
		self.cancelbutton['command'] = cancel

		self.widget.grid(row=0, column=0, padx=15, pady=15)

	def unsetWidget(self):
		self.backbutton['state'] = Tkinter.DISABLED
		self.nextbutton['state'] = Tkinter.DISABLED
		self.cancelbutton['state'] = Tkinter.DISABLED
		if self.widget is not None:
			self.widget.grid_forget()
			self.widget = None

# needs validation of port as int
class HostnamePortWidget(Tkinter.Frame):
	def __init__(self, parent, instructions=None, hostname=None, port=None):
		Tkinter.Frame.__init__(self, parent)

		if instructions is not None:
			self.instructionslabel = Tkinter.Label(self, text=instructions,
																	wraplength=wraplength, justify=Tkinter.LEFT)
			self.instructionslabel.grid(row=0, column=0, columnspan=2,
															sticky=Tkinter.W+Tkinter.N+Tkinter.S)

		if hostname is not None:
			self.hostnamelabel = Tkinter.Label(self, text='Hostname:')
			self.hostnamelabel.grid(row=1, column=0, sticky=Tkinter.E)

			self.hostnameentry = Tkinter.Entry(self)
			self.setHostname(hostname)
			self.hostnameentry.grid(row=1, column=1, stick=Tkinter.W)

		if port is not None:
			self.portlabel = Tkinter.Label(self, text='Port:')
			self.portlabel.grid(row=2, column=0, sticky=Tkinter.E)

			self.portentry = Tkinter.Entry(self)
			self.setPort(port)
			self.portentry.grid(row=2, column=1, stick=Tkinter.W)

	def setHostname(self, hostname):
		self.hostnameentry.delete(0, Tkinter.END)
		self.hostnameentry.insert(Tkinter.END, hostname)

	def setPort(self, port):
		self.portentry.delete(0, Tkinter.END)
		self.portentry.insert(Tkinter.END, str(port))

	def setHostnamePort(self, hostnameport):
		self.setHostname(hostnameport[0])
		self.setPort(hostnameport[1])

	def getHostname(self):
		hostname = self.hostnameentry.get()
		if hostname == '':
			return None
		else:
			return hostname

	def getPort(self):
		try:
			return int(self.portentry.get())
		except (TypeError, ValueError):
			return None

	def getHostnamePort(self):
		hostname = self.getHostname()
		port = self.getPort()
		if hostname is None or port is None:
			return None
		else:
			return (hostname, port)

class LauncherSetupWidget(Tkinter.Frame):
	def __init__(self, parent, hostname=None, port=None):
		Tkinter.Frame.__init__(self, parent)

		instructions = 'If the microcope is connected to a different computer check the box labeled \'Use remote microscope\' and follow the instructions. Click \'Next\' to continue setup.'

		instructionslabel = Tkinter.Label(self, text=instructions,
																	wraplength=wraplength, justify=Tkinter.LEFT)
		instructionslabel.grid(row=0, column=0, columnspan=2)

		self.useremotevariable = Tkinter.IntVar()
		useremotecheckbutton = Tkinter.Checkbutton(self,
																						text='Use remote microscope',
																						command=self.specifyLauncher,
																						variable=self.useremotevariable)
		useremotecheckbutton.grid(row=1, column=0)

		if hostname is None:
			hostname = ''
		if port is None:
			port = defaultlauncherport
		remoteinstructions = 'Please make sure \'Remote Leginon Server\' is running on the computer connected to the microscope. Then enter the hostname of the machine below.'
		self.hostnameportwidget = HostnamePortWidget(self, remoteinstructions,
																									hostname, port)

		self.hostnameportwidget.portlabel.grid_forget()
		self.hostnameportwidget.portentry.grid_forget()

		editportinstructions = 'Check the check box below if you wish to specify a port other than the default for \'Remote Leginon Server\'.'
		editportlabel = Tkinter.Label(self.hostnameportwidget,
																	text=editportinstructions,
																	wraplength=wraplength,
																	justify=Tkinter.LEFT)
		editportlabel.grid(row=2, column=0, columnspan=2)

		self.editportvariable = Tkinter.IntVar()
		editportcheckbutton = Tkinter.Checkbutton(self.hostnameportwidget,
																							text='Specify port',
																							variable=self.editportvariable,
																							command=self.specifyPort)
		editportcheckbutton.grid(row=3, column=0, columnspan=2)

	def specifyLauncher(self):
		if self.useremotevariable.get():
			self.hostnameportwidget.grid(row=2, column=0)
		else:
			self.hostnameportwidget.grid_forget()

	def specifyPort(self):
		if self.editportvariable.get():
			self.hostnameportwidget.portlabel.grid(row=4, column=0, sticky=Tkinter.E)
			self.hostnameportwidget.portentry.grid(row=4, column=1, sticky=Tkinter.W)
		else:
			self.hostnameportwidget.portlabel.grid_forget()
			self.hostnameportwidget.portentry.grid_forget()

class InitialSetupWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)

#		instructions = 'Welcome to the Leginon setup wizard. This wizard will automatically start the programs neccessary for running Leginon on this computer. If the microcope is connected to a different computer check the box labeled \'Use remote microscope\'. Click \'Next\' and follow the setup instructions.'
		instructions = 'Welcome to the Leginon setup wizard. This wizard will automatically start the programs neccessary for running Leginon on this computer. If you which to specify a name to identify this session, check \'Specify session name\' and enter the session name. Click \'Next\' and follow the setup instructions.'
		instructionslabel = Tkinter.Label(self, text=instructions,
																	wraplength=wraplength, justify=Tkinter.LEFT)
		instructionslabel.grid(row=0, column=0, columnspan=2)

#		self.useremotevariable = Tkinter.IntVar()
#		useremotecheckbutton = Tkinter.Checkbutton(self,
#																						text='Use remote microscope',
#																						variable=self.useremotevariable)
#		useremotecheckbutton.grid(row=1, column=0)

		self.sessionlabel = Tkinter.Label(self, text='Session name:')
		self.sessionentry = Tkinter.Entry(self)

		self.editsessionvariable = Tkinter.IntVar()
		editsessioncheckbutton = Tkinter.Checkbutton(self,
																			text='Specify session name',
																			command=self.specifySession,
																			variable=self.editsessionvariable)
		editsessioncheckbutton.grid(row=1, column=0, columnspan=2)

	def specifySession(self):
		if self.editsessionvariable.get():
			self.sessionlabel.grid(row=2, column=0, sticky=Tkinter.E)
			self.sessionentry.grid(row=2, column=1, sticky=Tkinter.W)
		else:
			self.sessionlabel.grid_forget()
			self.sessionentry.grid_forget()

	def getSession(self):
		session = self.sessionentry.get()
		if self.editsessionvariable and session != '':
			return session
		else:
			return None

# Wizard needs to be a bit better, list of widgets for back and next
class StartWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		instructions = 'Leginon setup is complete. Click \'Next\' to initialize Leginon'
		instructionslabel = Tkinter.Label(self, text=instructions,
																	wraplength=wraplength, justify=Tkinter.LEFT)
		instructionslabel.grid(row=0, column=0)

class RunWidget(Tkinter.Frame):
	def __init__(self, parent):
		Tkinter.Frame.__init__(self, parent)
		self.instructionsvariable = Tkinter.StringVar()
		self.instructionsvariable.set('')
		instructionslabel = Tkinter.Label(self,
																	textvariable=self.instructionsvariable,
																	wraplength=wraplength, justify=Tkinter.LEFT)
		
		instructionslabel.grid(row=0, column=0)

	def run(self, session, remotelaunchers):
		self.startManager(session)

		# needs to be execptions
		for launcher in remotelaunchers:
			if not self.addNode(launcher[0], launcher[1]):
				return False

		locallauncher = self.startLocalLauncher()
		if locallauncher is None:
			return False

		if not self.addNode(locallauncher[0], locallauncher[1]):
			return False

		self.instructionsvariable.set('Leginon has initialized successfully, click \'Start\' to run Leginon.')
		return True

	def addNode(self, hostname, port, id=None, attempts=10):
		if id is None:
			id = (hostname,)
		if attempts < 1:
			while id not in self.manager.clients:
				try:
					self.manager.addNode(hostname, port)
				except:
					time.sleep(0.25)
		else:
			for i in range(attempts):
				try:
					self.manager.addNode(hostname, port)
					if id in self.manager.clients:
						break
				except:
					time.sleep(0.25)

		# should be exception
		if id in self.manager.clients:
			return True
		else:
			self.stopManager()
			self.instructionsvariable.set('Unable to initialize Leginon, please make sure the configuration entered is correct and try again.')
			return False

	def startManager(self, session=None):
		# will set to member of main application
		if session is None:
			self.manager = manager.Manager(('manager',), time.ctime())
		else:
			self.manager = manager.Manager(('manager',), session)

	def stopManager(self):
		del self.manager
		self.manager = None

	def startLocalLauncher(self):
#		launcherpath = '\\\\colossus\\amishare\\suloway\\pyleginon\\launcher.py'
		launcherpath = '\\\\colossus\\amishare\\suloway\\pyleginon\\launcher.py'

		if sys.platform == 'win32':
			process = os.spawnv(os.P_NOWAIT, 'C:\\Python22\\python.exe',
								['launcher.py', launcherpath])
		else:
			process = os.spawnv(os.P_NOWAIT, 'launcher.py', ['launcher.py'])

#		self.locallauncherprocess = process

		return (socket.gethostname(), defaultlauncherport)

class SetupWizard(Wizard):
	def __init__(self, parent):
		Wizard.__init__(self, parent, 'Setup Wizard')
		self.manager = None
		self.remotelauncher = None
		self.initialsetupwidget = InitialSetupWidget(self)
		self.launchersetupwidget = LauncherSetupWidget(self)
		self.startwidget = StartWidget(self)
		self.runwidget = RunWidget(self)
		self.initialSetup()

		self.wait_window(self)

	def initialSetup(self):
		self.setWidget(self.initialsetupwidget, None,
										self.launcherSetup, self.destroy)

	def launcherSetup(self):
		self.setWidget(self.launchersetupwidget, self.initialSetup,
										self.startSetup, self.destroy)

	def startSetup(self):
		self.setWidget(self.startwidget, self.launcherSetup,
										self.finishSetup, self.destroy)

	def finishSetup(self):
		session = self.initialsetupwidget.getSession()
		launcher = self.launchersetupwidget.hostnameportwidget.getHostnamePort()
		if launcher is None:
			launchers = []
		else:
			launchers = [launcher]

		if self.runwidget.run(session, launchers):
			self.setWidget(self.runwidget, None, self.destroy, None)
			self.manager = self.runwidget.manager
			if launcher is not None:
				self.remotelauncher = (launcher[0],)
			self.nextbutton['text'] = 'Start'
		else:
			self.setWidget(self.runwidget, self.startSetup, None, self.destroy)

