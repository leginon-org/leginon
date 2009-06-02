#!/usr/bin/env python
import sinedon
from sinedon import sqldict
import leginonconfig

class NotConnectedError(Exception):
	pass


class Project(sqldict.ObjectBuilder):
	'''Project: a class object to access the
	`projects` table in the project DB
	'''
	table = 'projects'
	columns = ['projectId', 'name', 'short_description', 'db']

class ProjectExperiment(sqldict.ObjectBuilder):
	'''ProjectExperiment: a class object to access the
	`projectexperiments` table in the project DB
	'''
	table = "projectexperiments"
	columns = ['projectId', 'name']
	indices = [ ('projectId', ['projectId'] )]

class ProjectProcessingDB(sqldict.ObjectBuilder):
	'''ProjectProcessingDB: a class object to access the
	`processingdb` table in the project DB
	'''
	table = "processingdb"
	columns = ['projectId', 'db']
	indices = [ ('projectId', ['projectId'] )]

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

		self.projects = Project().register(self.db)
		self.projectexperiments = ProjectExperiment().register(self.db)
		self.projectprocessingdb = ProjectProcessingDB().register(self.db)
		self.gridboxes = GridBox().register(self.db)
		self.grids = Grid().register(self.db)
		self.gridlocations = GridLocation().register(self.db)

	def getProjects(self):
		return self.projects

	def getProjectExperiments(self):
		return self.projectexperiments

	def getProjectId(self,sessiondata):
		projectexperiments = self.getProjectExperiments()
		allprojectexperiments = projectexperiments.getall()
		sessionname = sessiondata['name']
		for experiment in allprojectexperiments:
			if sessionname == experiment['name']:
				projectsession = experiment
				return int(projectsession['projectId'])
		return None	

	def getProcessingDB(self, projectId):
		processingdblist = self.projectprocessingdb.Index(['projectId'])
		result = processingdblist[projectId].fetchone()
		if result is None:
			return None
		try:
			return result['db']
		except KeyError:
			return None

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
	projectdata = ProjectData()
	projects = projectdata.getProjects()
	allprojects = projects.getall()
	#print allprojects;
	"""
	projectdata = ProjectData()

	print projectdata.getGridName(111)
	gridid = 751
	grids = projectdata.getGrids()
	gridsindex = grids.Index(['gridId'])
	grid = gridsindex[gridid].fetchone()
	print grid
	if grid is None:
		print
	gridtrayid = 58
	if grid['boxId'] != gridtrayid:
		print
	gridlocations = projectdata.getGridLocations()
	gridlocationsindex = gridlocations.Index(['gridId'])
	gridlocation = gridlocationsindex[gridid].fetchone()
	if gridlocation is None:
		print
	if gridlocation['gridboxId'] != gridtrayid:
		print
	print gridlocation
	#return int(gridlocation['location'])

	for i in range(1, 97):
		projectdata.newGrid('Robot Grids 2, #%d' % i, 113, i, 12, i)

	gridboxes = projectdata.getGridBoxes()
	labelindex = gridboxes.Index(['label'])
	gridboxlabels = map(lambda d: d['label'], gridboxes.getall())
	print gridboxlabels
	gridbox = labelindex['Simple Test Tray'].fetchone()
	gridboxid = gridbox['gridboxId']
	gridlocations = projectdata.getGridLocations()
	gridboxidindex = gridlocations.Index(['gridboxId'])
	gridlocations = gridboxidindex[gridboxid].fetchall()
	grids = projectdata.getGrids()
	grididindex = grids.Index(['gridId'])
	gridmapping = {}
	for gridlocation in gridlocations:
		grid = grididindex[gridlocation['gridId']].fetchone()
		gridmapping[grid['label']] = {'gridId': gridlocation['gridId'],
																	'location': gridlocation['location']}
	print gridmapping

	projectdata1 = ProjectData()
	projects = projectdata1.getProjects()
	print projects.getall()
	projectdata2 = ProjectData()
	projects = projectdata2.getProjects()
	allprojects = projects.getall()

	print allprojects

	# getall experiment name with his projectId
	projectexperiments = projectdata.getProjectExperiments()
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

