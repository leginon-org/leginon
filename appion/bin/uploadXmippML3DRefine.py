#!/usr/bin/env python

# python
import os, re, glob, shutil, math, sys

# appion
from appionlib import appiondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apParam
from appionlib import apFile
from appionlib import apImagicFile
from appionlib import apXmipp
from appionlib import apSymmetry
from appionlib import reconUploader

# spider stack writer
from pyami import spider

#======================
#======================

class uploadXmippML3DScript(reconUploader.generalReconUploader):
	
	def __init__(self):
		###	DEFINE THE NAME OF THE PACKAGE
		self.package = "XmippML3D"
		self.multiModelRefinementRun = True
		super(uploadXmippML3DScript, self).__init__()
		
	"""
	#=====================
	def addParserOptions(self):
		''' package-specific parser parameters '''
		
		### HOW MUCH IS ACTUALLY NEEDED? CAN GET ANYTHING FROM SELF.RUNPARAMS
		
		self.parser.add_option("--upload_root_path", dest="upload_root_path",
			help="path of the cluster where upload is run, e.g. /ami/data17/appion/11jan11a/recon/xmippML3Drecon2", metavar="PATH")			
		self.parser.add_option("--cluster_root_path", dest="cluster_root_path",
			help="path of the cluster where recon was run, e.g. /ddn/people/dlyumkis/appion/11jan11a/recon/xmippML3Drecon2", metavar="PATH")
			
		return
	"""
					
	#=====================
	def findLastCompletedIteration(self):
		''' find the last iteration that finished in ml3d job '''
		
		lastiter = 0
		if os.path.isdir(self.ml3dpath) is False:
			apDisplay.printError("ML3D projection matching did not run. Please double check and restart the job")
		volumefiles = glob.glob(os.path.join(self.ml3dpath, "*it*.vol"))
		volumefiles.sort()
		for vol in volumefiles:
			m = re.search("it0*([0-999])*", vol)
