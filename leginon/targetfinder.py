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

class TargetFinder(imagewatcher.ImageWatcher, targethandler.TargetWaitHandler):
	panelclass = gui.wx.TargetFinder.Panel
	settingsclass = data.TargetFinderSettingsData
	defaultsettings = {
		'queue': False,
		'wait for done': True,
		'ignore images': False,
		'user check': False,
		'queue drift': False,
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

	def findTargets(self, imdata, targetlist):
		'''
		Virtual function, inheritting classes implement creating targets
		'''
		raise NotImplementedError()

	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return

		querydata = data.AcquistiionImageData(list=imagelistdata)
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
		imagearray = imagedata['image']
		lastnumber = self.lastTargetNumber(image=imagedata,
																				session=self.session)
		number = lastnumber + 1
		imagetargets = self.panel.getTargetPositions(typename)
		if not imagetargets:
			return
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata,
																					drow, dcol,
																					type=typename,
																					list=targetlist,
																					number=number)
			self.publish(targetdata, database=True)
			number += 1

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.settings['ignore images']:
			return

		# check if there is already a target list for this image
		previouslists = self.researchTargetLists(image=imagedata)
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
	targetnames = ['focus', 'acquisition']
	panelclass = gui.wx.ClickTargetFinder.Panel
	settingsclass = data.ClickTargetFinderSettingsData
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.start()

	def findTargets(self, imdata, targetlist):
		# display image
		map(self.setTargets, zip([[]]*len(self.typenames), self.typenames))
		self.setImage(imdata['image'], 'Image')
		#self.clickimage.imagedata = imdata

		# user now clicks on targets
		self.notifyUserSubmit()
		self.userpause.clear()
		self.setStatus('user input')
		self.userpause.wait()
		self.setStatus('processing')
		self.logger.info('User has submitted targets')
		for i in self.targetnames:
			self.publishTargets(imdata, i, targetlist)


class MosaicClickTargetFinder(ClickTargetFinder):
	targetnames = ['acquisition']
	panelclass = gui.wx.MosaicClickTargetFinder.Panel
	settingsclass = data.MosaicClickTargetFinderSettingsData
	defaultsettings = dict(ClickTargetFinder.defaultsettings)
	defaultsettings.update({
		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'mosaic image on tile change': True,
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

		self.mosaic.setCalibrationClient(self.calclients[parameter])

		self.existing_targets = {}
		self.clearTiles()

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.logger.info('Target list done')
		### XXX should we clear self.mosaicimagelist here???
		#self.tileListToDatabase()
		self.clearTiles()
		self.outputEvent(event.MosaicDoneEvent())
		self.logger.info('Mosaic is done, notification sent')

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

	def submitTargets(self):
		self.logger.info('Submitting targets')
		self.getTargetDataList('acquisition')
		#self.getTargetDataList('focus')
		try:
			self.publish(self.targetlist, pubevent=True)
		except node.PublishError, e:
			self.logger.error('Submitting targets failed.')
		else:
			self.logger.info('Targets submitted')

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
		targets = self.researchTargets(image=imagedata)
		if targets and self.targetlist is None:
			self.targetlist = targets[0]['list']
		self.targetmap[imid] = targets
		self.logger.info('Image added to mosaic')

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			targets = self.researchTargets(image=imagedata)
			### set my target list to same as first target found
			if targets and self.targetlist is None:
				self.targetlist = targets[0]['list']
			self.targetmap[id] = targets

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
		targets = []
		donetargets = []
		self.displayedtargetdata = {}
		for id, targetlist in self.targetmap.items():
			for targetdata in targetlist:
				tile = self.tilemap[id]
				#tilepos = self.mosaic.getTilePosition(tile)
				r,c = self.targetToMosaic(tile, targetdata)
				vcoord = c,r
				if vcoord not in self.displayedtargetdata:
					self.displayedtargetdata[vcoord] = []
				self.displayedtargetdata[vcoord].append(targetdata)
				if targetdata['status'] in ('done', 'aborted'):
					donetargets.append(vcoord)
				else:
					targets.append(vcoord)
		self.setTargets(targets, 'acquisition')
		# ...
		#self.setTargets([], 'focus')
		self.setTargets(donetargets, 'done')
		self.updateCurrentPosition()
		self.setTargets(self.currentposition, 'position')
		n = len(targets)
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

	def mosaicToTarget(self, typename, row, col):
		self.logger.debug('mosaicToTarget r %s, c %s' % (row, col))
		unscaled = self.mosaic.unscaled((row,col))
		tile, pos = self.mosaic.mosaic2tile(unscaled)
		shape = tile.image.shape
		drow,dcol = pos[0]-shape[0]/2, pos[1]-shape[1]/2
		imagedata = tile.imagedata
		self.logger.debug('target tile image: %s, pos: %s' % (imagedata.dbid,pos))
		### create a new target list if we don't have one already
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)
		targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=self.targetlist)
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
		self.beep()

	def clearMosaicImage(self):
		self.setImage(None, 'Image')
		self.mosaicimage = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None

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

	def findSquares(self):
		if self.mosaicimagedata is None:
			message = 'You must dave the current mosaic image before finding squares on it.'
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

