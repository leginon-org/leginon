#!/usr/bin/env python

import threading
import node
import application
import data
import event
import launcher

False=0
True=1

class Manager(node.Node):
	'''Overlord of the nodes. Handles node communication (data and events).'''
	def __init__(self, id, tcpport=None, xmlrpcport=None):
		# the id is manager (in a list)

		self.clients = {}

		node.Node.__init__(self, id, {}, tcpport=tcpport, xmlrpcport=xmlrpcport)

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
		'''Overrides node.Node.main'''
		pass

	def start(self):
		'''Overrides node.Node.start'''
		self.print_location()
		interact_thread = self.interact()

		self.main()

		# wait until the interact thread terminates
		interact_thread.join()
		self.exit()

	def exit(self):
		'''Overrides node.Node.exit'''
		self.server.exit()

	# client methods

	def addClient(self, newid, loc):
		'''Add a client of clientclass to a node keyed by the node ID.'''
		self.clients[newid] = self.clientclass(self.ID(), loc)

	def delClient(self, newid):
		'''Deleted a client to a node by the node ID.'''
		if newid in self.clients:
			del self.clients[newid]

	# event methods

	def outputEvent(self, ievent, wait, nodeid):
		'''Overrides node.Node.outputEvent to use the client dictionary.'''
		try:
			self.clients[nodeid].push(ievent)
		except KeyError:
			self.printerror('cannot output event %s to %s' % (ievent, nodeid))
			return
		if wait:
			self.waitEvent(ievent)

	def confirmEvent(self, ievent):
		'''Override node.Node.confirmEvent to distribute a confirmation event to the node waiting for confirmation of the event.'''
		self.outputEvent(event.ConfirmationEvent(self.ID(), ievent.id),
											0, ievent.id[:-1])

	def handleConfirmedEvent(self, ievent):
		'''Event handler for distributing a confirmation event to the node waiting for confirmation of the event.'''
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
		'''Map distribution of an event of eventclass from a node to a node.'''
		args = (eventclass, from_node, to_node)
		self.app.addBindSpec(args)

		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distributeEvents(self, ievent):
		'''Push event to eventclients based on event class and source.'''
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
				self.printerror('cannot push to node ' + str(nodeid)
												+ ', unregistering')
				# group into another function
				self.removeNode(to_node)
				# also remove from launcher registry
				self.delLauncher(to_node)

	# launcher related methods

#	def newLauncher(self, newid):
#		'''Create a launcher node running in a thread within the manager's process.'''
#		t = threading.Thread(name='%s launcher thread' % newid[-1],
#								target=launcher.Launcher, args=(newid, self.nodelocations))
#		t.start()
#		launcher.Launcher(newid, self.nodelocations)

	def addLauncher(self, nodeid, location):
		'''Register a launcher with the UI, aliases the launcher to the node ID, location and launchable node classes.'''
		name = nodeid[-1]
		#print self.clients[nodeid]
		self.uilauncherdict[name] = {'id':nodeid, 'location':location, 'node classes id':None}

	def delLauncher(self, nodeid):
		'''Unregister a launcher from the UI.'''
		name = nodeid[-1]
		try:
			del self.uilauncherdict[name]
		except:
			pass
		self.updateLauncherDictDataDict()

	def getLauncherNodeClasses(self, launchername):
		'''Retrieve a list of launchable classes from a launcher by alias launchername.'''
		dataid = self.uilauncherdict[launchername]['node classes id']
		loc = self.uilauncherdict[launchername]['location']
		launcherid = self.uilauncherdict[launchername]['id']
		try:
			nodeclassesdata = self.researchByLocation(loc, dataid)
		except IOError:
			self.printerror('cannot find launcher %s, unregistering' % launcherid)
			# group into another function
			self.removeNode(launcherid)
			# also remove from launcher registry
			self.delLauncher(launcherid)
		nodeclasses = nodeclassesdata.content
		return nodeclasses

	def handleNodeClassesPublish(self, event):
		'''Event handler for retrieving launchable classes.'''
		launchername = event.id[-2]
		dataid = event.content
		self.uilauncherdict[launchername]['node classes id'] = dataid
		self.updateLauncherDictDataDict(launchername)

	def updateLauncherDictDataDict(self, launchername=None):
		'''Refresh the UI launcher information.'''
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
		'''Event handler for registering a node with the manager. Initializes a client for the node and adds information regarding the node's location.'''
		nodeid = readyevent.id[:-1]
		self.printerror('registering node ' + str(nodeid))

		#print readyevent.content
		nodelocation = readyevent.content['location']

		# check if new node is launcher
