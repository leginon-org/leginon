import xmlrpcnode
import dataserver
import urllib
import cPickle
import location
import registry
import event

class Node(xmlrpcnode.xmlrpcnode):
	def __init__(self, manageraddress):
		xmlrpcnode.xmlrpcnode.__init__(self)

		self.datahandler = DataHandler(self)

		# it might be better to change NodeLocation to take
		# and instance of Location as part of the constructor
		# or the whole thing could be a dictionary
		self.location = location.NodeLocation(self.location.hostname,
							self.location.port,
							self.location.pid,
							self.datahandler.port)

		self.init_events()

		if manageraddress:
			manager_location = location.Location(manageraddress[0],
							manageraddress[1], None)
			self.id = self.manager_connect(manager_location.getURI())

	def init_events(self):
		raise NotImplementedError()

	def __del__(self):
		self.manager_close()

	def manager_connect(self, uri):
		self.addProxy('manager', uri)
		meths = self.EXPORT_methods()

		eventinfo = {}
		eventinfo['inputs'] = self.events.inputmap.keys()
		eventinfo['outputs'] = self.events.outputs

		locpickle = cPickle.dumps(self.location)
		eventpickle = cPickle.dumps(eventinfo)

		nodeinfo = {'location pickle' : locpickle, 'methods' : 'meths', 'events pickle': eventpickle}

		args = (nodeinfo,)
		self.callProxy('manager', 'addNode', args)

	def manager_close(self):
		print 'manager_close'
		try:
			args = (self.id,)
			self.callProxy('manager', 'deleteNode', args)
		except:
			pass

	def announce(self, eventinst):
		### this sends an outgoing event to the manager
		eventrepr = eventinst.xmlrpc_repr()
		args = (eventrepr,)
		self.callProxy('manager', 'notify', args)

	def EXPORT_event_dispatch(self, eventrepr):
		### this decides what to do with incoming events

		eventpickle = eventrepr['pickle']
		eventinst = cPickle.loads(eventpickle)
		eventclass = eventinst.__class__
		meth = self.events.inputmap[eventclass]
		apply(meth, (event,))

	def publish(self, dataid, data):
		self.datahandler.put(dataid, data)

	def research(self, dataid):
		data = self.datahandler.get(dataid)
		return data

class DataHandler(object):
	def __init__(self, mynode):
		self.mynode = mynode
		self.mydata = {}
		self.dataserver = dataserver.DataServer(self)
		self.port = self.dataserver.port

	def __getattr__(self, name):
		if name in self.mydata:
			return self.mydata[name]
		else:
			return None

	def put(self, dataid, data):
		### do something with the data
		###   to DB
		###   to file
		###   to server

		## this makes it accessable to the http server

		self.mydata[dataid] = data


		## notify manager of the new location
		location = self.mynode.location.getURI() + '/' + dataid
		args = (dataid, location)
		self.mynode.callProxy('manager', 'addLocation', args)

	def get(self, dataid):
		args = (dataid,)
		location = self.mynode.callProxy('manager', 'locate', args)
		urlfile = urllib.urlopen(location)
		data = cPickle.load(urlfile)

		return data

class Manager(xmlrpcnode.xmlrpcnode):
	def __init__(self, *args, **kwargs):
		xmlrpcnode.xmlrpcnode.__init__(self)
		self.registry = registry.Registry()
		self.bindings = {}
		self.locations = {}

	def EXPORT_addNode(self, node):

		id = self.registry.addEntry(
			registry.RegistryEntry(node['methods'],
				cPickle.loads(node['events pickle']),
				cPickle.loads(node['location pickle'])))
		self.addProxy(id, self.registry.entries[id].location.getURI())
		print 'node %s has been added' % id
		self.print_nodes()

	def EXPORT_deleteNode(self, id):
		try:
			#del(self.clients[nodeid])
			self.delProxy(id)
			print 'node %s has been deleted' % id
		except KeyError:
			pass

	def print_nodes(self):
		print 'NODES:'
		print self.registry

	def EXPORT_nodes(self):
		nodes = self.registry.xmlrpc_repr()
		print 'XMLRPCRPER', nodes
		return nodes

	def EXPORT_notify(self, source, eventrepr):
		eventinst = cPickle.loads(eventrepr['event'])
		eventclass = eventinst.__class__
		if eventclass in self.bindings:
			targets = self.bindings[key]
			for target in targets:
				args = (eventclass,)
				self.callProxy(target, 'event_dispatch', args)

	def EXPORT_bindings(self):
		##### not ready yet
		bindlist = []
		for key in self.bindings:
			binditem = (key, self.bindings[key])
			bindlist.append(binditem)
		return bindlist

	def EXPORT_addBinding(self, source, event, target, method):
		##### not ready yet
		key = (source,event)
		bindtup = (target, method)
		if key not in self.bindings:
			self.bindings[key] = []
		if bindtup not in self.bindings[key]:
			self.bindings[key].append(bindtup)
		print 'bindings', self.bindings

	def EXPORT_deleteBinding(self, source, event, target, method):
		###### not ready yet
		key = (source, event)
		bindtup = (target, method)
		if key in self.bindings:
			self.bindings[key].remove(bindtup)
			if not self.bindings[key]:
				del(self.bindings[key])

	def EXPORT_locate(self, dataid):
		######### I think this is replaced by the registry stuff
		## find the uri of the data referenced by dataid
		location = ''
		try:
			location = self.locations[dataid][0]
		except KeyError:
			pass
		except ValueError:
			pass
		return location

	def EXPORT_addLocation(self, dataid, location):
		##### same here
		if dataid not in self.locations:
			self.locations[dataid] = []
		self.locations[dataid].append(location)
		print 'new data location: ', dataid, location

	def EXPORT_deleteLocation(self, dataid, location):
		###### same here
		try:
			self.locations[dataid].remove(location)
		except KeyError:
			pass
		except ValueError:
			pass

if __name__ == '__main__':
	pass

