#!/usr/bin/env python

import uiserver
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
import datahandler
import leginonobject
import socket
import os

class DataHandler(node.DataHandler):
	def __init__(self, id, session, mynode):
		leginonobject.LeginonObject.__init__(self, id)
		## giving these all the same id, don't know why
		self.datakeeper = datahandler.DictDataKeeper(id, session)
		self.databinder = datahandler.DataBinder(id, session)
		self.dbdatakeeper = dbdatakeeper.DBDataKeeper(id, session)
		self.node = mynode

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

		node.Node.__init__(self, id, session, nodelocations={},
												datahandler=DataHandler, tcpport=tcpport,
												xmlrpcport=xmlrpcport, **kwargs)

		self.uiclientcontainers = {}

#		self.checkPythonVersion()
		self.uiserver.server.register_function(self.uiGetNodeLocations, 'getNodeLocations')

		self.nodelocations['manager'] = self.location()

		# ready nodes, someday 'initialized' nodes
		self.initializednodescondition = threading.Condition()
		self.initializednodes = []
		self.distmap = {}
		# maps event id to list of node it was distributed to if event['confirm']
		self.disteventswaiting = {}

		self.application = application.Application(self.ID(), self)

		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent,
															self.handleNodeClassesPublish)
		self.addEventInput(event.NodeInitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.NodeUninitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.PublishEvent, self.registerData)
		self.addEventInput(event.UnpublishEvent, self.unregisterData)
		self.addEventInput(event.ListPublishEvent, self.registerData)
		# this makes every received event get distributed
		self.addEventInput(event.Event, self.distributeEvents)

		self.launcherdict = {}
		self.managersetup = ManagerSetup(self)
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

	def outputEvent(self, ievent, nodeid, wait=False, timeout=None):
		'''
		output an event to a node using node id
		overrides Node.outputEvent, which sends events to manager
		'''
		try:
			client = self.clients[nodeid]
		except KeyError:
			return
		self.eventToClient(ievent, client, wait, timeout)

	def confirmEvent(self, ievent):
		'''
		override Node.confirmEvent to send confirmation to a node
		'''
		if ievent['confirm']:
			eventid = ievent['id']
			nodeid = ievent['id'][:-1]
			ev = event.ConfirmationEvent(eventid=eventid)
			self.outputEvent(ev, nodeid)

	def handleConfirmedEvent(self, ievent):
		'''Event handler for distributing a confirmation event to the node waiting for confirmation of the event.'''
		# handle if this is my own event that has been confirmed
		node.Node.handleConfirmedEvent(self, ievent)

		# no handle if this is a distributed event getting confirmed
		eventid = ievent['eventid']
		## node that just confirmed, not the original node
		nodeid = ievent['id'][:-1]
		if eventid in self.disteventswaiting:
			if nodeid in self.disteventswaiting[eventid]:
				self.disteventswaiting[eventid][nodeid].set()

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		'''Map distribution of an event of eventclass from a node to a node.'''
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def delEventDistmap(self, eventclass, fromnodeid, tonodeid=None):
		try:
			self.distmap[eventclass][fromnodeid].remove(tonodeid)
		except (KeyError, ValueError):
			self.printerror(str(eventclass) + ': ' + str(fromnodeid) + ' to '
											+ str(tonodeid) + ' no such binding')
			return

	def distributeEvents(self, ievent):
		'''Push event to eventclients based on event class and source.'''
		eventclass = ievent.__class__
		eventid = ievent['id']
		#from_node = ievent.id[:-1]
		from_node = eventid[:-1]
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

		### set up confirmation event waiting
		ewaits = self.disteventswaiting
		if ievent['confirm']:
			ewaits[eventid] = {}
			for to_node in do:
				ewaits[eventid][to_node] = threading.Event()

		### distribute event
		for to_node in do:
			try:
				### this is a special case of outputEvent
				### so we don't use outputEvent here
				try:
					self.clients[to_node].push(ievent)
				except IOError:
					### bad client, get rid of it
					self.printerror('cannot push to node ' + str(to_node) + ', unregistering')
					self.removeNode(to_node)
					self.delLauncher(to_node)
					raise
				self.logEvent(ievent, 'distributed to %s' % (to_node,))
			except:
				self.printException()
				# make sure we don't wait for confirmation
				if ievent['confirm']:
					ewaits[eventid][to_node].set()

		### wait for all confirmations to come back
		### the "and do" part make sure we only confirm if events
		### were actually distributed since all events actually
		### come through this handler
		if ievent['confirm'] and do:
			## need confirmation from all nodes
			for e in ewaits[eventid].values():
				e.wait()
			del ewaits[eventid]
			## now confirm back to original event sender
			## in this case, don't confirm unless this
			## event was actually intended for this handler
			## is this a good idea?
			self.confirmEvent(ievent)

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
		launchers.sort()
		self.uilauncherselect.set(launchers, 0)

	def getLauncherNodeClasses(self, dataid, location, launcherid):
		'''Retrieve a list of launchable classes from a launcher by alias launchername.'''
		try:
			nodeclassesdata = self.researchByLocation(location, dataid)
		except:
			nodeclassesdata = None
			self.printException()
			self.printerror('cannot find launcher %s, unregistering' % launcherid)
			# group into another function
			self.removeNode(launcherid)
			# also remove from launcher registry
			self.delLauncher(launcherid)
			raise

		if nodeclassesdata is None:
			nodeclasses = None
		else:
			nodeclasses = nodeclassesdata['nodeclasses']
		return nodeclasses

	def handleNodeClassesPublish(self, ievent):
		'''Event handler for retrieving launchable classes.'''
		launchername = ievent['id'][-2]
		dataid = ievent['dataid']
		loc = self.launcherdict[launchername]['location']
		launcherid = self.launcherdict[launchername]['ID']
		nodeclasses = self.getLauncherNodeClasses(dataid, loc, launcherid)
		if nodeclasses is None:
			del self.launcherdict[launchername]
		else:
			self.launcherdict[launchername]['classes'] = nodeclasses

		## update the UI stuff
		launchers = self.launcherdict.keys()
		launchers.sort()
		self.uilauncherselect.set(launchers, 0)

		self.confirmEvent(ievent)

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

		self.confirmEvent(readyevent)

	def addNodeUIClient(self, nodeid, nodelocation):
		if nodeid in self.uiclientcontainers:
			self.deleteNodeUIClient(nodeid)
		clientcontainer = uidata.LargeClientContainer(str(nodeid[-1]),
														(nodelocation['hostname'], nodelocation['UI port']))
		try:
			self.uiserver.addObject(clientcontainer)
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
		self.confirmEvent(unavailable_event)

	def deleteNodeUIClient(self, nodeid):
		# also remove from launcher registry
		try:
			name = self.uiclientcontainers[nodeid].name
			del self.uiclientcontainers[nodeid]
			self.uiserver.deleteObject(name)
		except:
			self.printerror('cannot delete client container for node')

	def handleNodeStatus(self, ievent):
		nodeid = ievent['id'][:-1]
		if isinstance(ievent, event.NodeInitializedEvent):
			self.setNodeStatus(nodeid, True)
		elif isinstance(ievent, event.NodeUninitializedEvent):
			self.setNodeStatus(nodeid, False)
		self.confirmEvent(ievent)

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

	def launchNode(self, launcher, newproc, target, name, nodeargs=(), dependencies=[]):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = name of a class in this launchers node class list
		dependencies = node dependent on to launch
		'''
		args = (launcher, newproc, target, name, nodeargs, dependencies)
		t = threading.Thread(target=self.waitNode, args=args)
		t.start()
		nodeid = self.id + (name,)
		return nodeid

	def waitNode(self, launcher, newproc, target, name, nodeargs, dependencies):
		newid = self.id + (name,)
		args = (newid, self.session, self.nodelocations) + nodeargs
		dependencyids = []
		for dependency in dependencies:
			dependencyids.append(('manager', dependency))

		# be dependent on the launcher you're launching from by default
		if launcher not in dependencyids:
			dependencyids.append(launcher)

		self.waitNodes(dependencyids)
		ev = event.LaunchEvent(id=self.ID(), newproc=newproc, targetclass=target, args=args)
		self.outputEvent(ev, launcher, wait=True)

		#attempts = 5
		#for i in range(attempts):
		#	try:
		#		print 'OUTPUT LaunchEvent', target
		#		self.outputEvent(ev, launcher, wait=True)
		#		print 'DONE OUTPUT LaunchEvent', target
		#	except:
		#		self.printException()
		#		time.sleep(1.0)
		#		if i == attempts - 1:
		#			raise
		#	else:
		#		break

	def waitNodes(self, nodes):
		self.initializednodescondition.acquire()
		while not self.sublist(nodes, self.initializednodes):
			self.initializednodescondition.wait(0.1)
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

		try:
			client.push(e)
		except EOFError:
			self.printerror('manager unable to add node')

	def killNode(self, nodeid):
		'''Attempt telling a node to die and unregister. Unregister if communication with the node fails.'''
		ev = event.KillEvent()
		try:
			self.outputEvent(ev, nodeid)
		except:
			self.printException()
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
		self.confirmEvent(unpublishevent)

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

	def loadApp(self, name):
		'''Calls application.Application.load.'''
		if self.uilauncheraliascontainer is not None:
			self.applicationcontainer.deleteObject('Launcher Aliases')
		self.application.load(name)
		aliases = self.application.getLauncherAliases()
		uialiasselectors = []
		launchers = self.launcherdict.keys()
		launchers.sort()
		for alias in aliases:
			uialiasselectors.append(uidata.SingleSelectFromList(alias, launchers, 0))
		self.uilauncheraliascontainer = uidata.Container('Launcher Aliases')
		self.uilauncheraliascontainer.addObjects(uialiasselectors)
		self.applicationcontainer.addObject(self.uilauncheraliascontainer)

	def launchApp(self):
		'''Calls application.Application.launch.'''
		if self.uilauncheraliascontainer is None:
			return
		for alias in self.uilauncheraliascontainer.getObjects():
			self.application.setLauncherAlias(alias.getName(),
																				(alias.getSelectedValue(),))
		self.application.launch()

	def killApp(self):
		'''Calls application.Application.kill.'''
		if self.uilauncheraliascontainer is not None:
			self.applicationcontainer.deleteObject('Launcher Aliases')
		self.uilauncheraliascontainer = None
		self.application.kill()

	# UI methods

	def uiUpdateNodeInfo(self):
		'''Updates nodes lists and info in UI.'''
		nodes = self.clients.keys()
		nodes = map(str, nodes)
		self.uikillselect.set(nodes, 0)
		self.uifromnodeselect.set(nodes, 0)
		self.uitonodeselect.set(nodes, 0)

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
		hostname = self.uiaddnodehostname.getSelectedValue()
		port = self.uiaddnodeport.get()
		self.addNode(hostname, port)

	def uiLaunch(self):
		launchername = self.uilauncherselect.getSelectedValue()
		launcherid = self.launcherdict[launchername]['ID']
		process = self.uilaunchflag.get()
		nodeclass = self.uiclassselect.getSelectedValue()
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
		self.killNode(eval(value))

	def uiAddDistmap(self):
		'''UI function using addEventDistmap. Strings represent event classes and node IDs.'''
		eventclass_str = self.uieventselect.getSelectedValue()
		fromnodeidstr = self.uifromnodeselect.getSelectedValue()
		tonodeidstr = self.uitonodeselect.getSelectedValue()
		self.printerror('binding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		self.addEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

	def uiDelDistmap(self):
		'''UI function using delEventDistmap. Strings represent event classes and node IDs.'''
		eventclass_str = self.uieventselect.getSelectedValue()
		fromnodeidstr = self.uifromnodeselect.getSelectedValue()
		tonodeidstr = self.uitonodeselect.getSelectedValue()
		self.printerror('unbinding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		self.delEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

	def	uiGetNodeLocations(self):
		'''UI helper for mapping a node alias to the node's location.'''
		nodelocations = self.uiNodeDict()
		nodelocations[str(self.id)] = self.location()
		return nodelocations

	def uiUpdateApplications(self):
		applicationdatalist = self.research(dataclass=data.ApplicationData)
		applicationnamelist = []
		for applicationdata in applicationdatalist:
			name = applicationdata['name']
			if name not in applicationnamelist:
				applicationnamelist.append(name)
		self.uiapplicationlist.set(applicationnamelist, 0)

	def uiLoadApp(self):
		'''UI helper for loadApp. See loadApp.'''
		name = self.uiapplicationlist.getSelectedValue()
		if name is not None:
			self.loadApp(name)
		else:
			self.outputError('No application selected')

	def uiLaunchApp(self):
		'''UI helper for launchApp. See launchApp.'''
		self.launchApp()

	def uiKillApp(self):
		'''UI helper for killApp. See killApp.'''
		self.killApp()

	def uiLauncherSelectCallback(self, value):
		launchername = self.uilauncherselect.getSelectedValue(value)
		classes = list(self.launcherdict[launchername]['classes'])
		classes.sort()
		self.uiclassselect.set(classes, 0)
		return value

	def defineUserInterface(self):
		'''See node.Node.defineUserInterface.'''
