#!/usr/bin/env python

#python
import glob, os, re, shutil, sys

#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apRecon
from appionlib import apParam
from appionlib import appiondata
from appionlib import apXmipp
from appionlib import apSymmetry
from appionlib import apImagicFile
from appionlib import reconUploader
from pyami import spider


#======================
#======================
class uploadXmippProjectionMatchingRefinementScript(reconUploader.generalReconUploader):

	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "Xmipp"
		self.multiModelRefinementRun = False
		super(uploadXmippProjectionMatchingRefinementScript, self).__init__()

	#=====================
	def findLastCompletedIteration(self):
		''' find the last iteration that finished the job '''

		if not self.params['euleronly']:
			filepattern = "Iter**reconstruction.vol"
		else:
			# If only refinement is run, there is no reconstruction volume, only euler angles
			filepattern = "Iter*current_angles.doc"

		lastiter = 0
		if os.path.isdir(self.projmatchpath) is False:
			apDisplay.printError("Could not find %s. Projection matching did not run. Please double check and restart the job" % self.projmatchpath)
		directories = glob.glob(os.path.join(self.projmatchpath, "Iter*"))
		directories.sort()
		for dir in directories:
			if os.path.isdir(dir):
				files = glob.glob(os.path.join(dir, filepattern))
				if isinstance(files, list) and len(files)>0:
					m = re.search("[0-9]+", os.path.basename(dir))
					iternum = int(m.group(0))
					if iternum > lastiter:
						lastiter = iternum
		apDisplay.printMsg("Xmipp ran "+str(lastiter)+" iterations")
		
		return lastiter

	#=====================
	def compute_stack_of_class_averages_and_reprojections(self, iteration):
		''' takes Xmipp single files, doc and sel files in projection-matching, creates a stack of class averages in the results directory '''

		if bool(self.runparams['package_params']['CleanUpFiles']) is False:

			os.chdir(os.path.join(self.projmatchpath, "Iter_%d" % iteration, "ProjMatchClasses"))

			### make projections, and put them back into resultspath
			selfile = "proj_match_classes.sel"
			refvolume = "../Iter_%d_reconstruction.vol" % iteration
			docfile = "proj_match_classes.doc"

