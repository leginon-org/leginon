#!/usr/bin/env python
import math

from leginon import leginondata


class PlateGridMaker(object):
	'''
	Make DB record of emgrids form prep plate name and well mapping type name
	'''
	def __init__(self):
		self.plate = None
		self.maptype = None
		self.projectid = 1

	def setProjectId(self,projectid):
		self.projectid = projectid

	def setPlate(self,platename):
		plates = leginondata.PrepPlateData(name=platename).query()
		if plates:
			if len(plates) == 1:
				self.plate = plates[0]

	def setWellMappingTypeByFormatData(self,gridformat,plateformat):
		q = leginondata.WellMappingTypeData()
		q['grid format'] = gridformat
		q['plate format'] = plateformat
		maptypes = q.query()
		if maptypes:
			if len(maptypes) == 1:
				self.maptype = maptypes[0]
		else:
			q = leginondata.WellMappingTypeData()
			q['grid format'] = gridformat
			q['plate format'] = plateformat
			q['name'] = '%d to %d' % (plateformat.dbid, gridformat.dbid)
			q.insert()
			self.maptype = q

	def setWellMappingType(self,typename):
		maptypes = leginondata.WellMappingTypeData(name=typename).query()
		if maptypes:
			if len(maptypes) == 1:
				self.maptype = maptypes[0]

	def getNumberOfGrids(self):
		if self.maptype:
			wells = self.maptype['plate format']['cols']*self.maptype['plate format']['rows']	 
			if self.maptype['grid format']['skips'] is None:
				skipcount = 0
			else:
				skipcount = len(self.maptype['grid format']['skips'])
			spots = self.maptype['grid format']['cols']*self.maptype['grid format']['rows']	- skipcount
			ngrids = int( math.ceil(float(wells) / float(spots)) )
			return ngrids
		return 0

	def getGridMakingPrintTrialNumber(self):
		q = leginondata.EMGridData(project = self.projectid,plate=self.plate)
		r = q.query()
		if r:
			trials = map((lambda x: x['print trial']),r)
			return max(trials) + 1
		else:
			return 1

	def makeGrid(self,grid_index=0):
		'''
		make grid at given grid_index and print trial number.
		Filenaming: p stands for print trial number. g is well group
		in the database. known to users as grid number
		'''
		grid_number = int(grid_index) + 1
		gridname = self.plate['name']+'p%dg%d' % (self.trial_number,grid_number)
		q = leginondata.EMGridData(project = self.projectid,mapping=self.maptype,plate=self.plate)
		q['well group'] = grid_number
		q['print trial'] = self.trial_number
		q['name'] = gridname
		q.insert()
		return q

	def makeGrids(self):
		'''
		Make grids with valid attributes for porjectId, platedata,
		and maptypedata.
		'''
		grids = []
		if self.maptype and self.plate:
			ngrids = self.getNumberOfGrids()
			self.trial_number = self.getGridMakingPrintTrialNumber()
			for n in range(ngrids):
				grids.append(self.makeGrid(n))
		return grids

	def makeGridsForPlate(self,projectid,plate_name,maptype_name):
		'''
		Make Grids with known plate name and maptype name
		'''
		self.setProjectId(projectid)
		self.setPlate(plate_name)
		self.setWellMappingType(maptype_name)
		self.makeGrids()

if __name__ == '__main__':
	app = PlateGridMaker()
	app.makeGridsForPlate(1,'plate1','96to100')
