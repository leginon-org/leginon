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
import event
import importexport
import leginonconfig
import launcher
import node
import threading
import uiserver
import uidata
import leginonobject
import extendedlogging
import copy
import uiclient
import newdict
import socket
import gui.wx.SetupWizard
import gui.wx.Manager
import nodeclassreg

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
		mydatabinder = DataBinder(self, tcpport=tcpport)
		node.Node.__init__(self, name, session, otherdatabinder=mydatabinder,
												xmlrpcport=xmlrpcport, **kwargs)

		self.frame = gui.wx.Manager.Frame(self, self.research, self.publish)

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

		self.application = None

		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent,
															self.handleNodeClassesPublish)
		self.addEventInput(event.NodeInitializedEvent, self.handleNodeStatus)
		self.addEventInput(event.NodeUninitializedEvent, self.handleNodeStatus)
		# this makes every received event get distributed
		self.addEventInput(event.Event, self.distributeEvents)

		self.launcherdict = {}
		# will move, I promise
		setup = gui.wx.SetupWizard.SetupWizard(self.frame,
																						self.research, self.publish)

		# handle better
		if setup.session is None:
			raise RuntimeError('Setup cancelled')

		self.session = setup.session
		self.frame.session = self.session
		self.uicontainer.session = setup.session
		self.uicontainer.getUserPreferencesFromDatabase()

		# needs threading, but shouldn't
		t = threading.Thread(name='create launcher thread',
													target=self.createLauncher)
		t.start()

		if setup.connect:
			self.addInstrumentLauncher()

	def onAddLauncherPanel(self, l):
		evt = gui.wx.Manager.AddLauncherPanelEvent(l)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def createLauncher(self):
		l = launcher.Launcher(socket.gethostname().lower(),
													session=self.session,
													managerlocation=self.location())
		self.onAddLauncherPanel(l)

	def addInstrumentLauncher(self):
		if self.session['instrument'] is None:
			self.logger.warning('Cannot add instrument\'s launcher.')
			return
		hostname = self.session['instrument']['hostname']
		if not hostname:
			self.logger.warning('Cannot add instrument\'s launcher.')
			return
		if hostname == socket.gethostname().lower():
			return
		try:
			location = {}
			location['TCP transport'] = {}
			location['TCP transport']['hostname'] = hostname
			location['TCP transport']['port'] = 55555
			self.addNode(hostname, location)
		except (IOError, TypeError, socket.error):
			self.logger.warning('Cannot add instrument\'s launcher.')

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

	def broadcastToNode(self, nodename):
		to_node = nodename
		for ievent in self.broadcast:
			### this is a special case of outputEvent
			### so we don't use outputEvent here
			try:
				eventcopy = copy.copy(ievent)
				eventcopy['destination'] = to_node
				self.clients[to_node].push(eventcopy)
			except IOError:
				### bad client, get rid of it
				self.logger.error('Cannot push to node ' + str(to_node)
													+ ', unregistering')
				self.removeNode(to_node)
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
					self.clients[to_node].push(eventcopy)
				except IOError:
					### bad client, get rid of it
					self.logger.error('Cannot push to node ' + str(to_node)
														+ ', unregistering')
					self.removeNode(to_node)
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

	def onAddLauncher(self, name):
		evt = gui.wx.Manager.AddLauncherEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onRemoveLauncher(self, name):
		evt = gui.wx.Manager.RemoveLauncherEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

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
				raise ValueError('Invalid launcher name')
			if sorted:
				classes.sort()
		return classes

	def _addLauncher(self, name, location):
		'''Add launcher to mapping, add UI client.'''
		if name in self.getLauncherNames():
			raise RuntimeError('Launcher name in use.')
		self.launcherdict[name] = {'location': location}
		self.addNodeUIClient(name, location['UI'])
		self.onAddLauncher(name)

	def delLauncher(self, name):
		'''Remove launcher from mapping and UI.'''
		try:
			del self.launcherdict[name]
		except KeyError:
			return
		self.deleteNodeUIClient(name)
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
			nodeclass = nodeclassreg.getNodeClass(classname)
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
				raise RuntimeError('Launcher specified by node has no client')
			try:
				nodelocationdata = self.nodelocations[launchername]
			except KeyError:
				raise RuntimeError('Launcher specified by node has no location data')
			return nodelocationdata['location']
		else:
			raise RuntimeError('Unable to find client for node')
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
		self.nodelocations[name] = data.NodeLocationData(initializer=initializer)

		self.confirmEvent(evt)

		self.onAddNode(name)

	def onAddNode(self, name):
		evt = gui.wx.Manager.AddNodeEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onRemoveNode(self, name):
		evt = gui.wx.Manager.RemoveNodeEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def addNodeUIClient(self, nodename, uilocation):
		if nodename in self.uiclientcontainers:
			self.deleteNodeUIClient(nodename)
		clientcontainer = uidata.LargeClientContainer(nodename, uilocation)
		try:
			self.uicontainer.addObject(clientcontainer)
			self.uiclientcontainers[nodename] = clientcontainer
		except:
			self.logger.exception('cannot add client container for node')

	def unregisterNode(self, evt):
		'''Event handler Removes all information, event mappings and the client.'''
		nodename = evt['node']
		self.removeNode(nodename)
		self.confirmEvent(evt)

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
										'manager location':self.location()}
		ev = event.CreateNodeEvent(initializer=initializer)
		self.outputEvent(ev, launcher, wait=True)

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
				self.logger.error('Failed to add node at ' + hostname + ':'
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
			# maybe didn't get uninitialized
			self.setNodeStatus(nodename, False)
			# group into another function
			self.removeNode(nodename)

	# application methods

	def getApplicationNames(self):
		names = []
		appdatalist = self.research(data.ApplicationData())
		for appdata in appdatalist:
			if appdata['name'] not in names:
				names.append(appdata['name'])
		return names

	def getApplications(self):
		apps = {}
		appdatalist = self.research(data.ApplicationData())
		for appdata in appdatalist:
			if appdata['name'] not in apps:
				app = application.Application(self)
				app.load(appdata['name'])
				apps[appdata['name']] = app
		return apps

	def getApplicationHistory(self):
		initializer = {'session': data.SessionData(user=self.session['user']),
										'application': data.ApplicationData()}
		appdata = data.LaunchedApplicationData(initializer=initializer)
		appdatalist = self.research(appdata)
		history = []
		for a in appdatalist:
			name =  a['application']['name']
			if name not in history:
				history.append(name)
		return history

	def onApplicationStarting(self, name, nnodes):
		evt = gui.wx.Manager.ApplicationStartingEvent(name, nnodes)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationNodeStarted(self, name):
		evt = gui.wx.Manager.ApplicationNodeStartedEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationStarted(self, name):
		evt = gui.wx.Manager.ApplicationStartedEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationKilled(self):
		evt = gui.wx.Manager.ApplicationKilledEvent()
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def waitApplication(self, app):
		nodes = list(app.launch())
		self.initializednodescondition.acquire()
		while nodes:
			for node in list(nodes):
				if node in self.initializednodes:
					nodes.remove(node)
					self.onApplicationNodeStarted(node)
			self.initializednodescondition.wait(0.01)
		self.initializednodescondition.release()

	def runApplication(self, app):
		name = app.applicationdata['name']
		nnodes = len(app.nodespecs)
		self.onApplicationStarting(name, nnodes)
		self.application = app
		initializer = {}
		initializer['session'] = self.session
		initializer['application'] = app.applicationdata
		self.waitApplication(app)
		d = data.LaunchedApplicationData(initializer=initializer)
		self.publish(d, database=True, dbforce=True)
		self.onApplicationStarted(name)

	def killApplication(self):
		self.application.kill()
		self.application = None
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
		nodenames = self.application.launch()
		self.waitNodes(nodenames)
		dat = data.LaunchedApplicationData(session=self.session, application=self.application.applicationdata)
		self.publish(dat, database=True, dbforce=True)

	def killApp(self):
		'''Calls application.Application.kill.'''
		self.application.kill()
		self.setLauncherSelectors(selectors=None)

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
		except IOError,e:
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

	# UI methods
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

	def uiGetNodeLocations(self):
		'''UI helper for mapping a node alias to the node's location.'''
		nodelocations = self.uiNodeDict()
		nodelocations[self.name] = self.location()
		return nodelocations
	
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

