#!/usr/bin/env python

import threading
import leginonconfig
import node
import application
import data
import event
import launcher
import copy
import time
import dbdatakeeper
import uidata

class DataHandler(node.DataHandler):
	def insert(self, idata):
		if isinstance(idata, event.Event):
			self.databinder.insert(idata)
		else:
			self.datakeeper.insert(copy.deepcopy(idata))

class Manager(node.Node):
	'''Overlord of the nodes. Handles node communication (data and events).'''
	def __init__(self, id, session, tcpport=None, xmlrpcport=None, **kwargs):
		# the id is manager (in a list)

		self.clients = {}

		node.Node.__init__(self, id, session, nodelocations={}, datahandler=DataHandler, tcpport=tcpport, xmlrpcport=xmlrpcport, **kwargs)

		self.uiclientcontainers = {}

		self.checkPythonVersion()
		self.uiserver.server.register_function(self.uiGetNodeLocations, 'getNodeLocations')

		self.nodelocations['manager'] = self.location()

		# ready nodes, someday 'initialized' nodes
		self.initializednodescondition = threading.Condition()
		self.initializednodes = []
		self.distmap = {}
		# maps event id to list of node it was distributed to if event['confirm']
		self.confirmmap = {}

		self.app = application.Application(self.ID(), self)

		# this makes every received event get distributed
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent,
															self.handleNodeClassesPublish)
		self.addEventInput(event.NodeInitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.NodeUninitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)
		self.addEventInput(event.Event, self.distributeEvents)

		self.launcherdict = {}
		self.defineUserInterface()
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
		self.outputEvent(event.ConfirmationEvent(id=self.ID(), eventid=ievent['id']),
											0, ievent['id'][:-1])

	def handleConfirmedEvent(self, ievent):
		'''Event handler for distributing a confirmation event to the node waiting for confirmation of the event.'''
		eventid = ievent['eventid']
		nodeid = eventid[:-1]
		if nodeid == self.id:
			# this is bad since it will fill up with lots of events
			if not eventid in self.confirmwaitlist:
				self.confirmwaitlist[eventid] = threading.Event()
				self.confirmwaitlist[eventid].set()
				#del self.confirmwaitlist[eventid]
		else:
			#self.confirmmap[eventid].remove(ievent.id[:-1])
			self.confirmmap[eventid].remove(ievent['id'][:-1])
			if len(self.confirmmap[eventid]) == 0:
				del self.confirmmap[eventid]
				self.outputEvent(ievent, 0, nodeid)

	def addEventDistmap(self, eventclass, from_node=None, to_node=None,
											addtoapp=True):
		'''Map distribution of an event of eventclass from a node to a node.'''
		args = (eventclass, from_node, to_node)
		if addtoapp:
			self.app.addBindingSpec(eventclass.__name__, from_node, to_node)

		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def delEventDistmap(self, eventclass, fromnodeid, tonodeid=None):
		try:
			self.distmap[eventclass][fromnodeid].remove(tonodeid)
		except:
			self.printerror(str(eventclass) + ': ' + str(fromnodeid) + ' to ' + str(tonodeid) + ' no such binding')
			self.printException()

		args = (eventclass, fromnodeid, tonodeid)
		self.app.delBindingSpec(eventclass.__name__, fromnodeid, tonoded)

	def distributeEvents(self, ievent):
		'''Push event to eventclients based on event class and source.'''
		eventclass = ievent.__class__
		#from_node = ievent.id[:-1]
		from_node = ievent['id'][:-1]
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
		if ievent['confirm']:
			self.confirmmap[ievent['id']] = do
		for to_node in do:
			self.logEvent(ievent, 'distributing to %s' % (to_node,))
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

	def addLauncher(self, nodeid, location):
		'''Register a launcher with the UI, aliases the launcher to the node ID, location and launchable node classes.'''
		name = nodeid[-1]
		self.launcherdict[name] = {'ID': nodeid, 'location': location}

	def delLauncher(self, nodeid):
		'''Unregister a launcher from the UI.'''
		name = nodeid[-1]
		try:
			del self.launcherdict[name]
		except KeyError:
			return
		# could check and keep selected if possible
		launchers = self.launcherdict.keys()
		if launchers:
			launchers.sort()
			selected = [0]
		else:
			selected = []
			self.uilauncherselect.set(launchers, selected)

	def getLauncherNodeClasses(self, dataid, location, launcherid):
		'''Retrieve a list of launchable classes from a launcher by alias launchername.'''
		try:
			nodeclassesdata = self.researchByLocation(location, dataid)
		except IOError:
			self.printerror('cannot find launcher %s, unregistering' % launcherid)
			# group into another function
			self.removeNode(launcherid)
			# also remove from launcher registry
			self.delLauncher(launcherid)
		nodeclasses = nodeclassesdata['nodeclasses']
		return nodeclasses

	def handleNodeClassesPublish(self, ievent):
		'''Event handler for retrieving launchable classes.'''
		launchername = ievent['id'][-2]
		dataid = ievent['dataid']
		try:
			self.launcherdict[launchername]['classes'] = self.getLauncherNodeClasses(
																	dataid,
																	self.launcherdict[launchername]['location'],
																	self.launcherdict[launchername]['ID'])
			launchers = self.launcherdict.keys()
			launchers.sort()
			self.uilauncherselect.set(launchers, [0])
		except:
			self.printException()

	# node related methods

	def registerNode(self, readyevent):
		'''Event handler for registering a node with the manager. Initializes a client for the node and adds information regarding the node's location.'''
		nodeid = readyevent['id'][:-1]
		self.printerror('registering node ' + str(nodeid))

		nodelocation = readyevent['location']

		# check if new node is launcher
		if readyevent['nodeclass'] == 'Launcher':
			self.addLauncher(nodeid, nodelocation)

		# for the clients and mapping
		self.addClient(nodeid, nodelocation)

		# published data of nodeid mapping to location of node
		nodelocationdata = self.datahandler.query(nodeid)
		if nodelocationdata is None:
			nodelocationdata = data.NodeLocationData(id=nodeid, location=nodelocation)
		else:
			# fools! should do something nifty to unregister, reregister, etc.
			nodelocationdata = data.NodeLocationData(id=nodeid, location=nodelocation)
		self.datahandler.insert(nodelocationdata)

		self.confirmEvent(readyevent)
		self.uiUpdateNodeInfo()
		self.addNodeUIClient(nodeid, nodelocation)

	def addNodeUIClient(self, nodeid, nodelocation):
		if nodeid in self.uiclientcontainers:
			self.deleteNodeUIClient(nodeid)
		clientcontainer = uidata.UIClientContainer(str(nodeid[-1]),
														(nodelocation['hostname'], nodelocation['UI port']))
		try:
			self.uiserver.addUIObject(clientcontainer)
			self.uiclientcontainers[nodeid] = clientcontainer
		except:
			self.printerror('cannot add client container for node')
			self.printException()

	def unregisterNode(self, unavailable_event):
		'''Event handler for unregistering the node from the manager. Removes all information, event mappings and the client related to the node.'''
		nodeid = unavailable_event['id'][:-1]
		self.removeNode(nodeid)
		self.delLauncher(nodeid)
		self.uiUpdateNodeInfo()
		self.deleteNodeUIClient(nodeid)

	def deleteNodeUIClient(self, nodeid):
		# also remove from launcher registry
		try:
			name = self.uiclientcontainers[nodeid].name
			del self.uiclientcontainers[nodeid]
			self.uiserver.deleteUIObject(name)
		except:
			self.printerror('cannot delete client container for node')
			self.printException()

	def handleNodeStatus(self, ievent):
		nodeid = ievent['id'][:-1]
		if isinstance(ievent, event.NodeInitializedEvent):
			self.setNodeStatus(nodeid, True)
		elif isinstance(ievent, event.NodeUninitializedEvent):
			self.setNodeStatus(nodeid, False)

	def setNodeStatus(self, nodeid, status):
		self.initializednodescondition.acquire()
		if status:
			if nodeid not in self.initializednodes:
				self.initializednodes.append(nodeid)
				self.initializednodescondition.notifyAll()
		else:
			if nodeid in self.initializednodes:
				self.initializednodes.remove(nodeid)
				self.initializednodescondition.notifyAll()
		self.initializednodescondition.release()

	def removeNode(self, nodeid):
		'''Remove data, event mappings, and client for the node with the specfied node ID.'''
