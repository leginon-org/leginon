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
import imagewatcher
import mosaic
import Mrc
import threading
import uidata
import node
import EM
import targethandler

class TargetFinder(imagewatcher.ImageWatcher, targethandler.TargetHandler):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [
																							event.TargetListDoneEvent] + EM.EMClient.eventinputs
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [
																							event.ImageTargetListPublishEvent] + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		self.targetlistevents = {}
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation,
																				**kwargs)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.emclient = EM.EMClient(self)

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
		targetlist = self.newTargetList()
		for imagedata in images:
			## now read the image, replace FileReference
			imagedata['image'] = imagedata['image'].read()
			self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		self.publish(targetlist, database=True, dbforce=True, pubevent=True)
		if self.wait_for_done.get():
			self.waitForTargetListDone()

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

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.ignore_images.get():
			return
		targetlist = self.newTargetList(image=imagedata)
		self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		self.logger.debug('publishing targetlist')
		self.publish(targetlist, database=True, pubevent=True)
		self.logger.debug('published targetlist %s' % (targetlist.dbid,))
		if self.wait_for_done.get():
			self.waitForTargetListDone()

	def makeTargetListEvent(self, targetlistdata):
		'''
		Creates a threading event to be waited on for target list data.
		'''
		tlistid = targetlistdata.dmid
		self.targetlistevents[tlistid] = {}
		self.targetlistevents[tlistid]['received'] = threading.Event()
		self.targetlistevents[tlistid]['status'] = 'waiting'

	def waitForTargetListDone(self):
		'''
		Waits until theading events of all target list data are cleared.
		'''
		for tid, teventinfo in self.targetlistevents.items():
			self.logger.info('%s waiting for %s' % (self.name, tid))
			teventinfo['received'].wait()
			self.logger.info('%s done waiting for %s' % (self.name, tid))
		self.targetlistevents.clear()
		self.logger.info('%s done waiting' % (self.name,))

	def notifyUserSubmit(self):
		message = 'waiting for you to submit targets'
		self.usersubmitmessage = self.messagelog.information(message)
		node.beep()

	def unNotifyUserSubmit(self):
		try:
			self.usersubmitmessage.clear()
		except:
			pass

	def handleTargetListDone(self, targetlistdoneevent):
		'''
		Receives a target list done event and sets the threading event.
		'''
		targetlistid = targetlistdoneevent['targetlistid']
		status = targetlistdoneevent['status']
		self.logger.info('Got target list done event, setting threading event %s'
											% (targetlistid,))
		if targetlistid in self.targetlistevents:
			self.targetlistevents[targetlistid]['status'] = status
			self.targetlistevents[targetlistid]['received'].set()
		self.confirmEvent(targetlistdoneevent)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Messages')

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.wait_for_done = uidata.Boolean('Wait for another node to process targets before declaring image process done', True, 'rw', persist=True)
		self.ignore_images = uidata.Boolean('Ignore Images', False, 'rw', persist=True)

		container = uidata.LargeContainer('Target Finder')
		container.addObject(self.messagelog, position={'expand': 'all'})
		container.addObjects((self.wait_for_done,self.ignore_images))

		self.uicontainer.addObject(container)

class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def findTargets(self, imdata, targetlist):
		## check if targets already found on this image
		previous = self.researchTargets(image=imdata)
		if previous:
			self.logger.warning('There are %s existing targets for this image'
													% (len(previous),))
			if self.preventrepeat.get():
				self.logger.error('You are not allowed to submit targets again')
				return

		# XXX would be nice to display existing targets too

		# display image
		self.clickimage.setTargets([])
		self.clickimage.setImage(imdata['image'])
		self.clickimage.imagedata = imdata

		# user now clicks on targets
		self.notifyUserSubmit()
		self.userpause.clear()
		self.logger.info('Waiting for user to select targets...')
		self.userpause.wait()
		self.unNotifyUserSubmit()
		self.logger.info('Done waiting')
		self.targetsFromClickImage(self.clickimage, 'focus', targetlist)
		self.targetsFromClickImage(self.clickimage, 'acquisition', targetlist)

	def submitTargets(self):
		self.userpause.set()

	def defineUserInterface(self):
		TargetFinder.defineUserInterface(self)

		self.clickimage = uidata.TargetImage('Clickable Image', None, 'rw')
		self.clickimage.addTargetType('acquisition', [], (0,255,0))
		self.clickimage.addTargetType('focus', [], (0,0,255))
		self.clickimage.addTargetType('done', [], (255,0,0))
		self.clickimage.addTargetType('position', [], (255,255,0))

		submitmethod = uidata.Method('Submit Targets', self.submitTargets)
		self.preventrepeat = uidata.Boolean('Do not allow submit if already submitted on this image', True, 'rw', persist=True)

		container = uidata.LargeContainer('Click Target Finder')
		container.addObjects((self.clickimage, submitmethod, self.preventrepeat))

		self.uicontainer.addObject(container)

