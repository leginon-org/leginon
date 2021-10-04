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

from leginon import icefinderback


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
###################
### But because of the use of __result, the subclass don't get them as attribute. AC 2021
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
		self.setComponents()
		self.setDefaults()

	def setComponents(self):
		## other necessary components
		super(HoleFinder, self).setComponents()

	def setDefaults(self):
		## some default configuration parameters
		super(HoleFinder, self).setDefaults()
		self.save_mrc = False
		self.holefinder_config = {'script': '','job_name':'hole','in_path':None,'out_dir':None, 'score_key':'probability','threshold':0}
		self.holestats_config = {'radius': 20}
		self.filter_config = {'tmin': -10, 'tmax': 20}
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
			self.holefinder_config['score_key']='probability'
		if threshold is not None:
			self.holefinder_config['threshold']=threshold
		else:
			# default threshold to 0
			self.holefinder_config['threshold']=0

	def run_holefinder(self):
		'''
		Threshold the correlation image.
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
			if self.holefinder_config['threshold'] is None or h[score_key] >= self.holefinder_config['threshold']:
				holes.append(StatsHole(h, n,[score_key])) # (row, col)
		self.updateHoles(holes)

	def getOutPath(self):
		job_basename = self.holefinder_config['job_name']
		outpath = os.path.join(self.holefinder_config['out_dir'],'%s.json' % job_basename)
		return outpath

	def swapxy(self, points):
		return [(point[1],point[0]) for point in points]

	def points_to_blobs(self, points):
			blobs = []
			for point in points:
				blob = imagefun.Blob(None, None, 1, point, 1.0, 1.0, 1.0, 1.0)
				blobs.append(blob)
			return blobs

	def configure_filter(self, tmin=None, tmax=None):
		if tmin is not None:
			self.filter_config['tmin'] = tmin
		if tmax is not None:
			self.filter_config['tmax'] = tmax

	def filter_score(self, tmin=None, tmax=None):
		'''
		Make holes2 that contains only good holes with score filter thresholds
		in filter_config.  This is not currently used in ScoreTargetFinder because
		we need ice thickness filter as hole2.
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
			holestats = self._calc_one_holestats(hole, im)
			if holestats is None:
				self.__results['holes'].remove(hole)
				continue
			self._set_holestats(hole, holestats, r)

	def calc_ice(self, i0=None, tmin=None, tmax=None, tstdmax=None, tstdmin=None):
		if self.__results['holes'] is None:
			raise RuntimeError('need holes to calculate ice')
		self.configure_ice(i0=i0,tmin=tmin,tmax=tmax, tstdmax=tstdmax, tstdmin=tstdmin)
		holes = self.__results['holes']
		holes, holes2 = self._calc_ice(holes)
		self.__update_result('holes2', holes2)
		#for h in holes:
		#	print h.stats

	def find_holes(self):
		'''
		For testing purpose. Configuration must be done already.
		'''
		self.run_holefinder()
		self.calc_holestats()
		self.calc_ice()
		#self.filter_score()


if __name__ == '__main__':
	from pyami import mrc
	hf = HoleFinder()
	mrc_path = '/Users/acheng/testdata/leginon/21aug27y/rawdata/21aug27y_i_00005gr_00023sq.mrc'
	score_key = 'probability'
	hf['original'] = mrc.read(mrc_path)
	hf.configure_holefinder('/Users/acheng/hl_finding.sh', 'test', mrc_path, out_dir='.', score_key=score_key)
	hf.configure_filter(tmin=-1, tmax=10)
	hf.configure_ice(i0=133, tmin=0.0)
	hf.find_holes()
	print hf['holes'][-1].stats
	#print 'holes scores',list(map((lambda x: x.stats[score_key]),hf['holes']))
	#print 'good holes scores',list(map((lambda x: x.stats[score_key]),hf['holes2']))
	hf.configure_ice(i0=130, tmin=0.05)
	hf.find_holes()
	print hf['holes'][-1].stats
