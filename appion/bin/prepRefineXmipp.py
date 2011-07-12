#!/usr/bin/env python

#appion
from appionlib import apPrepXmipp3D
from appionlib import apDisplay

class XmippPrepSingleRefinement(apPrepXmipp3D.XmippPrep3DRefinement):
	def setRefineMethod(self):
		self.refinemethod = 'xmipprecon'


	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("Xmipp projection match recon can take only one model")

#=====================
if __name__ == "__main__":
	app = XmippPrepSingleRefinement()
	app.start()
	app.close()

