# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/robotscreening.py,v $
# $Revision: 1.1 $
# $Name: not supported by cvs2svn $
# $Date: 2005-03-23 19:30:28 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import math
import numarray
import threading
import align
import data
import event
import instrument
import node
import presets
import calibrationclient
import targethandler
import gui.wx.AtlasViewer

class TargetError(Exception):
	pass

class Grids(object):
	def __init__(self):
		self.grids = []

	def addGrid(self, grid):
		self.grids.append(grid)

	def addGrids(self, grids):
		self.grids += grids

	def setGrids(self, grids):
		self.grids = grids

	def clearGrids(self):
		self.grids = []

	def hasGridID(self, gridid):
		for grid in self.grids:
			if grid.gridid == gridid:
				return True
		return False

	def getGridByID(self, gridid):
		for grid in self.grids:
			if grid.gridid == gridid:
				return grid
		return None

	def getGridInsertions(self):
		labels = []
		gridids = []
		for grid in self.grids:
			gridids.append(grid.gridid)
		gridids.sort()
		for gridid in gridids:
			numbers = []
			for insertion in grid.insertions:
				numbers.append(insertion.number)
			numbers.sort()
			for number in numbers:
				labels.append((gridid, number))
		return labels

class Grid(object):
	def __init__(self, gridid=None):
		self.gridid = gridid
		self.insertions = []

	def addInsertion(self, insertion):
		self.insertions.append(insertion)

	def addInsertions(self, insertions):
		self.insertions += insertions

	def setInsertions(self, insertions):
		self.insertions = insertsions

	def clearInsertions(self):
		self.insertions = []

	def hasInsertionNumber(self, number):
		for insertion in self.insertions:
			if insertion.number == number:
				return True
		return False

	def getInsertionByNumber(self, number):
		for insertion in self.insertions:
			if insertion.number == number:
				return insertion
		return None

	def getInsertionNumbers(self):
		numbers = []
		for insertion in self.insertions:
			numbers.append(insertion.number)
		numbers.sort()
		return numbers

class Insertion(object):
	def __init__(self, number=None):
		self.number = number
		self.images = []

	def addImage(self, image):
		self.images.append(image)

	def addImages(self, images):
		self.images += images

	def setImages(self, images):
		self.images = images

	def clearImage(self):
		self.images = []

class Image(object):
	def __init__(self, data=None, location=None):
		self.data = data
		self.location = location
		self.targets = []
		self.row = None
		self.column = None
		self.width = None
		self.height = None
		self.halfwidth = None
		self.halfheight = None

	def addTarget(self, target):
		self.targets.append(target)

	def addTargets(self, targets):
		self.targets += targets

	def setTargets(self, targets):
		self.targets = targets

	def clearTargets(self):
		self.targets = []

