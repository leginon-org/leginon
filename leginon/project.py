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

db = sqldict.SQLDict(**dbparams)

class Project(sqldict.ObjectBuilder):
	'''Project: a class object to access the
	`projects` table in the project DB
	'''
	table = 'projects'
	columns = ['projectId', 'name', 'short_description']
projects = Project().register(db)

class ProjectExperiment(sqldict.ObjectBuilder):
	'''ProjectExperiment: a class object to access the
	`projectexperiments` table in the project DB
	'''
	table = "projectexperiments"
	columns = ['projectId', 'name']
projectexperiments = ProjectExperiment().register(db)

########################################
## Testing
########################################

if __name__ == "__main__":
	# getall projects
	allprojects = projects.getall()
	print allprojects

	# getall experiment name with his projectId
	allprojectexperiments = projectexperiments.getall()
	print allprojectexperiments

	# insert a new session into the Test  Project database
	# newsession = ProjectExperiment(5, 'testexp')

	# if the session already exists, it won't be inserted again,
	# the existing primary will be returned. The function 
	# returns the last inserted id for a new insert
	#key = projectexperiments.insert([newsession.dumpdict()])
	#print key
