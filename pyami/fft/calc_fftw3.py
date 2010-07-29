#!/usr/bin/env python
debug = True

import os
import platform

import fftw3
import numpy

import pyami.fileutil
import calc_base

class FFTW3Calculator(calc_base.Calculator):
	def __init__(self):
		calc_base.Calculator.__init__(self)
		self.plan_flags = ['measure']
		self.plan_threads = 4  # 4 seems best on both dual core and quad core systems
		self.import_wisdom()

	def local_wisdom_filename(self):
		path = pyami.fileutil.getMyDir()
		hostname = platform.node()
		filename = os.path.join(path, 'wisdom', hostname)
		return filename

	def export_local_wisdom(self):
		filename = self.local_wisdom_filename()
		dir = os.path.dirname(filename)
		pyami.fileutil.mkdirs(dir)
		fftw3.export_wisdom_to_file(filename)

	def import_wisdom(self):
		#### Try to import wisdom from various locations
		wisdom_found = []
		## system wisdom is normally kept in /etc/fftw/wisdom
		try:
			fftw3.import_system_wisdom()
			wisdom_found.append('system')
		except:
			pass
		## We also look for our own wisdom locally
		local_wisdom_file = self.local_wisdom_filename()
		try:
			fftw3.import_wisdom_from_file(local_wisdom_file)
			wisdom_found.append(local_wisdom_file)
		except:
			pass
		if debug:
			if wisdom_found:
				print 'fftw wisdom found:'
				for name in wisdom_found:
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

	def _forward(self, image_array):
		input_array = numpy.zeros(image_array.shape, numpy.float)
		fftshape = image_array.shape[0], image_array.shape[1]/2+1
		fft_array = numpy.zeros(fftshape, dtype=complex)
		plan = fftw3.Plan(input_array, fft_array, direction='forward', flags=self.plan_flags, nthreads=self.plan_threads)
		input_array[:] = image_array
		plan()
		return fft_array

	def _reverse(self, fft_array):
		imageshape = fft_array.shape[0], 2*(fft_array.shape[1]-1)
		image_array = numpy.zeros(imageshape, dtype=float32)
		input_array = numpy.zeros(fft_array.shape, dtype=complex)
		plan = fftw3.Plan(input_array, image_array, direction='backward', flags=self.plan_flags, nthreads=self.plan_threads)
		input_array[:] = fft_array
		plan()
		return image_array
