# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/robotscreening.py,v $
# $Revision: 1.10 $
# $Name: not supported by cvs2svn $
# $Date: 2005-04-19 16:29:27 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import math
import numarray
import numarray.nd_image
import threading
import align
import data
import event
import instrument
import node
import presets
import project
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

		projectdata = None
		try:
			projectdata = project.ProjectData()
		except project.NotConnectedError, e:
			self.logger.warning('Failed to connect to the project database: %s' % e)

		for gridid in gridids:
			if projectdata is not None:
				label = projectdata.getGridLabel(gridid)
			else:
				label = None
			if label is None:
				label = 'Grid ID %d' % gridid
			numbers = []
			for insertion in grid.insertions:
				numbers.append(insertion.number)
			numbers.sort()
			for number in numbers:
				labels.append((label, gridid, number))
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

	def targetInImage(self, target, image):
		if image.location is None:
			raise ValueError('no location for image')
		r, c = target
		inrow = r >= image.location[0][0] and r <= image.location[0][1]
		incolumn = c >= image.location[1][0] and c <= image.location[1][1]
		return inrow and incolumn

	def updateAtlasTargets(self):
		targets = self.panel.getTargetPositions('Acquisition')
		if self.insertion is not None:
			self.insertion.images.reverse()
			for image in self.insertion.images:
				image.clearTargets()
				for target in list(targets):
					column, row = target
					try:
						if self.targetInImage((row, column), image):
							targets.remove(target)
							target = (row - image.location[0][0], column - image.location[1][0])
							image.addTarget(target)
					except ValueError:
						if image.data is None:
							self.logger.warning('No location for image')
						else:
							self.logger.warning('No location for image ID %d' % image.data.dbid)
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
		if image.data is None:
			self.logger.warning('No data for this image')
			return
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

	def getImageAtlasLocation(self, image, extrema):
		rows = (
			image.row - image.halfheight - extrema[0][0],
			image.row + image.halfheight - extrema[0][0]
		)
		columns = (
			image.column - image.halfwidth - extrema[1][0],
			image.column + image.halfwidth - extrema[1][0]
		)
		return rows, columns

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
			l = self.getImageAtlasLocation(image, extrema)
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

	def getCenterImage(self, insertion):
		extrema = self.getAtlasExtrema(insertion.images)
		center = ((extrema[0][1] - extrema[0][0])/2.0,
							(extrema[1][1] - extrema[1][0])/2.0)
		centerimage = None
		for image in insertion.images:
			if self.targetInImage(center, image):
				centerimage = image
				break
		if centerimage is None:
			raise ValueError('no center image to calculate affine transform')
		return centerimage

	def getImageCenter(self, image):
		shape = image.data['image'].shape
		row, column = shape[0]/2.0, shape[1]/2.0
		center = (row + image.location[0][0], column + image.location[1][0])
		return center

	def getInsertionTransform(self, centerimage, griddata):
		# acquire image and align
		imagedata = self.reacquireImage(centerimage.data, griddata=griddata)
		if imagedata is None:
			raise RuntimeError('image reacquisition failed')

		image1 = centerimage.data['image']
		image2 = imagedata['image']
		self.logger.info('Calculating main transform...')
		result = align.findRotationScaleTranslation(image1, image2)
		rotation, scale, shift, value = result
		m = 'Rotation: %g, scale: %g, shift: (%g, %g), peak value: %g'
		self.logger.info(m % ((rotation, scale) + shift + (value,)))

		return result, imagedata

	def getTargets(self, image, center,
									matrix, rotation, scale, shift, centerimagedata, griddata):
		targets = []
		for target1 in image.targets:
			# target relative to the center of the center image of the atlas
			target2 = (target1[0] + image.location[0][0] - center[0],
									target1[1] + image.location[1][0] - center[1])

			# transform target to where it should be for the current position
			# based on the transform of the center image
			target2 = numarray.matrixmultiply(matrix, target2) + shift

			# acquire where the target should be centered
			imagedata = self.reacquireImage(centerimagedata,
																			target=target2,
																			griddata=griddata)

			image1 = image.data['image']
			shape = image1.shape
			shift = -(target1[0] - shape[0]/2.0), -(target1[1] - shape[1]/2.0)
			image1 = numarray.nd_image.shift(image1, shift)
			image1 = align.rotateScaleOffset(image1, rotation, scale, (0.0, 0.0),
																				shape=(shape[0]/2.0, shape[1]/2.0))

			i = numarray.zeros(shape, image1.type())
			o = int(round(shape[0]/4.0)), int(round(shape[1]/4.0))
			i[o[0]:o[0]+image1.shape[0], o[1]:o[1]+image1.shape[1]] = image1
			image1 = i

			image2 = imagedata['image']
			shape = image2.shape
			i = numarray.zeros(image2.shape, image2.type())
			o = int(round(shape[0]/4.0)), int(round(shape[1]/4.0))
			i[o[0]:-o[0], o[1]:-o[1]] = image2[o[0]:-o[0], o[1]:-o[1]]
			image2 = i

			self.logger.info('Calculating target error transform...')
			shift, value = align.findTranslation(image1, image2)
			m = 'Shift: (%g, %g), peak value: %g'
			self.logger.info(m % (shift + (value,)))
			target = -shift[0], -shift[1]
			#target = numarray.matrixmultiply(matrix, target)

			shape = image.data['image'].shape
			target1 = target1[0] - shape[0]/2.0, target1[1] - shape[1]/2.0

			targets.append((target1, target, imagedata))
		return targets

	def processGridData(self, griddata):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(griddata['grid ID'])
		for insertion in grid.insertions:
			if insertion == self.insertion:
				self.setTargets([], 'Acquisition')

			# get a rough estimate of the grid transform
			centerimage = self.getCenterImage(insertion)
			center = self.getImageCenter(centerimage)
			result = self.getInsertionTransform(centerimage, griddata)
			transform, newcenterimagedata = result
			rotation, scale, shift, value = transform
			matrix, imatrix = align.getMatrices(rotation, scale)

			for image in insertion.images:
				# get the targets adjusted for error in the initial transform
				targets = self.getTargets(image, center,
																		imatrix, rotation, scale, shift,
																		newcenterimagedata, griddata)
				# remove targets for this image
				image.targets = []

				targetlist = self.newTargetList()
				targetdatalist = []
				for originaltarget, target, imagedata in targets:
					row, column = target
					targetdata = self.newTargetForImage(imagedata, row, column,
																							type='acquisition',
																							list=targetlist)
					self.publish(targetdata, database=True)
					targetdatalist.append((originaltarget, targetdata))

				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, database=True, dbforce=True, pubevent=True)
				self.waitForTargetListDone()

				'''
				targetlist = self.newTargetList()
				# revise the target based on the target picked on the original mosaic
				# images displayed for clarity in the database and web viewer
				for (row, column), targetdata in targetdatalist:
					originaltargetdata = \
						data.AcquisitionImageTargetData(initializer=targetdata)
					originaltargetdata['delta row'] = row
					originaltargetdata['delta column'] = column
					originaltargetdata['image'] = image.data
					originaltargetdata['scope'] = image.data['scope']
					originaltargetdata['camera'] = image.data['camera']
					originaltargetdata['version'] += 1
					originaltargetdata['list'] = targetlist
					originaltargetdata['status'] = 'done'
					self.publish(originaltargetdata, database=True)
				self.publish(targetlist, database=True, dbforce=True)
				'''

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

	def reacquireImage(self, imagedata, test=False, target=None, griddata=None):
		presetname = imagedata['preset']['name']
		presetdata = self.presetsclient.getPresetFromDB(presetname)

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

		targetdata = data.AcquisitionImageTargetData(initializer=imagedata['target'])
		emtargetdata = data.EMTargetData(initializer=imagedata['emtarget'])

		movetype = emtargetdata['movetype']
		calclient = self.calibrationclients[movetype]
		row = -targetdata['delta row']
		column = -targetdata['delta column']
		if target is not None:
			row -= target[0]
			column -= target[1]
		target = {'row': row, 'col': column}
		scope, camera = targetdata['scope'], targetdata['camera']
		try:
			scopedata = calclient.transform(target, scope, camera)
		except calibrationclient.NoMatrixCalibrationError, e:
			self.logger.error('No calibration for reacquisition: %s' % e)
			if test:
				return False
			else:
				return None

		if test:
			return True

		# check stage position
		emtargetdata[movetype] = dict(scopedata[movetype])
		emtargetdata['target'] = targetdata
		emtargetdata['preset'] = presetdata

		query = data.AcquisitionImageTargetData()
		query['preset'] = data.PresetData()
		query['preset']['name'] = presetname
		query['grid'] = griddata
		try:
			targetdata['number'] = max([r['number'] for r in self.research(query)])+1
		except ValueError:
			targetdata['number'] = 0

		targetdata['preset'] = presetdata
		targetdata['grid'] = griddata
		targetdata['version'] = 0
		targetdata['status'] = 'done'
		targetdata['list'] = None
		targetdata['image'] = None

		self.presetsclient.toScope(presetname, emtargetdata)

		errorstring = 'Image acqisition failed: %s'
		try:
			imagedata = self.instrument.getData(data.CorrectedCameraImageData)
		except:
			self.logger.error(errorstring % 'cannot acquire image')
		if imagedata is None:
			return None
		# Jim says: store to DB to prevent referencing errors
		self.publish(imagedata['scope'], database=True)
		self.publish(imagedata['camera'], database=True)
		imagedata = data.AcquisitionImageData(initializer=imagedata)
		imagedata['target'] = targetdata
		imagedata['emtarget'] = emtargetdata
		imagedata['preset'] = presetdata
		imagedata['label'] = self.name
		imagedata['grid'] = griddata
		self.setImageFilename(imagedata)

		self.publish(imagedata, pubevent=True, database=True)

		return imagedata

	def setImageFilename(self, imagedata):
		sessionstr = self.session['name']
		grididstr = 'GridID%05d' % (imagedata['grid']['grid ID'],)
		insertionstr = 'Insertion%03d' % (imagedata['grid']['insertion'],)
		targetstr = '%05d%s' % (imagedata['target']['number'],
														imagedata['preset']['name'])
		parts = (sessionstr, grididstr, insertionstr, targetstr)
		sep = '_'
		filename = sep.join(parts)
		imagedata['filename'] = filename

