#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
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
		self.parser.set_usage("Usage: %prog --norefclass=ID --tilt-stack=# --classnums=#,#,# [options]")
		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit RCT run to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit RCT run to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("--classnum", "--classnums", dest="classnums", type="str",
			help="Class numbers to use for rct volume, e.g. 0,1,2", metavar="#")
		self.parser.add_option("--tilt-stack", dest="tiltstackid", type="int",
			help="Tilted Stack ID", metavar="#")
		self.parser.add_option("--norefclass", dest="norefclassid", type="int",
			help="Noref class id", metavar="ID")
		self.parser.add_option("--runname", dest="runname",
			help="Run name", metavar="ID")
		self.parser.add_option("--num-iters", dest="numiters", type="int", default=6, 
			help="Number of tilted image shift refinement iterations", metavar="#")
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="Particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float", default=10.0,
			help="Low pass volume filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpasspart", dest="highpasspart", type="float", default=600.0,
			help="High pass particle filter (in Angstroms)", metavar="#")
		self.parser.add_option("--description", dest="description", type="str",
			help="Description of RCT run", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['classnums'] is None:
			apDisplay.printError("class number was not defined")
		rawclasslist = self.params['classnums'].split(",")
		self.classlist = []	
		for cnum in rawclasslist:
			try:
				self.classlist.append(int(cnum))
			except:
				apDisplay.printError("could not parse: "+cnum)
		if self.params['runname'] is None:
			apDisplay.printError("new stack name was not defined")
		if self.params['norefclassid'] is None:
			apDisplay.printError("noref class ID was not defined")
		if self.params['tiltstackid'] is None:
			apDisplay.printError("tilt stack ID was not defined")
		if self.params['radius'] is None:
			apDisplay.printError("particle mask radius was not defined")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")
		
		#get the stack ID from the noref class ID
		self.norefclassdata = appionData.ApNoRefClassRunData.direct_query(self.params['norefclassid'])
		norefRun = self.norefclassdata['norefRun']
		self.params['notstackid'] = norefRun['stack'].dbid
		if self.params['notstackid'] is None:
			apDisplay.printError("untilted stackid was not defined")
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
		spiderstack = os.path.join(self.params['outdir'], "rctstack"+self.timestamp+".spi")
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
		rctrunq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['tiltstackid'])
		rctrunq['path']  = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		rctrunq['norefclass'] = appionData.ApNoRefClassRunData.direct_query(self.params['norefclassid'])
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
		rawspifile = os.path.join(self.params['outdir'], "rawvolume%s-%03d.spi"%(self.timestamp, iternum))
		emanvolfile = os.path.join(self.params['outdir'], "volume%s-%03d.mrc"%(self.timestamp, iternum))
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
	def getGoodParticles(self, classpartdatas):
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("sorting particles")
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			if classnum in self.classlist:
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
		return includeParticle, tiltParticlesData

	#=====================
	def makeEulerDoc(self, tiltParticlesData):
		count = 0
		eulerfile = os.path.join(self.params['outdir'], "eulersdoc"+self.timestamp+".spi")
		eulerf = open(eulerfile, "w")
		apDisplay.printMsg("creating Euler doc file")
		starttime = time.time()
		tiltParticlesData.sort(self.sortTiltParticlesData)
		for stackpartdata in tiltParticlesData:
			count += 1
			if count%100 == 0:
				sys.stderr.write(".")
				eulerf.flush()
			gamma, theta, phi, tiltangle = apTiltPair.getParticleTiltRotationAngles(stackpartdata)
			inplane = self.getParticleNoRefInPlaneRotation(stackpartdata)
			psi = -1.0*(gamma + inplane)
			while psi < 0:
				psi += 360.0
			### this is the original eman part num; count is new part num
			partnum = stackpartdata['particleNumber']-1
			line = operations.spiderOutLine(count, [phi, tiltangle, psi])
			eulerf.write(line)
		eulerf.close()
		apDisplay.printColor("finished Euler doc file in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return eulerfile

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
		includeParticle, tiltParticlesData = self.getGoodParticles(classpartdatas)

		### write kept particles to file
		self.params['keepfile'] = os.path.join(self.params['outdir'], "keepfile"+self.timestamp+".lst")
		apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
		kf = open(self.params['keepfile'], "w")
		for partnum in includeParticle:
			kf.write(str(partnum)+"\n")
		kf.close()

		### make new stack of tilted particle from that run
		tiltstackfile = os.path.join(tiltstackdata['path']['path'], tiltstackdata['name'])
		rctstackfile = os.path.join(self.params['outdir'], "rctstack"+self.timestamp+".hed")
		apFile.removeStack(rctstackfile)
		apStack.makeNewStack(tiltstackfile, rctstackfile, self.params['keepfile'])
		spiderstack = self.convertStackToSpider(rctstackfile)

		### make doc file of Euler angles
		eulerfile = self.makeEulerDoc(tiltParticlesData)

		### iterations over volume creation
		looptime = time.time()
		### back project particles into filter volume
		volfile = os.path.join(self.params['outdir'], "volume%s-%03d.spi"%(self.timestamp, 0))
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
			volfile = os.path.join(self.params['outdir'], "volume%s-%03d.spi"%(self.timestamp, iternum))
			backproject.backproject3F(alignstack, eulerfile, volfile,
				numpart=len(includeParticle))

			### center/convert the volume file
			emanvolfile = self.processVolume(volfile, iternum)

		### optimize Euler angles
		#NOT IMPLEMENTED YET

		### insert volumes into DB
		self.insertRctRun(emanvolfile)

#=====================
if __name__ == "__main__":
	rctVolume = rctVolumeScript()
	rctVolume.start()
	rctVolume.close()

