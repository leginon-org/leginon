#!/usr/bin/env python

import cPickle, threading

class EventDistributor(object):
	def __init__(self, registry):
		self.bindings = EventBindings()
		self.registry = registry

	def insert(self, sourceid, eventinst):
		t = threading.Thread(target=self.distribute, args=(sourceid, eventinst))
		t.start()
		
	def distribute(self, sourceid, eventinst):
		eventclass = eventinst.__class__
		key = (sourceid,eventclass)
		if key in self.bindings:
			eventrepr = eventinst.xmlrpc_repr()
			targets = self.bindings[key]
			for targetid in targets:
				args = (eventrepr,)
				loc = self.registry.entries[targetid].location
				loc.rpc('event_dispatch', args)

	def addBinding(self, sourceid, targetid, eventclass):
		## this should probably be moved into event.EventDistributor
		key = (sourceid,eventclass)
		if key not in self.bindings:
			self.bindings[key] = []
		if targetid not in self.bindings[key]:
			self.bindings[key].append(targetid)

	def deleteBinding(self, sourceid, targetid, eventclass):
		## this should probably be moved into event.EventDistributor
		key = (sourceid, eventclass)
		if key in self.bindings:
			try:
				self.bindings[key].remove(targetid)
				if not self.bindings[key]:
					del(self.bindings[key])
			except ValueError:
				pass


class EventBindings(dict):
	def __init__(self):
		dict.__init__(self)

	def xmlrpc_repr(self):
		## since xmlrpc only allows strings for dict keys, we create
		## a list representation instead.  Also using the xmlrpc_repr
		## of the event class
		bindlist = []
		for key in self:
			sourceid, eventclass = key
			targetlist = self[key]

			eventrepr = eventclass.class_xmlrpc_repr()
			newkey = sourceid, eventrepr

			binditem = (newkey, targetlist)
			bindlist.append(binditem)
		return bindlist


class NodeEvents(object):
	def __init__(self):
		self.inputmap = {}
		self.outputs = []

	def addInput(self, eventclass, handler):
		self.inputmap[eventclass] = handler

	def deleteInput(self, eventclass, handler):
		raise NotImplementedError()

	def addOutput(self, eventclass):
		self.outputs.append(eventclass)

	def deleteOutput(self, eventclass, handler):
		raise NotImplementedError()

	def __str__(self):
		ret = 'Input Map:  %s\n' % self.inputmap
		ret += 'Outputs:  %s\n' % self.outputs
		return ret

	def xmlrpc_repr(self):
		repr = {}
		repr['outputs'] = []
		for eventclass in self.outputs:
			classrepr = eventclass.class_xmlrpc_repr()
			repr['outputs'].append(classrepr)
		repr['inputs'] = []
		for eventclass in self.inputmap:
			classrepr = eventclass.class_xmlrpc_repr()
			repr['inputs'].append(classrepr)
		return repr


class Event(object):
	def __init__(self):
		pass

	def hierarchy(cls):
		mybasetup = bases_tup(cls)
		return mybasetup
	hierarchy = classmethod(hierarchy)

	def xmlrpc_repr(thing):
		"""
		thing can be class or instance
		"""

		picklestring = cPickle.dumps(thing)
		xmlrpcdict = {'class':thing.hierarchy(), 'pickle':picklestring}
		return xmlrpcdict

	class_xmlrpc_repr = classmethod(xmlrpc_repr)

	def __str__(self):
		ret = 'hierarchy: ' + `self.hierarchy()`
		return ret


def bases_tup(classobject):
	"""
	generates a tuple by recursively getting names of base classes
	"""
	basetup = ()
	if classobject != object:
		myname = classobject.__name__
		mybase = classobject.__bases__[0]
		mybasetup = bases_tup(mybase)
		basetup = mybasetup + (myname,)
	return basetup


class MyEvent(Event):
	def __init__(self, stuff):
		Event.__init__(self)
		self.stuff = stuff

	def xmlrpc_repr(self):
		repr = Event.xmlrpc_repr(self)
		repr['stuff'] = self.stuff
		return repr

	def __str__(self):
		ret = Event.__str__(self)
		ret = '%s\nstuff:  %s' % (ret, str(self.stuff))
		return ret


class YourEvent(Event):
	def __init__(self, stuff):
		Event.__init__(self)
		self.stuff = stuff

	def xmlrpc_repr(self):
		repr = Event.xmlrpc_repr(self)
		repr['stuff'] = self.stuff
		return repr

	def __str__(self):
		ret = Event.__str__(self)
		ret = '%s\nstuff:  %s' % (ret, str(self.stuff))
		return ret


class DataPublished(Event):
	def __init__(self, dataid):
		Event.__init__(self)
		self.dataid = dataid

	def xmlrpc_repr(self):
		repr = Event.xmlrpc_repr(self)
		repr['dataid'] = self.dataid
		return repr

	def __str__(self):
		ret = Event.__str__(self)
		ret = '%s\ndataid:  %d' % (ret, self.dataid)
		return ret


class ImagePublished(DataPublished):
	def __init__(self, dataid):
		DataPublished.__init__(self, dataid)



if __name__ == '__main__':
	import sys, pickle

	if sys.argv[1] == 'put':
		i = ImageReady()
		pf = open('eventpickle', 'w')
		pickle.dump(i, pf)
		print 'i', i.tostring()

	elif sys.argv[1] == 'get':
		pf = open('eventpickle', 'r')
		i = pickle.load(pf)
		print 'i', i.tostring()
