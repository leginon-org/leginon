import subprocess
import json
import os
import multiprocessing
import time
import math
import numpy
import requests

from pyami import groupfun, convexhull
from leginon import leginondata
from leginon import mosaicexternalfinder
from leginon import targetfinder
from leginon import ptolemyhandler as ph
import gui.wx.MosaicScoreTargetFinder

class StatsBlob(object):
	def __init__(self, info_dict, index):
		'''Simple blob object with image and stats as attribute
			both input and output center/vertices = (row, col) on image
		'''
		mean = info_dict['brightness']
		stddev = 1.0
		size = info_dict['area']
		score = info_dict['score']
		center = info_dict['center'][0],info_dict['center'][1]
		vertices = info_dict['vertices']
		self.center_modified = False
		# n in blob is the same as size from Ptolemy. Need n for displaying stats
		# in gui.
		self.stats = {"label_index": index, "center":center, "n":size, "size":size, "mean":mean, "score":score}
		self.vertices = vertices
		self.info_dict = info_dict
		self.grid_id = info_dict['grid_id']
		# do something for merging ?
		self.image_id = info_dict['image_id']
		self.square_id = info_dict['square_id']

class MosaicActiveLearnTargetFinder(mosaicexternalfinder.MosaicScoreTargetFinder):
	"""
	External script score finder that operates on individual grid atlas tile.  Multithread
	process is added when each tile is added, and then loaded later. 
	"""
	panelclass = gui.wx.MosaicScoreTargetFinder.Panel
	settingsclass = leginondata.MosaicScoreTargetFinderSettingsData
	defaultsettings = dict(mosaicexternalfinder.MosaicScoreTargetFinder.defaultsettings)

	eventoutputs = mosaicexternalfinder.MosaicScoreTargetFinder.eventoutputs
	targetnames = mosaicexternalfinder.MosaicScoreTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicActiveLearnTargetFinder, self).__init__(id, session, managerlocation, **kwargs)
		self.tileblobmap = {}
		self.finder_blobs = []
		self.mblob_values = []
		self.start()
		self.p = {}
		self.script_exists = None
		ph.initialize()
		

	def hasValidScoringScript(self):
		self.baseurl = self.settings['scoring script']
		r = requests.get(ph.BASEURL)
		if not r.ok:
			if self.script_exists == False:
				#log error just once.
				return
			else:
				self.script_exists = False
				self.logger.error('url %s not accessible.' % scoring_script)
				return
		else:
			self.script_exists = True
		return self.script_exists

	def findSquareBlobs(self):
		"""
		Get blobs at finder scale with stats. In this case load the
		blobs found during _addTile
		"""
		if self.script_exists == False:
			self.logger.error('You must reload the atlas if you have changed the script path')
			return []
		if not self.hasValidScoringScript():
			self.logger.error('Failed square finding without scoring script')
			self.script_exists = None #reset
			return []
		imids = list(map((lambda x: int(x)),self.p.keys()))
		# gather subprocesses
		self.logger.info('Gathering finder results')
		for imid in imids:
			self.p[imid].join()
			self.p[imid].terminate()
			self.p.pop(imid)
		self.logger.info('All scripts finished')
		new_imids = set(imids).difference(self.tileblobmap.keys())
		self.loadBlobs()
		for imid in new_imids:
			label = '%d' % imid
			if label in self.ext_blobs:
				self.tileblobmap[imid] = self.ext_blobs[label]
			else:
				self.tileblobmap[imid] = []
			tile = self.tilemap[imid]
			self.addMosaicBlobValues(tile,imid)
		# merge finder blobs
		self.mergeFinderBlobs()
		return list(self.finder_blobs)

	def _runPtolemyBlobFinder(self, imagedata):
		ph.push_lm(imagedata)

		
	def loadBlobs(self):
		'''
		load target locations and score as StatsBlob
		'''
		self.ext_blobs = {}
		blob_dicts = []
		try:
			blob_dicts=ph.current_lm_state()
			if not blob_dicts:
				raise RuntimeError('get current_lm_state failed')
		except Exception as e:
			# probably access error
			self.logger.error("Square finder read error: %s" % e)
			for img_id in self.imagemap.keys():
				self.ext_blobs[img_id] = []
			return
		# blob_dicts is for all images
		def _revindex(value_tuple):
			return value_tuple[1],value_tuple[0]
		for n, b in enumerate(blob_dicts):
			#ptolemy write its coordinates in (x,y) modify them first.
			b['center'] = _revindex(b['center'])
			b['vertices'] = list(map((lambda x: _revindex(x)),b['vertices']))
			label = '%d' % b['image_id']
			if label not in self.ext_blobs.keys():
				self.ext_blobs[label] = []
			self.ext_blobs[label].append(StatsBlob(b,n)) # (row, col)

	def _addTile(self, imagedata):
		super(MosaicActiveLearnTargetFinder, self)._addTile(imagedata)
		if not self.hasValidScoringScript():
			return
		mrcpath = os.path.join(imagedata['session']['image path'], imagedata['filename']+'.mrc')
		imid = imagedata.dbid
		label = '%d' % imid
		self.logger.info('running external square finding on imgid=%d' % imid)
		job_basename = self.getJobBasename(label)
		self.p[imid] = multiprocessing.Process(target=self._runPtolemyBlobFinder, args=(imagedata,))
		self.p[imid].start()
