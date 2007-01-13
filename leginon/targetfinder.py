#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import data
import event
import instrument
import imagewatcher
import mosaic
import Mrc
import threading
import node
import targethandler
import convolver
import imagefun
import numarray
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.MosaicClickTargetFinder
import os
import libCV
import math
import polygon
import raster
import presets
try:
	set = set
except NameError:
	import sets
	set = Set

class TargetFinder(imagewatcher.ImageWatcher, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetFinder.Panel
	settingsclass = data.TargetFinderSettingsData
	defaultsettings = {
		'queue': False,
		'wait for done': True,
		'ignore images': False,
		'user check': False,
		'queue drift': True,
	}
	eventinputs = imagewatcher.ImageWatcher.eventinputs \
									+ [event.AcquisitionImagePublishEvent] \
									+ targethandler.TargetWaitHandler.eventinputs
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs \
									+ targethandler.TargetWaitHandler.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation,
																				**kwargs)
		targethandler.TargetWaitHandler.__init__(self)
		self.instrument = instrument.Proxy(self.objectservice, self.session)

	def readImage(self, filename):
		imagedata = self.getImageFromDB(filename)
		if imagedata is None:
			try:
				orig = Mrc.mrc_to_numeric(filename)
			except Exception, e:
				self.logger.exception('Read image failed: %s' % e[-1])
				return
		else:
			orig = imagedata['image']
		self.currentimagedata = imagedata

		self.setImage(orig, 'Original')

	def getImageFromDB(self, filename):
		# only want filename without path and extension
		filename = os.path.split(filename)[1]
		filename = '.'.join(filename.split('.')[:-1])
		q = data.AcquisitionImageData(filename=filename)
		results = self.research(datainstance=q)
		print 'len', len(results)
		if not results:
			return None
		imagedata = results[0]
		return imagedata

	def findTargets(self, imdata, targetlist):
		'''
		Virtual function, inheritting classes implement creating targets
		'''
		raise NotImplementedError()

	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return

		querydata = data.AcquisitionImageData(list=imagelistdata)
		## research, but don't read images until later
		images = self.research(querydata, readimages=False)
		targetlist = self.newTargetList(queue=self.settings['queue'])
		for imagedata in images:
			self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		if self.settings['queue']:
			self.logger.info('Queue is on... not generating event')
			pubevent=False
		else:
			self.logger.info('Queue is off... generating event')
			pubevent=True
		self.publish(targetlist, database=True, dbforce=True, pubevent=pubevent)
		if self.settings['wait for done'] and pubevent:
			self.setStatus('waiting')
			self.waitForTargetListDone()
			self.setStatus('processing')

	def targetsFromClickImage(self, clickimage, typename, targetlist):
		imagedata = clickimage.imagedata
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in clickimage.getTargetType(typename):
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			self.publish(targetdata, database=True)
			number += 1

	def publishTargets(self, imagedata, typename, targetlist):
		imagetargets = self.panel.getTargetPositions(typename)
		if not imagetargets:
			return
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata,
																				session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			self.publish(targetdata, database=True)
			number += 1

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.settings['ignore images']:
			return

		# check if there is already a target list for this image
		# exclude sublists (like rejected target lists)
		previouslists = self.researchTargetLists(image=imagedata, sublist=False)
		if previouslists:
			# I hope you can only have one target list on an image, right?
			targetlist = previouslists[0]
			db = False
			self.logger.info('Already processed this image... republishing')
		else:
			# no previous list, so create one and fill it with targets
			targetlist = self.newTargetList(image=imagedata, queue=self.settings['queue'])
			self.findTargets(imagedata, targetlist)
			self.logger.debug('Publishing targetlist...')
			db = True

		## if queue is turned on, do not notify other nodes of each target list publish
		if self.settings['queue']:
			pubevent = False
		else:
			pubevent = True
		self.publish(targetlist, database=db, pubevent=pubevent)
		self.logger.debug('Published targetlist %s' % (targetlist.dbid,))

		if self.settings['wait for done'] and not self.settings['queue']:
			self.makeTargetListEvent(targetlist)
			self.setStatus('waiting')
			self.waitForTargetListDone()
			self.setStatus('processing')

	def publishQueue(self):
		if self.settings['queue drift']:
			self.declareDrift('submit queue')
		queue = self.getQueue()
		self.publish(queue, pubevent=True)

	def notifyUserSubmit(self):
		message = 'Waiting for user to submit targets...'
		self.logger.info(message)
		self.beep()

	def submitTargets(self):
		self.userpause.set()