#		node.Node.defineUserInterface(self)

		self.uilaunchname = uidata.String('Name', '', 'rw')
		self.uiclassselect = uidata.SingleSelectFromList('Node Class', [], 0)
		self.uilauncherselect = uidata.SingleSelectFromList('Launcher', [], 0)
		self.uilauncherselect.setCallback(self.uiLauncherSelectCallback)
		self.uilaunchargs = uidata.String('Arguments', '()', 'rw')
		self.uilaunchflag = uidata.Boolean('Process', False, 'rw')
		launchmethod = uidata.Method('Launch', self.uiLaunch)
		launchobjects = (self.uilaunchname, self.uilauncherselect,
											self.uiclassselect, self.uilaunchargs,
											self.uilaunchflag, launchmethod)
		launchcontainer = uidata.LargeContainer('Launch')
		launchcontainer.addObjects(launchobjects)


		self.uinodeinfo = uidata.Struct('Node Info', {}, 'r')
		infoobjects = (self.uinodeinfo,)
		self.uiaddnodehostname = uidata.SingleSelectFromList('Hostname',
																										leginonconfig.LAUNCHERS, 0)
		self.uiaddnodeport = uidata.Integer('TCP Port', 55555, 'rw')
		addmethod = uidata.Method('Add', self.uiAddNode)
		addobjects = (self.uiaddnodehostname, self.uiaddnodeport, addmethod)
		self.uikillselect = uidata.SingleSelectFromList('Kill Node', [], 0)
		killmethod = uidata.Method('Kill', self.uiKillNode)
		killobjects = (self.uikillselect, killmethod)
		nodemanagementcontainer = uidata.LargeContainer('Node Management')
		nodemanagementcontainer.addObjects(infoobjects + addobjects + killobjects)

		self.uiapplicationlist = uidata.SingleSelectFromList('Application', [], 0)
		self.uiUpdateApplications()
		applicationrefreshmethod = uidata.Method('Refresh',
																							self.uiUpdateApplications)
		applicationloadmethod = uidata.Method('Load', self.uiLoadApp)
		applicationlaunchmethod = uidata.Method('Launch', self.uiLaunchApp)
		applicationkillmethod = uidata.Method('Kill', self.uiKillApp)
		applicationobjects = (self.uiapplicationlist, applicationrefreshmethod,
													applicationloadmethod, applicationlaunchmethod,
													applicationkillmethod)
		self.uilauncheraliascontainer = None
		self.applicationcontainer = uidata.LargeContainer('Application')
		self.applicationcontainer.addObjects(applicationobjects)

		self.uifromnodeselect = uidata.SingleSelectFromList('From Node', [], 0)
		self.uieventclasses = event.eventClasses()
		eventclasses = self.uieventclasses.keys()
		eventclasses.sort()
		self.uieventselect = uidata.SingleSelectFromList('Event', eventclasses, 0)
		self.uitonodeselect = uidata.SingleSelectFromList('To Node', [], 0)
		bindmethod = uidata.Method('Bind', self.uiAddDistmap)
		unbindmethod = uidata.Method('Unbind', self.uiDelDistmap)
		eventobjects = (self.uifromnodeselect, self.uieventselect,
										self.uitonodeselect, bindmethod, unbindmethod)
		eventcontainer = uidata.LargeContainer('Event Bindings')
		eventcontainer.addObjects(eventobjects)

		uimanagersetup = self.managersetup.getUserInterface()

		container = uidata.LargeContainer('Manager')

		container.addObject(uimanagersetup)
		container.addObjects((launchcontainer, nodemanagementcontainer,
														eventcontainer, self.applicationcontainer))
		self.uiserver.addObject(container)

