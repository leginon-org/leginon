#!/usr/bin/env python

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
	def __init__(self, id):
		# the id is manager (in a list)
		node.Node.__init__(self, id, None)

		self.common = common
		self.distmap = {}

		### this initializes the "UI server"
		self.uiInit()

		## this makes every received event get distributed
		self.addEventInput(event.Event, self.distribute)
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)

		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)

		#self.start()

	def main(self):
		pass

	def start(self):
		self.startRPC()
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

		# let UI server know about the new node
		self.uiAddNode(nodeid)
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.uiAddLauncher(nodeid)

	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

		# let UI server know about unregistered node
		## NOT DONE YET

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

	### the following ui* methods could be put into a seperate class
	### and maybe one day general node ui server class

	def uiInit(self):
		self.ui_info = {}
		self.ui_info['nodeclasses'] = {}
		self.ui_info['nodes'] = {}
		self.ui_info['launchers'] = {}
		self.ui_info['eventclasses'] = {}

		self.uiUpdateEventclasses()
		self.uiUpdateNodeclasses()

	def uiGetInfo(self, key):
		return self.ui_info[key].keys()

	def uiUpdateEventclasses(self):
		self.ui_info['eventclasses'] = event.eventClasses()

	def uiUpdateNodeclasses(self):
		self.ui_info['nodeclasses'] = common.nodeClasses()

	def uiAddNode(self, node_id):
		node_str = node_id[-1]
		self.ui_info['nodes'][node_str] = node_id

	def uiAddLauncher(self, launcher_id):
		launcher_str = launcher_id[-1]
		self.ui_info['launchers'][launcher_str] = launcher_id

	def uiLaunch(self, name, launcher_str, nodeclass_str, args, newproc):
		"interface to the launchNode method"

		launcher_id = self.ui_info['launchers'][launcher_str]
		nodeclass = self.ui_info['nodeclasses'][nodeclass_str]

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
		eventclass = self.ui_info['eventclasses'][eventclass_str]
		fromnode_id = self.ui_info['nodes'][fromnode_str]
		tonode_id = self.ui_info['nodes'][tonode_str]
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)

		## just to make xmlrpc happy
		return ''


if __name__ == '__main__':
	import signal, sys
	import managergui

	manager_id = ('manager',)
	m = Manager(manager_id)
	
	## GUI
	gui = 1
	if gui:
		tk = Tk()
		mgui = managergui.ManagerGUI(tk, m)
		mgui.pack()
		t = threading.Thread(target = tk.mainloop)
		t.setDaemon(1)
		t.start()
	## interact interface (could be changed to use ui* methods, like GUI)
	m.start()
