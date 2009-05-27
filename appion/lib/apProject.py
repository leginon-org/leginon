# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import sys
import time
#appion
import apDisplay
import leginondata
import apStack
import project
import appionData

#========================
def getProjectIdFromSessionName(sessionname):
	t0 = time.time()
	projectdata = project.ProjectData()
	projects = projectdata.getProjectExperiments()
	projectid = None
	for i in projects.getall():
		if i['name'] == sessionname:
			projectid = i['projectId']
	if not projectid:
		apDisplay.printError("no project associated with session "+sessionname)
	apDisplay.printMsg("Found project id="+str(projectid)+" for session "+sessionname
		+" in "+apDisplay.timeString(time.time()-t0))
	return projectid

#========================
def getProjectIdFromSessionId(sessionid):
	sessiondata = leginondata.SessionData.direct_query(sessionid)
	sessionname = sessiondata['name']
	projectid = getProjectIdFromSessionName(sessionname)
	return projectid

#========================
def getProjectIdFromStackId(stackid):
	sessiondata = apStack.getSessionDataFromStackId(stackid)
	sessionname = sessiondata['name']
	projectid = getProjectIdFromSessionName(sessionname)	
	return projectid

#========================
def getProjectIdFromAlignStackId(alignstackid):
	alignstackdata = appionData.ApAlignStackData.direct_query(alignstackid)
	stackid = alignstackdata['stack'].dbid
	projectid = getProjectIdFromStackId(stackid)	
	return projectid

#========================
def getAppionDBFromProjectId(projectid):
	projectdata = project.ProjectData()
	projectdb = projectdata.getProcessingDB(projectid)
	return projectdb




