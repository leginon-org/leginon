#!/usr/bin/env python

#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#

import application
import applications
from leginon import leginondata
import databinder
import datatransport
import event
import importexport
import leginonconfig
import launcher
import node
import threading
import logging
import copy
from pyami import moduleconfig
from pyami import ordereddict
from pyami import mysocket
# autotask
from leginon import autotask

from sinedon import directq

import socket
from wx import PyDeadObjectError
import gui.wx.Manager
import noderegistry
import remotecall
import time
import sys
import remoteserver

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
			# doing it to all keys
			dataclasses = list(self.bindings)
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
	objectserviceclass = remotecall.ManagerObjectService
	def __init__(self, session, tcpport=None, **kwargs):
		self.clients = {}

		self.name = 'Manager'
		self.initializeLogger()

		## need a special DataBinder
		name = DataBinder.__name__
		databinderlogger = gui.wx.LeginonLogging.getNodeChildLogger(name, self)
		mydatabinder = DataBinder(self, databinderlogger, tcpport=tcpport)
		node.Node.__init__(self, self.name, session, otherdatabinder=mydatabinder,
												**kwargs)

		self.objectservice = self.objectserviceclass(self)

		self.launcher = None
		self.frame = None

		self.nodelocations = {}
		self.broadcast = []

		self.tem_host = ''
		# notify user of logged error
		self.notifyerror = False
		# timeout timer
		self.timer_debug = False
		self.timeout_minutes = 30.0
		if self.timer_debug:
			self.timeout_minutes = 0.3
		self.timer = None
		self.timer_thread_lock = False

		# auto run testing
		self.autorun = False
		self.autogridslot = None
		self.autostagez = None
		self.auto_task = None
		self.square_finder_class_names = []
		self.mosaic_target_receiver = None
		self.auto_atlas_done = threading.Event()
		self.auto_done = threading.Event()
		# manager pause
		self.pausable_nodes = []
		self.paused_nodes = []

		# ready nodes, someday 'initialized' nodes
		self.initializednodescondition = threading.Condition()
		self.initializednodes = []
		self.distmap = {}
		# maps event id to list of node it was distributed to if event['confirm']
		self.disteventswaiting = {}

		self.application = None
		self.appnodes = []
		self.applicationevent = threading.Event()

		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent,
															self.handleNodeClassesPublish)
		self.addEventInput(event.NodeInitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.NodeUninitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.NodeLogErrorEvent, self.handleNodeLogError)
		self.addEventInput(event.ActivateNotificationEvent, self.handleNotificationStatus)
		self.addEventInput(event.DeactivateNotificationEvent, self.handleNotificationStatus)
		self.addEventInput(event.NodeBusyNotificationEvent, self.handleNodeBusyNotification)
		self.addEventInput(event.AutoDoneNotificationEvent, self.handleAutoDoneNotification)
		self.addEventInput(event.MosaicTargetReceiverNotificationEvent, self.handleMosaicTargetReceiverNotification)
		self.addEventInput(event.ManagerPauseAvailableEvent, self.handleManagerPauseAvailable)
		self.addEventInput(event.ManagerPauseNotAvailableEvent, self.handleManagerPauseNotAvailable)
		self.addEventInput(event.ManagerContinueAvailableEvent, self.handleManagerContinueAvailable)
		self.addEventInput(event.ManagerPauseEvent, self.handleManagerPause)
		self.addEventInput(event.ManagerContinueEvent, self.handleManagerContinue)
		# this makes every received event get distributed
		self.addEventInput(event.Event, self.distributeEvents)

		self.launcherdict = {}

	def waitForLaunchersReady(self, hostnames):
		for i in range(10):
			ready = True
			for hostname in hostnames:
				if hostname not in self.initializednodes:
					ready = False
			if ready:
				return
			time.sleep(1)
		sys.exit()

	def launchPreviousApp(self):
		names,launchers = self.getApplicationHistory()
		prevname = names[0]
		prevlaunchers = launchers[prevname]

		hostnames = [p[1] for p in prevlaunchers]
		self.waitForLaunchersReady(hostnames)
		#TODO: simulator still need a bit longer. Maybe ready too fast
		time.sleep(5)
		app = application.Application(self, prevname)
		app.load()
		for alias,hostname in prevlaunchers:
			app.setLauncherAlias(alias, hostname)
		self.runApplication(app)

	def run(self, session, clients, prevapp=False, gridslot=None, stagez=None, auto_task=None):
		self.session = session
		self.frame.session = self.session

		t = threading.Thread(name='create launcher thread',
													target=self.createLauncher)
		t.start()

		for client in clients:
			port = self.getPrimaryPort(client)
			try:
				self.addLauncher(client, port)
			except Exception, e:
				self.logger.warning('Failed to add launcher: %s' % e)

		if gridslot and auto_task is not None:
			self.autorun = True
			self.autogridslot = gridslot
			# None, 'atlas','full'
			self.auto_task = auto_task
		if stagez is not None:
			# float
			self.autostagez = stagez
		if prevapp:
			threading.Thread(target=self.launchPreviousApp).start()

	def getPrimaryPort(self, hostname):
		r = leginondata.ClientPortData(hostname=hostname).query()
		if not r:
			return 55555
		else:
			return r[0]['primary port']

	def getSessionByName(self, name):
		qsession = leginondata.SessionData(name=name)
		sessions = self.research(qsession, results=1)
		if sessions:
			session = sessions[0]
		else:
			session = None
		return session

	def setSessionByName(self, name):
		new_session = self.getSessionByName(name)
		if not new_session:
			print 'Cannot find existing session %s to set' % (name,)
		self.session = new_session
		## do every node
		do = list(self.initializednodes)
		for to_node in do:
			out = event.SetSessionEvent()
			out['session'] = self.session
			self.sendManagerNotificationEvent(to_node, out)
		self.frame.SetTitle('Leginon:  %s' % (name,))

	def onAddLauncherPanel(self, l):
		evt = gui.wx.Manager.AddLauncherPanelEvent(l)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def createLauncher(self):
		self.launcher = launcher.Launcher(mysocket.gethostname().lower(),
																			session=self.session,
																			managerlocation=self.location())
		self.onAddLauncherPanel(self.launcher)

	def location(self):
		location = {}
		location['hostname'] = mysocket.gethostname().lower()
		location['data binder'] = self.databinder.location()
		return location

	# main/start methods

	def start(self):
		'''Overrides node.Node.start'''
		pass

	def exit(self):
		self.cancelTimeoutTimer()
		# do not let others to restart it
		self.timer = False
		if self.launcher is not None:
			self.killNode(self.launcher.name, wait=True)
		launchers = self.getLauncherNames()
		nodes = self.getNodeNames()
		for node in nodes:
			if node not in launchers:
				self.killNode(node, wait=True)
		try:
			self.objectservice._exit()
		except (AttributeError, TypeError):
			pass
		self.databinder.exit()

	# client methods

	def addClient(self, name, databinderlocation):
		'''Add a databinder client for a node keyed by the node ID.'''
		self.clients[name] = datatransport.Client(databinderlocation,
																							self.clientlogger)

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
		return self.eventToClient(ievent, client, wait, timeout)

	def confirmEvent(self, ievent, status='ok'):
		'''
		override Node.confirmEvent to send confirmation to a node
		'''
		if ievent['confirm'] is not None:
			eventid = ievent['confirm']
			nodename = ievent['node']
			ev = event.ConfirmationEvent(eventid=eventid, status=status)
			self.outputEvent(ev, nodename)
			ievent['confirm'] = None

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


	def sendManagerNotificationEvent(self, to_node, ievent):
		'''
		Send a manager initiated event to a specific node. Unlike broadcast,
		this is specific, but also requires no node-to-node binding.
		'''
		try:
			eventcopy = copy.copy(ievent)
			eventcopy['destination'] = to_node
			self.clients[to_node].send(eventcopy)
		except datatransport.TransportError:
			### bad client, get rid of it
			self.logger.error('Cannot send from manager to node ' + str(to_node))
			raise
		self.logEvent(ievent, 'sent by manager to %s' % (to_node,))

	def broadcastToNode(self, nodename):
		to_node = nodename
		for ievent in self.broadcast:
			### this is a special case of outputEvent
			### so we don't use outputEvent here
			try:
				eventcopy = copy.copy(ievent)
				eventcopy['destination'] = to_node
				self.clients[to_node].send(eventcopy)
			except datatransport.TransportError:
				### bad client, get rid of it
				self.logger.error('Cannot send to node ' + str(to_node)
													+ ', unregistering')
				self.removeNode(to_node)
				raise
			self.logEvent(ievent, 'distributed to %s' % (to_node,))

	def distributeEvents(self, ievent):
		'''Push event to eventclients based on event class and source.'''
		## possible destinations are:
		## 1) all nodes  (if destination set to empty string)
		## 2) use application event bindings (destination is None)
		## 3) one node  (destination set to node name)
		if ievent['destination'] is '':
			if ievent['confirm'] is not None:
				raise RuntimeError('not allowed to wait for broadcast event')
			## do every node
			do = list(self.initializednodes)
			## save event for future nodes
			self.broadcast.append(ievent)
		elif ievent['destination'] is None:
			do = []
		else:
			do = [ievent['destination']]
		eventclass = ievent.__class__
		from_node = ievent['node']
		if not do:
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
			self.logger.debug('%s event from %s is not bound to any nodes' % (eventclass.__name__, from_node))
			if ievent['confirm'] is not None:
				## should let sender know about problem
				self.confirmEvent(ievent, 'no binding')
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
					eventcopy = copy.copy(ievent)
					eventcopy['destination'] = to_node
					self.clients[to_node].send(eventcopy)
					# Something will be sending an event to others if automated.
				except datatransport.TransportError:
					### bad client, get rid of it
					self.logger.error('Cannot send to node ' + str(to_node)
														+ ', unregistering')
					self.removeNode(to_node)
					raise
				self.logEvent(ievent, 'distributed to %s' % (to_node,))
			except Exception, e:
				self.logger.exception('Error distributing events: %s' % e)
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

	def onAddLauncher(self, name):
		evt = gui.wx.Manager.AddLauncherEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onRemoveLauncher(self, name):
		evt = gui.wx.Manager.RemoveLauncherEvent(name)
		try:
			self.frame.GetEventHandler().AddPendingEvent(evt)
		except PyDeadObjectError:
			pass

	def getLauncherCount(self):
		return len(self.launcherdict)

	def getLauncherNames(self, sorted=True):
		names = self.launcherdict.keys()
		if sorted:
			names.sort()
		return names

	def getLauncherClasses(self, name=None, sorted=True):
		if name is None:
			classes = {}
			for name in self.getLauncherNames():
				classes[name] = self.getLauncherClasses(name, sorted)
		else:
			try:
				classes = list(self.launcherdict[name]['classes'])
			except KeyError:
				raise ValueError('invalid launcher name')
			if sorted:
				classes.sort()
		return classes

	def _addLauncher(self, name, location):
		'''Add launcher to mapping, add UI client.'''
		if name in self.getLauncherNames():
			raise RuntimeError('launcher name in use')
		self.launcherdict[name] = {'location': location}
		self.onAddLauncher(name)

	def delLauncher(self, name):
		'''Remove launcher from mapping and UI.'''
		try:
			del self.launcherdict[name]
		except KeyError:
			return
		self.onRemoveLauncher(name)

	def handleNodeClassesPublish(self, ievent):
		'''Event handler for retrieving launchable classes.'''
		launchername = ievent['node']
		nodeclassesdata = ievent['data']
		nodeclasses = nodeclassesdata['nodeclasses']
		if nodeclasses is None:
			del self.launcherdict[launchername]
		else:
			self.launcherdict[launchername]['classes'] = nodeclasses
		self.confirmEvent(ievent)

	# node related methods

	def getNodeCount(self):
		return len(self.nodelocations)

	def getNodeClass(self, name):
		nodelocationdata = self.nodelocations[name]
		classname = nodelocationdata['class string']
		if self.isLauncher(classname):
			return launcher.Launcher
		else:
			nodeclass = noderegistry.getNodeClass(classname)
		return nodeclass

	def getNodeEventIO(self, name):
		nodeclass = self.getNodeClass(name)
		return {'inputs': nodeclass.eventinputs, 'outputs': nodeclass.eventoutputs}

	def getNodeNames(self, sorted=True):
		names = self.nodelocations.keys()
		if sorted:
			names.sort()
		return names

	def isLauncher(self, name):
		if name == 'Launcher':
			return True
		return False

	def setNodeClient(self, name, location):
		# if the node has a data binder, add it as a client
		if location['data binder'] is not None:
			self.addClient(name, location['data binder'])
		# otherwise use the node's launcher's client
		elif location['launcher'] in self.clients:
			launchername = location['launcher']
			try:
				self.clients[name] = self.clients[location['launcher']]
			except KeyError:
				raise RuntimeError('launcher specified by node has no client')
			try:
				nodelocationdata = self.nodelocations[launchername]
			except KeyError:
				raise RuntimeError('launcher specified by node has no location data')
			return nodelocationdata['location']
		else:
			raise RuntimeError('unable to find client for node')
		return location

	def registerNode(self, evt):
		'''
		Event handler for registering a node with the manager.  Initializes a
		client for the node and adds information regarding the node's location.
		'''

		name = evt['node']
		location = evt['location']
		classname = evt['nodeclass']

		# kill the node if it already exists. needs work.
		if name in self.getNodeNames():
			self.killNode(name)

		# check if new node is launcher.
		if self.isLauncher(classname):
			self._addLauncher(name, location)

		location = self.setNodeClient(name, location)

		# add node location to nodelocations dict
		initializer = {'location': location, 'class string': classname}
		self.nodelocations[name] = leginondata.NodeLocationData(initializer=initializer)

		self.confirmEvent(evt)

		if name in self.appnodes:
			self.onApplicationNodeStarted(name)
			self.appnodes.remove(name)
			if not self.appnodes:
				self.applicationevent.set()
		self.onAddNode(name)

	def onAddNode(self, name, status='ok'):
		evt = gui.wx.Manager.AddNodeEvent(name, status)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onRemoveNode(self, name):
		evt = gui.wx.Manager.RemoveNodeEvent(name)
		try:
			self.frame.GetEventHandler().AddPendingEvent(evt)
		except PyDeadObjectError:
			pass
		except RuntimeError:
			pass

	def unregisterNode(self, evt):
		'''Event handler Removes all information, event mappings and the client.'''
		nodename = evt['node']
		self.removeNode(nodename)
		self.confirmEvent(evt)

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

	def removeNode(self, name):
		'''Remove data, event mappings, and client.'''
		if name in self.nodelocations:
			self.removeNodeDistmaps(name)
			del self.nodelocations[name]
			self.delClient(name)
			self.delLauncher(name)
			self.onRemoveNode(name)
		else:
			self.logger.error('Manager: node ' + str(nodename) + ' does not exist')

	def removeNodeDistmaps(self, nodename):
		'''Remove event mappings related to the node with the specifed node ID.'''
		# needs to completely cleanup the distmap
		for eventclass in list(self.distmap):
			try:
				del self.distmap[eventclass][nodename]
			except KeyError:
				pass
			# prevent self.distmap change size error by making a copy of the keys.
			for othernodename in list(self.distmap[eventclass]):
				try:
					self.distmap[eventclass][othernodename].remove(nodename)
				except (KeyError, ValueError, RuntimeError) :
					pass

	def launchNode(self, launcher, target, name, dependencies=[]):
		'''
		Launch a node with a launcher node.
		launcher = id of launcher node
		target = name of a class in this launchers node class list
		dependencies = node dependent on to launch
		'''
		if name in self.nodelocations:
			self.logger.warning('Node \'%s\' already exists' % name)
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
										'manager location': self.location()}
		evt = event.CreateNodeEvent(initializer=initializer)
		cevt = self.outputEvent(evt, launcher, wait=True)
		status =  cevt['status']
		if status == 'failed':
			if name in self.appnodes:
				self.onApplicationNodeStarted(name, status)
				self.appnodes.remove(name)
				if not self.appnodes:
					self.applicationevent.set()
			self.onAddNode(name, status)

	def waitNodes(self, nodes):
		self.initializednodescondition.acquire()
		while not self.sublist(nodes, self.initializednodes):
			self.initializednodescondition.wait(0.01)
		self.initializednodescondition.release()

	# probably an easier way
	def sublist(self, list1, list2):
		'''returns True if all elements in list1 are in list2, otherwise False'''
		for i in list1:
			if i not in list2:
				return False
		return True

	def updateNodeOrder(self, nodeclasses=[]):
		nodeorder = self.sortNodes(nodeclasses)
		# broadcast?
		for launcher in self.launcherdict:
			evt = event.NodeOrderEvent(order=nodeorder)
			self.outputEvent(evt, launcher)

	def addLauncher(self, hostname, port):
		location = {}
		location['TCP transport'] = {}
		location['TCP transport']['hostname'] = hostname
		location['TCP transport']['port'] = port
		self.addNode(hostname, location)

	def addNode(self, name, location):
		'''Add a running node to the manager. Sends an event to the location.'''
		initializer = {'destination': name,
										'location': self.location(),
										'session': self.session}
		e = event.SetManagerEvent(initializer=initializer)
		client = datatransport.Client(location, self.clientlogger)
		try:
			client.send(e)
		except datatransport.TransportError:
			try:
				hostname = location['TCP transport']['hostname']
			except KeyError:
				hostname = '<unknown host>'
			try:
				tcp_port = location['TCP transport']['port']
			except KeyError:
				tcp_port = '<unknown port>'
			try:
				self.logger.error('Failed to add node at ' + hostname + ':'
															+ str(tcp_port))
			except AttributeError:
				pass

	def killNode(self, nodename, **kwargs):
		'''Attempt telling a node to die and unregister. Unregister if communication with the node fails.'''
		ev = event.KillEvent()
		try:
			self.outputEvent(ev, nodename, **kwargs)
		except:
			self.logger.exception('cannot send KillEvent to ' + nodename
														+ ', unregistering')
			# maybe didn't get uninitialized
			self.setNodeStatus(nodename, False)
			# group into another function
			self.removeNode(nodename)

