# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/atlasviewer.py,v $
# $Revision: 1.3 $
# $Name: not supported by cvs2svn $
# $Date: 2005-02-01 01:25:35 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import math
import numarray
import data
import node
import targethandler
import gui.wx.AtlasViewer

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

class AtlasViewer(node.Node, targethandler.TargetHandler):
	panelclass = gui.wx.AtlasViewer.Panel
	eventinputs = (
		node.Node.eventinputs +
		targethandler.TargetHandler.eventinputs
	)
	eventoutputs = (
		node.Node.eventoutputs +
		targethandler.TargetHandler.eventinputs
	)
	def __init__(self, id, session, managerlocation, **kwargs):
		self.grids = Grids()
		self.insertion = None
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.start()

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
			self.logger.warning('No grid information, ignoring image')
			return False
		elif imagedata['grid']['grid ID'] is None:
			self.logger.warning('No grid ID, ignoring image')
			return False
		elif imagedata['grid']['insertion'] is None:
			self.logger.warning('No insertion number, ignoring image')
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
					self.logger.warning('Different grid ID, ignoring image')
					continue
				if number is None:
					number = imagedata['grid']['insertion']
				elif imagedata['grid']['insertion'] != number:
					self.logger.warning('Different insertion number, ignoring image')
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
					if (target[0] >= l[0][0] and target[0] <= l[0][1] and
							target[1] >= l[1][0] and target[1] <= l[1][1]):
						image.addTarget(target)
						targets.remove(target)
			self.insertion.images.reverse()

	def setAtlas(self, gridid, number):
		self.updateAtlasTargets()
		grid = self.grids.getGridByID(gridid)
		self.insertion = grid.getInsertionByNumber(number)
		self.updateAtlasImage()
		self.panel.setAtlasDone()

	def updateAtlasImage(self):
		minrow = None
		mincolumn = None
		maxrow = None
		maxcolumn = None
		for image in self.insertion.images:
			image.width = image.data['preset']['dimension']['x']
			image.height = image.data['preset']['dimension']['y']
			targetdata = image.data['target']
			image.row = targetdata['delta row']
			image.column = targetdata['delta column']
			image.halfwidth = int(math.ceil(image.width/2.0))
			image.halfheight = int(math.ceil(image.height/2.0))
			if minrow is None or (image.row - image.halfheight) < minrow:
				minrow = image.row - image.halfheight
			if mincolumn is None or (image.column - image.halfwidth) < mincolumn:
				mincolumn = image.column - image.halfwidth
			if maxrow is None or (image.row + image.halfheight) > maxrow:
				maxrow = image.row + image.halfheight
			if maxcolumn is None or (image.column + image.halfwidth) > maxcolumn:
				maxcolumn = image.column + image.halfwidth
		shape = (maxrow - minrow, maxcolumn - mincolumn)
		atlasimage = numarray.zeros(shape, numarray.Float32)
		targets = []
		for image in self.insertion.images:
			i = image.data['image'].read()
			l = ((image.row - image.halfheight - minrow,
						image.row + image.halfheight - minrow),
					(image.column - image.halfwidth - mincolumn,
						image.column + image.halfwidth - mincolumn))
			atlasimage[l[0][0]:l[0][1], l[1][0]:l[1][1]] = i
			image.location = l
			targets += image.targets
		self.setImage(atlasimage, 'Image')
		self.setTargets(targets, 'Acquisition')

	def submitTargets(self):
		self.updateAtlasTargets()
		# should sort these properly
		for grid in self.grids.grids:
			# tell the robot to insert this grid
			# wait for the grid to be inserted
			for insertion in grid.insertions:
				for image in insertion.images:
					if image.targets:
						print grid.gridid, insertion.number, image.targets
				# acquire an image at a stage position in the atlas
				# align the image to the atlas for the grid targets picked on
				# check targets again?
				# rotate and shift targets
				# submit targets and wait for them to be done
		self.panel.targetsSubmitted()

