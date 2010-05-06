#!/usr/bin/env python
import sinedon
from sinedon import sqldict
import leginonconfig
import projectdata

use_processingdb_table = False
class NotConnectedError(Exception):
	pass

class GridBox(sqldict.ObjectBuilder):
	table = 'gridboxes'
	columns = ['gridboxId', 'label']

class Grid(sqldict.ObjectBuilder):
	table = 'grids'
#	columns = ['gridId', 'label', 'specimenId', 'number', 'boxId','preparation','concentration','fraction','note','sort']
	columns = ['gridId', 'label', 'boxId', 'projectId','prepdate','specimen', 
				'number', 'concentration','fraction','note']

class GridLocation(sqldict.ObjectBuilder):
	table = 'gridlocations'
	columns = ['gridlocationId', 'gridboxId', 'gridId', 'location']

class ProjectData:
	def __init__(self, **kwargs):
		# connection to the project database
		try:
			dbparams = sinedon.getConfig('projectdata')
		except:
			raise NotConnectedError('no project database')
		if not dbparams['host']:
			raise NotConnectedError('no hostname for project database')
		try:
			self.db = sqldict.SQLDict(**dbparams)
		except Exception, e:
			raise NotConnectedError(e)

		self.gridboxes = GridBox().register(self.db)
		self.grids = Grid().register(self.db)
		self.gridlocations = GridLocation().register(self.db)

	def getProjects(self):
		projq = projectdata.projects()
		return projq.query()

	def getProjectExperiments(self):
		projq = projectdata.projectexperiments()
		return projq.query()

	def getProjectId(self, sessiondata):
		projq = projectdata.projectexperiments()
		projq['session'] = sessiondata
		projdatas = projq.query(results=1)
		if not projdatas:
			print "Project Id not found for session"
			return None
		return projdatas[0].dbid

	def getProcessingDB(self, projectId):
		procq = projectdata.processingdb()
		projdata = projectdata.projects.direct_query(projectId)
		procq['project'] = projdata
		procdatas = procq.query(results=1)
		if not procdatas:
			print "Appion database not found for project id"
			return None
		return procdatas[0]['appiondb']

	def getGridBoxes(self):
		return self.gridboxes

	def getGrids(self):
		return self.grids

	def newGrid(self, label, specimenId, number, boxId, location):
		gridId = self.grids.insert([{'label': label, 'specimen': specimenId,
																	'number': number, 'boxId': boxId}])
		self.gridlocations.insert([{'gridboxId': boxId, 'gridId': gridId,
																'location': location}])
		return gridId

	def getGridLocations(self):
		return self.gridlocations

	def getProjectFromGridId(self, gridid):
		gridsindex = self.grids.Index(['gridId'])
		grid = gridsindex[gridid].fetchone()
		if grid is None:
			return None
		try:
			return grid['projectId']
		except KeyError:
			return None

	def getGridInfo(self, gridid):
		gridsindex = self.grids.Index(['gridId'])
		grid = gridsindex[gridid].fetchone()
		if grid is None:
			return None
		return grid
				
	def getGridLabel(self, gridid):
		gridsindex = self.grids.Index(['gridId'])
		grid = gridsindex[gridid].fetchone()
		if grid is None:
			return None
		try:
			return grid['label']
		except KeyError:
			return None

	def getGridNumber(self, gridid):
		gridsindex = self.grids.Index(['gridId'])
		grid = gridsindex[gridid].fetchone()
		if grid is None:
			return None
		try:
			return int(grid['number'])
		except:
			return None




########################################
## Testing
########################################

if __name__ == "__main__":
	import sys
	# getall projects
	projdata = ProjectData()
	projects = projdata.getProjects()
	print projects
	allprojects = projects.getall()
	print allprojects;
	"""
	projdata = ProjectData()

	#print projdata.getGridName(111)
	gridid = 751
	grids = projdata.getGrids()
	gridsindex = grids.Index(['gridId'])
	grid = gridsindex[gridid].fetchone()
	print grid
	if grid is None:
		print
	gridtrayid = 58
	if grid['boxId'] != gridtrayid:
		print
	gridlocations = projdata.getGridLocations()
	gridlocationsindex = gridlocations.Index(['gridId'])
	gridlocation = gridlocationsindex[gridid].fetchone()
	if gridlocation is None:
		print
	if gridlocation['gridboxId'] != gridtrayid:
		print
	print gridlocation
	#return int(gridlocation['location'])

	for i in range(1, 97):
		projdata.newGrid('Robot Grids 2, #%d' % i, 113, i, 12, i)

	gridboxes = projdata.getGridBoxes()
	labelindex = gridboxes.Index(['label'])
	gridboxlabels = map(lambda d: d['label'], gridboxes.getall())
	print gridboxlabels
	gridbox = labelindex['Simple Test Tray'].fetchone()
	gridboxid = gridbox['gridboxId']
	gridlocations = projdata.getGridLocations()
	gridboxidindex = gridlocations.Index(['gridboxId'])
	gridlocations = gridboxidindex[gridboxid].fetchall()
	grids = projdata.getGrids()
	grididindex = grids.Index(['gridId'])
	gridmapping = {}
	for gridlocation in gridlocations:
		grid = grididindex[gridlocation['gridId']].fetchone()
		gridmapping[grid['label']] = {'gridId': gridlocation['gridId'],
																	'location': gridlocation['location']}
	print gridmapping

	projdata1 = ProjectData()
	projects = projdata1.getProjects()
	print projects.getall()
	projdata2 = ProjectData()
	projects = projdata2.getProjects()
	allprojects = projects.getall()

	print allprojects

	# getall experiment name with his projectId
	projectexperiments = projdata.getProjectExperiments()
	allprojectexperiments = projectexperiments.getall()
	print allprojectexperiments

	#getall experiments with projectId=5
	print projectexperiments.projectId[5].fetchall()

	# insert a new session into the Test  Project database
	newsession = ProjectExperiment(5, 'testexp')

	# if the session already exists, it won't be inserted again,
	# the existing primary will be returned. The function 
	# returns the last inserted id for a new insert
	key = projectexperiments.insert([newsession.dumpdict()])
	print key
	"""

