#!/usr/bin/env python

"""
Kernel Probability Density Estimator Self-Organizing Map
"""

import appionScript
import apDisplay

#======================
#======================
class kerdenSOMScript(appionScript.AppionScript):
	#======================
	def setupParserOptions(self):
		self.parser.add_option("-a", "--alignstackid", dest="alignstackid",
			help="Alignment stack id", metavar="##")

	#======================
	def checkConflicts(self):
		if self.params['alignstackid'] is None:
			apDisplay.printError("Please enter an aligned stack id, e.g. --alignstackid=4")

	#======================
	def setRunDir(self):
		self.params['rundir'] = os.getcwd()

	#======================
	def start(self):
		apDisplay.printMsg("Hey this works")

#======================
#======================
if __name__ == '__main__':
	kerdenSOM = kerdenSOMScript()
	kerdenSOM.start()
	kerdenSOM.close()

