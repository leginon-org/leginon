#!/usr/bin/env python

import threading
import leginonobject
import datahandler
import node
import data
import common
import event
import signal

class Manager(node.Node):
	def __init__(self, id):
		# the id is manager (in a list)
		node.Node.__init__(self, id, None)

		self.common = common
		self.distmap = {}

		## this makes every received event get distributed
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)

		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)

		self.addEventInput(event.Event, self.distribute)

		#self.start()

	def main(self):
		pass

	def start(self):
		print self.location()
		interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		interact_thread.join()
		self.exit()

	def exit(self):
		self.server.exit()

	def nodeID(self, name):
		'return an id for a new node'
		return self.id + (name,)

	def addLauncher(self, nodeid):
		self.launcherlist.append(nodeid[-1])
		self.launcherdict[nodeid[-1]] = nodeid

	def delLauncher(self, nodeid):
		try:
			self.launcherlist.remove(nodeid[-1])
			del self.launcherdict[nodeid[-1]]
		except:
			pass

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

		# check if new node is launcher
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.addLauncher(nodeid)

	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

		# also remove from launcher registry
		self.delLauncher(nodeid)

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


	def defineUserInterface(self):
		self.ui_nodes = {}
		self.ui_launchers = {}

		self.ui_eventclasses = event.eventClasses()
		self.ui_nodeclasses = common.nodeClasses()

		eventclass_list = self.ui_eventclasses.keys()
		nodeclass_list = self.ui_nodeclasses.keys()
		self.launcherlist = []
		self.launcherdict = {}

		self.uiserver.RegisterMethod(self.uiGetID, (), 'id')

		argspec = (
			{'name':'name', 'type':'string'},
			{'name':'launcher_str', 'type':self.launcherlist},
			{'name':'nodeclass_str', 'type':nodeclass_list},
			{'name':'args', 'type':'string', 'default':''},
			{'name':'newproc', 'type':'boolean', 'default':False}
			)
		self.uiserver.RegisterMethod(self.uiLaunch, argspec, 'launch')

		argspec = (
			{'name':'eventclass_str', 'type':eventclass_list},
			{'name':'fromnode_str', 'type':self.clientlist},
			{'name':'tonode_str', 'type':self.clientlist}
			)
		self.uiserver.RegisterMethod(self.uiAddDistmap, argspec, 'bind')

	def uiGetID(self):
		return self.id

	def uiLaunch(self, name, launcher_str, nodeclass_str, args, newproc):
		"interface to the launchNode method"

		launcher_id = self.launcherdict[launcher_str]
		nodeclass = self.ui_nodeclasses[nodeclass_str]

		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher_id, newproc, nodeclass, name, args)

		## just to make xmlrpc happy
		return ''

	def uiAddDistmap(self, eventclass_str, fromnode_str, tonode_str):
		eventclass = self.ui_eventclasses[eventclass_str]
		fromnode_id = self.clientdict[fromnode_str]
		tonode_id = self.clientdict[tonode_str]
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)

		## just to make xmlrpc happy
		return ''


if __name__ == '__main__':
	import signal, sys

	manager_id = ('manager',)
	m = Manager(manager_id)

	## GUI
	gui = 1
	if gui:
		import managergui
		import Tkinter
		hostname = m.location()['hostname']
		port = m.location()['UI port']
		tk = Tkinter.Tk()
		mgui = managergui.ManagerGUI(tk, hostname, port)
		mgui.pack()
		t = threading.Thread(name = 'Tk GUI thread', target = tk.mainloop)
		t.setDaemon(1)
		t.start()
	## interact interface (could be changed to use ui* methods, like GUI)
	m.start()
