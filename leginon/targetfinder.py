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
import numarray.ma as ma
import numarray.nd_image as nd
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.MosaicClickTargetFinder
import os
import libCV
import math
import polygon
import raster
import presets
import time
try:
	set = set
except NameError:
	import sets
	set = sets.Set

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
		lastnumber = self.lastTargetNumber(image=imagedata, session=self.session)
		number = lastnumber + 1
		for imagetarget in imagetargets:
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(imagedata, drow, dcol, type=typename, list=targetlist, number=number)
			self.publish(targetdata, database=True)
			number += 1

	def displayPreviousTargets(self, targetlistdata):
		targets = self.researchTargets(list=targetlistdata)
		done = []
		acq = []
		foc = []
		halfrows = targetlistdata['image']['camera']['dimension']['y'] / 2
		halfcols = targetlistdata['image']['camera']['dimension']['x'] / 2
		for target in targets:
			drow = target['delta row']
			dcol = target['delta column']
			x = dcol + halfcols
			y = drow + halfrows
			disptarget = x,y
			if target['status'] in ('done', 'aborted'):
				done.append(disptarget)
			elif target['type'] == 'acquisition':
				acq.append(disptarget)
			elif target['type'] == 'focus':
				foc.append(disptarget)
		self.setTargets(acq, 'acquisition', block=True)
		self.setTargets(foc, 'focus', block=True)
		self.setTargets(done, 'done', block=True)

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.settings['ignore images']:
			return

		# check if there is already a target list for this image
		# or any other versions of this image (all from same target/preset)
		# exclude sublists (like rejected target lists)
		qtarget = imagedata['target']
		try:
			pname = imagedata['preset']['name']
			qpreset = data.PresetData(name=pname)
		except:
			qpreset = None
		qimage = data.AcquisitionImageData(target=qtarget, preset=qpreset)
		previouslists = self.researchTargetLists(image=qimage, sublist=False)
		if previouslists:
			# I hope you can only have one target list on an image, right?
			targetlist = previouslists[0]
			db = False
			self.logger.info('Existing target list on this image...')
			self.displayPreviousTargets(targetlist)
		else:
			# no previous list, so create one and fill it with targets
			targetlist = self.newTargetList(image=imagedata, queue=self.settings['queue'])
			db = True

		self.findTargets(imagedata, targetlist)
		self.logger.debug('Publishing targetlist...')

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

	def clearTargets(self,targettype):
		self.setTargets([], targettype, block=False)

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
		'axis ratio': 2.0,
		've limit': 50,
		'find section options':'Limit by Sections',
#		'black on white': False,
#		'limit region in sections': False,
		'section area': 99.0,
		'section axis ratio': 1.0,
		'max sections': 5,
		'adjust section area': 0.0,
		'section display': False,
		'raster spacing': 50,
		'raster angle': 0,
		# unlike other targetfinders, no wait is default
		'wait for done': False,
		#'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'create on tile change': 'all',
		'autofinder': False,
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
		self.mosaiccreated = threading.Event()
		self.presetsclient = presets.PresetsClient(self)

		self.mosaic.setCalibrationClient(self.calclients[parameter])

		self.existing_targets = {}
		self.clearTiles()

		self.reference_target = None

		self.onesectionarea = None
		self.oldonesectionarea1 = None		
		self.regionarrays = []
		self.regionellipses = []
		self.regionimage = None

		if self.__class__ == MosaicClickTargetFinder:
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		if self.settings['create on tile change'] == 'final':
			self.logger.debug('create final')
			self.createMosaicImage()
			self.logger.debug('done create final')
		if self.settings['autofinder']:
			self.logger.debug('auto target finder')
			self.autoTargetFinder()
			self.logger.debug('done auto target finder')

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
		if self.settings['autofinder']:
			return

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
		self.mosaicimage = self.mosaic.getMosaicImage(maxdim)
		self.mosaicimagedata = None

		self.logger.info('Displaying mosaic image')
		self.setImage(self.mosaicimage, 'Image')
		self.logger.info('image displayed, displaying targets...')
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		self.logger.info('targets displayed, setting region []...')
		self.setTargets([], 'region')
		self.logger.info('did that')
		self.beep()

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

	def reduceRegions(self,regions,axisratiolimits,velimit,sectionimage = None):
			regionarrays = []
			regionellipses = []
			displaypoints = []
			self.regionpolygon = []
			for i,region in enumerate(regions):
				regionpolygon = region['regionEllipse']
				regionaxismajor = regionpolygon[2]
				regionaxisminor = regionpolygon[3]
				axisratio = regionaxismajor/regionaxisminor
				if axisratio > axisratiolimits[0] and axisratio < axisratiolimits[1]:
					overlap = False
					regionrow = int(regionpolygon[0])
					regioncol = int(regionpolygon[1])
					for j,regionellipse in enumerate(regionellipses):
						halfminor = 0.5*regionellipse[3]
						if regionrow > regionellipse[0]-halfminor and regionrow < regionellipse[0]+halfminor and regioncol > regionellipse[1]-halfminor and regioncol < regionellipse[1]+halfminor:
							overlap = True
							break
					insidesections = False
					if sectionimage != None:
						if sectionimage[(regionrow,regioncol)] == 1:
							insidesections = True
					else:
						insidesections = True
					if not overlap and insidesections:
						regionellipse = region['regionEllipse']
						regionarray = region['regionBorder']
