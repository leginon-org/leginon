# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import sys
import time
#appion
from appionlib import apDisplay
import leginon.leginondata
from appionlib import apStack
import leginon.project
from appionlib import appiondata

#========================
def getProjectIdFromSessionName(sessionname):
	t0 = time.time()
	projectdata = leginon.project.ProjectData()
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
	sessiondata = leginon.leginondata.SessionData.direct_query(sessionid)
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
	alignstackdata = appiondata.ApAlignStackData.direct_query(alignstackid)
	stackid = alignstackdata['stack'].dbid
	projectid = getProjectIdFromStackId(stackid)
	return projectid

#========================
def getAppionDBFromProjectId(projectid):
	projectdata = leginon.project.ProjectData()
	projectdb = projectdata.getProcessingDB(projectid)
	return projectdb





