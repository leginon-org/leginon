#!/usr/bin/env python

#python
import sys
import os
import time
#appion
from appionlib import appionScript
from appionlib import apStack
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apStackMeanPlot
from appionlib.apTilt import apTiltPair
from pyami import mem, mrc

class TiltPairStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --known-stack=# --full-stack=# [options]")

		### integers
		self.parser.add_option("--known-stack", dest="knownstackid", type="int",
			help="Known Stack ID in the tilt pair", metavar="#")
		self.parser.add_option("--full-stack", dest="fullstackid", type="int",
			help="Stack ID to be filtered", metavar="#")

		### floats

		### choices
		self.parser.add_option("--no-meanplot", dest="meanplot", default=True,
			action="store_false", help="Do not create a mean/stdev plot")

	#=====================
	def checkConflicts(self):
		### check and make sure we got the stack id
		if self.params['knownstackid'] is None:
			apDisplay.printError("need a stackid to duplicate")
		if self.params['fullstackid'] is None:
			apDisplay.printError("full stack ID to filter was not defined")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['fullstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.abspath(path))

		self.params['rundir'] = os.path.join(uppath, self.params['runname'] )

	#=====================
	def getGoodParticles(self):
		'''
		Get particle numbers in eman format in fullstack that
		has tilt pair in knownstack
		'''
		includeParticle = []
		tiltParticlesData = []
		no_match_count = 0
		apDisplay.printMsg("Finding particles from tilt pairs ")
		
		### get stack data
		knownstackid = self.params['knownstackid']
		fullstackid = self.params['fullstackid']
		numpartl = apStack.getNumberStackParticlesFromId(self.params['knownstackid'])
		for partnum in range(1,numpartl+1):
			stpartdata = apStack.getStackParticle(knownstackid, partnum, True)
			# stpartdata and otherpartdata are related by tilt transform
			imgnum, transformdata, otherpartdata = apTiltPair.getTiltTransformFromParticle(stpartdata['particle'])
			apDisplay.printMsg('Mapping particle %d to %d' % (stpartdata['particle'].dbid,otherpartdata.dbid))
			fullstackpartdata = apStack.getStackParticleFromData(fullstackid, otherpartdata, True)
			if fullstackpartdata:
				# eman particle number starts from 0, appion database number starts from 1
				emantiltstackpartnum = fullstackpartdata['particleNumber']-1
				includeParticle.append(emantiltstackpartnum)
				tiltParticlesData.append(fullstackpartdata)
			else:
				no_match_count += 1
		apDisplay.printWarning('There are %d particles without a match in the requested full stack' % no_match_count)
		return includeParticle, tiltParticlesData

	#=====================
	def start(self):
		knownstackdata = apStack.getOnlyStackData(self.params['knownstackid'])
		fullstackdata = apStack.getOnlyStackData(self.params['fullstackid'])

		### get good particle numbers
		includeParticle, tiltParticlesData = self.getGoodParticles()
		self.numpart = len(includeParticle)

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile"+self.timestamp+".lst")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### make new stack of tilted particle from that run
		fullstackfile = os.path.join(fullstackdata['path']['path'], fullstackdata['name'])
		sb = os.path.splitext(fullstackdata['name'])
		newname = "tiltpairsub%d" % self.params['knownstackid']+sb[-1]
		newstackfile = os.path.join(self.params['rundir'], newname)
		apFile.removeStack(newstackfile, warn=False)
		apStack.makeNewStack(fullstackfile, newstackfile, self.params['keepfile'])
		if not os.path.isfile(newstackfile):
			apDisplay.printError("No stack was created")
		self.params['stackid'] = self.params['fullstackid']
		apStack.commitSubStack(self.params, newname, sorted=False)
		apStack.averageStack(stack=newstackfile)
		newstackid = apStack.getStackIdFromPath(newstackfile)
		if self.params['meanplot'] is True:
			apDisplay.printMsg("creating Stack Mean Plot montage for stackid")
			apStackMeanPlot.makeStackMeanPlot(newstackid)


#=====================
if __name__ == "__main__":
	app = TiltPairStackScript()
	app.start()
	app.close()