#			m = re.search("it0*([0-9]+)*", vol)
			iternum = int(m.group(0)[2:])
			if iternum > lastiter:
				lastiter = iternum
		apDisplay.printMsg("Xmipp ran "+str(lastiter)+" iterations")

		return lastiter

	#=====================
	def createModifiedLibFile(self):
		'''
		create a modified lib file that contains angles for all references. (this is currently a workaround, because ML3D lib file, i.e. 'ml3d_lib.doc',
		currently only reports the Euler angle projections for the FIRST, SINGLE reference. Therefore, it needs to be appended with parameters for all
		corresponding references (e.g. vol000002, vol000003, vol000004, etc. Using the generic libfile to create new class averages via 
		xmipp_mpi_angular_class_average DOES NOT WORK
		'''

		### create new ml3d_lib.doc file, somewhat of a workaround
		libf = open(os.path.join(self.ml3dpath, "ml3d_lib.doc"), "r")
		liblines = libf.readlines()
		libf.close()
		newliblines = []
		for j in range(self.runparams['package_params']['NumberOfReferences']):
			split_liblines = [l.split() for l in liblines]
			for k in range(len(split_liblines)):
				### change class avg ref value
				newrefval = int(split_liblines[k][0]) + len(split_liblines)*(j)
				newline = "\t"+str(newrefval)
				### append the rest of the line
				for l in range(1,len(split_liblines[k])):
					newline += "\t"+str(split_liblines[k][l])
				newliblines.append(newline+"\n")
		libf = open(os.path.join(self.ml3dpath, "ml3d_lib_new.doc"), "w")
		libf.writelines(newliblines)
		libf.close()		
		
		'''
		for j in range(self.runparams['package_params']['NumberOfReferences']):
			libf = open(os.path.join(self.ml3dpath, "ml3d_lib.doc"), "r")
			liblines = libf.readlines()
			libf.close()
			split_liblines = [l.split() for l in liblines]
			for k in range(len(split_liblines)):
				newrefval = int(split_liblines[k][0]) + len(split_liblines)*(j)
				newline = "\t"+str(newrefval)
				for l in range(1,len(split_liblines[k])):
					newline += "\t"+str(split_liblines[k][l])
				liblines.append(newline+"\n")
		libf = open(os.path.join(self.ml3dpath, "ml3d_lib_new.doc"), "w")
		libf.writelines(liblines)
		libf.close()
		'''
		return len(newliblines)

	#=====================			
	def compute_stack_of_class_averages_and_reprojections(self, iteration, reference_number):
		''' takes Xmipp single files, doc and sel files associated with ML3D, creates a stack of class averages in the results directory '''
			
		'''			
		### make projections, and put them back into resultspath
		selfile = "ml3d_it%.6d_vol%.6d.sel" % (iteration, reference_number)
		refvolume = "ml3d_it%.6d_vol%.6d.vol\n" % (iteration, reference_number)
		docfile = "ml3d_it%.6d_vol%.6d.doc" % (iteration, reference_number)
		
		apXmipp.compute_stack_of_class_averages_and_reprojections(self.ml3dpath, selfile, refvolume, docfile, \
			self.runparams['boxsize'], self.resultspath, self.params['timestamp'], iteration, reference_number, extract=True)

		return				
		'''		
		os.chdir(self.ml3dpath)		
				
		### remove "RunML3D/" from selfile (created by ML3D program), then extract header information to docfile
		selfile = "ml3d_it%.6d_vol%.6d.sel" % (iteration, reference_number)
		f = open(selfile, "r")
		lines = f.readlines()
		newlines = [re.sub("RunML3D/", "", line) for line in lines]
		f.close()
		f = open(selfile, "w")
		f.writelines(newlines)
		f.close()
		extractcmd = "xmipp_header_extract -i ml3d_it%.6d_vol%.6d.sel -o ml3d_it%.6d_vol%.6d.doc" \
			% (iteration, reference_number, iteration, reference_number)
		apParam.runCmd(extractcmd, "Xmipp")
		
		### create a projection params file and project the volume along identical Euler angles
		f = open("paramfile.descr", "w")
		f.write("ml3d_it%.6d_vol%.6d.vol\n" % (iteration, reference_number))
		f.write("tmpproj 1 xmp\n")
		f.write("%d %d\n" % (self.runparams['boxsize'], self.runparams['boxsize']))
		f.write("ml3d_it%.6d_vol%.6d.doc rot tilt psi\n" % (iteration, reference_number))
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
		docfile = "ml3d_it%.6d_vol%.6d.doc" % (iteration, reference_number)
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
			apDisplay.printWarning("number of projections does not match number of classes for model %d, iteration %d")
		stackarray = []
		stackname = os.path.join(self.resultspath, "proj-avgs_%s_it%.3d_vol%.3d.hed" % (self.params['timestamp'], iteration, reference_number))
		for i in range(len(projections)):
			stackarray.append(spider.read(projections[i]))
			stackarray.append(spider.read(projfile_sequence[i]))
		apImagicFile.writeImagic(stackarray, stackname, msg=False)
		
		### remove unnecessary files
		for file in glob.glob("tmpproj*"):
			apFile.removeFile(file)			
		
		os.chdir(self.params['rundir'])

		return
		
	#=====================
	def calculateFSCforIteration(self, iteration, reference_number):
		''' requires manipulation of data using Xmipp programs, benefits from MPI parallelization '''
	
		os.chdir(self.ml3dpath)
						
		### split selfile
		selfile = "ml3d_it%.6d_class_vol%.6d.sel" % (iteration,reference_number)
		xmipp_split_selfile_cmd = "xmipp_selfile_split -i %s" % selfile
		apParam.runCmd(xmipp_split_selfile_cmd, "Xmipp")

		### make even and odd docfiles from split selfile
		xmipp_mk_docfile_cmd1 = "xmipp_docfile_select_subset -i ml3d_it%.6d.doc -sel ml3d_it%.6d_class_vol%.6d_1.sel -o tmpdocfile_1.doc" \
			% (iteration,iteration,reference_number)
		apParam.runCmd(xmipp_mk_docfile_cmd1, "Xmipp")
		xmipp_mk_docfile_cmd2 = "xmipp_docfile_select_subset -i ml3d_it%.6d.doc -sel ml3d_it%.6d_class_vol%.6d_2.sel -o tmpdocfile_2.doc" \
			% (iteration,iteration,reference_number)
		apParam.runCmd(xmipp_mk_docfile_cmd2, "Xmipp")
		
		### create angular class averages from split docfiles and selfiles
		if self.params['nproc'] > 1:
			xmipp_average_cmd1 = "mpirun -np %d xmipp_mpi_angular_class_average -i tmpdocfile_1.doc -lib ml3d_lib_new.doc -o tmpclass_1" \
				% (self.params['nproc'])
			xmipp_average_cmd2 = "mpirun -np %d xmipp_mpi_angular_class_average -i tmpdocfile_2.doc -lib ml3d_lib_new.doc -o tmpclass_2" \
				% (self.params['nproc'])
		else:
			xmipp_average_cmd1 = "xmipp_angular_class_average -i tmpdocfile_1.doc -lib ml3d_lib_new.doc -o tmpclass_1"
			xmipp_average_cmd2 = "xmipp_angular_class_average -i tmpdocfile_2.doc -lib ml3d_lib_new.doc -o tmpclass_2"
		apParam.runCmd(xmipp_average_cmd1, "Xmipp")
		apParam.runCmd(xmipp_average_cmd2, "Xmipp")
		
		### reconstruct even volume
		if self.params['nproc'] > 1:
			xmipp_reconstruct_cmd = "mpirun -np %d xmipp_mpi_reconstruct_fourier -i tmpclass_1_classes.sel -o %s -weight" \
				% (self.params['nproc'], "even.vol")
		else:
			xmipp_reconstruct_cmd = "xmipp_reconstruct_fourier -i tmpclass_1_classes.sel -o %s -weight" \
				% ("even.vol")					
		apParam.runCmd(xmipp_reconstruct_cmd, "Xmipp")
		
		### reconstruct odd volume
		if self.params['nproc'] > 1:
			xmipp_reconstruct_cmd = "mpirun -np %d xmipp_mpi_reconstruct_fourier -i tmpclass_2_classes.sel -o %s -weight" \
				% (self.params['nproc'], "odd.vol")
		else:
			xmipp_reconstruct_cmd = "xmipp_reconstruct_fourier -i tmpclass_2_classes.sel -o %s -weight" \
				% ("odd.vol")					
		apParam.runCmd(xmipp_reconstruct_cmd, "Xmipp")
		
		### calculate FSC
		apDisplay.printMsg("calculating FSC resolution for iteration %d, volume %d using split selfile" % (iteration,reference_number))
		xmipp_resolution_cmd = "xmipp_resolution_fsc -ref even.vol -i odd.vol -sam %.3f" % (self.runparams['apix'])	
		apParam.runCmd(xmipp_resolution_cmd, "Xmipp")
		
		### rename FSC file, get resolution value, and remove unwanted files
		oldfscfile = os.path.join(self.ml3dpath, "odd.vol.frc")
		newfscfile = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.fsc" % (self.params['timestamp'],iteration,reference_number))
		if os.path.exists(oldfscfile):
			shutil.move(oldfscfile, newfscfile)
		apFile.removeFile("ml3d_it%.6d_class_vol%.6d_1.sel" % (iteration,reference_number))
		apFile.removeFile("ml3d_it%.6d_class_vol%.6d_2.sel" % (iteration,reference_number))
		list = []
		list += [f for f in glob.glob("odd*")]
		list += [f for f in glob.glob("even*")]
		list += [f for f in glob.glob("tmp*")]
		for file in list:
			apFile.removeFile(file)
			
		os.chdir(self.params['rundir'])

		return

	#=====================
	def createParticleDataFile(self, iteration, reference_number, total_num_2d_classes):
		''' puts all relevant particle information into a single text file that can be read by the uploader '''
		
		os.chdir(self.ml3dpath)
							
		### create docfile for the iteration and reference number
		docfile = os.path.join(self.ml3dpath, "ml3d_it%.6d.doc" % (iteration))
		selfile = "ml3d_it%.6d_class_vol%.6d.sel" % (iteration,reference_number)
		makedocfilecmd = "xmipp_docfile_select_subset -i %s -sel %s -o ml3d_it%.6d_class_vol%.6d.doc" \
			% (docfile, selfile, iteration,reference_number)
		apParam.runCmd(makedocfilecmd, "Xmipp")

		classes_per_volume = total_num_2d_classes / len(self.modeldata)
		
		### read output from ml3d
		ml3ddocfile = os.path.join(self.ml3dpath, "ml3d_it%.6d_class_vol%.6d.doc" % (iteration, reference_number))
		ml3df = open(ml3ddocfile, "r")
		ml3dlines = ml3df.readlines()[1:]
		ml3dsplitlines = [l.strip().split() for l in ml3dlines]
		ml3df.close()
		
		### write data in appion format to input file for uploading to the database
		particledataf = open(os.path.join(self.resultspath, "particle_data_%s_it%.3d_vol%.3d.txt" % (self.params['timestamp'], iteration, reference_number)), "w")
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

		for i in range(len(ml3dsplitlines)/2):
			if int(float(ml3dsplitlines[i*2+1][7])) % classes_per_volume == 0:
				n = classes_per_volume
			else:
				n = int(float(ml3dsplitlines[i*2+1][7])) % classes_per_volume
			phi = float(ml3dsplitlines[i*2+1][2]))
			theta = float(ml3dsplitlines[i*2+1][3]))
			psi = float(ml3dsplitlines[i*2+1][4]))
			mirror = bool(float(ml3dsplitlines[i*2+1][8])))
			if mirror is True:
				phi, theta, psi = apXmipp.calculate_equivalent_Eulers_without_flip(phi, theta, psi)
			particledataf.write("%9d" % (int(ml3dsplitlines[i*2][1][-10:-4])+1)) ### NOTE: IT IS IMPORTANT TO START WITH 1, OTHERWISE STACKMAPPING IS WRONG!!!
			particledataf.write("%10.4f" % phi)
			particledataf.write("%10.4f" % theta)
			particledataf.write("%10.4f" % psi)
			particledataf.write("%10.4f" % float(ml3dsplitlines[i*2+1][5]))
			particledataf.write("%10.4f" % float(ml3dsplitlines[i*2+1][6]))
