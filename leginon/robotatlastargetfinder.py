# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/robotatlastargetfinder.py,v $
# $Revision: 1.26 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-19 18:27:42 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import math
import numpy
import pyami.quietscipy
import scipy.ndimage
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
import gui.wx.RobotAtlasTargetFinder
import libCVwrapper

class TargetError(Exception):
	pass

class Grids(object):
	def __init__(self, node):
		self.grids = []
		self.node = node

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
		for grid in self.grids:
			label = self.node.getGridLabel(grid.gridid)
			number = self.node.getGridNumber(grid.gridid)
			inumbers = [insertion.number for insertion in grid.insertions]
			inumbers.sort()
			for inumber in inumbers:
				labels.append((label, grid.gridid, number, inumber))
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
	def __init__(self, grid, number):
		self.extrema = None
		self.shape = None
		self.grid = grid
		self.number = number
		self.images = []

	def addImage(self, image):
		self.images.append(image)

	def finalize(self):
		self.setExtrema()
		self.setShape()
		for image in self.images:
			self.setImageLocation(image)

	def setImageLocation(self, image):
		rows = (image.row - image.halfheight - self.extrema[0][0],
						image.row + image.halfheight - self.extrema[0][0])
		columns = (image.column - image.halfwidth - self.extrema[1][0],
								image.column + image.halfwidth - self.extrema[1][0])
		image.location = rows, columns

	def setExtrema(self):
		minrow = None
		mincolumn = None
		maxrow = None
		maxcolumn = None
		for image in self.images:
			if minrow is None or (image.row - image.halfheight) < minrow:
				minrow = image.row - image.halfheight
			if mincolumn is None or (image.column - image.halfwidth) < mincolumn:
				mincolumn = image.column - image.halfwidth
			if maxrow is None or (image.row + image.halfheight) > maxrow:
				maxrow = image.row + image.halfheight
			if maxcolumn is None or (image.column + image.halfwidth) > maxcolumn:
				maxcolumn = image.column + image.halfwidth
		self.extrema = ((minrow, maxrow), (mincolumn, maxcolumn))

	def setShape(self):
		self.shape = (self.extrema[0][1] - self.extrema[0][0],
									self.extrema[1][1] - self.extrema[1][0])

class Image(object):
	def __init__(self, insertion, imagedata, node):
		self.insertion = insertion
		self.data = imagedata
		self.node = node
		self.location = None
		self.width = imagedata['preset']['dimension']['x']
		self.height = imagedata['preset']['dimension']['y']
		targetdata = imagedata['target']
		self.row = targetdata['delta row']
		self.column = targetdata['delta column']
		self.halfwidth = int(math.ceil(self.width/2.0))
		self.halfheight = int(math.ceil(self.height/2.0))
		self.targetdatalist = self.node.researchTargets(session=self.node.session,
																										image=self.data)

	def addTarget(self, target):
		row, column = target
		targetdata = self.node.newTargetForTile(self.data, row, column,
																							type='acquisition', status='new')
																							#list=targetlist)
		self.node.publish(targetdata, database=True, dbforce=True)
		self.targetdatalist.insert(0, targetdata)

	def removeTarget(self, target):
		for targetdata in self.targetdatalist:
			t = targetdata['delta row'], targetdata['delta column']
			if t == target and targetdata['status'] == 'new':
				self.updateTargetStatus(targetdata, 'aborted')
				return
		raise ValueError

	def updateTargetStatus(self, targetdata, status):
		i = self.targetdatalist.index(targetdata)
		targetdata = targetdata.__class__(initializer=targetdata)
		targetdata['status'] = status
		self.node.publish(targetdata, database=True, dbforce=True)
		self.targetdatalist[i] = targetdata
		return targetdata

	def getNewTargets(self):
		targetdatalist = self.getNewTargetDataList()
		return [(d['delta row'], d['delta column']) for d in targetdatalist]

	def getNewTargetDataList(self):
		targetdatalist = []
		for targetdata in self.targetdatalist:
			if targetdata['status'] == 'new':
				targetdatalist.append(targetdata)
		return targetdatalist

	def hasTargets(self):
		for targetdata in self.targetdatalist:
			if targetdata['status'] in ['new', 'processing']:
				return True
		return False

