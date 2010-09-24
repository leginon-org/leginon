#!/usr/bin/env python

# standard library
import cPickle
import cStringIO
import types

# mapping of some string representations to bool value
bool_strings = {}
for s in ('true', 'on', 'yes'):
	bool_strings[s] = True
for s in ('false', 'off', 'no'):
	bool_strings[s] = False

def bool_converter(obj):
	'''
	Convert various objects to bool.
	If the string seems to be a bool or int representation, then treat it
	like one (default str to bool conversion only cares about empty/non-empty)
	'''
	if isinstance(obj, types.StringTypes):
		obj = obj.lower()
		if obj in bool_strings:
			# bool representation
			obj = bool_strings[obj]
		else:
			# numeric representation
			try:
				obj = float(obj)
			except:
				pass
	obj = bool(obj)
	return obj

def int_converter(value):
	return int(float(value))

def shape_converter(value):
	'''size must be either a bin factor integer or a shape of the form "AxB"'''
	# first convert value to sequence of numbers
	if isinstance(value, types.StringTypes):
		value = value.lower()
		numbers = value.split('x')
	else:
		numbers = list(value)
	# now convert numbers to integers
	numbers = map(float, numbers)
	numbers = map(int, numbers)
	return tuple(numbers)

class PipeInitError(Exception):
	pass

class PipeMissingArgs(PipeInitError):
	'''pipe init failed because some args given, but not all required args given'''
	pass

class PipeDisabled(PipeInitError):
	pass

class PipeSwitchedOff(PipeDisabled):
	'''pipe disabled because of switch argument'''
	pass

class PipeNoArgs(PipeDisabled):
	'''pipe disabled because no args were present'''
	pass

class Pipe(object):
	'''
	Base class for one step of a pipeline.
	These objects should be initialized with keyword arguments.
	The objects can then be called with the input as the only argument.
	'''
	switch_arg = None
	required_args = {}
	optional_args = {}
	optional_defaults = {}
	cache_file = True
	def __init__(self, **kwargs):
		self.parse_args(**kwargs)
		self.make_hash()
		self.make_names()

	def make_hash(self):
		self.signature = (self.__class__, self.args_tuple)
		self._hash = hash(self.signature)

	def make_names(self):
		self.make_dirname()
		self.make_resultname()

	def make_dirname(self):
		args = ['%s:%s' % (a,b) for (a,b) in self.args_tuple]
		args.insert(0, self.__class__.__name__)
		self._dirname = ','.join(args)

	def make_resultname(self):
		self._resultname = '00result.pickle'

	def put_result(self, f, result):
		cPickle.dump(result, f, cPickle.HIGHEST_PROTOCOL)

	def get_result(self, f):
		result = cPickle.load(f)
		return result

	def __hash__(self):
		return self._hash

	def __eq__(self, other):
		return self.signature == other.signature

	def __ne__(self, other):
		return self.signature != other.signature

	def __str__(self):
		parts = ['%s=%s' % (name,value) for (name,value) in self.signature[1]]
		allparts = ','.join(parts)
		return '%s(%s,%s)' % (self.__class__.__name__, id(self), allparts)

	def __repr__(self):
		return self.__str__()

	def resultname(self):
		return self._resultname

	def dirname(self):
		return self._dirname

	def parse_args(self, **kwargs):
		args_present = []
		args_missing = []
		if self.switch_arg:
			if self.switch_arg in kwargs:
				args_present.append(self.switch_arg)
				switch_arg_value = kwargs[self.switch_arg]
				enabled = bool_converter(switch_arg_value)
				if not enabled:
					raise PipeSwitchedOff('%s=%s' % (self.switch_arg, switch_arg_value))
			else:
				args_missing.append(self.switch_arg)

		self.kwargs = {}
		for name,converter in self.required_args.items():
			if name in kwargs and kwargs[name] is not None:
				args_present.append(name)
				self.kwargs[name] = converter(kwargs[name])
			else:
				args_missing.append(name)
		for name, converter in self.optional_args.items():
			if name in kwargs and kwargs[name] is not None:
				args_present.append(name)
				self.kwargs[name] = converter(kwargs[name])

		if args_missing:
			if args_present:
				raise PipeMissingArgs('got some args: %s, but missing: %s' % (args_present, args_missing))
			else:
				raise PipeNoArgs('pipe useless with no args')

		items = self.kwargs.items()
		items.sort()
		self.args_tuple = tuple(items)

	def __call__(self, input):
		return self.run(input, **self.kwargs)

	def run(self, input):
		raise NotImplementedError('define run')

	@classmethod
	def help_string(cls):
		f = cStringIO.StringIO()
		f.write('%s\n' % (cls.__name__,))
		if pipe_class.switch_arg:
			f.write('  %s\n' % (cls.switch_arg,))
		if cls.required_args:
			for arg in cls.required_args:
				f.write('  %s\n' % (arg,))
		if cls.optional_args:
			for arg in cls.optional_args:
				f.write('  %s (optional)\n' % (arg,))
		result = f.getvalue()
		f.close()
		return result
