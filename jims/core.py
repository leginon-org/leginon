#!/usr/bin/env python

# standard library
import cStringIO

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

import pyami.mem

cache_size = 400*1024*1024  # 400 MB
results = pyami.resultcache.ResultCache(cache_size)

class Pipe(object):
	'''
	Base class for one step of a pipeline.
	These objects should be initialized with keyword arguments.
	The objects can then be called with the input as the only argument.
	'''
	required_args = {}
	optional_args = {}
	def __init__(self, **kwargs):
		self.ready = False
		self.parse_args(**kwargs)
		self.make_hash()

	def make_hash(self):
		items = self.kwargs.items()
		items.sort()
		self.signature = (self.__class__, tuple(items))
		self._hash = hash(self.signature)

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

	def parse_args(self, **kwargs):
		self.kwargs = {}
		for name,type in self.required_args.items():
			if name in kwargs:
				self.kwargs[name] = type(kwargs[name])
			else:
				return
		self.ready = True
		for name, type in self.optional_args.items():
			if name in kwargs:
				self.kwargs[name] = type(kwargs[name])

	def __call__(self, input):
		return self.run(input, **self.kwargs)

	def run(self, input):
		raise NotImplementedError('define run')

class Read(Pipe):
	required_args = {'filename': str}

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
	required_args = {'power': int}
	optional_args = {'mask': int}
	def run(self, input, power, mask=None):
		output = pyami.fft.calculator.power(input, full=True, centered=True, mask=mask)
		return output

class Bin(Pipe):
	required_args = {'bin': int}
	def run(self, input, bin):
		output = pyami.imagefun.bin(input, bin)
		return output

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

class Generate(Pipe):
	optional_args = {'output_format': str}
	def run(self, input, output_format='JPEG'):
		### convert array to PIL image
		pil_image = scipy.misc.toimage(input)
		### generate desired output format
		s = self.output_to_string(pil_image, output_format)
		return s

	def output_to_string(self, pil_image, output_format):
		file_object = cStringIO.StringIO()
		self.output_to_file(pil_image, output_format, file_object)
		image_string = file_object.getvalue()
		file_object.close()
		return image_string

	def output_to_file(self, pil_image, output_format, file_object):
		pil_image.save(file_object, output_format)

pipe_order = [
	Read,
	Power,
	Bin,
	Scale,
	Generate,
]

def kwargs_to_pipeline(**kwargs):
	pipeline = []
	for pipe_class in pipe_order:
		pipe = pipe_class(**kwargs)
		if pipe.ready:
			pipeline.append(pipe)
	return tuple(pipeline)

def process(**kwargs):
	pipeline = kwargs_to_pipeline(**kwargs)

	### find all or part of the pipeline result in the cache
	n = len(pipeline)
	for i in range(n+1):
		done = pipeline[:n-i]
		remain = pipeline[n-i:]
		result = results.get(done)
		if result is not None:
			break

	### finish the remainder of the pipeline
	for pipe in remain:
		print 'RUNNING', pipe
		result = pipe(result)
		done = done + (pipe,)
		results.put(done, result)
	import pyami.mem

	return result


