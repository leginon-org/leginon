#!/usr/bin/env python
debug = True

import os
import platform
import sys

sys.stderr.write('*** Using custom copy of fftw3 wrapper\n')
from pyami.fft import fftw3
import numpy

import calc_base

import pyami.fileutil
import pyami.cpu

def log(msg):
	sys.stderr.write('calc_fftw3: ')
	sys.stderr.write(msg)
	sys.stderr.write('\n')

# determine number of cpus
try:
	threads = pyami.cpu.count()
	log('%s CPUs found, setting threads=%s' % (threads,threads))
except:
	log('could not get number of CPUs, setting threads=1')
	threads = 1

## args that are always passed to plan creation
global_plan_kwargs = {
	'flags': ['estimate'],
	'nthreads': threads,  # number of logical cpus seems best
}

## where to look for user customized wisdom
home = os.path.expanduser('~')
wisdom_file = 'fftw3-wisdom-' + platform.node()
wisdom_file = os.path.join(home, wisdom_file)

def load_wisdom():
	try:
		fftw3.import_system_wisdom()
		if debug:
			log('system wisdom imported')
	except:
		pass
	try:
		fftw3.import_wisdom_from_file(wisdom_file)
		if debug:
			log('local wisdom imported')
	except:
		pass

def store_wisdom():
		if os.path.exists(wisdom_file):
			os.remove(wisdom_file)
		fftw3.export_wisdom_to_file(wisdom_file)

class FFTW3Calculator(calc_base.Calculator):
	def __init__(self):
		calc_base.Calculator.__init__(self)
		load_wisdom()

	def make_full(self, fft_array):
		fftheight, fftwidth = fft_array.shape
		fullheight = fftheight
		fullwidth = 2*(fftwidth-1)
		fullshape = fullheight, fullwidth
		full_array = numpy.empty(fullshape, fft_array.dtype)
		## fill in left half
		full_array[:,:fftwidth] = fft_array
		## fill in right half
		full_array[0,fftwidth:] = numpy.fliplr(fft_array[:1,1:-1])
		full_array[1:,fftwidth:] = numpy.rot90(fft_array[1:,1:-1], 2)
		return full_array

	def make_half(self, fft_array):
		return fft_array

	def plan(self, *args, **kwargs):
		'''wrapper around fftw3.Plan to combine global and custom args'''
		all_kwargs = {}
		all_kwargs.update(global_plan_kwargs)
		all_kwargs.update(kwargs)
		plan = fftw3.Plan(*args, **all_kwargs)
		return plan

	def _forward(self, image_array):
		input_array = numpy.empty(image_array.shape, numpy.float)
		fftshape = image_array.shape[0], image_array.shape[1]/2+1
		fft_array = numpy.empty(fftshape, dtype=complex)
		newplan = self.plan(input_array, fft_array, direction='forward')
		input_array[:] = image_array
		newplan()
		return fft_array

	def _reverse(self, fft_array):
		imageshape = fft_array.shape[0], 2*(fft_array.shape[1]-1)
		image_array = numpy.empty(imageshape, dtype=numpy.float)
		input_array = numpy.empty(fft_array.shape, dtype=numpy.complex)
		newplan = self.plan(input_array, image_array, direction='backward')
		input_array[:] = fft_array
		newplan()
		return image_array

	def _fshape(self, fft_array, real_shape):
		'''
		Create a new fft_array by cropping or padding that will invert to
		a real image of the given shape
		'''
		new_fft_shape = real_shape[0], real_shape[1]/2+1
		new_fft_array = numpy.zeros(new_fft_shape, dtype=fft_array.dtype)
		halfheight = min(new_fft_shape[0] / 2, fft_array.shape[0] / 2)
		width = min(new_fft_shape[1], fft_array.shape[1])
		new_fft_array[:halfheight,:width] = fft_array[:halfheight,:width]
		new_fft_array[-halfheight:,:width] = fft_array[-halfheight:,:width]
		norm = fft_array.shape[0] * 2 * (fft_array.shape[1]-1)
		new_fft_array /= norm
		return new_fft_array
