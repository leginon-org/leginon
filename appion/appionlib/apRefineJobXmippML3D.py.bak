#!/usr/bin/env python
#	
#	SETS UP ALL THE NECESSARY FILES AND XMIPP PROTOCOLS SCRIPT FOR RUNNING ML3D REFINEMENT 
#

#python
import os
import time
import cPickle
#appion
from appionlib import apRefineJob
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apModel
from appionlib import apStack
from appionlib import apSymmetry
from appionlib import apXmipp
from appionlib import apParam


#======================
#======================
	
class XmippML3DRefineJob(apRefineJob.RefineJob):

	#=====================
	def setupParserOptions(self):		
		super(XmippML3DRefineJob,self).setupParserOptions()				
		### Xmipp ML3D-specific parameters
		self.parser.add_option("--NumberOfReferences", dest="NumberOfReferences", type="int",
			help="number of references to produce in the ML3D output. NOTE: You can start with a single initial model and produce \
				multiple references (the first iteration randomizes the seeds). You can also start with multiple initial models, in which \
				case the number of output references should be identical to the number of starting models.", metavar="INT")
		self.parser.add_option("--DoMlf", dest="DoMlf", default=False,
			action="store_true", help="Perform MLF3D instead of ML3D classification?")
		self.parser.add_option("--HighResLimit", dest="HighResLimit", type="int", default=15,
			help="No frequencies higher than this limit will be taken into account. If zero is given, no limit is imposed", metavar="INT")
		self.parser.add_option("--ProjMatchSampling", dest="ProjMatchSampling", type=int, default=15,
			help="Angular sampling for a quick projection matching to obtain right grey scale. As the resolution of the intial reference \
				should be low, this sampling can be relatively crude, e.g. 15", metavar="INT")
#		self.parser.add_option("--DoLowPassFilterReference", dest="DoLowPassFilterReference", default=False,
#			action="store_true", help="Low-pass filter the initial reference. It is highly recommended to low-pass filter your initial \
#				reference volume as much as you can.")						
		self.parser.add_option("--LowPassFilter", dest="LowPassFilter", type=float, default=50,
			help="Resolution of the low-pass filter (in Angstroms)", metavar="INT")			
		self.parser.add_option("--AngularSampling", dest="AngularSampling", default=10,
			help="Angular sampling for ML(F)3D classification: Fine samplings take huge amounts of CPU and memory. Therefore, in general, \
				don't use samplings finer than 10 degrees.", metavar="INT")	
		self.parser.add_option("--ImagesArePhaseFlipped", dest="ImagesArePhaseFlipped", default=False,
			action="store_true", help="stack images have gone through a phase-flipping operation in, for example, EMAN, ACE2, or SPIDER")				
		self.parser.add_option("--DoCorrectGreyScale", dest="DoCorrectGreyScale", default=False,
			action="store_true", help="The probabilities are based on squared differences, so that the absolute grey scale is important. \
				Often the greyscale values differ during package conversion, so this options should usually be used.")						

	
	'''
	#=====================
	def checkConflicts(self):
		num_in_models = len(self.params['modelid'].split(","))
		if num_in_models > 1:
			if num_in_models != self.params['NumberOfReferences']:
				apDisplay.printError("model IDs specified under '--modelid' must either refer to a single database entry or multiple database entries \
					whose sum is equivalent to '--NumberOfReferences'. Double check the values for '--modelid' and '--NumberOfReferences'")
		if self.params['cluster_root_path'] is None:
			apDisplay.printError("Please specify the path where the reconstruction will be run on a remote cluster")
		
		return
	'''
	
	def convertSymmetryNameForPackage(self,inputname):
		'''
		hedral symmetry key is of possible name, value is that of this package
		'''
		return apXmipp.convertSymmetryNameForPackage(inputname)

	#=====================
	def calcRefineMem(self):
		numgig = 2
		return numgig
			
	#=====================
	def setupXmippML3DProtocol(self):	
		''' sets up ML3D protocol parameters, pickles to file, etc.'''
	
		protocolname = 'xmipp_protocol_ml3d'
		### Locate protocol_ml3d
		protocol_ml3d = apXmipp.locateXmippProtocol(protocolname)
				
		### setup protocol parameters
		protocolPrm = {}
		### check for n input model dependencies
		protocolPrm["InitialReference"]                         	=       self.params['modelnames'][0]
		if len(self.params['modelnames']) > 1:
			selfile = "reference_volumes.sel"
			sf = open(selfile, "w")
			for model in self.params['modelnames']:	
				sf.write("%s\t1\n" % os.path.join(self.params['rundir'], model))
			sf.close()		
			protocolPrm["SeedsSelfile"]				=	os.path.join(self.params['rundir'], "reference_volumes.sel")
			protocolPrm["DoGenerateSeeds"]			=	False			
		else:
			protocolPrm["SeedsSelfile"]				=	""
			protocolPrm["DoGenerateSeeds"]			=	True
		protocolPrm["InSelFile"]					=	"partlist.sel" ### this maybe should not be hardcoded
		protocolPrm["WorkingDir"]					=	"ml3d"
		protocolPrm["DoDeleteWorkingDir"]			=	False
		protocolPrm["ProjectDir"]					=	self.params['recondir']
		protocolPrm["LogDir"]						=	"Logs"
		protocolPrm["DoMlf"]						=	self.params['DoMlf']
		protocolPrm["DoCorrectAmplitudes"]			=	False	
		protocolPrm["InCtfDatFile"]					=	"all_images.ctfdat"
		protocolPrm["HighResLimit"]					=	self.params['HighResLimit']
		protocolPrm["ImagesArePhaseFlipped"]		=	self.params['ImagesArePhaseFlipped']
		protocolPrm["InitialMapIsAmplitudeCorrected"]	=	False
		protocolPrm["SeedsAreAmplitudeCorrected"]		=	False
		protocolPrm["DoCorrectGreyScale"]				=	self.params['DoCorrectGreyScale']	
		protocolPrm["ProjMatchSampling"]				=	self.params['ProjMatchSampling']
		if (self.params['LowPassFilter']>1) is True:
			protocolPrm["DoLowPassFilterReference"]		=	True	
			protocolPrm["LowPassFilter"]				=	self.params['LowPassFilter']
		else:
			protocolPrm["DoLowPassFilterReference"]		= 	False
			protocolPrm["LowPassFilter"]				=	self.params['LowPassFilter']
		protocolPrm["PixelSize"]				        =	self.params['apix']
		protocolPrm["NumberOfReferences"]				=	self.params['NumberOfReferences']
		protocolPrm["DoJustRefine"]					    =	False
		protocolPrm["DoML3DClassification"]				=	True
		protocolPrm["AngularSampling"]					=	self.params['AngularSampling']
		protocolPrm["NumberOfIterations"]				=	self.params['numiter']
		protocolPrm["Symmetry"]						=	self.params['symmetry'][0]
		protocolPrm["DoNorm"]						=	False
		protocolPrm["DoFourier"]					=	False
		protocolPrm["RestartIter"]					=	0
		protocolPrm["ExtraParamsMLrefine3D"]				=	""
		protocolPrm["NumberOfThreads"]					=	1
		protocolPrm["DoParallel"]					=	self.params['nproc']>1
		protocolPrm["NumberOfMpiProcesses"]				=	self.params['nproc']
		protocolPrm["SystemFlavour"]					=	""
		protocolPrm["AnalysisScript"]					=	"visualize_ml3d.py"
		
		### write out python protocol into run directory
		protocolfile = os.path.join(self.params['remoterundir'],"%s.py" % protocolname)
		apXmipp.particularizeProtocol(protocol_ml3d, protocolPrm, protocolfile)
		os.chmod(os.path.join(self.params['rundir'], protocolfile), 0775)
				
		### Write the parameters for posterior uploading, both generic and specific
		self.runparams = {}
		self.runparams['reconstruction_package'] = "xmipp_ml3d"
		self.runparams['remoterundir'] = self.params['remoterundir']
