

import shelve
import cPickle


class ShelfDict(object):
	"""
	similar to the shelf in the standard shelve module,
	but this one accepts any object as a key rather than 
	just strings
	"""
	def __init__(self, filename):
		self.filename = filename
		self.__open_shelf()
		self.__close_shelf()

	def __open_shelf(self):
		print 'open'
		self.shelf = shelve.open(self.filename)

	def __close_shelf(self):
		print 'close'
		self.shelf.close()

	def __pickle_key(self, key):
		return cPickle.dumps(key, 1)

	def __unpickle_key(self, pkey):
		return cPickle.loads(pkey)


	##
	## methods below emulate the shelve.Shelf class
	##

	def __getitem__(self, key):
		newkey = self.__pickle_key(key)
		self.__open_shelf()
		try:
			value = self.shelf[newkey]
		except KeyError:
			# raising KeyError with key instead of newkey
			self.__close_shelf()
			raise KeyError(key)
		self.__close_shelf()
		return value

	def __setitem__(self, key, value):
		newkey = self.__pickle_key(key)
		self.__open_shelf()
		self.shelf[newkey] = value
		self.__close_shelf()
		
	def __delitem__(self, key):
		newkey = self.__pickle_key(key)
		self.__open_shelf()
		try:
			del self.shelf[newkey]
		except KeyError:
			# raising KeyError with key instead of newkey
			self.__close_shelf()
			raise KeyError(key)
		self.__close_shelf()

	def __len__(self):
		self.__open_shelf()
		length = len(self.shelf)
		self.__close_shelf()
		return length

	def __iter__(self):
		return self.iterkeys()

	def iterkeys(self):
		return iter(self.keys())

	def has_key(self, key):
		self.__open_shelf()
		newkey = self.__pickle_key(key)
		self.__close_shelf()
		return self.shelf.has_key(newkey)

	def keys(self):
		self.__open_shelf()
		pkeys = self.shelf.keys()
		self.__close_shelf()
		keys = map(self.__unpickle_key, pkeys)
		return keys

	def values(self):
		self.__open_shelf()
		d = dict(self.shelf)
		self.__close_shelf()
		return d.values()

	def items(self):
		self.__open_shelf()
		d = dict(self.shelf)
		self.__close_shelf()
		items = []
		for pkey,value in d.items():
			key = self.__unpickle_key(pkey)
			items.append((key,value))
		return items

	def update(self, newdict):
		self.__open_shelf()
		for key,value in newdict.items():
			newkey = self.__pickle_key(key)
			self.shelf[newkey] = value
		self.__close_shelf()
