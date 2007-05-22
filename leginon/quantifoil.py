#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from pyami import convolver, peakfinder, fftengine, correlator, imagefun, mrc, arraystats
import Numeric
import holefinderback
import os

ffteng = fftengine.fftEngine()

def circle_template(shape, minrad, maxrad):
	## circle image, to be inserted into template image later
	cirsize = int(2 * (maxrad + 1))
	cirshape = (cirsize,cirsize)
	wrap = (cirsize+1) // 2
	indices = Numeric.indices(cirshape)
	indices[0][wrap:] -= cirshape[0]
	indices[1][:,wrap:] -= cirshape[1]
	minradsq = minrad ** 2
	maxradsq = maxrad ** 2
	rsq = indices[0] ** 2 + indices[1] ** 2
	c = Numeric.where((rsq>=minradsq)&(rsq<=maxradsq), 1, 0)
	c = c.astype(Numeric.Int8)

	## final template of correct shape
	temp = Numeric.zeros(shape, Numeric.Int8)
	temp[:wrap,:wrap] = c[:wrap,:wrap]
	temp[:wrap,-wrap:] = c[:wrap,-wrap:]
	temp[-wrap:,-wrap:] = c[-wrap:,-wrap:]
	temp[-wrap:,:wrap] = c[-wrap:,:wrap]
	return temp

def kernel_image(shape, kernel):
	im = Numeric.zeros(shape, Numeric.Float32)
	wrap = kernel.shape[0] / 2
	im[:wrap+1,:wrap+1] = kernel[wrap:,wrap:]
	im[:wrap+1,-wrap:] = kernel[wrap:,:wrap]
	im[-wrap:,-wrap:] = kernel[:wrap,:wrap]
	im[-wrap:,:wrap+1] = kernel[:wrap,wrap:]
	return im

def gaussian(shape, sigma, n=5):
	gk = convolver.gaussian_kernel(n, sigma)
	return kernel_image(shape, gk)

def sobel_row(shape):
	k = convolver.sobel_row_kernel
	return kernel_image(shape, k)

def sobel_col(shape):
	k = convolver.sobel_col_kernel
	return kernel_image(shape, k)


_save_mrc = True
def save_mrc(image, filename):
	if _save_mrc: 
		print 'saving ', filename
		p = 'qimages'
		f = os.path.join(p, filename)
		mrc.write(image, f)

import timer

class QuantifoilSolver(object):
	def __init__(self):
		self.peakfinder = peakfinder.PeakFinder()
		self.conv = convolver.Convolver()

	def solve(self, image, crop1, crop2, vectorguess, tolerance, radius, thickness):
		## initial crop before vector search
		if crop1 is not None:
			print 'cropping image'
			image2 = image[crop1[0]:crop1[2], crop1[1]:crop1[3]]
		else:
			image2 = image
		print 'finding edges'
		t = timer.Timer('edge')
		edges2 = self.findEdges(image2)
		t.stop()
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
		temp = self.template(edges3.shape, vectors, radius, thickness)

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

	def template(self, shape, vectors, radius, thickness):
		## create lattice points image
		lat_im = Numeric.zeros(shape, Numeric.Float32)
		temp_lattice = self.latticePoints(vectors, (-1,0,1))
		print 'temp_lattice', temp_lattice
		for point in temp_lattice:
			p = int(round(point[0])),int(round(point[1]))
			lat_im[p] = 1.0
		lat_fft = ffteng.transform(lat_im)
		mrc.write(lat_im, 'lat_im.mrc')

		## create ring image
		minrad = radius - thickness / 2.0
		maxrad = radius + thickness / 2.0
		cir_im = circle_template(shape, minrad, maxrad)
		cir_fft = ffteng.transform(cir_im)
		mrc.write(cir_im, 'cir_im.mrc')

		## convolve
		temp_fft = Numeric.multiply(lat_fft, cir_fft)
		temp = ffteng.itransform(temp_fft)
		return temp

	def findLatticeVectors(self, edges, guess1, tolerance):
		print 'edges', edges.typecode()
		autocorr = correlator.auto_correlate(edges)
		save_mrc(autocorr, 'autocorr.mrc')
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
		gk = gaussian(image.shape, 1.2)
		srk = sobel_row(image.shape)
		sck = sobel_col(image.shape)

		imfft = ffteng.transform(image)
		gkfft = ffteng.transform(gk)
		srkfft = ffteng.transform(srk)
		sckfft = ffteng.transform(sck)

		smooth = Numeric.multiply(imfft, gkfft)

		refft = Numeric.multiply(smooth, srkfft)
		cefft = Numeric.multiply(smooth, sckfft)

		re = ffteng.itransform(refft)
		ce = ffteng.itransform(cefft)

		edges = Numeric.hypot(re,ce)

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
		# works for everything except test_square7
		#edges = Numeric.clip(edges, -0.5, 1.0)
		edges = imagefun.threshold(edges, 0.8)

		print 'done'
		return edges



	def lowPassFilter(self, image, sigma, size=9):
		k = convolver.gaussian_kernel(size, sigma)
		smooth = self.conv.convolve(image=image, kernel=k)
		return smooth

	def correlateTemplate(self, edges, temp):
		cc = correlator.cross_correlate(edges, temp)
		save_mrc(cc, 'cc.mrc')
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
		mean = arraystats.mean(roi)
		std = arraystats.std(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}

import fftengine
ffteng = fftengine.fftEngine()
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
	thickness = float(sys.argv[6])

	qs = QuantifoilSolver()

	square = mrc.read(filename)
	#crop1 = (256,256,1024-256,1024-256)
	#crop1 = (0,0,1024,1024)
	crop1 = None
	crop2 = None
	qs.solve(square, crop1, crop2, vectorguess, vectortol, radguess, thickness)