#		self.runparams['reconstruction_working_dir'] = protocolPrm["WorkingDir"]		
		self.runparams['reconstruction_working_dir'] = protocolPrm['WorkingDir']+"/RunML3D"
		self.runparams['numiter'] = protocolPrm['NumberOfIterations']
		self.runparams['NumberOfReferences'] = protocolPrm['NumberOfReferences']
		self.runparams['symmetry'] = protocolPrm["Symmetry"]
		self.runparams['package_params'] = protocolPrm
		paramfile = os.path.join(self.params['remoterundir'], "xmipp_ml3d_"+self.timestamp+"-params.pickle")
		apParam.dumpParameters(self.runparams, paramfile)
		
		### finished setup of input files, now run xmipp_protocols_ml3d.py from jobfile
		apDisplay.printMsg("finished setting up input files, now running xmipp_protocols_ml3d.py")
				
		return protocolfile, protocolPrm
	
	def makeNewTrialScript(self):
		print self.params['modelnames'][0]
		self.addSimpleCommand('ln -s %s %s' % (self.params['modelnames'][0], 
			os.path.join(self.params['remoterundir'], self.params['modelnames'][0])))
		partar = os.path.join(self.params['remoterundir'],'partfiles.tar.gz')
		partpath = os.path.join(self.params['remoterundir'],'partfiles')
		if not os.path.isdir(partpath):
			# partfiles need to be untared in its directory
			self.addSimpleCommand('mkdir %s' % partpath)
			self.addSimpleCommand('cd %s' % partpath)
			self.addSimpleCommand('tar xvf %s' % partar)
			# return to recondir
			self.addSimpleCommand('cd %s' % self.params['recondir'])
				
	#=====================
	def makePreIterationScript(self):
		tasks = {}
		self.addToLog('....Setting up Xmipp ML3D Protocol....')
		protocolfile, protocolPrm = self.setupXmippML3DProtocol()

		### check for variable root directories between file systems
		apXmipp.checkSelOrDocFileRootDirectoryInDirectoryTree(self.params['remoterundir'], self.params['rundir'], self.params['remoterundir'])
		
		self.addToLog('....Start running Xmipp Protocol....')
		tasks = self.addToTasks(tasks,'python %s' % protocolfile,self.calcRefineMem(),self.params['nproc'])
		protocol_pyname = os.path.basename(protocolfile)
		protocolname = protocol_pyname.split('.')[0]
		tasklogfilename = protocolname+'_'+protocolPrm['WorkingDir']+'.log'
		tasklogfile = os.path.join(self.params['recondir'],protocolPrm['LogDir'],tasklogfilename)
		tasks = self.logTaskStatus(tasks,'protocol_run',tasklogfile)
		tasks = self.addToTasks(tasks,'cp %s %s' % (protocolfile,self.params['recondir']))
		self.addJobCommands(tasks)	

#=====================
if __name__ == "__main__":
	ml3drefine3d = XmippML3DRefineJob()
	ml3drefine3d.start()
	ml3drefine3d.close()

