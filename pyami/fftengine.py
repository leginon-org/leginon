#!/usr/bin/env python

import quietscipy
import scipy.fftpack
import scipy.__config__

def real_fft2d(*args, **kwargs):
	return scipy.fftpack.fft2(*args, **kwargs)

def inverse_real_fft2d(*args, **kwargs):
	return scipy.fftpack.ifft2(*args, **kwargs).real

import time

class _fftEngine(object):
	'''base class for a FFT engine'''
	def __init__(self, *args, **kwargs):
		self.showtime = 0

	def transform(self, image):
		transimage = self.timer(self._transform, (image,))
		return transimage

	def itransform(self, image):
		itransimage = self.timer(self._itransform, (image,))
		return itransimage

	def timer(self, func, args=()):
		t0 = time.time()
		ret = apply(func, args)
		t1 = time.time()
		total = t1 - t0
		if self.showtime:
			print '%s %.5f' % (func.__name__, total)

		return ret

	def _transform(self, image):
		raise NotImplementedError()

	def _itransform(self, image):
		raise NotImplementedError()


class fftEngine(_fftEngine):
	'''subclass of fftEngine which uses FFT from scipy module'''
	def __init__(self, *args, **kwargs):
		_fftEngine.__init__(self)

	def _transform(self, im):
		fftim = real_fft2d(im)
		return fftim

	def _itransform(self, fftim):
		im = inverse_real_fft2d(fftim)
		return im

