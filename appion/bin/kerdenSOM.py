#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
"""

import appionScript
import apXmipp
import apDisplay

#======================
#======================
class kerdenSOMScript(appionScript.AppionScript):
	#======================
	def setupParserOptions(self):
		self.parser.add_option("-a", "--alignstackid", dest="alignstackid",
			help="Alignment stack id", metavar="##")
		self.parser.add_option("-m", "--maskrad", dest="maskrad",
			help="Mask radius in Angstroms", metavar="##")

	#======================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("Please enter an aligned stack id, e.g. --alignstackid=4")

	#======================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#======================
	def runKerdenSOM(self):
		"""
		From http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM

		KerDenSOM stands for "Kernel Probability Density Estimator Self-Organizing Map".
		It maps a set of high dimensional input vectors into a two-dimensional grid.
		"""
		kerdencmd = "xmipp_classify_kerdensom "

	#======================
	def start(self):
		apDisplay.printMsg("Hey this works")
		apXmipp.convertImagesToXmippData()
		self.runKerdenSOM()

#======================
#======================
if __name__ == '__main__':
	kerdenSOM = kerdenSOMScript()
	kerdenSOM.start()
	kerdenSOM.close()

