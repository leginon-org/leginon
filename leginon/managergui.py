#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface

class ManagerGUI(Frame):
	def __init__(self, parent, hostname, port):
		Frame.__init__(self, parent)
		self.uiclient = interface.Client(hostname, port)
		self.uiclient.getMethods()
		self.build_it()

	def update_all(self):
		self.uiclient.getMethods()

		launcherlist = self.uiclient.getargtype('launch','launcher_str')
		self.gui_launcherlist.setlist(launcherlist)

		nodeclasslist = self.uiclient.getargtype('launch','nodeclass_str')
		self.gui_nodeclasslist.setlist(nodeclasslist)

		fromnodelist = self.uiclient.getargtype('bind','fromnode_str')
		self.gui_fromnodelist.setlist(fromnodelist)

		tonodelist = self.uiclient.getargtype('bind','tonode_str')
		self.gui_tonodelist.setlist(tonodelist)

		eventlist = self.uiclient.getargtype('bind','eventclass_str')
		self.gui_eventclasslist.setlist(eventlist)



	def launch(self):
		'button callback'
		self.uiclient.setarg('launch','name',self.gui_launch_name.get())
		self.uiclient.setarg('launch', 'launcher_str', self.gui_launcherlist.get())
		self.uiclient.setarg('launch', 'nodeclass_str', self.gui_nodeclasslist.get())
		self.uiclient.setarg('launch', 'args', self.gui_launch_args.get())
		self.uiclient.setarg('launch', 'newproc', self.gui_launch_newproc.get())
		self.uiclient.execute('launch')

	def addDistmap(self):
		'button callback'
		self.uiclient.setarg('bind', 'eventclass_str', self.gui_eventclasslist.get())
		self.uiclient.setarg('bind', 'fromnode_str', self.gui_fromnodelist.get())
		self.uiclient.setarg('bind', 'tonode_str', self.gui_tonodelist.get())
		self.uiclient.execute('bind')

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


if __name__ == '__main__':
	
	import Tkinter, sys

	tk = Tkinter.Tk()
	mgui = ManagerGUI(tk, sys.argv[1], sys.argv[2])
	mgui.pack()
	tk.mainloop()



