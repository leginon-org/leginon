#!/usr/bin/env python

#pythonlib
import os
import re
import sys
import time
import shutil
#appion
from appionlib import appionScript
from appionlib import apFile
from appionlib import apEMAN
from appionlib import apStack
from appionlib import apProject
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
#leginon
#import leginon.leginondata
import leginon.project
import leginon.leginonconfig

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
		### check for stack file
		if self.params['stackfile'] is None:
			apDisplay.printError("Please provide a stack file, e.g., --file=/home/myfile.hed")
		if not os.path.isfile(self.params["stackfile"]):
			apDisplay.printError("Could not find stack file: %s"%(self.params["stackfile"]))
		if self.params["stackfile"][-4:] == ".hed" and not os.path.isfile(self.params["stackfile"][:-4]+".img"):
			apDisplay.printError("Could not find stack file: %s"%(self.params["stackfile"][:-4]+".img"))
		if self.params["stackfile"][-4:] == ".img" and not os.path.isfile(self.params["stackfile"][:-4]+".hed"):
			apDisplay.printError("Could not find stack file: %s"%(self.params["stackfile"][:-4]+".hed"))

		### check for parameters
		if self.params['apix'] is None:
			apDisplay.printError("Please provide a stack pixel size (in Angstroms), e.g., --apix=1.55")
		if self.params['apix'] < 1e-3 or self.params['apix'] > 1e5:
			apDisplay.printError("Please provide a REASONABLE stack pixel size (in Angstroms), e.g., --apix=1.55")
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
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if sessiondata:
			### METHOD 1 : session already exists
			apDisplay.printColor("Add images to an existing session", "cyan")
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
				directory = leginon.leginonconfig.mapPath(leginon.leginonconfig.IMAGE_PATH)
			except AttributeError:
				apDisplay.printWarning("Could not set directory")
				directory = ''
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
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		if not sessiondata:
			apDisplay.printError("Could not find session "+self.params['sessionname'])
		self.sessiondata = sessiondata
		path = os.path.abspath(self.sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		path = os.path.join(path, self.processdirname, self.params['runname'])
		self.params['rundir'] = path

	#=====================
	def setProcessingDirName(self):
		self.processdirname = "stacks"

	#=====================
	def start(self):
		### copy stack to rundir
		newstack = os.path.join(self.params['rundir'], "start.hed")
		if os.path.isfile(newstack):
			apDisplay.printError("Stack already exists")
		emancmd = "proc2d %s %s"%(self.params['stackfile'], newstack)
		if self.params['normalize'] is True:
			emancmd += " edgenorm"
		apEMAN.executeEmanCmd(emancmd)

		### set final parameters
		boxsize = apFile.getBoxSize(newstack)
		print "Boxsize: ",boxsize
		if not boxsize or boxsize <= 0:
			apDisplay.printError("Could not determine stack size")
		else:
			self.boxsize = boxsize[0]
		self.numpart = apFile.numImagesInStack(newstack)
		print "Num part: ",self.numpart
		if not self.numpart or self.numpart <= 0:
			apDisplay.printError("Could not determine number of particles")
		if self.numpart <= 4:
			apDisplay.printError("Not enough particles to upload")

		apStack.averageStack(newstack)

		#self.params['commit'] = False
		self.createStackData()

	#=====================
	#===================== custom functions
	#=====================

	#=====================
	def createSession(self, user, name, description, directory):
		sys.exit(1)
		imagedirectory = os.path.join(leginon.leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
		initializer = {
			'name': name,
			'comment': description,
			'user': user,
			'image path': imagedirectory,
		}
		sessionq = leginon.leginondata.SessionData(initializer=initializer)
		return self.publish(sessionq)

	#=====================
	def linkSessionProject(self, sessiondata, projectid):
		if self.projectdata is None:
			raise RuntimeError('Cannot link session, not connected to database.')
		projectsession = leginon.project.ProjectExperiment(projectid, sessiondata['name'])
		experiments = self.projectdata.getProjectExperiments()
		experiments.insert([projectsession.dumpdict()])

	#=====================
	def createStackData(self):
		apDisplay.printColor("Starting upload of stack", "blue")

		pathq = appiondata.ApPathData()
		pathq['path'] = self.params['rundir']

		manq = appiondata.ApManualParamsData()
		manq['diam'] = self.params['diameter']

		selectq = appiondata.ApSelectionRunData()
		selectq['name'] = 'fakestack_'+self.params['runname']
		selectq['hidden'] = True
		selectq['path'] = pathq
		selectq['session'] = self.sessiondata
		selectq['manparams'] = manq

		stackq = appiondata.ApStackData()
		stackq['name'] = "start.hed"
		stackq['path'] = pathq
		stackq['description'] = self.params['description']
		stackq['hidden'] = False
		stackq['pixelsize'] = self.params['apix']*1e-10
		stackq['centered'] = False

		stackparamq = appiondata.ApStackParamsData()
		stackparamq['boxSize'] = self.boxsize
		stackparamq['bin'] = 1
		stackparamq['phaseFlipped'] = self.params['ctfcorrect']
		if self.params['ctfcorrect'] is True:
			stackparamq['fileType'] = "manual"
		stackparamq['fileType'] = "imagic"
		stackparamq['normalized'] = self.params['normalize']
		stackparamq['lowpass'] = 0
		stackparamq['highpass'] = 0

		stackrunq = appiondata.ApStackRunData()
		stackrunq['stackRunName'] = self.params['runname']
		stackrunq['stackParams'] = stackparamq
		stackrunq['selectionrun'] = selectq
		stackrunq['session'] = self.sessiondata

		runsinstackq = appiondata.ApRunsInStackData()
		runsinstackq['stack'] = stackq
		runsinstackq['stackRun'] = stackrunq

		if self.params['commit'] is True:
			runsinstackq.insert()

		### for each particle
		sys.stderr.write("Starting particle upload")
		for i in range(self.numpart):
			if i % 100 == 0:
				sys.stderr.write(".")
			partq = appiondata.ApParticleData()
			partq['image'] = None  #We have no image, see if this works???
			partq['selectionrun'] = selectq
			partq['xcoord'] = int(i%1000)
			partq['ycoord'] = int(i/1000)
			partq['diameter'] = self.params['diameter']

			stackpartq = appiondata.ApStackParticlesData()
			stackpartq['particleNumber'] = i+1
			stackpartq['stack'] = stackq
			stackpartq['stackRun'] = stackrunq
			stackpartq['particle'] = partq
			stackpartq['mean'] = 0.0
			stackpartq['stdev'] = 1.0

			if self.params['commit'] is True:
				stackpartq.insert()

		sys.stderr.write("\n")
		return

#=====================
#=====================
#=====================
if __name__ == '__main__':
	uploadStack = UploadStack()
	uploadStack.start()
	uploadStack.close()





