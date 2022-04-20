#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
ma = numpy.ma
from pyami import arraystats

class CircleMaskCreator(object):
	def __init__(self):
		self.masks = {}

	def get(self, shape, center, minradius, maxradius):
		'''
		create binary mask of a circle centered at 'center'
		'''
		## use existing circle mask
		key = (shape, center, minradius, maxradius)
		if key in self.masks.keys():
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
			i0 = numpy.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = numpy.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			rsq = i0*i0+i1*i1
			c = numpy.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c.astype(numpy.int8)
		temp = numpy.fromfunction(circle, shape)
		self.masks[key] = temp
		return temp

	def get_circle_stats(self, image, coord, radius, save_mrc=False):
		if save_mrc:
			from pyami import mrc
		## select the region of interest
		rmin = int(coord[0]-radius)
		rmax = int(coord[0]+radius)
		cmin = int(coord[1]-radius)
		cmax = int(coord[1]+radius)
		## beware of boundaries
		if rmin < 0 or rmax >= image.shape[0] or cmin < 0 or cmax > image.shape[1]:
			return None
		subimage = image[rmin:rmax+1, cmin:cmax+1]
		if save_mrc:
			mrc.write(subimage, 'hole.mrc')
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.get(subimage.shape, center, 0, radius)
		if save_mrc:
			mrc.write(mask, 'holemask.mrc')
		im = numpy.ravel(subimage)
		mask = numpy.ravel(mask)
		roi = numpy.compress(mask, im)
		mean = arraystats.mean(roi)
		std = arraystats.std(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}
