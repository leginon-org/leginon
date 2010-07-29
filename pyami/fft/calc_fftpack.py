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
