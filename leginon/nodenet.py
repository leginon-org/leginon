import xmlrpcnode
import dataserver
import urllib
import cPickle
import location
import register

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
							-1, # not implemented?
							self.datahandler.port)

		## events should be initialized by subclass before this
		self.events = getattr(self, 'events', [])

		if manageraddress:
			manager_location = location.Location(manageraddress[0],
							manageraddress[1], None)
			self.id = self.manager_connect(manager_location.getURI())

	def __del__(self):
		self.manager_close()

	def manager_connect(self, uri):
		self.addProxy('manager', uri)
		meths = self.EXPORT_methods()

		### still thinking of the best way to pass events to manager
		### right now just passing nothing
		inevents = ()
		outevents = ()

		nodeinfo = {'location pickle' : cPickle.dumps(self.location),
				'methods' : meths,
				'inevents' : inevents,
				'outevents': outevents}

		args = (nodeinfo,)
		self.callProxy('manager', 'addNode', args)

	def manager_close(self):
		print 'manager_close'
		try:
			args = (self.id,)
			self.callProxy('manager', 'deleteNode', args)
		except:
			pass

	def announce(self, event):
		### this sends an outgoing event to the manager
		eventrepr = event.xmlrpc_repr()
		args = (eventrepr,)
		self.callProxy('manager', 'notify', args)

	def EXPORT_event_dispatch(self, eventrepr):
		### this decides what to do with incoming events

		eventpickle = eventrepr['pickle']
		event = cPickle.loads(eventpickle)
		eventclass = event.__class__
		meth = self.eventmap[eventclass]
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
		self.register = register.Register()
		self.bindings = {}
		self.locations = {}

	def EXPORT_addNode(self, node):
		id = self.register.addEntry(
			register.RegisterEntry(node['methods'],
				node['events'],
				cPickle.loads(node['location pickle'])))
		self.addProxy(id, self.register.entries[id].location.getURI())
		print 'node %s has been added' % id
		#print 'nodes: %s' % self.nodes

	def EXPORT_deleteNode(self, id):
		try:
			#del(self.clients[nodeid])
			self.delProxy(id)
			print 'node %s has been deleted' % id
		except KeyError:
			pass

	def EXPORT_nodes(self):
		return self.nodes

	def EXPORT_notify(self, source, event):
		key = (source,event)
		print 'key', key
		if key in self.bindings:
			print 'bound to', self.bindings[key]
			calls = self.bindings[key]
			for target,method in calls:
				self.callProxy(target, method)

	def EXPORT_bindings(self):
		bindlist = []
		for key in self.bindings:
			binditem = (key, self.bindings[key])
			bindlist.append(binditem)
		return bindlist

	def EXPORT_addBinding(self, source, event, target, method):
		key = (source,event)
		bindtup = (target, method)
		if key not in self.bindings:
			self.bindings[key] = []
		if bindtup not in self.bindings[key]:
			self.bindings[key].append(bindtup)
		print 'bindings', self.bindings

	def EXPORT_deleteBinding(self, source, event, target, method):
		key = (source, event)
		bindtup = (target, method)
		if key in self.bindings:
			self.bindings[key].remove(bindtup)
			if not self.bindings[key]:
				del(self.bindings[key])

	def EXPORT_locate(self, dataid):
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
		if dataid not in self.locations:
			self.locations[dataid] = []
		self.locations[dataid].append(location)
		print 'new data location: ', dataid, location

	def EXPORT_deleteLocation(self, dataid, location):
		try:
			self.locations[dataid].remove(location)
		except KeyError:
			pass
		except ValueError:
			pass

if __name__ == '__main__':
	pass