#		if isinstance(readyevent, event.LauncherAvailableEvent):
		if readyevent.content['class'] == 'Launcher':
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
		'''Event handler for unregistering the node from the manager. Removes all information, event mappings and the client related to the node.'''
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

		# also remove from launcher registry
		self.delLauncher(nodeid)

	def removeNode(self, nodeid):
		'''Remove data, event mappings, and client for the node with the specfied node ID.'''
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata is not None:
			self.removeNodeData(nodeid)
			self.removeNodeDistmaps(nodeid)
			self.server.datahandler.remove(nodeid)
			self.delClient(nodeid)
			self.printerror('node ' + str(nodeid) + ' unregistered')
		else:
			self.printerror('Manager: node ' + nodeid + ' does not exist')

	def removeNodeDistmaps(self, nodeid):
		'''Remove event mappings related to the node with the specifed node ID.'''
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
		'''Remove data associated with the node of specified node ID.'''
		# terribly inefficient
		for dataid in self.server.datahandler.ids():
			self.unpublishDataLocation(dataid, nodeid)

	def launchNode(self, launcher, newproc, target, name, nodeargs=()):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = name of a class in this launchers node class list
		args, kwargs = args for callable object
		'''
		args = (launcher, newproc, target, name, nodeargs)
		self.app.addLaunchSpec(args)

		newid = self.id + (name,)
		args = (newid, self.nodelocations) + nodeargs
		ev = event.LaunchEvent(self.ID(), newproc, target, args)
		self.outputEvent(ev, 0, launcher)
		return newid

	def addNode(self, hostname, port):
		'''Add a running node to the manager. Sends an event to the location.'''
		e = event.NodeAvailableEvent(self.id, self.location(), self.__class__.__name__)
		client = self.clientclass(self.ID(),
												{'hostname': hostname, 'TCP port': port})
		client.push(e)

	def killNode(self, nodeid):
		'''Attempt telling a node to die and unregister. Unregister if communication with the node fails.'''
		try:
			self.clients[nodeid].push(event.KillEvent(self.ID()))
		except IOError:
			self.printerror('cannot push KillEvent to ' + str(nodeid)
												+ ', unregistering')
			# group into another function
			self.removeNode(nodeid)
			# also remove from launcher registry
			self.delLauncher(nodeid)

	# data methods

	def registerData(self, publishevent):
		'''Event handler. Calls publishDataLocation. Operates on singular data IDs or lists of data IDs.'''
		if isinstance(publishevent, event.PublishEvent):
			id = publishevent.content
			self.publishDataLocation(id, publishevent.id[:-1])
		elif isinstance(publishevent, event.ListPublishEvent):
			for id in publishevent.content:
				self.publishDataLocation(id, publishevent.id[:-1])
		else:
			raise TypeError

	def publishDataLocation(self, dataid, nodeid):
		'''Registers the location of a piece of data by mapping the data's ID to its location. Appends location to list if data ID is already registered.'''
		datalocationdata = self.server.datahandler.query(dataid)
		if datalocationdata is None:
			datalocationdata = data.DataLocationData(dataid, [nodeid])
		else:
			datalocationdata.content.append(nodeid)
		self.server.datahandler._insert(datalocationdata)

	def unregisterData(self, unpublishevent):
		'''Event handler unregistering data from the manager. Removes a location mapped to the data ID.'''
		if isinstance(unpublishevent, event.UnpublishEvent):
			id = unpublishevent.content
			self.unpublishDataLocation(id, unpublishevent.id[:-1])
		else:
			raise TypeError

	def unpublishDataLocation(self, dataid, nodeid):
		'''Unregisters data by unmapping the location from the data ID. If no other location are mapped to the data ID, the data ID is removed.'''
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
		'''Calls application.Application.save.'''
		self.app.save(filename)

	def loadApp(self, filename):
		'''Calls application.Application.load.'''
		self.app.load(filename)

	def launchApp(self):
		'''Calls application.Application.launch.'''
		self.app.launch()

	def killApp(self):
		'''Calls application.Application.kill.'''
		self.app.kill()

	# UI methods

