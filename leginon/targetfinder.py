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
import convolver
import imagefun
import numarray
import gui.wx.TargetFinder
import gui.wx.ClickTargetFinder
import gui.wx.MosaicClickTargetFinder

class TargetFinder(imagewatcher.ImageWatcher, targethandler.TargetHandler):
	panelclass = gui.wx.TargetFinder.Panel
	settingsclass = data.TargetFinderSettingsData
	defaultsettings = {
		'wait for done': False,
		'ignore images': False,
	}
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
			num = imagedata['image'].read()
			imagedata.__setitem__('image', num, force=True)
			self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		self.publish(targetlist, database=True, dbforce=True, pubevent=True)
		if self.settings['wait for done']:
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

	def publishTargets(self, typename, targetlist):
		imagearray = self.imagedata['image']
		lastnumber = self.lastTargetNumber(image=self.imagedata,
																				session=self.session)
		number = lastnumber + 1
		for imagetarget in self.panel.getTargets(typename):
			column, row = imagetarget
			drow = row - imagearray.shape[0]/2
			dcol = column - imagearray.shape[1]/2

			targetdata = self.newTargetForImage(self.imagedata,
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
		targetlist = self.newTargetList(image=imagedata)
		self.findTargets(imagedata, targetlist)
		self.makeTargetListEvent(targetlist)
		self.logger.debug('publishing targetlist')
		self.publish(targetlist, database=True, pubevent=True)
		self.logger.debug('published targetlist %s' % (targetlist.dbid,))
		if self.settings['wait for done']:
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
		self.usersubmitmessage = self.logger.info(message)
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

class ClickTargetFinder(TargetFinder):
	panelclass = gui.wx.ClickTargetFinder.Panel
	settingsclass = data.ClickTargetFinderSettingsData
	defaultsettings = {
		'wait for done': False,
		'ignore images': False,
		'no resubmit': True,
	}
	def __init__(self, id, session, managerlocation, **kwargs):
		TargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.userpause = threading.Event()

		self.typenames = ['acquisition', 'focus', 'done', 'position']
		self.panel.addTargetTypes(self.typenames)

	def findTargets(self, imdata, targetlist):
		## check if targets already found on this image
		previous = self.researchTargets(image=imdata)
		if previous:
			self.logger.warning('There are %s existing targets for this image'
													% (len(previous),))
			if self.settings['no resubmit']:
				self.logger.error('You are not allowed to submit targets again')
				return

		# XXX would be nice to display existing targets too

		# display image
		map(self.panel.setTargets, zip(self.typenames, [[]]*len(self.typenames)))
		self.setImage(imdata['image'])
		#self.clickimage.imagedata = imdata
		self.imagedata = imdata

		# user now clicks on targets
		self.notifyUserSubmit()
		self.userpause.clear()
		self.logger.info('Waiting for user to select targets...')
		self.userpause.wait()
		self.unNotifyUserSubmit()
		self.logger.info('Done waiting')
		#self.targetsFromClickImage(self.clickimage, 'focus', targetlist)
		#self.targetsFromClickImage(self.clickimage, 'acquisition', targetlist)
		self.publishTargets('focus', targetlist)
		self.publishTargets('acquisition', targetlist)

	def submitTargets(self):
		self.userpause.set()

class MosaicClickTargetFinder(ClickTargetFinder):
	panelclass = gui.wx.MosaicClickTargetFinder.Panel
	settingsclass = data.MosaicClickTargetFinderSettingsData
	defaultsettings = {
		'wait for done': False,
		'ignore images': False,
		'no resubmit': True,
		# maybe not
		'calibration parameter': 'stage position',
		'scale image': True,
		'scale size': 512,
		'mosaic image on tile change': True,
		'size': 5,
		'sigma': 1.4,
		'threshold': 100.0,
		'border': 0,
		'max blobs': 100,
		'min blob size': 10,
		'max blob size': 10000,
		'min blob mean': 1000,
		'max blob mean': 20000,
		'min blob stdev': 10,
		'max blob stdev': 500,
	}

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
		self.mosaicimagedata = None
		self.convolver = convolver.Convolver()
		self.currentposition = []

		self.mosaic.setCalibrationClient(self.calclients['stage position'])

		self.existing_targets = {}
		self.clearTiles()

		if self.__class__ == MosaicClickTargetFinder:
			self.defineUserInterface()
			self.start()

	# not complete
	def handleTargetListDone(self, targetlistdoneevent):
		self.setStatus('Target list done')
		### XXX should we clear self.mosaicimagelist here???
		#self.tileListToDatabase()
		self.clearTiles()
		self.outputEvent(event.MosaicDoneEvent())
		self.setStatus('Mosaic is done, notification sent')

	def getTargetDataList(self, typename):
		displayedtargetdata = {}
		targetsfromimage = self.panel.getTargets(typename)
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
		self.setStatus('Sumbiting targets')
		self.getTargetDataList('acquisition')
		self.getTargetDataList('focus')
		self.publish(self.targetlist, pubevent=True)
		self.setStatus('Targets submitted')

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
			self.setStatus('Image already in mosaic')
			return

		self.setStatus('Adding image to mosaic')
		newtile = self.mosaic.addTile(imagedata)
		self.tilemap[imid] = newtile
		self.imagemap[imid] = imagedata
		targets = self.researchTargets(image=imagedata)
		if targets and self.targetlist is None:
			self.targetlist = targets[0]['list']
		self.targetmap[imid] = targets
		self.setStatus('Image added to mosaic')

	def targetsFromDatabase(self):
		for id, imagedata in self.imagemap.items():
			targets = self.researchTargets(image=imagedata)
			### set my target list to same as first target found
			if targets and self.targetlist is None:
				self.targetlist = targets[0]['list']
			self.targetmap[id] = targets

	def uiRefreshCurrentPosition(self):
		self.updateCurrentPosition()
		self.panel.setTargets('position', self.currentposition)

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
		self.setStatus('getting targets from database')
		self.targetsFromDatabase()
		self.displayTargets()

	def displayTargets(self):
		if self.mosaicimage is None:
			self.setStatus('create mosaic image before displaying targets')
			return
		self.setStatus('displaying targets')
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
		self.panel.setTargets('acquisition', targets)
		self.panel.setTargets('done', donetargets)
		self.updateCurrentPosition()
		self.panel.setTargets('position', self.currentposition)
		n = len(targets)
		ndone = len(donetargets)
		self.setStatus('displayed %s targets (%s done)' % (n+ndone, ndone))

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
		self.setStatus('Processing inbound image data')
		### create a new imagelist if not already done
		targets = imagedata['target']['list']
		imagelist = self.getMosaicImageList(targets)
		self.setStatus('creating MosaicTileData')
		self.logger.debug('creating MosaicTileData for image %s' % (imagedata.dbid,))
		tiledata = data.MosaicTileData(image=imagedata, list=imagelist, session=self.session)
		self.logger.debug('publishing MosaicTileData')
		self.publish(tiledata, database=True)
		self.logger.debug('published MosaicTileData')
		self.addTile(imagedata)
		if self.settings['mosaic image on tile change']:
			self.createMosaicImage()
		self.setStatus('Image data processed')

	def hasMosaicImage(self):
		if None in (self.mosaicimage, self.mosaicimagescale):
			return False
		return True

	def publishMosaicImage(self):
		if not self.hasMosaicImage():
			self.setStatus('generate a mosaic image before publishing')
			return
		self.setStatus('Publishing mosaic image data')
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
		self.setStatus('Mosaic published')

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
		self.setStatus('Clearing mosaic')
		self.clearTiles()
		self.setStatus('Loading mosaic images')
		try:
			tiles = self.mosaicselectionmapping[mosaicname]
		except KeyError:
			raise ValueError
		self.mosaicimagelist = tiles[0]['list']
		mosaicsession = self.mosaicimagelist['session']
		ntotal = len(tiles)
		if not ntotal:
			self.setStatus('no tiles in selected list')
			return
		for i, tile in enumerate(tiles):
			# create an instance model to query
			self.setStatus('Finding image %i of %i' % (i + 1, ntotal))
			imagedata = tile['image']
			self.addTile(imagedata)
		self.setStatus('Mosaic loaded (%i of %i images loaded successfully)' % (i+1, ntotal))
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
		self.setStatus('creating mosaic image')

		if self.settings['scale image']:
			maxdim = self.settings['scale size']
		else:
			maxdim = None
		self.mosaicimagescale = maxdim
		self.mosaicimage = self.mosaic.getMosaicImage(maxdim)
		self.mosaicimagedata = None

		self.setStatus('Displaying mosaic image')
		self.setImage(self.mosaicimage)
		## imagedata would be full mosaic image
		#self.clickimage.imagedata = None
		self.displayTargets()
		node.beep()

	def clearMosaicImage(self):
		self.setImage(None)
		self.mosaicimage = None
		self.mosaicimagescale = None
		self.mosaicimagedata = None

	def uiPublishMosaicImage(self):
		self.publishMosaicImage()

	def setCalibrationParameter(self, value):
		calclient = self.calclients[self.settings['calibration parameter']]
		self.mosaic.setCalibrationClient(calclient)

	def storeSquareFinderPrefs(self):
		prefs = data.SquareFinderPrefsData()
		prefs['image'] = self.mosaicimagedata
		prefs['lpf-size'] = self.lpfsize.get()
		prefs['lpf-sigma'] = self.lpfsigma.get()
		prefs['threshold'] = self.squares_thresh.get()
		prefs['border'] = self.border.get()
		prefs['maxblobs'] = self.maxblobs.get()
		prefs['minblobsize'] = self.minblobsize.get()
		prefs['maxblobsize'] = self.maxblobsize.get()
		prefs['mean-min'] = self.mean_min.get()
		prefs['mean-max'] = self.mean_max.get()
		prefs['std-min'] = self.std_min.get()
		prefs['std-max'] = self.std_max.get()
		self.publish(prefs, database=True)
		return prefs

	def findSquares(self):
		if self.mosaicimagedata is None:
			message = 'You must publish the current mosaic image before finding squares on it.'
			self.logger.error(message)
			return
		original_image = self.mosaicimagedata['image']

		message = 'finding squares'
		self.logger.info(message)
		self.setStatus(message)

		size = self.lpfsize.get()
		sigma = self.lpfsigma.get()
		kernel = convolver.gaussian_kernel(size, sigma)
		self.convolver.setKernel(kernel)
		image = self.convolver.convolve(image=original_image)
		self.filtered_image.set(image.astype(numarray.Float32))

		## threshold grid bars
		squares_thresh = self.squares_thresh.get()
		image = imagefun.threshold(image, squares_thresh)
		self.threshold_image.set(image.astype(numarray.Float32))

		## find blobs
		border = self.border.get()
		maxblobs = self.maxblobs.get()
		minblobsize = self.minblobsize.get()
		maxblobsize = self.maxblobsize.get()
		blobs = imagefun.find_blobs(original_image, image, border, maxblobs, maxblobsize, minblobsize)

		## use stats to find good ones
		mean_min = self.mean_min.get()
		mean_max = self.mean_max.get()
		std_min = self.std_min.get()
		std_max = self.std_max.get()
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
		self.panel.setTargets('acquisition', targets)

		message = 'found %s squares' % (len(targets),)
		self.logger.info(message)
		self.setStatus(message)

	def defineUserInterface(self):
		ClickTargetFinder.defineUserInterface(self)

		### Targets
		targetcont = uidata.Container('Targeting')
		refreshtargets = uidata.Method('Refresh Targets',
																		self.displayDatabaseTargets)
		refreshposition = uidata.Method('Refresh Current Position',
																		self.uiRefreshCurrentPosition)

		findsquarescont = uidata.Container('Square Finder')
		findsquares = uidata.Method('Find Squares', self.findSquares)

		self.lpfsize = uidata.Number('Low Pass Filter Size', 5, 'rw', persist=True, size=(4, 1))
		self.lpfsigma = uidata.Number('Low Pass Filter Sigma', 1.4, 'rw', persist=True, size=(6, 1))
		self.squares_thresh= uidata.Float('Grid Bar Threshold', 100.0, 'rw', persist=True, size=(4, 1))

		self.border = uidata.Number('Border', 0, 'rw', persist=True, size=(4, 1))
		self.maxblobs = uidata.Number('Maximum number of blobs', 100, 'rw', persist=True, size=(4, 1))
		self.minblobsize = uidata.Number('Minimum blob size', 10, 'rw', persist=True, size=(6, 1))
		self.maxblobsize = uidata.Number('Maximum blob size', 10000, 'rw', persist=True, size=(6, 1))
		meanlimits = uidata.Container('Mean Value Limits')
		self.mean_min = uidata.Number('Minimum', 1000, 'rw', persist=True)
		self.mean_max = uidata.Number('Maximum', 20000, 'rw', persist=True)
		meanlimits.addObject(self.mean_min, position={'position':(0,0)})
		meanlimits.addObject(self.mean_max, position={'position':(0,1)})

		stdlimits = uidata.Container('Standard Deviation Limits')
		self.std_min = uidata.Number('Minimum', 10, 'rw', persist=True)
		self.std_max = uidata.Number('Maximum', 500, 'rw', persist=True)
		stdlimits.addObject(self.std_min, position={'position':(0,0)})
		stdlimits.addObject(self.std_max, position={'position':(0,1)})

		self.filtered_image = uidata.Image('Filtered', None, 'r')
		self.threshold_image = uidata.Image('Thresholded', None, 'r')

		findsquarescont.addObjects((findsquares, self.lpfsize, self.lpfsigma, self.squares_thresh, self.border, self.maxblobs, self.minblobsize, self.maxblobsize, meanlimits, stdlimits, self.filtered_image, self.threshold_image))
		
		targetcont.addObject(refreshtargets, position={'position':(0,0)})
		targetcont.addObject(refreshposition, position={'position':(0,1)})
		targetcont.addObject(findsquarescont, position={'position':(1,0), 'span':(1,2)})

		container = uidata.LargeContainer('Mosaic Click Target Finder')
		container.addObjects((targetcont,))
		self.uicontainer.addObject(container)

