#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import application
import data
import datahandler
import datatransport
import dbdatakeeper
import event
import importexport
import leginonconfig
import managersetup
import node
import threading
import uiserver
import uidata
import leginonobject

class DataBinder(datahandler.DataBinder):
	def handleData(self, newdata):
		dataclass = newdata.__class__
		args = newdata
		for bindclass in self.bindings.keys():
			if issubclass(dataclass, bindclass):
				try:
					methods = self.bindings[bindclass]
					for method in methods:
						method(args)
				except KeyError:
					pass

	def addBinding(self, nodeid, dataclass, method):
		'method must take data instance as first arg'
		try:
			self.bindings[dataclass].append(method)
		except KeyError:
			self.bindings[dataclass] = [method]

	def delBinding(self, nodeid, dataclass=None, method=None):
		if dataclass is None:
			dataclasses = self.bindings.keys()
		else:
			dataclasses = [dataclass]
		for dataclass in dataclasses:
			try:
				if method is None:
					del self.bindings[dataclass]
				else:
					self.bindings[dataclass].remove(method)
					if not self.bindings[dataclass]:
						del self.bindings[dataclass]
			except (KeyError, ValueError):
				pass

class Manager(node.Node):
	'''Overlord of the nodes. Handles node communication (data and events).'''
	def __init__(self, id, session, tcpport=None, xmlrpcport=None, **kwargs):
		# the id is manager (in a list)

		self.clients = {}

		self.datahandler = node.DataHandler(self, databinderclass=DataBinder)
		self.server = datatransport.Server(self.datahandler, tcpport)
		self.uicontainer = uiserver.Server('Manager', xmlrpcport,
										dbdatakeeper=self.datahandler.dbdatakeeper, session=session)

		node.Node.__init__(self, id, session, **kwargs)

		self.uiclientcontainers = {}
		self.uicontainer.xmlrpcserver.register_function(self.uiGetNodeLocations,
																										'getNodeLocations')

		self.nodelocations['manager'] = self.location()

		# ready nodes, someday 'initialized' nodes
		self.initializednodescondition = threading.Condition()
		self.initializednodes = []
		self.distmap = {}
		# maps event id to list of node it was distributed to if event['confirm']
		self.disteventswaiting = {}

		self.application = application.Application(self)

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
		self.managersetup = managersetup.ManagerSetup(self)

	def location(self):
		location = leginonobject.LeginonObject.location(self)
		location['data transport'] = self.server.location()
		location['UI'] = self.uicontainer.location()
		return location

	# main/start methods

	def start(self):
		'''Overrides node.Node.start'''
		pass

	def exit(self):
		'''Overrides node.Node.exit'''
		self.server.exit()

	# client methods

	def addClient(self, newid, datatransportlocation):
		'''Add a client of clientclass to a node keyed by the node ID.'''
		self.clients[newid] = self.clientclass(datatransportlocation)

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
		ievent['destination'] = nodeid
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

		## if nothing to do, report a warning and return now
		if not do:
#			print 'FYI:  %s event from node %s is not bound to any nodes.' % (eventclass.__name__, from_node)
			return

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
					ievent['destination'] = to_node
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
		self.addNodeUIClient(nodeid, location['UI'])

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
		if launchers:
			selected = 0
		else:
			selected = None
			self.launchcontainer.disable()
		self.uilauncherselect.set(launchers, selected)
		self.deleteNodeUIClient(nodeid)

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

		self.uiUpdateLauncherInfo()
		self.confirmEvent(ievent)

	def uiUpdateLauncherInfo(self):
		try:
			launchers = self.launcherdict.keys()
			if launchers:
				self.launchcontainer.enable()
				launchers.sort()
				selected = 0
			else:
				self.launchcontainer.disable()
				selected = None
			self.uilauncherselect.set(launchers, selected)
		except AttributeError:
			pass

	# node related methods

	def registerNode(self, readyevent):
		'''Event handler for registering a node with the manager. Initializes a client for the node and adds information regarding the node's location.'''
		nodeid = readyevent['id'][:-1]
