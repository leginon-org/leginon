#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import time
import subprocess
import numpy
from pyami import mrc
#appion
from appionlib import particleLoop2
from appionlib import apDisplay
from appionlib import apTemplate
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apPeaks
from appionlib import apParam
from appionlib import apImage
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apSignature

class SignaturePickerLoop(particleLoop2.ParticleLoop):
	##=======================
	def checkPreviousTemplateRun(self):
		### check if we have a previous selection run
		selectrunq = appiondata.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['session'] = sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		rundatas = selectrunq.query(results=1)
		if not rundatas:
			return True
		rundata = rundatas[0]

		### check if we have a previous template run
		templaterunq = appiondata.ApTemplateRunData(selectionrun=rundata)
		templatedatas = templaterunq.query()
		if not templatedatas:
			return True

		### make sure of using same number of templates
		if len(self.params['templateIds']) != len(templatedatas):
			apDisplay.printError("different number of templates from last run")

		### make sure we have same rotation parameters
		for i, templateid in enumerate(self.params['templateIds']):
			templaterunq  = appiondata.ApTemplateRunData()
			templaterunq['selectionrun'] = rundata
			templaterunq['template']     = appiondata.ApTemplateImageData.direct_query(templateid)
			### this is wrong only check last template run not this run
			templatedata = templaterunq.query(results=1)[0]
		return True

	##################################################
	### COMMON FUNCTIONS
	##################################################

	##=======================
	def setRunDir(self):
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		path = os.path.join(path, self.processdirname, self.params['runname'])
		self.params['rundir'] = path

	##=======================
	def setupParserOptions(self):
		self.parser.add_option("--template-list", dest="templateliststr",
			help="Template Ids", metavar="#,#" )

		### True / False options
		self.parser.add_option("--use-mirrors", dest="templatemirrors", default=False,
			action="store_true", help="Use mirrors as additional templates")

		return

	##=======================
	def checkConflicts(self):
		if self.params['thresh'] is None:
			apDisplay.printError("threshold was not defined")

		### Check if we have templates
		if self.params['templateliststr'] is None:
			apDisplay.printError("template list was not specified, e.g. --template-list=34,56,12")

		### Parse template list
		oldtemplateids = self.params['templateliststr'].split(',')
		self.params['templateIds'] = []
		for tid in oldtemplateids:
			templateid = abs(int(tid))
			self.params['templateIds'].append(templateid)
			if self.params['templatemirrors'] is True:
				self.params['templateIds'].append(-1*templateid)

		return

	##=======================
	def preLoopFunctions(self):
		if len(self.imgtree) > 0:
			self.params['apix'] = apDatabase.getPixelSize(self.imgtree[0])
		# CREATES TEMPLATES
		# SETS params['templatelist'] AND self.params['templateapix']
		apTemplate.getTemplates(self.params)
		apDisplay.printColor("Template list: "+str(self.params['templatelist']), "cyan")
		self.checkPreviousTemplateRun()

		# convert templates to single mrc stack for signature
		tstack="templatestack.mrc"
		twods=[]
		for t in self.params['templatelist']:
			twods.append(mrc.read(t))
		imgar=numpy.array(twods)
		mrc.write(imgar, tstack)
		self.params['templatename']=tstack

	##=======================
	def processImage(self, imgdata, filtarray):
		if abs(self.params['apix'] - self.params['templateapix']) > 0.01:
			#rescale templates, apix has changed
			apTemplate.getTemplates(self.params)

		### RUN Signature

		### save filter image to .dwn.mrc
		imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".dwn.mrc")
		apImage.arrayToMrc(filtarray, imgpath, msg=False)

		### run Signature
		looptdiff = time.time()-self.proct0
		self.proct0 = time.time()
		plist = apSignature.runSignature(imgdata, self.params)
		proctdiff = time.time()-self.proct0
		f = open("template_image_timing.dat", "a")
		datstr = "%d\t%.5f\t%.5f\n"%(self.stats['count'], proctdiff, looptdiff)
		f.write(datstr)
		f.close()

		# convert list of particles to peaktree
		peaktree = apSignature.partToPeakTree(plist,self.params['bin'])
		return peaktree 

	##=======================
	def getParticleParamsData(self):
		selectparamsq = appiondata.ApSelectionParamsData()
		return selectparamsq

	##=======================
	def commitToDatabase(self, imgdata, rundata):
		#insert template data
		for i, templateid in enumerate(self.params['templateIds']):
			templaterunq = appiondata.ApTemplateRunData()
			templaterunq['selectionrun'] = rundata
			templaterunq['template']     = appiondata.ApTemplateImageData.direct_query(abs(templateid))
			templaterunq['mirror'] = self.params["templatemirrors"]
			if self.params['commit'] is True:
				templaterunq.insert()
		return


if __name__ == '__main__':
	imgLoop = SignaturePickerLoop()
	imgLoop.run()


