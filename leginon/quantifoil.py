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

	def solve(self, image, crop, vectorguess, tolerance, minrad, maxrad):
		edges = self.findEdges(image)
		Mrc.numeric_to_mrc(edges, 'edges.mrc')
		vectors = self.findLatticeVectors(edges, vectorguess, tolerance)
		#vector = self.findLatticeVectors(image, vectorguess, tolerance)
		print 'VECTORS', vectors

		image2 = image[crop[0]:crop[2], crop[1]:crop[3]]
		edges2 = self.findEdges(image2)
		temp_lattice = self.latticePoints(vectors, (-1,0,1))
		temp = self.createTemplate(edges2.shape, temp_lattice, minrad, maxrad)
		center = self.correlateTemplate(edges2, temp)
		print 'CENTER', center
		true_center = center[0] + crop[0], center[1] + crop[1]

		delta = apply(Numeric.hypot, vectors[0])
		imsize = max(image.shape)
		n = int(imsize / delta)
		print 'N', n
		points = range(-n,n)
		good_lattice = self.latticePoints(vectors, points)
		final_points = []
		for point in good_lattice:
			imagepoint = point[0] + true_center[0], point[1] + true_center[1]
			if imagepoint[0] >= 0 and imagepoint[0] < image.shape[0] and imagepoint[1] >= 0 and imagepoint[1] < image.shape[1]:
				final_points.append(imagepoint)
				imagefun.mark_image(image, imagepoint, 1500)
		Mrc.numeric_to_mrc(image, 'marked.mrc')
		return final_points

	def latticePoints(self, vectors, points):
		# perpendicular vector
		latticepoints = []
		for i1 in points:
			i1vect = (i1 * vectors[0][0], i1 * vectors[0][1])
			for i2 in points:
				i2vect = (i2 * vectors[1][0], i2 * vectors[1][1])
				point = (i1vect[0]+i2vect[0], i1vect[1]+i2vect[1])
				latticepoints.append(point)
		return latticepoints

	def findLatticeVectors(self, edges, guess1, tolerance):
		autocorr = imagefun.cross_correlate(edges,edges)
		shape = edges.shape

		## guess2 perpendicular to guess1
		guess2 = -guess1[1], guess1[0]

		vectors = []
		i = 0
		for guess in (guess1, guess2):
			## create a region of interest centered at guess
			rows = range(guess[0]-tolerance, guess[0]+tolerance+1)
			cols = range(guess[1]-tolerance, guess[1]+tolerance+1)
			roi_rows = Numeric.take(autocorr, rows, 0)
			roi = Numeric.take(roi_rows, cols, 1)
			Mrc.numeric_to_mrc(roi, 'autocorr%s.mrc' % (i))

			## to be proper, should use a circular mask here
			#mask = circle.get(shape, guess, 0, tolerance)
			#autocorr = Numeric.where(mask, autocorr, autocorr[guess[0]+tolerance,guess[1]])

			## find peak
			peak = self.peakfinder.subpixelPeak(newimage=roi, npix=5)
			roi_center = roi.shape[0]//2, roi.shape[1]//2
			v0 = (guess[0] + peak[0] - roi_center[0])
			v1 = (guess[1] + peak[1] - roi_center[1])
			vectors.append( (v0,v1) )
			i += 1

		return vectors

	def findEdges(self, image):

		image = self.lowPassFilter(image, 1.2)

		self.conv.setImage(image)
		# could probably get away with using gradient in only one direction
		kernel1 = convolver.sobel_row_kernel
		kernel2 = convolver.sobel_col_kernel
		edger = self.conv.convolve(kernel=kernel1)
		edgec = self.conv.convolve(kernel=kernel2)
		edges = Numeric.hypot(edger,edgec)

		## convolution leaves invalid borders
		# copy rows
		edges[0] = edges[1]
		edges[-1] = edges[-2]
		# copy cols
		edges[:,0] = edges[:,1]
		edges[:,-1] = edges[:,-2]

		# threshold
		edges = imagefun.zscore(edges)
		edges = Numeric.clip(edges, -0.5, 1.0)

		return edges

	def createTemplate(self, shape, centers, minrad, maxrad):
		temp = Numeric.zeros(shape, Numeric.Int8)
		for center in centers:
			newring = circle.get(shape, center, minrad, maxrad)
			temp = temp | newring
		return temp.astype(Numeric.Float32)

	def lowPassFilter(self, image, sigma, size=9):
		k = convolver.gaussian_kernel(size, sigma)
		smooth = self.conv.convolve(image=image, kernel=k)
		return smooth

	def correlateTemplate(self, edges, temp):
		cc = imagefun.cross_correlate(edges, temp)
		center = self.peakfinder.subpixelPeak(cc)
		return center


if __name__ == '__main__':
	import sys
	filename = sys.argv[1]
	guess = (int(sys.argv[2]), int(sys.argv[3]))
	tolerance = int(sys.argv[4])
	minrad = float(sys.argv[5])
	maxrad = float(sys.argv[6])

	qs = QuantifoilSolver()

	square = Mrc.mrc_to_numeric(filename)
	crop = (256,256,1024-256,1024-256)
	
	qs.solve(square, crop, guess, tolerance, minrad, maxrad)
