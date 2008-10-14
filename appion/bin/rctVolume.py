#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
#appion
import appionScript
import apStack
import apDisplay
import apDB
import appionData
import apEMAN
import apFile
from apTilt import apTiltPair
from apSpider import operations, backproject

appiondb = apDB.apdb

class rctVolumeScript(appionScript.AppionScript):
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
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float",
			help="low pass volume filter (in Angstroms)", metavar="#")

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
		if self.params['radius'] is None:
			apDisplay.printError("particle radius was not defined")
		
		#get the stack ID from the noref class ID
		self.norefclassdata = appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclassid'])
		norefRun = self.norefclassdata['norefRun']
		self.params['notstackid'] = norefRun['stack'].dbid
		if self.params['notstackid'] is None:
			apDisplay.printError("untilted stackid was not defined")
		boxsize = apStack.getStackBoxsize(self.params['notstackid'])
		if self.params['radius']*2 > boxsize-2:
			apDisplay.printError("particle radius is too big for stack boxsize")	

	#=====================
	def setOutDir(self):
		stackdata = apStack.getOnlyStackData(self.params['tiltstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		self.params['outdir'] = os.path.join(uppath, "rctvolume", self.params['runname'])

	#=====================
	def getParticleNoRefInPlaneRotation(self, stackpartdata):
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'], 
			stackpartdata['particleNumber'], self.params['notstackid'])
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		norefpartq = appionData.ApNoRefAlignParticlesData()
		norefpartq['particle'] = notstackpartdata
		classpartq['noref_particle'] = norefpartq
		classpartdatas = classpartq.query(results=1)
		if not classpartdatas or len(classpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation")
		inplane = classpartdatas[0]['noref_particle']['rotation']
		return inplane

	#=====================
	def convertStackToSpider(self, emanstackfile):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		emancmd  = "proc2d "
		if not os.path.isfile(emanstackfile):
			apDisplay.printError("stackfile does not exist: "+emanstackfile)
		emancmd += emanstackfile+" "

		spiderstack = os.path.join(self.params['outdir'], "rctstack0.spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "
		
		#emancmd += "apix="+str(self.stack['apix'])+" "
		#if self.params['lowpass'] > 0:
		#	emancmd += "lp="+str(self.params['lowpass'])+" "
		#emancmd += "last="+str(self.params['numpart']-1)+" "
		#emancmd += "shrink="+str(self.params['bin'])+" "
		#clipsize = int(math.floor(self.stack['boxsize']/self.params['bin'])*self.params['bin'])
		#emancmd += "clip="+str(clipsize)+","+str(clipsize)+" "
		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack

	#=====================
	def sortTiltParticlesData(self, a, b):
		if a['particleNumber'] > b['particleNumber']:
			return 1
		return -1

	#=====================
	def start(self):
		### get stack data
		notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])

		### get particles from noref class run
		classpartq = appionData.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		classpartdatas = classpartq.query()
		apDisplay.printMsg("Found "+str(len(classpartdatas))+" particles in the norefRun")

		### get good particle numbers
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("sorting particles")
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			if classnum == self.params['classnum']:
				notstackpartnum = classpart['noref_particle']['particle']['particleNumber']
				tiltstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['notstackid'], 
					notstackpartnum, self.params['tiltstackid'])
				if tiltstackpartdata is None:
					nopairParticle += 1
				else:
					emantiltstackpartnum = tiltstackpartdata['particleNumber']-1
					includeParticle.append(emantiltstackpartnum)
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
		apFile.removeStack(rctstackfile)
		apStack.makeNewStack(tiltstackfile, rctstackfile, self.params['keepfile'])
		spiderstack = self.convertStackToSpider(rctstackfile)

		### make doc file of Euler angles
		count = 0
		eulerfile = os.path.join(self.params['outdir'], "eulersdoc001.spi")
		eulerf = open(eulerfile, "w")
		apDisplay.printMsg("creating Euler doc file")
		starttime = time.time()
		tiltParticlesData.sort(self.sortTiltParticlesData)
		for stackpartdata in tiltParticlesData:
			count += 1
			gamma, theta, phi, tiltangle = apTiltPair.getParticleTiltRotationAngles(stackpartdata)
			inplane = self.getParticleNoRefInPlaneRotation(stackpartdata)
			psi = -1.0*(gamma + inplane)
			while psi < 0:
				psi += 360.0
			partnum = stackpartdata['particleNumber']-1
			line = operations.spiderOutLine(count, [phi, tiltangle, psi, partnum])
			eulerf.write(line)
		eulerf.close()
		apDisplay.printColor("finished Euler doc file in "+apDisplay.timeString(time.time()-starttime), "cyan")

		### iterations over volume creation
		looptime = time.time()
		### back project particles into filter volume
		volfile = os.path.join(self.params['outdir'], "volume%03d.spi"%(0))
		backproject.backprojectCG(spiderstack, eulerfile, volfile,
			numpart=len(includeParticle), pixrad=self.params['radius'])
		alignstack = spiderstack
		### center/convert the volume file
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		emanvolfile = os.path.join(self.params['outdir'], "volume-%s-%03d.mrc"%(self.timestamp, 0))
		emancmd = ("proc3d "+volfile+" "+emanvolfile+" center norm=0,1 apix="
			+str(apix)+" lp="+str(self.params['lowpassvol']))
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apFile.removeFile(volfile)
		emancmd = "proc3d "+emanvolfile+" "+volfile+" origin=0,0,0 spidersingle"
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		for i in range(self.params['numiters']):
			iternum = i+1
			apDisplay.printMsg("running backprojection iteration "+str(iternum))
			### xy-shift particles to volume projections
			alignstack = backproject.rctParticleShift(volfile, alignstack, eulerfile, iternum, 
				numpart=len(includeParticle), pixrad=self.params['radius'])
			apDisplay.printColor("finished volume refinement in "
				+apDisplay.timeString(time.time()-looptime), "cyan")

			### back project particles into better volume
			volfile = os.path.join(self.params['outdir'], "volume%03d.spi"%(iternum))
			backproject.backproject3F(alignstack, eulerfile, volfile,
				numpart=len(includeParticle))

			### center/convert the volume file
			emanvolfile = os.path.join(self.params['outdir'], "volume-%s-%03d.mrc"%(self.timestamp, iternum))
			emancmd = ("proc3d "+volfile+" "+emanvolfile+" center norm=0,1 apix="
				+str(apix)+" lp="+str(self.params['lowpassvol']))
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			apFile.removeFile(volfile)
			emancmd = "proc3d "+emanvolfile+" "+volfile+" origin=0,0,0 spidersingle"
			apEMAN.executeEmanCmd(emancmd, verbose=True)

		### optimize Euler angles

#=====================
if __name__ == "__main__":
	rctVolume = rctVolumeScript()
	rctVolume.start()
	rctVolume.close()

