#!/usr/bin/env python
import sqldict
import leginonconfig


# connection to the project database
dbparams = {
		'host':leginonconfig.DB_PROJECT_HOST,
		'user':leginonconfig.DB_PROJECT_USER,
		'db':leginonconfig.DB_PROJECT_NAME,
		'passwd':leginonconfig.DB_PROJECT_PASS
	}


class Project(sqldict.ObjectBuilder):
	'''Project: a class object to access the
	`projects` table in the project DB
	'''
	table = 'projects'
	columns = ['projectId', 'name', 'short_description']

class ProjectExperiment(sqldict.ObjectBuilder):
	'''ProjectExperiment: a class object to access the
	`projectexperiments` table in the project DB
	'''
	table = "projectexperiments"
	columns = ['projectId', 'name']
	indices = [ ('projectId', ['projectId'] )]

class GridBox(sqldict.ObjectBuilder):
	table = 'gridboxes'
	columns = ['gridboxId', 'label']

class Grid(sqldict.ObjectBuilder):
	table = 'grids'
	columns = ['gridId', 'label', 'specimenId', 'number', 'boxId']

class GridLocation(sqldict.ObjectBuilder):
	table = 'gridlocations'
	columns = ['gridlocationId', 'gridboxId', 'gridId', 'location']

class ProjectData:
	def __init__(self, **kwargs):
		self.dbprojectconnection = False
		self.db = sqldict.SQLDict(**dbparams)
		if self.db.isConnected():
			self.dbprojectconnection = True

		self.projects = Project().register(self.db)
		self.projectexperiments = ProjectExperiment().register(self.db)
		self.gridboxes = GridBox().register(self.db)
		self.grids = Grid().register(self.db)
		self.gridlocations = GridLocation().register(self.db)

	def isConnected(self):
		return self.dbprojectconnection

	def getProjects(self):
		return self.projects

	def getProjectExperiments(self):
		return self.projectexperiments

	def getGridBoxes(self):
		return self.gridboxes

	def getGrids(self):
		return self.grids

	def newGrid(self, label, specimenId, number, boxId, location):
		gridId = self.grids.insert([{'label': label, 'specimenId': specimenId,
																	'number': number, 'boxId': boxId}])
		self.gridlocations.insert([{'gridboxId': boxId, 'gridId': gridId,
																'location': location}])

	def getGridLocations(self):
		return self.gridlocations

########################################
## Testing
########################################

if __name__ == "__main__":
	import sys
	# getall projects
	#allprojects = projects.getall()
	projectdata = ProjectData()
	if not projectdata.isConnected():
		print "Project DB not available"
		sys.exit()

	"""
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

