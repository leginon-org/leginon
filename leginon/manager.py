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
		node.Node.__init__(self, id, {})
		self.uiserver.server.register_function(self.getNodeLocations, 'getNodeLocations')

		self.nodelocations['manager'] = self.location()
		self.distmap = {}
		# maps event id to list of node it was distributed to if event.confirm
		self.confirmmap = {}
		self.app = application.Application(self.ID(), self)

		## this makes every received event get distributed
		self.addEventInput(event.NodeAvailableEvent, self.registerNode)
		self.addEventInput(event.NodeUnavailableEvent, self.unregisterNode)
		self.addEventInput(event.NodeClassesPublishEvent, self.handleNodeClassesPublish)

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

	def addLauncher(self, nodeid, location):
		name = nodeid[-1]
		if name not in self.launcherlist:
			self.launcherlist.append(name)
		self.launcherdict[name] = {'id':nodeid, 'location':location, 'node classes id':None}

	def getLauncherNodeClasses(self, launchername):
		dataid = self.launcherdict[launchername]['node classes id']
		loc = self.launcherdict[launchername]['location']
		launcherid = self.launcherdict[launchername]['id']
		try:
			nodeclassesdata = self.researchByLocation(loc, dataid)
		except IOError:
			print "unable to research launcher, unregistering launcher:", launcherid
			# group into another function
			self.removeNode(launcherid)
			# also remove from launcher registry
			self.delLauncher(launcherid)
			ndict = self.nodeDict()
			self.nodetreedata.set(ndict)
		nodeclasses = nodeclassesdata.content
		return nodeclasses

	def handleNodeClassesPublish(self, event):
		launchername = event.id[-2]
		dataid = event.content
		self.launcherdict[launchername]['node classes id'] = dataid
		self.updateLauncherDictDataDict(launchername)

	def delLauncher(self, nodeid):
		name = nodeid[-1]
		try:
			self.launcherlist.remove(name)
			del self.launcherdict[name]
		except:
			pass
		self.updateLauncherDictDataDict()

	def updateLauncherDictDataDict(self, launchername=None):
		if launchername is not None:
			newdict = self.launcherdictdatadict
			newdict[launchername] = self.getLauncherNodeClasses(launchername)
		else:
			newdict = {}
			for name,value in self.launcherdict.items():
				newdict[name] = self.getLauncherNodeClasses(name)
		self.launcherdictdatadict = newdict

	def registerNode(self, readyevent):
		nodeid = readyevent.id[:-1]
		print 'registering node', nodeid

		nodelocation = readyevent.content

		# check if new node is launcher
		if isinstance(readyevent, event.LauncherAvailableEvent):
			self.addLauncher(nodeid, nodelocation)

		# for the clients and mapping
		self.addEventClient(nodeid, nodelocation)
		#print 'REGISTER NODE clients', self.clients

		# published data of nodeid mapping to location of node
		nodelocationdata = self.server.datahandler.query(nodeid)
		if nodelocationdata is None:
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		else:
			# fools! should do something nifty to unregister, reregister, etc.
			nodelocationdata = data.NodeLocationData(nodeid, nodelocation)
		self.server.datahandler._insert(nodelocationdata)


		ndict = self.nodeDict()
		self.nodetreedata.set(ndict)

		self.confirmEvent(readyevent)

	def unregisterNode(self, unavailable_event):
		nodeid = unavailable_event.id[:-1]
		self.removeNode(nodeid)

		# also remove from launcher registry
		self.delLauncher(nodeid)
		ndict = self.nodeDict()
		self.nodetreedata.set(ndict)

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

		newid = self.nodeID(name)
		args = (newid, self.nodelocations) + nodeargs
		#print 'LAUNCHNODE'
		self.launch(launcher, newproc, target, args)
		#print 'LAUNCHNODE launch(...'
		return newid

	def launch(self, launcher, newproc, target, args=(), kwargs={}):
		"""
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = name of a class in this launchers node class list
		args, kwargs = args for callable object
		"""
		#print 'MANAGER LAUNCH'
		ev = event.LaunchEvent(self.ID(), newproc, target, args, kwargs)
		#print 'EV', ev
		#self.clients[launcher].push(ev)
		#print 'CLIENTS', self.clients
		self.outputEvent(ev, nodeid=launcher)
		#print 'MANAGER LAUNCH DONE'

	def killNode(self, nodeid):
			try:
				self.clients[nodeid].push(event.KillEvent(self.ID()))
			except IOError:
				print "unable to push KillEvent to node, unregistering node", nodeid
				# group into another function
				self.removeNode(nodeid)
				# also remove from launcher registry
				self.delLauncher(nodeid)
				ndict = self.nodeDict()
				self.nodetreedata.set(ndict)

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

	def killApp(self):
		self.app.kill()
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
			try:
				self.clients[to_node].push(ievent)
			except IOError:
				print "unable to push to node, unregistering node", to_node
				# group into another function
				self.removeNode(to_node)
				# also remove from launcher registry
				self.delLauncher(to_node)
				ndict = self.nodeDict()
				self.nodetreedata.set(ndict)

				

	def newLauncher(self, name):
		t = threading.Thread(name='launcher thread', target=launcher.Launcher, args=(self.id + (name,), self.nodelocations))
		t.start()
		# for XML-RPC
		return ''

	def uiGetLauncherdict(self):
		self.updateLauncherDictDataDict()
		return self.launcherdictdatadict
		

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.ui_nodes = {}
		self.ui_launchers = {}

		self.ui_eventclasses = event.eventClasses()

		eventclass_list = self.ui_eventclasses.keys()
		eventclass_list.sort()
		self.launcherlist = []
		self.launcherdict = {}

		## UI data to be used as choices for method args
		self.launcherdictdatadict = {}
		self.launcherdictdata = self.registerUIData('launcherdict', 'struct', default=self.uiGetLauncherdict)
		self.eventclasslistdata = self.registerUIData('eventclasslist', 'array', default=eventclass_list)

		argspec = (
		self.registerUIData('Name', 'string'),
		self.registerUIData('Launcher and Class', 'array', choices=self.launcherdictdata),
		self.registerUIData('Args', 'string', default=''),
		self.registerUIData('New Process', 'boolean', default=False)
		)
		spec1 = self.registerUIMethod(self.uiLaunch, 'Launch', argspec)


		argspec = (
		self.registerUIData('Node', 'string', choices=self.clientlistdata),
		)
		spec2 = self.registerUIMethod(self.uiKill, 'Kill', argspec)

		argspec = (
		self.registerUIData('Event Class', 'string', choices=self.eventclasslistdata),
		self.registerUIData('From Node', 'string', choices=self.clientlistdata),
		self.registerUIData('To Node', 'string', choices=self.clientlistdata),
		)
		spec3 = self.registerUIMethod(self.uiAddDistmap, 'Bind', argspec)


		argspec = (
		self.registerUIData('Filename', 'string'),
		)
		saveapp = self.registerUIMethod(self.saveApp, 'Save', argspec)
		loadapp = self.registerUIMethod(self.loadApp, 'Load', argspec)
		launchapp = self.registerUIMethod(self.launchApp, 'Launch', ())
		killapp = self.registerUIMethod(self.killApp, 'Kill', ())

		app = self.registerUIContainer('Application', (saveapp, loadapp, launchapp, killapp))

		argspec = (self.registerUIData('ID', 'string'),)
		newlauncherspec = self.registerUIMethod(self.newLauncher, 'New Launcher', (argspec))

		launcherspec = self.registerUIContainer('Launcher', (newlauncherspec,))

		ndict = self.nodeDict()
		self.nodetreedata = self.registerUIData('Nodes', 'struct', permissions='r', default=ndict)
		argspec = (self.registerUIData('Hostname', 'string'),
								self.registerUIData('Port', 'integer'))
		addnodespec = self.registerUIMethod(self.uiAddNode, 'Add Node', (argspec))
		nodesspec = self.registerUIContainer('Nodes', (self.nodetreedata, addnodespec))

		self.registerUISpec('Manager', (nodespec, spec1, spec2, spec3, app, launcherspec, nodesspec))

	def nodeDict(self):
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

	def uiAddNode(self, hostname, port):
		e = event.ManagerAvailableEvent(self.id, self.location())
		try:
			client = self.clientclass(self.ID(), {'hostname': hostname, 'TCP port': port})
		except:
			print "Error: cannot connect to specified node"
		try:
			client.push(e)
		except:
			print "Error: cannot push to specified node"
		return ''

	def uiLaunch(self, name, launchclass, args, newproc=0):
		"""
		user interface to the launchNode method
		This simplifies the call for a user by using a
		string to represent the launcher ID, node class, and args
		"""

		launcher_str,nodeclass = launchclass

		print 'LAUNCH %s,%s,%s,%s,%s' % (name, launcher_str, nodeclass, args, newproc)

		launcher_id = self.launcherdict[launcher_str]['id']

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
		return ''

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

	def	getNodeLocations(self):
		nodelocations = self.nodeDict()
		nodelocations[self.id[-1]] = self.location()
		return nodelocations

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

