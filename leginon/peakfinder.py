#!/usr/bin/env python

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
			peak = Numeric.argmax(self.image.flat)
			rows,cols = self.shape
			peakrow = peak / rows
			peakcol = peak % rows
			pixelpeak = (peakrow, peakcol)
			self.results['pixel peak'] = pixelpeak

		return self.results['pixel peak']

	def subpixelPeak(self, npix=3, newimage=None):
		if newimage is not None:
			self.setImage(newimage)

		if self.results['subpixel peak'] is not None:
			return self.results['subpixel peak']

		self.pixelPeak()
		peakrow,peakcol = self.results['pixel peak']

		rows,cols = self.shape

		rowrange = (peakrow-npix/2, peakrow+npix/2+1)
		rowinds = Numeric.arrayrange(rowrange[0], rowrange[1])

		## fill in rowvals, wrap around array if necessary
		rowvals = []
		for row in rowinds:
			if row < 0:
				rowvals.append(self.image[rows + row, peakcol])
			elif row >= rows:
				rowvals.append(self.image[row - rows, peakcol])
			else:
				rowvals.append(self.image[row, peakcol])
		rowvals = Numeric.array(rowvals)

		colrange = (peakcol-npix/2, peakcol+npix/2+1)
		colinds = Numeric.arrayrange(colrange[0], colrange[1])

		## fill in colvals, wrap around array if necessary
		colvals = []
		for col in colinds:
			if col < 0:
				colvals.append(self.image[peakrow, cols + col])
			elif col >= cols:
				colvals.append(self.image[peakrow, col - cols])
			else:
				colvals.append(self.image[peakrow, col])
		colvals = Numeric.array(colvals)

		## create quadratic design matrix for row data
		row_dm = Numeric.zeros(npix * 3, Numeric.Float)
		row_dm.shape = (npix, 3)
		i = 0
		for row in rowinds:
			row_dm[i] = (1.0, row, row*row)
			i += 1

		## create quadratic design matrix for col data
		col_dm = Numeric.zeros(npix * 3, Numeric.Float)
		col_dm.shape = (npix, 3)
		i = 0
		for col in colinds:
			col_dm[i] = (1.0 ,col, col*col)
			i += 1

		## fit and find zero
		## use simple equation solver for case of 3 points
		if npix == 3:
			rowcoeffs = solve_linear_equations(row_dm, rowvals)
			colcoeffs = solve_linear_equations(col_dm, colvals)
		else:
			rowfit = linear_least_squares(row_dm, rowvals)
			rowcoeffs = rowfit[0]
			colfit = linear_least_squares(col_dm, colvals)
			colcoeffs = colfit[0]

		rowzero = -rowcoeffs[1][0] / 2 / rowcoeffs[2][0]
		colzero = -colcoeffs[1][0] / 2 / colcoeffs[2][0]

		subpixelpeak = (float(rowzero), float(colzero))
		self.results['subpixel peak'] = subpixelpeak
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