#						self.logger.info('Region %d has %d points' % (i, regionarray.shape[1]))
						## reduce to 20 points
						regionarray = libCV.PolygonVE(regionarray, velimit)
						regionarray.transpose()
						regionarrays.append(regionarray)
						regionellipses.append(regionellipse)
					
						regiondisplaypoints = self.transpose_points(regionarray)
						displaypoints.extend(regiondisplaypoints)				
						regionphi = regionpolygon[4]
						#print regionrow,regioncol,regionaxismajor,regionaxisminor,regionphi
			
			return regionarrays,regionellipses,displaypoints
	
	def regionsByLabel(self,image,mint,maxt,minsize,maxsize):
		imshape = image.shape

		sigma = 3.0
		smooth=nd.gaussian_filter(image,sigma)
		masked_region = ma.masked_inside(smooth,mint,maxt)
		regionimage = masked_region.mask()
		base=nd.generate_binary_structure(2,2)
		iteration = 3
		regionimage=nd.binary_erosion(regionimage,structure=base,iterations=iteration)
		regionlabel,nlabels = nd.label(regionimage)

		ones = numarray.ones(imshape)
		if nlabels > 0:
			regionareas = nd.sum(ones,regionlabel,range(1,nlabels+1))
		else:
			regionareas = []
		if nlabels == 1:
			regionareas = [regionareas]

		ngoodregion = 0
		newregionimage = numarray.zeros(imshape)
		for i, area in enumerate(regionareas):
			if area < minsize*0.2 or area > maxsize:
				continue
			else:
				ngoodregion += 1
				newregionimage += numarray.where(regionlabel==(i+1),1,0)