#			particledataf.write("%8d" % int(float(ml3dsplitlines[i*2+1][8]))) # deprecated: mirror is flipped already. Set to False
			particledataf.write("%8d" % int(reference_number))
			particledataf.write("%8d" % n)
			particledataf.write("%10.4f" % 0)
			particledataf.write("%8d" % 1)
			particledataf.write("%8d\n" % 1)
		particledataf.close()
		
		os.chdir(self.params['rundir'])
				
		return
		
	#=====================
	def parseFileForRunParameters(self):
		''' PACKAGE-SPECIFIC FILE PARSER: if the parameters were not pickled, parse protocols script to determine ML3D params '''
		
		### parameters can be found in python protocols
		xmipp_protocol_ml3d = apXmipp.importProtocolPythonFile("xmipp_protocol_ml3d", self.params['rundir'])
		
		packageparams = {}
		packageparams['InSelFile']						= xmipp_protocol_ml3d.InSelFile
		packageparams['InitialReference']				= xmipp_protocol_ml3d.InitialReference
		packageparams['WorkingDir']						= xmipp_protocol_ml3d.WorkingDir
		packageparams['DoDeleteWorkingDir']				= xmipp_protocol_ml3d.DoDeleteWorkingDir
#		packageparams['ProjectDir']						= xmipp_protocol_ml3d.ProjectDir
#		packageparams['LogDir']							= xmipp_protocol_ml3d.LogDir
		packageparams['DoMlf']							= xmipp_protocol_ml3d.DoMlf
		packageparams['DoCorrectAmplitudes']			= xmipp_protocol_ml3d.DoCorrectAmplitudes
		packageparams['InCtfDatFile']					= xmipp_protocol_ml3d.InCtfDatFile
		packageparams['HighResLimit']					= xmipp_protocol_ml3d.HighResLimit
		packageparams['ImagesArePhaseFlipped']			= xmipp_protocol_ml3d.ImagesArePhaseFlipped
		packageparams['InitialMapIsAmplitudeCorrected'] = xmipp_protocol_ml3d.InitialMapIsAmplitudeCorrected
		packageparams['SeedsAreAmplitudeCorrected']		= xmipp_protocol_ml3d.SeedsAreAmplitudeCorrected
		packageparams['DoCorrectGreyScale']				= xmipp_protocol_ml3d.DoCorrectGreyScale
		packageparams['ProjMatchSampling']				= xmipp_protocol_ml3d.ProjMatchSampling
		packageparams['DoLowPassFilterReference']		= xmipp_protocol_ml3d.DoLowPassFilterReference
		packageparams['LowPassFilter']					= xmipp_protocol_ml3d.LowPassFilter
		packageparams['PixelSize']						= xmipp_protocol_ml3d.PixelSize
		packageparams['DoGenerateSeeds']				= xmipp_protocol_ml3d.DoGenerateSeeds
		packageparams['NumberOfReferences']				= xmipp_protocol_ml3d.NumberOfReferences
		packageparams['DoJustRefine']					= xmipp_protocol_ml3d.DoJustRefine
		packageparams['SeedsSelfile']					= xmipp_protocol_ml3d.SeedsSelfile
		packageparams['DoML3DClassification']			= xmipp_protocol_ml3d.DoML3DClassification
		packageparams['AngularSampling']				= xmipp_protocol_ml3d.AngularSampling
		packageparams['NumberOfIterations']				= xmipp_protocol_ml3d.NumberOfIterations
		packageparams['Symmetry']						= xmipp_protocol_ml3d.Symmetry
		packageparams['DoNorm']							= xmipp_protocol_ml3d.DoNorm
		packageparams['DoFourier']						= xmipp_protocol_ml3d.DoFourier
		packageparams['RestartIter']					= xmipp_protocol_ml3d.RestartIter
		packageparams['ExtraParamsMLrefine3D']			= xmipp_protocol_ml3d.ExtraParamsMLrefine3D
