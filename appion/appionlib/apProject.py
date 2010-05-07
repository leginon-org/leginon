# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import sys
import time
#appion
from appionlib import apDisplay
import leginon.leginondata
from appionlib import apStack
import leginon.projectdata
from appionlib import appiondata
import sinedon

#========================
def getProjectIdFromSessionName(sessionname):
	t0 = time.time()
	### get session
	sessionq = leginon.leginondata.SessionData()
	sessionq['name'] = sessionname
	sessiondatas = sessionq.query(results=1)
	if not sessiondatas:
		apDisplay.printError("could not find session "+sessionname)	
	sessiondata = sessiondatas[0]

	### get project
	projq = leginon.projectdata.projects()
	projq['session'] = sessiondata
	projdatas = projq.query(results=1)
	if not projdatas:
		apDisplay.printError("could not find project for session "+sessionname)	
	projdata = projdatas[0]
	projectid = projdata.dbid

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

#========================
def setDBfromProjectId(projectid):
	newdbname = getAppionDBFromProjectId(projectid)
	sinedon.setConfig('appiondata', db=newdbname)
	apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")


