#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Numeric
import fftengine

## chose a FFT engine class
if fftengine.fftFFTW is None:
	fftclass = fftengine.fftNumeric
else:
	fftclass = fftengine.fftFFTW

class Correlator(object):
	'''
	Provides correlation handling functions.
	A buffer of two images is maintained.
	'''
	def __init__(self):
		self.fftengine = fftclass()
		self.clearBuffer()

	def setImage(self, index, newimage):
		'''put a new image in the buffer'''
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

		ccfft = Numeric.multiply(Numeric.conjugate(fft0), fft1)
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
		return cc

	def phaseCorrelate(self):
		# elementwise phase-correlation =
		# cross-correlation / magnitude(cross-correlation
		#print 'phaseCorrelate start'
		if self.results['phase correlation image'] is None:
			self.crossCorrelationFFT()
			ccfft = self.results['cross correlation fft']

			pcfft = ccfft / Numeric.absolute(ccfft)
			self.results['phase correlation fft'] = pcfft
			pc = self.fftengine.itransform(pcfft)
			## average out the artifical peak at 0,0
			pc[0,0] = (pc[0,1] + pc[0,-1] + pc[1,0] + pc[-1,0]) /4.0

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


class MissingImageError(Exception):
	def __init__(self, info):
		Exception.__init__(self, info)


if __name__ == '__main__':
	from Mrc import mrc_to_numeric
	from Tkinter import *
	from ImageViewer import ImageViewer
	import fftengine, peakfinder

	tk = Tk()
	iv = ImageViewer(tk)
	iv.pack()

	if 1:
		im1 = mrc_to_numeric('test1.mrc')
		im2 = mrc_to_numeric('test2.mrc')
	if 0:
		im1 = mrc_to_numeric('02dec12a.001.mrc')
		im2 = mrc_to_numeric('02dec12a.001.post.mrc')

	### set estimate = 0 for optimized fft (but longer planning step)
	if sys.platform == 'win32':
		f = fftengine.fftNumeric()
	else:
		f = fftengine.fftFFTW(estimate=1)
	c = Correlator(f)
	p = peakfinder.PeakFinder()

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
		#print 'peak', peak
		
		shift = wrap_coord(peak, pcim.shape)
		#print 'shift', shift

		#iv.import_numeric(pcim)
		#iv.update()

		raw_input('continue')