#		nodelocationdata = self.server.datahandler.query(nodeid)
		nodelocationdata = self.datahandler.query(nodeid)
		if nodelocationdata is not None:
			self.removeNodeData(nodeid)
			self.removeNodeDistmaps(nodeid)
#			self.server.datahandler.remove(nodeid)
			self.datahandler.remove(nodeid)
			self.delClient(nodeid)
			self.printerror('node ' + str(nodeid) + ' unregistered')
		else:
			self.printerror('Manager: node ' + str(nodeid) + ' does not exist')

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
#		for dataid in self.server.datahandler.ids():
		for dataid in self.datahandler.ids():
			self.unpublishDataLocation(dataid, nodeid)

	def launchNode(self, launcher, newproc, target, name, nodeargs=(), dependencies=[], addtoapp=True):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = name of a class in this launchers node class list
		dependencies = node dependent on to launch
		'''
		args = (launcher, newproc, target, name, nodeargs, dependencies)
		if addtoapp:
			self.app.addNodeSpec(target, name, launcher, nodeargs, newproc,
																													dependencies)
		t = threading.Thread(target=self.waitNode, args=args)
		t.start()
		return self.id + (name,)

	def waitNode(self, launcher, newproc, target, name, nodeargs, dependencies):
		newid = self.id + (name,)
		args = (newid, self.session, self.nodelocations) + nodeargs
		dependenciescopy = copy.copy(dependencies)

		# be dependent on the launcher you're launching from by default
		if launcher not in dependenciescopy:
			dependenciescopy.append(launcher)

		self.waitNodes(dependenciescopy)
		ev = event.LaunchEvent(id=self.ID(), newproc=newproc,
														targetclass=target, args=args)
		attempts = 5
		for i in range(attempts):
			try:
				self.outputEvent(ev, 0, launcher)
			except IOError:
				time.sleep(1.0)
				if i == attempts - 1:
					raise
			else:
				break

	def waitNodes(self, nodes):
		self.initializednodescondition.acquire()
		while not self.sublist(nodes, self.initializednodes):
			self.initializednodescondition.wait()
		self.initializednodescondition.release()

	# probably an easier way
	def sublist(self, list1, list2):
		'''returns True if all elements in list1 are in list2, otherwise False'''
		for i in list1:
			if i not in list2:
				return False
		return True

	def addNode(self, hostname, port):
		'''Add a running node to the manager. Sends an event to the location.'''
		e = event.NodeAvailableEvent(id=self.id, location=self.location(), nodeclass=self.__class__.__name__)
		client = self.clientclass(self.ID(),
												{'hostname': hostname, 'TCP port': port})
		client.push(e)

	def killNode(self, nodeid):
		'''Attempt telling a node to die and unregister. Unregister if communication with the node fails.'''
		try:
			self.clients[nodeid].push(event.KillEvent(id=self.ID()))
		except IOError:
			self.printerror('cannot push KillEvent to ' + str(nodeid)
												+ ', unregistering')
			# maybe didn't uninitialized
			self.setNodeStatus(nodeid, False)
			# group into another function
			self.removeNode(nodeid)
			# also remove from launcher registry
			self.delLauncher(nodeid)

	# data methods

	def registerData(self, publishevent):
		'''Event handler. Calls publishDataLocation. Operates on singular data IDs or lists of data IDs.'''
		if isinstance(publishevent, event.PublishEvent):
			id = publishevent['dataid']
			self.publishDataLocation(id, publishevent['id'][:-1])
		elif isinstance(publishevent, event.ListPublishEvent):
			for id in publishevent['idlist']:
				self.publishDataLocation(id, publishevent['id'][:-1])
		else:
			raise TypeError
		self.confirmEvent(publishevent)

	def publishDataLocation(self, dataid, nodeid):
		'''Registers the location of a piece of data by mapping the data's ID to its location. Appends location to list if data ID is already registered.'''
		datalocationdata = self.datahandler.query(dataid)
		if datalocationdata is None:
			datalocationdata = data.DataLocationData(id=dataid, location=[nodeid])
		else:
			if nodeid not in datalocationdata['location']:
				datalocationdata['location'].append(nodeid)
		self.datahandler.insert(datalocationdata)

	def unregisterData(self, unpublishevent):
		'''Event handler unregistering data from the manager. Removes a location mapped to the data ID.'''
		if isinstance(unpublishevent, event.UnpublishEvent):
			self.unpublishDataLocation(id, unpublishevent['id'][:-1])
		else:
			raise TypeError

	def unpublishDataLocation(self, dataid, nodeid):
		'''Unregisters data by unmapping the location from the data ID. If no other location are mapped to the data ID, the data ID is removed.'''
		datalocationdata = self.datahandler.query(dataid)
		if (datalocationdata is not None) and (type(datalocationdata) == data.DataLocationData):
			try:
				datalocationdata['location'].remove(nodeid)
				if len(datalocationdata['location']) == 0:
					self.datahandler.remove(dataid)
				else:
					self.datahandler.insert(datalocationdata)
			except ValueError:
				pass

	# application methods

	def saveApp(self, name):
		'''Calls application.Application.save.'''
		self.app.setName(name)
		self.app.save()

	def loadApp(self, name):
		'''Calls application.Application.load.'''
		self.app.load(name)

	def launchApp(self):
		'''Calls application.Application.launch.'''
		self.app.launch()

	def killApp(self):
		'''Calls application.Application.kill.'''
		self.app.kill()

	# UI methods

	def uiUpdateNodeInfo(self):
		'''Updates nodes lists and info in UI.'''
		nodes = self.clients.keys()
		if nodes:
			nodes = map(str, nodes)
			selected = [0]
		else:
			selected = []
		self.uikillselect.set(nodes, selected)
		self.uifromnodeselect.set(nodes, selected)
		self.uitonodeselect.set(nodes, selected)

		self.uinodeinfo.set(self.uiNodeDict())

