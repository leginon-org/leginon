#!/usr/bin/env python
import os
import shutil

#appion
from appionlib import apPrepRefine
from appionlib import apDisplay
from appionlib import apVolume

class EmanPrep3DRefinement(apPrepRefine.Prep3DRefinement):
	def setRefineMethod(self):
		self.refinemethod = 'emanrecon'

	def checkPackageConflicts(self):
		if len(self.modelids) != 1:
			apDisplay.printError("EMAN projection match can only take one model")

	def setFormat(self):
		self.stackspidersingle = False
		self.modelspidersingle = False

	def convertRefineModelIcosSymmetry(self,modelname,extname,modelfile,apix):
		# EMAN uses (5 3 2) only
		symmetry_description = self.model['data']['symmetry']['symmetry']
		tempfile = os.path.join(self.params['rundir'], "temp.%s" % (extname))
		if '(2 3 5)' in symmetry_description:
			apVolume.viper2eman(modelfile, tempfile, apix=self.stack['apix'])
			shutil.copy(tempfile,modelfile)
		if '(2 5 3)' in symmetry_description:
			apVolume.crowther2eman(modelfile, tempfile, apix=self.stack['apix'])
			shutil.copy(tempfile,modelfile)

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

