#!/usr/bin/env python

import string, cPickle


class Event(object):
	def __init__(self, source = None):
		self.source = source

	def class_string(self):
		myclass = self.__class__
		mybasetup = bases_tup(myclass)
		mystr = string.join(mybasetup, '.')
		return mystr

	def xmlrpc_repr(self):
		"""
		package the event into a dict for xmlrpc
		"""
		myclass = self.class_string()
		picklestring = cPickle.dumps(self)

		xmlrpcdict = {'class':myclass, 'pickle':picklestring}
		return xmlrpcdict


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

	def xmlrpc_repr(self):
		repr = Event.xmlrpc_repr(self)
		repr['newstuff'] = 'stuff for MyEvent'
		return repr


class YourEvent(Event):
	def __init__(self):
		Event.__init__(self)

	def xmlrpc_repr(self):
		repr = Event.xmlrpc_repr(self)
		repr['somestuff'] = 'stuff for YourEvent'
		return repr


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