class RobotAtlasTargetFinder(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.AtlasViewer.Panel
	eventinputs = (
		node.Node.eventinputs +
		targethandler.TargetWaitHandler.eventinputs +
		presets.PresetsClient.eventinputs +
		[
			event.GridLoadedEvent
		]
	)
	eventoutputs = (
		node.Node.eventoutputs +
		targethandler.TargetWaitHandler.eventoutputs +
		presets.PresetsClient.eventoutputs +
		[
			event.QueueGridsEvent,
			event.UnloadGridEvent,
		]
	)
	def __init__(self, id, session, managerlocation, **kwargs):
		self.grids = Grids()
		self.insertion = None

		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		targethandler.TargetWaitHandler.__init__(self)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.presetsclient = presets.PresetsClient(self)

		calibrationclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient,
			'stage position': calibrationclient.StageCalibrationClient,
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient,
			'image beam shift': calibrationclient.ImageBeamShiftCalibrationClient,
		}
		self.calibrationclients = {}
		for i, clientclass in calibrationclients.items():
			self.calibrationclients[i] = clientclass(self)

		self.addEventInput(event.GridLoadedEvent, self.onGridLoaded)

		self.start()

	def onGridLoaded(self, evt):
		# ...
		if evt['request node'] != self.name:
			return

		if evt['grid'] is None or evt['grid']['grid ID'] is None:
			self.logger.warning('Unknown loaded grid')
			return
		gridid = evt['grid']['grid ID']

		status = evt['status']
		if status == 'ok':
			self.logger.info('Robot loaded grid ID %d' % gridid)
			self.processGridData(evt['grid'])
		elif status == 'invalid':
			self.logger.warning('Grid ID %d not in current tray' % gridid)
		elif status == 'failed':
			self.logger.warning('Robot failed to load grid ID %d' % gridid)
		else:
			self.logger.warning('Unknown status for grid ID %d' % gridid)

	def getAtlases(self):
		self.insertion = None
		self.setImage(None, 'Image')
		self.setTargets([], 'Acquisition')
		self.updateGrids()
		self.panel.getAtlasesDone()

	def queryAtlases(self):
		querydata = data.MosaicTileData(session=self.session)
		tiledatalist = self.research(datainstance=querydata)
		imagedatarefs = {}
		for tiledata in tiledatalist:
			imagedataref = tiledata.special_getitem('image', dereference=False)
			if tiledata['list'].dbid in imagedatarefs:
				imagedatarefs[tiledata['list'].dbid].append(imagedataref)
			else:
				imagedatarefs[tiledata['list'].dbid] = [imagedataref]
		return imagedatarefs

	def validateImageData(self, imagedata):
		if imagedata is None:
			self.logger.warning('Cannot load image from database, ignoring image')
			return False
		elif imagedata['grid'] is None:
			self.logger.warning('No grid information, ignoring image (DBID %d)'
													% imagedata.dbid)
			return False
		elif imagedata['grid']['grid ID'] is None:
			self.logger.warning('No grid ID, ignoring image (DBID %d)'
													% imagedata.dbid)
			return False
		elif imagedata['grid']['insertion'] is None:
			msg = 'No insertion number, ignoring image (Grid ID %d, DBID %d)'
			msg %= (imagedata.dbid, imagedata['grid']['grid ID'])
			self.logger.warning(msg)
			return False
		return True

	def updateGrids(self):
		imagedatarefs = self.queryAtlases()
		for dbid, refs in imagedatarefs.items():
			gridid = None
			number = None
			imagedatalist = []
			for ref in refs:
				imagedata = self.researchDBID(ref.dataclass, ref.dbid, readimages=False)
				if not self.validateImageData(imagedata):
					continue
				if gridid is None:
					gridid = imagedata['grid']['grid ID']
				elif imagedata['grid']['grid ID'] != gridid:
					self.logger.warning('Grid ID in image list changed, ignoring image')
					continue
				if number is None:
					number = imagedata['grid']['insertion']
				elif imagedata['grid']['insertion'] != number:
					self.logger.warning('Insertion number in image list changed, ignoring image')
					continue
				imagedatalist.append(imagedata)

			if not imagedatalist:
				continue
			grid = self.grids.getGridByID(gridid)
			if grid is None:
				grid = Grid(gridid)
				self.grids.addGrid(grid)
			if grid.hasInsertionNumber(number):
				self.logger.warning('Duplicate insertion, ignoring images')
				continue
			insertion = Insertion(number)
			for imagedata in imagedatalist:
				insertion.addImage(Image(imagedata))
			grid.addInsertion(insertion)

	def updateAtlasTargets(self):
		targets = self.panel.getTargetPositions('Acquisition')
		if self.insertion is not None:
			self.insertion.images.reverse()
			for image in self.insertion.images:
				image.clearTargets()
				for target in list(targets):
					l = image.location
					column, row = target
					if (row >= l[0][0] and row <= l[0][1] and
							column >= l[1][0] and column <= l[1][1]):
						targets.remove(target)
						target = (row - l[0][0], column - l[1][0])
						image.addTarget(target)
			self.insertion.images.reverse()

	def setAtlas(self, gridid, number):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(gridid)
		self.insertion = grid.getInsertionByNumber(number)
		self.updateAtlasImage()
		self.panel.setAtlasDone()

	def updateImages(self, images):
		for image in images:
			self.updateImage(image)

	def updateImage(self, image):
		image.width = image.data['preset']['dimension']['x']
		image.height = image.data['preset']['dimension']['y']
		targetdata = image.data['target']
		image.row = targetdata['delta row']
		image.column = targetdata['delta column']
		image.halfwidth = int(math.ceil(image.width/2.0))
		image.halfheight = int(math.ceil(image.height/2.0))

	def getAtlasExtrema(self, images):
		minrow = None
		mincolumn = None
		maxrow = None
		maxcolumn = None
		for image in images:
			if minrow is None or (image.row - image.halfheight) < minrow:
				minrow = image.row - image.halfheight
			if mincolumn is None or (image.column - image.halfwidth) < mincolumn:
				mincolumn = image.column - image.halfwidth
			if maxrow is None or (image.row + image.halfheight) > maxrow:
				maxrow = image.row + image.halfheight
			if maxcolumn is None or (image.column + image.halfwidth) > maxcolumn:
				maxcolumn = image.column + image.halfwidth
		return ((minrow, maxrow), (mincolumn, maxcolumn))

	def updateAtlasImage(self):
		if self.insertion is None:
			self.setImage(None, 'Image')
			self.setTargets([], 'Acquisition')
			return
		self.updateImages(self.insertion.images)
		extrema = self.getAtlasExtrema(self.insertion.images)
		shape = (extrema[0][1] - extrema[0][0], extrema[1][1] - extrema[1][0])
		atlasimage = numarray.zeros(shape, numarray.Float32)
		targets = []
		for image in self.insertion.images:
			i = image.data['image']
			l = ((image.row - image.halfheight - extrema[0][0],
						image.row + image.halfheight - extrema[0][0]),
					(image.column - image.halfwidth - extrema[1][0],
						image.column + image.halfwidth - extrema[1][0]))
			atlasimage[l[0][0]:l[0][1], l[1][0]:l[1][1]] = i
			image.location = l
			for target in image.targets:
				targets.append((target[1] + l[1][0], target[0] + l[0][0]))
		self.setImage(atlasimage, 'Image')
		self.setTargets(targets, 'Acquisition')

	def hasTargets(self, grid):
		for insertion in grid.insertions:
			for image in insertion.images:
				if image.targets:
					if not self.reacquireImage(image.data, test=True):
						raise TargetError('will not be able to acquire image')
					return True
		return False

	def getGridsWithTargets(self):
		self.updateAtlasTargets()
		grids = []
		for grid in self.grids.grids:
			if self.hasTargets(grid):
				grids.append(grid)
		return grids

	def queueGrids(self, grids):
		evt = event.QueueGridsEvent()
		evt['grid IDs'] = [grid.gridid for grid in grids]
		self.outputEvent(evt)

	def unloadGrid(self, grid):
		evt = event.UnloadGridEvent()
		evt['grid ID'] = grid.gridid
		self.outputEvent(evt)
		self.logger.info('Robot notified to unload grid ID %d' % grid.gridid)

	def submitTargets(self):
		try:
			grids = self.getGridsWithTargets()
		except TargetError, e:
			self.logger.error('Aborting, error determining target: %s' % e)
			self.panel.targetsSubmitted()
			return

		if not grids:
			self.logger.warning('No targets for reacquisition')
			self.panel.targetsSubmitted()
			return

		self.queueGrids(grids)
		self.panel.targetsSubmitted()

	def processGridData(self, griddata):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(griddata['grid ID'])
		for insertion in grid.insertions:
			if insertion == self.insertion:
				self.setTargets([], 'Acquisition')
			for image in insertion.images:
				if not image.targets:
					continue
				# acquire image and align
				image1 = image.data['image']
				imagedata = self.reacquireImage(image.data)
				if imagedata is None:
					continue
				imagedata['grid'] = griddata
				self.setImageFilename(imagedata)
				self.publish(imagedata, pubevent=True, database=True)
				image2 = imagedata['image']
				theta, shift = align.alignImages(image1, image2)
				infostring = 'Rotation: %g, shift: (%g, %g)' % ((theta,) + shift)
				self.logger.info(infostring)

				targetlist = self.newTargetList()

				try:
					scope = self.instrument.getData(data.ScopeEMData)
				except:
					self.logger.warning('Failed to access microscope, continuing')
					continue
				try:
					camera = self.instrument.getData(data.CameraEMData, image=False)
				except:
					self.logger.warning('Failed to access camera, continuing')
					continue

				presetdata = image.data['preset']

				# align targets
				shape1 = image1.shape
				shape2 = image2.shape
				for target in image.targets:
					target = align.alignTarget(target, shape1, shape2, theta, shift)
					row = target[0] - shape2[0]/2
					column = target[1] - shape2[1]/2
					targetdata = self.newTargetForImage(imagedata, row, column,
																							type='acquisition',
																							list=targetlist)
					self.publish(targetdata, database=True)

				# remove targets for this image
				image.targets = []

				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, database=True, dbforce=True, pubevent=True)

				self.waitForTargetListDone()

		self.unloadGrid(grid)

	def getLastGridInsertion(self, gridid):
		initializer = {}
		initializer['grid ID'] = gridid
		querydata = data.GridData(initializer=initializer)
		griddatalist = self.research(querydata)
		maxinsertion = -1
		griddata = None
		for gd in griddatalist:
			if gd['insertion'] > maxinsertion:
				griddata = gd
				maxinsertion = gd['insertion']
		return griddata

	def reacquireImage(self, imagedata, test=False):
		presetdata = imagedata['preset']
		targetdata = imagedata['target']

		try:
			t = 'TEM'
			self.instrument.setTEM(presetdata['tem']['name'])
			t = 'CCD Camera'
			self.instrument.setCCDCamera(presetdata['ccdcamera']['name'])
		except (ValueError, TypeError, AttributeError, KeyError):
			self.logger.error('Cannot access %s for preset' % t)
			if test:
				return False
			else:
				return None

		# TODO: user select? should be in data
		movetype = 'stage position'

		calclient = self.calibrationclients[movetype]
		target = {'row': -targetdata['delta row'],
							'col': -targetdata['delta column']}

		try:
			scopedata = calclient.transform(target,
																			targetdata['scope'], targetdata['camera'])
		except calibrationclient.NoMatrixCalibrationError, e:
			self.logger.error('No calibration for reacquisition: %s' % e)
			if test:
				return False
			else:
				return None

		if test:
			return True

		# check stage position

		emtargetdata = data.EMTargetData()
		emtargetdata['preset'] = presetdata
		emtargetdata['movetype'] = movetype
		for i in ['image shift', 'beam shift', 'stage position']:
			emtargetdata[i] = dict(scopedata[i])
		emtargetdata['target'] = targetdata

		presetname = presetdata['name']
		self.presetsclient.toScope(presetname, emtargetdata)

		errorstring = 'Image acqisition failed: %s'
		try:
			imagedata = self.instrument.getData(data.CameraImageData)
		except:
			self.logger.error(errorstring % 'cannot acquire image')
		if imagedata is None:
			return None

		# Jim says: store to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)

		# TODO: targetdata
		imagedata = data.AcquisitionImageData(initializer=imagedata,
																					preset=presetdata,
																					label=self.name)

		return imagedata

	def setImageFilename(self, imagedata):
		if imagedata['filename']:
			return
		parts = []
		rootname = self.getRootName(imagedata)
		parts.append(rootname)

		if 'grid' in imagedata and imagedata['grid'] is not None:
			if imagedata['grid']['grid ID'] is not None:
				grididstr = '%05d' % (imagedata['grid']['grid ID'],)
				parts.append(grididstr)

		listlabel = ''
		# use either dmid id or target number
		if imagedata['target'] is None or imagedata['target']['number'] is None:
			numberstr = '%05d' % (imagedata.dmid[-1],)
		else:
			numberstr = '%05d' % (imagedata['target']['number'],)
			if imagedata['target']['list'] is not None:
				listlabel = imagedata['target']['list']['label']
		if imagedata['preset'] is None:
			presetstr = ''
		else:
			presetstr = imagedata['preset']['name']
		mystr = numberstr + presetstr
		sep = '_'

		if listlabel:
			parts.append(listlabel)
		parts.append(mystr)

		filename = sep.join(parts)
		imagedata['filename'] = filename

	def getRootName(self, imagedata):
		'''
		get the root name of an image from its parent
		'''
		parent_target = imagedata['target']
		if parent_target is None:
			## there is no parent target
			## create my own root name
			return self.newRootName()

		parent_image = parent_target['image']
		if parent_image is None:
			## there is no parent image
			return self.newRootName()

		## use root name from parent image
		parent_root = parent_image['filename']
		if parent_root:
			return parent_root
		else:
			return self.newRootName()

	def newRootName(self):
		name = self.session['name']
		return name

