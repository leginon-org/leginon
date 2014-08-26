#!/usr/bin/env python

#appion
from appionlib import apFindEMG
from appionlib import apTemplateCorrelator


class TemplateCorrelationGLoop(apTemplateCorrelator.TemplateCorrelationLoop):
	def setupParserOptions(self):
		super(TemplateCorrelationGLoop,self).setupParserOptions()
		self.parser.add_option("--ccsearchmult", dest="ccsearchmult", type="float", default=1.0,
			help="Distance of cross-correlation peak search in terms of the diameter", metavar="FLOAT")
		self.parser.add_option("--gcdev", dest="gcdev", type="int", default=0,
			help="Device number for the graphic card", metavar="INT")
		return

	def runTemplateCorrelator(self,imgdata):
		ccfilelist = apFindEMG.runFindEM(imgdata, self.params, thread=self.params['threadfindem'])
		return ccfilelist

	def findPeaks(self,imgdata,cclist):
		### find peaks in map
		return apFindEMG.findPeaks(imgdata, cclist, self.params)

if __name__ == '__main__':
	imgLoop = TemplateCorrelationGLoop()
	imgLoop.run()



#do nothing, just testing

