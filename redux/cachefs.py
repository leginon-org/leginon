#!/usr/bin/env python

import fs.osfs
import collections
import itertools
import os
import threading

debug = True
def debug(s):
	if debug:
		sys.stderr.write(s)
		sys.stderr.write('\n')

class FileObjectWrapper(object):
	'''
	Override the close method, so we can track changes to files.
	'''
	def __init__(self, fileobj, closecallback, name):
		self.fileobj = fileobj
		self.closecallback = closecallback
		self.name = name

	def __getattr__(self, attr):
		if attr in self.__dict__:
			return getattr(self, attr)
		return getattr(self.fileobj, attr)

	def close(self):
		# close the file, then run close callback
		self.fileobj.close()
		self.closecallback(self.name)

class Constrainer(object):
	'''
	Maintains a dict of sizes and a deque to track order of access.
	Keeps total size under the limit by removing the oldest items.
	'''
	debug = False
	def __init__(self, maxsize, remove_callback):
		self.max_size = maxsize
		self.remove_callback = remove_callback
		self.lock = threading.Lock()

		self.total_size = 0
		self.size_dict = {}
		self.order = collections.deque()

		if self.debug:
			self.print_contents()

	def print_contents(self):
		print '=============================================================='
		print 'ORDER', self.order
		print 'SIZES', self.size_dict
		print 'STATUS', '%s of %s' % (self.total_size, self.max_size)
		print '=============================================================='

	def insert(self, o, newsize):
		self.lock.acquire()
		if o in self.size_dict:
			oldsize = self.size_dict[o]
			self.order.remove(o)
		else:
			oldsize = 0

		self.size_dict[o] = newsize
		self.order.appendleft(o)
		self.total_size += (newsize - oldsize)

		self.__clean()
		if self.debug:
			self.print_contents()
		self.lock.release()

	def __clean(self):
		while self.total_size > self.max_size:
			self.__remove_oldest()

	def __remove_oldest(self):
		o = self.order.pop()
		oldsize = self.size_dict[o]
		del self.size_dict[o]
		self.total_size -= oldsize
		self.remove_callback(o)

# Compare two tuples based on their second value.
# This is used for sorting list of (filename, time) by time.
def cmp2(a, b):
	return cmp(a[1], b[1])


class CacheFS(fs.osfs.OSFS):
	'''
	This is a subclass of fs.osfs.OSFS.  It creates a size-limited
	cache inside the given directory.  The open method is overridden
	such that it returns a custom file object.  The custom file object
	will call back to this class when the file is closed.  This allows
	us to track all file access within the cache.  We track the order
	that files are accessed and if the size of a file changes.  When 
	the total size of all files exceeds the maximum, the oldest files
	are removed to keep the size below the maximum.
	'''
	def __init__(self, cachedir, maxsize):
		fs.osfs.OSFS.__init__(self, cachedir)
		self.constrainer = Constrainer(maxsize, self.remove)

		files = list(self.walkfiles())

		fileatimes = [(f,self.getinfo(f)['accessed_time']) for f in files]
		fileatimes.sort(cmp2)
		files = [fa[0] for fa in fileatimes]

		for f in files:
			self.constrainer.insert(f, self.getsize(f))

	def close_callback(self, name):
		newsize = self.getsize(name)
		self.constrainer.insert(name, newsize)

	def open(self, *args, **kwargs):
		'''
		Open file, return wrapped file object that allows
		tracking when the file is closed
		'''
		f = fs.osfs.OSFS.open(self, *args, **kwargs)
		name = args[0]
		f = FileObjectWrapper(f, self.close_callback, name)
		return f

	def remove(self, *args, **kwargs):
		'''
		Override default remove to also remove parent directory if it
		is empty.
		'''
		fs.osfs.OSFS.remove(self, *args, **kwargs)
		name = args[0]
		try:
			self.removedir(os.path.dirname(name), recursive=True)
		except fs.errors.DirectoryNotEmptyError:
			pass

test_cache_dir = 'cachedir'

def test_main():
	import time
	cfs = CacheFS(test_cache_dir, 50)
	f = cfs.open('/myfile%s' % (time.time(),), 'w')
	f.write('xxxxxxx')
	f.close()

if __name__ == '__main__':
	test_main()