#	def uiNodeDict(self):
#		nodes = self.clients.keys()
#		nodeinfo = {}
#		nodelist = self.uiNodeList()
#		for nodeidstr in nodelist:
#			nodeid = eval(nodeidstr)
#			nodelocationdata = self.datahandler.query(nodeid)
#			if nodelocationdata is not None:
#				nodelocation = nodelocationdata['location']
#				nodeinfo[str(nodeid)] = nodelocation
#		return nodeinfo

	def uiNodeDict(self):
		nodes = self.clients.keys()
		nodeinfo = {}
		for nodeid in nodes:
			nodelocationdata = self.datahandler.query(nodeid)
			if nodelocationdata is not None:
				nodelocation = nodelocationdata['location']
				nodeinfo[str(nodeid)] = nodelocation
		return nodeinfo

	def uiAddNode(self):
		'''UI helper calling addNode. See addNode.'''
		hostname = self.uiaddnodehostname.getSelectedValue()[0]
		port = self.uiaddnodeport.get()
		self.addNode(hostname, port)

	def uiLaunch(self):
		launchername = self.uilauncherselect.getSelectedValue()[0]
		launcherid = self.launcherdict[launchername]['ID']
		process = self.uilaunchflag.get()
		nodeclass = self.uiclassselect.getSelectedValue()[0]
		name = self.uilaunchname.get()
		args = '(%s)' % self.uilaunchargs.get()
		try:
			args = eval(args)
		except:
			self.printerror('error evaluating args during UI launch')
			self.printException()
			return
		self.launchNode(launcherid, process, nodeclass, name, args)

	def uiKillNode(self):
		'''UI helper calling killNode, using str node aliases. See killNode.'''
		value = self.uikillselect.getSelectedValue()
		if value:
			self.killNode(eval(value[0]))

	def uiAddDistmap(self):
		'''UI function using addEventDistmap. Strings represent event classes and node IDs.'''
		try:
			eventclass_str = self.uieventselect.getSelectedValue()[0]
			fromnodeidstr = self.uifromnodeselect.getSelectedValue()[0]
			tonodeidstr = self.uitonodeselect.getSelectedValue()[0]
		except IndexError:
			return
		self.printerror('binding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		self.addEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

	def uiDelDistmap(self):
		'''UI function using delEventDistmap. Strings represent event classes and node IDs.'''
		try:
			eventclass_str = self.uieventselect.getSelectedValue()[0]
			fromnodeidstr = self.uifromnodeselect.getSelectedValue()[0]
			tonodeidstr = self.uitonodeselect.getSelectedValue()[0]
		except IndexError:
			return
		self.printerror('unbinding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		self.delEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

	def	uiGetNodeLocations(self):
		'''UI helper for mapping a node alias to the node's location.'''
		nodelocations = self.uiNodeDict()
		nodelocations[str(self.id)] = self.location()
		return nodelocations

	def uiSaveApp(self):
		'''UI helper for saveApp. See saveApp.'''
		name = self.uiapplicationname.get()
		self.saveApp(name)

	def uiLoadApp(self):
		'''UI helper for loadApp. See loadApp.'''
		name = self.uiapplicationname.get()
		self.loadApp(name)

	def uiLaunchApp(self):
		'''UI helper for launchApp. See launchApp.'''
		self.launchApp()

	def uiKillApp(self):
		'''UI helper for killApp. See killApp.'''
		self.killApp()

	def uiLauncherSelectCallback(self, value):
		try:
			values = self.uilauncherselect.getSelectedValue(value)
			launchername = values[0]
			classes = list(self.launcherdict[launchername]['classes'])
			if classes:
				classes.sort()
				selected = [0]
			else:
				selected = []
			self.uiclassselect.set(classes, selected)
		except:
			self.uiclassselect.set([], [])
			self.printException()
		return value

	def defineUserInterface(self):
		'''See node.Node.defineUserInterface.'''
		node.Node.defineUserInterface(self)

		self.uilaunchname = uidata.UIString('Name', '', 'rw')
		self.uiclassselect = uidata.UISelectFromList('Node Class', [], [], 'r')
		self.uilauncherselect = uidata.UISelectFromList('Launcher', [], [], 'r',
																									self.uiLauncherSelectCallback)
		self.uilaunchargs = uidata.UIString('Arguments', '()', 'rw')
		self.uilaunchflag = uidata.UIBoolean('Process', False, 'rw')
		launchmethod = uidata.UIMethod('Launch', self.uiLaunch)
		launchobjects = (self.uilaunchname, self.uilauncherselect,
											self.uiclassselect, self.uilaunchargs,
											self.uilaunchflag, launchmethod)
		launchcontainer = uidata.UIMediumContainer('Launch')
		launchcontainer.addUIObjects(launchobjects)

		self.uinodeinfo = uidata.UIStruct('Node Info', {}, 'r')
		infoobjects = (self.uinodeinfo,)
		self.uiaddnodehostname = uidata.UISelectFromList('Hostname', leginonconfig.LAUNCHERS, [0], 'r')
		self.uiaddnodeport = uidata.UIInteger('TCP Port', 55555, 'rw')
		addmethod = uidata.UIMethod('Add', self.uiAddNode)
		addobjects = (self.uiaddnodehostname, self.uiaddnodeport, addmethod)
		self.uikillselect = uidata.UISelectFromList('Kill Node', [], [], 'r')
		killmethod = uidata.UIMethod('Kill', self.uiKillNode)
		killobjects = (self.uikillselect, killmethod)
		nodemanagementcontainer = uidata.UIMediumContainer('Node Management')
		nodemanagementcontainer.addUIObjects(infoobjects + addobjects + killobjects)

		self.uiapplicationname = uidata.UIString('Name', '', 'rw')
		applicationsavemethod = uidata.UIMethod('Save', self.uiSaveApp)
		applicationloadmethod = uidata.UIMethod('Load', self.uiLoadApp)
		applicationlaunchmethod = uidata.UIMethod('Launch', self.uiLaunchApp)
		applicationkillmethod = uidata.UIMethod('Kill', self.uiKillApp)
		applicationobjects = (self.uiapplicationname, applicationsavemethod,
													applicationloadmethod, applicationlaunchmethod,
													applicationkillmethod)
		applicationcontainer = uidata.UIMediumContainer('Application')
		applicationcontainer.addUIObjects(applicationobjects)

		self.uifromnodeselect = uidata.UISelectFromList('From Node', [], [], 'r')
		self.uieventclasses = event.eventClasses()
		eventclasses = self.uieventclasses.keys()
		eventclasses.sort()
		if eventclasses:
			selected = [0]
		else:
			selected = []
		self.uieventselect = uidata.UISelectFromList('Event', eventclasses,
																									selected, 'r')
		self.uitonodeselect = uidata.UISelectFromList('To Node', [], [], 'r')
		bindmethod = uidata.UIMethod('Bind', self.uiAddDistmap)
		unbindmethod = uidata.UIMethod('Unbind', self.uiDelDistmap)
		eventobjects = (self.uifromnodeselect, self.uieventselect,
										self.uitonodeselect, bindmethod, unbindmethod)
		eventcontainer = uidata.UIMediumContainer('Event Bindings')
		eventcontainer.addUIObjects(eventobjects)

		container = uidata.UIMediumContainer('Manager')
		container.addUIObjects((launchcontainer, nodemanagementcontainer,
														eventcontainer, applicationcontainer))
		self.uiserver.addUIObject(container)

if __name__ == '__main__':
	import sys
	try:
		session = sys.argv[1]
	except IndexError:
		session = time.strftime('%Y-%m-%d-%H-%M')

	m = Manager(('manager',), session)
	m.start()

