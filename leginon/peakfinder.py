#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import Numeric
from LinearAlgebra import linear_least_squares, solve_linear_equations
import time

class PeakFinder(object):
	def __init__(self):
		self.initResults()

	def initResults(self):
		self.results = {
			'pixel peak': None,
			'subpixel peak': None
			}

	def setImage(self, newimage):
		self.image = newimage
		self.shape = newimage.shape
		self.initResults()

	def getResults(self):
		return self.results

	def pixelPeak(self, newimage=None):
		if newimage is not None:
			self.setImage(newimage)

		if self.results['pixel peak'] is None:
			flatimage = Numeric.ravel(self.image)
			peak = Numeric.argmax(flatimage)
			peakvalue = flatimage[peak]
			rows,cols = self.shape
			peakrow = peak / cols
			peakcol = peak % cols
			pixelpeak = (peakrow, peakcol)
			self.results['pixel peak'] = pixelpeak
			self.results['pixel peak value'] = peakvalue
			#print 'pixel peak value', peakvalue

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
		row0 = -coeffs[1] / 2.0 / coeffs[0]
		col0 = -coeffs[3] / 2.0 / coeffs[2]

		## find peak value
		peak = coeffs[0] * row0**2 + coeffs[1] * row0 + coeffs[2] * col0**2 + coeffs[3] * col0 + coeffs[4]

		return {'row': row0, 'col': col0, 'value': peak, 'minsum': minsum}

	def subpixelPeak(self, newimage=None, npix=5):
		if newimage is not None:
			self.setImage(newimage)

		if self.results['subpixel peak'] is not None:
			return self.results['subpixel peak']

		self.pixelPeak()
		peakrow,peakcol = self.results['pixel peak']

		rows,cols = self.shape

		rowrange = (peakrow-npix/2, peakrow+npix/2+1)
		rowinds = range(rowrange[0], rowrange[1])

		colrange = (peakcol-npix/2, peakcol+npix/2+1)
		colinds = range(colrange[0], colrange[1])

		## cut out a region of interest around the peak
		roi = Numeric.zeros((npix,npix), Numeric.Float32)
		for row in range(npix):
			for col in range(npix):
				srow = peakrow + row - npix/2
				if srow >= rows:
					srow -= rows
				scol = peakcol + col - npix/2
				if scol >= cols:
					scol -= cols
				roi[row,col] = self.image[srow,scol]

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