class ClickTargetFinder(TargetFinder):
	targetnames = ['preview', 'reference', 'focus', 'acquisition']
	panelclass = gui.wx.ClickTargetFinder.Panel
	eventoutputs = TargetFinder.eventoutputs + [event.ReferenceTargetPublishEvent]
	settingsclass = data.ClickTargetFinderSettingsData
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.start()

	def findTargets(self, imdata, targetlist):
		# display image
		for target_name in self.targetnames:
			self.setTargets([], target_name, block=True)
		self.setImage(imdata['image'], 'Image')
		wait = True
		while wait:
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.setStatus('processing')
			preview_targets = self.panel.getTargetPositions('preview')
			if preview_targets:
				self.publishTargets(imdata, 'preview', targetlist)
				self.setTargets([], 'preview', block=True)
				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, database=True, dbforce=True, pubevent=True)
				self.setStatus('waiting')
				self.waitForTargetListDone()
			else:
				wait = False
		self.panel.targetsSubmitted()
		self.setStatus('processing')
		self.logger.info('Publishing targets...')
		for i in self.targetnames:
			if i == 'reference':
				self.publishReferenceTarget(imdata)
			else:
				self.publishTargets(imdata, i, targetlist)
		self.setStatus('idle')

	def publishReferenceTarget(self, image_data):
		try:
			column, row = self.panel.getTargetPositions('reference')[-1]
		except IndexError:
			return
		rows, columns = image_data['image'].shape
		delta_row = row - rows/2
		delta_column = column - columns/2
		reference_target = self.newReferenceTarget(image_data, delta_row, delta_column)
		try:
			self.publish(reference_target, database=True, pubevent=True)
		except node.PublishError, e:
			self.logger.error('Submitting reference target failed')
		else:
			self.logger.info('Reference target submitted')

