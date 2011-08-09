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
	
class xmippML3DRefineScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog [ options ]")
		
		### stack and initial model necessary for the refinement
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("--modelid", dest="modelid", type="str", 	
			help="input model(s) for multi-model refinement. You can start with one model or as many as you like. Just provide the \
				database IDs, like so: '--modelid=1' or '--modelid=1,3,17', etc.", metavar="ID#(s)")
				
		### appion-specific params (boxsize, pixelsize, etc.)
		self.parser.add_option("--apix", dest="apix", type="float",
			help="pixelsize of the particles / map during refinement", metavar="FLOAT")		
		self.parser.add_option("--boxsize", dest="boxsize", type="int",
			help="boxsize of the particles / map during refinement", metavar="INT")
		self.parser.add_option("--NumberOfReferences", dest="NumberOfReferences", type="int",
			help="number of references to produce in the ML3D output. NOTE: You can start with a single initial model and produce \
				multiple references (the first iteration randomizes the seeds). You can also start with multiple initial models, in which \
				case the number of output references should be identical to the number of starting models.", metavar="INT")
		self.parser.add_option("--numiter", dest="numiter", type="int", default=25,
			help="number of iterations to perform", metavar="INT")
		self.parser.add_option("--nproc", dest="nproc", type="int", default=128,
			help="number of processors to use in the refinement. NOTE: ML3D is EXTREMELY CPU-intensive. For example, A 25-iteration refinement of \
				an 80x80 boxsize stack of 100,000 particle at an angular sampling increment of 10 degrees will take ~1 CPU years to complete, i.e. \
				~ 33 hours on 256 processors!", metavar="INT")
		self.parser.add_option("--symid", dest="symid", type="int",
			help="symmetry database id, enter 25 for C1", metavar="ID#")
							
		### Xmipp ML3D-specific parameters
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
				
		### Xmipp path variables
		self.parser.add_option("--cluster_root_path", dest="cluster_root_path",
			help="path of the cluster where recon will be run, e.g. /ddn/people/dlyumkis/appion/11jan11a/recon/xmippML3Drecon2", metavar="PATH")
			
	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['apix'] is None:
			apDisplay.printError("pixel size is not defined")
		if self.params['boxsize'] is None:
			self.params['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		num_in_models = len(self.params['modelid'].split(","))
		if num_in_models > 1:
			if num_in_models != self.params['NumberOfReferences']:
				apDisplay.printError("model IDs specified under '--modelid' must either refer to a single database entry or multiple database entries \
					whose sum is equivalent to '--NumberOfReferences'. Double check the values for '--modelid' and '--NumberOfReferences'")
		if self.params['cluster_root_path'] is None:
			apDisplay.printError("Please specify the path where the reconstruction will be run on a remote cluster")
		
		return
		
	#=====================
	def dumpParameters(self, parameters):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = os.path.join(self.params['rundir'], "ml3d-"+self.timestamp+"-params.pickle")
		pf = open(paramfile, "w")
		cPickle.dump(parameters, pf)
		pf.close()
		
		return

	#=====================
	def start(self):
		### change to run directory
		os.chdir(self.params['rundir'])
	
		### Locate protocol_ml3d
		protocol_ml3d = apXmipp.locateXmippProtocol("xmipp_protocol_ml3d.py")

		### THIS STEP SHOULD BE DONE BY THE STACK CONVERTER IN THE JOB FILE
		
		### Convert input images to Spider
		stackdata = apStack.getOnlyStackData(self.params['stackid'])
		fnStack=os.path.join(stackdata['path']['path'], stackdata['name'])
		if os.path.exists(fnStack):
			partsellist = apXmipp.breakupStackIntoSingleFiles(fnStack)
		
		### scale all initial models and output in SPIDER format
		if not os.path.isdir(os.path.join(self.params['rundir'], "volumes")):
			os.mkdir(os.path.join(self.params['rundir'], "volumes"))
		modelselfile = open(os.path.join(self.params['rundir'], "initialmodels.sel"), "w")
		models = self.params['modelid'].split(",")
		for i in range(len(models)):
			modelid = models[i]
			spidervol = os.path.join(self.params['rundir'], "volumes", "it%.3i_vol%.3i.vol" % (0, i+1))
			apModel.rescaleModel(modelid, spidervol, self.params['boxsize'], self.params['apix'], spider=True)
			modelselfile.write(str(spidervol)+" 1\n")
					
		### setup protocol parameters
		protocolPrm = {}
#		protocolPrm["InSelFile"]						=	os.path.basename(partsellist)
		protocolPrm["InSelFile"]						=	"partlist.sel" ### this probably should not be hardcoded
		protocolPrm["InitialReference"]					=	os.path.join(self.params['rundir'], "volumes", "it%.3i_vol%.3i.vol" % (0, 1))
		protocolPrm["WorkingDir"]						=	"run1"
		protocolPrm["DoDeleteWorkingDir"]				=	False
		protocolPrm["ProjectDir"]						=	self.params['rundir']
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
		protocolPrm["DoGenerateSeeds"]					=	True
		protocolPrm["NumberOfReferences"]				=	self.params['NumberOfReferences']
		protocolPrm["DoJustRefine"]						=	False
		if len(models) > 1:
			protocolPrm["SeedsSelfile"]					=	os.path.join(self.params['rundir'], "initialmodels.sel")
		else:
			protocolPrm["SeedsSelfile"]					=	""
		protocolPrm["DoML3DClassification"]				=	True
		protocolPrm["AngularSampling"]					=	self.params['AngularSampling']
		protocolPrm["NumberOfIterations"]				=	self.params['numiter']
		protocolPrm["Symmetry"]							=	apSymmetry.getSymmetryDataFromID(self.params['symid'])['symmetry']
		protocolPrm["DoNorm"]							=	False
		protocolPrm["DoFourier"]						=	False
		protocolPrm["RestartIter"]						=	0
		protocolPrm["ExtraParamsMLrefine3D"]			=	""
		protocolPrm["NumberOfThreads"]					=	1
		protocolPrm["DoParallel"]						=	True
		protocolPrm["NumberOfMpiProcesses"]				=	self.params['nproc']
		protocolPrm["SystemFlavour"]					=	""
		protocolPrm["AnalysisScript"]					=	"visualize_ml3d.py"
		
		### write out python protocol into run directory
		apXmipp.particularizeProtocol(protocol_ml3d, protocolPrm, os.path.join(self.params['rundir'], "xmipp_protocol_ml3d.py"))
		os.chmod(os.path.join(self.params['rundir'], "xmipp_protocol_ml3d.py"), 0775)
				
		### Write the parameters for posterior uploading, both generic and specific
		self.params['mask'] = None
		self.params['imask'] = None
		self.params['reconstruction_package'] = "xmipp_ml3d"
		self.params['upload_root_path'] = self.params['rundir']
		self.params['cluster_root_path'] = self.params['cluster_root_path']
		self.params['reconstruction_working_dir'] = protocolPrm['WorkingDir']+"/RunML3D"
		self.params['package_params'] = protocolPrm
		self.dumpParameters(self.params)
		
		### finished setup of input files, now run xmipp_protocols_ml3d.py from jobfile
		apDisplay.printMsg("finished setting up input files, now running xmipp_protocols_ml3d.py")
		

#=====================
if __name__ == "__main__":
	ml3drefine3d = xmippML3DRefineScript()
	ml3drefine3d.start()
	ml3drefine3d.close()

