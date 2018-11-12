#!/usr/bin/env python
"""
general script for uploading a reconstruction that was run on either a local or external cluster. The reconstruction
procedure can either be run using one of the packages wrapped by Appion, or an external package. If the latter, then 
all parameters must be in the appropriate format for the upload procedure. 
"""

#python
import os, re, cPickle, glob, shutil

#appion
from appionlib import appiondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apEulerDraw
from appionlib import apEulerJump
from appionlib import apEulerCalc
from appionlib import apParam
from appionlib import apRecon
from appionlib import apStack
from appionlib import apSymmetry
from appionlib import apXmipp
from appionlib import apChimera
from appionlib import apProject
from appionlib import apFile

#=====================
#=====================
class generalReconUploader(appionScript.AppionScript):
		
	#=====================
	def setupParserOptions(self):
		
		self.parser.set_usage("Usage: %prog --runname=<name> --stackid=<int> --modelid=<int>\n\t "
			+"--description='<quoted text>'\n\t [ --package=EMAN --refinejobid=<int> --oneiter=<iter> --startiter=<iter> --zoom=<float> "
			+"--contour=<contour> --rundir=/path/ --commit ]")
		
		### if job did not finish or if you only want to upload certain iterations, specify here
		self.parser.add_option("--uploadIterations", dest="uploadIterations", 
			help="upload specified iteration(s), comma delimited. e.g. --uploadIterations=1 or --uploadIterations=1,2,3", metavar="list")
			
		### standard refinement parameters: these are optional and should only be specified in the absence of a pickle file
		self.parser.set_defaults(nproc=1)
		self.parser.add_option("--refinejobid", dest="jobid", type="int",
			help="jobid of refinement", metavar="INT")
		self.parser.add_option("--timestamp", dest="timestamp", type="str",
			help="timestampe associated with refinement, e.g. --timestamp=08nov25c07", metavar="INT")
		# This is the stack id of the original stack (not the temporary refine stack created during the prep step)
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--modelid", dest="modelid", type="str", 	
			help="input model(s) for multi-model refinement. You can start with one model or as many as you like. Just provide the \
				database IDs, like so: '--modelid=1' or '--modelid=1,3,17', etc.", metavar="ID#(s)")
		self.parser.add_option("--numberOfReferences", dest="NumberOfReferences", type="int",
			help="number of references produced during refinement", metavar="INT")
		self.parser.add_option("--numiter", dest="numiter", type="int",
			help="number of iterations performed during refinement", metavar="INT")
		# This is the apix of the prepared refine stack, which may be different from the original stack.
		self.parser.add_option("--apix", dest="apix", type="float",
			help="pixelsize of the particles / map during refinement", metavar="FLOAT")		
		# This is the boxsize of the prepared refine stack, which may be different from the original stack.
		self.parser.add_option("--boxsize", dest="boxsize", type="int",
			help="boxsize of the particles / map during refinement", metavar="INT")
		self.parser.add_option("--symid", dest="symid", type="int",
			help="symmetry database id, enter 25 for C1", metavar="ID#")
			
		self.parser.add_option("--euleronly", dest="euleronly", default=False,
			action="store_true", help="Commit refined euler angles without reconstruction")
		### chimera snapshots	
		self.parser.add_option("--snapfilter", dest="snapfilter", type="float",
			help="Low pass filter in angstroms for snapshot rendering (FSC_0.5 by default)", metavar="FLOAT")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.75,
			help="Zoom factor for snapshot rendering (1.75 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("--mass", dest="mass", type="int",
			help="Mass (in kDa) at which snapshot of density will be contoured", metavar="kDa")
			
		### cleanup files
		self.parser.add_option("--cleanup_files", dest="cleanup_files", default=False, action="store_true",
			help="cleanup all files associated with the external refinement package")
						
	#=====================
	def checkConflicts(self):
		### unpickle results or parse logfile, set default parameters if missing
		os.chdir(os.path.abspath(self.params['rundir']))
		if os.path.isdir(os.path.join(self.params['rundir'], "recon")):
			apDisplay.printWarning('recon dir already exist, no need to unpack')
		else:
			self.unpackResults()
	
		''' These are required error checks, everything else should be possible to obtain from the timestamped pickle file '''

		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		self.runparams = {}
		self.runparams['original_apix'] = ( stackdata['pixelsize'] / 1e-10 ) # convert pixelsize to angstroms per pixel.
		self.runparams['original_boxsize'] = stackdata['boxsize']
		# some functions in readRunParameters needs the above params
		self.runparams.update(self.readRunParameters())

		### parameters recovered from runparameter file(s)
		if not self.runparams.has_key('stackid'):
			if self.params['stackid'] is not None:
				self.runparams['stackid'] = self.params['stackid']
			else:
				apDisplay.printError("stack id must be specified for proper database insertion")
		if not self.runparams.has_key('modelid'):
			if self.params['modelid'] is not None:
				self.runparams['modelid'] = self.params['modelid']
			else:
				apDisplay.printError("model id must be specified for proper database insertion")
		if not self.runparams.has_key('NumberOfReferences'):
			if self.params['NumberOfReferences'] is not None:
				self.runparams['NumberOfReferences'] = self.params['NumberOfReferences']
			else:
				apDisplay.printError("number of references produced during the refinement needs to be specified")
		if not self.runparams.has_key('numiter'):
			if self.params['numiter'] is not None:
				self.runparams['numiter'] = self.params['numiter']
			else:
				apDisplay.printError("number of iterations run during the refinement needs to be specified")	
		if not self.runparams.has_key('boxsize'):
			if self.params['boxsize'] is not None:
				self.runparams['boxsize'] = self.params['boxsize']
			else:
				apDisplay.printError("boxsize of the map / particles submitted for refinement needs to be specified")
		if not self.runparams.has_key('apix'):
			if self.params['apix'] is not None:
				self.runparams['apix'] = self.params['apix']
			else:
				apDisplay.printError("pixelsize of the map / particles submitted for refinement needs to be specified")
		if not self.runparams.has_key('symmetry'):
			if self.params['symid'] is not None:
				self.runparams['symmetry'] = apSymmetry.getSymmetryDataFromID(self.params['symid'])
			else:
				apDisplay.printError("symmetry ID must be specified, you can input --symid=25 for an asymmetric reconstruction")
		# access multiModelRefinementRun this way in case it is not present
		if 'multiModelRefinementRun' in vars(self):
			if not self.runparams.has_key('NumberOfReferences') and self.multiModelRefinementRun is True:
				if self.params['NumberOfReferences'] is not None:
					self.runparams['NumberOfReferences'] = self.params['NumberOfReferences']
				else:
					apDisplay.printError("number of output models in refinement needs to be specified for multi-model run")		
		else:
			if self.params['NumberOfReferences'] is not None:
				self.runparams['NumberOfReferences'] = self.params['NumberOfReferences']
				if self.runparams['NumberOfReferences'] > 1:
					self.multiModelRefinementRun = True
				else:
					self.multiModelRefinementRun = False
			else:
				apDisplay.printError("number of output models (references) in refinement needs to be specified for multi-model run")			
		if not self.runparams.has_key('rundir'):
			self.runparams['rundir'] = self.params['rundir']
		if not self.runparams.has_key('reconstruction_working_dir'):
			self.runparams['reconstruction_working_dir'] = str(self.package)+"_results"
		if not self.runparams.has_key('mask'):
			self.runparams['mask'] = None
		if not self.runparams.has_key('imask'):
			self.runparams['imask'] = None	
		if not self.runparams.has_key('alignmentInnerRadius'):
			self.runparams['alignmentInnerRadius'] = None
		if not self.runparams.has_key('alignmentOuterRadius'):
			self.runparams['alignmentOuterRadius'] = None	
		if not self.runparams.has_key('angularSamplingRate'):
			self.runparams['angularSamplingRate'] = None
							
		### parameters specified for upload
		if self.params['jobid'] is not None:
			self.params['jobinfo'] = appiondata.ApAppionJobData.direct_query(self.params['jobid'])
		else:
			jobid = self.tryToGetJobID()
			if jobid is not False:
				self.params['jobinfo'] = appiondata.ApAppionJobData.direct_query(self.params['jobid'])
			else:
				self.params['jobinfo'] = None
		if self.params['timestamp'] is None and self.package == "external_package":
			apDisplay.printError("a timestamp (or some identifier) must be specified with the files. For example, the 3D mrc file " \
				"for iteration 1 should be named 'recon_YourIdentifier_it001_vol001.mrc, in which case the timestamp should be specified " \
				"as --timestamp=YourIdentifier")			
		elif self.params['timestamp'] is None and self.params['jobid'] is None and self.package != "external_package":
			self.params['timestamp'] = apParam.makeTimestamp()
		elif self.params['timestamp'] is None and self.params['jobid'] is not None:
			timestamp = self.getTimestamp()
			if timestamp is None:
				self.params['timestamp'] = apParam.makeTimestamp()
