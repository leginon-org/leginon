#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
#appion
import appionScript
import apStack
import apDisplay
import apDB
import appionData
import apEMAN
from apTilt import apTiltPair
from apSpider import operations, backproject

appiondb = apDB.apdb

class subStackScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --norefclass=ID --tilt-stack=# --classnum=# [options]")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("--classnum", dest="classnum", type="int",
			help="Class number to use for rct volume, e.g. 0,1,2", metavar="#")
		self.parser.add_option("--tilt-stack", dest="tiltstackid", type="int",
			help="Tilted Stack ID", metavar="#")
		self.parser.add_option("--norefclass", dest="norefclassid", type="int",
			help="noref class id", metavar="ID")
		self.parser.add_option("--runname", dest="runname",
			help="Run name", metavar="ID")
		self.parser.add_option("--num-iters", dest="numiters", type="int", default=6, 
			help="number of tilted image shift refinement iterations", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['classnum'] is None:
			apDisplay.printError("class number was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['norefclassid'] is None:
			apDisplay.printError("noref class ID was not defined")
		if self.params['tiltstackid'] is None:
			apDisplay.printError("tilt stack ID was not defined")
		
		#get the stack ID from the noref class ID
		self.norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		norefRun = self.norefclassdata['norefRun']
		self.params['notstackid'] = norefRun['stack'].dbid
		if self.params['notstackid'] is None:
			apDisplay.printError("untilted stackid was not defined")

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['tiltstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['outdir'] = os.path.join(uppath, "rctvolume", self.params['runname'])

	#=====================
	def getParticleNoRefInPlaneRotation(self, stackpartdata):
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		classpartq['noref_particle']['particle'] = stackpartdata
		classpartdatas = classpartq.query(results=1)
		if not classpartdatas or len(classpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation")
		inplane = classpartdatas[0]['noref_particle']['rotation']
		return inplane

	#=====================
	def start(self):
		### get stack data
		notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])

		### get particles from noref class run
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		classpartdatas = classpartq.query()

		### get good particle numbers
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("sorting particles")
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			notstackpartnum = classpart['noref_particle']['particle']['particleNumber']
			tiltstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['notstackid'], 
				notstackpartnum, self.params['tiltstackid'])
			if tiltstackpartdata is None:
				nopairParticle += 1
			elif classnum == self.params['classnum']:
				emantiltstackpartnum = tiltstackpartdata['particleNumber']-1
				includeParticle.append(emanstackpartnum)
				tiltParticlesData.append(tiltstackpartdata)
			else:
				excludeParticle += 1
		includeParticle.sort()
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding \n\t"
			+str(excludeParticle)+" particles with "+str(nopairParticle)+" unpaired particles")
		if len(includeParticle) < 1:
			apDisplay.printError("No particles were kept")
		#print includeParticle

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['outdir'], "keepfile-"+self.timestamp+".list")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### make new stack of tilted particle from that run
		tiltstackfile = os.path.join(tiltstackdata['path']['path'], tiltstackdata['name'])
		rctstackfile = os.path.join(self.params['outdir'], "rctstack-"+self.timestamp+".hed")
		apStack.makeNewStack(tiltstackfile, rctstackfile, self.params['keepfile'])

		### make doc file of Euler angles
		count = 0
		eulerfile = os.path.join(self.params['outdir'], "eulersdoc001.spi")
		eulerf = open(eulerfile, "w")
		for stackpartdata in tiltParticlesData:
			count += 1
			gamma, theta, phi, tiltangle = apTiltPair.getParticleTiltRotationAngles(stackpartdata)
			inplane = self.getParticleNoRefInPlaneRotation(stackpartdata)
			psi = -1.0*(gamma + inplane)
			line = operations.spiderOutputLine3(count, phi, tiltangle, psi)
			eulerf.write(line)
		eulerf.close()
		
		### iterations over volume creation
		for iternum in range(self.params['numiters']):
			### back project particles into volume	
			### project volume
			### re-align particles volume
			apDisplay.printError("end of line")

		### optimize Euler angles

#=====================
if __name__ == "__main__":
	subStack = subStackScript()
	subStack.start()
	subStack.close()

