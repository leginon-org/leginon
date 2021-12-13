#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
import fftengine
import imagefun
import warnings

class Correlator(object):
	'''
	Provides correlation handling functions.
	A buffer of two images is maintained.
	'''
	def __init__(self, pad=False, shrink=False):
		self.fftengine = fftengine.fftEngine()
		self.clearBuffer()
		self.pad = pad
		self.shrink = shrink
		self.shrink_factor = 1

	def setImage(self, index, newimage):
		'''put a new image in the buffer'''
		if self.pad:
			newimage = imagefun.pad(newimage)
		if self.shrink:
			self.shrink_factor = imagefun.shrink_factor(newimage.shape)
			self.buffer[index]['image'] = imagefun.shrink(newimage)
		else:
			self.buffer[index]['image'] = newimage
		self.setFFT(index, None)
		self.initResults()

	def getImage(self, index):
		'''retrieve an image from the buffer'''
		ret = self.buffer[index]['image']
		return ret

	def setFFT(self, index, newfft):
		'''put a new fft in the buffer'''
		self.buffer[index]['fft'] = newfft

	def getFFT(self, index):
		'''retrieve an image fft from the buffer'''
		return self.buffer[index]['fft']

	def insertImage(self, newimage):
		'''Insert a new image into the image buffer, fifo style'''
		self.buffer[0]['image'] = self.buffer[1]['image']
		self.buffer[0]['fft'] = self.buffer[1]['fft']
		self.setImage(1, newimage)

	def clearBuffer(self):
		self.buffer = [
			{'image':None, 'fft':None},
			{'image':None, 'fft':None}
			]
		self.initResults()

	def initResults(self):
		self.results = {
			'cross correlation fft': None,
			'cross correlation image': None,
			'phase correlation fft': None,
			'phase correlation image': None,
			}

	def getResults(self, key=None):
		return self.results

	def crossCorrelationFFT(self):
		'''
		produce a cross correlation fft
		mainly an intermediate step
		'''

		if self.results['cross correlation fft'] is not None:
			return self.results['cross correlation fft']

		im0 = self.getImage(0)
		if im0 is None:
			raise MissingImageError('no image in buffer slot 0')

		im1 = self.getImage(1)
		if im1 is None:
			raise MissingImageError('no image in buffer slot 1')

		if im0.shape != im1.shape:
			raise RuntimeError('images not same dimensions')
		
		## calculate FFTs of subject images, if not already done
		fft0 = self.getFFT(0)
		if fft0 is None:
			fft0 = self.fftengine.transform(im0)
			self.setFFT(0, fft0)

		fft1 = self.getFFT(1)
		if fft1 is None:
			if im1 is im0:
				fft1 = fft0
			else:
				fft1 = self.fftengine.transform(im1)
			self.setFFT(1, fft1)

		ccfft = numpy.multiply(numpy.conjugate(fft0), fft1)
		self.results['cross correlation fft'] = ccfft
		return ccfft
	
	def crossCorrelate(self):
		'''calculate the cross correlation image'''
		if self.results['cross correlation image'] is None:
			# invert correlation to use
			self.crossCorrelationFFT()
			ccfft = self.results['cross correlation fft']

			cc = self.fftengine.itransform(ccfft)
			self.results['cross correlation image'] = cc
		else:
			cc = self.results['cross correlation image']
		return cc

	def phaseCorrelate(self, zero=True, wiener=False):
		# elementwise phase-correlation =
		# cross-correlation / magnitude(cross-correlation
		#print 'phaseCorrelate start'
		if self.results['phase correlation image'] is None:
			self.crossCorrelationFFT()
			ccfft = self.results['cross correlation fft']
			if wiener:
				rstart = int(0.4 * ccfft.shape[0])
				rstop = int(0.5 * ccfft.shape[0])
				region = ccfft[rstart:rstop]
				noise = 10 * numpy.mean(region.real * region.real + region.imag * region.imag)
				d = numpy.sqrt(ccfft.real*ccfft.real+ccfft.imag*ccfft.imag+noise)
			else:
				d = numpy.absolute(ccfft)

			try:
				with warnings.catch_warnings():
					# catch RuntimeWarning and turn them into exception
					warnings.simplefilter("error")
					pcfft = ccfft / d
			except RuntimeWarning:
				# use cross correlation and move on.
				pcfft = ccfft
			self.results['phase correlation fft'] = pcfft
			pc = self.fftengine.itransform(pcfft)
			if zero:
				pc[0, 0] = 0

			self.results['phase correlation image'] = pc
		return pc

#### this is a utility function to convert an unsigned coordinate
#### to a +- shift from 0 by wrapping around
def wrap_coord(coord, shape):
	wraplimit = (shape[0]/2, shape[1]/2)
	# if coord is past halfway, shift is negative, wrap
	if coord[0] < wraplimit[0]:
		wrapped0 = coord[0]
	else:
		wrapped0 = coord[0] - shape[0]
	if coord[1] < wraplimit[1]:
		wrapped1 = coord[1]
	else:
		wrapped1 = coord[1] - shape[1]
	return (wrapped0, wrapped1)

def cross_correlate(im1, im2, pad=False, shrink=False):
	cor = Correlator(pad=pad, shrink=shrink)
	cor.setImage(0, im2)
	cor.setImage(1, im1)
	return cor.crossCorrelate()

def phase_correlate(im1, im2, zero=True, pad=False, wiener=False, shrink=False):
	cor = Correlator(pad=pad, shrink=shrink)
	cor.setImage(0, im2)
	cor.setImage(1, im1)
	return cor.phaseCorrelate(zero=zero, wiener=wiener)

def auto_correlate(im, pad=False, shrink=False):
	return cross_correlate(im, im, pad=pad, shrink=shrink)

class MissingImageError(Exception):
	def __init__(self, info):
		Exception.__init__(self, info)


if __name__ == '__main__':
	import mrc, fftengine, peakfinder

	if 1:
		im1 = mrc.read('test1.mrc')
		im2 = mrc.read('test2.mrc')
	if 0:
		im1 = mrc.read('02dec12a.001.mrc')
		im2 = mrc.read('02dec12a.001.post.mrc')

	c = Correlator()
	p = peakfinder.PeakFinder()

	c.setImage(0,im2)
	for im in (im1, im2, im1, im2, im1, im2, im1):
		c.insertImage(im)
		try:
			c.phaseCorrelate()
		except:
			print 'exception in phaseCorrelate'
			raw_input('continue')
			continue

		res = c.getResults()
		pcim = res['phase correlation image']
		p.setImage(pcim)
		p.subpixelPeak()
		peak = p.getResults()['subpixel peak']
		
		shift = wrap_coord(peak, pcim.shape)

		raw_input('continue')