#		packageparams['NumberOfThreads']				= xmipp_protocol_ml3d.NumberOfThreads
#		packageparams['DoParallel']						= xmipp_protocol_ml3d.DoParallel
#		packageparams['NumberOfMpiProcesses']			= xmipp_protocol_ml3d.NumberOfMpiProcesses
#		packageparams['SystemFlavour']					= xmipp_protocol_ml3d.SystemFlavour
#		packageparams['AnalysisScript']					= xmipp_protocol_ml3d.AnalysisScript
		
		if xmipp_protocol_ml3d.Symmetry[:1] == "i":
			sym = "icos"
		else:
			sym = xmipp_protocol_ml3d.Symmetry
			sym = sym.split()[0]
		
		### set global parameters
		runparams = {}
		runparams['symmetry'] = apSymmetry.findSymmetry(sym)
		runparams['apix'] = packageparams['PixelSize']
		runparams['angularSamplingRate'] = packageparams['AngularSampling']
		runparams['NumberOfReferences'] = packageparams['NumberOfReferences']
		runparams['numiter'] = packageparams['NumberOfIterations']		
		runparams['package_params'] = packageparams
		runparams['remoterundir'] = os.path.abspath(xmipp_protocol_ml3d.ProjectDir)
		
		return runparams
		
	#=====================
	def instantiateML3DParamsData(self, iteration):
		''' fill in database entry for ApXmippML3DRefineIterData table '''
		
		### NOTE: AT THIS TIME, ALL PARAMETERS ARE SINGLE-COMPONENT IN ML3D_PROTOCOLS SCRIPT
		### I.E. YOU CANNOT SPECIFY MULTIPLE VALUES FOR DIFFERENT ITERATIONS
		
		### fill in database object
		ML3DProtocolParamsq = appiondata.ApXmippML3DRefineIterData()
		ML3DProtocolParamsq["InSelFile"]						=	self.runparams['package_params']["InSelFile"]
		ML3DProtocolParamsq["InitialReference"]					=	self.runparams['package_params']["InitialReference"]
		ML3DProtocolParamsq["WorkingDir"]						=	self.runparams['package_params']["WorkingDir"]
		ML3DProtocolParamsq["DoDeleteWorkingDir"]				=	self.runparams['package_params']["DoDeleteWorkingDir"]
