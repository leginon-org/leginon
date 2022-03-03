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

from leginon import icefinderback, statshole

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

	def configure_holefinder(self, script=None, job_name='hole', in_path=None, out_dir=None, score_key=None, threshold=None):
		'''
		configuration for holefinder to run. Each non-None kwarg is added.
		'''
		if not in_path and self.__results['original']:
			self.temp_in_path = '%s.mrc' % job_name
			mrc.write(self.__results['original'], self.temp_in_path)
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
		if self.__results['original'] is None:
			raise RuntimeError('need original image to run hole finding')
		self.temp_in_path = None

		self._runExternalHoleFinder(dict(self.holefinder_config))
		self.loadHoles()
	
	def _runExternalHoleFinder(self,config):
		script = config['script']
		if not script:
			raise ValueError('%s invalid.' % script)
		job_basename = config['job_name']
		out_dir = config['out_dir']
		input_mrc_path = config['in_path']
		outpath = os.path.join(out_dir, '%s.json' % job_basename)
		if os.path.isfile(outpath):
			os.remove(outpath)
		# This process must create the output '%s.json' % job_basename at outpath
		cmd = 'source %s %s %s %s' % (script, job_basename, input_mrc_path, out_dir)
		proc = subprocess.Popen(cmd, shell=True)
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
			self.__update_result('holes', [])
			raise RuntimeError('hole finder did not run: %s missing' % outpath)
			return
		f = open(outpath,'r')
		# returns one line
		line = f.readlines()[0]
		hole_dicts = json.loads(line)
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

	def filter_score(self, tmin=None, tmax=None):
		'''
		Make holes2 that contains only good holes with score filter thresholds
		in filter_config.  This is not currently used in ScoreTargetFinder because
		we need ice thickness filter as hole2.
		Instead, holefinder_config['threshold'] is used as tmin score filter.
		'''
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to filter by score')
		score_key = self.holefinder_config['score_key']
		self.configure_filter(tmin=tmin,tmax=tmax)
		holes = self.__results['holes']
		holes2 = []
		tmin = self.filter_config['tmin']
		tmax = self.filter_config['tmax']
		for hole in holes:
			if score_key not in hole.stats:
				## no score
				continue
			score = hole.stats[score_key]
			if (tmin <= score <= tmax):
				holes2.append(hole)
				hole.stats['good'] = True
			else:
				hole.stats['good'] = False

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

	def calc_ice(self, i0=None, tmin=None, tmax=None, input_name='holes'):
		'''
		Set result holes2 that contains only good holes from ice thickness thresholds
		in ice_config.
		Duplicates what is in icefinderback because __results must be in the same module.
		'''
		if self.__results[input_name] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax)
		holes = self.__results[input_name]
		holes, holes2 = self.ice.calc_ice(holes)
		self.__update_result('holes2', holes)
		self.__update_result('holes2', holes2)

	def make_convolved(self, input_name='holes'):
		"""
		Sample results of the input_name.
		Duplicates what is in icefinderback because __results must be in the same module.
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
		Duplicates what is in icefinderback because __results must be in the same module.
		"""
		holes = self.__results[input_name]
		sampled = self.sample.sampleHoles(holes)
		self.__update_result(input_name, sampled)

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
