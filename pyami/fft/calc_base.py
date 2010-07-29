'''
This module defines the base class for all FFT calculators.
Subclasses must define:
	_forward  - takes image and returns fft
	_reverse  - takes fft and returns image
	make_full - takes output of _forward and returns full fft
	make_half - takes output of _forward and returns half fft
'''

import numpy

import pyami.weakattr

class Calculator(object):
	def __init__(self):
		self.stashing_on = True

	def enable_stashing(self):
		self.stashing_on = True

	def disable_stashing(self):
		# should we delete all stashed ffts?
		self.stashing_on = False

	def stash(self, main, name, associate):
		## prevent modification to both main and associate to ensure
		## that they correspond to each other forever
		if not self.stashing_on:
			return
		main.setflags(write=False)
		associate.setflags(write=False)
		pyami.weakattr.set(main, name, associate)

	def getStashed(self, main, name):
		try:
			f = pyami.weakattr.get(main, name)
		except AttributeError:
			f = None
		return f

	def unstash(self, main, name):
		associate = self.getStashed(main, name)
		if associate is None:
			# already unstashed
			return
		## no longer associated with each other, so make them writable
		main.setflags(write=True)
		associate.setflags(write=True)
		pyami.weakattr.set(main, 'fft', None)

	def forward_raw(self, image_array):
		## check if fft already associated with this image array
		f = self.getStashed(image_array, 'fft')
		if f is None:
			print 'REALLY DOING IT'
			f = self._forward(image_array)
			self.stash(image_array, 'fft', f)
		return f

	def forward(self, image_array, full=False, centered=False):
		fft_array = self.forward_raw(image_array)
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

	def OLD_calc_power(self, fft_array):
		pow = numpy.absolute(fft_array)
		try:
			pow = numpy.log(pow)
		except OverflowError:
			pow = numpy.log(pow+1e-20)
		return pow

	def _calc_power(self, fft_array):
		pow = numpy.absolute(fft_array)
		return pow

	def power(self, image_array, full=False, centered=False):
		fft_array = self.forward_raw(image_array)
		pow = self.getStashed(fft_array, 'power')
		if pow is None:
			pow = self._calc_power(fft_array)
			self.stash(fft_array, 'power', pow)
		pow = self.post_fft(pow, full, centered)
		return pow