#		finalregionimage=nd.binary_fill_holes(newregionimage,structure=base)
		finalregionimage = newregionimage
		finalregionlabel,ngoodregion = nd.label(finalregionimage)

		if ngoodregion > 0:
			regioncenters = nd.center_of_mass(ones,finalregionlabel,range(1,ngoodregion+1))
		else:
			regioncenters = []
		if ngoodregion == 1:
			regioncenters = [regioncenters]
				
		return finalregionimage,ngoodregion,regioncenters
		
	def regionsFromCenters(self,centers,maxsize):	
		halfedge = math.sqrt(maxsize)/(2*(1+math.sqrt(2.0)))
		halfbox = math.sqrt(maxsize)/2
		regionimage = numarray.zeros(self.mosaicimage.shape)
		regionarrays=[]
		for center in centers:
			polygon = [
					[center[0]-halfedge,center[1]-halfbox],
					[center[0]+halfedge,center[1]-halfbox],
					[center[0]+halfbox,center[1]-halfedge],
					[center[0]+halfbox,center[1]+halfedge],
					[center[0]+halfedge,center[1]+halfbox],
					[center[0]-halfedge,center[1]+halfbox],
					[center[0]-halfbox,center[1]+halfedge],
					[center[0]-halfbox,center[1]-halfedge]
				]
			regionarray = numarray.array(polygon,numarray.Float32)
			regionarrays.append(regionarray)
		return regionarrays
		
	def findRegions(self):
		imshape = self.mosaicimage.shape
		self.regionarrays = []
		self.regionellipses = []
		self.regionimage = numarray.zeros(imshape)
		maxsize = self.settings['max region area']
		minsize = self.settings['min region area']
		onesectionarea1 = self.settings['section area']
		sectionaxisratio = float(self.settings['section axis ratio'])
		maxsection = self.settings['max sections']
		displaysection = self.settings['section display']
		findsectionoption = self.settings['find section options']
		modifyarea = self.settings['adjust section area']

		newareasetting = False
		if self.oldonesectionarea1 == None or self.oldonesectionarea1 != self.settings['section area'] or modifyarea < 0.01:
			newareasetting = True
		self.oldonesectionarea1 = onesectionarea1

		if findsectionoption == 'Sections Only':
			sectiononly = True
			limitbysection = False
		else:
			if findsectionoption == 'Limit by Sections':
				limitbysection = True
				sectiononly = False
			else:
				limitbysection = False
				sectiononly = False		

		minsize /= 100.0
		maxsize /= 100.0
		onesectionarea = onesectionarea1 / 100.0
		modifyarea = modifyarea / 100.0

		tileshape = self.mosaic.tiles[0].image.shape
		tilearea = tileshape[0] * tileshape[1]
		mosaicarea = imshape[0] * imshape[1]
		areascale = self.mosaic.scale * self.mosaic.scale
		scale = areascale * tilearea / mosaicarea
		minsize = scale * minsize
		maxsize = scale * maxsize
		onesectionarea = scale * onesectionarea

		if findsectionoption =='Regions from Centers':
			manualcenters = self.panel.getTargetPositions('region')
			if manualcenters:
				manualcenters = self.transpose_points(manualcenters)
			maxsizepixel = maxsize * mosaicarea
			self.regionarrays = self.regionsFromCenters(manualcenters,maxsizepixel)
			self.regionellipses = manualcenters
			return

		velimit = self.settings['ve limit']
		mint = self.settings['min threshold']
		maxt = self.settings['max threshold']
		axisratiolimit = self.settings['axis ratio']
		
		# make zero border
		pad = 2
		self.mosaicimage[:pad] = 0
		self.mosaicimage[-pad:] = 0
		self.mosaicimage[:,:pad] = 0
		self.mosaicimage[:,-pad:] = 0
		t00=time.time()
		print "-------------"
		
		# get background stats
		background = numarray.where(self.mosaicimage>maxt,1,0)
		backgroundlabel,nlabels = nd.label(background)
		bkgrndmean = nd.mean(self.mosaicimage,labels=backgroundlabel)
		bkgrndstddev = nd.standard_deviation(self.mosaicimage,labels=backgroundlabel)
		t01=time.time()
		print "---%5.1f-----background mean %f, stddev %f" % ((t01-t00),bkgrndmean, bkgrndstddev)
				
		#refresh to setting if not auto adjust
		if self.onesectionarea == None or newareasetting:
			self.onesectionarea = onesectionarea

		tolerance = 0.5
		onesectionmin = self.onesectionarea*(1-tolerance)
		multisections=self.onesectionarea*maxsection*(1+tolerance)

		sectiondisplaypoints=[]
		sectionarrays = []
		sectionellipses = []
		
#		Find Section with simple thresholding and Label in numarray.nd_image for now until
#		better segamentation is available for sections that connects to the edge

