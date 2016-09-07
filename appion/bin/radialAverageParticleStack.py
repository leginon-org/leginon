#!/usr/bin/env python

#python
import os
import shutil
#pyami
from pyami import imagefun
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apImagicFile

class RadialAverageStackScript(appionScript.AppionScript):
	"""
	AppionScript to create radial averaged image on each particle in the
	particle stack.
	"""

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--new-stack-name", dest="runname",
			help="New stack name", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")
		if self.params['description'] is None:
			apDisplay.printError("substack description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

		#make sure that old stack is numbered
		apEMAN.checkStackNumbering(oldstack)

		processed_stack = os.path.join(self.params['rundir'], 'r_avg.img')
		apStack.checkForPreviousStack(processed_stack)

		numpart = apFile.numImagesInStack(oldstack)

		for p in range(1,numpart+1):	
			a = apImagicFile.readSingleParticleFromStack(oldstack, p)
			ravg = imagefun.radialAverageImage(a)
			# TO DO: may need to write first particle differently
			apImagicFile.appendParticleToStackFile(ravg, processed_stack)
		#run centering algorithm
		if not os.path.isfile(processed_stack, ):
			apDisplay.printError("No stack was created")

		included = range(numpart)
		apStack.commitSubStack(self.params, newname='r_avg.hed', radial_averaged=True, included=included)
		apStack.averageStack(stack=processed_stack)

#=====================
if __name__ == "__main__":
	cenStack = RadialAverageStackScript()
	cenStack.start()
	cenStack.close()

