#!/usr/bin/env python

#
# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see  http://ami.scripps.edu/software/leginon-license
#

import convolver
import imagefun

import numpy
import quietscipy
import scipy.ndimage as nd_image
from scipy.linalg import lstsq as linear_least_squares

class FindPeakError(Exception):
	pass

class PeakFinder(object):
	def __init__(self, lpf=1.5):
		self.initResults()
		if lpf is not None:
			self.lpf = True
			gauss = convolver.gaussian_kernel(lpf)
			self.filter = convolver.Convolver(kernel=gauss)
		else:
			self.lpf = False

	def initResults(self):
		self.results = {
			'pixel peak': None,
			'subpixel peak': None
			}

	def setImage(self, newimage):
		if self.lpf:
			self.image = self.filter.convolve(image=newimage)
		else:
			self.image = newimage
		self.shape = newimage.shape
		self.initResults()

	def getResults(self):
		return self.results

	def pixelPeak(self, newimage=None, guess=None, limit=None):
		"""
		guess = where to center your search for the peak (row,col)
		limit = shape of the search box (with guess at the center)
		Setting guess and limit can serve two purposes:
			1) You can imit your peak search if you are pretty sure
				where it will be
			2) Given that the image may wrap around into negative
				space, you can specify that you want to search for the peak
				in these out of bounds areas.  For instance, a (512,512)
				image may have a peak at (500,500).  You may specify a guess
				of (-10,-10) and a relatively small limit box.
				The (500,500) peak will be found, but it will be returned
				as (-12,-12).
		"""
		if newimage is not None:
			self.setImage(newimage)

		if self.results['pixel peak'] is None:

			if None not in (guess, limit):
				cropcenter = limit[0]/2.0-0.5, limit[1]/2.0-0.5
				im = imagefun.crop_at(self.image, guess, limit)
			else:
				cropcenter = None
				im = self.image

			peak = numpy.argmax(im.ravel())
			peakvalue = im.flat[peak]
			rows,cols = im.shape
			peakrow = peak / cols
			peakcol = peak % cols

			if cropcenter is not None:
				peakrow = int(round(guess[0]+peakrow-cropcenter[0]))
				peakcol = int(round(guess[1]+peakcol-cropcenter[1]))

			pixelpeak = (peakrow, peakcol)
			self.results['pixel peak'] = pixelpeak
			self.results['pixel peak value'] = peakvalue
			if peakrow < 0:
				unsignedr = peakrow + self.image.shape[0]
			else:
				unsignedr = peakrow
			if peakcol < 0:
				unsignedc = peakcol + self.image.shape[0]
			else:
				unsignedc = peakcol
			self.results['unsigned pixel peak'] = unsignedr,unsignedc

			#NEIL's SNR calculation
			self.results['noise']  = nd_image.standard_deviation(im)
			self.results['mean']   = nd_image.mean(im)
			self.results['signal'] = self.results['pixel peak value'] - self.results['mean']
			if self.results['noise'] == self.results['noise'] and self.results['noise'] != 0.0:
				self.results['snr'] = self.results['signal'] / self.results['noise']
			else:
				self.results['snr'] = self.results['pixel peak value']
			#print self.results['noise'],self.results['mean'],self.results['signal'],self.results['snr']

		return self.results['pixel peak']
	"""
	def gaussFitPeak(self, a):
		sol = gaussfit.gaussfit(a)
		return {'row': sol[0][3], 'col': sol[0][4], 'minsum': sol[2], 'coeffs': sol[0], 'value':None }
	"""

	def quadFitPeak(self, a):
		'''
		fit 2d quadratic to a numpy array which should
		contain a peak.
		Returns the peak coordinates, and the peak value
		'''
		rows,cols = a.shape

		## create design matrix and vector
		dm = numpy.zeros(rows * cols * 5, numpy.float32)
		dm.shape = (rows * cols, 5)
		v = numpy.zeros((rows * cols,), numpy.float32)

		i = 0
		for row in range(rows):
			for col in range(cols):
				dm[i] = (row**2, row, col**2, col, 1)
				v[i] = a[row,col]
				i += 1

		try:
			## find root
			## fit quadratic
			fit = linear_least_squares(dm, v)
			coeffs = fit[0]
			minsum = fit[1]
			row0 = -coeffs[1] / 2.0 / coeffs[0]
			col0 = -coeffs[3] / 2.0 / coeffs[2]
		except ZeroDivisionError:
			raise FindPeakError('peak least squares fit has zero coefficient')
		except ValueError:
			raise FindPeakError('peak least squares fit has bad coefficient')

		## find peak value
		peak = coeffs[0] * row0**2 + coeffs[1] * row0 + coeffs[2] * col0**2 + coeffs[3] * col0 + coeffs[4]

		return {'row': row0, 'col': col0, 'value': peak, 'minsum': minsum, 'coeffs': coeffs}

	def subpixelPeak(self, newimage=None, npix=5, guess=None, limit=None):
		'''
		see pixelPeak doc string for info about guess and limit
		'''
		if newimage is not None:
			self.setImage(newimage)

		if self.results['subpixel peak'] is not None:
			return self.results['subpixel peak']

		self.pixelPeak(guess=guess, limit=limit)
		peakrow,peakcol = self.results['pixel peak']

		## cut out a region of interest around the peak
		roi = imagefun.crop_at(self.image, (peakrow,peakcol), (npix,npix))

		## fit a quadratic to it and find the subpixel peak
		roipeak = self.quadFitPeak(roi)
		#roipeak = self.gaussFitPeak(roi)
		subfailed = False
		if roipeak['row'] < 0 or roipeak['row'] > npix or numpy.isnan(roipeak['row']):
			srow = float(peakrow)
			subfailed = True
		else:
			srow = peakrow + roipeak['row'] - npix/2
		if roipeak['col'] < 0 or roipeak['col'] > npix or numpy.isnan(roipeak['col']):
			scol = float(peakcol)
			subfailed = True
		else:
			scol = peakcol + roipeak['col'] - npix/2

		peakvalue = roipeak['value']
		peakminsum = roipeak['minsum']

		subpixelpeak = (srow, scol)
		self.results['subpixel peak'] = subpixelpeak
		self.results['subpixel peak value'] = peakvalue
		self.results['minsum'] = peakminsum
		self.results['coeffs'] = roipeak['coeffs']
		self.results['subfailed'] = subfailed

		#NEIL's SNR calculation
		self.results['noise']  = nd_image.standard_deviation(self.image)
		self.results['mean']   = nd_image.mean(self.image)
		self.results['signal'] = self.results['pixel peak value'] - self.results['mean']
		if self.results['noise'] == self.results['noise'] and self.results['noise'] != 0.0:
			self.results['snr'] = self.results['signal'] / self.results['noise']
		else:
			self.results['snr'] = self.results['pixel peak value']

		return subpixelpeak
	
	def clearBuffer(self):
		self.image = None
		self.shape = None
		self.initResults()

def findPixelPeak(image, guess=None, limit=None, lpf=None):
	pf = PeakFinder(lpf=lpf)
	pf.pixelPeak(newimage=image, guess=guess, limit=limit)
	return pf.getResults()

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	pf = PeakFinder(lpf=lpf)
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

def test1():
	im = numpy.array(
		[[1,1,1],
		[1,3,2],
		[1,1,1]]
		)
	p = PeakFinder(lpf=None)
	p.setImage(im)
	p.pixelPeak()
	p.subpixelPeak(npix=3)
	res = p.getResults()
	print 'results', res

def test2(mrc1, mrc2):
	import Mrc
	import correlator
	cor = correlator.Correlator()
	im1 = Mrc.mrc_to_numeric(mrc1)
	im2 = Mrc.mrc_to_numeric(mrc2)

	'''
	im1 = im1[:512,:512]
	im2 = im2[200:712,200:712]
	'''

	cor.insertImage(im1)
	cor.insertImage(im2)
	pc = cor.phaseCorrelate()
	Mrc.numeric_to_mrc(pc, 'pc.mrc')
	print findSubpixelPeak(pc, npix=7, lpf=1.0)

if __name__ == '__main__':
	import sys
	test1()
	#test2(sys.argv[1], sys.argv[2])