#		self.printerror('registering node ' + str(nodeid))
		nodelocationdata = self.datahandler.query(nodeid)
		if nodelocationdata is not None:
			self.killNode(nodeid)

		nodelocation = readyevent['location']
		classstring = readyevent['nodeclass']

		# check if new node is launcher
		if classstring == 'Launcher':
			self.addLauncher(nodeid, nodelocation)

		# for the clients and mapping
		if 'data transport' in nodelocation \
															and nodelocation['data transport'] is not None:
			datatransportlocation = nodelocation['data transport']
			self.addClient(nodeid, datatransportlocation)
		elif 'launcher' in nodelocation \
															and nodelocation['launcher'] in self.clients:
			self.clients[nodeid] = self.clients[nodelocation['launcher']]
			nodelocation = self.datahandler.query(nodelocation['launcher'])
			nodelocation = nodelocation['location']
		else:
			# weak
			raise RuntimeError('Cannot connect to node')

		# published data of nodeid mapping to location of node
		initializer = {'id': nodeid,
										'location': nodelocation,
										'class string': classstring}
		nodelocationdata = data.NodeLocationData(initializer=initializer)
		self.datahandler.insert(nodelocationdata)

		self.confirmEvent(readyevent)
		self.uiUpdateNodeInfo()

		self.confirmEvent(readyevent)

	def addNodeUIClient(self, nodeid, uilocation):
		if nodeid in self.uiclientcontainers:
			self.deleteNodeUIClient(nodeid)
		clientcontainer = uidata.LargeClientContainer(str(nodeid[-1]), uilocation)
		try:
			self.uicontainer.addObject(clientcontainer)
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
		self.confirmEvent(unavailable_event)

	def deleteNodeUIClient(self, nodeid):
		# also remove from launcher registry
		try:
			name = self.uiclientcontainers[nodeid].name
			del self.uiclientcontainers[nodeid]
			self.uicontainer.deleteObject(name)
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
		nodelocationdata = self.datahandler.query(nodeid)
		if nodelocationdata is not None:
			self.removeNodeData(nodeid)
			self.removeNodeDistmaps(nodeid)
			self.datahandler.remove(nodeid)
			self.delClient(nodeid)
