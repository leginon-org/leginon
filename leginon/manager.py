#!/usr/bin/env python

from Tix import *
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
	def __init__(self, id, usegui=0):
		# the id is manager (in a list)
		node.Node.__init__(self, id, None)

		self.common = common
		self.distmap = {}

		self.gui_ok = 0
		self.usegui = usegui

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
		if self.usegui:
			self.start_gui()
		self.interact()
		self.exit()

	def exit(self):
		self.server.exit()

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

		self.gui_add_node(readyevent)


	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

	def removeNode(self, nodeid):
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata:
			self.removeNodeData(nodeid)
			self.removeNodeDistmaps(nodeid)
			self.server.datahandler.remove(nodeid)
			self.delEventClient(nodeid)
			print 'node', nodeid, 'unregistered'
		else:
			print 'node', nodeid, 'does not exist'

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

	def launchNode(self, launcher, newproc, target, name, nodeargs=()):
		manloc = self.location()
		newid = self.nodeID(name)
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

	def killNode(self, nodeid):
		self.clients[nodeid].push(event.KillEvent(self.ID()))
		self.removeNode(nodeid)

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
		self.gui_launcher_str2id = {}
		self.gui_launcherlist = ComboBox(f)
		lab.pack(side=TOP)
		self.gui_launcherlist.pack(side=TOP)
		f.pack(side=TOP)

		f = Frame(launch_frame)
		lab = Label(f, text='Node Class')
		self.gui_nodeclasslist = ComboBox(f)
		self.nodeclasses = common.nodeClasses()
		for nodeclass in self.nodeclasses:
			self.gui_nodeclasslist.insert(END, nodeclass)
		lab.pack(side=TOP)
		self.gui_nodeclasslist.pack(side=TOP)
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
		launch_but['command'] = self.gui_launch_command
		launch_but.pack(side=TOP)

		launch_frame.pack(side=LEFT)

		####################
		##### Event Frame

		event_frame = Frame(root, relief=RAISED, bd=3)

		f = Frame(event_frame)
		lab = Label(f, text='Event Type')
		self.gui_eventclasslist = ComboBox(f)
		self.eventclasses = event.eventClasses()
		for eventclass in self.eventclasses:
			self.gui_eventclasslist.insert(END, eventclass)
		lab.pack(side=TOP)
		self.gui_eventclasslist.pack(side=TOP)
		f.pack(side=TOP)


		f = Frame(event_frame)
		lab = Label(f, text='From Node')
		self.gui_fromnodelist = ComboBox(f)
		self.gui_fromnodelist_str2id = {}
		lab.pack(side=TOP)
		self.gui_fromnodelist.pack(side=TOP)
		f.pack(side=TOP)

		f = Frame(event_frame)
		lab = Label(f, text='To Node')
		self.gui_tonodelist = ComboBox(f)
		self.gui_tonodelist_str2id = {}
		lab.pack(side=TOP)
		self.gui_tonodelist.pack(side=TOP)
		f.pack(side=TOP)

		addevent_but = Button(event_frame, text='Add Event Distmap')
		addevent_but['command'] = self.gui_event_command
		addevent_but.pack(side=TOP)

		event_frame.pack(side=LEFT)

		self.gui_ok = 1
		root.mainloop()


	def gui_add_node(self, eventinst):
		if not self.gui_ok:
			return

		self.junk = eventinst
		print 'STUFF %s' % (eventinst,)
		print 'STUFF %s' % (eventinst.id,)
		print 'STUFF %s' % (eventinst.id[:-1],)
		nodeid = eventinst.id[:-1]
		str_id = str(nodeid)
		print 'nodeid %s' % (nodeid,)

		## add to the to and from node lists
		print 'HELLO'
		self.gui_fromnodelist.insert(END, str_id)
		self.gui_fromnodelist_str2id[str_id] = nodeid
		self.gui_tonodelist.insert(END, str_id)
		self.gui_tonodelist_str2id[str_id] = nodeid
		print 'BYE'

		## stuff to do if Node is a Launcher
		if isinstance(eventinst, event.LauncherAvailableEvent):
			str_id = str(nodeid)
			self.gui_launcherlist.insert(END, str_id)
			self.gui_launcher_str2id[str_id] = nodeid

	def gui_del_node(self, launcherid):
		if not self.gui_ok:
			return
		### NOT DONE YET

	def gui_launch_command(self):

		launcher_str = self.gui_launcherlist.entry.get()
		launcher_id = self.gui_launcher_str2id[launcher_str]

		newproc = self.gui_launch_newproc.get()

		target = self.gui_nodeclasslist.entry.get()
		target = self.nodeclasses[target]

		newname = self.gui_launch_name.get()

		args = self.gui_launch_args.get()
		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher_id, newproc, target, newname, args)

	def gui_event_command(self):
		eventclass = self.gui_eventclasslist.entry.get()
		eventclass = self.eventclasses[eventclass]

		fromnode_str = self.gui_fromnodelist.entry.get()
		fromnode_id = self.gui_fromnodelist_str2id[fromnode_str]

		tonode_str = self.gui_tonodelist.entry.get()
		tonode_id = self.gui_tonodelist_str2id[tonode_str]
		
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)


if __name__ == '__main__':
	import signal, sys

	manager_id = ('manager',)
	m = Manager(manager_id, usegui=1)
	#m = Manager(manager_id, usegui=0)

