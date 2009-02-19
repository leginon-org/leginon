#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

#python
import os
import sys
import re
import pprint
import time
import shutil
import subprocess
#appion
import appionScript
import apUpload
import apTemplate
import apStack
import apDisplay
import apDatabase
import leginondata
import appionData
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
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="INT")

		### optional input methods
		self.parser.add_option("-t", "--templatestack", dest="templatestack",
			help="Filename of the template stack", metavar="FILE")
		self.parser.add_option("--clusterId", dest="clusterId", type="int",
			help="ID for particle clustering (optional)", metavar="INT")
		self.parser.add_option("--templatetype", dest="templatetype", type="str",
                        help="the type of template stack (i.e. class averages or forward projections)", metavar="STR")
		self.parser.add_option("--newname", "--name", dest="newname", type="str",
                        help="new name of the template stack, as it will be stored in the templatestacks directory", metavar="STR")
		self.parser.add_option("--apix", dest="apix", type="float",
                        help="angstroms per pixel of the file", metavar="FLOAT")
		self.parser.add_option("--boxsize", dest="boxsize", type="float",
                        help="boxsize of the file", metavar="FLOAT")

	#=====================
	def checkConflicts(self):
		### make sure the necessary parameters are set
		if self.params['description'] is None:
			apDisplay.printError("enter a template description")
		if self.params['templatestack'] is None:
			apDisplay.printError("enter a template stack file")
		if self.params['templatetype'] is None:
			apDisplay.printError("enter the template type (i.e. class averages / forward projections)")
		if self.params['newname'] is None:
			templatestacksq = appionData.ApTemplateStackData()
			templatestacks = templatestacksq.query()
			num_templatestacks = len(templatestacks)
			new_num = num_templatestacks + 1
			self.params['newname'] = "templatestack"+str(new_num)+"_"+str(self.params['session'])

		### get apix value
		if (self.params['apix'] is None and self.params['clusterId'] is None):
			apDisplay.printError("Enter value for angstroms per pixel")
		
		### get boxsize if not specified
		if self.params['boxsize'] is None:
			emancmd = "iminfo "+self.params['templatestack']	
			proc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			results = proc.stdout
			proc.wait() 
			for line in results:
				res = re.search("([0-9]+)x([0-9]+)x([0-9])", line)
				if res:
					num1 = int(res.groups()[0])
					num2 = int(res.groups()[1])
					if num1 == num2:
						self.params['boxsize'] = num1

		### check for session
		if self.params['session'] is None:
			if self.params['clusterId'] is not None:
				clusterdata = appionData.ApClusteringStackData.direct_query(self.params['clusterId'])
				stackid = clusterdata['clusterrun']['alignstack']['stack'].dbid 
				sessiondata = apStack.getSessionDataFromStackId(stackid)
				self.params['session'] = sessiondata['name']
		if self.params['session'] is None:
			apDisplay.printError("Could not find session")
		
		if self.params['templatestack'] is not None:
			self.params['templatestack'] = os.path.abspath(self.params['templatestack'])

	#=====================
	def setRunDir(self):
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path,"templatestacks")

	#=====================
	def uploadTemplateStack(self, insert=False):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
	
		uploadq = appionData.ApTemplateStackData()
		uploadq['project|projects|project'] = self.params['projectid']
		if self.params['clusterId'] is not None:
			uploadq['clusterstack'] = self.params['clusterId']
		uploadq['origfile'] = self.params['templatestack']
		uploadq['templatename'] = self.params['newname']
		if self.params['templatetype'] == "clsavg":
			uploadq['cls_avgs'] = True
		if self.params['templatetype'] == "forward_proj":
			uploadq['forward_proj'] = True
		uploadq['description'] = self.params['description']
		uploadq['session'] = sessiondata
		uploadq['apix'] = self.params['apix']
		uploadq['boxsize'] = self.params['boxsize']
		uploadq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.join(self.params['rundir'], "templatestacks")))
		if insert is True:
			uploadq.insert()

	#=======================
	def start(self):
		print self.params
		if self.params['clusterId'] is not None:
			self.useClusterForTemplateStack()
		else:
			apDisplay.printMsg("Using local file: '"+str(self.params['templatestack'])+"' to upload template")

		# copy templates to final location
		if str(self.params['templatestack'])[-4:] == (".img" or ".hed"):
			self.params['templatestack'] = self.params['templatestack'][:-4]
		if str(self.params['newname'])[-4:] == (".img" or ".hed"):
			self.params['newname'] = self.params['newname'][:-4]
		shutil.copyfile(str(self.params['templatestack'])+".img", os.path.join(self.params['rundir'], str(self.params['newname'])+".img"))
		shutil.copyfile(str(self.params['templatestack'])+".hed", os.path.join(self.params['rundir'], str(self.params['newname'])+".hed"))

		# insert templates to database
		if self.params['commit'] is True:
			self.uploadTemplateStack(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

#=====================
if __name__ == "__main__":
	uploadTemplate = uploadTemplateScript()
	uploadTemplate.start()
	uploadTemplate.close()

	
