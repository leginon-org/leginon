#!/usr/bin/env python

import threading
import leginonobject
import datahandler
import node
import application
import data
import event
import launcher

False=0
True=1

class Manager(node.Node):
	def __init__(self, id):
		# the id is manager (in a list)

		self.clients = {}

		node.Node.__init__(self, id, {})

		self.uiserver.server.register_function(self.uiGetNodeLocations,
																						'getNodeLocations')

		self.nodelocations['manager'] = self.location()

		self.distmap = {}
		# maps event id to list of node it was distributed to if event.confirm
		self.confirmmap = {}

		self.app = application.Application(self.ID(), self)

		## this makes every received event get distributed
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent,
															self.handleNodeClassesPublish)
		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)
		self.addEventInput(event.Event, self.distributeEvents)

		#self.start()

	# main/start methods

	def main(self):
		pass

	def start(self):
		self.print_location()
		interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		interact_thread.join()
		self.exit()

	def exit(self):
		self.server.exit()

	# client methods

	def addClient(self, newid, loc):
		self.clients[newid] = self.clientclass(self.ID(), loc)

	def delClient(self, newid):
		if newid in self.clients:
			del self.clients[newid]

	# event methods

	def outputEvent(self, ievent, wait, nodeid):
		try:
			self.clients[nodeid].push(ievent)
		except KeyError:
			print 'Manager: cannot output event %s to %s' % (ievent, nodeid)
			return
		if wait:
			self.waitEvent(ievent)

	def confirmEvent(self, ievent):
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id),
											0, ievent.id[:-1])

	def handleConfirmedEvent(self, ievent):
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

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		args = (eventclass, from_node, to_node)
		self.app.addBindSpec(args)

		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distributeEvents(self, ievent):
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
			try:
				self.clients[to_node].push(ievent)
			except IOError:
				print "Manager: cannot push to node %s, unregistering" % nodeid
				# group into another function
				self.removeNode(to_node)
				# also remove from launcher registry
				self.delLauncher(to_node)

	# launcher related methods

	def newLauncher(self, newid):
		print self.nodelocations
		t = threading.Thread(name='launcher thread',
								target=launcher.Launcher, args=(newid, self.nodelocations))
		t.start()

	def addLauncher(self, nodeid, location):
		name = nodeid[-1]
		self.uilauncherdict[name] = {'id':nodeid, 'location':location, 'node classes id':None}

	def delLauncher(self, nodeid):
		name = nodeid[-1]
		try:
			del self.uilauncherdict[name]
		except:
			pass
		self.updateLauncherDictDataDict()

	def getLauncherNodeClasses(self, launchername):
		dataid = self.uilauncherdict[launchername]['node classes id']
		loc = self.uilauncherdict[launchername]['location']
		launcherid = self.uilauncherdict[launchername]['id']
		try:
			nodeclassesdata = self.researchByLocation(loc, dataid)
		except IOError:
			print "Manager: cannot find launcher %s, unregistering" % launcherid
			# group into another function
			self.removeNode(launcherid)
			# also remove from launcher registry
			self.delLauncher(launcherid)
		nodeclasses = nodeclassesdata.content
		return nodeclasses

	def handleNodeClassesPublish(self, event):
		launchername = event.id[-2]
		dataid = event.content
		self.uilauncherdict[launchername]['node classes id'] = dataid
		self.updateLauncherDictDataDict(launchername)

	def updateLauncherDictDataDict(self, launchername=None):
		if launchername is not None:
			newdict = self.uilauncherdictdatadict
			newdict[launchername] = self.getLauncherNodeClasses(launchername)
		else:
			newdict = {}
			for name,value in self.uilauncherdict.items():
				newdict[name] = self.getLauncherNodeClasses(name)
		self.uilauncherdictdatadict = newdict

	# node related methods

	def registerNode(self, readyevent):
		nodeid = readyevent.id[:-1]
		print 'Manager: registering node', nodeid

		nodelocation = readyevent.content

		# check if new node is launcher
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.addLauncher(nodeid, nodelocation)

		# for the clients and mapping
		self.addClient(nodeid, nodelocation)

		# published data of nodeid mapping to location of node
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata is None:
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		else:
			# fools! should do something nifty to unregister, reregister, etc.
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		self.server.datahandler._insert(nodelocationdata)

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
			self.delClient(nodeid)
			print 'Manager: node', nodeid, 'unregistered'
		else:
			print 'Manager: node', nodeid, 'does not exist'

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

	def launchNode(self, launcher, newproc, target, name, nodeargs=()):
		"""
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = name of a class in this launchers node class list
		args, kwargs = args for callable object
		"""
		args = (launcher, newproc, target, name, nodeargs)
		self.app.addLaunchSpec(args)

		newid = self.id + (name,)
		args = (newid, self.nodelocations) + nodeargs
		ev = event.LaunchEvent(self.ID(), newproc, target, args)
		self.outputEvent(ev, 0, launcher)
		return newid

	def killNode(self, nodeid):
			try:
				self.clients[nodeid].push(event.KillEvent(self.ID()))
			except IOError:
				print "Manager: cannot push KillEvent to %s, unregistering" % nodeid
				# group into another function
				self.removeNode(nodeid)
				# also remove from launcher registry
				self.delLauncher(nodeid)

	# data methods

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

	# application methods

	def saveApp(self, filename):
		self.app.save(filename)

	def loadApp(self, filename):
		self.app.load(filename)

	def launchApp(self):
		self.app.launch()

	def killApp(self):
		self.app.kill()

	# UI methods

	def uiNewLauncher(self, name):
		self.newLauncher(self.id + (name,))
		return ''

	def uiGetLauncherDict(self):
		self.updateLauncherDictDataDict()
		return self.uilauncherdictdatadict

	def uiNodeDict(self):
		"""
		return a dict describing all currently managed nodes
		"""
		nodeinfo = {}
		nodedict = self.uiNodeIDMapping()
		for nodename in nodedict:
			nodeid = nodedict[nodename]
			nodelocationdata = self.server.datahandler.query(nodeid)
			if nodelocationdata is not None:
				nodeloc = nodelocationdata.content
				nodeinfo[nodename] = nodeloc
		return nodeinfo

	def uiAddNode(self, hostname, port):
		e = event.ManagerAvailableEvent(self.id, self.location())
		try:
			client = self.clientclass(self.ID(),
												{'hostname': hostname, 'TCP port': port})
		except:
			print "Manager: cannot connect to specified node"
		try:
			client.push(e)
		except:
			print "Manager: cannot push to specified node"
		return ''

	def uiLaunchNode(self, name, launchclass, args, newproc=0):
		"""
		user interface to the launchNode method
		This simplifies the call for a user by using a
		string to represent the launcher ID, node class, and args
		"""

		launcher_str, nodeclass = launchclass

		print 'Manager: launching \'%s\' on \'%s\' (class %s)' \
								% (name, launcher_str, nodeclass) 
		launcher_id = self.uilauncherdict[launcher_str]['id']

		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			print 'problem evaluating args'
			return

		self.launchNode(launcher_id, newproc, nodeclass, name, args)
		return ''

	def uiKillNode(self, nodename):
		nodedict = self.uiNodeIDMapping()
		nodeid = nodedict[nodename]
		self.killNode(nodeid)
		return ''

	def uiAddDistmap(self, eventclass_str, fromnode_str, tonode_str):
		"""
		a user interface to addEventDistmap
		uses strings to represent event class and node IDs
		"""
		print 'Manager: binding event %s from %s to %s' \
						% (eventclass_str, fromnode_str, tonode_str)
		eventclass = self.uieventclasses[eventclass_str]
		nodedict = self.uiNodeIDMapping()
		fromnode_id = nodedict[fromnode_str]
		tonode_id = nodedict[tonode_str]
		self.addEventDistmap(eventclass, fromnode_id, tonode_id)

		## just to make xmlrpc happy
		return ''

	def	uiGetNodeLocations(self):
		nodelocations = self.uiNodeDict()
		nodelocations[self.id[-1]] = self.location()
		return nodelocations

	def uiSaveApp(self, filename):
		self.saveApp(filename)
		return ''

	def uiLoadApp(self, filename):
		self.loadApp(filename)
		return ''

	def uiLaunchApp(self):
		self.launchApp()
		return ''

	def uiKillApp(self):
		self.killApp()
		return ''

	def uiNodeListCallback(self):
		nodelist = []
		for newid in self.clients:
			nodelist.append(newid[-1])
		return nodelist

	def uiNodeIDMapping(self):
		nodedict = {}
		for newid in self.clients:
			nodedict[newid[-1]] = newid
		return nodedict

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		# this is data for ui to read, but not visible
		nodelistdata = self.registerUIData('nodelist', 'array', 'r')
		nodelistdata.set(self.uiNodeListCallback)

		# launch node from tree of launchers
		self.uilauncherdict = {}
		self.uilauncherdictdatadict = {}
		self.uilauncherdictdata = self.registerUIData('launcherdict',
												'struct', 'r', default=self.uiGetLauncherDict)

		argspec = (self.registerUIData('Name', 'string'),
								self.registerUIData('Launcher and Class', 'array',
												choices=self.uilauncherdictdata),
								self.registerUIData('Args', 'string', default=''),
								self.registerUIData('New Process', 'boolean', default=False))
		launchspec = self.registerUIMethod(self.uiLaunchNode, 'Launch', argspec)

		# list active nodes for killing
		argspec = (self.registerUIData('Node', 'string',
										choices=nodelistdata),)
		killspec = self.registerUIMethod(self.uiKillNode, 'Kill', argspec)

		# bind event from one node to another node
		self.uieventclasses = event.eventClasses()
		eventclass_list = self.uieventclasses.keys()
		eventclass_list.sort()
		self.uieventclasslistdata = self.registerUIData('eventclasslist', 'array',
																		'r', default=eventclass_list)
		argspec = (self.registerUIData('Event Class', 'string',
											choices=self.uieventclasslistdata),
								self.registerUIData('From Node', 'string',
											choices=nodelistdata),
								self.registerUIData('To Node', 'string',
											choices=nodelistdata))
		bindspec = self.registerUIMethod(self.uiAddDistmap, 'Bind', argspec)

		# save/load/killing applications
		argspec = (self.registerUIData('Filename', 'string'),)
		saveapp = self.registerUIMethod(self.uiSaveApp, 'Save', argspec)
		loadapp = self.registerUIMethod(self.uiLoadApp, 'Load', argspec)
		launchapp = self.registerUIMethod(self.uiLaunchApp, 'Launch', ())
		killapp = self.registerUIMethod(self.uiKillApp, 'Kill', ())
		appspec = self.registerUIContainer('Application',
									(saveapp, loadapp, launchapp, killapp))

		# creating a launcher
		argspec = (self.registerUIData('ID', 'string'),)
		newlauncherspec = self.registerUIMethod(self.uiNewLauncher,
															'New Launcher', (argspec))
		launcherspec = self.registerUIContainer('Launcher', (newlauncherspec,))

		# managing other nodes, information on nodes, adding a node
		self.uinodesdata = self.registerUIData('Nodes', 'struct', 'r')
		self.uinodesdata.set(self.uiNodeDict)
		argspec = (self.registerUIData('Hostname', 'string'),
								self.registerUIData('TCP Port', 'integer'))
		addnodespec = self.registerUIMethod(self.uiAddNode, 'Add Node', (argspec))
		nodesspec = self.registerUIContainer('Nodes',
											(self.uinodesdata, addnodespec))

		self.registerUISpec('Manager', (nodespec, launchspec,
								killspec, bindspec, appspec, launcherspec, nodesspec))

if __name__ == '__main__':
	import sys
	import time

	m = Manager(('manager',))

	p = False

	try:
		p = sys.argv[1]
	except IndexError:
		pass

	if p:
		import profile
		profile.run("m.start()", "%s.profile" % m.id[-1])
	else:
		m.start()

