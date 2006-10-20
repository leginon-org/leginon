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

try:
	import numarray as Numeric
	from numarray.linear_algebra import linear_least_squares
except:
	import Numeric
	from LinearAlgebra import linear_least_squares

class FindPeakError(Exception):
	pass

class PeakFinder(object):
	def __init__(self, lpf=None):
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
		'''
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
		'''
		if newimage is not None:
			self.setImage(newimage)

		if self.results['pixel peak'] is None:

			if None not in (guess, limit):
				#print 'GUESS,LIMIT', guess, limit
				cropcenter = limit[0]/2.0-0.5, limit[1]/2.0-0.5
				im = imagefun.crop_at(self.image, guess, limit)
			else:
				cropcenter = None
				im = self.image


			flatimage = Numeric.ravel(im)
			peak = Numeric.argmax(flatimage)
			peakvalue = flatimage[peak]
			rows,cols = im.shape
			peakrow = peak / cols
			peakcol = peak % cols
			#print 'IM PEAK', peakrow, peakcol

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

		return self.results['pixel peak']

	def quadFitPeak(self, numarray):
		'''
		fit 2d quadratic to a Numeric array which should
		contain a peak.
		Returns the peak coordinates, and the peak value
		'''
		rows,cols = numarray.shape

		## create design matrix and vector
		dm = Numeric.zeros(rows * cols * 5, Numeric.Float32)
		dm.shape = (rows * cols, 5)
		v = Numeric.zeros((rows * cols,), Numeric.Float32)

		i = 0
		for row in range(rows):
			for col in range(cols):
				dm[i] = (row**2, row, col**2, col, 1)
				v[i] = numarray[row,col]
				i += 1

		## fit quadratic
		fit = linear_least_squares(dm, v)
		coeffs = fit[0]
		minsum = fit[1][0]

		## find root
		try:
			row0 = -coeffs[1] / 2.0 / coeffs[0]
			col0 = -coeffs[3] / 2.0 / coeffs[2]
		except ZeroDivisionError:
			raise FindPeakError('peak least squares fit has zero coefficient')

		## find peak value
		peak = coeffs[0] * row0**2 + coeffs[1] * row0 + coeffs[2] * col0**2 + coeffs[3] * col0 + coeffs[4]

		return {'row': row0, 'col': col0, 'value': peak, 'minsum': minsum}

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
		srow = peakrow + roipeak['row'] - npix/2
		scol = peakcol + roipeak['col'] - npix/2
		peakvalue = roipeak['value']
		peakminsum = roipeak['minsum']

		subpixelpeak = (srow, scol)
		self.results['subpixel peak'] = subpixelpeak
		self.results['subpixel peak value'] = peakvalue
		self.results['minsum'] = peakminsum
		return subpixelpeak
	
	def clearBuffer(self):
		self.image = None
		self.shape = None
		self.initResults()

def findPixelPeak(image, guess=None, limit=None):
	pf = PeakFinder()
	pf.pixelPeak(newimage=image, guess=guess, limit=limit)
	return pf.getResults()

def findSubpixelPeak(image, npix=5, guess=None, limit=None):
	pf = PeakFinder()
	pf.subpixelPeak(newimage=image, npix=npix, guess=guess, limit=limit)
	return pf.getResults()

if __name__ == '__main__':
	im = Numeric.array(
		[[1,1,1],
		[1,3,2],
		[1,1,1]]
		)

	p = PeakFinder()
	p.setImage(im)
	p.pixelPeak()
	p.subpixelPeak()
	res = p.getResults()
	print 'results', res
