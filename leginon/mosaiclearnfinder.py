import subprocess
import json
import os
import multiprocessing
import time
import requests

from leginon import leginondata
from leginon import mosaicexternalfinder
from leginon import targetfinder
from leginon import ptolemyhandler as ph
from leginon import statssquare
from leginon import updatetargetorder
import gui.wx.MosaicLearnTargetFinder

def revindex(value_tuple):
	return value_tuple[1],value_tuple[0]

def dummy():
	'''
	dummy function for fake multiprocess.
	'''
	return

class MosaicLearnTargetFinder(mosaicexternalfinder.MosaicScoreTargetFinder):
	"""
	External script score finder that operates on individual grid atlas tile.  Multithread
	process is added when each tile is added, and then loaded later. 
	"""
	panelclass = gui.wx.MosaicLearnTargetFinder.Panel
	settingsclass = leginondata.MosaicLearnTargetFinderSettingsData
	# same as MosaicScoreTargetFinder except one
	defaultsettings = dict(mosaicexternalfinder.MosaicScoreTargetFinder.defaultsettings)
	defaultsettings.pop('scoring_script',None)

	eventoutputs = mosaicexternalfinder.MosaicScoreTargetFinder.eventoutputs
	targetnames = mosaicexternalfinder.MosaicScoreTargetFinder.targetnames

	def __init__(self, id, session, managerlocation, **kwargs):
		super(MosaicLearnTargetFinder, self).__init__(id, session, managerlocation, **kwargs)
		self.tileblobmap = {}
		self.finder_blobs = []
		self.mblob_values = []
		self.start()
		self.p = {}
		self.server_exists = None
		self.target_order_updater=updatetargetorder.SquareTargetOrderUpdater(self.session,self.logger)
		self.done_update_ptolemy_targets = False

	def hasValidPtolemyService(self):
		r = requests.get(ph.BASEURL)
		if not r.ok:
			if self.server_exists == False:
				#log error just once.
				return
			else:
				self.server_exists = False
				self.logger.error('url %s not accessible.' % ph.BASEURL)
				return
		else:
			self.server_exists = True
		return self.server_exists

	def hasValidScoringScript(self):
		return self.hasValidPtolemyService()

	def findSquareBlobs(self):
		"""
		Get blobs at finder scale with stats. In this case load the
		blobs found during _addTile
		"""
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
		self.logger.info('All finished')
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
				raise RuntimeError('get current_lm_state failed from ptolemy server error. Not recoverable.')
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
		if not self.hasValidPtolemyService():
			return
		mrcpath = os.path.join(imagedata['session']['image path'], imagedata['filename']+'.mrc')
		imid = imagedata.dbid
		label = '%d' % imid
		# if already has PtolemySquare, don't push
		r = leginondata.PtolemySquareData(session=self.session,tile_id=imid).query()
		if not r:
			self.logger.info('running ptolemy square finding on imgid=%d' % imid)
			self.p[imid] = multiprocessing.Process(target=self._runPtolemyBlobFinder, args=(imagedata,))
		else:
			self.logger.info('load current square finding score on imgid=%d' % imid)
			self.p[imid] = multiprocessing.Process(target=dummy)
		self.p[imid].start()

	def loadSquareBlobsAfterAllTiles(self):
		'''
		Load current square state as blobs.
		'''
		# This is called after createMosaicImage in loadMosaicTiles
		# self.tileblobmap is empty at this point.
		# populate self.tileblobmap from self.imagemap so that
		# it can be used to filter self.ext_blobs
		for imid in self.imagemap.keys():
			label = '%d' % imid
			self.tileblobmap[imid] = []
			tile = self.tilemap[imid]
			self.addMosaicBlobValues(tile,imid)
		self.finder_blobs = []
		self.mblob_values = []
		if self.mosaicimage is None:
			self.logger.error('Must have atlas display to find squares')
			return
		try:
			# get current_lm_state ptolemy blobs at finder scale with stats on this atlas
			blobs = self.getCurrentStateBlobs()
		except ValueError as e:
			self.logger.error(e)
			return
		# convert to targets and display
		targets = self.blobStatsTargets(blobs, self.finder_scale_factor)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')
		time.sleep(2)
		mosaic_image_shape = self.mosaicimage.shape
		self.refreshDatabaseDisplayedTargets()

	def researchSquareWithStats(self, row, col):
		'''
		Use row and col from mosaicimage to find SquareStatsData which contains
		merged ptolemy squares
		'''
		#TODO: maybe better do multiple square to ptolemy square mapping.
		# since we want to go from ptolemy square to squarestats.
		if not self.mosaicimagedata:
			raise ValueError('No mosaicimagedata')
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

	def confirmMosaicImage(self,imagedata):
		'''
		Make sure there is MosaicImageData based on input imagedata. It is required
		to properly find the square stats and ptolemy square to add to the target.
		'''
		# newly acquired mosaic that use auto finding would have self.mosaicimagedata
		if self.mosaicimagedata:
			return
		if not imagedata['list']:
			raise ValueError('Image not acquired to make mosaic')
		scale = self.settings['scale size']
		r = leginondata.MosaicImageData(session=self.session, list=imagedata['list']).query(results=1)
		if not r:
			# If the scale size setting is changed without saving image, there is no self.mosaicimagedata
			#self.publishMosaicImage()
			raise ValueError('You must Enable auto targeting to use this')
		else:
			self.logger.info('Loading existing mosaic image data')
			self.mosaicimagedata = r[0]

	def mosaicToTarget(self, typename, row, col, **kwargs):
		'''
		Convert and publish the mosaic position to targetdata of the tile image.
		'''
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		# must have self.mosaicimagedata to researchSquareWithStats
		self.confirmMosaicImage(imagedata)
		# add SquareStatsData that contains ptolemy merging list in targetdata
		square = self.researchSquareWithStats(row, col)
		if square is None:
			raise ValueError('No ptolemy results to be linked to the target')
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist, square=square, **kwargs)
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata

	def updatePtolemyTargets(self):
		"""
		Find all ptolemy targets, merge and filter out those on edge and already
		in database.  Submitting these targets means Ptolemy will be the one deciding
		on the target order, not leginon.  There is no sampling nor stats filtering.
		"""
		self.finder_blobs = []
		self.mblob_values = []
		if self.mosaicimage is None:
			self.logger.error('Must have atlas display to find squares')
			return
		try:
			# get blobs at finder scale with stats
			blobs = self.getCurrentStateBlobs()
		except ValueError as e:
			self.logger.error(e)
			return
		targets = self.blobStatsTargets(blobs, self.finder_scale_factor)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')
		##################################
		# TODO: This clear targets thread won't complete before
		# getPanelTargets is called below
		self.setTargets([], 'acquisition')
		###################################
		time.sleep(2)
		# get ranked and filtered acquisition
		mosaic_image_shape = self.mosaicimage.shape
		self.refreshDatabaseDisplayedTargets()
		xytargets = self.getPanelTargets(mosaic_image_shape)
		##################################
		# HACKING: disgard all acquisition targets because the
		# above threading problem
		xytargets['acquisition']=[]
		###################################
		#
		xys = self.runDatabaseBlobFilter(blobs, xytargets)
		message = 'found %s squares' % (len(xys),)
		self.last_xys = xys
		## display them
		# IMPORTANT: Don't put back unprocessed but submitted targets
		# because they will get duplicated.
		# It will also cause autoSubmitTargets break its while loop
		# to break too early
		self.setTargets(xys, 'acquisition')
		self.setTargets([], 'example')
		self.logger.info(message)
		self.done_update_ptolemy_targets = True

	def runDatabaseBlobFilter(self, finder_blobs, xytargets):
		'''
		Filter the blobs at finder image scale to get final targets.
		xytargets are dictionary of existing targets on the mosaic image.
		No example and thresholding. Edge targets are filtered out.
		'''
		if not finder_blobs:
			return []
		# These xy tuples are those in the database on self.mosaic scale.
		database_xys=self.existing_position_targets.keys()
		##############
		# blobs and filtering are done at smaller dimension to save memory usage.
		##############
		s = self.finder_scale_factor
		finder_database_points = map((lambda x: (x[1]//s,x[0]//s)),database_xys)
		priority_blobs, other_blobs, finder_display_array = self._runBlobRankFilter(finder_blobs, [], finder_database_points)
		# filter out blobs with edge only.  We want ptolemy to decide the rest of the workflow.
		other_blobs = self.filterOnEdge(other_blobs)
		combined_blobs = priority_blobs+other_blobs
		################
		# turn combined blobs into targets at the original mosaic dimension
		################
		targets = map((lambda x: self.blobToDisplayTarget(x,self.finder_scale_factor)), combined_blobs)
		# TODO: Should we keep this?
		# flat list of multihole convolution at the original mosaic dimension
		targets = self.multiHoleConvolution(targets)
		return targets

	def filterOnEdge(self, blobs):
		self.logger.info('Filtering out targets on atlas edges....')
		good_blobs = []
		for i, blob in enumerate(blobs):
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			try:
				on_edge = self.finder_edge_mosaicimage[row,column]
			except Exception as e:
				self.logger.debug('edge filtering error: %s' % e)
				on_edge = True
			if not on_edge:
				good_blobs.append(blob)
		return good_blobs

	def getCurrentStateBlobs(self):
		# like findSquareBlobs
		self.loadBlobs()
		for label in self.ext_blobs.keys():
			imid = int(label)
			if imid not in self.tileblobmap.keys():
				# from a different atlas
				self.ext_blobs.pop(label, None)
				continue
			self.tileblobmap[imid] = self.ext_blobs[label]
			tile = self.tilemap[imid]
			self.addMosaicBlobValues(tile,imid)
		# merge finder blobs
		self.mergeFinderBlobs()
		return list(self.finder_blobs)

	def updateSquareTargetOrder(self):
		if not self.targetlist:
			self.logger.error('targetlist unknown to update order on')
			return
		if not self.mosaicimagelist:
			self.logger.error('need mosaic image to update on')
			return
		lab = self.mosaicimagelist['targets']['label']
		if self.done_update_ptolemy_targets:
			self.logger.info('Reorder targets by pre-trained model score')
			initial_score=True
			# reset
			self.done_update_ptolemy_targets = False
		else:
			self.logger.info('Reorder targets by learning model score')
			initial_score=False
		self.target_order_updater.updateOrder(initial_score, mosaic_name=lab)