#		ML3DProtocolParamsq["ProjectDir"]						=	self.runparams['package_params']["ProjectDir"]
#		ML3DProtocolParamsq["LogDir"]							=	self.runparams['package_params']["LogDir"]
		ML3DProtocolParamsq["DoMlf"]							=	self.runparams['package_params']["DoMlf"]
		ML3DProtocolParamsq["DoCorrectAmplitudes"]				=	self.runparams['package_params']["DoCorrectAmplitudes"]
		ML3DProtocolParamsq["InCtfDatFile"]						=	self.runparams['package_params']["InCtfDatFile"]
		ML3DProtocolParamsq["HighResLimit"]						=	self.runparams['package_params']["HighResLimit"]
		ML3DProtocolParamsq["ImagesArePhaseFlipped"]			=	self.runparams['package_params']["ImagesArePhaseFlipped"]
		ML3DProtocolParamsq["InitialMapIsAmplitudeCorrected"]	=	self.runparams['package_params']["InitialMapIsAmplitudeCorrected"]
		ML3DProtocolParamsq["SeedsAreAmplitudeCorrected"]		=	self.runparams['package_params']["SeedsAreAmplitudeCorrected"]
		ML3DProtocolParamsq["DoCorrectGreyScale"]				=	self.runparams['package_params']["DoCorrectGreyScale"]
		ML3DProtocolParamsq["ProjMatchSampling"]				=	self.runparams['package_params']["ProjMatchSampling"]
		ML3DProtocolParamsq["DoLowPassFilterReference"]			=	self.runparams['package_params']["DoLowPassFilterReference"]
		ML3DProtocolParamsq["LowPassFilter"]					=	self.runparams['package_params']["LowPassFilter"]
		ML3DProtocolParamsq["PixelSize"]						=	self.runparams['package_params']["PixelSize"]
		ML3DProtocolParamsq["DoGenerateSeeds"]					=	self.runparams['package_params']["DoGenerateSeeds"]
		ML3DProtocolParamsq["NumberOfReferences"]				=	self.runparams['package_params']["NumberOfReferences"]
		ML3DProtocolParamsq["DoJustRefine"]						=	self.runparams['package_params']["DoJustRefine"]
		ML3DProtocolParamsq["SeedsSelfile"]						=	self.runparams['package_params']["SeedsSelfile"]
		ML3DProtocolParamsq["DoML3DClassification"]				=	self.runparams['package_params']["DoML3DClassification"]
		ML3DProtocolParamsq["AngularSampling"]					=	self.runparams['package_params']["AngularSampling"]
		ML3DProtocolParamsq["NumberOfIterations"]				=	self.runparams['package_params']["NumberOfIterations"]
		ML3DProtocolParamsq["Symmetry"]							=	self.runparams['package_params']["Symmetry"]
		ML3DProtocolParamsq["DoNorm"]							=	self.runparams['package_params']["DoNorm"]
		ML3DProtocolParamsq["DoFourier"]						=	self.runparams['package_params']["DoFourier"]
		ML3DProtocolParamsq["RestartIter"]						=	self.runparams['package_params']["RestartIter"]
		ML3DProtocolParamsq["ExtraParamsMLrefine3D"]			=	self.runparams['package_params']["ExtraParamsMLrefine3D"]
