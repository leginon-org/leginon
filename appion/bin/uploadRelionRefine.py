#!/usr/bin/env python

#python
import os
import re
import sys
import time
import math
import subprocess
import shutil
#appion
from appionlib import appionScript
from appionlib import apEMAN
from appionlib import apDisplay
from appionlib import apChimera
from appionlib import apEulerJump
from appionlib import apEulerCalc
from appionlib import apStack
from appionlib import apModel
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apSymmetry
from appionlib import apRecon
from appionlib import apFrealign
from appionlib import reconUploader
from appionlib import apFile

class UploadRelionScript(reconUploader.generalReconUploader):
	
	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "Relion"
		self.multiModelRefinementRun = False
		super(UploadRelionScript, self).__init__()
			
	#=====================
	def findLastCompletedIteration(self):
		#recondir = os.path.join(self.params['rundir'], "recon")
		recondir = self.params['rundir']
		iternum = 0
		stop = False
		while stop is False:
			## check if iteration is complete
			iternum += 1

			class1Volume = "recon_it%03d_half1_model.star"%(iternum)
			class2Volume = "recon_it%03d_half2_model.star"%(iternum)
			class1Volumepath = os.path.join(recondir,class1Volume)
			class2Volumepath = os.path.join(recondir,class2Volume)
			if not os.path.isfile(class1Volumepath) or not os.path.isfile(class2Volumepath):
				apDisplay.printWarning("Model.star file %s or %s is missing"%(class1Volumepath, class2Volumepath))
				stop = True
				break

		### set last working iteration
		numiter = iternum-1
		if numiter < 1:
			apDisplay.printError("No iterations were found")
		apDisplay.printColor("Found %d complete iterations"%(numiter), "green")

		return numiter	
	
	
	def parseParticleDataIterationFile(self,paramfile,test=False):
		'''
		parse data.star file from Relion 1.2:
	data_images
	
	loop_
	_rlnVoltage #1
	_rlnDefocusU #2
	_rlnDefocusV #3
	_rlnDefocusAngle #4
	_rlnSphericalAberration #5
	_rlnAmplitudeContrast #6
	_rlnImageName #7
	_rlnMicrographName #8
	_rlnGroupNumber #9
	_rlnAngleRot #10
	_rlnAngleTilt #11
	_rlnAnglePsi #12
	_rlnOriginX #13
	_rlnOriginY #14
	_rlnClassNumber #15
	_rlnNormCorrection #16
	_rlnMagnificationCorrection #17
	_rlnRandomSubset #18
	_rlnLogLikeliContribution #19
	_rlnMaxValueProbDistribution #20
	_rlnNrOfSignificantSamples #21
	  120.000000 15077.300000 14183.700000   -41.860000     2.000000     0.360000 1@/ami/data00/appion/zz07jul25b/recon/relion_recon63/start.mrcs          1            1    69.185200    65.769858  -107.659774     0.321202    -0.178798            1     1.000000     1.000000            1 48957.121482 8.954495e-05         1710
		
		'''
		if not os.path.isfile(paramfile):
			apDisplay.printError("Relion data.star file does not exist: %s" % (paramfile))
	
		f = open(paramfile, "r")
		partdict = {}
		inloop = False
		partnum = 1 ### partnum starts with 1, not 0
		apDisplay.printMsg("Processing particle data file: %s" % (paramfile))
		
		for line in f:
			line = line.strip()
			if line.startswith("loop_"):
				inloop = True
				continue
			elif inloop and line.startswith("_"):
				### comment line
				continue
			elif inloop and not line:
				inloop = False
				break # reached the end of this section of the file
			elif inloop and line:
				sline = line.split()
				paramdict = {
					'partnum' : partnum,   
					'volatage' : float(sline[0]),   
					'defocusU' : float(sline[1]),
					'defocusV' : float(sline[2]),
					'defocusAngle' : float(sline[3]),
					'sphericalAberration' : float(sline[4]),
					'amplitudeContrast' : float(sline[5]),
					'imageName' : sline[6],
					'micrographName' : int(sline[7]),
					'groupNumber' : int(sline[8]),
					'angleRot' : float(sline[9]),
					'angleTilt' : float(sline[10]),
					'anglePsi' : float(sline[11]),
					'originX' : float(sline[12]),
					'originY' : float(sline[13]),
					'classNumber' : int(sline[14]),
					'normCorrection' : float(sline[15]),
					'magnificationCorrection' : float(sline[16]),
					'randomSubset' : int(sline[17]),
					'logLikeliContribution' : float(sline[18]),
					'maxValueProbDistribution' : float(sline[19]),
					'nrOfSignificantSamples' : int(sline[20]),
				}
				partdict[paramdict['partnum']] = paramdict
				partnum = partnum + 1
	
			# test mode returns only two particles
			if test and len(parttree) == 2:
				break
		f.close()
	
		if len(partdict) < 2:
			apDislay.printError("No particles found in particle data file %s" % (paramfile))
	
		apDisplay.printMsg("Processed %d particles" % (len(partdict)))
		return partdict	
	
	#=====================
	def createParticleDataFile(self, iteration, package_database_object):
		''' puts all relevant particle information into a single text file that can be read by the uploader '''
		
		os.chdir(self.projmatchpath)
		
		### read particle info
		paramfile = os.path.join(self.projmatchpath, "recon_it%03d_data.star"%(iteration))
		parttree = self.parseParticleDataIterationFile(paramfile)

		### write data in appion format to input file for uploading to the database
		partdatafilepath = os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol001.txt" % (self.params['timestamp'], iteration))
		particledataf = open(partdatafilepath, "w")
		particledataf.write("### column info: ")
		particledataf.write("(1) particle number ")
		particledataf.write("(2) phi ")
		particledataf.write("(3) theta ")
		particledataf.write("(4) omega ")
		particledataf.write("(5) shiftx ")
		particledataf.write("(6) shifty ")
		particledataf.write("(7) mirror ")
		particledataf.write("(8) 3D reference # ")
		particledataf.write("(9) 2D class # ")
		particledataf.write("(10) quality factor ")
		particledataf.write("(11) kept particle ")
		particledataf.write("(12) postRefine kept particle \n")				

		### add each particle to the file
		count = 0
		for partnum, partdict in parttree.items():
			count += 1
			if count % 500 == 0:
				apDisplay.printMsg("Wrote %d particles to Particle Data File: %s"%(count,partdatafilepath))
			phi, theta, omega = apEulerCalc.convertFrealignEulersTo3DEM(float(partdict['angleRot']), float(partdict['angleTilt']), float(partdict['anglePsi']))
			particledataf.write("%.6d\t" % partnum) ### NOTE: IT IS IMPORTANT TO START WITH 1, OTHERWISE STACKMAPPING IS WRONG!!!
			particledataf.write("%.6f\t" % phi)
			particledataf.write("%.6f\t" % theta)
			particledataf.write("%.6f\t" % omega)
			particledataf.write("%.6f\t" % float(partdict['originX']))
			particledataf.write("%.6f\t" % float(partdict['originY']))
			particledataf.write("%.6d\t" % 0)
			particledataf.write("%.6d\t" % 1)
			particledataf.write("%.6d\t" % 0)
			particledataf.write("%.6d\t" % 1)
			# DOn't think this applies to Relion?
			#if partdict['phase_residual'] > package_database_object['thresh']:
				#particledataf.write("%.6f\t" % 1)
			#else:
				#particledataf.write("%.6f\t" % 1) #TODO: this should be false???
			particledataf.write("%.6f\t" % 1)
			particledataf.write("%.6f\n" % 1)
			
		### close the new file
		particledataf.close()
		
		os.chdir(self.params['rundir'])
				
		return
	
	#===============
	def convertBool(self, val):
		""" Convert single letter T or F to bool"""
		if val.lower().startswith('f') or val.strip() == '0':
			return False
		return True	

	#=====================
	def readParamsFromOptimiserFile(self, iternum):
		"""
		read the recon_it000_optimiser.star file to get iteration parameters,
		such as symmetry and phase residual cutoff
		"""
		iterparams = {'iternum': iternum,}
		#recondir = os.path.join(self.params['rundir'], "recon")
		recondir = self.params['rundir']

		optimiserfile = "recon_it%03d_optimiser.star"%(iternum)
		optimiserfilepath = os.path.join(recondir, optimiserfile)
		
		# Create a dictionary of parameters found in the optimiser file
		paramdict = {}
		
		### parse optimiser file to populate dictionary
		f = open(optimiserfilepath, "r")
		
		for line in f:
			if line.startswith("# RELION optimiser"):
				continue
			elif line.startswith("# --o"): # The command used to run Relion
				sline = line.strip()
				bits = sline.split("--")
				
				for bit in bits:
					params = bit.split()
					key = params[0]
					if len(params) > 1 :
						value = params[1]
						paramdict[key] = value
					else:
						paramdict[key] = True

			elif line.startswith("_"): # star format entry
				
				sline = line.strip()
				bits = sline.split()
				if len(bits) < 2 :
					continue
				key = bits[0]
				value = bits[1]
				paramdict[key] = value

			elif line.startswith("EOF"):
				break
			
		f.close()
				
		# TODO: There are more parameters to add here
		# fill on the iteration params that we care about
		iterparams['ctf']                     = self.convertBool(paramdict['_rlnDoCorrectCtf']) if paramdict['_rlnDoCorrectCtf'] else False
		iterparams['ctf_intact_first_peak']   = self.convertBool(paramdict['_rlnDoIgnoreCtfUntilFirstPeak']) if paramdict['_rlnDoIgnoreCtfUntilFirstPeak'] else False
		iterparams['ctf_corrected_ref']       = self.convertBool(paramdict['_rlnRefsAreCtfCorrected']) if paramdict['_rlnRefsAreCtfCorrected'] else False
		iterparams['offset_step']             = int(paramdict['offset_step'])
		iterparams['auto_local_healpix_order'] = int(paramdict['_rlnAutoLocalSearchesHealpixOrder'])
		iterparams['healpix_order']           = int(paramdict['healpix_order'])
		iterparams['offset_range']            = int(paramdict['offset_range'])
		iterparams['ini_high']                = int(paramdict['ini_high'])
		iterparams['sym']                     = paramdict['sym']

		### convert symetry to Appion
		symtext = apFrealign.convertFrealignSymToAppionSym(iterparams['sym'])
		symmdata = apSymmetry.findSymmetry(symtext)
		apDisplay.printMsg("Found symmetry %s with id %s"%(symmdata['eman_name'], symmdata.dbid))
		iterparams['symmdata'] = symmdata
		
		return iterparams
	
		#=====================
	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER: if the parameters were not pickled, parse protocols script to determine projection-matching params '''

		"""
		read the combine file to get iteration parameters,
		such as symmetry and phase residual cutoff
		"""
		iternum = 1
		iterparams = self.readParamsFromOptimiserFile(iternum)
		
		### set global parameters
		runparams = {}
		runparams['numiter'] = self.findLastCompletedIteration()
		runparams['mask'] = int(iterparams['mask'])
		runparams['imask'] = int(iterparams['imask'])
		runparams['symmetry'] = iterparams['symmdata']
		runparams['package_params'] = iterparams
		runparams['remoterundir'] = self.params['rundir']
		runparams['rundir'] = self.params['rundir']
		runparams['NumberOfReferences'] = 1 # assume 1 for now, until frealign does more.

		return runparams

	#=====================
	def instantiateProjMatchParamsData(self, iteration):
		''' fill in database entry for ApRelionIterData table '''

		### read iteration info
		iterparams = self.readParamsFromOptimiserFile(iteration)

		iterq = appiondata.ApRelionIterData()
		keys = ('ini_high','ctf', 'offset_step', 'auto_local_healpix_order', 'healpix_order',
			'offset_range', 'ctf_intact_first_peak', 'ctf_corrected_ref')
		for key in keys:
			iterq[key] = iterparams[key]

		return iterq
	
	#======================	
	def convertFSCFileForIteration(self, iteration):
		'''  RElion FSC info is in recon_it002_model.star and the final recon_model.star file, convert this to 3DEM format 
			 For the final iteration, we need to use recon_model.star rather than the iteration specific file to get the actual values.
		'''
	
		lastiter = self.findLastCompletedIteration() 
		if iteration == lastiter:
			fscfile = os.path.join(self.projmatchpath, "recon_model.star"%(iteration))
		else:
			fscfile = os.path.join(self.projmatchpath, "recon_it%.3d_half1_model.star"%(iteration))

		try: 
			f = open(fscfile, "r")
		except IOError, e:
			if iteration == lastiter:
				apDisplay.printWarning("%s file could not be opened, data will NOT be inserted into the database. Relion did NOT run to completion." % fscfile)
			else:
				apDisplay.printWarning("%s file could not be opened, data will NOT be inserted into the database" % fscfile)
			return False
		
		newfscfile = open(os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.fsc" % (self.params['timestamp'], iteration)), "w")
		newfscfile.write("### column (1) inverse Angstroms, column (2) Fourier Shell Correlation (FSC)")
		indatamodel = False
		
		for line in f:
			line = line.strip()
			if line.startswith("data_model_class_1"):
				indatamodel = True
				continue
			elif indatamodel and ( line.startswith("_") or line.startswith("loop_") ): 
				continue
			elif indatamodel and line.startswith("data_model_groups"):
				indatamodel = False
				break
			elif indatamodel and line:
				bits = line.split()
				resolution = float(bits[1]) # already in inverse angstrom
				fsc = float(bits[4]) # should go from a value of 1 to 0
				newfscfile.write("%.6f\t%.6f\n" % (resolution, fsc))

		newfscfile.close()
		f.close()
		
		return True
	
	#=====================
	# Use Dmitry's code to combine the 2 halfs of the data
	# This should give a better approximation of the volume 
	# at a given iteration prior to the final model provided by Relion
	def combineMRCs(self, half1vol, half2vol, finalvol):
		import numpy
		from pyami import mrc
		
		nvol = 1 # nvol is the number of output mrc files, e.g. 2-model, 3-model refinement, etc.
		box = self.runparams['boxsize']
		filelist = [half1vol, half2vol]
		
		appended = numpy.zeros(((box,box,box)))
		for file in filelist:
			f = mrc.read(file)
			appended += f
		appended = (appended / nvol)
		
		summed = mrc.write(appended, finalvol)

	
	#=====================
	def start(self):
		
		### Set FSC resolution criterion
		self.fscResCriterion = 0.145
		
		### database entry parameters
		package_table = 'ApRelionIterData|relionParams'
		
		### set projection-matching path
		#self.projmatchpath = os.path.abspath(os.path.join(self.params['rundir'], "recon"))
		self.projmatchpath = os.path.abspath(self.params['rundir'])
	
		### determine which iterations to upload
		lastiter = self.findLastCompletedIteration()
		uploadIterations = self.verifyUploadIterations(lastiter)	

		for iteration in uploadIterations:
		
			apDisplay.printColor("uploading iteration %d" % iteration, "cyan")
			
			package_database_object = self.instantiateProjMatchParamsData(iteration)
			
			### move FSC file to results directory
			self.FSCExists = self.convertFSCFileForIteration(iteration)
				
			### create a text file with particle information
			self.createParticleDataFile(iteration, package_database_object)
					
			# Use Dmitrys code to combine the 2 halves mrcs
			### create mrc file of map for iteration and reference number

			half1vol = os.path.join(self.projmatchpath, "recon_it%.3d_half1_class001.mrc" % iteration)
			half2vol = os.path.join(self.projmatchpath, "recon_it%.3d_half2_class001.mrc" % iteration)
			newvol   = os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.mrc" % (self.params['timestamp'], iteration))
			self.combineMRCs( half1vol, half2vol, newvol )
			if iteration == lastiter:
				oldvol = os.path.join(self.projmatchpath, "recon_class001.mrc")
				apFile.safeCopy(oldvol, newvol)
			
			### make chimera snapshot of volume
			self.createChimeraVolumeSnapshot(newvol, iteration)
			
			### instantiate database objects
			self.insertRefinementRunData(iteration)
			self.insertRefinementIterationData(iteration, package_table, package_database_object)

			###  make symlink only after successful insertion				
#			if os.path.isfile(newvol):
#				if os.path.isfile(oldvol):
#					apFile.removeFile(oldvol,True)
#				try:
#					os.symlink(newvol, oldvol)
#				except IOError, e:
#					print e

		### calculate Euler jumps
		self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)	
		
		### query the database for the completed refinements BEFORE deleting any files ... returns a dictionary of lists
		### e.g. {1: [5, 4, 3, 2, 1]} means 5 iters completed for refine 1
#		complete_refinements = self.verifyNumberOfCompletedRefinements(multiModelRefinementRun=False)
#		if self.params['cleanup_files'] is True:
#			self.cleanupFiles(complete_refinements)

#=====================
if __name__ == "__main__":
	upload3D = UploadRelionScript()
	upload3D.start()
	upload3D.close()
	
		
