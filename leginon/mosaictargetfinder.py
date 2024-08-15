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
import multihole
from pyami import convolver, imagefun, mrc, ordereddict, affine
from pyami import groupfun
import numpy
import pyami.quietscipy
import scipy.ndimage as nd
import gui.wx.MosaicClickTargetFinder

import os
import math
import random
import json

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
	mosaictarget_defaultsettings = {
		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'create on tile change': 'all',
		'autofinder': False,
		'target grouping': {
			'total targets': 10,
			'classes': 1,
			'group method': 'value delta',
			'randomize blobs': True,
		},
		'target multiple':1,
	}
	defaultsettings.update(mosaictarget_defaultsettings)
	auto_square_finder_defaultsettings = {
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
			'min size': 10,  # used in blob-finding threshold
			'max size': 10000,
			'min mean': 1000, # used in filtering
			'max mean': 20000,
			'min stdev': 10,
			'max stdev': 500,
			'min filter size': 10, # used in filtering and sampling
			'max filter size': 10000,
		},
	}
	defaultsettings.update(auto_square_finder_defaultsettings)

	eventoutputs = targetfinder.ClickTargetFinder.eventoutputs + [
			event.MosaicDoneEvent]
	targetnames = ['acquisition','focus','preview','reference','done','Blobs', 'example']
	target_group_methods = ['value delta','target count','jenks']

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
		self.finder_mosaic = mosaic.EMMosaic(self.calclients[parameter])
		self.mosaicimagelist = None
		self.oldmosaicimagelist = None
		self.mosaicimage = None
		self.mosaicname = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None
		self.finder_mosaicimage = None
		self.finder_edge_mosaicimage = None
		self.finder_scale_factor = 1
		self.convolver = convolver.Convolver()
		self.multihole = multihole.TemplateConvolver()
		self.currentposition = []
		self.target_order = []
		self.sq_prefs = None
		self.mosaiccreated = threading.Event()
		self.autofinderlock = threading.Lock()
		self.sessionclearlock = threading.Lock()
		self.userpause = threading.Event()
		self.presetsclient = presets.PresetsClient(self)

		self.mosaic.setCalibrationClient(self.calclients[parameter])
		self.finder_mosaic.setCalibrationClient(self.calclients[parameter])
		self.oldmosaic.setCalibrationClient(self.calclients[parameter])
		self.oldsession = self.session

		self.existing_targets = {}
		self.donetargets = []
		self.last_xys = [] # last acquisition targets found in autofinder
		self.mask_xys = []
		self.clearTiles()
		self.autotask_type = None

		self.reference_target = None
		self.setRefreshTool(self.settings['check method']=='remote')

		self.addEventInput(event.NotifyTaskTypeEvent, self.handleNotifyTaskType)
		self.addEventInput(event.SubmitMosaicTargetsEvent, self.handleSubmitMosaicTargets)

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	def insertDoneTargetList(self, targetlistdata):
		# this class targetlist must not be recorded done so that
		# more targets can be added to it
		self.logger.debug('%s did not insert done on %d' % (self.name,targetlistdata.dbid))
		pass

	def handleSetSessionEvent(self, ievent):
		self.sessionclearlock.acquire()
		super(MosaicClickTargetFinder, self).handleSetSessionEvent(ievent)
		self.clearTiles()
		self.sessionclearlock.release()


	def handleSubmitMosaicTargets(self, evt):
		self.notifyTargetReceiver()
		self.autoSubmitTargets()

	def autoReloadLastAtlas(self):
		try:
			selection = self.getMosaicNames()[0]
		except IndexError:
			self.logger.error('No existing mosaic to reload')
			return
		self.setMosaicName(selection)
		self.loadMosaicTiles(selection)
		# use existing target map to get count of targets
		# count includes also the done targets
		count = sum(map((lambda x: len(self.targetmap[x]['acquisition'])), self.targetmap.keys()))
		# length of self.last_xys is used to make target submission wait for display thread.
		self.last_xys = range(count-len(self.donetargets))
		# notify manage atlas and targets are loaded.
		self.notifyAutoDone('atlas')
		self.setStatus('idle')

	def handleNotifyTaskType(self, evt):
		self.autotask_type = evt['task']
		if self.autotask_type == 'submit squares':
			self.autoReloadLastAtlas()

	def notifyTargetReceiver(self):
			'''
			Notify Manager where the targets are sent to.
			'''
			evt = event.MosaicTargetReceiverNotificationEvent()
			evt['receiver'] = self.next_acq_node['node']['alias']
			self.outputEvent(evt)

	def handleTargetListDone(self, targetlistdoneevent):
		if targetlistdoneevent:
			self.logger.debug('Got real targetlistdone event')
		else:
			self.logger.debug('Handle fake targetlistdone event')
		# wait until addTile thread is finished.
		while self.autofinderlock.locked():
			time.sleep(0.5)
		while len(self.mosaic.tiles) < 1:
			self.logger.info('waiting for at least one mosaic tile to create mosaic image')
			time.sleep(0.2)
		if self.settings['create on tile change'] in ('all','final',):
			self.createMosaicImage(True)
		if not self.hasNewImageVersion():
			self.targetsFromDatabase()
			# fresh atlas without acquisition targets (done or not) should run autofinder
			count = sum(map((lambda x: len(self.targetmap[x]['acquisition'])), self.targetmap.keys()))
			if count == 0 and self.settings['autofinder']:
				self.logger.debug('auto target finder')
				self.autoTargetFinder()
		# Pause here from gui
		if not self.userpause.is_set():
			msg = 'autosubmit paused by user'
			self.logger.info(msg)
			if self.settings['autofinder']:
				# Send this message to slack
				msg += ' in session %s' % self.session['name']
				msg = '%s %s' % (self.name, msg)
				self.outputEvent(event.NodeLogErrorEvent(message=msg))
			self.setStatus('user input')
		self.userpause.wait()
		self.setStatus('processing')
		#
		# trigger activation of submit button in the gui.
		self.panel.doneTargetList()
		# auto submit targets if from auto full run.
		self.notifyAutoDone('atlas')
		self.setStatus('idle')

	def guiPauseBeforeSubmit(self):
		self.userpause.clear()

	def guiTargetMask(self, xys):
		'''
		get mask fitted shape vertices in a list of (x,y) at mosaic
		'''
		self.mask_xys = xys

	def autoTargetFinder(self):
		"""
		automated target finder.  This includes general finder and then ranker to filter
		and sample the targets.
		"""
		if self.mosaicimage is None:
			self.logger.error('Must have atlas display to find squares')
			return
		self.publishMosaicImage()
		try:
			# get blobs at finder scale with stats
			blobs = self.findSquareBlobs()
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
		blobs = self.filterBlobsByMask(blobs)
		xys = self.runBlobRankFilter(blobs, xytargets)
		message = 'found %s squares' % (len(xys),)
		self.last_xys = xys
		## display them
		# IMPORTANT: Don't put back unprocessed but submitted targets
		# because they will get duplicated.
		# It will also cause autoSubmitTargets break its while loop
		# too early
		self.setTargets(xys, 'acquisition')
		self.setTargets([], 'example')
		self.logger.info(message)

	def autoSubmitTargets(self):
		"""
		Submit autofinder targets.
		"""
		# Target display is in a separate thread and has slight lag.
		while 1:
			time.sleep(0.1)
			try:
				# Check the display to make sure the targets are displayed as found.
				target_positions_from_image = self.panel.getTargetPositions('acquisition')
			except ValueError:
				pass
			if len(target_positions_from_image) == len(self.last_xys):
				break
		self.submitTargets()

	def publishNewTargetsOfType(self, typename):
		'''
		Get positions of the typename targets from atlas, publish the new ones,
		and then update self.existing_position_targets with the published one added.
		'''
		displayedtargetdata = {}
		try:
			target_positions_from_image = self.panel.getTargetPositions(typename)
		except ValueError:
			return
		if self.settings['sort target']:
			target_positions_from_image = self.sortTargets(target_positions_from_image)
		for coord_tuple in target_positions_from_image:
			##  check if it is an existing position with database target.
			if coord_tuple in self.existing_position_targets and self.existing_position_targets[coord_tuple]:
				# pop so that it has a smaller dictionary to check
				targetdata = self.existing_position_targets[coord_tuple].pop()
			else:
				# This is a new position, publish it
				c,r = coord_tuple
				targetdata = self.mosaicToTarget(typename, r, c)
			# Both new and old targetdata get put into displayedtargetdata
			if coord_tuple not in displayedtargetdata:
				displayedtargetdata[coord_tuple] = []
			if targetdata['number'] not in self.target_order:
				self.target_order.append(targetdata['number'])
			displayedtargetdata[coord_tuple].append(targetdata)
		# update self.existing_position_targets.
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
		"""
		Overwrite TargetFinder submitTargets.
		"""
		self.terminated_remote = False
		self.userpause.set()
		# clear targets and not really submit if not full autoscreen
		# because submitTargets call
		# and self.userpause.set are both activated with gui submit tool.
		if self.autotask_type == 'atlas':
			self.displayDatabaseTargets()
			# reset autotask_type to None so submit on the last autorun  grid is possible.
			self.autotask_type = None
			# trigger onTargetsSubmitted in the gui.
			self.panel.targetsSubmitted()
			return

		if self.mosaicimage is None:
			self.setStatus('idle')
			return

		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			# force to make it in front
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
		"""
		The real submit target part. targetlist should be created by now.
		"""
		# create a list of targets of each type
		self.logger.info('Submitting targets...')
		self.target_order = self.getTargetOrder(self.targetlist)
		try:
			self.publishNewTargetsOfType('acquisition')
			self.publishNewTargetsOfType('focus')
			self.publishNewTargetsOfType('preview')
		except ValueError as e:
			self.logger.error('New target creation failed: %s' % e)
			self.logger.error('Reload tiles with auto finding to correct this.')
			# trigger onTargetsSubmitted in the gui.
			self.panel.targetsSubmitted()
			return
		except Exception as e:
			self.logger.error('New target creation failed: %s' % e)
			# trigger onTargetsSubmitted in the gui.
			self.panel.targetsSubmitted()
			return
		try:
			self.publishTargetOrder(self.targetlist,self.target_order)
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
		self.clearAllTargets()
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		self.finder_mosaic.clear()
		self.userpause.set()
		self.targetlist = None
		self.clearMosaicImage()
		self.clearFinderMosaicImage()

	def addTile(self, imagedata):
		'''
		Add tile into mosaic and various mappings. Lock autofinder
		in handleTargetListDone so that this is done before that event
		is handled.
		'''
		self.logger.debug('addTile image: %s' % (imagedata.dbid,))
		imid = imagedata.dbid
		if imid in self.tilemap:
			self.logger.info('Image already in mosaic')
			return
		self._addTile(imagedata)

	def _addTile(self, imagedata):
		'''
		Add tile into mosaic and various mappings.
		'''
		self.logger.info('Adding image to mosaic')
		imid = imagedata.dbid
		newtile = self.mosaic.addTile(imagedata)
		self.finder_mosaic.addTile(imagedata)
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
		self.logger.info('Refreshing targets from database and ignoring unsaved ones...')
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
		# self.donetargets is used to help confirm targets are all displayed
		# in autoReloadLastAtlas
		self.donetargets = donetargets
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
		self.setTargets([], 'example')
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
		# not to force insertion so mosaicimage and tile images are on the same imagelist
		self.publish(self.mosaicimagelist, database=True)
		self.logger.debug('published new mosaic image list')
		self.setMosaicName(targetlist)
		return self.mosaicimagelist

	def processImageData(self, imagedata):
		'''
		different from ClickTargetFinder because findTargets is
		not per image, instead we have submitTargets.
		Each new image becomes a tile in a mosaic.
		'''
		while self.sessionclearlock.locked():
			time.sleep(0.5)
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
		self.autofinderlock.acquire()
		self.addTile(imagedata)

		if self.settings['create on tile change'] == 'all':
			self.logger.debug('create all')
			self.createMosaicImage(False)
			self.logger.debug('done create all')
		self.autofinderlock.release()

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
		self.writeMosaicInfo(self.mosaic, self.mosaicimagedata)

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
		self.autofinderlock.acquire()
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
			self.createMosaicImage(True)
		self.loadSquareBlobsAfterAllTiles()
		# use currentimagedata to set TargetImageVectors for target multiple
		self.setTargetImageVectors(self.currentimagedata)
		self.autofinderlock.release()
		# hacking
		self.handleTargetListDone(None)

	def loadSquareBlobsAfterAllTiles(self):
		'''
		load square blobs if available after create final mosaic image.
		'''
		pass

	def targetToMosaic(self, tile, targetdata):
		scalepos = self._targetToMosaic(tile, targetdata, self.mosaic)
		return scalepos

	def _targetToMosaic(self, tile, targetdata, mosaic_instance):
		shape = tile.image.shape
		drow = targetdata['delta row']
		dcol = targetdata['delta column']
		tilepos = drow+shape[0]/2, dcol+shape[1]/2
		return self._tile2MosaicPosition(tile, tilepos, mosaic_instance)

	def _tile2MosaicPosition(self, tile, tilepos, mosaic_instance):
		# tilepos is written as (r, c)
		# scalepos is written as (r, c)
		mospos = mosaic_instance.tile2mosaic(tile, tilepos)
		scaledpos = mosaic_instance.scaled(mospos)
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
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist, **kwargs)
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata

	def createMosaicImage(self, is_final=True):
		self.logger.info('creating mosaic image')

		self.setCalibrationParameter()

		if self.settings['scale image']:
			maxdim = self.settings['scale size']
			if not is_final:
				# make smaller mosaic unless it is the final display.  This
				# reduces peak memory usage
				maxdim = 1024
		else:
			maxdim = None
		self.mosaicimagescale = maxdim
		try:
			self.mosaicimage = self.mosaic.getMosaicImage(maxdim)
			if is_final:
				# create finder mosaic image only for final display.
				self.createFinderMosaicImage()
		except Exception, e:
			self.logger.error('Failed Creating mosaic image: %s' % e)
		self.mosaicimagedata = None

		self.logger.info('Displaying mosaic image')
		self.setImage(self.mosaicimage, 'Image')
		self.logger.info('image displayed, displaying targets...')
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

	def clearFinderMosaicImage(self):
		self.finder_mosaicimage = None
		self.finder_edge_mosaicimage = None
		self.finder_scale_factor = 1

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
		prefs['minblobsize'] = self.settings['blobs']['min filter size']
		prefs['maxblobsize'] = self.settings['blobs']['max filter size']
		prefs['mean-min'] = self.settings['blobs']['min mean']
		prefs['mean-max'] = self.settings['blobs']['max mean']
		prefs['std-min'] = self.settings['blobs']['min stdev']
		prefs['std-max'] = self.settings['blobs']['max stdev']
		self.publish(prefs, database=True)
		return prefs

	def getExampleAndPanelTargets(self, xytargets):
		existing_targets = xytargets['done']
		existing_targets.extend(xytargets['acquisition'])
		return xytargets['example'], existing_targets

	def setFinderScaleFactor(self):
		old_maxdim = self.mosaicimagescale
		if old_maxdim is None:
			old_maxdim = max(self.mosaicimage.shape)
		# no bigger than 2048
		scale_factor = int(math.ceil(old_maxdim / 2048.0))
		self.finder_scale_factor = scale_factor

	def createFinderMosaicImage(self):
		'''
		Downsize mosaicimage so that it does not use too much
		resource in blob finding.
		'''
		self.setFinderScaleFactor()
		old_maxdim = self.mosaicimagescale
		new_maxdim = old_maxdim // self.finder_scale_factor
		self.logger.info('Scale down mosaic to finder max dimension of %d' % new_maxdim)
		self.finder_maxdim = new_maxdim
		self.finder_mosaicimage = self.finder_mosaic.getMosaicImage(new_maxdim)
		# make edge_mosaicimage with a guess of the edge width at 15% of image length.
		# This is not exact but appears good enough.
		self.finder_edge_mosaicimage = self.finder_mosaic.getEdgeMosaicImage(new_maxdim, width=None)
		self.logger.debug('Scaling  Target mapping from shape %s to %s with setting of max size of %d' % (self.finder_mosaicimage.shape, self.mosaicimage.shape, self.settings['scale size']))
		self.logger.debug('Finder edge mosaicimage edge width = %d pixels' % self.finder_mosaic.edge_width)

	def writeMosaicInfo(self, m_inst, mosaicimagedata):
		scale = m_inst.scale
		shape = mosaicimagedata.imageshape()
		pos=m_inst.positionByCalibration({'x':0.0,'y':0.0})
		pixel_pos = (pos[0]+shape[0]/(2*scale), pos[1]+shape[1]/(2*scale))
		center_tile = m_inst.getNearestTile(pixel_pos[0], pixel_pos[1])
		info = {}
		label = mosaicimagedata['list']['targets']['label']
		json_name = '%s_' % (self.session['name'])
		if label:
			json_name += label
		json_path = os.path.join(self.session['image path'],json_name+'.json')
		info['session image path'] = self.session['image path']
		info['mosaic_label'] = mosaicimagedata['list']['targets']['label']
		info['full_mosaic_shape'] = {'rows':m_inst.mosaicshape[0],'cols':m_inst.mosaicshape[1]}
		info['mosaic_image'] = {}
		info['mosaic_image']['filename'] = mosaicimagedata['filename']+'.mrc'
		info['mosaic_image']['scale'] = scale
		info['center_tile_filename'] = center_tile.imagedata['filename']+'.mrc'
		info['tiles'] = []
		for t in m_inst.tiles:
			tinfo = {}
			tinfo['filename'] = t.imagedata['filename']+'.mrc'
			tinfo['corner_pos'] = {'row': t.corner_pos[0],'col':t.corner_pos[1]}
			info['tiles'].append(tinfo)
		info_str = json.dumps(info)
		f = open(json_path,'w')
		f.write(info_str)
		f.close()

	def findSquareBlobs(self):
		message = 'finding squares'
		self.logger.info(message)

		sigma = self.settings['lpf']['sigma']
		kernel = convolver.gaussian_kernel(sigma)
		self.convolver.setKernel(kernel)
		finder_image = self.convolver.convolve(image=self.finder_mosaicimage)
		self.setImage(finder_image, 'Filtered')

		## threshold grid bars
		squares_thresh = self.settings['threshold']
		self.logger.info('squares threshhold is %.1f' % float(squares_thresh))
		finder_image = imagefun.threshold(finder_image, squares_thresh)
		self.setImage(finder_image, 'Thresholded')
		# mask for label
		self.finder_mask = finder_image

		## find blobs
		blobs = imagefun.find_blobs(self.finder_mosaicimage, self.finder_mask,
																self.settings['blobs']['border'],
																self.settings['blobs']['max'],
																self.settings['blobs']['max size'],
																self.settings['blobs']['min size'],
																method='biggest',
																)
		return blobs

	def setFilterSettings(self, example_blobs):
		if example_blobs:
			# use the stats of the example blobs
			means = map((lambda x: x.stats['mean']), example_blobs)
			mean_min = min(means)
			mean_max = max(means)
			stddevs = map((lambda x: x.stats['stddev']), example_blobs)
			std_min = min(stddevs)
			std_max = max(stddevs)
			sizes = map((lambda x: x.stats['n']), example_blobs)
			size_min = min(sizes)
			size_max = max(sizes)
			self.settings['blobs']['min mean'] = mean_min
			self.settings['blobs']['max mean'] = mean_max
			self.settings['blobs']['min stdev'] = std_min
			self.settings['blobs']['max stdev'] = std_max
			self.settings['blobs']['min filter size'] = size_min
			self.settings['blobs']['max filter size'] = size_max
			self.setSettings(self.settings, False)
			return

	def filterBlobsByMask(self, blobs):
		if len(self.mask_xys) < 3:
			return blobs
		s = self.finder_scale_factor
		finder_vertices = map((lambda x: (x[1]//s,x[0]//s)),self.mask_xys)
		new_blobs = []
		def blob_in_polygon(x):
			return polygon.point_inside_polygon(x['center'][0], x['center'][1], finder_vertices)
		blobs = filter((lambda x: blob_in_polygon(x.stats)), blobs)
		return blobs

	def runBlobRankFilter(self, finder_blobs, xytargets):
		'''
		Filter the blobs at finder image scale to get final targets.
		xytargets are dictionary of existing targets on the mosaic image.
		When examples are present in this dictionary, the blob contain
		them are placed at the top rank.
		'''
		if not finder_blobs:
			return []
		example_xys=xytargets['example']
		# These xy tuples are those in the database on self.mosaic scale.
		database_xys=self.existing_position_targets.keys()
		##############
		# blobs and filtering are done at smaller dimension to save memory usage.
		##############
		s = self.finder_scale_factor
		finder_example_points = map((lambda x: (x[1]//s,x[0]//s)),example_xys)
		finder_database_points = map((lambda x: (x[1]//s,x[0]//s)),database_xys)
		priority_blobs, other_blobs, finder_display_array = self._runBlobRankFilter(finder_blobs, finder_example_points, finder_database_points)
		if finder_display_array is not None:
			self.setImage(finder_display_array, 'Thresholded')
		# filter out blobs with stats settings.
		other_blobs = self.filterStats(other_blobs)
		# sample some non-priority blobs
		non_priority_total = self.settings['target grouping']['total targets']-len(priority_blobs)
		other_blobs = self.sampleBlobs(other_blobs, non_priority_total)
		combined_blobs = priority_blobs+other_blobs
		################
		# turn combined blobs into targets at the original mosaic dimension
		################
		targets = map((lambda x: self.blobToDisplayTarget(x,self.finder_scale_factor)), combined_blobs)
		# flat list of multihole convolution at the original mosaic dimension
		targets = self.multiHoleConvolution(targets)
		return targets

	def multiHoleConvolution(self, targets):
		'''
		Convolute targets using a lattice based on next acquisition
		targetimagevectors
		'''
		target_groups = map((lambda x: self._multihole_list(x)), targets)
		# return a flat list of targets
		return [t for tgroup in target_groups for t in tgroup] 

	def _multihole_list(self, original_target):
		'''
		Returns a list of convoluted targets
		'''
		npoint = self.settings['target multiple']
		if not npoint:
			npoint = 1
		self.multihole.setConfig(npoint, single_scale=1.0)
		axis_vectors = numpy.array([self.targetimagevectors['y'],self.targetimagevectors['x']])
		self.multihole.setUnitVector(axis_vectors)
		lattice_vectors = self.multihole.makeLatticeVectors()
		targets = numpy.ndarray.tolist(lattice_vectors)
		# shift based on original_target
		targets = map((lambda x: (x[0]+original_target[0],x[1]+original_target[1])), targets)
		# [(row0,col0),(row1,col1),....]
		return targets

	def _runBlobRankFilter(self, blobs, example_points, panel_points):
		'''
		Rank blobs and filter them by some filter.  All
		input and output are at finder image scale.
		'''
		example_blobs = []
		example_blob_indices = []

		# display_array is at finder shape
		has_priority, to_avoid, display_array =  self.filterPoints(blobs, example_points, panel_points)
		# save examples for ranking and filtering
		for i, b in enumerate(blobs):
			l = b.stats['label_index']
			# TODO: for this to work blobs, has_priority must ordered like blobs
			if has_priority[l]:
				# blobs that contains example_points
				example_blobs.append(b)
				example_blob_indices.append(i)
		## use example_blobs stats to find good ones
		self.setFilterSettings(example_blobs)
		#
		#
		blob_sizes = numpy.array(map((lambda x: x.stats['n']),blobs))
		self.logger.info('Mean blob size is %.1f' % ( blob_sizes.mean(),))
		example_blob_indices.sort()
		# move the examples to front of the targetlist
		for i in example_blob_indices:
			blobs.insert(0, blobs.pop(i))
		# filter out blobs to avoid
		def is_false(b):
			return not to_avoid[b.stats['label_index']]
		# set aside example blobs not need to be avoided
		priority_blobs = filter(is_false, example_blobs)
		# remove any to_avoid blobs from the rest of the blobs
		blobs = filter(is_false, blobs[len(priority_blobs):])
		return priority_blobs, blobs, display_array

	def filterPoints(self, blobs, example_points, panel_points):
		'''
		Return boolean for each blob. All input and output are
		at image scale of the smaller a.k.a. finder scale.
		has_priority: at least one example_point is in the blob
		to_avoid: at least one panel_point is in the blob
		display_array: some image array to display in the gui as
				Thresholded image.
		'''
		return self.filterPointsByLabel(blobs, example_points, panel_points)

	def filterPointsByLabel(self, blobs, example_points, panel_points):
		'''
		filter points at finder image scale.
		'''
		labels, n = imagefun.scipylabels(self.finder_mask)
		has_priority = imagefun.hasPointsInLabel(labels, n, example_points)
		to_avoid = imagefun.hasPointsInLabel(labels, n, panel_points)
		return has_priority, to_avoid, labels


	def blobToDisplayTarget(self, blob, finder_scale):
			row = blob.stats['center'][0]*finder_scale
			column = blob.stats['center'][1]*finder_scale
			return (column, row)

	def filterStats(self, blobs):
		'''
		filter based on blob stats
		'''
		self.sq_prefs = self.storeSquareFinderPrefs()
		mean_min = self.settings['blobs']['min mean']
		mean_max = self.settings['blobs']['max mean']
		std_min = self.settings['blobs']['min stdev']
		std_max = self.settings['blobs']['max stdev']
		size_min = self.settings['blobs']['min filter size']
		size_max = self.settings['blobs']['max filter size']
		good_blobs = []
		for blob in blobs:
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			mean = blob.stats['mean']
			std = blob.stats['stddev']
			size = blob.stats['n']
			try:
				on_edge = self.finder_edge_mosaicimage[row,column]
			except Exception as e:
				self.logger.debug('edge filtering error: %s' % e)
				on_edge = True
			if (mean_min <= mean <= mean_max) and (std_min <= std <= std_max) and (size_min <= size <= size_max) and not on_edge:
				good_blobs.append(blob)
			else:
				stats = leginondata.SquareStatsData(session=self.session, prefs=self.sq_prefs, row=row, column=column, mean=mean, stdev=std, size=size)
				stats['good'] = False
				stats['on_edge'] = on_edge
				# only publish bad stats
				self.publish(stats, database=True)
		return good_blobs

	def getGroupMethodChoices(self):
		return self.target_group_methods

	def _getBlobStatsKeyForGrouping(self):
		return 'n'

	def _getGrouperValueMinMax(self):
		value_min = self.settings['blobs']['min filter size']
		value_max = self.settings['blobs']['max filter size']
		return value_min, value_max

	def _setSampler(self, grouper, total_target_need,randomize_blobs):
		return groupfun.BlobRandomSizeSampler(grouper, total_target_need, self.logger)

	def sampleBlobs(self, blobs, total_targets_need):
		total_blobs = len(blobs)
		if total_blobs <= total_targets_need:
			# Nothing to do
			self.logger.info('Number of filtered blobs (%d) < number of requested targets (%d). Use all.' % (total_blobs, total_targets_need))
			return blobs
		n_class = self.settings['target grouping']['classes']
		group_method = self.settings['target grouping']['group method']
		randomize_blobs = self.settings['target grouping']['randomize blobs']
		stats_key = self._getBlobStatsKeyForGrouping()
		try:
			if group_method == 'value delta':
				grouper = groupfun.EqualValueDeltaIndexGrouper(blobs, n_class, stats_key)
				value_min, value_max = self._getGrouperValueMinMax()
				grouper.setValueMinMax(value_min, value_max)
			elif group_method == 'target count':
				grouper = groupfun.EqualCountBlobIndexGrouper(blobs, n_class, stats_key)
			elif group_method == 'jenks':
				grouper = groupfun.JenksIndexGrouper(blobs, n_class, stats_key)
			grouper.groupBlobIndex()
			sampler = self._setSampler(grouper, total_targets_need,randomize_blobs)
			return sampler.sampleBlobs()
		except Exception as e:
			self.logger.error('sampling error: %s' % e)
			return []

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