class MosaicClickTargetFinder(ClickTargetFinder):
	panelclass = gui.wx.MosaicClickTargetFinder.Panel
	settingsclass = data.MosaicClickTargetFinderSettingsData
	defaultsettings = dict(ClickTargetFinder.defaultsettings)
	defaultsettings.update({
		'min region area': 0.01,
		'max region area': 0.8,
		've limit': 50,
		'black on white': False,
		'raster spacing': 50,
		'raster angle': 0,
		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'mosaic image on tile change': True,
		'watchdone': False,
		'targetpreset': None,
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

	eventoutputs = ClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position':
												calibrationclient.ModeledStageCalibrationClient(self)
		}
		self.images = {
			'Original': None,
			'Extra Crispy': None,
			'Filtered': None,
			'Thresholded': None
		}
		parameter = self.settings['calibration parameter']
		self.mosaic = mosaic.EMMosaic(self.calclients[parameter])
		self.mosaicimagelist = None
		self.mosaicimage = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None
		self.convolver = convolver.Convolver()
		self.currentposition = []
		self.imagesourcedone = threading.Event()
		self.presetsclient = presets.PresetsClient(self)

		self.mosaic.setCalibrationClient(self.calclients[parameter])

		self.existing_targets = {}
		self.clearTiles()

		self.reference_target = None

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		if self.settings['watchdone']:
			# HACK: TargetListDone indicates that all grid images are
			# acquired could probably figure this out with a little
			# research instead of a user setting
			self.imagesourcedone.set()

	def getTargetDataList(self, typename):
		displayedtargetdata = {}
		targetsfromimage = self.panel.getTargetPositions(typename)
		for t in targetsfromimage:
			## if displayed previously (not clicked)...
			if t in self.displayedtargetdata and self.displayedtargetdata[t]:
				targetdata = self.displayedtargetdata[t].pop()
			else:
				c,r = t
				targetdata = self.mosaicToTarget(typename, r, c)
			if t not in displayedtargetdata:
				displayedtargetdata[t] = []
			displayedtargetdata[t].append(targetdata)
		self.displayedtargetdata = displayedtargetdata

	def getDisplayedReferenceTarget(self):
		try:
			column, row = self.panel.getTargetPositions('reference')[-1]
		except IndexError:
			return None
		imagedata, delta_row, delta_column = self._mosaicToTarget(row, column)
		return self.newReferenceTarget(imagedata, delta_row, delta_column)

	def submitTargets(self):
		self.userpause.set()
		if self.settings['watchdone']:
			return
		self.logger.info('Submitting targets...')
		self.getTargetDataList('acquisition')
		self.getTargetDataList('focus')
		if self.targetlist is not None:
			try:
				self.publish(self.targetlist, pubevent=True)
			except node.PublishError, e:
				self.logger.error('Submitting acquisition targets failed')
			else:
				self.logger.info('Acquisition targets submitted')

		reference_target = self.getDisplayedReferenceTarget()
		if reference_target is not None:
			try:
				self.publish(reference_target, database=True, pubevent=True)
			except node.PublishError, e:
				self.logger.error('Submitting reference target failed')
			else:
				self.logger.info('Reference target submitted')

	def clearTiles(self):
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		self.targetlist = None
		if self.settings['mosaic image on tile change']:
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
		self.targetmap[imid] = {}
		for type in ('acquisition','focus'):
			targets = self.researchTargets(image=imagedata, type=type)
			if targets and self.targetlist is None:
				self.targetlist = targets[0]['list']
			self.targetmap[imid][type] = targets
		self.logger.info('Image added to mosaic')

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			self.targetmap[id] = {}
			for type in ('acquisition','focus'):
				targets = self.researchTargets(image=imagedata, type=type)
				### set my target list to same as first target found
				if targets and self.targetlist is None:
					self.targetlist = targets[0]['list']
				self.targetmap[id][type] = targets
		self.reference_target = self.getReferenceTarget()

	def refreshCurrentPosition(self):
		self.updateCurrentPosition()
		self.setTargets(self.currentposition, 'position')

	def updateCurrentPosition(self):
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
		center = self.mosaic.getFakeParameter()
		shift = {}
		for axis in ('x','y'):
			shift[axis] = stagepos[axis] - center[axis]

		## this is unscaled and relative to center of mosaic image
		delta = self.mosaic.positionByCalibration(shift)
		moshape = self.mosaic.mosaicshape
		pos = moshape[0]/2+delta[0], moshape[1]/2+delta[1]
		pos = self.mosaic.scaled(pos)
		vcoord = pos[1],pos[0]
		### this is a list of targets, in this case, one target
		self.currentposition = [vcoord]

	def displayDatabaseTargets(self):
		self.logger.info('Getting targets from database...')
		self.targetsFromDatabase()
		self.displayTargets()

	def displayTargets(self):
		if self.mosaicimage is None:
			self.logger.error('Create mosaic image before displaying targets')
			return
		self.logger.info('Displaying targets...')
		donetargets = []
		self.displayedtargetdata = {}
		targets = {}
		for type in ('acquisition','focus'):
			targets[type] = []
			for id, targetlists in self.targetmap.items():
				targetlist = targetlists[type]
				for targetdata in targetlist:
					tile = self.tilemap[id]
					#tilepos = self.mosaic.getTilePosition(tile)
					r,c = self.targetToMosaic(tile, targetdata)
					vcoord = c,r
					if vcoord not in self.displayedtargetdata:
						self.displayedtargetdata[vcoord] = []
					if targetdata['status'] in ('done', 'aborted'):
						donetargets.append(vcoord)
						self.displayedtargetdata[vcoord].append(targetdata)
					elif targetdata['status'] in ('new','processing'):
						targets[type].append(vcoord)
						self.displayedtargetdata[vcoord].append(targetdata)
					else:
						# other status ignored (mainly NULL)
						pass
			self.setTargets(targets[type], type)
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
		n = 0
		for type in ('acquisition','focus'):
			n += len(targets[type])
		ndone = len(donetargets)
		self.logger.info('displayed %s targets (%s done)' % (n+ndone, ndone))

	def getMosaicImageList(self, targetlist):
		self.logger.debug('in getMosaicImageList')
		if not targetlist['mosaic']:
			self.logger.debug('target list not mosaic')
			raise RuntimeError('TargetListData for mosaic ImageListData should have mosaic=True')
		if self.mosaicimagelist and self.mosaicimagelist['targets'] is targetlist:
			### same targetlist we got before
			self.logger.debug('same targets')
			return self.mosaicimagelist
		self.logger.debug('new image list data')

		### clear mosaic here
		self.clearTiles()

		self.mosaicimagelist = data.ImageListData(session=self.session, targets=targetlist)
		self.logger.debug('publishing new mosaic image list')
		self.publish(self.mosaicimagelist, database=True, dbforce=True)
		self.logger.debug('published new mosaic image list')
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
		self.logger.debug('creating MosaicTileData for image %s' % (imagedata.dbid,))
		tiledata = data.MosaicTileData(image=imagedata, list=imagelist, session=self.session)
		self.logger.debug('publishing MosaicTileData')
		self.publish(tiledata, database=True)
		self.logger.debug('published MosaicTileData')
		self.addTile(imagedata)
		if self.settings['mosaic image on tile change']:
			self.createMosaicImage()
		self.logger.debug('Image data processed')

	def hasMosaicImage(self):
		if None in (self.mosaicimage, self.mosaicimagescale):
			return False
		return True

	def publishMosaicImage(self):
		if not self.hasMosaicImage():
			self.logger.info('Generate a mosaic image before saving it')
			return
		self.logger.info('Saving mosaic image data')
		mosaicimagedata = data.MosaicImageData()
		mosaicimagedata['session'] = self.session
		mosaicimagedata['list'] = self.mosaicimagelist
		mosaicimagedata['image'] = self.mosaicimage
		mosaicimagedata['scale'] = self.mosaicimagescale
		filename = 'mosaic'
		lab = self.mosaicimagelist['targets']['label']
		if lab:
			filename = filename + '_' + lab
		dim = self.mosaicimagescale
		filename = filename + '_' + str(dim)
		mosaicimagedata['filename'] = filename
		self.publish(mosaicimagedata, database=True)
		self.mosaicimagedata = mosaicimagedata
		self.logger.info('Mosaic saved')

	def researchMosaicTileData(self):
		tilequery = data.MosaicTileData(session=self.session, list=data.ImageListData())
		mosaictiles = self.research(datainstance=tilequery)
		mosaiclists = {}
		for tile in mosaictiles:
			list = tile['list']
			label = '(no label)'
			if list['targets'] is not None:
				if list['targets']['label']:
					label = list['targets']['label']
			key = '%s:  %s' % (list.dbid, label)
			if key not in mosaiclists:
				mosaiclists[key] = []
			mosaiclists[key].append(tile)
		self.mosaicselectionmapping = mosaiclists
		return mosaiclists

	def getMosaicNames(self):
		self.researchMosaicTileData()
		return self.mosaicselectionmapping.keys()

	def loadMosaicTiles(self, mosaicname):
		self.logger.info('Clearing mosaic')
		self.clearTiles()
		self.logger.info('Loading mosaic images')
		try:
			tiles = self.mosaicselectionmapping[mosaicname]
		except KeyError:
			raise ValueError
		self.mosaicimagelist = tiles[0]['list']
		mosaicsession = self.mosaicimagelist['session']
		ntotal = len(tiles)
		if not ntotal:
			self.logger.info('no tiles in selected list')
			return
		for i, tile in enumerate(tiles):
			# create an instance model to query
			self.logger.info('Finding image %i of %i' % (i + 1, ntotal))
			imagedata = tile['image']
			self.addTile(imagedata)
		self.reference_target = self.getReferenceTarget()
		self.logger.info('Mosaic loaded (%i of %i images loaded successfully)' % (i+1, ntotal))
		if self.settings['mosaic image on tile change']:
			self.createMosaicImage()

	def targetToMosaic(self, tile, targetdata):
		shape = tile.image.shape
		drow = targetdata['delta row']
		dcol = targetdata['delta column']
		tilepos = drow+shape[0]/2, dcol+shape[1]/2
		mospos = self.mosaic.tile2mosaic(tile, tilepos)
		scaledpos = self.mosaic.scaled(mospos)
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
		self.logger.debug('mosaicToTarget r %s, c %s' % (row, col))
		unscaled = self.mosaic.unscaled((row,col))
		tile, pos = self.mosaic.mosaic2tile(unscaled)
		shape = tile.image.shape
		drow,dcol = pos[0]-shape[0]/2, pos[1]-shape[1]/2
		imagedata = tile.imagedata
		self.logger.debug('target tile image: %s, pos: %s' % (imagedata.dbid,pos))
		return imagedata, drow, dcol

	def mosaicToTarget(self, typename, row, col):
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		### create a new target list if we don't have one already
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)
		targetdata = self.newTargetForTile(imagedata, drow, dcol, type=typename, list=self.targetlist)
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
		self.mosaicimage = self.mosaic.getMosaicImage(maxdim)
		self.mosaicimagedata = None

		self.logger.info('Displaying mosaic image')
		self.setImage(self.mosaicimage, 'Image')
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		self.setTargets([], 'region')
		self.beep()
		## if all images are now in mosaic, then do processing
		if self.imagesourcedone.isSet():
			self.autoTargetFinder()

	def clearMosaicImage(self):
		self.setImage(None, 'Image')
		self.mosaicimage = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None
		self.regionarrays = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def setCalibrationParameter(self):
		calclient = self.calclients[self.settings['calibration parameter']]
		self.mosaic.setCalibrationClient(calclient)

	def storeSquareFinderPrefs(self):
		prefs = data.SquareFinderPrefsData()
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

	def findRegions(self):
		imshape = self.mosaicimage.shape
		minsize = self.settings['min region area']
		maxsize = self.settings['max region area']
		black_on_white = self.settings['black on white']
		minsize /= 100.0
		maxsize /= 100.0
		white_on_black =  not black_on_white

		tileshape = self.mosaic.tiles[0].image.shape
		tilearea = tileshape[0] * tileshape[1]
		mosaicarea = imshape[0] * imshape[1]
		areascale = self.mosaic.scale * self.mosaic.scale
		scale = areascale * tilearea / mosaicarea
		minsize = scale * minsize
		maxsize = scale * maxsize

		velimit = self.settings['ve limit']
		mint = self.settings['min threshold']
		maxt = self.settings['max threshold']
		# make zero border
		pad = 2
		self.mosaicimage[:pad] = 0
		self.mosaicimage[-pad:] = 0
		self.mosaicimage[:,:pad] = 0
		self.mosaicimage[:,-pad:] = 0
		regions,image = libCV.FindRegions(self.mosaicimage, minsize, maxsize, 0, 0, white_on_black,black_on_white)
		self.regionarrays = []
		displaypoints = []
		for i,region in enumerate(regions):
			regionarray = region['regionBorder']
			self.logger.info('Region %d has %d points' % (i, regionarray.shape[1]))
			## reduce to 20 points
			regionarray = libCV.PolygonVE(regionarray, velimit)
			regionarray.transpose()
			self.regionarrays.append(regionarray)

			regiondisplaypoints = self.transpose_points(regionarray)
			displaypoints.extend(regiondisplaypoints)

		self.setTargets(displaypoints, 'region', block=False)

	def autoSpacingAngle(self):
		imagedata = self.imagemap[self.imagemap.keys()[0]]
		tem = imagedata['scope']['tem']
		cam = imagedata['camera']['ccdcamera']
		ht = imagedata['scope']['high tension']

		# transforming from target mag
		targetpresetname = self.settings['targetpreset']
		targetpreset = self.presetsclient.getPresetByName(targetpresetname)
		mag1 = targetpreset['magnification']
		dim1 = targetpreset['dimension']['x']
		bin1 = targetpreset['binning']['x']
		fulldim = dim1 * bin1
		p1 = (0,fulldim)

		# transforming into mag of atlas
		mag2 = imagedata['scope']['magnification']
		bin2 = imagedata['camera']['binning']['x']

		print 'p2p', tem, cam, ht, mag1, mag2, p1
		p2 = self.calclients['stage position'].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		print 'P2', p2
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		print 'bin', p2
		# atlas scaling
		atlasscale = self.mosaic.scale
		p2 = atlasscale*p2[0], atlasscale*p2[1]
		print 'atlas', p2
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		print 'overlap', p2
		
		spacing = numarray.hypot(*p2)
		angle = numarray.arctan2(*p2)
		angle = math.degrees(angle)
		return spacing,angle

	def makeRaster(self):
		shape = self.mosaicimage.shape
		spacing = self.settings['raster spacing']
		angledeg = self.settings['raster angle']
		anglerad = math.radians(angledeg)
		rasterpoints = raster.createRaster(shape, spacing, anglerad)
		fullrasterset = set()
		'''
		boxes = []
		for region in self.regionarrays:
			box = self.regionToBox(region, spacing)
			boxes.append(box)
		'''

		# if self.regionarrays is empty, check for manually picked region
		#if not self.regionarrays:
		if len(self.regionarrays) < 2:
			manualregion = self.panel.getTargetPositions('region')
			if manualregion:
				manualregion = self.transpose_points(manualregion)
				manualregionarray = numarray.array(manualregion)
				self.regionarrays = [manualregionarray]

		## this block will reduce the number of raster points
		if self.regionarrays:
			print 'original raster', len(rasterpoints)
			region = self.regionarrays[0]
			gmin0 = gmax0 = region[0][0]
			gmin1 = gmax1 = region[0][1]
			for region in self.regionarrays:
				min0 = min(region[:,0])
				min1 = min(region[:,1])
				max0 = max(region[:,0])
				max1 = max(region[:,1])
				if min0 < gmin0:
					gmin0 = min0
				if min1 < gmin1:
					gmin1 = min1
				if max0 > gmax0:
					gmax0 = max0
				if max1 > gmax1:
					gmax1 = max1
			gmin0 -= (2*spacing)
			gmin1 -= (2*spacing)
			gmax0 += (2*spacing)
			gmax1 += (2*spacing)
			newrasterpoints = []
			for rasterpoint in rasterpoints:
				if gmin0 < rasterpoint[0] < gmax0:
					if gmin1 < rasterpoint[1] < gmax1:
						newrasterpoints.append(rasterpoint)
			rasterpoints = newrasterpoints
			print 'reduced raster', len(rasterpoints)

		#for region in self.regionarrays:
		for region in self.regionarrays:
			### keep raster points that are either in the polygon
			### or near the polygon
			fillraster = polygon.pointsInPolygon(rasterpoints, region)
			fullrasterset = fullrasterset.union(fillraster)

			leftovers = list(set(rasterpoints).difference(fillraster))
			print 'leftover raster', len(leftovers)

			distances = polygon.distancePointsToPolygon(leftovers, region)
			isnear = distances < spacing
			#nearraster = numarray.compress(distances<spacing, rasterpoints)
			nearraster = []
			for i, point in enumerate(leftovers):
				if isnear[i]:
					nearraster.append(point)
			fullrasterset = fullrasterset.union(nearraster)
		# set is unordered, so use original rasterpoints for order
		self.fullraster = []
		for point in rasterpoints:
			if point in fullrasterset:
				self.fullraster.append(point)

		fullrasterdisplay = self.transpose_points(self.fullraster)
		self.setTargets(fullrasterdisplay, 'acquisition', block=True)

	def regionToBox(self, region, space):
		minr,minc = region[0]
		maxr,maxc = region[0]
		for r,c in region:
			if r < minr:
				minr = r
			if c < minc:
				minc = c
			if r > maxr:
				maxr = r
			if c > maxc:
				maxc = c
		minr -= space
		maxr += space
		minc -= space
		maxc += space
		box = [(minr,minc),(minr,maxc),(maxr,maxc),(maxr,minc)]
		return box

	def makeFocusTarget(self):
		if not self.regionarrays:
			return
		biggestregion = self.regionarrays[0]
		biggestregionlen = len(biggestregion)
		for region in self.regionarrays:
			newlen = len(region)
			if newlen > biggestregionlen:
				biggestregionlen = newlen
				biggestregion = region

		#center = polygon.getPolygonCenter(biggestregion)

		box = self.regionToBox(biggestregion, 0)
		print 'box', box
		p0 = box[0]
		p1 = box[2]
		center = (p1[0]+p0[0])/2, (p1[1]+p0[1])/2
		print 'center', center

		focusdisplay = self.transpose_points([center])
		print 'display'
		self.setTargets(focusdisplay, 'focus', block=True)

	def findSquares(self):
		if self.mosaicimagedata is None:
			message = 'You must save the current mosaic image before finding squares on it.'
			self.logger.error(message)
			return
		original_image = self.mosaicimagedata['image']

		message = 'finding squares'
		self.logger.info(message)

		sigma = self.settings['lpf']['sigma']
		kernel = convolver.gaussian_kernel(sigma)
		self.convolver.setKernel(kernel)
		image = self.convolver.convolve(image=original_image)
		self.setImage(image.astype(numarray.Float32), 'Filtered')

		## threshold grid bars
		squares_thresh = self.settings['threshold']
		image = imagefun.threshold(image, squares_thresh)
		self.setImage(image.astype(numarray.Float32), 'Thresholded')

		## find blobs
		blobs = imagefun.find_blobs(original_image, image,
																self.settings['blobs']['border'],
																self.settings['blobs']['max'],
																self.settings['blobs']['max size'],
																self.settings['blobs']['min size'])

		## use stats to find good ones
		mean_min = self.settings['blobs']['min mean']
		mean_max = self.settings['blobs']['max mean']
		std_min = self.settings['blobs']['min stdev']
		std_max = self.settings['blobs']['max stdev']
		targets = []
		prefs = self.storeSquareFinderPrefs()
		rows, columns = image.shape
		for blob in blobs:
			row = blob.stats['center'][0]
			column = blob.stats['center'][1]
			mean = blob.stats['mean']
			std = blob.stats['stddev']
			stats = data.SquareStatsData(prefs=prefs, row=row, column=column, mean=mean, stdev=std)
			if (mean_min <= mean <= mean_max) and (std_min <= std <= std_max):
				stats['good'] = True
				## create a display target
				targets.append((column,row))
			else:
				stats['good'] = False
			self.publish(stats, database=True)

		## display them
		self.setTargets(targets, 'acquisition')

		message = 'found %s squares' % (len(targets),)
		self.logger.info(message)

	def autoTargetFinder(self):
		self.imagesourcedone.clear()

		self.logger.info('Finding regions...')
		self.findRegions()
		self.logger.info('Filling regions with raster...')
		self.makeRaster()
		self.logger.info('Making focus target...')
		self.makeFocusTarget()
		## user part
		if self.settings['user check']:
			self.setStatus('user input')
			self.logger.info('Waiting for user to check targets...')
			self.panel.submitTargets()
			self.userpause.clear()
			self.userpause.wait()
			self.panel.targetsSubmitted()
		self.setStatus('processing')

		## get targets from image
		targets = {}
		targets['acquisition'] = self.panel.getTargetPositions('acquisition')
		targets['focus'] = self.panel.getTargetPositions('focus')
		
		## new target list
		if targets['acquisition'] or targets['focus']:
			targetlist = self.newTargetList()
			self.publish(targetlist, database=True, dbforce=True)
		else:
			self.setStatus('idle')
			return

		for type in ('focus', 'acquisition'):
			n = len(targets[type])
			self.logger.info('Publishing %d %s targets...' % (n, type))
			for t in targets[type]:
				## convert to TargetData
				c,r = t
				imagedata, drow, dcol = self._mosaicToTarget(r, c)
				targetdata = self.newTargetForTile(imagedata, drow, dcol, type=type, list=targetlist)
				self.publish(targetdata, database=True, dbforce=True)

		self.publish(targetlist, pubevent=True)
		self.setStatus('idle')
