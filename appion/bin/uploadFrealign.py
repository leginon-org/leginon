#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import subprocess
#appion
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apChimera
from appionlib import apEulerJump
from appionlib import apStack
from appionlib import apModel
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apSymmetry
from appionlib import apRecon

class UploadFrealign(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --commit --description='<text>' [options]")
		### ints
		self.parser.add_option("--prepid", dest="prepid", type="int",
			help="ID for frealign prep", metavar="#")

		self.parser.add_option("--stackid", dest="stackid", type="int",
			help="ID for particle stack (optional)", metavar="#")
		self.parser.add_option("--modelid", dest="modelid", type="int",
			help="ID for initial model (optional)", metavar="#")

		self.parser.add_option("--mass", dest="mass", type="int",
			help="Particle mass in kDa for Chimera snapshots (optional)", metavar="#")

		### floats
		self.parser.add_option("--zoom", dest="zoom", type="float", default=1.0,
			help="Zoom factor for Chimera snapshots (optional)", metavar="#")

	#=====================
	def checkConflicts(self):
		if self.params['mass'] is None:
			apDisplay.printError("Please provide an estimate for the mass (in kDa), e.g. --mass=782")
		if self.params['prepid'] is not None:
			self.setPrepFrealignData(self.params['prepid'])
		if self.params['stackid'] is None:
			apDisplay.printError("Please provide a particle stack id")
		if self.params['modelid'] is None:
			apDisplay.printError("Please provide a initial model id")

	#=====================
	def setRunDir(self):
		apDisplay.printError("Please provide a run directory")

	#=====================
	def setPrepFrealignData(self, prepid):
		prepdata = appiondata.ApFrealignPrepareData.direct_query(prepid)
		#print prepdata
		self.params['stackid'] = prepdata['stack'].dbid
		self.params['modelid'] = prepdata['model'].dbid
		self.params['rundir'] = prepdata['path']['path']

	#=====================
	def parseFrealignParamFile(self, iternum):
		"""
		parse a typical FREALIGN parameter file from v8.08
		"""
		paramfile = "params.iter%03d.par"%(iternum)

		if not os.path.isfile(paramfile):
			apDisplay.printError("Parameter file does not exist: %s"%(paramfile))

		### cannot assume spaces will separate columns.
		#0000000001111111111222222222233333333334444444444555555555566666666667777777777888888888899999999990000000000
		#1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
		#     24  219.73   84.00  299.39   15.33  -17.51  10000.     1  27923.7  27923.7  -11.41   0.00    0.00
		f = open(paramfile, "r")
		parttree = []
		apDisplay.printMsg("Processing parameter file: %s"%(paramfile))
		for line in f:
			sline = line.strip()
			if sline[0] == "C":
				### comment line
				continue
			partdict = {
				'partnum': int(line[0:7].strip()),
				'euler1': float(line[8:15]),
				'euler2': float(line[16:23]),
				'euler3': float(line[24:31]),
				'shiftx': float(line[32:39]),
				'shifty': float(line[40:47]),
				'phase_residual': float(line[88:94]),
			}
			parttree.append(partdict)
		f.close()
		if len(parttree) < 2:
			apDisplay.printError("No particles found in parameter file %s"%(paramfile))


		apDisplay.printMsg("Processed %d particles"%(len(parttree)))
		return parttree

	#=====================
	def checkResults(self):
		if not os.path.isfile("params.iter001.par"):
			### we do not have results
			if not os.path.isfile("results.tgz"):
				apDisplay.printError("Could not find Frealign results...")
			### the results are still zipped
			apDisplay.printMsg("Unzipping Frealign results...")
			cmd = "tar -xzf results.tgz"
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		if not os.path.isfile("threed.001a.hed"):
			### we do not have results
			if not os.path.isfile("models.tgz"):
				apDisplay.printError("Could not find Frealign models...")
			### the models are still zipped
			apDisplay.printMsg("Unzipping Frealign models...")
			cmd = "tar -xzf models.tgz"
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()
		return			

	#=====================
	def processFrealignVolume(self, iternum, symname):
		volumeImagicFile = os.path.join(self.params['rundir'], "threed.%03da.hed"%(iternum))
		if not os.path.isfile(volumeImagicFile):
			apDisplay.printError("Failed to find volume: %s"%(volumeImagicFile))
		volumeMrcFile = os.path.join(self.params['rundir'], "threed.%03da.mrc"%(iternum))
		if not os.path.isfile(volumeMrcFile):
			emancmd = "proc3d %s %s apix=%.3f origin=0,0,0 norm=0,1"%(volumeImagicFile, volumeMrcFile, self.apix)
			apEMAN.executeEmanCmd(emancmd, verbose=True, showcmd=True)
		if not os.path.isfile(volumeMrcFile):
			apDisplay.printError("Failed to convert volume")

		apChimera.filterAndChimera(volumeMrcFile, res=10, apix=self.apix, chimtype='snapshot',
			contour=1.0, zoom=self.params['zoom'], sym=symname, silhouette=True, mass=self.params['mass'])

		return volumeMrcFile

	#===============
	def cb(self, val):
		""" Convert single letter T or F to bool"""
		if val.lower().startswith('f') or val.strip() == '0':
			return False
		return True

	#=====================
	def readParamsFromCombineFile(self, iternum):
		"""
		read the combine file to get iteration parameters,
		such as symmetry and phase residual cutoff
		"""
		iterparams = {'iternum': iternum,}

		combinefile = "iter%03d/frealign.iter%03d.combine.sh"%(iternum, iternum)
		f = open(combinefile, "r")
		### locate start
		for line in f:
			if line.startswith("### START FREALIGN ###"):
				break

		### parse file
		cards = []
		for line in f:
			cards.append(line.strip())
			if line.startswith("EOF"):
				break
		f.close()

		### get lots of info from card #1
		data = cards[1].split(",")
		#print data
		iterparams['cform'] = data[0]
		iterparams['iflag'] = int(data[1])
		iterparams['fmag'] = self.cb(data[2])
		iterparams['fdef'] = self.cb(data[3])
		iterparams['fastig'] = self.cb(data[4])
		iterparams['fpart'] = self.cb(data[5])
		iterparams['iewald'] = float(data[6])
		iterparams['fbeaut'] = self.cb(data[7])
		iterparams['fcref'] = self.cb(data[8])
		iterparams['fmatch'] = self.cb(data[9])
		iterparams['ifsc'] = self.cb(data[10])
		iterparams['fstat'] = self.cb(data[11])
		iterparams['iblow'] = int(data[12])

		### get lots of info from card #2
		data = cards[2].split(",")
		#print data
		iterparams['mask'] = float(data[0])
		iterparams['imask'] = float(data[1])
		iterparams['wgh'] = float(data[3])
		iterparams['xstd'] = float(data[4])
		iterparams['pbc'] = float(data[5])
		iterparams['boff'] = float(data[6])
		iterparams['dang'] = float(data[7]) ### only used for recon search
		iterparams['itmax'] = int(data[8])
		iterparams['ipmax'] = int(data[9])

		### get symmetry info from card #5
		symmdata = apSymmetry.findSymmetry(cards[5])
		apDisplay.printMsg("Found symmetry %s with id %s"%(symmdata['eman_name'], symmdata.dbid))
		iterparams['symmdata'] = symmdata

		### get threshold info from card #6
		data = cards[6].split(",")
		#print data
		iterparams['target'] = float(data[2])
		iterparams['thresh'] = float(data[3])
		iterparams['cs'] = float(data[4])

		### get limit info from card #7
		data = cards[7].split(",")
		#print data
		iterparams['rrec'] = float(data[0])
		iterparams['highpass'] = float(data[1])
		iterparams['lowpass'] = float(data[2])
		iterparams['rbfact'] = float(data[4])

		#print iterparams
		return iterparams

	#==================
	def getRMeasureData(self, volumeDensity):
		volPath = os.path.join(self.params['rundir'], volumeDensity)
		if not os.path.exists(volPath):
			apDisplay.printWarning("R Measure failed, volume density not found: "+volPath)
			return None

		resolution = apRecon.runRMeasure(self.apix, volPath)
		if resolution is None:
			return None

		rmesq = appiondata.ApRMeasureData()
		rmesq['volume']=os.path.basename(volumeDensity)
		rmesq['rMeasure']=resolution
		return rmesq

	#==================
	def getResolutionData(self, iternum):
		fscfile = 'fsc.eotest.%d'%(iternum)
		fscpath = os.path.join(self.params['rundir'], "iter%03d"%(iternum), fscfile)

		if not os.path.isfile(fscpath):
			apDisplay.printWarning("Could not find FSC file: "+fscpath)
			return None

		# calculate the resolution:
		halfres = apRecon.calcRes(fscpath, self.boxsize, self.apix)
		apDisplay.printColor("FSC 0.5 Resolution of %.3f Angstroms"%(halfres), "cyan")

		# save to database
		resq=appiondata.ApResolutionData()
		resq['half'] = halfres
		resq['fscfile'] = fscfile

		return resq

	#==================
	def insertFSCData(self, iternum, refineIterData):
		fscfile = 'fsc.eotest.%d'%(iternum)
		fscpath = os.path.join(self.params['rundir'], "iter%03d"%(iternum), fscfile)

		if not os.path.isfile(fscpath):
			apDisplay.printWarning("Could not find FSC file: "+fscpath)
			return None

		f = open(fscpath, 'r')
		apDisplay.printMsg("inserting FSC Data into database")
		numinserts = 0
		for line in f:
			fscq = appiondata.ApFSCData()
			fscq['refineIter'] = refineIterData
			sline = line.strip()
			bits = sline.split('\t')
			fscq['pix'] = int(bits[0])
			fscq['value'] = float(bits[1])

			numinserts+=1
			if self.params['commit'] is True:
				fscq.insert()

		apDisplay.printMsg("inserted "+str(numinserts)+" rows of FSC data into database")
		f.close()

	#=====================
	def getRunData(self):
		### setup refinement run
		jobdata = apDatabase.getJobDataFromPathAndType(self.params['rundir'], "runfrealign")
		runq = appiondata.ApRefineRunData()
		runq['runname'] = self.params['runname']
		runq['package'] = "Frealign"
		runq['description'] = self.params['description']
		runq['hidden'] = False
		runq['num_iter'] = self.numiter
		runq['stack'] = apStack.getOnlyStackData(self.params['stackid'])
		runq['initialModel'] = apModel.getModelFromId(self.params['modelid'])
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		runq['job'] = jobdata
		return runq

	#=====================
	def setIterData(self, iterparams, volumeDensity):
		frealigniterq = appiondata.ApFrealignIterData()
		frealignkeys = ('wgh', 'xstd', 'pbc',
			'itmax', 'ipmax', 'target', 'thresh', 'cs',
			'rrec', 'highpass', 'lowpass', 'rbfact')
		for key in frealignkeys:
			frealigniterq[key] = iterparams[key]

		iternum = iterparams['iternum']

		iterq = appiondata.ApRefineIterData()
		iterq['iteration'] = iternum
		iterq['exemplar'] = False
		### mask values are in pixels
		iterq['mask'] = iterparams['mask']/self.apix
		iterq['imask'] = iterparams['imask']/self.apix
		iterq['volumeDensity'] = os.path.basename(volumeDensity)

		### Frealign does not produce class averages :(
		iterq['refineClassAverages'] = None
		iterq['postRefineClassAverages'] = None
		iterq['classVariance'] = None

		iterq['symmetry'] = iterparams['symmdata']
		iterq['refineRun'] = self.runq
		iterq['resolution'] = self.getResolutionData(iternum)
		iterq['rMeasure'] = self.getRMeasureData(volumeDensity)
		iterq['frealignParams'] = frealigniterq
		return iterq

	#==================
	def insertRefineParticleData(self, iterdata, parttree):
		apDisplay.printMsg("Inserting particle data")
		phase_threshold = float(iterdata['frealignParams']['thresh'])
		count = 0
		for partdict in parttree:
			count += 1
			if count % 1000 == 0:
				apDisplay.printMsg("Inserted %d particles"%(count))
			partrefineq = appiondata.ApRefineParticleData()

			partrefineq['refineIter'] = iterdata
			partnum = partdict['partnum']
			stackpartid = self.stackmapping[partnum]
			stackpartdata = appiondata.ApStackParticleData.direct_query(stackpartid)
			partrefineq['particle'] = stackpartdata

			partkeys = ('shiftx', 'shifty', 'euler1', 'euler2', 'euler3', 'phase_residual')
			for key in partkeys:
				partrefineq[key] = partdict[key]

			### check if particle was rejected
			if partdict['phase_residual'] > iterdata['frealignParams']['thresh']:
				partrefineq['refine_keep'] = False
			else:
				partrefineq['refine_keep'] = True

			partrefineq['mirror'] = False
			partrefineq['postRefine_keep'] = False
			partrefineq['euler_convention'] = 'zyz'

			if self.params['commit'] is True:
				partrefineq.insert()

		return

	#=====================
	def uploadIteration(self, iternum):
		if self.runq is None:
			### setup refinement run
			self.runq = self.getRunData()

		### read iteration info
		iterparams = self.readParamsFromCombineFile(iternum)

		### read particle info
		parttree = self.parseFrealignParamFile(iternum)

		### get volume info
		volumeMrcFile = self.processFrealignVolume(iternum, symname=iterparams['symmdata']['eman_name'])

		### get volume info
		iterdata = self.setIterData(iterparams, volumeMrcFile)

		### insert FSC data
		self.insertFSCData(iternum, iterdata)

		### insert particle data
		self.insertRefineParticleData(iterdata, parttree)

	#=====================
	def getNumberOfIterations(self):
		iternum = 0
		stop = False
		while stop is False:
			## check if iteration is complete
			iternum += 1

			paramfile = "params.iter%03d.par"%(iternum)
			if not os.path.isfile(paramfile):
				apDisplay.printWarning("Parameter file %s is missing"%(paramfile))
				stop = True
				break

			imagicvolume = "threed.%03da.hed"%(iternum)
			if not os.path.isfile(imagicvolume):
				apDisplay.printWarning("Volume file %s is missing"%(imagicvolume))
				stop = True
				break

			combineshell = "iter%03d/frealign.iter%03d.combine.sh"%(iternum, iternum)
			if not os.path.isfile(combineshell):
				apDisplay.printWarning("Shell file %s is missing"%(combineshell))
				stop = True
				break

		### set last working iteration
		numiter = iternum-1
		if numiter < 1:
			apDisplay.printError("No iterations were found")
		apDisplay.printColor("Found %d complete iterations"%(numiter), "green")

		return numiter

	#=====================
	def start(self):
		"""
		this is the main component of the script
		where all the processing is done
		"""
		### initialize some variables
		self.runq = None
		self.apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		apDisplay.printMsg("Pixel size: %.5f"%(self.apix))
		self.boxsize = apStack.getStackBoxsize(self.params['stackid'])
		apDisplay.printMsg("Box size: %d"%(self.boxsize))

		self.checkResults()
		self.stackmapping = apRecon.partnum2defid(self.params['stackid'])
		self.numiter = self.getNumberOfIterations()
		for i in range(self.numiter):
			iternum = i+1
			apDisplay.printColor("\nUploading iteration %d of %d\n"%(iternum, self.numiter), "green")
			self.uploadIteration(iternum)

		reconrunid = apRecon.getReconRunIdFromNamePath(self.params['runname'], self.params['rundir'])
		if reconrunid:
			apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
			eulerjump = apEulerJump.ApEulerJump()
			eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, self.params['stackid'])
			apRecon.setGoodBadParticlesFromReconId(reconrunid)
		else:
			apDisplay.printWarning("Could not find recon run id")

if __name__ == '__main__':
	upfrealign = UploadFrealign()
	upfrealign.start()
	upfrealign.close()
