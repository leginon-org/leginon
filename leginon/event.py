#!/usr/bin/env python

import string


class Event(object):
	def __init__(self, source):
		self.source = source

	def tostring(self):
		myclass = self.__class__
		mybasetup = bases_tup(myclass)
		mystr = string.join(mybasetup, '.')
		return mystr


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




class DataPublished(Event):
	def __init__(self):
		Event.__init__(self)


class ImageReady(DataReady):
	def __init__(self):
		DataReady.__init__(self)



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