#			apXmipp.compute_stack_of_class_averages_and_reprojections(d, selfile, refvolume, docfile, \
#				self.runparams['boxsize'], self.resultspath, self.params['timestamp'], iteration)
					
			### remove "lastdir" component from selfile (created by Xmipp program), then extract header information to docfile
			f = open(selfile, "r")
			lines = f.readlines()
			newlines = [re.sub("ProjMatchClasses/", "", line) for line in lines]
			f.close()
			f = open(selfile[:-4]+"_new.sel", "w")
			f.writelines(newlines)
			f.close()

			### create a projection params file and project the volume along identical Euler angles
			f = open("paramfile.descr", "w")
			f.write("%s\n" % refvolume)
			f.write("tmpproj 1 xmp\n")
			f.write("%d %d\n" % (self.runparams['boxsize'], self.runparams['boxsize']))
			f.write("%s rot tilt psi\n" % docfile)
			f.write("NULL\n")
			f.write("0 0\n")
			f.write("0 0\n")
			f.write("0 0\n")
			f.write("0 0\n")
			f.write("0 0\n")
			f.close()
			projectcmd = "xmipp_project -i paramfile.descr"
			apParam.runCmd(projectcmd, "Xmipp")
			
			### get order of projections in docfile
			d = open(docfile, "r")
			lines = d.readlines()[1:]
			d.close()
			projfile_sequence = []
			for i, l in enumerate(lines):
				if i % 2 == 0:
					filename = os.path.basename(l.split()[1])
					projfile_sequence.append(filename)
				else: pass
				
			### create stack of projections and class averages
			projections = glob.glob("tmpproj**xmp")
			projections.sort()
			if len(projections) != len(projfile_sequence):
				apDisplay.printWarning("number of projections does not match number of classes")
			stackarray = []
			stackname = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d.hed" % (self.params['timestamp'], iteration, 1))
			for i in range(len(projections)):
				stackarray.append(spider.read(projections[i]))
				stackarray.append(spider.read(projfile_sequence[i]))
			apImagicFile.writeImagic(stackarray, stackname, msg=False)
			
			### remove unnecessary files
			for file in glob.glob("tmpproj*"):
				apFile.removeFile(file)
			os.chdir(self.params['rundir'])
		else:
			apDisplay.printWarning("all projection-matching files were cleaned up ... NOT creating class-average / re-projection stack")

		return

	#=====================
	def getBadParticlesForIteration(self, iteration):
		''' 
		currently parses the file kept_particles_during_classification.txt, this is in OUR version of Xmipp ONLY, 
		and needs to be changed / updated at next Xmipp release
		'''
		
		badpartlist = []
		badpartfile = open(os.path.join(self.projmatchpath, "Iter_%d" % iteration, "kept_particles_during_classification.txt"))
		lines = badpartfile.readlines()
		split = [l.strip().split() for l in lines]
		for i,line in enumerate(split):
			if bool(float(line[1])) == False:
				head, tail = os.path.split(line[0])
				badpart = int(re.search("[0-9]+", tail).group(0))
				badpartlist.append(badpart)
			
		return badpartlist

	#=====================
	def createParticleDataFile(self, iteration):
		''' puts all relevant particle information into a single text file that can be read by the uploader '''
		
		os.chdir(self.projmatchpath)
				
		### read output from projection-matching
		docfile = os.path.join(self.projmatchpath, "Iter_%d" % iteration, "Iter_%d_current_angles.doc" % iteration)						
		docf = open(docfile, "r")
		doclines = docf.readlines()[1:]
		docsplitlines = [l.strip().split() for l in doclines]
		docf.close()
		
		### get bad particles
		try:
			badpartlist = self.getBadParticlesForIteration(iteration)
		except IOError, e:
			apDisplay.printWarning("bad particle list not found, talk to Dmitry about using a modified version of Xmipp")
			badpartlist = []
		
		### write data in appion format to input file for uploading to the database
		particledataf = open(os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol001.txt" % (self.params['timestamp'], iteration)), "w")
#		particledataf.write("### column info: ")
		particledataf.write("#%8s" % "partnum")
		particledataf.write("%10s" % "phi")
		particledataf.write("%10s" % "theta")
		particledataf.write("%10s" % "omega")
		particledataf.write("%10s" % "shiftx")
		particledataf.write("%10s" % "shifty")
#		particledataf.write("(7) mirror")
		particledataf.write("%8s" % "3D_ref#")
		particledataf.write("%8s" % "2D_cls#")
		particledataf.write("%10s" % "qfact")
		particledataf.write("%8s" % "keptp")
		particledataf.write("%8s\n" % "p_keptp")
		for i in range(len(docsplitlines)/2):
			phi = float(docsplitlines[i*2+1][2])
			theta = float(docsplitlines[i*2+1][3])
			psi = float(docsplitlines[i*2+1][4])
			mirror = bool(float(docsplitlines[i*2+1][8]))
			if mirror is True:
				phi, theta, psi = apXmipp.calculate_equivalent_Eulers_without_flip(phi, theta, psi)
			particledataf.write("%9d" % (int(docsplitlines[i*2][1][-10:-4])+1)) ### NOTE: IT IS IMPORTANT TO START WITH 1, OTHERWISE STACKMAPPING IS WRONG!!!
			particledataf.write("%10.4f" % phi)
			particledataf.write("%10.4f" % theta)
			particledataf.write("%10.4f" % psi)
			particledataf.write("%10.4f" % float(docsplitlines[i*2+1][5]))
			particledataf.write("%10.4f" % float(docsplitlines[i*2+1][6]))
#			particledataf.write("%8d" % 0) # deprecated: mirror is flipped already. Set to False
			particledataf.write("%8d" % 1)
			particledataf.write("%8d" % float(docsplitlines[i*2+1][7]))
			particledataf.write("%10.4f" % float(docsplitlines[i*2+1][9]))
			if i in badpartlist:
				particledataf.write("%8d" % 0)
			else:
				particledataf.write("%8d" % 1)
			particledataf.write("%8d\n" % 1)
		particledataf.close()
		
		os.chdir(self.params['rundir'])
				
		return

	#=====================
	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER: if the parameters were not pickled, parse protocols script to determine projection-matching params '''

		### parameters can be found in python protocols
		xmipp_protocol_projmatch = apXmipp.importProtocolPythonFile("xmipp_protocol_projmatch", self.params['rundir'])
			
		packageparams = {}
		packageparams['NumberofIterations']					= xmipp_protocol_projmatch.NumberofIterations
		packageparams['MaskFileName']						= xmipp_protocol_projmatch.MaskFileName
		packageparams['MaskRadius']						= xmipp_protocol_projmatch.MaskRadius
		packageparams['InnerRadius']						= xmipp_protocol_projmatch.InnerRadius
		packageparams['OuterRadius']						= xmipp_protocol_projmatch.OuterRadius
		packageparams['SymmetryGroup']						= xmipp_protocol_projmatch.SymmetryGroup
		packageparams['FourierMaxFrequencyOfInterest']				= xmipp_protocol_projmatch.FourierMaxFrequencyOfInterest
		packageparams['SelFileName']						= xmipp_protocol_projmatch.SelFileName
		packageparams['DocFileName']						= xmipp_protocol_projmatch.DocFileName
		packageparams['ReferenceFileName']					= xmipp_protocol_projmatch.ReferenceFileName
		packageparams['WorkingDir']						= xmipp_protocol_projmatch.WorkingDir
#		packageparams['DoDeleteWorkingDir']					= xmipp_protocol_projmatch.DoDeleteWorkingDir
#		packageparams['ContinueAtIteration']					= xmipp_protocol_projmatch.ContinueAtIteration
		packageparams['CleanUpFiles']						= xmipp_protocol_projmatch.CleanUpFiles
#		packageparams['ProjectDir']						= xmipp_protocol_projmatch.ProjectDir
#		packageparams['LogDir']							= xmipp_protocol_projmatch.LogDir
		packageparams['DoCtfCorrection']					= xmipp_protocol_projmatch.DoCtfCorrection
		packageparams['CTFDatName']						= xmipp_protocol_projmatch.CTFDatName
		packageparams['DoAutoCtfGroup']						= xmipp_protocol_projmatch.DoAutoCtfGroup
		packageparams['CtfGroupMaxDiff']					= xmipp_protocol_projmatch.CtfGroupMaxDiff
		packageparams['CtfGroupMaxResol']					= xmipp_protocol_projmatch.CtfGroupMaxResol
#		packageparams['SplitDefocusDocFile']					= xmipp_protocol_projmatch.SplitDefocusDocFile
		packageparams['PaddingFactor']						= xmipp_protocol_projmatch.PaddingFactor
		packageparams['WienerConstant']						= xmipp_protocol_projmatch.WienerConstant
		packageparams['DataArePhaseFlipped']					= xmipp_protocol_projmatch.DataArePhaseFlipped
		packageparams['ReferenceIsCtfCorrected']				= xmipp_protocol_projmatch.ReferenceIsCtfCorrected
		packageparams['DoMask']							= xmipp_protocol_projmatch.DoMask
		packageparams['DoSphericalMask']					= xmipp_protocol_projmatch.DoSphericalMask
#		packageparams['DoProjectionMatching']					= xmipp_protocol_projmatch.DoProjectionMatching
#		packageparams['DisplayProjectionMatching']				= xmipp_protocol_projmatch.DisplayProjectionMatching
#		packageparams['AvailableMemory']					= xmipp_protocol_projmatch.AvailableMemory
		packageparams['AngSamplingRateDeg']					= xmipp_protocol_projmatch.AngSamplingRateDeg
		packageparams['MaxChangeInAngles']					= xmipp_protocol_projmatch.MaxChangeInAngles
		packageparams['PerturbProjectionDirections']				= xmipp_protocol_projmatch.PerturbProjectionDirections
		packageparams['MaxChangeOffset']					= xmipp_protocol_projmatch.MaxChangeOffset
		packageparams['Search5DShift']						= xmipp_protocol_projmatch.Search5DShift
		packageparams['Search5DStep']						= xmipp_protocol_projmatch.Search5DStep
		packageparams['DoRetricSearchbyTiltAngle']				= xmipp_protocol_projmatch.DoRetricSearchbyTiltAngle
		packageparams['Tilt0']							= xmipp_protocol_projmatch.Tilt0
		packageparams['TiltF']							= xmipp_protocol_projmatch.TiltF
		packageparams['SymmetryGroupNeighbourhood']				= xmipp_protocol_projmatch.SymmetryGroupNeighbourhood
		packageparams['OnlyWinner']						= xmipp_protocol_projmatch.OnlyWinner
		packageparams['MinimumCrossCorrelation']				= xmipp_protocol_projmatch.MinimumCrossCorrelation
		packageparams['DiscardPercentage']					= xmipp_protocol_projmatch.DiscardPercentage
		packageparams['ProjMatchingExtra']					= xmipp_protocol_projmatch.ProjMatchingExtra
		packageparams['DoAlign2D']						= xmipp_protocol_projmatch.DoAlign2D
		packageparams['Align2DIterNr']						= xmipp_protocol_projmatch.Align2DIterNr
		packageparams['Align2dMaxChangeOffset']					= xmipp_protocol_projmatch.Align2dMaxChangeOffset
		packageparams['Align2dMaxChangeRot']					= xmipp_protocol_projmatch.Align2dMaxChangeRot
#		packageparams['DoReconstruction']					= xmipp_protocol_projmatch.DoReconstruction
#		packageparams['DisplayReconstruction']					= xmipp_protocol_projmatch.DisplayReconstruction
		packageparams['ReconstructionMethod']					= xmipp_protocol_projmatch.ReconstructionMethod
		packageparams['ARTLambda']						= xmipp_protocol_projmatch.ARTLambda
		packageparams['ARTReconstructionExtraCommand']				= xmipp_protocol_projmatch.ARTReconstructionExtraCommand
		packageparams['WBPReconstructionExtraCommand']				= xmipp_protocol_projmatch.WBPReconstructionExtraCommand
		packageparams['FourierReconstructionExtraCommand']			= xmipp_protocol_projmatch.FourierReconstructionExtraCommand
#		packageparams['DoSplitReferenceImages']					= xmipp_protocol_projmatch.DoSplitReferenceImages
		packageparams['ResolSam']						= xmipp_protocol_projmatch.ResolSam
#		packageparams['DisplayResolution']					= xmipp_protocol_projmatch.DisplayResolution
		packageparams['ConstantToAddToFiltration']				= xmipp_protocol_projmatch.ConstantToAddToFiltration
#		packageparams['NumberOfThreads']					= xmipp_protocol_projmatch.NumberOfThreads
#		packageparams['DoParallel']						= xmipp_protocol_projmatch.DoParallel
#		packageparams['NumberOfMpiProcesses']					= xmipp_protocol_projmatch.NumberOfMpiProcesses
#		packageparams['MpiJobSize']						= xmipp_protocol_projmatch.MpiJobSize
#		packageparams['SystemFlavour']						= xmipp_protocol_projmatch.SystemFlavour
#		packageparams['AnalysisScript']						= xmipp_protocol_projmatch.AnalysisScript

		if xmipp_protocol_projmatch.SymmetryGroup[:1] == "i":
			sym = "icos"
		else:
			sym = xmipp_protocol_projmatch.SymmetryGroup
			sym = sym.split()[0]

		### set global parameters
		runparams = {}
		runparams['numiter'] = packageparams['NumberofIterations']
		# Mask should be in pixels of original stack. Xmipp returns pixels in terms of preped stack.
		# so orig_pix = preped_pix * (orig_boxsize / preped_boxsize). 
		# This is needed in case the prepedatack was binned.
		boxscale = self.runparams['original_boxsize'] / self.runparams['boxsize']
		runparams['mask'] = packageparams['MaskRadius'] * boxscale 
		runparams['alignmentInnerRadius'] = packageparams['InnerRadius'] * boxscale
		runparams['alignmentOuterRadius'] = packageparams['OuterRadius'] * boxscale
		runparams['symmetry'] = apSymmetry.findSymmetry(sym)
		runparams['angularSamplingRate'] = packageparams['AngSamplingRateDeg']
		runparams['apix'] = packageparams['ResolSam']
		runparams['package_params'] = packageparams
		runparams['remoterundir'] = os.path.abspath(xmipp_protocol_projmatch.ProjectDir)
		runparams['rundir'] = self.params['rundir']

		return runparams

	#=====================
	def instantiateProjMatchParamsData(self, iteration):
		''' fill in database entry for ApXmippRefineIterData table '''
	
		### get all components that might have multiple values for iterations (these are the ones set in Xmipp Protocols)
		AngSamplingRateDeg			= apRecon.getComponentFromVector(self.runparams['package_params']['AngSamplingRateDeg'], iteration-1)
		MaxChangeOffset				= apRecon.getComponentFromVector(self.runparams['package_params']['MaxChangeOffset'], iteration-1)
		MaxChangeInAngles			= apRecon.getComponentFromVector(self.runparams['package_params']['MaxChangeInAngles'], iteration-1)
		Search5DShift				= apRecon.getComponentFromVector(self.runparams['package_params']['Search5DShift'], iteration-1)
		Search5DStep				= apRecon.getComponentFromVector(self.runparams['package_params']['Search5DStep'], iteration-1)
		MinimumCrossCorrelation			= apRecon.getComponentFromVector(self.runparams['package_params']['MinimumCrossCorrelation'], iteration-1)
		DiscardPercentage			= apRecon.getComponentFromVector(self.runparams['package_params']['DiscardPercentage'], iteration-1)
		DoAlign2D				= apRecon.getComponentFromVector(self.runparams['package_params']['DoAlign2D'], iteration-1)
		Align2dMaxChangeOffset			= apRecon.getComponentFromVector(self.runparams['package_params']['Align2dMaxChangeOffset'], iteration-1)
		Align2dMaxChangeRot			= apRecon.getComponentFromVector(self.runparams['package_params']['Align2dMaxChangeRot'], iteration-1)
		ReconstructionMethod			= apRecon.getComponentFromVector(self.runparams['package_params']['ReconstructionMethod'], iteration-1)
		ARTLambda				= apRecon.getComponentFromVector(self.runparams['package_params']['ARTLambda'], iteration-1)
		ConstantToAddToFiltration		= apRecon.getComponentFromVector(self.runparams['package_params']['ConstantToAddToFiltration'], iteration-1)

		### setup database object using components for each iteration
		refineProtocolParamsq = appiondata.ApXmippRefineIterData()
		refineProtocolParamsq['NumberofIterations']					= self.runparams['package_params']['NumberofIterations']
		refineProtocolParamsq['MaskFileName']						= self.runparams['package_params']['MaskFileName']
		refineProtocolParamsq['MaskRadius']						= self.runparams['package_params']['MaskRadius']
		refineProtocolParamsq['InnerRadius']						= self.runparams['package_params']['InnerRadius']
		refineProtocolParamsq['OuterRadius']						= self.runparams['package_params']['OuterRadius']
		refineProtocolParamsq['SymmetryGroup']						= self.runparams['package_params']['SymmetryGroup']
		refineProtocolParamsq['FourierMaxFrequencyOfInterest']				= self.runparams['package_params']['FourierMaxFrequencyOfInterest']
		refineProtocolParamsq['SelFileName']						= self.runparams['package_params']['SelFileName']
		refineProtocolParamsq['DocFileName']						= self.runparams['package_params']['DocFileName']
		refineProtocolParamsq['ReferenceFileName']					= self.runparams['package_params']['ReferenceFileName']
		refineProtocolParamsq['WorkingDir']						= self.runparams['package_params']['WorkingDir']
#		refineProtocolParamsq['DoDeleteWorkingDir']					= self.runparams['package_params']['DoDeleteWorkingDir']
#		refineProtocolParamsq['ContinueAtIteration']					= self.runparams['package_params']['ContinueAtIteration']
		refineProtocolParamsq['CleanUpFiles']						= self.runparams['package_params']['CleanUpFiles']
#		refineProtocolParamsq['ProjectDir']						= self.runparams['package_params']['ProjectDir']
#		refineProtocolParamsq['LogDir']							= self.runparams['package_params']['LogDir']
		refineProtocolParamsq['DoCtfCorrection']					= self.runparams['package_params']['DoCtfCorrection']
		refineProtocolParamsq['CTFDatName']						= self.runparams['package_params']['CTFDatName']
		refineProtocolParamsq['DoAutoCtfGroup']						= self.runparams['package_params']['DoAutoCtfGroup']
		refineProtocolParamsq['CtfGroupMaxDiff']					= self.runparams['package_params']['CtfGroupMaxDiff']
		refineProtocolParamsq['CtfGroupMaxResol']					= self.runparams['package_params']['CtfGroupMaxResol']
#		refineProtocolParamsq['SplitDefocusDocFile']					= self.runparams['package_params']['SplitDefocusDocFile']
		refineProtocolParamsq['PaddingFactor']						= self.runparams['package_params']['PaddingFactor']
		refineProtocolParamsq['WienerConstant']						= self.runparams['package_params']['WienerConstant']
		refineProtocolParamsq['DataArePhaseFlipped']					= self.runparams['package_params']['DataArePhaseFlipped']
		refineProtocolParamsq['ReferenceIsCtfCorrected']				= self.runparams['package_params']['ReferenceIsCtfCorrected']
		refineProtocolParamsq['DoMask']							= self.runparams['package_params']['DoMask']
		refineProtocolParamsq['DoSphericalMask']					= self.runparams['package_params']['DoSphericalMask']
#		refineProtocolParamsq['DoProjectionMatching']					= self.runparams['package_params']['DoProjectionMatching']
#		refineProtocolParamsq['DisplayProjectionMatching']				= self.runparams['package_params']['DisplayProjectionMatching']
#		refineProtocolParamsq['AvailableMemory']					= self.runparams['package_params']['AvailableMemory']
		refineProtocolParamsq['AngSamplingRateDeg']					= AngSamplingRateDeg
		refineProtocolParamsq['MaxChangeInAngles']					= MaxChangeInAngles
		refineProtocolParamsq['PerturbProjectionDirections']				= self.runparams['package_params']['PerturbProjectionDirections']
		refineProtocolParamsq['MaxChangeOffset']					= MaxChangeOffset
		refineProtocolParamsq['Search5DShift']						= Search5DShift		
		refineProtocolParamsq['Search5DStep']						= Search5DStep
		refineProtocolParamsq['DoRetricSearchbyTiltAngle']				= self.runparams['package_params']['DoRetricSearchbyTiltAngle']
		refineProtocolParamsq['Tilt0']							= self.runparams['package_params']['Tilt0']
		refineProtocolParamsq['TiltF']							= self.runparams['package_params']['TiltF']
		refineProtocolParamsq['SymmetryGroupNeighbourhood']				= self.runparams['package_params']['SymmetryGroupNeighbourhood']
		refineProtocolParamsq['OnlyWinner']						= self.runparams['package_params']['OnlyWinner']
		refineProtocolParamsq['MinimumCrossCorrelation']				= MinimumCrossCorrelation
		refineProtocolParamsq['DiscardPercentage']					= DiscardPercentage
		refineProtocolParamsq['ProjMatchingExtra']					= self.runparams['package_params']['ProjMatchingExtra']
		refineProtocolParamsq['DoAlign2D']						= DoAlign2D
		refineProtocolParamsq['Align2DIterNr']						= self.runparams['package_params']['Align2DIterNr']
		refineProtocolParamsq['Align2dMaxChangeOffset']					= Align2dMaxChangeOffset
		refineProtocolParamsq['Align2dMaxChangeRot']					= Align2dMaxChangeRot
#		refineProtocolParamsq['DoReconstruction']					= self.runparams['package_params']['DoReconstruction']
#		refineProtocolParamsq['DisplayReconstruction']					= self.runparams['package_params']['DisplayReconstruction']
		refineProtocolParamsq['ReconstructionMethod']					= ReconstructionMethod
		refineProtocolParamsq['ARTLambda']						= ARTLambda
		refineProtocolParamsq['ARTReconstructionExtraCommand']				= self.runparams['package_params']['ARTReconstructionExtraCommand']
		refineProtocolParamsq['WBPReconstructionExtraCommand']				= self.runparams['package_params']['WBPReconstructionExtraCommand']
		refineProtocolParamsq['FourierReconstructionExtraCommand']			= self.runparams['package_params']['FourierReconstructionExtraCommand']
#		refineProtocolParamsq['DoSplitReferenceImages']					= self.runparams['package_params']['DoSplitReferenceImages']
		refineProtocolParamsq['ResolSam']						= self.runparams['package_params']['ResolSam']
#		refineProtocolParamsq['DisplayResolution']					= self.runparams['package_params']['DisplayResolution']
		refineProtocolParamsq['ConstantToAddToFiltration']				= ConstantToAddToFiltration
#		refineProtocolParamsq['NumberOfThreads']					= self.runparams['package_params']['NumberOfThreads']
#		refineProtocolParamsq['DoParallel']						= self.runparams['package_params']['DoParallel']
#		refineProtocolParamsq['NumberOfMpiProcesses']					= self.runparams['package_params']['NumberOfMpiProcesses']
#		refineProtocolParamsq['MpiJobSize']						= self.runparams['package_params']['MpiJobSize']
#		refineProtocolParamsq['SystemFlavour']						= self.runparams['package_params']['SystemFlavour']
#		refineProtocolParamsq['AnalysisScript']						= self.runparams['package_params']['AnalysisScript']

		return refineProtocolParamsq
	
	#=====================
	def cleanupFiles(self, complete_refinements):
		''' deletes all intermediate files for which database entries exitst '''
		
 		### cleanup directories (projection-matching and reference libraries)
		os.chdir(self.runparams['package_params']['WorkingDir'])
		if os.path.isdir("ProjMatchClasses"):
			apFile.removeDir("ProjMatchClasses")
		if os.path.isdir("ReferenceLibrary"):
			apFile.removeDir("ReferenceLibrary")
			
		### cleanup temp files
		for file in glob.glob(os.path.join(self.resultspath, "*tmp.mrc")):
			apFile.removeFile(file)
		
		### cleanup files (.vol only now ... I'm leaving the .fsc, .sel, and .doc files *** Dmitry)
		for reference_number, iters in complete_refinements.iteritems():
			for iteration in iters:
				for file in glob.glob(os.path.join("Iter_%d" % iteration, "*.vol")): 
					apFile.removeFile(file)
		os.chdir(self.params['rundir'])
		
		return
	
	#=====================
	def start(self):
		
		### database entry parameters
		package_table = 'ApXmippRefineIterData|xmippParams'
		
		### set projection-matching path
		self.projmatchpath = os.path.abspath(os.path.join(self.params['rundir'], "recon", self.runparams['package_params']['WorkingDir']))
#		self.projmatchpath = os.path.abspath(os.path.join(self.params['rundir'], self.runparams['package_params']['WorkingDir']))
	
		### check for variable root directories between file systems
		apXmipp.checkSelOrDocFileRootDirectoryInDirectoryTree(self.params['rundir'], self.runparams['remoterundir'], self.runparams['rundir'])

		### determine which iterations to upload
		lastiter = self.findLastCompletedIteration()
		uploadIterations = self.verifyUploadIterations(lastiter)	
	
		### upload each iteration
		for iteration in uploadIterations:
		
			apDisplay.printColor("uploading iteration %d" % iteration, "cyan")
		
			### set package parameters, as they will appear in database entries
			package_database_object = self.instantiateProjMatchParamsData(iteration)
			
			### move FSC file to results directory
			oldfscfile = os.path.join(self.projmatchpath, "Iter_%d" % iteration, "Iter_%d_resolution.fsc" % iteration)
			newfscfile = os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.fsc" % (self.params['timestamp'],iteration))
			if os.path.exists(oldfscfile):
				shutil.copyfile(oldfscfile, newfscfile)
			
			### create a stack of class averages and reprojections (optional)
			self.compute_stack_of_class_averages_and_reprojections(iteration)
				
			### create a text file with particle information
			self.createParticleDataFile(iteration)
					
			if not self.params['euleronly']:
				### create mrc file of map for iteration and reference number
				oldvol = os.path.join(self.projmatchpath, "Iter_%d" % iteration, "Iter_%d_reconstruction.vol" % iteration)
				newvol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol001.mrc" % (self.params['timestamp'], iteration))
				mrccmd = "proc3d %s %s apix=%.3f" % (oldvol, newvol, self.runparams['apix'])
				apParam.runCmd(mrccmd, "EMAN")
			
				### make chimera snapshot of volume
				self.createChimeraVolumeSnapshot(newvol, iteration)
			
			### instantiate database objects
			self.insertRefinementRunData(iteration)
			self.insertRefinementIterationData(iteration, package_table, package_database_object)
				
		### calculate Euler jumps
		if self.runparams['numiter'] > 1:
			self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)	
		
		### query the database for the completed refinements BEFORE deleting any files ... returns a dictionary of lists
		### e.g. {1: [5, 4, 3, 2, 1]} means 5 iters completed for refine 1
		complete_refinements = self.verifyNumberOfCompletedRefinements(multiModelRefinementRun=False)
		if self.params['cleanup_files'] is True:
			self.cleanupFiles(complete_refinements)

#=====================
if __name__ == "__main__":
	upload3D = uploadXmippProjectionMatchingRefinementScript()
	upload3D.start()
	upload3D.close()