#	def uiNewLauncher(self, name):
#		'''UI helper calling newLauncher. See newLauncher.'''
#		self.newLauncher(self.id + (name,))
#		return ''

	def uiGetLauncherDict(self):
		'''UI helper updated and retrieves launcher information.'''
		self.updateLauncherDictDataDict()
		return self.uilauncherdictdatadict

	def uiNodeDict(self):
		'''Returns a dict describing all currently managed nodes aliasing a readablenode name to the node's location.'''
		nodeinfo = {}
		nodelist = self.uiNodeList()
		for nodeidstr in nodelist:
			nodeid = eval(nodeidstr)
			nodelocationdata = self.server.datahandler.query(nodeid)
			if nodelocationdata is not None:
				nodeloc = nodelocationdata.content
				nodeinfo[nodeidstr] = nodeloc
		return nodeinfo

	def uiAddNode(self, hostname, port):
		'''UI helper calling addNode. See addNode.'''
		try:
			self.addNode(hostname, port)
		except:
			self.printerror('cannot connect to specified node')
		return ''

	def uiLaunchNode(self, name, launchclass, args, newproc=0):
		'''UI to the launchNode method, simplifies the call for a user by using a string to represent the launcher ID, node class, and args.'''

		if len(launchclass) != 2:
			raise ValueError('launchclass must contain launcher and class')
		launcher_str, nodeclass = launchclass

		self.printerror('launching \'%s\' on \'%s\' (class %s)'
										% (name, launcher_str, nodeclass))
		launcher_id = self.uilauncherdict[launcher_str]['id']

		args = '(%s)' % args
		try:
			args = eval(args)
		except:
			self.printerror('problem evaluating args for launch')
			return

		self.launchNode(launcher_id, newproc, nodeclass, name, args)
		return ''

	def uiKillNode(self, nodeidstr):
		'''UI helper calling killNode, using user readable node aliases. See killNode.'''
		self.killNode(eval(nodeidstr))
		return ''

	def uiAddDistmap(self, eventclass_str, fromnodeidstr, tonodeidstr):
		'''a UI helper for addEventDistmap. Uses strings to represent event class and node IDs.'''
		self.printerror('binding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		self.addEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

		## just to make xmlrpc happy
		return ''

	def	uiGetNodeLocations(self):
		'''UI helper for mapping a node alias to the node's location.'''
		nodelocations = self.uiNodeDict()
		nodelocations[str(self.id)] = self.location()
		return nodelocations

	def uiSaveApp(self, filename):
		'''UI helper for saveApp. See saveApp.'''
		self.saveApp(filename)
		return ''

	def uiLoadApp(self, filename):
		'''UI helper for loadApp. See loadApp.'''
		self.loadApp(filename)
		return ''

	def uiLaunchApp(self):
		'''UI helper for launchApp. See launchApp.'''
		self.launchApp()
		return ''

	def uiKillApp(self):
		'''UI helper for killApp. See killApp.'''
		self.killApp()
		return ''

	def uiNodeList(self):
		'''UI callback function returning list of user readable node aliases.'''
		nodelist = []
		for newid in self.clients:
			nodelist.append(str(newid))
		return nodelist

#	def uiNodeIDMapping(self):
#		'''UI callback function returning a dictionary mapping user readable node aliases to node IDs.'''
#		nodedict = {}
#		for newid in self.clients:
#			nodedict[str(newid)] = newid
#		return nodedict

	def defineUserInterface(self):
		'''See node.Node.defineUserInterface.'''
		nodespec = node.Node.defineUserInterface(self)

		# this is data for ui to read, but not visible
		nodelistdata = self.registerUIData('nodelist', 'array', 'r')
		nodelistdata.registerCallback(self.uiNodeList)

		# launch node from tree of launchers
		self.uilauncherdict = {}
		self.uilauncherdictdatadict = {}
		self.uilauncherdictdata = self.registerUIData('launcherdict', 'struct', 'r')
		self.uilauncherdictdata.registerCallback(self.uiGetLauncherDict)

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
#		argspec = (self.registerUIData('ID', 'string'),)
#		newlauncherspec = self.registerUIMethod(self.uiNewLauncher,
#															'New Launcher', (argspec))
#		launcherspec = self.registerUIContainer('Launcher', (newlauncherspec,))

		# managing other nodes, information on nodes, adding a node
		self.uinodesdata = self.registerUIData('Nodes', 'struct', 'r')
		self.uinodesdata.registerCallback(self.uiNodeDict)
		argspec = (self.registerUIData('Hostname', 'string'),
								self.registerUIData('TCP Port', 'integer'))
		addnodespec = self.registerUIMethod(self.uiAddNode, 'Add Node', (argspec))
		nodesspec = self.registerUIContainer('Nodes',
											(self.uinodesdata, addnodespec))

		self.registerUISpec('Manager', (nodespec, launchspec,
#								killspec, bindspec, appspec, launcherspec, nodesspec))
								killspec, bindspec, appspec, nodesspec))

if __name__ == '__main__':
	import sys

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

