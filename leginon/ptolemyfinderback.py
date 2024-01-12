#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import subprocess
import json
import numpy
import math
from pyami import imagefun, mrc, arraystats
from leginon import ptolemyhandler as ph
import os

from leginon import scorefinderback, icefinderback, statshole, lattice

class ScoreResultMissingError(Exception):
	'''Raised when score result is missing.  This assumes ptolemy server fails.
	Requests from user to downgrade this because it is too often.
	'''
	pass

###################
### Because of the use of __result, the subclass don't get them as attribute. AC 2021
###################
class HoleFinder(scorefinderback.HoleFinder):
	'''
	Create an instance of HoleFinder:
		hf = HoleFinder()
	Give it an image to work with:
		hf['original'] = some_numeric_array
	Configure the processes:
		hf.configure_holefinder(dirname, max_radius)
	Do the processes step by step, or the whole thing:
		hf.find_holes()
	'''
	def __init__(self):
		## These are the results that are maintained by this
		## object for external use through the __getitem__ method.
		self.__results = {
			'original': None, # original image
			'holes': None,  # holes found by holefinder
			'holes2': None, # good holes to use after convolution, ice filtering etc.
			'holes3': None, #original unconvolved holes, to be later added to holes2
		}

		## This defines which dependent results should be cleared
		## when a particular result is updated.
		## Read this as:
		##  If you update key, clear everything in the dependent tuple
		self.__dependents = {
			'original': ('holes',),
			'holes': ('holes2',),
			'holes2': (),
			'holes3': (),
		}
		self.setComponents()
		self.setDefaults()
		self.square = None
		self.lattice_matrix = None

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()

	def setDefaults(self):
		## some default configuration parameters
		super(HoleFinder, self).setDefaults()
		self.save_mrc = False
		self.holefinder_config = {'imagedata':{}, 'score_key':'score','threshold':0}
		self.holestats_config = {'radius': 20}
		self.filter_config = {'tmin': -10, 'tmax': 20}
		self.convolve_config = {'conv_vect':None}

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

	def updateHoles(self, holes):
		self.__update_result('holes', holes)

	def update_result(self, key, image):
		self.__update_result(key, image)

	def get_result(self, key):
		return self.__results[key]

	def configure_holefinder(self, imagedata=None, score_key=None, threshold=None):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		if imagedata is not None:
			self.holefinder_config['imagedata']= imagedata
		else:
			raise RuntimeError('need imagedata to run hole finding')
		if score_key is not None:
			self.holefinder_config['score_key']= score_key
		else:
			# default score_key is probability in ptolemy med2high
			self.holefinder_config['score_key']='score'
		if threshold is not None:
			self.holefinder_config['threshold']=threshold
		else:
			# default threshold to 0
			self.holefinder_config['threshold']=0

	def run_holefinder(self):
		'''
		Return external hole finder holes found
		'''
		if self.get_result('original') is None:
			raise RuntimeError('need original image to run hole finding')
		jsondict = self._runPtolemyHoleFinder(dict(self.holefinder_config))
		self.loadHoles(jsondict)

	def _runPtolemyHoleFinder(self,config):
		imagedata = config['imagedata']
		jsondict = ph.push_and_evaluate_mm(imagedata)
		return jsondict

	def jsonCenterToHoleCenter(self, json_center):
		"""
		Conversion of center tuple in json file to StatsHole definition of (r,c)
		"""
		# return center in (row, col)
		return (json_center[1], json_center[0])

	def loadHoles(self, jsondict):
		'''
		load target locations and score as StatsHole
		'''
		hole_dicts = jsondict
		# set lattice matrix for centerCarbon
		self.setLatticeMatrix(hole_dicts)
		holes = []
		score_key = self.holefinder_config['score_key']
		for n, h in enumerate(hole_dicts):
			if score_key not in h.keys():
				raise ValueError('Score key "%s" not valid. Please change in Hole Settings' % score_key)
			# convert to r,c
			h['center'] = self.jsonCenterToHoleCenter(h['center'])
			h['convolved'] = False
			# apply score minimum threshold
			if self.holefinder_config['threshold'] is None or h[score_key] >= self.holefinder_config['threshold']:
				holes.append(statshole.StatsHole(h, n,[score_key,'convolved'])) # (row, col)
		self.updateHoles(holes)

	def setLatticeMatrix(self, hole_dicts):
		"""
		set lattice_matrix from unfiltered hole centers.
		"""
		# Ptolemy currently only do square lattice.
		# blob center here is in r,c
		b_centers = map((lambda x: self.jsonCenterToHoleCenter(x['center'])), hole_dicts)
		im_center = self.im_shape[0]//2, self.im_shape[1]//2
		b_centers = lattice.sortPointsByDistances(b_centers, center=im_center)
		b_centers = lattice.sortPointsByDistances(b_centers, center=b_centers[0])
		c0 = b_centers[0]
		v1 = b_centers[1][0]-c0[0], b_centers[1][1]-c0[1]
		# default is square lattice
		v2 = v1[1], -v1[0]
		m = numpy.array([[v1[0],v1[1]],[v2[0],v2[1]]])
		self.lattice_matrix = m

	def getOutPath(self):
		"""
		Return full output json file path determined by holefinder_config.
		"""
		job_basename = self.holefinder_config['job_name']
		outpath = os.path.join(self.holefinder_config['out_dir'],'%s.json' % job_basename)
		return outpath

	def swapxy(self, points):
		"""
		Swap (x,y) tuple to (y,x) on all items in the list.
		"""
		return [(point[1],point[0]) for point in points]

	def configure_ice(self, i0=None, tmin=None, tmax=None, tstdmax=None, tstdmin=None):
		if i0 is not None:
			ph.set_noice_hole_intensity(i0)
		super(HoleFinder, self).configure_ice(i0, tmin, tmax, tstdmax, tstdmin)

	def configure_filter(self, tmin=None, tmax=None):
		"""
		Set score filter min and max values if not None.
		"""
		if tmin is not None:
			self.filter_config['tmin'] = tmin
		if tmax is not None:
			self.filter_config['tmax'] = tmax

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.run_holefinder()
		# for focus anyhole filtering, good holes are in holes2 results
		#self.calc_holestats()
		#self.calc_ice()
		# template convolution. This will replace holes2 results
		self.make_convolved()
		self.calc_holestats(input_name='holes2')
		self.calc_ice(input_name='holes2')
		self.sampling(input_name='holes2')

if __name__ == '__main__':
	hf = HoleFinder()
	hl_id = 5897
	from leginon import leginondata
	imagedata = leginondata.AcquisitionImageData().direct_query(hl_id)
	score_key = 'score'
	hf['original'] = imagedata['image']
	hf.configure_holefinder(imagedata, score_key=score_key, threshold=0.0)
	hf.configure_filter(tmin=-1, tmax=10) # score filter
	hf.configure_ice(i0=180, tmin=0.0)
	hf.configure_convolve(conv_vect=[(20,0),])
	hf.configure_sample(classes=2, samples=4, category='thickness-mean')
	hf.find_holes()
	print('first holes of',len(hf['holes']),hf['holes'][0].stats)
	print('first holes2 of',len(hf['holes2']),hf['holes2'][0].stats)
