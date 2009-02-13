#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import calibrationclient
import leginondata
import event
import instrument
import imagewatcher
import mosaic
import threading
import node
import targethandler
from pyami import convolver, imagefun, mrc
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

try:
	set = set
except NameError:
	import sets
	set = sets.Set


class MosaicClickTargetFinder(targetfinder.ClickTargetFinder):
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
	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		targetfinder.ClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)
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
		self.mosaiccreated = threading.Event()
		self.presetsclient = presets.PresetsClient(self)

		self.mosaic.setCalibrationClient(self.calclients[parameter])

		self.existing_targets = {}
		self.clearTiles()

		self.reference_target = None

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		if self.settings['create on tile change'] == 'final':
			self.logger.debug('create final')
			self.createMosaicImage()
			self.logger.debug('done create final')

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
		try:
			if self.settings['autofinder']:
				return
		except:
			pass

		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)

		self.logger.info('Submitting targets...')
		self.getTargetDataList('acquisition')
		self.getTargetDataList('focus')
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
		if self.__class__ != MosaicClickTargetFinder:
			self.setTargets([], 'region')

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
		'''
		if not targetlist['mosaic']:
			self.logger.debug('target list not mosaic')
			raise RuntimeError('TargetListData for mosaic ImageListData should have mosaic=True')
		'''
		if self.mosaicimagelist and self.mosaicimagelist['targets'] is targetlist:
			### same targetlist we got before
			self.logger.debug('same targets')
			return self.mosaicimagelist
		self.logger.debug('new image list data')

		### clear mosaic here
		self.clearTiles()

		self.mosaicimagelist = leginondata.ImageListData(session=self.session, targets=targetlist)
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
		tiledata = leginondata.MosaicTileData(image=imagedata, list=imagelist, session=self.session)
		self.logger.debug('publishing MosaicTileData')
		self.publish(tiledata, database=True)
		self.logger.debug('published MosaicTileData')
		self.addTile(imagedata)

		if self.settings['create on tile change'] == 'all':
			self.logger.debug('create all')
			self.createMosaicImage()
			self.logger.debug('done create all')

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
		mosaicimagedata = leginondata.MosaicImageData()
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
		tilequery = leginondata.MosaicTileData(session=self.session, list=leginondata.ImageListData())
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
		if self.settings['create on tile change'] in ('all', 'final'):
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
		drow,dcol = pos[0]-shape[0]/2.0, pos[1]-shape[1]/2.0
		imagedata = tile.imagedata
		self.logger.debug('target tile image: %s, pos: %s' % (imagedata.dbid,pos))
		return imagedata, drow, dcol

	def mosaicToTarget(self, typename, row, col):
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		### create a new target list if we don't have one already
		'''
		if self.targetlist is None:
			self.targetlist = self.newTargetList()
			self.publish(self.targetlist, database=True, dbforce=True)
		'''
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
		self.mosaicimagedata = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def setCalibrationParameter(self):
		calclient = self.calclients[self.settings['calibration parameter']]
		self.mosaic.setCalibrationClient(calclient)

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
		self.setImage(image, 'Filtered')

		## threshold grid bars
		squares_thresh = self.settings['threshold']
		image = imagefun.threshold(image, squares_thresh)
		self.setImage(image, 'Thresholded')

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
			stats = leginondata.SquareStatsData(prefs=prefs, row=row, column=column, mean=mean, stdev=std)
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