#		if limitbysection or sectiononly:
		uselibCV = False
		if uselibCV and (limitbysection or sectiononly):
			
			#find sections
			count = 0	
			maxt1 = bkgrndmean+2*bkgrndstddev
			mosaicmax = self.mosaicimage.max()
			stepmaxt = 0.49*(mosaicmax - maxt1)
			stepscale = 0.8
			
			axisratiomax = sectionaxisratio * maxsection
			axisratiomin = sectionaxisratio / maxsection
			axisratiolimits = [axisratiomin,axisratiomax]

			while len(sectionarrays) == 0 and maxt1 < mosaicmax:
				count += 1
				minsize1 = onesectionmin
				maxsize1 = multisections
				m = numarray.clip(self.mosaicimage, mint, maxt1)
				regions,image = libCV.FindRegions(m, minsize1, maxsize1, 0, 0, False,True)
				sectionarrays,sectionellipses,sectiondisplaypoints = self.reduceRegions(regions,axisratiolimits,velimit,None)
				minsize1 = stepscale*onesectionmin
				maxt1 += stepmaxt

			self.logger.info('found %i sections after %i iterations' % (len(sectionarrays),count))
			
		if len(sectiondisplaypoints) == 0:
			if uselibCV and (not limitbysection):
				# rough section by threshold only
				masked_section = ma.masked_inside(self.mosaicimage,mint,maxt)
				sectionimage = masked_section.mask()
				nlabel = 1
			else:
				# good section as image only - smooth,threshold,size limit etc.
				minsizepixels = onesectionmin * mosaicarea
				maxsizepixels = multisections * mosaicarea
				sectionimage, nsection,sectionellipses = self.regionsByLabel(self.mosaicimage,mint,maxt,minsizepixels,maxsizepixels)
				self.logger.info('use sectionimage for rastering and found %d good sections' %nsection)
		else:
			sectionimage = polygon.plotPolygons(imshape,sectionarrays)
			nonmissingregion = numarray.where(self.mosaicimage==0,0,1)
			sectionimage = sectionimage*nonmissingregion
		
		# get section stats
		sectionlabel,nlabels = nd.label(sectionimage)

		# skip everything if no section found
		if nlabels == 0:
			return
		sectionarea = sectionimage.sum()
		sectionmean = nd.mean(self.mosaicimage,labels=sectionlabel)