##############################
# Leginon Remote Requirement
	def handleManagerPauseAvailable(self, ievent):
		self._addPausableNode(ievent['node'])
		self._removePausedNode(ievent['node'])

	def handleManagerPauseNotAvailable(self, ievent):
		self._removePausableNode(ievent['node'])
		self._removePausedNode(ievent['node'])

	def handleManagerPause(self, ievent):
		for to_node in self.pausable_nodes:
			out = event.PauseEvent()
			self.sendManagerNotificationEvent(to_node, out)

	def handleManagerContinueAvailable(self, ievent):
		self._removePausableNode(ievent['node'])
		self._addPausedNode(ievent['node'])

	def handleManagerContinue(self, ievent):

		if len(self.paused_nodes) >= 1:
			self.logger.warning('Continue the most recently paused node')
			to_nodes = self.paused_nodes
			if not ievent['all']:
				to_nodes = [self.paused_nodes[-1],]
			for to_node in to_nodes:
				out = event.ContinueEvent()
				self.sendManagerNotificationEvent(to_node, out)

	def _addPausableNode(self, nodename):
		if nodename not in self.pausable_nodes:
			self.pausable_nodes.append(nodename)

	def _removePausableNode(self, nodename):
		try:
			self.pausable_nodes.remove(nodename)
		except ValueError:
			# not in the list
			pass

	def _addPausedNode(self, nodename):
		if nodename not in self.paused_nodes:
			self.paused_nodes.append(nodename)

	def _removePausedNode(self, nodename):
		try:
			self.paused_nodes.remove(nodename)
		except ValueError:
			# not in the list
			pass

