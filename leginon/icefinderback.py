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
		center = info_dict['center'][0],info_dict['center'][1]
		# stats will be displayed in target panel
		self.stats = {"center":center}
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
			'holes2': None, #good holes to use
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

	def _set_holestats(self, hole, holestats, radius=None):
		hole.stats['hole_stat_radius'] = radius
		hole.stats['hole_n'] = holestats['n']
		hole.stats['hole_mean'] = holestats['mean']
		hole.stats['hole_std'] = holestats['std']

	def calc_ice(self, i0=None, tmin=None, tmax=None):
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax)
		holes = self.__results['holes']
		holes, holes2 = self._calc_ice(holes)
		self.__update_result('holes2', holes2)

	def _calc_ice(self, holes):
		'''
		Return holes2 that contains only good holes with ice thickness thresholds
		in ice_config.
		'''
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
		return holes, holes2

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.run_holefinder()
		self.calc_holestats()
		self.calc_ice()

	def calc_holestats(self, radius=None):
		'''
		This adds hole stats to holes.  Note: Need to copy this in
		subclasses since self.__results are not accessible in the subclass.
		'''
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate hole stats')
		self.configure_holestats(radius=radius)
		im = self.__results['original']
		r = self.holestats_config['radius']
		holes = list(self.__results['holes'])
		for hole in holes:
			holestats = self._calc_one_holestats(hole, im)
			if holestats is None:
				self.__results['holes'].remove(hole)
				continue
			self._set_holestats(hole, holestats, r)

	def _calc_one_holestats(self, hole, im):
		r = self.holestats_config['radius']
		coord = hole.stats['center']
		holestats = self.circle.get_circle_stats(im, coord, r)
		return holestats

class TestIceFinder(IceFinder):
	def setDefault(self):
		super(TestIceFinder, self).setDefault()
		self.holefinder_config = {'number':10}

	def configure_holefinder(self, number=10):
		self.holefinder_config['number'] = number

	def run_holefinder(self):
		holes = []
		for n in range(self.holefinder_config['number']):
			h = {'center':[100*n,200*n]}
			holes.append(StatsHole(h, n)) # (row, col)
		self.updateHoles(holes)

if __name__ == '__main__':
	from pyami import mrc
	hf = TestIceFinder()
	mrc_path = '/Users/acheng/testdata/leginon/21aug27y/rawdata/21aug27y_i_00005gr_00023sq.mrc'
	hf['original'] = mrc.read(mrc_path)
	hf.configure_holefinder(number=2)
	hf.configure_holestats(radius=20)
	hf.configure_ice(i0=150, tmin=0, tmax=1, tstdmax=1, tstdmin=0)
	hf.find_holes()
	if hf['holes2']:
		print hf['holes2'][0].stats
