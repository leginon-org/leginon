#!/usr/bin/env python

import scipy.fftpack
import numpy

import calc_base

class FFTPACKCalculator(calc_base.Calculator):
	def __init__(self):
		calc_base.Calculator.__init__(self)

	def make_full(self, fft_array):
		return fft_array

	def make_half(self, fft_array):
		shape1 = int(fft_array.shape[1] / 2) + 1
		return fft_array[:,:shape1]

	def _forward(self, image_array):
		return scipy.fftpack.fft2(image_array)

	def _reverse(self, fft_array):
		return scipy.fftpack.ifft2(fft_array).real

	def _fshape(self, fft_array, real_shape):
		'''
		Create a new fft_array by cropping or padding that will invert to
		a real image of the given shape
		'''
		new_fft_shape = real_shape
		new_fft_array = numpy.zeros(new_fft_shape, dtype=fft_array.dtype)
		halfheight = min(new_fft_shape[0] / 2, fft_array.shape[0] / 2)
		halfwidth = min(new_fft_shape[1] / 2, fft_array.shape[1] / 2)
		new_fft_array[:halfheight,:halfwidth] = fft_array[:halfheight,:halfwidth]
		new_fft_array[-halfheight:,:halfwidth] = fft_array[-halfheight:,:halfwidth]
		new_fft_array[:halfheight,-halfwidth:] = fft_array[:halfheight,-halfwidth:]
		new_fft_array[-halfheight:,-halfwidth:] = fft_array[-halfheight:,-halfwidth:]
		norm = float(numpy.prod(fft_array.shape)) / float(numpy.prod(real_shape))
		new_fft_array /= norm
		return new_fft_array