##############################
# Timeout Timer/Error SlackNotification
	def handleNodeBusyNotification(self, ievent):
		self.restartTimeoutTimer()

	def cancelTimeoutTimer(self):
			if hasattr(self.timer,'is_alive') and self.timer.is_alive():
				self.timer.cancel()
				if self.timer_debug:
					print 'timer canceled'

	def slackTimeoutNotification(self, msg = ''):
		timeout = self.timeout_minutes*60.0
		if not msg:
			msg = 'Leginon has been idle for %.1f minutes' % self.timeout_minutes
		self.slackNotification(msg)
		evt = event.IdleNotificationEvent(destination='')
		self.distributeEvents(evt)
		self.timer = False

	def setTimeoutTimerStatus(self, status):
		'''
		Set timeout timer/error notification active status to True or False.
		'''
		evt = event.SetNotificationStatusEvent(destination='')
		evt['active'] = status
		self.distributeEvents(evt)

	def restartTimeoutTimer(self):
		'''
		Restart timeout timer is called when certain events are
		sent to manager to indicate that Leginon is still busy.
		Add NodeBusyNotificationEvent in the node that need to send
		the notification.
		'''
		# Multiply thread may access this. Now that we monitor only
		# sparsed event, this may not be as critical.  Leave it for now.
		if self.timer_thread_lock:
			return
		self.timer_thread_lock = True
		self._restartTimeoutTimer()
		self.timer_thread_lock = False

	def _restartTimeoutTimer(self):
		'''
		Restart timeout timer if self.timer is not False.
		Possible self timer values:
		None: Default and the value when notification is not active.
		False: The value to stop new Timer to be started to avoid
			hanging when Leginon is shutting down and new notification
			to be sent after it is already sent.
		'''
		if not self.notifyerror:
			self.cancelTimeoutTimer()
			self.timer = None
			return
		if self.timer == False:
			return
		self.cancelTimeoutTimer()
		# canceled timer can not be restarted. make a new one.
		timeout = self.timeout_minutes*60.0
		self.timer = threading.Timer(timeout,self.slackTimeoutNotification)
		self.timer.start()
		if self.timer_debug:
			print('timer restarted with timeout set to %.0f sec' % timeout)

	# Node Error Notification
	def handleNodeLogError(self, ievent):
		msg = ievent['message']
		if self.notifyerror:
			self.slackNotification(msg)

	def handleNotificationStatus(self, ievent):
		'''
		Handle (De)ActivateNotificationEvent from PresetsManager.
		'''
		nodename = ievent['node']
		if isinstance(ievent, event.ActivateNotificationEvent):
			self.tem_host = ievent['tem_host']
			if not ievent['silent']:
				self.timeout_minutes = ievent['timeout_minutes']
				msg = '%.1f minutes timeout and error notification is activated' % (self.timeout_minutes)
				self.slackNotification(msg)
			# reset
			self.notifyerror = True
			# first allow timer to restart, if was set to false by completing a timeout
			if self.timer == False:
				self.timer = None
			self.restartTimeoutTimer()
		elif isinstance(ievent, event.DeactivateNotificationEvent):
			self.cancelTimeoutTimer()
			self.timer = None
			self.notifyerror = False

	def slackNotification(self, msg):
		msg = '%s %s' % (self.tem_host, msg)
		try:
			from slack import slack_interface
			slack_inst = slack_interface.SlackInterface()
			channel = slack_inst.getDefaultChannel()
			slack_inst.sendMessage(channel,'%s ' % (msg))
		except:
			print msg

	# application methods

	def handleAutoDoneNotification(self, ievent):
		if ievent['task'] == 'atlas':
			self.auto_atlas_done.set()
		if self.auto_task == 'full':
			# since all acquisition node send this event, make sure it is the right one.
			if self.mosaic_target_receiver and ievent['node'] == self.mosaic_target_receiver:
				self.auto_done.set()

	def handleMosaicTargetReceiverNotification(self, ievent):
		# set node alias that mosaic click target finder that sends targets to.  The targetlist done
		# from there signals end of full auto task
		self.mosaic_target_receiver = ievent['receiver']

	def getBuiltinApplications(self):
		apps = [appdict['application'] for appdict in applications.builtin.values()]
		return apps

	def getApplicationNames(self,show_hidden=False):
		names = []
		hiddennames = []
		appdatalist = self.getBuiltinApplications()
		appdatalist.extend(self.research(leginondata.ApplicationData()))
		for appdata in appdatalist:
			appname = appdata['name']
			if appname not in names:
				if show_hidden is True:
					names.append(appname)
				else:
					if appname not in hiddennames:
						if not appdata['hide']:
								names.append(appname)
						else:
							hiddennames.append(appname)
		return names

	def getApplications(self,show_hidden=False):
		apps = {}
		hiddens = []
		appdatalist = self.getBuiltinApplications()
		appdatalist.extend(self.research(leginondata.ApplicationData()))
		for appdata in appdatalist:
			appname = appdata['name']
			if appname not in apps:
				app = application.Application(self, name=appname)
				if show_hidden:
					apps[appname] = app
				else:
					if appname not in hiddens:
						if appdata['hide']:
							hiddens.append(appname)
						else:
							apps[appname] = app
		#	adding hidden apps from history when show_hidden is False is removed
		# to improve the speed.
		appnames = apps.keys()
		appnames.sort()
		orderedapps = ordereddict.OrderedDict()
		for appname in appnames:
			orderedapps[appname] = apps[appname]
		return orderedapps

	def getApplicationAffixList(self,affix_type='prefix'):
		'''
		Get application prefix list to filter for history. Defined in leginon/leginon_session.cfg
		'''
		try:
			affixlist = moduleconfig.getConfigured('leginon_session.cfg', 'leginon', True)['app'][affix_type]
			if type(affixlist) == type(2):
				# single entry integer is translated to integer, not list of string
				affixlist = ['%d' % affixlist]
			if type(affixlist) == type(''):
				# single entry is translated to string, not list of string
				if affixlist == '':
					affixlist = []
				else:
					affixlist = [affixlist]
		except IOError:
			affixlist = []
		except KeyError:
			# ok if not assigned
			affixlist = []
		except Exception as e:
			raise ValueError('unknown application %s error: %s' % (affix_type,str(e)))
		return affixlist

	def _getAppNamesFromPrefix(self, f):
		'''
		Use direct mysql query to return prefix application names.
		'''
		q = " SELECT name from ApplicationData where name like '%s%%'; " % (f,)
		results = directq.complexMysqlQuery('leginondata',q)
		return list(set(map((lambda x: x['name']),results)))

	def _getAppNamesFromPostfix(self, f):
		'''
		Use direct mysql query to return postfix application names.
		'''
		q = " SELECT name from ApplicationData where name like '%%%s'; " % (f,)
		results = directq.complexMysqlQuery('leginondata',q)
		return list(set(map((lambda x: x['name']),results)))

	def _getLaunchedApplicationByName(self, appname=''):
		'''
		Return most recent launched application data by user,
		90 day limit, and application name.
		'''
		t0=time.time()
		app = leginondata.ApplicationData(hide=False, name=appname)
		initializer = {'session': leginondata.SessionData(user=self.session['user']),
					'application': app}
		lappdata = leginondata.LaunchedApplicationData(initializer=initializer)
		lappdatalist = self.research(lappdata, timelimit='-90 0:0:0',results=1)
		return lappdatalist

	def _getPrefixUserLaunchedApplications(self, prefixlist):
		'''
		Return launched spplication results by prefix list, session user,
		and time limit.
		'''
		lappdatalist = []
		for f in prefixlist:
			names = self._getAppNamesFromPrefix(f)
			names = list(filter((lambda x: x not in self.apnames), names))
			for n in names:
				apps = self._getLaunchedApplicationByName(appname=n)
				if apps:
					lappdatalist.extend(apps) # only one item in apps
					self.apnames.append(n)
		return lappdatalist

	def _getPostfixUserLaunchedApplications(self, postfixlist):
		'''
		Return launched application results by postfix list, session user,
		and time limit.
		'''
		lappdatalist = []
		for f in postfixlist:
			names = self._getAppNamesFromPostfix(f)
			names = list(filter((lambda x: x not in self.apnames), names))
			for n in names:
				apps = self._getLaunchedApplicationByName(appname=n)
				if apps:
					lappdatalist.extend(apps) # only one item in apps
					self.apnames.append(n)
		return lappdatalist

	def _getSessionLaunchedApplications(self):
		lappdatalist_long = leginondata.LaunchedApplicationData(session=self.session).query()
		lappdatalist=[]
		for lapp in lappdatalist_long:
			name = lapp['application']['name']
			if name not in self.apnames:
				self.apnames.append(name)
				lappdatalist.append(lapp)
		return lappdatalist

	def getApplicationHistory(self):
		t0 = time.time()
		prefixlist = self.getApplicationAffixList('prefix')
		postfixlist = self.getApplicationAffixList('postfix')
		lappdatalist = []
		self.apnames = []
		# keep session history
		session_lappdatalist = self._getSessionLaunchedApplications()
		session_history = list(self.apnames)
		# faster if prefix or postfix is set when the same applications were
		# used by the same user many times.
		if prefixlist:
			lapps = self._getPrefixUserLaunchedApplications(prefixlist,)
			lappdatalist.extend(lapps)
		if postfixlist:
			lapps = self._getPostfixUserLaunchedApplications(postfixlist)
			lappdatalist.extend(lapps)
		if not lappdatalist:
			# slow er method get all application names and then filter.
			apnames = self.getApplicationNames()
			apnames = list(filter((lambda x: x not in self.apnames), apnames))
			for n in apnames:
				lapps = self._getLaunchedApplicationByName(appname=n)
				if lapps:
					lappdatalist.extend(lapps) # only one item in apps
		# reverse sort by dbid so that the most recent is at the front
		history_ids = list(map((lambda x: x.dbid), lappdatalist))
		history_ids.sort()
		# keep session_history at front of the final list
		session_history_ids = list(map((lambda x:x.dbid), session_lappdatalist))
		session_history_ids.reverse()
		history_ids.extend(session_history_ids)
		history_ids.reverse()
		# contruct final history
		amap = {}
		history = []
		for lid in history_ids:
			l = leginondata.LaunchedApplicationData().direct_query(lid)
			n = l['application']['name']
			history.append(n)
			amap[n] = l['launchers']
		return history, amap

	def onApplicationStarting(self, name, nnodes):
		evt = gui.wx.Manager.ApplicationStartingEvent(name, nnodes)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationNodeStarted(self, name, status='ok'):
		evt = gui.wx.Manager.ApplicationNodeStartedEvent(name, status)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationStarted(self, name):
		evt = event.ApplicationLaunchedEvent(application=self.application.applicationdata,destination='')
		self.distributeEvents(evt)
		evt = gui.wx.Manager.ApplicationStartedEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationKilled(self):
		evt = gui.wx.Manager.ApplicationKilledEvent()
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def validateApplication(self, app):
		return app.validateTransformManagerNavigatorBindings()

	def runApplication(self, app):
		name = app.applicationdata['name']
		nnodes = len(app.nodespecs)
		self.applicationevent.clear()
		self.clearRemoteNodes()
		self.onApplicationStarting(name, nnodes)
		self.application = app
		initializer = {}
		initializer['session'] = self.session
		initializer['application'] = app.applicationdata
		initializer['launchers'] = app.launchernames.items()
		self.appnodes = app.getNodeNames()
		app.launch()
		self.applicationevent.wait()
		d = leginondata.LaunchedApplicationData(initializer=initializer)
		self.publish(d, database=True, dbforce=True)
		self.onApplicationStarted(name)
		if self.autorun:
			try:
				self.tasker = autotask.AutoTaskOrganizer(self.session)
			except ValueError:
				self.autorun = False
				print('Failed to start auto task organizer. Will not autorun')
				return
			except Exception:
				raise
			self.auto_class_names = ['PresetsManager', 'TEMController','MosaicTargetMaker']
			self.auto_class_aliases = self.getAutoStartNodeNames(app)
			self.setTimeoutTimerStatus(True)
			self.autoStartApplication(self.auto_task)

	def getAutoStartNodeNames(self, app):
		'''
		Get node alias for the node classes that auto start will
		send event to.
		'''
		self.square_finder_class_names = ['MosaicClickTargetFinder','MosaicScoreTargetFinder']
		self.auto_class_names = ['PresetsManager', 'TEMController','MosaicTargetMaker',]
		self.auto_class_names.extend(self.square_finder_class_names)
		auto_class_aliases = {}
		for key in self.auto_class_names:
			auto_class_aliases[key] = None
			for spec in app.nodespecs:
				if spec['class string'] == key:
					auto_class_aliases[key] = spec['alias']
					break
		return auto_class_aliases

	def autoStartApplication(self, task='atlas'):
		'''
		Experimental automatic start of application.
		'''
		if task is None:
			return
		node_name = self.auto_class_aliases['PresetsManager']
		if node_name is None:
			return
		# TODO How to know instruments are ready?
		# simulator pause
		time.sleep(2)
		ievent = event.ChangePresetEvent()
		# TODO determine which preset name to set.
		ievent['name'] = 'gr'
		ievent['emtarget'] = None
		ievent['keep image shift'] = False
		self.outputEvent(ievent, node_name, wait=True, timeout=None)
		# load grid
		node_name = self.auto_class_aliases['TEMController']
		if node_name is not None:
			ievent = event.LoadAutoLoaderGridEvent()
			ievent['slot name'] = self.autogridslot
			self.outputEvent(ievent, node_name, wait=True, timeout=None)
		# acquire grid atlas
		node_name = self.auto_class_aliases['MosaicTargetMaker']
		if node_name is not None:
			ievent = event.MakeTargetListEvent()
			# Set grid to None for now since we don't have a system for
			# passing emgrid info, yet.
			ievent['grid'] = None
			ievent['stagez'] = self.autostagez
			self.outputEvent(ievent, node_name, wait=False, timeout=None)
		# let square finder node knows what the task is.
		for class_name in self.square_finder_class_names:
			node_name = self.auto_class_aliases[class_name]
			if node_name is not None:
				ievent = event.NotifyTaskTypeEvent()
				ievent['task'] = task
				self.outputEvent(ievent, node_name, wait=False, timeout=None)
		self.auto_atlas_done.clear()
		# Listen to atlas finished
		self.auto_atlas_done.wait()
		#
		if task == 'full':
			#submit auto square target and move on.
			class_names = filter((lambda x: self.auto_class_aliases[x] is not None), self.square_finder_class_names)
			if class_names:
				node_name = self.auto_class_aliases[class_names[0]]
				self.auto_done.clear()
				ievent = event.SubmitMosaicTargetsEvent()
				self.outputEvent(ievent, node_name, wait=False, timeout=None)
				self.auto_done.wait()
		# next grid session
		next_auto_task = self.tasker.nextAutoTask()
		if next_auto_task:
			next_auto_session = next_auto_task['auto session']
			# set global values
			self.autogridslot = '%d' % next_auto_session['slot number']
			self.auto_task = next_auto_task['task']
			self.setSessionByName(next_auto_session['session']['name'])
			# run it
			self.autoStartApplication(self.auto_task)
		else:
			# finishing
			current_timeout = self.timeout_minutes + 0
			self.cancelTimeoutTimer()
			self.slackTimeoutNotification('autotasks all finished')
			# refs #12775 prevent autorun
			self.autorun = False
			self.notifyerror = False

	def killApplication(self):
		self.cancelTimeoutTimer()
		# set back to default
		self.timer = None
		self.application.kill()
		self.application = None
		# refs #12775 need to reset so it does not broadcase while launching new app or node.
		self.broadcast = []
		self.onApplicationKilled()

	def loadApp(self, name):
		'''Calls application.Application.load.'''
		launchers = self.launcherdict.keys()
		if launchers:
			launchers.sort()
		else:
			self.logger.error('No available launchers to run application')
			return
		self.application.load(name)

	def launchApp(self):
		'''Calls application.Application.launch.'''
		if not self.have_selectors:
			return
		for alias in self.uilauncherselectors.values():
			aliasvalue = alias.getSelectedValue()
			self.application.setLauncherAlias(alias.name, aliasvalue)
		try:
			nodenames = self.application.launch()
		except RuntimeError,e:
			self.logger.error('Application launch failed: %s' % e)
			return
		self.waitNodes(nodenames)
		dat = leginondata.LaunchedApplicationData(session=self.session, application=self.application.applicationdata)
		self.publish(dat, database=True, dbforce=True)

	def killApp(self):
		'''Calls application.Application.kill.'''
		self.application.kill()

	def exportApplication(self, filename, appname):
		if filename is None:
			return
		app = importexport.ImportExport()
		dump = app.exportApplication(appname)
		if dump is None:
			self.logger.warning('Application invalid')
			return
		try:
			f = open(filename,'w')
			f.write(dump)
			f.close()
		except IOError, e:
			self.logger.exception('Unable to export application to "%s"' % filename)

	def importApplication(self, filename):
		if filename is None:
			return
		try:
			app = importexport.ImportExport()
			app.importApplication(filename)
			messages = app.getMessageLog()
			if messages['information']:
				self.logger.info(messages['information'])
			if messages['warning']:
				self.logger.warning(messages['warning'])
		except ValueError:
			self.logger.exception('Unable to import application from "%s"' % filename)

	def sortNodes(self, nodeclasses=[]):
		allclassnames = noderegistry.getNodeClassNames()
		classtypes = ['Priority', 'Pipeline', 'Calibrations', 'Utility', 'Finale']
		sortclasses = {}
		for classtype in classtypes:
			sortclasses[classtype] = []
		for classname in allclassnames:
			for appnodealias, appnodeclassname in nodeclasses:
				if appnodeclassname == classname:
					nodeclass = noderegistry.getNodeClass(classname)
					classtype = nodeclass.classtype
					sortclasses[classtype].append(appnodealias)
		# sort pipeline nodes by bindings
		if sortclasses['Pipeline']:
			froms = {}
			tos = {}
			for node in sortclasses['Pipeline']:
				froms[node] = []
				tos[node] = []
			for eventclass, fromnode in self.distmap.items():
				for node in sortclasses['Pipeline']:
					if issubclass(eventclass,
								(event.ImageTargetListPublishEvent, event.ImagePublishEvent, event.MakeTargetListEvent)):
						if node in fromnode:
							for tonode in sortclasses['Pipeline']:
								if tonode in fromnode[node]:
									froms[node].append(tonode)
									tos[tonode].append(fromnode)
			starters = []
			for key, value in tos.items():
				if not value:
					starters.append(key)

			sorted = []
			for starter in starters:
				sorted += depth(starter, froms)
			for node in sortclasses['Pipeline']:
				if node not in sorted:
					sorted.append(node)
			sortclasses['Pipeline'] = []
			for s in sorted:
				if s not in sortclasses['Pipeline']:
					sortclasses['Pipeline'].append(s)

		nodeorder = []
		for sortcls in classtypes:
			try:
				nodeorder += sortclasses[sortcls]
				del sortclasses[sortcls]
			except KeyError:
				pass

		for nodes in sortclasses.values():
			nodeorder += nodes

		return nodeorder

	def clearRemoteNodes(self):
		app = remoteserver.RemoteSessionServer(None, self.session)
		app.clearRemoteNodes()

def depth(parent, map):
	l = [parent]
	for child in map[parent]:
		l += depth(child, map)
	return l

if __name__ == '__main__':
	import sys
	import time

	try:
		session = sys.argv[1]
	except IndexError:
		session = time.strftime('%Y-%m-%d-%H-%M')

	initializer = {'name': session}
	m = Manager(('manager',), leginondata.SessionData(initializer=initializer))
	m.start()