#			self.printerror('node ' + str(nodeid) + ' unregistered')
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

	def launchNode(self, launcher, target, name, dependencies=[]):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		target = name of a class in this launchers node class list
		dependencies = node dependent on to launch
		'''
		nodeid = self.id + (name,)
		nodelocationdata = self.datahandler.query(nodeid)
		if nodelocationdata is not None:
			self.messagelog.warning('Node \'%s\' already exists' % name)
			return nodeid

		args = (launcher, target, nodeid, dependencies)
		t = threading.Thread(name='manager wait node thread',
													target=self.waitNode, args=args)
		t.start()
		return nodeid

	def waitNode(self, launcher, target, nodeid, dependencies):
		args = (nodeid, self.session, self.nodelocations)
		dependencyids = []
		for dependency in dependencies:
			dependencyids.append(('manager', dependency))

		# be dependent on the launcher you're launching from by default
		if launcher not in dependencyids:
			dependencyids.append(launcher)

		self.waitNodes(dependencyids)
		initializer = {'id': self.ID(),
										'targetclass': target,
										'node ID': nodeid,
										'session': self.session,
										'node locations':self.nodelocations}
		ev = event.CreateNodeEvent(initializer=initializer)
		self.outputEvent(ev, launcher, wait=True)

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

	def addNode(self, location, nodeid):
		'''Add a running node to the manager. Sends an event to the location.'''
		e = event.SetManagerEvent(id=self.id, destination=nodeid,
																	location=self.location(),
																	session=self.session)
		client = self.clientclass(location)
		try:
			client.push(e)
		except (IOError, EOFError):
			try:
				hostname = location['TCP transport']['hostname']
			except KeyError:
				hostname = '<unknown host>'
			try:
				tcp_port = location['TCP transport']['port']
			except KeyError:
				tcp_port = '<unknown port>'
			try:
				self.messagelog.error('Failed to add node at ' + hostname + ':'
															+ str(tcp_port))
			except AttributeError:
				pass

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
		launchers = self.launcherdict.keys()
		if launchers:
			launchers.sort()
		else:
			self.messagelog.error('No available launchers to run application')
			return
		self.application.load(name)
		aliases = self.application.getLauncherAliases()
		uialiasselectors = []
		for alias in aliases:
			uialiasselectors.append(uidata.SingleSelectFromList(alias, launchers, 0))
		self.setLauncherSelectors(uialiasselectors)

	def launchApp(self):
		'''Calls application.Application.launch.'''
		if not self.have_selectors:
			return
		for alias in self.uilauncherselectors.uiobjectlist:
			aliasvalue = alias.getSelectedValue()
			self.application.setLauncherAlias(alias.name, (aliasvalue,))
		self.application.launch()

	def killApp(self):
		'''Calls application.Application.kill.'''
		self.application.kill()
		self.setLauncherSelectors(selectors=None)

	def exportApplication(self, filename):
		if filename is None:
			return
		appname = self.uiapplicationlist.getSelectedValue()
		app = importexport.ImportExport()
		dump = app.exportApplication(appname)
		try:
			f = open(filename,'w')
			f.write(dump)
			f.close()
		except IOError,e:
			self.printerror('Unable to export application to "%s"' % filename)

	def importApplication(self, filename):
		if filename is None:
			return
		try:
			appname = self.uiapplicationlist.getSelectedValue()
			app = importexport.ImportExport()
			app.importApplication(filename)
		except ValueError:
			self.printerror('Unable to import application from "%s"' % filename)

	# UI methods
	def uiExportApp(self):
		try:
			self.importexportcontainer.addObject(uidata.SaveFileDialog(
																	'Export Application', self.exportApplication))
		except ValueError:
			pass

	def uiImportApp(self):
		try:
			self.importexportcontainer.addObject(uidata.LoadFileDialog(
																	'Import Application', self.importApplication))
		except ValueError:
			pass

	def uiUpdateNodeInfo(self):
		'''Updates nodes lists and info in UI.'''
		try:
			nodes = self.clients.keys()
			if nodes:
				self.killcontainer.enable()
				self.bindeventcontainer.enable()
				nodes = map(str, nodes)
				nodes.sort()
				selected = 0
			else:
				self.killcontainer.disable()
				self.bindeventcontainer.disable()
				selected = None
			self.uikillselect.set(nodes, selected)
			self.uifromnodeselect.set(nodes, selected)
			self.uitonodeselect.set(nodes, selected)
			self.uinodeinfo.set(self.uiNodeDict())
		except AttributeError:
			pass

	def uiNodeDict(self):
		nodes = self.clients.keys()
		nodeinfo = {}
		for nodeid in nodes:
			nodelocationdata = self.datahandler.query(nodeid)
			if nodelocationdata is not None:
				nodelocation = nodelocationdata['location']
				nodeinfo[str(nodeid)] = nodelocation
				nodeinfo[str(nodeid)]['class'] = nodelocationdata['class string']
		return nodeinfo

	def uiAddNode(self):
		'''UI helper calling addNode. See addNode.'''
		hostname = self.uiaddnodehostname.get()
		if hostname is None:
			self.messagelog.error('No hostname entered for adding a node')
		port = self.uiaddnodeport.get()
		location = {}
		location['TCP transport'] = {}
		location['TCP transport']['hostname'] = hostname
		location['TCP transport']['port'] = port
		self.addNode(location, (hostname,))

	def uiLaunch(self):
		launchername = self.uilauncherselect.getSelectedValue()
		launcherid = self.launcherdict[launchername]['ID']
		nodeclass = self.uiclassselect.getSelectedValue()
		name = self.uilaunchname.get()
		if not name:
			self.messagelog.error('Invalid node name "%s"' % name)
			return
		args = ()
		self.launchNode(launcherid, nodeclass, name)

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
		if fromnodeidstr is None or tonodeidstr is None:
			self.messagelog.error('Invalid node to bind event')
			return
		self.addEventDistmap(eventclass, eval(fromnodeidstr), eval(tonodeidstr))

	def uiDelDistmap(self):
		'''UI function using delEventDistmap. Strings represent event classes and node IDs.'''
		eventclass_str = self.uieventselect.getSelectedValue()
		fromnodeidstr = self.uifromnodeselect.getSelectedValue()
		tonodeidstr = self.uitonodeselect.getSelectedValue()
		self.printerror('unbinding event %s from %s to %s'
										% (eventclass_str, fromnodeidstr, tonodeidstr))
		eventclass = self.uieventclasses[eventclass_str]
		if fromnodeidstr is None or tonodeidstr is None:
			self.messagelog.error('Invalid node to unbind event')
			return
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
			self.messagelog.error('No application selected')

	def uiLaunchApp(self):
		'''UI helper for launchApp. See launchApp.'''
		self.launchApp()

	def uiKillApp(self):
		'''UI helper for killApp. See killApp.'''
		self.killApp()

	def uiLauncherSelectCallback(self, value):
		if value is None:
			launchername = None
		else:
			launchername = self.uilauncherselect.getSelectedValue(value)
		try:
			classes = list(self.launcherdict[launchername]['classes'])
			classes.sort()
			selected = 0
		except KeyError:
			classes = []
			selected = None
		self.uiclassselect.set(classes, selected)
		return value

	def uiSubmitDiaryMessage(self):
		diarymessage = self.diarymessage.get()
		diarydata = data.DiaryData(session=self.session, message=diarymessage)
		self.publish(diarydata, database=True)

	def setLauncherSelectors(self, selectors=None):
		try:
			self.uilauncheraliascontainer.deleteObject('Aliases')
		except:
			pass
		if selectors is None:
			self.have_selectors = False
			self.uilauncherselectors =  uidata.String('Aliases','Load Application First', 'r')
		else:
			self.have_selectors = True
			self.uilauncherselectors = uidata.Container('Aliases')
			self.uilauncherselectors.addObjects(selectors)
		self.uilauncheraliascontainer.addObject(self.uilauncherselectors)

	def defineUserInterface(self):
		'''See node.Node.defineUserInterface.'''
#		node.Node.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Message Log')

		self.uilaunchname = uidata.String('Name', '', 'rw')
		self.uiclassselect = uidata.SingleSelectFromList('Node Class', [], 0)
		self.uilauncherselect = uidata.SingleSelectFromList('Launcher', [], 0)
		self.uilauncherselect.setCallback(self.uiLauncherSelectCallback)
		launchmethod = uidata.Method('Create', self.uiLaunch)
		launchobjects = (self.uilaunchname, self.uilauncherselect,
											self.uiclassselect,
											launchmethod)
		self.launchcontainer = uidata.Container('Create New Node')
		self.launchcontainer.addObjects(launchobjects)


		self.uinodeinfo = uidata.Struct('Node Information', {}, 'r')
		infoobjects = (self.uinodeinfo,)
		self.uiaddnodehostname = uidata.HistoryData(uidata.String, 'Hostname',
																								None, persist=True)
		self.uiaddnodeport = uidata.Integer('TCP Port', 55555, 'rw')
		addmethod = uidata.Method('Add', self.uiAddNode)
		addobjects = (self.uiaddnodehostname, self.uiaddnodeport, addmethod)
		addcontainer = uidata.Container('Add Existing Node')
		addcontainer.addObjects(addobjects)
		self.uikillselect = uidata.SingleSelectFromList('Node', [], 0)
		killmethod = uidata.Method('Kill', self.uiKillNode)
		killobjects = (self.uikillselect, killmethod)
		self.killcontainer = uidata.Container('Kill Node')
		self.killcontainer.addObjects(killobjects)
		nodemanagementcontainer = uidata.LargeContainer('Nodes')
		nodemanagementcontainer.addObjects((self.uinodeinfo, self.launchcontainer,
																				addcontainer, self.killcontainer))

		### Applications

		# import/export container
		self.importexportcontainer = uidata.Container('Import / Export')
		applicationexportmethod = uidata.Method('Export', self.uiExportApp)
		applicationimportmethod = uidata.Method('Import', self.uiImportApp)
		importexportobjects = (applicationexportmethod, applicationimportmethod)
		self.importexportcontainer.addObjects(importexportobjects)


		launchkillcontainer = uidata.Container('Launch / Kill')
		self.uiapplicationlist = uidata.SingleSelectFromList('Application', [], 0)
		self.uiUpdateApplications()
		applicationrefreshmethod = uidata.Method('Refresh', self.uiUpdateApplications)
		applicationloadmethod = uidata.Method('Load', self.uiLoadApp)

		# this container is filled by the setLauncherSelectors() method
		self.uilauncheraliascontainer = uidata.Container('Launcher Selection')
		self.setLauncherSelectors(selectors=None)

		applicationlaunchmethod = uidata.Method('Launch', self.uiLaunchApp)
		applicationkillmethod = uidata.Method('Kill', self.uiKillApp)
		launchkillobjects = (
		 applicationrefreshmethod,
		 self.uiapplicationlist,
		 applicationloadmethod,
		 self.uilauncheraliascontainer,
		 applicationlaunchmethod,
		 applicationkillmethod
		)
		launchkillcontainer.addObjects(launchkillobjects)

		applicationobjects = (
		 launchkillcontainer,
		 self.importexportcontainer,
		)
		self.applicationcontainer = uidata.LargeContainer('Applications')
		self.applicationcontainer.addObjects(applicationobjects)

		## Events
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
		self.bindeventcontainer = uidata.Container('Bind Events')
		self.bindeventcontainer.addObjects(eventobjects)
		eventcontainer = uidata.LargeContainer('Events')
		eventcontainer.addObjects((self.bindeventcontainer,))

		self.diarymessage = uidata.String('Message', '', 'rw')
		diarymethod = uidata.Method('Submit', self.uiSubmitDiaryMessage)
		diarycontainer = uidata.LargeContainer('Diary')
		diarycontainer.addObjects((self.diarymessage, diarymethod))

#		uimanagersetup = self.managersetup.getUserInterface()

		container = uidata.LargeContainer('Manager')

#		container.addObject(uimanagersetup)
		container.addObjects((self.messagelog, nodemanagementcontainer,
													eventcontainer, self.applicationcontainer))
													#, diarycontainer))

		self.uiUpdateNodeInfo()
		self.uiUpdateLauncherInfo()

		self.uicontainer.addObject(container)

if __name__ == '__main__':
	import sys
	import time

	try:
		session = sys.argv[1]
	except IndexError:
		session = time.strftime('%Y-%m-%d-%H-%M')

	initializer = {'name': session}
	m = Manager(('manager',), data.SessionData(initializer=initializer))
	m.start()

