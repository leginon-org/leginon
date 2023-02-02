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
from leginon import statssquare
import gui.wx.MosaicScoreTargetFinder

def revindex(value_tuple):
	return value_tuple[1],value_tuple[0]

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
		self.server_exists = None

	def hasValidPtolemyService(self):
		r = requests.get(ph.BASEURL)
		if not r.ok:
			if self.server_exists == False:
				#log error just once.
				return
			else:
				self.server_exists = False
				self.logger.error('url %s not accessible.' % scoring_script)
				return
		else:
			self.server_exists = True
		return self.server_exists

	def findSquareBlobs(self):
		"""
		Get blobs at finder scale with stats. In this case load the
		blobs found during _addTile
		"""
		print "Running findSquareBlobs with Ptolemy server"
		if self.server_exists == False:
			return []
		if not self.hasValidPtolemyService():
			self.logger.error('Failed square finding without running Ptolemy server')
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
		# TODO: this sleep makes it less likely to fail in reloading atlas
		# but need better solution.
		time.sleep(6)
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

	def savePtolemySquare(self,infodict):
		q=leginondata.PtolemySquareData(session=self.session)
		q['tile_id']=infodict['image_id']
		q['grid_id']=infodict['grid_id']
		q['square_id']=infodict['square_id']
		q['center_x']=infodict['center'][1]
		q['center_y']=infodict['center'][0]
		q.insert()
		return q
		
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
		for n, b in enumerate(blob_dicts):
			#ptolemy write its coordinates in (x,y) modify them first. we want
			# them in (row, col)
			b['center'] = revindex(b['center'])
			b['vertices'] = list(map((lambda x: revindex(x)),b['vertices']))
			label = '%d' % b['image_id']
			b['tile_image'] = self._getTileImage(label)
			b['squares'] = [self.savePtolemySquare(b).dbid,]
			if label not in self.ext_blobs.keys():
				self.ext_blobs[label] = []
			self.ext_blobs[label].append(statssquare.StatsBlob(b,n)) # (row, col)

	def _addTile(self, imagedata):
		super(mosaicexternalfinder.MosaicScoreTargetFinder, self)._addTile(imagedata)
		if not self.hasValidScoringScript():
			return
		mrcpath = os.path.join(imagedata['session']['image path'], imagedata['filename']+'.mrc')
		imid = imagedata.dbid
		label = '%d' % imid
		self.logger.info('running external square finding on imgid=%d' % imid)
		job_basename = self.getJobBasename(label)
		self.p[imid] = multiprocessing.Process(target=self._runPtolemyBlobFinder, args=(imagedata,))
		self.p[imid].start()

	def researchSquareWithStats(self, row, col):
		'''
		Use row and col from mosaicimage to find SquareStatsData which contains
		merged ptolemy squares
		'''
		#TODO: maybe better do multiple square to ptolemy square mapping.
		# since we want to go from ptolemy square to squarestats.
		pref_q = leginondata.ScoreSquareFinderPrefsData(image=self.mosaicimagedata)
		q = leginondata.SquareStatsData(column=col, row=row,score_prefs=pref_q)
		results = q.query(results=1)
		if not results:
			return self.findNearestSquare(pref_q, row, col)
		return results[0]	

	def findNearestSquare(self, prefdata, row, col):
		stats = leginondata.SquareStatsData(score_prefs=prefdata).query()
		if not stats:
			self.logger.error('no squares found by Ptolemy')
			return None
		magnitudes = map((lambda x: (col-x['column'])**2+(row-x['row'])**2), stats)
		nearest = stats[magnitudes.index(min(magnitudes))]
		return nearest

	def mosaicToTarget(self, typename, row, col, **kwargs):
		'''
		Convert and publish the mosaic position to targetdata of the tile image.
		'''
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		# TODO add SquareStatsData that contains ptolemy merging list in targetdata
		square = self.researchSquareWithStats(row, col)
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist, square=square, **kwargs)
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata
