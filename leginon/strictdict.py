#!/usr/bin/env python
'''
Provides several specialized mapping types derived from the built-in dict type.
'''

import Numeric
from types import NoneType
import copy

class NumericArrayType:
	'''
	This represents Numeric.ArrayType, since pickle won't accept it
	'''

def validateNumericArray(obj):
	try:
		obj.typecode
	except AttributeError:
		raise TypeError()
	return obj

## still missing from these classes: ##   __copy__

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
	### I have chosen to maintain lists of keys, values, and items
	### while it would be sufficient to maintain just one ordered list.
	### This optimizes the keys(), values(), and items() methods, but
	### makes __setitem__ and __delitem__ take longer since it has to 
	### update the lists.  So it seems to be well suited to a smaller
	### dict where items are set once and viewed or iterated over many
	### times.
	def __init__(self, map_or_seq=None):
		## initialize the base class dict, and self.ordered_keys
		self.__ordered_keys = []
		self.__ordered_values = []
		self.__ordered_items = []
		if map_or_seq is None:
			dict.__init__(self)
		else:
			dict.__init__(self, map_or_seq)
			try:
				# mapping:  will have a items() method but
				# order is unpredictable (unless another
				# OrderedDict is used)
				self.__ordered_items = map_or_seq.items()
			except AttributeError:
				### sequence:  order is defined
				self.__ordered_items = list(map_or_seq)
			self.__ordered_keys = [item[0] for item in self.__ordered_items]
			self.__ordered_values = [item[1] for item in self.__ordered_items]

	def keys(self):
		return list(self.__ordered_keys)

	def values(self):
		return list(self.__ordered_values)

	def items(self):
		return list(self.__ordered_items)

	def __setitem__(self, key, value):
		dict.__setitem__(self, key, value)
		self.__setlists(key, value)

	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self.__dellists(key)

	def __setlists(self, key, value):
		try:
			# update item
			i = self.__ordered_keys.index(key)
			self.__ordered_values[i] = value
			self.__ordered_items[i] = (key,value)
		except ValueError:
			# new item
			self.__ordered_keys.append(key)
			self.__ordered_values.append(value)
			self.__ordered_items.append((key,value))

	def __dellists(self, key, value):
		## could check for ValueErro exception here but
		## I'm assuming dict.__delitem__ already called
		## and would have already raised KeyError
		i = self.__ordered_keys.index(key)
		del self.__ordered_keys[i]
		del self.__ordered_values[i]
		del self.__ordered_items[i]

	def update(self, other):
		for k in other.keys():
			self[k] = other[k]

	def __str__(self):
		'''
		imitate dict.__str__ but with items in proper order
		'''
		itemlist = []
		for key,value in self.__ordered_items:
			itemstr = "%s: %s" % (repr(key), repr(value))
			itemlist.append(itemstr)
		joinedstr = ', '.join(itemlist)
		finalstr = '{%s}' % (joinedstr,)
		return finalstr

	def __repr__(self):
		s = repr(self.__ordered_items)
		r = '%s(%s)' % (self.__class__.__name__, s)
		return r


class KeyedDict(OrderedDict):
	'''
	KeyedDict takes OrderedDict one step further and sets
	the exact set of keys at initialization.  Attempting to 
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

	def friendly_update(self, other):
		'''
		Like update(), but this one will ignore keys from the source
		mapping that are invalid, rather than raise an exception.
		If this is more useful than the regular update, maybe we 
		should think about replacing update with friendly_update.
		'''
		for key,value in other.items():
			try:
				self[key] = value
			except KeyError:
				pass

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
	required type.  A failure will result in a ValueError exception.
	For example:  

		t = TypedDict({'aaa': 5, 'bbb': 1.5})
		t['aaa'] = 555    # OK, 555 is int
		t['aaa'] = '555'  # OK, str '555' can be converted to int 555
		t['aaa'] = 4.5    # OK, float 4.5 can be convert to int 4
		t['aaa'] = '4.5'  # ValueError, str '4.5' not valid

	example of a type_map_or_seq:
	   {'aaa': int, 'bbb': float}
	   (('aaa', int), ('bbb', float))

	 The type must either double as a factory function, or you must
	 map a factory function to the type using _factories attribute.
	'''
	def __init__(self, map_or_seq=None, type_map_or_seq=None):
		### create a KeyedDict to hold the types
		if type_map_or_seq is not None:
			### already provided
			self.__types = KeyedDict(type_map_or_seq)
			for key,valuetype in self.__types.items():
				self.__validateType(valuetype)
		elif map_or_seq is not None:
			### create it from the map_or_seq initializer
			self.__types = KeyedDict(map_or_seq)
			for key,value in self.__types.items():
				valuetype = type(value)
				self.__types[key] = valuetype
				self.__validateType(valuetype)
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
		'''
		In the spirit of keys(), values(), and items(), this method
		returns the types or each item.  These types exist for 
		the lifetime of the object.  This actually returns a
		KeyedDict object although the other methods return lists.
		Maybe this should return a list too...
		'''
		return KeyedDict(self.__types)

	def __validateType(self, type):
		f = self.getFactory(type)
		if f is None:
			raise TypeError('%s, invalid type for TypedDict item, try added it to the factories dict' % (type,))

	def __validateValue(self, key, value):
		'''uses a factory function from factories to validate a value'''
		# None is always valid
		if value is None:
			return None

		valuetype = self.__types[key]
		valuefactory = self.getFactory(valuetype)

		try:
			newvalue = valuefactory(value)
		except ValueError, detail:
			newdetail = '%s, value for %s must be %s; ' % (value, key,valuetype)
			newdetail += str(detail)
			raise TypeError(newdetail)
		except TypeError, detail:
			newdetail = '%s, value for %s must be %s; ' % (value, key,valuetype)
			newdetail += str(detail)
			raise TypeError(newdetail)
		return newvalue

	def __setitem__(self, key, value):
		newvalue = self.__validateValue(key, value)
		KeyedDict.__setitem__(self, key, newvalue)

	def getFactory(self, valuetype):
		## check for special cases that we know about
		if valuetype in self._factories:
			f = self._factories[valuetype]
		elif callable(valuetype):
			## type object may be a factory function
			f = valuetype
		else:
			f = None
		return f

	_factories = {
		## is None necessary? should factory convert anything to None?
		## Or raise exception for anything except None?
		NoneType: lambda x: None,

		## object type can handle anything. Should this use x.copy()?
		## Probably should, but classes in this module have no copy method.
		object: lambda x: x,

		## from Numeric
		NumericArrayType: validateNumericArray,
	}


if __name__ == '__main__':
	class newtype(object):
		pass
	d = {'a': 3, 'b': 777}
	initseq = [(1,2), ('a',8.4), ('bbb', 'a'), ('ccc', None), ('ordereddict', OrderedDict(d))]
	t = TypedDict(initseq)
	print 't', t
	print 't.types()', t.types()
