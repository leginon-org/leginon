#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import threading

from leginon import leginondata
from leginon import event
from leginon import node
from leginon import gridentry
from leginon import plategridmaker
from leginon import project
from leginon.gui.wx import PlateGridEntry

class PlateGridEntry(gridentry.GridEntry):
	'''
	Node to make grids from given prep plate and grid format.  As subclass
	of GridEntry, it also starts data acquisition of a grid selection.
	'''
	eventinputs = node.Node.eventinputs + [event.TargetListDoneEvent,
																					event.MosaicDoneEvent]
	eventoutputs = node.Node.eventoutputs + [event.MakeTargetListEvent
										]
	panelclass = PlateGridEntry.Panel
	settingsclass = leginondata.PlateGridEntrySettingsData
	defaultsettings = {
		'grid name': None,
		'plate name': None,
		'grid format name': None,
		'plate format name': None,
	}

	def __init__(self, id, session, managerlocation, **kwargs):
		self.gridmaker = plategridmaker.PlateGridMaker()
		self.plates = []
		self.pformats = {}
		self.gformats = {}
		super(PlateGridEntry,self).__init__(id, session, managerlocation, **kwargs)

	def getGridNames(self):
		gridnames = []
		if self.projectid is not None:
			emgridq = leginondata.EMGridData(project = self.projectid)
		else:
			emgridq = leginondata.EMGridData()
		results = emgridq.query()
		if results:
			for result in results:
				# Only get grids with well-spot-mapping
				if not result['mapping']:
					continue
				newname = result['name']
				if newname not in gridnames:
					gridnames.append(newname)
				else:
					self.logger.warning('Duplicated grid name "%s" not included' % newname)
		return gridnames
					
	def getEMGrid(self, gridname):
		'''
		Returns EMGridData for gridname.
		'''
		if self.projectid is not None:
			emgridq = leginondata.EMGridData(project = self.projectid, name = gridname)
		else:
			emgridq = leginondata.EMGridData(name = gridname)
		results = emgridq.query(results=1)
		if results:
			return results[0]
		else:
			return None

	def getGridFormats(self):
		'''
		Get all grid formats. Returns the names for gui.
		'''
		formats = leginondata.EMGridFormatData().query()
		self.gformats = {}
		for f in formats:
			formatname = '%02d x %02d: %s' % (f['rows'],f['cols'],f['skips'])
			self.gformats[formatname] = f
		return self.gformats.keys()

	def getGridFormatData(self,formatname):
		if formatname in self.gformats.keys():
			return self.gformats[formatname]
		else:
			self.logger.error('Grid format %s not found' % formatname)
			return None

	def publishNewEMGrids(self,gridformat_name, plate_name):
		'''
		save new EMGrids in database for given grid format and plate.
		'''
		self.gridmaker.setProjectId(self.projectid)
		self.gridmaker.setPlate(plate_name)
		# convert to format data
		plate_format = self.plates[plate_name]['plate format']
		grid_format = self.gformats[gridformat_name]
		self.gridmaker.setWellMappingTypeByFormatData(grid_format,plate_format)
		# make grids
		newgrids = self.gridmaker.makeGrids()
		self.settings['grid name'] = newgrids[0]['name']
		self.logger.info('new grids inserted into the database')

	def getPlateNames(self):
		'''
		Get all prep plates. Returns the unique names for gui.
		'''
		self.plates = {}
		if self.projectid is not None:
			plateq = leginondata.PrepPlateData(project=self.projectid)
		else:
			plateq = leginondata.PrepPlateData()
		results = plateq.query()
		if results:
			for result in results:
				newname = result['name']
				if newname not in self.plates.keys():
					self.plates[newname] = result
				else:
					self.logger.warning('Duplicated plate name "%s" not included' % newname)
		return self.plates.keys()

	def getPlateFormats(self):
		'''
		Get plate formats and return a name for gui selector.
		'''
		formats = leginondata.PrepPlateFormatData().query()
		self.pformats = {}
		for f in formats:
			formatname = '%02d x %02d' % (f['rows'],f['cols'])
			self.pformats[formatname] = f
		return self.pformats.keys()

	def getPlateFormatData(self,formatname):
		if formatname in self.pformats.keys():
			return self.pformats[formatname]
		else:
			self.logger.error('Plate format %s not found' % formatname)
			return None

	def publishNewPlate(self,newplate,formatname):
		'''
		Save new prep plate in database.
		'''
		q = leginondata.PrepPlateData()
		q['name'] = newplate
		q['plate format'] = self.getPlateFormatData(formatname)
		q['project'] = self.projectid
		try:
			self.publish(q, database=True)
		except node.PublishError:
			raise
		self.settings['plate name'] = newplate
		self.settings['plate format name'] = formatname
		self.logger.info('new plate inserted into the database')

	def onBadPlateName(self,e):
		self.logger.error('New plate entry failed: %s' % e)