#				apDisplay.printError("please specify the timestamp associated with the refinement parameters, e.g. --timestamp=08nov25c07")
			
		### basic refinement variables
		self.initializeRefinementUploadVariables()

		return
	
	#=====================
	def unpackResults(self):
		''' untar results, if this hasn't been done yet '''
		if os.path.exists(os.path.join(self.params['rundir'], "recon_results.tar.gz")):
			apParam.runCmd("tar -xvzf recon_results.tar.gz", "SHELL")
			apParam.runCmd("rm recon_results.tar.gz", "SHELL")
		if os.path.exists(os.path.join(self.params['rundir'], "volumes.tar.gz")):
			apParam.runCmd("tar -xvzf volumes.tar.gz", "SHELL")
			apParam.runCmd("rm volumes.tar.gz", "SHELL")
		

	#=====================
	def tryToGetJobID(self):
		jobname = self.params['runname'] + '.job'
		jobtype = 'recon'
		jobpath = self.params['rundir']
		qpath = appiondata.ApPathData(path=os.path.abspath(jobpath))
		q = appiondata.ApAppionJobData(name=jobname, jobtype=jobtype, path=qpath)
		results = q.query()
		if len(results) == 1:
			### success, only one job id found
			return results[0].dbid
		elif len(results) > 1:
			### fail because too many job ids
			jobids = [result.dbid for result in results]
			apDisplay.printWarning("Several job IDs found for this run %s: You should manually specify a jobid, if it exists" % jobids)
			return False
		else:
			### no job found
			apDisplay.printWarning("No job IDs found for this run, you should manually specify a jobid, if it exists")
			return False
				
	#=====================	
	def initializeRefinementUploadVariables(self):
		''' untars results, reads required parameters, establishes necessary objects for upload script '''
		
		apDisplay.printColor("uploading refinement results for %s reconstruction routine" % (self.package), "cyan")
		
		### establish directories and make an appion results directory
		self.basepath = os.path.abspath(self.params['rundir'])
		self.resultspath = os.path.abspath(os.path.join(self.params['rundir'], str(self.package)+"_results"))
		if not os.path.isdir(self.resultspath):
			os.mkdir(self.resultspath)		
		self.reconpath = os.path.abspath(os.path.join(self.params['rundir'], self.runparams['reconstruction_working_dir']))
						
		### get all stack parameters, map particles in reconstruction to particles in stack, get all model data
		self.stackdata = apStack.getOnlyStackData(self.runparams['stackid'])
		self.stackmapping = apRecon.partnum2defid(self.runparams['stackid'])
		self.modeldata = []
		if len(self.runparams['modelid'].split(",")) > 1:
			models = self.runparams['modelid'].split(",")
			for i in range(len(models)): 
				self.modeldata.append(appiondata.ApInitialModelData.direct_query(int(models[i])))
		else:
			self.modeldata.append(appiondata.ApInitialModelData.direct_query(self.runparams['modelid']))
			
		### Set the default FSC Resolution criterion
		self.fscResCriterion = 0.5
			
		return

	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER. This should be defined in subclasses if the parameters were not pickled.  Return parameters in dictionary form'''
		raise NotImplementedError('parseFileForRunParameters is not defined')
		
	#=====================
	def readRunParameters(self):
		''' read pickled run parameters for refinement procedure '''
		if self.params['timestamp'] is not None:
			paramfile = glob.glob("*"+self.params['timestamp']+"-params.pickle")
		else:
			paramfile = glob.glob("*-params.pickle")
		if self.package == "external_package":
			return {}
		else:
			if len(paramfile) == 0 or not os.path.isfile(paramfile[0]):
				apDisplay.printWarning("Could not find run parameters pickle file ... trying to get values from logfile")
				try:
					runparams = self.parseFileForRunParameters()
				except Exception, e:
					apDisplay.printError("Could not determine run parameters for refinement: %s ...you may try uploading as an external package." % e)
			else:
				f = open(paramfile[0], "r")
				runparams = cPickle.load(f)
				f.close()
		
			return runparams

	#=====================
	def getTimestamp(self):
		''' find timestamp associated with job, e.g. 08nov02b35'''
		
		jobdata = appiondata.ApRefineRunData.direct_query(self.params["jobid"])
		try:
			timestamp = jobdata['timestamp']
		except:
			apDisplay.printWarning("timestamp could not be found from the jobdata")
			return None
		apDisplay.printMsg("Found timestamp = '"+timestamp+"'")
		return timestamp
					
	#=====================
	def readParticleFile(self, iteration, reference_number=1):
		''' reads all parameters associated with the refinement for each particle, returns a nested list '''
		
		pdataf = os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol%.3d.txt" % (self.params['timestamp'], iteration, reference_number))
		if not os.path.isfile(pdataf):
			apDisplay.printError("no particle text file found; this is a requirement for the upload to insert " \
				"Euler angles, shifts, etc. Make sure that you have a particle_data_%s_it%.3d_vol%.3d.txt file with" \
				"all parameters" % (self.params['timestamp'], iteration, reference_number))
		porderf = os.path.join(self.basepath,'stackpartorder.list')
		return readParticleFileByFilePath(pdataf,porderf)
		
	
	#=====================
	def verifyUploadIterations(self, lastiter=float("inf")):
		''' verify number of completed / specified iterations '''
		if self.params['uploadIterations'] is not None:
			uploadIterations = self.params['uploadIterations'].split(",")
			uploadIterations = [int(iter) for iter in uploadIterations]
			uploadIterations.sort()
			if lastiter < uploadIterations[-1]:
				apDisplay.printError("iteration %d has not been completed by %s. Please specify the exact iterations " \
					"that you would like to upload, e.g. --uploadIterations=1,2,3,4,5,6,7,8" % (uploadIterations[-1], self.package))
		else:
			if self.runparams['numiter'] != lastiter and lastiter != float("inf"):
				apDisplay.printError("%s job did not go to completion. The last completed iteration is %d, out of " \
					"%d specified. Please specify the exact iterations that you would like to upload like so: " \
					"--uploadIterations=1,2,3,4,5,6,7,8" % (self.package, lastiter, self.runparams['numiter']))
			uploadIterations = [i for i in range(1,self.runparams['numiter']+1)]	
			
		return uploadIterations
		
	#=====================
	def insertRefinementRunData(self, iteration, reference_number=1):
		''' fills in database entry object for ApRefineRunData table '''
		
		### fill in ApMultiModelRefineRunData object, if valid
		if self.multiModelRefinementRun is True:
			multimodelq = appiondata.ApMultiModelRefineRunData()
			multimodelq['runname'] = self.params['runname']
			multimodelq['REF|projectdata|projects|project'] = apProject.getProjectIdFromStackId(self.runparams['stackid'])
			multimodelq['session'] = apStack.getSessionDataFromStackId(self.runparams['stackid'])
			multimodelq['num_refinements'] = self.runparams['NumberOfReferences']
			self.multimodelq = multimodelq
		
		### fill in ApRefineRunData object
		runq = appiondata.ApRefineRunData()
		runq['runname'] = self.params['runname']
		runq['stack'] = self.stackdata
		runq['reference_number'] = reference_number
		earlyresult=runq.query(results=1) # check unique run
		if earlyresult:
			apDisplay.printWarning("Run already exists in the database.\nIdentical data will not be reinserted")
		paramdescription = self.params['description']
		if not paramdescription:
			paramdescription=None
		runq['job'] = self.params['jobinfo']
		if len(self.modeldata) > 1:
			runq['initialModel'] = self.modeldata[reference_number-1]
		else:
			runq['initialModel'] = self.modeldata[0]
		runq['package'] = self.package
		runq['path'] = appiondata.ApPathData(path=os.path.abspath(self.resultspath))
		runq['description'] = paramdescription
		runq['num_iter'] = self.runparams['numiter']
		if self.multiModelRefinementRun is True:
			runq['multiModelRefineRun'] = self.multimodelq
		
		result = runq.query(results=1)

		# save run entry in the parameters
		if result:
			self.refinerunq = result[0]
		elif self.params['commit'] is True:
			apDisplay.printMsg("Refinement Run was not found, setting to inserted values")
			self.refinerunq = runq
		else:
			apDisplay.printWarning("Refinement Run was not found, setting to 'None'")
			self.refinerunq = None
		
		return 
		
	#=====================
	def insertRefinementIterationData(self, iteration, package_table=None, package_database_object=None, reference_number=1):
		''' fills in database entry for ApRefineIterData table '''

		if not self.params['euleronly']:				
			### get resolution
			try:
				fscfile = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.fsc" \
					% (self.params['timestamp'], iteration, reference_number))
				fscRes = apRecon.getResolutionFromGenericFSCFile(fscfile, self.runparams['boxsize'], self.runparams['apix'],filtradius=3, criterion=self.fscResCriterion)
				apDisplay.printColor("FSC " + str(self.fscResCriterion) + " Resolution: "+str(fscRes), "cyan")
				resq = appiondata.ApResolutionData()
				resq['half'] = fscRes
				resq['fscfile'] = os.path.basename(fscfile)
			except Exception, e:
				apDisplay.printWarning("An error occured while reading fsc data: ")
				print e
				apDisplay.printWarning("The following FSC file does not exist or is unreadable: %s " % (fscfile))
				resq = None
		else:
			resq = None
			
		### fill in ApRefineIterData object
		iterationParamsq = appiondata.ApRefineIterData()
		if package_table is not None and package_database_object is not None:
			iterationParamsq[str(package_table.split("|")[1])] = package_database_object
		iterationParamsq['refineRun'] = self.refinerunq
		iterationParamsq['iteration'] = iteration
		iterationParamsq['resolution'] = resq
		if not self.params['euleronly']:				
			iterationParamsq['rMeasure'] = self.getRMeasureData(iteration, reference_number)
		else:
			iterationParamsq['rMeasure'] = None
		iterationParamsq['mask'] = apRecon.getComponentFromVector(self.runparams['mask'], iteration-1)
		iterationParamsq['imask'] = apRecon.getComponentFromVector(self.runparams['imask'], iteration-1)
		iterationParamsq['alignmentInnerRadius'] = apRecon.getComponentFromVector(self.runparams['alignmentInnerRadius'], iteration-1)
		iterationParamsq['alignmentOuterRadius'] = apRecon.getComponentFromVector(self.runparams['alignmentOuterRadius'], iteration-1)
		try:
			iterationParamsq['symmetry'] = self.runparams['symmetry']
		except Exception, e:
			symmetry = self.runparams['symmetry'].split()[0]
			iterationParamsq['symmetry'] = apSymmetry.findSymmetry( symmetry )
		iterationParamsq['exemplar'] = False
		iterationParamsq['volumeDensity'] = "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, reference_number)
		projections_and_avgs = "proj-avgs_%s_it%.3d_vol%.3d.img" \
			% (self.params['timestamp'], iteration, reference_number)
		if os.path.exists(os.path.join(self.resultspath, projections_and_avgs)):
			iterationParamsq['refineClassAverages'] = projections_and_avgs
		refined_projections_and_avgs = "refined_proj-avgs_%s_it%.3d_vol%.3d.img" \
			% (self.params['timestamp'], iteration, reference_number)
		if os.path.exists(os.path.join(self.resultspath, refined_projections_and_avgs)):
			iterationParamsq['postRefineClassAverages'] = refined_projections_and_avgs
		varianceAvgs = "variance_avgs_%s_it%.3d_vol%.3d.img" \
			% (self.params['timestamp'], iteration, reference_number)
		if os.path.exists(os.path.join(self.resultspath, varianceAvgs)):
			iterationParamsq['classVariance'] = varianceAvgs

		if not self.params['euleronly']:
			### insert FSC data into database
			try:
				self.insertFSCData(fscfile, iterationParamsq)
			except Exception, e:
				print e
				apDisplay.printWarning("FSC file does not exist or is unreadable")			
		
		### fill in ApRefineReferenceData object
		referenceParamsq = appiondata.ApRefineReferenceData()
#		referenceParamsq['volumeDensityStart'] = "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration-1, reference_number)
		referenceParamsq['volumeDensityEnd'] = "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, reference_number)
		referenceParamsq['reference_number'] = reference_number
		referenceParamsq['path'] = appiondata.ApPathData(path=os.path.abspath(self.resultspath))
		referenceParamsq['iteration'] = iterationParamsq
		
		### insert refinement iteration information into database
		if self.params['commit'] is True:
			apDisplay.printMsg("inserting Refinement Data into database")
			referenceParamsq.insert()
		else:
			apDisplay.printWarning("not committing results to database")
				
		### get all particle data for this iteration
		particledata = self.readParticleFile(iteration, reference_number)

		self.insertRefinementParticleData(particledata, iterationParamsq, referenceParamsq)

		### create euler freq map
		if self.params['commit'] is True:
			apDisplay.printMsg("creating euler frequency map")
			if self.package != 'EMAN':
					postrefine = True
			else:
					postrefine = False
			apEulerDraw.createEulerImages(self.refinerunq.dbid, iteration, path=self.params['rundir'], postrefine=postrefine)
			for f in glob.glob("euler**png"):
				shutil.move(f, os.path.join(self.resultspath, f))
		
		return
		
	#==================		
	def insertRefinementParticleData(self, particledata, iterationParamsq, referenceParamsq, euler_convention='zxz'):	
		''' inserts all particle data into database, based on parameters from text file '''
		
		apDisplay.printMsg("inserting particle data into database ... this may take some time")
		
		for i in range(len(particledata)):
			prtlq = appiondata.ApRefineParticleData()
			
			### map particle to stack
#			prtlnum = particledata[i]['partnum']+1 ### offset by 1
			prtlnum = particledata[i]['partnum']
			defid = self.stackmapping[prtlnum]
			stackp = appiondata.ApStackParticleData.direct_query(defid)
			if not stackp:
				apDisplay.printError("particle "+str(prtlnum)+" not in stack id="+str(self.runparams['stackid']))

			### convert icos convention to standard convention
			full_sym_name = iterationParamsq['symmetry']['symmetry']
			if 'Icos' in full_sym_name:
				# Icos particle data from particle file is always in 235
				full_sym_name = 'Icos (2 3 5) Viper/3DEM'
			phi,theta,omega = apEulerCalc.convert3DEMEulerToStandardSym(full_sym_name,particledata[i]['phi'], particledata[i]['theta'], particledata[i]['omega'])
						
			### convert Euler angles from 3DEM to EMAN format (temporary fix)
			alt, az, phi = apXmipp.convertXmippEulersToEman(phi, theta, omega)

			if self.multiModelRefinementRun is True:
				prtlq['multiModelRefineRun'] = self.multimodelq
			prtlq['refineIter'] = iterationParamsq
			prtlq['reference_number'] = referenceParamsq
			prtlq['particle'] = stackp
			prtlq['euler1'] = float(alt)
			prtlq['euler2'] = float(az)
			prtlq['euler3'] = float(phi)
			prtlq['shiftx'] = particledata[i]['shiftx']
			prtlq['shifty'] = particledata[i]['shifty']
			prtlq['mirror'] = 0
#			prtlq['mirror'] = particledata[i]['mirror']
			try:
				prtlq['3Dref_num'] = particledata[i]['refnum']
			except:
				pass
			try:
				prtlq['2Dclass_num'] = particledata[i]['clsnum']
			except:
				pass
			try:
				prtlq['quality_factor'] = particledata[i]['quality']
			except:
				pass
			try:
				prtlq['refine_keep'] = particledata[i]['refine_keep']
			except:
				pass
			try:
				prtlq['postRefine_keep'] = particledata[i]['postRefine_keep']				
			except:
				pass
			prtlq['euler_convention'] = euler_convention
						
			if self.params['commit'] is True:
				prtlq.insert()

		return
		
	#==================
	def insertFSCData(self, fscfile, refineIterData):
		''' 
		current functions read the inverse pixel number and correlation value. This function, therefore, converts
		generic FSC parameters into pixel / correlation format
		'''
		
		if not os.path.isfile(fscfile):
			apDisplay.printWarning("Could not open FSC file: "+fscfile)

		### skip commented out lines and read FSC data
		f = open(fscfile, 'r')
		fscfileinfo = f.readlines()
		f.close()
		for i, info in enumerate(fscfileinfo):
			if info[0] == "#":
				pass
			else:
				fscfileinfo = fscfileinfo[i:]
				break
		
		### insert FSC data into database with the convention: pixel number, FSC
		numinserts = 0
		for j, info in enumerate(fscfileinfo):
			fscq = appiondata.ApFSCData()	
			fscq['refineIter'] = refineIterData	
			fscq['pix'] = j+1
			fscq['value'] = float(info.split()[1])
			numinserts+=1
			if self.params['commit'] is True:
				fscq.insert()
		if self.params['commit'] is True:
			apDisplay.printMsg("inserted "+str(numinserts)+" rows of FSC data into database")
		
		return 
				
	#=====================
	def getRMeasureData(self, iteration, reference_number=1):
		''' run rMeasure resolution and return database object '''
	
		volumeDensity = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.mrc" \
			% (self.params['timestamp'], iteration, reference_number))
		if not os.path.exists(volumeDensity):
			apDisplay.printWarning("R Measure failed, volume density not found: "+volumeDensity)
			return None

		resolution = apRecon.runRMeasure(self.runparams['apix'], volumeDensity)
		if resolution is None:
			return None

		### database object
		rmesq = appiondata.ApRMeasureData()
		rmesq['volume'] = "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, reference_number)
		rmesq['rMeasure'] = resolution

		return rmesq	
		
	#=====================
	def createChimeraVolumeSnapshot(self, volume, iteration, reference_number=1):
		''' create chimera snapshot images of volume '''
		
		if self.params['snapfilter']:
			resolution = self.params['snapfilter']
		else:
			newfscfile = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.fsc" \
				% (self.params['timestamp'], iteration, reference_number))
			try:
				resolution = apRecon.getResolutionFromGenericFSCFile(newfscfile, self.runparams['boxsize'], self.runparams['apix'],filtradius=3, criterion=self.fscResCriterion)
			except:
				apDisplay.printWarning("Failed to get resolution from generic FSC file: "+newfscfile)
				resolution = 30
		apDisplay.printWarning("Running Chimera Snapshot with resolution: %d " % resolution)
		
		# TODO: need to work this out. 
        # symmetry was hard coded to 'c1'. why?
		try:
			symmetry = self.runparams['symmetry']
		except Exception, e:
			symmetry = self.runparams['symmetry'].split()[0]
			symmetry = apSymmetry.findSymmetry( symmetry )
            
		apChimera.filterAndChimera(volume, resolution, self.runparams['apix'], 
			self.runparams['boxsize'], 'snapshot', self.params['contour'], self.params['zoom'],
			sym=symmetry, mass=self.params['mass'])	
			
	#=====================
	def calculateEulerJumpsAndGoodBadParticles(self, uploadIterations):
		''' calculate euler jumps for entire recon, currently based on EMAN ZXZ convention '''
		
		if self.params['commit'] is True:
			reconrunid = self.refinerunq.dbid
					
			### make table entries of good-bad particles
			apRecon.setGoodBadParticlesFromReconId(reconrunid)

			### verify completed refinements and iterations
			refinecomplete = self.verifyNumberOfCompletedRefinements(multiModelRefinementRun=self.multiModelRefinementRun)
			
			if self.multiModelRefinementRun is True: 
				### Euler jumpers calculated from ApMultiModelRefineRunData in multi-model case, looping over values in all single-model refinements			
				multimodelrunid = self.multimodelq.dbid
				if len(uploadIterations) > 1:
					apDisplay.printMsg("calculating euler jumpers for multi-model refinement="+str(multimodelrunid))
					eulerjump = apEulerJump.ApEulerJump()
					### TECHNICALLY, IT DOESN'T MAKE SENSE TO PASS THE RECONRUNID, SINCE PARTICLES CAN BE JUMPING,
					### BUT AS FAR AS I CAN TELL, IT DOESN'T MAKE A DIFFERENCE IN THE RESULTING QUERY, SINCE THE VARIABLE
					### IS ONLY USED TO QUERY FOR STACK PARTICLES, WHICH ARE IDENTICAL IN MULTI-MODEL AND SINGLE-MODEL REFINEMENT
					### CASES. THEREFORE, THE LAST RECONRUNID IS PASSES ... * DMITRY
					eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, self.runparams['stackid'], multimodelrunid=multimodelrunid)
			else:
				### Euler jumpers calculated from ApRefineRunData in single-model case
				if len(uploadIterations) > 1 or \
				(refinecomplete.itervalues().next()[-1] == self.runparams['numiter'] and len(refinecomplete.itervalues().next())>1): 
					apDisplay.printMsg("calculating euler jumpers for recon="+str(reconrunid))
					eulerjump = apEulerJump.ApEulerJump()
					eulerjump.calculateEulerJumpsForEntireRecon(reconrunid, self.runparams['stackid'])
		
		return
		
	#=====================
	def verifyNumberOfCompletedRefinements(self, multiModelRefinementRun=False):
		""" 
		queries te database to determine how many iterations of individual refinements have been completed:
		returns a list of completed iterations in a dictionary of completed refinements
		"""

		refine_complete = {}	
		if multiModelRefinementRun is False:
			iterdata = appiondata.ApRefineIterData()
			iterdata['refineRun'] = self.refinerunq
			itercompletedata = iterdata.query()
			iter_complete = []
			for iter in itercompletedata:
				iter_complete.append(iter['iteration'])
			iter_complete.sort()
			refine_complete[self.refinerunq['reference_number']] = iter_complete
		else:
			refinedata = appiondata.ApRefineRunData()
			refinedata['multiModelRefineRun'] = self.multimodelq
			refinecompletedata = refinedata.query()
			for i, refine in enumerate(refinecompletedata):
				iterdata = appiondata.ApRefineIterData()
				iterdata['refineRun'] = refine
				itercompletedata = iterdata.query()
				iter_complete = []
				for iter in itercompletedata:
					iter_complete.append(iter['iteration'])
				iter_complete.sort()
				refine_complete[refine['reference_number']] = iter_complete
		return refine_complete
		
	
# general function that does not need database connection
def readParticleFileByFilePath(pdatafile,porderfile=''):
	# read particle file
	f = open(pdatafile,'r')
	finfo = f.readlines()
	f.close()
	for i, info in enumerate(finfo):
		if info[0] == "#":
			pass
		else:
			finfo = finfo[i:]
			break
	apDisplay.printMsg("reading particle parameters in file: %s" % os.path.basename(pdatafile))
	
	# use saved particle order file particle number if availabe
	if porderfile and os.path.isfile(porderfile):
		orderf = open(porderfile,'r')
		lines = orderf.readlines()
		orderlist = map(lambda x:int(x[:-1]),lines)
	else:
		orderlist = range(1,len(finfo)+1)
	# construct data
	particledata = {}			
	for j, info in enumerate(finfo):
		alldata = {}			
		data = info.strip().split()
		# Information lines in ParticleFile is not necessarily sorted by particle number in the prepared stack.
		# EMAN result is ordered by class number, for example
		alldata['partnum'] = orderlist[int(data[0])-1]
		alldata['phi'] = float(data[1])
		alldata['theta'] = float(data[2])
		alldata['omega'] = float(data[3])
		alldata['shiftx'] = float(data[4])
		alldata['shifty'] = float(data[5])
		try:
			alldata['refnum'] = float(data[6])
		except:
			pass
		try:
			alldata['clsnum'] = float(data[7])
		except:
			pass
		try:
			alldata['quality'] = float(data[8])
		except:
			pass
		try:
			alldata['refine_keep'] = bool(float(data[9]))
		except:
			pass
		try:
			alldata['postRefine_keep'] = bool(float(data[10]))
		except: 
			pass
#		alldata['mirror'] = bool(float(data[6]))
#		alldata['refnum'] = float(data[7])
#		alldata['clsnum'] = float(data[8])
#		alldata['quality'] = float(data[9])
#		alldata['refine_keep'] = bool(float(data[10]))
#		alldata['postRefine_keep'] = bool(float(data[11]))
		particledata[j] = alldata
	return particledata


	def onClose(self):
		# do some clean up
			tasksender_jobs = glob.glob(os.path.join(self.params['rundir'],'tasksender*'))
			for filename in tasksender_jobs:
				apFile.removeFile(filename)
			
