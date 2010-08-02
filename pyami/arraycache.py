#!/usr/bin/env python

import weakref

class CachedArray(object):
	def __init__(self, filename, array):
		self.filename = filename
		self.array = array
		self.size = array.size * array.itemsize
		self.refcount = 0
		self.array.setflags(write=False)

class ArrayCache(object):
	def __init__(self, size_max):
		self.weakdict = weakref.WeakValueDictionary()
		self.strong_list = []
		self.strong_size_max = size_max
		self.strong_size = 0

	def put(self, filename, array):
		if filename in self.weakdict:
			cached = self.weakdict[filename]
		else:
			cached = CachedArray(filename, array)
			self.weakdict[filename] = cached
			self.strong_size += cached.size
			self.clean_strong()
		self.insert_strong(cached)

	def get(self, filename):
		try:
			cached = self.weakdict[filename]
		except:
			return None
		## this bumps it to the head of the strong list
		self.insert_strong(cached)
		return cached.array

	def insert_strong(self, cached):
		self.strong_list.insert(0, cached)
		cached.refcount += 1

	def remove_strong(self):
		cached = self.strong_list.pop()
		cached.refcount -= 1
		if cached.refcount == 0:
			self.strong_size -= cached.size

	def clean_strong(self):
		while self.strong_size > self.strong_size_max:
			self.remove_strong()

def test():
	import numpy
	cache = ArrayCache(100)
	print 'KEYS', cache.weakdict.keys()

	for f in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'f', 'e', 'a'):
		a = numpy.arange(20, dtype=numpy.uint8)
		print 'PUT', f
		cache.put(f, a)
		print 'KEYS', [x.filename for x in cache.strong_list]
	print ''

	for f in ('d', 'd', 'b'):
		print 'GET', f, cache.get(f)
		print 'KEYS', [x.filename for x in cache.strong_list]
	print ''

	for f in ('b', 'b',):
		a = numpy.arange(20, dtype=numpy.uint8)
		print 'PUT', f
		cache.put(f, a)
		print 'KEYS', [x.filename for x in cache.strong_list]
	print ''


if __name__ == '__main__':
	test()
