#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import numpy
import math
from pyami import imagefun, mrc, arraystats
import pyami.circle
import ice
import os

class StatsHole(object):
	def __init__(self, info_dict, index, statskeys={}):
		'''Simple blob object with image and stats as attribute
			center = (row, col) on image
		'''
		center = info_dict['center']
		# stats will be displayed in target panel
		self.stats = {"center":center,"hole_number":index+1} # (r,c)
		for key in statskeys:
			self.stats[key]=info_dict[key]
		self.info_dict = info_dict


### Note:  we should create a base class ImageProcess
### which defines the basic idea of a series of operations on 
### an image or a pipeline of operations.
### In subclasses such as HoleFinder, we would just have to define
### the steps and the dependencies.  The dependency checking and result
### management would be taken care of by the base class.

class IceFinder(object):
	'''
	Create an instance of HoleFinder:
		hf = HoleFinder()
	Give it an image to work with:
		hf['original'] = some_numeric_array
	Configure the processes:
		hf.configure_out_json(dirname, json_filename)
		hf.configure_score_choice(sc_min, sc_max)
	Do the processes step by step, or the whole thing:
		hf.find_holes()
	'''
	def __init__(self):
		self.setComponents()
		self.setDefaults()

		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None,
			'holes': None,
			'holes2': None, #good holes to use, including convolved
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('holes',),
			'holes': ('holes2',),
			'holes2': (),
		}

	def setComponents(self):
		## other necessary components
		self.circle = pyami.circle.CircleMaskCreator()
		self.icecalc = ice.IceCalculator()

	def setDefaults(self):
		## some default configuration parameters
		self.save_mrc = False
		self.holefinder_config = {}
		self.holestats_config = {'radius': 20}
		self.ice_config = {'i0': None, 'tmin': 0.0, 'tmax': 0.1, 'tstdmin': 0.05,'tstdmax':0.5}
		self.convolve_config = {'acq_vect':None}

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

	def configure_holefinder(self):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		self.holefinder_config = {}

	def run_holefinder(self):
		NotImplemented

	def updateHoles(self, holes):
		self.__update_result('holes', holes)

	def configure_holestats(self, radius=None):
		if radius is not None:
			self.holestats_config['radius'] = radius

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

	def configure_convolve(self, acq_vect=None):
		# r,c
		if acq_vect is not None:
			self.convolve_config['acq_vect'] = acq_vect

	def _set_holestats(self, hole, holestats, radius=None):
		hole.stats['hole_stat_radius'] = radius
		hole.stats['hole_n'] = holestats['n']
		hole.stats['hole_mean'] = holestats['mean']
		hole.stats['hole_std'] = holestats['std']

	def calc_ice(self, i0=None, tmin=None, tmax=None, input_name='holes'):
		'''
		Set result holes2 that contains only good holes from ice thickness thresholds
		in ice_config.
		'''
		if self.__results[input_name] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax)
		holes = self.__results[input_name]
		holes, holes2 = self._calc_ice(holes)
		self.__update_result('holes2', holes2)

	def _calc_ice(self, holes):
		'''
		Return holes2 that contains only good holes with ice thickness thresholds
		in ice_config.
		'''
		holes2 = []
		i0 = self.ice_config['i0']
		self.icecalc.set_i0(i0)
		for hole in holes:
			if 'hole_mean' not in hole.stats:
				## no mean was calculated
				continue
			hole = self._calc_one_ice(hole)
			if hole.stats['good'] == True:
				holes2.append(hole)
		return holes, holes2

	def _calc_one_ice(self, hole):
		'''
		Thresholding ice thickness on one hole
		'''
		tmin = self.ice_config['tmin']
		tmax = self.ice_config['tmax']
		tstdmax = self.ice_config['tstdmax']
		tstdmin = self.ice_config['tstdmin']
		mean = hole.stats['hole_mean']
		std = hole.stats['hole_std']
		tm = self.icecalc.get_thickness(mean)
		hole.stats['thickness-mean'] = tm
		ts = self.icecalc.get_stdev_thickness(std, mean)
		hole.stats['thickness-stdev'] = ts
		if (tmin <= tm <= tmax) and (tstdmin <= ts < tstdmax):
			hole.stats['good'] = True
		else:
			hole.stats['good'] = False
		return hole

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.run_holefinder()
		# for focus anyhole filtering
		self.calc_holestats()
		self.calc_ice()
		# template convolution
		self.make_convolved()
		self.calc_holestats(input_name='holes2')
		self.calc_ice(input_name='holes2')

	def calc_holestats(self, radius=None, input_name='holes'):
		'''
		This adds hole stats to holes.  Note: Need to copy this in
		subclasses since self.__results are not accessible in the subclass.
		'''
		if self.__results[input_name] is None:
			raise RuntimeError('need holes to calculate hole stats')
		self.configure_holestats(radius=radius)
		im = self.__results['original']
		r = self.holestats_config['radius']
		holes = list(self.__results[input_name])
		for hole in holes:
			center = hole.stats['center']
			holestats = self.calc_center_holestats(center, im, r)
			if holestats is None:
				self.__results[input_name].remove(hole)
				continue
			self._set_holestats(hole, holestats)

	def _calc_one_holestats(self, hole, im, r):
		coord = hole.stats['center']
		return self.calc_center_holestats(coord, im, r)

	def calc_center_holestats(self, coord, im, r):
		'''
		Returns stats centered at coord (r,c)
		'''
		holestats = self.circle.get_circle_stats(im, coord, r)
		return holestats

	def swapxy(self, points):
		"""
		Swap (x,y) tuple to (y,x) on all items in the list.
		"""
		return [(point[1],point[0]) for point in points]

	def points_to_blobs(self, points):
		'''
		Nor used.
		'''
		blobs = []
		#points are (x,y)
		for point in points:
			blob = imagefun.Blob(None, None, 1, point, 1.0, 1.0, 1.0, 1.0)
			blobs.append(blob)
		return blobs

	def make_convolved(self):
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to generate convolved targets')
			return
		# reset before start
		self.__update_result('holes2', [])
		acq_vect = self.convolve_config['acq_vect'] # list of (del_r,del_c)s
		goodholes = list(self.__results['holes'])
		if not acq_vect:
			return
		#real part
		r = self.holestats_config['radius']
		im = self.__results['original']
		convolved = self._make_convolved(goodholes, im, r, acq_vect)
		self.__update_result('holes2', convolved)

	def _make_convolved(self, holes, im, r, acq_vect):
		imshape = im.shape
		convolved = []
		for j, hole in enumerate(holes):
			for i, vect in enumerate(acq_vect):
				center = hole.stats['center'] #(r,c)
				target = center[0]+vect[0], center[1]+vect[1]
				tary = target[1]
				tarx = target[0]
				if tarx < 0 or tarx >= imshape[1] or tary < 0 or tary >= imshape[0]:
					continue
				h = hole.info_dict
				h.update(hole.stats)
				h['center'] = target #(r,c)
				h['convolved'] = True
				n = hole.stats['hole_number'] # (target number base 1)
				# convolved newhole has all old stats items
				newhole = StatsHole(h, n, h.keys())
				convolved.append(newhole)
		return convolved

