#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

try:
	import numarray as Numeric
	from numarray.linear_algebra import linear_least_squares
except:
	import Numeric
	from LinearAlgebra import linear_least_squares

class FindPeakError(Exception):
	pass

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
		try:
			row0 = -coeffs[1] / 2.0 / coeffs[0]
			col0 = -coeffs[3] / 2.0 / coeffs[2]
		except ZeroDivisionError:
			raise FindPeakError('peak least squares fit has zero coefficient')

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

def findPixelPeak(image):
	peak = Numeric.argmax(image.flat)
	rows, cols = image.shape
	peakrow, peakcol = divmod(peak, cols)
	peakvalue = image[peakrow, peakcol]
	pixelpeak = (peakrow, peakcol)
	results = {}
	results['pixel peak'] = pixelpeak
	results['pixel peak value'] = peakvalue
	return results

def weightedPeakFit(numarray):
	rows, cols = numarray.shape
	w = numarray/numarray[rows/2, cols/2]
	rowoffset = 0.0
	columnoffset = 0.0
	for i in range(rows):
		for j in range(cols):
			if i == 0 and j == 0:
				continue
			di = i - rows/2
			dj = j - cols/2
			angle = Numeric.arctan2(di, dj)
			weight = Numeric.absolute(Numeric.sin(angle)) + Numeric.absolute(Numeric.cos(angle))
			rowoffset += Numeric.sin(angle)*w[i, j]/weight
			columnoffset += Numeric.cos(angle)*w[i, j]/weight
	return {'row': rowoffset, 'col': columnoffset}

def quadraticPeakFit(numarray):
	rows, cols = numarray.shape

	# create design matrix and vector
	dm = Numeric.zeros(rows * cols * 5, numarray.type())
	dm.shape = (rows * cols, 5)
	v = Numeric.zeros((rows * cols,), numarray.type())

	i = 0
	for row in range(rows):
		for col in range(cols):
			dm[i] = (row**2, row, col**2, col, 1)
			v[i] = numarray[row, col]
			i += 1

	# fit quadratic
	fit = linear_least_squares(dm, v)
	coeffs = fit[0]
	minsum = fit[1][0]

	# find root
	row0 = -coeffs[1] / 2.0 / coeffs[0] - rows/2
	col0 = -coeffs[3] / 2.0 / coeffs[2] - cols/2

	## find peak value
	peak = coeffs[0] * row0**2 + coeffs[1] * row0 + coeffs[2] * col0**2 + coeffs[3] * col0 + coeffs[4]

	return {'row': row0, 'col': col0, 'value': peak, 'minsum': minsum}

def findSubpixelPeak(image, npix=5):
	results = findPixelPeak(image)
	peakrow, peakcol = results['pixel peak']

	rows, cols = image.shape

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
			roi[row,col] = image[srow,scol]

	# fit a quadratic to it and find the subpixel peak
	roipeak = quadraticPeakFit(roi)
	#roipeak = weightedPeakFit(roi)
	srow = peakrow + roipeak['row']
	scol = peakcol + roipeak['col']

	subpixelpeak = (srow, scol)
	results['subpixel peak'] = subpixelpeak
	try:
		results['subpixel peak value'] = roipeak['value']
		results['minsum'] = roipeak['minsum']
	except KeyError:
		pass
	return results

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
