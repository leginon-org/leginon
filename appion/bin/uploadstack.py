#!/usr/bin/env python

#pythonlib
import os
import sys
import time
import shutil
#appion
import appionScript
import apDisplay
import apFile
import apProject
#leginon
import leginondata
import project
import leginonconfig

class UploadStack(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		standard appionScript
		"""
		### strings
		self.parser.add_option("--session", "--sessionname", dest="sessionname",
			help="Session name", metavar="NAME")
		self.parser.add_option("--file", dest="stackfile",
			help="Stack Imagic file (in Angstroms)", metavar="FILE")

		### floats
		self.parser.add_option("--diam", dest="diameter", type="float",
			help="Estimated diameter of partice (in Angstroms)", metavar="FILE")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Stack pixel size (in Angstroms)", metavar="#")

		### true / false
		self.parser.add_option("--ctf-corrected", dest="ctfcorrect", default=False,
			action="store_true", help="Particles are ctf corrected")
		self.parser.add_option("--not-ctf-corrected", dest="ctfcorrect", default=False,
			action="store_false", help="Particles are NOT ctf corrected")
		self.parser.add_option("--normalize", dest="normalize", default=False,
			action="store_true", help="Normalize particles")
		self.parser.add_option("--no-normalize", dest="normalize", default=False,
			action="store_false", help="Do NOT normalize particles")

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
		self.params['rundir'] = ???

	#=====================
	def start(self):
		info = self.readUploadInfo(self.batchinfo[imgnum])

		### copy stack to rundir
		newstack = os.path.join(self.params['rundir'], "start.hed")
		emancmd = "proc2d %s %s"%(self.params['stackfile'], newstack)
		self.params['normalize'] is True:
			emancmd += " edgenorm"
		apEMAN.executeEmanCmd(emancmd)

		### set final parameters
		self.boxsize = apFile.getBoxSize(newstack)
		self.numpart = apFile.numImagesInStack(newstack)

		self.params['commit'] = False
		self.createStackData()

	#=====================
	#===================== custom functions
	#=====================

	#=====================
	def createSession(self, user, name, description, directory):
		sys.exit(1)
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
		pathq = appionData.ApPathData()
		pathq['path'] = self.params['rundir']

		manq = appionData.ApManualParamsData()
		manq['diam'] = self.params['diameter']

		selectq = appionData.ApSelectionRunData()
		selectq['name'] = 'fakestack_'+self.params['runname']
		selectq['hidden'] = True
		selectq['path'] = pathq
		selectq['session'] = self.sessiondata
		selectq['manparams'] = manq

		stackq = appionData.ApStackData()
		stackq['name'] = "start.hed"
		stackq['path'] = pathq
		stackq['description'] = self.params['description']
		stackq['hidden'] = False
		stackq['pixelsize'] = self.params['apix']
		stackq['centered'] = False
		stackq['project|projects|project'] = self.params['projectid']

		stackparamq = appionData.ApStackParamsData()
		stackparamq['boxSize'] = self.boxsize
		stackparamq['bin'] = 1
		stackparamq['phaseFlipped'] = self.params['ctfcorrect']
		if self.params['ctfcorrect'] is True:
			stackparamq['fileType'] = "manual"
		stackparamq['fileType'] = "imagic"
		stackparamq['normalized'] = self.params['normalize']
		stackparamq['lowpass'] = 0
		stackparamq['highpass'] = 0

		stackrunq = appionData.ApStackRunData()
		stackrunq['stackRunName'] = self.params['runname']
		stackrunq['stackParams'] = stackparamq
		stackrunq['selectionrun'] = selectq
		stackrunq['session'] = self.sessiondata

		runsinstackq = appionData.ApRunsInStackData()
		runsinstackq['stack'] = stackq
		runsinstackq['stackRun'] = stackrunq
		runsinstackq['project|projects|project'] = self.params['projectid']

		if self.params['commit'] is True:
			runsinstackq.insert()

		### for each particle
		for i in range(self.numpart):
			partq = appionData.ApParticleData()
			partq['image'] = None  #We have no image, see if this works???
			partq['selectionrun'] = selectq
			partq['xcoord'] = int(i%1000)
			partq['ycoord'] = int(i/1000)
			partq['diameter'] = self.params['diameter']

			stackpartq = appionData.ApStackParticlesData()
			stackpartq['particleNumber'] = i+1
			stackpartq['stack'] = stackq
			stackpartq['stackRun'] = stackrunq
			stackpartq['particle'] = partq
			stackpartq['mean'] = 0.0
			stackpartq['stdev'] = 1.0

			if self.params['commit'] is True:
				stackpartq.insert()

#=====================
#=====================
#=====================
if __name__ == '__main__':
	uploadStack = UploadStack()
	uploadStack.start()
	uploadStack.close()




