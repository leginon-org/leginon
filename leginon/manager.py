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
import databinder
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
import extendedlogging
import copy

class DataBinder(databinder.DataBinder):
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

	def addBinding(self, nodename, dataclass, method):
		'method must take data instance as first arg'
		try:
			self.bindings[dataclass].append(method)
		except KeyError:
			self.bindings[dataclass] = [method]

	def delBinding(self, nodename, dataclass=None, method=None):
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
	def __init__(self, session, tcpport=None, xmlrpcport=None, **kwargs):
		self.clients = {}

		name = 'Manager'
		self.initializeLogger(name)

		## need a special DataBinder
		mydatabinder = DataBinder(tcpport=tcpport, loggername=self.logger.name)
		node.Node.__init__(self, name, session, otherdatabinder=mydatabinder, xmlrpcport=xmlrpcport, **kwargs)

		self.nodelocations = {}
		self.broadcast = []

		self.uiclientcontainers = {}
		self.uicontainer.xmlrpcserver.register_function(self.uiGetNodeLocations,
																										'getNodeLocations')

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
		# this makes every received event get distributed
		self.addEventInput(event.Event, self.distributeEvents)

		self.launcherdict = {}
		self.managersetup = managersetup.ManagerSetup(self)

	def location(self):
		location = leginonobject.LeginonObject.location(self)
		location['data binder'] = self.databinder.location()
		location['UI'] = self.uicontainer.location()
		return location

	# main/start methods

	def start(self):
		'''Overrides node.Node.start'''
		pass

	def exit(self):
		'''Overrides node.Node.exit'''
		#self.server.exit()

	# client methods

	def addClient(self, name, databinderlocation):
		'''Add a databinder client for a node keyed by the node ID.'''
		self.clients[name] = datatransport.Client(databinderlocation, loggername=self.logger.name)

	def delClient(self, name):
		'''Deleted a client to a node by the node ID.'''
		if name in self.clients:
			del self.clients[name]

	# event methods

	def outputEvent(self, ievent, nodename, wait=False, timeout=None):
		'''
		output an event to a node using node name
		overrides Node.outputEvent, which sends events to manager
		'''
		try:
			client = self.clients[nodename]
		except KeyError:
			return
		ievent['destination'] = nodename
		self.eventToClient(ievent, client, wait, timeout)

	def confirmEvent(self, ievent):
		'''
		override Node.confirmEvent to send confirmation to a node
		'''
		if ievent['confirm'] is not None:
			eventid = ievent['confirm']
			nodename = ievent['node']
			ev = event.ConfirmationEvent(eventid=eventid)
			self.outputEvent(ev, nodename)

	def handleConfirmedEvent(self, ievent):
		'''Event handler for distributing a confirmation event to the node waiting for confirmation of the event.'''
		# handle if this is my own event that has been confirmed
		node.Node.handleConfirmedEvent(self, ievent)

		# no handle if this is a distributed event getting confirmed
		eventid = ievent['eventid']
		## node that just confirmed, not the original node
		nodename = ievent['node']
		if eventid in self.disteventswaiting:
			if nodename in self.disteventswaiting[eventid]:
				self.disteventswaiting[eventid][nodename].set()

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		'''Map distribution of an event of eventclass from a node to a node.'''
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def delEventDistmap(self, eventclass, fromnodename, tonodename=None):
		try:
			self.distmap[eventclass][fromnodename].remove(tonodename)
		except (KeyError, ValueError):
			self.logger.info(str(eventclass) + ': ' + str(fromnodename) + ' to '
												+ str(tonodename) + ' no such binding')
			return

	def broadcastToNode(self, nodename):
		to_node = nodename
		for ievent in self.broadcast:
			### this is a special case of outputEvent
			### so we don't use outputEvent here
			try:
				eventcopy = copy.deepcopy(ievent)
				eventcopy['destination'] = to_node
				self.clients[to_node].push(eventcopy)
			except IOError:
				### bad client, get rid of it
				self.logger.error('Cannot push to node ' + str(to_node)
													+ ', unregistering')
				self.removeNode(to_node)
				self.delLauncher(to_node)
				raise
			self.logEvent(ievent, 'distributed to %s' % (to_node,))

	def distributeEvents(self, ievent):
		'''Push event to eventclients based on event class and source.'''
		if ievent['destination'] is '':
			if ievent['confirm'] is not None:
				raise RuntimeError('not allowed to wait for broadcast event')
			## do every node
			do = list(self.initializednodes)
			## save event for future nodes
			self.broadcast.append(ievent)
		else:
			do = []
		eventclass = ievent.__class__
		from_node = ievent['node']
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
#			self.logger.info('%s event from node %s is not bound to any nodes'
#												% (eventclass.__name__, from_node))
			return

		### set up confirmation event waiting
		ewaits = self.disteventswaiting
		eventid = ievent['confirm']
		if eventid is not None:
			ewaits[eventid] = {}
			for to_node in do:
				ewaits[eventid][to_node] = threading.Event()

		### distribute event
		for to_node in do:
			try:
				### this is a special case of outputEvent
				### so we don't use outputEvent here
				try:
					## want to keep original ievent
					## I have a feeling this may cause a problem with
					## event confirmation since eventcopy will have
					## a new dmid, not sure...
					eventcopy = copy.deepcopy(ievent)
					eventcopy['destination'] = to_node
					self.clients[to_node].push(eventcopy)
				except IOError:
					### bad client, get rid of it
					self.logger.error('Cannot push to node ' + str(to_node)
														+ ', unregistering')
					self.removeNode(to_node)
					self.delLauncher(to_node)
					raise
				self.logEvent(ievent, 'distributed to %s' % (to_node,))
			except:
				self.logger.exception('')
				# make sure we don't wait for confirmation
				if eventid is not None:
					ewaits[eventid][to_node].set()

		### wait for all confirmations to come back
		### the "do" part makes sure we only confirm if events
		### were actually distributed since all events actually
		### come through this handler
		if do and eventid is not None:
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

	def addLauncher(self, nodename, location):
		'''Register a launcher with the UI, aliases the launcher to the node ID, location and launchable node classes.'''
		self.launcherdict[nodename] = {'location': location}
		self.addNodeUIClient(nodename, location['UI'])

	def delLauncher(self, nodename):
		'''Unregister a launcher from the UI.'''
		try:
			del self.launcherdict[nodename]
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
		self.deleteNodeUIClient(nodename)

	def handleNodeClassesPublish(self, ievent):
		'''Event handler for retrieving launchable classes.'''
		launchername = ievent['node']
		nodeclassesdata = ievent['data']
		nodeclasses = nodeclassesdata['nodeclasses']
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
		nodename = readyevent['node']
		if nodename in self.nodelocations:
			self.killNode(nodename)

		nodelocation = readyevent['location']
		classstring = readyevent['nodeclass']

		# check if new node is launcher
		if classstring == 'Launcher':
			self.addLauncher(nodename, nodelocation)

		# for the clients and mapping
		if 'data binder' in nodelocation \
															and nodelocation['data binder'] is not None:
			databinderlocation = nodelocation['data binder']
			self.addClient(nodename, databinderlocation)
		elif 'launcher' in nodelocation \
															and nodelocation['launcher'] in self.clients:
			self.clients[nodename] = self.clients[nodelocation['launcher']]
			nodelocation = self.nodelocations[nodelocation['launcher']]
			nodelocation = nodelocation['location']
		else:
			# weak
			raise RuntimeError('Cannot connect to node')

		# add node location to nodelocations dict
		initializer = {'location': nodelocation,
										'class string': classstring}
		nodelocationdata = data.NodeLocationData(initializer=initializer)
		self.nodelocations[nodename] = nodelocationdata

		self.confirmEvent(readyevent)
		self.uiUpdateNodeInfo()

		self.confirmEvent(readyevent)

	def addNodeUIClient(self, nodename, uilocation):
		if nodename in self.uiclientcontainers:
			self.deleteNodeUIClient(nodename)
		clientcontainer = uidata.LargeClientContainer(nodename, uilocation)
		try:
			self.uicontainer.addObject(clientcontainer)
			self.uiclientcontainers[nodename] = clientcontainer
		except:
			self.logger.exception('cannot add client container for node')

	def unregisterNode(self, unavailable_event):
		'''Event handler for unregistering the node from the manager. Removes all information, event mappings and the client related to the node.'''
		nodename = unavailable_event['node']
		self.removeNode(nodename)
		self.delLauncher(nodename)
		self.uiUpdateNodeInfo()
		self.confirmEvent(unavailable_event)

	def deleteNodeUIClient(self, nodename):
		# also remove from launcher registry
		try:
			del self.uiclientcontainers[nodename]
			self.uicontainer.deleteObject(nodename)
		except:
			self.logger.exception('cannot delete client container for node')

	def handleNodeStatus(self, ievent):
		nodename = ievent['node']
		if isinstance(ievent, event.NodeInitializedEvent):
			self.setNodeStatus(nodename, True)
			self.broadcastToNode(nodename)
		elif isinstance(ievent, event.NodeUninitializedEvent):
			self.setNodeStatus(nodename, False)
		self.confirmEvent(ievent)

	def setNodeStatus(self, nodename, status):
		self.initializednodescondition.acquire()
		if status:
			if nodename not in self.initializednodes:
				self.initializednodes.append(nodename)
				self.initializednodescondition.notifyAll()
		else:
			if nodename in self.initializednodes:
				self.initializednodes.remove(nodename)
				self.initializednodescondition.notifyAll()
		self.initializednodescondition.release()

	def removeNode(self, nodename):
		'''Remove data, event mappings, and client for the node with the specfied node ID.'''
		if nodename in self.nodelocations:
			self.removeNodeDistmaps(nodename)
			del self.nodelocations[nodename]
			self.delClient(nodename)
		else:
			self.logger.error('Manager: node ' + str(nodename) + ' does not exist')

	def removeNodeDistmaps(self, nodename):
		'''Remove event mappings related to the node with the specifed node ID.'''
		# needs to completely cleanup the distmap
		for eventclass in self.distmap:
			try:
				del self.distmap[eventclass][nodename]
			except KeyError:
				pass
			for othernodename in self.distmap[eventclass]:
				try:
					self.distmap[eventclass][othernodename].remove(nodename)
				except ValueError:
					pass

	def launchNode(self, launcher, target, name, dependencies=[]):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		target = name of a class in this launchers node class list
		dependencies = node dependent on to launch
		'''
		if name in self.nodelocations:
			self.messagelog.warning('Node \'%s\' already exists' % name)
			return name

		args = (launcher, target, name, dependencies)
		t = threading.Thread(name='manager wait node thread',
													target=self.waitNode, args=args)
		t.start()
		return name

	def waitNode(self, launcher, target, name, dependencies):
		dependencyids = []
		for dependency in dependencies:
			dependencyids.append(('manager', dependency))

		# be dependent on the launcher you're launching from by default
		if launcher not in dependencyids:
			dependencyids.append(launcher)

		self.waitNodes(dependencyids)
		initializer = {'targetclass': target,
										'node': name,
										'session': self.session,
										'manager location':self.location()}
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

	def addNode(self, location, nodename):
		'''Add a running node to the manager. Sends an event to the location.'''
		e = event.SetManagerEvent(destination=nodename,
																	location=self.location(),
																	session=self.session)
		client = datatransport.Client(location, loggername=self.logger.name)
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

	def killNode(self, nodename):
		'''Attempt telling a node to die and unregister. Unregister if communication with the node fails.'''
		ev = event.KillEvent()
		try:
			self.outputEvent(ev, nodename)
		except:
			self.logger.exception('cannot push KillEvent to ' + nodename
														+ ', unregistering')
			# maybe didn't uninitialized
			self.setNodeStatus(nodename, False)
			# group into another function
			self.removeNode(nodename)
			# also remove from launcher registry
			self.delLauncher(nodename)

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
		for alias in self.uilauncherselectors.values():
			aliasvalue = alias.getSelectedValue()
			self.application.setLauncherAlias(alias.name, aliasvalue)
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
			self.logger.exception('Unable to export application to "%s"' % filename)

	def importApplication(self, filename):
		if filename is None:
			return
		try:
			appname = self.uiapplicationlist.getSelectedValue()
			app = importexport.ImportExport()
			app.importApplication(filename)
		except ValueError:
			self.logger.exception('Unable to import application from "%s"' % filename)

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
		for nodename in nodes:
			if nodename in self.nodelocations:
				nodelocationdata = self.nodelocations[nodename]
				nodelocation = nodelocationdata['location']
				nodeinfo[nodename] = nodelocation
				nodeinfo[nodename]['class'] = nodelocationdata['class string']
		return nodeinfo

	def uiAddNode(self):
		'''UI helper calling addNode. See addNode.'''
		self.addmethod.disable()
		hostname = self.uiaddnodehostname.get()
		if not hostname:
			self.messagelog.error('No hostname entered for adding a node')
			self.addmethod.enable()
			return
		port = self.uiaddnodeport.get()
		location = {}
		location['TCP transport'] = {}
		location['TCP transport']['hostname'] = hostname
		location['TCP transport']['port'] = port
		self.addNode(location, hostname)
		self.addmethod.enable()

	def uiLaunch(self):
		launchername = self.uilauncherselect.getSelectedValue()
		nodeclass = self.uiclassselect.getSelectedValue()
		name = self.uilaunchname.get()
		if not name:
			self.messagelog.error('Invalid node name "%s"' % name)
			return
		self.launchNode(launchername, nodeclass, name)

	def uiKillNode(self):
		'''UI helper calling killNode, using str node aliases. See killNode.'''
		value = self.uikillselect.getSelectedValue()
		self.killNode(value)

	def uiAddDistmap(self):
		'''UI function using addEventDistmap. Strings represent event classes and node IDs.'''
		eventclass_str = self.uieventselect.getSelectedValue()
		fromnodenamestr = self.uifromnodeselect.getSelectedValue()
		tonodenamestr = self.uitonodeselect.getSelectedValue()
		self.logger.info('binding event %s from %s to %s'
											% (eventclass_str, fromnodenamestr, tonodenamestr))
		eventclass = self.uieventclasses[eventclass_str]
		if fromnodenamestr is None or tonodenamestr is None:
			self.messagelog.error('Invalid node to bind event')
			return
		self.addEventDistmap(eventclass, fromnodenamestr, tonodenamestr)

	def uiDelDistmap(self):
		'''UI function using delEventDistmap. Strings represent event classes and node IDs.'''
		eventclass_str = self.uieventselect.getSelectedValue()
		fromnodenamestr = self.uifromnodeselect.getSelectedValue()
		tonodenamestr = self.uitonodeselect.getSelectedValue()
		self.logger.info('unbinding event %s from %s to %s'
											% (eventclass_str, fromnodenamestr, tonodenamestr))
		eventclass = self.uieventclasses[eventclass_str]
		if fromnodenamestr is None or tonodenamestr is None:
			self.messagelog.error('Invalid node to unbind event')
			return
		self.delEventDistmap(eventclass, fromnodenamestr, tonodenamestr)

	def uiGetNodeLocations(self):
		'''UI helper for mapping a node alias to the node's location.'''
		nodelocations = self.uiNodeDict()
		nodelocations[self.name] = self.location()
		return nodelocations

	def uiUpdateApplications(self):
		applicationdatalist = self.research(dataclass=data.ApplicationData)
		applicationnamelist = []
		for applicationdata in applicationdatalist:
			name = applicationdata['name']
			if name not in applicationnamelist:
				applicationnamelist.append(name)
		applicationnamelist.sort()
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
		#node.Node.defineUserInterface(self)
		self.messagelog = uidata.MessageLog('Message Log')

		self.uinodeinfo = uidata.Struct('Node Information', {}, 'r',
																	tooltip='Information about current running '
																	+ 'nodes including their class and location')

		self.uilaunchname = uidata.String('Name', '', 'rw',
															tooltip='Name to assign node when it is created')
		self.uilauncherselect = uidata.SingleSelectFromList('Launcher', [], 0,
															tooltip='Launcher to create node on')
		self.uiclassselect = uidata.SingleSelectFromList('Node Class', [], 0,
															tooltip='Class of node to be created')
		self.uilauncherselect.setCallback(self.uiLauncherSelectCallback)
		launchmethod = uidata.Method('Create', self.uiLaunch,
																	tooltip='Create a new node')
		launchobjects = (self.uilaunchname, self.uilauncherselect,
											self.uiclassselect)
		self.launchcontainer = uidata.Container('Create New Node')
		self.launchcontainer.addObjects(launchobjects)
		self.launchcontainer.addObject(launchmethod,
																		position={'justify': ['right']})

		self.uiaddnodehostname = uidata.HistoryData(uidata.String, 'Hostname',
																								None, persist=True)
		self.uiaddnodeport = uidata.Integer('TCP Port', 55555, 'rw', size=(5, 1))
		self.addmethod = uidata.Method('Add', self.uiAddNode)
		addcontainer = uidata.Container('Add Existing Node')
		addcontainer.addObject(self.uiaddnodehostname,
														position={'position': (0, 0),
																			'span': (1, 2)})
		addcontainer.addObject(self.uiaddnodeport,
														position={'position': (1, 0)})
		addcontainer.addObject(self.addmethod, position={'position': (1, 1),
																											'justify': ['right']})

		self.uikillselect = uidata.SingleSelectFromList('Node', [], 0)
		killmethod = uidata.Method('Kill', self.uiKillNode)
		killobjects = (self.uikillselect, killmethod)
		self.killcontainer = uidata.Container('Kill Node')
		self.killcontainer.addObjects(killobjects)

		self.killcontainer.positionObject(self.uikillselect, {'position': (0, 0)})
		self.killcontainer.positionObject(killmethod, {'position': (0, 1)})

		nodemanagementcontainer = uidata.LargeContainer('Nodes')
		nodemanagementcontainer.addObject(self.launchcontainer,
																			position={'position': (0, 0),
																								'expand': 'all'})
		nodemanagementcontainer.addObject(addcontainer,
																			position={'position': (1, 0),
																								'expand': 'all'})
		nodemanagementcontainer.addObject(self.killcontainer,
																			position={'position': (2, 0),
																								'expand': 'all'})
		nodemanagementcontainer.addObject(self.uinodeinfo,
																			position={'position': (0, 1),
																								'span': (3, 1),
																								'justify': ['center']})

		### Applications

		# import/export container
		self.importexportcontainer = uidata.Container('Import / Export')
		applicationexportmethod = uidata.Method('Export', self.uiExportApp)
		applicationimportmethod = uidata.Method('Import', self.uiImportApp)
		self.importexportcontainer.addObject(applicationimportmethod,
																					position={'position': (0, 0)})
		self.importexportcontainer.addObject(applicationexportmethod,
																					position={'position': (0, 1)})


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
		launchkillcontainer.addObject(self.uiapplicationlist,
																	position={'position': (0, 0)})
		launchkillcontainer.addObject(applicationrefreshmethod,
																	position={'position': (0, 1)})
		launchkillcontainer.addObject(applicationloadmethod,
																	position={'position': (1, 1)})
		launchkillcontainer.addObject(self.uilauncheraliascontainer,
																	position={'position': (1, 0), 'span': (3, 1)})
		launchkillcontainer.addObject(applicationlaunchmethod,
																	position={'position': (2, 1)})
		launchkillcontainer.addObject(applicationkillmethod,
																	position={'position': (3, 1)})

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
		self.bindeventcontainer.positionObject(self.uifromnodeselect,
																					{'position': (0, 0), 'span': (1, 2)})
		self.bindeventcontainer.positionObject(self.uieventselect,
																					{'position': (1, 0), 'span': (1, 2)})
		self.bindeventcontainer.positionObject(self.uitonodeselect,
																					{'position': (2, 0), 'span': (1, 2)})
		self.bindeventcontainer.positionObject(bindmethod,
																					{'position': (3, 0),
																						'justify': ['center', 'right']})
		self.bindeventcontainer.positionObject(unbindmethod,
																					{'position': (3, 1),
																						'justify': ['center', 'left']})

		eventcontainer = uidata.LargeContainer('Events')
		eventcontainer.addObjects((self.bindeventcontainer,))

		self.diarymessage = uidata.String('Message', '', 'rw')
		diarymethod = uidata.Method('Submit', self.uiSubmitDiaryMessage)
		diarycontainer = uidata.LargeContainer('Diary')
		diarycontainer.addObjects((self.diarymessage, diarymethod))

#		uimanagersetup = self.managersetup.getUserInterface()

		container = uidata.LargeContainer('Manager')

		#self.initializeLoggerUserInterface()

		# cheat a little here
		clientlogger = extendedlogging.getLogger(self.logger.name + '.'
																							+ datatransport.Client.__name__)
		if clientlogger.container not in self.logger.container.values():
			self.logger.container.addObject(clientlogger.container,
																			position={'span': (1,2), 'expand': 'all'})

#		container.addObject(uimanagersetup)
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((self.logger.container, nodemanagementcontainer,
													eventcontainer, self.applicationcontainer))

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

