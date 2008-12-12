#!/usr/bin/env python

#pythonlib
import os
import sys
import re
#appion
import particleLoop2
import apFindEM
import apImage
import apDisplay
import apTemplate
import apDatabase
import appionData
import apPeaks
import apParticle
import apParam
#legacy
#import apViewIt
#import selexonFunctions  as sf1

class TemplateCorrelationLoop(particleLoop2.ParticleLoop):

	def preLoopFunctions(self):
		apTemplate.getTemplates(self.params)

	def particleProcessImage(self, imgdata):
		imgname = imgdata['filename']
		if abs(self.params['apix'] - self.params['templateapix']) > 0.01:
			#rescale templates, apix has changed
			apTemplate.getTemplates(self.params)
		### RUN FindEM
		if 'method' in self.params and self.params['method'] == "experimental":
			#ccmaplist = sf2.runCrossCorr(params,imgname)
			#peaktree  = apPeaks.findPeaks(imgdata, ccmaplist, self.params)
			sys.exit(1)
		else:
			ccmaplist = apFindEM.runFindEM(imgdata, self.params)
			peaktree  = apPeaks.findPeaks(imgdata, ccmaplist, self.params)
		return peaktree

	def getParticleParamsData(self):
		selectparamsq = appionData.ApSelectionParamsData()
		return selectparamsq

	def particleCommitToDatabase(self, imgdata):
		runq=appionData.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session']
		runnames = runq.query(results=1)

		if apTemplate.checkTemplateParams(runnames[0], self.params) is True:
			#insert template params
			for n in range(len(self.params['templateIds'])):
				apTemplate.insertTemplateRun(self.params, runnames[0], n)
		return

	def particleCommitToDatabaseRealRef(self, imgdata):
		runq=appionData.ApSelectionRunData()
		runq['name'] = self.params['runname']
		runq['session'] = imgdata['session']
		runnames = runq.query(results=1)

		if apTemplate.checkTemplateParams(runnames[0], self.params) is True:
			#insert template params
			for n in range(len(self.params['templateIds'])):
				apTemplate.insertTemplateRun(self.params, runnames[0], n)
		return

	def setupParserOptions(self):
		self.parser.add_option("--templateIds", dest="templateIds", 
			help="Template Ids")
		self.parser.add_option("--method", dest="method",
			help="Method")
		self.parser.add_option("--ranges", dest="ranges",
			help="List of start angle, end angle and angle increment: e.g. 0,360,10;0,180,5")
		self.parser.add_option("--mapdir", dest="mapdir", default="ccmaxmaps",
			help="mapdir")
		self.parser.add_option("--templateapix", dest="templateapix", default=None,
			help="Template apix")		
		### True / False options
		self.parser.add_option("--multiple_range", dest="multiple_range", default=False,
			action="store_true", help="more than one range is specified")
		self.parser.add_option("--keepall", dest="keepall", default=False,
			action="store_true", help="keep all")
		return
	
	def checkConflicts(self):
		if not self.params['templateIds']:
			apDisplay.printError("templateIds not specified, please run uploadTemplate.py")
		else:
			self.params['templateIds'] = self.params['templateIds'].split(',')

		### Check ranges to make sure it corresponds to the number of template and parse it accordingly
		if not self.params['ranges']:
			apDisplay.printError("range not specified, please provide range in the order of templateIds")
		else:
			ranges = self.params['ranges'].split('x')
			
			if not len(self.params['templateIds']) == len(ranges):
				apDisplay.printError("the number of templates and ranges do not match")
			
			num = 0
			for r in ranges:
				num+=1
				angs = r.split(',')
				if not len(angs) == 3:
					apDisplay.printError("the range is not defined correctly")
					
				self.params['startang'+str(num)]=int(angs[0])
				self.params['endang'+str(num)]=int(angs[1])
				self.params['incrang'+str(num)]=int(angs[2])
			
			if num > 1:	
				self.params['multiple_range']=True
		return

	def postLoopFunctions(self):
		if not self.params['keepall']:
			apParam.removefiles(self.params['rundir'],(self.params['sessionname'],'dwn.mrc'))
		return

if __name__ == '__main__':
	imgLoop = TemplateCorrelationLoop()
	imgLoop.run()

