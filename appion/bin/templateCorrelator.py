#!/usr/bin/env python

#pythonlib
import os
import sys
import re
import time
#appion
import particleLoop2
import apFindEM
import apDisplay
import apTemplate
import apDatabase
import appionData
import apPeaks
import apParam
import apImage


class TemplateCorrelationLoop(particleLoop2.ParticleLoop):
	##=======================
	def checkPreviousTemplateRun(self):
		### check if we have a previous selection run
		selectrunq = appionData.ApSelectionRunData()
		selectrunq['name'] = self.params['runname']
		selectrunq['session'] = sessiondata = apDatabase.getSessionDataFromSessionName(self.params['sessionname'])
		rundatas = selectrunq.query(results=1)
		if not rundatas:
			return True
		rundata = rundatas[0]

		### check if we have a previous template run
		templaterunq = appionData.ApTemplateRunData(selectionrun=rundata)
		templatedatas = templaterunq.query()
		if not templatedatas:
			return True

		### make sure of using same number of templates
		if len(self.params['templateIds']) != len(templatedatas):
			apDisplay.printError("different number of templates from last run")

		### make sure we have same rotation parameters
		for i, templateid in enumerate(self.params['templateIds']):
			templaterunq  = appionData.ApTemplateRunData()
			templaterunq['selectionrun'] = rundata
			templaterunq['template']     = appionData.ApTemplateImageData.direct_query(templateid)
			### this is wrong only check last template run not this run
			templatedata = templaterunq.query(results=1)[0]
			if ( templatedata['range_start'] != self.params["startang"+str(i+1)] or
				 templatedata['range_end']   != self.params["endang"+str(i+1)] or
				 templatedata['range_incr']  != self.params["incrang"+str(i+1)] ):
				print i+1, templateid
				print templatedata['range_start'], self.params["startang"+str(i+1)]
				print templatedata['range_end'], self.params["endang"+str(i+1)]
				print templatedata['range_incr'], self.params["incrang"+str(i+1)]
				apDisplay.printWarning("different template search ranges from last run")
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
		self.parser.add_option("--range-list", dest="rangeliststr",
			help="Start, end, and increment angles: e.g. 0,360,10x0,180,5", metavar="#,#,#x#,#,#")	

		### True / False options
		self.parser.add_option("--thread-findem", dest="threadfindem", default=False,
			action="store_true", help="Run findem crosscorrelation in threads")
		self.parser.add_option("--spectral", dest="spectral", default=False,
			action="store_true", help="Use spectral correlation instead of normal correlation")
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

		### Check if we have ranges
		if self.params['rangeliststr'] is None:
			apDisplay.printError("range not specified, please provide range in the order of templateIds")

		### Check that numbers of ranges and templates are equal
		rangestrlist = self.params['rangeliststr'].split('x')
		if len(self.params['templateIds']) != len(rangestrlist):
			apDisplay.printError("the number of templates and ranges do not match")



		

		### Parse range list
		i = 0
		for rangestr in rangestrlist:
			self.params['range'+str(i)] = rangestr
			angs = rangestr.split(",")
			if not len(angs) == 3:
				apDisplay.printError("the range is not defined correctly")
			self.params['startang'+str(i+1)] = float(angs[0])
			self.params['endang'+str(i+1)]   = float(angs[1])
			self.params['incrang'+str(i+1)]  = float(angs[2])
			self.params['mirror'+str(i+1)]  = False
			if self.params['templatemirrors'] is True:
				i+=1
				self.params['startang'+str(i+1)] = float(angs[0])
				self.params['endang'+str(i+1)]   = float(angs[1])
				self.params['incrang'+str(i+1)]  = float(angs[2])
				self.params['mirror'+str(i+1)]  = True
			i+=1		
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

	##=======================
	def processImage(self, imgdata, filtarray):
		if abs(self.params['apix'] - self.params['templateapix']) > 0.01:
			#rescale templates, apix has changed
			apTemplate.getTemplates(self.params)

		### RUN FindEM

		### save filter image to .dwn.mrc
		imgpath = os.path.join(self.params['rundir'], imgdata['filename']+".dwn.mrc")
		apImage.arrayToMrc(filtarray, imgpath, msg=False)

		### run FindEM
		looptdiff = time.time()-self.proct0
		self.proct0 = time.time()
		if self.params['spectral'] is True:
			ccmaplist = apFindEM.runSpectralFindEM(imgdata, self.params, thread=self.params['threadfindem'])
		else:
			ccmaplist = apFindEM.runFindEM(imgdata, self.params, thread=self.params['threadfindem'])	
		proctdiff = time.time()-self.proct0
		f = open("template_image_timing.dat", "a")
		datstr = "%d\t%.5f\t%.5f\n"%(self.stats['count'], proctdiff, looptdiff)
		f.write(datstr)
		f.close()

		### find peaks in map
		peaktree  = apPeaks.findPeaks(imgdata, ccmaplist, self.params)

		return peaktree

	##=======================
	def getParticleParamsData(self):
		selectparamsq = appionData.ApSelectionParamsData()
		return selectparamsq

	##=======================
	def commitToDatabase(self, imgdata, rundata):
		#insert template rotation data
		for i, templateid in enumerate(self.params['templateIds']):
			templaterunq = appionData.ApTemplateRunData()
			templaterunq['selectionrun'] = rundata	
			templaterunq['template']     = appionData.ApTemplateImageData.direct_query(abs(templateid))
			templaterunq['range_start']  = self.params["startang"+str(i+1)]
			templaterunq['range_end']    = self.params["endang"+str(i+1)]
			templaterunq['range_incr']   = self.params["incrang"+str(i+1)]
			templaterunq['mirror']   = self.params["mirror"+str(i+1)]
			if self.params['commit'] is True:
				templaterunq.insert()
		return


if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

