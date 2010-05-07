# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import sys
import time
#appion
from appionlib import apDisplay
from appionlib import apStack
from appionlib import appiondata
import sinedon
import leginon.projectdata
import leginon.leginondata

#========================
def getProjectIdFromSessionData(sessiondata):
	projq = leginon.projectdata.projectexperiments()
	projq['session'] = sessiondata
	projdatas = projq.query(results=1)
	if not projdatas:
		apDisplay.printError("could not find project for session "+sessionname)	
	projdata = projdatas[0]
	projectid = projdata['project'].dbid
	return projectid

#========================
def getProjectIdFromSessionId(sessionid):
	sessiondata = leginon.leginondata.SessionData.direct_query(sessionid)
	projectid = getProjectIdFromSessionData(sessiondata)
	return projectid

#========================
def getProjectIdFromSessionName(sessionname):
	t0 = time.time()
	### get session
	sessiondata = getSessionDataFromSessionName(sessionname)

	### get project
	projectid = getProjectIdFromSessionData(sessiondata)

	apDisplay.printMsg("Found project id="+str(projectid)+" for session "+sessionname
		+" in "+apDisplay.timeString(time.time()-t0))
	return projectid

#========================
def getSessionDataFromSessionName(sessionname):
	t0 = time.time()
	### get session
	sessionq = leginon.leginondata.SessionData()
	sessionq['name'] = sessionname
	sessiondatas = sessionq.query(results=1)
	if not sessiondatas:
		apDisplay.printError("could not find session "+sessionname)	
	sessiondata = sessiondatas[0]
	return sessiondata

#========================
def getSessionIdFromSessionName(sessionname):
	sessiondata = getSessionDataFromSessionName(sessionname)
	sessionid = sessiondata.dbid
	return sessionid

#========================
def getProjectIdFromStackId(stackid):
	sessiondata = apStack.getSessionDataFromStackId(stackid)
	projectid = getProjectIdFromSessionData(sessiondata)
	return projectid

#========================
def getProjectIdFromAlignStackId(alignstackid):
	alignstackdata = appiondata.ApAlignStackData.direct_query(alignstackid)
	stackid = alignstackdata['stack'].dbid
	projectid = getProjectIdFromStackId(stackid)
	return projectid

#========================
def getAppionDBFromProjectId(projectid):
	projdata = leginon.projectdata.projects.direct_query(projectid)
	processingdbq = leginon.projectdata.processingdb()
	processingdbq['project'] = projdata
	procdatas = processingdbq.query(results=1)
	if not procdatas:
		apDisplay.printError("could not find appion db name for project %d "%(projectid))
	procdata = procdatas[0]
	dbname = procdata['appiondb']
	return dbname

#========================
def setDBfromProjectId(projectid):
	newdbname = getAppionDBFromProjectId(projectid)
	sinedon.setConfig('appiondata', db=newdbname)
	apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")


