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

class TargetFinder(imagewatcher.ImageWatcher):
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + [
																							event.ImageTargetListPublishEvent]
	eventinputs = imagewatcher.ImageWatcher.eventinputs + [
																							event.TargetListDoneEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		self.targetlist = []
		self.targetlistevents = {}
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation,
																				**kwargs)
		self.addEventInput(event.TargetListDoneEvent, self.handleTargetListDone)
		self.emclient = EM.EMClient(self)

	def researchImageTargets(self, imagedata):
		'''
		Get a list of all targets that have this image as their parent.
		only want most recent versions of each
		'''
		targetquery = data.AcquisitionImageTargetData(image=imagedata)
		targets = self.research(datainstance=targetquery)

		## now filter out only the latest versions
		# map target id to latest version
		# assuming query result is ordered by timestamp, this works
		have = {}
		for target in targets:
			targetnum = target['number']
			if targetnum not in have:
				have[targetnum] = target
		havelist = have.values()
		havelist.sort(self.compareTargetNumber)
		if havelist:
			self.logger.info('Found %s targets for image'
												% (len(havelist),))
		return havelist

	def compareTargetNumber(self, first, second):
		return cmp(first['number'], second['number'])

	def lastTargetNumber(self, imagedata):
		'''
		Returns the number of the last target associated with the given image data.
		'''
		targets = self.researchImageTargets(imagedata)
		maxnumber = 0
		for target in targets:
			if target['number'] > maxnumber:
				maxnumber = target['number']
		return maxnumber

	def findTargets(self, imdata):
		'''
		Virtual function, inheritting classes implement building self.targetlist,
		a list of ImageTargetData items.
		'''
		raise NotImplementedError()

	### this needs to be done by linking images to an ImageList object
	### or something like that, data containing lists of data needs 
	### to outlawed to avoid data referencing and database storing problems
	def processImageListData(self, imagelistdata):
		if 'images' not in imagelistdata or imagelistdata['images'] is None:
			return
		for ref in imagelistdata['images']:
			imagedata = ref.getData()
			if imagedata is None:
				continue
			self.findTargets(imagedata)
		self.publishTargetList()

	def processImageData(self, imagedata):
		'''
		Gets and publishes target information of specified image data.
		'''
		if self.ignore_images.get():
			return
		self.findTargets(imagedata)
		self.publishTargetList()

	def publishTargetList(self):
		'''
		Updates and publishes the target list self.targetlist. Waits for target
		to be "done" if specified.
		'''

		self.unNotifyUserSubmit()

		## map image id to max target number in DB
		## so we don't have to query DB every iteration of the loop
		targetnumbers = {}

		## add a 'number' to the target and then publish it
		for target in self.targetlist:
			# target may have number if it was previously published
			if target['number'] is None:
				parentimage = target['image']
				## should I use dmid or dbid?
				parentid = parentimage.dmid
				if parentid in targetnumbers:
					last_targetnumber = targetnumbers[parentid]
				else:
					last_targetnumber = self.lastTargetNumber(parentimage)
					targetnumbers[parentid] = last_targetnumber

				## increment target number
				targetnumbers[parentid] += 1
				target['number'] = targetnumbers[parentid]
			self.logger.info('Publishing (%s, %s) %s' %
					(target['delta row'], target['delta column'], target['image'].dmid))
			self.publish(target, database=True)
			targetrefs.append(target.reference())

		## make a list of references to the targets
		refs = map(lambda x: x.reference(), self.targetlist)
		targetlistdata = data.ImageTargetListData(targets=refs)

		self.makeTargetListEvent(targetlistdata)

		self.publish(targetlistdata, pubevent=True)

		self.targetlist = []
		# wait for target list to be processed by other node
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
			self.logger.info('%s waiting for %s' % (self.id, tid))
			teventinfo['received'].wait()
			self.logger.info('%s done waiting for %s' % (self.id, tid))
		self.targetlistevents.clear()
		self.logger.info('%s done waiting' % (self.id,))

	def notifyUserSubmit(self):
		myname = self.id[-1]
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

	def newTargetData(self, imagedata, type, drow, dcol):
		'''
		returns a new target data object with data filled in from the image data
		'''
		imagearray = imagedata['image']
		targetdata = data.AcquisitionImageTargetData(type=type, version=0, status='new')
		targetdata['image'] = imagedata
		targetdata['scope'] = imagedata['scope']
		targetdata['camera'] = imagedata['camera']
		targetdata['preset'] = imagedata['preset']
		targetdata['type'] = type
		targetdata['delta row'] = drow
		targetdata['delta column'] = dcol
		return targetdata

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)

		self.messagelog = uidata.MessageLog('Messages')

		# turn off data queuing by default
		self.uidataqueueflag.set(False)

		self.wait_for_done = uidata.Boolean('Wait for another node to process targets before declaring image process done', True, 'rw', persist=True)
		self.ignore_images = uidata.Boolean('Ignore Images', False, 'rw', persist=True)

		container = uidata.LargeContainer('Target Finder')
		container.addObjects((self.messagelog, self.wait_for_done,self.ignore_images))

		self.uicontainer.addObject(container)

