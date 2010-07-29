'''
This module defines the base class for all FFT calculators.
Subclasses must define:
	_forward  - takes image and returns fft
	_reverse  - takes fft and returns image
	make_full - takes output of _forward and returns full fft
	make_half - takes output of _forward and returns half fft
'''

import pyami.weakattr

class Calculator(object):
	def __init__(self):
		self.stashing_on = True

	def enable_stashing(self):
		self.stashing_on = True

	def disable_stashing(self):
		# should we delete all stashed ffts?
		self.stashing_on = False

	def stash(self, image_array, fft_array):
		## prevent modification to both image and fft to ensure
		## that stashed fft corresponds to image forever
		image_array.setflags(write=False)
		fft_array.setflags(write=False)
		pyami.weakattr.set(image_array, 'fft', fft_array)

	def getStashedFFT(self, image_array):
		try:
			f = pyami.weakattr.get(image_array, 'fft')
		except AttributeError:
			f = None
		return f

	def unstash(self, image_array):
		fft_array = self.getStashedFFT(image_array)
		if fft_array is None:
			# already unstashed
			return
		## no longer associated with each other, so make them writable
		image_array.setflags(write=True)
		fft_array.setflags(write=True)
		pyami.weakattr.set(image_array, 'fft', None)

	def forward_if_necessary(self, image_array):
		## check if fft already associated with this image array
		f = self.getStashedFFT(image_array)
		if f is None:
			f = self._forward(image_array)
			if self.stashing_on:
				self.stash(image_array, f)
		return f

	def forward(self, image_array, full=False, centered=False):
		fft_array = self.forward_if_necessary(image_array)
		fft_array = self.post_fft(fft_array, full, centered)
		return fft_array

	def reverse(fft_array):
		return self._reverse(fft_array)

	def post_fft(self, fft_array, full=False, centered=False):
		'''handle conversion between full<->half, and centered or not'''
		if full:
			fft_array = self.make_full(fft_array)
			if centered:
				fft_array = pyami.imagefun.swap_quadrants(fft_array)
		else:
			fft_array = self.make_half(fft_array)
		return fft_array

	def _calc_power(self, fft_array):
		pow = numpy.absolute(fft_array)
		try:
			pow = numpy.log(pow)
		except OverflowError:
			pow = numpy.log(pow+1e-20)
		return pow

	def power(self, image_array, full=False, centered=False):
		fft_array = self.forward_if_necessary(image_array)
		pow = self._calc_power(fft_array)
		pow = self.post_fft(pow, full, centered)
		return pow

