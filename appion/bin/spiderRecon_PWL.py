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
from appionlib import appionScript
from appionlib import apStack
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apRecon
from appionlib import apChimera
from appionlib import apProject
from appionlib import apParam
from appionlib.apTilt import apTiltPair
from appionlib.apSpider import operations
try:
	from appionlib.apSpider import backprojectPWL
except ImportError:
	print "Pick-wei fix this"
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
		#self.parser.add_option("--classnums", dest="classnums", type="str",
		#	help="Class numbers to use for rct volume, e.g. 0,1,2", metavar="#")
		self.parser.add_option("--initvol", dest="initvol", type="str",
			help="Path and file name of initial model", metavar="#")
		
		### integers
		self.parser.add_option("--part-stack", dest="partstackid", type="int",
			help="Particle Stack ID", metavar="#")
		self.parser.add_option("--modelid", dest="modelid", type="int", 
			help="model ID", metavar="#")
		self.parser.add_option("--refine-iters", dest="refineiters", type="int", default=4, 
			help="Number of euler angle refinement iterations", metavar="#")
		self.parser.add_option("--mask-rad", dest="radius", type="int",
			help="Particle mask radius (in pixels)", metavar="ID")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Binning of the stack image", metavar="ID")
		self.parser.add_option("--num-part", dest="numpart", type="int",
			help="Limit number of particles, for debugging", metavar="#")
		self.parser.add_option("--median", dest="median", type="int", default=3,
			help="Median filter", metavar="#")

		### floats
		self.parser.add_option("--initvolapix", dest="initvolapix", type="float",
			help="initial model apix", metavar="#")
		self.parser.add_option("--lowpassvol", dest="lowpassvol", type="float", default=10.0,
			help="Low pass volume filter (in Angstroms)", metavar="#")
		self.parser.add_option("--highpasspart", dest="highpasspart", type="float", default=600.0,
			help="High pass particle filter (in Angstroms)", metavar="#")
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
		### check and make sure we got the stack id
		if self.params['partstackid'] is None:
			apDisplay.printError("please specify a stack ID")
		else:
			self.partstackdata = appiondata.ApStackData.direct_query(self.params['partstackid'])
						
		if self.params['radius'] is None:
			apDisplay.printError("particle mask radius was not defined")
		if self.params['description'] is None:
			apDisplay.printError("enter a description")
		
		boxsize = self.getBoxSize()
		if self.params['radius']*2 > boxsize-2:
			apDisplay.printError("particle radius is too big for stack boxsize")	

		if self.params['initvol'] is None and self.params['modelid'] is None:
			apDisplay.printError("--initvol: please specify an initial model")

		if self.params['initvol'] is not None and self.params['modelid'] is not None:
			apDisplay.printError("please specify only initvol or modelid")
		
		if self.params['initvol'] is not None:
			if os.path.isfile(self.params['initvol']) is False:
				apDisplay.printError(self.params['initvol']+" does not exist!")
			if self.params['initvolapix'] is None:
				apDisplay.printError("Please specify apix for initial model!")	
		

				
	#=====================
	def setRunDir(self):
		stackdata = apStack.getOnlyStackData(self.params['partstackid'], msg=False)
		path = stackdata['path']['path']
		uppath = os.path.dirname(os.path.dirname(os.path.abspath(path)))
		
		self.params['rundir'] = os.path.join(uppath, "SpiderRecon",
			self.params['runname'] )

		print self.params['rundir']
		
