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
		self.indices = {}

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
		if shape in self.indices:
			return self.indices[shape]

		wrap0 = (shape[0]+1)/2
		wrap1 = (shape[1]+1)/2
		indices = Numeric.indices(shape)
		indices[0][wrap0:] -= shape[0]
		indices[1][:,wrap1:] -= shape[1]

		self.indices[shape] = indices
		return indices

	def get(self, shape, center, minradius, maxradius, value=1):
		'''
		create binary mask of a circle centered at 'center'
		with minradiux and maxradius
		'''
		minradsq = minradius*minradius
		maxradsq = maxradius*maxradius

		def circle(indices0,indices1):
			i0 = indices0 - center[0]
			i1 = indices0 - center[0]
			rsq = i0*i0+i1*i1
			print 'B'
			c = Numeric.where((rsq>=minradsq)&(rsq<=maxradsq), value, 0)
			print 'C'
			return c.astype(Numeric.Int8)
		## this is like Numeric.from_function, but I want to create
		## my own indices
		indices = self.wrapped_indices(shape)
		temp = apply(circle, tuple(indices))
		return temp

circle = CircleTemplateCreator()

_save_mrc = True
def save_mrc(image, filename):
	if _save_mrc: 
		print 'saving ', filename
		Mrc.numeric_to_mrc(image, filename)

class QuantifoilSolver(object):
	def __init__(self):
		self.peakfinder = peakfinder.PeakFinder()
		self.conv = convolver.Convolver()

	def solve(self, image, crop1, crop2, vectorguess, tolerance, minrad, maxrad):
		## initial crop before vector search
		if crop1 is not None:
			print 'cropping image'
			image2 = image[crop1[0]:crop1[2], crop1[1]:crop1[3]]
		else:
			image2 = image
		print 'finding edges'
		edges2 = self.findEdges(image2)
		save_mrc(edges2, 'edges.mrc')

		## find the vectors based on guess and tolerance
		print 'finding vectors'
		vectors = self.findLatticeVectors(edges2, vectorguess, tolerance)
		print 'VECTOR0', vectors[0]
		print 'VECTOR1', vectors[1]

		## second crop before center search
		if crop2 is not None:
			print 'cropping image'
			image3 = image2[crop2[0]:crop2[2], crop2[1]:crop2[3]]
			edges3 = edges2[crop2[0]:crop2[2], crop2[1]:crop2[3]]
		else:
			image3 = image2
			edges3 = edges2

		print 'creating template from vectors'
		# should calculate size of template more carefully
		temp_lattice = self.latticePoints(vectors, (-1,0,1))
		temp = self.createTemplate(edges3.shape, temp_lattice, minrad, maxrad)
		print 'finding center'
		center = self.correlateTemplate(edges3, temp)
		print 'CENTER', center

		## find actual center based on prior cropping
		true_center = list(center)
		if crop1 is not None:
			center[0] += crop1[0]
			center[1] += crop1[1]
		if crop2 is not None:
			center[0] += crop2[0]
			center[1] += crop2[1]

		print 'clean up'
		# This is the brainless way to figure out the complete lattice.
		# It makes sure to cover the entire image.
		vectordist = apply(Numeric.hypot, vectors[0])
		maxdist = apply(Numeric.hypot, image.shape)
		n = int(maxdist / vectordist)
		points = range(-n,n)
		good_lattice = self.latticePoints(vectors, points)
		final_points = []
		for point in good_lattice:
			imagepoint = point[0] + true_center[0], point[1] + true_center[1]
			if imagepoint[0] >= 0 and imagepoint[0] < image.shape[0] and imagepoint[1] >= 0 and imagepoint[1] < image.shape[1]:
				final_points.append(imagepoint)
				imagefun.mark_image(image, imagepoint, 1500)
		save_mrc(image, 'marked.mrc')
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

	def createTemplate(self, shape, centers, minrad, maxrad):
		temp = Numeric.zeros(shape, Numeric.Int8)
		for center in centers:
			print 'c', center
			newring = circle.get(shape, center, minrad, maxrad)
			temp = temp | newring
		return temp.astype(Numeric.Float32)

	def template(self, shape, vectors, radius, thickness):
		temp_lattice = self.latticePoints(vectors, (-1,0,1))
		temp = self.createTemplate(edges3.shape, temp_lattice, minrad, maxrad)

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
			save_mrc(roi, 'autocorr%s.mrc' % (i))

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

		print 'low pass'
		image = self.lowPassFilter(image, 1.2)
		#k = convolver.gaussian_kernel(size, sigma)
		#smooth = self.conv.convolve(image=image, kernel=k)

		print 'setImage'
		self.conv.setImage(image)
		# could probably get away with using gradient in only one direction
		print 'kernel setup'
		kernel1 = convolver.sobel_row_kernel
		kernel2 = convolver.sobel_col_kernel
		print 'edger'
		edger = self.conv.convolve(kernel=kernel1)
		print 'edgec'
		edgec = self.conv.convolve(kernel=kernel2)
		print 'hypot'
		edges = Numeric.hypot(edger,edgec)

		## convolution leaves invalid borders
		# copy rows
		print 'clean up'
		edges[0] = edges[1]
		edges[-1] = edges[-2]
		# copy cols
		edges[:,0] = edges[:,1]
		edges[:,-1] = edges[:,-2]

		# threshold
		print 'threshold'
		edges = imagefun.zscore(edges)
		print 'clip'
		edges = Numeric.clip(edges, -0.5, 1.0)

		print 'done'
		return edges

	def lowPassFilter(self, image, sigma, size=9):
		k = convolver.gaussian_kernel(size, sigma)
		smooth = self.conv.convolve(image=image, kernel=k)
		return smooth

	def correlateTemplate(self, edges, temp):
		cc = imagefun.cross_correlate(edges, temp)
		center = self.peakfinder.subpixelPeak(cc)
		return center

	def get_hole_stats(self, image, coord, radius):
		## select the region of interest
		rmin = int(coord[0]-radius)
		rmax = int(coord[0]+radius)
		cmin = int(coord[1]-radius)
		cmax = int(coord[1]+radius)
		## beware of boundaries
		if rmin < 0 or rmax >= image.shape[0] or cmin < 0 or cmax > image.shape[1]:
			return None

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		save_mrc(subimage, 'hole.mrc')
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.circle.get(subimage.shape, center, 0, radius)
		save_mrc(mask, 'holemask.mrc')
		im = Numeric.ravel(subimage)
		mask = Numeric.ravel(mask)
		roi = Numeric.compress(mask, im)
		mean = imagefun.mean(roi)
		std = imagefun.stdev(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}

import fftengine
ffteng = fftengine.fftNumeric()
def power(numericarray):
	fft = ffteng.transform(numericarray)
	amplitude = Numeric.absolute(fft)
	return amplitude

if __name__ == '__main__':
	import sys
	filename = sys.argv[1]
	vectorguess = (int(sys.argv[2]), int(sys.argv[3]))
	vectortol = int(sys.argv[4])
	radguess = float(sys.argv[5])
	radtol = float(sys.argv[6])

	minrad = radguess - radtol
	maxrad = radguess + radtol

	qs = QuantifoilSolver()

	square = Mrc.mrc_to_numeric(filename)
	#crop1 = (256,256,1024-256,1024-256)
	#crop1 = (0,0,1024,1024)
	crop1 = None
	crop2 = None
	qs.solve(square, crop1, crop2, vectorguess, vectortol, minrad, maxrad)
