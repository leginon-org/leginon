#!/usr/bin/env python

#python
import os
import re
import time
import sys
import random
import math
import shutil
import glob
import cPickle
import subprocess
import numpy
import MySQLdb
#appion
import appionScript
import apDisplay
import apFile
import apTemplate
import apStack
import apParam
import apEMAN
import apXmipp
import appionData
import apVolume
import spyder
import apImagicFile
import apProject
from apSpider import alignment
from pyami import spider
import sinedon

"""
USE 
http://www.wadsworth.org/spider_doc/spider/docs/man/sy.html
to create SYMMETRY DOC files
"""

#=====================
#=====================
class MaximumLikelihoodScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")

		### strings
		self.parser.add_option("--sym", "--symmetry", dest="symmetry",
			help="Symmetry", metavar="#")
		self.parser.add_option("-m", "--model-ids", dest="modelstr",
			help="Initial Model IDs", metavar="#")

		### integers
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--cluster-id", dest="clusterid", type="int",
			help="clustering stack id", metavar="ID")
		self.parser.add_option("--align-id", dest="alignid", type="int",
			help="alignment stack id", metavar="ID")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("--nproc", dest="nproc", type="int",
			help="Number of processor to use", metavar="ID#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")
		self.parser.add_option("--numvol", dest="nvol", type="int", default=2,
			help="Number of volumes to create", metavar="#")
		self.parser.add_option("--max-iter", dest="maxiter", type="int", default=100,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--phi", "--angle-increment", dest="phi", type="int", default=5,
			help="Projection sampling interval (degrees)", metavar="#")
		self.parser.add_option("--psi", "--angle-inplane", dest="psi", type="int", default=5,
			help="In-plane rotation sampling interval (degrees)", metavar="#")

		### floats
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="float",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="float",
			help="High pass filter radius (in Angstroms)", metavar="#")

		### true/false
		self.parser.add_option("-F", "--fast", dest="fast", default=True,
			action="store_true", help="Use fast method")
		self.parser.add_option("--no-fast", dest="fast", default=True,
			action="store_false", help="Do NOT use fast method")
		self.parser.add_option("-M", "--mirror", dest="mirror", default=True,
			action="store_true", help="Use mirror method")
		self.parser.add_option("--no-mirror", dest="mirror", default=True,
			action="store_false", help="Do NOT use mirror method")
		self.parser.add_option("--norm", dest="norm", default=False,
			action="store_true", help="Use internal normalization for data with normalization errors")
		self.parser.add_option("--no-norm", dest="norm", default=False,
			action="store_false", help="Do NOT use internal normalization")

		### choices
		self.fastmodes = ( "normal", "narrow", "wide" )
		self.parser.add_option("--fast-mode", dest="fastmode",
			help="Search space reduction cutoff criteria", metavar="MODE", 
			type="choice", choices=self.fastmodes, default="normal" )
		self.convergemodes = ( "normal", "fast", "slow" )
		self.parser.add_option("--converge", dest="converge",
			help="Convergence criteria mode", metavar="MODE", 
			type="choice", choices=self.convergemodes, default="normal" )

	#=====================
	def checkConflicts(self):
		apDisplay.printMsg("rm -f *.hed *.img *.doc *.vol *.mrc *.spi *.log *~ *.pickle *.hist *.proj *.xmp *.sel *.basis *.original; rm -fr volume*")
		### check for missing and duplicate entries
		#if self.params['alignid'] is None and self.params['clusterid'] is None:
		#	apDisplay.printError("Please provide either --cluster-id or --align-id")
		if self.params['alignid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please provide only one of either --cluster-id or --align-id")		

		if self.params['modelstr'] is None and self.params['nvol'] is None:
			apDisplay.printError("Please provide model numbers or number of volumes")
		elif self.params['modelstr'] is not None:
			modellist = self.params['modelstr'].split(",")
			self.params['modelids'] = []
			for modelid in modellist:
				self.params['modelids'].append(int(modelid))

		### get the stack ID from the other IDs
		if self.params['alignid'] is not None:
			self.alignstackdata = appionData.ApAlignStackData.direct_query(self.params['alignid'])
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		elif self.params['clusterid'] is not None:
			self.clusterstackdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.alignstackdata = self.clusterstackdata['clusterrun']['alignstack']
			self.params['stackid'] = self.alignstackdata['stack'].dbid
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")


		#if self.params['description'] is None:
		#	apDisplay.printError("run description was not defined")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if not self.params['fastmode'] in self.fastmodes:
			apDisplay.printError("fast mode must be on of: "+str(self.fastmodes))
		maxparticles = 150000
		minparticles = 50
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: " 
				+ str(maxparticles) + " requested: " + str(self.params['numpart']))
		if self.params['numpart'] < minparticles:
			apDisplay.printError("not enough particles requested, min: " 
				+ str(minparticles) + " requested: " + str(self.params['numpart']))
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)

		### find number of processors
		if self.params['nproc'] is None:
			self.nproc = apParam.getNumProcessors()
		else:
			self.nproc = self.params['nproc']
		self.mpirun = self.checkMPI()

	#=====================
	def setRunDir(self):
		"""
		This funcion is only run when the user does not specifiy 'rundir'
		"""
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "maxlike-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		cPickle.dump(self.params, pf)
		pf.close()

	#=====================
	def insertMaxLikeJob(self):
		maxjobq = appionData.ApMaxLikeJobData()
		maxjobq['runname'] = self.params['runname']
		maxjobq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		maxjobdatas = maxjobq.query(results=1)
		if maxjobdatas:
			alignrunq = appionData.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		maxjobq['timestamp'] = self.timestamp
		maxjobq['finished'] = False
		maxjobq['hidden'] = False
		#if self.params['commit'] is True:
		#	maxjobq.insert()
		self.params['maxlikejobid'] = maxjobq.dbid
		print "self.params['maxlikejobid']",self.params['maxlikejobid']
		return

	#=====================
	def readyUploadFlag(self):
		if self.params['commit'] is False:
			return
		config = sinedon.getConfig('appionData')
		dbc = MySQLdb.Connect(**config)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApMaxLikeJobData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['maxlikejobid'])+"'"
		)
		cursor.execute(query)
		cursor.close()
		dbc.close()

	#=====================
	def estimateIterTime(self):
		secperiter = 0.12037
		calctime = (
			(self.params['numpart']/1000.0)
			*(self.stack['boxsize']/self.params['bin'])**2
			/self.params['angle']**2
			/float(self.nproc)
			*secperiter
		)
		if self.params['mirror'] is True:
			calctime *= 2.0
		self.params['estimatedtime'] = calctime
		apDisplay.printColor("Estimated first iteration time: "+apDisplay.timeString(calctime), "purple")

	#=====================
	def checkMPI(self):
		mpiexe = apParam.getExecPath("mpirun")
		if mpiexe is None:
			return None
		xmippexe = apParam.getExecPath("xmipp_mpi_ml_refine3d")
		if xmippexe is None:
			return None
		lddcmd = "ldd "+xmippexe+" | grep mpi"
		proc = subprocess.Popen(lddcmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		proc.wait()
		lines = proc.stdout.readlines()
		#print "lines=", lines
		if lines and len(lines) > 0:
			return mpiexe
		else:
			apDisplay.printWarning("Failed to find mpirun")
			print "lines=", lines
			return None

	#=====================
	def writeXmippLog(self, text):
		f = open("xmipp.log", "a")
		f.write(apParam.getLogHeader())
		f.write(text+"\n")
		f.close()

	#=====================
	def createGaussianSphere(self, volfile, boxsize):
		stdev = boxsize/5.0
		randdev = boxsize/20.0
		halfbox = boxsize/2.0
		#width of Gaussian
		gaussstr = ("%.3f,%.3f,%.3f"
			%(stdev+randdev*random.random(), stdev+randdev*random.random(), stdev+randdev*random.random()))
		apDisplay.printMsg("Creating Gaussian volume with stdev="+gaussstr)
		mySpider = spyder.SpiderSession(logo=False)
		mySpider.toSpiderQuiet("MO 3",
			spyder.fileFilter(volfile),
			"%d,%d,%d"%(boxsize,boxsize,boxsize),
			"G", #G for Gaussian
			"%.3f,%.3f,%.3f"%(halfbox,halfbox,halfbox), #center of Gaussian
			gaussstr,
		)
		mySpider.close()
		return

	#=====================
	def normalizeVolume(self, volfile):
		"""
mkdir CorrectGreyscale

xmipp_header_extract -i experimental_images.sel -o experimental_images.doc

xmipp_angular_project_library  -i bad_greyscale.vol -experimental_images experimental_images.doc -o CorrectGreyscale/ref -sampling_rate 15 -sym c1h -compute_neighbors -angular_distance -1

xmipp_angular_projection_matching  -i experimental_images.doc -o CorrectGreyscale/corrected_reference -ref CorrectGreyscale/ref

xmipp_mpi_angular_class_average  -i CorrectGreyscale/corrected_reference.doc -lib CorrectGreyscale/ref_angles.doc -o CorrectGreyscale/corrected_reference

xmipp_mpi_reconstruct_wbp  -i CorrectGreyscale/corrected_reference_classes.sel -o corrected_reference.vol -threshold 0.02 -sym c1  -use_each_image -weight
		"""
		volroot = os.path.splitext(volfile)[0]
		volroot = re.sub("\.", "_", volroot)
		normfolder = os.path.join(self.params['rundir'], volroot)
		apParam.createDirectory(normfolder)

		### Create Euler doc file for particles
		partselfile = os.path.join(self.params['rundir'], self.partlistdocfile)
		parteulerdoc = os.path.join(normfolder, "parteulers.doc")
		xmippcmd = "xmipp_header_extract -i %s -o %s"%(partselfile, parteulerdoc)
		apEMAN.executeEmanCmd(xmippcmd, verbose=False)
		if not os.path.isfile(parteulerdoc):
			apDisplay.printError("Could not normalize volume for file: "+volfile)

		### Create projections
		refprefix = os.path.join(normfolder, "refproj"+self.timestamp)
		if self.nproc > 1 and self.mpirun is not None:
			xmipppath = apParam.getExecPath("xmipp_mpi_angular_project_library", die=True)
			xmippexe = self.mpirun+" -np "+str(self.nproc)+" "+xmipppath
		else:
			xmippexe = "xmipp_angular_project_library"
		xmippcmd = ("%s -i %s -experimental_images %s -o %s"
			%(xmippexe, volfile, parteulerdoc, refprefix))
		xmippcmd += " -sampling_rate %d -compute_neighbors -angular_distance -1 -perturb 0.5"%(self.params['phi'])
		if self.params['symmetry'] is not None:
			xmippcmd += " -sym "+str(self.params['symmetry'])
		apEMAN.executeEmanCmd(xmippcmd, verbose=False)
		refs = glob.glob(refprefix+"*.xmp")
		if not refs:
			apDisplay.printError("Could not normalize volume for file: "+volfile)

		### Match projections
		fixprefix = os.path.join(normfolder, "match"+self.timestamp)
		if self.nproc > 1 and self.mpirun is not None:
			xmipppath = apParam.getExecPath("xmipp_mpi_angular_projection_matching", die=True)
			xmippexe = self.mpirun+" -np "+str(self.nproc)+" "+xmipppath
		else:
			xmippexe = "xmipp_angular_projection_matching"
		xmippcmd = ("%s -i %s -o %s -ref %s"
			%(xmippexe, parteulerdoc, fixprefix, refprefix))
		apEMAN.executeEmanCmd(xmippcmd, verbose=False)
		docfile = fixprefix+".doc"
		if not os.path.isfile(docfile):
			apDisplay.printError("Could not normalize volume for file: "+volfile)

		### Create projection averages
		correctprefix = os.path.join(normfolder, "correctproj"+self.timestamp)
		if self.nproc > 1 and self.mpirun is not None:
			xmipppath = apParam.getExecPath("xmipp_mpi_angular_class_average", die=True)
			xmippexe = self.mpirun+" -np "+str(self.nproc)+" "+xmipppath
		else:
			xmippexe = "xmipp_angular_class_average"
		xmippcmd = ("%s -i %s.doc -lib %s_angles.doc -o %s"
			%(xmippexe, fixprefix, refprefix, correctprefix))
		apEMAN.executeEmanCmd(xmippcmd, verbose=False)
		refs = glob.glob(correctprefix+"*.xmp")
		if not refs:
			apDisplay.printError("Could not normalize volume for file: "+volfile)

		### Backproject
		correctvolfile = os.path.join(normfolder, "volume"+self.timestamp+".spi")
		if self.nproc > 1 and self.mpirun is not None:
			xmipppath = apParam.getExecPath("xmipp_mpi_reconstruct_wbp", die=True)
			xmippexe = self.mpirun+" -np "+str(self.nproc)+" "+xmipppath
		else:
			xmippexe = "xmipp_reconstruct_wbp"
		xmippcmd = ("%s -i %s_classes.sel -o %s"
			%(xmippexe, correctprefix, correctvolfile))
		xmippcmd += " -threshold 0.02 -use_each_image -weight"
		if self.params['symmetry'] is not None:
			xmippcmd += " -sym "+str(self.params['symmetry'])
		apEMAN.executeEmanCmd(xmippcmd, verbose=False)

		if not os.path.isfile(correctvolfile):
			apDisplay.printError("Could not normalize volume for file: "+volfile)
		return correctvolfile

	#=====================
	def setupVolumes(self, boxsize, apix):
		voldocfile = "volumelist"+self.timestamp+".doc"
		f = open(voldocfile, "w")
		if self.params['modelstr'] is not None:
			for i, modelid in enumerate(self.params['modelids']):
				### Scale volume
				mrcvolfile = os.path.join(self.params['rundir'], "volume%s_%02d_%05d.mrc"%(self.timestamp, i+1, modelid))
				apVolume.rescaleModelId(modelid, mrcvolfile, apix, boxsize)

				### Convert volume to spider
				spivolfile = os.path.join(self.params['rundir'], "volume%s_%02d_%05d.spi"%(self.timestamp, i+1, modelid))
				emancmd = "proc3d %s %s spidersingle"%(mrcvolfile, spivolfile)
				apEMAN.executeEmanCmd(emancmd, verbose=False)

				### Normalize volume
				normalvolfile = self.normalizeVolume(spivolfile)
		
				### Write to selection file
				f.write(normalvolfile+" 1\n")
		else:
			for i in range(self.params['nvol']):
				### Create Gaussian sphere
				spivolfile = os.path.join(self.params['rundir'], "volume%s_%02d.spi"%(self.timestamp, i+1))
				self.createGaussianSphere(spivolfile, boxsize)

				### Normalize volume
				normalvolfile = self.normalizeVolume(spivolfile)

				### Write to selection file
				f.write(normalvolfile+" 1\n")
		f.close()
		return voldocfile

	#=====================
	def setupParticles(self):
		self.params['localstack'] = os.path.join(self.params['rundir'], self.timestamp+".hed")

		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		boxsize = int(math.floor(self.stack['boxsize']/float(self.params['bin']*2)))*2
		apix = self.stack['apix']*self.params['bin']

		proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1:
			clipsize = boxsize*self.params['bin']
			proccmd += " shrink=%d clip=%d,%d "%(self.params['bin'],clipsize,clipsize)
		if self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		proccmd += " last="+str(self.params['numpart']-1)
		apFile.removeStack(self.params['localstack'], warn=False)
		apEMAN.executeEmanCmd(proccmd, verbose=True)

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])
		return (boxsize, apix)

	#=====================
	def runrefine(self):
		### setup Xmipp command
		recontime = time.time()

		xmippopts = ( " "
			+" -i "+os.path.join(self.params['rundir'], self.partlistdocfile)
			+" -vol "+os.path.join(self.params['rundir'], self.voldocfile)
			+" -iter "+str(self.params['maxiter'])
			+" -o "+os.path.join(self.params['rundir'], "part"+self.timestamp)
			+" -psi_step "+str(self.params['psi'])
			+" -ang "+str(self.params['phi'])
		)
		### fast mode
		if self.params['fast'] is True:
			xmippopts += " -fast "
			if self.params['fastmode'] == "narrow":
				xmippopts += " -C 1e-10 "
			elif self.params['fastmode'] == "wide":
				xmippopts += " -C 1e-18 "
		### convergence criteria
		if self.params['converge'] == "fast":
			xmippopts += " -eps 5e-3 "
		elif self.params['converge'] == "slow":
			xmippopts += " -eps 5e-8 "
		else:
			xmippopts += " -eps 5e-5 "
		### mirrors
		if self.params['mirror'] is True:
			xmippopts += " -mirror "
		### normalization
		if self.params['norm'] is True:
			xmippopts += " -norm "
		### symmetry
		if self.params['symmetry'] is not None:
			xmippopts += " -sym "+self.params['symmetry']+" "

		if self.nproc > 1 and self.mpirun is not None:
			### use multi-processor
			apDisplay.printColor("Using "+str(self.nproc)+" processors!", "green")
			xmippexe = apParam.getExecPath("xmipp_mpi_ml_refine3d", die=True)
			mpiruncmd = self.mpirun+" -np "+str(self.nproc)+" "+xmippexe+" "+xmippopts
			self.writeXmippLog(mpiruncmd)
			apEMAN.executeEmanCmd(mpiruncmd, verbose=True, showcmd=True)
		else:
			### use single processor
			xmippexe = apParam.getExecPath("xmipp_ml_refine3d", die=True)
			xmippcmd = xmippexe+" "+xmippopts
			self.writeXmippLog(xmippcmd)
			apEMAN.executeEmanCmd(xmippcmd, verbose=True, showcmd=True)
		apDisplay.printMsg("Reconstruction time: "+apDisplay.timeString(time.time() - recontime))

	#=====================
	def start(self):
		#self.insertMaxLikeJob()

		#self.estimateIterTime()
		self.dumpParameters()

		### set particles
		(boxsize, apix) = self.setupParticles()

		### setup volumes

		self.voldocfile = self.setupVolumes(boxsize, apix)

		### run the refinement
		self.dumpParameters()
		self.runrefine()

		#self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	maxLike = MaximumLikelihoodScript(True)
	maxLike.start()
	maxLike.close()


