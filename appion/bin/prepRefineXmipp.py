#!/usr/bin/env python

#appion
from appionlib import apPrepXmipp3D
from appionlib import apDisplay

class XmippPrepSingleRefinement(apPrepXmipp3D.XmippPrep3DRefinement):
	def setupParserOptions(self):
		super(XmippPrepSingleRefinement,self).setupParserOptions()
		self.parser.add_option("--maskVolId", dest="maskVolId", type="int",
			help="Arbitrary mask model id (0 outside protein, 1 inside). Arbitrary and spherical masks "
			+"are mutually exclusive")

	def setRefineMethod(self):
		self.refinemethod = 'xmipprecon'


	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("Xmipp projection match recon can take only one model")

	def processMaskVol(self,prepdata):
		if 'maskVolId' in self.params.keys() and self.params['maskVolId'] > 0:
			self.processModel(prepdata,self.params['maskVolId'],True)

#=====================
if __name__ == "__main__":
	app = XmippPrepSingleRefinement()
	app.start()
	app.close()

