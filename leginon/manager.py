#!/usr/bin/env python

from Tkinter import *
import threading
import leginonobject
import datahandler
import node
import data
import common
import event
import signal
import os

class Manager(node.Node):
	def __init__(self, id, gui=0):
		# the id is manager (in a list)
		node.Node.__init__(self, id, None)

		self.common = common
		self.distmap = {}

		self.gui_ok = 0
		if gui:
			self.start_gui()

		## this makes every received event get distributed
		self.addEventInput(event.Event, self.distribute)
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)

		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)

		self.main()

	def main(self):
		print self.location()


		self.interact()

	def nodeID(self, name):
		'return an id for a new node'
		return self.id + (name,)

	def registerNode(self, readyevent):
		nodeid = readyevent.id[:-1]
		print 'registering node', nodeid
		nodelocation = readyevent.content

		# for the clients and mapping
		self.addEventClient(nodeid, nodelocation)
		print self.clients

		# published data of nodeid mapping to location of node
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata == None:
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		else:
			# fools! should do something nifty to unregister, reregister, etc.
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		self.server.datahandler._insert(nodelocationdata)

		## stuff to do if Node is a Launcher
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.gui_add_launcher(nodeid)

	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		print 'unregistering node', nodeid

		#print 'removing data references:'
		self.removeNodeData(nodeid)
		#print self.server.datahandler.datadict

		#print 'removing event mappings:'
		self.removeNodeDistmaps(nodeid)
		#print self.distmap

		#print 'removing node reference and client:'
		self.removeNode(nodeid)
		#print self.server.datahandler.datadict
		#print self.clients

	def removeNode(self, nodeid):
		self.server.datahandler.remove(nodeid)
		self.delEventClient(nodeid)

	def removeNodeDistmaps(self, nodeid):
		# needs to completely cleanup the distmap
		for eventclass in self.distmap:
			try:
				del self.distmap[eventclass][nodeid]
			except KeyError:
				pass
			for othernodeid in self.distmap[eventclass]:
				try:
					self.distmap[eventclass][othernodeid].remove(nodeid)
				except ValueError:
					pass

	def removeNodeData(self, nodeid):
		# terribly inefficient
		for dataid in self.server.datahandler.ids():
			self.unpublishDataLocation(dataid, nodeid)

	def registerData(self, publishevent):
		if isinstance(publishevent, event.PublishEvent):
			id = publishevent.content
			self.publishDataLocation(id, publishevent.id[:-1])
		elif isinstance(publishevent, event.ListPublishEvent):
			for id in publishevent.content:
				self.publishDataLocation(id, publishevent.id[:-1])
		else:
			raise TypeError

	# creates/appends list with nodeid of published data
	def publishDataLocation(self, dataid, nodeid):
		datalocationdata = self.server.datahandler.query(dataid)
		if datalocationdata == None:
			datalocationdata = data.DataLocationData(dataid, [nodeid])
		else:
			datalocationdata.content.append(nodeid)
		self.server.datahandler._insert(datalocationdata)

	def unregisterData(self, unpublishevent):
		if isinstance(unpublishevent, event.UnpublishEvent):
			id = unpublishevent.content
			self.unpublishDataLocation(id, unpublishevent.id[:-1])
		else:
			raise TypeError

	# creates/appends list with nodeid of published data
	def unpublishDataLocation(self, dataid, nodeid):
		datalocationdata = self.server.datahandler.query(dataid)
		if datalocationdata and (type(datalocationdata) == data.DataLocationData):
			try:
				datalocationdata.content.remove(nodeid)
				if len(datalocationdata.content) == 0:
					self.server.datahandler.remove(dataid)
				else:
					self.server.datahandler._insert(datalocationdata)
			except ValueError:
				pass

	def launchNode(self, launcher, newproc, target, newid, nodeargs=()):
		manloc = self.location()
		args = (newid, manloc) + nodeargs
		self.launch(launcher, newproc, target, args)

	def launch(self, launcher, newproc, target, args=(), kwargs={}):
		"""
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = callable object under self.common
		args, kwargs = args for callable object
		"""
		ev = event.LaunchEvent(self.ID(), newproc, target, args, kwargs)
		self.clients[launcher].push(ev)

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, ievent):
		'''push event to eventclients based on event class and source'''
		eventclass = ievent.__class__
		from_node = ievent.id[:-1]
		done = []
		for distclass,fromnodes in self.distmap.items():
			if issubclass(eventclass, distclass):
				for fromnode in (from_node, None):
					if fromnode in fromnodes:
						for to_node in fromnodes[from_node]:
							if to_node:
								if to_node not in done:
									self.clients[to_node].push(ievent)
									done.append(to_node)
							else:
								for to_node in self.handler.clients:
									if to_node not in done:
										self.clients[to_node].push(ievent)
										done.append(to_node)

	def start_gui(self):
		guithread = threading.Thread(target=self.gui)
		guithread.setDaemon(1)
		guithread.start()

	def gui(self):
		"""
		open a GUI for the manager	
		"""

		root = Tk()

		self.gui_launch_launcher = StringVar()
		self.gui_launch_target = StringVar()
		self.gui_launch_newproc = IntVar()
		self.gui_launch_name = StringVar()
		self.gui_launch_args = StringVar()

		#### Launch Node Frame
		launch_frame = Frame(root)

		launch_lab = Label(launch_frame, text='LAUNCHER')
		launch_lab.pack(side=TOP)

		f = Frame(launch_frame, relief=RAISED)
		lab = Label(f, text='Launcher ID')
		ent = Entry(f, textvariable=self.gui_launch_launcher)
		self.gui_launcherlist = Listbox(f, height=6)

		self.gui_launcherlist.bind('<Button-1>', self.gui_select_launcherid)
		self.gui_launcher_str2id = {}

		lab.grid(row=0, column=0, sticky=S)
		ent.grid(row=1, column=0, sticky=N)
		self.gui_launcherlist.grid(row=0, column=1, rowspan=2)

		f.pack(side=TOP)



		f = Frame(launch_frame)
		lab = Label(f, text='Node Class')
		ent = Entry(f, textvariable=self.gui_launch_target)
		
		self.gui_nodeclasslist = Listbox(f, height=10)
		self.gui_nodeclasslist.bind('<Button-1>', self.gui_select_nodeclass)
		## fill listbox with classes from common module
		self.nodeclasses = common.nodeClasses()
		for nodeclass in self.nodeclasses:
			self.gui_nodeclasslist.insert(END, nodeclass)

		lab.grid(row=0, column=0, sticky=S)
		ent.grid(row=1, column=0, sticky=N)
		self.gui_nodeclasslist.grid(row=0, column=1, rowspan=2)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Name')
		ent = Entry(f, textvariable=self.gui_launch_name)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Args')
		ent = Entry(f, textvariable=self.gui_launch_args)
		lab.pack(side=LEFT)
		ent.pack(side=LEFT)
		f.pack(side=TOP)

		newproc = Checkbutton(launch_frame, text='New Process', variable=self.gui_launch_newproc) 
		newproc.pack(side=TOP)

		launch_but = Button(launch_frame, text='LAUNCH')
		launch_but['command'] = self.gui_launch_command
		launch_but.pack(side=TOP)

		launch_frame.pack(side=TOP)

		self.gui_ok = 1
		root.mainloop()

	def gui_add_launcher(self, launcherid):
		if not self.gui_ok:
			return
		str_id = str(launcherid)
		self.gui_launcherlist.insert(END, str_id)
		self.gui_launcher_str2id[str_id] = launcherid

	def gui_del_launcher(self, launcherid):
		if not self.gui_ok:
			return
		### NOT DONE YET

	def gui_select_launcherid(self, guievent):
		launcherlist = self.gui_launcherlist.get(0,END)
		#launcherindex = int(self.gui_launcherlist.curselection()[0])
		launcherindex = self.gui_launcherlist.nearest(int(guievent.y))
		launcher = launcherlist[launcherindex]
		self.gui_launch_launcher.set(launcher)

	def gui_select_nodeclass(self, guievent):
		targetlist = self.gui_nodeclasslist.get(0,END)
		#targetindex = int(self.gui_nodeclasslist.curselection()[0])
		targetindex = self.gui_nodeclasslist.nearest(int(guievent.y))
		targetname = targetlist[targetindex]
		self.gui_launch_target.set(targetname)

	def gui_launch_command(self):

		launcher_str = self.gui_launch_launcher.get()
		launcher_id = self.gui_launcher_str2id[launcher_str]
		newproc = self.gui_launch_newproc.get()

		target = self.gui_launch_target.get()
		target = self.nodeclasses[target]

		newname = self.gui_launch_name.get()
		newid = self.nodeID(newname)

		args = self.gui_launch_args.get()
		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher_id, newproc, target, newid, args)


if __name__ == '__main__':
	import signal, sys

	manager_id = ('manager',)
	m = Manager(manager_id, gui=1)

