#!/usr/bin/env python

import threading
import leginonobject
import datahandler
import node
import application
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
		# maps event id to list of node it was distributed to if event.confirm
		self.confirmmap = {}
		self.app = application.Application(self.ID(), self)

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
		self.print_location()
		#print self.location()
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

	def confirmEvent(self, ievent):
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id), \
				0, ievent.id[:-1])

	def registerConfirmedEvent(self, ievent):
		nodeid = ievent.content[:-1]
		if nodeid == self.id:
			# this is bad since it will fill up with lots of events
			if not ievent.content in self.confirmwaitlist:
				self.confirmwaitlist[ievent.content] = threading.Event()
				self.confirmwaitlist[ievent.content].set()
				#del self.confirmwaitlist[ievent.content]
		else:
			self.confirmmap[ievent.content].remove(ievent.id[:-1])
			if len(self.confirmmap[ievent.content]) == 0:
				del self.confirmmap[ievent.content]
				self.outputEvent(ievent, 0, nodeid)

	def addLauncher(self, nodeid):
		name = nodeid[-1]
		if name not in self.launcherlist:
			self.launcherlist.append(name)
		self.launcherdict[name] = nodeid

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
		if nodelocationdata is None:
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		else:
			# fools! should do something nifty to unregister, reregister, etc.
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		self.server.datahandler._insert(nodelocationdata)

		# check if new node is launcher
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.addLauncher(nodeid)

		self.confirmEvent(readyevent)

	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

		# also remove from launcher registry
		self.delLauncher(nodeid)

	def removeNode(self, nodeid):
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata is not None:
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
		if datalocationdata is None:
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
		if (datalocationdata is not None) and (type(datalocationdata) == data.DataLocationData):
			try:
				datalocationdata.content.remove(nodeid)
				if len(datalocationdata.content) == 0:
					self.server.datahandler.remove(dataid)
				else:
					self.server.datahandler._insert(datalocationdata)
			except ValueError:
				pass

	def launchNode(self, launcher, newproc, target, name, nodeargs=()):
		args = (launcher, newproc, target, name, nodeargs)
		self.app.addLaunchSpec(args)

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
		args = (eventclass, from_node, to_node)
		self.app.addBindSpec(args)

		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def saveApp(self, filename):
		self.app.save(filename)
		return ''

	def loadApp(self, filename):
		self.app.load(filename)
		return ''

	def launchApp(self):
		self.app.launch()
		return ''

	def distribute(self, ievent):
		'''push event to eventclients based on event class and source'''
		eventclass = ievent.__class__
		from_node = ievent.id[:-1]
		do = []
		for distclass,fromnodes in self.distmap.items():
			if issubclass(eventclass, distclass):
				for fromnode in (from_node, None):
					if fromnode in fromnodes:
						for to_node in fromnodes[from_node]:
							if to_node is not None:
								if to_node not in do:
									do.append(to_node)
							else:
								for to_node in self.handler.clients:
									if to_node not in do:
										do.append(to_node)
		if ievent.confirm:
			self.confirmmap[ievent.id] = do
		for to_node in do:
			self.clients[to_node].push(ievent)

	def print_location(self):
		loc = self.location()
		for key,value in loc.items():
			print '%-25s  %s' % (key,value)

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.ui_nodes = {}
		self.ui_launchers = {}

		self.ui_eventclasses = event.eventClasses()
		self.ui_nodeclasses = common.nodeClasses()

		eventclass_list = self.ui_eventclasses.keys()
		eventclass_list.sort()
		nodeclass_list = self.ui_nodeclasses.keys()
		nodeclass_list.sort()
		self.launcherlist = []
		self.launcherdict = {}

		test = self.registerUIData('Test', 'string', permissions='rw')

		argspec = (
		self.registerUIData('Name', 'string', permissions='rw'),
		self.registerUIData('Launcher', 'string', permissions='rw', enum=self.launcherlist),
		self.registerUIData('Node Class', 'string', permissions='rw', enum=nodeclass_list),
		self.registerUIData('Args', 'string', permissions='rw', default=''),
		self.registerUIData('New Process', 'boolean', permissions='rw', default=False)
		)

		spec1 = self.registerUIMethod(self.uiLaunch, 'Launch', argspec)

		self.registerUISpec('MANAGER', (nodespec, test, spec1))

		return

		argspec = (
			{'name':'nodename', 'alias':'Node', 'type':self.clientlist},
			)
		self.registerUIFunction(self.uiKill, argspec, 'Kill (experimental)')

		argspec = (
			{'name':'eventclass_str', 'alias':'Event Class', 'type':eventclass_list},
			{'name':'fromnode_str', 'alias':'From Node', 'type':self.clientlist},
			{'name':'tonode_str', 'alias':'To Node', 'type':self.clientlist}
			)
		self.registerUIFunction(self.uiAddDistmap, argspec, 'Bind')
		
		self.registerUIFunction(self.uiNodes, (), 'nodes', returntype='struct')
		argspec = (
			{'name':'filename', 'alias':'Filename', 'type':'string'},)
		self.registerUIFunction(self.saveApp, argspec, 'Save App')
		self.registerUIFunction(self.loadApp, argspec, 'Load App')
		self.registerUIFunction(self.launchApp, (), 'Launch App')

	def uiNodes(self):
		"""
		return a dict describing all currently managed nodes
		"""
		nodeinfo = {}
		for nodename in self.clientlist:
			nodeid = self.clientdict[nodename]
			nodelocationdata = self.server.datahandler.query(nodeid)
			if nodelocationdata is not None:
				nodeloc = nodelocationdata.content
				nodeinfo[nodename] = nodeloc	
		return nodeinfo

	def uiLaunch(self, name, launcher_str, nodeclass_str, args, newproc=0):
		"""
		user interface to the launchNode method
		This simplifies the call for a user by using a
		string to represent the launcher ID, node class, and args
		"""
		print 'LAUNCH %s,%s,%s,%s,%s' % (name, launcher_str, nodeclass_str, args, newproc)

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

	def uiKill(self, nodename):
		nodeid = self.clientdict[nodename]
		self.killNode(nodeid)

	def uiAddDistmap(self, eventclass_str, fromnode_str, tonode_str):
		"""
		a user interface to addEventDistmap
		uses strings to represent event class and node IDs
		"""
		print 'BIND %s,%s,%s' % (eventclass_str, fromnode_str, tonode_str)
		eventclass = self.ui_eventclasses[eventclass_str]
		fromnode_id = self.clientdict[fromnode_str]
		tonode_id = self.clientdict[tonode_str]
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)

		## just to make xmlrpc happy
		return ''


if __name__ == '__main__':
	import signal, sys, time

	manager_id = ('manager',)
	#manager_id = 'manager'
	m = Manager(manager_id)

	## GUI
	gui = 1
	if gui:
		import nodegui
		import Tkinter
		tk = Tkinter.Tk()
		mgui = nodegui.NodeGUI(tk, node=m)
		#tk.wm_title('Leginon Manager')
		mgui.pack()
#		t = threading.Thread(name = 'Tk GUI thread', target = tk.mainloop)
#		t.setDaemon(1)
#		t.start()
	## interact interface (could be changed to use ui* methods, like GUI)
	m.start()

