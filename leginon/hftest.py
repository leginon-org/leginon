#!/usr/bin/env python

import imagefun
import Mrc
import Numeric
import holefinderback
import convolver
import peakfinder

class CircleTemplateCreator(object):
	def __init__(self):
		self.templates = {}

	def wrapped_indices(self, shape):
		'''
		creates a set of indices like Numeric.indices, but 
		includes negative values, which wrap around to the second
		half of the image
		'''
		## These wrap limits are selected such that at least half (odd
		## shape leads to one more row/col) of the image will remain
		## the same, and the rest will be the wrapped negative side.
		# Integer division is intended here.
		wrap0 = (shape[0]+1)/2
		wrap1 = (shape[1]+1)/2
		indices = Numeric.indices(shape)
		indices[0][wrap0:] -= shape[0]
		indices[1][:,wrap1:] -= shape[1]
		return indices

	def get(self, shape, center, minradius, maxradius, value=1):
		'''
		create binary mask of a circle centered at 'center'
		with minradiux and maxradius
		'''
		## use existing circle mask
		key = (shape, center, minradius, maxradius)
		if self.templates.has_key(key):
			return self.templates[key]

		minradsq = minradius*minradius
		maxradsq = maxradius*maxradius
		def circle(indices0,indices1):
			i0 = indices0 - center[0]
			i1 = indices1 - center[1]
			rsq = i0*i0+i1*i1
			c = Numeric.where((rsq>=minradsq)&(rsq<=maxradsq), value, 0)
			return c.astype(Numeric.Int8)
		## this is like Numeric.from_function, but I want to create
		## my own indices
		indices = self.wrapped_indices(shape)
		temp = apply(circle, tuple(indices))
		self.templates[key] = temp
		return temp

circle = CircleTemplateCreator()

class QuantifoilSolver(object):
	def __init__(self):
		self.peakfinder = peakfinder.PeakFinder()
		self.conv = convolver.Convolver()

	def solve(self, image):
		pass

	def findLatticeVector(self, image, guess, tolerance):
		edges = self.edges = self.findEdges(image)
		autocorr = imagefun.cross_correlate(edges,edges)

		shape = square.shape

		## create a mask to select the region of interest
		ring = circle.get(shape, guess, 0, tolerance)
		autocorr = Numeric.where(ring, autocorr, autocorr[guess[0]+tolerance,guess[1]])

		## crop:  only need first quadrant up to the guess plus tolerance
		autocorr = autocorr[:guess[0]+tolerance, :guess[1]+tolerance]

		## find peak
		peak = self.peakfinder.subpixelPeak(newimage=autocorr)
		return peak

	def findEdges(self, image):
		self.conv.setImage(image)
		# could probably get away with using gradient in only one direction
		kernel1 = convolver.sobel_row_kernel
		kernel2 = convolver.sobel_col_kernel
		edger = self.conv.convolve(kernel=kernel1)
		edgec = self.conv.convolve(kernel=kernel2)
		edges = Numeric.hypot(edger,edgec)
		return edges

	def createTemplate(self, shape, vector, minrad, maxrad):
		# perpendicular vector
		vector2 = (-vector[1], vector[0])
		temp = Numeric.zeros(shape, Numeric.Int8)
		for i1 in (-3, -2, -1, 0, 1, 2, 3):
			i1vect = (i1 * vector[0], i1 * vector[1])
			for i2 in (-3, -2, -1, 0, 1, 2, 3):
				i2vect = (i2 * vector2[0], i2 * vector2[1])
				center = (i1vect[0]+i2vect[0], i1vect[1]+i2vect[1])
				newring = circle.get(shape, center, minrad, maxrad)
				temp = temp | newring
		return temp.astype(Numeric.Float32)

	def lowPassFilter(self, image, sigma, size=9):
		k = convolver.gaussian_kernel(size, sigma)
		smooth = self.conv.convolve(image=image, kernel=k)
		return smooth

	def findOffset(self, image, guess, tolerance, minrad, maxrad):
		print 'findLatticeVector'
		vector = self.findLatticeVector(image, guess, tolerance)
		print 'VECTOR', vector
		print 'createTemplate'
		temp = self.createTemplate(image.shape, vector, minrad, maxrad)
		#temp = self.lowPassFilter(temp, 1.0)
		print 'cross_correlate'
		#cc = imagefun.cross_correlate(self.edges, temp)
		print 'zscore edges'
		edges = imagefun.zscore(self.edges)
		Mrc.numeric_to_mrc(edges, 'edges.mrc')
		print 'zscore temp'
		temp = imagefun.zscore(temp)
		Mrc.numeric_to_mrc(temp, 'temp.mrc')
		#cc = imagefun.phase_correlate(edges, temp)
		cc = imagefun.cross_correlate(edges, temp)
		#cc = self.lowPassFilter(cc, 1.0)
		Mrc.numeric_to_mrc(cc, 'cc.mrc')
		print 'subpixelPeak'
		peak = self.peakfinder.subpixelPeak(cc)
		return peak


if __name__ == '__main__':
	import sys
	filename = sys.argv[1]
	guess = (int(sys.argv[2]), int(sys.argv[3]))
	tolerance = int(sys.argv[4])
	minrad = float(sys.argv[5])
	maxrad = float(sys.argv[6])

	qs = QuantifoilSolver()

	square = Mrc.mrc_to_numeric(filename)
	
	center = qs.findOffset(square, guess, tolerance, minrad, maxrad)
	print 'CENTER', center
