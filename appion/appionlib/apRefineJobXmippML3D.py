#!/usr/bin/env python
#	
#	SETS UP ALL THE NECESSARY FILES AND XMIPP PROTOCOLS SCRIPT FOR RUNNING ML3D REFINEMENT 
#

#python
import os
import time
import cPickle
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apModel
from appionlib import apStack
from appionlib import apSymmetry
from appionlib import apXmipp


#======================
#======================
	
class XmippML3DRefineJob(appionScript.AppionScript):

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
		self.parser.add_option("--ProjMatchSampling", dest="ProjMatchSampling", default=15,
			help="Angular sampling for a quick projection matching to obtain right grey scale. As the resolution of the intial reference \
				should be low, this sampling can be relatively crude, e.g. 15", metavar="INT")
		self.parser.add_option("--DoLowPassFilterReference", dest="DoLowPassFilterReference", default=False,
			action="store_true", help="Low-pass filter the initial reference. It is highly recommended to low-pass filter your initial \
				reference volume as much as you can.")						
		self.parser.add_option("--LowPassFilter", dest="LowPassFilter", default=50,
			help="Resolution of the low-pass filter (in Angstroms)", metavar="INT")			
		self.parser.add_option("--AngularSampling", dest="AngularSampling", default=10,
			help="Angular sampling for ML(F)3D classification: Fine samplings take huge amounts of CPU and memory. Therefore, in general, \
				don't use samplings finer than 10 degrees.", metavar="INT")	
				
#		### Xmipp path variables
#		self.parser.add_option("--cluster_root_path", dest="cluster_root_path",
#			help="path of the cluster where recon will be run, e.g. /ddn/people/dlyumkis/appion/11jan11a/recon/xmippML3Drecon2", metavar="PATH")
	
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
		if len(self.params['modelnames']) > 1:
			selfile = "reference_volumes.sel"
			sf = open(selfile, "w")
			for model in self.params['modelnames']:	
				sf.write(str(model)+"\t1\n")
			sf.close()		
			protocolPrm["InitialReference"]				=	""
			protocolPrm["SeedsSelfile"]					=	os.path.join(self.params['rundir'], "initialmodels.sel")
			protocolPrm["DoGenerateSeeds"]				=	False			
		else:
			protocolPrm["InitialReference"]				=	self.params['modelnames'][0]
			protocolPrm["SeedsSelfile"]					=	""
			protocolPrm["DoGenerateSeeds"]				=	True
		protocolPrm["InSelFile"]						=	"partlist.sel" ### this probably should not be hardcoded
		protocolPrm["WorkingDir"]						=	"ml3d"
		protocolPrm["DoDeleteWorkingDir"]				=	False
		protocolPrm["ProjectDir"]						=	self.params['recondir']
		protocolPrm["LogDir"]							=	"Logs"
		protocolPrm["DoMlf"]							=	self.params['DoMlf']
		protocolPrm["DoCorrectAmplitudes"]				=	True
		protocolPrm["InCtfDatFile"]						=	"all_images.ctfdat"
		protocolPrm["HighResLimit"]						=	self.params['HighResLimit']
		protocolPrm["ImagesArePhaseFlipped"]			=	True		### DEFAULTED TO TRUE FOR NOW, SHOULD QUERY DATABASE, BUT A BIT COMPLICATED DUE TO MULTIPLE POTENTIAL STACK RUNS
		protocolPrm["InitialMapIsAmplitudeCorrected"]	=	False
		protocolPrm["SeedsAreAmplitudeCorrected"]		=	False
		protocolPrm["DoCorrectGreyScale"]				=	True
		protocolPrm["ProjMatchSampling"]				=	self.params['ProjMatchSampling']
		protocolPrm["DoLowPassFilterReference"]			=	self.params['DoLowPassFilterReference']
		protocolPrm["LowPassFilter"]					=	self.params['LowPassFilter']
		protocolPrm["PixelSize"]						=	"%.3f" % self.params['apix']
		protocolPrm["NumberOfReferences"]				=	self.params['NumberOfReferences']
		protocolPrm["DoJustRefine"]						=	False
		protocolPrm["DoML3DClassification"]				=	True
		protocolPrm["AngularSampling"]					=	self.params['AngularSampling']
		protocolPrm["NumberOfIterations"]				=	self.params['numiter']
		protocolPrm["Symmetry"]							=	self.params['symmetry']
		protocolPrm["DoNorm"]							=	False
		protocolPrm["DoFourier"]						=	False
		protocolPrm["RestartIter"]						=	0
		protocolPrm["ExtraParamsMLrefine3D"]			=	""
		protocolPrm["NumberOfThreads"]					=	1
		protocolPrm["DoParallel"]						=	self.params['nproc']>1
		protocolPrm["NumberOfMpiProcesses"]				=	self.params['nproc']
		protocolPrm["SystemFlavour"]					=	""
		protocolPrm["AnalysisScript"]					=	"visualize_ml3d.py"
		
		### write out python protocol into run directory
		protocolfile = os.path.join(self.params['remoterundir'],"%s.py" % protocolname)
		apXmipp.particularizeProtocol(protocol_ml3d, protocolPrm, protocolfile))
		os.chmod(os.path.join(self.params['rundir'], protocolfile), 0775)
				
		### Write the parameters for posterior uploading, both generic and specific
		self.runparams['reconstruction_package'] = "xmipp_ml3d"
#		self.runparams['upload_root_path'] = self.params['rundir']
#		self.runparams['cluster_root_path'] = self.params['cluster_root_path']
		self.runparams['reconstruction_working_dir'] = protocolPrm['WorkingDir']+"/RunML3D"
		self.runparams['package_params'] = protocolPrm
		paramfile = os.path.join(self.params['rundir'], "xmipp_ml3d_"+self.timestamp+"-params.pickle")
		apParam.dumpParameters(self.runparams, paramfile)
		
		### finished setup of input files, now run xmipp_protocols_ml3d.py from jobfile
		apDisplay.printMsg("finished setting up input files, now running xmipp_protocols_ml3d.py")
				
		return protocolfile, protocolPrm
				
	#=====================
	def makePreIterationScript(self):
		tasks = {}
		self.addToLog('....Setting up Xmipp ML3D Protocol....')
		protocolfile, protocolPrm = self.setupXmippML3DProtocol()
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

