#!/usr/bin/env python

#python
import os
import shutil
#appion
import appionScript
import apStack
import apDisplay
import apEMAN

class centerStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
		self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("-m", "--mask", dest="mask", type="int",
			help="Outer mask")
		self.parser.add_option("-x", "--maxshift", dest="maxshift", type="int",
			help="Maximum shift")
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
		# add mask & maxshift to rundir if specifie
		if self.params['mask'] is not None:
			self.params['runname'] = self.params['runname']+"_"+str(self.params['mask'])
		if self.params['maxshift'] is not None:
			self.params['runname'] = self.params['runname']+"_"+str(self.params['maxshift'])
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])
		

	#=====================
	def start(self):
		#new stack path
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

		#make sure that old stack is numbered
		apEMAN.checkStackNumbering(oldstack)

		alignedstack = os.path.join(self.params['rundir'], 'ali.img')
		badstack = os.path.join(self.params['rundir'], 'bad.img')
		apStack.checkForPreviousStack(alignedstack)

		#run centering algorithm
		apStack.centerParticles(oldstack, self.params['mask'], self.params['maxshift'])
		self.params['keepfile'] = os.path.join(self.params['rundir'],'keepfile.txt')
		apEMAN.writeStackParticlesToFile(alignedstack, self.params['keepfile'])
		if not os.path.isfile(alignedstack, ):
			apDisplay.printError("No stack was created")

		#get number of particles
		f = open(self.params['keepfile'], "r")
		numparticles = len(f.readlines())
		f.close()
		self.params['description'] += (
			(" ... %d eman centered substack id %d" 
			% (numparticles, self.params['stackid']))
		)
		
		apStack.commitSubStack(self.params, newname='ali.hed', centered=True)
		apStack.averageStack(stack=alignedstack)
		if (os.path.exists(badstack)):
			apStack.averageStack(stack=badstack, outfile='badaverage.mrc')

#=====================
if __name__ == "__main__":
	cenStack = centerStackScript()
	cenStack.start()
	cenStack.close()

