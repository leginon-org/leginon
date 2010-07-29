#!/usr/bin/env python
debug = True

import os
import platform

import fftw3
import numpy

import calc_base

import pyami.fileutil

## args that are always passed to plan creation
global_plan_kwargs = {
	'flags': ['measure'],  # 'patient' never seems to help
	'nthreads': 4,  # 4 seems best on both dual core and quad core systems
}

## set up where to find local wisdom.  Under this directory, there will
## be a wisdom file named after the host.
mydir = pyami.fileutil.getMyDir()
local_wisdom_path = os.path.join(mydir, 'wisdom')

class FFTW3Calculator(calc_base.Calculator):
	def __init__(self):
		calc_base.Calculator.__init__(self)
		self.import_wisdom()

	def local_wisdom_filename(self):
		hostname = platform.node()
		filename = os.path.join(local_wisdom_path, hostname)
		return filename

	def export_local_wisdom(self):
		filename = self.local_wisdom_filename()
		if os.path.exists(filename):
			os.remove(filename)
		dir = os.path.dirname(filename)
		pyami.fileutil.mkdirs(dir)
		fftw3.export_wisdom_to_file(filename)

	def import_local_wisdom(self):
		local_wisdom_file = self.local_wisdom_filename()
		try:
			fftw3.import_wisdom_from_file(local_wisdom_file)
			self.wisdom_found.append(local_wisdom_file)
		except:
			pass

	def import_wisdom(self):
		self.wisdom_found = []
		#### Try to import wisdom from various locations
		## system wisdom is normally kept in /etc/fftw/wisdom
		try:
			fftw3.import_system_wisdom()
			self.wisdom_found.append('system')
		except:
			pass
		## We also look for our own wisdom locally
		self.import_local_wisdom()
		if debug:
			if self.wisdom_found:
				print 'fftw wisdom found:'
				for name in self.wisdom_found:
					print '  %s' % (name,)
			else:
				print 'no wisdom found'

	def make_full(self, fft_array):
		fftheight, fftwidth = fft_array.shape
		fullheight = fftheight
		fullwidth = 2*(fftwidth-1)
		fullshape = fullheight, fullwidth
		full_array = numpy.zeros(fullshape, fft_array.dtype)
		## fill in left half
		full_array[:,:fftwidth] = fft_array
		## fill in right half
		full_array[0,fftwidth:] = numpy.fliplr(fft_array[:1,1:-1])
		full_array[1:,fftwidth:] = numpy.rot90(fft_array[1:,1:-1], 2)
		return full_array

	def make_half(self, fft_array):
		return fft_array

	def plan(self, *args, **kwargs):
		'''wrapper around fftw3.Plan, so we can track changes in wisdom'''
		wisdom_before = fftw3.export_wisdom_to_string()
		all_kwargs = {}
		all_kwargs.update(global_plan_kwargs)
		all_kwargs.update(kwargs)
		plan = fftw3.Plan(*args, **all_kwargs)
		wisdom_after = fftw3.export_wisdom_to_string()
		if len(wisdom_before) != len(wisdom_after):
			if debug:
				print 'wisdom updated, saving new local wisdom file'
			self.export_local_wisdom()
		return plan

	def _forward(self, image_array):
		input_array = numpy.zeros(image_array.shape, numpy.float)
		fftshape = image_array.shape[0], image_array.shape[1]/2+1
		fft_array = numpy.zeros(fftshape, dtype=complex)
		newplan = self.plan(input_array, fft_array, direction='forward')
		input_array[:] = image_array
		newplan()
		return fft_array

	def _reverse(self, fft_array):
		imageshape = fft_array.shape[0], 2*(fft_array.shape[1]-1)
		image_array = numpy.zeros(imageshape, dtype=float32)
		input_array = numpy.zeros(fft_array.shape, dtype=complex)
		newplan = self.plan(input_array, image_array, direction='backward')
		input_array[:] = fft_array
		newplan()
		return image_array
