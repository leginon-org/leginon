# The Leginon software is Copyright 2004
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
#
# $Source: /ami/sw/cvsroot/pyleginon/atlasviewer.py,v $
# $Revision: 1.2 $
# $Name: not supported by cvs2svn $
# $Date: 2005-01-28 23:40:36 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import math
import numarray
import data
import node
import targethandler
import gui.wx.AtlasViewer

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
		self.atlases = {}
		self.gridid = None
		self.insertion = None
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.start()

	def getAtlasLabels(self):
		labels = []
		for gridid in self.atlases:
			insertions = self.atlases[gridid].keys()
			insertions.sort()
			for insertion in insertions:
				labels.append((gridid, insertion))
		return labels

	def getAtlases(self):
		self.gridid = None
		self.insertion = None
		self.setImage(None, 'Image')
		self.setTargets([], 'Acquisition')
		querydata = data.MosaicTileData(session=self.session)
		tiledatalist = self.research(datainstance=querydata)
		imagedatarefs = {}
		for tiledata in tiledatalist:
			imagedataref = tiledata.special_getitem('image', dereference=False)
			if tiledata['list'].dbid in imagedatarefs:
				imagedatarefs[tiledata['list'].dbid].append(imagedataref)
			else:
				imagedatarefs[tiledata['list'].dbid] = [imagedataref]
		self.atlases = self.classifyMosaicTileData(imagedatarefs)
		self.panel.getAtlasesDone()

	def classifyMosaicTileData(self, imagedatarefs):
		info = {}
		for dbid, refs in imagedatarefs.items():
			gridid = None
			insertion = None
			imagedatalist = []
			for ref in refs:
				imagedata = self.researchDBID(ref.dataclass, ref.dbid, readimages=False)
				if imagedata is None:
					self.logger.warning('Cannot load image from database, ignoring image')
					continue
				if imagedata['grid'] is None:
					self.logger.warning('No grid information, ignoring image')
					continue
				if imagedata['grid']['grid ID'] is None:
					self.logger.warning('No grid ID, ignoring image')
					continue
				if imagedata['grid']['insertion'] is None:
					self.logger.warning('No insertion number, ignoring image')
					continue
				if gridid is None:
					gridid = imagedata['grid']['grid ID']
				elif imagedata['grid']['grid ID'] != gridid:
					self.logger.warning('Different grid ID, ignoring image')
					continue
				if insertion is None:
					insertion = imagedata['grid']['insertion']
				elif imagedata['grid']['insertion'] != insertion:
					self.logger.warning('Different insertion number, ignoring image')
					continue
				imagedatalist.append(imagedata)
			if not imagedatalist:
				continue
			if gridid not in info:
				info[gridid] = {}
			if insertion in info[gridid]:
				self.logger.warning('Duplicate insertion, ignoring images')
				continue
			info[gridid][insertion] = {}
			info[gridid][insertion]['image data'] = imagedatalist
			info[gridid][insertion]['targets'] = []
		return info

	def updateAtlasTargets(self):
		targets = self.panel.getTargetPositions('Acquisition')
		try:
			self.atlases[self.gridid][self.insertion]['targets'] = targets
		except KeyError:
			pass

	def setAtlas(self, gridid, insertion):
		self.updateAtlasTargets()
		self.gridid = gridid
		self.insertion = insertion
		try:
			imagedatalist = self.atlases[self.gridid][self.insertion]['image data']
		except KeyError:
			self.node.error('Failed to load atlas')
			return
		atlasimage = self.getAtlasImage(imagedatalist)
		self.setImage(atlasimage, 'Image')
		targets = self.atlases[self.gridid][self.insertion]['targets']
		self.setTargets(targets, 'Acquisition')
		self.panel.setAtlasDone()

	def getAtlasImage(self, imagedatalist):
		if not imagedatalist:
			return None
		minrow = None
		mincolumn = None
		maxrow = None
		maxcolumn = None
		atlasimages = []
		for imagedata in imagedatalist:
			width = imagedata['preset']['dimension']['x']
			height = imagedata['preset']['dimension']['y']
			targetdata = imagedata['target']
			row, column = targetdata['delta row'], targetdata['delta column']
			halfwidth = int(math.ceil(width/2.0))
			halfheight = int(math.ceil(height/2.0))
			if minrow is None or (row - halfheight) < minrow:
				minrow = row - halfheight
			if mincolumn is None or (column - halfwidth) < mincolumn:
				mincolumn = column - halfwidth
			if maxrow is None or (row + halfheight) > maxrow:
				maxrow = row + halfheight
			if maxcolumn is None or (column + halfwidth) > maxcolumn:
				maxcolumn = column + halfwidth
			atlasimages.append((imagedata['image'], width, height, row, column))
		atlasshape = (maxrow - minrow, maxcolumn - mincolumn)
		atlasimage = numarray.zeros(atlasshape, numarray.Float32)
		for fileref, width, height, row, column in atlasimages:
			halfwidth = int(math.ceil(width/2.0))
			halfheight = int(math.ceil(height/2.0))
			image = fileref.read()
			i = ((row - halfheight - minrow, row + halfheight - minrow),
						(column - halfwidth - mincolumn, column + halfwidth - mincolumn))
			atlasimage[i[0][0]:i[0][1], i[1][0]:i[1][1]] = image
		return atlasimage

	def submitTargets(self):
		self.updateAtlasTargets()
		for gridid in self.atlases:
			insertions = self.atlases[gridid].keys()
			insertions.sort()
			targets = []
			for insertion in insertions:
				targets += self.atlases[gridid][insertion]['targets']
			if targets:
				# tell the robot to insert this grid
				# wait for the grid to be inserted
				# acquire an image at a stage position in the atlas
				# align the image to the atlas for the grid targets picked on
				# check targets again?
				# rotate and shift targets
				# submit targets and wait for them to be done
				print gridid
		self.panel.targetsSubmitted()

