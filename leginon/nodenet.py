
import xmlrpcnode
import dataserver
import urllib
import cPickle


class Node(xmlrpcnode.xmlrpcnode):
	def __init__(self, id, manageraddress):
		xmlrpcnode.xmlrpcnode.__init__(self)

		self.id = id
		self.datahandler = DataHandler(self)
		self.dataport = self.datahandler.port

		## eventmap and outevents should be initialized by subclass before this
		## __init__ is called, but if not, they are initialize here
		self.eventmap = getattr(self, 'eventmap', {})
		self.outevents = getattr(self, 'outevents', [])
		
		if manageraddress:
			managerhost, managerport = manageraddress
			manager_uri = 'http://' + managerhost + ':' + `managerport`
			self.manager_connect(manager_uri)

	def __del__(self):
		self.manager_close()

	def manager_connect(self, uri):
		self.addProxy('manager', uri)
		meths = self.EXPORT_methods()
		dataport = self.dataport
		nodeinfo = {'id':self.id, 'host':self.host, 'port':self.port, 'dataport':dataport, 'methods':meths, 'events':self.events}
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
		location = 'http://' + self.mynode.host + ':' + `self.port` + '/' + dataid
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
		self.nodes = {}
		self.bindings = {}
		self.locations = {}

	def EXPORT_addNode(self, node):
		nodeid = node['id']
		self.nodes[nodeid] = node
		host = node['host']
		port = node['port']
		uri = 'http://' + host + ':' + `port`
		self.addProxy(nodeid, uri)
		print 'node %s has been added' % nodeid
		print 'nodes: %s' % self.nodes

	def EXPORT_deleteNode(self, nodeid):
		try:
			del(self.clients[nodeid])
			self.delProxy(nodeid)
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

