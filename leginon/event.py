#!/usr/bin/env python

import cPickle

class NodeEvents(object):
	def __init__(self):
		self.inputmap = {}
		self.outputs = []

	def addInput(self, eventclass, handler):
		self.inputmap[eventclass] = handler

	def addOutput(self, eventclass):
		self.outputs.append(eventclass)

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
		repr['inputs'] = {}
		for eventclass in self.inputmap:
			classrepr = eventclass.class_xmlrpc_repr()
			repr['inputs'] = classrepr
		return repr


class Event(object):
	def __init__(self, source = None):
		self.source = source

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
	def __init__(self):
		Event.__init__(self)


class YourEvent(Event):
	def __init__(self):
		Event.__init__(self)


class DataPublished(Event):
	def __init__(self):
		Event.__init__(self)

class ImagePublished(DataPublished):
	def __init__(self):
		DataPublished.__init__(self)



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
