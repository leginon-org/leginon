#!/usr/bin/env python

#python
import sys
import os
import shutil
import numpy
import time
import threading
import math
from scipy import ndimage
#appion
import appionScript
import apStack
import apDisplay
import appionData
import apEMAN
import apFile
import apRecon
import apChimera
import apProject
import apParam
from apTilt import apTiltPair
from apSpider import operations, backproject, alignment
from pyami import mem, mrc

class otrVolumeScript(appionScript.AppionScript):
	#=====================
	def onInit(self):
		self.rotmirrorcache = {}
		self.fscresolution = None
		self.rmeasureresolution = None

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --cluster-id=ID --tilt-stack=# --classnums=#,#,# [options]")

		### strings
		self.parser.add_option("--classnums", dest="classnums", type="str",
			help="Class numbers to use for rct volume, e.g. 0,1,2", metavar="#")

		### integers
		self.parser.add_option("--tilt-stack", dest="tiltstackid", type="int",
			help="Tilted Stack ID", metavar="#")
		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")
		self.parser.add_option("--num-iters", dest="numiters", type="int", default=4, 
			help="Number of tilted image shift refinement iterations", metavar="#")
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="Particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--tilt-bin", dest="tiltbin", type="int", default=1,
			help="Binning of the tilted image", metavar="ID")
		self.parser.add_option("--num-part", dest="numpart", type="int",
			help="Limit number of particles, for debugging", metavar="#")
		self.parser.add_option("--median", dest="median", type="int", default=3,
			help="Median filter", metavar="#")

		### floats
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float", default=10.0,
			help="Low pass volume filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpasspart", dest="highpasspart", type="float", default=600.0,
			help="High pass particle filter (in Angstroms)", metavar="#")
		self.parser.add_option("--min-score", dest="minscore", type="float",
			help="Minimum cross-correlation score", metavar="#")
		self.parser.add_option("--contour", dest="contour", type="float", default=3.0,
			help="Chimera snapshot contour", metavar="#")
		self.parser.add_option("--zoom", dest="zoom", type="float", default=1.1,
			help="Chimera snapshot zoom", metavar="#")

		### true/false
		self.parser.add_option("--no-eotest", dest="eotest", default=True,
			action="store_false", help="Do not perform eotest for resolution")
		self.parser.add_option("--eotest", dest="eotest", default=True,
			action="store_true", help="Perform eotest for resolution")
		self.parser.add_option("--skip-chimera", dest="skipchimera", default=False,
			action="store_true", help="Skip chimera imaging")

		### choices
		self.mirrormodes = ( "all", "yes", "no" )
		self.parser.add_option("--mirror", dest="mirror",
			help="Mirror mode", metavar="MODE", 
			type="choice", choices=self.mirrormodes, default="all" )

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
			self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
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
		
		boxsize = self.getBoxSize()
		if self.params['radius']*2 > boxsize-2:
			apDisplay.printError("particle radius is too big for stack boxsize")	

		if self.params['notstackid'] == self.params['tiltstackid']:
			apDisplay.printError("tilt stack and align stack are the same: %d vs. %d"%
				(self.params['notstackid'],self.params['tiltstackid']))

	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['tiltstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+"-"
		classliststr = tempstr[:-1]

		self.params['rundir'] = os.path.join(uppath, "otrvolume",
			self.params['runname'], "class"+str(classliststr) )



		### check if path exists in db already
		otrrunq = appionData.ApOtrRunData()
		otrrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		otrdata = otrrunq.query()
		if otrdata:
			apDisplay.printError("otr data already exists in database")

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
	def convertStackToSpider(self, emanstackfile, classnum):
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
		spiderstack = os.path.join(self.params['rundir'], str(classnum), "otrstack"+self.timestamp+".spi")
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
	def getBoxSize(self):
		boxsize = apStack.getStackBoxsize(self.params['tiltstackid'])
		if self.params['tiltbin'] == 1:
			return boxsize
		newbox = int( math.floor( boxsize / float(self.params['tiltbin']) / 2.0)* 2.0 )
		return newbox

	#=====================
	def getGoodAlignParticles(self, cnum):
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		badmirror = 0
		badscore = 0
		apDisplay.printMsg("Sorting particles from classes")
		count = 0
		startmem = mem.active()
		t0 = time.time()
		if self.params['clusterid'] is not None:
			### method 1: get particles from clustering data
			clusterpartq = appionData.ApClusteringParticlesData()
			clusterpartq['clusterstack'] = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			clusterpartdatas = clusterpartq.query()
			apDisplay.printMsg("Sorting "+str(len(clusterpartdatas))+" clustered particles")

			for clustpart in clusterpartdatas:
				count += 1
				if count%50 == 0:
					sys.stderr.write(".")
					memdiff = (mem.active()-startmem)/count/1024.0
					if memdiff > 3:
						apDisplay.printColor("Memory increase: %d MB/part"%(memdiff), "red")
				#write to text file
				clustnum = clustpart['refnum']-1
				if ( self.params['minscore'] is not None 
				 and clustpart['alignparticle']['score'] is not None 
				 and clustpart['alignparticle']['score'] < self.params['minscore'] ):
					badscore += 1
					continue
				if clustnum == cnum:
					notstackpartnum = clustpart['alignparticle']['stackpart']['particleNumber']
					tiltstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['notstackid'], 
						notstackpartnum, self.params['tiltstackid'])
					if tiltstackpartdata is None:
						nopairParticle += 1
					else:
						inplane, mirror = self.getParticleInPlaneRotation(tiltstackpartdata)
						if ( self.params['mirror'] == "all"
						 or (self.params['mirror'] == "no" and mirror is False)
						 or (self.params['mirror'] == "yes" and mirror is True) ):
							emantiltstackpartnum = tiltstackpartdata['particleNumber']-1
							includeParticle.append(emantiltstackpartnum)
							tiltParticlesData.append(tiltstackpartdata)
							if self.params['numpart'] is not None and len(includeParticle) > self.params['numpart']:
								break
						else:
							badmirror += 1
				else:
					excludeParticle += 1
		else:
			### method 2: get particles from alignment data
			alignpartq = appionData.ApAlignParticlesData()
			alignpartq['alignstack'] = self.alignstackdata
			alignpartdatas = alignpartq.query()
			apDisplay.printMsg("Sorting "+str(len(alignpartdatas))+" aligned particles")

			for alignpart in alignpartdatas:
				count += 1
				if count%50 == 0:
					sys.stderr.write(".")
					memdiff = (mem.active()-startmem)/count/1024.0
					if memdiff > 3:
						apDisplay.printColor("Memory increase: %d MB/part"%(memdiff), "red")
				#write to text file
				alignnum = alignpart['ref']['refnum']-1
				if ( self.params['minscore'] is not None 
				 and alignpart['score'] is not None 
				 and alignpart['score'] < self.params['minscore'] ):
					badscore += 1
					continue
				if alignnum == cnum:
					notstackpartnum = alignpart['stackpart']['particleNumber']
					tiltstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['notstackid'], 
						notstackpartnum, self.params['tiltstackid'])
					if tiltstackpartdata is None:
						nopairParticle += 1
					else:
						inplane, mirror = self.getParticleInPlaneRotation(tiltstackpartdata)
						if ( self.params['mirror'] == "all"
						 or (self.params['mirror'] == "no" and mirror is False)
						 or (self.params['mirror'] == "yes" and mirror is True) ):
							emantiltstackpartnum = tiltstackpartdata['particleNumber']-1
							includeParticle.append(emantiltstackpartnum)
							tiltParticlesData.append(tiltstackpartdata)
							if self.params['numpart'] is not None and len(includeParticle) > self.params['numpart']:
								break
						else:
							badmirror += 1
				else:
					excludeParticle += 1
		includeParticle.sort()
		if time.time()-t0 > 1.0:
			apDisplay.printMsg("\nSorting time: "+apDisplay.timeString(time.time()-t0))
		apDisplay.printMsg("Keeping "+str(len(includeParticle))+" and excluding \n\t"
			+str(excludeParticle)+" particles with "+str(nopairParticle)+" unpaired particles")
		if badmirror > 0:
			apDisplay.printMsg("Particles with bad mirrors: %d"%(badmirror))
		if badscore > 0:
			apDisplay.printColor("Particles with bad scores: %d"%(badscore), "cyan")
		if len(includeParticle) < 1:
			apDisplay.printError("No particles were kept")
		memdiff = (mem.active()-startmem)/count/1024.0
		if memdiff > 0.1:
			apDisplay.printColor("Memory increase: %.2f MB/part"%(memdiff), "red")
		return includeParticle, tiltParticlesData

	#=====================
	def getParticleInPlaneRotation(self, tiltstackpartdata):
		partid = tiltstackpartdata.dbid
		if partid in self.rotmirrorcache:
			### use cached value
			return self.rotmirrorcache[partid] 

		partnum = tiltstackpartdata['particleNumber']
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'], 
			partnum, self.params['notstackid'])

		alignpartq = appionData.ApAlignParticlesData()
		alignpartq['stackpart'] = notstackpartdata
		alignpartq['alignstack'] = self.alignstackdata
		alignpartdatas = alignpartq.query()
		if not alignpartdatas or len(alignpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation for particle %d"%(tiltstackpartdata['particleNumber']))
		inplane = alignpartdatas[0]['rotation']
		mirror = alignpartdatas[0]['mirror']
		self.rotmirrorcache[partid] = (inplane, mirror)
		return inplane, mirror
		
	#=====================
	def insertOtrRun(self, volfile):
		### insert otr run data
		otrrunq = appionData.ApOtrRunData()
		otrrunq['runname']    = self.params['runname']
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+","
		classliststr = tempstr[:-1]
		otrrunq['classnums']  = classliststr
		if len(self.classlist) == 1:
			otrrunq['classnum']  = self.classlist[0]
		otrrunq['numiter']    = self.params['numiters']
		otrrunq['maskrad']    = self.params['radius']
		otrrunq['lowpassvol'] = self.params['lowpassvol']
		otrrunq['highpasspart'] = self.params['highpasspart']
		otrrunq['description'] = self.params['description']
		otrrunq['path']  = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		otrrunq['norefclass'] = appionData.ApNoRefClassRunData.direct_query(self.params['norefclassid'])
		otrrunq['tiltstack']  = apStack.getOnlyStackData(self.params['tiltstackid'])
		if self.params['commit'] is True:
			otrrunq.insert()

		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['otrrun'] = otrrunq
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
	def processVolume(self, spivolfile, cnum, iternum=0):
		### set values
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])*self.params['tiltbin']
		boxsize = self.getBoxSize()
		
		volfilename = os.path.splitext(spivolfile)[0]
		rawspifile = volfilename + "-raw.spi"
		mrcvolfile = volfilename + ".mrc"
		lowpass = self.params['lowpassvol']
		### copy original to raw file
		shutil.copy(spivolfile, rawspifile)

		### convert to mrc
		emancmd = ("proc3d "+spivolfile+" "+mrcvolfile+" norm=0,1 apix="+str(apix))
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		### median filter
		rawvol = mrc.read(mrcvolfile)
		medvol = ndimage.median_filter(rawvol, size=self.params['median'])
		mrc.write(medvol, mrcvolfile)

		### low pass filter
		emancmd = ("proc3d "+mrcvolfile+" "+mrcvolfile+" center norm=0,1 apix="
			+str(apix)+" lp="+str(lowpass))
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		### set origin
		emancmd = "proc3d "+mrcvolfile+" "+mrcvolfile+" origin=0,0,0 "
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		### mask volume
		emancmd = "proc3d "+mrcvolfile+" "+mrcvolfile+" mask="+str(self.params['radius'])
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		### convert to spider
		apFile.removeFile(spivolfile)
		emancmd = "proc3d "+mrcvolfile+" "+spivolfile+" spidersingle"
		apEMAN.executeEmanCmd(emancmd, verbose=False)

		### image with chimera
		if self.params['skipchimera'] is False:
			snapshotthread = threading.Thread(target=apChimera.renderSnapshots, 
				args=(mrcvolfile, self.params['contour'], self.params['zoom'], 'c1'))
			snapshotthread.setDaemon(1)
			snapshotthread.start()
			animationthread = threading.Thread(target=apChimera.renderAnimation, 
				args=(mrcvolfile, self.params['contour'], self.params['zoom'], 'c1'))
			animationthread.setDaemon(1)
			animationthread.start()
		return mrcvolfile

	#=====================
	def getGoodParticles(self, classpartdatas, norefclassnum):
		includeParticle = []
		tiltParticlesData = []
		nopairParticle = 0
		excludeParticle = 0
		apDisplay.printMsg("sorting particles")
		for classpart in classpartdatas:
			#write to text file
			classnum = classpart['classNumber']-1
			if classnum == norefclassnum:
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
		return includeParticle, tiltParticlesData

	#=====================
	def makeEulerDoc(self, tiltParticlesData, cnum):
		count = 0
		eulerfile = os.path.join(self.params['rundir'], str(cnum), "eulersdoc"+self.timestamp+".spi")
		eulerf = open(eulerfile, "w")
		apDisplay.printMsg("Creating Euler angles doc file")
		starttime = time.time()
		tiltParticlesData.sort(self.sortTiltParticlesData)
		startmem = mem.active()
		for stackpartdata in tiltParticlesData:
			count += 1
			if count%50 == 0:
				sys.stderr.write(".")
				eulerf.flush()
				memdiff = (mem.active()-startmem)/count/1024.0
				if memdiff > 3:
					apDisplay.printColor("Memory increase: %d MB/part"%(memdiff), "red")
			tiltrot, theta, notrot, tiltangle = apTiltPair.getParticleTiltRotationAnglesOTR(stackpartdata)
			inplane, mirror = self.getParticleInPlaneRotation(stackpartdata)
			totrot = -1.0*(notrot + inplane)
			if mirror is True:
				#theta flips to the back
				tiltangle = -1.0 * tiltangle + 180 #tiltangle = tiltangle + 180.0   #theta
				totrot = -1.0 * totrot - 180.0  #phi
				tiltrot = tiltrot + 180            #tiltrot = -1.0 * tiltrot + 180.0 #psi
			while totrot < 0:
				totrot += 360.0
			### this is the original eman part num; count is new part num
			partnum = stackpartdata['particleNumber']-1
			line = operations.spiderOutLine(count, [tiltrot, tiltangle, totrot])
			eulerf.write(line)
		eulerf.close()
		apDisplay.printColor("\nFinished Euler angle doc file in "+apDisplay.timeString(time.time()-starttime), "cyan")
		memdiff = (mem.active()-startmem)/count/1024.0
		if memdiff > 0.1:
			apDisplay.printColor("Memory increase: %.2f MB/part"%(memdiff), "red")
		return eulerfile

	#=====================
	def initialBPRP(self, classnum, volfile, spiderstack, eulerfile, numpart, pixrad):

		# file that stores the number of iteration for BPRP
		BPRPcount = os.path.join(self.params['rundir'], str(classnum), "numiter.spi")

		if (os.path.isfile(BPRPcount)):
			apDisplay.printMsg("BP RP counter file exists: "+BPRPcount+"! File will be deleted.")
			apFile.removeFile(BPRPcount)

		BPRPlambda=2e-5
		backproject.backprojectRP(spiderstack, eulerfile, volfile,
			pixrad=pixrad, classnum=classnum, lambDa=BPRPlambda, numpart=numpart)

		count = 0
		rounds = 0

		### repeat BPRP for 100 times with different values of lambda or until BPRP manages to do 50 iterations
		while count < 50 and rounds < 100:
			if (os.path.isfile(BPRPcount)):
				bc = open(BPRPcount, "r")
				for line in bc.readlines():
					value = line.split()
					if value[0]=="1":
						count = int(float(value[2]))
						if count < 50:
							apDisplay.printMsg("BPRP iteration is "+str(count)+" (less than 50)... redoing BPRP")
							bc.close()
							apFile.removeFile(BPRPcount)
							BPRPlambda = BPRPlambda/2
							backproject.backprojectRP(spiderstack, eulerfile, volfile,
								pixrad=pixrad, classnum=classnum, lambDa=BPRPlambda, numpart=numpart)
			else:
				apDisplay.printWarning("numiter is missing")
				continue
			rounds+=1

		### print warning if BPRP reaches 100 rounds
		if rounds >=100:
			apDisplay.printWarning("BPRP attempted 100 times but iteration is still less than 50. Check BPRP params.")

		return

	#===================== Andres script #1 --- p.align_APSH.spi
	def projMatchRefine(self, classnum, volfile, alignstack, eulerfile, boxsize, numpart, pixrad, iternum):

		APSHout = backproject.alignAPSH(volfile, alignstack, eulerfile, classnum, boxsize, numpart, pixrad, self.timestamp, iternum)

		### check APSH output
		if (os.path.isfile(APSHout) is False):
			apDisplay.printError("AP SH alignment did not generate a valid output file. Please check parameters and rerun!")

		apsh = open(APSHout, "r")

		neweulerdoc = os.path.join(self.params['rundir'], str(classnum),"newEulersdoc-%03d.spi"%(iternum))
		neweulerfile = open(neweulerdoc, "w")
		rotshiftdoc = os.path.join(self.params['rundir'], str(classnum),"rotShiftdoc-%03d.spi"%(iternum))
		rotshiftfile = open(rotshiftdoc, "w")

		starttime = time.time()

		count = 0
		for line in apsh.readlines():
			value = line.split()
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue
			key = int(float(value[6]))
			rot = float(value[7])
			cumX = float(value[8])
			cumY = float(value[9])
			psi = float(value[2])
			theta = float(value[3])
			phi = float(value[4])

			### rotate and shift particle
			APSHstack = backproject.rotshiftParticle(alignstack, key, rot, cumX, cumY, iternum, self.timestamp, str(classnum))

			### write out new euler file
			eulerline = operations.spiderOutLine(key, [psi, theta, phi])
			neweulerfile.write(eulerline)

			rotshiftline = operations.spiderOutLine(key, [rot, 1.00, cumX, cumY])
			rotshiftfile.write(rotshiftline)
			count+=1
			
			if (count%20) == 0:
				apDisplay.printColor(str(numpart-count)+" particles left", "cyan")
				apDisplay.printColor("Estimated time left is "+apDisplay.timeString(((time.time()-starttime)/count)*(numpart-count)), "cyan")
			
		apDisplay.printColor("finished rotating and shifting particles "+apDisplay.timeString(time.time()-starttime), "cyan")

		neweulerfile.close()
		rotshiftfile.close()
		return APSHout, APSHstack, neweulerdoc

	#===================== Andres script #2 --- p.weighted_CCC_APSH.spi
	def cccAPSH(self, APSHout, classnum, iternum):
		### Calculate absolute shifts
		absshifts=[]

		if not os.path.isfile(APSHout):
			apDisplay.printError("APSH output file not found: "+APSHout)

		apsh = open(APSHout, "r")

		for line in apsh.readlines():
			value = line.split()
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue

			### absshift = sqrt(x^2 + y^2)
			absshift = math.sqrt((float(value[8])*float(value[8]))+(float(value[9])*float(value[9])))
			absshifts.append(absshift)

		apsh.close()

		### calculate the mean, variance and stdev of the absolute shift of the dataset
		APSHmean = (numpy.array(absshifts)).mean()
		APSHvar = (numpy.array(absshifts)).var()
		APSHstd = (numpy.array(absshifts)).std()

		### calculate the weighted cross correlation values

		####################################################################
		##
		##								1
		## prob(shift) = ------------------ * e^[-1/2*(shift-mean)/stdev]**2
		##						stdev*sqrt(2*pi)
		##
		####################################################################
		const = APSHstd*math.sqrt(2*math.pi)
		probs=[]

		for absshift in absshifts:

			### probability for each particle
			prob = (1/const)*math.exp((-1/2)*((absshift-APSHmean)/APSHstd)*((absshift-APSHmean)/APSHstd))
			probs.append(prob)

		### output file for APSH with weighted CC values
		APSHout_weighted = os.path.join(self.params['rundir'], str(classnum), "apshOut_weighted-%03d.spi"%(iternum))

		apsh = open(APSHout, "r")
		apshCCC = open(APSHout_weighted, "w")

		notline=0

		for i,line in enumerate(apsh.readlines()):
			value = line.split()
			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				notline+=1
				continue

			key = int(float(value[6]))
			weightedCCvalue = float(value[12])*probs[i-notline]

			psi = float(value[2])
			theta = float(value[3])
			phi = float(value[4])
			ref = float(value[5])
			partnum =  float(value[6])
			rot = float(value[7])
			cumX = float(value[8])
			cumY = float(value[9])
			proj = float(value[10])
			diff = float(value[11])
			inplane = float(value[13])
			sx = float(value[14])
			sy = float(value[15])
			mirror = float(value[16])


			### write out new APSH file
			APSHline = operations.spiderOutLine(key, [psi, theta, phi, ref, partnum, rot, cumX, cumY, proj, diff, weightedCCvalue, inplane, sx, sy, mirror])
			apshCCC.write(APSHline)

		apshCCC.close()
		apsh.close()

		return APSHout_weighted

	#===================== Andres script #3 --- p.make_wCCC_Selfile_APSH.spi
	def makecccAPSHselectFile(self, APSHout, classnum, iternum, factor):

		if (os.path.isfile(APSHout) is False):
			apDisplay.printError("File "+ APSHout +" does not exist!")

		apshFile = open(APSHout, "r")
		corrValues = []

		for line in apshFile.readlines():
			value = line.split()

			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue

			corrValues.append(float(value[12]))

		apshFile.close()

		corrmean = (numpy.array(corrValues)).mean()
		corrvar = (numpy.array(corrValues)).var()
		corrstd = (numpy.array(corrValues)).std()

		threshold = corrmean + (factor*corrstd)

		count = 1
		part = 1

		corrSelect = os.path.join(self.params['rundir'], str(classnum), "apshCorrSelect-%03d.spi"%(iternum))
		corrSelectFile = open(corrSelect, "w")


		for i,corrValue in enumerate(corrValues):

			if corrValue >= threshold:
				line = operations.spiderOutLine(count, [i+1])
				corrSelectFile.write(line)
				count+=1

		corrSelectFile.close()

		return corrSelect

	#===================== Andres script #4 --- p.makeselect_APSH.spi
	def splitOddEven(self, classnum, select, iternum):

		if (os.path.isfile(select) is False):
			apDisplay.printError("File "+ select +" does not exist!")

		selectFile = open(select, "r")
		selectFilename = os.path.splitext(os.path.basename(select))[0]

		selectOdd = os.path.join(self.params['rundir'], str(classnum), selectFilename+"Odd.spi")
		selectOddFile = open(selectOdd, "w")

		selectEven = os.path.join(self.params['rundir'], str(classnum), selectFilename+"Even.spi")
		selectEvenFile = open(selectEven, "w")

		countOdd=1
		countEven=1

		for line in selectFile.readlines():
			value = line.split()

			try:
				int(value[0])
			except:
				#apDisplay.printMsg(line)
				continue

			if float(value[0])%2.0 == 1.0:
				sline = operations.spiderOutLine(countOdd, [int(value[0])])
				selectOddFile.write(line)
				countOdd+=1
			else:
				sline = operations.spiderOutLine(countEven, [int(value[0])])
				selectEvenFile.write(line)
				countEven+=1

		selectOddFile.close()
		selectEvenFile.close()

		return selectOdd, selectEven

	#===================== Andres script #5 --- p.BPRP_APSH.spi
	def APSHbackProject(self, spiderstack, eulerfile, volfile, classnum, selectFile):

		# file that stores the number of iteration for BPRP
		BPRPcount = os.path.join(self.params['rundir'], str(classnum), "numiter.spi")

		if (os.path.isfile(BPRPcount)):
			apDisplay.printMsg("BP RP counter file exists: "+BPRPcount+"! File will be deleted.")
			apFile.removeFile(BPRPcount)

		BPRPlambda=2e-5
		backproject.backprojectRP(spiderstack, eulerfile, volfile,
			pixrad=self.params['radius'], classnum=classnum, lambDa=BPRPlambda, selfile=selectFile)

		count = 0
		rounds = 0

		### repeat BPRP for 100 times with different values of lambda or until BPRP manages to do 50 iterations
		while count < 50 and rounds < 100:
			if (os.path.isfile(BPRPcount)):
				bc = open(BPRPcount, "r")
				for line in bc.readlines():
					value = line.split()
					if value[0]=="1":
						count = int(float(value[2]))
						if count < 50:
							apDisplay.printMsg("BPRP iteration is "+str(count)+" (less than 50)... redoing BPRP")
							bc.close()
							apFile.removeFile(BPRPcount)
							BPRPlambda = BPRPlambda/2
							backproject.backprojectRP(spiderstack, eulerfile, volfile,
								pixrad=self.params['radius'], classnum=classnum, lambDa=BPRPlambda, selfile=selectFile)
			else:
				apDisplay.printWarning("numiter is missing")
				continue
			rounds+=1

		### print warning if BPRP reaches 100 rounds
		if rounds >=100:
			apDisplay.printWarning("BPRP attempted 100 times but iteration is still less than 50. Check BPRP params.")

		return

	#=====================
	def computeClassVolPair(self):
		done=[]
		pairlist=[]

		for i in self.classlist:
			for j in self.classlist:
				done.append(i)
				if j not in done:
					pair=[]
					pair.append(i)
					pair.append(j)
					pairlist.append(pair)
		return pairlist

	#=====================
	def start(self):
		### get stack data
		notstackdata = apStack.getOnlyStackData(self.params['notstackid'])
		tiltstackdata = apStack.getOnlyStackData(self.params['tiltstackid'])
		
		for cnum in self.classlist:

			print "\n"
			apDisplay.printMsg("###########################")
			apDisplay.printMsg("Processing stack of class "+str(cnum)+"")
			apDisplay.printMsg("###########################")
			print "\n"
			
			### get good particle numbers
			includeParticle, tiltParticlesData = self.getGoodAlignParticles(cnum)
			self.numpart = len(includeParticle)

			### write kept particles to file
			apParam.createDirectory(os.path.join(self.params['rundir'], str(cnum)))
			self.params['keepfile'] = os.path.join(self.params['rundir'], str(cnum), "keepfile"+self.timestamp+".lst")
			apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
			kf = open(self.params['keepfile'], "w")
			for partnum in includeParticle:
				kf.write(str(partnum)+"\n")
			kf.close()

			### make new stack of tilted particle from that run
			tiltstackfile = os.path.join(tiltstackdata['path']['path'], tiltstackdata['name'])
			otrstackfile = os.path.join(self.params['rundir'], str(cnum), "otrstack"+self.timestamp+".hed")
			apFile.removeStack(otrstackfile)
			apStack.makeNewStack(tiltstackfile, otrstackfile, self.params['keepfile'])
			spiderstack = self.convertStackToSpider(otrstackfile, cnum)

			### make doc file of Euler angles
			eulerfile = self.makeEulerDoc(tiltParticlesData, cnum)

			### iterations over volume creation
			looptime = time.time()

			### back project particles into volume
			volfile = os.path.join(self.params['rundir'], str(cnum), "volume%s-%03d.spi"%(self.timestamp, 0))
			self.initialBPRP(cnum, volfile, spiderstack, eulerfile, len(includeParticle), self.params['radius'])
			### RCT backproject method
			#backproject.backprojectCG(spiderstack, eulerfile, volfile, numpart=len(includeParticle), pixrad=self.params['radius'])

			### filter the volume (low-pass Butterworth)
			apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])
			backproject.butterworthLP(volfile, apix)

			### need work... filtered volume overwrites on the existing volume
			backproject.normalizeVol(volfile)

			alignstack = spiderstack

			### center/convert the volume file
			mrcvolfile = self.processVolume(volfile, cnum, 0)

			for i in range(4):
				iternum = i+1
				apDisplay.printMsg("running backprojection iteration "+str(iternum))
				### xy-shift particles to volume projections
				alignstack = backproject.otrParticleShift(volfile, alignstack, eulerfile, iternum,
					numpart=len(includeParticle), pixrad=self.params['radius'], timestamp=self.timestamp, classnum=cnum)
				apDisplay.printColor("finished volume refinement in "
					+apDisplay.timeString(time.time()-looptime), "cyan")

				### back project particles into better volume
				volfile = os.path.join(self.params['rundir'], str(cnum), "volume%s-%03d.spi"%(self.timestamp, iternum))
				backproject.backproject3F(alignstack, eulerfile, volfile, numpart=len(includeParticle))

				### filter the volume (low-pass Butterworth)
				backproject.butterworthLP(volfile, apix)

				### need work... filtered volume has a different name
				backproject.normalizeVol(volfile)

				### center/convert the volume file
				mrcvolfile = self.processVolume(volfile, cnum, iternum)

			###############################
			#										#
			# Andres's refinement steps	#
			#										#
			###############################
			print "\n"
			apDisplay.printMsg("##################################")
			apDisplay.printMsg("Starting Andres' refinement steps")
			apDisplay.printMsg("##################################")
			print "\n"


			for j in range(5):
				iternum = j+1
				appionData.ApPathData.direct_query(1)
				apDisplay.printMsg("Starting projection-matching refinement/XMIPP iteration "+str(iternum))

				boxsize = self.getBoxSize()
				### projection-matching refinement/XMIPP
				apshout, apshstack, apsheuler = self.projMatchRefine(cnum, volfile, alignstack, eulerfile, boxsize, len(includeParticle), self.params['radius'], iternum)

				apDisplay.printMsg("Calculating weighted cross-correlation coefficients")

				### calculation of weighted cross-correlation coefficients
				apshout_weighted = self.cccAPSH(apshout, cnum, iternum)

				apDisplay.printMsg("Creating select files based on weighted cross-correlation coefficients")

				### create select files based on calculated weighted-cross-correlation
				corrSelect = self.makecccAPSHselectFile(apshout_weighted, cnum, iternum, factor=0.1)

				### create volume file names
				apshVolfile = os.path.join(self.params['rundir'], str(cnum), "apshVolume-%03d.spi"%(iternum))

				### run BPRP on selected particles
				self.APSHbackProject(apshstack, apsheuler, apshVolfile, cnum, corrSelect)

				### center volume
				filename = os.path.splitext(apshVolfile)[0]
				apshVolFileCentered = filename+"_centered.spi"
				backproject.centerVolume(apshVolfile, apshVolFileCentered)

				### calculate FSC
				
				### generate odd and even select files for FSC calculation
				corrSelectOdd, corrSelectEven = self.splitOddEven(cnum, corrSelect, iternum)
				
				apshOddVolfile = os.path.join(self.params['rundir'], str(cnum), "apshVolume_Odd-%03d.spi"%(iternum))
				apshEvenVolfile = os.path.join(self.params['rundir'], str(cnum), "apshVolume_Even-%03d.spi"%(iternum))
				
				self.APSHbackProject(apshstack, apsheuler, apshOddVolfile, cnum, corrSelectOdd)
				self.APSHbackProject(apshstack, apsheuler, apshEvenVolfile, cnum, corrSelectEven)
				
				fscout = os.path.join(self.params['rundir'], str(cnum), "FSCout-%03d.spi"%(iternum))
				#backproject.calcFSC(apshCenteredVols[1], apshCenteredVols[2], fscout)

				### filter volume
				#backproject.butterworthFscLP(apshVolfile, fscout)

				volfile = apshVolFileCentered
				eulerfile = apsheuler
				mrcvolfile = self.processVolume(volfile, cnum, iternum)

				print "\n"
				apDisplay.printMsg("###########################")
				apDisplay.printMsg("Done with iteration "+str(j+1)+"")
				apDisplay.printMsg("###########################")
				print "\n"
		

		sys.exit(1)
		
		if len(self.classlist) > 1:
			#get a list of all unique combinations of volumes
			pairlist = self.computeClassVolPair()

		### insert volumes into DB
		self.insertOtrRun(mrcvolfile)

#=====================
if __name__ == "__main__":
	otrVolume = otrVolumeScript()
	otrVolume.start()
	otrVolume.close()

