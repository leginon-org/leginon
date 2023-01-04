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
import pyami.circle
import os

from leginon import icefinderback, statshole, lattice

class ScoreResultMissingError(Exception):
	'''Raised when score result is missing.  This assumes script fails.
	Requests from user to downgrade this because it is too often.
	'''
	pass

###################
### Because of the use of __result, the subclass don't get them as attribute. AC 2021
###################
class HoleFinder(icefinderback.IceFinder):
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
		self.setComponents()
		self.setDefaults()
		self.lattice_matrix = None

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()

	def setDefaults(self):
		## some default configuration parameters
		super(HoleFinder, self).setDefaults()
		self.save_mrc = False
		self.holefinder_config = {'script': '','job_name':'hole','in_path':None,'out_dir':None, 'score_key':'score','threshold':0}
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

	def configure_holefinder(self, script=None, job_name='hole', in_path=None, out_dir=None, score_key=None, threshold=None):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		if not in_path and self.get_result('original'):
			self.temp_in_path = '%s.mrc' % job_name
			mrc.write(self.get_result('original'), self.temp_in_path)
			in_path = self.temp_in_path
		if not script or not in_path or not out_dir:
				raise ValueError('incomplete configuration')
		if not os.path.exists(in_path):
			raise ValueError('input %s does not exist' % in_path)
		self.holefinder_config['script']=script
		if job_name is not None:
			self.holefinder_config['job_name']=job_name
		else:
			# default job_name to 'hole'
			self.holefinder_config['job_name']='hole'
		if not os.path.exists(in_path):
			self.holefinder_config['in_path']=None
			raise ValueError('input %s does not exist' % in_path)
		else:
			self.holefinder_config['in_path']=in_path
			if os.path.isdir(out_dir):
				self.holefinder_config['out_dir']=out_dir
			else:
				raise ValueError('output dir %s does not exist' % out_dir)
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
		self.temp_in_path = None

		self._runExternalHoleFinder(dict(self.holefinder_config))
		self.loadHoles()
	
	def _runExternalHoleFinder(self,config):
		scoring_script = config['script']
		if not scoring_script:
			raise ValueError('%s invalid.' % scoring_script)
		shell_source = '/bin/bash'
		if scoring_script.endswith('csh'):
			shell_source = '/bin/csh'
		job_basename = config['job_name']
		out_dir = config['out_dir']
		input_mrc_path = config['in_path']
		outpath = os.path.join(out_dir, '%s.json' % job_basename)
		if os.path.isfile(outpath):
			os.remove(outpath)
		# This process must create the output '%s.json' % job_basename at outpath
		cmd = 'source %s %s %s %s' % (scoring_script, job_basename, input_mrc_path, out_dir)
		proc = subprocess.Popen(cmd, shell=True, executable=shell_source)
		proc.wait()

	def jsonCenterToHoleCenter(self, json_center):
		"""
		Conversion of center tuple in json file to StatsHole definition of (r,c)
		"""
		# return center in (row, col)
		return (json_center[1], json_center[0])

	def loadHoles(self):
		'''
		load target locations and score as StatsHole
		'''
		outpath = self.getOutPath()
		if not os.path.isfile(outpath):
			self.update_result('holes', [])
			raise ScoreResultMissingError('hole finder did not run: %s missing' % outpath)
			return
		f = open(outpath,'r')
		# returns one line
		line = f.readlines()[0]
		hole_dicts = json.loads(line)
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
	from pyami import mrc
	hf = HoleFinder()
	mrc_path = '/Users/acheng/testdata/leginon/21aug27y/rawdata/21aug27y_i_00005gr_00023sq.mrc'
	score_key = 'score'
	hf['original'] = mrc.read(mrc_path)
	hf.configure_holefinder('/Users/acheng/hl_finding.sh', 'test', mrc_path, out_dir='.', score_key=score_key, threshold=0.0)
	hf.configure_filter(tmin=-1, tmax=10) # score filter
	hf.configure_ice(i0=133, tmin=0.0)
	hf.configure_convolve(conv_vect=[(20,0),])
	hf.configure_sample(classes=2, samples=4, category='thickness-mean')
	hf.find_holes()
	print 'first holes of',len(hf['holes']),hf['holes'][0].stats
	print 'first holes2 of',len(hf['holes2']),hf['holes2'][0].stats