#		sectionstddev = nd.standard_deviation(self.mosaicimage,labels=sectionlabel)
		sectionareanum = sectionarea / (self.onesectionarea * mosaicarea)
		sectionareaint = int(round(sectionareanum))
		
		if abs(sectionareanum-sectionareaint) < modifyarea:
			self.onesectionarea = float(sectionarea) /(sectionareaint * mosaicarea)
			areapercenttile = 100 * self.onesectionarea /scale
			self.logger.info('modify per-section area to %f for next round' %areapercenttile)
		t02=time.time()
		print "----%5.1f----section num %d mean %f" % ((t02-t01),sectionareaint, sectionmean)
		
		if not (limitbysection or sectiononly):
			sectionimage = None
		else:
			self.regionimage = sectionimage
		
		if sectiononly:
			regionarrays = sectionarrays
			regionellipses = sectionellipses
			displaypoints = sectiondisplaypoints
		else:
			
			# find tissue
		
			if modifyarea > 0.0001:
				nregionmin = max(len(sectionarrays),sectionareaint)
			else:
				nregionmin = max(len(sectionarrays),1)

				
			tissuecontrast = (sectionmean-mint)/abs(mint-sectionmean)
			
			if tissuecontrast >0:
				black_on_white = True
				white_on_black = False
			else:
				black_on_white = False
				white_on_black = True
		
			maxt2 = sectionmean+bkgrndstddev*tissuecontrast

			count = 0
			regionarrays = []
			displaypoints = []
			stepscale = 0.2
			while len(regionarrays) < nregionmin and maxt2*tissuecontrast > sectionmean*tissuecontrast:
				count += 1
				avgt = (mint+maxt2)/2
				mint2a = avgt-(maxt2-mint)*tissuecontrast/2
				maxt2a = avgt+(maxt2-mint)*tissuecontrast/2
				m = numarray.clip(self.mosaicimage, mint2a, maxt2a)
				regions,image = libCV.FindRegions(m, minsize, maxsize, 0, 0, white_on_black,black_on_white)
				regionarrays,regionellipses,displaypoints = self.reduceRegions(regions,[1.0,self.settings['axis ratio']],velimit,sectionimage)
				minsize = stepscale*minsize
				maxt2 = maxt2-stepscale*bkgrndstddev*tissuecontrast
				if minsize*mosaicarea < 4:
					break
		
			self.logger.info('found %i regions after %i iterations' % (len(regionarrays),count))
			t03=time.time()
			print "----%5.1f----tissue" % ((t03-t02),)
			if displaysection:
				displaypoints.extend(sectiondisplaypoints)

		self.regionarrays = regionarrays
		self.regionellipses = regionellipses

		self.setTargets(displaypoints, 'region', block=False)
			
	def clearRegions(self):
		imshape = self.mosaicimage.shape
		self.regionarrays = []
		self.regionimage = None
		self.clearTargets('region')

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

		p2 = self.calclients['modeled stage position'].pixelToPixel(tem, cam, ht, mag1, mag2, p1)
		# bin
		p2 = p2[0]/float(bin2), p2[1]/float(bin2)
		# atlas scaling
		atlasscale = self.mosaic.scale
		p2 = atlasscale*p2[0], atlasscale*p2[1]
		# overlap
		overlap = self.settings['raster overlap']
		overlapscale = 1.0 - overlap/100.0
		p2 = overlapscale*p2[0], overlapscale*p2[1]
		
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

		#if self.regionarrays is not defined, make it an empty array
		try:
			len(self.regionarrays)
		except TypeError:
			self.regionarrays=[]

		# if self.regionarrays is empty, check for manually picked region
		#if not self.regionarrays:
		if len(self.regionarrays) < 1 and self.settings['find section options']!='Regions from Centers':
			manualregion = self.panel.getTargetPositions('region')
			if manualregion:
				manualregion = self.transpose_points(manualregion)
				manualregionarray = numarray.array(manualregion)
				self.regionarrays = [manualregionarray]

		if len(self.regionarrays) > 0:
			rasterpoints = self.insideRegionArrays(rasterpoints,spacing)
		else:
			rasterpoints = self.insideRegionImage(rasterpoints)

		fullrasterdisplay = self.transpose_points(rasterpoints)
		self.setTargets(fullrasterdisplay, 'acquisition', block=True)

	def insideRegionImage(self, rasterpoints):
		results = []
		for point in rasterpoints:
			row = int(round(point[0]))
			col = int(round(point[1]))
			if row < 0 or row >= self.regionimage.shape[0]:
				continue
			if col < 0 or col >= self.regionimage.shape[1]:
				continue
			if self.regionimage[row,col]:
				results.append(point)
		return results

	def insideRegionArrays(self, rasterpoints,spacing):
		fullrasterset = set()

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
			if len(region) > 1:
				distances = polygon.distancePointsToPolygon(leftovers, region)
			else:
			# handle the case for one point in the region
				regionlist = region.tolist()
				regionlist =[(regionlist[0][0],regionlist[0][1]),(regionlist[0][0]+1,regionlist[0][1]+1)]
				newregion = numarray.array(regionlist)
				distances = polygon.distancePointsToPolygon(leftovers, newregion)
				
			isnear = distances < spacing
			#nearraster = numarray.compress(distances<spacing, rasterpoints)
			nearraster = []
			for i, point in enumerate(leftovers):
				if isnear[i]:
					nearraster.append(point)
			fullrasterset = fullrasterset.union(nearraster)
		# set is unordered, so use original rasterpoints for order
		fullraster = []
		for point in rasterpoints:
			if point in fullrasterset:
				fullraster.append(point)

		return fullraster


	def makeFocusTarget(self):
		if not self.regionellipses:
			return
		middle = len(self.regionellipses) / 2
		middleregion = self.regionellipses[middle]
		center = middleregion[0],middleregion[1]
		
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
		#if targets['acquisition'] or targets['focus']:
		targetlist = self.newTargetList()
		self.publish(targetlist, database=True, dbforce=True)
		##### commented out so it will still publish,
		#####   even if empty target list
		#else:
		#	self.setStatus('idle')
		#	return

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
