##
## should we make update() accept a sequence just like __init__ ?
##
class OrderedDict(dict):
	'''
	OrderedDict is like a dict, but the order of items IS defined.

	Like the dict built-in function, it can be initialized with either 
	a mapping or sequence, but if an unordered mapping is used, then
	the initial order of the OrderedDict instance is unpredictable.

	When items are added after inialization, the order in which they
	are added determines their order in the OrderedDict.  However,
	updated an item that already exists does not change its order.
	Only if the item is deleted and then added again will it move to
	the end of the order.

	The str() and repr() representations are also properly ordered.
	'''
	def __init__(self, map_or_seq=None):
		## initialize the base class dict, and self.ordered_keys
		self.__ordered_keys = []
		if map_or_seq is None:
			dict.__init__(self)
		else:
			dict.__init__(self, map_or_seq)
			try:
				# mapping:  will have a keys() method but
				# order is unpredictable (unless another
				# OrderedDict is used)
				self.__ordered_keys = list(map_or_seq.keys())
			except AttributeError:
				### sequence:  order is defined
				for item in map_or_seq:
					key = item[0]
					self.__ordered_keys.append(key)

	def keys(self):
		return list(self.__ordered_keys)

	def values(self):
		vals = []
		for key in self.__ordered_keys:
			vals.append(self[key])
		return vals

	def items(self):
		itemlist = []
		for key in self.__ordered_keys:
			itemlist.append((key, self[key]))
		return itemlist

	def __setitem__(self, key, value):
		dict.__setitem__(self, key, value)
		if key not in self.__ordered_keys:
			self.__ordered_keys.append(key)

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self.__ordered_keys.remove(key)

	def update(self, other):
		for k in other.keys():
			self[k] = other[k]

	def __repr__(self):
		itemlist = []
		for key in self.__ordered_keys:
			itemstr = "%s: %s" % (repr(key), repr(self[key]))
			itemlist.append(itemstr)
		joinedstr = ', '.join(itemlist)
		finalstr = '{%s}' % (joinedstr,)
		return finalstr

	def __str__(self):
		return self.__repr__()


class KeyedDict(OrderedDict):
	'''
	KeyedDict takes OrderedDict one step further and sets
	the exact set of items at initialization.  Attempting to 
	get or set a key that is not allowed will result in a 
	KeyError.  Attempting to delete an item will result in 
	a NotImplementedError.
	'''
	def __init__(self, map_or_seq=None):
		OrderedDict.__init__(self, map_or_seq)

	def __delitem__(self, key):
		raise NotImplementedError('All items exist for the life of the object')

	def __setitem__(self, key, value):
		if key in self.keys():
			OrderedDict.__setitem__(self, key, value)
		else:
			raise KeyError('%s, new items not allowed' % (key,))

class TypedDict(KeyedDict):
	'''
	TypedDict takes KeyedDict one step further and declares the type
	of each of its items.  This type declaration can either be done in
	one of two ways:  a) using the usual map_or_seq initializer, 
	in which case the initial values determine the item types, or
	b) using the type_def initializer, similar to the map_or_seq, but 
	in place of values are the types

	An item's type is not entirely strict.  When an item is set to a 
	new value, an attempt is made to convert the new value to the 
	required type.  A failure will result in a ValueError.
	For example:  

		t = TypedDict({'aaa': 5, 'bbb': 1.5})
		j
	example of a type_map_or_seq:
	   {'aaa': int, 'bbb': float}
	   (('aaa', int), ('bbb', float))
	'''
	def __init__(self, map_or_seq=None, type_map_or_seq=None):
		### create a KeyedDict to hold the types
		if type_map_or_seq is not None:
			### already provided
			self.__types = KeyedDict(type_map_or_seq)
		elif map_or_seq is not None:
			### create it from the map_or_seq initializer
			self.__types = KeyedDict(map_or_seq)
			for key,value in self.__types.items():
				self.__types[key] = type(value)
		else:
			### empty
			self.__types = KeyedDict()
				
		### determine initializer for my base class
		if map_or_seq is not None:
			### already provided
			initializer = KeyedDict(map_or_seq)
		elif type_map_or_seq is not None:
			### from type_map_or_sequence
			initializer = KeyedDict(type_map_or_seq)
			for key in initializer:
				initializer[key] = None
		else:
			initializer = None
		### make sure initializer obeys the type rules
		if initializer is not None:
			for key,value in initializer.items():
				initializer[key] = self.__validateValue(key, value)
		### finally initialize my base class
		KeyedDict.__init__(self, initializer)

	def types(self):
		return dict(self.__types)

	def __validateType(self, type):
		if type not in factories:
			raise ValueError('%s, invalid type for TypedDict' % (type,))

	def __validateValue(self, key, value):
		'''uses a factory function from factories to validate a value'''
		valuetype = self.__types[key]
		valuefactory = factories[valuetype]
		return valuefactory(value)

	def __setitem__(self, key, value):
		newvalue = self.__validateValue(key, value)
		KeyedDict.__setitem__(self, key, newvalue)

### this is the mapping of type to a factory function for that type
### the factory function should take one argument which 
### it will attempt to convert to an instance of that type, or raise
### a ValueError if the argument cannot be converted
import Numeric

factories = {
	## most of these are built in types which double as factories
	int: int,
	long: long,
	float: float,
	complex: complex,
	str: str,
	tuple: tuple,
	list: list,
	dict: dict,
	Numeric.ArrayType: Numeric.array
}
