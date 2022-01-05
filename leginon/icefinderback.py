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
import random
from pyami import imagefun, mrc, arraystats, groupfun
import pyami.circle
import ice
import os
import statshole

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
	def __init__(self, is_testing=False):
		self.save_mrc = is_testing
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
			'original': ('holes','holes2'),
			'holes': ('holes2',),
			'holes2': (),
		}

	def setComponents(self):
		## other necessary components
		self.circle = pyami.circle.CircleMaskCreator()
		self.holestats = statshole.HoleStatsCalculator()
		self.ice = statshole.HoleIceCalculator()
		self.convolve = statshole.HoleConvolver()
		self.good = statshole.GoodHoleFilter()
		self.sample = statshole.HoleSampler()

	def setDefaults(self):
		## some default configuration parameters
		self.save_mrc = False
		self.im_shape = None
		self.holefinder_config = {}
		self.holestats.configure({'radius':20, 'im':None})
		self.ice.configure({'i0': 1, 'tmin': -5,'tmax':5, 'tstdmax':5, 'tstdmin':0})
		self.convolve.configure({'conv_vect':[],'im_shape': self.im_shape})
		self.sample.configure({'classes': 1, 'samples': 100,'category':'hole_number'})

	def _set_image(self, value):
		self.image = value
		if value is None:
			self.im_shape = None
		else:
			self.im_shape = value.shape

	def __getitem__(self, key):
		return self.__results[key]

	def __setitem__(self, key, value):
		## only some images are allowed to be set externally
		## (right now, only original)
		if key in ('original',):
			self.__update_result(key, value)
			self._set_image(value)

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

	def saveTestMrc(self, img, mrc_name):
		if self.save_mrc:
			print('saving %s' % mrc_name)
			mrc.write(img, mrc_name)

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
		im = self.image
		self.holestats.configure({'radius':radius, 'im':im})

	def configure_ice(self, i0=None, tmin=None, tmax=None, tstdmax=None, tstdmin=None):
		self.ice.configure({'i0': i0, 'tmin': tmin,'tmax':tmax, 'tstdmax':tstdmax, 'tstdmin':tstdmin})

	def configure_convolve(self, conv_vect=None):
		# conv_vect in r,c
		self.convolve.configure({'conv_vect':conv_vect,'im_shape': self.im_shape})

	def configure_sample(self, classes=None, samples=None, category=None):
		configs = {'classes': classes, 'samples': samples,'category':category}
		self.sample.configure(configs)

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
		holes, holes2 = self.ice.calc_ice(holes)
		self.__results['holes2']=holes2

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
		self.sampling(input_name='holes2')

	def calc_holestats(self, radius=None, input_name='holes'):
		'''
		This adds hole stats to holes.  Note: Need to copy this in
		subclasses since self.__results are not accessible in the subclass.
		'''
		if self.__results[input_name] is None:
			raise RuntimeError('need holes to calculate hole stats')
		self.configure_holestats(radius=radius)
		holes = list(self.__results[input_name])
		holes = self.holestats.calc_stats(holes)
		self.__update_result(input_name, holes)

	def filter_good(self, input_name='holes2'):
		'''
		This filter holes with good is True.  Note: Need to copy this in
		subclasses since self.__results are not accessible in the subclass.
		'''
		holes = list(self.__results[input_name])
		holes = self.good.filter_good(holes)
		self.__update_result('holes2', holes)

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

	def make_convolved(self, input_name='holes'):
		"""
		Make convolved results as holes2.
		Note: Subclass needs to duplicate this because __results must be in the same module.
		"""
		if self.__results[input_name] is None:
			raise RuntimeError('need %s to generate convolved targets' % input_name)
			return
		# convolve from these goodholes
		goodholes = list(self.__results[input_name])
		conv_vect = self.convolve.configs['conv_vect'] # list of (del_r,del_c)s
		# reset before start
		self.__update_result('holes2', [])
		if not conv_vect:
			return
		#real part
		convolved = self.convolve.make_convolved(goodholes)
		self.__update_result('holes2', convolved)

	def sampling(self, input_name='holes2'):
		"""
		Sample results of the input_name.
		Note: Subclass needs to duplicate this because __results must be in the same module.
		"""
		holes = self.__results[input_name]
		sampled = self.sample.sampleHoles(holes)
		self.__update_result(input_name, sampled)

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
			holes.append(statshole.StatsHole(h, n, h.keys())) # (row, col)
		self.updateHoles(holes)

if __name__ == '__main__':
	from pyami import mrc
	hf = TestIceFinder()
	mrc_path = '/Users/acheng/testdata/leginon/21aug27y/rawdata/21aug27y_i_00005gr_00023sq.mrc'
	hf['original'] = mrc.read(mrc_path)
	hf.configure_holefinder(count=10)
	hf.configure_holestats(radius=20)
	hf.configure_ice(i0=150, tmin=0, tmax=1, tstdmax=1, tstdmin=0)
	hf.configure_convolve(conv_vect=[(0,0),(20,0)])
	hf.configure_sample(classes=2, samples=4, category='center')
	hf.find_holes()
	print 'number of holes', len(hf['holes'])
	for h in hf['holes']:
		print h.stats
	if hf['holes2']:
		print ''
		print 'number of holes2 after processing', len(hf['holes2'])
		for h in hf['holes2']:
			print h.stats
