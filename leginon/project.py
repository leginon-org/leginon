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
	'''Project: a class object to access the
	`projects` table in the project DB
	'''
	table = 'gridboxes'
	columns = ['gridboxId', 'label']

class ProjectData:
	def __init__(self, **kwargs):
		self.dbprojectconnection = False
		self.db = sqldict.SQLDict(**dbparams)
		if self.db.isConnected():
			self.dbprojectconnection = True

		self.projects = Project().register(self.db)
		self.projectexperiments = ProjectExperiment().register(self.db)
		self.gridboxes = GridBox().register(self.db)

	def isConnected(self):
		return self.dbprojectconnection

	def getProjects(self):
		return self.projects

	def getProjectExperiments(self):
		return self.projectexperiments

	def getGridBox(self):
		return self.gridboxes

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
	projects = projectdata.getProjects()
	print projects.getall()
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

