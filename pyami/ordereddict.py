
class OrderedDict(dict):
	def __init__(self, initializer={}):
		try:
			items = initializer.items()
		except AttributeError:
			items = list(initializer)
		self.__keys = [i[0] for i in items]
		dict.__init__(self, initializer)

	## definining __reduce__ allows unpickler to call __init__ 	 
	def __reduce__(self): 	 
		state = dict(self.__dict__) 	 
		## giving the new object an initializer has a lot of 	 
		## duplicate information to what is given in the 	 
		## state dict, but it is necessary to get the dict 	 
		## base class to have its items set 	 
		initializer = dict(self.items()) 	 
		return (self.__class__, (initializer,), state)

	def __setitem__(self, key, value):
		if not dict.__contains__(self, key):
			self.__keys.append(key)
		dict.__setitem__(self, key, value)

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self.__keys.remove(key)

	def update(self, other):
		for key in other.keys():
			self[key] = other[key]

	def keys(self):
		return list(self.__keys)

	def values(self):
		return map(super(OrderedDict, self).__getitem__, self.__keys)

	def items(self):
		values = OrderedDict.values(self)
		return zip(self.__keys, values)

	def __str__(self):
		'''
		imitate dict.__str__ but with items in proper order
		'''
		itemlist = []
		for key,value in self.items():
			valuestr = str(value)
			itemstr = "%s: %s" % (str(key), valuestr)
			itemlist.append(itemstr)
		joinedstr = ', '.join(itemlist)
		finalstr = '{%s}' % (joinedstr,)
		return finalstr
