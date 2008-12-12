#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

#python
import os
import sys
import re
import pprint
import time
#appion
import appionScript
import apUpload
import apTemplate
import apStack
import apDisplay
import apDatabase
import appionData
import apEMAN
import apProject

#=====================
class uploadTemplateScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
			+"--description='<text>' [options]")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Template pixel size in Angstroms per pixel", metavar="FLOAT")
		self.parser.add_option("--diam", dest="diam", type="int",
			help="Approximate diameter of particle (in Angstroms)", metavar="INT")
		self.parser.add_option("-t", "--template", dest="template",
			help="Filename of the template (wild cards accepted)", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="INT")
		self.parser.add_option("--norefid", dest="norefid", type="int",
			help="ID for reference-free alignment (optional)", metavar="INT")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")
		self.parser.add_option("--stackimgnum", dest="stackimgnum", type="int",
			help="Particle number in stack", metavar="INT")
		self.parser.add_option("--avgstack", dest="avgstack", default=False,
			action="store_true", help="Average all particles in stack for template")

	#=====================
	def checkConflicts(self):
		# make sure the necessary parameters are set
		if self.params['stackid'] is None and self.params['apix'] is None:
			apDisplay.printError("enter a pixel size")
		if self.params['diam'] is None:
			apDisplay.printError("enter the particle diameter in Angstroms")
		if self.params['stackid'] is not None and self.params['norefid'] is not None:
			apDisplay.printError("only one of either stackid or norefid can be used, NOT both")
		if self.params['template'] is None and self.params['stackid'] is None and self.params['norefid'] is None:
			apDisplay.printError("enter a template root name (wild cards are valid)")
		if self.params['template'] is not None:
			self.params['template'] = os.path.abspath(self.params['template'])
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID")
		if self.params['description'] is None:
			apDisplay.printError("enter a template description")

	#=====================
	def setRunDir(self):
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path,"templates")

	#=====================
	def useStackForTemplate(self):
		apDisplay.printMsg("Using stack to make template")
		### get stack data (path, file)
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		if self.params['apix'] is None:
			self.params['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		stackpath = stackdata['path']['path']
		stackname = stackdata['name']
		absstackpath = os.path.join(stackpath, stackname)
		abstemplatepath = None

		### averaging all files together
		if self.params['avgstack'] is True:
			apDisplay.printMsg("Averaging all images in stack")
			templatename = "template"+str(self.params['stackid'])+"avg.mrc"
			abstemplatepath = os.path.join(stackpath,templatename)
			### average all images using proc2d
			emancmd = "proc2d %s %s average" % (absstackpath, abstemplatepath)
		elif self.params['stackimgnum'] is not None:
			### check to see if stackimagenum is within the boundary of the stack
			# there has to be a faster way of doing this... -neil
			stacksize = len(apStack.getStackParticlesFromId(self.params['stackid']))
			num = self.params['stackimgnum']
			if num > stacksize or num < 0:
				apDisplay.printError("'stackimagenum' is NOT within the boundary of the stack: 0->"+str(stacksize))
			apDisplay.printMsg("Extracting image %i from stack" % self.params['stackimgnum'])
			templatename = "template"+str(self.params['stackimgnum'])+".mrc"
			abstemplatepath= os.path.join(stackpath,templatename)
			### run proc2d with params['stackimgnum']
			emancmd = "proc2d %s %s first=%i last=%i" % (absstackpath, abstemplatepath, num, num)
		else:
			apDisplay.printError("could not create template from stack specify either 'stackimgnum' or 'avgstack'")

		###  create template
		apDisplay.printMsg("creating "+templatename+" in "+stackpath+"...\n")
		apEMAN.executeEmanCmd(emancmd)
		self.params['templatelist'] = []
		self.params['templatelist'].append(abstemplatepath)

	#=====================
	def useRefFreeForTemplate(self):
		apDisplay.printMsg("Using reference-free class to make template")
		norefClassdata = appionData.ApNoRefClassRunData.direct_query(self.params['norefid'])
		
		#Get class average file path through ApNoRefRunData
		norefRun=norefClassdata['norefRun']
		norefpath = norefRun['path']['path']
		norefname = norefRun['name']
		#norefpath = os.path.join(norefpath, norefname)
				
		#Get class average file name
		norefClassFile = norefClassdata['classFile']
		norefClassFile+=".img"

		#complete path of the class average file
		absnorefpath = os.path.join(norefpath, norefClassFile)
		apDisplay.printMsg("noref class file: "+absnorefpath)

		#get the num of classes
		classnum = norefClassdata['num_classes']
		imgnum = self.params['stackimgnum']	

		#make sure that params['stackimgnum'] is less than the num of classes
		if imgnum > classnum or imgnum < 0:
				apDisplay.printError("'stackimagenum' is NOT within the boundary of the stack: 0->"+str(classnum))

		templatename = "template"+str(imgnum)+".mrc"
		abstemplatepath= os.path.join(norefpath, templatename)

		#run proc2d with params['stackimgnum']
		apDisplay.printMsg("creating "+templatename+" in "+norefpath+"...\n")
		emancmd = "proc2d %s %s first=%i last=%i" % (absnorefpath, abstemplatepath, imgnum, imgnum)
		apEMAN.executeEmanCmd(emancmd)
		
		#Add file names to params['templatelist']
		self.params['templatelist'] = []
		self.params['templatelist'].append(abstemplatepath)

	#=====================
	def start(self):
		if self.params['stackid'] is not None:
			self.useStackForTemplate()
		elif self.params['norefid'] is not None:
			self.useRefFreeForTemplate()
		else:
			apDisplay.printMsg("Using local file: '"+str(self.params['template'])+"' to upload template")
			#find the number of template files
			apTemplate.findTemplates(self.params)

		apDisplay.printColor("Template List:","green")
		pprint.pprint(self.params['templatelist'])
		time.sleep(2)

		# copy templates to final location
		apTemplate.copyTemplatesToOutdir(self.params, self.timestamp)

		self.params['projectId'] = apProject.getProjectIdFromSessionName(self.params['session'])

		# insert templates to database
		apTemplate.insertTemplateImage(self.params)

#=====================
if __name__ == "__main__":
	uploadTemplate = uploadTemplateScript()
	uploadTemplate.start()
	uploadTemplate.close()

	
