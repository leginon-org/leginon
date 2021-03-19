#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

import calibrationclient
from leginon import leginondata
from leginon import project
import event
import instrument
import imagewatcher
import mosaic
import threading
import node
import targethandler
from pyami import convolver, imagefun, mrc, ordereddict, affine
import numpy
import pyami.quietscipy
import scipy.ndimage as nd
import gui.wx.MosaicClickTargetFinder

import os
import math
import polygon
import raster
import presets
import time
import targetfinder
import imagehandler

try:
	set = set
except NameError:
	import sets
	set = sets.Set



class MosaicClickTargetFinder(targetfinder.ClickTargetFinder, imagehandler.ImageHandler):
	panelclass = gui.wx.MosaicClickTargetFinder.Panel
	settingsclass = leginondata.MosaicClickTargetFinderSettingsData
	defaultsettings = dict(targetfinder.ClickTargetFinder.defaultsettings)
	defaultsettings.update({

		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'create on tile change': 'all',
		'lpf': {
			'on': True,
			'size': 5,
			'sigma': 1.4,
		},
		'threshold': 100.0,
		'blobs': {
			'on': True,
			'border': 0,
			'max': 100,
			'min size': 10,
			'max size': 10000,
			'min mean': 1000,
			'max mean': 20000,
			'min stdev': 10,
			'max stdev': 500,
		},
	})

	eventoutputs = targetfinder.ClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]
	targetnames = ['acquisition','focus','preview','reference','done','Blobs']
	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselections = {}
		targetfinder.ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self),
			'beam size':
												calibrationclient.BeamSizeCalibrationClient(self),
		}
		self.images = {
			'Original': None,
			'Extra Crispy': None,
			'Filtered': None,
			'Thresholded': None
		}
		parameter = self.settings['calibration parameter']
		self.mosaic = mosaic.EMMosaic(self.calclients[parameter])
		self.oldmosaic = mosaic.EMMosaic(self.calclients[parameter])
		self.mosaicimagelist = None
		self.oldmosaicimagelist = None
		self.mosaicimage = None
		self.mosaicname = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None
		self.convolver = convolver.Convolver()
		self.currentposition = []
		self.mosaiccreated = threading.Event()
		self.presetsclient = presets.PresetsClient(self)

		self.mosaic.setCalibrationClient(self.calclients[parameter])
		self.oldmosaic.setCalibrationClient(self.calclients[parameter])
		self.oldsession = self.session

		self.existing_targets = {}
		self.clearTiles()

		self.reference_target = None
		self.setRefreshTool(self.settings['check method']=='remote')

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	def insertDoneTargetList(self, targetlistdata):
		# this class targetlist must not be recorded done so that
		# more targets can be added to it
		self.logger.debug('%s did not insert done on %d' % (self.name,targetlistdata.dbid))
		pass

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.logger.warning('Got targetlistdone event')
		if self.settings['create on tile change'] == 'final':
			self.logger.debug('create final')
			self.createMosaicImage()
			self.logger.debug('done create final')
		if not self.hasNewImageVersion():
			self.targetsFromDatabase()
			# fresh atlas without acquisition targets (done or not) should run autofinder
			count = sum(map((lambda x: len(self.targetmap[x]['acquisition'])), self.targetmap.keys()))
			if count == 0:
				self.runAutoFinderRanker()
		# trigger activation of submit button in the gui.
		self.panel.doneTargetList()
		# TODO: auto submit targets if from auto run.
		self.notifyAutoDone('atlas')

	def runAutoFinderRanker(self):
		self.publishMosaicImage()
		# get blobs with stats
		blobs = self.findSquareBlobs()
		targets = self.blobStatsTargets(blobs)
		self.logger.info('Number of blobs: %s' % (len(targets),))
		self.setTargets(targets, 'Blobs')
		# get ranked and filtered acquisition
		xys = self.runBlobRankFilter(blobs)
		## display them
		self.setTargets(xys, 'acquisition')
		message = 'found %s squares' % (len(xys),)
		self.logger.info(message)

	def notifyAutoDone(self,task='atlas'):
			'''
			Notify Manager that the node has finished automated task so that automated
			task can move on.  Need this because it is a different thread.
			'''
			evt = event.AutoDoneNotificationEvent()
			evt['task'] = task
			self.outputEvent(evt)

	def getTargetDataList(self, typename):
		'''
		Get positions of the typename targets from atlas, publish the new ones,
		and then update self.existing_position_targets with the published one added.
		'''
		displayedtargetdata = {}
		try:
			target_positions_from_image = self.panel.getTargetPositions(typename)
		except ValueError:
			return
		for coord_tuple in target_positions_from_image:
			##  check if it is an existing position with database target.
			if coord_tuple in self.existing_position_targets and self.existing_position_targets[coord_tuple]:
				# pop so that it has a smaller dictionary to check
				targetdata = self.existing_position_targets[coord_tuple].pop()
			else:
				# This is a new position, publish it
				c,r = coord_tuple
				targetdata = self.mosaicToTarget(typename, r, c)
			if coord_tuple not in displayedtargetdata:
				displayedtargetdata[coord_tuple] = []
			displayedtargetdata[coord_tuple].append(targetdata)
		# update self.existing_position_targets,  This is still a bit strange.
		for coord_tuple in displayedtargetdata:
			self.existing_position_targets[coord_tuple] = displayedtargetdata[coord_tuple]

	def _getTargetDisplayInfo(self,image_pixelsize):
		vectors, beam_diameter_on_image = super(MosaicClickTargetFinder, self)._getTargetDisplayInfo(image_pixelsize)
		if self.mosaic and self.mosaic.scale:
			scale = self.mosaic.scale
		else:
			scale = 1
		scaled_vectors = {'x':(scale*vectors['x'][0],scale*vectors['x'][1]),'y':(scale*vectors['y'][0],scale*vectors['y'][1])}
		beam_diameter_on_image *= scale
		return scaled_vectors, beam_diameter_on_image

	def getDisplayedReferenceTarget(self):
		try:
			column, row = self.panel.getTargetPositions('reference')[-1]
		except (IndexError, ValueError) as e:
			return None
		imagedata, delta_row, delta_column = self._mosaicToTarget(row, column)
		return self.newReferenceTarget(imagedata, delta_row, delta_column)

	def submitTargets(self):
		self.terminated_remote = False
		self.userpause.set()
		try:
			if self.settings['autofinder']:
				# trigger onTargetsSubmitted in the gui.
				self.panel.targetsSubmitted()
				return
		except:
			pass

		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)

		if self.hasNewImageVersion():
			self.logger.error('New version of images were acquired after this atlas is generated')
			self.logger.error('You must refresh the map and repick the targets')
			# trigger onTargetsSubmitted in the gui.
			self.panel.targetsSubmitted()
			return

		# self.existing_position_targets becomes empty on the second
		# submit if not refreshed. 
		self.refreshDatabaseDisplayedTargets()
		if self.remote and self.settings['check method'] == 'remote':
			if not self.remote_targeting.userHasControl():
				self.logger.warning('remote user has not given control. Use local check')
			else:
				success = self.sendTargetsToRemote()
				if success:
					self.waitForTargetsFromRemote()
				if not success or self.terminated_remote:
					self.logger.warning('targets not submitted. Try again.')
					# don't finish submit, so that it can be redone
					self.panel.targetsSubmitted()
					return
		self.finishSubmitTarget()

	def finishSubmitTarget(self):
		# create target list
		self.logger.info('Submitting targets...')
		self.getTargetDataList('acquisition')
		self.getTargetDataList('focus')
		self.getTargetDataList('preview')
		try:
			self.publish(self.targetlist, pubevent=True)
		except node.PublishError, e:
			self.logger.error('Submitting acquisition targets failed')
		else:
			self.logger.info('Acquisition targets submitted on %s' % self.getMosaicLabel())

		reference_target = self.getDisplayedReferenceTarget()
		if reference_target is not None:
			try:
				self.publish(reference_target, database=True, pubevent=True)
			except node.PublishError, e:
				self.logger.error('Submitting reference target failed')
			else:
				self.logger.info('Reference target submitted on %s' % self.getMosaicLabel())
		self.logger.info('Done target submission')
		# trigger onTargetsSubmitted in the gui.
		self.panel.targetsSubmitted()

	def clearTiles(self):
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		self.targetlist = None
		if self.settings['create on tile change'] in ('all', 'final'):
			self.clearMosaicImage()

	def addTile(self, imagedata):
		self.logger.debug('addTile image: %s' % (imagedata.dbid,))
		imid = imagedata.dbid
		if imid in self.tilemap:
			self.logger.info('Image already in mosaic')
			return

		self.logger.info('Adding image to mosaic')
		newtile = self.mosaic.addTile(imagedata)
		self.tilemap[imid] = newtile
		self.imagemap[imid] = imagedata
		self.targetlist, onetargetmap = self._makeTargetMap(imagedata, self.targetlist)
		self.targetmap[imid] = onetargetmap
		self.logger.info('Image added to mosaic')
		if self.targetlist:
			self.logger.debug('add tile targetlist %d' % (self.targetlist.dbid,))
			self.logger.debug( 'add tile, imid %d %s' % (imid, imagedata['filename']))
			self.logger.debug( 'add targetmap %d'% (len(self.targetmap[imid]['acquisition']),))

	def _makeTargetMap(self, imagedata, targetlist=None):
		'''
		Make targetmap on the input targetlist
		'''
		onetargetmap = {}
		for type in ('acquisition','focus'):
			targets = self.researchTargets(image=imagedata, type=type)
			if targets and targetlist is None:
				# targetlist that of the first target of the first imagedata.
				targetlist = targets[0]['list']
			onetargetmap[type] = targets
		return targetlist, onetargetmap

	def hasNewImageVersion(self):
		for id, imagedata in self.imagemap.items():
			recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
			if recent_imagedata.dbid != imagedata.dbid:
				return True
		return False

	def targetsFromDatabase(self):
		'''
		This function sets the most recent version of the targets in targetmap and reference target.
		'''
		for id, imagedata in self.imagemap.items():
			recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
			self.targetmap[id] = {}
			for type in ('acquisition','focus'):
				targets = self.researchTargets(image=recent_imagedata, type=type)
				### set my target list to same as first target found
				if targets and self.targetlist is None:
					self.targetlist = targets[0]['list']
				self.targetmap[id][type] = targets
		self.reference_target = self.getReferenceTarget()

	def refreshRemoteTargets(self):
		if self.remote and self.settings['check method'] == 'remote':
			self.displayDatabaseTargets()
			# Send targets to remote and wait for submission
			# self.existing_position_targets becomes empty on the second
			# submit if not refreshed. 
			self.refreshDatabaseDisplayedTargets()
			success = self.sendTargetsToRemote()
			if success:
				self.waitForTargetsFromRemote()
				self.finishSubmitTarget()


	def refreshCurrentPosition(self):
		self.updateCurrentPosition()
		self.setTargets(self.currentposition, 'position')

	def updateCurrentPosition(self):
		'''
		update current stage position on the mosaic.
		Does not work if calibration parameter is image shift
		'''
		try:
			image = self.imagemap.values()[0]
		except:
			self.logger.exception('Need tiles and mosaic image')
			return
		# should get tem from data
		try:
			stagepos = self.instrument.tem.StagePosition
		except:
			stagepos = None

		if stagepos is None:
			self.currentposition = []
			self.logger.exception('could not get current position')
			return
		self.setCalibrationParameter()

		## self.mosaic knows the center, and need stagepos to integrate
		## modeled stage position (row,col)
		delta = self.mosaic.positionByCalibration(stagepos)
		## this is unscaled and relative to center of mosaic image
		moshape = self.mosaic.mosaicshape
		pos = moshape[0]/2+delta[0], moshape[1]/2+delta[1]
		pos = self.mosaic.scaled(pos)
		vcoord = pos[1],pos[0]
		### this is a list of targets, in this case, one target
		self.currentposition = [vcoord]

	def refreshDatabaseDisplayedTargets(self):
		self.logger.info('Getting targets from database...')
		if not self.hasNewImageVersion():
			self.targetsFromDatabase()
		else:
			self.logger.error('Can not refresh with new image version')
		# refresh but not set display.  Thefefore does not care about the returned values
		self.createExistingPositionTargets()

	def createExistingPositionTargets(self):
		# start fresh
		self.existing_position_targets, targets, donetargets = self._createExistingPositionTargets(self.targetmap, self.tilemap, self.mosaic)
		return targets, donetargets

	def _createExistingPositionTargets(self,targetmap, tilemap, mosaic_instance):
		existing_position_targets = {}
		targets = {}
		donetargets = []
		donedict = {}
		for ttype in ('acquisition','focus'):
			targets[ttype] = []
			for id, targetlists in targetmap.items():
				if ttype not in targetlists.keys():
					targetlist = []
				else:
					targetlist = targetlists[ttype]
				for targetdata in targetlist:
					tile = tilemap[id]
					#tilepos = self.mosaic.getTilePosition(tile)
					r,c = self._targetToMosaic(tile, targetdata, mosaic_instance)
					vcoord = c,r
					if vcoord not in existing_position_targets:
						# a position without saved target as default.
						existing_position_targets[vcoord] = []
					if targetdata['status'] in ('done', 'aborted'):
						existing_position_targets[vcoord].append(targetdata)
						donedict[targetdata['number']]=vcoord
					elif targetdata['status'] in ('new','processing'):
						existing_position_targets[vcoord].append(targetdata)
						targets[ttype].append(vcoord)
					else:
						# other status ignored (mainly NULL)
						pass
		# sort donetargets by target number
		donekeys = donedict.keys()
		donekeys.sort()
		for k in donekeys:
			donetargets.append(donedict[k])
		return existing_position_targets, targets, donetargets

	def displayDatabaseTargets(self):

		self.logger.info('Getting targets from database...')
		if not self.hasNewImageVersion():
			self.targetsFromDatabase()
		else:
			self.loadMosaicTiles(self.getMosaicName())
		self.displayTargets()

	def displayTargets(self):
		if self.mosaicimage is None:
			self.logger.error('Create mosaic image before displaying targets')
			return
		self.logger.info('Displaying targets...')
		donetargets = []
		if self.__class__ != MosaicClickTargetFinder:
			self.setTargets([], 'region')

		#
		targets, donetargets = self.createExistingPositionTargets()
		for ttype in targets.keys():
			self.setTargets(targets[ttype], ttype)
		self.setTargets(donetargets, 'done')

		# ...
		reference_target = []
		if self.reference_target is not None:
			id = self.reference_target['image'].dbid
			try:
				tile = self.tilemap[id]
				y, x = self.targetToMosaic(tile, self.reference_target)
				reference_target = [(x, y)]
			except KeyError:
				pass
		self.setTargets(reference_target, 'reference')

		self.updateCurrentPosition()
		self.setTargets(self.currentposition, 'position')
		self.setTargets([], 'preview')
		n = 0
		for type in ('acquisition','focus'):
			n += len(targets[type])
		ndone = len(donetargets)
		self.logger.info('displayed %s targets (%s done)' % (n+ndone, ndone))
		# trigger activation of submit button in the gui. Won't get here
		# without mosaic.
		self.panel.doneTargetDisplay()

	def getMosaicImageList(self, targetlist):
		self.logger.debug('in getMosaicImageList')
		'''
		if not targetlist['mosaic']:
			self.logger.debug('target list not mosaic')
			raise RuntimeError('TargetListData for mosaic ImageListData should have mosaic=True')
		'''
		if self.mosaicimagelist and self.mosaicimagelist['targets'] is targetlist:
			### same targetlist we got before
			self.logger.debug('same targets')
			self.setMosaicName(targetlist)
			return self.mosaicimagelist
		self.logger.debug('new image list data')

		### clear mosaic here
		self.clearTiles()

		self.mosaicimagelist = leginondata.ImageListData(session=self.session, targets=targetlist)
		self.logger.debug('publishing new mosaic image list')
		self.publish(self.mosaicimagelist, database=True, dbforce=True)
		self.logger.debug('published new mosaic image list')
		self.setMosaicName(targetlist)
		return self.mosaicimagelist

	def processImageData(self, imagedata):
		'''
		different from ClickTargetFinder because findTargets is
		not per image, instead we have submitTargets.
		Each new image becomes a tile in a mosaic.
		'''
		self.logger.info('Processing inbound image data')
		### create a new imagelist if not already done
		targets = imagedata['target']['list']
		if not targets:
			self.logger.info('No targets to process')
			return
		imagelist = self.getMosaicImageList(targets)
		self.logger.debug('creating MosaicTileData for image %d' % (imagedata.dbid,))
		tiledata = leginondata.MosaicTileData(image=imagedata, list=imagelist, session=self.session)
		self.logger.debug('publishing MosaicTileData')
		self.publish(tiledata, database=True)
		self.setMosaicNameFromImageList(imagelist)
		self.logger.debug('published MosaicTileData')
		self.currentimagedata = imagedata
		self.addTile(imagedata)

		if self.settings['create on tile change'] == 'all':
			self.logger.debug('create all')
			self.createMosaicImage()
			self.logger.debug('done create all')

		self.logger.debug('Image data processed')

	def hasMosaicImage(self):
		
		if self.mosaicimage is None or  self.mosaicimagescale is None:
			return False
		return True

	def publishMosaicImage(self):
		if not self.hasMosaicImage():
			self.logger.info('Generate a mosaic image before saving it')
			return
		self.logger.info('Saving mosaic image data')
		mosaicimagedata = leginondata.MosaicImageData()
		mosaicimagedata['session'] = self.session
		mosaicimagedata['list'] = self.mosaicimagelist
		mosaicimagedata['image'] = self.mosaicimage
		mosaicimagedata['scale'] = self.mosaicimagescale
		filename = '%s_mosaic' % self.session['name'] # include name for remote to clear on session
		lab = self.mosaicimagelist['targets']['label']
		if lab:
			filename = filename + '_' + lab
		dim = self.mosaicimagescale
		filename = filename + '_' + str(dim)
		mosaicimagedata['filename'] = filename
		self.publish(mosaicimagedata, database=True)
		self.mosaicimagedata = mosaicimagedata
		self.logger.info('Mosaic saved')

	def _researchMosaicTileData(self,imagelist=None, session=None):
		if session is None:
			session = self.session
		tilequery = leginondata.MosaicTileData(session=session, list=imagelist)
		mosaictiles = self.research(datainstance=tilequery)
		return mosaictiles

	def researchMosaicTileData(self,imagelist=None):
		tiles = self._researchMosaicTileData(imagelist)
		self.mosaicselections =  self.makeMosaicSelectionsFromTiles(tiles)

	def makeMosaicSelectionsFromTiles(self, tiles):
		mosaiclist = ordereddict.OrderedDict()
		for tile in tiles:
			imglist = tile['list']
			key = self.makeMosaicNameFromImageList(imglist)
			if key not in mosaiclist:
				mosaiclist[key] = imglist
		return mosaiclist

	def getMosaicNames(self):
		self.researchMosaicTileData()
		return self.mosaicselections.keys()

	def setMosaicName(self, mosaicname):
		self.mosaicname = mosaicname

	def setMosaicNameFromImageList(self,list):
		key = self.makeMosaicNameFromImageList(list)
		self.setMosaicName(key)

	def makeMosaicNameFromImageList(self,imglist):
		label = '(no label)'
		if imglist['targets'] is not None:
			if imglist['targets']['label']:
				label = imglist['targets']['label']
			elif imglist['targets']['image'] and imglist['targets']['image']['preset'] and imglist['targets']['image']['target']:
				label = '%d%s' % (imglist['targets']['image']['target']['number'],imglist['targets']['image']['preset']['name'])
		key = '%s:  %s' % (imglist.dbid, label)
		return key

	def getMosaicLabel(self):
		bits = self.getMosaicName().split(':')
		label = ':'.join(bits[1:]).strip()
		return label

	def getMosaicName(self):
		'''
		return a name that has both image list dbid and label in this format: dbid: label
		'''
		return self.mosaicname

	def getMosaicTiles(self, mosaicname):
		return tiles

	def loadMosaicTiles(self, mosaicname):
		self.logger.info('Clearing mosaic')
		self.clearTiles()
		self.logger.info('Loading mosaic images')
		try:
			tile_imagelist = self.mosaicselections[mosaicname]
		except KeyError:
			# new inbound mosaic is not in selectionmapping. Refresh the list and try again
			self.researchMosaicTileData()
			if mosaicname not in self.mosaicselections.keys():
				raise ValueError
			else:
				tile_imagelist = self.mosaicselections[mosaicname]
		self.mosaicimagelist = tile_imagelist
		mosaicsession = self.mosaicimagelist['session']
		tiles = self._researchMosaicTileData(tile_imagelist)
		ntotal = len(tiles)
		if not ntotal:
			self.logger.info('no tiles in selected list')
			return
		for i, tile in enumerate(tiles):
			# create an instance model to query
			self.logger.info('Finding image %i of %i' % (i + 1, ntotal))
			imagedata = tile['image']
			recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
			self.addTile(recent_imagedata)
			self.currentimagedata = recent_imagedata
		self.reference_target = self.getReferenceTarget()
		self.logger.info('Mosaic loaded (%i of %i images loaded successfully)' % (i+1, ntotal))
		if self.settings['create on tile change'] in ('all', 'final'):
			self.createMosaicImage()
		# hacking
		self.handleTargetListDone(None)

	def targetToMosaic(self, tile, targetdata):
		scalepos = self._targetToMosaic(tile, targetdata, self.mosaic)
		return scalepos

	def _targetToMosaic(self, tile, targetdata, mosaic_instance):
		shape = tile.image.shape
		drow = targetdata['delta row']
		dcol = targetdata['delta column']
		tilepos = drow+shape[0]/2, dcol+shape[1]/2
		mospos = mosaic_instance.tile2mosaic(tile, tilepos)
		scaledpos = mosaic_instance.scaled(mospos)
		return scaledpos

	def scaleToMosaic(self, d):
		shape = tile.image.shape
		drow = targetdata['delta row']
		dcol = targetdata['delta column']
		tilepos = drow+shape[0]/2, dcol+shape[1]/2
		mospos = self.mosaic.tile2mosaic(tile, tilepos)
		scaledpos = self.mosaic.scaled(mospos)
		return scaledpos

	def _mosaicToTarget(self, row, col):
		'''
		Convert mosaic position to target position on a tile image.
		'''
		return self._mosaicToTargetOnMosaic(row, col, self.mosaic)

	def _mosaicToTargetOnMosaic(self, row, col, mosaic_instance):
		self.logger.debug('mosaicToTarget r %s, c %s' % (row, col))
		unscaled = mosaic_instance.unscaled((row,col))
		tile, pos = mosaic_instance.mosaic2tile(unscaled)
		shape = tile.image.shape
		drow,dcol = pos[0]-shape[0]/2.0, pos[1]-shape[1]/2.0
		imagedata = tile.imagedata
		self.logger.debug('target tile image: %s, pos: %s' % (imagedata.dbid,pos))
		return imagedata, drow, dcol

	def mosaicToTarget(self, typename, row, col, **kwargs):
		'''
		Convert and publish the mosaic position to targetdata of the tile image.
		'''
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		### create a new target list if we don't have one already
		'''
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)
		'''
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist, **kwargs)
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata

	def createMosaicImage(self):
		self.logger.info('creating mosaic image')

		self.setCalibrationParameter()

		if self.settings['scale image']:
			maxdim = self.settings['scale size']
		else:
			maxdim = None
		self.mosaicimagescale = maxdim
		try:
			self.mosaicimage = self.mosaic.getMosaicImage(maxdim)
		except Exception, e:
			self.logger.error('Failed Creating mosaic image: %s' % e)
		self.mosaicimagedata = None

		self.logger.info('Displaying mosaic image')
		self.setImage(self.mosaicimage, 'Image')
		self.logger.info('image displayed, displaying targets...')
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		self.beep()

	def clearMosaicImage(self):
		self.setImage(None, 'Image')
		self.mosaicimage = None
		self.mosaicimagescale = None
		#clear remote mosaic image
		if self.remote_targeting and self.mosaicimagedata:
			self.remote_targeting.unsetImage(self.mosaicimagedata)
		self.mosaicimagedata = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def setCalibrationParameter(self):
		calclient = self.calclients[self.settings['calibration parameter']]
		self.mosaic.setCalibrationClient(calclient)

	#=============Target Transfer Aligner==============
	def researchAlignerOldMosaicTileData(self):
		'''
		Make a dictionary of old mosaic tiles for each image list
		'''
		# TO DO: gui and mechanism for selecting from an older session.
		if self.oldsession.dbid == self.session.dbid:
			self.oldmosaicselections = self.mosaicselections
		else:
			all_oldtiles = self._researchMosaicTileData(None, self.oldsession)
			self.oldmosaicselections = self.makeMosaicSelectionsFromTiles(all_oldtiles)

	def getAlignerOldMosaicNames(self):
		'''
		Get names of old mosaic for gui.
		'''
		self.researchAlignerOldMosaicTileData()
		return self.oldmosaicselections.keys()

	def setAlignerOldMosaic(self, mosaicname):
		'''
		Set old mosaic which has done targets to be transferred.
		'''
		self.oldtargetlist = None
		self.oldtargetmap = {}
		self.oldtilemap = {}
		self.oldmosaic.clear()
		self.Affine_matrix = None
		tile_imagelist = self.oldmosaicselections[mosaicname]
		self.oldmosaicimagelist = tile_imagelist
		# specify session based on tile_imagelist
		tiles = self._researchMosaicTileData(tile_imagelist, tile_imagelist['session'])
		for i, tile in enumerate(tiles):
			imagedata = tile['image']
			added_tile = self.oldmosaic.addTile(imagedata)
			imid = imagedata.dbid
			self.oldtilemap[imid] = added_tile
			self.oldtargetlist, onetargetmap = self._makeTargetMap(imagedata, self.oldtargetlist)
			self.oldtargetmap[imid] = onetargetmap

	def getAlignerOldMosaicImage(self):
		calclient = self.calclients[self.settings['calibration parameter']]
		self.oldmosaic.setCalibrationClient(calclient)
		maxdim = self.mosaicimagescale
		mosaicimage = self.oldmosaic.getMosaicImage(maxdim)
		return mosaicimage

	def getAlignerNewMosaicImage(self):
		mosaicimage = self.mosaicimage
		return mosaicimage

	def getAlignerOldTargets(self):		
		existing_old_targets, targets, donetargets = self._createExistingPositionTargets(self.oldtargetmap, self.oldtilemap, self.oldmosaic)
		# only transfer done targets for now.
		return donetargets

	def calculateTransform(self, targets1, targets2):
		'''
		Calculate Affine transformation matrix from list of matching points.
		'''
		points1 = map((lambda t: (t.x,t.y)),targets1)
		points2 = map((lambda t: (t.x,t.y)),targets2)
		if len(points1) < 3:
			A = numpy.matrix([(1,0,0),(0,1,0),(0,0,1)])
			residule = 0.0
		else:
			A, residule = affine.solveAffineMatrixFromImageTargets(points1,points2)
		self.Affine_matrix = A
		return A, residule

	def transformTargets(self, affine_matrix, targets1):
		'''
		Transform targets with affine matrix
		'''
		if not targets1:
			return []
		points1 = map((lambda t: (t.x,t.y)),targets1)
		points2 = affine.transformImageTargets(affine_matrix, points1)
		return points2

	def saveAlignerNewTargets(self, targets):
		'''
		Save transferred targets on the new mosaic.
		'''
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)

		for t in targets:
			col = t.x
			row = t.y
			# by using the returned new target, it makes sure the transaction is completed.
			newtarget = self.mosaicToTarget('acquisition', row, col, status='new')
			self.mosaicToTarget('acquisition', row, col, number=newtarget['number'],status='done')

	def saveTransform(self):
		q = leginondata.MosaicTransformMatrixData(session=self.session)
		q['imagelist1'] = self.oldmosaicimagelist
		q['imagelist2'] = self.mosaicimagelist
		q['move type'] = self.settings['calibration parameter']
		q['matrix'] = self.Affine_matrix
		q.insert()

	def showScaleRotationFromTransform(self):
		'''
		Show in logger the scale and rotation obtained.
		TODO: take into account mosaic formation and get scale.
		'''
		m = self.Affine_matrix
		rotation_radians = math.atan2(m[(0,1)],m[(0,0)])
		self.logger.info('Affine transform rotation to apply on old atlas is %.1f degrees' % (math.degrees(rotation_radians)))

	def acceptResults(self, targets):
		self.saveAlignerNewTargets(targets)
		self.saveTransform()
		self.displayDatabaseTargets()
		self.showScaleRotationFromTransform()

	def getAlignerNewSessionKey(self):
		'''
		Return this session key as a fake entry for gui so it aligns with
		the old one.
		'''
		s = self.session
		k = '%6d: %s' % (s.dbid, s['name'])
		return k

	def getAlignerOldSessionKeys(self):
		'''
		Returns all session keys in the project for selection and the current session
		'''
		p = project.ProjectData()
		self.projectid = p.getProjectId(self.session)
		self.projectsessions = p.getSessionsFromProjectId(self.projectid)
		self.oldsession_selections = {}
		for s in self.projectsessions:
			k = '%6d: %s' % (s.dbid, s['name'])
			self.oldsession_selections[k] = s
		selection_keys = list(self.oldsession_selections)
		selection_keys.sort()
		selection_keys.reverse()
		return selection_keys, '%6d: %s' % (self.session.dbid, self.session['name'])

	def onSelectOldSession(self, session_key):
		'''
		Called from gui when a session key is selected.
		'''
		self.oldsession = self.oldsession_selections[session_key]
		return self.getAlignerOldMosaicNames()

	#=============Target Finding==============
	def storeSquareFinderPrefs(self):
		prefs = leginondata.SquareFinderPrefsData()
		prefs['image'] = self.mosaicimagedata
		prefs['lpf-sigma'] = self.settings['lpf']['sigma']
		prefs['threshold'] = self.settings['threshold']
		prefs['border'] = self.settings['blobs']['border']
		prefs['maxblobs'] = self.settings['blobs']['max']
		prefs['minblobsize'] = self.settings['blobs']['min size']
		prefs['maxblobsize'] = self.settings['blobs']['max size']
		prefs['mean-min'] = self.settings['blobs']['min mean']
		prefs['mean-max'] = self.settings['blobs']['max mean']
		prefs['std-min'] = self.settings['blobs']['min stdev']
		prefs['std-max'] = self.settings['blobs']['max stdev']
		self.publish(prefs, database=True)
		return prefs

	def getExampleTargets(self):
		mosaic_image_shape = self.mosaicimage.shape
		xytargets = self.getPanelTargets(mosaic_image_shape)
		return xytargets['preview']

	def findSquareBlobs(self):
		message = 'finding squares'
		self.logger.info(message)

		sigma = self.settings['lpf']['sigma']
		kernel = convolver.gaussian_kernel(sigma)
		self.convolver.setKernel(kernel)
		image = self.convolver.convolve(image=self.mosaicimage)
		self.setImage(image, 'Filtered')

		example_targets = self.getExampleTargets()
		if example_targets:
			guess_thresholds = [image.mean(),]
			shape = image.shape
			hs = (128,128) # half size of the stats square
			for t in example_targets:
				guess_thresholds.append(image[max(0,t[1]-hs[1]):min(shape[0],t[1]+hs[1]),
																			max(0,t[0]-hs[0]):min(shape[1],t[0]+hs[0])].mean())
			guesses = ','.join(map((lambda x: '%.2f' % x),guess_thresholds))
			self.logger.info('guessed thresholds from examples: %s' % guesses)
			squares_thresh = min(guess_thresholds)
		else:
			## threshold grid bars
			squares_thresh = self.settings['threshold']
		self.logger.info('squares threshhold is %.1f' % float(squares_thresh))
		image = imagefun.threshold(image, squares_thresh)
		self.setImage(image, 'Thresholded')

		points_of_interest = []
		if example_targets:
			points_of_interest = map(lambda x: (x[1],x[0]), example_targets)
		## find blobs
		blobs = imagefun.find_blobs(self.mosaicimage, image,
																self.settings['blobs']['border'],
																self.settings['blobs']['max'],
																self.settings['blobs']['max size'],
																self.settings['blobs']['min size'],
																points_of_interest=points_of_interest,
																)
		self.example_blobs = []
		self.example_blob_indices = []
		# save examples for ranking and filtering
		for i, b in enumerate(blobs):
			if b.stats['has_poi']:
				# blobs that contains example_targets
				self.example_blobs.append(b)
				self.example_blob_indices.append(i)
		return blobs

	def runBlobRankFilter(self, blobs):
		'''
		Filter the blobs to get final targets. When example_blobs are present,
		they are placed at the top rank.
		'''
		## use stats to find good ones
		if not self.example_blobs:
			mean_min = self.settings['blobs']['min mean']
			mean_max = self.settings['blobs']['max mean']
			std_min = self.settings['blobs']['min stdev']
			std_max = self.settings['blobs']['max stdev']
			size_min = self.settings['blobs']['min size']
			size_max = self.settings['blobs']['max size']
		else:
			# use the stats of the example blobs
			means = map((lambda x: x.stats['mean']), self.example_blobs)
			mean_min = min(means)
			mean_max = max(means)
			stddevs = map((lambda x: x.stats['stddev']), self.example_blobs)
			std_min = min(stddevs)
			std_max = max(stddevs)
			sizes = map((lambda x: x.stats['n']), self.example_blobs)
			size_min = min(sizes)
			size_max = max(sizes)
			self.settings['blobs']['min mean'] = mean_min
			self.settings['blobs']['max mean'] = mean_max
			self.settings['blobs']['min stdev'] = std_min
			self.settings['blobs']['max stdev'] = std_max
			self.setSettings(self.settings, False)
		targets = []
		prefs = self.storeSquareFinderPrefs()
		if blobs:
			blob_sizes = numpy.array(map((lambda x: x.stats['n']),blobs))
			self.logger.info('Mean blob size is %.1f' % ( blob_sizes.mean(),))
			self.example_blob_indices.sort()
			# move the examples to front of the targetlist
			for i in self.example_blob_indices:
				blobs.insert(0, blobs.pop(i))
		for blob in blobs:
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			mean = blob.stats['mean']
			std = blob.stats['stddev']
			size = blob.stats['n']
			stats = leginondata.SquareStatsData(prefs=prefs, row=row, column=column, mean=mean, stdev=std)
			if (mean_min <= mean <= mean_max) and (std_min <= std <= std_max) and (size_min <= size <= size_max):
				stats['good'] = True
				## create a display target
				targets.append((column,row))
			else:
				stats['good'] = False
			self.publish(stats, database=True)
		return targets

	def checkSettings(self,settings):
		# always queuing. No need to check "wait for process" conflict
		return []

	def sendTargetsToRemote(self):
		'''
		Remote service target without confirmation
		'''
		# 1. createMosaicImage
		try:
			self.publishMosaicImage()
			mosaic_image_shape = self.mosaicimage.shape
		except AttributeError:
			self.logger.error('Need mosaic image to set targets')
			return False
		# 2. get displayed targets
		xytargets = self.getPanelTargets(mosaic_image_shape)
		# 3. send to remote server
		# put stuff in OutBox
		self.remote_targeting.setImage(self.mosaicimagedata)
		self.remote_targeting.setOutTargets(xytargets)
		return True

	def waitForTargetsFromRemote(self):
		self.logger.info('Waiting for remote targets')
		self.setStatus('remote')
		# targetxys are target coordinates in x, y grouped by targetnames
		targetxys = self.remote_targeting.getInTargets()
		# targetxys returns False if remote control is terminated by remote administrator
		if targetxys is not False:
			self.displayRemoteTargetXYs(targetxys)
		else:
			self.logger.error('remote targeting terminated by administrator. Use local targets.')
			self.terminated_remote = True
		preview_targets = self.panel.getTargetPositions('preview')
		if preview_targets:
			self.logger.error('can not handle preview with remote')
		self.setStatus('idle')

	def setRefreshTool(self, state):
		if not self.remote_toolbar:
			# requests not available or on the client so session is unknown
			return
		if state is True:
			self.remote_toolbar.addClickTool('refresh','refreshRemoteTargets','refresh atlas to submit more','none')
		else:
			if 'refresh' in self.remote_toolbar.tools:
				self.remote_toolbar.removeClickTool('refresh')
		# finalize toolbar and send to leginon-remote
		self.remote_toolbar.finalizeToolbar()

	def uiChooseCheckMethod(self, method):
		'''
		handle gui check method choice.  Bypass using self.settings['check method']
		because that is not yet set.
		'''
		if not self.remote_targeting or not self.remote_targeting.remote_server_active:
			return
		state = (method == 'remote')
		self.setRefreshTool(state)
