#!/usr/bin/env python

'''
This module defines FFT and inverse FFT functions for 2-D numpy arrays.
It will use fftw3 if available, otherwise it will use scipy.fftpack.

The two public functions are "transform" and "itransform", with the following
usage:
	fft_array = transform(image_array, full=False, centered=False)
	image_array = itransform(fft_array)
'''

import numpy
import os
import platform

debug = True
#force_package = 'fftpack'
force_package = None

## try importing the fft packages:  fftw3 and scipy.fftpack
packages = {}
try:
	import fftw3
	packages['fftw3'] = fftw3
except:
	pass
try:
	import scipy.fftpack
	packages['fftpack'] = scipy.fftpack
except:
	pass
if not packages:
	raise ImportError('You need to install either fftw3 or scipy.fftpack')

## check for forced package, otherwise prefer fftw3 because it is faster
if force_package is not None:
	if force_package in packages:
		using = force_package
	else:
		raise ImportError('Forced package not imported: %s' % (force_package,))
elif 'fftw3' in packages:
	using = 'fftw3'
else:
	using = 'fftpack'
if debug:
	print 'fft package:', using

## functions that are defined differently depending on which fft package

if using == 'fftw3':
	plan_flags = ['measure']
	plan_threads = 1

	#### Try to import wisdom from various locations
	wisdom_found = []
	## system wisdom is normally kept in /etc/fftw/wisdom
	try:
		fftw3.import_system_wisdom()
		wisdom_found.append('system')
	except:
		pass
	## We also look for our own wisdom locally
	path = pyami.version.getInstalledLocation()
	hostname = platform.node()
	local_wisdom_file = os.path.join(path, 'wisdom', hostname)
	try:
		fftw3.import_wisdom_from_file(local_wisdom_file)
		wisdom_found.append(local_wisdom_file)
	except:
		pass
	if debug and wisdom_found:
		print 'fftw wisdom found:'
		for name in wisdom_found:
			print '  %s' % (name,)

	def make_full(fft_array):
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

	def make_half(fft_array):
		return fft_array

	def _fft(image_array):
		input_array = numpy.zeros(image_array.shape, numpy.float)
		fftshape = image_array.shape[0], image_array.shape[1]/2+1
		fft_array = numpy.zeros(fftshape, dtype=complex)
		#plan = fftw3.Plan(input_array, fft_array, direction='forward', flags=['measure'], nthreads=4)
		plan = fftw3.Plan(input_array, fft_array, direction='forward', flags=plan_flags, nthreads=plan_threads)
		input_array[:] = image_array
		plan()
		fftw3.export_wisdom_to_file('mywisdom')
		return fft_array

	def _ifft(fft_array):
		imageshape = fft_array.shape[0], 2*(fft_array.shape[1]-1)
		image_array = numpy.zeros(imageshape, dtype=float32)
		input_array = numpy.zeros(fft_array.shape, dtype=complex)
		plan = fftw3.Plan(input_array, image_array, direction='backward', flags=plan_flags, nthreads=plan_threads)
		input_array[:] = fft_array
		plan()
		return image_array

elif using == 'fftpack':
	def make_full(fft_array):
		return fft_array

	def make_half(fft_array):
		shape1 = int(fft_array.shape[1] / 2) + 1
		return fft_array[:,:shape1]

	def _fft(image_array):
		return scipy.fftpack.fft2(image_array)

	def _ifft(fft_array):
		return scipy.fftpack.ifft2(fft_array).real


def transform(image_array, full=False, centered=False):
	fft_array = _fft(image_array)
	if full:
		fft_array = make_full(fft_array)
	else:
		fft_array = make_half(fft_array)
	return fft_array

def itransform(fft_array):
	return _ifft(fft_array)

def _calc_power(fft_array):
	pow = numpy.absolute(fft_array)
	try:
		pow = numpy.log(pow)
	except OverflowError:
		pow = numpy.log(pow+1e-20)
	return pow

def power(image_array):
	fft_array = _fft(image_array)
	pow = _calc_power(fft_array)
	pow = make_full(pow)
	return pow

if __name__ == '__main__':
	import mrc
	import time
	a = mrc.read('4k.mrc')
	for i in range(5):
		t0 = time.time()
		transform(a)
		print 'time', time.time()-t0