class MosaicClickTargetFinder(ClickTargetFinder):
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
		self.mosaic = mosaic.EMMosaic(self.calclients['stage position'])
		self.mosaicimagelist = None
		self.mosaicimage = None
		self.mosaicimagescale = None
		self.currentposition = []

		self.mosaic.setCalibrationClient(self.calclients['stage position'])

		self.existing_targets = {}
		self.clearTiles()

		if self.__class__ == MosaicClickTargetFinder:
			self.defineUserInterface()
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.setStatusMessage('Target list done')
		### XXX should we clear self.mosaicimagelist here???
		#self.tileListToDatabase()
		self.clearTiles()
		self.outputEvent(event.MosaicDoneEvent())
		self.setStatusMessage('Mosaic is done, notification sent')

	def getTargetDataList(self, typename):
		displayedtargetdata = {}
		targetsfromimage = self.clickimage.getTargetType(typename)
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
		self.setStatusMessage('Sumbiting targets')
		self.getTargetDataList('acquisition')
		self.getTargetDataList('focus')
		self.publish(self.targetlist, pubevent=True)
		self.setStatusMessage('Targets submitted')

	def clearTiles(self):
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		self.targetlist = None
		if hasattr(self, 'autocreate') and self.autocreate.get():
			self.clearMosaicImage()

	def addTile(self, imagedata):
		self.logger.debug('addTile image: %s' % (imagedata.dbid,))
		imid = imagedata.dbid
		if imid in self.tilemap:
			self.setStatusMessage('Image already in mosaic')
			return

		self.setStatusMessage('Adding image to mosaic')
		newtile = self.mosaic.addTile(imagedata)
		self.tilemap[imid] = newtile
		self.imagemap[imid] = imagedata
		targets = self.researchTargets(image=imagedata)
		if targets and self.targetlist is None:
			self.targetlist = targets[0]['list']
		self.targetmap[imid] = targets
		self.setStatusMessage('Image added to mosaic')

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			targets = self.researchTargets(image=imagedata)
			### set my target list to same as first target found
			if targets and self.targetlist is None:
				self.targetlist = targets[0]['list']
			self.targetmap[id] = targets

	def uiRefreshCurrentPosition(self):
		self.updateCurrentPosition()
		self.clickimage.setTargetType('position', self.currentposition)

	def updateCurrentPosition(self):
		try:
			image = self.imagemap.values()[0]
		except:
			self.logger.exception('Need tiles and mosaic image')
			return
		try:
			stagepos = self.emclient.getScope()['stage position']
		except EM.ScopeUnavailable:
			stagepos = None

		if stagepos is None:
			self.currentposition = []
			self.logger.exception('could not get current position')
			return
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
		self.setStatusMessage('getting targets from database')
		self.targetsFromDatabase()
		self.displayTargets()

	def displayTargets(self):
		if self.mosaicimage is None:
			self.setStatusMessage('create mosaic image before displaying targets')
			return
		self.setStatusMessage('displaying targets')
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
		self.clickimage.setTargetType('acquisition', targets)
		self.clickimage.setTargetType('done', donetargets)
		self.updateCurrentPosition()
		self.clickimage.setTargetType('position', self.currentposition)
		n = len(targets)
		ndone = len(donetargets)
		self.setStatusMessage('displayed %s targets (%s done)' % (n+ndone, ndone))

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
		self.setStatusMessage('Processing inbound image data')
		### create a new imagelist if not already done
		targets = imagedata['target']['list']
		imagelist = self.getMosaicImageList(targets)
		self.setStatusMessage('creating MosaicTileData')
		self.logger.debug('creating MosaicTileData for image %s' % (imagedata.dbid,))
		tiledata = data.MosaicTileData(image=imagedata, list=imagelist, session=self.session)
		self.logger.debug('publishing MosaicTileData')
		self.publish(tiledata, database=True)
		self.logger.debug('published MosaicTileData')
		self.addTile(imagedata)
		if self.autocreate.get():
			self.createMosaicImage()
		self.setStatusMessage('Image data processed')

	def publishMosaicImage(self):
		if None in (self.mosaicimage, self.mosaicimagescale):
			self.setStatusMessage('generate a mosaic image before publishing')
			return
		self.setStatusMessage('Publishing mosaic image data')
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
		self.setStatusMessage('Mosaic published')

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

	def updateMosaicSelection(self):
		self.setStatusMessage('Updating mosaic selection')
		self.researchMosaicTileData()
		self.mosaicselection.set(self.mosaicselectionmapping.keys(), 0)
		self.setStatusMessage('Mosaic selection updated')

	def mosaicTilesFromDatabase(self):
		self.setStatusMessage('Clearing mosaic')
		self.clearTiles()
		self.setStatusMessage('Loading mosaic images')
		key = self.mosaicselection.getSelectedValue()
		tiles = self.mosaicselectionmapping[key]
		self.mosaicimagelist = tiles[0]['list']
		mosaicsession = self.mosaicimagelist['session']
		ntotal = len(tiles)
		if not ntotal:
			self.setStatusMessage('no tiles in selected list')
			return
		for i, tile in enumerate(tiles):
			# create an instance model to query
			self.setStatusMessage('Finding image %i of %i' % (i + 1, ntotal))
			imagedata = tile['image']
			self.addTile(imagedata)
		self.setStatusMessage('Mosaic loaded (%i of %i images loaded successfully)' % (i+1, ntotal))
		if self.autocreate.get():
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
		self.setStatusMessage('creating mosaic image')

		if self.scaleimage.get():
			maxdim = self.maxdimension.get()
		else:
			maxdim = None
		self.mosaicimagescale = maxdim
		self.mosaicimage = self.mosaic.getMosaicImage(maxdim)

		self.setStatusMessage('Displaying mosaic image')
		self.clickimage.setImage(self.mosaicimage)
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		node.beep()

	def clearMosaicImage(self):
		self.clickimage.setImage(None)
		self.mosaicimage = None
		self.mosaicimagescale = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def uiSetCalibrationParameter(self, value):
		if not hasattr(self, 'uicalibrationparameter'):
			return value
		parameter = self.uicalibrationparameter.getSelectedValue(value)
		calclient = self.calclients[parameter]
		self.mosaic.setCalibrationClient(calclient)
		return value

	def setStatusMessage(self, message):
		self.statusmessage.set(message)

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)

		self.wait_for_done.set(False)

		self.statusmessage = uidata.String('Current status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		### tiles management
		tilescontainer = uidata.Container('Mosaic Tiles')

		clearmethod = uidata.Method('Reset Tile List', self.clearTiles)

		# load tiles from db
		loadcontainer = uidata.Container('Tile Lists Published in This Session')
		self.mosaicselection = uidata.SingleSelectFromList('Mosaic', [], 0)
		self.updateMosaicSelection()

		refreshmethod = uidata.Method('Refresh', self.updateMosaicSelection)
		loadmethod = uidata.Method('Load', self.mosaicTilesFromDatabase)
		loadcontainer.addObject(refreshmethod, position={'position':(0,0)})
		loadcontainer.addObject(self.mosaicselection, position={'position':(0,1)})
		loadcontainer.addObject(loadmethod, position={'position':(0,2)})

		tilescontainer.addObject(clearmethod, position={'position':(0,0)})
		tilescontainer.addObject(loadcontainer, position={'position':(1,0), 'span':(1,2)})

		### Mosaic Image Management
		mosaicimagecont = uidata.Container('Mosaic Image')

		parameters = self.calclients.keys()
		self.uicalibrationparameter = uidata.SingleSelectFromList(
																				'Calibration Parameter',
																				parameters,
																				parameters.index('stage position'),
																				callback=self.uiSetCalibrationParameter,
																				persist=True)
		self.scaleimage = uidata.Boolean('Scale Image', True, 'rw', persist=True)
		self.maxdimension = uidata.Integer('Maximum Dimension', 512, 'rw',
																				persist=True)
		createmethod = uidata.Method('Create Mosaic Image From Tile List',
																	self.createMosaicImage)
		pubmethod = uidata.Method('Publish Current Mosaic Image',
															self.uiPublishMosaicImage)
		self.autocreate = uidata.Boolean(
									'Create mosaic image whenever tile list changes', True, 'rw')

		mosaicimagecont.addObject(self.uicalibrationparameter, position={'position':(0,0), 'span':(1,2)})
		mosaicimagecont.addObject(self.scaleimage, position={'position':(1,0)})
		mosaicimagecont.addObject(self.maxdimension, position={'position':(1,1)})
		mosaicimagecont.addObject(createmethod, position={'position':(2,0), 'span':(1,2)})
		mosaicimagecont.addObject(self.autocreate, position={'position':(3,0), 'span':(1,2)})
		mosaicimagecont.addObject(pubmethod, position={'position':(4,0), 'span':(1,2)})

		### Targets
		targetcont = uidata.Container('Targeting')
		refreshtargets = uidata.Method('Refresh Targets',
																		self.displayDatabaseTargets)
		refreshposition = uidata.Method('Refresh Current Position',
																		self.uiRefreshCurrentPosition)
		targetcont.addObject(refreshtargets, position={'position':(0,0)})
		targetcont.addObject(refreshposition, position={'position':(0,1)})

		container = uidata.LargeContainer('Mosaic Click Target Finder')
		container.addObjects((statuscontainer, tilescontainer, mosaicimagecont, targetcont))
		self.uicontainer.addObject(container)

