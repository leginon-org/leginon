#!/usr/bin/env python
import sqldict


# connection to the project database
db = sqldict.SQLDict(host="cronus1", user="usr_object", db="project")

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

'''
# getall projects
allprojects = projects.getall()
print allprojects


# insert a new session into the Test  Project database
newsession = ProjectExperiment(5, 'testexp')

# if the session already exists, it won't be inserted again,
# the existing primary will be returned. The function 
# returns the last inserted id for a new insert
key = projectexperiments.insert([newsession.dumpdict()])
print key
'''
