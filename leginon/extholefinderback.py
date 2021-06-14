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
import pyami.quietscipy
import scipy.ndimage
import math
from pyami import imagefun, peakfinder, convolver, correlator, mrc, arraystats
import ice

hole_template_files = {}
hole_templates = {}

class CircleMaskCreator(object):
	def __init__(self):
		self.masks = {}

	def get(self, shape, center, minradius, maxradius):
		'''
		create binary mask of a circle centered at 'center'
		'''
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
			i0 = numpy.where(indices0<cutoff[0], indices0-center[0]+lshift[0], indices0-center[0]+gshift[0])
			i1 = numpy.where(indices1<cutoff[1], indices1-center[1]+lshift[1], indices1-center[0]+gshift[1])
			rsq = i0*i0+i1*i1
			c = numpy.where((rsq>=minradsq)&(rsq<=maxradsq), 1.0, 0.0)
			return c.astype(numpy.int8)
		temp = numpy.fromfunction(circle, shape)
		self.masks[key] = temp
		return temp

class ExtHole(object):
	def __init__(self, point):
		self.stats = {}
		self.stats['center'] = tuple(point) # (row, col)

### Note:  we should create a base class ImageProcess
### which defines the basic idea of a series of operations on
### an image or a pipeline of operations.
### In subclasses such as HoleFinder, we would just have to define
### the steps and the dependencies.  The dependency checking and result
### management would be taken care of by the base class.
class HoleFinder(object):
	'''
	Create an instance of HoleFinder:
		hf = HoleFinder()
	Give it an image to work with:
		hf['original'] = some_numeric_array
	Configure the processes:
		hf.configure_extholes(hole_diameter, spacing, cmd)
		hf.configure_holestats(radius)
		hf.configure_ice(i0, tmin, tmax)
	Do the processes step by step, or the whole thing:
		hf.find_holes()
	'''
	def __init__(self):
		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None,
			'extholes': None,
			'holes': None,
			'markedholes': None,
			'holes2': None,
			'markedholes2': None,
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('extholes',),
			'extholes': ('holes',),
			'holes': ('holes2','markedholes'),
			'markedholes': (),
			'holes2': ('markedholes2',),
			'markedholes2': (),
		}

		## other necessary components
		self.convolver = convolver.Convolver()
		self.circle = CircleMaskCreator()
		self.icecalc = ice.IceCalculator()

		## some default configuration parameters
		self.save_mrc = False
		self.extholes_config = {'command':'','hole_diameter':30}
		self.holestats_config = {'radius': 20}
		self.ice_config = {'i0': None, 'min': 0.0, 'max': 0.1, 'std': 0.05}

	def __getitem__(self, key):
		return self.__results[key]

	def __setitem__(self, key, value):
		## only some images are allowed to be set externally
		## (right now, only original)
		if key in ('original',):
			self.__update_result(key, value)

	def __update_result(self, key, image):
		'''
		This updates a result in the self.__results dict.
		It also clears all dependent results.
		'''
		## clear my dependents recursively
		for depkey in self.__dependents[key]:
			self.__update_result(depkey, None)
		## update this result
		self.__results[key] = image

	def configure_extholes(self, diameter=None, spacing=None, command=None):
		if diameter is not None:
			self.extholes_config['hole diameter'] = diameter
		if spacing is not None:
			self.extholes_config['spacing'] = spacing
		if command is not None:
			self.extholes_config['command'] = command

	def run_extholes(self):
		'''
		Find holes with external command.
		'''
		#self.extholes_config should be set before calling this.
		fromimage = 'original'
		if self.__results[fromimage] is None:
			raise RuntimeError('need image %s before running external program' % (fromimage,))

		diameter = self.extholes_config['hole diameter']
		spacing =	self.extholes_config['spacing']
		command = self.extholes_config['command']

		# Put your function call here:
		# use command to find holes using self.__results[fromimage] as input
		# For example:
		# holes_found = your_holefinder(self.__results[fromimage], diameter, spacing)

		# Here is an example of the result. (row,col)
		holes_found = [(120,100),(50,80),(20,30)] # list of (row,col) coordinates of the holes as output.
		# update the results with the key extholes
		self.__update_result('extholes', self.points_to_extholes(holes_found))

	def points_to_extholes(self, points):
			'''
			Create a list of Hole objects to carry information.
			'''
			extholes = []
			for p in points:
				extholes.append(ExtHole(p))
			return extholes

	def swapxy(self, points):
		return [(point[1],point[0]) for point in points]

	def extholes_to_holes(self):
		'''
		Convert extholes to holes with stats.
		'''
		if self.__results['extholes'] is None:
			raise RuntimeError('need to run external command to create hole stats')

		shape = self.__results['original'].shape
		# make make list of blob coords:
		extholes = self.__results['extholes']
		points = []
		pointdict = {}
		for ehole in extholes:
			point = tuple(ehole.stats['center']) # (r,c)
			points.append(point)
			pointdict[point] = ehole

		if not points:
			holes = []
		else:
			holes = extholes
		self.__update_result('holes', holes)

	def updateHoles(self, holes):
		self.__update_result('holes', holes)

	def mark_holes(self):
		'''
		Create an image that shows the holes. This is for debug purpose.
		'''
		if self.__results['holes'] is None or self.__results['original'] is None:
			raise RuntimeError('need original image and holes before marking holes')
		image = self.__results['original']
		im = image.copy()
		value = arraystats.min(im)
		for hole in self.__results['holes']:
			coord = hole.stats['center']
			imagefun.mark_image(im, coord, value)
		self.__update_result('markedholes', im)
		if self.save_mrc:
			mrc.write(im, 'markedholes.mrc')

	def get_hole_stats(self, image, coord, radius):
		'''
		calculate stats at a circle around the coordinate.
		'''
		## select the region of interest
		rmin = int(coord[0]-radius)
		rmax = int(coord[0]+radius)
		cmin = int(coord[1]-radius)
		cmax = int(coord[1]+radius)
		## beware of boundaries
		if rmin < 0 or rmax >= image.shape[0] or cmin < 0 or cmax > image.shape[1]:
			return None

		subimage = image[rmin:rmax+1, cmin:cmax+1]
		if self.save_mrc:
			mrc.write(subimage, 'hole.mrc')
		center = subimage.shape[0]/2.0, subimage.shape[1]/2.0
		mask = self.circle.get(subimage.shape, center, 0, radius)
		if self.save_mrc:
			mrc.write(mask, 'holemask.mrc')
		im = numpy.ravel(subimage)
		mask = numpy.ravel(mask)
		roi = numpy.compress(mask, im)
		mean = arraystats.mean(roi)
		std = arraystats.std(roi)
		n = len(roi)
		return {'mean':mean, 'std': std, 'n':n}

	def configure_holestats(self, radius=None):
		if radius is not None:
			self.holestats_config['radius'] = radius

	def calc_holestats(self, radius=None):
		'''
		This adds hole stats to holes.
		'''
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate hole stats')
		self.configure_holestats(radius=radius)
		im = self.__results['original']
		r = self.holestats_config['radius']
		holes = list(self.__results['holes'])
		for hole in holes:
			coord = hole.stats['center']
			holestats = self.get_hole_stats(im, coord, r)
			if holestats is None:
				self.__results['holes'].remove(hole)
				continue
			hole.stats['hole_stat_radius'] = r
			hole.stats['hole_n'] = holestats['n']
			hole.stats['hole_mean'] = holestats['mean']
			hole.stats['hole_std'] = holestats['std']

	def configure_ice(self, i0=None, tmin=None, tmax=None, tstdmax=None, tstdmin=None):
		if i0 is not None:
			self.ice_config['i0'] = i0
		if tmin is not None:
			self.ice_config['tmin'] = tmin
		if tmax is not None:
			self.ice_config['tmax'] = tmax
		if tstdmax is not None:
			self.ice_config['tstdmax'] = tstdmax
		if tstdmin is not None:
			self.ice_config['tstdmin'] = tstdmin

	def calc_ice(self, i0=None, tmin=None, tmax=None):
		'''
		Calculate relative ice stats of the hole.
		'''
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax)
		holes = self.__results['holes']
		holes2 = []
		i0 = self.ice_config['i0']
		tmin = self.ice_config['tmin']
		tmax = self.ice_config['tmax']
		tstdmax = self.ice_config['tstdmax']
		tstdmin = self.ice_config['tstdmin']
		self.icecalc.set_i0(i0)
		for hole in holes:
			if 'hole_mean' not in hole.stats:
				## no mean was calculated
				continue
			mean = hole.stats['hole_mean']
			std = hole.stats['hole_std']
			tm = self.icecalc.get_thickness(mean)
			hole.stats['thickness-mean'] = tm
			ts = self.icecalc.get_stdev_thickness(std, mean)
			hole.stats['thickness-stdev'] = ts
			if (tmin <= tm <= tmax) and (tstdmin <= ts < tstdmax):
				holes2.append(hole)
				hole.stats['good'] = True
			else:
				hole.stats['good'] = False
		self.__update_result('holes2', holes2)

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.run_extholes()
		self.extholes_to_holes()
		self.mark_holes()
		self.calc_holestats()
		#self.calc_ice()

if __name__ == '__main__':
	from pyami import mrc
	hf = HoleFinder()
	hf['original'] = mrc.read('holetemplate.mrc')
	hf.configure_extholes(diameter=29, spacing=100, command='')
	hf.find_holes()
