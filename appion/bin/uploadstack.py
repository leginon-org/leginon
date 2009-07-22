#!/usr/bin/env python

#pythonlib
import os
import shutil
import time
import numpy
import math
#appion
import appionScript
import apDatabase
import apDisplay
import apProject
#leginon
import gui.wx.SetupWizard
import leginondata
import project
import leginonconfig
#pyami
from pyami import mrc, jpg

class UploadStack(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		self.parser.add_option("--session", "--sessionname", dest="sessionname",
			help="Session name", metavar="NAME")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Stack pixel size (in Angstroms)", metavar="#")
		self.parser.add_option("--file", dest="stackfile",
			help="Stack Imagic file (in Angstroms)", metavar="FILE")

	#=====================
	def checkConflicts(self):
		"""
		standard appionScript
		"""
		if self.params['stackfile'] is None:
			apDisplay.printError("Please provide a stack file, e.g., --file=/home/myfile.hed")
		if not os.path.isfile(self.params["stackfile"]):
			apDisplay.printError("Could not find stack file: %s"%(self.params["stackfile"]))

		if self.params['apix'] is None:
			apDisplay.printError("Please provide a stack pixel size (in Angstroms), e.g., --apix=1.55")
		if self.params['sessionname'] is None:
			apDisplay.printError("Please provide a Session name, e.g., --session=09feb12b")
		if self.params['projectid'] is None:
			apDisplay.printError("Please provide a Project database ID, e.g., --projectid=42")
		if self.params['description'] is None:
			apDisplay.printError("Please provide a Description, e.g., --description='awesome data'")

		#This really is not conflict checking but to set up new session.
		#There is no place in Appion script for this special case

	#=====================
	def onInit(self):
		"""
		standard appionScript
		"""
		sessionq = leginondata.SessionData(name=self.params['sessionname'])
		sessiondatas = sessionq.query()
		if len(sessiondatas) > 0:
			### METHOD 1 : session already exists
			apDisplay.printColor("Add images to an existing session", "cyan")
			sessiondata = sessiondatas[0]
			### what about linking an existing session with project id to a new project id
			oldprojectid = apProject.getProjectIdFromSessionName(self.params['sessionname'])
			if oldprojectid != self.params['projectid']:
				apDisplay.printError("You cannot assign an existing session (PID %d) to a different project (PID %d)"%
					(oldprojectid, self.params['projectid']))
		else:
			### METHOD 2 : create new session
			apDisplay.printColor("Creating a new session", "cyan")
			### die for now
			sys.exit(1)
			try:
				directory = leginonconfig.mapPath(leginonconfig.IMAGE_PATH)
			except AttributeError:
				apDisplay.printWarning("Could not set directory")
				directory = ''
			if self.params['userid'] is not None:
				userdata = leginondata.UserData.direct_query(self.params['userid'])
			else:
				userdata = None
			sessiondata = self.createSession(userdata, self.params['sessionname'], self.params['description'], directory)
			self.linkSessionProject(sessiondata, self.params['projectid'])

		self.sessiondata = sessiondata
		return

	#=====================
	def setRunDir(self):
		"""
		standard appionScript
		"""	
		self.params['rundir'] = self.session['image path']

	#=====================
	def start(self):
		info = self.readUploadInfo(self.batchinfo[imgnum])

		### copy stack to rundir
		oldstackroot = os.path.basename(self.params['stackfile'])[:-4]
		oldstackhed = oldstackroot+".hed"
		oldstackimg = oldstackroot+".img"
		newstackhed = os.path.join(self.params['rundir'], "start.hed")
		newstackimg = os.path.join(self.params['rundir'], "start.img")
		if not os.path.isfile(oldstackhed):
			apDisplay.printError("Could not find file: "+oldstackhed)
		shutil.copy(oldstackhed,newstackhed)
		if not os.path.isfile(oldstackimg):
			apDisplay.printError("Could not find file: "+oldstackimg)
		shutil.copy(oldstackimg,newstackimg)

	#=====================
	#===================== custom functions
	#=====================

	#=====================
	def createSession(self, user, name, description, directory):
		imagedirectory = os.path.join(leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
		initializer = {
			'name': name,
			'comment': description,
			'user': user,
			'image path': imagedirectory,
		}
		sessionq = leginondata.SessionData(initializer=initializer)
		return self.publish(sessionq)

	#=====================
	def linkSessionProject(self, sessiondata, projectid):
		if self.projectdata is None:
			raise RuntimeError('Cannot link session, not connected to database.')
		projectsession = project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

	#=====================
	def createStackData(self):
		appionData.ApStackData()
		appionData.ApStackRunData()
		appionData.ApStackParamsData()
		appionData.ApRunsInStackData()


#=====================
#=====================
#=====================
if __name__ == '__main__':
	uploadStack = UploadStack()
	uploadStack.start()
	uploadStack.close()




