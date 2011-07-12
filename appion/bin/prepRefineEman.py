#!/usr/bin/env python

#appion
from appionlib import apPrepRefine
from appionlib import apDisplay

class EmanPrep3DRefinement(apPrepRefine.Prep3DRefinement):
	def setRefineMethod(self):
		self.refinemethod = 'emanrecon'

	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("EMAN projection match can only take one model")

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	def addStackToSend(self,hedfilepath):
		# Imagic Format stack has 'hed' and 'img' files
		self.addToFilesToSend(hedfilepath)
		imgfilepath = hedfilepath.replace('hed','img')
		self.addToFilesToSend(imgfilepath)

#=====================
if __name__ == "__main__":
	app = EmanPrep3DRefinement()
	app.start()
	app.close()

