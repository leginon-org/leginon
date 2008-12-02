# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import sys
import time
#appion
import apDisplay
import apDB
import leginondata
import apStack
import project
import appionData

appiondb = apDB.apdb
leginondb = apDB.db

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
	sessiondata = leginondb.direct_query(leginondata.SessionData, sessionid)
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
	alignstackdata = appiondb.direct_query(appionData.ApAlignStackData, self.params['alignstackid'])
	stackid = alignstackdata['stack'].dbid
	projectid = getProjectIdFromStackId(stackid)	
	return projectid




