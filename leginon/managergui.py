
from Tkinter import *
import Pmw
import xmlrpclib

class ManagerGUI(Frame):
	def __init__(self, parent, managerobject=None, host=None, port=None):
		Frame.__init__(self, parent)
		if managerobject:
			self.manager = managerobject
		elif host and port:
			uri = 'http://%s:%s' % (host, port)
			self.manager = xmlrpclib.ServerProxy(uri)
		else:
			raise RuntimeError('specify either managerobject or host and port')

		self.build_it()

	def update_all(self):
		self.update_launcherlist()
		self.update_nodelists()
		self.update_eventclasslist()
		self.update_nodeclasslist()

	def update_launcherlist(self):
		launcherlist = self.manager.uiGetInfo('launchers')
		self.gui_launcherlist.setlist(launcherlist)
	def update_nodelists(self):
		nodelist = self.manager.uiGetInfo('nodes')
		self.gui_fromnodelist.setlist(nodelist)
		self.gui_tonodelist.setlist(nodelist)
	def update_eventclasslist(self):
		eventclasslist = self.manager.uiGetInfo('eventclasses')
		self.gui_eventclasslist.setlist(eventclasslist)
	def update_nodeclasslist(self):
		nodeclasslist = self.manager.uiGetInfo('nodeclasses')
		self.gui_nodeclasslist.setlist(nodeclasslist)


	def launch(self):
		'button callback'
		name = self.gui_launch_name.get()
		launcher_str = self.gui_launcherlist.get()
		nodeclass_str = self.gui_nodeclasslist.get()
		args = self.gui_launch_args.get()
		newproc = self.gui_launch_newproc.get()
		self.manager.uiLaunch(name, launcher_str, nodeclass_str, args, newproc)

	def addDistmap(self):
		'button callback'
		eventclass_str = self.gui_eventclasslist.get()
		fromnode_str = self.gui_fromnodelist.get()
		tonode_str = self.gui_tonodelist.get()
		self.manager.uiAddDistmap(eventclass_str, fromnode_str, tonode_str)

	def build_it(self):
		"""
		open a GUI for the manager	
		"""

		root = Frame(self)

		######################
		#### Launch Node Frame
		self.gui_launch_newproc = IntVar()
		self.gui_launch_name = StringVar()
		self.gui_launch_args = StringVar()

		launch_frame = Frame(root, relief=RAISED, bd=3)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Name')
		ent = Entry(f, textvariable=self.gui_launch_name)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Launcher ID')
		self.gui_launcherlist = Pmw.ComboBox(f)
		lab.pack(side=LEFT)
		self.gui_launcherlist.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Class')
		self.gui_nodeclasslist = Pmw.ComboBox(f)
		lab.pack(side=LEFT)
		self.gui_nodeclasslist.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Args')
		ent = Entry(f, textvariable=self.gui_launch_args)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		newproc = Checkbutton(launch_frame, text='New Process', variable=self.gui_launch_newproc) 
		newproc.pack(side=TOP)

		launch_but = Button(launch_frame, text='Launch')
		launch_but['command'] = self.launch
		launch_but.pack(side=TOP)

		launch_frame.pack(side=LEFT)

		####################
		##### Event Frame

		event_frame = Frame(root, relief=RAISED, bd=3)

		f = Frame(event_frame)
		lab = Label(f, text='Event Type')
		self.gui_eventclasslist = Pmw.ComboBox(f)
		lab.pack(side=LEFT)
		self.gui_eventclasslist.pack(side=LEFT)
		f.pack(side=TOP)



		f = Frame(event_frame)
		lab = Label(f, text='From Node')
		self.gui_fromnodelist = Pmw.ComboBox(f)
		lab.pack(side=LEFT)
		self.gui_fromnodelist.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(event_frame)
		lab = Label(f, text='To Node')
		self.gui_tonodelist = Pmw.ComboBox(f)
		lab.pack(side=LEFT)
		self.gui_tonodelist.pack(side=LEFT)
		f.pack(side=TOP)

		addevent_but = Button(event_frame, text='Add Event Distmap')
		addevent_but['command'] = self.addDistmap
		addevent_but.pack(side=TOP)

		event_frame.pack(side=TOP)

		##########
		### other
		update_but = Button(root, text='REFRESH', command=self.update_all)
		update_but.pack(side=TOP, expand=YES)

		self.update_all()

		root.pack()



