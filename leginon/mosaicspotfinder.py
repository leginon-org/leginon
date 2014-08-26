#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from leginon import leginondata
from leginon import rasterindexer
from pyami import ordereddict
import event
import mosaictargetfinder
import gui.wx.MosaicSpotFinder
import math
import time
try:
	set = set
except NameError:
	import sets
	set = sets.Set

class MosaicSpotFinder(mosaictargetfinder.MosaicClickTargetFinder):
	'''
	Target selection and mapping of spot targets to plate wells
	of a multiple picoliter specimen grid atlas.
	'''

	panelclass = gui.wx.MosaicSpotFinder.Panel
	settingsclass = leginondata.MosaicSpotFinderSettingsData
	defaultsettings = dict(mosaictargetfinder.MosaicClickTargetFinder.defaultsettings)
	defaultsettings.update({
		'autofinder': False,
	})

	eventoutputs = mosaictargetfinder.MosaicClickTargetFinder.eventoutputs + [event.MosaicDoneEvent]

	def __init__(self, id, session, managerlocation, **kwargs):
		self.mosaicselectionmapping = {}
		mosaictargetfinder.MosaicClickTargetFinder.__init__(self, id, session, managerlocation, **kwargs)

		self.rasterindexer = rasterindexer.RasterIndexer()

		if self.__class__ == MosaicSpotFinder:
			self.emgriddata = None
			self.spottargets = {}
			self.mapname = ''
			self.start()


	def handleTargetListDone(self, targetlistdoneevent):
		if self.settings['create on tile change'] == 'final':
			self.logger.debug('create final')
			self.createMosaicImage()
			self.logger.debug('done create final')
		if self.settings['autofinder']:
			self.logger.debug('auto target finder')
			self.autoTargetFinder()
			self.logger.debug('done auto target finder')

	def createMosaicImage(self):
		super(MosaicSpotFinder,self).createMosaicImage()
		# reset emgriddata after new mosaic image is created
		self.emgriddata = None
		if self.imagemap:
			imids = self.imagemap.keys()
		if imids:
			griddata = self.imagemap[imids[0]]['grid']
			if griddata:
				self.emgriddata = griddata['emgrid']
		self.hasValidEMGrid()

	def hasValidEMGrid(self):
		if not self.emgriddata:
			self.logger.error('No emgrid set')
			return False
		if not self.emgriddata['mapping']:
			self.logger.error('%s is not printed from a prep plate' % (self.emgriddata['name']))
			return False
		return True

	def getTargetDataList(self, typename):
		'''
		create self.displayedtargetdata which is a dictionary
		with (column,row) target position as keys, and targetdata
		as values
		'''
		displayedtargetdata = {}
		targetsfromimage = self.panel.getTargetPositions(typename)
		for i, t in enumerate(targetsfromimage):
			## if displayed previously (not clicked)...
			if t in self.displayedtargetdata and self.displayedtargetdata[t]:
				targetdata = self.displayedtargetdata[t].pop()
			else:
				c,r = t
				if not self.spottargets or typename != 'acquisition':
					spotname = None
				else:
					# key is spot number (start from 1)
					spotname = self.spottargets[i+1]['map']['name']
				targetdata = self.mosaicToTarget(typename, r, c,spotname)
			if t not in displayedtargetdata:
				displayedtargetdata[t] = []
			displayedtargetdata[t].append(targetdata)
		self.displayedtargetdata = displayedtargetdata

	def mosaicToTarget(self, typename, row, col, spotidname=None):
		'''
		Transfer targets positions and other info on mosaic to
		targetdata for the tile images.
		The targetdata created are inserted to database within this function.
		'''
		imagedata, drow, dcol = self._mosaicToTarget(row, col)
		# publish as targets on most recent version of image to preserve adjusted z
		recent_imagedata = self.researchImages(list=imagedata['list'],target=imagedata['target'])[-1]
		targetdata = self.newTargetForTile(recent_imagedata, drow, dcol, type=typename, list=self.targetlist)
		if spotidname:
			outname, spotmapdata = self.getWell(name=spotidname)
			targetdata['spotmap'] = spotmapdata
		## can we do dbforce here?  it might speed it up
		self.publish(targetdata, database=True)
		return targetdata

	def clearTiles(self):
		self.clearTargets('well')
		super(MosaicSpotFinder, self).clearTiles()

	def clearSpotTargets(self):
		imshape = self.mosaicimage.shape
		self.spottargets = {}
		self.clearTargets('well')

	def guiGetSpotRegister(self):
		'''
		Make cell position and value pairs for wx.grid
		'''
		rasterspots = {}
		keylist = self.spottargets.keys()
		for spot_number in keylist:
			spotposition = self.spottargets[spot_number]['map']['spot position']
			raster_rc = (spotposition['row']-1,spotposition['col']-1)
			if raster_rc not in rasterspots.keys():
				rasterspots[raster_rc] = '%d' % (spot_number)
			else:
				rasterspots[raster_rc] += ',%d' % (spot_number)
		return rasterspots

	def guiSetSpotTargets(self, rasterspots):
		'''
		Set spottargets from gui.  Input rasterspots are already validated.
		'''
		newspottargets = {}
		for raster_rc in rasterspots:
			# keys from rasterspots from gui are (row,col) starts from (0,0)
			raster_cr = (raster_rc[1],raster_rc[0])
			wellname, spotmapdata = self.getWell(raster_2dindex=raster_cr)

			spots = rasterspots[raster_rc]
			bits = spots.split(',')
			bit = bits[0].strip()
			if len(bit) == 0 :
				continue
			# key for spottargets are spot numbers (start from 1)
			spot_number = int(bit)
			if spot_number not in newspottargets.keys():
				newspottargets[spot_number] = {
							'map':spotmapdata,'coord':self.spottargets[spot_number]['coord']}
		self.spottargets = newspottargets.copy()
		targets = self.makeWellTargetsAndStats()
		self.setTargets(targets,'well')
		self.logger.info('spot assignment saved')

	def validateSpotRegister(self,rasterspots):
		spot_numbers = []
		for raster_rc in rasterspots:
			# keys from rasterspots from gui are (row,col) starts from (0,0)
			raster_cr = (raster_rc[1],raster_rc[0])
			spots = rasterspots[raster_rc]
			bits = spots.split(',')
			if len(bits) > 1:
				self.logger.error(
							'more than on spot is mapped to the same well at (c,r) = (%d,%d)'
							% (raster_cr[0]+1,raster_cr[1]+1))
				return False
			else:
				bit = bits[0].strip()
				if len(bit) == 0 :
					continue
				# key for spottargets are spot numbers (start from 1)
				spot_number = int(bit)
				if spot_number in spot_numbers:
					self.logger.error(
								'same spot %d is mapped to more than one well' % spot_number)
					return False
				else:
					if spot_number not in self.spottargets.keys():
						self.logger.error(
									'%d not in range of existing targets' % spot_number)
						return False
					spot_numbers.append(spot_number)
		acq_positions = self.panel.getTargetPositions('acquisition')
		if len(spot_numbers) < len(acq_positions):
			allspots = set(range(1,len(acq_positions)+1))
			missings = list(allspots.difference(spot_numbers))
			self.logger.error(
						'Not all spots are assigned. Missing %s' % (missings))
			return False
		return True

	def getRasterFormat(self):
		gridformat = self.getGridFormat()
		if gridformat:
			return (gridformat['cols'], gridformat['rows'])
		else:
			return None

	def getWell(self, raster_2dindex=None, name=None):
		'''
		Returns plate well name and the SpotWellMapData from
		2dindex of the raster at the grid format.  Alternatively,
		the plat well name can be used instead of raster_2dindex
		to get the same output, mainly for getting its SpotWellMapData
		'''
		wellgroup = self.emgriddata['well group']
		qwpt = self.emgriddata['mapping']
		q = leginondata.SpotWellMapData(mapping=qwpt)
		q['well group'] = wellgroup
		if raster_2dindex:
			q['spot position'] = {'col':raster_2dindex[0]+1,'row':raster_2dindex[1]+1}
		if name:
			q['name'] = name
		r = q.query(results=1)
		if r:
			return r[0]['name'], r[0]
		else:
			return 'n/a', None

	def setSpotTargetsFromTwoLists(self,spot_positions,raster_indices):
		'''
		Set self.spottargets from two ordered lists, spot_positions
		and grid format raster 2d indices
		'''
		self.spottargets = {}
		for i, spot in enumerate(spot_positions):
			raster_2dindex = raster_indices[i]
			wellname, spotmapdata = self.getWell(raster_2dindex)
			self.spottargets[i+1] = {'map':spotmapdata,'coord':spot}

	def makeWellTargetsAndStats(self):
		'''
		Make targets to be set to gui.wx.TargetPanel.
		The targets in the list have information
		of the grid format raster and the plate well name coded in stats
		'''
		targets = []
		for spot_number in range(1,len(self.spottargets)+1):
			spottarget = self.spottargets[spot_number]
			spot = spottarget['coord']
			spotmap = spottarget['map']
			target = {}
			target['x'] = spot[0]
			target['y'] = spot[1]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Raster Col'] = spotmap['spot position']['col']
			target['stats']['Raster Row'] = spotmap['spot position']['row']
			target['stats']['Well Name'] = spotmap['name']
			targets.append(target)
		return targets

	def makeWellTargetsFromTwoLists(self,spot_positions,raster_indices):
		'''
		Set attribute spottargets and then make targets for gui.
		'''
		self.setSpotTargetsFromTwoLists(spot_positions,raster_indices)
		return self.makeWellTargetsAndStats()

	def findSpotIDNames(self):
		'''
		Get grid raster index and plate well names from displayed
		target positions.  Display these in gui, too.
		'''
		self.spottargets = {}
		acq_positions = self.panel.getTargetPositions('acquisition')
		raster_format = self.getRasterFormat() #(total_cols, total_rows)
		index_positions = self.rasterindexer.runRasterIndexer(raster_format, acq_positions)
		well_targets = self.makeWellTargetsFromTwoLists(acq_positions,index_positions)
		self.setTargets(well_targets,'well')

	def getGridFormat(self):
		if self.emgriddata and self.emgriddata['mapping']:
			gridformat = self.emgriddata['mapping']['grid format']
			return gridformat
			
