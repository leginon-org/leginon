#!/usr/bin/env python

# standard library
import cStringIO
import operator
import os
import cPickle
import types

# third party
import numpy
import scipy.misc
import scipy.ndimage
import scipy.stats

# myami
import pyami.mrc
#pyami.mrc.cache_enabled = True
import pyami.numpil
import pyami.imagefun
import pyami.fft
import pyami.resultcache
import pyami.weakattr

# local
import cache

cache_size = 400*1024*1024  # 400 MB
results = cache.Cache(cache_size)

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
			if name in kwargs:
				args_present.append(name)
				self.kwargs[name] = converter(kwargs[name])
			else:
				args_missing.append(name)
		for name, converter in self.optional_args.items():
			if name in kwargs:
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

class Read(Pipe):
	cache_file = False
	required_args = {'filename': os.path.abspath}

	def make_dirname(self):
		abs = os.path.abspath(self.kwargs['filename'])
		drive,tail = os.path.splitdrive(self.kwargs['filename'])
		self._dirname = tail[1:]

	def run(self, input, filename):
		## input ignored
		### determine input format
		if filename.endswith('mrc') or filename.endswith('MRC'):
			## use MRC module to read
			input_format = 'mrc'
		else:
			## use PIL to read
			input_format = 'PIL'

		### Read image file
		if input_format == 'mrc':
			# use mrc
			image_array = pyami.mrc.read(filename)
		elif input_format == 'PIL':
			# use PIL
			image_array = pyami.numpil.read(filename)
		return image_array

class Power(Pipe):
	switch_arg = 'power'
	def run(self, input):
		output = pyami.fft.calculator.power(input, full=True, centered=True)
		return output

def int_converter(value):
	return int(float(value))

class Mask(Pipe):
	required_args = {'maskradius': int_converter}
	def run(self, input, maskradius):
		maskradius = int(maskradius)
		output = pyami.imagefun.center_mask(input, maskradius, copy=True)
		return output

	def make_dirname(self):
		# only one arg, which is desriptive enough, so keeping it simple
		args = ['%s:%s' % (a,b) for (a,b) in self.args_tuple]
		self._dirname = ','.join(args)

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

class Shape(Pipe):
	required_args = {'shape': shape_converter}
	def run(self, input, shape):
		# make sure shape is same dimensions as input image
		if len(shape) != len(input.shape):
			raise ValueError('mismatch in number of dimensions: %s -> %s' % (input.shape, shape))

		# determine whether to use imagefun.bin or scipy.ndimage.zoom
		# for now, bin function only allows same bin factor on all axes
		binfactor = input.shape[0] / shape[0]
		zoomfactors = []
		for i in range(len(shape)):
			# zoom factor on this axis
			zoomfactors.append(float(shape[i])/float(input.shape[i]))

			# check original shape is divisible by new shape
			if input.shape[i] % shape[i]:
				binfactor = None   # binning will not work
				
			# check bin factor on this axis same as other axes
			if input.shape[i] / shape[i] != binfactor:
				binfactor = None  # binning will not work

		if binfactor:
			output = pyami.imagefun.bin(input, binfactor)
		else:
			output = scipy.ndimage.zoom(input, zoomfactors)
		return output

	def make_dirname(self):
		dims = map(str, self.kwargs['shape'])
		dims = 'x'.join(dims)
		self._dirname = dims

class Scale(Pipe):
	required_args = {'scaletype': str, 'scalemin': float, 'scalemax': float}
	def run(self, input, scaletype, scalemin, scalemax):
		if scaletype == 'minmax':
			result = self.scale_minmax(input, scalemin, scalemax)
		elif scaletype == 'stdev':
			result = self.scale_stdev(input, scalemin, scalemax)
		elif scaletype == 'cdf':
			result = self.scale_cdf(input, scalemin, scalemax)
		else:
			raise ValueError('bad scaletype: %s' % (scaletype,))
		return result

	def linearscale(self, input, min, max):
		image_array = pyami.imagefun.linearscale(input, (min, max), (0,255))
		image_array = numpy.clip(image_array, 0, 255)
		return image_array

	def scale_minmax(self, input, min, max):
		return self.linearscale(input, min, max)

	def scale_stdev(self, input, min, max):
		mean = pyami.arraystats.mean(input)
		std = pyami.arraystats.std(input)
		scalemin = mean + min * std
		scalemax = mean + max * std
		return self.linearscale(input, scalemin, scalemax)

	def scale_cdf(self, input, min, max):
		bins = 1000
		try:
			cumfreq, lower, width, x = pyami.weakattr.get(input, 'cumfreq')
		except:
			cumfreq, lower, width, x = scipy.stats.cumfreq(input, bins)
			pyami.weakattr.set(input, 'cumfreq', (cumfreq, lower, width, x))
		cumfreq = cumfreq / input.size
		pmin = True
		for j in range(bins):
			if pmin and cumfreq[j] >= min:
				pmin = False
				minval = j
			elif cumfreq[j] >= max:
				maxval = j
				break
		scalemin = lower + (minval+0.5) * width
		scalemax = lower + (maxval+0.5) * width
		return self.linearscale(input, scalemin, scalemax)

class Format(Pipe):
	optional_args = {'output_format': str}
	optional_defaults = {'output_format': 'JPEG'}
	file_formats = {'JPEG': '.jpg', 'GIF': '.gif', 'TIFF': '.tif', 'MRC': '.mrc'}
	def run(self, input, output_format='JPEG'):
		if output_format not in self.file_formats:
			raise ValueError('output_format: %s' % (output_format,))

		if output_format == 'MRC':
			s = self.run_mrc(input)
		else:
			s = self.run_pil(input, output_format)

		return s

	def run_mrc(self, input):
		file_object = cStringIO.StringIO()
		mrc.write(input, file_object)

	def run_pil(self, input, output_format):
		pil_image = scipy.misc.toimage(input)
		file_object = cStringIO.StringIO()
		pil_image.save(file_object, output_format)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def make_dirname(self):
		self._dirname = None

	def make_resultname(self):
		if 'output_format' in self.kwargs:
			format = self.kwargs['output_format']
		else:
			format = self.optional_defaults['output_format']
		self._resultname = 'result' + self.file_formats[format]

	def put_result(self, f, result):
		f.write(result)

	def get_result(self, f):
		return f.read()

pipe_order = [
	Read,
	Power,
	Mask,
	Shape,
	Scale,
	Format,
]

def kwargs_to_pipeline(**kwargs):
	pipeline = []
	for pipe_class in pipe_order:
		try:
			pipe = pipe_class(**kwargs)
		except PipeDisabled:
			print 'Pipe skipped: %s' % (pipe_class,)
			continue
		pipeline.append(pipe)
	return tuple(pipeline)

def process(**kwargs):
	pipeline = kwargs_to_pipeline(**kwargs)

	### find all or part of the pipeline result in the cache
	n = len(pipeline)
	for i in range(n):
		done = pipeline[:n-i]
		print 'Trying Get:', done
		result = results.get(done)
		if result is not None:
			remain = pipeline[n-i:]
			break

	if result is None:
		done = ()
		remain = pipeline

	print 'Done:', done

	### finish the remainder of the pipeline
	for pipe in remain:
		print 'Running', pipe
		result = pipe(result)
		done = done + (pipe,)
		results.put(done, result)

	return result