#		### check if path exists in db already
#		otrrunq = appiondata.ApOtrRunData()
#		otrrunq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
#		otrdata = otrrunq.query()
#		if otrdata:
#			apDisplay.printError("otr data already exists in database")

	#=====================
	def getParticleNoRefInPlaneRotation(self, stackpartdata):
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'],
			stackpartdata['particleNumber'], self.params['notstackid'])
		classpartq = appiondata.ApNoRefClassParticlesData()
		classpartq['classRun'] = self.norefclassdata
		norefpartq = appiondata.ApNoRefAlignParticlesData()
		norefpartq['particle'] = notstackpartdata
		classpartq['noref_particle'] = norefpartq
		classpartdatas = classpartq.query(results=1)
		if not classpartdatas or len(classpartdatas) != 1:
			apDisplay.printError("could not get inplane rotation")
		inplane = classpartdatas[0]['noref_particle']['rotation']
		return inplane

	#=====================
	def convertStackToSpider(self, emanstackfile, spiderstack=None):
		"""
		takes the stack file and creates a spider file ready for processing
		"""
		if not os.path.isfile(emanstackfile):
			apDisplay.printError("stackfile does not exist: "+emanstackfile)

		### first high pass filter particles
		#apDisplay.printMsg("pre-filtering particles")
		#apix = apStack.getStackPixelSizeFromStackId(self.params['partstackid'])
		#emancmd = ("proc2d "+emanstackfile+" "+emanstackfile
		#	+" apix="+str(apix)+" hp="+str(self.params['highpasspart'])
		#	+" inplace")
		#apEMAN.executeEmanCmd(emancmd, verbose=True)

		### convert imagic stack to spider
		emancmd  = "proc2d "
		emancmd += emanstackfile+" "
		if spiderstack is None:
			spiderstack = os.path.join(self.params['rundir'], "start.spi")
		apFile.removeFile(spiderstack, warn=True)
		emancmd += spiderstack+" "

		emancmd += "spiderswap edgenorm"
		starttime = time.time()
		apDisplay.printColor("Running spider stack conversion this can take a while", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished eman in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spiderstack
		
	#=====================
	def convertVolToSpider(self, mrcvolfile=None, modelid=None, apix=None, spivolfile=None):
		"""
		takes the mrc volume and creates a spider file ready for processing
		"""
		if modelid is not None:
			initModelData = appiondata.ApInitialModelData.direct_query(modelid)
			mrcvolfile = initModelData['path']['path']+"/"+initModelData['name']
			apix = initModelData['pixelsize']
			
		stackapix = apStack.getStackPixelSizeFromStackId(self.params['partstackid'])*self.params['bin']
		stackboxsize = apStack.getStackBoxsize(self.params['partstackid'])/self.params['bin']
		
		print apix
		print mrcvolfile

		if not os.path.isfile(mrcvolfile):
			apDisplay.printError("volfile does not exist: "+mrcvolfile)

		### first high pass filter particles
		#apDisplay.printMsg("pre-filtering particles")
		#apix = apStack.getStackPixelSizeFromStackId(self.params['partstackid'])
		#emancmd = ("proc3d "+mrcvolfile+" "+emanstackfile
		#	+" apix="+str(apix)+" hp="+str(self.params['highpasspart'])
		#	+" inplace")
		#apEMAN.executeEmanCmd(emancmd, verbose=True)

		### convert imagic stack to spider
		emancmd  = "proc3d "
		emancmd += mrcvolfile+" "
		if spivolfile is None:
			spivolfile = os.path.join(self.params['rundir'], "threed-0a.spi")
		apFile.removeFile(spivolfile, warn=True)
		emancmd += spivolfile+" "

		emancmd += "scale="+str(apix/stackapix)+" "
		emancmd += "clip="+str(stackboxsize)+","+str(stackboxsize)+","+str(stackboxsize)+" "
		emancmd += "spidersingle"
		starttime = time.time()
		apDisplay.printColor("Running spider volume conversion", "cyan")
		apEMAN.executeEmanCmd(emancmd, verbose=True)
		apDisplay.printColor("finished conversion in "+apDisplay.timeString(time.time()-starttime), "cyan")
		return spivolfile

	#=====================
	def sortTiltParticlesData(self, a, b):
		if a['particleNumber'] > b['particleNumber']:
			return 1
		return -1

	#=====================
	def getBoxSize(self):
		boxsize = apStack.getStackBoxsize(self.params['partstackid'])
		if self.params['bin'] == 1:
			return boxsize
		newbox = int( math.floor( boxsize / float(self.params['bin']) / 2.0)* 2.0 )
		return newbox



	#=====================
	def getParticleInPlaneRotation(self, tiltstackpartdata):
		partid = tiltstackpartdata.dbid
		if partid in self.rotmirrorcache:
			### use cached value
			return self.rotmirrorcache[partid] 

		partnum = tiltstackpartdata['particleNumber']
		notstackpartdata = apTiltPair.getStackParticleTiltPair(self.params['tiltstackid'], 
			partnum, self.params['notstackid'])

		alignpartq = appiondata.ApAlignParticleData()
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
		### setup resolutions
		fscresq = appiondata.ApResolutionData()
		fscresq['type'] = "fsc"
		fscresq['half'] = self.fscresolution
		fscresq['fscfile'] = "fscdata"+self.timestamp+".fsc"
		rmeasureq = appiondata.ApResolutionData()
		rmeasureq['type'] = "rmeasure"
		rmeasureq['half'] = self.rmeasureresolution
		rmeasureq['fscfile'] = None

		### insert rct run data
		otrrunq = appiondata.ApOtrRunData()
		otrrunq['runname']    = self.params['runname']
		tempstr = ""
		for cnum in self.classlist:
			tempstr += str(cnum)+","
		classliststr = tempstr[:-1]
		otrrunq['classnums']  = classliststr
		otrrunq['numiter']    = self.params['numiters']
		otrrunq['euleriter']  = self.params['refineiters']
		otrrunq['maskrad']    = self.params['radius']
		otrrunq['lowpassvol'] = self.params['lowpassvol']
		otrrunq['highpasspart'] = self.params['highpasspart']
		otrrunq['median'] = self.params['median']
		otrrunq['description'] = self.params['description']
		otrrunq['path']  = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		otrrunq['alignstack'] = self.alignstackdata
		otrrunq['tiltstack']  = apStack.getOnlyStackData(self.params['tiltstackid'])
		otrrunq['numpart']  = self.numpart
		otrrunq['fsc_resolution'] = fscresq
		otrrunq['rmeasure_resolution'] = rmeasureq
		if self.params['commit'] is True:
			otrrunq.insert()

		### insert 3d volume density
		densq = appiondata.Ap3dDensityData()
		densq['otrrun'] = otrrunq
		densq['path'] = appiondata.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		densq['symmetry'] = appiondata.ApSymmetryData.direct_query(25)
		densq['pixelsize'] = apStack.getStackPixelSizeFromStackId(self.params['partstackid'])*self.params['bin']
		densq['boxsize'] = self.getBoxSize()
		densq['lowpass'] = self.params['lowpassvol']
		densq['highpass'] = self.params['highpasspart']
		densq['mask'] = self.params['radius']
		#densq['iterid'] = self.params['numiters']
		densq['description'] = self.params['description']
		densq['resolution'] = self.fscresolution
		densq['rmeasure'] = self.rmeasureresolution
		densq['session'] = apStack.getSessionDataFromStackId(self.params['tiltstackid'])
		densq['md5sum'] = apFile.md5sumfile(volfile)
		if self.params['commit'] is True:
			densq.insert()

		return

	#=====================
	def processVolume(self, spivolfile, cnum, iternum=0):
		### set values
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])*self.params['bin']
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
			apChimera.renderSnapshots(mrcvolfile, self.params['contour'], self.params['zoom'], 'c1')
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

			### Hack for OTR to work ( bad tilt axis angle from tilt picker )
			tiltrot = -7.0
			notrot = -7.0
			
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
	def projMatchRefine(self, volfile, alignstack, boxsize, numpart, pixrad, iternum):

		APSHout, projstack, numprojs = backprojectPWL.alignAPSH(volfile, alignstack, boxsize, numpart, pixrad, self.timestamp, iternum)
		### check APSH output
		if (os.path.isfile(APSHout) is False):
			apDisplay.printError("AP SH alignment did not generate a valid output file. Please check parameters and rerun!")

		apsh = open(APSHout, "r")

		neweulerdoc = os.path.join(self.params['rundir'],"newEulersdoc-%03d.spi"%(iternum))
		neweulerfile = open(neweulerdoc, "w")
		rotshiftdoc = os.path.join(self.params['rundir'],"rotShiftdoc-%03d.spi"%(iternum))
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
			cumX = float(value[14]) #float(value[8])
			cumY = float(value[15]) #float(value[9])
			psi = float(value[2])
			theta = float(value[3])
			phi = float(value[4])
			mirror = int(float(value[16]))
			
			### write out new euler file
			eulerline = operations.spiderOutLine(key, [psi, theta, phi])
			neweulerfile.write(eulerline)
			
			### write out new rotate-shift-mirror file
			rotshiftline = operations.spiderOutLine(key, [key, rot, 1.00, cumX, cumY, mirror])
			rotshiftfile.write(rotshiftline)
			count+=1
			
			#if (count%20) == 0:
			#	apDisplay.printColor(str(numpart-count)+" particles left", "cyan")
			#	apDisplay.printColor("Estimated time left is "+apDisplay.timeString(((time.time()-starttime)/count)*(numpart-count)), "cyan")
		
		neweulerfile.close()
		rotshiftfile.close()

		### rotate and shift particle
		APSHstack = backprojectPWL.rotshiftParticle(alignstack, rotshiftdoc, iternum, self.timestamp)
		#APSHstack = backprojectPWL.rotshiftParticle(alignstack, key, rot, cumX, cumY, mirror, iternum, self.timestamp)
			
		apDisplay.printColor("finished rotating and shifting particles "+apDisplay.timeString(time.time()-starttime), "cyan")

		return APSHout, APSHstack, neweulerdoc, projstack, numprojs

	#===================== Andres script #2 --- p.weighted_CCC_APSH.spi
	def cccAPSH(self, APSHout, iternum):
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
		APSHout_weighted = os.path.join(self.params['rundir'], "apshOut_weighted-%03d.spi"%(iternum))

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
	def makecccAPSHselectFile(self, APSHout, iternum, factor):

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

		corrSelect = os.path.join(self.params['rundir'], "apshCorrSelect-%03d.spi"%(iternum))
		corrSelectFile = open(corrSelect, "w")


		for i,corrValue in enumerate(corrValues):

			if corrValue >= threshold:
				line = operations.spiderOutLine(count, [i+1])
				corrSelectFile.write(line)
				count+=1

		corrSelectFile.close()

		if count == 0:
			apDisplay.printError("no correlation value is above threshold!")

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
	def APSHbackProject(self, spiderstack, eulerfile, volfile, selectFile):

		# file that stores the number of iteration for BPRP
		BPRPcount = os.path.join(self.params['rundir'], "numiter.spi")

		if (os.path.isfile(BPRPcount)):
			apDisplay.printMsg("BP RP counter file exists: "+BPRPcount+"! File will be deleted.")
			apFile.removeFile(BPRPcount)

		BPRPlambda=2e-5
		backprojectPWL.backprojectRP(spiderstack, eulerfile, volfile,
			pixrad=self.params['radius'], lambDa=BPRPlambda, numpart=selectFile)

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
							backprojectPWL.backprojectRP(spiderstack, eulerfile, volfile,
								pixrad=self.params['radius'], lambDa=BPRPlambda, numpart=selectFile)
			else:
				apDisplay.printWarning("numiter is missing")
				continue
			rounds+=1

		### print warning if BPRP reaches 100 rounds
		if rounds >=100:
			apDisplay.printWarning("BPRP attempted 100 times but iteration is still less than 50. Check BPRP params.")

		return

	#=====================
	def runEoTest(self, corrSelectOdd, corrSelectEven, cnum, apshstack, apsheuler, iternum):

				
		apshOddVolfile = os.path.join(self.params['rundir'], str(cnum), "apshVolume_Odd-%03d.spi"%(iternum))
		apshEvenVolfile = os.path.join(self.params['rundir'], str(cnum), "apshVolume_Even-%03d.spi"%(iternum))
		
		self.APSHbackProject(apshstack, apsheuler, apshOddVolfile, cnum, corrSelectOdd)
		self.APSHbackProject(apshstack, apsheuler, apshEvenVolfile, cnum, corrSelectEven)
		
		fscout = os.path.join(self.params['rundir'], str(cnum), "FSCout-%03d.spi"%(iternum))
		backproject.calcFSC(apshOddVolfile, apshEvenVolfile, fscout)

		### Calculate FSC - taken from Neil's RCT script
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])*self.params['bin']
		emancmd = "proc3d %s %s"%(apshEvenVolfile, apshEvenVolfile+".mrc")
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		emancmd = "proc3d %s %s"%(apshOddVolfile, apshOddVolfile+".mrc")
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		fscfile = os.path.join(self.params['rundir'], "fscdata%s.fsc"%(self.timestamp))
		emancmd = "proc3d %s %s fsc=%s"%(apshEvenVolfile+".mrc", apshOddVolfile+".mrc", fscfile)
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)

		if not os.path.isfile(fscfile):
			apDisplay.printError("Even-Odd fsc calculation failed")
		boxsize = self.getBoxSize()
		self.fscresolution = apRecon.getResolutionFromFSCFile(fscfile, boxsize, apix, msg=True)
		apDisplay.printColor( ("Final FSC resolution: %.5f" % (self.fscresolution)), "cyan")
		
		return fscout

	#=====================
	def runRmeasure(self, volfile):
		emancmd = "proc3d %s %s"%(volfile, "rmeasure.mrc")
		apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		apix = apStack.getStackPixelSizeFromStackId(self.params['tiltstackid'])*self.params['bin']
		self.rmeasureresolution = apRecon.runRMeasure(apix, "rmeasure.mrc")
		#apDisplay.printColor("Final Rmeasure resolution: "+str(self.rmeasureresolution), "cyan")
		apFile.removeFile("rmeasure.mrc")


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
		stackdata = apStack.getOnlyStackData(self.params['partstackid'])
			
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

		if self.params['initvol'] is not None:
			spidervol = self.convertVolToSpider(mrcvolfile=self.params['initvol'], apix=self.params['initvolapix'])
		
		if self.params['modelid'] is not None:	
			spidervol = self.convertVolToSpider(modelid=self.params['modelid'])
		
		partstack = stackdata['path']['path']+"/"+stackdata['name']
		spiderstack = self.convertStackToSpider(partstack)
		
		partsnum = apStack.getNumberStackParticlesFromId(self.params['partstackid'])
		
		for j in range(self.params['refineiters']):
			iternum = j+1
			appiondata.ApPathData.direct_query(1)
			apDisplay.printMsg("Starting projection-matching refinement/XMIPP iteration "+str(iternum))

			boxsize = self.getBoxSize()
			### projection-matching refinement/XMIPP
			apshout, apshstack, apsheuler, projstack, numprojs = self.projMatchRefine(spidervol, spiderstack, boxsize, partsnum, self.params['radius'], iternum)

			apDisplay.printMsg("Calculating weighted cross-correlation coefficients")

			### calculation of weighted cross-correlation coefficients
			apshout_weighted = self.cccAPSH(apshout, iternum)

			apDisplay.printMsg("Creating select files based on weighted cross-correlation coefficients")

			### create select files based on calculated weighted-cross-correlation
			corrSelect = self.makecccAPSHselectFile(apshout_weighted, iternum, factor=0.1)

			### create volume file names
			apshVolfile = os.path.join(self.params['rundir'], "apshVolume-BPCG-%03d.spi"%(iternum))
			apshVolfile2 = os.path.join(self.params['rundir'], "apshVolume-BPRP-%03d.spi"%(iternum))

			### run BPRP on selected particles
			backprojectPWL.backprojectCG(apshstack, apsheuler, apshVolfile, partsnum, self.params['radius'])
			self.APSHbackProject(apshstack, apsheuler, apshVolfile2, partsnum)


			### center volume
			filename = os.path.splitext(apshVolfile)[0]
			apshVolFileCentered = filename+"_centered.spi"
			backprojectPWL.centerVolume(apshVolfile, apshVolFileCentered)

			### generate class averages
			backprojectPWL.createClassAverages(apshstack,projstack,apshout,numprojs,boxsize,outclass="classes",rotated=True,shifted=True,dataext=".spi")


			print "check~~!!!"
			sys.exit(1)

			### calculate FSC
			
			### generate odd and even select files for FSC calculation
			corrSelectOdd, corrSelectEven = self.splitOddEven(cnum, corrSelect, iternum)
			fscout = self.runEoTest(corrSelectOdd, corrSelectEven, cnum, apshstack, apsheuler, iternum)
			self.runRmeasure(apshVolFileCentered)
			
			### filter volume
			backproject.butterworthFscLP(apshVolFileCentered, fscout)

			### reset file names for next round
			volfile = apshVolFileCentered
			eulerfile = apsheuler
			mrcvolfile = self.processVolume(volfile, cnum, iternum)

			print "\n"
			apDisplay.printMsg("###########################")
			apDisplay.printMsg("Done with iteration "+str(j+1)+"")
			apDisplay.printMsg("###########################")
			print "\n"
		
		#if len(self.classlist) > 1:
			#get a list of all unique combinations of volumes
		#	pairlist = self.computeClassVolPair()

		### insert volumes into DB
		self.insertOtrRun(mrcvolfile)

#=====================
if __name__ == "__main__":
	otrVolume = otrVolumeScript()
	otrVolume.start()
	otrVolume.close()

