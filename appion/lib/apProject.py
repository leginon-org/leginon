# FUNCTIONS THAT WORK ON TEMPLATES

#pythonlib
import os
import shutil
import math
import re
import time
import numpy
import sys
import glob
import pprint
#import numarray.convolve as convolve
#appion
import apImage
import apFile
import apParam
import apDisplay
import apDatabase
import apDB
import appionData
import project

appiondb = apDB.apdb


#========================
def getProjectIdFromSessionName(sessionname):
	projectdata = project.ProjectData()
	projects = projectdata.getProjectExperiments()
	for i in projects.getall():
		if i['name'] == sessionname:
			projectid = i['projectId']
	if not projectid:
		apDisplay.printError("no project associated with session "+sessionname)
	apDisplay.printMsg("Found project id="+str(projectid)+" for session "+sessionname)
	return projectid



#========================
def getProjectIdFromSessionId(sessionid):

	return projectid





#========================
def getProjectIdFromStackId(stackid):

	return projectid




