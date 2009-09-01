#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

#python
import os
import sys
import re
import pprint
import time
import shutil
#appion
import appionScript
import apTemplate
import apStack
import apDisplay
import apDatabase
import appiondata
import apEMAN
import apFile
import apProject

#=====================
class uploadTemplateScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
			+"--description='<text>' [options]")

		### required info
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Template pixel size in Angstroms per pixel", metavar="FLOAT")
		self.parser.add_option("--diam", dest="diam", type="int",
			help="Approximate diameter of particle (in Angstroms)", metavar="INT")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="INT")

		### optional input methods
		self.parser.add_option("-t", "--template", dest="template",
			help="Filename of the template (wild cards accepted)", metavar="FILE")
		self.parser.add_option("--alignid", dest="alignid", type="int",
			help="ID for particle alignment (optional)", metavar="INT")
		self.parser.add_option("--clusterid", dest="clusterid", type="int",
			help="ID for particle clustering (optional)", metavar="INT")
		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="INT")

		### img number list
		self.parser.add_option("--imgnums", dest="imgnums",
			help="Particle numbers in stack, e.g. 0,15,3", metavar="LIST")
		self.parser.add_option("--avgstack", dest="avgstack", default=False,
			action="store_true", help="Average all particles in stack for template")

	#=====================
	def checkConflicts(self):
		### make sure the necessary parameters are set
		if self.params['description'] is None:
			apDisplay.printError("enter a template description")
		if self.params['diam'] is None:
			apDisplay.printError("enter the particle diameter in Angstroms")

		### make sure we have something
		if (self.params['template'] is None
		  and self.params['stackid'] is None
		  and self.params['clusterid'] is None
		  and self.params['alignid'] is None
		):
			apDisplay.printError("enter a template root name (wild cards are valid)")

		### check if apix is needed
		if (self.params['apix'] is None
		  and self.params['stackid'] is None
		  and self.params['clusterid'] is None
		  and self.params['alignid'] is None
		):
			apDisplay.printError("enter a pixel size")

		### check for session
		if self.params['session'] is None:
			if self.params['alignid'] is not None:
				alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignid'])
				stackid = alignstackdata['stack'].dbid
				sessiondata = apStack.getSessionDataFromStackId(stackid)
				self.params['session'] = sessiondata['name']
			elif self.params['stackid'] is not None:
				stackid = self.params['stackid']
				sessiondata = apStack.getSessionDataFromStackId(stackid)
				self.params['session'] = sessiondata['name']
			elif self.params['alignid'] is not None:
				clusterstackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
				stackid = clusterstackdata['clusterrun']['alignstack']['stack'].dbid
				sessiondata = apStack.getSessionDataFromStackId(stackid)
				self.params['session'] = sessiondata['name']
		if self.params['session'] is  None:
			apDisplay.printError("Could not find session")

		if self.params['template'] is not None:
			self.params['template'] = os.path.abspath(self.params['template'])

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
		apDisplay.printMsg("Using stack to make templates")
		sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
		self.params['session'] = sessiondata['name']
		self.params['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		self.params['templatelist'] = []

		if self.params['avgstack'] is True:
			### averaging all particles together
			apDisplay.printMsg("Averaging all images in stack")
			templatename = "stack%d-average.mrc"%(self.params['stackid'])
			oldtemplatepath = os.path.join(stackdata['path']['path'], "average.mrc")
			abstemplatepath = os.path.join(stackdata['path']['path'], templatename)
			if os.path.isfile(oldtemplatepath):
				shutil.copy(oldtemplatepath, abstemplatepath)
			else:
				### average all images using proc2d
				emancmd = "proc2d %s %s average" % (stackfile, abstemplatepath)
				apEMAN.executeEmanCmd(emancmd)
			if os.path.isfile(abstemplatepath):
				self.params['templatelist'] = [abstemplatepath]

		elif self.params['imgnums'] is not None:
			### check to see if stackimagenum is within the boundary of the stack
			numpart = apFile.numImagesInStack(stackfile)
			for i in self.params['imgnums'].split(","):
				partnum = int(i)
				if partnum > numpart or partnum < 0:
					apDisplay.printError("'imgnums' is NOT within the boundary of the stack: %d > %d"%(partnum,numpart))
				apDisplay.printMsg("Extracting image %d from stack" % partnum)
				templatename = "stack%d-particle%d.mrc"%(self.params['stackid'],partnum)
				abstemplatepath= os.path.join(stackdata['path']['path'], templatename)
				### run proc2d with params['stackimgnum']
				emancmd = "proc2d %s %s first=%d last=%d" % (stackfile, abstemplatepath, partnum, partnum)
				###  create template
				apDisplay.printMsg("creating "+templatename)
				apEMAN.executeEmanCmd(emancmd)
				if os.path.isfile(abstemplatepath):
					self.params['templatelist'].append(abstemplatepath)

	#=====================
	def useAlignForTemplate(self):
		apDisplay.printMsg("Using alignment stack to make templates")
		alignstackdata = appiondata.ApAlignStackData.direct_query(self.params['alignid'])
		self.params['apix'] = alignstackdata['pixelsize']
		stackfile = os.path.join(alignstackdata['path']['path'], alignstackdata['refstackfile'])
		self.params['templatelist'] = []
		stackid = alignstackdata['stack'].dbid
		sessiondata = apStack.getSessionDataFromStackId(stackid)
		self.params['session'] = sessiondata['name']

		### check to see if stackimagenum is within the boundary of the stack
		numpart = apFile.numImagesInStack(stackfile)
		for i in self.params['imgnums'].split(","):
			partnum = int(i)
			if partnum > numpart or partnum < 0:
				apDisplay.printError("'imgnums' is NOT within the boundary of the stack: %d > %d"%(partnum,numpart))
			apDisplay.printMsg("Extracting image %d from align stack" % partnum)
			templatename = "align%d-average%d.mrc"%(self.params['alignid'],partnum)
			abstemplatepath= os.path.join(alignstackdata['path']['path'], templatename)
			### run proc2d with params['stackimgnum']
			emancmd = "proc2d %s %s first=%d last=%d" % (stackfile, abstemplatepath, partnum, partnum)
			###  create template
			apDisplay.printMsg("creating "+templatename)
			apEMAN.executeEmanCmd(emancmd)
			if os.path.isfile(abstemplatepath):
				self.params['templatelist'].append(abstemplatepath)

	#=====================
	def useClusterForTemplate(self):
		apDisplay.printMsg("Using clustering stack to make templates")
		clusterstackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		self.params['apix'] = clusterstackdata['clusterrun']['alignstack']['pixelsize']
		stackfile = os.path.join(clusterstackdata['path']['path'], clusterstackdata['avg_imagicfile'])
		self.params['templatelist'] = []
		stackid = clusterstackdata['clusterrun']['alignstack']['stack'].dbid
		sessiondata = apStack.getSessionDataFromStackId(stackid)
		self.params['session'] = sessiondata['name']

		### check to see if stackimagenum is within the boundary of the stack
		numpart = apFile.numImagesInStack(stackfile)
		for i in self.params['imgnums'].split(","):
			partnum = int(i)
			if partnum > numpart or partnum < 0:
				apDisplay.printError("'imgnums' is NOT within the boundary of the stack: %d > %d"%(partnum,numpart))
			apDisplay.printMsg("Extracting image %d from cluster stack" % partnum)
			templatename = "cluster%d-average%d.mrc"%(self.params['clusterid'],partnum)
			abstemplatepath= os.path.join(clusterstackdata['path']['path'], templatename)
			### run proc2d with params['stackimgnum']
			emancmd = "proc2d %s %s first=%d last=%d" % (stackfile, abstemplatepath, partnum, partnum)
			###  create template
			apDisplay.printMsg("creating "+templatename)
			apEMAN.executeEmanCmd(emancmd)
			if os.path.isfile(abstemplatepath):
				self.params['templatelist'].append(abstemplatepath)

	#=====================
	def start(self):
		if self.params['stackid'] is not None:
			self.useStackForTemplate()
		elif self.params['alignid'] is not None:
			self.useAlignForTemplate()
		elif self.params['clusterid'] is not None:
			self.useClusterForTemplate()
		else:
			apDisplay.printMsg("Using local file: '"+str(self.params['template'])+"' to upload template")
			#find the number of template files
			apTemplate.findTemplates(self.params)

		### check for templates
		apDisplay.printColor("Template List:","green")
		pprint.pprint(self.params['templatelist'])
		if not self.params['templatelist']:
			apDisplay.printError("Could not find templates")

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