class ManagerSetup(object):
	def __init__(self, manager):
		self.manager = manager

		self.defineUserInterface()

		self.initUsers()
		self.initInstruments()

	def start(self):
		session = self.uiGetSession()
		if session is not None:
			self.manager.session = session
			self.manager.publish(session, database=True)
			if session['instrument'] is not None and session['instrument']['hostname'] not in self.manager.launcherdict.keys():
				try:
					hostname = session['instrument']['hostname']
					if hostname:
						self.manager.addNode(hostname, 55555)
				except (IOError, TypeError, socket.error), e:
					if isinstance(e, socket.error):
						self.manager.outputWarning('Cannot add instrument\'s launcher.')
			parent = self.container.getParent()
			if parent is not None:
				parent.deleteObject(self.container.getName())
		else:
			messagestring = 'Session "%s" already exists.' % self.session_name.get()
			message = uidata.MessageDialog('Error', messagestring)
			self.container.addObject(message)

	def uiGetSession(self):
		session_name = self.session_name.get()
		initializer = {'name': session_name,
								'user': data.UserData(initializer={'group': data.GroupData()}),
								'instrument': data.InstrumentData()}
		sessioninstance = data.SessionData(initializer=initializer)
		sessions = self.manager.research(datainstance=sessioninstance)
		if sessions:
			return sessions[0]
			#return None
		else:
			return self.getSession(session_name)

	def getSession(self, session_name):
		initializer = {'name': session_name, 'user': self.uiGetUser(), 'instrument': self.uiGetInstrument(), 'image path': self.image_path.get()}
		return data.SessionData(initializer=initializer)

	def initInstruments(self):
		instruments = self.getInstruments()
		self.instruments = self.indexByName(instruments)
		self.instruments['None'] = data.InstrumentData(name='None',description='No Instrument', hostname=None, scope=None, camera=None)
		self.uiUpdateInstrument()

	def uiUpdateInstrument(self):
		instrumentnames = self.instruments.keys()
		instrumentnames.sort()
		try:
			index = instrumentnames.index('None')
		except ValueError:
			index = 0
		self.instrumentselection.set(instrumentnames, index)

	def uiGetInstrument(self):
		instrumentname = self.instrumentselection.getSelectedValue()
		if instrumentname in self.instruments:
			return self.instruments[instrumentname]
		else:
			return None

	def getInstruments(self):
		instrumentinitializer = {}
		instrumentinstance = data.InstrumentData(initializer=instrumentinitializer)
		instrumentdatalist = self.manager.research(datainstance=instrumentinstance)
		return instrumentdatalist

	def initUsers(self):
		self.initAdmin()
		users = self.getUsers()
		self.users = self.indexByName(users)
		self.uiUpdateUsers()

	def uiUpdateUsers(self):
		usernames = self.users.keys()
		usernames.sort()
		self.userselection.set(usernames, 0)

	def uiGetUser(self):
		username = self.userselection.getSelectedValue()
		if username in self.users:
			return self.users[username]
		else:
			return None

	def indexByName(self, datalist):
		index = {}
		for indexdata in datalist:
			try:
				index[indexdata['name']] = indexdata
			except (TypeError, IndexError):
				pass
		return index

	def getUsers(self):
		self.initAdmin()
		groupinstance = data.GroupData()
		userinitializer = {'group': groupinstance}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		return userdatalist

	def initAdmin(self):
		adminuser = self.getAdminUser()
		if adminuser is None:
			admingroup = self.getAdminGroup()
			if admingroup is None:
				admingroup = self.addAdminGroup()
			adminuser = self.addAdminUser(admingroup)

	def getAdminGroup(self):
		groupinitializer = {'name': 'administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		groupdatalist = self.manager.research(datainstance=groupinstance)
		try:
			return groupdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminGroup(self):
		groupinitializer = {'name': 'administrators',
												'description': 'Administrators'}
		groupinstance = data.GroupData(initializer=groupinitializer)
		self.manager.publish(groupinstance, database=True)
		return groupinstance

	def getAdminUser(self):
		userinitializer = {'name': 'administrator', 'group': data.GroupData()}
		userinstance = data.UserData(initializer=userinitializer)
		userdatalist = self.manager.research(datainstance=userinstance)
		try:
			return userdatalist[0]
		except (TypeError, IndexError):
			return None

	def addAdminUser(self, group):
		userinitializer = {'name': 'administrator',
												'full name': 'Administrator',
												'group': group}
		userinstance = data.UserData(initializer=userinitializer)
		self.manager.publish(userinstance, database=True)
		return userinstance

	def uiUserSelectCallback(self, index):
		if not hasattr(self, 'userselection'):
			return index
		username = self.userselection.getSelectedValue(index)
		if username in self.users:
			userdata = self.users[username]
			try:
				self.userfullname.set(userdata['full name'])
			except KeyError:
				self.userfullname.set('')
			try:
				self.usergroup.set(userdata['group']['name'])
			except KeyError:
				self.usergroup.set('')
		else:
			self.userfullname.set('')
			self.usergroup.set('')
		return index

	def uiInstrumentSelectCallback(self, index):
		if not hasattr(self, 'instrumentselection'):
			return index
		instrumentname = self.instrumentselection.getSelectedValue(index)
		if instrumentname in self.instruments:
			instrumentdata = self.instruments[instrumentname]
			try:
				self.instrumentdescription.set(instrumentdata['description'])
			except (TypeError, KeyError):
				self.instrumentdescription.set('')
			try:
				self.instrumenthostname.set(instrumentdata['hostname'])
			except (TypeError, KeyError):
				self.instrumenthostname.set('')
		else:
			self.instrumentdescription.set('')
			self.instrumenthostname.set('')
		return index

	def defineUserInterface(self):
#		self.manager.uiserver.disable()
		self.container = uidata.ExternalContainer('Manager Setup')

		usercontainer = uidata.Container('User')
		self.userselection = uidata.SingleSelectFromList('Name', [], 0, self.uiUserSelectCallback, persist=True)
		self.userfullname = uidata.String('Full Name', '', 'r')
		self.usergroup = uidata.String('Group Name', '', 'r')
		usercontainer.addObjects((self.userselection,
																		self.userfullname,
																		self.usergroup))
		self.container.addObject(usercontainer)

		instrumentcontainer = uidata.Container('Instrument')
		self.instrumentselection = uidata.SingleSelectFromList('Name', [], 0, self.uiInstrumentSelectCallback, persist=True)
		self.instrumentdescription = uidata.String('Description', '', 'r')
		self.instrumenthostname = uidata.String('Hostname', '', 'r')

		instrumentcontainer.addObjects((self.instrumentselection,
																		self.instrumentdescription,
																		self.instrumenthostname))

		self.container.addObject(instrumentcontainer)

		session_name = time.strftime('%Y-%m-%d')
		self.session_name = uidata.String('Session Name', session_name, 'rw', persist=True)
		self.container.addObject(self.session_name)
		## default path comes from leginonconfig
		image_path = os.path.join(leginonconfig.IMAGE_PATH,session_name)
		self.image_path = uidata.String('Image Path', image_path, 'rw', persist=True)
		self.container.addObject(self.image_path)

		startmethod = uidata.Method('Start', self.start)
		self.container.addObject(startmethod)

	def getUserInterface(self):
		return self.container

if __name__ == '__main__':
	import sys
	try:
		session = sys.argv[1]
	except IndexError:
		session = time.strftime('%Y-%m-%d-%H-%M')

	initializer = {'name': session}
	m = Manager(('manager',), data.SessionData(initializer=initializer))
	m.start()