class TestIceFinder(IceFinder):
	def setDefault(self):
		super(TestIceFinder, self).setDefault()
		self.holefinder_config = {'count':10}

	def configure_holefinder(self, count=10):
		self.holefinder_config['count'] = count

	def run_holefinder(self):
		holes = []
		for n in range(self.holefinder_config['count']):
			h = {'center':[100*n+100,200*n+100],'convolved':False}
			holes.append(StatsHole(h, n, h.keys())) # (row, col)
		self.updateHoles(holes)

if __name__ == '__main__':
	from pyami import mrc
	hf = TestIceFinder()
	mrc_path = '/Users/acheng/testdata/leginon/21aug27y/rawdata/21aug27y_i_00005gr_00023sq.mrc'
	hf['original'] = mrc.read(mrc_path)
	hf.configure_holefinder(count=2)
	hf.configure_holestats(radius=20)
	hf.configure_ice(i0=150, tmin=0, tmax=1, tstdmax=1, tstdmin=0)
	hf.configure_convolve(acq_vect=[(0,0),(20,0)])
	hf.find_holes()
	print 'number of holes', len(hf['holes'])
	for h in hf['holes']:
		print 'holes',h.stats
	print hf['holes'][0].stats
	if hf['holes2']:
		print len(hf['holes2'])
		for h in hf['holes2']:
			print 'holes after processing', h.stats
