#!/usr/bin/env python

import imagefun
import Mrc
import Numeric
import holefinderback
import convolver
import peakfinder

class CircleMaskCreator(object):
	def __init__(self):
		self.masks = {}

	def get(self, shape, center, minradius, maxradius):
		'''
		create binary mask of a circle centered at 'center'
		'''

		## wrap around negative values
		newcenter = list(center)
		while newcenter[0] < 0:
			newcenter[0] += shape[0]
		while newcenter[1] < 0:
			newcenter[1] += shape[1]
		center = tuple(newcenter)

		## use existing circle mask
		key = (shape, center, minradius, maxradius)
		if self.masks.has_key(key):
			return self.masks[key]

		## set up shift and wrapping of circle on image
		halfshape = shape[0] / 2.0, shape[1] / 2.0
		cutoff = [0.0, 0.0]
		lshift = [0.0, 0.0]
		gshift = [0.0, 0.0]
		for axis in (0,1):
			if center[axis] < halfshape[axis]:
				cutoff[axis] = center[axis] + halfshape[axis]
				lshift[axis] = 0
				gshift[axis] = -shape[axis]
			else:
				cutoff[axis] = center[axis] - halfshape[axis]
				lshift[axis] = shape[axis]
				gshift[axis] = 0
		minradsq = minradius*minradius
		maxradsq = maxradius*maxradius
		def circle(indices0,indices1):
			## this shifts and wraps the indices
			i0 = Numeric.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = Numeric.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			rsq = i0*i0+i1*i1
			c = Numeric.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c.astype(Numeric.Int8)
		temp = Numeric.fromfunction(circle, shape)
		self.masks[key] = temp
		return temp


circle = CircleMaskCreator()

class QuantifoilSolver(object):
	def __init__(self):
		self.peakfinder = peakfinder.PeakFinder()
		self.gradient = convolver.Convolver()

	def solve(self, image):
		pass

	def findLatticeVector(self, image, guess, tolerance):
		edges = self.findEdges(image)
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
		self.gradient.setImage(image)
		# could probably get away with using gradient in only one direction
		kernel1 = convolver.sobel_row_kernel
		kernel2 = convolver.sobel_col_kernel
		edger = self.gradient.convolve(kernel=kernel1)
		edgec = self.gradient.convolve(kernel=kernel2)
		edges = Numeric.hypot(edger,edgec)
		return edges

	def createTemplate(self, shape, vector, minrad, maxrad):
		# perpendicular vector
		vector2 = (-vector[1], vector[0])
		temp = Numeric.zeros(shape, Numeric.Int8)
		for i1 in (-1, 0, 1):
			i1vect = (i1 * vector[0], i1 * vector[1])
			for i2 in (-1, 0, 1):
				i2vect = (i2 * vector2[0], i2 * vector2[1])
				center = (i1vect[0]+i2vect[0], i1vect[1]+i2vect[1])
				newring = circle.get(shape, center, minrad, maxrad)
				fname = str(i1) + str(i2) + '.mrc'
				temp += newring
		return temp
		

	def findOffset(self, image, guess, tolerance):
		vector = self.findLatticeVector(image, guess, tolerance)


		
if __name__ == '__main__':
	import sys

	qs = QuantifoilSolver()
	temp = qs.createTemplate((1024,1024), (40,117), 20, 25)
	Mrc.numeric_to_mrc(temp, 'temp.mrc')
	sys.exit()


	filename = sys.argv[1]
	guess = (int(sys.argv[2]), int(sys.argv[3]))
	tolerance = int(sys.argv[4])

	square = Mrc.mrc_to_numeric(filename)
	
	vector = qs.findLatticeVector(square, guess, tolerance)
	print 'VECTOR', vector