class RobotAtlasTargetFinder(node.Node, targethandler.TargetWaitHandler):
	panelclass = gui.wx.RobotAtlasTargetFinder.Panel
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
		self.grids = Grids(self)
		self.insertion = None

		node.Node.__init__(self, id, session, managerlocation, **kwargs)

		targethandler.TargetWaitHandler.__init__(self)

		self.instrument = instrument.Proxy(self.objectservice, self.session)
		self.presetsclient = presets.PresetsClient(self)
		self.abortevent = threading.Event()

		calibrationclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient,
			'stage position': calibrationclient.StageCalibrationClient,
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient,
			'image beam shift': calibrationclient.ImageBeamShiftCalibrationClient,
		}
		self.calibrationclients = {}
		for i, clientclass in calibrationclients.items():
			self.calibrationclients[i] = clientclass(self)

		self.projectdata = None
		try:
			self.projectdata = project.ProjectData()
		except Exception, e:
			self.logger.warning('Failed to connect to the project database: %s' % e)
		self.addEventInput(event.GridLoadedEvent, self.onGridLoaded)

		self.start()

	def getGridLabel(self, gridid):
		if self.projectdata is not None:
			label = self.projectdata.getGridLabel(gridid)
		else:
			label = 'ID %d' % gridid
		return label

	def getGridNumber(self, gridid):
		if self.projectdata is not None:
			return self.projectdata.getGridNumber(gridid)
		else:
			return None

	def onGridLoaded(self, evt):
		# ...
		if evt['request node'] != self.name:
			return

		if evt['grid'] is None or evt['grid']['grid ID'] is None:
			self.logger.warning('Unknown loaded grid')
			return
		gridid = evt['grid']['grid ID']

		label = self.getGridLabel(gridid)

		status = evt['status']
		if status == 'ok':
			self.logger.info('Robot loaded grid %s' % label)
			self.processGridData(evt['grid'])
		elif status == 'invalid':
			self.logger.warning('Grid %s not in current tray' % label)
		elif status == 'failed':
			self.logger.warning('Robot failed to load grid %s' % label)
			self.abortGridTargets(evt['grid'])
		else:
			self.logger.warning('Unknown status for grid %s' % label)
			
	def abortGridTargets(self,griddata):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(griddata['grid ID'])
		for insertion in grid.insertions:

			targetimages = []
			for image in insertion.images:
				if image.hasTargets():
					targetimages.append(image)
			if not targetimages:
				continue
		for image in targetimages:
			targets = []
			targetdatalist = list(image.targetdatalist)
			for targetdata in targetdatalist:
				if targetdata['status'] == 'new':
					targetdata = image.updateTargetStatus(targetdata, 'aborted')
				elif targetdata['status'] == 'processing':
					targetdata = image.updateTargetStatus(targetdata, 'aborted')
				else:
					continue
		self.updateAtlasTargets()

	def getAtlases(self):
		self.insertion = None
		self.setImage(None, 'Image')
		self.setTargets([], 'New')
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
		elif imagedata['grid']['grid ID'] is None and (not 'emgrid' in imagedata['grid'].keys() or imagedata['grid']['emgrid'] is None):
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
			insertion = Insertion(grid, number)
			for imagedata in imagedatalist:
				insertion.addImage(Image(insertion, imagedata, self))
			insertion.finalize()
			grid.addInsertion(insertion)

	def targetInImage(self, target, image):
		r, c = target
		inrow = r >= image.location[0][0] and r <= image.location[0][1]
		incolumn = c >= image.location[1][0] and c <= image.location[1][1]
		return inrow and incolumn

	def updateAtlasTargets(self):
		if self.insertion is None:
			return

		targets = list(self.panel.getTargetPositions('New'))

		for image in self.insertion.images:

			existingtargets = image.getNewTargets()

			for target in list(targets):
				column, row = target
				if self.targetInImage((row, column), image):
					targets.remove(target)
					target = (row - image.halfheight - image.location[0][0], column - image.halfwidth - image.location[1][0])
					if target in existingtargets:
						existingtargets.remove(target)
					else:
						image.addTarget(target)

			for target in existingtargets:
				image.removeTarget(target)

	def setAtlas(self, gridid, number):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(gridid)
		self.insertion = grid.getInsertionByNumber(number)
		self.updateAtlasView()
		self.panel.setAtlasDone()

	def updateAtlasView(self):
		self.updateAtlasViewImage()
		self.updateAtlasViewTargets()

	def updateAtlasViewImage(self):
		if self.insertion is None:
			self.setImage(None, 'Image')
			return
		atlasimage = numpy.zeros(self.insertion.shape, numpy.float32)
		for image in self.insertion.images:
			atlasimage[image.location[0][0]:image.location[0][1],
								image.location[1][0]:image.location[1][1]] = image.data['image']
		self.setImage(atlasimage, 'Image')

	def updateAtlasViewTargets(self):
		if self.insertion is None:
			self.setTargets([], 'New')
			self.setTargets([], 'Submitted')
			self.setTargets([], 'Processed')
			return
		newtargets = []
		submittedtargets = []
		processedtargets = []
		# markdonetargets is a temporary function used once when the first pass targets
		# are filtered but not marked done.  By marking them done as they are displayed,
		# there is no need to remove them one by one.  Should be made proper later.
		#markdonetargets = []
		for image in self.insertion.images:
			for targetdata in image.targetdatalist:
				target = (targetdata['delta column'] + image.halfwidth + image.location[1][0],
									targetdata['delta row'] + image.halfheight + image.location[0][0])
				if targetdata['status'] == 'new':
					newtargets.append(target)
					#markdonetargets.append(targetdata)
				elif targetdata['status'] == 'processing':
					submittedtargets.append(target)
				elif targetdata['status'] == 'done':
					processedtargets.append(target)
		self.setTargets(newtargets, 'New')
		self.setTargets(submittedtargets, 'Submitted')
		self.setTargets(processedtargets, 'Processed')
		#self.markTargetsDone(markdonetargets)

	def hasTargets(self, grid):
		for insertion in grid.insertions:
			for image in insertion.images:
				if image.hasTargets():
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
		label = self.getGridLabel(grid.gridid)
		self.logger.info('Robot notified to unload grid %s' % label)

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
		center = ((insertion.extrema[0][1] - insertion.extrema[0][0])/2.0,
							(insertion.extrema[1][1] - insertion.extrema[1][0])/2.0)
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

	def getTransform(self, centerimagedata1, griddata2):
		griddata1 = centerimagedata1['grid']
		result = self.loadTransform(griddata1, griddata2)
		if result is None:
			centerimagedata2 = self.reacquireImage(centerimagedata1,
																							griddata=griddata2)
			image1 = centerimagedata1['image']
			image2 = centerimagedata2['image']
			self.logger.info('Calculating main transform...')
			result = align.findRotationScaleTranslation(image1, image2)
			self.saveTransform(result, griddata1, griddata2)
		else:
			self.logger.info('Loading main transform...')
		rotation, scale, shift, rsvalue, value = result
		rsm = 'Rotation: %g, scale: %g, peak value: %g' % (rotation, scale, rsvalue)
		tm = 'shift: (%g, %g), peak value: %g' % (shift + (value,))
		self.logger.info(rsm + ', ' + tm)

		return result, centerimagedata2

	def getTransform_sift(self, centerimagedata1, griddata2):
		# Not yet working
		griddata1 = centerimagedata1['grid']
		result = self.loadTransform(griddata1, griddata2)
		if result is None:
			centerimagedata2 = self.reacquireImage(centerimagedata1,
																							griddata=griddata2)
			image1 = centerimagedata1['image']
			image2 = centerimagedata2['image']
			self.logger.info('Calculating main transform...')
			resultold = align.findRotationScaleTranslation(image1, image2)
			resultmatrix = libCVwrapper.MatchImages(image1, image2)
			# The following conversion may be incorrect
			rotation = math.atan2(resultmatrix[(0,1)],resultmatrix[(1,1)])
			scale = 1
			shift = (resultmatrix[(0,0)],resultmatrix[(1,0)])
			result = rotation,scale,shift,1,1
			self.saveTransform(result, griddata1, griddata2)
		else:
			self.logger.info('Loading main transform...')
		rotation, scale, shift, rsvalue, value = result
		rsm = 'Rotation: %g, scale: %g, peak value: %g' % (rotation, scale, rsvalue)
		tm = 'shift: (%g, %g), peak value: %g' % (shift + (value,))
		self.logger.info(rsm + ', ' + tm)

		return result, centerimagedata2

	def saveTransform(self, result, griddata1, griddata2):
		rotation, scale, shift, rsvalue, value = result
		transformdata = data.LogPolarGridTransformData()
		transformdata['rotation'] = rotation
		transformdata['scale'] = scale
		transformdata['translation'] = {'x': shift[1], 'y': shift[0]}
		transformdata['RS peak value'] = rsvalue
		transformdata['T peak value'] = value
		transformdata['grid 1'] = griddata1
		transformdata['grid 2'] = griddata2
		self.publish(transformdata, database=True)

	def loadTransform(self, griddata1, griddata2):
		querydata = data.LogPolarGridTransformData()
		querydata['grid 1'] = griddata1
		querydata['grid 2'] = griddata2
		resultdatalist = self.research(querydata, results=1)
		if not resultdatalist:
			return None
		transformdata = resultsdatalist[0]
		rotation = transformdata['rotation'] = rotation
		scale = transformdata['scale'] = scale
		translation = transformdata['translation']
		shift = (translation['y'], translation['x'])
		rsvalue = transformdata['RS peak value']
		value = transformdata['T peak value']
		return rotation, scale, shift, rsvalue, value

	def getTargets(self, image, center,
									matrix, rotation, scale, centershift, centerimagedata, griddata):
		targets = []
		targetdatalist = list(image.targetdatalist)
		for targetdata in targetdatalist:
			if targetdata['status'] == 'new':
				targetdata = image.updateTargetStatus(targetdata, 'processing')
			elif targetdata['status'] == 'processing':
				pass
			else:
				continue
			target1 = targetdata['delta row'], targetdata['delta column']

			# target relative to the center of the center image of the atlas
			target2 = (target1[0]+image.halfheight+image.location[0][0] - center[0],
									target1[1]+image.halfwidth+image.location[1][0] - center[1])

			# transform target to where it should be for the current position
			# based on the transform of the center image
			#target2 = numpy.dot(matrix, target2) + centershift
			# ???
			target2 = numpy.dot(matrix, target2) - centershift

			# acquire where the target should be centered
			imagedata = self.reacquireImage(centerimagedata,
																			target=target2,
																			griddata=griddata)

			image1 = image.data['image']
			shift = -target1[0], -target1[1]
			image1 = scipy.ndimage.shift(image1, shift)
			shape = image1.shape
			image1 = align.rotateScaleOffset(image1, rotation, scale, (0.0, 0.0),
																				shape=(shape[0]/2, shape[1]/2))

			i = numpy.zeros(shape, image1.dtype)
			o = int(round(shape[0]/4.0)), int(round(shape[1]/4.0))
			i[o[0]:o[0]+image1.shape[0], o[1]:o[1]+image1.shape[1]] = image1
			image1 = i

			image2 = imagedata['image']
			shape = image2.shape
			i = numpy.zeros(image2.shape, image2.dtype)
			o = int(round(shape[0]/4.0)), int(round(shape[1]/4.0))
			i[o[0]:-o[0], o[1]:-o[1]] = image2[o[0]:-o[0], o[1]:-o[1]]
			image2 = i

			self.logger.info('Calculating target error transform...')
			shift, value = align.findTranslation(image1, image2)
			m = 'Shift: (%g, %g), peak value: %g'
			self.logger.info(m % (shift + (value,)))
			target = -shift[0], -shift[1]
			#target = numpy.dot(matrix, target)

			targets.append((targetdata, target, imagedata))

		return targets

	def processGridData(self, griddata):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(griddata['grid ID'])
		for insertion in grid.insertions:

			targetimages = []
			for image in insertion.images:
				if image.hasTargets():
					targetimages.append(image)
			if not targetimages:
				continue

			# get a rough estimate of the grid transform
			centerimage = self.getCenterImage(insertion)
			center = self.getImageCenter(centerimage)
			result = self.getTransform(centerimage.data, griddata)
			transform, newcenterimagedata = result
			rotation, scale, shift, rsvalue, value = transform
			matrix, imatrix = align.getMatrices(rotation, scale)

			self.abortevent.clear()
			for image in targetimages:
				# get the targets adjusted for error in the initial transform
				targets = self.getTargets(image, center,
																		imatrix, rotation, scale, shift,
																		newcenterimagedata, griddata)
				if insertion == self.insertion:
					self.updateAtlasViewTargets()
				# use first transformed target as the reference target
				if image == targetimages[0]:
					self.updateReferenceTarget(targets[0])
				targetlist = self.newTargetList(image=image.data)
				self.publish(targetlist, database=True, dbforce=True)
				targetdatalist = []
				for originaltargetdata, target, imagedata in targets:
					row, column = target
					targetdata = self.newTargetForTile(imagedata, row, column,
																							type='acquisition',
																							list=targetlist)
					## maybe should be forced
					self.publish(targetdata, database=True, dbforce=True)
					targetdatalist.append((originaltargetdata, targetdata))

				self.makeTargetListEvent(targetlist)
				self.publish(targetlist, pubevent=True)

				self.waitForTargetListDone()

				for originaltargetdata, targetdata in targetdatalist:
					targetquery = targetdata.__class__(initializer=targetdata)
					targetquery['status'] = None
					query = data.AcquisitionImageData(session=self.session,
																						target=targetquery)
					imagedatalist = self.research(query, readimages=False)
					for imagedata in imagedatalist:
						imagedata = data.AcquisitionImageData(initializer=imagedata)
						imagedata['target'] = originaltargetdata
						## this will probably save the image file again with
						## the same filename
						self.publish(imagedata, database=True)
					image.updateTargetStatus(originaltargetdata, 'done')
				if insertion == self.insertion:
					self.updateAtlasViewTargets()

				## check for abort
				if self.abortevent.isSet():
					break

		self.unloadGrid(grid)

	def abortInsertion(self):
		self.abortevent.set()

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
		self.logger.debug('preset name: %s' % (presetname, ))
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
		if movetype == 'modeled stage position':
			scopeparam = 'stage position'
		else:
			scopeparam = movetype
		emtargetdata[scopeparam] = dict(scopedata[scopeparam])
		emtargetdata['target'] = targetdata
		#emtargetdata['preset'] = presetdata

		query = data.AcquisitionImageTargetData()
		query['session'] = self.session
		query['preset'] = data.PresetData()
		query['preset']['name'] = presetname
		query['grid'] = griddata
		try:
			targetdata['number'] = max([r['number'] for r in self.research(query)])+1
		except ValueError:
			targetdata['number'] = 0
		self.logger.debug('new number: %s' % (targetdata['number'], ))

		targetdata['preset'] = presetdata
		targetdata['grid'] = griddata
		targetdata['version'] = 0
		targetdata['status'] = 'done'
		targetdata['list'] = None
		targetdata['image'] = None

		## It seems like emtargetdata is being cleaned from DataManager before
		## the call to presetsclient.toScope.
		## As in Acquisition node:
		## publish in DB because it will likely be needed later
		## when returning to the same target,
		## even after it is removed from memory
		self.publish(emtargetdata, database=True)

		self.presetsclient.toScope(presetname, emtargetdata)

		errorstring = 'Image acqisition failed: %s'
		try:
			imagedata2 = self.instrument.getData(data.CorrectedCameraImageData)
		except:
			imagedata2 = None
			self.logger.error(errorstring % 'cannot acquire image')
		if imagedata2 is None:
			return None
		# Jim says: store to DB to prevent referencing errors
		self.publish(imagedata2['scope'], database=True)
		self.publish(imagedata2['camera'], database=True)
		imagedata2 = data.AcquisitionImageData(initializer=imagedata2)
		imagedata2['target'] = targetdata
		imagedata2['emtarget'] = emtargetdata
		imagedata2['preset'] = presetdata
		imagedata2['label'] = self.name
		imagedata2['grid'] = griddata
		self.setImageFilename(imagedata2)
		self.logger.debug('new filename: %s' % (imagedata2['filename'], ))

		self.publish(imagedata2, pubevent=True, database=True)

	
		return imagedata2

	def setImageFilename(self, imagedata):
		sessionstr = self.session['name']
		grid = imagedata['grid']
		parts = [sessionstr,]
		gridname = ''
		if grid is not None:
			gridname = ''
			if 'emgrid' in grid and grid['emgrid'] is not None and grid['emgrid']['name']:
				# new, shorter style with grid name
				if grid['emgrid']['project'] is not None:
					gridname = ('Prj%03d'% grid['emgrid']['project'])+'_'
				gridname = (gridname + grid['emgrid']['name']).replace(' ','_')
				leadlabels = ['','i']
			else:
				# old style
				gridname = '%05d' % grid['grid ID']
				leadlabels = ['Grid','Insertion']
			grididstr = leadlabels[0]+gridname
			parts.append(grididstr)
			if 'insertion' in grid and grid['insertion'] is not None:
				insertionstr = '%s%03d' % (leadlabels[1],grid['insertion'])
				parts.append(insertionstr)
		targetstr = '%05d%s' % (imagedata['target']['number'],imagedata['preset']['name'])
		parts.append(targetstr)
		sep = '_'
		filename = sep.join(parts)
		imagedata['filename'] = filename

	def updateReferenceTarget(self, target):
		imagedata = target[2]
		delta_row,delta_column = target[1]
		reference_target = self.newReferenceTarget(imagedata, delta_row, delta_column)
		try:
			self.publish(reference_target, database=True, pubevent=True)
		except node.PublishError, e:
			self.logger.error('Submitting reference target failed')
		else:
			self.logger.info('Reference target submitted')
