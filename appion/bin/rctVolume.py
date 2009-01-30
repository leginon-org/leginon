#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
import math
import threading
#appion
import appionScript
import apStack
import apDisplay
import appionData
import apEMAN
import apFile
import apRecon
import apProject
from apTilt import apTiltPair
from apSpider import operations, backproject

class rctVolumeScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --cluster-id=ID --tilt-stack=# --classnums=#,#,# [options]")
		self.parser.add_option("--classnums", dest="classnums", type="str",
			help="Class numbers to use for rct volume, e.g. 0,1,2", metavar="#")
		self.parser.add_option("--tilt-stack", dest="tiltstackid", type="int",
			help="Tilted Stack ID", metavar="#")

		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")

		self.parser.add_option("--num-iters", dest="numiters", type="int", default=6, 
			help="Number of tilted image shift refinement iterations", metavar="#")
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="Particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float", default=10.0,
			help="Low pass volume filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpasspart", dest="highpasspart", type="float", default=600.0,
			help="High pass particle filter (in Angstroms)", metavar="#")

	#=====================
	def checkConflicts(self):
		### parse class list
		if self.params['classnums'] is None:
			apDisplay.printError("class number was not defined")
		rawclasslist = self.params['classnums'].split(",")
		self.classlist = []	
		for cnum in rawclasslist:
			try:
				self.classlist.append(int(cnum))
			except:
				apDisplay.printError("could not parse: "+cnum)

		### check for missing and duplicate entries
		if self.params['alignid'] is None and self.params['clusterid'] is None:
			apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")		

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['notstackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = clusterstackdata['clusterrun']['alignstack']
			self.params['notstackid'] = self.alignstackdata['stack'].dbid

		### check and make sure we got the stack id
		if self.params['notstackid'] is None:
			apDisplay.printError("untilted stackid was not found")

		if self.params['tiltstackid'] is None:
			apDisplay.printError("tilt stack ID was not defined")
		if self.params['radius'] is None:
			apDisplay.printError("particle mask radius was not defined")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")
		
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])
		if self.params['radius']*2 > boxsize-2:
			apDisplay.printError("particle radius is too big for stack boxsize")	

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['tiltstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+"-"
		classliststr = tempstr[:-1]

		self.params['rundir'] = os.path.join(uppath, "rctvolume", 
			self.params['runname'], "class"+str(classliststr) )

	#=====================
	def getParticleInPlaneRotation(self, tiltstackpartdata):
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'], 
			tiltstackpartdata['particleNumber'], self.params['notstackid'])

		alignpartq = appionData.ApAlignParticlesData()
		alignpartq['stackpart'] = notstackpartdata
		alignpartq['alignstack'] = self.alignstackdata
		alignpartdatas = alignpartq.query()
		if not alignpartdatas or len(alignpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation for particle %d"%(tiltstackpartdata['particleNumber']))
		inplane = alignpartdatas[0]['rotation']
		mirror = alignpartdatas[0]['mirror']
		return inplane, mirror

	#=====================
	def convertStackToSpider(self, emanstackfile):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		if not os.path.isfile(emanstackfile):
			apDisplay.printError("stackfile does not exist: "+emanstackfile)

		### first high pass filter particles
		apDisplay.printMsg("pre-filtering particles")
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		emancmd = ("proc2d "+emanstackfile+" "+emanstackfile
			+" apix="+str(apix)+" hp="+str(self.params['highpasspart'])
			+" inplace")
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		### convert imagic stack to spider
		emancmd  = "proc2d "
		emancmd += emanstackfile+" "
		spiderstack = os.path.join(self.params['rundir'], "rctstack"+self.timestamp+".spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

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
	def insertRctRun(self, volfile):
		### insert rct run data
		rctrunq = appionData.ApRctRunData()
		rctrunq['runname']    = self.params['runname']
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+","
		classliststr = tempstr[:-1]
		rctrunq['classnums']  = classliststr
		if len(self.classlist) == 1:
			rctrunq['classnum']  = self.classlist[0]
		rctrunq['numiter']    = self.params['numiters']
		rctrunq['maskrad']    = self.params['radius']
		rctrunq['lowpassvol'] = self.params['lowpassvol']
		rctrunq['highpasspart'] = self.params['highpasspart']
		rctrunq['description'] = self.params['description']
		rctrunq['path']  = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		rctrunq['alignstack'] = self.alignstackdata
		rctrunq['tiltstack']  = apStack.getOnlyStackData(self.params['tiltstackid'])
		if self.params['commit'] is True:
			rctrunq.insert()

		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['rctrun'] = rctrunq
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = appionData.ApSymmetryData.direct_query(25)
		densq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		densq['boxsize'] = apStack.getStackBoxsize(self.params['tiltstackid'])
		densq['lowpass'] = self.params['lowpassvol']
		densq['highpass'] = self.params['highpasspart']
		densq['mask'] = self.params['radius']
		#densq['iterid'] = self.params['numiters']
		densq['description'] = self.params['description']
		#densq['resolution'] = float
		densq['session'] = apStack.getSessionDataFromStackId(self.params['tiltstackid'])
		densq['md5sum'] = apFile.md5sumfile(volfile)
		if self.params['commit'] is True:
			densq.insert()

		return

	#=====================
	def processVolume(self, spivolfile, iternum=0):
		### set values
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])
		rawspifile = os.path.join(self.params['rundir'], "rawvolume%s-%03d.spi"%(self.timestamp, iternum))
		emanvolfile = os.path.join(self.params['rundir'], "volume%s-%03d.mrc"%(self.timestamp, iternum))
		lowpass = self.params['lowpassvol']
		### copy original to raw file
		shutil.copy(spivolfile, rawspifile)
		### process volume files
		emancmd = ("proc3d "+spivolfile+" "+emanvolfile+" center norm=0,1 apix="
			+str(apix)+" lp="+str(lowpass))
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		emancmd = "proc3d "+emanvolfile+" "+emanvolfile+" origin=0,0,0 "
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		emancmd = "proc3d "+emanvolfile+" "+emanvolfile+" mask="+str(self.params['radius'])
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		### convert to spider
		apFile.removeFile(spivolfile)
		emancmd = "proc3d "+emanvolfile+" "+spivolfile+" spidersingle"
		apEMAN.executeEmanCmd(emancmd, verbose=False)
		### image with chimera
		chimerathread = threading.Thread(target=apRecon.renderSnapshots, 
			args=(emanvolfile, 30, None, 1.5, 0.9, apix, 'c1', boxsize, False))
		chimerathread.setDaemon(1)
		chimerathread.start()

		return emanvolfile

	#=====================
	def makeEulerDoc(self, tiltParticlesData):
		count = 0
		eulerfile = os.path.join(self.params['rundir'], "eulersdoc"+self.timestamp+".spi")
		eulerf = open(eulerfile, "w")
		apDisplay.printMsg("Creating Euler angles doc file")
		starttime = time.time()
		tiltParticlesData.sort(self.sortTiltParticlesData)
		for stackpartdata in tiltParticlesData:
			count += 1
			if count%100 == 0:
				sys.stderr.write(".")
				eulerf.flush()
			gamma, theta, phi, tiltangle = apTiltPair.getParticleTiltRotationAngles(stackpartdata)
			inplane, mirror = self.getParticleInPlaneRotation(stackpartdata)
			if mirror is True:
				#theta flips to the back
				tiltangle = 360.0 - tiltangle
				#phi is rotated 180 degrees
				phi += 180.0
				while phi > 360:
					phi -= 360.0
			psi = -1.0*(gamma + inplane)
			while psi < 0:
				psi += 360.0
			### this is the original eman part num; count is new part num
			partnum = stackpartdata['particleNumber']-1
			line = operations.spiderOutLine(count, [phi, tiltangle, psi])
			eulerf.write(line)
		eulerf.close()
		apDisplay.printColor("Finished Euler angle doc file in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return eulerfile

	#=====================
	def getGoodAlignParticles(self):
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("Sorting particles from classes")

		if self.params['clusterid'] is not None:
			### method 1: get particles from clustering data
			clusterpartq = appionData.ApClusteringParticlesData()
			clusterpartq['clusterstack'] = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			clusterpartdatas = clusterpartq.query()
			apDisplay.printMsg("Found "+str(len(clusterpartdatas))+" clustered particles")

			for clustpart in clusterpartdatas:
				#write to text file
				clustnum = clustpart['refnum']-1
				if clustnum in self.classlist:
					notstackpartnum = clustpart['alignparticle']['stackpart']['particleNumber']
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
		else:
			### method 2: get particles from alignment data
			alignpartq = appionData.ApAlignParticlesData()
			alignpartq['alignstack'] = self.alignstackdata
			alignpartdatas = alignpartq.query()
			apDisplay.printMsg("Found "+str(len(alignpartdatas))+" aligned particles")

			for alignpart in alignpartdatas:
				#write to text file
				alignnum = alignpart['ref']['refnum']-1
				if alignnum in self.classlist:
					notstackpartnum = alignpart['stackpart']['particleNumber']
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
		return includeParticle, tiltParticlesData

	#=====================
	def start(self):
		### get stack data
		notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])

		### get good particle numbers
		includeParticle, tiltParticlesData = self.getGoodAlignParticles()

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile"+self.timestamp+".lst")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### make new stack of tilted particle from that run
		tiltstackfile = os.path.join(tiltstackdata['path']['path'], tiltstackdata['name'])
		rctstackfile = os.path.join(self.params['rundir'], "rctstack"+self.timestamp+".hed")
		apFile.removeStack(rctstackfile)
		apStack.makeNewStack(tiltstackfile, rctstackfile, self.params['keepfile'])
		spiderstack = self.convertStackToSpider(rctstackfile)

		### make doc file of Euler angles
		eulerfile = self.makeEulerDoc(tiltParticlesData)

		### iterations over volume creation
		looptime = time.time()
		### back project particles into filter volume
		volfile = os.path.join(self.params['rundir'], "volume%s-%03d.spi"%(self.timestamp, 0))
		backproject.backprojectCG(spiderstack, eulerfile, volfile,
			numpart=len(includeParticle), pixrad=self.params['radius'])
		alignstack = spiderstack

		### center/convert the volume file
		emanvolfile = self.processVolume(volfile, 0)

		for i in range(self.params['numiters']):
			iternum = i+1
			apDisplay.printMsg("running backprojection iteration "+str(iternum))
			### xy-shift particles to volume projections
			alignstack = backproject.rctParticleShift(volfile, alignstack, eulerfile, iternum, 
				numpart=len(includeParticle), pixrad=self.params['radius'], timestamp=self.timestamp)
			apDisplay.printColor("finished volume refinement in "
				+apDisplay.timeString(time.time()-looptime), "cyan")

			### back project particles into better volume
			volfile = os.path.join(self.params['rundir'], "volume%s-%03d.spi"%(self.timestamp, iternum))
			backproject.backproject3F(alignstack, eulerfile, volfile,
				numpart=len(includeParticle))

			### center/convert the volume file
			emanvolfile = self.processVolume(volfile, iternum)

		### optimize Euler angles
		#NOT IMPLEMENTED YET

		### insert volumes into DB
		self.insertRctRun(emanvolfile)
		time.sleep(30)

#=====================
if __name__ == "__main__":
	rctVolume = rctVolumeScript()
	rctVolume.start()
	rctVolume.close()

