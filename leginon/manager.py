#!/usr/bin/env python

#
# COPYRIGHT:
#	   The Leginon software is Copyright 2003
#	   The Scripps Research Institute, La Jolla, CA
#	   For terms of the license agreement
#	   see  http://ami.scripps.edu/software/leginon-license
#

import application
import leginondata
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
from pyami import ordereddict
import socket
from wx import PyDeadObjectError
import gui.wx.Manager
import noderegistry
import remotecall
import time
import sys

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
	objectserviceclass = remotecall.ManagerObjectService
	def __init__(self, session, tcpport=None, **kwargs):
		self.clients = {}

		self.name = 'Manager'
		self.initializeLogger()

		## need a special DataBinder
		name = DataBinder.__name__
		databinderlogger = gui.wx.Logging.getNodeChildLogger(name, self)
		mydatabinder = DataBinder(self, databinderlogger, tcpport=tcpport)
		node.Node.__init__(self, self.name, session, otherdatabinder=mydatabinder,
												**kwargs)

		self.objectservice = self.objectserviceclass(self)

		self.launcher = None
		self.frame = None

		self.nodelocations = {}
		self.broadcast = []

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

		app = application.Application(self, prevname)
		app.load()
		for alias,hostname in prevlaunchers:
			app.setLauncherAlias(alias, hostname)
		self.runApplication(app)

	def run(self, session, clients, prevapp=False):
		self.session = session
		self.frame.session = self.session

		t = threading.Thread(name='create launcher thread',
													target=self.createLauncher)
		t.start()

		for client in clients:
			try:
				self.addLauncher(client, 55555)
			except Exception, e:
				self.logger.warning('Failed to add launcher: %s' % e)

		if prevapp:
			threading.Thread(target=self.launchPreviousApp).start()

	def getSessionByName(self, name):
		qsession = leginondata.SessionData(name=name)
		sessions = self.research(qsession, results=1)
		if sessions:
			session = sessions[0]
		else:
			session = None
		return session

	def onAddLauncherPanel(self, l):
		evt = gui.wx.Manager.AddLauncherPanelEvent(l)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def createLauncher(self):
		self.launcher = launcher.Launcher(socket.gethostname().lower(),
																			session=self.session,
																			managerlocation=self.location())
		self.onAddLauncherPanel(self.launcher)

	def location(self):
		location = {}
		location['hostname'] = socket.gethostname().lower()
		location['data binder'] = self.databinder.location()
		return location

	# main/start methods

	def start(self):
		'''Overrides node.Node.start'''
		pass

	def exit(self):
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

	# application methods

	def getApplicationNames(self):
		names = []
		appdatalist = self.research(leginondata.ApplicationData())
		for appdata in appdatalist:
			if appdata['name'] not in names:
				names.append(appdata['name'])
		return names

	def getApplications(self):
		apps = {}
		appdatalist = self.research(leginondata.ApplicationData())
		for appdata in appdatalist:
			appname = appdata['name']
			if appname not in apps:
				app = application.Application(self, name=appname)
				apps[appname] = app
		appnames = apps.keys()
		appnames.sort()
		orderedapps = ordereddict.OrderedDict()
		for appname in appnames:
			orderedapps[appname] = apps[appname]
		return orderedapps

	def getApplicationHistory(self):
		initializer = {'session': leginondata.SessionData(user=self.session['user']),
										'application': leginondata.ApplicationData()}
		appdata = leginondata.LaunchedApplicationData(initializer=initializer)
		appdatalist = self.research(appdata, timelimit='-90 0:0:0')
		history = []
		map = {}
		for a in appdatalist:
			name =  a['application']['name']
			if name not in history:
				history.append(name)
				map[name] = a['launchers']
		return history, map

	def onApplicationStarting(self, name, nnodes):
		evt = gui.wx.Manager.ApplicationStartingEvent(name, nnodes)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationNodeStarted(self, name, status='ok'):
		evt = gui.wx.Manager.ApplicationNodeStartedEvent(name, status)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationStarted(self, name):
		evt = gui.wx.Manager.ApplicationStartedEvent(name)
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def onApplicationKilled(self):
		evt = gui.wx.Manager.ApplicationKilledEvent()
		self.frame.GetEventHandler().AddPendingEvent(evt)

	def runApplication(self, app):
		name = app.applicationdata['name']
		nnodes = len(app.nodespecs)
		self.applicationevent.clear()
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

	def launchApp(self):
		'''Calls application.Application.launch.'''
		if not self.have_selectors:
			return
		for alias in self.uilauncherselectors.values():
			aliasvalue = alias.getSelectedValue()
			self.application.setLauncherAlias(alias.name, aliasvalue)
		nodenames = self.application.launch()
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
		neworder = []
		for classname in allclassnames:
			for appnodealias, appnodeclassname in nodeclasses:
				if appnodeclassname == classname:
					neworder.append(appnodealias)
		return neworder

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