class ClickTargetFinder(TargetFinder):
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		if self.__class__ == ClickTargetFinder:
			self.defineUserInterface()
			self.start()

	def findTargets(self, imdata):
		## check if targets already found on this image
		previous = self.researchImageTargets(imdata)
		if previous:
			self.logger.warning('There are %s existing targets for this image'
													% (len(previous),))
			self.targetlist = previous
			if self.preventrepeat.get():
				self.logger.error('You are not allowed to submit targets again')
				return

		# display image
		self.clickimage.setTargets([])
		self.clickimage.setImage(imdata['image'])
		self.clickimage.imagedata = imdata

		# user now clicks on targets
		self.notifyUserSubmit()
		self.userpause.clear()
		self.logger.info('Waiting for user to select targets...')
		self.userpause.wait()
		self.logger.info('Done waiting')
		self.targetlist += self.getTargetDataList('focus')
		self.targetlist += self.getTargetDataList('acquisition')

	def submitTargets(self):
		self.userpause.set()

	def getTargetDataList(self, typename):
		targetlist = []
		for imagetarget in self.clickimage.getTargetType(typename):
			column, row = imagetarget
			imagedata = self.clickimage.imagedata
			imagearray = imagedata['image']
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetData(imagedata, typename, drow, dcol)
			targetlist.append(targetdata)
		return targetlist

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
		self.mosaicdata = None
		self.mosaicimage = None
		self.mosaicdata = None
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
		self.tileListToDatabase()
		self.clearTiles()
		self.outputEvent(event.MosaicDoneEvent())
		self.setStatusMessage('Mosaic is done, notification sent')

	def submitTargets(self):
		self.setStatusMessage('Sumbiting targets')
		targetlist = self.getTargetDataList('acquisition')
		self.targetlist.extend(targetlist)
		self.publishTargetList()
		self.setStatusMessage('Targets submitted')

	def clearTiles(self):
		self.idlist = []
		self.tilemap = {}
		self.imagemap = {}
		self.targetmap = {}
		self.mosaic.clear()
		if hasattr(self, 'autocreate') and self.autocreate.get():
			self.clearMosaicImage()

	def addTile(self, imagedata):
		print 'THIS SHOULD NOT USE DBID'
		print 'THIS SHOULD USE A NEW DATA TYPE FOR TILEDATA THAT LINKS TO MOSAICDATA AND IMAGEDATA'
		print 'MOSAICDATA SHOULD NOT HAVE ID LIST'
		imid = imagedata.dbid
		if imid in self.tilemap:
			self.setStatusMessage('Image already in mosaic')
			return

		self.setStatusMessage('Adding image to mosaic')
		self.idlist.append(imid)
		newtile = self.mosaic.addTile(imagedata)
		self.tilemap[imid] = newtile
		self.imagemap[imid] = imagedata
		targets = self.researchImageTargets(imagedata)
		self.targetmap[imid] = targets
		self.setStatusMessage('Image added to mosaic')

		## generate new MosaicData
		initializer = {'data IDs': list(self.idlist)}
		self.mosaicdata = data.MosaicData(initializer=initializer)

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			targets = self.researchImageTargets(imagedata)
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
		stagepos = self.emclient.getScope()['stage position']
		# for testing with mosaic 151 from 04apr02b
		# this is the center of image 207 (the center of 3 images)
		#stagepos = {'x': -0.000547287, 'y': 6.08626e-5}

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

	def processImageData(self, imagedata):
		'''
		different from ClickTargetFinder because findTargets is
		not per image, instead we have submitTargets.
		'''
		self.setStatusMessage('Processing inbound image data')
		self.addTile(imagedata)
		if self.autocreate.get():
			self.createMosaicImage()
		self.setStatusMessage('Image data processed')

	def tileListToDatabase(self):
		if not self.idlist:
			self.setStatusMessage('Mosaic is empty')
			return
		self.setStatusMessage('Publishing mosaic data')
		self.publish(self.mosaicdata, database=True)

	def publishMosaicImage(self):
		if None in (self.mosaicdata, self.mosaicimage, self.mosaicimagescale):
			self.setStatusMessage('generate a mosaic image before publishing')
			return
		self.setStatusMessage('Publishing mosaic image data')
		mosaicimagedata = data.MosaicImageData()
		mosaicimagedata['mosaic'] = self.mosaicdata
		mosaicimagedata['image'] = self.mosaicimage
		mosaicimagedata['scale'] = self.mosaicimagescale
		self.publish(mosaicimagedata, database=True)
		self.setStatusMessage('Mosaic published')

	def updateMosaicSelection(self):
		self.setStatusMessage('Updating mosaic selection')
		instance = data.MosaicData(session=self.session)
		self.setStatusMessage('Finding mosaics')
		mosaics = self.research(datainstance=instance)
		self.mosaicselectionmapping = {}
		print 'SHOULD NOT USE DBID, SHOULD USE TIMESTAMP OR SOMETHING PEOPLE CAN UNDERSTAND'
		for mosaic in mosaics:
			key = str(mosaic['session']['name']) + ' ' + str(mosaic.dbid)
			self.mosaicselectionmapping[key] = mosaic
		self.mosaicselection.set(self.mosaicselectionmapping.keys(), 0)
		self.setStatusMessage('Mosaic selection updated')

	def mosaicTilesFromDatabase(self):
		self.setStatusMessage('Loading mosaic')
		key = self.mosaicselection.getSelectedValue()
		try:
			self.mosaicdata = self.mosaicselectionmapping[key]
		except KeyError:
			self.setStatusMessage('Invalid mosaic selected')
			return
		self.setStatusMessage('Clearing mosaic')
		self.clearTiles()
		mosaicsession = self.mosaicdata['session']
		self.setStatusMessage('Finding mosaic images and data')
		ntotal = len(self.mosaicdata['data IDs'])
		for i, dataid in enumerate(self.mosaicdata['data IDs']):
			# create an instance model to query
			self.setStatusMessage('Finding image %i of %i' % (i + 1, ntotal))
			imagedata = self.researchDMID(data.AcquisitionImageData, dataid)
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
		unscaled = self.mosaic.unscaled((row,col))
		tile, pos = self.mosaic.mosaic2tile(unscaled)
		shape = tile.image.shape
		drow,dcol = pos[0]-shape[0]/2, pos[1]-shape[1]/2
		imagedata = tile.imagedata
		targetdata = self.newTargetData(imagedata, typename, drow, dcol)
		return targetdata

	def createMosaicImage(self):
		if self.mosaicdata is None:
			self.setStatusMessage('need tiles to create mosaic image')
			return

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

	def getTargetDataList(self, typename):
		targetlist = []
		displayedtargetdata = {}
		targetsfromimage = self.clickimage.getTargetType(typename)
		for t in targetsfromimage:
			## if displayed previously (not clicked)...
			if t in self.displayedtargetdata and self.displayedtargetdata[t]:
				targetdata = self.displayedtargetdata[t].pop()
			else:
				c,r = t
				targetdata = self.mosaicToTarget(typename, r, c)
			targetlist.append(targetdata)
			if t not in displayedtargetdata:
				displayedtargetdata[t] = []
			displayedtargetdata[t].append(targetdata)
		self.displayedtargetdata = displayedtargetdata
		return targetlist

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
		publishtilelist = uidata.Method('Publish Tile List',
																		self.tileListToDatabase)

		# load tiles from db
		loadcontainer = uidata.Container('Tile Lists Published in This Session')
		self.mosaicselection = uidata.SingleSelectFromList('Mosaic', [], 0)
		self.updateMosaicSelection()

		refreshmethod = uidata.Method('Refresh', self.updateMosaicSelection)
		loadmethod = uidata.Method('Load', self.mosaicTilesFromDatabase)
		loadcontainer.addObjects((refreshmethod, self.mosaicselection, loadmethod))

		tilescontainer.addObjects((clearmethod, publishtilelist, loadcontainer))


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

		mosaicimagecont.addObjects((self.uicalibrationparameter, self.scaleimage,
																self.maxdimension, createmethod,
																self.autocreate, pubmethod))

		### Targets
		targetcont = uidata.Container('Targeting')
		refreshtargets = uidata.Method('Refresh Targets',
																		self.displayDatabaseTargets)
		refreshposition = uidata.Method('Refresh Current Position',
																		self.uiRefreshCurrentPosition)
		targetcont.addObjects((refreshtargets, refreshposition))

		container = uidata.LargeContainer('Mosaic Click Target Finder')
		container.addObjects((statuscontainer, tilescontainer, mosaicimagecont, targetcont))
		self.uicontainer.addObject(container)