#		ML3DProtocolParamsq["NumberOfThreads"]					=	self.runparams['package_params']["NumberOfThreads"]
#		ML3DProtocolParamsq["DoParallel"]						=	self.runparams['package_params']["DoParallel"]
#		ML3DProtocolParamsq["NumberOfMpiProcesses"]				=	self.runparams['package_params']["NumberOfMpiProcesses"]
#		ML3DProtocolParamsq["SystemFlavour"]					=	self.runparams['package_params']["SystemFlavour"]
#		ML3DProtocolParamsq["AnalysisScript"]					=	self.runparams['package_params']["AnalysisScript"]

		return ML3DProtocolParamsq

	#=====================
	def cleanupFiles(self, complete_refinements):
		''' deletes all intermediate files for which database entries exitst '''
		
		### cleanup directories (grey-scale correction and initial reference generation)
		os.chdir(self.runparams['package_params']['WorkingDir'])
		for i in range(self.runparams['package_params']['NumberOfReferences']):
			if os.path.isdir("GenerateSeed_%d" % (i+1)):
				apFile.removeDir("GenerateSeed_%d" % (i+1))
		if os.path.isdir("CorrectGreyscale"):
			apFile.removeDir("CorrectGreyscale")
		
		### cleanup temp files
		for file in glob.glob(os.path.join(self.resultspath, "*tmp.mrc")):
			apFile.removeFile(file)
	
		### cleanup ML3D files (.vol, .xmp, and .proj files for now ... I'm leaving the .basis, .sel, .doc, .hist, and .log files *** Dmitry)
		apFile.removeFile("corrected_reference.vol")
		apFile.removeFile("initial_reference.vol")
		os.chdir(self.ml3dpath)
		delete_projections = True
		for reference_number, iters in complete_refinements.iteritems():
			apFile.removeFile("ml3d_it000000_vol%.6d.vol" % reference_number)
			for iteration in iters:
				for file in glob.glob("ml3d_it%.6d*.xmp" % iteration):
					apFile.removeFile(os.path.join(self.ml3dpath, file))
				for file in glob.glob("ml3d_it%.6d_vol%.6d.vol" % (iteration, reference_number)):
					apFile.removeFile(os.path.join(self.ml3dpath, file))
			if self.runparams['numiter'] != iters[-1]:	### if one of the iterations did not completely upload
				delete_projections = False
		if delete_projections is True:
			for file in glob.glob("ml3d_ref*.xmp"):
				apFile.removeFile(file)
			for file in glob.glob("ml3d_lib*.proj"):
				apFile.removeFile(file)
		os.chdir(self.params['rundir'])
	
		return

	#=====================
	def start(self):
		
		### database entry parameters
		package_table = 'ApXmippML3DRefineIterData|xmippML3DParams'
				
		### set ml3d path
		self.ml3dpath = os.path.abspath(os.path.join(self.params['rundir'], "recon", self.runparams['package_params']['WorkingDir'], "RunML3D"))
			
		### check for variable root directories between file systems
		if os.path.split(self.runparams['remoterundir'])[1] == "recon":
			self.runparams['remoterundir'] = os.path.split(self.runparams['remoterundir'])[0]
		apXmipp.checkSelOrDocFileRootDirectoryInDirectoryTree(self.params['rundir'], self.runparams['remoterundir'], self.params['rundir'])
						
		### determine which iterations to upload
		lastiter = self.findLastCompletedIteration()
		uploadIterations = self.verifyUploadIterations(lastiter)				

		### create ml3d_lib.doc file somewhat of a workaround, but necessary to make projections
		total_num_2d_classes = self.createModifiedLibFile()
		
		### upload each iteration
		for iteration in uploadIterations:
			
			### set package parameters, as they will appear in database entries
			package_database_object = self.instantiateML3DParamsData(iteration)
			
			for j in range(self.runparams['NumberOfReferences']):
				
				### calculate FSC for each iteration using split selfile (selfile requires root directory change)
				self.calculateFSCforIteration(iteration, j+1)
				
				### create a stack of class averages and reprojections (optional)
				self.compute_stack_of_class_averages_and_reprojections(iteration, j+1)
					
				### create a text file with particle information
				self.createParticleDataFile(iteration, j+1, total_num_2d_classes)
						
				### create mrc file of map for iteration and reference number
				oldvol = os.path.join(self.ml3dpath, "ml3d_it%.6d_vol%.6d.vol" % (iteration, j+1))
				newvol = os.path.join(self.resultspath, "recon_%s_it%.3d_vol%.3d.mrc" % (self.params['timestamp'], iteration, j+1))
				mrccmd = "proc3d %s %s apix=%.3f" % (oldvol, newvol, self.runparams['apix'])
				apParam.runCmd(mrccmd, "EMAN")
				
				### make chimera snapshot of volume
				self.createChimeraVolumeSnapshot(newvol, iteration, j+1)
				
				### instantiate database objects
				self.insertRefinementRunData(iteration, j+1)
				self.insertRefinementIterationData(iteration, package_table, package_database_object, j+1)
				
		### calculate Euler jumps
		if self.runparams['numiter'] > 1:
			self.calculateEulerJumpsAndGoodBadParticles(uploadIterations)			
			
		### query the database for the completed refinements BEFORE deleting any files ... returns a dictionary of lists
		### e.g. {1: [5, 4, 3, 2, 1], 2: [6, 5, 4, 3, 2, 1]} means 5 iters completed for refine 1 & 6 iters completed for refine 2
		complete_refinements = self.verifyNumberOfCompletedRefinements(multiModelRefinementRun=True)
		if self.params['cleanup_files'] is True:
			self.cleanupFiles(complete_refinements)
			
		
#=====================
if __name__ == "__main__":
	refine3d = uploadXmippML3DScript()
	refine3d.start()
	refine3d.close()

