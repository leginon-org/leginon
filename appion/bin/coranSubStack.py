#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apRecon
from appionlib import apStackMeanPlot


class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [options]")

		### Ints
		self.parser.add_option("-i", "--iterid", dest="iterid", type="int",
			help="iteration id", metavar="ID")

	#=====================
	def checkConflicts(self):
		### check for missing and duplicate entries
		if self.params['iterid'] is None:
			apDisplay.printError("Please provide --iterid")
		if self.params['description'] is None:
			apDisplay.printError("Please provide --description")
		if self.params['runname'] is None:
			apDisplay.printError("Please provide --runname")

		### get the stack ID from the other IDs
		self.iterdata = appiondata.ApRefinementData.direct_query(self.params['iterid'])
		self.params['stackid'] = apStack.getStackIdFromRecon(self.iterdata['refinementRun'].dbid)
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'])

		### check and make sure we got the stack id
		if self.params['stackid'] is None:
			apDisplay.printError("Could not find stackid from iterid")

	#=====================
	def setRunDir(self):
		path = self.stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))
		self.params['rundir'] = os.path.join(uppath, self.params['runname'])

	#=====================
	def start(self):
		### new stack path
		oldstack = os.path.join(self.stackdata['path']['path'], self.stackdata['name'])
		newstack = os.path.join(self.params['rundir'], self.stackdata['name'])
		apStack.checkForPreviousStack(newstack)

		### get particles from stack
		apDisplay.printMsg("Querying stack particles")
		t0 = time.time()
		stackpartq =  appiondata.ApParticleClassificationData()
		stackpartq['refinement'] = self.iterdata
		particles = stackpartq.query()
		apDisplay.printMsg("Finished in "+apDisplay.timeString(time.time()-t0))

		### write included particles to text file
		includeParticle = []
		excludeParticle = 0
		f = open("test.log", "w")
		count = 0
		apDisplay.printMsg("Processing stack particles")
		t0 = time.time()
		for part in particles:
			count += 1
			if count%500 == 0:
				sys.stderr.write(".")
			emanstackpartnum = part['particle']['particleNumber']-1

			if part['coran_keep'] == 1:
				### good particle
				includeParticle.append(emanstackpartnum)
				f.write("%d\t%d\tinclude\n"%(count, emanstackpartnum))
			else:
				### bad particle
				excludeParticle += 1
				f.write("%d\t%d\texclude\n"%(count, emanstackpartnum))
		sys.stderr.write("\n")
		apDisplay.printMsg("Finished in "+apDisplay.timeString(time.time()-t0))

		f.close()
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))
			+" and excluding "+str(excludeParticle)+" particles")

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### get number of particles
		numparticles = len(includeParticle)
		self.params['description'] += ( " ... %d no jumpers substack" % (numparticles,))

		### create the new sub stack
		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])

		if not os.path.isfile(newstack):
			apDisplay.printError("No stack was created")

		apStack.averageStack(stack=newstack)
		if self.params['commit'] is True:
			apStack.commitSubStack(self.params)
			newstackid = apStack.getStackIdFromPath(newstack)
			apStackMeanPlot.makeStackMeanPlot(newstackid, gridpoints=6)


#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()


